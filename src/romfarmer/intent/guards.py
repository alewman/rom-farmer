"""Deterministic guards on stochastic proposals (intent brief v3 §Q4).

Moved from ``farmhand/optimizer/nodes.py::_apply_guards``.  In the intent
loop the *agent* is the critic, so these guards run inside
``validate_spec`` on a spec **revision**: a proposal that loosens a
threshold while the previous plan overshot the budget is rejected before it
ever reaches PLAN.  No LLM, no LangGraph — a while loop and arithmetic.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from romfarmer.ir.spec import Spec

STEP_SNAP = 0.05


def apply_guards(
    proposed: Mapping[str, float],
    current: Mapping[str, float],
    delta_bytes: int,
    history: Sequence[Any] = (),
    *,
    floor_keys: frozenset[str] = frozenset(),
    step: float = STEP_SNAP,
) -> dict[str, float]:
    """Sanitise proposed per-key thresholds against the current ones.

    1. Unknown keys (invented by the proposer) are ignored.
    2. ``floor_keys`` are pinned to 0.0.
    3. Values are clamped to [0, 1] and snapped to ``step``.
    4. After a spike (``history[-1].is_spike``) a change is capped at one step.
    5. Overshoot invariant: while ``delta_bytes > 0`` (over budget) a key may
       not be loosened (lowered) — the proposer may only tighten.
    """
    result = dict(current)
    is_overshoot = delta_bytes > 0
    last_spike = False
    if history:
        last = history[-1]
        last_spike = bool(
            last.get("is_spike", False)
            if isinstance(last, dict)
            else getattr(last, "is_spike", False)
        )

    for key, proposed_val in proposed.items():
        if key not in current:
            continue
        if key in floor_keys:
            result[key] = 0.0
            continue
        clamped = max(0.0, min(1.0, float(proposed_val)))
        snapped = round(round(clamped / step) * step, 10)
        if last_spike:
            diff = snapped - current[key]
            if abs(diff) > step:
                snapped = current[key] + (step if diff > 0 else -step)
                snapped = round(round(snapped / step) * step, 10)
        if is_overshoot and snapped < current.get(key, 0.0) - 1e-6:
            snapped = current.get(key, 0.0)
        result[key] = round(snapped, 4)
    return result


def guard_spec_revision(
    previous: Spec, revised: Spec, previous_headroom_p50: int | None
) -> list[str]:
    """Violations when *revised* loosens *previous* although the previous plan overshot.

    Returns human-readable reasons (empty = OK).  Only applies when the
    previous dry run reported ``headroom_p50 < 0``; otherwise any change is
    allowed (the agent is exploring an under-full card).
    """
    if previous_headroom_p50 is None or previous_headroom_p50 >= 0:
        return []
    prev = {p.platform: p for p in previous.platforms}
    out: list[str] = []
    for p in revised.platforms:
        q = prev.get(p.platform)
        if q is None:
            out.append(
                f"{p.platform}: added a platform while over budget by {-previous_headroom_p50:,} bytes"
            )
            continue
        pm, qm = p.passes.rating.min, q.passes.rating.min
        if qm is not None and (pm is None or pm < qm - 1e-9):
            out.append(
                f"{p.platform}: rating.min loosened {qm} → {pm} while over budget (only tighten on overshoot)"
            )
        pb, qb = p.passes.budget.max_bytes, q.passes.budget.max_bytes
        if qb is not None and (pb is None or pb > qb):
            out.append(f"{p.platform}: budget.max_bytes raised {qb:,} → {pb} while over budget")
        if p.passes.rating.unrated == "keep" and q.passes.rating.unrated == "drop":
            out.append(f"{p.platform}: rating.unrated loosened drop → keep while over budget")
    return out
