"""Recompress arcade ROM archives (ZIP → 7z).

Arcade ROM ZIPs are multi-file archives (each file is a chip dump).
Emulators like MAME and FBNeo can read either .zip or .7z format.
7z with LZMA2 typically saves 10-30% over ZIP/deflate.

This stage:
  1. Extracts all files from the source .zip
  2. Repacks them into a .7z with LZMA2 compression
  3. Stores the .7z in CAS for instant multi-frontend reuse
  4. Deposits the .7z in work_dir for CopyArcadeStage to pick up

CAS integration:
  - Uses the source ZIP's MD5 as cache key (format="7z", params include level)
  - On cache hit: hardlink from CAS to work_dir (no recompression)
  - On cache miss: recompress → store in CAS → hardlink

CHDs are NOT touched — they pass through CopyArcadeStage unchanged.
"""

import hashlib
import logging
import shutil
import subprocess
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import Stage, StageContext, StageResult, StageStatus

logger = logging.getLogger(__name__)


class RecompressArcadeStage(Stage):
    """Recompress arcade ROM ZIPs to 7z for space savings."""

    _DEFAULT_PARAMS = {
        "format": "7z",
        "compression_level": 9,
        "method": "LZMA2",
    }

    def __init__(
        self,
        cache_manager: Optional[Any] = None,
        compression_level: int = 9,
        method: str = "LZMA2",
    ):
        """Initialize arcade recompression stage.

        Args:
            cache_manager: Optional ROM cache for CAS acceleration.
            compression_level: 7z compression level (1-9, default 9).
            method: 7z compression method (default LZMA2).
        """
        super().__init__("Recompress Arcade")
        self.cache_manager = cache_manager
        self.compression_level = compression_level
        self.method = method
        self._cache_params = {
            "format": "7z",
            "compression_level": compression_level,
            "method": method,
        }

        # Stats
        self._recompressed = 0
        self._cache_hits = 0
        self._failed = 0
        self._skipped = 0

    def should_skip(self, context: StageContext) -> bool:
        """Skip if no source files."""
        return not context.source_files

    def execute(self, context: StageContext) -> StageResult:
        """Recompress arcade ZIPs to 7z.

        Source ZIPs are read from ``context.source_files`` (populated by
        FilterArcadeStage).  The resulting .7z files are placed in
        ``context.work_dir`` and tracked in ``context.extracted_files``
        so that CopyArcadeStage can pick them up.
        """
        if self.should_skip(context):
            return StageResult(
                status=StageStatus.SKIPPED,
                message="No source files to recompress",
            )

        start_time = time.time()

        # Validate 7z binary
        tool_path = shutil.which("7z")
        if not tool_path:
            return StageResult(
                status=StageStatus.FAILED,
                message="7z binary not found in PATH",
            )

        context.work_dir.mkdir(parents=True, exist_ok=True)

        recompressed_files: List[Path] = []
        remaining_source_files: List[Path] = []
        source_zip_count = 0

        self._log_info(
            context,
            f"Recompressing {len(context.source_files)} arcade ROMs to 7z"
            f" (LZMA2, level {self.compression_level})…",
        )

        for src_file in context.source_files:
            # Only recompress .zip files — anything else passes through
            if src_file.suffix.lower() != ".zip":
                remaining_source_files.append(src_file)
                self._skipped += 1
                continue

            source_zip_count += 1
            output_path = context.work_dir / (src_file.stem + ".7z")

            # ── CAS fast path ────────────────────────────────────────
            if self.cache_manager:
                if self._try_cache(src_file, output_path, context):
                    recompressed_files.append(output_path)
                    continue

            # ── Recompress ────────────────────────────────────────────
            try:
                self._recompress_zip(src_file, output_path, tool_path)

                # Store in CAS
                if self.cache_manager:
                    self._store_in_cas(src_file, output_path, context)

                recompressed_files.append(output_path)
                self._recompressed += 1
            except Exception as e:
                self._log_warning(
                    context, f"  ⚠ Failed to recompress {src_file.name}: {e}",
                )
                # Fall back: keep original .zip for CopyArcadeStage
                remaining_source_files.append(src_file)
                self._failed += 1

        # Tell CopyArcadeStage where to find the recompressed ROMs.
        # extracted_files = recompressed .7z in work_dir
        # source_files = anything we couldn't recompress (fallback .zips)
        context.extracted_files = recompressed_files
        context.source_files = remaining_source_files

        duration = time.time() - start_time
        message = (
            f"Recompressed {self._recompressed} ROMs, "
            f"{self._cache_hits} from CAS, "
            f"{self._failed} failed, "
            f"{self._skipped} skipped (non-zip)"
        )
        self._log_info(context, message)

        return StageResult(
            status=StageStatus.SUCCESS if self._failed == 0 else StageStatus.WARNING,
            message=message,
            files_processed=source_zip_count,
            files_matched=self._recompressed + self._cache_hits,
            duration_seconds=duration,
            details={
                "recompressed": self._recompressed,
                "cache_hits": self._cache_hits,
                "failed": self._failed,
                "skipped_non_zip": self._skipped,
            },
        )

    # ── CAS helpers ───────────────────────────────────────────────────────

    def _try_cache(
        self, src_file: Path, output_path: Path, context: StageContext,
    ) -> bool:
        """Try to serve the .7z from CAS. Returns True on hit."""
        try:
            md5 = self._calculate_md5(src_file)
            if not md5:
                return False

            result = self.cache_manager.get(
                source_md5=md5, format="7z", params=self._cache_params,
            )
            if result.hit:
                if self.cache_manager.link_to(result.cache_path, output_path):
                    self._cache_hits += 1
                    self._log_info(
                        context, f"  ✓ CAS hit: {src_file.name}",
                    )
                    return True
        except Exception:
            pass
        return False

    def _store_in_cas(
        self, src_file: Path, built_file: Path, context: StageContext,
    ) -> None:
        """Store a freshly-recompressed .7z in CAS."""
        try:
            md5 = self._calculate_md5(src_file)
            if not md5:
                return

            store_result = self.cache_manager.store(
                source_md5=md5,
                source_file=src_file,
                built_file=built_file,
                format="7z",
                params=self._cache_params,
                tool_name="7z",
            )

            if store_result.hit and store_result.cache_path:
                # Replace work-dir copy with CAS hardlink
                try:
                    built_file.unlink()
                    import os
                    os.link(store_result.cache_path, built_file)
                except OSError:
                    pass  # keep the copy
        except Exception as e:
            self._log_warning(
                context, f"  CAS store failed for {src_file.name}: {e}",
            )

    # ── Compression ───────────────────────────────────────────────────────

    def _recompress_zip(
        self, zip_path: Path, output_path: Path, tool_path: str,
    ) -> None:
        """Extract a ZIP and repack as 7z.

        Uses a temp directory so a failed compression doesn't leave
        partial output.
        """
        with tempfile.TemporaryDirectory(
            prefix="arcade_7z_", dir=zip_path.parent,
        ) as tmp:
            tmp_dir = Path(tmp)

            # Extract ZIP contents
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(tmp_dir)

            # Build 7z command over the extracted files
            cmd = [
                tool_path,
                "a",
                "-t7z",
                f"-mx={self.compression_level}",
                f"-m0={self.method.lower()}",
                str(output_path),
                # Add all files in the temp dir
                str(tmp_dir / "*"),
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False,
            )
            if result.returncode != 0:
                # Clean up partial output
                if output_path.exists():
                    output_path.unlink()
                raise RuntimeError(f"7z failed (rc={result.returncode}): {result.stderr}")

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _calculate_md5(file_path: Path) -> Optional[str]:
        """Calculate MD5 hash of a file."""
        try:
            h = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192 * 1024), b""):
                    h.update(chunk)
            return h.hexdigest()
        except Exception:
            return None
