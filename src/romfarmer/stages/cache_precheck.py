"""Cache pre-check stage to skip extraction for cached files."""

import zipfile
from pathlib import Path
from typing import List, Optional, Tuple

from .base import Stage, StageContext, StageResult, StageStatus
from ..cache import CacheManager


class CachePreCheckStage(Stage):
    """Pre-check cache before extraction to skip already-cached files.
    
    This stage reads ZIP headers (without extraction) to get CRC32 and
    uncompressed size, then checks if those files are already in cache
    using the ZIP identity.
    
    For torrentzipped archives (Myrient, etc.), the CRC32 is stable and
    can uniquely identify contents without extraction.
    
    For cache hits:
    - Hardlink the cached CHD to output
    - Remove from files to process (skip extraction)
    
    For cache misses:
    - Leave in files to process (continue with extraction)
    
    This can save significant time by skipping extraction entirely
    for files we've already processed.
    """
    
    def __init__(
        self, 
        cache_manager: Optional[CacheManager] = None,
        output_format: str = 'chd',
    ):
        """Initialize cache pre-check stage.
        
        Args:
            cache_manager: ROM cache manager
            output_format: Expected output format ('chd', 'rvz', etc.)
        """
        super().__init__("Cache Pre-Check")
        self.cache_manager = cache_manager
        self.output_format = output_format
        
        # Build cache params based on format
        if output_format == 'chd':
            self._cache_params = {
                'format': output_format,
                'compression': 'lzma',
            }
        elif output_format == '7z':
            self._cache_params = {
                'format': output_format,
                'compression_level': 9,
                'method': 'LZMA2',
            }
        elif output_format == 'zip':
            self._cache_params = {
                'format': output_format,
                'compression_level': 9,
                'method': 'deflate',
            }
        else:
            self._cache_params = {
                'format': output_format,
                'compression': 'default',
            }
        
        # Stats
        self._skipped = 0
        self._checked = 0
    
    def should_skip(self, context: StageContext) -> bool:
        """Skip if no cache manager or no files."""
        if not self.cache_manager:
            return True
        if not context.filtered_files:
            return True
        return False
    
    def execute(self, context: StageContext) -> StageResult:
        """Pre-check cache for files before extraction.
        
        Args:
            context: Stage context with files to check
            
        Returns:
            Stage result
        """
        if self.should_skip(context):
            return StageResult(
                status=StageStatus.SKIPPED,
                message="Cache pre-check skipped (no cache or no files)",
            )
        
        self._log_info(context, f"Pre-checking cache for {len(context.filtered_files)} files...")
        
        files_to_process: List[Path] = []
        cached_outputs: List[Path] = []
        
        # Determine output directory
        output_dir = context.work_dir
        
        for file_path in context.filtered_files:
            self._checked += 1
            
            # Skip non-ZIP files
            if file_path.suffix.lower() != '.zip':
                files_to_process.append(file_path)
                continue
            
            # Try to get ZIP identity from headers
            try:
                zip_identity = self._get_zip_identity(file_path)
                if not zip_identity:
                    files_to_process.append(file_path)
                    continue
                
                zip_crc32, zip_content_size, internal_name = zip_identity
                
                # Check cache by ZIP identity (CRC32 + size)
                cache_result = self.cache_manager.get_by_zip_identity(
                    zip_crc32=zip_crc32,
                    zip_content_size=zip_content_size,
                    format=self.output_format,
                    params=self._cache_params,
                )
                
                if cache_result.hit:
                    # Cache hit! Create output via hardlink
                    # Use internal filename to determine output name
                    output_name = Path(internal_name).stem + f'.{self.output_format}'
                    output_path = output_dir / output_name
                    
                    if self.cache_manager.link_to(cache_result.cache_path, output_path):
                        self._skipped += 1
                        cached_outputs.append(output_path)
                        self._log_info(context, f"  ✓ Cache hit (skip extract): {file_path.name}")
                        continue
                
                # Cache miss - needs processing
                files_to_process.append(file_path)
                
            except Exception as e:
                # On any error, fall back to normal processing
                self._log_warning(context, f"  Pre-check failed for {file_path.name}: {e}")
                files_to_process.append(file_path)
        
        # Update context with reduced file list
        context.filtered_files = files_to_process
        
        # Add cached outputs to compressed_files so they're included in output
        if not hasattr(context, 'cached_outputs'):
            context.cached_outputs = []
        context.cached_outputs.extend(cached_outputs)
        
        message = f"Pre-checked {self._checked} files: {self._skipped} cached (skipped), {len(files_to_process)} need processing"
        self._log_info(context, message)
        
        return StageResult(
            status=StageStatus.SUCCESS,
            message=message,
            files_processed=self._checked,
            files_matched=self._skipped,
            details={
                "cached_skipped": self._skipped,
                "needs_processing": len(files_to_process),
                "cached_outputs": [str(p) for p in cached_outputs],
            }
        )
    
    def _get_zip_identity(self, zip_path: Path) -> Optional[Tuple[str, int, str]]:
        """Get ZIP identity from headers: (CRC32, size, filename) of largest file.
        
        Reads only the central directory, no extraction needed.
        For torrentzipped archives, CRC32 is stable and unique.
        
        Args:
            zip_path: Path to ZIP file
            
        Returns:
            Tuple of (crc32_hex, uncompressed_size, filename), or None
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Find the largest file (main content)
                largest_info = None
                largest_size = 0
                
                for info in zf.infolist():
                    if not info.is_dir() and info.file_size > largest_size:
                        largest_size = info.file_size
                        largest_info = info
                
                if not largest_info:
                    return None
                
                # Format CRC32 as 8-character lowercase hex
                crc32_hex = format(largest_info.CRC, '08x')
                
                return (crc32_hex, largest_info.file_size, largest_info.filename)
                
        except Exception:
            return None
