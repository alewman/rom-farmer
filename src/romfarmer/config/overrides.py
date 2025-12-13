"""Configuration override merging utilities.

This module provides clean, predictable merging of build-level overrides
with platform configurations using Pydantic's model_copy().

Merge Semantics:
- Simple fields (enabled, name): Direct replacement
- Nested objects (dat, compression, selection): Deep merge
- Lists (targets, sources): Replace or filter based on content type
- None values: Explicitly disable/clear the field
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from .models import (
    CompressionConfig,
    CompressionFormat,
    DATConfig,
    ExtractionConfig,
    ExtractionType,
    ListFileConfig,
    OrganizationConfig,
    PlatformConfig,
    SelectionConfig,
    SourceConfig,
    TargetProfile,
)

logger = logging.getLogger(__name__)


class OverrideResult:
    """Result of applying overrides with logging info."""
    
    def __init__(self, config: PlatformConfig):
        self.config = config
        self.changes: List[str] = []
    
    def log_change(self, field: str, value: Any):
        """Record a change for logging."""
        self.changes.append(f"{field} = {value}")
    
    def log_all(self):
        """Log all recorded changes."""
        if self.changes:
            logger.info(f"Applied {len(self.changes)} overrides:")
            for change in self.changes:
                logger.info(f"  • {change}")


def apply_overrides(
    config: PlatformConfig,
    overrides: Dict[str, Any],
    storage_config: Optional[Dict[str, Any]] = None
) -> PlatformConfig:
    """
    Apply build-level overrides to a platform configuration.
    
    This is the main entry point for override application. It handles
    all field types with appropriate merge semantics.
    
    Args:
        config: Original platform configuration
        overrides: Dictionary of override values from build config
        storage_config: Optional storage configuration for path templates
        
    Returns:
        New PlatformConfig with overrides applied
    """
    if not overrides:
        return config
    
    result = OverrideResult(config)
    
    # Start with a copy of the config
    updates: Dict[str, Any] = {}
    
    # Simple field overrides (direct replacement)
    for field in ['enabled', 'name', 'multi_disc_handling']:
        if field in overrides:
            updates[field] = overrides[field]
            result.log_change(field, overrides[field])
    
    # DAT configuration (deep merge)
    if 'dat' in overrides:
        updates['dat'] = _merge_dat_config(config.dat, overrides['dat'])
        result.log_change('dat', updates['dat'])
    
    # Compression configuration (deep merge)
    if 'compression' in overrides:
        updates['compression'] = _merge_compression_config(
            config.compression, 
            overrides['compression']
        )
        result.log_change('compression', updates['compression'])
    
    # Extraction configuration (deep merge)
    if 'extraction' in overrides:
        updates['extraction'] = _merge_extraction_config(
            config.extraction,
            overrides['extraction']
        )
        result.log_change('extraction', updates['extraction'])
    
    # Selection configuration (deep merge or replace)
    if 'selection' in overrides:
        updates['selection'] = _merge_selection_config(
            config.selection,
            overrides['selection']
        )
        result.log_change('selection', updates['selection'])
    
    # Sources (replace entirely)
    if 'sources' in overrides:
        updates['sources'] = _parse_sources(overrides['sources'])
        result.log_change('sources', f"{len(updates['sources'])} sources")
    
    # Lists configuration (deep merge or disable)
    if 'lists' in overrides:
        if overrides['lists'] is None:
            updates['lists'] = None
            result.log_change('lists', 'disabled')
        else:
            updates['lists'] = _merge_lists_config(
                config.lists,
                overrides['lists']
            )
            result.log_change('lists', updates['lists'])
    
    # Targets (replace or filter)
    if 'targets' in overrides:
        updates['targets'] = _process_targets_override(
            config.targets,
            overrides['targets'],
            overrides.get('organization'),
            config,
            storage_config
        )
        result.log_change('targets', f"{len(updates['targets'])} targets")
    
    # Apply all updates using model_copy
    new_config = config.model_copy(update=updates)
    
    result.log_all()
    return new_config


def _merge_dat_config(
    existing: Optional[DATConfig],
    overrides: Dict[str, Any]
) -> DATConfig:
    """Merge DAT configuration overrides."""
    if existing is None:
        # Create new from overrides
        data = dict(overrides)
        if 'file' in data and data['file'] is not None:
            data['file'] = Path(data['file'])
        return DATConfig(**data)
    
    # Deep merge: override specified fields only
    updates = {}
    for key, value in overrides.items():
        if key == 'file' and value is not None:
            value = Path(value)
        updates[key] = value
    
    return existing.model_copy(update=updates)


def _merge_compression_config(
    existing: Optional[CompressionConfig],
    overrides: Dict[str, Any]
) -> CompressionConfig:
    """Merge compression configuration overrides."""
    data = dict(overrides)
    
    # Handle enum conversion
    if 'format' in data and isinstance(data['format'], str):
        data['format'] = CompressionFormat(data['format'])
    
    if existing is None:
        return CompressionConfig(**data)
    
    return existing.model_copy(update=data)


def _merge_extraction_config(
    existing: ExtractionConfig,
    overrides: Dict[str, Any]
) -> ExtractionConfig:
    """Merge extraction configuration overrides."""
    data = dict(overrides)
    
    # Handle enum conversion
    if 'type' in data and isinstance(data['type'], str):
        data['type'] = ExtractionType(data['type'])
    
    # Handle path conversions
    for path_field in ['keys_directory', 'ps3dec_path']:
        if path_field in data and data[path_field] is not None:
            data[path_field] = Path(data[path_field])
    
    return existing.model_copy(update=data)


def _merge_selection_config(
    existing: Optional[SelectionConfig],
    overrides: Dict[str, Any]
) -> Optional[SelectionConfig]:
    """Merge selection configuration overrides."""
    from .models import SelectionStrategy
    
    if overrides is None:
        return None
    
    data = dict(overrides)
    
    # Handle enum conversion for strategy field
    if 'strategy' in data and isinstance(data['strategy'], str):
        data['strategy'] = SelectionStrategy(data['strategy'])
    
    if existing is None:
        return SelectionConfig(**data)
    
    return existing.model_copy(update=data)


def _merge_lists_config(
    existing: Optional[ListFileConfig],
    overrides: Dict[str, Any]
) -> ListFileConfig:
    """Merge list file configuration overrides."""
    data = dict(overrides)
    
    # Handle path conversion
    if 'directory' in data:
        data['directory'] = Path(data['directory'])
    
    if existing is None:
        return ListFileConfig(**data)
    
    return existing.model_copy(update=data)


def _parse_sources(sources_data: List[Dict[str, Any]]) -> List[SourceConfig]:
    """Parse source configuration list."""
    sources = []
    for src_data in sources_data:
        data = dict(src_data)
        if 'path' in data and data['path'] is not None:
            data['path'] = Path(data['path'])
        sources.append(SourceConfig(**data))
    return sources


def _process_targets_override(
    existing_targets: List[TargetProfile],
    targets_override: Union[List[str], List[Dict[str, Any]]],
    organization_default: Optional[Union[str, Dict[str, Any]]],
    config: PlatformConfig,
    storage_config: Optional[Dict[str, Any]]
) -> List[TargetProfile]:
    """
    Process targets override.
    
    Two modes:
    1. List of strings: Filter existing targets by name
    2. List of dicts: Replace targets entirely with new definitions
    """
    if not targets_override:
        return existing_targets
    
    # Mode 1: Filter by name (list of strings)
    if all(isinstance(t, str) for t in targets_override):
        allowed_names = set(targets_override)
        return [t for t in existing_targets if t.name in allowed_names]
    
    # Mode 2: Full replacement (list of dicts)
    new_targets = []
    for t_data in targets_override:
        if isinstance(t_data, str):
            # Mixed mode: treat string as filter, skip
            continue
            
        target_data = dict(t_data)
        
        # Handle output_path
        if 'output_path' in target_data:
            target_data['output_path'] = Path(target_data['output_path'])
        elif storage_config and storage_config.get('output_template'):
            target_data['output_path'] = _generate_output_path(
                target_data,
                config,
                storage_config
            )
        
        # Handle organization shortcut (string -> dict)
        if 'organization' in target_data:
            org = target_data['organization']
            if isinstance(org, str):
                target_data['organization'] = {'style': org}
        elif organization_default:
            # Apply default organization
            if isinstance(organization_default, str):
                target_data['organization'] = {'style': organization_default}
            else:
                target_data['organization'] = organization_default
        
        new_targets.append(TargetProfile(**target_data))
    
    return new_targets


def _generate_output_path(
    target_data: Dict[str, Any],
    config: PlatformConfig,
    storage_config: Dict[str, Any]
) -> Path:
    """Generate output path from template."""
    template = storage_config.get('output_template', '{platform}')
    output_base = Path(storage_config.get('output_base', 'output'))
    
    platform = config.name
    target = target_data.get('name', 'default')
    
    # Platform folder mapping
    platform_map = storage_config.get('platform_folder_map', {})
    if target in platform_map and platform in platform_map[target]:
        platform = platform_map[target][platform]
    
    # Extract filter/region from DAT source
    filter_name = 'custom'
    region = 'all'
    
    if config.dat and config.dat.source:
        dat_source = str(config.dat.source.value).lower()
        
        if '1g1r' in dat_source:
            filter_name = '1g1r'
        elif 'nointro' in dat_source:
            filter_name = 'nointro'
        elif 'redump' in dat_source:
            filter_name = 'redump'
        
        if 'eng' in dat_source:
            region = 'eng'
        elif 'usa' in dat_source:
            region = 'usa'
        elif 'jp' in dat_source:
            region = 'jp'
    
    # Format from compression
    fmt = 'raw'
    if config.compression and config.compression.format:
        fmt = config.compression.format.value
    
    folder_name = template.format(
        platform=platform,
        filter=filter_name,
        region=region,
        format=fmt,
        target=target
    )
    
    return output_base / folder_name
