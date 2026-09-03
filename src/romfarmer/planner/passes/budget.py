"""budget pass — size-based selection.

Selects the highest-rated games that fit within
``manifest.effective_budget_bytes``.

Algorithm (mirrors ``SelectionFilter.RATING_BUDGET`` strategy):
1. Sort units by rating descending, then by ``canonical_name`` asc for stability.
   Units with ``rating=None`` are ranked per ``manifest.budget_unrated_as``
   (default: the per-platform median of rated units).
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


def _rank(unit: GameUnit, unrated_rank: float) -> float:
    return unit.rating if unit.rating is not None else unrated_rank


def _median(values: list[float]) -> float:
    vs = sorted(values)
    n = len(vs)
    return vs[n // 2] if n % 2 else (vs[n // 2 - 1] + vs[n // 2]) / 2.0


def run(
    catalog: Catalog,
    manifest: BuildManifest,
    kb: KnowledgeBase,
    cost_model: CostModel,
) -> PassResult:
    """Greedily keep top-rated units within budget.

    Unrated units are ranked per ``manifest.budget_unrated_as``: ``"median"``
    (default) places them at the per-platform median of the rated units in the
    catalog entering this pass, so trimming removes genuinely low-rated
    content first and unrated content only when the budget reaches the middle.
    ``"worst"`` reproduces the old ``-inf`` behaviour.  The median used is
    recorded in ``PassTrace.notes``.

    The surviving catalog is returned in selection order (rating descending)
    so the executor's stop-early guard trims from the bottom, not
    alphabetically.
    """
    budget = manifest.effective_budget_bytes
    if budget is None:
        return PassResult(
            catalog=catalog,
            trace=PassTrace(pass_name=PASS_NAME, removed=(), added=()),
        )

    platform = str(catalog.platform or manifest.platform or "")
    tool = manifest.chain[0] if manifest.chain else None

    unrated_rank = manifest.unrated_rank()
    notes: list[str] = []
    if unrated_rank is None:
        rated = [u.rating for u in catalog.units if u.rating is not None]
        unrated_rank = _median(rated) if rated else 0.0
        notes.append(
            f"unrated_as=median → {unrated_rank:.3f} (n_rated={len(rated)}/{len(catalog.units)})"
        )
    else:
        notes.append(f"unrated_as={manifest.budget_unrated_as}")

    sorted_units = sorted(catalog.units, key=lambda u: (-_rank(u, unrated_rank), u.canonical_name))
    accumulated = 0
    kept: list[GameUnit] = []
    removed: list[tuple[UnitId, str]] = []
    labels: set[str] = set()

    for unit in sorted_units:
        source_bytes = unit.source_size
        try:
            predicted, label = cost_model.predict_output_bytes(source_bytes, platform, tool)
        except Exception:
            # No prior at all — use source size as a pessimistic estimate
            predicted = source_bytes
            label = "fallback:source_size"
        labels.add(label)

        if accumulated + predicted <= budget:
            kept.append(unit)
            accumulated += predicted
        else:
            removed.append(
                (
                    unit.unit_id,
                    f"budget: adding {predicted:,} bytes (cumulative {accumulated:,}) "
                    f"would exceed {budget:,} [{label}]",
                )
            )

    notes.append(
        f"predicted_bytes={accumulated} budget={budget} tool={tool} [{', '.join(sorted(labels))}]"
    )
    new_catalog = Catalog(platform=catalog.platform, units=tuple(kept), warnings=catalog.warnings)
    return PassResult(
        catalog=new_catalog,
        trace=PassTrace(
            pass_name=PASS_NAME,
            removed=tuple(removed),
            added=(),
            notes=tuple(notes),
        ),
    )
