"""Configuration system for ROM Groomer.

This module provides a hierarchical configuration system with:
- Master build configs (rocknix-512gb.yaml)
- Platform configs (nes.yaml, saturn.yaml)
- Target profiles (batocera, rocknix, everdrive)
- YAML loading with validation
- Path resolution and environment variable substitution
"""

from .models import (
    BuildConfig,
    PlatformConfig,
    TargetProfile,
    DATConfig,
    SourceConfig,
    ListFileConfig,
    OrganizationConfig,
    CompressionConfig,
    DATSource,
    OrganizationStyle,
    CompressionFormat,
    SystemType,
)
from .loader import ConfigLoader, load_build_config, load_platform_config

__all__ = [
    "BuildConfig",
    "PlatformConfig",
    "TargetProfile",
    "DATConfig",
    "SourceConfig",
    "ListFileConfig",
    "OrganizationConfig",
    "CompressionConfig",
    "DATSource",
    "OrganizationStyle",
    "CompressionFormat",
    "SystemType",
    "ConfigLoader",
    "load_build_config",
    "load_platform_config",
]
