"""budget pass — size-based selection.

Selects the highest-rated games that fit within
``manifest.effective_budget_bytes``.

Algorithm (mirrors ``SelectionFilter.RATING_BUDGET`` strategy):
1. Sort units by rating descending, then by ``canonical_name`` asc for stability.
   Units with ``rating=None`` sort below rated units.
2. Greedily accumulate units until adding the next unit would exceed the budget.
   Multi-disc sets are atomic (all-or-nothing: ``GameUnit.source_size`` sums all
   discs).
3. Units beyond the budget are removed with a reason that includes predicted
   cumulative size.

If ``manifest.effective_budget_bytes`` is ``None``, this pass is a no-op.

The pass uses ``CostModel.predict_output_bytes`` for size estimation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from romfarmer.ir.catalog import Catalog, GameUnit, PassResult, PassTrace, UnitId

if TYPE_CHECKING:
    from romfarmer.analysis.knowledge import KnowledgeBase
    from romfarmer.ir.manifest import BuildManifest
    from romfarmer.planner.costmodel import CostModel

PASS_NAME = "budget"


def _sort_key(unit: GameUnit) -> tuple[float, str]:
    """Rating desc (None → -inf), then name asc."""
    r = unit.rating if unit.rating is not None else float("-inf")
    return (-r, unit.canonical_name)


def run(
    catalog: Catalog,
    manifest: "BuildManifest",
    kb: "KnowledgeBase",
    cost_model: "CostModel",
) -> PassResult:
    """Greedily keep top-rated units within budget."""
    budget = manifest.effective_budget_bytes
    if budget is None:
        return PassResult(
            catalog=catalog,
            trace=PassTrace(pass_name=PASS_NAME, removed=(), added=()),
        )

    platform = str(catalog.platform or manifest.platform or "")

    sorted_units = sorted(catalog.units, key=_sort_key)
    accumulated = 0
    keep_ids: set[UnitId] = set()
    removed: list[tuple[UnitId, str]] = []

    for unit in sorted_units:
        source_bytes = unit.source_size
        try:
            predicted, label = cost_model.predict_output_bytes(
                source_bytes, platform
            )
        except Exception:
            # Unknown platform / no cost model data — use source size as pessimistic estimate
            predicted = source_bytes
            label = "fallback:source_size"

        if accumulated + predicted <= budget:
            keep_ids.add(unit.unit_id)
            accumulated += predicted
        else:
            removed.append((
                unit.unit_id,
                f"budget: adding {predicted:,} bytes (cumulative {accumulated:,}) "
                f"would exceed {budget:,} [{label}]",
            ))

    new_catalog = catalog.keep(keep_ids)
    return PassResult(
        catalog=new_catalog,
        trace=PassTrace(
            pass_name=PASS_NAME,
            removed=tuple(removed),
            added=(),
        ),
    )
