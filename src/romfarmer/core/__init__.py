"""Core utilities for ROM Farmer.

This module provides foundational functionality used across the project:
- Hashing: System-aware ROM hashing for metadata matching
- Configuration: Project-wide settings
- Logging: Centralized logging configuration
- Paths: Path resolution and management
"""

from .hashing import (
    # Primary entry points
    calculate_md5,
    calculate_hash,
    hash_for_metadata_lookup,
    calculate_md5_with_auto_detect,
    
    # Strategy helpers
    get_hashing_strategy,
    is_arcade_system,
    detect_system_from_path,
    
    # Types
    HashResult,
    HashingStrategy,
    
    # Constants
    ARCADE_SYSTEMS,
    DIRECT_HASH_EXTENSIONS,
)

__all__ = [
    # Hashing functions
    "calculate_md5",
    "calculate_hash",
    "hash_for_metadata_lookup",
    "calculate_md5_with_auto_detect",
    "get_hashing_strategy",
    "is_arcade_system",
    "detect_system_from_path",
    # Hashing types
    "HashResult",
    "HashingStrategy",
    # Constants
    "ARCADE_SYSTEMS",
    "DIRECT_HASH_EXTENSIONS",
]
