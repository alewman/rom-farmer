"""Cache store stage — ingest extracted files into CAS.

For pipelines that extract files without transformation (RVZ, raw cartridge
ROMs, etc.), this stage stores the extracted output in the CAS cache and
replaces the work-dir copy with a hardlink from CAS.

Benefits:
  - CAS becomes self-contained (no need for source archives to rebuild)
  - Multi-frontend builds are instant (hardlink from CAS, zero disk cost)
  - Identical files across platforms are automatically deduplicated

This is the "store" counterpart to CachePreCheckStage. Together they form
the complete CAS passthrough:

    CachePreCheckStage  →  (extraction stage)  →  CacheStoreStage
    "skip if cached"        UnzipRVZ / etc.        "store if new"
"""

import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .base import Stage, StageContext, StageResult, StageStatus
from ..cache import CacheManager


class CacheStoreStage(Stage):
    """Store extracted files in CAS after extraction.

    Runs after an extraction stage (UnzipRVZ, ExtractArchive, etc.) to
    ingest the extracted files into the content-addressed cache. Each file
    is stored by its MD5, and the work-dir copy is replaced with a
    hardlink from CAS so downstream stages (Organize) get CAS-backed files.

    Files that were already served from cache (via CachePreCheckStage)
    are skipped — they're already CAS-backed.
    """

    def __init__(
        self,
        cache_manager: Optional[CacheManager] = None,
        output_format: Optional[str] = "rvz",
        tool_name: str = "passthrough",
    ):
        """Initialize cache store stage.

        Args:
            cache_manager: ROM cache manager instance.
            output_format: File format label for CAS (e.g. 'rvz', 'nes', 'gba').
                Use ``None`` for auto-detect mode — the format is derived
                from each file's extension. This handles platforms with
                mixed or varying ROM extensions.
            tool_name: Tool label recorded in the cache DB.
        """
        super().__init__("Cache Store")
        self.cache_manager = cache_manager
        self.output_format = output_format  # None = auto-detect
        self.tool_name = tool_name

        # Stats
        self._stored = 0
        self._already_cached = 0
        self._failed = 0

    def _resolve_format(self, file_path: Path) -> str:
        """Return the CAS format string for a file.

        Fixed format when ``output_format`` is set, otherwise derive from
        the file extension.
        """
        if self.output_format is not None:
            return self.output_format
        return file_path.suffix.lstrip(".").lower() or "bin"

    def _cache_params(self, fmt: str) -> dict:
        """Return cache params for the given format."""
        return {
            "format": fmt,
            "compression": "passthrough",
        }

    # ── skip logic ────────────────────────────────────────────────────────

    def should_skip(self, context: StageContext) -> bool:
        """Skip when there is no cache manager or no extracted files."""
        if not self.cache_manager:
            return True
        files = context.extracted_files or context.filtered_files
        if not files:
            return True
        return False

    # ── execute ───────────────────────────────────────────────────────────

    def execute(self, context: StageContext) -> StageResult:
        """Store every extracted file in CAS and replace with a hardlink.

        Uses ``extracted_files`` if available (from UnzipRVZ / ExtractArchive),
        otherwise falls back to ``filtered_files`` (for no-extraction paths).

        Already-cached outputs produced by CachePreCheckStage are skipped.
        """
        if self.should_skip(context):
            return StageResult(
                status=StageStatus.SKIPPED,
                message="Cache store skipped (no cache or no files)",
            )

        # Files produced by the extraction stage
        files = list(context.extracted_files or context.filtered_files)

        # Build a set of paths that CachePreCheckStage already linked from CAS
        # so we don't re-store them.
        cached_paths = set()
        if hasattr(context, "cached_outputs"):
            cached_paths = {Path(p) if not isinstance(p, Path) else p for p in context.cached_outputs}

        self._log_info(
            context,
            f"Storing {len(files)} files in CAS"
            + (f" (format={self.output_format})" if self.output_format else " (auto-detect format)")
            + "…",
        )

        stored_files: List[Path] = []

        for file_path in files:
            # Skip files that were already linked from CAS by pre-check stage
            if file_path in cached_paths:
                self._already_cached += 1
                stored_files.append(file_path)
                continue

            if not file_path.exists():
                self._log_warning(context, f"  ⚠ File not found: {file_path.name}")
                self._failed += 1
                continue

            try:
                # Compute source MD5
                source_md5 = self._calculate_md5(file_path)
                if not source_md5:
                    self._failed += 1
                    continue

                # Resolve format for this file
                fmt = self._resolve_format(file_path)
                params = self._cache_params(fmt)

                # Check CAS first — file may already exist from a previous build
                cache_result = self.cache_manager.get(
                    source_md5=source_md5,
                    format=fmt,
                    params=params,
                )

                if cache_result.hit:
                    # Already in CAS — replace work-dir file with a hardlink
                    self._replace_with_link(file_path, cache_result.cache_path, context)
                    self._already_cached += 1
                    stored_files.append(file_path)
                    continue

                # Not in CAS — resolve ZIP identity for fast pre-check on future builds
                zip_crc32, zip_content_size = self._get_zip_identity(file_path, context)

                # Store in CAS (copies file into store/, records in DB)
                store_result = self.cache_manager.store(
                    source_md5=source_md5,
                    source_file=file_path,
                    built_file=file_path,        # same file — no transformation
                    format=fmt,
                    params=params,
                    tool_name=self.tool_name,
                    zip_crc32=zip_crc32,
                    zip_content_size=zip_content_size,
                )

                if store_result.hit and store_result.cache_path:
                    # Replace work-dir copy with hardlink to CAS (saves space)
                    self._replace_with_link(file_path, store_result.cache_path, context)
                    self._stored += 1
                    stored_files.append(file_path)
                    self._log_info(context, f"  ✓ Stored: {file_path.name}")
                else:
                    # Store didn't fail hard but didn't produce a path — keep original
                    self._failed += 1
                    stored_files.append(file_path)

            except Exception as e:
                self._log_warning(context, f"  ⚠ Cache store failed for {file_path.name}: {e}")
                self._failed += 1
                stored_files.append(file_path)  # Keep original on failure

        # Update context — downstream (Organize) sees the same file list,
        # but now files are backed by CAS hardlinks.
        if context.extracted_files:
            context.extracted_files = stored_files
        else:
            context.filtered_files = stored_files

        message = (
            f"Cached {self._stored} new, "
            f"{self._already_cached} already cached, "
            f"{self._failed} failed"
        )
        self._log_info(context, message)

        return StageResult(
            status=StageStatus.SUCCESS,
            message=message,
            files_processed=len(files),
            files_matched=self._stored + self._already_cached,
            files_failed=self._failed,
            details={
                "stored": self._stored,
                "already_cached": self._already_cached,
                "failed": self._failed,
            },
        )

    # ── helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _calculate_md5(file_path: Path) -> Optional[str]:
        """Calculate MD5 hash of a file."""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192 * 1024), b""):  # 8 MB chunks
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return None

    @staticmethod
    def _get_zip_identity(
        file_path: Path, context: StageContext
    ) -> Tuple[Optional[str], Optional[int]]:
        """Look up ZIP identity from context for fast future pre-checks."""
        if hasattr(context, "zip_identity_map") and file_path in context.zip_identity_map:
            return context.zip_identity_map[file_path]
        return None, None

    def _replace_with_link(
        self, work_path: Path, cache_path: Path, context: StageContext
    ) -> None:
        """Replace a work-dir file with a hardlink to the CAS copy.

        If the hardlink fails (cross-filesystem), the original is kept.
        """
        try:
            import os

            work_path.unlink()
            os.link(cache_path, work_path)
        except OSError:
            # Cross-filesystem or permission error — keep the copy
            self._log_warning(
                context,
                f"  Could not hardlink {work_path.name} from CAS, keeping copy",
            )
