"""Apply list files stage (delete, add from Myrient, add from extras)."""

import time
from pathlib import Path
from typing import Dict, List, Set

from .base import Stage, StageContext, StageResult, StageStatus


class ApplyListsStage(Stage):
    """Apply list files to filter and augment ROM collection.

    List file patterns:
    - {system}-delete: Remove unwanted ROMs (e.g., nes-delete = 26 pirate carts)
    - {system}+{name}: Add from Myrient, creates subdirectory (e.g., nes+Best-Games)
    - {system}.{name}: Add from extra sources, creates subdirectory (e.g., nes.Translations)

    Subdirectories:
    - Best-Games becomes _Best-Games/ (with prefix)
    - Files in list are moved to subdirectory
    """

    def __init__(self):
        """Initialize list files stage."""
        super().__init__("Apply Lists")

    def should_skip(self, context: StageContext) -> bool:
        """Skip if no list configuration."""
        return (
            context.platform_config.lists is None
            or not context.filtered_files
        )

    def execute(self, context: StageContext) -> StageResult:
        """Execute list file application.

        Args:
            context: Stage context with filtered files

        Returns:
            StageResult with list operations applied
        """
        start_time = time.time()

        if self.should_skip(context):
            return StageResult(
                status=StageStatus.SKIPPED,
                message="No list configuration",
            )

        lists_config = context.platform_config.lists
        platform = context.platform_name

        self._log(context, f"[cyan]Applying list files from: {lists_config.directory}[/cyan]")

        # Find list files
        delete_lists = self._find_delete_lists(lists_config.directory, platform)
        add_myrient_lists = self._find_add_lists(lists_config.directory, platform, "+")
        add_extra_lists = self._find_add_lists(lists_config.directory, platform, ".")

        self._log(context, f"  Delete lists: {len(delete_lists)}")
        self._log(context, f"  Add (Myrient) lists: {len(add_myrient_lists)}")
        self._log(context, f"  Add (Extra) lists: {len(add_extra_lists)}")

        # Track operations
        deleted_files = []
        added_files = {}  # subdirectory -> [files]
        files_remaining = context.filtered_files.copy()

        # Step 1: Apply delete lists
        if delete_lists:
            deleted_files = self._apply_delete_lists(
                delete_lists, files_remaining, context
            )
            files_remaining = [f for f in files_remaining if f not in deleted_files]
            self._log(
                context,
                f"  [yellow]Deleted: {len(deleted_files)} files[/yellow]",
            )

        # Step 2: Apply add lists (create subdirectories)
        all_add_lists = {**add_myrient_lists, **add_extra_lists}
        if all_add_lists:
            added_files = self._apply_add_lists(
                all_add_lists, files_remaining, context
            )
            total_added = sum(len(files) for files in added_files.values())
            self._log(
                context,
                f"  [green]Organized into subdirs: {total_added} files in {len(added_files)} subdirs[/green]",
            )

        # Update context
        context.organized_files = added_files
        context.filtered_files = files_remaining

        duration = time.time() - start_time

        context.stats["apply_lists"] = {
            "deleted_files": len(deleted_files),
            "subdirectories": len(added_files),
            "files_in_subdirs": sum(len(files) for files in added_files.values()),
            "files_remaining": len(files_remaining),
        }

        return StageResult(
            status=StageStatus.SUCCESS,
            message=f"Applied lists: {len(deleted_files)} deleted, {len(added_files)} subdirs created",
            files_processed=len(context.filtered_files) + len(deleted_files),
            duration_seconds=duration,
            details={
                "deleted": [f.name for f in deleted_files],
                "subdirectories": list(added_files.keys()),
            },
        )

    def _find_delete_lists(self, list_dir: Path, platform: str) -> List[Path]:
        """Find delete list files for platform.

        Args:
            list_dir: List files directory
            platform: Platform name (e.g., "nes")

        Returns:
            List of delete list file paths
        """
        pattern = f"{platform}-delete*"
        return list(list_dir.glob(pattern))

    def _find_add_lists(
        self, list_dir: Path, platform: str, separator: str
    ) -> Dict[str, Path]:
        """Find add list files for platform.

        Args:
            list_dir: List files directory
            platform: Platform name
            separator: "+" for Myrient, "." for extras

        Returns:
            Dictionary of {list_name: list_file_path}
        """
        lists = {}
        if separator == "+":
            pattern = f"{platform}+*"
        else:
            pattern = f"{platform}.*"

        for list_file in list_dir.glob(pattern):
            # Extract list name: "nes+Best-Games" -> "Best-Games"
            name_parts = list_file.stem.split(separator, 1)
            if len(name_parts) == 2:
                list_name = name_parts[1]
                lists[list_name] = list_file

        return lists

    def _apply_delete_lists(
        self, delete_lists: List[Path], files: List[Path], context: StageContext
    ) -> List[Path]:
        """Apply delete lists to file collection.

        Args:
            delete_lists: List of delete list files
            files: Current file list
            context: Stage context

        Returns:
            List of deleted files
        """
        # Read all files to delete
        files_to_delete = set()
        for list_file in delete_lists:
            with open(list_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        files_to_delete.add(line)

        # Match and mark for deletion
        deleted = []
        for file_path in files:
            # Check if filename (without .zip) matches delete list
            filename = file_path.stem  # "Contra (USA).zip" -> "Contra (USA)"

            if filename in files_to_delete or file_path.name in files_to_delete:
                deleted.append(file_path)
                # Delete from work directory
                if file_path.exists():
                    file_path.unlink()

        return deleted

    def _apply_add_lists(
        self, add_lists: Dict[str, Path], files: List[Path], context: StageContext
    ) -> Dict[str, List[Path]]:
        """Apply add lists to create subdirectories.

        Args:
            add_lists: Dictionary of {list_name: list_file_path}
            files: Current file list
            context: Stage context

        Returns:
            Dictionary of {subdirectory: [files]}
        """
        organized = {}

        for list_name, list_file in add_lists.items():
            # Read files in list
            list_files = set()
            with open(list_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        list_files.add(line)

            # Find matching files
            matched_files = []
            for file_path in files:
                filename = file_path.stem
                if filename in list_files or file_path.name in list_files:
                    matched_files.append(file_path)

            if matched_files:
                # Create subdirectory name with prefix
                subdir_prefix = context.platform_config.targets[0].organization.subdir_prefix or "_"
                subdir_name = f"{subdir_prefix}{list_name}"
                subdir_path = context.work_dir / subdir_name
                subdir_path.mkdir(exist_ok=True)

                # Move files to subdirectory
                moved_files = []
                for file_path in matched_files:
                    dest_path = subdir_path / file_path.name
                    if file_path.exists() and not dest_path.exists():
                        file_path.rename(dest_path)
                        moved_files.append(dest_path)

                organized[subdir_name] = moved_files

        return organized
