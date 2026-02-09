"""Utility modules for ROM Farmer."""

from .storage_budget import (
    StorageBudget,
    BudgetTracker,
    parse_size_spec,
    compute_storage_budget,
    format_size,
)

from .size_tracking import (
    PlatformSizeRecord,
    SizeDatabase,
    get_size_db,
    record_platform_size,
    estimate_platform_size,
)

from .video_converter import (
    VideoProfile,
    VideoConverter,
    get_profile_from_device_config as get_video_profile_from_device_config,
    get_video_converter,
    PROFILES as VIDEO_PROFILES,
)

from .image_converter import (
    ImageProfile,
    ImageConverter,
    get_profile_from_device_config as get_image_profile_from_device_config,
    get_image_converter,
    PROFILES as IMAGE_PROFILES,
)

__all__ = [
    # Storage budget
    "StorageBudget",
    "BudgetTracker",
    "parse_size_spec",
    "compute_storage_budget",
    "format_size",
    # Size tracking
    "PlatformSizeRecord",
    "SizeDatabase",
    "get_size_db",
    "record_platform_size",
    "estimate_platform_size",
    # Video conversion
    "VideoProfile",
    "VideoConverter",
    "get_video_profile_from_device_config",
    "get_video_converter",
    "VIDEO_PROFILES",
    # Image conversion
    "ImageProfile",
    "ImageConverter",
    "get_image_profile_from_device_config",
    "get_image_converter",
    "IMAGE_PROFILES",
]
