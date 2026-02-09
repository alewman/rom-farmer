"""Built-in plugin catalog — wraps all existing stages as plugins.

This module provides factory functions that create StageAdapter-wrapped
plugins for every built-in stage. Each adapter declares the correct
requires/provides I/O contract, capability, priority, and platform scope.

The catalog is the bridge between the legacy stage system and the new
plugin architecture. Over time, stages will be rewritten as native plugins,
but the catalog ensures the entire pipeline works through the plugin
system immediately.

Usage::

    from romfarmer.plugins.catalog import register_builtin_plugins

    registry = PluginRegistry()
    register_builtin_plugins(registry)
    # All 22 stages now available as plugins
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .adapter import StageAdapter
from .protocol import PluginCapability
from .registry import PluginRegistry

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# I/O Contracts for all built-in stages
# ═══════════════════════════════════════════════════════════════════════════════
#
# Each entry defines:
#   - capability: Plugin phase category
#   - requires: Context fields the stage reads
#   - provides: Context fields the stage writes
#   - priority: Ordering within capability phase (lower = earlier)
#   - platforms: Platform restrictions (empty = universal)
#
# These contracts were audited from the execute() methods of each stage.
# ═══════════════════════════════════════════════════════════════════════════════

STAGE_CONTRACTS: Dict[str, Dict[str, Any]] = {
    # ── Filtering ─────────────────────────────────────────────────────────
    "pre-filter": {
        "capability": PluginCapability.FILTER,
        "requires": frozenset({"source_files", "platform_config"}),
        "provides": frozenset({"source_files"}),
        "priority": 5,
        "description": "Pre-DAT filename filters (letter, region, language)",
    },
    "filter-dat": {
        "capability": PluginCapability.FILTER,
        "requires": frozenset({"source_files", "dat_file", "platform_config"}),
        "provides": frozenset({"matched_files", "filtered_files", "file_md5s"}),
        "priority": 10,
        "description": "Match source files against DAT database via MD5",
    },
    "filter-1g1r": {
        "capability": PluginCapability.FILTER,
        "requires": frozenset({"matched_files", "dat_file"}),
        "provides": frozenset({"filtered_files"}),
        "priority": 20,
        "description": "One Game One ROM selection from DAT parent/clone sets",
    },
    "filter-arcade": {
        "capability": PluginCapability.FILTER,
        "requires": frozenset({"source_files", "dat_file", "platform_config"}),
        "provides": frozenset({"matched_files", "filtered_files"}),
        "priority": 10,
        "description": "Arcade ROM filtering with driver/romof/hardware support",
    },

    # ── Selection ─────────────────────────────────────────────────────────
    "selection-filter": {
        "capability": PluginCapability.SELECT,
        "requires": frozenset({"filtered_files", "platform_config"}),
        "provides": frozenset({"filtered_files"}),
        "priority": 10,
        "description": "Rating/generation/tier-based selection filter",
    },
    "filter-rating": {
        "capability": PluginCapability.SELECT,
        "requires": frozenset({"filtered_files"}),
        "provides": frozenset({"filtered_files"}),
        "priority": 20,
        "description": "Filter by game rating threshold",
    },
    "apply-lists": {
        "capability": PluginCapability.SELECT,
        "requires": frozenset({"filtered_files", "platform_config"}),
        "provides": frozenset({"filtered_files", "organized_files"}),
        "priority": 30,
        "description": "Apply keep/delete/add lists to filtered files",
    },

    # ── Cache ─────────────────────────────────────────────────────────────
    "cache-pre-check": {
        "capability": PluginCapability.CACHE,
        "requires": frozenset({"filtered_files"}),
        "provides": frozenset({"filtered_files"}),
        "priority": 10,
        "description": "Skip extraction for files already in cache",
    },

    # ── Extraction ────────────────────────────────────────────────────────
    "extract-archive": {
        "capability": PluginCapability.EXTRACT,
        "requires": frozenset({"filtered_files", "work_dir"}),
        "provides": frozenset({"extracted_files", "zip_identity_map"}),
        "priority": 10,
        "description": "Extract ROM/disc files from ZIP archives",
    },
    "extract-ps3": {
        "capability": PluginCapability.EXTRACT,
        "requires": frozenset({"filtered_files", "work_dir"}),
        "provides": frozenset({"extracted_files"}),
        "priority": 10,
        "platforms": frozenset({"ps3"}),
        "description": "Decrypt and extract PS3 ISOs via ps3dec",
    },
    "unzip-rvz": {
        "capability": PluginCapability.EXTRACT,
        "requires": frozenset({"filtered_files", "work_dir"}),
        "provides": frozenset({"extracted_files"}),
        "priority": 10,
        "platforms": frozenset({"wii", "gc"}),
        "description": "Extract RVZ-compressed Wii/GameCube images",
    },
    "copy-arcade": {
        "capability": PluginCapability.EXTRACT,
        "requires": frozenset({"filtered_files", "output_dir"}),
        "provides": frozenset({"extracted_files"}),
        "priority": 10,
        "description": "Copy arcade ROMs directly (no extraction needed)",
    },

    # ── Compression ───────────────────────────────────────────────────────
    "compress-chd": {
        "capability": PluginCapability.COMPRESS,
        "requires": frozenset({"extracted_files", "work_dir"}),
        "provides": frozenset({"compressed_files", "disc_groups"}),
        "priority": 10,
        "description": "Convert disc images (CUE/BIN) to CHD format",
    },
    "compress-archive": {
        "capability": PluginCapability.COMPRESS,
        "requires": frozenset({"extracted_files", "work_dir"}),
        "provides": frozenset({"compressed_files"}),
        "priority": 10,
        "description": "Compress ROMs to 7z or ZIP archives",
    },
    "convert-xiso": {
        "capability": PluginCapability.COMPRESS,
        "requires": frozenset({"extracted_files", "work_dir"}),
        "provides": frozenset({"compressed_files"}),
        "priority": 10,
        "platforms": frozenset({"xbox"}),
        "description": "Convert Xbox disc images to XISO format",
    },
    "compress-squashfs": {
        "capability": PluginCapability.COMPRESS,
        "requires": frozenset({"compressed_files", "work_dir"}),
        "provides": frozenset({"compressed_files"}),
        "priority": 20,
        "platforms": frozenset({"xbox"}),
        "description": "Compress XISO to Squashfs (post-XISO conversion)",
    },

    # ── Organization ──────────────────────────────────────────────────────
    "create-m3u": {
        "capability": PluginCapability.ORGANIZE,
        "requires": frozenset({"compressed_files", "work_dir"}),
        "provides": frozenset({"m3u_files", "disc_metadata"}),
        "priority": 10,
        "description": "Create M3U playlists for multi-disc games",
    },
    "organize": {
        "capability": PluginCapability.ORGANIZE,
        "requires": frozenset({"output_dir"}),
        "provides": frozenset({"organized_files"}),
        "priority": 20,
        "description": "Organize processed files into output directory structure",
    },

    # ── Metadata ──────────────────────────────────────────────────────────
    "generate-metadata": {
        "capability": PluginCapability.METADATA,
        "requires": frozenset({"output_dir", "platform_config"}),
        "provides": frozenset(),
        "priority": 10,
        "description": "Generate gamelist.xml metadata from scraper databases",
    },

    # ── PS3-specific ──────────────────────────────────────────────────────
    "apply-ps3-updates": {
        "capability": PluginCapability.ORGANIZE,
        "requires": frozenset({"extracted_files", "output_dir"}),
        "provides": frozenset(),
        "priority": 15,
        "platforms": frozenset({"ps3"}),
        "description": "Apply PS3 game updates and DLC from PSN/NPS",
    },
    "transform-ps3": {
        "capability": PluginCapability.COMPRESS,
        "requires": frozenset({"filtered_files", "work_dir"}),
        "provides": frozenset({"compressed_files"}),
        "priority": 10,
        "platforms": frozenset({"ps3"}),
        "description": "PS3 ROM transformation pipeline",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Factory functions
# ═══════════════════════════════════════════════════════════════════════════════


def _create_stage(stage_name: str, **kwargs) -> Any:
    """Lazy-create a stage instance by name.

    Uses lazy imports to avoid circular dependencies and keep
    startup fast.

    Args:
        stage_name: Plugin name from STAGE_CONTRACTS
        **kwargs: Constructor arguments for the stage

    Returns:
        Stage instance
    """
    # Import map: plugin-name → (module, class_name)
    _STAGE_MAP = {
        "pre-filter": ("romfarmer.stages.pre_filter", "PreFilterStage"),
        "filter-dat": ("romfarmer.stages.filter_dat", "FilterDATStage"),
        "filter-1g1r": ("romfarmer.stages.filter_1g1r", "Filter1G1RStage"),
        "filter-arcade": ("romfarmer.stages.filter_arcade", "FilterArcadeStage"),
        "selection-filter": ("romfarmer.stages.filter_selection", "SelectionFilter"),
        "filter-rating": ("romfarmer.stages.filter_rating", "FilterRatingStage"),
        "apply-lists": ("romfarmer.stages.apply_lists", "ApplyListsStage"),
        "cache-pre-check": ("romfarmer.stages.cache_precheck", "CachePreCheckStage"),
        "extract-archive": ("romfarmer.stages.extract.ExtractArchiveStage", "ExtractArchiveStage"),
        "extract-ps3": ("romfarmer.stages.extract_ps3", "ExtractPS3Stage"),
        "unzip-rvz": ("romfarmer.stages.unzip_rvz", "UnzipRVZStage"),
        "copy-arcade": ("romfarmer.stages.copy_arcade", "CopyArcadeStage"),
        "compress-chd": ("romfarmer.stages.compress", "CompressCHDStage"),
        "compress-archive": ("romfarmer.stages.compress_archive", "CompressArchiveStage"),
        "convert-xiso": ("romfarmer.stages.convert_xiso", "ConvertXISOStage"),
        "compress-squashfs": ("romfarmer.stages.convert_xiso", "CompressSquashfsStage"),
        "create-m3u": ("romfarmer.stages.m3u", "CreateM3UStage"),
        "organize": ("romfarmer.stages.organize", "OrganizeStage"),
        "generate-metadata": ("romfarmer.stages.metadata", "GenerateMetadataStage"),
        "apply-ps3-updates": ("romfarmer.stages.apply_ps3_updates", "ApplyPS3UpdatesStage"),
        "transform-ps3": ("romfarmer.stages.transform_ps3", "TransformPS3Stage"),
    }

    # Fix: extract-archive has wrong module path
    if stage_name == "extract-archive":
        module_path = "romfarmer.stages.extract"
        class_name = "ExtractArchiveStage"
    else:
        entry = _STAGE_MAP.get(stage_name)
        if not entry:
            raise ValueError(f"Unknown stage: {stage_name}")
        module_path, class_name = entry

    import importlib
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    return cls(**kwargs)


def create_plugin(
    stage_name: str,
    stage_kwargs: Optional[Dict[str, Any]] = None,
) -> StageAdapter:
    """Create a plugin-wrapped stage by name.

    Args:
        stage_name: Plugin name from STAGE_CONTRACTS
        stage_kwargs: Constructor arguments for the underlying stage

    Returns:
        StageAdapter wrapping the stage

    Raises:
        ValueError: If stage_name is not in STAGE_CONTRACTS
    """
    contract = STAGE_CONTRACTS.get(stage_name)
    if not contract:
        raise ValueError(
            f"Unknown plugin: {stage_name}. "
            f"Available: {', '.join(sorted(STAGE_CONTRACTS.keys()))}"
        )

    stage = _create_stage(stage_name, **(stage_kwargs or {}))

    return StageAdapter(
        stage=stage,
        capability=contract["capability"],
        requires=contract.get("requires", frozenset()),
        provides=contract.get("provides", frozenset()),
        priority=contract.get("priority", 50),
        platforms=contract.get("platforms", frozenset()),
        name_override=stage_name,  # Use canonical catalog name
    )


def register_builtin_plugins(
    registry: PluginRegistry,
    stage_configs: Optional[Dict[str, Dict[str, Any]]] = None,
) -> int:
    """Register all built-in stages as plugins in the registry.

    Creates StageAdapter-wrapped plugins for stages that don't need
    constructor arguments. Stages that require constructor params
    (like CachePreCheckStage, CompressCHDStage, etc.) must be
    registered separately with their config.

    Args:
        registry: Plugin registry to populate
        stage_configs: Optional dict of {plugin_name: {constructor_kwargs}}
            for stages that need configuration

    Returns:
        Number of plugins registered
    """
    configs = stage_configs or {}

    # Stages that can be created with no arguments
    NO_ARG_STAGES = {
        "pre-filter",
        "filter-dat",
        "filter-1g1r",
        "filter-arcade",
        "apply-lists",
        "extract-archive",
        "copy-arcade",
        "create-m3u",
        "organize",
    }

    count = 0
    for name in sorted(STAGE_CONTRACTS.keys()):
        if name in configs or name in NO_ARG_STAGES:
            try:
                kwargs = configs.get(name, {})
                plugin = create_plugin(name, stage_kwargs=kwargs)
                registry.register(plugin, source="built-in")
                count += 1
            except Exception as e:
                logger.warning(f"Failed to register built-in plugin '{name}': {e}")
        else:
            logger.debug(
                f"Skipping '{name}' — requires constructor config "
                f"(pass via stage_configs)"
            )

    logger.info(f"Registered {count} built-in plugins")
    return count


def get_contract(name: str) -> Optional[Dict[str, Any]]:
    """Get the I/O contract for a stage.

    Args:
        name: Plugin/stage name

    Returns:
        Contract dict or None if not found
    """
    return STAGE_CONTRACTS.get(name)


def list_contracts() -> Dict[str, Dict[str, Any]]:
    """Get all stage contracts.

    Returns:
        Dict of plugin name → contract
    """
    return dict(STAGE_CONTRACTS)
