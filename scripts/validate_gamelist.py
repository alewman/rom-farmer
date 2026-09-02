#!/usr/bin/env python3
"""
Validate gamelist.xml files for RetroBat platforms.

Checks:
  1. XML parses without error
  2. Every <game>/<folder> has a <path> element
  3. ROM/folder paths exist on disk (relative to the platform directory)
  4. All media paths (image, screenshot, boxart, wheel, cartridge, marquee,
     mix, video, manual, thumbnail, fanart, titleshot, map, bezel, magazine,
     boxback) point to existing files when non-empty
  5. No duplicate <path> entries within a single gamelist
  6. ARRM-style sortnames ("3595 =-  Game Name") that break ES alphabetical sort
  7. ZZZ(notgame)/#NONGAME entries that should be hidden or excluded
  8. Duplicate display names (same <name>, different <path>) — e.g. "(A)/(B)/(C)" sets
  9. Metadata coverage stats (--stats): % of games with desc/image/rating

Fixes (applied in-place when requested):
  --fix-sortnames   Strip the ARRM numeric prefix from <sortname> fields.
                    "3595 =-  Game Name" -> "Game Name"
                    If the result equals <name>, the <sortname> element is removed.
  --fix-nongames    Set <hidden>true</hidden> on all ZZZ(notgame) entries.

Usage:
  # Quick summary of all platforms
  python validate_gamelist.py /path/to/roms

  # Only show broken platforms
  python validate_gamelist.py --errors-only /path/to/roms

  # Verbose: list every broken entry
  python validate_gamelist.py -v --errors-only /path/to/roms/gb

  # Skip media checks (structure + ROM paths only)
  python validate_gamelist.py --no-media /path/to/roms

  # Show metadata coverage stats
  python validate_gamelist.py --stats /path/to/roms

  # Fix ARRM sortnames across all platforms (writes files in-place)
  python validate_gamelist.py --fix-sortnames /path/to/roms

  # Fix + hide ZZZ nongame entries
  python validate_gamelist.py --fix-sortnames --fix-nongames /path/to/roms
"""

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

# ARRM sortname prefix: "3595 =-  " or "128 =-  "
_ARRM_SORTNAME_RE = re.compile(r"^\d+\s+=-\s+")

# All media fields ES reads from gamelist.xml
MEDIA_FIELDS = [
    "image",
    "thumbnail",
    "video",
    "marquee",
    "wheel",
    "boxart",
    "boxback",
    "cartridge",
    "screenshot",
    "mix",
    "fanart",
    "titleshot",
    "manual",
    "magazine",
    "map",
    "bezel",
]


@dataclass
class Issue:
    entry_type: str  # "game" or "folder"
    name: str  # display name (or path stem if no name)
    path: str  # the <path> value
    kind: str  # "missing_rom", "missing_media", "no_path", "duplicate",
    # "arrm_sortname", "nongame", "duplicate_name"
    detail: str  # which field / what path is missing


@dataclass
class MetadataCoverage:
    total: int = 0
    has_name: int = 0
    has_desc: int = 0
    has_image: int = 0
    has_rating: int = 0
    has_video: int = 0

    def pct(self, n: int) -> str:
        if self.total == 0:
            return "n/a"
        return f"{100 * n // self.total}%"


@dataclass
class PlatformResult:
    platform: str
    gamelist_path: Path
    parse_error: str | None = None

    total: int = 0
    ok: int = 0
    issues: list = field(default_factory=list)
    coverage: MetadataCoverage = field(default_factory=MetadataCoverage)
    sortnames_fixed: int = 0
    nongames_hidden: int = 0

    @property
    def missing_rom_count(self) -> int:
        return sum(1 for i in self.issues if i.kind == "missing_rom")

    @property
    def missing_media_count(self) -> int:
        return sum(1 for i in self.issues if i.kind == "missing_media")

    @property
    def duplicate_count(self) -> int:
        return sum(1 for i in self.issues if i.kind == "duplicate")

    @property
    def no_path_count(self) -> int:
        return sum(1 for i in self.issues if i.kind == "no_path")

    @property
    def arrm_sortname_count(self) -> int:
        return sum(1 for i in self.issues if i.kind == "arrm_sortname")

    @property
    def nongame_count(self) -> int:
        return sum(1 for i in self.issues if i.kind == "nongame")

    @property
    def duplicate_name_count(self) -> int:
        return sum(1 for i in self.issues if i.kind == "duplicate_name")

    @property
    def has_issues(self) -> bool:
        return bool(self.parse_error or self.issues)


def resolve_path(platform_dir: Path, raw_path: str) -> Path:
    """Resolve a gamelist-relative path to an absolute filesystem path."""
    # Paths start with "./" — strip and join with platform dir
    stripped = raw_path.lstrip("./").lstrip("/")
    return platform_dir / stripped


def strip_arrm_prefix(sortname: str) -> str:
    """Remove ARRM numeric prefix: '3595 =-  Game Name' -> 'Game Name'."""
    return _ARRM_SORTNAME_RE.sub("", sortname).strip()


def validate_platform(
    platform_dir: Path,
    check_media: bool = True,
    fix_sortnames: bool = False,
    fix_nongames: bool = False,
) -> PlatformResult:
    gamelist_path = platform_dir / "gamelist.xml"
    result = PlatformResult(
        platform=platform_dir.name,
        gamelist_path=gamelist_path,
    )

    if not gamelist_path.exists():
        result.parse_error = "gamelist.xml not found"
        return result

    # 1. XML parse check
    try:
        tree = ET.parse(gamelist_path)
    except ET.ParseError as e:
        result.parse_error = f"XML parse error: {e}"
        return result

    root = tree.getroot()
    modified = False  # track if we need to write the file back

    # First pass: collect all visible display names at root level for duplicate-name detection
    # (Only root-level games; subdir entries legitimately repeat names. Exclude hidden entries.)
    root_name_counts: Counter = Counter()
    for elem in root:
        if elem.tag != "game":
            continue
        path_el = elem.find("path")
        if path_el is None or not path_el.text:
            continue
        # Root-level only (no "/" in the path besides the leading "./")
        rel = path_el.text.lstrip("./")
        if "/" not in rel:
            # Skip already-hidden entries
            if elem.findtext("hidden", "").strip().lower() == "true":
                continue
            name_el = elem.find("name")
            name = (name_el.text or "").strip() if name_el is not None else ""
            if name and not name.startswith("ZZZ(notgame)"):
                root_name_counts[name] += 1

    # Second pass: full validation
    seen_paths: dict[str, int] = {}

    for elem in root:
        tag = elem.tag
        if tag not in ("game", "folder"):
            continue

        result.total += 1
        entry_had_issue = False

        name_el = elem.find("name")
        name = (name_el.text or "").strip() if name_el is not None else ""

        path_el = elem.find("path")
        if path_el is None or not path_el.text:
            result.issues.append(
                Issue(
                    entry_type=tag,
                    name=name,
                    path="",
                    kind="no_path",
                    detail="<path> element is missing or empty",
                )
            )
            entry_had_issue = True
            continue

        raw_path = path_el.text
        display_name = name or Path(raw_path).stem
        rel = raw_path.lstrip("./")
        is_root_entry = "/" not in rel

        # 2. ZZZ / nongame check (skip if already hidden)
        already_hidden = elem.findtext("hidden", "").strip().lower() == "true"
        if (name.startswith("ZZZ(notgame)") or name == "#NONGAME") and not already_hidden:
            result.issues.append(
                Issue(
                    entry_type=tag,
                    name=display_name,
                    path=raw_path,
                    kind="nongame",
                    detail="ZZZ(notgame) entry should be hidden",
                )
            )
            entry_had_issue = True
            if fix_nongames:
                hidden_el = elem.find("hidden")
                if hidden_el is None:
                    hidden_el = ET.SubElement(elem, "hidden")
                if hidden_el.text != "true":
                    hidden_el.text = "true"
                    result.nongames_hidden += 1
                    modified = True

        # 3. ARRM sortname check
        sortname_el = elem.find("sortname")
        if sortname_el is not None and sortname_el.text:
            if _ARRM_SORTNAME_RE.match(sortname_el.text):
                cleaned = strip_arrm_prefix(sortname_el.text)
                result.issues.append(
                    Issue(
                        entry_type=tag,
                        name=display_name,
                        path=raw_path,
                        kind="arrm_sortname",
                        detail=f"ARRM prefix: {sortname_el.text!r} -> {cleaned!r}",
                    )
                )
                entry_had_issue = True
                if fix_sortnames:
                    if cleaned == name or not cleaned:
                        # sortname equals name — just remove it
                        elem.remove(sortname_el)
                    else:
                        sortname_el.text = cleaned
                    result.sortnames_fixed += 1
                    modified = True

        # 4. Duplicate path check
        if raw_path in seen_paths:
            result.issues.append(
                Issue(
                    entry_type=tag,
                    name=display_name,
                    path=raw_path,
                    kind="duplicate",
                    detail="duplicate of earlier entry",
                )
            )
            entry_had_issue = True
        else:
            seen_paths[raw_path] = 1

        # 5. Duplicate display name check (root-level visible games only)
        if (
            is_root_entry
            and tag == "game"
            and name
            and not already_hidden
            and not name.startswith("ZZZ(notgame)")
            and root_name_counts[name] > 1
        ):
            result.issues.append(
                Issue(
                    entry_type=tag,
                    name=display_name,
                    path=raw_path,
                    kind="duplicate_name",
                    detail=f"display name appears {root_name_counts[name]}x in root",
                )
            )
            entry_had_issue = True

        # 6. ROM/folder path existence
        abs_path = resolve_path(platform_dir, raw_path)
        if not abs_path.exists():
            result.issues.append(
                Issue(
                    entry_type=tag,
                    name=display_name,
                    path=raw_path,
                    kind="missing_rom",
                    detail=f"path does not exist: {abs_path}",
                )
            )
            entry_had_issue = True

        # 7. Media field existence
        if check_media:
            for field_name in MEDIA_FIELDS:
                media_el = elem.find(field_name)
                if media_el is None or not media_el.text or not media_el.text.strip():
                    continue
                media_abs = resolve_path(platform_dir, media_el.text)
                if not media_abs.exists():
                    result.issues.append(
                        Issue(
                            entry_type=tag,
                            name=display_name,
                            path=raw_path,
                            kind="missing_media",
                            detail=f"<{field_name}> missing: {media_abs}",
                        )
                    )
                    entry_had_issue = True

        # 8. Metadata coverage (root-level games only)
        if is_root_entry and tag == "game":
            cov = result.coverage
            cov.total += 1
            if name:
                cov.has_name += 1
            if elem.findtext("desc", "").strip():
                cov.has_desc += 1
            if elem.findtext("image", "").strip():
                cov.has_image += 1
            if elem.findtext("rating", "").strip():
                cov.has_rating += 1
            if elem.findtext("video", "").strip():
                cov.has_video += 1

        if not entry_had_issue:
            result.ok += 1

    if modified:
        ET.indent(tree, space="  ")
        tree.write(str(gamelist_path), encoding="utf-8", xml_declaration=True)

    return result


def format_result(
    result: PlatformResult,
    verbose: bool,
    errors_only: bool,
    show_stats: bool,
) -> str | None:
    """Format a single platform result for output. Returns None if suppressed."""
    lines = []

    if result.parse_error:
        lines.append(f"  [PARSE ERROR] {result.parse_error}")
    else:
        media_issues = sum(1 for i in result.issues if i.kind == "missing_media")
        status = "OK" if not result.has_issues else "FAIL"
        lines.append(
            f"  [{status}] {result.total} entries | "
            f"{result.ok} clean | "
            f"missing rom: {result.missing_rom_count} | "
            f"missing media: {media_issues} | "
            f"dup path: {result.duplicate_count} | "
            f"nongame: {result.nongame_count} | "
            f"bad sortname: {result.arrm_sortname_count} | "
            f"dup name: {result.duplicate_name_count}"
        )

        if result.sortnames_fixed or result.nongames_hidden:
            fixes = []
            if result.sortnames_fixed:
                fixes.append(f"sortnames fixed: {result.sortnames_fixed}")
            if result.nongames_hidden:
                fixes.append(f"nongames hidden: {result.nongames_hidden}")
            lines.append("  [FIXED] " + ", ".join(fixes))

        if show_stats and result.coverage.total > 0:
            cov = result.coverage
            lines.append(
                f"  [STATS] root games: {cov.total} | "
                f"desc: {cov.pct(cov.has_desc)} | "
                f"image: {cov.pct(cov.has_image)} | "
                f"rating: {cov.pct(cov.has_rating)} | "
                f"video: {cov.pct(cov.has_video)}"
            )

        if verbose and result.issues:
            for kind_label, kind_key in [
                ("MISSING ROM", "missing_rom"),
                ("DUPLICATE PATH", "duplicate"),
                ("NO PATH", "no_path"),
                ("NONGAME", "nongame"),
                ("BAD SORTNAME", "arrm_sortname"),
                ("DUPLICATE NAME", "duplicate_name"),
            ]:
                kind_issues = [i for i in result.issues if i.kind == kind_key]
                if not kind_issues:
                    continue
                lines.append(f"    [{kind_label}] ({len(kind_issues)})")
                for issue in kind_issues:
                    lines.append(f"      {issue.name!r}  {issue.path}")
                    if issue.detail and kind_key not in (
                        "nongame",
                        "duplicate_name",
                        "missing_rom",
                    ):
                        lines.append(f"        -> {issue.detail}")

            media_issues_list = [i for i in result.issues if i.kind == "missing_media"]
            if media_issues_list:
                lines.append(f"    [MISSING MEDIA] ({len(media_issues_list)} refs)")
                by_game: dict[str, list] = {}
                for issue in media_issues_list:
                    by_game.setdefault(issue.name, []).append(issue.detail)
                for game_name, details in by_game.items():
                    lines.append(f"      {game_name!r}:")
                    for d in details:
                        lines.append(f"        {d}")

    if errors_only and not result.has_issues and not result.parse_error:
        if not (show_stats and result.coverage.total > 0):
            return None

    header = f"{result.platform}  ({result.gamelist_path})"
    return header + "\n" + "\n".join(lines)


def find_platforms(base: Path) -> list[Path]:
    """Return sorted list of platform directories under base that have a gamelist.xml."""
    return sorted(d for d in base.iterdir() if d.is_dir() and (d / "gamelist.xml").exists())


def main():
    parser = argparse.ArgumentParser(
        description="Validate gamelist.xml files for RetroBat platforms.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "paths",
        nargs="+",
        metavar="PATH",
        help=(
            "Platform directory (e.g. roms-retrobat/gb) or base directory "
            "(e.g. roms-retrobat) to scan all platforms."
        ),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show every broken entry (default: summary only)",
    )
    parser.add_argument(
        "--errors-only",
        action="store_true",
        help="Only print platforms that have issues",
    )
    parser.add_argument(
        "--no-media",
        action="store_true",
        help="Skip media path checks (only validate ROM paths and XML structure)",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show metadata coverage stats per platform (desc/image/rating/video %%)",
    )
    parser.add_argument(
        "--fix-sortnames",
        action="store_true",
        help=(
            "Strip ARRM numeric prefix from <sortname> fields in-place. "
            "'3595 =-  Game Name' -> 'Game Name' (or removes <sortname> if result == <name>)"
        ),
    )
    parser.add_argument(
        "--fix-nongames",
        action="store_true",
        help="Set <hidden>true</hidden> on all ZZZ(notgame) entries in-place.",
    )
    args = parser.parse_args()

    if args.fix_sortnames or args.fix_nongames:
        fixes = []
        if args.fix_sortnames:
            fixes.append("--fix-sortnames")
        if args.fix_nongames:
            fixes.append("--fix-nongames")
        print(f"FIX MODE: {', '.join(fixes)} — files will be written in-place")
        print()

    platforms: list[Path] = []
    for raw in args.paths:
        p = Path(raw)
        if not p.exists():
            print(f"ERROR: path not found: {p}", file=sys.stderr)
            sys.exit(1)
        if (p / "gamelist.xml").exists():
            platforms.append(p)
        elif p.is_dir():
            found = find_platforms(p)
            if not found:
                print(f"WARNING: no gamelist.xml found under {p}", file=sys.stderr)
            platforms.extend(found)
        else:
            print(f"ERROR: {p} is not a directory", file=sys.stderr)
            sys.exit(1)

    if not platforms:
        print("No platforms to validate.", file=sys.stderr)
        sys.exit(1)

    total_platforms = 0
    platforms_with_issues = 0
    grand_total = 0
    grand_ok = 0
    grand_missing_rom = 0
    grand_missing_media = 0
    grand_duplicates = 0
    grand_arrm = 0
    grand_nongame = 0
    grand_dup_name = 0
    grand_sortnames_fixed = 0
    grand_nongames_hidden = 0

    for platform_dir in platforms:
        result = validate_platform(
            platform_dir,
            check_media=not args.no_media,
            fix_sortnames=args.fix_sortnames,
            fix_nongames=args.fix_nongames,
        )

        output = format_result(
            result,
            verbose=args.verbose,
            errors_only=args.errors_only,
            show_stats=args.stats,
        )
        if output is not None:
            print(output)

        total_platforms += 1
        if result.has_issues:
            platforms_with_issues += 1
        grand_total += result.total
        grand_ok += result.ok
        grand_missing_rom += result.missing_rom_count
        grand_missing_media += result.missing_media_count
        grand_duplicates += result.duplicate_count
        grand_arrm += result.arrm_sortname_count
        grand_nongame += result.nongame_count
        grand_dup_name += result.duplicate_name_count
        grand_sortnames_fixed += result.sortnames_fixed
        grand_nongames_hidden += result.nongames_hidden

    print()
    print("=" * 60)
    print(f"SUMMARY  ({total_platforms} platforms)")
    print(f"  Total entries:       {grand_total}")
    print(f"  Clean entries:       {grand_ok}")
    print(f"  Missing ROM paths:   {grand_missing_rom}")
    print(f"  Missing media refs:  {grand_missing_media}")
    print(f"  Duplicate paths:     {grand_duplicates}")
    print(f"  ARRM bad sortnames:  {grand_arrm}")
    print(f"  ZZZ nongame entries: {grand_nongame}")
    print(f"  Duplicate names:     {grand_dup_name}")
    if args.fix_sortnames or args.fix_nongames:
        print()
        print(f"  Sortnames fixed:     {grand_sortnames_fixed}")
        print(f"  Nongames hidden:     {grand_nongames_hidden}")
    print(f"  Platforms OK:        {total_platforms - platforms_with_issues}/{total_platforms}")

    sys.exit(1 if platforms_with_issues > 0 else 0)


if __name__ == "__main__":
    main()
