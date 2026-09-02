"""curated_lists pass — apply include / exclude lists.

``manifest.curated_exclude``: set of canonical game names to always remove.
``manifest.curated_include``: set of canonical game names to always keep
    (rescue list — overrides any previous pass's removal).

The pass runs in two steps:
1. Remove all units in ``curated_exclude`` (exact canonical_name match).
2. Re-add (restore) units whose ``canonical_name`` is in ``curated_include``
   that were somehow already removed — **but** the in-memory Catalog only
   contains surviving units, so this pass can only protect units that are
   *still present*.  Units not in the current catalog are silently ignored
   (they may have been removed by a prior pass for a good reason, or never
   existed in the source).

The ``added`` field of ``PassTrace`` records any units that were *prevented*
from being removed (i.e., units in ``curated_include`` that were also in
``curated_exclude`` — the include list wins).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from romfarmer.ir.catalog import Catalog, PassResult, PassTrace, UnitId

if TYPE_CHECKING:
    from romfarmer.analysis.knowledge import KnowledgeBase
    from romfarmer.ir.manifest import BuildManifest
    from romfarmer.planner.costmodel import CostModel

PASS_NAME = "curated_lists"


def run(
    catalog: Catalog,
    manifest: BuildManifest,
    kb: KnowledgeBase,
    cost_model: CostModel,
) -> PassResult:
    """Apply curated include/exclude lists."""
    if not manifest.curated_exclude and not manifest.curated_include:
        return PassResult(
            catalog=catalog,
            trace=PassTrace(pass_name=PASS_NAME, removed=(), added=()),
        )

    removed: list[tuple[UnitId, str]] = []
    rescued: list[tuple[UnitId, str]] = []

    for unit in catalog.units:
        name = unit.canonical_name
        in_exclude = name in manifest.curated_exclude
        in_include = name in manifest.curated_include

        if in_exclude and not in_include:
            removed.append((unit.unit_id, f"curated_exclude: {name!r}"))
        elif in_exclude and in_include:
            # include wins — note it as rescued/added
            rescued.append((unit.unit_id, f"curated_include rescued {name!r} from exclude list"))

    removed_ids = {uid for uid, _ in removed}
    new_catalog = catalog.without(removed_ids)
    return PassResult(
        catalog=new_catalog,
        trace=PassTrace(
            pass_name=PASS_NAME,
            removed=tuple(removed),
            added=tuple(rescued),
        ),
    )
