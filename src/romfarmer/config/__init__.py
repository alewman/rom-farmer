"""Configuration system for ROM Farmer.

This module provides a hierarchical configuration system with:
- Master build configs (rocknix-512gb.yaml)
- Platform configs (nes.yaml, saturn.yaml)
- Frontend configs (batocera.yaml, rocknix.yaml) - NEW
- Device configs (pc.yaml, r36s.yaml) - NEW
- Target configs (batocera-pc.yaml, rocknix-r36s.yaml) - NEW
- Platform tiers config (platform_tiers.yaml) - NEW
- YAML loading with validation
- Path resolution and environment variable substitution
"""

from .models import (
    BuildConfig,
    BuildType,
    PlatformConfig,
    TargetProfile,
    DATConfig,
    SourceConfig,
    ListFileConfig,
    OrganizationConfig,
    CompressionConfig,
    ExtractionConfig,
    ExtractionType,
    DATSource,
    OrganizationStyle,
    CompressionFormat,
    SystemType,
    # Tier system models
    PlatformTiersConfig,
    TierDefinition,
    TierStrategy,
    AllocationRules,
    StorageProfile,
)
from .loader import ConfigLoader, load_build_config, load_platform_config

# New target capabilities system
from .frontend import FrontendConfig, FrontendPlatformConfig, FrontendDefaults, MediaType
from .device import DeviceConfig, DisplayConfig, MediaSizingConfig
from .target import TargetConfig, TargetOverrides, ComposedTarget
from .target_loader import (
    TargetConfigLoader,
    load_frontend,
    load_device,
    load_target,
    load_composed_target,
    list_frontends,
    list_devices,
    list_targets,
)
from .tiers_loader import load_platform_tiers

__all__ = [
    # Build and platform models
    "BuildConfig",
    "BuildType",
    "PlatformConfig",
    "TargetProfile",
    "DATConfig",
    "SourceConfig",
    "ListFileConfig",
    "OrganizationConfig",
    "CompressionConfig",
    "ExtractionConfig",
    "ExtractionType",
    "DATSource",
    "OrganizationStyle",
    "CompressionFormat",
    "SystemType",
    "ConfigLoader",
    "load_build_config",
    "load_platform_config",
    # Tier system models
    "PlatformTiersConfig",
    "TierDefinition",
    "TierStrategy",
    "AllocationRules",
    "StorageProfile",
    "load_platform_tiers",
    # Frontend models
    "FrontendConfig",
    "FrontendPlatformConfig",
    "FrontendDefaults",
    "MediaType",
    # Device models
    "DeviceConfig",
    "DisplayConfig",
    "MediaSizingConfig",
    # Target models
    "TargetConfig",
    "TargetOverrides",
    "ComposedTarget",
    # Target loaders
    "TargetConfigLoader",
    "load_frontend",
    "load_device",
    "load_target",
    "load_composed_target",
    "list_frontends",
    "list_devices",
    "list_targets",
]
