"""sample pass — deterministic random subset for test builds.

``romfarmer build run … --test-sample N --seed S`` sets ``manifest.sample_n``
and ``manifest.sample_seed``.  Selection is by ``sorted(unit_id)`` under a
seeded ``random.Random`` so the same (catalog, seed) always yields the same
subset — the plan stays a pure function of (manifest, catalog).

Runs last, after every real selection pass, so the sample is drawn from what
the build would actually have produced.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from romfarmer.ir.catalog import Catalog, PassResult, PassTrace, UnitId

if TYPE_CHECKING:
    from romfarmer.analysis.knowledge import KnowledgeBase
    from romfarmer.ir.manifest import BuildManifest
    from romfarmer.planner.costmodel import CostModel

PASS_NAME = "sample"


def run(
    catalog: Catalog,
    manifest: BuildManifest,
    kb: KnowledgeBase,
    cost_model: CostModel,
) -> PassResult:
    """Keep a seeded random sample of ``manifest.sample_n`` units."""
    n = manifest.sample_n
    if n is None or n >= len(catalog.units):
        return PassResult(catalog=catalog, trace=PassTrace(pass_name=PASS_NAME, removed=()))

    ordered = sorted(catalog.units, key=lambda u: str(u.unit_id))
    rng = random.Random(manifest.sample_seed)
    chosen: set[UnitId] = {u.unit_id for u in rng.sample(ordered, n)}
    removed = tuple(
        (u.unit_id, f"sample: not in --test-sample {n} (seed={manifest.sample_seed})")
        for u in ordered
        if u.unit_id not in chosen
    )
    return PassResult(
        catalog=catalog.keep(chosen),
        trace=PassTrace(pass_name=PASS_NAME, removed=removed),
    )
