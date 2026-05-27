"""State schema for the LangGraph budget optimizer loop."""

from __future__ import annotations

import operator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Any, Dict, List, Literal, Optional

from typing_extensions import TypedDict

# ---------------------------------------------------------------------------
# Supplementary dataclasses (not part of LangGraph state directly)
# ---------------------------------------------------------------------------


@dataclass
class PoolEntry:
    """A single game entry in the pool manifest for one platform.

    Represents a game (or multi-disc group treated atomically) after the
    superset build pass.  ``size_bytes`` is the total compressed output size
    for all discs in the group.
    """

    name: str
    rating: float  # 0.0 – 1.0 from scraped_games DB; 0.0 if not in DB
    generation: str  # e.g. "gen5", "gen6", "gen7_handheld"
    size_bytes: int  # compressed output size (sum across all discs)
    multi_disc_group: Optional[str] = None  # None → single disc/cart
    is_disc_anchor: bool = True  # True → threshold check applies to this entry
    platform: str = ""


@dataclass
class BuildReport:
    """Estimated or actual build report for one selection pass.

    When produced by :func:`estimate_build_size` it is purely in-memory
    (no disk I/O).  When produced after a real organize pass it may be
    verified against the staging directory.
    """

    total_size_bytes: int
    per_platform_sizes: Dict[str, int] = field(default_factory=dict)
    per_generation_sizes: Dict[str, int] = field(default_factory=dict)
    per_generation_game_counts: Dict[str, int] = field(default_factory=dict)
    per_platform_game_counts: Dict[str, int] = field(default_factory=dict)
    multi_disc_groups_included: int = 0
    total_game_count: int = 0
    # Set when this report comes from a real staged directory walk
    staging_path: Optional[Path] = None
    is_estimated: bool = True

    @property
    def total_size_gb(self) -> float:
        return self.total_size_bytes / (1024**3)


@dataclass
class IterationLog:
    """Full record of one optimizer iteration."""

    iteration: int
    thresholds: Dict[str, float]
    used_bytes: int
    free_bytes: int
    delta_bytes: int  # used - target_used;  >0 = overshoot, <0 = undershoot
    action: str  # human-readable description of what changed
    critic_rationale: str
    wall_time_s: float = 0.0
    is_spike: bool = False  # True if large delta despite small threshold change


@dataclass
class CriticDecision:
    """Validated output from the LLM critic node."""

    thresholds: Dict[str, float]
    rationale: str
    expected_direction: Literal["grow", "shrink", "hold"]


@dataclass
class OptimizerResult:
    """Final result returned by :func:`run_optimizer`."""

    verdict: Literal["converged", "exhausted", "infeasible"]
    final_thresholds: Dict[str, float]
    final_report: Optional[BuildReport]
    history: List[IterationLog]
    iterations_used: int


# ---------------------------------------------------------------------------
# LangGraph TypedDict state
# ---------------------------------------------------------------------------


class BudgetState(TypedDict):
    """Mutable state threaded through the LangGraph optimizer loop.

    Immutable fields (set in ``init_builder``, never changed):
        target_total_bytes, target_free_bytes, tolerance_bytes,
        max_iterations, build_name, pool_root

    Mutable per-iteration fields:
        iteration, thresholds, platform_overrides,
        last_report, last_used_bytes, last_free_bytes, delta_to_target,
        no_progress_count, verdict

    Append-only lists (use ``operator.add`` reducer):
        history
    """

    # ── Immutable targets ───────────────────────────────────────────────────
    build_name: str
    pool_root: str  # str path so it is JSON-serializable
    target_total_bytes: int  # volume capacity
    target_free_bytes: int  # desired headroom (e.g. 30 GB)
    tolerance_bytes: int  # acceptable overshoot/undershoot of headroom (e.g. 5 GB)
    max_iterations: int

    # ── Current thresholds ─────────────────────────────────────────────────
    # Keys are generation names from CONSOLE_GENERATIONS (e.g. "gen3", "gen5").
    # Values are min_rating floats in [0.0, 1.0].
    thresholds: Dict[str, float]
    # Optional per-platform pins that override the generation threshold.
    platform_overrides: Dict[str, float]

    # ── Last build observation ─────────────────────────────────────────────
    last_report: Optional[Any]  # BuildReport (Any to keep TypedDict serializable)
    last_used_bytes: int
    last_free_bytes: int  # = target_total - last_used
    delta_to_target: int  # last_used - (target_total - target_free); + = overshoot

    # ── Loop counters ──────────────────────────────────────────────────────
    iteration: int
    no_progress_count: int
    verdict: Optional[str]  # None | "converged" | "exhausted" | "infeasible"

    # ── Pool capacity snapshot (set in init_builder, immutable) ─────────────
    # Max bytes available per generation if threshold were 0.0
    per_generation_max_bytes: Dict[str, int]
    # Actual max rating observed per generation in the pool
    per_generation_max_rating: Dict[str, float]

    # ── Append-only iteration log ──────────────────────────────────────────
    history: Annotated[List[Any], operator.add]
