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
        rating_min: Minimum rating threshold (0.0–1.0).  ``None`` = disabled.
        rating_top_n: Keep at most *n* highest-rated games.  ``None`` = no
            limit.
        budget_bytes: Total output size budget in bytes.  ``None`` = unlimited.
        safety_margin: Fraction reserved as safety headroom (e.g. ``0.05``
            = 5%).  Multiplied into ``budget_bytes`` before comparison.
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
    """

    platform: PlatformId | None = None
    # Region
    preferred_regions: tuple[str, ...] = ()
    # Rating
    rating_min: float | None = None
    rating_top_n: int | None = None
    # Budget
    budget_bytes: int | None = None
    safety_margin: float = 0.05
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

    @property
    def effective_budget_bytes(self) -> int | None:
        """``budget_bytes * (1 - safety_margin)``, or ``None`` if no budget."""
        if self.budget_bytes is None:
            return None
        return int(self.budget_bytes * (1.0 - self.safety_margin))
