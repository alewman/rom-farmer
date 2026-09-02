"""romfarmer.planner.passes — pure planner passes.

Each pass has the signature::

    run(
        catalog: Catalog,
        manifest: BuildManifest,
        kb: KnowledgeBase,
        cost_model: CostModel,
    ) -> PassResult

All passes are **pure**: no filesystem access, no symlinks, no database writes.
They receive all inputs as arguments and return a new ``Catalog`` + a
``PassTrace`` (the audit log that powers ``romfarmer plan --explain``).
"""

from .arcade import run as arcade
from .budget import run as budget
from .curated_lists import run as curated_lists
from .dat_dedup import run as dat_dedup
from .dat_filter import run as dat_filter
from .generation import run as generation
from .one_g_one_r import run as one_g_one_r
from .rating import run as rating
from .region import run as region
from .sample import run as sample

# Canonical order for a single-platform build.  The orchestrator and the
# `plan` CLI both use this so `plan --explain` predicts exactly what `build`
# does.  `generation` is cross-platform and is run by the driver separately.
DEFAULT_PASSES = [
    region,
    dat_filter,
    dat_dedup,
    one_g_one_r,
    arcade,
    rating,
    curated_lists,
    budget,
    sample,
]

__all__ = [
    "DEFAULT_PASSES",
    "region",
    "dat_filter",
    "dat_dedup",
    "one_g_one_r",
    "arcade",
    "rating",
    "curated_lists",
    "generation",
    "budget",
    "sample",
]
