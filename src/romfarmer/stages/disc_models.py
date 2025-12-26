"""Models for disc-based systems."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class DiscMetadata:
    """Metadata for a disc-based game.
    
    For multi-disc games, metadata should come from the first disc.
    This is used for scraping, images, and gamelist.xml generation.
    """
    
    game_base_name: str
    """Base name without disc number (e.g., 'Panzer Dragoon Saga (USA)')"""
    
    first_disc_path: Path
    """Path to the first disc (CHD or CUE)"""
    
    all_discs: List[Path]
    """All disc files in order (Disc 1, 2, 3, ...)"""
    
    disc_count: int
    """Total number of discs"""
    
    # Metadata from first disc only
    title: str
    """Clean game title from first disc"""
    
    region: Optional[str] = None
    """Region code (USA, Europe, Japan, etc.)"""
    
    language: Optional[str] = None
    """Language code if specified"""
    
    # For organization and gamelist.xml
    needs_m3u: bool = False
    """True if this is a multi-disc game requiring M3U"""
    
    primary_file: Optional[Path] = None
    """M3U file if multi-disc, otherwise first/only CHD"""
    
    m3u_path: Optional[Path] = None
    """Path to generated M3U file for multi-disc games"""
    
    def __post_init__(self):
        """Calculate derived fields."""
        self.needs_m3u = self.disc_count > 1
        if not self.primary_file:
            self.primary_file = self.m3u_path if self.needs_m3u else self.first_disc_path


@dataclass
class CueSheet:
    """Parsed CUE sheet information."""
    
    cue_path: Path
    """Path to the .cue file"""
    
    bin_files: List[Path]
    """List of .bin files referenced in the CUE"""
    
    disc_number: Optional[int] = None
    """Disc number if detected from filename"""
    
    game_base_name: Optional[str] = None
    """Base game name without disc number"""
    
    # ZIP origin tracking (for cache pre-check)
    source_zip_path: Optional[Path] = None
    """Path to original ZIP file this was extracted from"""
    
    source_zip_crc32: Optional[str] = None
    """CRC32 of main content from ZIP header (e.g., '2578c3f9')"""
    
    source_zip_content_size: Optional[int] = None
    """Uncompressed size of main content from ZIP header"""
    
    def is_valid(self) -> bool:
        """Check if all referenced BIN files exist."""
        return all(bin_file.exists() for bin_file in self.bin_files)


@dataclass
class IsoDisc:
    """ISO disc information for UMD/DVD-based systems (PSP, PS2, etc.).
    
    Unlike CD-based systems that use CUE/BIN pairs, UMD and DVD systems
    use standalone ISO files.
    """
    
    iso_path: Path
    """Path to the .iso file"""
    
    disc_number: Optional[int] = None
    """Disc number if detected from filename"""
    
    game_base_name: Optional[str] = None
    """Base game name without disc number"""
    
    # ZIP origin tracking (for cache pre-check)
    source_zip_path: Optional[Path] = None
    """Path to original ZIP file this was extracted from"""
    
    source_zip_crc32: Optional[str] = None
    """CRC32 of main content from ZIP header (e.g., '2578c3f9')"""
    
    source_zip_content_size: Optional[int] = None
    """Uncompressed size of main content from ZIP header"""
    
    def is_valid(self) -> bool:
        """Check if ISO file exists."""
        return self.iso_path.exists()
