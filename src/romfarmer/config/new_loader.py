"""Loaders for the new declarative config types.

Provides functions to load:
- SlimPlatformConfig from config/platforms/ (slim format)
- RecipeSpec from config/recipes/
- BuildSpec from config/builds/ (new format)
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .slim_platform import (
    ArcadeFilter,
    DATReference,
    ListPatterns,
    PS3Config,
    SlimPlatformConfig,
    XboxConfig,
)
from .recipe import RecipeSpec
from .build_spec import BuildSpec, DeployConfig, PostBuildHook
from .models import (
    DATSource,
    ExtractionType,
    SelectionConfig,
    SourceConfig,
)
from romfarmer.core.paths import get_paths


def _load_yaml(path: Path) -> Dict[str, Any]:
    """Load YAML file with environment variable substitution."""
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    
    with open(path) as f:
        content = f.read()
    
    content = os.path.expandvars(content)
    return yaml.safe_load(content)


# ═══════════════════════════════════════════════════════════════════════════════
# Slim Platform Loader
# ═══════════════════════════════════════════════════════════════════════════════

def load_slim_platform(
    name: str,
    config_root: Optional[Path] = None,
) -> SlimPlatformConfig:
    """Load a slim platform config from YAML.
    
    Supports both the new slim format AND the old fat format (for migration).
    When loading an old format, strips non-intrinsic fields automatically.
    
    Args:
        name: Platform name (without .yaml)
        config_root: Config root directory (default: auto-detect)
        
    Returns:
        SlimPlatformConfig with intrinsic facts only
    """
    if config_root is None:
        config_root = Path(__file__).parent.parent.parent.parent / "config"
    
    config_path = config_root / "platforms" / f"{name}.yaml"
    raw = _load_yaml(config_path)
    
    # Detect format: if 'targets' key exists, it's the old fat format
    if "targets" in raw:
        return _convert_fat_to_slim(raw)
    
    # New slim format — parse directly
    return _parse_slim_platform(raw)


def _parse_slim_platform(raw: Dict[str, Any]) -> SlimPlatformConfig:
    """Parse a new-format slim platform YAML."""
    
    # Parse DAT reference
    dat_data = raw.get("dat", {})
    if isinstance(dat_data.get("source"), str):
        dat_data["source"] = DATSource(dat_data["source"])
    if "file" in dat_data and dat_data["file"] is not None:
        dat_data["file"] = Path(dat_data["file"])
    dat = DATReference(**dat_data)
    
    # Parse sources
    sources = _parse_sources(raw.get("sources", []))
    chd_sources = _parse_sources(raw.get("chd_sources", [])) if "chd_sources" in raw else None
    
    # Parse extraction type
    extraction = ExtractionType.NONE
    if "extraction" in raw:
        ext = raw["extraction"]
        if isinstance(ext, str):
            extraction = ExtractionType(ext)
        elif isinstance(ext, dict):
            extraction = ExtractionType(ext.get("type", "none"))
    
    # Parse list patterns
    list_patterns = None
    if "list_patterns" in raw:
        list_patterns = ListPatterns(**raw["list_patterns"])
    
    # Parse arcade filter
    arcade_filter = None
    if "arcade_filter" in raw:
        arcade_filter = ArcadeFilter(**raw["arcade_filter"])
    
    # Parse PS3 config
    ps3 = None
    if "ps3" in raw:
        ps3_data = dict(raw["ps3"])
        for path_field in ["keys_directory", "ps3dec_path", "nps_database", "pkg_archive"]:
            if path_field in ps3_data and ps3_data[path_field] is not None:
                ps3_data[path_field] = Path(ps3_data[path_field])
        ps3 = PS3Config(**ps3_data)
    
    # Parse Xbox config
    xbox = None
    if "xbox" in raw:
        xbox_data = dict(raw["xbox"])
        if "extract_xiso_path" in xbox_data and xbox_data["extract_xiso_path"] is not None:
            xbox_data["extract_xiso_path"] = Path(xbox_data["extract_xiso_path"])
        xbox = XboxConfig(**xbox_data)
    
    # Parse samples sources
    samples_sources = None
    if "samples_sources" in raw:
        samples_sources = _parse_sources(raw["samples_sources"])
    elif "samples" in raw:
        # Legacy: 'samples' key
        samples_sources = _parse_sources(raw["samples"])
    
    return SlimPlatformConfig(
        name=raw["name"],
        display_name=raw.get("display_name"),
        type=raw.get("type"),
        emulator=raw.get("emulator"),
        metadata_system=raw.get("metadata_system"),
        dat=dat,
        sources=sources,
        chd_sources=chd_sources,
        extraction=extraction,
        multi_disc=raw.get("multi_disc", raw.get("multi_disc_handling", False)),
        list_patterns=list_patterns,
        arcade_filter=arcade_filter,
        bios=raw.get("bios"),
        samples_sources=samples_sources,
        ps3=ps3,
        xbox=xbox,
    )


def _convert_fat_to_slim(raw: Dict[str, Any]) -> SlimPlatformConfig:
    """Convert an old-format (fat) platform config to slim.
    
    This is the backward compatibility shim. It reads the full old format
    and extracts only the intrinsic fields.
    """
    # Parse DAT reference from old format
    dat_data = raw.get("dat", {})
    if isinstance(dat_data.get("source"), str):
        dat_data["source"] = DATSource(dat_data["source"])
    if "file" in dat_data and dat_data["file"] is not None:
        dat_data["file"] = Path(dat_data["file"])
    dat = DATReference(
        source=dat_data.get("source", DATSource.RETOOL_1G1R_ENG),
        file=dat_data.get("file"),
        expected_count=dat_data.get("expected_count"),
        match_method=dat_data.get("match_method", "hash"),
        version=dat_data.get("version"),
        filter_driver=dat_data.get("filter_driver"),
        filter_romof=dat_data.get("filter_romof"),
        exclude_romof=dat_data.get("exclude_romof"),
        name_pattern=dat_data.get("name_pattern"),
        exclude_name_pattern=dat_data.get("exclude_name_pattern"),
    )
    
    # Parse sources
    sources = _parse_sources(raw.get("sources", []))
    chd_sources = _parse_sources(raw.get("chd_sources", [])) if "chd_sources" in raw else None
    
    # Parse extraction type from old nested format
    extraction = ExtractionType.NONE
    ext_data = raw.get("extraction", {})
    if isinstance(ext_data, dict):
        if ext_data.get("enabled", False) and ext_data.get("type"):
            extraction = ExtractionType(ext_data["type"])
        elif not ext_data.get("enabled", True) and ext_data.get("type", "none") == "none":
            extraction = ExtractionType.NONE
    
    # Convert old lists format to new list_patterns
    list_patterns = None
    lists_data = raw.get("lists", {})
    if lists_data and isinstance(lists_data, dict):
        patterns = lists_data.get("patterns", {})
        if patterns:
            list_patterns = ListPatterns(
                delete=patterns.get("delete"),
                add_myrient=patterns.get("add_myrient"),
                add_extra=patterns.get("add_extra"),
                add=patterns.get("add"),
            )
    
    # Parse arcade filter
    arcade_filter = None
    if "arcade_filter" in raw:
        arcade_filter = ArcadeFilter(**raw["arcade_filter"])
    
    # Extract PS3 config from old format
    ps3 = None
    if extraction == ExtractionType.PS3:
        ps3_data = {}
        if ext_data.get("keys_directory"):
            ps3_data["keys_directory"] = Path(ext_data["keys_directory"])
        if ext_data.get("ps3dec_path"):
            ps3_data["ps3dec_path"] = Path(ext_data["ps3dec_path"])
        updates = raw.get("updates", {})
        if updates:
            ps3_data["nps_database"] = Path(updates["nps_database"]) if updates.get("nps_database") else None
            ps3_data["pkg_archive"] = Path(updates["pkg_archive"]) if updates.get("pkg_archive") else None
            ps3_data["use_sony_psn"] = updates.get("use_sony_psn", True)
        dlc = raw.get("dlc", {})
        if dlc:
            ps3_data["dlc_enabled"] = dlc.get("enabled", False)
            ps3_data["dlc_mode"] = dlc.get("mode", "copy")
        if ps3_data:
            ps3 = PS3Config(**ps3_data)
    
    # Extract Xbox config from old format
    xbox = None
    if extraction == ExtractionType.XISO:
        xbox_data = {}
        if ext_data.get("extract_xiso_path"):
            xbox_data["extract_xiso_path"] = Path(ext_data["extract_xiso_path"])
        if xbox_data:
            xbox = XboxConfig(**xbox_data)
    
    # Parse samples sources
    samples_sources = None
    if "samples" in raw:
        samples_sources = _parse_sources(raw["samples"])
    
    return SlimPlatformConfig(
        name=raw["name"],
        display_name=raw.get("display_name"),
        type=raw.get("type"),
        emulator=raw.get("emulator"),
        metadata_system=raw.get("metadata_system"),
        dat=dat,
        sources=sources,
        chd_sources=chd_sources,
        extraction=extraction,
        multi_disc=raw.get("multi_disc_handling", raw.get("multi_disc", False)),
        list_patterns=list_patterns,
        arcade_filter=arcade_filter,
        bios=raw.get("bios"),
        samples_sources=samples_sources,
        ps3=ps3,
        xbox=xbox,
    )


def _parse_sources(sources_data: list) -> List[SourceConfig]:
    """Parse source configuration list."""
    sources = []
    for src in sources_data:
        if isinstance(src, dict):
            data = dict(src)
            if "path" in data and data["path"] is not None:
                data["path"] = Path(data["path"])
            sources.append(SourceConfig(**data))
    return sources


# ═══════════════════════════════════════════════════════════════════════════════
# Recipe Loader
# ═══════════════════════════════════════════════════════════════════════════════

def load_recipe(
    name: str,
    config_root: Optional[Path] = None,
) -> RecipeSpec:
    """Load a recipe from YAML.
    
    Args:
        name: Recipe name (without .yaml)
        config_root: Config root directory
        
    Returns:
        Validated RecipeSpec
    """
    if config_root is None:
        config_root = Path(__file__).parent.parent.parent.parent / "config"
    
    config_path = config_root / "recipes" / f"{name}.yaml"
    raw = _load_yaml(config_path)
    
    # Parse selection if present
    if "selection" in raw and raw["selection"] is not None:
        raw["selection"] = SelectionConfig(**raw["selection"])
    
    return RecipeSpec(**raw)


def load_all_recipes(
    config_root: Optional[Path] = None,
) -> Dict[str, RecipeSpec]:
    """Load all recipes from the recipes directory.
    
    Returns:
        Dict mapping recipe name to RecipeSpec
    """
    if config_root is None:
        config_root = Path(__file__).parent.parent.parent.parent / "config"
    
    recipes_dir = config_root / "recipes"
    if not recipes_dir.exists():
        return {}
    
    recipes = {}
    for yaml_file in sorted(recipes_dir.glob("*.yaml")):
        name = yaml_file.stem
        try:
            recipes[name] = load_recipe(name, config_root)
        except Exception as e:
            raise ValueError(f"Failed to load recipe '{name}': {e}") from e
    
    return recipes


# ═══════════════════════════════════════════════════════════════════════════════
# Build Spec Loader
# ═══════════════════════════════════════════════════════════════════════════════

def load_build_spec(
    name: str,
    config_root: Optional[Path] = None,
) -> BuildSpec:
    """Load a build spec from YAML.
    
    Searches for the build config in:
    1. config/builds/new/{name}.yaml  (new-format builds)
    2. config/builds/{name}.yaml      (may be old or new format)
    
    Detects whether the YAML is new-format (has 'recipes' key) or
    old-format (has 'includes' or 'platform_overrides'). Only loads
    new-format files as BuildSpec.
    
    Args:
        name: Build name (without .yaml)
        config_root: Config root directory
        
    Returns:
        Validated BuildSpec
        
    Raises:
        ValueError: If the config is old-format (use load_build_config instead)
        FileNotFoundError: If no config found
    """
    if config_root is None:
        config_root = Path(__file__).parent.parent.parent.parent / "config"
    
    # Search in new/ subdirectory first, then builds/
    candidates = [
        config_root / "builds" / "new" / f"{name}.yaml",
        config_root / "builds" / f"{name}.yaml",
    ]
    
    config_path = None
    for candidate in candidates:
        if candidate.exists():
            config_path = candidate
            break
    
    if config_path is None:
        raise FileNotFoundError(
            f"Build config not found: {name}\n"
            f"Searched: {', '.join(str(c) for c in candidates)}"
        )
    
    raw = _load_yaml(config_path)
    
    # Detect old format
    if "includes" in raw or "platform_overrides" in raw:
        raise ValueError(
            f"Build config '{name}' is in old format (has 'includes' or 'platform_overrides'). "
            "Use load_build_config() for legacy configs, or migrate to new recipe-based format."
        )
    
    # Parse nested objects
    if "selection" in raw and raw["selection"] is not None:
        raw["selection"] = SelectionConfig(**raw["selection"])
    
    if "generation_filter" in raw and raw["generation_filter"] is not None:
        from .models import GenerationFilterConfig
        raw["generation_filter"] = GenerationFilterConfig(**raw["generation_filter"])
    
    if "deploy" in raw and raw["deploy"] is not None:
        raw["deploy"] = DeployConfig(**raw["deploy"])
    
    if "post_build" in raw:
        raw["post_build"] = [
            PostBuildHook(**hook) if isinstance(hook, dict) else hook
            for hook in raw["post_build"]
        ]
    
    return BuildSpec(**raw)
