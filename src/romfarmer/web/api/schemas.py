"""Schema API routes — JSON Schema from Pydantic models for form generation."""

from __future__ import annotations

import logging

from fastapi import APIRouter

logger = logging.getLogger("romfarmer.web.api.schemas")

router = APIRouter()


@router.get("/platform")
async def platform_schema():
    """Get JSON Schema for PlatformConfig."""
    from romfarmer.config.models import PlatformConfig

    return PlatformConfig.model_json_schema()


@router.get("/build-spec")
async def build_spec_schema():
    """Get JSON Schema for BuildSpec (new format)."""
    from romfarmer.config.build_spec import BuildSpec

    return BuildSpec.model_json_schema()


@router.get("/build-config")
async def build_config_schema():
    """Get JSON Schema for BuildConfig (legacy format)."""
    from romfarmer.config.models import BuildConfig

    return BuildConfig.model_json_schema()


@router.get("/target")
async def target_schema():
    """Get JSON Schema for TargetConfig."""
    from romfarmer.config.target import TargetConfig

    return TargetConfig.model_json_schema()


@router.get("/selection")
async def selection_schema():
    """Get JSON Schema for SelectionConfig."""
    from romfarmer.config.models import SelectionConfig

    return SelectionConfig.model_json_schema()


@router.get("/compression")
async def compression_schema():
    """Get JSON Schema for CompressionConfig."""
    from romfarmer.config.models import CompressionConfig

    return CompressionConfig.model_json_schema()


@router.get("/enums")
async def enums():
    """Get all enum values for populating dropdowns."""
    from romfarmer.config.models import (
        CompressionFormat,
        DATSource,
        ExtractionType,
        OrganizationStyle,
        SelectionSortBy,
        SelectionStrategy,
    )

    return {
        "compression_formats": [e.value for e in CompressionFormat],
        "dat_sources": [e.value for e in DATSource],
        "extraction_types": [e.value for e in ExtractionType],
        "organization_styles": [e.value for e in OrganizationStyle],
        "selection_strategies": [e.value for e in SelectionStrategy],
        "selection_sort_by": [e.value for e in SelectionSortBy],
    }
