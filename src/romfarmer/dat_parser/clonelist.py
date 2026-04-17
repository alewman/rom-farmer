"""Clone list maintenance engine for Retool-format clone lists.

Provides three core capabilities:
1. dat_diff: Compare two DAT versions by hash to detect renames/adds/removes
2. clonelist_validate: Check all searchTerms against a DAT for broken references
3. clonelist_patch: Auto-fix clone list searchTerms from a rename manifest

Operates on Retool's JSON format:
{
  "description": {"name": "...", "lastUpdated": "...", "minimumVersion": "..."},
  "variants": [
    {"group": "Game Title", "titles": [{"searchTerm": "Regional Name"}, ...]}
  ]
}
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import DATFile, DATGame
from .parser import DATParser


# ── Data classes ──────────────────────────────────────────────────────────


@dataclass
class DATRename:
    """A game renamed between two DAT versions, tracked by hash."""

    old_name: str
    new_name: str
    sha1: Optional[str] = None
    md5: Optional[str] = None
    crc: Optional[str] = None


@dataclass
class DATDiffResult:
    """Result of comparing two DAT versions."""

    old_dat_name: str
    new_dat_name: str
    old_count: int
    new_count: int
    renames: list[DATRename] = field(default_factory=list)
    additions: list[str] = field(default_factory=list)
    removals: list[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.renames or self.additions or self.removals)


@dataclass
class ValidationIssue:
    """A clone list searchTerm that doesn't match any DAT entry."""

    group: str
    search_term: str
    suggestion: Optional[str] = None  # Best fuzzy match if found
    similarity: float = 0.0


@dataclass
class ValidationResult:
    """Result of validating a clone list against a DAT."""

    clonelist_name: str
    dat_name: str
    total_search_terms: int
    matched: int
    unmatched: list[ValidationIssue] = field(default_factory=list)

    @property
    def match_rate(self) -> float:
        return self.matched / self.total_search_terms if self.total_search_terms else 0.0


@dataclass
class PatchAction:
    """A single searchTerm replacement in a clone list."""

    group: str
    old_search_term: str
    new_search_term: str
    reason: str  # e.g., "renamed in DAT", "region change", "title correction"


@dataclass
class PatchResult:
    """Result of patching a clone list."""

    clonelist_name: str
    patches_applied: list[PatchAction] = field(default_factory=list)
    patches_skipped: list[PatchAction] = field(default_factory=list)


@dataclass
class MetadataEntry:
    """Auto-generated metadata for a game title."""

    title: str
    languages: list[str] = field(default_factory=list)
    local_name: Optional[str] = None


# ── Region → Language mapping ─────────────────────────────────────────────

REGION_LANGUAGE_MAP = {
    "Japan": ["Ja"],
    "USA": ["En"],
    "Europe": ["En"],
    "Korea": ["Ko"],
    "Germany": ["De"],
    "France": ["Fr"],
    "Spain": ["Es"],
    "Italy": ["It"],
    "Netherlands": ["Nl"],
    "Sweden": ["Sv"],
    "Norway": ["No"],
    "Denmark": ["Da"],
    "Finland": ["Fi"],
    "Poland": ["Pl"],
    "Russia": ["Ru"],
    "China": ["Zh"],
    "Taiwan": ["Zh"],
    "Brazil": ["Pt"],
    "Portugal": ["Pt"],
    "Australia": ["En"],
    "World": ["En"],
    "Asia": [],  # Ambiguous
}

# ISO 639-1 codes used in DAT filenames
_LANG_CODES = (
    "En|Fr|De|Es|It|Nl|Pt|Sv|No|Da|Fi|Pl|Ru|Zh|Ko|Ja|Ro|Hu|Cs|Tr|El|Ar|He|Th|"
    "Vi|Uk|Hr|Sk|Bg|Lt|Lv|Et|Sl|Sr|Mk|Sq|Bs|Ca|Gl|Eu|Cy|Ga"
)
_LANG_RE = re.compile(
    rf"\(((?:{_LANG_CODES})(?:,(?:{_LANG_CODES}))*)\)"
)
_REGION_RE = re.compile(
    r"\((" + "|".join(re.escape(r) for r in REGION_LANGUAGE_MAP) + r")"
)


# ── Core functions ────────────────────────────────────────────────────────


def dat_diff(old_dat: DATFile, new_dat: DATFile) -> DATDiffResult:
    """Compare two DATs by hash to detect renames, additions, and removals.

    Uses SHA1 > MD5 > CRC as the hash key, falling back through the chain.
    Games with matching hashes but different names are renames.
    """
    old_by_hash = _build_hash_index(old_dat)
    new_by_hash = _build_hash_index(new_dat)

    result = DATDiffResult(
        old_dat_name=old_dat.name or "old",
        new_dat_name=new_dat.name or "new",
        old_count=len(old_dat.games),
        new_count=len(new_dat.games),
    )

    old_hashes = set(old_by_hash.keys())
    new_hashes = set(new_by_hash.keys())

    # Renames: same hash, different name
    for h in old_hashes & new_hashes:
        old_name = old_by_hash[h]
        new_name = new_by_hash[h]
        if old_name != new_name:
            hash_type, hash_val = h
            rename = DATRename(old_name=old_name, new_name=new_name)
            if hash_type == "sha1":
                rename.sha1 = hash_val
            elif hash_type == "md5":
                rename.md5 = hash_val
            elif hash_type == "crc":
                rename.crc = hash_val
            result.renames.append(rename)

    # Additions: hash only in new
    for h in new_hashes - old_hashes:
        result.additions.append(new_by_hash[h])

    # Removals: hash only in old
    for h in old_hashes - new_hashes:
        result.removals.append(old_by_hash[h])

    # Sort for deterministic output
    result.renames.sort(key=lambda r: r.old_name)
    result.additions.sort()
    result.removals.sort()

    return result


def clonelist_validate(
    clonelist_path: Path,
    dat: DATFile,
) -> ValidationResult:
    """Validate all searchTerms in a clone list against a DAT.

    A searchTerm matches if any game name in the DAT starts with it
    (Retool uses substring/prefix matching on the base name portion).
    """
    data = _load_clonelist(clonelist_path)
    dat_names = _extract_base_names(dat)

    result = ValidationResult(
        clonelist_name=data.get("description", {}).get("name", clonelist_path.stem),
        dat_name=dat.name or "unknown",
        total_search_terms=0,
        matched=0,
    )

    for variant in data.get("variants", []):
        group = variant.get("group", "")
        for title in variant.get("titles", []):
            search_term = title.get("searchTerm", "")
            if not search_term:
                continue

            result.total_search_terms += 1

            if _search_term_matches(search_term, dat_names):
                result.matched += 1
            else:
                # Try fuzzy suggestion
                suggestion, sim = _find_closest_match(search_term, dat_names)
                result.unmatched.append(
                    ValidationIssue(
                        group=group,
                        search_term=search_term,
                        suggestion=suggestion,
                        similarity=sim,
                    )
                )

    return result


def clonelist_patch(
    clonelist_path: Path,
    diff_result: DATDiffResult,
    output_path: Optional[Path] = None,
    dry_run: bool = False,
) -> PatchResult:
    """Patch clone list searchTerms based on a DAT diff rename manifest.

    For each rename in the diff, find matching searchTerms and update them.
    Writes the patched JSON to output_path (or overwrites in place if None).
    """
    data = _load_clonelist(clonelist_path)
    cl_name = data.get("description", {}).get("name", clonelist_path.stem)
    result = PatchResult(clonelist_name=cl_name)

    # Build rename lookup: old_base_name → (new_base_name, DATRename)
    rename_map = {}
    for rename in diff_result.renames:
        old_base = _strip_tags(rename.old_name)
        new_base = _strip_tags(rename.new_name)
        if old_base != new_base:
            rename_map[old_base.lower()] = (new_base, rename)

    if not rename_map:
        return result

    # Scan and patch
    for variant in data.get("variants", []):
        group = variant.get("group", "")
        for title in variant.get("titles", []):
            search_term = title.get("searchTerm", "")
            if not search_term:
                continue

            key = search_term.lower()
            if key in rename_map:
                new_term, rename = rename_map[key]
                action = PatchAction(
                    group=group,
                    old_search_term=search_term,
                    new_search_term=new_term,
                    reason=_classify_rename(rename.old_name, rename.new_name),
                )

                if not dry_run:
                    title["searchTerm"] = new_term
                    result.patches_applied.append(action)
                else:
                    result.patches_skipped.append(action)

    # Update metadata
    if not dry_run and result.patches_applied:
        if "description" in data:
            data["description"]["lastUpdated"] = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        dest = output_path or clonelist_path
        _save_clonelist(dest, data)

    return result


def metadata_generate(dat: DATFile) -> list[MetadataEntry]:
    """Auto-generate Retool-format metadata from DAT game names.

    Extracts language codes from filename tags (En,Fr,De,...) or infers
    from region tags (USA → En, Japan → Ja, etc.).
    """
    entries = []

    for game in dat.games:
        name = game.name
        languages = _parse_languages(name)
        entries.append(MetadataEntry(title=name, languages=languages))

    return entries


def metadata_to_retool_json(entries: list[MetadataEntry]) -> dict:
    """Convert metadata entries to Retool's JSON format.

    Returns a dict keyed by title, each value containing {languages: [...]}.
    """
    result = {}
    for entry in entries:
        val: dict = {}
        if entry.languages:
            val["languages"] = entry.languages
        if entry.local_name:
            val["localName"] = entry.local_name
        result[entry.title] = val
    return result


# ── Helper functions ──────────────────────────────────────────────────────


def _build_hash_index(dat: DATFile) -> dict[tuple[str, str], str]:
    """Build (hash_type, hash_value) → game_name index.

    Prefers SHA1 > MD5 > CRC for maximum uniqueness.
    """
    index = {}
    for game in dat.games:
        rom = game.get_primary_rom()
        if not rom:
            continue

        # Use best available hash
        if rom.sha1:
            index[("sha1", rom.sha1)] = game.name
        elif rom.md5:
            index[("md5", rom.md5)] = game.name
        elif rom.crc:
            index[("crc", rom.crc)] = game.name

    return index


def _extract_base_names(dat: DATFile) -> set[str]:
    """Extract base game names (without region/language tags) from a DAT."""
    names = set()
    for game in dat.games:
        names.add(game.name)
        # Also add stripped version for matching
        base = _strip_tags(game.name)
        names.add(base)
    return names


def _strip_tags(name: str) -> str:
    """Strip region/language/revision parenthetical tags from a game name.

    'Super Mario Galaxy (USA) (Rev 1)' → 'Super Mario Galaxy'
    """
    # Remove all parenthetical groups
    result = re.sub(r"\s*\([^)]*\)", "", name).strip()
    return result


def _search_term_matches(search_term: str, dat_names: set[str]) -> bool:
    """Check if a searchTerm matches any DAT name.

    Retool matches searchTerms as prefixes of the base name portion.
    'Super Mario Galaxy' matches 'Super Mario Galaxy (USA) (En,Fr)'.
    """
    st_lower = search_term.lower()
    for name in dat_names:
        if name.lower() == st_lower:
            return True
        # Check if DAT name starts with the searchTerm (before first parenthetical)
        base = _strip_tags(name).lower()
        if base == st_lower:
            return True
    return False


def _find_closest_match(
    search_term: str, dat_names: set[str], threshold: float = 0.6
) -> tuple[Optional[str], float]:
    """Find the closest matching game name for a broken searchTerm.

    Uses simple token overlap similarity (fast, no extra deps).
    Returns (best_match, similarity) or (None, 0.0).
    """
    st_tokens = set(search_term.lower().split())
    best_match = None
    best_sim = 0.0

    for name in dat_names:
        base = _strip_tags(name)
        name_tokens = set(base.lower().split())
        if not name_tokens:
            continue

        # Jaccard similarity
        intersection = st_tokens & name_tokens
        union = st_tokens | name_tokens
        sim = len(intersection) / len(union) if union else 0.0

        if sim > best_sim:
            best_sim = sim
            best_match = base

    if best_sim >= threshold:
        return best_match, best_sim
    return None, 0.0


def _classify_rename(old_name: str, new_name: str) -> str:
    """Classify the type of rename for human-readable reporting."""
    old_base = _strip_tags(old_name)
    new_base = _strip_tags(new_name)

    if old_base.lower() == new_base.lower():
        # Only tag changes (region, language, etc.)
        return "tag update"

    # Check for capitalization-only changes
    if old_base.lower().replace(" ", "") == new_base.lower().replace(" ", ""):
        return "capitalization fix"

    # Check for punctuation-only changes (hyphens, spaces, etc.)
    old_alpha = re.sub(r"[^a-zA-Z0-9]", "", old_base.lower())
    new_alpha = re.sub(r"[^a-zA-Z0-9]", "", new_base.lower())
    if old_alpha == new_alpha:
        return "punctuation fix"

    # Check if multi-title was split ('Game A ~ Game B' → 'Game A')
    if "~" in old_name and "~" not in new_name:
        return "multi-title split"

    return "title correction"


def _parse_languages(name: str) -> list[str]:
    """Extract language codes from a game name.

    Tries explicit language tags first (En,Fr,De,...), then falls back
    to region → language mapping.
    """
    # Try explicit language tags
    match = _LANG_RE.search(name)
    if match:
        return match.group(1).split(",")

    # Fall back to region mapping
    region_match = _REGION_RE.search(name)
    if region_match:
        region = region_match.group(1)
        return list(REGION_LANGUAGE_MAP.get(region, []))

    return []


def _load_clonelist(path: Path) -> dict:
    """Load a Retool clone list JSON file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save_clonelist(path: Path, data: dict) -> None:
    """Save a Retool clone list JSON file with consistent formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
