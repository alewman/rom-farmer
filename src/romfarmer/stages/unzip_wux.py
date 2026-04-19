"""Stage for extracting WUX files from archives.

For Wii U games stored in Myrient's WUX format.
WUX is a compressed encrypted disc image — Cemu decrypts on-the-fly!
"""

import zipfile
from pathlib import Path
from typing import List

from ..stages.base import Stage, StageContext, StageResult, StageStatus


class UnzipWUXStage(Stage):
    """Extract WUX files from ZIP archives.

    For Nintendo Wii U, Myrient provides games as .wux files inside .zip
    archives. WUX (Wii U compressed image) is already compressed and is
    used directly by Cemu without conversion.

    This stage simply extracts WUX files from ZIP archives to the work
    directory.
    """

    def __init__(self):
        """Initialize the UnzipWUX stage."""
        super().__init__("Unzip WUX")

    def execute(self, context: StageContext) -> StageResult:
        """Extract WUX files from ZIP archives.

        Args:
            context: Stage context with filtered files

        Returns:
            StageResult with extraction statistics
        """
        files_to_extract = context.filtered_files or context.matched_files
        if not files_to_extract:
            self._log_warning(context, "No files to extract")
            return StageResult(
                status=StageStatus.SKIPPED,
                message="No files to extract",
                files_processed=0,
                files_matched=0,
                files_failed=0,
            )

        self._log_info(context, f"Extracting {len(files_to_extract)} WUX archives...")

        extracted_files: List[Path] = []
        failed_files: List[Path] = []

        for zip_file in files_to_extract:
            try:
                extracted = self._extract_wux(zip_file, context.work_dir)

                if extracted:
                    extracted_files.extend(extracted)

                    for wux_file in extracted:
                        size_gb = wux_file.stat().st_size / 1e9
                        self._log_info(
                            context,
                            f"  {wux_file.name} ({size_gb:.1f} GB)"
                        )
                else:
                    self._log_warning(
                        context,
                        f"No WUX files found in {zip_file.name}"
                    )
                    failed_files.append(zip_file)

            except Exception as e:
                self._log_error(
                    context,
                    f"Failed to extract {zip_file.name}: {e}"
                )
                failed_files.append(zip_file)

        context.extracted_files = extracted_files

        total_size_gb = sum(f.stat().st_size for f in extracted_files) / 1e9

        message = f"Extracted {len(extracted_files)} WUX files ({total_size_gb:.1f} GB total)"
        if failed_files:
            message += f", {len(failed_files)} failed"

        return StageResult(
            status=StageStatus.SUCCESS if extracted_files else StageStatus.FAILED,
            message=message,
            files_processed=len(files_to_extract),
            files_matched=len(extracted_files),
            files_failed=len(failed_files),
        )

    def _extract_wux(self, zip_file: Path, work_dir: Path) -> List[Path]:
        """Extract WUX file(s) from a ZIP archive.

        Args:
            zip_file: Path to ZIP archive
            work_dir: Working directory for extraction

        Returns:
            List of extracted WUX file paths
        """
        extracted = []

        extract_dir = work_dir / zip_file.stem
        extract_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_file, 'r') as zf:
            wux_files = [f for f in zf.namelist() if f.lower().endswith('.wux')]

            if not wux_files:
                return []

            for wux_filename in wux_files:
                zf.extract(wux_filename, extract_dir)

                extracted_path = extract_dir / wux_filename

                if extracted_path.exists():
                    extracted.append(extracted_path)

        return extracted
