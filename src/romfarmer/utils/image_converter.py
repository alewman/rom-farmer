"""Image resizing utility for optimizing images for different devices.

Implements a caching strategy where resized images are stored in
metadata/media/{type}-{profile}/ and reused across builds.

Key Features:
- Resolution downscaling for small screens
- Format optimization (PNG → JPG for photos where appropriate)
- Persistent cache to avoid re-processing
- Profile-based sizing from device config
- Smart skip for images already at or below target size
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ImageProfile:
    """Image sizing profile for a target device class."""
    
    name: str
    """Profile identifier (e.g., 'handheld', 'desktop')"""
    
    max_width: int
    """Maximum image width in pixels"""
    
    max_height: int
    """Maximum image height in pixels"""
    
    quality: int = 85
    """JPEG quality (1-100) or PNG compression level"""
    
    convert_to_jpg: bool = False
    """Convert PNG to JPG for better compression (loses transparency)"""


# Pre-defined profiles
PROFILES = {
    # For tiny handheld screens (R36S, Miyoo Mini, etc.)
    "micro": ImageProfile(
        name="micro",
        max_width=160,
        max_height=120,
        quality=80,
    ),
    
    # For standard handheld screens (640-854px wide)
    "handheld": ImageProfile(
        name="handheld",
        max_width=320,
        max_height=240,
        quality=85,
    ),
    
    # For larger handhelds / portable monitors
    "portable": ImageProfile(
        name="portable",
        max_width=640,
        max_height=480,
        quality=90,
    ),
    
    # Original quality - no conversion
    "original": None,
}


def get_profile_from_device_config(media_sizing) -> Optional[ImageProfile]:
    """Create an ImageProfile from device MediaSizingConfig.
    
    Args:
        media_sizing: MediaSizingConfig from device.yaml
        
    Returns:
        ImageProfile matching device constraints, or None for original quality
    """
    max_w = media_sizing.max_image_width
    max_h = media_sizing.max_image_height
    
    # If dimensions are large enough, use original
    if max_w >= 1024 and max_h >= 768:
        return None
    
    # Determine quality based on size
    if max_w <= 200:
        quality = 80
    elif max_w <= 400:
        quality = 85
    else:
        quality = 90
    
    return ImageProfile(
        name=f"custom-{max_w}x{max_h}",
        max_width=max_w,
        max_height=max_h,
        quality=quality,
    )


class ImageConverter:
    """Handles image resizing with caching for build optimization."""
    
    # Media types that should be processed
    SUPPORTED_TYPES = {"image", "cartridge", "boxart", "screenshot", "wheel"}
    
    def __init__(self, media_root: Path):
        """Initialize image converter.
        
        Args:
            media_root: Root directory for media files (e.g., metadata/media/)
        """
        self.media_root = media_root
        self._pillow_checked = False
        self._pillow_available = False
    
    def _check_pillow(self) -> bool:
        """Check if Pillow is available."""
        if self._pillow_checked:
            return self._pillow_available
        
        self._pillow_checked = True
        try:
            from PIL import Image
            self._pillow_available = True
        except ImportError:
            self._pillow_available = False
            logger.warning("Pillow not available - image conversion disabled")
        
        return self._pillow_available
    
    def get_cache_dir(self, media_type: str, profile: ImageProfile) -> Path:
        """Get the cache directory for a media type and profile.
        
        Args:
            media_type: Type of media (image, cartridge, etc.)
            profile: Image sizing profile
            
        Returns:
            Path to cache directory
        """
        return self.media_root / f"{media_type}-{profile.name}"
    
    def get_image_info(self, image_path: Path) -> Optional[Tuple[int, int, int]]:
        """Get image dimensions and file size.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple of (width, height, file_size_bytes) or None on error
        """
        if not self._check_pillow():
            return None
        
        try:
            from PIL import Image
            
            with Image.open(image_path) as img:
                width, height = img.size
            file_size = image_path.stat().st_size
            return (width, height, file_size)
        except Exception as e:
            logger.debug(f"Could not get image info for {image_path}: {e}")
            return None
    
    def needs_conversion(self, image_path: Path, profile: ImageProfile) -> bool:
        """Check if an image needs resizing for the given profile.
        
        Args:
            image_path: Path to original image
            profile: Target profile
            
        Returns:
            True if image exceeds profile dimensions, False otherwise
        """
        info = self.get_image_info(image_path)
        if not info:
            return False
        
        width, height, _ = info
        
        # Only convert if dimensions exceed profile max
        return width > profile.max_width or height > profile.max_height
    
    def get_cached_path(self, original_path: Path, media_type: str, profile: ImageProfile) -> Path:
        """Get the cached path for a resized image.
        
        Maintains the same hash-based directory structure as originals.
        
        Args:
            original_path: Path to original image
            media_type: Type of media (image, cartridge, etc.)
            profile: Target profile
            
        Returns:
            Path where cached image should be stored
        """
        # Original images are stored as: {type}/{hash_prefix}/{hash}.png
        # Cached images use same structure: {type}-{profile}/{hash_prefix}/{hash}.png
        
        original_dir = self.media_root / media_type
        
        try:
            rel_path = original_path.relative_to(original_dir)
        except ValueError:
            # Not under expected dir, use filename only
            rel_path = Path(original_path.name)
        
        cache_dir = self.get_cache_dir(media_type, profile)
        return cache_dir / rel_path
    
    def convert_image(
        self,
        source_path: Path,
        media_type: str,
        profile: ImageProfile,
        force: bool = False
    ) -> Optional[Path]:
        """Resize an image to the specified profile.
        
        Uses cached version if available. Resizes and caches if not.
        
        Args:
            source_path: Path to original image
            media_type: Type of media (image, cartridge, etc.)
            profile: Target sizing profile
            force: Force re-conversion even if cached
            
        Returns:
            Path to resized image (may be cached), or None on error
        """
        if not self._check_pillow():
            logger.warning("Pillow not available, returning original image")
            return source_path
        
        cached_path = self.get_cached_path(source_path, media_type, profile)
        
        # Check cache first
        if cached_path.exists() and not force:
            logger.debug(f"Using cached image: {cached_path}")
            return cached_path
        
        # Check if conversion is needed
        if not self.needs_conversion(source_path, profile):
            logger.debug(f"Image already meets profile requirements: {source_path}")
            return source_path
        
        # Create cache directory
        cached_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            from PIL import Image
            
            original_size = source_path.stat().st_size
            
            with Image.open(source_path) as img:
                original_dims = img.size
                
                # Calculate new size maintaining aspect ratio
                img.thumbnail(
                    (profile.max_width, profile.max_height),
                    Image.Resampling.LANCZOS
                )
                new_dims = img.size
                
                # Determine output format
                # Keep PNG for images with transparency, otherwise use original format
                has_alpha = img.mode in ('RGBA', 'LA', 'PA') or (
                    img.mode == 'P' and 'transparency' in img.info
                )
                
                if profile.convert_to_jpg and not has_alpha:
                    # Convert to RGB for JPEG
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    cached_path = cached_path.with_suffix('.jpg')
                    img.save(cached_path, 'JPEG', quality=profile.quality, optimize=True)
                else:
                    # Keep original format
                    if source_path.suffix.lower() in ('.jpg', '.jpeg'):
                        img.save(cached_path, 'JPEG', quality=profile.quality, optimize=True)
                    else:
                        # PNG - use compression
                        img.save(cached_path, 'PNG', optimize=True)
            
            # Check if converted file is valid
            if not cached_path.exists():
                logger.error(f"Conversion failed - output not created: {cached_path}")
                return None
            
            converted_size = cached_path.stat().st_size
            
            # Log results
            savings = (original_size - converted_size) / original_size * 100
            logger.info(
                f"Resized: {source_path.name} "
                f"({original_dims[0]}x{original_dims[1]} -> {new_dims[0]}x{new_dims[1]}, "
                f"{original_size // 1024}KB -> {converted_size // 1024}KB, "
                f"{savings:.1f}% smaller)"
            )
            
            return cached_path
            
        except Exception as e:
            logger.error(f"Image conversion failed: {e}")
            if cached_path.exists():
                cached_path.unlink()
            return None
    
    def get_optimized_image(
        self,
        source_path: Path,
        media_type: str,
        profile: Optional[ImageProfile]
    ) -> Path:
        """Get the best available image for the given profile.
        
        This is the main entry point for the build pipeline.
        Returns the resized image if available/possible, otherwise original.
        
        Args:
            source_path: Path to original image
            media_type: Type of media (image, cartridge, etc.)
            profile: Target profile, or None for original quality
            
        Returns:
            Path to the image to use (resized or original)
        """
        if profile is None:
            return source_path
        
        if media_type not in self.SUPPORTED_TYPES:
            return source_path
        
        # Check cache first (fast path)
        cached_path = self.get_cached_path(source_path, media_type, profile)
        if cached_path.exists():
            return cached_path
        
        # Check if conversion is even needed
        if not self.needs_conversion(source_path, profile):
            return source_path
        
        # Convert and cache
        result = self.convert_image(source_path, media_type, profile)
        return result if result else source_path


def get_image_converter(media_root: Optional[Path] = None) -> ImageConverter:
    """Factory function to create an ImageConverter.
    
    Args:
        media_root: Root media directory. Defaults to metadata/media/
        
    Returns:
        Configured ImageConverter instance
    """
    if media_root is None:
        media_root = Path.cwd() / "metadata" / "media"
    
    return ImageConverter(media_root)
