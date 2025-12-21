"""Video transcoding utility for optimizing videos for different devices.

Implements a caching strategy where converted videos are stored in
metadata/media/video-{profile}/ and reused across builds.

Key Features:
- Resolution downscaling for small screens
- Bitrate reduction for storage savings
- Persistent cache to avoid re-encoding
- Profile-based encoding presets
"""

import hashlib
import subprocess
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


@dataclass
class VideoProfile:
    """Video encoding profile for a target device class."""
    
    name: str
    """Profile identifier (e.g., 'handheld', 'desktop', 'micro')"""
    
    max_width: int
    """Maximum video width in pixels"""
    
    max_height: int
    """Maximum video height in pixels"""
    
    max_bitrate_kbps: int
    """Maximum bitrate in kbps"""
    
    crf: int = 28
    """Constant Rate Factor (18=high quality, 28=good balance, 35=small file)"""
    
    preset: str = "medium"
    """FFmpeg encoding preset (ultrafast, fast, medium, slow)"""
    
    audio_bitrate_kbps: int = 64
    """Audio bitrate in kbps (64k is fine for gameplay audio)"""


# Pre-defined profiles
PROFILES = {
    # For tiny handheld screens (R36S, Miyoo Mini, etc.)
    # 320x240 effective, keep videos small
    "micro": VideoProfile(
        name="micro",
        max_width=320,
        max_height=240,
        max_bitrate_kbps=200,
        crf=30,
        audio_bitrate_kbps=48,
    ),
    
    # For standard handheld screens (640-854px wide)
    # R36S, RGB10 Max3, RG35XX, etc.
    "handheld": VideoProfile(
        name="handheld",
        max_width=480,
        max_height=360,
        max_bitrate_kbps=400,
        crf=28,
        audio_bitrate_kbps=64,
    ),
    
    # For larger handhelds / portable monitors (720p-ish)
    # Steam Deck, Odin 2, laptops
    "portable": VideoProfile(
        name="portable",
        max_width=640,
        max_height=480,
        max_bitrate_kbps=800,
        crf=26,
        audio_bitrate_kbps=96,
    ),
    
    # Original quality - no conversion
    "original": None,
}


def get_profile_from_device_config(media_sizing) -> Optional[VideoProfile]:
    """Create a VideoProfile from device MediaSizingConfig.
    
    Args:
        media_sizing: MediaSizingConfig from device.yaml
        
    Returns:
        VideoProfile matching device constraints, or None for original quality
    """
    resolution = media_sizing.video_max_resolution.lower()
    bitrate = media_sizing.video_max_bitrate_kbps
    
    # Map resolution string to max dimensions
    resolution_map = {
        "240p": (426, 240),
        "360p": (640, 360),
        "480p": (854, 480),
        "720p": (1280, 720),
        "1080p": (1920, 1080),
    }
    
    max_w, max_h = resolution_map.get(resolution, (1920, 1080))
    
    # If resolution is 720p+ and bitrate is 2000+, use original
    if max_w >= 1280 and bitrate >= 2000:
        return None
    
    # Determine CRF based on bitrate
    if bitrate <= 300:
        crf = 30
    elif bitrate <= 600:
        crf = 28
    elif bitrate <= 1200:
        crf = 26
    else:
        crf = 24
    
    return VideoProfile(
        name=f"custom-{resolution}-{bitrate}k",
        max_width=max_w,
        max_height=max_h,
        max_bitrate_kbps=bitrate,
        crf=crf,
    )


class VideoConverter:
    """Handles video conversion with caching for build optimization."""
    
    def __init__(self, media_root: Path):
        """Initialize video converter.
        
        Args:
            media_root: Root directory for media files (e.g., metadata/media/)
        """
        self.media_root = media_root
        self.original_dir = media_root / "video"
        self._ffmpeg_checked = False
        self._ffmpeg_available = False
    
    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available."""
        if self._ffmpeg_checked:
            return self._ffmpeg_available
        
        self._ffmpeg_checked = True
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                timeout=5
            )
            self._ffmpeg_available = result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            self._ffmpeg_available = False
        
        if not self._ffmpeg_available:
            logger.warning("FFmpeg not available - video conversion disabled")
        
        return self._ffmpeg_available
    
    def get_cache_dir(self, profile: VideoProfile) -> Path:
        """Get the cache directory for a profile.
        
        Args:
            profile: Video encoding profile
            
        Returns:
            Path to cache directory
        """
        return self.media_root / f"video-{profile.name}"
    
    def get_video_info(self, video_path: Path) -> Optional[Tuple[int, int, int]]:
        """Get video dimensions and bitrate.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Tuple of (width, height, bitrate_kbps) or None on error
        """
        if not self._check_ffmpeg():
            return None
        
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "quiet",
                    "-select_streams", "v:0",
                    "-show_entries", "stream=width,height,bit_rate",
                    "-of", "csv=p=0",
                    str(video_path)
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split(",")
                if len(parts) >= 3:
                    width = int(parts[0])
                    height = int(parts[1])
                    bitrate = int(parts[2]) // 1000 if parts[2] != "N/A" else 0
                    return (width, height, bitrate)
        except Exception as e:
            logger.debug(f"Could not get video info for {video_path}: {e}")
        
        return None
    
    def needs_conversion(self, video_path: Path, profile: VideoProfile) -> bool:
        """Check if a video needs conversion for the given profile.
        
        Args:
            video_path: Path to original video
            profile: Target profile
            
        Returns:
            True if conversion would reduce size, False otherwise
        """
        info = self.get_video_info(video_path)
        if not info:
            return False
        
        width, height, bitrate = info
        
        # Convert if resolution exceeds profile max
        if width > profile.max_width or height > profile.max_height:
            return True
        
        # Convert if bitrate exceeds profile max (with 10% tolerance)
        if bitrate > profile.max_bitrate_kbps * 1.1:
            return True
        
        return False
    
    def get_cached_path(self, original_path: Path, profile: VideoProfile) -> Path:
        """Get the cached path for a converted video.
        
        Maintains the same hash-based directory structure as originals.
        
        Args:
            original_path: Path to original video
            profile: Target profile
            
        Returns:
            Path where cached video should be stored
        """
        # Original videos are stored as: video/{hash_prefix}/{hash}.mp4
        # Cached videos use same structure: video-{profile}/{hash_prefix}/{hash}.mp4
        
        # Get relative path from video directory
        try:
            rel_path = original_path.relative_to(self.original_dir)
        except ValueError:
            # Not under original_dir, use filename only
            rel_path = Path(original_path.name)
        
        cache_dir = self.get_cache_dir(profile)
        return cache_dir / rel_path
    
    def convert_video(
        self,
        source_path: Path,
        profile: VideoProfile,
        force: bool = False
    ) -> Optional[Path]:
        """Convert a video to the specified profile.
        
        Uses cached version if available. Converts and caches if not.
        
        Args:
            source_path: Path to original video
            profile: Target encoding profile
            force: Force re-conversion even if cached
            
        Returns:
            Path to converted video (may be cached), or None on error
        """
        if not self._check_ffmpeg():
            logger.warning("FFmpeg not available, returning original video")
            return source_path
        
        cached_path = self.get_cached_path(source_path, profile)
        
        # Check cache first
        if cached_path.exists() and not force:
            logger.debug(f"Using cached video: {cached_path}")
            return cached_path
        
        # Check if conversion is needed
        if not self.needs_conversion(source_path, profile):
            logger.debug(f"Video already meets profile requirements: {source_path}")
            return source_path
        
        # Create cache directory
        cached_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build ffmpeg command
        # Scale: maintain aspect ratio, max width/height
        scale_filter = (
            f"scale='min({profile.max_width},iw)':'min({profile.max_height},ih)':"
            f"force_original_aspect_ratio=decrease"
        )
        
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-i", str(source_path),
            "-c:v", "libx264",
            "-preset", profile.preset,
            "-crf", str(profile.crf),
            "-maxrate", f"{profile.max_bitrate_kbps}k",
            "-bufsize", f"{profile.max_bitrate_kbps * 2}k",
            "-vf", scale_filter,
            "-c:a", "aac",
            "-b:a", f"{profile.audio_bitrate_kbps}k",
            "-movflags", "+faststart",  # Enable streaming
            str(cached_path)
        ]
        
        try:
            logger.info(f"Converting video: {source_path.name} -> {profile.name}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per video
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                if cached_path.exists():
                    cached_path.unlink()
                return None
            
            # Verify output exists and is valid
            if not cached_path.exists():
                logger.error(f"Conversion failed - output not created: {cached_path}")
                return None
            
            # Check if converted file is actually smaller
            original_size = source_path.stat().st_size
            converted_size = cached_path.stat().st_size
            
            if converted_size >= original_size:
                logger.info(
                    f"Converted file not smaller ({converted_size} >= {original_size}), "
                    f"will use original"
                )
                # Keep the cache file anyway to avoid re-converting
                # But return original path
                return source_path
            
            savings = (original_size - converted_size) / original_size * 100
            logger.info(
                f"Converted: {source_path.name} "
                f"({original_size // 1024}KB -> {converted_size // 1024}KB, "
                f"{savings:.1f}% smaller)"
            )
            
            return cached_path
            
        except subprocess.TimeoutExpired:
            logger.error(f"Video conversion timed out: {source_path}")
            if cached_path.exists():
                cached_path.unlink()
            return None
        except Exception as e:
            logger.error(f"Video conversion failed: {e}")
            if cached_path.exists():
                cached_path.unlink()
            return None
    
    def get_optimized_video(
        self,
        source_path: Path,
        profile: Optional[VideoProfile]
    ) -> Path:
        """Get the best available video for the given profile.
        
        This is the main entry point for the build pipeline.
        Returns the converted video if available/possible, otherwise original.
        
        Args:
            source_path: Path to original video
            profile: Target profile, or None for original quality
            
        Returns:
            Path to the video to use (converted or original)
        """
        if profile is None:
            return source_path
        
        # Check cache first (fast path)
        cached_path = self.get_cached_path(source_path, profile)
        if cached_path.exists():
            return cached_path
        
        # Check if conversion is even needed
        if not self.needs_conversion(source_path, profile):
            return source_path
        
        # Convert and cache
        result = self.convert_video(source_path, profile)
        return result if result else source_path


def get_video_converter(media_root: Optional[Path] = None) -> VideoConverter:
    """Factory function to create a VideoConverter.
    
    Args:
        media_root: Root media directory. Defaults to metadata/media/
        
    Returns:
        Configured VideoConverter instance
    """
    if media_root is None:
        media_root = Path.cwd() / "metadata" / "media"
    
    return VideoConverter(media_root)
