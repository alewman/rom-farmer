"""Pydantic models for configuration validation."""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class DATSource(str, Enum):
    """DAT file source types."""

    RETOOL_1G1R_ENG = "retool_1g1r_eng"
    RETOOL_1G1R_USA = "retool_1g1r_usa"
    NOINTRO_STANDARD = "nointro_standard"
    REDUMP_STANDARD = "redump_standard"
    REDUMP_RETOOL_1G1R_ENG = "redump_retool_1g1r_eng"  # Redump with Retool filtering
    REDUMP_RETOOL_1G1R_USA = "redump_retool_1g1r_usa"
    MANUAL_SCAN = "manual_scan"  # For PS3, etc.


class OrganizationStyle(str, Enum):
    """Organization styles for different targets."""

    RICH = "rich"  # Batocera: deep subdirs, full metadata
    BALANCED = "balanced"  # RocknIX: alphabetical grouping
    MINIMAL = "minimal"  # Everdrive: sort2folders with 50 file limit
    FLAT = "flat"  # No organization, all files in one directory


class CompressionFormat(str, Enum):
    """Supported compression formats."""

    NONE = "none"  # Loose files (for real hardware/Everdrive)
    ZIP = "zip"
    SEVENZ = "7z"
    CHD = "chd"
    CSO = "cso"
    XISO = "xiso"
    RVZ = "rvz"
    SQUASHFS = "sqfs"
    JB = "jb"  # PS3 decrypted folder
    GZIP = "gzip"  # PS3 ISO compression for ps3netsrv


class ExtractionType(str, Enum):
    """Types of content to extract from archives."""

    NONE = "none"  # Don't extract, keep archives as-is
    CARTRIDGE = "cartridge"  # Extract ROM files (.nes, .vb, .smd, etc.)
    DISC = "disc"  # Extract disc images (CUE/BIN, ISO)
    PS3 = "ps3"  # Decrypt and extract PS3 ISO to JB folder format
    MIXED = "mixed"  # Platform has both cartridge and disc games


class PatternType(str, Enum):
    """Pattern matching types for scope filters."""

    GLOB = "glob"  # Shell-style wildcards (*.USA*, [A-M]*)
    REGEX = "regex"  # Full regex support


class ScopeStrategy(str, Enum):
    """Strategies for selecting files in scope filters."""

    FIRST = "first"  # First N files (after sorting)
    LAST = "last"  # Last N files (after sorting)
    RANDOM = "random"  # Random N files
    LARGEST = "largest"  # N largest files by size
    SMALLEST = "smallest"  # N smallest files by size
    ALPHABETICAL = "alphabetical"  # First N alphabetically
    RATING_BUDGET = "rating_budget"  # Quality-based with size budget


# Alias for backward compatibility
SelectionStrategy = ScopeStrategy


class ScopeSortBy(str, Enum):
    """Sort criteria for scope filters."""

    NAME = "name"  # Sort by filename
    SIZE = "size"  # Sort by file size
    MODIFIED = "modified"  # Sort by modification time


class ScopePattern(BaseModel):
    """Pattern configuration for scope filters."""

    type: PatternType = Field(
        default=PatternType.GLOB,
        description="Pattern matching type"
    )
    value: str = Field(
        description="Pattern to match against filenames"
    )


class ScopeSort(BaseModel):
    """Sort configuration for scope filters."""

    by: ScopeSortBy = Field(
        default=ScopeSortBy.NAME,
        description="What to sort by"
    )
    order: str = Field(
        default="asc",
        description="Sort order: asc or desc"
    )


class SelectionConfig(BaseModel):
    """Selection filter configuration for choosing which ROMs to include."""

    name: Optional[str] = Field(None, description="Selection configuration name (for referenced configs)")
    description: Optional[str] = Field(None, description="Human-readable description")
    
    # Strategy and limits
    strategy: ScopeStrategy = Field(
        default=ScopeStrategy.FIRST,
        description="Selection strategy"
    )
    limit: Optional[int] = Field(
        None,
        description="Maximum number of games to select",
        gt=0
    )
    percentage: Optional[float] = Field(
        None,
        description="Select percentage of games (e.g., 20 for first 20%)",
        gt=0,
        le=100
    )
    offset: Optional[float] = Field(
        None,
        description="Skip this percentage before selecting (for phased builds, e.g., offset=20 skips first 20%)",
        ge=0,
        lt=100
    )
    
    # Pattern filtering (optional, applied before strategy)
    pattern: Optional[ScopePattern] = Field(
        None,
        description="Pattern to filter filenames"
    )
    
    # Metadata-based exclusions
    exclude_hidden: bool = Field(
        default=False,
        description="Exclude games marked as hidden in EmulationStation metadata"
    )
    exclude_unrated: bool = Field(
        default=False,
        description="Exclude games with no rating (rating = 0.0 or NULL)"
    )
    exclude_demos: bool = Field(
        default=False,
        description="Exclude demos, betas, protos, samples (filename-based)"
    )
    
    # Rating budget options (for RATING_BUDGET strategy)
    max_size_gb: Optional[float] = Field(
        None,
        description="Maximum total size in GB (for rating_budget strategy)",
        gt=0
    )
    min_rating: Optional[float] = Field(
        None,
        description="Minimum rating threshold 0.0-1.0 (for rating_budget strategy)",
        ge=0.0,
        le=1.0
    )
    
    # Sorting (optional)
    sort: Optional[ScopeSort] = Field(
        None,
        description="Sort configuration before applying strategy"
    )


# Keep ScopeConfig as alias for backward compatibility
ScopeConfig = SelectionConfig


class SystemType(str, Enum):
    """System complexity types - DEPRECATED, use extraction config instead."""

    SIMPLE = "simple"  # No-Intro ZIPs, no extraction
    MEDIUM = "medium"  # Redump, extraction + compression
    COMPLEX = "complex"  # Multi-disc, special handling
    VERY_COMPLEX = "very_complex"  # PS3, Xbox 360 DLC, etc.


class DATConfig(BaseModel):
    """DAT file configuration."""

    source: DATSource = Field(
        description="DAT source type (retool preferred)"
    )
    file: Optional[Path] = Field(
        None, description="Explicit DAT file path (overrides source)"
    )
    expected_count: Optional[int] = Field(
        None, description="Expected game count for validation"
    )

    @field_validator("file")
    @classmethod
    def validate_file_exists(cls, v: Optional[Path]) -> Optional[Path]:
        """Validate DAT file exists if specified."""
        if v is not None and not v.exists():
            raise ValueError(f"DAT file not found: {v}")
        return v


class SourceConfig(BaseModel):
    """Source ROM configuration."""

    path: Path = Field(description="Source directory path")
    type: str = Field(
        "myrient", description="Source type (myrient, custom, etc.)"
    )
    recursive: bool = Field(True, description="Scan subdirectories")

    @field_validator("path")
    @classmethod
    def validate_path_exists(cls, v: Path) -> Path:
        """Validate source path exists."""
        if not v.exists():
            raise ValueError(f"Source path not found: {v}")
        return v


class ListFileConfig(BaseModel):
    """List file configuration."""

    directory: Path = Field(description="Directory containing list files")
    patterns: Dict[str, str] = Field(
        default={
            "delete": "{system}-delete",
            "add_myrient": "{system}+*",
            "add_extra": "{system}.*",
        },
        description="List file naming patterns",
    )

    @field_validator("directory")
    @classmethod
    def validate_directory_exists(cls, v: Path) -> Path:
        """Validate list directory exists."""
        if not v.exists():
            raise ValueError(f"List directory not found: {v}")
        return v


class OrganizationConfig(BaseModel):
    """Organization configuration."""

    style: OrganizationStyle = Field(description="Organization style")
    max_files_per_group: Optional[int] = Field(
        50, description="Max files per group for MINIMAL style"
    )
    create_subdirs: bool = Field(
        True, description="Create subdirectories for list files"
    )
    subdir_prefix: Optional[str] = Field(
        None, description="Prefix for subdirectories (e.g., '_')"
    )


class CompressionConfig(BaseModel):
    """Compression configuration."""

    format: CompressionFormat = Field(description="Target compression format")
    tool: Optional[str] = Field(None, description="Compression tool path")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Tool-specific parameters"
    )
    verify: bool = Field(True, description="Verify compressed files")


class ExtractionConfig(BaseModel):
    """Extraction configuration for archives."""
    
    enabled: bool = Field(
        False, description="Enable extraction from ZIP/7z archives"
    )
    type: ExtractionType = Field(
        ExtractionType.NONE, 
        description="Type of content to extract (cartridge ROM, disc image, etc.)"
    )
    # PS3-specific settings
    keys_directory: Optional[Path] = Field(
        None, description="Directory containing PS3 disc keys (.dkey files)"
    )
    ps3dec_path: Optional[str] = Field(
        None, description="Path to PS3Dec tool (defaults to tools/bin/ps3dec)"
    )


class RatingFilterConfig(BaseModel):
    """Rating-based filtering configuration."""
    
    enabled: bool = Field(
        False, description="Enable rating-based filtering"
    )
    top_n: Optional[int] = Field(
        None, description="Keep only top N highest-rated games"
    )
    max_size_gb: Optional[float] = Field(
        None, description="Keep top-rated games that fit within size budget (GB)"
    )
    min_rating: Optional[float] = Field(
        None, description="Minimum rating threshold (0.0-1.0)"
    )
    
    @model_validator(mode='after')
    def validate_filter_criteria(self):
        """Ensure at least one filter criterion is specified if enabled."""
        if self.enabled:
            if not any([self.top_n, self.max_size_gb, self.min_rating]):
                raise ValueError(
                    "At least one filter criterion (top_n, max_size_gb, min_rating) "
                    "must be specified when rating_filter is enabled"
                )
        return self


class TargetProfile(BaseModel):
    """Target system profile (Batocera, RocknIX, Everdrive)."""

    name: str = Field(description="Profile name")
    output_path: Path = Field(description="Output directory")
    organization: OrganizationConfig = Field(
        description="Organization configuration"
    )
    compression: Optional[CompressionConfig] = Field(
        None, description="Compression override for this target"
    )
    metadata: bool = Field(
        True, description="Generate metadata (gamelist.xml)"
    )
    enabled: bool = Field(True, description="Enable this target")

    @field_validator("output_path")
    @classmethod
    def validate_output_path_parent(cls, v: Path) -> Path:
        """Validate output path parent exists."""
        if not v.parent.exists():
            raise ValueError(f"Output parent directory not found: {v.parent}")
        return v


class PlatformConfig(BaseModel):
    """Configuration for a single platform (NES, Saturn, etc.)."""

    name: str = Field(description="Platform name")
    system_type: Optional[SystemType] = Field(
        None, description="System complexity type (DEPRECATED - use extraction config)"
    )
    dat: DATConfig = Field(description="DAT configuration")
    sources: List[SourceConfig] = Field(description="Source ROM locations")
    lists: Optional[ListFileConfig] = Field(
        None, description="List file configuration"
    )
    extraction: ExtractionConfig = Field(
        default_factory=lambda: ExtractionConfig(enabled=False, type=ExtractionType.NONE),
        description="Extraction configuration"
    )
    selection: Optional[SelectionConfig] = Field(
        None,
        description="Selection filter configuration (replaces rating_filter)"
    )
    rating_filter: RatingFilterConfig = Field(
        default_factory=lambda: RatingFilterConfig(enabled=False),
        description="Rating-based filtering configuration (DEPRECATED - use selection instead)"
    )
    compression: Optional[CompressionConfig] = Field(
        None, description="Default compression for this platform"
    )
    targets: List[TargetProfile] = Field(description="Output targets")
    enabled: bool = Field(True, description="Enable this platform")

    # Legacy settings - kept for backward compatibility
    extract_archives: Optional[bool] = Field(
        None, description="DEPRECATED: Use extraction.enabled instead"
    )
    multi_disc_handling: bool = Field(
        False, description="Enable multi-disc detection"
    )
    custom_stages: List[str] = Field(
        default_factory=list, description="Custom stage names"
    )

    @model_validator(mode="after")
    def validate_platform_config(self) -> "PlatformConfig":
        """Validate platform configuration consistency."""
        # Migrate legacy extract_archives to new extraction config
        if self.extract_archives is not None:
            self.extraction.enabled = self.extract_archives
            
        # Auto-detect extraction type from system_type if not explicitly set
        if self.system_type is not None and self.extraction.type == ExtractionType.NONE:
            if self.system_type == SystemType.SIMPLE:
                self.extraction.enabled = False
            elif self.system_type == SystemType.COMPLEX:
                # COMPLEX systems (Wii/GameCube) use UnzipRVZStage
                # Keep extraction disabled so legacy system_type routing is used
                self.extraction.enabled = False
            elif self.system_type == SystemType.MEDIUM:
                self.extraction.enabled = True
                # Try to infer type from compression format
                if self.compression and self.compression.format == CompressionFormat.CHD:
                    self.extraction.type = ExtractionType.DISC
                elif self.extraction.enabled:
                    # Default to cartridge if extracting but not CHD
                    self.extraction.type = ExtractionType.CARTRIDGE

        return self


class BuildConfig(BaseModel):
    """Master build configuration (e.g., rocknix-512gb.yaml)."""

    name: str = Field(description="Build name")
    description: Optional[str] = Field(None, description="Build description")
    platforms: List[str] = Field(
        description="Platform config files to include"
    )
    global_dat_priority: List[DATSource] = Field(
        default=[
            DATSource.RETOOL_1G1R_ENG,
            DATSource.RETOOL_1G1R_USA,
            DATSource.NOINTRO_STANDARD,
            DATSource.REDUMP_STANDARD,
        ],
        description="Global DAT source priority",
    )
    global_lists: Optional[ListFileConfig] = Field(
        None, description="Global list file configuration"
    )
    workspace: Path = Field(
        Path("/data/emu/rom-groomer-python"),
        description="Workspace root directory",
    )
    dat_directory: Path = Field(
        Path("/data/emu/dats"), description="DAT files directory"
    )
    checkpoint_enabled: bool = Field(
        True, description="Enable checkpointing for resume"
    )
    parallel_platforms: bool = Field(
        False, description="Process platforms in parallel"
    )
    max_workers: int = Field(4, description="Max parallel workers")

    @field_validator("workspace", "dat_directory")
    @classmethod
    def validate_directory_exists(cls, v: Path) -> Path:
        """Validate directory exists."""
        if not v.exists():
            raise ValueError(f"Directory not found: {v}")
        return v
