"""Domain objects for processing stages.

This module contains typed domain objects that replace generic dictionaries
and provide better type safety and clarity in the stage pipeline.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


@dataclass
class PreFilters:
    """Pre-filtering configuration applied before DAT matching.
    
    These filters run on filenames only (no I/O) to reduce
    the number of files that need MD5 hashing.
    """
    
    letter: Optional[str] = None
    """Filter by first letter of filename (e.g., 'A', 'B')"""
    
    regions: Optional[List[str]] = None
    """Filter by region tags (e.g., ['USA', 'World'])"""
    
    languages: Optional[List[str]] = None
    """Filter by language tags (e.g., ['En', 'Eng'])"""
    
    def is_active(self) -> bool:
        """Check if any filter is configured."""
        return (
            self.letter is not None
            or self.regions is not None
            or self.languages is not None
        )


@dataclass
class FileSet:
    """Tracks files through the processing pipeline.
    
    Each stage operates on and updates these file lists.
    The flow is typically:
    source -> matched -> filtered -> extracted -> compressed -> organized
    """
    
    source: List[Path] = field(default_factory=list)
    """Original source files from ROM directory"""
    
    matched: List[Path] = field(default_factory=list)
    """Files matched against DAT database"""
    
    filtered: List[Path] = field(default_factory=list)
    """Files after selection/rating filters"""
    
    extracted: List[Path] = field(default_factory=list)
    """Files extracted from archives (CUE/BIN, ROMs)"""
    
    compressed: List[Path] = field(default_factory=list)
    """Files after compression (CHD, 7z, etc.)"""
    
    organized: Dict[str, List[Path]] = field(default_factory=dict)
    """Files organized into output structure (subdir -> files)"""
    
    m3u: List[Path] = field(default_factory=list)
    """M3U playlist files for multi-disc games"""
    
    def count_total(self) -> int:
        """Count total files in organized output."""
        return sum(len(files) for files in self.organized.values())


@dataclass 
class FileHashes:
    """MD5 hashes for files at different stages.
    
    Used for DAT matching and metadata lookup.
    """
    
    source_md5: Dict[Path, str] = field(default_factory=dict)
    """MD5 of original source files (from ARRM or computed)"""
    
    rom_md5: Dict[Path, str] = field(default_factory=dict)
    """MD5 of extracted ROM files (for cartridge metadata)"""
    
    def get_md5(self, path: Path) -> Optional[str]:
        """Get MD5 for a file, checking both source and ROM hashes."""
        return self.rom_md5.get(path) or self.source_md5.get(path)


@dataclass
class DiscGame:
    """Information about a disc-based game (single or multi-disc).
    
    Used for disc extraction, CHD compression, and M3U generation.
    """
    
    base_name: str
    """Base game name without disc number"""
    
    disc_files: List[Path] = field(default_factory=list)
    """CUE/BIN or ISO files for each disc"""
    
    chd_files: List[Path] = field(default_factory=list)
    """CHD files after compression"""
    
    m3u_file: Optional[Path] = None
    """M3U playlist file (for multi-disc)"""
    
    total_size_bytes: int = 0
    """Combined size of all disc files"""
    
    @property
    def is_multi_disc(self) -> bool:
        """Check if this is a multi-disc game."""
        return len(self.disc_files) > 1


@dataclass
class DiscProcessing:
    """State for disc-based game processing.
    
    Tracks disc groups, metadata, and CHD conversion progress.
    """
    
    games: Dict[str, DiscGame] = field(default_factory=dict)
    """All disc games by base name"""
    
    cue_sheets: Dict[str, Any] = field(default_factory=dict)
    """Parsed CUE sheet data by game name"""
    
    def add_game(self, game: DiscGame) -> None:
        """Add a disc game to tracking."""
        self.games[game.base_name] = game
    
    def get_multi_disc_games(self) -> List[DiscGame]:
        """Get all multi-disc games."""
        return [g for g in self.games.values() if g.is_multi_disc]


@dataclass
class ProcessingStats:
    """Statistics collected during pipeline execution.
    
    Provides detailed metrics for reporting and debugging.
    """
    
    files_scanned: int = 0
    files_matched: int = 0
    files_filtered: int = 0
    files_extracted: int = 0
    files_compressed: int = 0
    files_organized: int = 0
    
    bytes_processed: int = 0
    bytes_output: int = 0
    
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    custom: Dict[str, Any] = field(default_factory=dict)
    """Stage-specific statistics"""
    
    def add_error(self, message: str) -> None:
        """Record an error."""
        self.errors.append(message)
    
    def add_warning(self, message: str) -> None:
        """Record a warning."""
        self.warnings.append(message)
    
    @property
    def compression_ratio(self) -> float:
        """Calculate compression ratio (output/input)."""
        if self.bytes_processed == 0:
            return 0.0
        return self.bytes_output / self.bytes_processed


@dataclass
class Transformation:
    """Record of a file transformation through the pipeline.
    
    Tracks the history of how a source file became an output file,
    useful for debugging and metadata generation.
    """
    
    source_path: Path
    """Original source file"""
    
    source_md5: Optional[str] = None
    """MD5 of source file"""
    
    output_path: Optional[Path] = None
    """Final output file"""
    
    output_md5: Optional[str] = None
    """MD5 of output file"""
    
    steps: List[str] = field(default_factory=list)
    """Processing steps applied (e.g., ['extract', 'compress_chd'])"""
    
    game_name: Optional[str] = None
    """Matched game name from DAT"""
    
    def add_step(self, step: str) -> None:
        """Record a processing step."""
        self.steps.append(step)
