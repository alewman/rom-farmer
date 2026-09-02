"""Farm-Hand — AI-driven ROM deployment module.

Introspects remote targets (Batocera, RockNIX) via SSH, plans optimal
ROM deployment across available storage, drives rom-farmer to build
size-optimized collections, and deploys results.
"""

from romfarmer.farmhand.models import (
    DeploymentPlan,
    DeploymentStatus,
    PlatformAllocation,
    PlatformTier,
    TargetProfile,
    TransferProgress,
    VolumeInfo,
    VolumeRole,
)

__all__ = [
    "TargetProfile",
    "VolumeInfo",
    "VolumeRole",
    "PlatformAllocation",
    "PlatformTier",
    "DeploymentPlan",
    "DeploymentStatus",
    "TransferProgress",
]
