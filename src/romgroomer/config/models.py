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
    MANUAL_SCAN = "manual_scan"  # For PS3, etc.


class OrganizationStyle(str, Enum):
    """Organization styles for different targets."""

    RICH = "rich"  # Batocera: deep subdirs, full metadata
    BALANCED = "balanced"  # RocknIX: alphabetical grouping
    MINIMAL = "minimal"  # Everdrive: sort2folders with 50 file limit
    FLAT = "flat"  # No organization, all files in one directory


class CompressionFormat(str, Enum):
    """Supported compression formats."""

    NONE = "none"
    ZIP = "zip"
    SEVENZ = "7z"
    CHD = "chd"
    CSO = "cso"
    XISO = "xiso"
    RVZ = "rvz"
    SQUASHFS = "sqfs"
    JB = "jb"  # PS3 decrypted folder
    GZIP = "gzip"  # PS3 ISO compression for ps3netsrv


class SystemType(str, Enum):
    """System complexity types."""

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
    system_type: SystemType = Field(description="System complexity type")
    dat: DATConfig = Field(description="DAT configuration")
    sources: List[SourceConfig] = Field(description="Source ROM locations")
    lists: Optional[ListFileConfig] = Field(
        None, description="List file configuration"
    )
    compression: Optional[CompressionConfig] = Field(
        None, description="Default compression for this platform"
    )
    targets: List[TargetProfile] = Field(description="Output targets")
    enabled: bool = Field(True, description="Enable this platform")

    # System-specific settings
    extract_archives: bool = Field(
        False, description="Extract ZIP archives (False for No-Intro)"
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
        # Simple systems (No-Intro) should not extract
        if self.system_type == SystemType.SIMPLE and self.extract_archives:
            raise ValueError(
                f"Platform {self.name}: SIMPLE systems should not extract archives"
            )

        # Redump systems should extract
        if (
            self.system_type in [SystemType.MEDIUM, SystemType.COMPLEX]
            and not self.extract_archives
        ):
            raise ValueError(
                f"Platform {self.name}: MEDIUM/COMPLEX systems should extract archives"
            )

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
