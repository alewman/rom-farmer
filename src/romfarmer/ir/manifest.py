"""romfarmer.ir.manifest — BuildManifest: the resolved build configuration.

``BuildManifest`` is the output of the RESOLVE phase and the primary input to
the PLAN phase.  Every planner pass receives a ``BuildManifest`` alongside the
``Catalog`` it is filtering.

This is a frozen IR-layer type.  It may only import from ``romfarmer.ir.*``
and the standard library — never from legacy ``romfarmer`` modules.
"""

from __future__ import annotations

from dataclasses import dataclass

from .catalog import PlatformId
from .chain import FormatChain


@dataclass(frozen=True, slots=True)
class BuildManifest:
    """Resolved build configuration for one platform (or a generation group).

    Constructed by the RESOLVE phase from the YAML configs and passed
    unchanged to every planner pass.

    Attributes:
        platform: The target platform id, or ``None`` for a multi-platform
            generation-level manifest.
        preferred_regions: Region preferences in descending priority order,
            e.g. ``("USA", "World", "Europe", "Japan")``.
        chain: The negotiated ``FormatChain`` (recipe ∩ target profile); its
            first element is the CostModel tool key.  ``()`` = unknown.
        rating_min: Minimum rating threshold on the **unit interval** (0.0–1.0;
            ``ScrapedGame.rating`` is stored 0–1).  Values > 1.0 are rejected
            at construction.  ``None`` = disabled.
        rating_unrated: What the rating pass does with units that have no
            rating when ``rating_min`` is set: ``"keep"`` (unknown ≠ bad) or
            ``"drop"``.
        budget_unrated_as: Where the budget pass ranks unrated units:
            ``"median"`` (default — the per-platform median of rated units,
            computed over the catalog entering the pass), ``"worst"``,
            ``"best"``, or a float on the unit interval.
        rating_top_n: Keep at most *n* highest-rated games.  ``None`` = no
            limit.
        budget_bytes: Total output size budget in bytes.  ``None`` = unlimited.
        safety_margin: Legacy fixed headroom fraction.  Retired — defaults to 0;
            the card-level constraint is the measured aggregate p90 headroom.
        generation_name: Logical generation key (e.g. ``"gen6"``).  ``None``
            = no cross-platform generation deduplication.
        generation_platform_order: Platform ids in priority order for the
            generation pass (highest priority first).  Ignored when
            ``generation_name`` is ``None``.
        curated_include: Canonical game names that must *not* be removed by
            any pass (rescued games / always-include lists).
        curated_exclude: Canonical game names that must always be removed
            regardless of other pass results.
        arcade_working_only: Arcade pass — keep only ``driver_status=good``
            games.
        arcade_include_hacks: Arcade pass — retain known hacks.
        arcade_include_bootlegs: Arcade pass — retain known bootlegs.
        ps3_keys_directory: PS3 lowering — directory containing Redump
            "Disc Keys TXT" zips, keyed by disc stem.  ``None`` = not PS3
            (or keys unavailable; lowering will fail at EXECUTE time).
    """

    platform: PlatformId | None = None
    chain: FormatChain = ()
    # Region
    preferred_regions: tuple[str, ...] = ()
    # Rating
    rating_min: float | None = None
    rating_top_n: int | None = None
    rating_unrated: str = "keep"
    # Budget
    budget_bytes: int | None = None
    budget_unrated_as: str = "median"
    safety_margin: float = 0.0  # retired 2026-09-03: p90 headroom (PlanSummary) is the constraint
    # Generation dedup
    generation_name: str | None = None
    generation_platform_order: tuple[str, ...] = ()
    # Curated lists
    curated_include: frozenset[str] = frozenset()
    curated_exclude: frozenset[str] = frozenset()
    # Arcade
    arcade_working_only: bool = True
    arcade_include_hacks: bool = False
    arcade_include_bootlegs: bool = False
    # Arcade selection decided at RESOLVE from DAT facts (cloneof/sourcefile/
    # romof/comment/driver_status) the catalog never sees.  None = not arcade.
    arcade_selected: frozenset[str] | None = None
    arcade_rejections: tuple[tuple[str, str], ...] = ()
    # DAT gate: drop units with no DAT match (the 1G1R DAT defines the set)
    dat_filter: bool = False
    # Name-heuristic 1G1R. Off when the DAT is already a Retool 1G1R export —
    # every entry it kept is a distinct title by Retool's judgement.
    one_g_one_r: bool = True
    # Test builds: seeded random subset applied after all other passes
    sample_n: int | None = None
    sample_seed: int = 0
    # PS3 lowering
    ps3_keys_directory: str | None = None

    def __post_init__(self) -> None:
        # Rating thresholds are on the unit interval.  A threshold like 3.5
        # (a 0–10 scale assumption) would silently remove every rated unit.
        if self.rating_min is not None and not (0.0 <= self.rating_min <= 1.0):
            raise ValueError(
                f"rating_min must be on the unit interval 0.0–1.0, got {self.rating_min!r}"
            )
        if self.rating_top_n is not None and self.rating_top_n < 1:
            raise ValueError(f"rating_top_n must be >= 1, got {self.rating_top_n!r}")
        if self.rating_unrated not in ("keep", "drop"):
            raise ValueError(
                f"rating_unrated must be 'keep' or 'drop', got {self.rating_unrated!r}"
            )
        self.unrated_rank()  # validates budget_unrated_as
        if not (0.0 <= self.safety_margin < 1.0):
            raise ValueError(f"safety_margin must be in [0, 1), got {self.safety_margin!r}")

    def unrated_rank(self) -> float | None:
        """``budget_unrated_as`` as a rating, or ``None`` for ``"median"`` (pass computes it)."""
        v = self.budget_unrated_as
        if v == "median":
            return None
        if v == "worst":
            return float("-inf")
        if v == "best":
            return float("inf")
        try:
            f = float(v)
        except ValueError:
            raise ValueError(
                f"budget_unrated_as must be 'median', 'worst', 'best' or a float, got {v!r}"
            ) from None
        if not (0.0 <= f <= 1.0):
            raise ValueError(f"budget_unrated_as float must be on the unit interval, got {f!r}")
        return f

    @property
    def effective_budget_bytes(self) -> int | None:
        """``budget_bytes * (1 - safety_margin)``, or ``None`` if no budget."""
        if self.budget_bytes is None:
            return None
        return int(self.budget_bytes * (1.0 - self.safety_margin))
