"""Space optimization planner for Farm-Hand.

Given a target profile (with volume info) and rom-farmer's platform size data,
produces a DeploymentPlan that maximizes game coverage within available storage.

The planner implements a greedy bin-packing strategy:
1. Classify every platform by output size tier (tiny → massive)
2. Always include tiny/small platforms (they cost almost nothing)
3. Include medium platforms if space allows
4. For large/massive platforms, propose rating_budget selections sized to fit
5. Spread platforms across volumes intelligently
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from romfarmer.farmhand.models import (
    DeploymentPlan,
    DeploymentStatus,
    PlatformAllocation,
    PlatformSizeInfo,
    PlatformTier,
    SelectionAction,
    TargetProfile,
    VolumeInfo,
    VolumeRole,
)

logger = logging.getLogger(__name__)

# Tier thresholds in bytes
TIER_THRESHOLDS = {
    PlatformTier.TINY: 1 * 1024**3,  # < 1 GB
    PlatformTier.SMALL: 10 * 1024**3,  # 1–10 GB
    PlatformTier.MEDIUM: 100 * 1024**3,  # 10–100 GB
    PlatformTier.LARGE: 500 * 1024**3,  # 100–500 GB
    # anything above is MASSIVE
}

# Default budget allocations for large platforms (as percentage of remaining space)
# These are starting points — the AI agent can override any of them
DEFAULT_LARGE_BUDGET_GB = {
    "ps2": 80,  # Top ~200 games
    "psx": 60,  # Top ~300 games
    "psp": 40,  # Top ~150 games
    "xbox": 40,  # Top ~100 games
    "xbox360": 0,  # Skip by default (5.87 TB full set)
    "3ds": 40,  # Top ~200 games
    "dreamcast": 60,  # Top ~400 games
    "pcenginecd": 30,  # Top ~200 games
}

# Default space reservation for saves, BIOS, metadata, screenshots, etc.
DEFAULT_RESERVED_GB = 30


def classify_tier(size_bytes: int) -> PlatformTier:
    """Classify a platform into a size tier based on its full output size."""
    if size_bytes < TIER_THRESHOLDS[PlatformTier.TINY]:
        return PlatformTier.TINY
    elif size_bytes < TIER_THRESHOLDS[PlatformTier.SMALL]:
        return PlatformTier.SMALL
    elif size_bytes < TIER_THRESHOLDS[PlatformTier.MEDIUM]:
        return PlatformTier.MEDIUM
    elif size_bytes < TIER_THRESHOLDS[PlatformTier.LARGE]:
        return PlatformTier.LARGE
    else:
        return PlatformTier.MASSIVE


class SpacePlanner:
    """Plans optimal ROM deployment for a target device.

    Usage:
        planner = SpacePlanner(size_data_path="config/size_data.json")
        plan = planner.create_plan(
            target=target_profile,
            reserved_gb=30,
            exclude_platforms=["xbox360"],
        )
    """

    def __init__(
        self,
        size_data_path: str | Path | None = None,
        workspace_root: Path | None = None,
    ) -> None:
        if workspace_root is None:
            from romfarmer.core.paths import get_paths

            workspace_root = get_paths().workspace_root
        self.workspace_root = workspace_root

        if size_data_path is None:
            size_data_path = self.workspace_root / "config" / "size_data.json"

        self.size_data = self._load_size_data(Path(size_data_path))

    # ------------------------------------------------------------------
    # Size data loading
    # ------------------------------------------------------------------

    def _load_size_data(self, path: Path) -> dict[str, PlatformSizeInfo]:
        """Load platform size data from rom-farmer's size_data.json."""
        if not path.exists():
            logger.warning("Size data not found at %s", path)
            return {}

        with open(path) as f:
            raw = json.load(f)

        platforms: dict[str, PlatformSizeInfo] = {}
        for platform_name, entries in raw.items():
            if not entries:
                continue
            # Use the latest entry (last in the list)
            latest = entries[-1]
            size_bytes = latest.get("output_size_bytes", 0)
            platforms[platform_name] = PlatformSizeInfo(
                platform=platform_name,
                compression=latest.get("compression", ""),
                full_set_bytes=size_bytes,
                full_set_files=latest.get("output_files", 0),
                tier=classify_tier(size_bytes),
            )

        logger.info("Loaded size data for %d platforms", len(platforms))
        return platforms

    def get_platform_sizes(self) -> dict[str, PlatformSizeInfo]:
        """Return the loaded platform size data."""
        return dict(self.size_data)

    # ------------------------------------------------------------------
    # Plan creation
    # ------------------------------------------------------------------

    def create_plan(
        self,
        target: TargetProfile,
        reserved_gb: float = DEFAULT_RESERVED_GB,
        exclude_platforms: list[str] | None = None,
        include_only: list[str] | None = None,
        budget_overrides: dict[str, float] | None = None,
        prefer_primary_for: list[str] | None = None,
    ) -> DeploymentPlan:
        """Create a deployment plan for the target.

        Args:
            target: Scanned target profile with volume info.
            reserved_gb: Space to reserve for saves/BIOS/metadata per volume.
            exclude_platforms: Platforms to skip entirely.
            include_only: If set, only plan for these platforms.
            budget_overrides: Per-platform budget in GB (overrides defaults).
            prefer_primary_for: Platforms that should go on the primary volume.

        Returns:
            A DeploymentPlan with per-platform allocations.
        """
        exclude_platforms = set(exclude_platforms or [])
        budget_overrides = budget_overrides or {}
        prefer_primary_for = set(prefer_primary_for or [])

        reserved_bytes = int(reserved_gb * 1024**3)

        # Gather ROM volumes and compute available space
        rom_volumes = target.get_rom_volumes()
        if not rom_volumes:
            logger.error("No ROM volumes found on target")
            return DeploymentPlan(
                target_name=target.name,
                status=DeploymentStatus.FAILED,
                notes=["No ROM storage volumes found on target"],
            )

        # Compute per-volume available space (minus reservation)
        volume_budgets: dict[str, int] = {}
        for vol in rom_volumes:
            per_vol_reserve = reserved_bytes if vol.role == VolumeRole.PRIMARY else 0
            available = max(0, vol.available_bytes - per_vol_reserve)
            volume_budgets[vol.mount_point] = available

        total_available = sum(volume_budgets.values())

        plan = DeploymentPlan(
            target_name=target.name,
            status=DeploymentStatus.PLANNING,
            reserved_bytes=reserved_bytes,
            total_available_bytes=total_available,
        )

        # Filter platforms
        candidate_platforms = dict(self.size_data)
        if include_only:
            candidate_platforms = {
                k: v for k, v in candidate_platforms.items() if k in include_only
            }
        for excluded in exclude_platforms:
            candidate_platforms.pop(excluded, None)

        # Sort by tier (smallest first) so we fill guaranteed platforms first
        sorted_platforms = sorted(
            candidate_platforms.values(),
            key=lambda p: p.full_set_bytes,
        )

        # Track remaining space per volume
        remaining: dict[str, int] = dict(volume_budgets)

        # Phase 1: Always include tiny and small platforms
        for pinfo in sorted_platforms:
            if pinfo.tier not in (PlatformTier.TINY, PlatformTier.SMALL):
                continue

            volume = self._pick_volume(
                pinfo.platform, pinfo.full_set_bytes, rom_volumes, remaining, prefer_primary_for
            )
            if volume is None:
                plan.notes.append(
                    f"WARN: No space for {pinfo.platform} ({pinfo.full_set_bytes / 1024**3:.1f} GB)"
                )
                continue

            alloc = PlatformAllocation(
                platform=pinfo.platform,
                tier=pinfo.tier,
                action=SelectionAction.INCLUDE_ALL,
                full_set_bytes=pinfo.full_set_bytes,
                allocated_bytes=pinfo.full_set_bytes,
                target_volume=volume.mount_point,
                files_total=pinfo.full_set_files,
            )
            plan.allocations.append(alloc)
            remaining[volume.mount_point] -= pinfo.full_set_bytes

        # Phase 2: Include medium platforms if they fit
        for pinfo in sorted_platforms:
            if pinfo.tier != PlatformTier.MEDIUM:
                continue

            volume = self._pick_volume(
                pinfo.platform, pinfo.full_set_bytes, rom_volumes, remaining, prefer_primary_for
            )
            if volume is not None:
                alloc = PlatformAllocation(
                    platform=pinfo.platform,
                    tier=pinfo.tier,
                    action=SelectionAction.INCLUDE_ALL,
                    full_set_bytes=pinfo.full_set_bytes,
                    allocated_bytes=pinfo.full_set_bytes,
                    target_volume=volume.mount_point,
                    files_total=pinfo.full_set_files,
                )
                plan.allocations.append(alloc)
                remaining[volume.mount_point] -= pinfo.full_set_bytes
            else:
                # Medium platform doesn't fit in full — try budget
                budget_gb = budget_overrides.get(
                    pinfo.platform,
                    pinfo.full_set_bytes / (2 * 1024**3),  # half as default
                )
                budget_bytes = int(budget_gb * 1024**3)
                volume = self._pick_volume(
                    pinfo.platform, budget_bytes, rom_volumes, remaining, prefer_primary_for
                )
                if volume:
                    alloc = PlatformAllocation(
                        platform=pinfo.platform,
                        tier=pinfo.tier,
                        action=SelectionAction.BUDGET_SELECT,
                        full_set_bytes=pinfo.full_set_bytes,
                        allocated_bytes=budget_bytes,
                        target_volume=volume.mount_point,
                        selection_strategy="rating_budget",
                        selection_max_gb=budget_gb,
                    )
                    plan.allocations.append(alloc)
                    remaining[volume.mount_point] -= budget_bytes
                    plan.builds_needed.append(f"{pinfo.platform}-budget-{budget_gb:.0f}gb")
                else:
                    self._add_skipped(plan, pinfo, "No space even for budget selection")

        # Phase 3: Large and massive platforms — always use budget selection
        for pinfo in sorted_platforms:
            if pinfo.tier not in (PlatformTier.LARGE, PlatformTier.MASSIVE):
                continue

            # Check if user explicitly budgeted this platform
            budget_gb = budget_overrides.get(
                pinfo.platform,
                DEFAULT_LARGE_BUDGET_GB.get(pinfo.platform, 0),
            )

            if budget_gb <= 0:
                self._add_skipped(plan, pinfo, "No budget assigned (massive platform)")
                continue

            budget_bytes = int(budget_gb * 1024**3)
            volume = self._pick_volume(
                pinfo.platform, budget_bytes, rom_volumes, remaining, prefer_primary_for
            )

            if volume:
                alloc = PlatformAllocation(
                    platform=pinfo.platform,
                    tier=pinfo.tier,
                    action=SelectionAction.BUDGET_SELECT,
                    full_set_bytes=pinfo.full_set_bytes,
                    allocated_bytes=budget_bytes,
                    target_volume=volume.mount_point,
                    selection_strategy="rating_budget",
                    selection_max_gb=budget_gb,
                    selection_min_rating=0.5,
                )
                plan.allocations.append(alloc)
                remaining[volume.mount_point] -= budget_bytes
                plan.builds_needed.append(f"{pinfo.platform}-budget-{budget_gb:.0f}gb")
            else:
                self._add_skipped(plan, pinfo, f"No space for {budget_gb:.0f} GB budget")

        # Compute summary stats
        included = [a for a in plan.allocations if a.action != SelectionAction.SKIP]
        skipped = [a for a in plan.allocations if a.action == SelectionAction.SKIP]
        plan.platforms_included = len(included)
        plan.platforms_skipped = len(skipped)
        plan.total_allocated_bytes = sum(a.allocated_bytes for a in included)
        plan.total_estimated_files = sum(a.files_total for a in included)

        # Volume allocation summary
        for vol in rom_volumes:
            vol_allocs = plan.get_allocations_for_volume(vol.mount_point)
            plan.volume_allocations[vol.mount_point] = sum(a.allocated_bytes for a in vol_allocs)

        plan.status = DeploymentStatus.PENDING
        plan.notes.append(
            f"Plan: {plan.platforms_included} platforms, "
            f"{plan.total_allocated_bytes / 1024**3:.1f} GB allocated, "
            f"{plan.headroom_gb:.1f} GB headroom"
        )

        logger.info(plan.summary())
        return plan

    # ------------------------------------------------------------------
    # Volume assignment
    # ------------------------------------------------------------------

    def _pick_volume(
        self,
        platform: str,
        needed_bytes: int,
        volumes: list[VolumeInfo],
        remaining: dict[str, int],
        prefer_primary_for: set[str],
    ) -> VolumeInfo | None:
        """Pick the best volume for a platform allocation.

        Strategy:
        - If platform is in prefer_primary_for, try primary first
        - Otherwise use best-fit: smallest volume with enough space
        - This naturally fills primary first (since it's usually smaller)
          and spills large platforms to secondary storage
        """
        rom_volumes = [v for v in volumes if v.role in (VolumeRole.PRIMARY, VolumeRole.SECONDARY)]

        if platform in prefer_primary_for:
            # Try primary first
            for vol in rom_volumes:
                if (
                    vol.role == VolumeRole.PRIMARY
                    and remaining.get(vol.mount_point, 0) >= needed_bytes
                ):
                    return vol

        # Best-fit: pick volume with smallest remaining space that still fits
        candidates = [
            vol for vol in rom_volumes if remaining.get(vol.mount_point, 0) >= needed_bytes
        ]

        if not candidates:
            return None

        # Sort by remaining space ascending (best fit)
        candidates.sort(key=lambda v: remaining[v.mount_point])
        return candidates[0]

    def _add_skipped(
        self,
        plan: DeploymentPlan,
        pinfo: PlatformSizeInfo,
        reason: str,
    ) -> None:
        """Add a skipped platform to the plan."""
        alloc = PlatformAllocation(
            platform=pinfo.platform,
            tier=pinfo.tier,
            action=SelectionAction.SKIP,
            full_set_bytes=pinfo.full_set_bytes,
        )
        plan.allocations.append(alloc)
        plan.notes.append(f"SKIP {pinfo.platform}: {reason} (full set: {pinfo.full_set_gb:.1f} GB)")

    # ------------------------------------------------------------------
    # Utility: what-if analysis
    # ------------------------------------------------------------------

    def estimate_platforms_count(self, available_gb: float) -> dict[str, Any]:
        """Quick estimate: how many platforms fit in this much space?

        Returns a summary dict useful for MCP/CLI display.
        """
        available_bytes = int(available_gb * 1024**3)

        tiers: dict[str, list[dict]] = {
            "include_all": [],
            "budget_needed": [],
            "skip": [],
        }
        running_total = 0

        sorted_platforms = sorted(
            self.size_data.values(),
            key=lambda p: p.full_set_bytes,
        )

        for pinfo in sorted_platforms:
            if pinfo.tier in (PlatformTier.TINY, PlatformTier.SMALL):
                running_total += pinfo.full_set_bytes
                tiers["include_all"].append(
                    {
                        "platform": pinfo.platform,
                        "size_gb": round(pinfo.full_set_gb, 2),
                        "files": pinfo.full_set_files,
                        "tier": pinfo.tier.value,
                    }
                )
            elif pinfo.tier == PlatformTier.MEDIUM:
                if running_total + pinfo.full_set_bytes <= available_bytes:
                    running_total += pinfo.full_set_bytes
                    tiers["include_all"].append(
                        {
                            "platform": pinfo.platform,
                            "size_gb": round(pinfo.full_set_gb, 2),
                            "files": pinfo.full_set_files,
                            "tier": pinfo.tier.value,
                        }
                    )
                else:
                    budget = DEFAULT_LARGE_BUDGET_GB.get(pinfo.platform, 20)
                    tiers["budget_needed"].append(
                        {
                            "platform": pinfo.platform,
                            "full_size_gb": round(pinfo.full_set_gb, 2),
                            "suggested_budget_gb": budget,
                            "tier": pinfo.tier.value,
                        }
                    )
            else:
                budget = DEFAULT_LARGE_BUDGET_GB.get(pinfo.platform, 0)
                if budget > 0:
                    tiers["budget_needed"].append(
                        {
                            "platform": pinfo.platform,
                            "full_size_gb": round(pinfo.full_set_gb, 2),
                            "suggested_budget_gb": budget,
                            "tier": pinfo.tier.value,
                        }
                    )
                else:
                    tiers["skip"].append(
                        {
                            "platform": pinfo.platform,
                            "full_size_gb": round(pinfo.full_set_gb, 2),
                            "tier": pinfo.tier.value,
                        }
                    )

        return {
            "available_gb": available_gb,
            "guaranteed_gb": round(running_total / 1024**3, 2),
            "guaranteed_platforms": len(tiers["include_all"]),
            "budget_platforms": len(tiers["budget_needed"]),
            "skip_platforms": len(tiers["skip"]),
            **tiers,
        }
