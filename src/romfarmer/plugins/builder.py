"""Plugin-aware pipeline builder.

Bridges the existing builder.py (which assembles stages imperatively)
with the new plugin system. This module provides a `build_plugin_pipeline`
function that mirrors `build_pipeline` but returns a PluginPipeline
with event bus integration.

This is a drop-in replacement: the build orchestrator can switch between
legacy Pipeline and PluginPipeline by changing one function call.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config.resolver import ResolvedPlatformConfig
from ..config.models import (
    CompressionFormat,
    ExtractionType,
)
from .adapter import StageAdapter
from .catalog import STAGE_CONTRACTS
from .events import EventBus
from .pipeline import PluginPipeline
from .protocol import PluginCapability
from .registry import PluginRegistry

logger = logging.getLogger(__name__)


def build_plugin_pipeline(
    resolved: ResolvedPlatformConfig,
    cache_manager: Optional[Any] = None,
    composed_target: Optional[Any] = None,
    work_dir: Optional[Path] = None,
    event_bus: Optional[EventBus] = None,
    registry: Optional[PluginRegistry] = None,
) -> PluginPipeline:
    """Build a PluginPipeline from a resolved platform config.

    This mirrors builder.py's build_pipeline() but produces a PluginPipeline
    with event bus integration. The stage assembly logic is identical —
    same stages, same order, same config adaptation — but each stage is
    wrapped as a plugin via StageAdapter.

    Args:
        resolved: Fully resolved platform configuration
        cache_manager: Optional ROM cache for build acceleration
        composed_target: Optional composed target for pipeline context
        work_dir: Working directory for temp files
        event_bus: Event bus for lifecycle events (created if None)
        registry: Optional pre-populated registry (for custom plugins)

    Returns:
        PluginPipeline ready for execution
    """
    from ..stages.builder import build_pipeline as legacy_build_pipeline

    # Build the legacy pipeline to get the assembled stage list
    legacy_pipeline = legacy_build_pipeline(
        resolved=resolved,
        cache_manager=cache_manager,
        composed_target=composed_target,
        work_dir=work_dir,
    )

    # Wrap each stage as a plugin using the catalog contracts
    plugins = []
    for stage in legacy_pipeline.stages:
        # Try to find the matching contract by stage class name
        contract = _find_contract_for_stage(stage)
        if contract:
            adapter = StageAdapter(
                stage=stage,
                capability=contract["capability"],
                requires=contract.get("requires", frozenset()),
                provides=contract.get("provides", frozenset()),
                priority=contract.get("priority", 50),
                platforms=contract.get("platforms", frozenset()),
                name_override=contract.get("_catalog_name"),
            )
        else:
            # Unknown stage — wrap with generic metadata
            logger.warning(
                f"No catalog contract for stage '{stage.name}' "
                f"({stage.__class__.__name__}). Using generic wrapper."
            )
            adapter = StageAdapter(
                stage=stage,
                capability=PluginCapability.FILTER,
            )
        plugins.append(adapter)

    bus = event_bus or EventBus()

    pipeline = PluginPipeline(
        plugins=plugins,
        event_bus=bus,
    )

    logger.info(
        f"Built plugin pipeline for {resolved.platform}: "
        f"{len(plugins)} plugins "
        f"(extraction={resolved.extraction_type.value}, "
        f"compression={resolved.compression.value})"
    )

    return pipeline


# ═══════════════════════════════════════════════════════════════════════════════
# Stage → Contract mapping
# ═══════════════════════════════════════════════════════════════════════════════

# Map stage class names to catalog keys
_CLASS_TO_CATALOG: Dict[str, str] = {
    "PreFilterStage": "pre-filter",
    "FilterDATStage": "filter-dat",
    "Filter1G1RStage": "filter-1g1r",
    "FilterArcadeStage": "filter-arcade",
    "SelectionFilter": "selection-filter",
    "FilterRatingStage": "filter-rating",
    "ApplyListsStage": "apply-lists",
    "CachePreCheckStage": "cache-pre-check",
    "ExtractArchiveStage": "extract-archive",
    "ExtractPS3Stage": "extract-ps3",
    "UnzipRVZStage": "unzip-rvz",
    "CopyArcadeStage": "copy-arcade",
    "CompressCHDStage": "compress-chd",
    "CompressArchiveStage": "compress-archive",
    "ConvertXISOStage": "convert-xiso",
    "CompressSquashfsStage": "compress-squashfs",
    "CreateM3UStage": "create-m3u",
    "OrganizeStage": "organize",
    "GenerateMetadataStage": "generate-metadata",
    "ApplyPS3UpdatesStage": "apply-ps3-updates",
    "TransformPS3Stage": "transform-ps3",
}


def _find_contract_for_stage(stage: Any) -> Optional[Dict[str, Any]]:
    """Find the catalog contract matching a stage instance.

    Args:
        stage: Stage instance

    Returns:
        Contract dict with added _catalog_name key, or None
    """
    class_name = stage.__class__.__name__
    catalog_name = _CLASS_TO_CATALOG.get(class_name)
    if not catalog_name:
        return None

    contract = STAGE_CONTRACTS.get(catalog_name)
    if not contract:
        return None

    # Return a copy with the catalog name included
    result = dict(contract)
    result["_catalog_name"] = catalog_name
    return result
