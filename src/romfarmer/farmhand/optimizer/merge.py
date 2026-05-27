"""Pool merge utility — combine pool manifests from multiple builds.

When a full deployment spans multiple builds (e.g., nointro + redump +
nintendo-disc), the optimizer needs a single combined pool so it can reason
about total size across all content. This module merges per-build pools into
one directory the optimizer can consume via ``--pool-root``.

If the same platform appears in more than one source (unusual, but possible
if you accidentally include overlapping builds), entries are merged by game
name — the first source wins for duplicate names.
"""

from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .pool import _write_manifest, load_pool
from .state import PoolEntry

logger = logging.getLogger(__name__)


@dataclass
class MergeResult:
    """Summary of a pool merge operation."""

    output_root: Path
    platforms_merged: int
    platforms_total: int
    games_total: int
    conflicts_resolved: int  # platforms that appeared in >1 source
    source_breakdown: Dict[str, List[str]]  # source_build → [platform, ...]


def merge_pools(
    sources: List[Path],
    output: Path,
    *,
    overwrite: bool = True,
) -> MergeResult:
    """Merge pool manifests from multiple source directories into *output*.

    Args:
        sources: Paths to ``.pool`` directories (each produced by
                 ``collect_pool`` or ``farmhand collect-pool``).
        output: Destination directory for the merged pool.  Will be created
                if it does not exist.  If it already contains manifests and
                *overwrite* is True (default), they are replaced.
        overwrite: When True, existing manifests in *output* are replaced by
                   fresher data from the sources.  When False, existing
                   manifests are preserved and only new platforms are added.

    Returns:
        :class:`MergeResult` with stats.
    """
    output.mkdir(parents=True, exist_ok=True)

    # Track which source each platform came from (for conflict reporting)
    seen: Dict[str, str] = {}  # platform → first source label
    conflicts_resolved = 0
    source_breakdown: Dict[str, List[str]] = {}
    games_total = 0

    for source_dir in sources:
        if not source_dir.exists():
            logger.warning(f"Pool source not found, skipping: {source_dir}")
            continue

        source_label = source_dir.parent.name  # e.g. "nointro-1g1r-eng-7z-batocera-v2"
        source_breakdown[source_label] = []

        manifests = sorted(source_dir.glob("*.json"))
        if not manifests:
            logger.warning(f"No manifests found in {source_dir}")
            continue

        for manifest_path in manifests:
            platform = manifest_path.stem
            dest_path = output / manifest_path.name

            if platform in seen:
                conflicts_resolved += 1
                logger.info(
                    f"  Platform '{platform}' from '{source_label}' conflicts with "
                    f"'{seen[platform]}' — merging entries"
                )
                # Merge: load both, combine by name (first seen wins for dupes)
                existing = _load_raw_entries(dest_path)
                incoming = _load_raw_entries(manifest_path)
                merged = _merge_entries(existing, incoming)
                _write_raw_entries(dest_path, merged)
                games_total += len(merged)
            else:
                # First time we see this platform
                if not dest_path.exists() or overwrite:
                    shutil.copy2(manifest_path, dest_path)
                    entries = _load_raw_entries(dest_path)
                    games_total += len(entries)
                else:
                    # overwrite=False and file already exists — preserve
                    entries = _load_raw_entries(dest_path)
                    games_total += len(entries)
                    logger.debug(f"  Preserving existing manifest for '{platform}'")

                seen[platform] = source_label
                source_breakdown[source_label].append(platform)

        logger.info(
            f"  Source '{source_label}': "
            f"{len(source_breakdown[source_label])} platforms"
        )

    result = MergeResult(
        output_root=output,
        platforms_merged=len(seen),
        platforms_total=sum(len(v) for v in source_breakdown.values()),
        games_total=games_total,
        conflicts_resolved=conflicts_resolved,
        source_breakdown=source_breakdown,
    )

    logger.info(
        f"Merge complete: {result.platforms_merged} platforms, "
        f"{result.games_total} games → {output}"
    )
    return result


def merge_pools_from_builds(
    build_names: List[str],
    output: Path,
    output_base: Optional[Path] = None,
    *,
    overwrite: bool = True,
) -> MergeResult:
    """Convenience wrapper: merge pools from named builds under *output_base*.

    Looks for pools at ``output_base / build_name / .pool`` for each name.

    Args:
        build_names: Build names whose pools should be merged.
        output: Destination directory.
        output_base: Root of all build outputs.  Defaults to ``output/``
                     relative to the workspace root (resolved via
                     :func:`romfarmer.core.paths.get_paths`).
        overwrite: Passed through to :func:`merge_pools`.
    """
    if output_base is None:
        from romfarmer.core.paths import get_paths

        output_base = get_paths().workspace_root / "output"

    sources: List[Path] = []
    for name in build_names:
        pool_dir = output_base / name / ".pool"
        if pool_dir.exists():
            sources.append(pool_dir)
        else:
            logger.warning(
                f"No pool found for build '{name}' at {pool_dir}. "
                "Run 'farmhand collect-pool' first."
            )

    if not sources:
        raise FileNotFoundError(
            f"No pool manifests found for any of the specified builds: "
            f"{', '.join(build_names)}\n"
            "Run 'romfarmer farmhand collect-pool <build-name>' for each build first."
        )

    return merge_pools(sources, output, overwrite=overwrite)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_raw_entries(path: Path) -> List[dict]:
    """Load a manifest as a list of raw dicts."""
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load manifest {path}: {e}")
        return []


def _write_raw_entries(path: Path, entries: List[dict]) -> None:
    """Write a list of raw dicts to a manifest file."""
    with open(path, "w") as f:
        json.dump(entries, f, indent=2)


def _merge_entries(existing: List[dict], incoming: List[dict]) -> List[dict]:
    """Merge two lists of pool entries, deduplicating by game name.

    The existing list takes precedence for duplicate names (first-seen wins).
    New entries from *incoming* that aren't in *existing* are appended.
    """
    names_seen = {e["name"] for e in existing}
    merged = list(existing)
    for entry in incoming:
        if entry["name"] not in names_seen:
            merged.append(entry)
            names_seen.add(entry["name"])
    return merged
