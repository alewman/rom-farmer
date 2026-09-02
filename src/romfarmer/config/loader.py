"""Configuration file loader with YAML support and validation."""

import os
from pathlib import Path
from typing import Any

import yaml

from romfarmer.core.paths import get_paths

from .models import BuildConfig, PlatformConfig


class ConfigLoader:
    """Load and validate configuration files."""

    def __init__(self, config_root: Path | None = None):
        """Initialize config loader.

        Args:
            config_root: Root directory for config files. Defaults to workspace/config.
        """
        if config_root is None:
            config_root = Path(__file__).parent.parent.parent.parent / "config"
        self.config_root = config_root
        self.workspace_root = get_paths().workspace_root

    def _load_yaml(self, path: Path) -> dict[str, Any]:
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

    def _resolve_paths(self, config: dict[str, Any]) -> dict[str, Any]:
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
                    # Resolve relative paths
                    if not path.is_absolute():
                        # These paths should resolve against workspace root, not config root
                        # 'file' for DAT configs is relative to workspace root (dats/ folder)
                        workspace_relative_keys = ["directory", "output_path", "workspace", "file"]
                        if parent_key in workspace_relative_keys:
                            path = (self.workspace_root / path).resolve()
                        else:
                            path = (self.config_root / path).resolve()
                    return path
            return obj

        return _resolve(config)

    def load_build_config(self, name: str, _seen: set | None = None) -> BuildConfig:
        """Load master build configuration with nested orchestration support.

        Args:
            name: Build config name (without .yaml extension)
            _seen: Internal set to detect circular includes

        Returns:
            Validated BuildConfig with resolved includes

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValidationError: If config is invalid
            ValueError: If circular include detected
        """
        # Detect circular includes
        if _seen is None:
            _seen = set()
        if name in _seen:
            raise ValueError(f"Circular orchestration include detected: {name}")
        _seen.add(name)

        config_path = self.config_root / "builds" / f"{name}.yaml"
        raw_config = self._load_yaml(config_path)
        resolved_config = self._resolve_paths(raw_config)

        # Process includes recursively
        includes = resolved_config.get("includes", [])
        if includes:
            # Collect platforms and overrides from all included orchestrations
            all_platforms = []
            merged_overrides = {}
            merged_settings = resolved_config.get("settings", {}).copy()
            merged_storage = resolved_config.get("storage", {}).copy()

            for include_name in includes:
                included_config = self.load_build_config(include_name, _seen.copy())

                # Add platforms (preserving order, avoiding duplicates)
                for platform in included_config.platforms:
                    if platform not in all_platforms:
                        all_platforms.append(platform)

                # Merge platform_overrides (later includes override earlier)
                if included_config.platform_overrides:
                    merged_overrides.update(included_config.platform_overrides)

                # Merge settings (parent overrides children)
                for key, value in included_config.settings.items():
                    if key not in merged_settings:
                        merged_settings[key] = value

                # Merge storage (parent overrides children)
                for key, value in included_config.storage.items():
                    if key not in merged_storage:
                        merged_storage[key] = value

            # Add this config's platforms after includes
            for platform in resolved_config.get("platforms", []):
                if platform not in all_platforms:
                    all_platforms.append(platform)

            # Parent overrides take precedence
            merged_overrides.update(resolved_config.get("platform_overrides", {}))

            # Update resolved config with merged values
            resolved_config["platforms"] = all_platforms
            resolved_config["platform_overrides"] = merged_overrides
            resolved_config["settings"] = merged_settings
            resolved_config["storage"] = merged_storage

        # Apply excludes - remove platforms from the final list
        excludes = resolved_config.get("excludes", [])
        if excludes:
            resolved_config["platforms"] = [
                p for p in resolved_config.get("platforms", []) if p not in excludes
            ]

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


def load_build_config(name: str, config_root: Path | None = None) -> BuildConfig:
    """Load build configuration (convenience function).

    Args:
        name: Build config name
        config_root: Config root directory

    Returns:
        Validated BuildConfig
    """
    loader = ConfigLoader(config_root)
    return loader.load_build_config(name)


def load_platform_config(name: str, config_root: Path | None = None) -> PlatformConfig:
    """Load platform configuration (convenience function).

    Args:
        name: Platform config name
        config_root: Config root directory

    Returns:
        Validated PlatformConfig
    """
    loader = ConfigLoader(config_root)
    return loader.load_platform_config(name)
