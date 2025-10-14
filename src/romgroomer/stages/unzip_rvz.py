"""Stage for extracting RVZ files from archives.

For Wii and GameCube games stored in Myrient's RVZ format.
RVZ is Dolphin's native compressed format - no conversion needed!
"""

import zipfile
from pathlib import Path
from typing import List

from ..stages.base import Stage, StageContext, StageResult, StageStatus


class UnzipRVZStage(Stage):
    """Extract RVZ files from ZIP archives.
    
    For Nintendo Wii and GameCube, Myrient provides games in RVZ format
    (Dolphin's native compressed format using zstd). These files can be
    used directly without any conversion!
    
    This stage simply extracts RVZ files from ZIP archives to the work
    directory.
    """
    
    def __init__(self):
        """Initialize the UnzipRVZ stage."""
        super().__init__("Unzip RVZ")
    
    def execute(self, context: StageContext) -> StageResult:
        """Extract RVZ files from ZIP archives.
        
        Args:
            context: Stage context with matched files
            
        Returns:
            StageResult with extraction statistics
        """
        self._log_info(context, "Extracting RVZ files from archives...")
        
        extracted_files: List[Path] = []
        failed_files: List[Path] = []
        
        for zip_file in context.matched_files:
            try:
                extracted = self._extract_rvz(zip_file, context.work_dir)
                
                if extracted:
                    extracted_files.extend(extracted)
                    
                    # Log each extracted file with size
                    for rvz_file in extracted:
                        size_gb = rvz_file.stat().st_size / 1e9
                        self._log_info(
                            context,
                            f"  {rvz_file.name} ({size_gb:.1f} GB)"
                        )
                else:
                    self._log_warning(
                        context,
                        f"No RVZ files found in {zip_file.name}"
                    )
                    failed_files.append(zip_file)
                    
            except Exception as e:
                self._log_error(
                    context,
                    f"Failed to extract {zip_file.name}: {e}"
                )
                failed_files.append(zip_file)
        
        # Update context
        context.extracted_files = extracted_files
        
        # Calculate total size
        total_size_gb = sum(f.stat().st_size for f in extracted_files) / 1e9
        
        # Build result message
        message = f"Extracted {len(extracted_files)} RVZ files ({total_size_gb:.1f} GB total)"
        if failed_files:
            message += f", {len(failed_files)} failed"
        
        return StageResult(
            status=StageStatus.SUCCESS if extracted_files else StageStatus.FAILED,
            message=message,
            files_processed=len(context.matched_files),
            files_matched=len(extracted_files),
            files_failed=len(failed_files),
        )
    
    def _extract_rvz(self, zip_file: Path, work_dir: Path) -> List[Path]:
        """Extract RVZ file(s) from a ZIP archive.
        
        Args:
            zip_file: Path to ZIP archive
            work_dir: Working directory for extraction
            
        Returns:
            List of extracted RVZ file paths
        """
        extracted = []
        
        # Create extraction directory (use zip stem as folder name)
        extract_dir = work_dir / zip_file.stem
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(zip_file, 'r') as zf:
            # Find RVZ files in archive
            rvz_files = [f for f in zf.namelist() if f.lower().endswith('.rvz')]
            
            if not rvz_files:
                return []
            
            # Extract each RVZ file
            for rvz_filename in rvz_files:
                # Extract to work directory
                zf.extract(rvz_filename, extract_dir)
                
                # Get full path of extracted file
                extracted_path = extract_dir / rvz_filename
                
                # Ensure file exists
                if extracted_path.exists():
                    extracted.append(extracted_path)
        
        return extracted
