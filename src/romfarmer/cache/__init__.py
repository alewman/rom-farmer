"""
ROM Cache Module

Provides caching for transformed ROM files (CHD, RVZ, 7z, etc.) to avoid
redundant processing across builds. Files are stored by source hash and
can be linked to output directories to save disk space.

Also supports folder-based outputs (PS3, daphne, scummvm, etc.) via
TreeCache entries that reference TreeManifest objects in the CAS.
"""

from .config import CacheConfig, CacheLinkMode, CacheResult, CacheVerifyLevel
from .manager import CacheManager
from .models import ROMCache, TreeCache

__all__ = [
    "CacheManager",
    "CacheConfig",
    "CacheResult",
    "CacheLinkMode",
    "CacheVerifyLevel",
    "ROMCache",
    "TreeCache",
]
