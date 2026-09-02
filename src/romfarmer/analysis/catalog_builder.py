"""CatalogBuilder — CATALOG phase: scan + hash + DAT-match + grouping → Catalog.

This module absorbs the *identity* half of ``stages/filter_dat.py``: it
discovers source files, builds partial ``Identity`` objects (zip_identity from
ZIP central-dir + MD5 from the metadata DB cache), optionally matches against
a ``DATFile``, strips disc tags, groups multi-disc sets, and enriches each
``GameUnit`` with metadata from the ``KnowledgeBase``.

It does **not** create symlinks, write to the work directory, or modify any
global state.  It returns an immutable ``Catalog``.

Multi-disc atomicity: grouping happens *here* and nowhere else.  Once the
``Catalog`` is returned, every downstream planner pass operates at unit
granularity — there is no API to reach an individual ``DiscRef``.
See ``docs/compiler-refactor/04-edge-case-designs.md`` §1.
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
import zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING

from romfarmer.ir.catalog import (
    Catalog,
    CatalogWarning,
    DiscRef,
    GameUnit,
    PlatformId,
    SourceRef,
    UnitId,
)
from romfarmer.ir.identity import Identity, ZipIdentity

if TYPE_CHECKING:
    from romfarmer.analysis.file_digest_cache import FileDigestCache
    from romfarmer.analysis.knowledge import KnowledgeBase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Filename parsing helpers
# ---------------------------------------------------------------------------

_DISC_TAG = re.compile(r"\s*\((?:Disc|Disk|CD)\s*(\d+)\)", re.IGNORECASE)
_REGION_TAG = re.compile(r"\(([^)]+)\)")

# Ordered region-string keywords (matches against parenthetical tags)
_REGION_KEYWORDS: dict[str, frozenset[str]] = {
    "USA": frozenset({"usa", "us", "ntsc-u", "ntsc"}),
    "Europe": frozenset({"europe", "eur", "pal"}),
    "Japan": frozenset({"japan", "jpn", "ntsc-j"}),
    "World": frozenset({"world"}),
    "Germany": frozenset({"germany", "ger"}),
    "France": frozenset({"france", "fra"}),
    "Spain": frozenset({"spain", "spa"}),
    "Italy": frozenset({"italy", "ita"}),
    "Australia": frozenset({"australia", "aus"}),
    "Korea": frozenset({"korea", "kor"}),
    "China": frozenset({"china", "chi"}),
    "Brazil": frozenset({"brazil", "bra"}),
    "Netherlands": frozenset({"netherlands", "nld"}),
    "Sweden": frozenset({"sweden", "swe"}),
}

_LANG_TAG = re.compile(
    r"\((?:En|Fr|De|Es|It|Ja|Nl|Pt|Sv|No|Da|Fi|Pl|Ru|Zh|Ko)(?:[,+][A-Za-z]{2})*\)"
)


def _strip_disc_tag(stem: str) -> str:
    """Return the disc-tag-stripped canonical name for grouping."""
    return _DISC_TAG.sub("", stem).strip()


def _disc_index(stem: str) -> int:
    """Return the disc number (1-based) parsed from a filename stem."""
    m = _DISC_TAG.search(stem)
    return int(m.group(1)) if m else 1


def _parse_regions(name: str) -> frozenset[str]:
    """Extract known region strings from parenthetical tags."""
    found: set[str] = set()
    for tag in _REGION_TAG.findall(name):
        for part in re.split(r"[,;+/]", tag):
            token = part.strip().lower()
            for region, keywords in _REGION_KEYWORDS.items():
                if token in keywords:
                    found.add(region)
    return frozenset(found)


def _parse_languages(name: str) -> frozenset[str]:
    """Extract ISO-639-1 language codes from parenthetical tags."""
    found: set[str] = set()
    for m in _LANG_TAG.finditer(name):
        tag_inner = m.group().strip("()")
        for code in re.split(r"[,+]", tag_inner):
            found.add(code.strip())
    return frozenset(found)


# ---------------------------------------------------------------------------
# Identity helpers
# ---------------------------------------------------------------------------


def _zip_identity(path: Path) -> ZipIdentity | None:
    """Read ZIP central-dir to build a ``ZipIdentity`` (no extraction)."""
    try:
        with zipfile.ZipFile(path, "r") as zf:
            members = zf.infolist()
            if not members:
                return None
            # Pick the largest member (the ROM content) or the .cue for
            # CD-based sets — mirrors FilterDAT behaviour.
            cue_members = [m for m in members if m.filename.lower().endswith(".cue")]
            dominant = cue_members[0] if cue_members else max(members, key=lambda m: m.file_size)
            return ZipIdentity(
                member_crc32=dominant.CRC,
                member_size=dominant.file_size,
                member_name=dominant.filename,
            )
    except (zipfile.BadZipFile, OSError) as exc:
        logger.debug("_zip_identity(%s): %s", path, exc)
        return None


def _md5_from_zip(path: Path) -> str | None:
    """Compute MD5 of the dominant member of a ZIP (full extraction in memory).

    Used only when the metadata DB has no cached value.
    """
    try:
        with zipfile.ZipFile(path, "r") as zf:
            members = zf.infolist()
            if not members:
                return None
            cue_members = [m for m in members if m.filename.lower().endswith(".cue")]
            dominant = cue_members[0] if cue_members else max(members, key=lambda m: m.file_size)
            data = zf.read(dominant.filename)
        md5 = hashlib.md5(data)
        return md5.hexdigest()
    except (zipfile.BadZipFile, OSError, KeyError) as exc:
        logger.debug("_md5_from_zip(%s): %s", path, exc)
        return None


def _identity_for(path: Path, md5_cache: dict[Path, str]) -> Identity:
    """Build a partial ``Identity`` for *path*."""
    size = path.stat().st_size if path.exists() else None
    md5 = md5_cache.get(path)
    if path.suffix.lower() == ".zip":
        zip_id = _zip_identity(path)
        return Identity(size=size, md5=md5, zip_identity=zip_id)
    return Identity(size=size, md5=md5)


# ---------------------------------------------------------------------------
# DAT matching helpers
# ---------------------------------------------------------------------------


def _dat_name_for(path: Path, md5_cache: dict[Path, str], dat_file: object | None) -> str | None:
    """Return the canonical DAT name for *path*, or ``None`` if unmatched."""
    if dat_file is None:
        return None
    try:
        from romfarmer.dat_parser import ROMMatcher

        matcher = ROMMatcher(dat_file)  # type: ignore[arg-type]  # DATFile from legacy module
        # Try MD5-based match first
        md5 = md5_cache.get(path)
        if md5:
            result = matcher.match_by_hash(path, md5=md5)
            if result is not None and getattr(result, "dat_game", None) is not None:
                return str(result.dat_game.name)  # type: ignore[union-attr]
        # Fallback: match by filename
        result = matcher.match_file(path)
        if result is not None and getattr(result, "dat_game", None) is not None:
            return str(result.dat_game.name)  # type: ignore[union-attr]
        return None
    except Exception as exc:
        logger.debug("_dat_name_for(%s): %s", path, exc)
        return None


# ---------------------------------------------------------------------------
# CatalogBuilder
# ---------------------------------------------------------------------------


class CatalogBuilder:
    """Scans a source directory and builds a typed ``Catalog``.

    Usage::

        builder = CatalogBuilder(
            platform=PlatformId("psx"),
            source_dir=Path("/roms/psx"),
            knowledge_base=kb,
        )
        catalog = builder.build()

    Args:
        platform: Platform identifier (e.g. ``"psx"``).
        source_dir: Directory containing the source ROM files (ZIPs or raw).
        knowledge_base: Read-only metadata facade.  Used to enrich GameUnits
            with rating / tier / generation fields.
        dat_file: Optional parsed DAT file for canonical name resolution.
        md5_cache: Pre-populated {Path → md5} map (e.g. from the ActionCache
            or the metadata DB).  Avoids re-hashing known files.
        file_digest_cache: Optional ``FileDigestCache`` instance.  When
            provided, ``(size, mtime_ns, inode)`` triples are checked before
            computing MD5s.  Unchanged files are served from cache; newly
            computed values are stored back.  ``None`` disables the cache.
        max_workers: Thread pool size for parallel MD5 computation.
        extensions: File extensions to scan.  Defaults to a broad ROM set.
    """

    _DEFAULT_EXTENSIONS: frozenset[str] = frozenset(
        {
            ".zip",
            ".7z",
            ".iso",
            ".bin",
            ".cue",
            ".img",
            ".chd",
            ".rvz",
            ".wbfs",
            ".gcm",
            ".xiso",
            ".wux",
            ".nes",
            ".sfc",
            ".smc",
            ".gb",
            ".gbc",
            ".gba",
            ".nds",
            ".3ds",
            ".nsp",
            ".xci",
            ".rom",
            ".a26",
            ".a52",
            ".lnx",
        }
    )

    def __init__(
        self,
        platform: PlatformId,
        source_dir: Path,
        knowledge_base: KnowledgeBase,
        dat_file: object | None = None,
        md5_cache: dict[Path, str] | None = None,
        file_digest_cache: FileDigestCache | None = None,
        max_workers: int = 4,
        extensions: frozenset[str] | None = None,
    ) -> None:
        self._platform = platform
        self._source_dir = source_dir
        self._kb = knowledge_base
        self._dat_file = dat_file
        self._md5_cache: dict[Path, str] = dict(md5_cache or {})
        self._file_digest_cache = file_digest_cache
        self._max_workers = max_workers
        self._extensions = extensions or self._DEFAULT_EXTENSIONS

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def build(self) -> Catalog:
        """Scan the source directory and return an immutable ``Catalog``."""
        source_files = self._discover_files()
        if not source_files:
            logger.debug(
                "CatalogBuilder(%s): no files found in %s", self._platform, self._source_dir
            )
            return Catalog(platform=self._platform, units=(), warnings=())

        # Ensure MD5s are available for DAT matching
        self._populate_md5s(source_files)

        # Build DiscRef per file
        disc_refs: list[tuple[str, DiscRef]] = []
        for path in source_files:
            canonical = _strip_disc_tag(path.stem)
            disc_idx = _disc_index(path.stem)
            identity = _identity_for(path, self._md5_cache)
            dat_name = _dat_name_for(path, self._md5_cache, self._dat_file)
            source_ref = SourceRef(path=path, platform=self._platform)
            disc_refs.append(
                (
                    canonical,
                    DiscRef(
                        index=disc_idx,
                        source=source_ref,
                        identity=identity,
                        dat_name=dat_name,
                    ),
                )
            )

        # Group into multi-disc sets
        groups: dict[str, list[DiscRef]] = defaultdict(list)
        for canonical, disc_ref in disc_refs:
            groups[canonical].append(disc_ref)

        # Build GameUnits, collect warnings
        units: list[GameUnit] = []
        warnings: list[CatalogWarning] = []

        for canonical, discs in groups.items():
            # Sort by index
            sorted_discs = sorted(discs, key=lambda d: d.index)
            indices = [d.index for d in sorted_discs]

            # Check for non-contiguous indices (quarantine warning)
            if len(indices) > 1:
                expected = list(range(1, len(indices) + 1))
                if indices != expected:
                    warnings.append(
                        CatalogWarning(
                            unit_key=canonical,
                            reason=f"non-contiguous disc set: {indices}",
                        )
                    )

            # Derive metadata from the first disc's filename (stable)
            sample_path = sorted_discs[0].source.path
            regions = _parse_regions(sample_path.stem)
            languages = _parse_languages(sample_path.stem)

            # Enrich from KnowledgeBase
            rating = self._kb.get_rating(str(self._platform), canonical)

            unit = GameUnit(
                unit_id=UnitId(hashlib.sha1(f"{self._platform}:{canonical}".encode()).hexdigest()),
                platform=self._platform,
                canonical_name=canonical,
                discs=tuple(sorted_discs),
                region=regions,
                languages=languages,
                rating=rating,
            )
            units.append(unit)

        logger.info(
            "CatalogBuilder(%s): %d units (%d files, %d warnings)",
            self._platform,
            len(units),
            len(source_files),
            len(warnings),
        )
        return Catalog(
            platform=self._platform,
            units=tuple(units),
            warnings=tuple(warnings),
        )

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _discover_files(self) -> list[Path]:
        """Return sorted list of ROM files in ``source_dir``."""
        if not self._source_dir.exists():
            logger.warning("CatalogBuilder: source_dir does not exist: %s", self._source_dir)
            return []
        files = [
            p
            for p in self._source_dir.iterdir()
            if p.is_file() and p.suffix.lower() in self._extensions
        ]
        return sorted(files)

    def _populate_md5s(self, files: list[Path]) -> None:
        """Fill ``_md5_cache`` for files not already present."""
        missing = [f for f in files if f not in self._md5_cache]
        if not missing:
            return

        # ── Fast-path: check FileDigestCache before hashing ───────────
        scan_start_ns = time.time_ns()
        if self._file_digest_cache is not None:
            still_missing: list[Path] = []
            for path in missing:
                try:
                    stat = path.stat()
                    cached_md5 = self._file_digest_cache.lookup(path, stat, scan_start_ns)
                    if cached_md5 is not None:
                        self._md5_cache[path] = cached_md5
                    else:
                        still_missing.append(path)
                except OSError:
                    still_missing.append(path)
            missing = still_missing
            if not missing:
                logger.debug(
                    "CatalogBuilder: all %d MD5s served from digest cache",
                    len(list(self._md5_cache)),
                )
                return

        logger.debug("CatalogBuilder: computing MD5s for %d files", len(missing))

        def _compute(path: Path) -> tuple[Path, str | None]:
            if path.suffix.lower() == ".zip":
                return path, _md5_from_zip(path)
            try:
                h = hashlib.md5()
                with open(path, "rb") as fh:
                    for chunk in iter(lambda: fh.read(65536), b""):
                        h.update(chunk)
                return path, h.hexdigest()
            except OSError:
                return path, None

        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            futures = {pool.submit(_compute, p): p for p in missing}
            for future in as_completed(futures):
                path, md5 = future.result()
                if md5:
                    self._md5_cache[path] = md5
                    # Store back to digest cache
                    if self._file_digest_cache is not None:
                        try:
                            stat = path.stat()
                            self._file_digest_cache.store(path, stat, md5)
                        except OSError:
                            pass
