"""generation pass — 1G1Gen cross-platform deduplication.

Implements "1 Game 1 Generation": when a game exists on multiple platforms
within the same console generation, keep only the version from the
highest-priority platform.

Input: a *merged* ``Catalog`` spanning all platforms in the generation
       (``catalog.platform`` is ``None``).

Algorithm:
1. Normalize all canonical names via ``_norm_key`` (lowercase, strip
   punctuation) to build a cross-platform match key.
2. For each match key that appears on multiple platforms, keep the version
   from the highest-priority platform (index 0 in
   ``manifest.generation_platform_order``).
3. Lower-priority duplicates are removed with a human-readable reason that
   names both the kept and removed platform.

If ``manifest.generation_name`` is ``None`` or
``manifest.generation_platform_order`` has fewer than 2 entries, this pass
is a no-op.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import TYPE_CHECKING

from romfarmer.ir.catalog import Catalog, GameUnit, PassResult, PassTrace, UnitId

if TYPE_CHECKING:
    from romfarmer.analysis.knowledge import KnowledgeBase
    from romfarmer.ir.manifest import BuildManifest
    from romfarmer.planner.costmodel import CostModel

PASS_NAME = "generation"

_NON_ALNUM = re.compile(r"[^a-z0-9 ]+")


def _norm_key(name: str) -> str:
    """Lowercase + strip non-alphanumeric (except space) for cross-platform matching."""
    return _NON_ALNUM.sub("", name.lower()).strip()


def run(
    catalog: Catalog,
    manifest: "BuildManifest",
    kb: "KnowledgeBase",
    cost_model: "CostModel",
) -> PassResult:
    """Remove cross-platform duplicates based on platform priority."""
    if (
        manifest.generation_name is None
        or len(manifest.generation_platform_order) < 2
    ):
        return PassResult(
            catalog=catalog,
            trace=PassTrace(pass_name=PASS_NAME, removed=(), added=()),
        )

    priority_order = manifest.generation_platform_order  # index 0 = highest
    priority_map: dict[str, int] = {p: i for i, p in enumerate(priority_order)}

    # Group units by normalised match key + platform
    # match_key → {platform → list[GameUnit]}
    by_key: dict[str, dict[str, list[GameUnit]]] = defaultdict(lambda: defaultdict(list))
    for unit in catalog.units:
        plat = str(unit.platform)
        if plat not in priority_map:
            # Platform not part of this generation — skip
            continue
        key = _norm_key(unit.canonical_name)
        by_key[key][plat].append(unit)

    removed: list[tuple[UnitId, str]] = []

    for match_key, platforms in by_key.items():
        if len(platforms) <= 1:
            continue  # No cross-platform duplicate

        # Find the highest-priority platform present
        best_plat = min(platforms.keys(), key=lambda p: priority_map.get(p, 9999))

        for plat, units in platforms.items():
            if plat == best_plat:
                continue
            for unit in units:
                removed.append((
                    unit.unit_id,
                    f"generation {manifest.generation_name}: "
                    f"'{unit.canonical_name}' on {plat!r} "
                    f"superseded by {best_plat!r}",
                ))

    removed_ids = {uid for uid, _ in removed}
    new_catalog = catalog.without(removed_ids)
    return PassResult(
        catalog=new_catalog,
        trace=PassTrace(
            pass_name=PASS_NAME,
            removed=tuple(removed),
            added=(),
        ),
    )
