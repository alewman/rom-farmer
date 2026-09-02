"""dat_dedup pass — one source file per DAT entry.

When multiple source files matched the same DAT entry name (e.g. both the
original and a RE edition matched the same DAT game), we keep only the best
one.  Best = highest difflib similarity between ``path.stem`` and ``dat_name``
(exact match wins outright).

Units without a ``dat_name`` on any disc are passed through unchanged.
"""

from __future__ import annotations

import difflib
from collections import defaultdict
from typing import TYPE_CHECKING

from romfarmer.ir.catalog import Catalog, DiscRef, GameUnit, PassResult, PassTrace, UnitId

if TYPE_CHECKING:
    from romfarmer.analysis.knowledge import KnowledgeBase
    from romfarmer.ir.manifest import BuildManifest
    from romfarmer.planner.costmodel import CostModel

PASS_NAME = "dat_dedup"


def _similarity(stem: str, dat_name: str) -> float:
    if stem == dat_name:
        return 1.0
    return difflib.SequenceMatcher(None, stem.lower(), dat_name.lower()).ratio()


def run(
    catalog: Catalog,
    manifest: BuildManifest,
    kb: KnowledgeBase,
    cost_model: CostModel,
) -> PassResult:
    """Keep the best-matching unit per DAT entry name; pass through unmatched."""
    # Group units by their primary dat_name (from disc 0 / first disc with a name)
    by_dat: dict[str, list[GameUnit]] = defaultdict(list)
    no_dat: list[GameUnit] = []

    for unit in catalog.units:
        dat_name = _primary_dat_name(unit.discs)
        if dat_name is None:
            no_dat.append(unit)
        else:
            by_dat[dat_name].append(unit)

    removed: list[tuple[UnitId, str]] = []
    keep_ids: set[UnitId] = {u.unit_id for u in no_dat}

    for dat_name, units in by_dat.items():
        if len(units) == 1:
            keep_ids.add(units[0].unit_id)
            continue
        # Pick the best match
        best = max(
            units,
            key=lambda u: _similarity(u.canonical_name, dat_name),
        )
        keep_ids.add(best.unit_id)
        for unit in units:
            if unit.unit_id != best.unit_id:
                removed.append(
                    (
                        unit.unit_id,
                        f"dat_dedup: worse match for DAT entry '{dat_name}' "
                        f"(kept '{best.canonical_name}')",
                    )
                )

    new_catalog = catalog.keep(keep_ids)
    return PassResult(
        catalog=new_catalog,
        trace=PassTrace(
            pass_name=PASS_NAME,
            removed=tuple(removed),
            added=(),
        ),
    )


def _primary_dat_name(discs: tuple[DiscRef, ...]) -> str | None:
    """Return the dat_name from the first disc that has one."""
    for disc in discs:
        if disc.dat_name is not None:
            return disc.dat_name
    return None
