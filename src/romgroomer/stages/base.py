"""Base classes for processing stages."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

from rich.console import Console
from rich.progress import Progress

from .domain import (
    PreFilters,
    FileSet,
    FileHashes,
    DiscProcessing,
    ProcessingStats,
    Transformation,
)


# Module logger
logger = logging.getLogger(__name__)


class StageStatus(str, Enum):
    """Stage execution status."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageContext:
    """Context passed between stages.
    
    This is the primary data structure flowing through the pipeline.
    Each stage reads from and updates this context.
    
    The context is organized into logical groups:
    - Platform info: platform_name, platform_config, target_name
    - Directories: source_dir, work_dir, output_dir  
    - Files: files (FileSet) tracks files through pipeline
    - Hashes: hashes (FileHashes) for DAT matching
    - Disc processing: discs (DiscProcessing) for disc-based systems
    - Pre-filters: pre_filters (PreFilters) for filename filtering
    - Stats: stats (ProcessingStats) for metrics
    """

    # Platform info
    platform_name: str
    platform_config: Any  # PlatformConfig
    target_name: str

    # Working directories
    source_dir: Path
    work_dir: Path
    output_dir: Path

    # DAT info
    dat_file: Optional[Any] = None  # DATFile from dat_parser

    # === Domain Objects (new structured approach) ===
    
    files: FileSet = field(default_factory=FileSet)
    """File tracking through the pipeline"""
    
    hashes: FileHashes = field(default_factory=FileHashes)
    """MD5 hashes for DAT matching"""
    
    discs: DiscProcessing = field(default_factory=DiscProcessing)
    """Disc-based game processing state"""
    
    pre_filters: PreFilters = field(default_factory=PreFilters)
    """Pre-DAT filename filters"""
    
    processing_stats: ProcessingStats = field(default_factory=ProcessingStats)
    """Structured processing statistics (domain object)"""
    
    transformations: List[Transformation] = field(default_factory=list)
    """File transformation history"""

    # === Legacy fields (for backward compatibility) ===
    # These will be deprecated in a future version
    
    source_files: List[Path] = field(default_factory=list)
    """DEPRECATED: Use files.source instead"""
    
    matched_files: List[Path] = field(default_factory=list)
    """DEPRECATED: Use files.matched instead"""
    
    filtered_files: List[Path] = field(default_factory=list)
    """DEPRECATED: Use files.filtered instead"""
    
    organized_files: Dict[str, List[Path]] = field(default_factory=dict)
    """DEPRECATED: Use files.organized instead"""
    
    file_md5s: Dict[Path, str] = field(default_factory=dict)
    """DEPRECATED: Use hashes.source_md5 instead"""
    
    rom_md5_map: Dict[Path, str] = field(default_factory=dict)
    """DEPRECATED: Use hashes.rom_md5 instead"""

    extracted_files: List[Path] = field(default_factory=list)
    """DEPRECATED: Use files.extracted instead"""
    
    compressed_files: List[Path] = field(default_factory=list)
    """DEPRECATED: Use files.compressed instead"""
    
    m3u_files: List[Path] = field(default_factory=list)
    """DEPRECATED: Use files.m3u instead"""
    
    disc_groups: Dict[str, Any] = field(default_factory=dict)
    """DEPRECATED: Use discs.games instead"""
    
    disc_metadata: Dict[str, Any] = field(default_factory=dict)
    """DEPRECATED: Use discs.cue_sheets instead"""

    letter_filter: Optional[str] = None
    """DEPRECATED: Use pre_filters.letter instead"""
    
    region_filter: Optional[List[str]] = None
    """DEPRECATED: Use pre_filters.regions instead"""
    
    language_filter: Optional[List[str]] = None
    """DEPRECATED: Use pre_filters.languages instead"""

    # Statistics (dict for backward compatibility)
    stats: Dict[str, Any] = field(default_factory=dict)
    """Stage statistics (dict for backward compatibility)"""

    # Console for output (optional, prefer using logger)
    console: Optional[Console] = None
    
    def __post_init__(self):
        """Sync legacy fields with domain objects."""
        # Sync pre_filters from legacy fields if set
        if self.letter_filter and not self.pre_filters.letter:
            self.pre_filters.letter = self.letter_filter
        if self.region_filter and not self.pre_filters.regions:
            self.pre_filters.regions = self.region_filter
        if self.language_filter and not self.pre_filters.languages:
            self.pre_filters.languages = self.language_filter


@dataclass
class StageResult:
    """Result of stage execution."""

    status: StageStatus
    message: str
    files_processed: int = 0
    files_matched: int = 0
    files_skipped: int = 0
    files_failed: int = 0
    duration_seconds: float = 0.0
    error: Optional[Exception] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def is_success(self) -> bool:
        """Check if stage succeeded."""
        return self.status == StageStatus.SUCCESS

    def get_summary(self) -> str:
        """Get human-readable summary."""
        if self.status == StageStatus.SUCCESS:
            return f"✓ {self.message} ({self.files_processed} files, {self.duration_seconds:.1f}s)"
        elif self.status == StageStatus.FAILED:
            return f"✗ {self.message}: {self.error}"
        elif self.status == StageStatus.SKIPPED:
            return f"⊘ {self.message}"
        else:
            return f"⋯ {self.message}"


class Stage(ABC):
    """Base class for processing stages."""

    def __init__(self, name: str):
        """Initialize stage.

        Args:
            name: Stage name for logging
        """
        self.name = name

    @abstractmethod
    def execute(self, context: StageContext) -> StageResult:
        """Execute the stage.

        Args:
            context: Stage context with input files and config

        Returns:
            StageResult with execution details
        """
        pass

    def should_skip(self, context: StageContext) -> bool:
        """Check if stage should be skipped.

        Args:
            context: Stage context

        Returns:
            True if stage should be skipped
        """
        return False

    def validate_context(self, context: StageContext) -> Optional[str]:
        """Validate context before execution.

        Args:
            context: Stage context

        Returns:
            Error message if validation fails, None if valid
        """
        return None

    def _log(self, context: StageContext, message: str, style: str = ""):
        """Log message to console.

        Args:
            context: Stage context
            message: Message to log
            style: Rich style string
        """
        if context.console:
            if style:
                context.console.print(f"[{style}]{message}[/{style}]")
            else:
                context.console.print(message)
    
    def _log_info(self, context: StageContext, message: str):
        """Log info message."""
        self._log(context, f"  {message}", "dim")
    
    def _log_warning(self, context: StageContext, message: str):
        """Log warning message."""
        self._log(context, f"  ⚠ {message}", "yellow")
    
    def _log_error(self, context: StageContext, message: str):
        """Log error message."""
        self._log(context, f"  ✗ {message}", "red")
