"""Base classes for ROM processing."""

import asyncio
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from ..models.rom import Rom


@dataclass
class ProcessedRom:
    """Result of ROM processing.
    
    Attributes:
        original: Original ROM metadata from parser
        original_path: Original input file/directory
        processed_path: Final output file/directory
        format: Output format (e.g., '.nes', '.chd', '.sqfs')
        transformations: List of stages applied
        disc_files: List of disc files (for multi-disc games)
        metadata: Additional metadata from processing
        success: Whether processing was successful
        error: Error message if processing failed
    """
    
    original: Optional[Rom] = None
    original_path: Optional[Path] = None
    processed_path: Optional[Path] = None
    format: str = ""
    transformations: list[str] = field(default_factory=list)
    disc_files: list[Path] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None


class ProcessingStage(ABC):
    """Base class for a single processing stage.
    
    Each stage does ONE thing (extract, decrypt, convert, etc.) and can
    be composed into pipelines for different platforms.
    
    Example:
        >>> class ExtractArchiveStage(ProcessingStage):
        ...     async def process(self, input_path: Path, context: dict) -> Path:
        ...         if input_path.suffix == '.zip':
        ...             return await self._extract_zip(input_path, context['temp_dir'])
        ...         return input_path
        ...     
        ...     def can_process(self, input_path: Path) -> bool:
        ...         return input_path.suffix in ['.zip', '.7z', '.rar']
    """
    
    @abstractmethod
    async def process(self, input_path: Path, context: dict) -> Path:
        """Process input and return output path.
        
        Args:
            input_path: File or directory to process
            context: Shared context between stages containing:
                - temp_dir: Temporary directory for intermediate files
                - output_dir: Final output directory
                - rom: ROM metadata from parser
                - profile: Platform profile being used
                - transformations: List of applied transformations
                
        Returns:
            Path to processed output (may be same as input if no processing needed)
            
        Raises:
            ProcessingError: If processing fails
        """
        pass
    
    @abstractmethod
    def can_process(self, input_path: Path) -> bool:
        """Check if this stage can process the input.
        
        Args:
            input_path: File or directory to check
            
        Returns:
            True if this stage can process the input
        """
        pass
    
    def configure(self, config: dict[str, Any]) -> None:
        """Configure stage with platform-specific settings.
        
        Args:
            config: Configuration dictionary from platform profile
        """
        pass
    
    async def _run_command(
        self,
        cmd: list[str],
        cwd: Optional[Path] = None,
        check: bool = True,
    ) -> tuple[str, str]:
        """Run external command asynchronously.
        
        Args:
            cmd: Command and arguments to run
            cwd: Working directory
            check: Raise exception on non-zero exit code
            
        Returns:
            Tuple of (stdout, stderr)
            
        Raises:
            ProcessingError: If command fails and check=True
        """
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        
        stdout, stderr = await process.communicate()
        
        if check and process.returncode != 0:
            raise ProcessingError(
                f"Command failed: {' '.join(cmd)}\n"
                f"Exit code: {process.returncode}\n"
                f"stderr: {stderr.decode()}"
            )
        
        return stdout.decode(), stderr.decode()


class BaseProcessor(ABC):
    """Base class for ROM processors.
    
    Processors handle the complete workflow for processing a ROM,
    including all transformation stages.
    """
    
    @abstractmethod
    async def process(
        self,
        input_path: Path,
        output_dir: Path,
        rom: Optional[Rom] = None,
    ) -> ProcessedRom:
        """Process a ROM file.
        
        Args:
            input_path: Input ROM file or directory
            output_dir: Output directory for processed ROM
            rom: Optional ROM metadata from parser
            
        Returns:
            ProcessedRom with results and metadata
        """
        pass


class ProcessingError(Exception):
    """Exception raised when ROM processing fails."""
    
    pass
