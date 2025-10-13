"""Base classes for processing stages."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.progress import Progress


class StageStatus(str, Enum):
    """Stage execution status."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageContext:
    """Context passed between stages."""

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

    # Files being processed
    source_files: List[Path] = field(default_factory=list)
    matched_files: List[Path] = field(default_factory=list)
    filtered_files: List[Path] = field(default_factory=list)
    organized_files: Dict[str, List[Path]] = field(default_factory=dict)

    # Disc processing (Phase 4)
    extracted_files: List[Path] = field(default_factory=list)
    """CUE files extracted from ZIPs"""
    
    compressed_files: List[Path] = field(default_factory=list)
    """CHD files created from CUE/BIN"""
    
    m3u_files: List[Path] = field(default_factory=list)
    """M3U playlist files for multi-disc games"""
    
    disc_groups: Dict[str, Any] = field(default_factory=dict)
    """Grouped discs by game base name (str -> List[CueSheet])"""
    
    disc_metadata: Dict[str, Any] = field(default_factory=dict)
    """Metadata for each game (str -> DiscMetadata)"""
    
    # Complex transformations (Phase 5)
    transformations: List[Any] = field(default_factory=list)
    """FileTransformation records for multi-step processing"""

    # Statistics
    stats: Dict[str, Any] = field(default_factory=dict)

    # Console for output
    console: Optional[Console] = None


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
