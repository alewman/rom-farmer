"""Pydantic models for Farm-Hand deployment system.

Defines the data structures for target profiles, volume information,
deployment plans, and transfer tracking.
"""

from __future__ import annotations

import enum
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class VolumeRole(str, enum.Enum):
    """Role assignment for a storage volume on the target."""

    PRIMARY = "primary"  # Default ROM storage (e.g., /userdata)
    SECONDARY = "secondary"  # Overflow/large platforms (e.g., ext HDD)
    ARCHIVE = "archive"  # Cold storage, rarely accessed
    SYSTEM = "system"  # OS / boot — not for ROMs


class PlatformTier(str, enum.Enum):
    """Size classification for a platform's full output."""

    TINY = "tiny"  # <1 GB — always include all
    SMALL = "small"  # 1–10 GB — always include all
    MEDIUM = "medium"  # 10–100 GB — include if space allows
    LARGE = "large"  # 100–500 GB — needs selection/budget
    MASSIVE = "massive"  # >500 GB — always needs aggressive selection


class DeploymentStatus(str, enum.Enum):
    """Status of a deployment operation."""

    PENDING = "pending"
    PLANNING = "planning"
    BUILDING = "building"
    TRANSFERRING = "transferring"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SelectionAction(str, enum.Enum):
    """What to do with a platform during deployment."""

    INCLUDE_ALL = "include_all"  # Deploy the full set
    BUDGET_SELECT = "budget_select"  # Use rating_budget strategy
    CURATED_LIST = "curated_list"  # Use a curated keep list
    SKIP = "skip"  # Do not deploy this platform


# ---------------------------------------------------------------------------
# Volume & System Info
# ---------------------------------------------------------------------------


class VolumeInfo(BaseModel):
    """Information about a mounted storage volume on the target."""

    mount_point: str = Field(description="Mount point path (e.g., /userdata)")
    filesystem: str = Field(default="", description="Filesystem type (ext4, vfat, etc.)")
    device: str = Field(default="", description="Block device (e.g., /dev/nvme0n1p2)")
    total_bytes: int = Field(description="Total volume capacity in bytes")
    used_bytes: int = Field(description="Used space in bytes")
    available_bytes: int = Field(description="Available space in bytes")
    use_percent: float = Field(description="Usage percentage (0-100)")
    role: VolumeRole = Field(default=VolumeRole.SYSTEM, description="Assigned role")
    rom_path: Optional[str] = Field(
        default=None,
        description="Path where ROMs should go on this volume (e.g., /userdata/roms)",
    )

    @property
    def available_gb(self) -> float:
        return self.available_bytes / (1024**3)

    @property
    def total_gb(self) -> float:
        return self.total_bytes / (1024**3)

    @property
    def used_gb(self) -> float:
        return self.used_bytes / (1024**3)


class SystemInfo(BaseModel):
    """System information gathered from a remote target."""

    hostname: str = ""
    os_name: str = ""  # e.g., "Batocera" or "RockNIX"
    os_version: str = ""
    architecture: str = ""
    cpu_model: str = ""
    cpu_cores: int = 0
    cpu_threads: int = 0
    memory_total_mb: int = 0
    memory_available_mb: int = 0
    display_resolution: str = ""
    kernel_version: str = ""


class TargetCapabilities(BaseModel):
    """What the target system can do — discovered binaries and supported formats."""

    binaries: list[str] = Field(default_factory=list, description="Available binaries on target")
    emulators: list[str] = Field(
        default_factory=list, description="Detected emulator cores/executables"
    )
    supported_formats: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Per-platform supported file formats (e.g., {'psx': ['.chd', '.pbp']})",
    )
    has_7z: bool = Field(default=False, description="Whether 7z/7zr is available on target")
    has_chdman: bool = Field(default=False, description="Whether chdman is available on target")


# ---------------------------------------------------------------------------
# Target Profile
# ---------------------------------------------------------------------------


class TargetProfile(BaseModel):
    """Complete profile for a deployment target — persisted as YAML."""

    name: str = Field(description="Human-readable target name (e.g., batocera-nuc-livingroom)")
    host: str = Field(description="SSH host (IP or hostname)")
    port: int = Field(default=22, description="SSH port")
    user: str = Field(default="root", description="SSH username")
    auth_method: str = Field(
        default="password", description="Authentication method: password or key_file"
    )
    key_file: Optional[str] = Field(default=None, description="Path to SSH private key")
    frontend: str = Field(default="batocera", description="Frontend type (batocera, rocknix, etc.)")
    device_type: str = Field(default="pc", description="Device type from rom-farmer targets")

    # Discovered state (populated by analyzer)
    system_info: Optional[SystemInfo] = Field(default=None)
    volumes: list[VolumeInfo] = Field(default_factory=list)
    capabilities: Optional[TargetCapabilities] = Field(default=None)
    existing_roms: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Platform -> list of ROM filenames already on target",
    )

    # Metadata
    last_scanned: Optional[datetime] = Field(default=None)
    last_deployed: Optional[datetime] = Field(default=None)
    notes: str = Field(default="")

    def get_rom_volumes(self) -> list[VolumeInfo]:
        """Return volumes assigned to ROM storage (primary + secondary)."""
        return [
            v
            for v in self.volumes
            if v.role in (VolumeRole.PRIMARY, VolumeRole.SECONDARY) and v.rom_path
        ]

    def get_primary_volume(self) -> Optional[VolumeInfo]:
        """Return the primary ROM volume, if any."""
        for v in self.volumes:
            if v.role == VolumeRole.PRIMARY:
                return v
        return None

    def total_available_bytes(self) -> int:
        """Total available ROM storage across all ROM volumes."""
        return sum(v.available_bytes for v in self.get_rom_volumes())

    def total_available_gb(self) -> float:
        return self.total_available_bytes() / (1024**3)


# ---------------------------------------------------------------------------
# Platform Allocation & Deployment Plan
# ---------------------------------------------------------------------------


class PlatformSizeInfo(BaseModel):
    """Size data for a platform from rom-farmer's size_data.json."""

    platform: str
    compression: str = ""
    full_set_bytes: int = 0
    full_set_files: int = 0
    tier: PlatformTier = PlatformTier.TINY

    @property
    def full_set_gb(self) -> float:
        return self.full_set_bytes / (1024**3)


class PlatformAllocation(BaseModel):
    """Deployment decision for a single platform."""

    platform: str = Field(description="Platform name (e.g., psx, nes, saturn)")
    display_name: str = Field(default="", description="Human-readable name")
    tier: PlatformTier = Field(description="Size classification")
    action: SelectionAction = Field(description="What to do with this platform")

    # Size info
    full_set_bytes: int = Field(default=0, description="Size of full set from size_data")
    allocated_bytes: int = Field(default=0, description="Budgeted size for this platform")
    actual_bytes: int = Field(default=0, description="Actual deployed size (after transfer)")

    # Volume assignment
    target_volume: str = Field(default="", description="Mount point of target volume")

    # Selection parameters (if action is BUDGET_SELECT)
    selection_strategy: str = Field(default="", description="e.g., rating_budget")
    selection_max_gb: float = Field(default=0, description="Budget in GB for selection")
    selection_min_rating: float = Field(default=0, description="Minimum rating threshold")
    selection_limit: int = Field(default=0, description="Max game count")

    # Build config (if a custom build is needed)
    build_config_name: Optional[str] = Field(
        default=None, description="Name of generated build config"
    )

    # Transfer state
    files_total: int = Field(default=0)
    files_transferred: int = Field(default=0)
    bytes_transferred: int = Field(default=0)

    @property
    def allocated_gb(self) -> float:
        return self.allocated_bytes / (1024**3)

    @property
    def full_set_gb(self) -> float:
        return self.full_set_bytes / (1024**3)


class DeploymentPlan(BaseModel):
    """Complete deployment plan for a target — what goes where and how."""

    target_name: str = Field(description="Target profile name")
    created_at: datetime = Field(default_factory=datetime.now)
    status: DeploymentStatus = Field(default=DeploymentStatus.PENDING)

    # Budget
    reserved_bytes: int = Field(
        default=20 * 1024**3,
        description="Space reserved for saves, BIOS, metadata, etc.",
    )
    total_available_bytes: int = Field(default=0, description="Total ROM-usable space on target")

    # Per-volume breakdown
    volume_allocations: dict[str, int] = Field(
        default_factory=dict,
        description="Mount point -> total bytes allocated to ROMs on that volume",
    )

    # Platform decisions
    allocations: list[PlatformAllocation] = Field(
        default_factory=list, description="Per-platform deployment decisions"
    )

    # Summary stats
    platforms_included: int = Field(default=0)
    platforms_skipped: int = Field(default=0)
    total_allocated_bytes: int = Field(default=0)
    total_estimated_files: int = Field(default=0)

    # Build configs to generate (for platforms needing custom builds)
    builds_needed: list[str] = Field(
        default_factory=list,
        description="Build config names that need to be created/run",
    )

    notes: list[str] = Field(
        default_factory=list,
        description="Human-readable plan notes and rationale",
    )

    @property
    def total_allocated_gb(self) -> float:
        return self.total_allocated_bytes / (1024**3)

    @property
    def total_available_gb(self) -> float:
        return self.total_available_bytes / (1024**3)

    @property
    def headroom_bytes(self) -> int:
        return self.total_available_bytes - self.total_allocated_bytes

    @property
    def headroom_gb(self) -> float:
        return self.headroom_bytes / (1024**3)

    def get_allocations_for_volume(self, mount_point: str) -> list[PlatformAllocation]:
        """Get all platform allocations assigned to a specific volume."""
        return [a for a in self.allocations if a.target_volume == mount_point]

    def summary(self) -> str:
        """Human-readable plan summary."""
        lines = [
            f"Deployment Plan for {self.target_name}",
            f"  Available: {self.total_available_gb:.1f} GB "
            f"(reserved: {self.reserved_bytes / (1024**3):.0f} GB)",
            f"  Allocated: {self.total_allocated_gb:.1f} GB "
            f"({self.headroom_gb:.1f} GB headroom)",
            f"  Platforms: {self.platforms_included} included, "
            f"{self.platforms_skipped} skipped",
            f"  Files: ~{self.total_estimated_files:,}",
        ]
        if self.builds_needed:
            lines.append(f"  Builds needed: {len(self.builds_needed)}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Transfer Progress
# ---------------------------------------------------------------------------


class TransferProgress(BaseModel):
    """Real-time transfer progress tracking."""

    platform: str = ""
    current_file: str = ""
    files_total: int = 0
    files_done: int = 0
    bytes_total: int = 0
    bytes_done: int = 0
    bytes_per_second: float = 0
    started_at: Optional[datetime] = None
    eta_seconds: Optional[float] = None

    @property
    def percent(self) -> float:
        if self.bytes_total == 0:
            return 0.0
        return (self.bytes_done / self.bytes_total) * 100

    @property
    def speed_mbps(self) -> float:
        return self.bytes_per_second / (1024**2)
