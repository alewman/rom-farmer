"""Pool manifest: collection and fast in-memory size estimation.

A pool manifest captures all games from a superset build (min_rating=0.0,
no size cap) so that the optimizer loop can run fast iterations in memory
without touching the disk.

Pool manifests live at::

    output/{build_name}/.pool/{platform}.json

Each manifest is a list of :class:`PoolEntry` dicts serialized with
``dataclasses.asdict``.

Typical lifecycle
-----------------
1. Run a superset build (or use an existing broad build output).
2. Call :func:`collect_pool` to walk the output directory, look up ratings
   from ``romfarmer.db``, and write per-platform JSON manifests.
3. The optimizer loop calls :func:`estimate_build_size` on every iteration —
   pure in-memory, no disk I/O.
4. On convergence, the full orchestrator re-runs with the winning thresholds.
"""

from __future__ import annotations

import dataclasses
import json
import logging
import os
import re
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from .state import BuildReport, PoolEntry

logger = logging.getLogger(__name__)

_DISC_RE = re.compile(r"\s*\(Disc\s*\d+\)|\s*\(Disk\s*\d+\)", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Generation lookup (cached)
# ---------------------------------------------------------------------------


def _build_generation_map() -> Dict[str, str]:
    """Return platform → generation name mapping from CONSOLE_GENERATIONS."""
    try:
        from romfarmer.ai.generation import CONSOLE_GENERATIONS

        mapping: Dict[str, str] = {}
        for gen in CONSOLE_GENERATIONS:
            for platform in gen.platforms:
                # First definition wins (some platforms appear in multiple gens)
                if platform not in mapping:
                    mapping[platform] = gen.name
        return mapping
    except ImportError:
        logger.warning("Could not import CONSOLE_GENERATIONS; generation labels unavailable")
        return {}


_GENERATION_MAP: Optional[Dict[str, str]] = None


def _get_generation(platform: str) -> str:
    global _GENERATION_MAP
    if _GENERATION_MAP is None:
        _GENERATION_MAP = _build_generation_map()
    return _GENERATION_MAP.get(platform, "unknown")


# ---------------------------------------------------------------------------
# Default thresholds by generation
# ---------------------------------------------------------------------------

# Business rules:
#   gen3 / gen4 → floor immediately at 0.0 (tiny files, pack 100%)
#   gen5 / gen5_handheld → start 0.8, loosen in 0.05 steps
#   gen6 / gen6_handheld → start 0.9, tighten aggressively on overshoot
#   gen7 / gen7_handheld → start 0.9 same as gen6
#   others (arcade, portable, unknown) → 0.0

DEFAULT_THRESHOLDS: Dict[str, float] = {
    "gen3": 0.0,
    "gen4": 0.0,
    "gen5": 0.8,
    "gen5_handheld": 0.8,
    "gen6": 0.9,
    "gen6_handheld": 0.9,
    "gen7": 0.9,
    "gen7_handheld": 0.9,
    "arcade": 0.0,
    "portable": 0.0,
    "unknown": 0.0,
}


# ---------------------------------------------------------------------------
# Rating DB helpers
# ---------------------------------------------------------------------------


def _open_metadata_db(workspace_root: Path) -> Optional[Path]:
    """Locate romfarmer.db under the workspace."""
    candidates = [
        workspace_root / "metadata" / "database" / "romfarmer.db",
        workspace_root / "romfarmer.db",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def _fetch_ratings(db_path: Path, game_names: List[str]) -> Dict[str, float]:
    """Query scraped_games for ratings by base game name (best-effort fuzzy)."""
    if not db_path or not db_path.exists():
        return {}

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    ratings: Dict[str, float] = {}

    for name in game_names:
        try:
            cursor.execute(
                "SELECT rating FROM scraped_games WHERE name LIKE ? OR filename LIKE ? "
                "ORDER BY rating DESC LIMIT 1",
                (f"%{name}%", f"%{name}%"),
            )
            row = cursor.fetchone()
            if row and row[0] is not None:
                ratings[name] = float(row[0])
        except Exception:
            pass

    conn.close()
    return ratings


# ---------------------------------------------------------------------------
# collect_pool
# ---------------------------------------------------------------------------


def collect_pool(
    build_name: str,
    output_base: Path,
    workspace_root: Optional[Path] = None,
) -> Path:
    """Walk a superset build output directory and write pool manifests.

    For each platform directory found under ``output_base / build_name /``,
    enumerate all output files, group them by multi-disc base name, look up
    ratings from ``romfarmer.db``, determine generation, and write a JSON
    manifest to ``output_base / build_name / .pool / {platform}.json``.

    Args:
        build_name: Build name (e.g. "nointro-1g1r-eng-7z-batocera").
        output_base: Base output directory (typically ``output/``).
        workspace_root: Workspace root for locating metadata DB.
                        Defaults to ``output_base.parent``.

    Returns:
        Path to the pool root directory (``output_base / build_name / .pool``).
    """
    if workspace_root is None:
        workspace_root = output_base.parent

    build_output = output_base / build_name
    if not build_output.exists():
        raise FileNotFoundError(f"Build output not found: {build_output}")

    pool_root = build_output / ".pool"
    pool_root.mkdir(parents=True, exist_ok=True)

    db_path = _open_metadata_db(workspace_root)
    if db_path is None:
        logger.warning("romfarmer.db not found; all ratings will be 0.0")

    generation_map = _build_generation_map()
    manifests_written = 0

    for platform_dir in sorted(build_output.iterdir()):
        if platform_dir.name.startswith(".") or not platform_dir.is_dir():
            continue

        platform = platform_dir.name
        generation = generation_map.get(platform, "unknown")
        entries = _collect_platform_entries(platform_dir, platform, generation, db_path)

        manifest_path = pool_root / f"{platform}.json"
        _write_manifest(manifest_path, entries)
        logger.info(f"  Pool manifest: {platform} → {len(entries)} games")
        manifests_written += 1

    logger.info(f"Collected pool: {manifests_written} platforms → {pool_root}")
    return pool_root


def _collect_platform_entries(
    platform_dir: Path,
    platform: str,
    generation: str,
    db_path: Optional[Path],
) -> List[PoolEntry]:
    """Enumerate files in a platform output directory → list of PoolEntry."""
    # Group files by base game name (strip disc suffix)
    groups: Dict[str, List[Path]] = {}
    for root, _dirs, files in os.walk(platform_dir):
        for fname in files:
            if fname.startswith("."):
                continue
            fpath = Path(root) / fname
            stem = fpath.stem
            base = _DISC_RE.sub("", stem).strip()
            groups.setdefault(base, []).append(fpath)

    if not groups:
        return []

    # Fetch ratings in one batch
    ratings = _fetch_ratings(db_path, list(groups.keys())) if db_path else {}

    entries: List[PoolEntry] = []
    for base_name, disc_files in sorted(groups.items()):
        total_size = sum(f.stat().st_size for f in disc_files if f.exists())
        rating = ratings.get(base_name, 0.0)
        is_multi = len(disc_files) > 1
        entries.append(
            PoolEntry(
                name=base_name,
                rating=rating,
                generation=generation,
                size_bytes=total_size,
                multi_disc_group=base_name if is_multi else None,
                is_disc_anchor=True,
                platform=platform,
            )
        )
    return entries


def _write_manifest(path: Path, entries: List[PoolEntry]) -> None:
    payload = [dataclasses.asdict(e) for e in entries]
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)


# ---------------------------------------------------------------------------
# load_pool
# ---------------------------------------------------------------------------


def load_pool(pool_root: Path) -> Dict[str, List[PoolEntry]]:
    """Load all per-platform pool manifests from ``pool_root``.

    Returns:
        Mapping of platform name → list of PoolEntry objects.
    """
    result: Dict[str, List[PoolEntry]] = {}
    if not pool_root.exists():
        return result

    for manifest_path in sorted(pool_root.glob("*.json")):
        platform = manifest_path.stem
        try:
            with open(manifest_path) as f:
                raw = json.load(f)
            result[platform] = [PoolEntry(**entry) for entry in raw]
        except Exception as e:
            logger.warning(f"Failed to load pool manifest {manifest_path}: {e}")

    return result


# ---------------------------------------------------------------------------
# estimate_build_size  (the hot loop path)
# ---------------------------------------------------------------------------


def estimate_build_size(
    pool: Dict[str, List[PoolEntry]],
    thresholds: Dict[str, float],
    platform_overrides: Optional[Dict[str, float]] = None,
) -> BuildReport:
    """Apply thresholds to the pool and return an estimated BuildReport.

    This is pure in-memory — no disk I/O.  O(N) in total game count.

    Args:
        pool: Platform → entries, from :func:`load_pool`.
        thresholds: Generation name → min_rating.  Unknown generations
                    default to 0.0.
        platform_overrides: Optional per-platform min_rating that takes
                            precedence over the generation threshold.

    Returns:
        :class:`BuildReport` with ``is_estimated=True``.
    """
    overrides = platform_overrides or {}

    total_bytes = 0
    per_platform: Dict[str, int] = {}
    per_gen_bytes: Dict[str, int] = {}
    per_gen_count: Dict[str, int] = {}
    per_platform_count: Dict[str, int] = {}
    multi_disc_groups = 0
    total_games = 0

    for platform, entries in pool.items():
        platform_bytes = 0
        platform_count = 0

        for entry in entries:
            threshold = overrides.get(platform, thresholds.get(entry.generation, 0.0))
            if entry.rating >= threshold:
                platform_bytes += entry.size_bytes
                platform_count += 1
                per_gen_bytes[entry.generation] = (
                    per_gen_bytes.get(entry.generation, 0) + entry.size_bytes
                )
                per_gen_count[entry.generation] = (
                    per_gen_count.get(entry.generation, 0) + 1
                )
                if entry.multi_disc_group is not None:
                    multi_disc_groups += 1

        per_platform[platform] = platform_bytes
        per_platform_count[platform] = platform_count
        total_bytes += platform_bytes
        total_games += platform_count

    return BuildReport(
        total_size_bytes=total_bytes,
        per_platform_sizes=per_platform,
        per_generation_sizes=per_gen_bytes,
        per_generation_game_counts=per_gen_count,
        per_platform_game_counts=per_platform_count,
        multi_disc_groups_included=multi_disc_groups,
        total_game_count=total_games,
        is_estimated=True,
    )
