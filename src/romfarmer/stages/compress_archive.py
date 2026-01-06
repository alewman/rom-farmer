"""Compress ROM files to archive formats (7z, ZIP) with cache support."""

import hashlib
import os
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..config.models import CompressionFormat
from ..cache import CacheManager
from .base import Stage, StageContext, StageResult, StageStatus

# Standard timestamp for all archived files (No-Intro/TOSEC standard)
# December 24, 1996 23:32:00 UTC - used for reproducible/deterministic builds
STANDARD_ZIP_DATE_TIME = (1996, 12, 24, 23, 32, 0)


class CompressArchiveStage(Stage):
    """Compress ROM files to archive formats.
    
    Supports 7z and ZIP compression for cartridge ROMs.
    Used after extraction to recompress ROM files with better compression.
    
    Supports ROM caching for build acceleration - if an archive for a given
    source file already exists in cache, it will be linked instead of rebuilt.
    """
    
    def __init__(
        self,
        db_session: Optional[Session] = None,
        cache_manager: Optional[CacheManager] = None,
    ):
        """Initialize compression stage.
        
        Args:
            db_session: Database session for transformation recording (optional)
            cache_manager: ROM cache manager (optional, enables caching)
        """
        super().__init__("Compress Archives")
        self.db_session = db_session
        self.cache_manager = cache_manager
        
        # Stats for cache hits/misses
        self._cache_hits = 0
        self._cache_misses = 0
    
    def _get_cache_params(self, compression_format: CompressionFormat, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Build cache parameters for lookup/storage.
        
        Args:
            compression_format: 7z or zip
            parameters: Compression parameters from config
            
        Returns:
            Dict of cache parameters
        """
        return {
            'format': compression_format.value,
            'compression_level': parameters.get('compression_level', 9),
            'method': parameters.get('method', 'LZMA2' if compression_format == CompressionFormat.SEVENZ else 'deflate'),
        }
    
    def _calculate_source_md5(self, rom_path: Path) -> Optional[str]:
        """Calculate MD5 hash of source ROM file for cache lookup.
        
        Args:
            rom_path: Path to ROM file
            
        Returns:
            MD5 hex string or None if failed
        """
        try:
            hash_md5 = hashlib.md5()
            with open(rom_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192 * 1024), b''):  # 8MB chunks
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return None
    
    def should_skip(self, context: StageContext) -> bool:
        """Skip if no files to compress or compression not needed.
        
        Args:
            context: Stage context
            
        Returns:
            True if should skip
        """
        # Check if there are files to compress
        has_extracted = bool(context.extracted_files)
        
        # Check if there are pre-cached outputs (from CachePreCheckStage)
        has_cached = hasattr(context, 'cached_outputs') and bool(context.cached_outputs)
        
        # Skip only if no files AND no cached outputs
        if not has_extracted and not has_cached:
            return True
        
        # If we have cached outputs but nothing to compress, we still need to run
        # to populate compressed_files with the cached outputs
        if not has_extracted and has_cached:
            return False
        
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
        
        compressed_files: List[Path] = []
        
        # Include any files already cached by CachePreCheckStage
        if hasattr(context, 'cached_outputs') and context.cached_outputs:
            cached_count = len(context.cached_outputs)
            compressed_files.extend(context.cached_outputs)
            self._cache_hits += cached_count
            self._log_info(context, f"  Including {cached_count} pre-cached files (skipped extraction)")
        
        compression_format = context.platform_config.compression.format
        compression_config = context.platform_config.compression
        
        # If all files were pre-cached, we're done - no compression needed
        if not context.extracted_files:
            context.compressed_files = compressed_files
            return StageResult(
                status=StageStatus.SUCCESS,
                message=f"All {len(compressed_files)} files from cache (extraction skipped)",
                files_processed=len(compressed_files),
                files_matched=self._cache_hits,
            )
        
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
        
        failed = 0
        parameters = compression_config.parameters or {}
        cache_params = self._get_cache_params(compression_format, parameters)
        
        for rom_path in context.extracted_files:
            try:
                # Determine output path
                if compression_format == CompressionFormat.SEVENZ:
                    output_path = rom_path.with_suffix('.7z')
                else:
                    output_path = rom_path.with_suffix('.zip')
                
                source_md5: Optional[str] = None
                cache_hit = False
                
                # Check cache if enabled
                if self.cache_manager:
                    source_md5 = self._calculate_source_md5(rom_path)
                    if source_md5:
                        cache_result = self.cache_manager.get(
                            source_md5=source_md5,
                            format=compression_format.value,
                            params=cache_params,
                        )
                        if cache_result.hit:
                            # Cache hit - link instead of compressing
                            try:
                                link_success = self.cache_manager.link_to(
                                    cache_result.cache_path,
                                    output_path,
                                )
                                if link_success and output_path.exists():
                                    self._cache_hits += 1
                                    cache_hit = True
                                    self._log_info(context, f"  ✓ Cache hit: {rom_path.name} → linked from cache")
                                    
                                    # Clean up source ROM file since we're using cached archive
                                    if rom_path.exists():
                                        rom_path.unlink()
                                    
                                    compressed_files.append(output_path)
                                    continue  # Skip to next file
                            except Exception as link_err:
                                self._log_warning(context, f"  Cache link failed: {link_err}, will rebuild")
                
                # Cache miss or no cache - compress normally
                compressed_path = self._compress_file(
                    context, 
                    rom_path, 
                    compression_format,
                    tool_path,
                    parameters
                )
                
                if compressed_path and compressed_path.exists():
                    compressed_files.append(compressed_path)
                    
                    # Store in cache if enabled
                    if self.cache_manager and source_md5:
                        try:
                            # Get ZIP identity for fast pre-check on future builds
                            zip_crc32 = None
                            zip_content_size = None
                            if hasattr(context, 'zip_identity_map') and rom_path in context.zip_identity_map:
                                zip_crc32, zip_content_size = context.zip_identity_map[rom_path]
                            
                            self.cache_manager.store(
                                source_md5=source_md5,
                                source_file=rom_path,
                                built_file=compressed_path,
                                format=compression_format.value,
                                params=cache_params,
                                tool_name='7z' if compression_format == CompressionFormat.SEVENZ else 'zip',
                                zip_crc32=zip_crc32,
                                zip_content_size=zip_content_size,
                            )
                            self._cache_misses += 1
                            self._log_info(context, f"  ✓ Stored in cache: {rom_path.name}")
                        except Exception as cache_err:
                            self._log_warning(context, f"  Cache store failed: {cache_err}")
                else:
                    failed += 1
            except Exception as e:
                self._log_error(context, f"Failed to compress {rom_path.name}: {e}")
                failed += 1
        
        # Update context
        context.compressed_files = compressed_files
        
        # Build message with cache stats
        if self.cache_manager:
            message = f"Compressed {len(compressed_files)} files to {compression_format.value} (cache: {self._cache_hits} hits, {self._cache_misses} misses)"
        else:
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
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
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
