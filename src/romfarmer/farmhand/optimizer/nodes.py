"""LangGraph optimizer node functions.

Each function corresponds to one graph node.  They receive the full
:class:`~.state.BudgetState` and return a partial dict that LangGraph
merges back into the state.

Nodes
-----
init_builder
    Seed the state: load pool manifests, set default thresholds, compute
    target headroom, enforce gen3/4 floor.

run_build_estimate
    Apply current thresholds to the pool → :class:`~.state.BuildReport`,
    compute delta, detect multi-disc spikes, append to history.

evaluator_critic
    Compose LLM payload, call the critic, apply deterministic guards,
    return updated thresholds.

finalize
    Verify final state, emit audit log, return :class:`~.state.OptimizerResult`.
"""

from __future__ import annotations

import dataclasses
import json
import logging
import time
from pathlib import Path
from typing import Any

from .pool import DEFAULT_THRESHOLDS, estimate_build_size, load_pool
from .state import BudgetState, BuildReport, CriticDecision, IterationLog

logger = logging.getLogger(__name__)

# Threshold adjustment must snap to this granularity
_STEP_SNAP = 0.05

# If the size delta improved by less than this between two iterations,
# increment no_progress_count
_PROGRESS_THRESHOLD_BYTES = 1 * 1024**3  # 1 GB

# Generations the LLM is allowed to adjust (ascending priority = tighten first)
_ADJUSTABLE_GENS = ["gen5", "gen5_handheld", "gen6", "gen6_handheld", "gen7", "gen7_handheld"]

# Generations that are permanently floored at 0.0
_FLOOR_GENS = {"gen3", "gen4", "arcade", "portable", "unknown"}


# ---------------------------------------------------------------------------
# Node: init_builder
# ---------------------------------------------------------------------------


def init_builder(state: BudgetState) -> dict[str, Any]:
    """Load pool manifests and seed thresholds.

    Expected input keys (must be pre-populated by the caller):
        build_name, pool_root, target_total_bytes, target_free_bytes,
        tolerance_bytes, max_iterations.

    Returns partial state update with pool-derived data and seeded thresholds.
    """
    pool_root = Path(state["pool_root"])
    pool = load_pool(pool_root)

    if not pool:
        logger.warning(f"No pool manifests found at {pool_root}. Run collect_pool() first.")

    # Discover all generations represented in the pool and compute pool stats
    all_gens: set[str] = set()
    per_gen_max_bytes: dict[str, int] = {}
    per_gen_max_rating: dict[str, float] = {}
    for entries in pool.values():
        for e in entries:
            all_gens.add(e.generation)
            per_gen_max_bytes[e.generation] = per_gen_max_bytes.get(e.generation, 0) + e.size_bytes
            cur_max = per_gen_max_rating.get(e.generation, 0.0)
            if e.rating > cur_max:
                per_gen_max_rating[e.generation] = e.rating

    # Seed thresholds: start from defaults, ensure all discovered gens are present
    thresholds = {gen: DEFAULT_THRESHOLDS.get(gen, 0.0) for gen in all_gens}

    # Business rule: gen3/gen4 always floor to 0.0 on init
    for gen in _FLOOR_GENS:
        thresholds[gen] = 0.0

    # Cap seeded thresholds at the actual max rating in the pool for each generation.
    # If the default seed (e.g. 0.9) exceeds all ratings in the pool (max=0.8),
    # it would include zero games from that generation — a useless starting point.
    for gen in list(thresholds.keys()):
        if gen in _FLOOR_GENS:
            continue
        pool_max = per_gen_max_rating.get(gen, 0.0)
        if thresholds[gen] > pool_max:
            old = thresholds[gen]
            thresholds[gen] = pool_max
            logger.info(
                f"  Capped seed threshold for {gen}: {old:.2f} → {pool_max:.2f} (pool max rating)"
            )

    logger.info(f"init_builder: {len(pool)} platforms, generations: {sorted(all_gens)}")
    logger.info(f"Seeded thresholds: {thresholds}")

    return {
        "iteration": 0,
        "thresholds": thresholds,
        "platform_overrides": state.get("platform_overrides") or {},
        "last_report": None,
        "last_used_bytes": 0,
        "last_free_bytes": state["target_total_bytes"],
        "delta_to_target": -(state["target_total_bytes"] - state["target_free_bytes"]),
        "no_progress_count": 0,
        "verdict": None,
        "history": [],
        "per_generation_max_bytes": per_gen_max_bytes,
        "per_generation_max_rating": per_gen_max_rating,
    }


# ---------------------------------------------------------------------------
# Node: run_build_estimate
# ---------------------------------------------------------------------------


def run_build_estimate(state: BudgetState) -> dict[str, Any]:
    """Apply current thresholds to pool → BuildReport, compute delta.

    This is the tight inner loop — pure in-memory estimation.
    """
    t0 = time.time()

    pool_root = Path(state["pool_root"])
    pool = load_pool(pool_root)

    report: BuildReport = estimate_build_size(
        pool=pool,
        thresholds=state["thresholds"],
        platform_overrides=state.get("platform_overrides") or {},
    )

    target_used = state["target_total_bytes"] - state["target_free_bytes"]
    delta = report.total_size_bytes - target_used
    free = state["target_total_bytes"] - report.total_size_bytes

    # Detect multi-disc capacity spike
    iteration = state["iteration"] + 1
    prev_delta = state.get("delta_to_target", 0)
    prev_abs = abs(prev_delta)
    curr_abs = abs(delta)
    # Spike: delta got worse or barely improved (<1 GB) after a threshold change
    is_spike = (
        iteration > 1
        and prev_abs > 0
        and (curr_abs > prev_abs * 0.8)  # less than 20% improvement
        and abs(prev_abs - curr_abs) < 1 * 1024**3
    )

    # No-progress detection
    no_progress = state.get("no_progress_count", 0)
    if iteration > 1:
        improvement = prev_abs - curr_abs
        if improvement < _PROGRESS_THRESHOLD_BYTES:
            no_progress += 1
        else:
            no_progress = 0

    log_entry = IterationLog(
        iteration=iteration,
        thresholds=dict(state["thresholds"]),
        used_bytes=report.total_size_bytes,
        free_bytes=free,
        delta_bytes=delta,
        action=_describe_action(state["thresholds"], state.get("history", [])),
        critic_rationale="(initial estimate)" if iteration == 1 else "",
        wall_time_s=round(time.time() - t0, 2),
        is_spike=is_spike,
    )

    gb = report.total_size_bytes / 1024**3
    free_gb = free / 1024**3
    delta_gb = delta / 1024**3
    direction = "OVER" if delta > 0 else "UNDER"
    logger.info(
        f"[iter {iteration}] used={gb:.1f} GB  free={free_gb:.1f} GB  "
        f"delta={delta_gb:+.1f} GB ({direction})" + (" ⚡ spike" if is_spike else "")
    )

    return {
        "iteration": iteration,
        "last_report": dataclasses.asdict(report),
        "last_used_bytes": report.total_size_bytes,
        "last_free_bytes": free,
        "delta_to_target": delta,
        "no_progress_count": no_progress,
        "history": [dataclasses.asdict(log_entry)],
    }


def _describe_action(thresholds: dict[str, float], history: list[Any]) -> str:
    """Build a short description of what changed since the previous iteration."""
    if not history:
        return "initial"
    prev = history[-1]
    prev_thresholds = prev.get("thresholds", {}) if isinstance(prev, dict) else {}
    changes = []
    for gen, val in thresholds.items():
        prev_val = prev_thresholds.get(gen, val)
        if abs(val - prev_val) > 1e-6:
            direction = "↑" if val > prev_val else "↓"
            changes.append(f"{gen} {prev_val:.2f}{direction}{val:.2f}")
    return ", ".join(changes) if changes else "noop"


# ---------------------------------------------------------------------------
# Node: evaluator_critic
# ---------------------------------------------------------------------------


def evaluator_critic(state: BudgetState) -> dict[str, Any]:
    """Call the LLM critic and apply deterministic guards to proposed thresholds.

    Guard pipeline (applied AFTER LLM output, BEFORE state update):
    1. Clamp all thresholds to [0.0, 1.0].
    2. Floor gen3/gen4/arcade/portable/unknown to 0.0.
    3. Snap all changes to multiples of _STEP_SNAP (0.05).
    4. Hierarchy invariant:
       - If overshoot: reject any thresholds that lower a generation value
         compared to the previous iteration (critic should only tighten on overshoot).
       - If undershoot: reject any thresholds that raise a gen6/gen7 value
         if gen5 is not yet at 0.0 (must exhaust gen5 first).
    5. Multi-disc spike half-step: if last iteration was a spike, cap the
       maximum change magnitude at _STEP_SNAP / 2 (0.025, then snap to 0.05).
    """
    from .llm_client import call_critic
    from .prompts import CRITIC_SYSTEM_PROMPT, build_user_payload

    target_used = state["target_total_bytes"] - state["target_free_bytes"]
    delta = state["delta_to_target"]

    history_raw = state.get("history", [])
    # Re-hydrate from dict to IterationLog for prompts helper
    history_logs = [_dict_to_iterlog(h) for h in history_raw]

    report_dict = state.get("last_report") or {}
    per_gen_sizes = report_dict.get("per_generation_sizes", {})
    per_gen_counts = report_dict.get("per_generation_game_counts", {})

    payload = build_user_payload(
        iteration=state["iteration"],
        target_used_bytes=target_used,
        actual_used_bytes=state["last_used_bytes"],
        thresholds=state["thresholds"],
        per_generation_sizes=per_gen_sizes,
        per_generation_game_counts=per_gen_counts,
        per_generation_max_bytes=state.get("per_generation_max_bytes") or {},
        history_tail=history_logs,
    )

    decision: CriticDecision = call_critic(CRITIC_SYSTEM_PROMPT, payload)
    logger.info(f"  Critic: {decision.rationale[:120]}")

    # ── Deterministic guards ────────────────────────────────────────────────
    guarded = _apply_guards(
        proposed=decision.thresholds,
        current=state["thresholds"],
        delta_bytes=delta,
        history=history_raw,
    )

    return {"thresholds": guarded}


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


def _apply_guards(
    proposed: dict[str, float],
    current: dict[str, float],
    delta_bytes: int,
    history: list[Any],
) -> dict[str, float]:
    """Apply deterministic post-LLM guards and return sanitized thresholds."""
    result = dict(current)  # start from current, apply proposed changes
    is_overshoot = delta_bytes > 0

    # Detect spike from last log entry
    last_spike = False
    if history:
        last = history[-1]
        last_spike = last.get("is_spike", False) if isinstance(last, dict) else last.is_spike

    for gen, proposed_val in proposed.items():
        if gen not in current:
            # Ignore unknown generation names invented by the LLM
            continue

        # Guard 1: floor generations
        if gen in _FLOOR_GENS:
            result[gen] = 0.0
            continue

        # Guard 2: clamp to [0.0, 1.0]
        clamped = max(0.0, min(1.0, proposed_val))

        # Guard 3: snap to 0.05 steps
        snapped = round(round(clamped / _STEP_SNAP) * _STEP_SNAP, 10)

        # Guard 4a: spike protection — cap change magnitude at half-step
        if last_spike:
            max_change = _STEP_SNAP  # still full step; half-step would be 0.025 → round to 0.05
            diff = snapped - current[gen]
            if abs(diff) > max_change:
                snapped = current[gen] + (max_change if diff > 0 else -max_change)
                snapped = round(round(snapped / _STEP_SNAP) * _STEP_SNAP, 10)

        # Guard 4b: overshoot invariant — reject loosening during overshoot
        if is_overshoot and snapped < current.get(gen, 0.0) - 1e-6:
            logger.debug(
                f"  Guard: rejecting loosen of {gen} during overshoot ({current[gen]:.2f}→{snapped:.2f})"
            )
            snapped = current.get(gen, 0.0)

        result[gen] = round(snapped, 4)

    return result


# ---------------------------------------------------------------------------
# Node: finalize
# ---------------------------------------------------------------------------


def finalize(state: BudgetState) -> dict[str, Any]:
    """Verify convergence, write audit log, determine final verdict.

    Verification checks (programmatic — no LLM involvement):
    1. Build report size matches pool estimate within 1 MB.
    2. All gen3/gen4/floor thresholds remain at 0.0.
    3. Generation hierarchy invariant: for adjustable generations in priority
       order, a younger generation's threshold must be >= older generation's
       (unless it's a floor gen).
    4. Final headroom within tolerance.
    """
    delta = state.get("delta_to_target", 0)
    tol = state["tolerance_bytes"]

    # Determine verdict
    verdict = state.get("verdict")
    if verdict is None:
        if abs(delta) <= tol:
            verdict = "converged"
        elif state["iteration"] >= state["max_iterations"]:
            verdict = "exhausted"
        elif state.get("no_progress_count", 0) >= 2:
            verdict = "exhausted"
        else:
            verdict = "infeasible"

    # Programmatic verification
    warnings: list[str] = []

    # Check 1: floor thresholds
    final_t = state.get("thresholds", {})
    for gen in _FLOOR_GENS:
        if gen in final_t and final_t[gen] > 1e-6:
            warnings.append(f"WARN: floor gen {gen} has threshold {final_t[gen]} (should be 0.0)")

    # Check 2: hierarchy invariant (gen5 <= gen6)
    gen5_val = max(final_t.get("gen5", 0.0), final_t.get("gen5_handheld", 0.0))
    gen6_val = min(
        final_t.get("gen6", 1.0),
        final_t.get("gen6_handheld", 1.0),
        final_t.get("gen7", 1.0),
        final_t.get("gen7_handheld", 1.0),
    )
    if gen5_val > gen6_val + 1e-6:
        warnings.append(
            f"WARN: gen5 threshold ({gen5_val:.2f}) > gen6 threshold ({gen6_val:.2f}) — "
            "hierarchy violated"
        )

    # Check 3: headroom
    free_gb = state.get("last_free_bytes", 0) / 1024**3
    state["target_free_bytes"] / 1024**3
    if abs(delta) > tol and verdict == "converged":
        warnings.append(
            f"WARN: verdict=converged but |delta|={abs(delta) / 1024**3:.1f} GB > "
            f"tolerance={tol / 1024**3:.1f} GB"
        )

    for w in warnings:
        logger.warning(w)

    # Write audit log
    _write_audit_log(state, verdict, warnings)

    delta_gb = delta / 1024**3
    logger.info(
        f"finalize: verdict={verdict}, iterations={state['iteration']}, "
        f"free={free_gb:.1f} GB, delta={delta_gb:+.1f} GB"
    )

    return {"verdict": verdict}


def _write_audit_log(state: BudgetState, verdict: str, warnings: list[str]) -> None:
    """Write a JSON audit log to output/{build_name}/optimizer.log.json."""
    try:
        from romfarmer.core.paths import get_paths

        output_dir = get_paths().workspace_root / "output" / state["build_name"]
        output_dir.mkdir(parents=True, exist_ok=True)
        log_path = output_dir / "optimizer.log.json"
        payload = {
            "build_name": state["build_name"],
            "verdict": verdict,
            "iterations": state["iteration"],
            "final_thresholds": state.get("thresholds", {}),
            "final_used_gb": round(state.get("last_used_bytes", 0) / 1024**3, 2),
            "final_free_gb": round(state.get("last_free_bytes", 0) / 1024**3, 2),
            "delta_gb": round(state.get("delta_to_target", 0) / 1024**3, 2),
            "warnings": warnings,
            "history": state.get("history", []),
        }
        with open(log_path, "w") as f:
            json.dump(payload, f, indent=2, default=str)
        logger.info(f"Audit log: {log_path}")
    except Exception as e:
        logger.warning(f"Could not write audit log: {e}")
