"""Farm-Hand target configuration loader.

Reads YAML connection profiles from config/farmhand/targets/ and
manages scan profiles in config/farmhand/profiles/.

Target configs (YAML) contain:
  - Connection details (host, port, user, password/key)
  - System identity (frontend, device, target build config)
  - Volume hints (pinned platforms, reserve space)

Scan profiles (JSON) contain:
  - Full TargetProfile from the analyzer
  - Auto-populated on each scan; stale data gets refreshed
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

import yaml

from romfarmer.farmhand.models import TargetProfile, VolumeRole

logger = logging.getLogger(__name__)


class TargetConfigError(Exception):
    """Invalid target configuration."""


def get_farmhand_config_dir(workspace_root: Path) -> Path:
    """Return the farmhand config root (config/farmhand/)."""
    return workspace_root / "config" / "farmhand"


def get_targets_dir(workspace_root: Path) -> Path:
    """Return the targets config directory."""
    return get_farmhand_config_dir(workspace_root) / "targets"


def get_profiles_dir(workspace_root: Path) -> Path:
    """Return the scan profiles directory."""
    return get_farmhand_config_dir(workspace_root) / "profiles"


# ---------------------------------------------------------------------------
# Target config loading (YAML)
# ---------------------------------------------------------------------------


def list_targets(workspace_root: Path) -> list[str]:
    """List available target config names (without extension)."""
    targets_dir = get_targets_dir(workspace_root)
    if not targets_dir.exists():
        return []
    return sorted(
        p.stem for p in targets_dir.glob("*.yaml")
        if not p.name.startswith(".")
    )


def load_target_config(workspace_root: Path, name: str) -> dict[str, Any]:
    """Load a target config YAML by name.

    Args:
        workspace_root: Project root path.
        name: Target name (e.g., "batocera-nuc") — matches filename without .yaml.

    Returns:
        Parsed YAML as dict.

    Raises:
        TargetConfigError: If config doesn't exist or is invalid.
    """
    config_path = get_targets_dir(workspace_root) / f"{name}.yaml"
    if not config_path.exists():
        available = list_targets(workspace_root)
        raise TargetConfigError(
            f"Target config '{name}' not found at {config_path}. "
            f"Available targets: {available or 'none'}"
        )

    try:
        data = yaml.safe_load(config_path.read_text())
    except yaml.YAMLError as exc:
        raise TargetConfigError(f"Invalid YAML in {config_path}: {exc}") from exc

    if not isinstance(data, dict):
        raise TargetConfigError(f"Target config must be a YAML mapping, got {type(data)}")

    # Validate required fields
    for field in ("name", "host"):
        if field not in data:
            raise TargetConfigError(f"Target config missing required field: {field}")

    return data


def target_config_to_ssh_kwargs(config: dict[str, Any]) -> dict[str, Any]:
    """Extract SSH connection kwargs from a target config dict.

    Returns dict suitable for SSHClient(**kwargs).
    """
    kwargs: dict[str, Any] = {
        "host": config["host"],
        "port": config.get("port", 22),
        "user": config.get("user", "root"),
    }
    if config.get("password"):
        kwargs["password"] = config["password"]
    if config.get("key_file"):
        kwargs["key_file"] = config["key_file"]
    return kwargs


# ---------------------------------------------------------------------------
# Profile persistence (JSON)
# ---------------------------------------------------------------------------


def save_profile(workspace_root: Path, profile: TargetProfile) -> Path:
    """Save a TargetProfile to the profiles directory as JSON.

    Returns the path where it was saved.
    """
    profiles_dir = get_profiles_dir(workspace_root)
    profiles_dir.mkdir(parents=True, exist_ok=True)

    profile_path = profiles_dir / f"{profile.name}.json"
    profile_path.write_text(profile.model_dump_json(indent=2))
    logger.info("Saved profile to %s", profile_path)
    return profile_path


def load_profile(workspace_root: Path, name: str) -> Optional[TargetProfile]:
    """Load a saved scan profile by target name.

    Returns None if not found.
    """
    profile_path = get_profiles_dir(workspace_root) / f"{name}.json"
    if not profile_path.exists():
        # Also check legacy location (config/farmhand/<name>.json)
        legacy_path = get_farmhand_config_dir(workspace_root) / f"{name}.json"
        if legacy_path.exists():
            profile_path = legacy_path
        else:
            return None

    try:
        data = json.loads(profile_path.read_text())
        return TargetProfile.model_validate(data)
    except Exception as exc:
        logger.warning("Failed to load profile %s: %s", profile_path, exc)
        return None


def list_profiles(workspace_root: Path) -> list[str]:
    """List available scan profile names."""
    profiles_dir = get_profiles_dir(workspace_root)
    names = []
    if profiles_dir.exists():
        names.extend(p.stem for p in profiles_dir.glob("*.json"))
    # Also check legacy location
    legacy_dir = get_farmhand_config_dir(workspace_root)
    if legacy_dir.exists():
        names.extend(
            p.stem for p in legacy_dir.glob("*.json")
            if p.stem not in names
        )
    return sorted(names)
