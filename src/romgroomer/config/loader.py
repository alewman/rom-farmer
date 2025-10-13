"""Configuration file loader with YAML support and validation."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .models import BuildConfig, PlatformConfig


class ConfigLoader:
    """Load and validate configuration files."""

    def __init__(self, config_root: Optional[Path] = None):
        """Initialize config loader.

        Args:
            config_root: Root directory for config files. Defaults to workspace/config.
        """
        if config_root is None:
            config_root = Path(__file__).parent.parent.parent.parent / "config"
        self.config_root = config_root

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

    def _resolve_paths(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve relative paths in configuration.

        Args:
            config: Configuration dictionary

        Returns:
            Configuration with resolved paths
        """

        def _resolve(obj: Any, parent_key: str = "") -> Any:
            """Recursively resolve paths."""
            if isinstance(obj, dict):
                return {k: _resolve(v, k) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_resolve(item, parent_key) for item in obj]
            elif isinstance(obj, str):
                # Convert path-like strings to Path objects
                if parent_key in [
                    "path",
                    "file",
                    "directory",
                    "output_path",
                    "workspace",
                    "dat_directory",
                ]:
                    path = Path(obj)
                    # Resolve relative to config root if relative
                    if not path.is_absolute():
                        path = (self.config_root / path).resolve()
                    return path
            return obj

        return _resolve(config)

    def load_build_config(self, name: str) -> BuildConfig:
        """Load master build configuration.

        Args:
            name: Build config name (without .yaml extension)

        Returns:
            Validated BuildConfig

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValidationError: If config is invalid
        """
        config_path = self.config_root / "builds" / f"{name}.yaml"
        raw_config = self._load_yaml(config_path)
        resolved_config = self._resolve_paths(raw_config)

        return BuildConfig(**resolved_config)

    def load_platform_config(self, name: str) -> PlatformConfig:
        """Load platform configuration.

        Args:
            name: Platform config name (without .yaml extension)

        Returns:
            Validated PlatformConfig

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValidationError: If config is invalid
        """
        config_path = self.config_root / "platforms" / f"{name}.yaml"
        raw_config = self._load_yaml(config_path)
        resolved_config = self._resolve_paths(raw_config)

        return PlatformConfig(**resolved_config)

    def load_platform_configs(self, platform_names: list[str]) -> list[PlatformConfig]:
        """Load multiple platform configurations.

        Args:
            platform_names: List of platform config names

        Returns:
            List of validated PlatformConfig objects
        """
        return [self.load_platform_config(name) for name in platform_names]


def load_build_config(name: str, config_root: Optional[Path] = None) -> BuildConfig:
    """Load build configuration (convenience function).

    Args:
        name: Build config name
        config_root: Config root directory

    Returns:
        Validated BuildConfig
    """
    loader = ConfigLoader(config_root)
    return loader.load_build_config(name)


def load_platform_config(
    name: str, config_root: Optional[Path] = None
) -> PlatformConfig:
    """Load platform configuration (convenience function).

    Args:
        name: Platform config name
        config_root: Config root directory

    Returns:
        Validated PlatformConfig
    """
    loader = ConfigLoader(config_root)
    return loader.load_platform_config(name)
