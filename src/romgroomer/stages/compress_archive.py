"""Compress ROM files to archive formats (7z, ZIP)."""

import os
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import List, Optional

from ..config.models import CompressionFormat
from .base import Stage, StageContext, StageResult, StageStatus

# Standard timestamp for all archived files (No-Intro/TOSEC standard)
# December 24, 1996 23:32:00 UTC - used for reproducible/deterministic builds
STANDARD_ZIP_DATE_TIME = (1996, 12, 24, 23, 32, 0)


class CompressArchiveStage(Stage):
    """Compress ROM files to archive formats.
    
    Supports 7z and ZIP compression for cartridge ROMs.
    Used after extraction to recompress ROM files with better compression.
    """
    
    def __init__(self):
        """Initialize compression stage."""
        super().__init__("Compress Archives")
    
    def should_skip(self, context: StageContext) -> bool:
        """Skip if no files to compress or compression not needed.
        
        Args:
            context: Stage context
            
        Returns:
            True if should skip
        """
        # Skip if no extracted files
        if not context.extracted_files:
            return True
        
        # Skip if compression format is RAW (loose files)
        compression_format = context.platform_config.compression.format
        if compression_format == CompressionFormat.NONE:
            return True
        
        # Skip if format is CHD (handled by separate stage)
        if compression_format == CompressionFormat.CHD:
            return True
        
        # Only handle 7Z and ZIP
        if compression_format not in [CompressionFormat.SEVENZ, CompressionFormat.ZIP]:
            return True
        
        return False
    
    def execute(self, context: StageContext) -> StageResult:
        """Compress ROM files to archives.
        
        Args:
            context: Stage context
            
        Returns:
            Stage result
        """
        if self.should_skip(context):
            return StageResult(
                status=StageStatus.SKIPPED,
                message="Archive compression not needed",
            )
        
        compression_format = context.platform_config.compression.format
        compression_config = context.platform_config.compression
        
        # Validate compression tool
        tool_path = Path(compression_config.tool) if compression_config.tool else None
        
        # If tool not specified, try to find it in PATH
        if not tool_path:
            if compression_format == CompressionFormat.SEVENZ:
                found_tool = shutil.which('7z')
                if found_tool:
                    tool_path = Path(found_tool)
            elif compression_format == CompressionFormat.ZIP:
                found_tool = shutil.which('zip')
                if found_tool:
                    tool_path = Path(found_tool)
        
        if not tool_path or not tool_path.exists():
            return StageResult(
                status=StageStatus.FAILED,
                message=f"Compression tool not found: {compression_config.tool or compression_format.value}",
            )
        
        self._log_info(context, f"Compressing {len(context.extracted_files)} files to {compression_format.value}...")
        
        compressed_files: List[Path] = []
        failed = 0
        
        for rom_path in context.extracted_files:
            try:
                compressed_path = self._compress_file(
                    context, 
                    rom_path, 
                    compression_format,
                    tool_path,
                    compression_config.parameters
                )
                if compressed_path:
                    compressed_files.append(compressed_path)
                else:
                    failed += 1
            except Exception as e:
                self._log_error(context, f"Failed to compress {rom_path.name}: {e}")
                failed += 1
        
        # Update context
        context.compressed_files = compressed_files
        
        message = f"Compressed {len(compressed_files)} files to {compression_format.value}"
        
        return StageResult(
            status=StageStatus.SUCCESS,
            message=message,
            files_processed=len(context.extracted_files),
            files_matched=len(compressed_files),
            files_failed=failed,
            details={
                "compressed": [str(p) for p in compressed_files],
                "format": compression_format.value,
            }
        )
    
    def _compress_file(
        self,
        context: StageContext,
        rom_path: Path,
        compression_format: CompressionFormat,
        tool_path: Path,
        parameters: dict
    ) -> Optional[Path]:
        """Compress a single ROM file.
        
        Args:
            context: Stage context
            rom_path: Path to ROM file
            compression_format: Target compression format
            tool_path: Path to compression tool
            parameters: Compression parameters from config
            
        Returns:
            Path to compressed file or None if failed
        """
        try:
            if compression_format == CompressionFormat.SEVENZ:
                return self._compress_7z(rom_path, tool_path, parameters)
            elif compression_format == CompressionFormat.ZIP:
                return self._compress_zip(rom_path, tool_path, parameters)
            else:
                self._log_error(context, f"Unsupported compression format: {compression_format}")
                return None
                
        except Exception as e:
            self._log_error(context, f"Failed to compress {rom_path.name}: {e}")
            return None
    
    def _compress_7z(
        self,
        rom_path: Path,
        tool_path: Path,
        parameters: dict
    ) -> Optional[Path]:
        """Compress ROM file to 7z.
        
        Args:
            rom_path: Path to ROM file
            tool_path: Path to 7z binary
            parameters: Compression parameters (compression_level, method, etc.)
            
        Returns:
            Path to compressed file or None if failed
        """
        # Output path: same directory, .7z extension
        output_path = rom_path.with_suffix('.7z')
        
        # Build 7z command
        # 7z a -t7z -m0=lzma2 -mx=9 output.7z input.rom
        # File timestamps are already set to No-Intro standard (1996-12-24 23:32) during extraction
        # 7z will preserve these timestamps by default
        cmd = [
            str(tool_path),
            'a',  # Add to archive
            '-t7z',  # 7z format
        ]
        
        # Add compression level
        level = parameters.get('compression_level', 9)
        cmd.append(f'-mx={level}')
        
        # Add compression method
        method = parameters.get('method', 'LZMA2')
        cmd.append(f'-m0={method.lower()}')
        
        # Output and input files
        cmd.extend([str(output_path), str(rom_path)])
        
        # Run compression
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            raise Exception(f"7z failed: {result.stderr}")
        
        # Remove original ROM file
        rom_path.unlink()
        
        return output_path
    
    def _compress_zip(
        self,
        rom_path: Path,
        tool_path: Path,
        parameters: dict
    ) -> Optional[Path]:
        """Compress ROM file to ZIP with deterministic timestamps.
        
        Args:
            rom_path: Path to ROM file
            tool_path: Path to zip binary (unused - we use Python's zipfile module)
            parameters: Compression parameters (compression_level, etc.)
            
        Returns:
            Path to compressed file or None if failed
        """
        # Output path: same directory, .zip extension
        output_path = rom_path.with_suffix('.zip')
        
        # Get compression level (0-9, default 9)
        level = parameters.get('compression_level', 9)
        
        # Map compression level to zipfile constants
        # 0 = no compression, 1-9 = deflate compression
        if level == 0:
            compression = zipfile.ZIP_STORED
        else:
            compression = zipfile.ZIP_DEFLATED
        
        # Create ZIP archive with deterministic timestamp
        with zipfile.ZipFile(output_path, 'w', compression=compression) as zf:
            # Create ZipInfo with standard No-Intro timestamp
            zip_info = zipfile.ZipInfo(rom_path.name)
            zip_info.date_time = STANDARD_ZIP_DATE_TIME
            zip_info.compress_type = compression
            
            # Set compression level (only affects DEFLATED)
            if compression == zipfile.ZIP_DEFLATED:
                # compresslevel parameter available in Python 3.7+
                zf.compresslevel = level
            
            # Write file data with standardized timestamp
            with open(rom_path, 'rb') as f:
                zf.writestr(zip_info, f.read())
        
        # Remove original ROM file
        rom_path.unlink()
        
        return output_path
