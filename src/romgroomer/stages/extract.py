"""Extract archive stage for disc-based systems."""

import re
import shutil
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

from .base import Stage, StageContext, StageResult, StageStatus
from .disc_models import CueSheet


class ExtractArchiveStage(Stage):
    """Extract ZIP archives containing disc images.
    
    For disc-based systems (Saturn, PS1, SegaCD), extract ZIPs to access
    CUE/BIN files for compression. Also detects multi-disc games and
    groups them by base name.
    """
    
    def __init__(self):
        """Initialize extraction stage."""
        super().__init__("Extract Archives")
        self.disc_pattern = re.compile(r'\(Disc (\d+)\)', re.IGNORECASE)
    
    def should_skip(self, context: StageContext) -> bool:
        """Skip if system doesn't require extraction.
        
        Args:
            context: Stage context
            
        Returns:
            True if should skip
        """
        # Skip if no files to extract
        if not context.filtered_files:
            return True
        
        # Skip if system doesn't extract
        if not context.platform_config.extract_archives:
            return True
        
        return False
    
    def execute(self, context: StageContext) -> StageResult:
        """Extract archives and parse disc structure.
        
        Args:
            context: Stage context
            
        Returns:
            Stage result
        """
        if self.should_skip(context):
            return StageResult(
                status=StageStatus.SKIPPED,
                message="Extraction not needed for this system",
            )
        
        self._log_info(context, f"Extracting {len(context.filtered_files)} archives...")
        
        extracted_cues: List[CueSheet] = []
        disc_groups: Dict[str, List[CueSheet]] = {}
        failed = 0
        
        for zip_path in context.filtered_files:
            try:
                cue_sheet = self._extract_archive(context, zip_path, context.work_dir)
                if cue_sheet and cue_sheet.is_valid():
                    extracted_cues.append(cue_sheet)
                    
                    # Group by base name for multi-disc detection
                    base_name = cue_sheet.game_base_name or zip_path.stem
                    if base_name not in disc_groups:
                        disc_groups[base_name] = []
                    disc_groups[base_name].append(cue_sheet)
                else:
                    self._log_warning(context, f"Invalid CUE sheet in {zip_path.name}")
                    failed += 1
            except Exception as e:
                self._log_error(context, f"Failed to extract {zip_path.name}: {e}")
                failed += 1
        
        # Sort discs within each group
        for base_name, discs in disc_groups.items():
            disc_groups[base_name] = sorted(
                discs,
                key=lambda d: d.disc_number or 0
            )
        
        # Update context
        context.extracted_files = [cue.cue_path for cue in extracted_cues]
        context.disc_groups = disc_groups
        
        # Count multi-disc games
        multi_disc_count = sum(1 for discs in disc_groups.values() if len(discs) > 1)
        
        # Clean up ZIP symlinks from work directory (created by FilterDAT)
        # These are no longer needed after extraction
        for zip_path in context.filtered_files:
            if zip_path.is_symlink() and zip_path.exists():
                try:
                    zip_path.unlink()
                    self._log(context, f"  Cleaned up symlink: {zip_path.name}")
                except Exception as e:
                    self._log_warning(context, f"Failed to remove symlink {zip_path.name}: {e}")
        
        message = f"Extracted {len(extracted_cues)} discs ({multi_disc_count} multi-disc games)"
        
        return StageResult(
            status=StageStatus.SUCCESS,
            message=message,
            files_processed=len(context.filtered_files),
            files_matched=len(extracted_cues),
            files_failed=failed,
            details={
                "extracted": [str(cue.cue_path) for cue in extracted_cues],
                "disc_groups": {
                    name: [str(d.cue_path) for d in discs]
                    for name, discs in disc_groups.items()
                },
                "multi_disc_games": multi_disc_count,
            }
        )
    
    def _extract_archive(self, context: StageContext, zip_path: Path, work_dir: Path) -> Optional[CueSheet]:
        """Extract archive and parse CUE sheet.
        
        Args:
            context: Stage context
            zip_path: Path to ZIP file
            work_dir: Working directory for extraction
            
        Returns:
            Parsed CUE sheet or None if failed
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Extract all files
                zf.extractall(work_dir)
                
                # Find CUE file
                cue_files = [
                    f for f in zf.namelist()
                    if f.lower().endswith('.cue')
                ]
                
                if not cue_files:
                    self._log_warning(context, f"No CUE file found in {zip_path.name}")
                    return None
                
                if len(cue_files) > 1:
                    self._log_warning(
                        context,
                        f"Multiple CUE files in {zip_path.name}, using first"
                    )
                
                cue_path = work_dir / cue_files[0]
                return self._parse_cue_sheet(cue_path)
                
        except Exception as e:
            self._log_error(context, f"Failed to extract {zip_path.name}: {e}")
            return None
    
    def _parse_cue_sheet(self, cue_path: Path) -> CueSheet:
        """Parse CUE sheet to find BIN files.
        
        Args:
            cue_path: Path to CUE file
            
        Returns:
            Parsed CUE sheet
        """
        bin_files: List[Path] = []
        
        # Read CUE file
        with open(cue_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                # Look for FILE lines: FILE "track.bin" BINARY
                if line.strip().upper().startswith('FILE'):
                    # Extract filename between quotes
                    match = re.search(r'FILE\s+"([^"]+)"', line, re.IGNORECASE)
                    if match:
                        bin_name = match.group(1)
                        bin_path = cue_path.parent / bin_name
                        bin_files.append(bin_path)
        
        # Detect disc number from filename
        disc_number = None
        game_base_name = None
        
        match = self.disc_pattern.search(cue_path.stem)
        if match:
            disc_number = int(match.group(1))
            # Remove disc info from base name
            game_base_name = self.disc_pattern.sub('', cue_path.stem).strip()
        else:
            game_base_name = cue_path.stem
        
        return CueSheet(
            cue_path=cue_path,
            bin_files=bin_files,
            disc_number=disc_number,
            game_base_name=game_base_name,
        )
