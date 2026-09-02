"""Recipe configuration — reusable processing templates.

A Recipe declares HOW a category of platforms should be processed.
It's the bridge between platform intrinsics (WHAT) and deployment
targets (WHERE).

Recipes are composable — a build can stack multiple recipes, with
later recipes overriding earlier ones for overlapping platforms.

Examples:
    # All cartridge platforms get 7z compression
    nointro-7z:
      platforms: [nes, snes, gb, gba, ...]
      compression: 7z
      dat_filter: retool_1g1r_eng

    # All disc platforms get CHD compression
    redump-chd:
      platforms: [psx, saturn, dreamcast, ...]
      compression: chd
      dat_filter: redump_retool_1g1r_eng

    # Test recipe: stack on top to limit to 10 games
    test-10:
      selection:
        strategy: random
        limit: 10
        seed: 42
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from .models import (
    CompressionFormat,
    MetadataFilterConfig,
    SelectionConfig,
)


class RecipeSpec(BaseModel):
    """A reusable processing template for a category of platforms.

    Recipes answer: "For these platforms, what processing choices do I want?"

    Key design decisions:
    - `platforms` is a list of platform names. Empty means "applies to all
      platforms in the build" (useful for test recipes that limit game count).
    - `compression` is a string (not enum) because the recipe doesn't validate
      against platform capabilities — the resolver does that.
    - `selection` is optional — when present, it stacks on top of whatever
      the platform would otherwise get.
    """

    name: str = Field(description="Recipe identifier (e.g., 'nointro-7z', 'redump-chd')")
    description: str = Field(
        default="", description="Human-readable description of what this recipe does"
    )

    # Which platforms this recipe applies to
    # Empty list = applies to all platforms in the build
    platforms: list[str] = Field(
        default_factory=list,
        description="Platform names this recipe applies to. Empty = all platforms in build.",
    )

    # Processing choices
    dat_filter: str | None = Field(
        None,
        description="DAT filter variant override (e.g., 'retool_1g1r_eng'). "
        "None = use platform's default dat.source.",
    )
    compression: str | None = Field(
        None,
        description="Compression format: '7z', 'zip', 'chd', 'rvz', 'none', etc. "
        "None = use platform/target default.",
    )

    # Selection/filtering
    selection: SelectionConfig | None = Field(
        None,
        description="Selection filter to apply (e.g., limit to N games, rating budget). "
        "Stacks on top of any existing selection.",
    )
    metadata_filter: MetadataFilterConfig | None = Field(
        None,
        description="Metadata-driven filter (genre, rating, players, nongames). "
        "Keeps/drops ROMs based on scraped_games DB entries.",
    )

    # List application
    apply_lists: bool | None = Field(
        None,
        description="Whether to apply keep/delete lists. "
        "None = default (True for platforms with list_patterns).",
    )

    # Metadata generation
    metadata: bool | None = Field(
        None, description="Whether to generate metadata (gamelist.xml). None = use target default."
    )

    # Arcade-specific overrides
    arcade_filter_overrides: dict[str, Any] | None = Field(
        None, description="Override arcade filter settings from platform config"
    )

    # PS3 DLC override
    ps3_dlc_enabled: bool | None = Field(
        None, description="Override PS3 DLC processing. None = use platform default."
    )
    ps3_updates_enabled: bool | None = Field(
        None, description="Override PS3 updates. None = use platform default."
    )

    @field_validator("compression")
    @classmethod
    def validate_compression(cls, v: str | None) -> str | None:
        """Validate compression format if specified."""
        if v is not None:
            valid = {"none", "7z", "zip", "chd", "cso", "rvz", "xiso", "sqfs", "jb", "gzip"}
            if v.lower() not in valid:
                raise ValueError(
                    f"Invalid compression format '{v}'. Must be one of: {', '.join(sorted(valid))}"
                )
            return v.lower()
        return v

    def applies_to(self, platform_name: str) -> bool:
        """Check if this recipe applies to a given platform.

        Args:
            platform_name: Platform identifier

        Returns:
            True if this recipe applies (empty platforms list = applies to all)
        """
        if not self.platforms:
            return True
        return platform_name in self.platforms

    def get_effective_compression(self) -> CompressionFormat | None:
        """Get the compression format as an enum, if specified.

        Returns:
            CompressionFormat enum or None
        """
        if self.compression is None:
            return None

        # Map string to enum
        compression_map = {
            "none": CompressionFormat.NONE,
            "7z": CompressionFormat.SEVENZ,
            "zip": CompressionFormat.ZIP,
            "chd": CompressionFormat.CHD,
            "cso": CompressionFormat.CSO,
            "rvz": CompressionFormat.RVZ,
            "xiso": CompressionFormat.XISO,
            "sqfs": CompressionFormat.SQUASHFS,
            "jb": CompressionFormat.JB,
            "gzip": CompressionFormat.GZIP,
        }
        return compression_map.get(self.compression)
