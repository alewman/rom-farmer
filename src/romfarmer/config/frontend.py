"""Frontend configuration models.

Frontends represent software distributions like Batocera, RocknIX, RetroDeck, etc.
They define:
- Folder naming conventions (what the frontend calls each platform folder)
- Media support (what media types the frontend can display)
- Per-platform format support (what file extensions each emulator can open)
- Compression fallback rules
"""

from enum import Enum

from pydantic import BaseModel, Field


class MediaType(str, Enum):
    """Media types that frontends may support."""

    IMAGE = "image"  # Box art, screenshots
    MIX = "mix"  # Combined artwork (miximage)
    WHEEL = "wheel"  # Logo wheels
    MARQUEE = "marquee"  # Marquee images
    VIDEO = "video"  # Video previews
    MANUAL = "manual"  # PDF manuals
    CARTRIDGE = "cartridge"  # 3D cartridge renders
    FANART = "fanart"  # Fan artwork
    TITLESCREEN = "titlescreen"  # Title screen captures
    BOXBACK = "boxback"  # Back of box images


class FrontendPlatformConfig(BaseModel):
    """Per-platform configuration within a frontend.

    Defines what file extensions the frontend's emulator for this platform
    can open, and the preferred compression format.
    """

    extensions: list[str] = Field(
        description="File extensions the emulator can open (e.g., ['.nes', '.zip', '.7z'])"
    )
    preferred_compression: str = Field(
        default="none",
        description="Preferred compression format: none, zip, 7z, chd, cso, rvz, etc.",
    )
    folder: str | None = Field(
        default=None,
        description="Override folder name for this platform (if different from folder_mapping)",
    )


class FrontendDefaults(BaseModel):
    """Default settings for builds targeting this frontend."""

    organization: str = Field(
        default="flat", description="Default organization style: flat, balanced, minimal"
    )
    metadata: bool = Field(default=True, description="Generate metadata (gamelist.xml) by default")


class FrontendConfig(BaseModel):
    """Configuration for a frontend (Batocera, RocknIX, etc.).

    A frontend is a software distribution that runs on hardware devices.
    It defines how ROM files should be organized, what formats are supported,
    and what media types can be displayed.
    """

    name: str = Field(description="Frontend identifier (e.g., 'batocera', 'rocknix')")
    description: str | None = Field(
        default=None, description="Human-readable description of the frontend"
    )

    # Folder mapping: internal platform name → frontend folder name
    # Only list differences from internal names
    folder_mapping: dict[str, str] = Field(
        default_factory=dict,
        description="Map internal platform names to frontend folder names (e.g., megacd → segacd)",
    )

    # Media support: what media types this frontend can display
    media_support: list[MediaType] = Field(
        default_factory=lambda: [MediaType.IMAGE, MediaType.VIDEO],
        description="Media types this frontend can display",
    )

    # Per-platform format configuration
    # Key is platform name, value is FrontendPlatformConfig
    platforms: dict[str, FrontendPlatformConfig] = Field(
        default_factory=dict,
        description="Per-platform format configuration (extensions, compression)",
    )

    # Global compression fallback rules
    # If a requested format isn't supported, fall back to these
    compression_fallback: dict[str, str] = Field(
        default_factory=dict, description="Fallback compression formats (e.g., '7z' → 'zip')"
    )

    # Default settings for builds
    defaults: FrontendDefaults = Field(
        default_factory=FrontendDefaults,
        description="Default settings for builds targeting this frontend",
    )

    def get_folder_name(self, platform: str) -> str:
        """Get the folder name for a platform on this frontend.

        Args:
            platform: Internal platform name (e.g., 'megacd')

        Returns:
            Frontend-specific folder name (e.g., 'segacd' for RocknIX)
        """
        return self.folder_mapping.get(platform, platform)

    def get_platform_config(self, platform: str) -> FrontendPlatformConfig | None:
        """Get the platform-specific configuration.

        Args:
            platform: Internal platform name

        Returns:
            FrontendPlatformConfig if defined, None otherwise
        """
        return self.platforms.get(platform)

    def get_preferred_compression(self, platform: str, default: str = "none") -> str:
        """Get the preferred compression format for a platform.

        Args:
            platform: Internal platform name
            default: Default compression if not specified

        Returns:
            Preferred compression format string
        """
        platform_config = self.get_platform_config(platform)
        if platform_config:
            return platform_config.preferred_compression
        return default

    def get_extensions(self, platform: str) -> list[str] | None:
        """Get supported file extensions for a platform.

        Args:
            platform: Internal platform name

        Returns:
            List of extensions if defined, None otherwise
        """
        platform_config = self.get_platform_config(platform)
        if platform_config:
            return platform_config.extensions
        return None

    def supports_media(self, media_type: MediaType) -> bool:
        """Check if this frontend supports a media type.

        Args:
            media_type: The media type to check

        Returns:
            True if supported, False otherwise
        """
        return media_type in self.media_support

    def apply_compression_fallback(self, requested: str) -> str:
        """Apply compression fallback if format not supported.

        Args:
            requested: Requested compression format

        Returns:
            Either the requested format or its fallback
        """
        return self.compression_fallback.get(requested, requested)
