"""
Centralized path resolution for ROM Farmer.

This module provides a single source of truth for all path resolution,
eliminating hardcoded paths throughout the codebase. Paths can be configured
via environment variables, configuration files, or defaults.

Usage:
    from romfarmer.core.paths import paths
    
    # Access paths
    db_path = paths.metadata_db
    temp_dir = paths.temp_dir
    
    # Or create custom resolver with different workspace
    custom_paths = PathResolver(workspace_root=Path("/custom/workspace"))
"""

import os
from functools import cached_property
from pathlib import Path
from typing import Optional

import yaml


class PathResolver:
    """
    Resolve and manage paths consistently across the application.
    
    Paths are resolved in the following priority order:
    1. Environment variables (ROMGROOMER_*)
    2. Configuration file (romfarmer.yaml or .romfarmer.yaml)
    3. Sensible defaults relative to workspace root
    
    Attributes:
        workspace_root: The root directory of the ROM Farmer workspace
    """
    
    # Environment variable prefix
    ENV_PREFIX = "ROMGROOMER"
    
    # Default subdirectory names
    DEFAULTS = {
        "config_dir": "config",
        "logs_dir": "logs",
        "state_dir": "state",
        "temp_dir": "temp",
        "output_dir": "output",
        "metadata_dir": "metadata/database",
        "dats_dir": "dats",
        "lists_dir": "lists",
        "scripts_dir": "scripts",
    }
    
    def __init__(
        self,
        workspace_root: Optional[Path] = None,
        config_file: Optional[Path] = None,
    ):
        """
        Initialize path resolver.
        
        Args:
            workspace_root: Root directory for the workspace. If not provided,
                           uses ROMGROOMER_WORKSPACE env var or auto-detects.
            config_file: Optional path to configuration file with path overrides.
        """
        self._workspace_root = workspace_root or self._detect_workspace_root()
        self._config = self._load_config(config_file)
        self._env_overrides = self._load_env_overrides()
    
    def _detect_workspace_root(self) -> Path:
        """
        Auto-detect workspace root directory.
        
        Checks in order:
        1. ROMGROOMER_WORKSPACE environment variable
        2. Current working directory if it contains pyproject.toml
        3. Parent directories looking for pyproject.toml
        4. Falls back to current directory
        """
        # Check environment variable
        env_workspace = os.environ.get(f"{self.ENV_PREFIX}_WORKSPACE")
        if env_workspace:
            return Path(env_workspace)
        
        # Check current directory
        cwd = Path.cwd()
        if (cwd / "pyproject.toml").exists():
            return cwd
        
        # Walk up looking for pyproject.toml
        for parent in cwd.parents:
            if (parent / "pyproject.toml").exists():
                return parent
            # Don't go above home directory
            if parent == Path.home():
                break
        
        # Default to current directory
        return cwd
    
    def _load_config(self, config_file: Optional[Path]) -> dict:
        """Load configuration from file if present."""
        if config_file and config_file.exists():
            with open(config_file) as f:
                return yaml.safe_load(f) or {}
        
        # Try standard locations
        for name in ["romfarmer.yaml", ".romfarmer.yaml"]:
            config_path = self._workspace_root / name
            if config_path.exists():
                with open(config_path) as f:
                    return yaml.safe_load(f) or {}
        
        return {}
    
    def _load_env_overrides(self) -> dict:
        """Load path overrides from environment variables."""
        overrides = {}
        for key in self.DEFAULTS:
            env_key = f"{self.ENV_PREFIX}_{key.upper()}"
            value = os.environ.get(env_key)
            if value:
                overrides[key] = Path(value)
        return overrides
    
    def _resolve_path(self, key: str, default_subdir: str) -> Path:
        """
        Resolve a path using the priority chain.
        
        Priority: env var > config file > default
        """
        # Check environment override
        if key in self._env_overrides:
            return self._env_overrides[key]
        
        # Check config file
        paths_config = self._config.get("paths", {})
        if key in paths_config:
            path = Path(paths_config[key])
            if path.is_absolute():
                return path
            return self._workspace_root / path
        
        # Use default
        return self._workspace_root / default_subdir
    
    # -------------------------------------------------------------------------
    # Core Directories
    # -------------------------------------------------------------------------
    
    @property
    def workspace_root(self) -> Path:
        """Root directory of the ROM Farmer workspace."""
        return self._workspace_root
    
    @cached_property
    def config_dir(self) -> Path:
        """Directory containing configuration files."""
        return self._resolve_path("config_dir", self.DEFAULTS["config_dir"])
    
    @cached_property
    def logs_dir(self) -> Path:
        """Directory for log files."""
        path = self._resolve_path("logs_dir", self.DEFAULTS["logs_dir"])
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @cached_property
    def state_dir(self) -> Path:
        """Directory for build state files (resume capability)."""
        path = self._resolve_path("state_dir", self.DEFAULTS["state_dir"])
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @cached_property
    def temp_dir(self) -> Path:
        """Directory for temporary working files."""
        path = self._resolve_path("temp_dir", self.DEFAULTS["temp_dir"])
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @cached_property
    def output_dir(self) -> Path:
        """Default directory for build outputs."""
        path = self._resolve_path("output_dir", self.DEFAULTS["output_dir"])
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @cached_property
    def metadata_dir(self) -> Path:
        """Directory for metadata database."""
        path = self._resolve_path("metadata_dir", self.DEFAULTS["metadata_dir"])
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @cached_property
    def dats_dir(self) -> Path:
        """Directory containing DAT files."""
        return self._resolve_path("dats_dir", self.DEFAULTS["dats_dir"])
    
    @cached_property
    def lists_dir(self) -> Path:
        """Directory containing list files (delete, add, etc.)."""
        return self._resolve_path("lists_dir", self.DEFAULTS["lists_dir"])
    
    @cached_property
    def scripts_dir(self) -> Path:
        """Directory for utility scripts."""
        return self._resolve_path("scripts_dir", self.DEFAULTS["scripts_dir"])
    
    # -------------------------------------------------------------------------
    # Specific Files
    # -------------------------------------------------------------------------
    
    @cached_property
    def metadata_db(self) -> Path:
        """Path to the metadata SQLite database."""
        return self.metadata_dir / "romfarmer.db"
    
    # -------------------------------------------------------------------------
    # Config Subdirectories
    # -------------------------------------------------------------------------
    
    @cached_property
    def platforms_dir(self) -> Path:
        """Directory containing platform configuration files."""
        return self.config_dir / "platforms"
    
    @cached_property
    def builds_dir(self) -> Path:
        """Directory containing build configuration files."""
        return self.config_dir / "builds"
    
    @cached_property
    def selections_dir(self) -> Path:
        """Directory containing selection preset files."""
        return self.config_dir / "selections"
    
    @cached_property
    def sources_file(self) -> Path:
        """Path to sources.yaml file."""
        return self.config_dir / "sources.yaml"
    
    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------
    
    def build_state_file(self, build_name: str) -> Path:
        """Get path to build state file for a specific build."""
        return self.state_dir / f".build_state_{build_name}.yaml"
    
    def build_log_file(self, build_name: str) -> Path:
        """Get path to build log file for a specific build."""
        return self.logs_dir / f"build_{build_name}.log"
    
    def build_report_file(self, build_name: str) -> Path:
        """Get path to build report file for a specific build."""
        return self.logs_dir / f"build_report_{build_name}.txt"
    
    def platform_config_file(self, platform_name: str) -> Path:
        """Get path to platform configuration file."""
        return self.platforms_dir / f"{platform_name}.yaml"
    
    def build_config_file(self, build_name: str) -> Path:
        """Get path to build configuration file."""
        return self.builds_dir / f"{build_name}.yaml"
    
    def platform_temp_dir(self, platform_name: str) -> Path:
        """Get temporary directory for a specific platform."""
        path = self.temp_dir / platform_name
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def platform_output_dir(
        self,
        platform_name: str,
        target_name: str,
        dat_variant: str = "1g1r-eng",
        compression_format: str = "7z"
    ) -> Path:
        """
        Generate output directory path following naming convention.
        
        Pattern: {output_dir}/{dat_variant}-{format}-{target}/{platform}
        Example: /output/1g1r-eng-7z-batocera/nes
        """
        folder_name = f"{dat_variant}-{compression_format}-{target_name}"
        path = self.output_dir / folder_name / platform_name
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def ensure_dirs(self) -> None:
        """Ensure all required directories exist."""
        for attr in ["logs_dir", "state_dir", "temp_dir", "output_dir", "metadata_dir"]:
            getattr(self, attr)  # Access triggers creation via cached_property
    
    def __repr__(self) -> str:
        return f"PathResolver(workspace_root={self._workspace_root})"


# -----------------------------------------------------------------------------
# Module-level singleton for convenience
# -----------------------------------------------------------------------------

# Lazy initialization - will be created on first access
_paths: Optional[PathResolver] = None


def get_paths() -> PathResolver:
    """
    Get the global PathResolver instance.
    
    Creates the instance on first call. For custom configuration,
    use init_paths() before accessing.
    """
    global _paths
    if _paths is None:
        _paths = PathResolver()
    return _paths


def init_paths(
    workspace_root: Optional[Path] = None,
    config_file: Optional[Path] = None,
) -> PathResolver:
    """
    Initialize the global PathResolver with custom settings.
    
    Call this at application startup if you need non-default paths.
    
    Args:
        workspace_root: Custom workspace root directory
        config_file: Custom configuration file path
    
    Returns:
        The initialized PathResolver instance
    """
    global _paths
    _paths = PathResolver(workspace_root=workspace_root, config_file=config_file)
    return _paths


# Convenience alias
paths = property(lambda self: get_paths())


# For direct attribute access without calling get_paths()
class _PathsProxy:
    """Proxy class for convenient attribute access to paths."""
    
    def __getattr__(self, name):
        return getattr(get_paths(), name)


# Export a proxy object for direct access
paths = _PathsProxy()
