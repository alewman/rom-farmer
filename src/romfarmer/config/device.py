"""Device configuration models.

Devices represent hardware like R36S, Steam Deck, PC, etc.
They define:
- Display resolution and aspect ratio
- Media sizing constraints (to avoid wasting storage on oversized images)
- Unsupported platforms (systems the device's CPU can't emulate)
"""

from typing import List, Optional, Tuple

from pydantic import BaseModel, Field, field_validator


class DisplayConfig(BaseModel):
    """Display configuration for a device."""
    
    resolution: Tuple[int, int] = Field(
        default=(1920, 1080),
        description="Display resolution as (width, height)"
    )
    aspect_ratio: str = Field(
        default="16:9",
        description="Display aspect ratio (e.g., '4:3', '16:9', '16:10')"
    )
    
    @field_validator("resolution", mode="before")
    @classmethod
    def validate_resolution(cls, v):
        """Accept list or tuple for resolution."""
        if isinstance(v, list):
            return tuple(v)
        return v


class MediaSizingConfig(BaseModel):
    """Media sizing constraints to optimize storage.
    
    Images and videos larger than these limits are candidates for
    downscaling/transcoding to save storage space.
    """
    
    max_image_width: int = Field(
        default=1024,
        description="Maximum image width in pixels",
        gt=0
    )
    max_image_height: int = Field(
        default=768,
        description="Maximum image height in pixels",
        gt=0
    )
    video_max_resolution: str = Field(
        default="720p",
        description="Maximum video resolution (480p, 720p, 1080p)"
    )
    video_max_bitrate_kbps: int = Field(
        default=3000,
        description="Maximum video bitrate in kbps",
        gt=0
    )


class DeviceConfig(BaseModel):
    """Configuration for a device (R36S, Steam Deck, PC, etc.).
    
    A device is hardware that runs a frontend. It defines hardware
    constraints like display resolution and CPU capability limits.
    
    The `unsupported_platforms` list should be populated through testing -
    start empty and add platforms as you discover they don't run well
    on the device.
    """
    
    name: str = Field(
        description="Device identifier (e.g., 'r36s', 'steamdeck', 'pc')"
    )
    description: Optional[str] = Field(
        default=None,
        description="Human-readable description of the device"
    )
    
    # Display configuration
    display: DisplayConfig = Field(
        default_factory=DisplayConfig,
        description="Display configuration (resolution, aspect ratio)"
    )
    
    # Media sizing constraints
    media_sizing: MediaSizingConfig = Field(
        default_factory=MediaSizingConfig,
        description="Media sizing constraints for optimization"
    )
    
    # Platforms this device CANNOT run (discovered through testing)
    # These are CPU/performance limitations, not frontend support
    unsupported_platforms: List[str] = Field(
        default_factory=list,
        description="Platforms this device cannot emulate (e.g., ['ps2', 'ps3', 'gamecube'])"
    )
    
    @field_validator('unsupported_platforms', mode='before')
    @classmethod
    def validate_unsupported_platforms(cls, v):
        """Handle YAML files that have the key with only comments (returns None)."""
        if v is None:
            return []
        return v
    
    def supports_platform(self, platform: str) -> bool:
        """Check if this device can run a platform.
        
        Args:
            platform: Platform name to check
            
        Returns:
            True if supported (not in unsupported list), False otherwise
        """
        return platform.lower() not in [p.lower() for p in self.unsupported_platforms]
    
    def get_optimal_image_size(self) -> Tuple[int, int]:
        """Get the optimal image size for this device.
        
        Returns:
            Tuple of (width, height) for optimal images
        """
        return (self.media_sizing.max_image_width, self.media_sizing.max_image_height)
