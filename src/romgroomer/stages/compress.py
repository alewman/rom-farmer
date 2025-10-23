"""Compress disc images to CHD format."""

import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from .base import Stage, StageContext, StageResult, StageStatus
from .disc_models import CueSheet


class CompressCHDStage(Stage):
    """Compress BIN/CUE disc images to CHD format.
    
    Uses chdman to convert disc images to compressed CHD format.
    Tracks transformations for hash management.
    """
    
    def __init__(self, chdman_path: Optional[Path] = None):
        """Initialize compression stage.
        
        Args:
            chdman_path: Path to chdman binary (auto-detected if None)
        """
        super().__init__("Compress to CHD")
        self.chdman_path = chdman_path or self._find_chdman()
    
    def _find_chdman(self) -> Optional[Path]:
        """Find chdman binary.
        
        Returns:
            Path to chdman or None if not found
        """
        # Check in tools directory
        tools_chdman = Path(__file__).parent.parent.parent.parent / "tools" / "bin" / "chdman"
        if tools_chdman.exists():
            return tools_chdman
        
        # Check system PATH
        system_chdman = shutil.which("chdman")
        if system_chdman:
            return Path(system_chdman)
        
        return None
    
    def should_skip(self, context: StageContext) -> bool:
        """Skip if no files to compress or no chdman.
        
        Args:
            context: Stage context
            
        Returns:
            True if should skip
        """
        if not context.extracted_files:
            return True
        
        if not self.chdman_path:
            self._log_error(context, "chdman not found, cannot compress discs")
            return True
        
        return False
    
    def validate_context(self, context: StageContext) -> bool:
        """Validate context has required data.
        
        Args:
            context: Stage context
            
        Returns:
            True if valid
        """
        if not self.chdman_path or not self.chdman_path.exists():
            self._log_error(context, f"chdman not found at {self.chdman_path}")
            return False
        
        return True
    
    def execute(self, context: StageContext) -> StageResult:
        """Compress disc images to CHD.
        
        Args:
            context: Stage context
            
        Returns:
            Stage result
        """
        if self.should_skip(context):
            return StageResult(
                status=StageStatus.SKIPPED,
                message="No files to compress or chdman not found",
            )
        
        if not self.validate_context(context):
            return StageResult(
                status=StageStatus.FAILED,
                message="chdman validation failed",
                error="chdman not found or not executable",
            )
        
        self._log_info(context, f"Compressing {len(context.extracted_files)} discs to CHD...")
        
        compressed_files: List[Path] = []
        failed = 0
        
        for cue_path in context.extracted_files:
            try:
                chd_path = self._compress_to_chd(context, cue_path)
                if chd_path and chd_path.exists():
                    compressed_files.append(chd_path)
                    # Clean up CUE/BIN files after successful compression
                    self._cleanup_source_files(context, cue_path)
                else:
                    self._log_error(context, f"Failed to create CHD for {cue_path.name}")
                    failed += 1
            except Exception as e:
                self._log_error(context, f"Failed to compress {cue_path.name}: {e}")
                failed += 1
        
        # Update context
        context.compressed_files = compressed_files
        
        message = f"Compressed {len(compressed_files)} discs to CHD"
        
        return StageResult(
            status=StageStatus.SUCCESS,
            message=message,
            files_processed=len(context.extracted_files),
            files_matched=len(compressed_files),
            files_failed=failed,
            details={
                "compressed": [str(p) for p in compressed_files],
                "format": "chd",
            }
        )
    
    def _compress_to_chd(self, context, cue_path: Path) -> Optional[Path]:
        """Compress CUE/BIN to CHD.
        
        Args:
            cue_path: Path to CUE file
            
        Returns:
            Path to created CHD or None if failed
        """
        # Output CHD has same name as CUE
        chd_path = cue_path.with_suffix('.chd')
        
        try:
            # Run chdman createcd
            cmd = [
                str(self.chdman_path),
                'createcd',
                '-i', str(cue_path),
                '-o', str(chd_path),
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )
            
            if result.returncode != 0:
                self._log_error(context, f"chdman failed for {cue_path.name}:")
                self._log_error(context, result.stderr)
                return None
            
            return chd_path
            
        except Exception as e:
            self._log_error(context, f"Exception running chdman: {e}")
            return None
    
    def _cleanup_source_files(self, context, cue_path: Path):
        """Clean up CUE and BIN files after successful compression.
        
        Args:
            cue_path: Path to CUE file
        """
        try:
            # Parse CUE to find BIN files
            bin_files: List[Path] = []
            
            with open(cue_path, 'r', encoding='utf-8', errors='ignore') as f:
                import re
                for line in f:
                    if line.strip().upper().startswith('FILE'):
                        match = re.search(r'FILE\s+"([^"]+)"', line, re.IGNORECASE)
                        if match:
                            bin_name = match.group(1)
                            bin_path = cue_path.parent / bin_name
                            bin_files.append(bin_path)
            
            # Delete CUE file
            if cue_path.exists():
                cue_path.unlink()
            
            # Delete BIN files
            for bin_path in bin_files:
                if bin_path.exists():
                    bin_path.unlink()
                    
        except Exception as e:
            self._log_warning(context, f"Failed to cleanup source files: {e}")
