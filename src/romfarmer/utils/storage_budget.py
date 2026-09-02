"""Storage budget utilities.

Handles parsing storage specifications like "512gb", "1tb" and computing
usable storage after accounting for filesystem overhead and reserved space.
"""

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Size unit multipliers (binary - 1GB = 1024^3 bytes)
SIZE_UNITS = {
    "b": 1,
    "kb": 1024,
    "mb": 1024**2,
    "gb": 1024**3,
    "tb": 1024**4,
    "pb": 1024**5,
}

# Storage constants
FILESYSTEM_OVERHEAD_FACTOR = 0.93  # ~7% lost to filesystem formatting
DEFAULT_RESERVED_GB = 20  # Reserve for OS, saves, updates, etc.


@dataclass
class StorageBudget:
    """Represents a parsed and computed storage budget.

    Attributes:
        raw_capacity_bytes: Advertised capacity in bytes (e.g., 512GB = 512*1024^3)
        formatted_capacity_bytes: Usable after formatting (raw * 0.93)
        reserved_bytes: Space reserved for system use
        available_bytes: Actual available budget for ROMs
        original_spec: Original specification string (e.g., "512gb")
    """

    raw_capacity_bytes: int
    formatted_capacity_bytes: int
    reserved_bytes: int
    available_bytes: int
    original_spec: str

    @property
    def available_gb(self) -> float:
        """Available space in gigabytes."""
        return self.available_bytes / SIZE_UNITS["gb"]

    @property
    def available_mb(self) -> int:
        """Available space in megabytes (rounded down)."""
        return int(self.available_bytes / SIZE_UNITS["mb"])

    def __str__(self) -> str:
        """Human-readable string representation."""
        return (
            f"StorageBudget({self.original_spec}): "
            f"{self.available_gb:.1f}GB available "
            f"(raw: {self.raw_capacity_bytes / SIZE_UNITS['gb']:.0f}GB, "
            f"formatted: {self.formatted_capacity_bytes / SIZE_UNITS['gb']:.1f}GB, "
            f"reserved: {self.reserved_bytes / SIZE_UNITS['gb']:.1f}GB)"
        )

    def is_unlimited(self) -> bool:
        """Check if this represents unlimited storage."""
        return self.original_spec.lower() == "unlimited"


def parse_size_spec(spec: str) -> int:
    """Parse a size specification to bytes.

    Supports formats:
    - "512gb", "512GB", "512 GB" - gigabytes
    - "1tb", "1 TB" - terabytes
    - "2048mb" - megabytes
    - "123456789" - raw bytes
    - "unlimited" - returns sys.maxsize

    Args:
        spec: Size specification string

    Returns:
        Size in bytes

    Raises:
        ValueError: If spec cannot be parsed
    """
    import sys

    spec = spec.strip().lower()

    # Special case: unlimited
    if spec == "unlimited":
        return sys.maxsize

    # Try to parse with unit
    match = re.match(r"^(\d+(?:\.\d+)?)\s*([a-z]+)?$", spec)
    if not match:
        raise ValueError(f"Cannot parse size spec: {spec}")

    value_str, unit = match.groups()
    value = float(value_str)

    if unit is None:
        # No unit = bytes
        return int(value)

    if unit not in SIZE_UNITS:
        raise ValueError(f"Unknown size unit: {unit} (valid: {', '.join(SIZE_UNITS.keys())})")

    return int(value * SIZE_UNITS[unit])


def compute_storage_budget(
    spec: str,
    filesystem_overhead: float = FILESYSTEM_OVERHEAD_FACTOR,
    reserved_gb: float = DEFAULT_RESERVED_GB,
) -> StorageBudget:
    """Compute available storage budget from a specification.

    Takes into account:
    1. Filesystem formatting overhead (~7% loss)
    2. Reserved space for OS, saves, updates

    Args:
        spec: Size specification (e.g., "512gb", "1tb", "unlimited")
        filesystem_overhead: Multiplier for formatted capacity (default 0.93)
        reserved_gb: GB to reserve for system use (default 20)

    Returns:
        StorageBudget instance with computed values

    Example:
        >>> budget = compute_storage_budget("512gb")
        >>> print(budget.available_gb)  # ~456.16 GB
    """
    import sys

    raw_bytes = parse_size_spec(spec)

    # Handle unlimited case
    if raw_bytes == sys.maxsize:
        return StorageBudget(
            raw_capacity_bytes=raw_bytes,
            formatted_capacity_bytes=raw_bytes,
            reserved_bytes=0,
            available_bytes=raw_bytes,
            original_spec=spec,
        )

    # Compute formatted capacity (after filesystem overhead)
    formatted_bytes = int(raw_bytes * filesystem_overhead)

    # Compute reserved space
    reserved_bytes = int(reserved_gb * SIZE_UNITS["gb"])

    # Compute available
    available_bytes = max(0, formatted_bytes - reserved_bytes)

    budget = StorageBudget(
        raw_capacity_bytes=raw_bytes,
        formatted_capacity_bytes=formatted_bytes,
        reserved_bytes=reserved_bytes,
        available_bytes=available_bytes,
        original_spec=spec,
    )

    logger.debug(f"Computed storage budget: {budget}")

    return budget


def format_size(size_bytes: int, precision: int = 1) -> str:
    """Format a byte size as human-readable string.

    Args:
        size_bytes: Size in bytes
        precision: Decimal precision (default 1)

    Returns:
        Human-readable size string (e.g., "1.5 GB")
    """
    if size_bytes == 0:
        return "0 B"

    import sys

    if size_bytes >= sys.maxsize:
        return "unlimited"

    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.{precision}f} {unit}"
        size_bytes /= 1024.0

    return f"{size_bytes:.{precision}f} PB"


class BudgetTracker:
    """Tracks storage budget usage during a build.

    Provides methods to allocate and track space usage per platform.
    """

    def __init__(self, budget: StorageBudget):
        """Initialize tracker with a storage budget.

        Args:
            budget: StorageBudget instance defining available space
        """
        self.budget = budget
        self.allocations: dict[str, int] = {}  # platform -> allocated bytes
        self.actual_usage: dict[str, int] = {}  # platform -> actual bytes used

    @property
    def total_allocated(self) -> int:
        """Total bytes allocated so far."""
        return sum(self.allocations.values())

    @property
    def total_used(self) -> int:
        """Total bytes actually used so far."""
        return sum(self.actual_usage.values())

    @property
    def remaining(self) -> int:
        """Remaining available bytes."""
        return self.budget.available_bytes - self.total_used

    @property
    def remaining_allocated(self) -> int:
        """Remaining unallocated bytes."""
        return self.budget.available_bytes - self.total_allocated

    def can_allocate(self, size_bytes: int) -> bool:
        """Check if size can be allocated within budget.

        Args:
            size_bytes: Size to check

        Returns:
            True if allocation would fit
        """
        if self.budget.is_unlimited():
            return True
        return (self.total_allocated + size_bytes) <= self.budget.available_bytes

    def allocate(self, platform: str, size_bytes: int) -> bool:
        """Allocate space for a platform.

        Args:
            platform: Platform name
            size_bytes: Estimated size in bytes

        Returns:
            True if allocated, False if would exceed budget
        """
        if not self.can_allocate(size_bytes):
            logger.warning(
                f"Cannot allocate {format_size(size_bytes)} for {platform}: "
                f"only {format_size(self.remaining_allocated)} remaining"
            )
            return False

        self.allocations[platform] = size_bytes
        logger.debug(f"Allocated {format_size(size_bytes)} for {platform}")
        return True

    def record_actual(self, platform: str, size_bytes: int):
        """Record actual size used for a platform.

        Args:
            platform: Platform name
            size_bytes: Actual size in bytes
        """
        self.actual_usage[platform] = size_bytes

        # Log variance from allocation
        if platform in self.allocations:
            allocated = self.allocations[platform]
            variance = size_bytes - allocated
            variance_pct = (variance / allocated * 100) if allocated > 0 else 0

            if abs(variance_pct) > 20:
                logger.warning(
                    f"{platform}: actual {format_size(size_bytes)} vs "
                    f"allocated {format_size(allocated)} ({variance_pct:+.1f}%)"
                )

    def get_summary(self) -> dict:
        """Get summary of budget usage.

        Returns:
            Dictionary with budget summary
        """
        return {
            "total_budget": format_size(self.budget.available_bytes),
            "total_allocated": format_size(self.total_allocated),
            "total_used": format_size(self.total_used),
            "remaining": format_size(self.remaining),
            "platforms": len(self.actual_usage),
            "utilization_pct": (
                (self.total_used / self.budget.available_bytes * 100)
                if not self.budget.is_unlimited()
                else 0
            ),
        }
