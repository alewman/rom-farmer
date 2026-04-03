"""CAS ingest stage — store loose files in CAS for cross-build dedup.

For platforms with no extraction (ExtractionType.NONE), source files are
already in their final format. This stage ingests them into the content-
addressable store so subsequent builds for different frontends get instant
hardlinks from CAS instead of re-reading from source.

Pipeline position:
    Filter → ApplyLists → **CASIngestStage** → Organize/EmitExtras

The stage:
  1. Hashes each filtered file (MD5)
  2. Stores it in CAS if not already present
  3. Creates a hardlink in work_dir pointing to the CAS blob
  4. Updates filtered_files to reference the work_dir copies

Downstream stages (Organize, EmitExtras) then operate on CAS-backed
files, and the output gets hardlinked from CAS — zero additional disk
cost for multi-frontend builds.
"""

import hashlib
import logging
import os
import time
from pathlib import Path
from typing import List, Optional

from .base import Stage, StageContext, StageResult, StageStatus

logger = logging.getLogger(__name__)


class CASIngestStage(Stage):
    """Ingest loose source files into CAS for deduplication.

    Unlike CacheStoreStage (which replaces work-dir files in-place after
    extraction), this stage is designed for the no-extraction path where
    source files should not be modified.
    """

    def __init__(self, cache_manager: Optional[object] = None):
        super().__init__("CAS Ingest")
        self.cache_manager = cache_manager

        # Stats
        self._stored = 0
        self._already_cached = 0
        self._failed = 0

    def should_skip(self, context: StageContext) -> bool:
        if not self.cache_manager:
            return True
        files = context.filtered_files
        if not files:
            return True
        return False

    def execute(self, context: StageContext) -> StageResult:
        if self.should_skip(context):
            return StageResult(
                status=StageStatus.SKIPPED,
                message="CAS ingest skipped (no cache or no files)",
            )

        start = time.time()
        files = list(context.filtered_files)
        work_dir = context.work_dir
        work_dir.mkdir(parents=True, exist_ok=True)

        self._log_info(context, f"Ingesting {len(files)} files into CAS...")

        cas_backed: List[Path] = []

        for file_path in files:
            if not file_path.exists():
                self._log_warning(context, f"  File not found: {file_path.name}")
                self._failed += 1
                continue

            try:
                # Hash the source file
                source_md5 = self._calculate_md5(file_path)
                if not source_md5:
                    self._failed += 1
                    cas_backed.append(file_path)  # keep original
                    continue

                # Format from extension (wad, iso, etc.)
                fmt = file_path.suffix.lstrip(".").lower() or "bin"
                params = {"format": fmt, "compression": "passthrough"}

                # Check CAS — may already exist from a previous build
                cache_result = self.cache_manager.get(
                    source_md5=source_md5,
                    format=fmt,
                    params=params,
                )

                if cache_result.hit:
                    # Already in CAS — hardlink to work_dir
                    work_path = work_dir / file_path.name
                    if not work_path.exists():
                        try:
                            os.link(cache_result.cache_path, work_path)
                        except OSError:
                            os.link(file_path, work_path)
                    cas_backed.append(work_path)
                    self._already_cached += 1
                    continue

                # Not in CAS — store it (copies into store/, records in DB)
                store_result = self.cache_manager.store(
                    source_md5=source_md5,
                    source_file=file_path,
                    built_file=file_path,
                    format=fmt,
                    params=params,
                    tool_name="passthrough",
                )

                if store_result.hit and store_result.cache_path:
                    # Stored successfully — hardlink CAS blob to work_dir
                    work_path = work_dir / file_path.name
                    if not work_path.exists():
                        try:
                            os.link(store_result.cache_path, work_path)
                        except OSError:
                            os.link(file_path, work_path)
                    cas_backed.append(work_path)
                    self._stored += 1
                else:
                    # Store failed — keep original source path
                    cas_backed.append(file_path)
                    self._failed += 1

            except Exception as e:
                self._log_warning(
                    context, f"  CAS ingest failed for {file_path.name}: {e}"
                )
                self._failed += 1
                cas_backed.append(file_path)

        # Update context — downstream stages get CAS-backed work_dir paths
        context.filtered_files = cas_backed

        duration = time.time() - start
        message = (
            f"Ingested {self._stored} new, "
            f"{self._already_cached} from cache, "
            f"{self._failed} failed "
            f"({len(cas_backed)} total)"
        )
        self._log_info(context, message)

        return StageResult(
            status=StageStatus.SUCCESS,
            message=message,
            files_processed=len(files),
            files_matched=self._stored + self._already_cached,
            files_failed=self._failed,
            duration_seconds=duration,
            details={
                "stored": self._stored,
                "already_cached": self._already_cached,
                "failed": self._failed,
            },
        )

    @staticmethod
    def _calculate_md5(file_path: Path) -> Optional[str]:
        """Calculate MD5 hash of a file."""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192 * 1024), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return None
