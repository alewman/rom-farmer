"""Filter ROMs against DAT file stage."""

import time
from pathlib import Path
from typing import List

from ..dat_parser import DATFile, ROMMatcher
from .base import Stage, StageContext, StageResult, StageStatus


class FilterDATStage(Stage):
    """Filter source ROM files against DAT file.

    For No-Intro:
    - Match ZIP files against Retool DAT entries
    - Copy matched ZIPs to work directory (no extraction!)
    - Track unmatched files for reporting

    For Redump:
    - Match ZIP files against Retool DAT entries
    - Mark for extraction in next stage
    """

    def __init__(self):
        """Initialize DAT filter stage."""
        super().__init__("Filter DAT")

    def should_skip(self, context: StageContext) -> bool:
        """Skip if no DAT file or no source files."""
        return context.dat_file is None or not context.source_files

    def validate_context(self, context: StageContext) -> str | None:
        """Validate context."""
        if not context.source_dir.exists():
            return f"Source directory not found: {context.source_dir}"
        if not context.work_dir.exists():
            context.work_dir.mkdir(parents=True, exist_ok=True)
        return None

    def execute(self, context: StageContext) -> StageResult:
        """Execute DAT filtering.

        Args:
            context: Stage context with DAT and source files

        Returns:
            StageResult with matched files
        """
        start_time = time.time()

        # Validate
        error = self.validate_context(context)
        if error:
            return StageResult(
                status=StageStatus.FAILED,
                message="Validation failed",
                error=ValueError(error),
            )

        if self.should_skip(context):
            return StageResult(
                status=StageStatus.SKIPPED,
                message="No DAT file or source files",
            )

        self._log(context, f"[cyan]Filtering against DAT: {context.dat_file.name}[/cyan]")
        self._log(context, f"  Games in DAT: {context.dat_file.get_game_count():,}")
        self._log(context, f"  Source files: {len(context.source_files):,}")

        # Create matcher
        matcher = ROMMatcher(context.dat_file)

        # Match files
        matched_files = []
        unmatched_files = []
        hash_matched = 0
        name_matched = 0

        for file_path in context.source_files:
            # Try MD5 matching first if we have it (from ARRM metadata)
            # This handles renamed files (e.g., Redump region improvements)
            result = None
            if hasattr(context, 'file_md5s') and file_path in context.file_md5s:
                md5 = context.file_md5s[file_path]
                result = matcher.match_by_hash(file_path, md5=md5)
                if result.is_matched():
                    hash_matched += 1
            
            # Fallback to name-based matching
            if not result or not result.is_matched():
                result = matcher.match_file(file_path)
                if result.is_matched():
                    name_matched += 1

            if result.is_matched():
                matched_files.append(file_path)
            else:
                unmatched_files.append(file_path)

        # Copy matched files to work directory (for No-Intro, these stay as ZIPs)
        copied_files = []
        for file_path in matched_files:
            dest_path = context.work_dir / file_path.name
            if not dest_path.exists():
                # For now, create symlink (copy in production)
                try:
                    dest_path.symlink_to(file_path)
                    copied_files.append(dest_path)
                except OSError:
                    # If symlink fails, try copy
                    import shutil
                    shutil.copy2(file_path, dest_path)
                    copied_files.append(dest_path)
            else:
                copied_files.append(dest_path)

        # Update context
        context.matched_files = copied_files
        context.filtered_files = copied_files

        # Statistics
        duration = time.time() - start_time
        match_rate = (len(matched_files) / len(context.source_files) * 100) if context.source_files else 0

        context.stats["dat_filter"] = {
            "source_files": len(context.source_files),
            "matched_files": len(matched_files),
            "unmatched_files": len(unmatched_files),
            "match_rate": match_rate,
            "copied_files": len(copied_files),
            "hash_matched": hash_matched,
            "name_matched": name_matched,
        }

        self._log(
            context,
            f"  [green]Matched: {len(matched_files):,} ({match_rate:.1f}%)[/green]",
        )
        if hash_matched > 0:
            self._log(
                context,
                f"    [cyan]MD5 matched: {hash_matched:,}[/cyan]",
            )
        if name_matched > 0:
            self._log(
                context,
                f"    [cyan]Name matched: {name_matched:,}[/cyan]",
            )
        self._log(
            context,
            f"  [yellow]Unmatched: {len(unmatched_files):,}[/yellow]",
        )

        return StageResult(
            status=StageStatus.SUCCESS,
            message=f"Filtered {len(matched_files):,} ROMs from {len(context.source_files):,} files",
            files_processed=len(context.source_files),
            files_matched=len(matched_files),
            files_skipped=len(unmatched_files),
            duration_seconds=duration,
            details={
                "matched": [f.name for f in matched_files[:10]],  # Sample
                "unmatched": [f.name for f in unmatched_files[:10]],  # Sample
                "match_rate": match_rate,
            },
        )
