"""Budget optimizer — iterative LangGraph loop for fitting ROM builds to a storage target.

The optimizer accepts a superset pool manifest (all games passing DAT/region/language
filters) and a storage target with headroom tolerance.  It runs a tight
evaluator-optimizer loop — using an LLM critic to adjust per-generation rating
thresholds — until the estimated build size sits inside the window
``[target_total - target_free - tolerance, target_total - target_free + tolerance]``.

All iteration work is pure in-memory estimation against the pool manifest
(zero disk I/O).  Only the final converged thresholds are handed to the
full orchestrator to produce the actual staged build.

Typical usage::

    from romfarmer.farmhand.optimizer import run_optimizer, collect_pool

    # 1. (once) collect pool manifest from an existing superset build output
    collect_pool(build_name="nointro-1g1r-eng", output_base=Path("output"))

    # 2. run the optimizer loop
    result = run_optimizer(
        build_name="nointro-1g1r-eng",
        target_total_bytes=2_000_000_000_000,  # 1.9 TB
        target_free_bytes=30 * 1024**3,
        tolerance_bytes=5 * 1024**3,
        max_iterations=8,
    )
    print(result.verdict, result.final_thresholds)
"""

from __future__ import annotations

from .graph import build_optimizer_graph, run_optimizer
from .merge import MergeResult, merge_pools, merge_pools_from_builds
from .pool import collect_pool, estimate_build_size, load_pool
from .state import BudgetState, BuildReport, CriticDecision, IterationLog, OptimizerResult
from .thresholds import (
    ApplyResult,
    apply_thresholds_to_build,
    apply_thresholds_to_builds,
    load_thresholds_from_optimizer_log,
)

__all__ = [
    "collect_pool",
    "load_pool",
    "estimate_build_size",
    "BudgetState",
    "IterationLog",
    "CriticDecision",
    "BuildReport",
    "OptimizerResult",
    "build_optimizer_graph",
    "run_optimizer",
    "merge_pools",
    "merge_pools_from_builds",
    "MergeResult",
    "apply_thresholds_to_build",
    "apply_thresholds_to_builds",
    "load_thresholds_from_optimizer_log",
    "ApplyResult",
]
