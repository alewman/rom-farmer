"""region pass — filter to preferred regions only.

Removes units whose ``region`` set has no overlap with
``manifest.preferred_regions``.  Units with an empty region set are kept
(region unknown — do not discard by default).

If ``manifest.preferred_regions`` is empty the pass is a no-op.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from romfarmer.ir.catalog import Catalog, PassResult, PassTrace, UnitId

if TYPE_CHECKING:
    from romfarmer.analysis.knowledge import KnowledgeBase
    from romfarmer.ir.manifest import BuildManifest
    from romfarmer.planner.costmodel import CostModel

PASS_NAME = "region"


def run(
    catalog: Catalog,
    manifest: "BuildManifest",
    kb: "KnowledgeBase",
    cost_model: "CostModel",
) -> PassResult:
    """Remove units whose region is not in ``manifest.preferred_regions``."""
    if not manifest.preferred_regions:
        return PassResult(
            catalog=catalog,
            trace=PassTrace(pass_name=PASS_NAME, removed=(), added=()),
        )

    preferred = frozenset(manifest.preferred_regions)
    removed: list[tuple[UnitId, str]] = []

    for unit in catalog.units:
        if unit.region and not (unit.region & preferred):
            removed.append((
                unit.unit_id,
                f"region {sorted(unit.region)} not in preferred {sorted(preferred)}",
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
