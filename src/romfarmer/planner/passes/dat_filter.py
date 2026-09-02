"""dat_filter pass — keep only units that matched an entry in the platform DAT.

The DAT (typically a Retool 1G1R export) *defines* the collection: anything
in the source directory that did not match a DAT entry — pirates, unlicensed
dumps, regions the DAT excluded, stray files — is dropped here.  This is the
semantic the legacy ``FilterDATStage`` provided and the compiler initially
lost; without it a "1G1R English" build emitted every file in the source.

Gated by ``manifest.dat_filter``.  When the platform has no DAT (digital
stores, arcade sets driven by their own metadata) the manifest leaves it
``False`` and this pass is a no-op.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from romfarmer.ir.catalog import Catalog, PassResult, PassTrace, UnitId

if TYPE_CHECKING:
    from romfarmer.analysis.knowledge import KnowledgeBase
    from romfarmer.ir.manifest import BuildManifest
    from romfarmer.planner.costmodel import CostModel

PASS_NAME = "dat_filter"


def run(
    catalog: Catalog,
    manifest: BuildManifest,
    kb: KnowledgeBase,
    cost_model: CostModel,
) -> PassResult:
    """Remove units with no DAT match on any disc."""
    if not manifest.dat_filter:
        return PassResult(catalog=catalog, trace=PassTrace(pass_name=PASS_NAME, removed=()))

    keep: set[UnitId] = set()
    removed: list[tuple[UnitId, str]] = []
    for unit in catalog.units:
        if any(d.dat_name is not None for d in unit.discs):
            keep.add(unit.unit_id)
        else:
            removed.append((unit.unit_id, "dat_filter: no DAT entry matched this file"))

    return PassResult(
        catalog=catalog.keep(keep),
        trace=PassTrace(pass_name=PASS_NAME, removed=tuple(removed)),
    )
