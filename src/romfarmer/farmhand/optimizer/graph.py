"""Budget-optimizer loop and top-level run_optimizer() entry point.

LEGACY: this in-process evaluator-optimizer (LLM critic over a pool collected
from a prior superset build) is superseded by the intent loop
(``romfarmer.intent``: agent proposes a Spec, ``dry_run`` over cached catalogs,
``validate_spec`` applies the same guards).  Kept for ``romfarmer farmhand
optimize`` until that command is retargeted; LangGraph is no longer required.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .nodes import evaluator_critic, finalize, init_builder, run_build_estimate
from .pool import collect_pool as _collect_pool
from .state import BudgetState, IterationLog, OptimizerResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Conditional edge routing
# ---------------------------------------------------------------------------


def route_after_build(state: BudgetState) -> str:
    """Decide the next node after run_build_estimate.

    Returns:
        "done"      → finalize  (within tolerance)
        "exhausted" → finalize  (max iterations or stall)
        "critic"    → evaluator_critic  (needs adjustment)
    """
    delta = state.get("delta_to_target", 0)
    tol = state["tolerance_bytes"]

    if abs(delta) <= tol:
        logger.info(f"  route: converged (|delta|={abs(delta) / 1024**3:.2f} GB ≤ tol)")
        return "done"

    if state["iteration"] >= state["max_iterations"]:
        logger.info(f"  route: exhausted (max_iterations={state['max_iterations']} reached)")
        return "exhausted"

    if state.get("no_progress_count", 0) >= 2:
        logger.info("  route: exhausted (no_progress_count >= 2)")
        return "exhausted"

    return "critic"


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------


class _OptimizerLoop:
    """The former LangGraph graph as a plain loop (intent brief v3 Q4: LangGraph dropped).

    Topology::

        init_builder → run_build_estimate ─┬─ done/exhausted → finalize
                                            └─ critic → evaluator_critic → run_build_estimate
    """

    def invoke(self, state: dict[str, Any]) -> dict[str, Any]:
        state = dict(state)
        state.update(init_builder(state))  # type: ignore[arg-type]
        while True:
            state.update(run_build_estimate(state))  # type: ignore[arg-type]
            route = route_after_build(state)  # type: ignore[arg-type]
            if route in ("done", "exhausted"):
                break
            state.update(evaluator_critic(state))  # type: ignore[arg-type]
        state.update(finalize(state))  # type: ignore[arg-type]
        return state


def build_optimizer_graph() -> _OptimizerLoop:
    """Return the optimizer loop (kept for callers that used the LangGraph app's ``.invoke``)."""
    return _OptimizerLoop()


def run_optimizer(
    build_name: str,
    target_total_bytes: int,
    target_free_bytes: int = 30 * 1024**3,
    tolerance_bytes: int = 5 * 1024**3,
    max_iterations: int = 8,
    pool_root: Path | None = None,
    platform_overrides: dict[str, float] | None = None,
    collect_pool_first: bool = False,
    output_base: Path | None = None,
) -> OptimizerResult:
    """Run the (legacy, in-process) budget optimizer loop.

    Args:
        build_name: Name of the build (used to locate pool manifests and
                    write the audit log).
        target_total_bytes: Total capacity of the target volume in bytes.
        target_free_bytes: Desired free headroom after the build (e.g. 30 GB).
        tolerance_bytes: Acceptable deviation from ``target_free_bytes``
                         on either side (e.g. ±5 GB).
        max_iterations: Hard cap on the number of critic-adjust cycles.
        pool_root: Path to the ``.pool`` directory containing platform
                   manifests.  Defaults to
                   ``output/{build_name}/.pool``.
        platform_overrides: Optional per-platform threshold pins that take
                            precedence over the generation threshold.
        collect_pool_first: If True, run :func:`~.pool.collect_pool` to
                            (re-)generate pool manifests before optimizing.
                            Requires ``output_base`` to point to the superset
                            build output.
        output_base: Only needed when ``collect_pool_first=True``.

    Returns:
        :class:`~.state.OptimizerResult` with verdict, final thresholds,
        final report, and full iteration history.
    """
    from romfarmer.core.paths import get_paths

    workspace = get_paths().workspace_root

    if pool_root is None:
        pool_root = workspace / "output" / build_name / ".pool"

    if collect_pool_first:
        if output_base is None:
            output_base = workspace / "output"
        logger.info(f"Collecting pool manifest from {output_base / build_name} …")
        _collect_pool(build_name=build_name, output_base=output_base, workspace_root=workspace)

    if not pool_root.exists():
        raise FileNotFoundError(
            f"Pool root not found: {pool_root}\n"
            "Run collect_pool() first or pass collect_pool_first=True."
        )

    # ── Pre-check: is the target achievable at all? ────────────────────────
    from .pool import estimate_build_size, load_pool

    _pool = load_pool(pool_root)
    _max_report = estimate_build_size(_pool, {})  # all thresholds = 0.0
    _target_used = target_total_bytes - target_free_bytes
    if _max_report.total_size_bytes < _target_used - tolerance_bytes:
        _max_gb = _max_report.total_size_bytes / 1024**3
        _tgt_gb = _target_used / 1024**3
        logger.warning(
            f"Pool capacity {_max_gb:.1f} GB is less than target {_tgt_gb:.1f} GB. "
            f"Optimizer will run but cannot reach target — reporting best-effort result."
        )

    app = build_optimizer_graph()

    initial_state: dict[str, Any] = {
        "build_name": build_name,
        "pool_root": str(pool_root),
        "target_total_bytes": target_total_bytes,
        "target_free_bytes": target_free_bytes,
        "tolerance_bytes": tolerance_bytes,
        "max_iterations": max_iterations,
        # Remaining fields are seeded by init_builder
        "thresholds": {},
        "platform_overrides": platform_overrides or {},
        "last_report": None,
        "last_used_bytes": 0,
        "last_free_bytes": target_total_bytes,
        "delta_to_target": -(target_total_bytes - target_free_bytes),
        "iteration": 0,
        "no_progress_count": 0,
        "verdict": None,
        "history": [],
        "per_generation_max_bytes": {},
        "per_generation_max_rating": {},
    }

    logger.info(
        f"Starting optimizer: build={build_name}, "
        f"target={target_total_bytes / 1024**3:.0f} GB, "
        f"headroom={target_free_bytes / 1024**3:.0f} GB ±{tolerance_bytes / 1024**3:.0f} GB, "
        f"max_iter={max_iterations}"
    )

    final_state = app.invoke(initial_state)

    # Re-hydrate history from dicts to IterationLog objects
    history = [_dict_to_iterlog(h) for h in (final_state.get("history") or [])]

    from .state import BuildReport

    last_report_dict = final_state.get("last_report")
    last_report: BuildReport | None = None
    if last_report_dict:
        try:
            last_report = BuildReport(**last_report_dict)
        except Exception:
            pass

    return OptimizerResult(
        verdict=final_state.get("verdict") or "infeasible",
        final_thresholds=final_state.get("thresholds", {}),
        final_report=last_report,
        history=history,
        iterations_used=final_state.get("iteration", 0),
    )


def _dict_to_iterlog(d: Any) -> IterationLog:
    if isinstance(d, IterationLog):
        return d
    if isinstance(d, dict):
        return IterationLog(
            iteration=d.get("iteration", 0),
            thresholds=d.get("thresholds", {}),
            used_bytes=d.get("used_bytes", 0),
            free_bytes=d.get("free_bytes", 0),
            delta_bytes=d.get("delta_bytes", 0),
            action=d.get("action", ""),
            critic_rationale=d.get("critic_rationale", ""),
            wall_time_s=d.get("wall_time_s", 0.0),
            is_spike=d.get("is_spike", False),
        )
    return IterationLog(0, {}, 0, 0, 0, "", "")
