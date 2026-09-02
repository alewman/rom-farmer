"""Cache configuration models.

These classes define configuration for the ROM cache system.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .models import ROMCache


class CacheLinkMode(str, Enum):
    """How to provide cached files to output directories."""
    
    HARDLINK = "hardlink"  # Same inode, zero space, same filesystem only
    SYMLINK = "symlink"    # Cross-filesystem, but breaks if cache moves
    COPY = "copy"          # Full copy, portable but uses 2x space


class CacheVerifyLevel(str, Enum):
    """How thoroughly to verify cached files."""
    
    NONE = "none"      # Trust DB, fastest
    EXISTS = "exists"  # Check file exists (default)
    SIZE = "size"      # Check exists + size matches
    MD5 = "md5"        # Full verification, slowest


@dataclass
class CacheConfig:
    """Cache configuration."""
    
    cache_dir: Path = field(default_factory=lambda: Path("cache"))
    enabled: bool = True
    link_mode: CacheLinkMode = CacheLinkMode.HARDLINK
    verify_level: CacheVerifyLevel = CacheVerifyLevel.EXISTS
    check_tool_version: bool = True
    
    @classmethod
    def from_env(cls, workspace_root: Optional[Path] = None) -> "CacheConfig":
        """Load configuration from environment variables."""
        cache_dir = os.environ.get("ROMGROOMER_CACHE_DIR", "cache")
        if workspace_root and not Path(cache_dir).is_absolute():
            cache_dir = workspace_root / cache_dir
        
        return cls(
            cache_dir=Path(cache_dir),
            enabled=os.environ.get("ROMGROOMER_CACHE_ENABLED", "true").lower() == "true",
            link_mode=CacheLinkMode(
                os.environ.get("ROMGROOMER_CACHE_LINK_MODE", "hardlink").lower()
            ),
            verify_level=CacheVerifyLevel(
                os.environ.get("ROMGROOMER_CACHE_VERIFY_LEVEL", "exists").lower()
            ),
            check_tool_version=os.environ.get(
                "ROMGROOMER_CACHE_CHECK_TOOL_VERSION", "true"
            ).lower() == "true",
        )


@dataclass
class CacheResult:
    """Result of a cache operation."""
    
    hit: bool
    cache_path: Optional[Path] = None
    linked_path: Optional[Path] = None
    entry: Optional["ROMCache"] = None  # Forward reference
    message: str = ""
