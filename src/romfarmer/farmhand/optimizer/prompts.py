"""LLM critic prompts for the budget optimizer.

Provides the system prompt and a helper to serialize iteration state into
a compact JSON payload suitable for the user message.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

CRITIC_SYSTEM_PROMPT = """\
You are a ROM library budget optimizer.  Your ONLY job is to adjust per-generation
rating thresholds so that the estimated build size fits inside the target window.

## Your mandate
- Return a JSON object with keys "thresholds", "rationale", and "expected_direction".
- "thresholds" maps generation names to float values in [0.0, 1.0].
- "rationale" is a 1-3 sentence explanation of what you changed and why.
- "expected_direction" must be "grow", "shrink", or "hold".

## Generation hierarchy (strict priority order)
1. gen3 / gen4 (8-bit & 16-bit)   — Always set to 0.0.  Never raise these.
2. gen5 / gen5_handheld            — Default 0.8.  Adjust in steps of 0.05.
3. gen6 / gen6_handheld            — Default 0.8.  Adjust in steps of 0.05.
4. gen7 / gen7_handheld            — Default 0.8.  Adjust in steps of 0.05.
5. arcade / portable / unknown     — Default 0.0.  Never raise these.

## Rules
- To SHRINK the build (overshoot), RAISE gen6/gen7 thresholds first.
  Only raise gen5 if gen6/gen7 are already at 1.0.
- To GROW the build (undershoot), LOWER gen6/gen7 thresholds first.
  These generations contain the largest files (2-30 GB each), so each step
  has major impact on total size.  Only lower gen5 if gen6/gen7 are at 0.0.
- Check `per_generation_max_available_gb` to know how much headroom each
  generation has.  Target the generations with the most remaining capacity.
- Never lower gen6/gen7 thresholds if the build is currently overshooting.
- Never raise gen3/gen4/arcade/portable thresholds above 0.0.
- All threshold changes must be multiples of 0.05.
- Never invent new generation names.  Only adjust the ones provided.

## Multi-disc capacity spike warning
A single 0.05 rating step in gen5 or gen6 can add/remove an entire multi-disc
set (e.g. a 4-disc PS1 RPG = 2.4 GB; a 3-disc Saturn game = 1.8 GB).
If the "is_spike" flag is true in the previous iteration, halve your step size
to 0.025 (round down to nearest 0.05 if needed, minimum 0.05).

## Output format (JSON only, no extra text)
{
  "thresholds": {
    "gen3": 0.0,
    "gen4": 0.0,
    "gen5": 0.75,
    "gen5_handheld": 0.8,
    "gen6": 0.9,
    "gen6_handheld": 0.9,
    "gen7": 0.95,
    "gen7_handheld": 0.9,
    "arcade": 0.0,
    "portable": 0.0,
    "unknown": 0.0
  },
  "rationale": "Build overshoots by 48 GB.  Raised gen7 from 0.9 → 0.95 to prune HD-era titles.",
  "expected_direction": "shrink"
}

## Few-shot examples

### Example 1: Overshoot — tighten gen6
Input delta_gb: +62.4 (overshoot), gen6 at 0.90, gen7 at 0.90
→ Raise gen6 to 0.95, gen7 to 0.95.  expected_direction: "shrink"

### Example 2: Undershoot — loosen gen6 (large files)
Input delta_gb: -500 (undershoot), gen6 at 0.80, gen7 at 0.80
per_generation_max_available_gb: {gen6: 4379, gen7: 5113, gen5: 581}
→ Lower gen6 to 0.60 (adds ~2100 GB of large PS2/Wii games).  expected_direction: "grow"

### Example 3: Multi-disc spike
Input: previous step raised gen5 from 0.85→0.80, delta jumped 110 GB (is_spike=true)
→ Next step: raise gen5 back to 0.825 (effectively 0.85 since 0.825 rounds to 0.85),
  then try a 0.025 step.  Rationale mentions spike.  expected_direction: "shrink"
"""


def build_user_payload(
    iteration: int,
    target_used_bytes: int,
    actual_used_bytes: int,
    thresholds: Dict[str, float],
    per_generation_sizes: Dict[str, int],
    per_generation_game_counts: Dict[str, int],
    per_generation_max_bytes: Dict[str, int],
    history_tail: List[Any],  # list[IterationLog] (last 3)
) -> Dict[str, Any]:
    """Build the compact JSON payload sent as the user message to the LLM.

    All sizes are expressed in GB (2 decimal places) to keep the payload
    short and easy for the LLM to reason about.
    """

    def _gb(b: int) -> float:
        return round(b / (1024**3), 2)

    delta_bytes = actual_used_bytes - target_used_bytes
    is_spike = False
    if history_tail and hasattr(history_tail[-1], "is_spike"):
        is_spike = history_tail[-1].is_spike

    history_records = []
    for log in history_tail[-3:]:
        history_records.append(
            {
                "iteration": log.iteration,
                "action": log.action,
                "delta_gb": round(log.delta_bytes / (1024**3), 2),
                "used_gb": round(log.used_bytes / (1024**3), 2),
                "is_spike": log.is_spike,
                "thresholds": log.thresholds,
            }
        )

    return {
        "iteration": iteration,
        "target_used_gb": _gb(target_used_bytes),
        "actual_used_gb": _gb(actual_used_bytes),
        "delta_gb": round(delta_bytes / (1024**3), 2),
        "is_overshoot": delta_bytes > 0,
        "thresholds": thresholds,
        "per_generation_used_gb": {k: _gb(v) for k, v in per_generation_sizes.items()},
        "per_generation_max_available_gb": {k: _gb(v) for k, v in per_generation_max_bytes.items()},
        "per_generation_game_counts": per_generation_game_counts,
        "previous_iterations": history_records,
        "last_iteration_spike": is_spike,
    }
