"""rating pass — filter by scraped/external rating.

Three sub-modes (all use ``GameUnit.rating``, populated by ``CatalogBuilder``
from the ``KnowledgeBase``):

- ``manifest.rating_min``: remove units whose rating < threshold (unit
  interval, 0.0–1.0).  Units with ``rating=None`` are *kept* unless
  ``manifest.rating_unrated == "drop"``.
- ``manifest.rating_top_n``: keep only the top-N rated units (ties broken
  by ``canonical_name`` asc for determinism).  Units with ``rating=None``
  sort below rated units.
- Both together: apply ``rating_min`` first, then ``rating_top_n``.

If neither is set, the pass is a no-op.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from romfarmer.ir.catalog import Catalog, GameUnit, PassResult, PassTrace, UnitId

if TYPE_CHECKING:
    from romfarmer.analysis.knowledge import KnowledgeBase
    from romfarmer.ir.manifest import BuildManifest
    from romfarmer.planner.costmodel import CostModel

PASS_NAME = "rating"


def _rating_sort_key(unit: GameUnit) -> tuple[float, str]:
    """(rating desc, name asc) — None ratings sort below 0.0."""
    return (-(unit.rating if unit.rating is not None else -1.0), unit.canonical_name)


def run(
    catalog: Catalog,
    manifest: BuildManifest,
    kb: KnowledgeBase,
    cost_model: CostModel,
) -> PassResult:
    """Apply rating-min and/or top-N filtering."""
    if manifest.rating_min is None and manifest.rating_top_n is None:
        return PassResult(
            catalog=catalog,
            trace=PassTrace(pass_name=PASS_NAME, removed=(), added=()),
        )

    removed: list[tuple[UnitId, str]] = []
    survivors: list[GameUnit] = list(catalog.units)

    # 1. Minimum threshold
    if manifest.rating_min is not None:
        threshold = manifest.rating_min
        next_survivors: list[GameUnit] = []
        drop_unrated = manifest.rating_unrated == "drop"
        for unit in survivors:
            if unit.rating is None:
                if drop_unrated:
                    removed.append(
                        (unit.unit_id, f"rating: unrated (unrated=drop, min {threshold:.2f})")
                    )
                else:
                    next_survivors.append(unit)
            elif unit.rating < threshold:
                removed.append(
                    (
                        unit.unit_id,
                        f"rating {unit.rating:.2f} < min {threshold:.2f}",
                    )
                )
            else:
                next_survivors.append(unit)
        survivors = next_survivors

    # 2. Top-N cap
    if manifest.rating_top_n is not None:
        n = manifest.rating_top_n
        sorted_survivors = sorted(survivors, key=_rating_sort_key)
        kept = sorted_survivors[:n]
        cut = sorted_survivors[n:]
        for unit in cut:
            removed.append(
                (
                    unit.unit_id,
                    f"rating top-{n} cap (rating={unit.rating})",
                )
            )
        survivors = kept

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
