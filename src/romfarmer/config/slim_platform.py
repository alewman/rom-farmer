"""Slim platform configuration — intrinsic facts only.

A SlimPlatformConfig contains ONLY immutable facts about a platform:
what it is, where its ROMs come from, how its archives are structured.

It explicitly does NOT contain:
- Compression settings (build choice)
- Target/output paths (target-specific)
- Organization style (target-specific)
- Selection/filtering (build choice)
- enabled flag (build choice)

These concerns are handled by Recipes and Targets respectively.
"""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from .models import (
    DATSource,
    ExtractionType,
    SourceConfig,
)


class ListPatterns(BaseModel):
    """List file patterns for a platform.
    
    These describe the naming conventions for keep/delete list files,
    which is an intrinsic property of how the platform's curated lists
    are organized on disk.
    """
    
    delete: Optional[str] = Field(
        None, description="Delete list pattern (e.g., 'saturn-delete')"
    )
    add_myrient: Optional[str] = Field(
        None, description="Myrient additions pattern (e.g., 'saturn+*')"
    )
    add_extra: Optional[str] = Field(
        None, description="Extra additions pattern (e.g., 'saturn.*')"
    )
    add: Optional[str] = Field(
        None, description="Generic additions pattern (e.g., 'fbneo+*') — arcade style"
    )


class DATReference(BaseModel):
    """Reference to a DAT file for this platform.
    
    This is intrinsic — it describes which DAT collection this platform
    belongs to and how to find its DAT file.
    """
    
    source: DATSource = Field(
        description="DAT source type (retool_1g1r_eng, redump_retool_1g1r_eng, fbneo_official, etc.)"
    )
    file: Optional[Path] = Field(
        None, description="Explicit DAT file path (for arcade platforms)"
    )
    expected_count: Optional[int] = Field(
        None, description="Expected game count for validation"
    )
    match_method: str = Field(
        "hash", description="Match method: 'hash' or 'fuzzy_name'"
    )
    version: Optional[str] = Field(
        None, description="DAT version (for arcade DATs)"
    )
    # Arcade-specific DAT filtering
    filter_driver: Optional[str] = Field(
        None, description="MAME driver name to filter by (e.g., 'naomi')"
    )
    filter_romof: Optional[str] = Field(
        None, description="MAME romof/BIOS to filter by"
    )
    exclude_romof: Optional[List[str]] = Field(
        None, description="Exclude games with these BIOS dependencies"
    )
    name_pattern: Optional[str] = Field(
        None, description="Glob pattern to filter game names"
    )
    exclude_name_pattern: Optional[str] = Field(
        None, description="Glob pattern to exclude game names"
    )


class ArcadeFilter(BaseModel):
    """Arcade-specific game filtering configuration.
    
    Intrinsic to the platform — describes which subset of the arcade
    ROM set this platform represents.
    """
    
    mode: str = Field(
        default="relaxed",
        description="Filter mode: strict, relaxed, permissive"
    )
    include_hacks: bool = Field(default=False)
    include_bootlegs: bool = Field(default=False)
    include_prototypes: bool = Field(default=False)
    include_homebrew: bool = Field(default=False)
    include_demos: bool = Field(default=False)
    include_working_only: bool = Field(default=True)
    region_priority: List[str] = Field(
        default_factory=lambda: ["world", "usa", "europe", "japan"]
    )


class PS3Config(BaseModel):
    """PS3-specific intrinsic configuration.
    
    These are facts about how PS3 ROMs need to be processed,
    not build choices.
    """
    
    keys_directory: Optional[Path] = Field(
        None, description="PS3 disc keys directory"
    )
    ps3dec_path: Optional[Path] = Field(
        None, description="Path to PS3Dec tool"
    )
    # Updates
    nps_database: Optional[Path] = Field(
        None, description="NoPayStation database path (PS3_DLCS.tsv)"
    )
    pkg_archive: Optional[Path] = Field(
        None, description="PKG archive directory"
    )
    use_sony_psn: bool = Field(
        default=True, description="Check Sony PSN cache for updates"
    )
    # DLC
    dlc_enabled: bool = Field(default=False)
    dlc_mode: str = Field(
        default="copy", description="DLC mode: copy or extract"
    )


class XboxConfig(BaseModel):
    """Xbox/Xbox 360-specific intrinsic configuration."""
    
    extract_xiso_path: Optional[Path] = Field(
        None, description="Path to extract-xiso tool"
    )


class SlimPlatformConfig(BaseModel):
    """Intrinsic facts about a platform.
    
    This model contains ONLY things that are true about the platform itself,
    regardless of which build or target is using it.
    
    Naming convention: "slim" because it's the platform config stripped of
    all build and target concerns.
    """
    
    # Identity
    name: str = Field(description="Platform identifier (e.g., 'saturn', 'nes', 'fbneo')")
    display_name: Optional[str] = Field(
        None, description="Human-readable name (e.g., 'Nintendo - Game Boy Advance')"
    )
    type: Optional[str] = Field(
        None, description="Platform type: 'arcade' for arcade systems, None for consoles"
    )
    emulator: Optional[str] = Field(
        None, description="Emulator name (e.g., 'fbneo', 'mame', 'flycast')"
    )
    metadata_system: Optional[str] = Field(
        None,
        description="System name for metadata lookups (defaults to platform name). "
                    "Useful for arcade platforms that share MAME metadata."
    )
    
    # DAT reference
    dat: DATReference = Field(description="DAT file reference")
    
    # Sources
    sources: List[SourceConfig] = Field(description="Source ROM locations")
    chd_sources: Optional[List[SourceConfig]] = Field(
        None, description="CHD source locations (arcade platforms with CHD games)"
    )
    
    # Extraction type — intrinsic to the platform's ROM format
    extraction: ExtractionType = Field(
        default=ExtractionType.NONE,
        description="How to extract games from archives: none, cartridge, disc, rvz, ps3, xiso"
    )
    
    # Multi-disc
    multi_disc: bool = Field(
        default=False, description="Platform has multi-disc games"
    )
    
    # List file patterns
    list_patterns: Optional[ListPatterns] = Field(
        None, description="List file naming patterns for this platform"
    )
    
    # Arcade-specific
    arcade_filter: Optional[ArcadeFilter] = Field(
        None, description="Arcade game filtering configuration"
    )
    bios: Optional[List[str]] = Field(
        None, description="Required BIOS files (arcade)"
    )
    samples_sources: Optional[List[SourceConfig]] = Field(
        None, description="Sample audio file sources (FBNeo)"
    )
    
    # PS3-specific
    ps3: Optional[PS3Config] = Field(
        None, description="PS3-specific configuration"
    )
    
    # Xbox-specific
    xbox: Optional[XboxConfig] = Field(
        None, description="Xbox/Xbox 360-specific configuration"
    )
    
    @property
    def is_arcade(self) -> bool:
        """Check if this is an arcade platform."""
        return self.type == "arcade"
    
    @property
    def dat_source(self) -> DATSource:
        """Convenience accessor for the DAT source."""
        return self.dat.source
    
    def get_metadata_system(self) -> str:
        """Get the system name for metadata lookups."""
        return self.metadata_system or self.name
