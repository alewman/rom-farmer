"""Target configuration models.

Targets compose a Frontend and Device together. They represent a specific
deployment scenario like "RocknIX on R36S" or "Batocera on Steam Deck".

Targets can also define overrides for specific combinations.
"""

from typing import Any

from pydantic import BaseModel, Field

from .device import DeviceConfig
from .frontend import FrontendConfig, MediaType


class TargetOverrides(BaseModel):
    """Target-specific overrides that modify frontend/device behavior."""

    # Platform-specific overrides at the target level
    platforms: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Per-platform overrides (e.g., disable a platform for this target)",
    )

    # Additional unsupported platforms beyond device limits
    additional_unsupported: list[str] = Field(
        default_factory=list, description="Additional platforms to exclude for this specific target"
    )


class TargetConfig(BaseModel):
    """Configuration for a target (frontend + device combination).

    A target represents a specific deployment scenario. It references
    a frontend (software) and device (hardware) and can provide
    target-specific overrides.

    Examples:
        - rocknix-r36s: RocknIX frontend on R36S handheld
        - batocera-pc: Batocera frontend on desktop PC
        - batocera-steamdeck: Batocera frontend on Steam Deck
    """

    name: str = Field(description="Target identifier (e.g., 'rocknix-r36s')")
    description: str | None = Field(
        default=None, description="Human-readable description of the target"
    )

    # References to frontend and device configs
    frontend: str = Field(description="Frontend name (must match a frontend config file)")
    device: str = Field(description="Device name (must match a device config file)")

    # Target-specific overrides
    overrides: TargetOverrides = Field(
        default_factory=TargetOverrides, description="Target-specific overrides"
    )


class ComposedTarget(BaseModel):
    """A fully resolved target with frontend and device configs loaded.

    This is the runtime representation of a target after all configs
    have been loaded and composed together.
    """

    name: str = Field(description="Target name")
    description: str | None = Field(default=None)

    # Loaded configurations
    frontend: FrontendConfig = Field(description="Loaded frontend configuration")
    device: DeviceConfig = Field(description="Loaded device configuration")

    # Original target config for reference
    target_config: TargetConfig = Field(description="Original target configuration")

    def supports_platform(self, platform: str) -> bool:
        """Check if this target supports a platform.

        Platform must be supported by BOTH frontend (has config) and device
        (not in unsupported list).

        Args:
            platform: Platform name to check

        Returns:
            True if both frontend and device support the platform
        """
        # Check device support
        if not self.device.supports_platform(platform):
            return False

        # Check target-specific exclusions
        if platform.lower() in [
            p.lower() for p in self.target_config.overrides.additional_unsupported
        ]:
            return False

        # Frontend support is more flexible - if no platform config, we assume
        # it's supported with default settings
        return True

    def get_folder_name(self, platform: str) -> str:
        """Get the folder name for a platform on this target.

        Args:
            platform: Internal platform name

        Returns:
            Target-specific folder name
        """
        return self.frontend.get_folder_name(platform)

    def get_preferred_compression(self, platform: str, default: str = "none") -> str:
        """Get the preferred compression format for a platform.

        Args:
            platform: Internal platform name
            default: Default if not specified

        Returns:
            Preferred compression format
        """
        compression = self.frontend.get_preferred_compression(platform, default)
        # Apply fallback if needed
        return self.frontend.apply_compression_fallback(compression)

    def get_extensions(self, platform: str) -> list[str] | None:
        """Get supported file extensions for a platform.

        Args:
            platform: Internal platform name

        Returns:
            List of supported extensions, or None if not specified
        """
        return self.frontend.get_extensions(platform)

    def supports_media(self, media_type: MediaType) -> bool:
        """Check if this target supports a media type.

        Args:
            media_type: The media type to check

        Returns:
            True if frontend supports this media type
        """
        return self.frontend.supports_media(media_type)

    def get_unsupported_platforms(self) -> list[str]:
        """Get all platforms that are not supported by this target.

        Combines device unsupported + target-specific additional unsupported.

        Returns:
            List of unsupported platform names
        """
        unsupported = set(self.device.unsupported_platforms)
        unsupported.update(self.target_config.overrides.additional_unsupported)
        return sorted(unsupported)

    def get_optimal_image_size(self):
        """Get optimal image size based on device display.

        Returns:
            Tuple of (width, height)
        """
        return self.device.get_optimal_image_size()

    def generate_output_folder_name(self, storage_budget: str, profile: str) -> str:
        """Generate the output folder name for this target.

        Format: {frontend}-{device}-{storage}-{profile}

        Args:
            storage_budget: Storage budget string (e.g., '512gb', 'unlimited')
            profile: Build profile (e.g., 'complete', 'test-10games')

        Returns:
            Output folder name
        """
        return f"{self.frontend.name}-{self.device.name}-{storage_budget}-{profile}"
