"""Configuration system for ROM Farmer.

This module provides a hierarchical configuration system with:
- Master build configs (rocknix-512gb.yaml)
- Platform configs (nes.yaml, saturn.yaml)
- Frontend configs (batocera.yaml, rocknix.yaml) - NEW
- Device configs (pc.yaml, r36s.yaml) - NEW
- Target configs (batocera-pc.yaml, rocknix-r36s.yaml) - NEW
- Platform tiers config (platform_tiers.yaml) - NEW
- Generation configs (generations.yaml) - NEW (1G1Gen cross-platform dedup)
- YAML loading with validation
- Path resolution and environment variable substitution
"""

from .device import DeviceConfig, DisplayConfig, MediaSizingConfig

# New target capabilities system
from .frontend import FrontendConfig, FrontendDefaults, FrontendPlatformConfig, MediaType
from .loader import ConfigLoader, load_build_config, load_platform_config
from .models import (
    AllocationRules,
    BuildConfig,
    BuildType,
    CompressionConfig,
    CompressionFormat,
    DATConfig,
    DATSource,
    ExtractionConfig,
    ExtractionType,
    GenerationFilterConfig,
    ListFileConfig,
    OrganizationConfig,
    OrganizationStyle,
    PlatformConfig,
    # Tier system models
    PlatformTiersConfig,
    SourceConfig,
    StorageProfile,
    SystemType,
    TargetProfile,
    TierDefinition,
    TierStrategy,
)
from .target import ComposedTarget, TargetConfig, TargetOverrides
from .target_loader import (
    TargetConfigLoader,
    list_devices,
    list_frontends,
    list_targets,
    load_composed_target,
    load_device,
    load_frontend,
    load_target,
)
from .tiers_loader import load_platform_tiers

__all__ = [
    # Build and platform models
    "BuildConfig",
    "BuildType",
    "GenerationFilterConfig",
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
