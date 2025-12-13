"""Target, Frontend, and Device configuration loaders.

This module provides functions to load and compose target configurations
from their constituent frontend and device configs.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .frontend import FrontendConfig, FrontendPlatformConfig, FrontendDefaults, MediaType
from .device import DeviceConfig, DisplayConfig, MediaSizingConfig
from .target import TargetConfig, TargetOverrides, ComposedTarget


class TargetConfigLoader:
    """Load and compose target configurations."""

    def __init__(self, config_root: Optional[Path] = None):
        """Initialize target config loader.

        Args:
            config_root: Root directory for config files. Defaults to workspace/config.
        """
        if config_root is None:
            config_root = Path(__file__).parent.parent.parent.parent / "config"
        self.config_root = config_root
        
        # Cache loaded configs to avoid reloading
        self._frontend_cache: Dict[str, FrontendConfig] = {}
        self._device_cache: Dict[str, DeviceConfig] = {}
        self._target_cache: Dict[str, TargetConfig] = {}

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML file with environment variable substitution.

        Args:
            path: Path to YAML file

        Returns:
            Parsed YAML as dictionary

        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path) as f:
            content = f.read()

        # Substitute environment variables
        content = os.path.expandvars(content)

        return yaml.safe_load(content)

    def load_frontend(self, name: str) -> FrontendConfig:
        """Load a frontend configuration.

        Args:
            name: Frontend name (e.g., 'batocera', 'rocknix')

        Returns:
            Validated FrontendConfig

        Raises:
            FileNotFoundError: If frontend config doesn't exist
            ValidationError: If config is invalid
        """
        # Check cache first
        if name in self._frontend_cache:
            return self._frontend_cache[name]

        config_path = self.config_root / "frontends" / f"{name}.yaml"
        raw_config = self._load_yaml(config_path)

        # Parse media_support as MediaType enum values
        if 'media_support' in raw_config:
            raw_config['media_support'] = [
                MediaType(m) if isinstance(m, str) else m
                for m in raw_config['media_support']
            ]

        # Parse platform configs
        if 'platforms' in raw_config:
            platforms = {}
            for platform_name, platform_data in raw_config['platforms'].items():
                platforms[platform_name] = FrontendPlatformConfig(**platform_data)
            raw_config['platforms'] = platforms

        # Parse defaults
        if 'defaults' in raw_config:
            raw_config['defaults'] = FrontendDefaults(**raw_config['defaults'])

        frontend = FrontendConfig(**raw_config)
        self._frontend_cache[name] = frontend
        return frontend

    def load_device(self, name: str) -> DeviceConfig:
        """Load a device configuration.

        Args:
            name: Device name (e.g., 'pc', 'r36s', 'steamdeck')

        Returns:
            Validated DeviceConfig

        Raises:
            FileNotFoundError: If device config doesn't exist
            ValidationError: If config is invalid
        """
        # Check cache first
        if name in self._device_cache:
            return self._device_cache[name]

        config_path = self.config_root / "devices" / f"{name}.yaml"
        raw_config = self._load_yaml(config_path)

        # Parse nested configs
        if 'display' in raw_config:
            raw_config['display'] = DisplayConfig(**raw_config['display'])
        
        if 'media_sizing' in raw_config:
            raw_config['media_sizing'] = MediaSizingConfig(**raw_config['media_sizing'])

        device = DeviceConfig(**raw_config)
        self._device_cache[name] = device
        return device

    def load_target(self, name: str) -> TargetConfig:
        """Load a target configuration (without composing frontend/device).

        Args:
            name: Target name (e.g., 'rocknix-r36s', 'batocera-pc')

        Returns:
            Validated TargetConfig

        Raises:
            FileNotFoundError: If target config doesn't exist
            ValidationError: If config is invalid
        """
        # Check cache first
        if name in self._target_cache:
            return self._target_cache[name]

        config_path = self.config_root / "targets" / f"{name}.yaml"
        raw_config = self._load_yaml(config_path)

        # Parse overrides
        if 'overrides' in raw_config:
            raw_config['overrides'] = TargetOverrides(**raw_config['overrides'])

        target = TargetConfig(**raw_config)
        self._target_cache[name] = target
        return target

    def load_composed_target(self, name: str) -> ComposedTarget:
        """Load and compose a target with its frontend and device configs.

        This is the main entry point for getting a fully resolved target
        configuration that can be used for builds.

        Args:
            name: Target name (e.g., 'rocknix-r36s', 'batocera-pc')

        Returns:
            ComposedTarget with frontend and device loaded

        Raises:
            FileNotFoundError: If any config doesn't exist
            ValidationError: If any config is invalid
        """
        # Load the target config
        target_config = self.load_target(name)

        # Load referenced frontend and device
        frontend = self.load_frontend(target_config.frontend)
        device = self.load_device(target_config.device)

        # Compose into a ComposedTarget
        return ComposedTarget(
            name=target_config.name,
            description=target_config.description,
            frontend=frontend,
            device=device,
            target_config=target_config
        )

    def list_frontends(self) -> List[str]:
        """List all available frontend configurations.

        Returns:
            List of frontend names (without .yaml extension)
        """
        frontends_dir = self.config_root / "frontends"
        if not frontends_dir.exists():
            return []
        return sorted([
            f.stem for f in frontends_dir.glob("*.yaml")
        ])

    def list_devices(self) -> List[str]:
        """List all available device configurations.

        Returns:
            List of device names (without .yaml extension)
        """
        devices_dir = self.config_root / "devices"
        if not devices_dir.exists():
            return []
        return sorted([
            f.stem for f in devices_dir.glob("*.yaml")
        ])

    def list_targets(self) -> List[str]:
        """List all available target configurations.

        Returns:
            List of target names (without .yaml extension)
        """
        targets_dir = self.config_root / "targets"
        if not targets_dir.exists():
            return []
        return sorted([
            f.stem for f in targets_dir.glob("*.yaml")
        ])

    def clear_cache(self):
        """Clear all cached configurations."""
        self._frontend_cache.clear()
        self._device_cache.clear()
        self._target_cache.clear()


# Convenience functions for direct usage

def load_frontend(name: str, config_root: Optional[Path] = None) -> FrontendConfig:
    """Load frontend configuration (convenience function).

    Args:
        name: Frontend name
        config_root: Config root directory

    Returns:
        Validated FrontendConfig
    """
    loader = TargetConfigLoader(config_root)
    return loader.load_frontend(name)


def load_device(name: str, config_root: Optional[Path] = None) -> DeviceConfig:
    """Load device configuration (convenience function).

    Args:
        name: Device name
        config_root: Config root directory

    Returns:
        Validated DeviceConfig
    """
    loader = TargetConfigLoader(config_root)
    return loader.load_device(name)


def load_target(name: str, config_root: Optional[Path] = None) -> TargetConfig:
    """Load target configuration without composition (convenience function).

    Args:
        name: Target name
        config_root: Config root directory

    Returns:
        Validated TargetConfig
    """
    loader = TargetConfigLoader(config_root)
    return loader.load_target(name)


def load_composed_target(name: str, config_root: Optional[Path] = None) -> ComposedTarget:
    """Load and compose target configuration (convenience function).

    This is the main function to use when you need a fully resolved
    target configuration.

    Args:
        name: Target name
        config_root: Config root directory

    Returns:
        ComposedTarget with frontend and device loaded
    """
    loader = TargetConfigLoader(config_root)
    return loader.load_composed_target(name)


def list_frontends(config_root: Optional[Path] = None) -> List[str]:
    """List available frontends (convenience function)."""
    loader = TargetConfigLoader(config_root)
    return loader.list_frontends()


def list_devices(config_root: Optional[Path] = None) -> List[str]:
    """List available devices (convenience function)."""
    loader = TargetConfigLoader(config_root)
    return loader.list_devices()


def list_targets(config_root: Optional[Path] = None) -> List[str]:
    """List available targets (convenience function)."""
    loader = TargetConfigLoader(config_root)
    return loader.list_targets()
