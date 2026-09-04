"""Pydantic models for configuration validation.

Note: Default paths are intentionally set to None or relative paths.
Use romfarmer.core.paths.PathResolver for runtime path resolution.
"""

import contextvars
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class DATSource(str, Enum):
    """DAT file source types."""

    NONE = "none"  # No DAT — digital-only platforms (WiiWare, etc.)
    RETOOL_1G1R_ENG = "retool_1g1r_eng"
    RETOOL_1G1R_ALL = "retool_1g1r_all"
    RETOOL_1G1R_USA = "retool_1g1r_usa"
    NOINTRO_STANDARD = "nointro_standard"
    REDUMP_STANDARD = "redump_standard"
    REDUMP_RETOOL_1G1R_ENG = "redump_retool_1g1r_eng"  # Redump with Retool filtering
    REDUMP_RETOOL_1G1R_USA = "redump_retool_1g1r_usa"
    MANUAL_SCAN = "manual_scan"  # For PS3, etc.
    # Arcade sources
    MAME_OFFICIAL = "mame_official"  # MAME official DAT
    MAME = "mame"  # Filter from MAME DAT by driver
    FBNEO_OFFICIAL = "fbneo_official"  # FBNeo official DAT
    HBMAME_OFFICIAL = "hbmame_official"  # HBMAME official DAT


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
    RVZ = "rvz"  # Unzip RVZ archives (Wii/GameCube)
    WUX = "wux"  # Unzip WUX archives (Wii U)
    PS3 = "ps3"  # Decrypt and extract PS3 ISO to JB folder format
    XISO = "xiso"  # Convert Redump ISO to XISO format (Xbox/Xbox 360)
    MIXED = "mixed"  # Platform has both cartridge and disc games


class PatternType(str, Enum):
    """Pattern matching types for selection filters."""

    GLOB = "glob"  # Shell-style wildcards (*.USA*, [A-M]*)
    REGEX = "regex"  # Full regex support


class SelectionStrategy(str, Enum):
    """Strategies for selecting files in selection filters."""

    FIRST = "first"  # First N files (after sorting)
    LAST = "last"  # Last N files (after sorting)
    RANDOM = "random"  # Random N files
    LARGEST = "largest"  # N largest files by size
    SMALLEST = "smallest"  # N smallest files by size
    ALPHABETICAL = "alphabetical"  # First N alphabetically
    RATING_BUDGET = "rating_budget"  # Quality-based with size budget


# Backward compatibility alias
ScopeStrategy = SelectionStrategy


class SelectionSortBy(str, Enum):
    """Sort criteria for selection filters."""

    NAME = "name"  # Sort by filename
    SIZE = "size"  # Sort by file size
    MODIFIED = "modified"  # Sort by modification time


# Backward compatibility alias
ScopeSortBy = SelectionSortBy


class SelectionPattern(BaseModel):
    """Pattern configuration for selection filters."""

    type: PatternType = Field(default=PatternType.GLOB, description="Pattern matching type")
    value: str = Field(description="Pattern to match against filenames")


# Backward compatibility alias
ScopePattern = SelectionPattern


class SelectionSort(BaseModel):
    """Sort configuration for selection filters."""

    by: SelectionSortBy = Field(default=SelectionSortBy.NAME, description="What to sort by")
    order: str = Field(default="asc", description="Sort order: asc or desc")


# Backward compatibility alias for SelectionSort
ScopeSort = SelectionSort


class SelectionConfig(BaseModel):
    """Selection filter configuration for choosing which ROMs to include."""

    name: str | None = Field(
        None, description="Selection configuration name (for referenced configs)"
    )
    description: str | None = Field(None, description="Human-readable description")

    # Strategy and limits
    strategy: SelectionStrategy = Field(
        default=SelectionStrategy.FIRST, description="Selection strategy"
    )
    limit: int | None = Field(None, description="Maximum number of games to select", gt=0)
    percentage: float | None = Field(
        None, description="Select percentage of games (e.g., 20 for first 20%)", gt=0, le=100
    )
    offset: float | None = Field(
        None,
        description="Skip this percentage before selecting (for phased builds, e.g., offset=20 skips first 20%)",
        ge=0,
        lt=100,
    )

    # Pattern filtering (optional, applied before strategy)
    pattern: SelectionPattern | None = Field(None, description="Pattern to filter filenames")

    # Metadata-based exclusions
    exclude_hidden: bool = Field(
        default=False, description="Exclude games marked as hidden in EmulationStation metadata"
    )
    exclude_unrated: bool = Field(
        default=False, description="Exclude games with no rating (rating = 0.0 or NULL)"
    )
    exclude_demos: bool = Field(
        default=False, description="Exclude demos, betas, protos, samples (filename-based)"
    )

    # Region preferences for 1G1R and region pass (highest priority first)
    # e.g. ["USA", "World", "Europe", "Japan"]
    preferred_regions: list[str] = Field(
        default_factory=list,
        description="Region preferences in priority order (highest first). "
        "Consumed by the 1G1R and region planner passes.",
    )

    # Rating budget options (for RATING_BUDGET strategy)
    max_size_gb: float | None = Field(
        None, description="Maximum total size in GB (for rating_budget strategy)", gt=0
    )
    min_rating: float | None = Field(
        None,
        description="Minimum rating threshold 0.0-1.0 (for rating_budget strategy)",
        ge=0.0,
        le=1.0,
    )
    top_n: int | None = Field(None, description="Keep at most the N highest-rated games", ge=1)
    unrated: Literal["keep", "drop"] = Field(
        "keep",
        description="Rating pass: what to do with unrated games when min_rating is set",
    )
    unrated_as: str = Field(
        "median",
        description="Budget pass: rank unrated games as 'median' (of rated games, per platform), "
        "'worst', 'best', or a 0.0-1.0 float",
    )
    safety_margin: float = Field(
        0.0,
        description="Retired (2026-09-03): fixed headroom fraction. The aggregate p90 headroom in "
        "PlanSummary is the constraint. Kept for legacy configs that set it explicitly.",
        ge=0.0,
        lt=1.0,
    )

    # Sorting (optional)
    sort: SelectionSort | None = Field(
        None, description="Sort configuration before applying strategy"
    )

    # Random seed (for reproducible RANDOM strategy)
    seed: int | None = Field(
        None, description="Random seed for reproducible RANDOM strategy selection"
    )


# Backward compatibility alias
ScopeConfig = SelectionConfig


class SystemType(str, Enum):
    """System complexity types - DEPRECATED, use extraction config instead."""

    SIMPLE = "simple"  # No-Intro ZIPs, no extraction
    MEDIUM = "medium"  # Redump, extraction + compression
    COMPLEX = "complex"  # Multi-disc, special handling
    VERY_COMPLEX = "very_complex"  # PS3, Xbox 360 DLC, etc.


class DATConfig(BaseModel):
    """DAT file configuration."""

    source: DATSource = Field(description="DAT source type (retool preferred)")
    file: Path | None = Field(None, description="Explicit DAT file path (overrides source)")
    expected_count: int | None = Field(None, description="Expected game count for validation")
    match_method: str = Field(
        "hash",
        description="Match method: 'hash' (default, exact MD5), 'fuzzy_name' (fallback to name matching when hash fails)",
    )
    filter_driver: str | None = Field(
        None, description="MAME driver name to filter by (e.g., 'naomi', 'model2')"
    )
    filter_romof: str | None = Field(
        None, description="MAME romof/BIOS to filter by (e.g., 'naomi2' for Naomi 2 games)"
    )
    exclude_romof: list[str] | None = Field(
        None,
        description="Exclude games with these BIOS dependencies (e.g., ['naomi2'] to exclude Naomi 2 from Naomi)",
    )
    name_pattern: str | None = Field(
        None,
        description="Glob pattern to filter game names (e.g., '*SGB Enhanced*' for Super Game Boy games)",
    )
    exclude_name_pattern: str | None = Field(
        None,
        description="Glob pattern to exclude game names (e.g., '*SGB Enhanced*' to exclude Super Game Boy games from base set)",
    )

    @field_validator("file")
    @classmethod
    def validate_file_exists(cls, v: Path | None) -> Path | None:
        """Validate DAT file exists if specified."""
        if v is not None and not v.exists():
            raise ValueError(f"DAT file not found: {v}")
        return v


# Load-time switch for SourceConfig's path-exists check (see load_slim_platform).
CHECK_SOURCE_PATHS: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "romfarmer_check_source_paths", default=True
)


class SourceConfig(BaseModel):
    """Source ROM configuration."""

    path: Path | None = Field(None, description="Source directory path (absolute)")
    root: str | None = Field(None, description="Source root ID (from sources.yaml)")
    subdir: str | None = Field(None, description="Subdirectory relative to root")
    type: str = Field("myrient", description="Source type (myrient, custom, etc.)")
    recursive: bool = Field(True, description="Scan subdirectories")

    @model_validator(mode="after")
    def validate_path_or_root(self):
        """Ensure either path or root+subdir is specified."""
        if not self.path and not self.root:
            raise ValueError("Either 'path' or 'root' must be specified for source")

        # If path is specified, it must exist — unless the loader says the paths
        # are not going to be used (a Spec supplies its own sources; the bare-
        # environment gate must not need this host's mounts).
        if self.path and CHECK_SOURCE_PATHS.get() and not self.path.exists():
            # We allow non-existent paths if we are going to resolve them later via root?
            # No, Pydantic validation happens at load time.
            # If we use 'root', 'path' will be None initially, so this check is fine.
            # But if 'path' is provided, it should exist.
            raise ValueError(f"Source path not found: {self.path}")

        return self


class ListFileConfig(BaseModel):
    """List file configuration."""

    directory: Path = Field(description="Directory containing list files")
    patterns: dict[str, str] = Field(
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
    max_files_per_group: int | None = Field(50, description="Max files per group for MINIMAL style")
    create_subdirs: bool = Field(True, description="Create subdirectories for list files")
    subdir_prefix: str | None = Field(None, description="Prefix for subdirectories (e.g., '_')")


class CompressionConfig(BaseModel):
    """Compression configuration."""

    format: CompressionFormat = Field(description="Target compression format")
    tool: str | None = Field(None, description="Compression tool path")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Tool-specific parameters")
    verify: bool = Field(True, description="Verify compressed files")


class ExtractionConfig(BaseModel):
    """Extraction configuration for archives and disc images."""

    enabled: bool = Field(default=False, description="Enable extraction")
    type: ExtractionType = Field(
        default=ExtractionType.NONE, description="Type of content to extract"
    )
    # PS3-specific settings
    keys_directory: Path | None = Field(None, description="PS3 disc keys directory")
    ps3dec_path: Path | None = Field(None, description="Path to PS3Dec tool")
    # Xbox XISO settings
    extract_xiso_path: Path | None = Field(None, description="Path to extract-xiso tool")


class PS3UpdatesConfig(BaseModel):
    """PS3 updates configuration."""

    enabled: bool = Field(default=True, description="Apply official game updates")
    nps_database: Path | None = Field(
        default=None, description="NoPayStation database path (PS3_DLCS.tsv)"
    )
    pkg_archive: Path | None = Field(default=None, description="PKG archive directory")
    use_sony_psn: bool = Field(default=True, description="Also check Sony PSN cache for updates")


class PS3DLCMode(str, Enum):
    """PS3 DLC handling modes."""

    NONE = "none"  # Don't process DLC
    EXTRACT = "extract"  # Extract and merge DLC into disc (for real PS3)
    COPY = "copy"  # Copy PKG files to _PKG folder (for RPCS3)


class PS3DLCConfig(BaseModel):
    """PS3 DLC configuration."""

    enabled: bool = Field(default=False, description="Enable DLC processing")
    mode: PS3DLCMode = Field(
        default=PS3DLCMode.COPY,
        description="DLC handling mode: extract (merge to disc) or copy (PKG to _PKG folder)",
    )


class RatingFilterConfig(BaseModel):
    """Rating-based filtering configuration."""

    enabled: bool = Field(False, description="Enable rating-based filtering")
    top_n: int | None = Field(None, description="Keep only top N highest-rated games")
    max_size_gb: float | None = Field(
        None, description="Keep top-rated games that fit within size budget (GB)"
    )
    min_rating: float | None = Field(None, description="Minimum rating threshold (0.0-1.0)")

    @model_validator(mode="after")
    def validate_filter_criteria(self):
        """Ensure at least one filter criterion is specified if enabled."""
        if self.enabled:
            if not any([self.top_n, self.max_size_gb, self.min_rating]):
                raise ValueError(
                    "At least one filter criterion (top_n, max_size_gb, min_rating) "
                    "must be specified when rating_filter is enabled"
                )
        return self


class GenerationFilterConfig(BaseModel):
    """Cross-platform generation deduplication configuration.

    Implements "1 Game 1 Generation" (1G1Gen) filtering for disc-based systems.
    When enabled, games that appear on multiple platforms in the same console
    generation will be deduplicated based on platform priority.

    Example Gen 6 (PS2 > GameCube > Xbox):
        - Grand Theft Auto: Vice City exists on all three platforms
        - Result: Keep PS2 version, remove GameCube and Xbox versions
        - Lower priority platforms become "exclusives only"

    Configuration:
        generation_filter:
          enabled: true
          generation: gen6  # Use gen5, gen6, gen7, or gen4cd

    Output folders will be named like: output/gen6-dedupe-batocera/
    """

    enabled: bool = Field(False, description="Enable cross-platform generation deduplication")
    generation: str = Field(description="Generation identifier (gen5, gen6, gen7, gen4cd)")
    rescue_lists: dict[str, list[str]] | None = Field(
        None, description="Platform -> list of game names to protect from removal"
    )

    @field_validator("generation")
    @classmethod
    def validate_generation(cls, v: str) -> str:
        """Validate generation identifier."""
        valid_generations = ["gen4cd", "gen5", "gen6", "gen7"]
        if v not in valid_generations:
            raise ValueError(
                f"Invalid generation '{v}'. Must be one of: {', '.join(valid_generations)}"
            )
        return v


class TargetProfile(BaseModel):
    """Target system profile (Batocera, RocknIX, Everdrive)."""

    name: str = Field(description="Profile name")
    output_path: Path = Field(description="Output directory")
    organization: OrganizationConfig = Field(description="Organization configuration")
    compression: CompressionConfig | None = Field(
        None, description="Compression override for this target"
    )
    metadata: bool = Field(True, description="Generate metadata (gamelist.xml)")
    enabled: bool = Field(True, description="Enable this target")

    # Removed strict parent directory validation to allow for dynamic path generation
    # where the parent directory might not exist yet.


class MetadataFilterConfig(BaseModel):
    """Metadata-driven ROM filter configuration.

    Runs after DAT matching (once MD5s are known) and drops or keeps ROMs
    based on their ``scraped_games`` database entry.  All conditions are
    ANDed together — a ROM must pass every active condition to survive.

    Typical uses::

        # Strip nongames + hidden entries from every build
        metadata_filter:
          exclude_nongames: true
          exclude_hidden: true

        # Shoot-em-up target — keep only matching genres
        metadata_filter:
          include_genres:
            - "Shoot'em Up"
            - "Shoot'em Up / Vertical"
            - "Shoot'em Up / Horizontal"
            - "Shooter"
          require_metadata: false   # keep unscraped ROMs too

        # Quality cut
        metadata_filter:
          min_rating: 0.7
          exclude_nongames: true
    """

    # --- Name-based ---
    exclude_nongames: bool = Field(
        default=False,
        description="Exclude entries whose scraped name starts with 'ZZZ' (ARRM nongame marker)",
    )
    exclude_name_patterns: list[str] = Field(
        default_factory=list,
        description=(
            "Glob patterns matched against the scraped game name.  "
            "Any match → exclude.  E.g. ['ZZZ*', '*[BIOS]*']"
        ),
    )

    # --- Genre ---
    include_genres: list[str] = Field(
        default_factory=list,
        description=(
            "Whitelist of genre substrings.  A ROM is kept if its scraped genre "
            "contains ANY of these strings (case-insensitive).  "
            "ROMs with no genre are kept unless require_metadata=True."
        ),
    )
    exclude_genres: list[str] = Field(
        default_factory=list,
        description=(
            "Blacklist of genre substrings.  A ROM is excluded if its scraped genre "
            "contains ANY of these strings (case-insensitive)."
        ),
    )

    # --- Rating ---
    min_rating: float | None = Field(
        default=None,
        description="Minimum ScreenScraper rating (0.0–1.0).  ROMs below this are excluded.",
        ge=0.0,
        le=1.0,
    )

    # --- Players ---
    min_players: int | None = Field(
        default=None,
        description=(
            "Minimum player count.  E.g. min_players=2 keeps only multiplayer games.  "
            "Parsed from scraped 'players' field ('1', '1-2', '1-4', '4+', ...)."
        ),
        ge=1,
    )

    # --- Flags ---
    exclude_hidden: bool = Field(
        default=False,
        description="Exclude ROMs whose scraped_games.hidden flag is set.",
    )

    # --- Metadata presence ---
    require_metadata: bool = Field(
        default=False,
        description=(
            "When True, ROMs with no scraped_games entry are excluded.  "
            "When False (default), unscraped ROMs always pass through."
        ),
    )
    has_metadata: bool = Field(
        default=False,
        description=(
            "When True, only include ROMs that have a scraped_games entry.  "
            "Alias for require_metadata=True (more readable in configs)."
        ),
    )

    @model_validator(mode="after")
    def sync_has_metadata(self) -> "MetadataFilterConfig":
        """has_metadata=True implies require_metadata=True."""
        if self.has_metadata:
            self.require_metadata = True
        return self


class PlatformConfig(BaseModel):
    """Configuration for a single platform (NES, Saturn, etc.)."""

    name: str = Field(description="Platform name")
    type: str | None = Field(
        None, description="Platform type: 'arcade' for arcade systems, None for consoles"
    )
    emulator: str | None = Field(
        None, description="Emulator name (e.g., 'fbneo', 'mame', 'flycast')"
    )
    metadata_system: str | None = Field(
        None,
        description="System name to use for metadata lookups (defaults to platform name). "
        "Useful for platforms that share ROMs (e.g., Sega arcade platforms use 'mame')",
    )
    system_type: SystemType | None = Field(
        None, description="System complexity type (DEPRECATED - use extraction config)"
    )
    dat: DATConfig | None = Field(None, description="DAT configuration")
    sources: list[SourceConfig] = Field(description="Source ROM locations")
    chd_sources: list[SourceConfig] | None = Field(
        None, description="CHD source locations (arcade platforms)"
    )
    arcade_filter: dict[str, Any] | None = Field(
        None, description="Arcade-specific filter configuration"
    )
    lists: ListFileConfig | None = Field(None, description="List file configuration")
    extraction: ExtractionConfig = Field(
        default_factory=lambda: ExtractionConfig(enabled=False, type=ExtractionType.NONE),
        description="Extraction configuration",
    )
    updates: PS3UpdatesConfig | None = Field(None, description="PS3 updates configuration")
    dlc: PS3DLCConfig | None = Field(None, description="PS3 DLC configuration")
    selection: SelectionConfig | None = Field(
        None, description="Selection filter configuration (replaces rating_filter)"
    )
    metadata_filter: MetadataFilterConfig | None = Field(
        None, description="Metadata-driven filter (genre, rating, players, nongames, etc.)"
    )
    rating_filter: RatingFilterConfig = Field(
        default_factory=lambda: RatingFilterConfig(enabled=False),
        description="Rating-based filtering configuration (DEPRECATED - use selection instead)",
    )
    compression: CompressionConfig | None = Field(
        None, description="Default compression for this platform"
    )
    targets: list[TargetProfile] = Field(description="Output targets")
    enabled: bool = Field(True, description="Enable this platform")

    # Legacy settings - kept for backward compatibility
    extract_archives: bool | None = Field(
        None, description="DEPRECATED: Use extraction.enabled instead"
    )
    multi_disc_handling: bool = Field(False, description="Enable multi-disc detection")
    custom_stages: list[str] = Field(default_factory=list, description="Custom stage names")

    @model_validator(mode="after")
    def validate_platform_config(self) -> "PlatformConfig":
        """Validate platform configuration consistency."""
        import warnings

        # Track if user explicitly set extraction.enabled
        user_set_extraction = self.extraction.enabled or self.extraction.type != ExtractionType.NONE

        # Deprecation warning for system_type
        if self.system_type is not None:
            warnings.warn(
                f"Platform '{self.name}': 'system_type' is deprecated. "
                "Use 'extraction' config instead. See docs for migration guide.",
                DeprecationWarning,
                stacklevel=2,
            )

        # Migrate legacy extract_archives to new extraction config
        if self.extract_archives is not None:
            warnings.warn(
                f"Platform '{self.name}': 'extract_archives' is deprecated. "
                "Use 'extraction.enabled' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            self.extraction.enabled = self.extract_archives
            user_set_extraction = True  # User explicitly set via legacy field

        # Auto-detect extraction type from system_type only if not explicitly set
        if self.system_type is not None and not user_set_extraction:
            if self.system_type == SystemType.SIMPLE:
                self.extraction.enabled = False
            elif self.system_type == SystemType.COMPLEX:
                # COMPLEX systems (Wii/GameCube) use RVZ extraction
                self.extraction.enabled = True
                self.extraction.type = ExtractionType.RVZ
            elif self.system_type == SystemType.VERY_COMPLEX:
                # VERY_COMPLEX systems like PS3
                self.extraction.enabled = True
                self.extraction.type = ExtractionType.PS3
            elif self.system_type == SystemType.MEDIUM:
                self.extraction.enabled = True
                # Try to infer type from compression format
                if self.compression and self.compression.format == CompressionFormat.CHD:
                    self.extraction.type = ExtractionType.DISC
                else:
                    # Default to cartridge if extracting but not CHD
                    self.extraction.type = ExtractionType.CARTRIDGE

        # If user set extraction.enabled but no type, try to infer from system_type or compression
        if self.extraction.enabled and self.extraction.type == ExtractionType.NONE:
            if self.system_type == SystemType.COMPLEX:
                self.extraction.type = ExtractionType.RVZ
            elif self.system_type == SystemType.VERY_COMPLEX:
                self.extraction.type = ExtractionType.PS3
            elif self.compression and self.compression.format == CompressionFormat.CHD:
                self.extraction.type = ExtractionType.DISC
            else:
                self.extraction.type = ExtractionType.CARTRIDGE

        return self


class BuildType(str, Enum):
    """Build types for different use cases."""

    TARGET = "target"  # Multi-system build for a target (frontend + device)
    SYSTEM = "system"  # Single platform build
    LEGACY = "legacy"  # Old-style build (for backwards compatibility during migration)


class TierStrategy(str, Enum):
    """Selection strategy for platform tiers."""

    ALWAYS_INCLUDE = "always_include"  # Include entire 1G1R set
    BEST_OF = "best_of"  # Use best-of list only
    BEST_OF_EXTENDED = "best_of_extended"  # Best-of + notable games
    SKIP = "skip"  # Don't include this tier


class TierDefinition(BaseModel):
    """Definition of a single platform tier."""

    description: str = ""
    default_strategy: TierStrategy = TierStrategy.ALWAYS_INCLUDE
    estimated_total_mb: int | None = None  # For Tier 1/2 (total)
    estimated_per_platform_mb: int | None = None  # For Tier 3+ (per platform)
    platforms: list[str] = Field(default_factory=list)


class AllocationRules(BaseModel):
    """Rules for allocating storage budget across tiers."""

    guaranteed_tiers: list[int] = Field(default_factory=lambda: [1, 2])
    guaranteed_reserve_percent: int = 10
    tier_3_threshold_gb: int = 64
    tier_3_max_percent: int = 40
    tier_4_threshold_gb: int = 128
    tier_4_max_percent: int = 30
    tier_5_threshold_gb: int = 500
    tier_5_max_percent: int = 50


class StorageProfile(BaseModel):
    """Pre-defined storage profile for common scenarios."""

    description: str = ""
    max_tier: int = 5
    tier_3_strategy: TierStrategy = TierStrategy.BEST_OF
    tier_4_strategy: TierStrategy = TierStrategy.BEST_OF
    tier_5_strategy: TierStrategy = TierStrategy.SKIP

    @field_validator("tier_3_strategy", "tier_4_strategy", "tier_5_strategy", mode="before")
    @classmethod
    def validate_strategy(cls, v):
        """Convert string to TierStrategy enum."""
        if isinstance(v, str):
            return TierStrategy(v)
        return v


class PlatformTiersConfig(BaseModel):
    """Platform tier system configuration.

    Defines storage priority for platforms when building space-constrained targets.
    Loaded from config/platform_tiers.yaml.
    """

    tier_1: TierDefinition = Field(default_factory=TierDefinition)
    tier_2: TierDefinition = Field(default_factory=TierDefinition)
    tier_3: TierDefinition = Field(default_factory=TierDefinition)
    tier_4: TierDefinition = Field(default_factory=TierDefinition)
    tier_5: TierDefinition = Field(default_factory=TierDefinition)
    allocation_rules: AllocationRules = Field(default_factory=AllocationRules)
    profiles: dict[str, StorageProfile] = Field(default_factory=dict)

    def get_tier(self, tier_num: int) -> TierDefinition:
        """Get tier definition by number."""
        tier_map = {
            1: self.tier_1,
            2: self.tier_2,
            3: self.tier_3,
            4: self.tier_4,
            5: self.tier_5,
        }
        return tier_map.get(tier_num, TierDefinition())

    def get_platform_tier(self, platform: str) -> int | None:
        """Get the tier number for a platform.

        Returns:
            Tier number (1-5) or None if platform not in any tier
        """
        for tier_num in range(1, 6):
            tier = self.get_tier(tier_num)
            if platform in tier.platforms:
                return tier_num
        return None

    def get_profile(self, profile_name: str) -> StorageProfile | None:
        """Get a storage profile by name."""
        return self.profiles.get(profile_name)

    def get_strategy_for_tier(
        self, tier_num: int, profile: StorageProfile | None = None
    ) -> TierStrategy:
        """Get the selection strategy for a tier.

        Args:
            tier_num: Tier number (1-5)
            profile: Optional storage profile to override defaults

        Returns:
            TierStrategy for the tier
        """
        if profile:
            # Profile overrides for tiers 3-5
            if tier_num == 3:
                return profile.tier_3_strategy
            elif tier_num == 4:
                return profile.tier_4_strategy
            elif tier_num == 5:
                return profile.tier_5_strategy
            # Tiers 1-2 always use always_include
            return TierStrategy.ALWAYS_INCLUDE

        # Use tier's default strategy
        return self.get_tier(tier_num).default_strategy


class BuildConfig(BaseModel):
    """Master build configuration (e.g., rocknix-512gb.yaml).

    Supports two build modes:

    1. TARGET BUILD (type: target)
       - Builds multiple platforms for a specific target (frontend + device)
       - Output folder: {frontend}-{device}-{storage}-{profile}/
       - Example: rocknix-r36s-512gb-complete/

    2. SYSTEM BUILD (type: system)
       - Builds a single platform with specific settings
       - Output folder: {platform}-{compression}-{selection}/
       - Example: saturn-chd-all/

    Also supports nested orchestration via the 'includes' field for complex builds.

    Example (Target Build):
        name: r36s-complete
        type: target
        target: rocknix-r36s
        storage_budget: 512gb
        profile: complete
        platforms: all

    Example (System Build):
        name: saturn-chd-all
        type: system
        platform: saturn
        compression: chd
        selection: all

    Example (Legacy Build - backwards compatible):
        name: 1tb-batocera
        includes:
          - nointro-1g1r-eng-7z-batocera
          - redump-1g1r-eng-chd-batocera
        excludes:
          - 3ds
        platforms: []
    """

    name: str = Field(description="Build name")
    description: str | None = Field(None, description="Build description")
    version: str | None = Field(None, description="Build version")

    # ═══════════════════════════════════════════════════════════════════════════
    # NEW: Build type and target configuration
    # ═══════════════════════════════════════════════════════════════════════════
    build_type: BuildType | None = Field(
        default=None,
        description="Build type: 'target' (multi-system), 'system' (single platform), or None (legacy)",
    )
    target: str | None = Field(
        default=None,
        description="Target name for target builds (e.g., 'rocknix-r36s', 'batocera-pc')",
    )
    storage_budget: str | None = Field(
        default=None, description="Storage budget (e.g., '512gb', '1tb', 'unlimited')"
    )
    profile: str | None = Field(
        default=None,
        description="Build profile name for output folder (e.g., 'complete', 'test-10games', 'favorites')",
    )
    platform_budgets: dict[str, str] = Field(
        default_factory=dict,
        description="Per-platform storage budgets (e.g., {'psx': '80gb', '3ds': '50gb'})",
    )

    # For system builds (single platform)
    platform: str | None = Field(
        default=None, description="Single platform for system builds (e.g., 'saturn')"
    )
    compression: str | None = Field(
        default=None, description="Compression format for system builds (e.g., 'chd', 'zip', '7z')"
    )
    selection: str | None = Field(
        default=None,
        description="Selection name for system builds (e.g., 'all', 'japanese', 'top30')",
    )

    # Selection override for special builds (e.g., test builds with 10 games per system)
    selection_override: SelectionConfig | None = Field(
        default=None,
        description="Override selection for all platforms (e.g., limit to 10 games for testing)",
    )

    # Generation-based cross-platform deduplication (1G1Gen)
    generation_filter: GenerationFilterConfig | None = Field(
        default=None, description="Cross-platform generation deduplication configuration (1G1Gen)"
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # Legacy fields (still supported for backwards compatibility)
    # ═══════════════════════════════════════════════════════════════════════════
    includes: list[str] = Field(
        default_factory=list,
        description="Other orchestration configs to include (processed before platforms)",
    )
    excludes: list[str] = Field(
        default_factory=list,
        description="Platforms to exclude from the final build (applied after includes)",
    )
    platforms: list[str] = Field(
        default_factory=list,
        description="Platform config files to include (in addition to includes)",
    )
    global_dat_priority: list[DATSource] = Field(
        default=[
            DATSource.RETOOL_1G1R_ENG,
            DATSource.RETOOL_1G1R_USA,
            DATSource.NOINTRO_STANDARD,
            DATSource.REDUMP_STANDARD,
        ],
        description="Global DAT source priority",
    )
    global_lists: ListFileConfig | None = Field(None, description="Global list file configuration")
    workspace: Path | None = Field(
        None,
        description="Workspace root directory (auto-detected if not set)",
    )
    dat_directory: Path | None = Field(
        None, description="DAT files directory (defaults to workspace/dats)"
    )
    checkpoint_enabled: bool = Field(True, description="Enable checkpointing for resume")
    parallel_platforms: bool = Field(False, description="Process platforms in parallel")
    max_workers: int = Field(4, description="Max parallel workers")

    # Added fields for flexibility
    settings: dict[str, Any] = Field(default_factory=dict, description="Build execution settings")
    storage: dict[str, Any] = Field(default_factory=dict, description="Storage paths configuration")
    platform_overrides: dict[str, Any] = Field(
        default_factory=dict, description="Platform-specific overrides"
    )

    # Post-build hooks - commands to run after all platforms complete
    post_build: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Commands to run after build completes (e.g., jdupes for deduplication)",
    )

    # Deployment configuration
    deploy: dict[str, Any] | None = Field(
        None, description="Deployment configuration (rsync to target device)"
    )

    @field_validator("workspace", "dat_directory", mode="before")
    @classmethod
    def validate_directory_exists(cls, v: Path | None) -> Path | None:
        """Validate directory exists if specified."""
        if v is not None and not Path(v).exists():
            raise ValueError(f"Directory not found: {v}")
        return v

    @model_validator(mode="after")
    def validate_has_content(self):
        """Validate build configuration based on build type."""
        # Determine build type if not explicitly set
        if self.build_type is None:
            if self.target is not None:
                # Has target = target build
                object.__setattr__(self, "build_type", BuildType.TARGET)
            elif self.platform is not None and self.compression is not None:
                # Has single platform + compression = system build
                object.__setattr__(self, "build_type", BuildType.SYSTEM)
            elif self.includes or self.platforms:
                # Has includes/platforms = legacy build
                object.__setattr__(self, "build_type", BuildType.LEGACY)

        # Validate based on build type
        if self.build_type == BuildType.TARGET:
            if not self.target:
                raise ValueError("Target builds require 'target' field")
            if not self.profile:
                raise ValueError("Target builds require 'profile' field")
            # storage_budget defaults to 'unlimited' if not specified
            if not self.storage_budget:
                object.__setattr__(self, "storage_budget", "unlimited")

        elif self.build_type == BuildType.SYSTEM:
            if not self.platform:
                raise ValueError("System builds require 'platform' field")
            if not self.compression:
                raise ValueError("System builds require 'compression' field")
            # selection defaults to 'all' if not specified
            if not self.selection:
                object.__setattr__(self, "selection", "all")

        elif self.build_type == BuildType.LEGACY or self.build_type is None:
            # Legacy validation: must have includes or platforms
            if not self.includes and not self.platforms:
                raise ValueError(
                    "Legacy builds require at least one of 'includes' or 'platforms'. "
                    "Or specify 'target' for a target build, or 'platform' + 'compression' for a system build."
                )

        return self

    def get_output_folder_name(self) -> str:
        """Generate the output folder name based on build type.

        Returns:
            Output folder name string
        """
        if self.build_type == BuildType.TARGET:
            # Will be computed with composed target: {frontend}-{device}-{storage}-{profile}
            # For now, return a placeholder that will be resolved later
            return f"{self.target}-{self.storage_budget}-{self.profile}"

        elif self.build_type == BuildType.SYSTEM:
            return f"{self.platform}-{self.compression}-{self.selection}"

        else:
            # Legacy: use the build name
            return self.name

    def is_target_build(self) -> bool:
        """Check if this is a target build."""
        return self.build_type == BuildType.TARGET

    def is_system_build(self) -> bool:
        """Check if this is a system build."""
        return self.build_type == BuildType.SYSTEM

    def is_legacy_build(self) -> bool:
        """Check if this is a legacy build."""
        return self.build_type == BuildType.LEGACY or self.build_type is None
