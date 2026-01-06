"""
ROM Cache Module

Provides caching for transformed ROM files (CHD, RVZ, 7z, etc.) to avoid
redundant processing across builds. Files are stored by source hash and
can be linked to output directories to save disk space.
"""

from .manager import CacheManager
from .config import CacheConfig, CacheLinkMode, CacheVerifyLevel, CacheResult
from .models import ROMCache

__all__ = [
    "CacheManager",
    "CacheConfig",
    "CacheResult",
    "CacheLinkMode",
    "CacheVerifyLevel",
    "ROMCache",
]