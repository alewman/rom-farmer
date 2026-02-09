"""Smart build loader — auto-detects old vs new build format.

Tries to load a build config as the new BuildSpec format first. If the
config is in old format (has 'includes' or 'platform_overrides' keys),
falls back to the old BuildOrchestrator.

This allows gradual migration: old builds keep working while new builds
use the declarative engine.
"""

import logging
from pathlib import Path
from typing import Optional, Union

import yaml

from romfarmer.core.paths import get_paths


logger = logging.getLogger(__name__)


def load_orchestrator(
    build_name: str,
    config_root: Optional[Path] = None,
) -> Union["NewBuildOrchestrator", "BuildOrchestrator"]:
    """Load the appropriate orchestrator for a build config.

    Detects format by inspecting the YAML:
    - If 'recipes' key is present → new format → NewBuildOrchestrator
    - Otherwise → old format → BuildOrchestrator

    Also searches config/builds/new/ for new-format configs.

    Args:
        build_name: Build config name (without .yaml)
        config_root: Config root directory (default: auto-detect)

    Returns:
        Either a NewBuildOrchestrator or legacy BuildOrchestrator
    """
    if config_root is None:
        config_root = get_paths().workspace_root / "config"

    # Search for the build config in both old and new locations
    candidates = [
        config_root / "builds" / "new" / f"{build_name}.yaml",
        config_root / "builds" / f"{build_name}.yaml",
    ]

    config_path = None
    for candidate in candidates:
        if candidate.exists():
            config_path = candidate
            break

    if config_path is None:
        raise FileNotFoundError(
            f"Build config not found: {build_name}\n"
            f"Searched: {', '.join(str(c) for c in candidates)}"
        )

    # Peek at the YAML to detect format
    with open(config_path) as f:
        raw = yaml.safe_load(f)

    if _is_new_format(raw):
        logger.info(f"Loading new-format build: {build_name} ({config_path})")
        from romfarmer.new_orchestrator import NewBuildOrchestrator
        return NewBuildOrchestrator.from_config(build_name, config_root)
    else:
        logger.info(f"Loading legacy-format build: {build_name}")
        from romfarmer.build_orchestrator import BuildOrchestrator
        return BuildOrchestrator.from_config(build_name)


def _is_new_format(raw: dict) -> bool:
    """Detect whether a build config is new format.

    New format has:
    - 'recipes' key (required)
    - 'target' key (required)
    - No 'includes', 'platform_overrides', or 'storage' (dict) keys

    Old format has:
    - 'includes' key (meta-orchestration)
    - 'platform_overrides' key (per-platform overrides)
    - 'storage' key as dict with 'output_base', 'temp_path'
    - 'settings' key
    """
    if "recipes" in raw:
        return True
    if "includes" in raw or "platform_overrides" in raw:
        return False
    # Ambiguous — treat as old format for safety
    return False


def detect_build_format(build_name: str) -> str:
    """Detect the format of a build config.

    Returns:
        'new' or 'legacy'
    """
    config_root = get_paths().workspace_root / "config"

    candidates = [
        config_root / "builds" / "new" / f"{build_name}.yaml",
        config_root / "builds" / f"{build_name}.yaml",
    ]

    for candidate in candidates:
        if candidate.exists():
            with open(candidate) as f:
                raw = yaml.safe_load(f)
            return "new" if _is_new_format(raw) else "legacy"

    return "unknown"
