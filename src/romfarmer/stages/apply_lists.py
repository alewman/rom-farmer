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

        # Track operations and errors
        deleted_files = []
        added_files = {}  # subdirectory -> [files]
        files_remaining = context.filtered_files.copy()
        errors = []  # Track missing files for reporting
        myrient_added = {}  # Initialize for later use
        extra_added = {}  # Initialize for later use

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

        # Step 2: Apply Myrient add lists (rescue from source, transform)
        if add_myrient_lists:
            myrient_added, myrient_rescued, myrient_errors = self._apply_add_lists(
                add_myrient_lists, files_remaining, context, source_type="myrient"
            )
            added_files.update(myrient_added)
            errors.extend(myrient_errors)
            # Add rescued files back to files_remaining so they flow through pipeline
            files_remaining.extend(myrient_rescued)
            total_myrient = sum(len(files) for files in myrient_added.values())
            self._log(
                context,
                f"  [green]Added from Myrient: {total_myrient} files in {len(myrient_added)} subdirs[/green]",
            )
        
        # Step 3: Apply Extra add lists (copy from extra directory, no transform)
        if add_extra_lists:
            extra_added, extra_errors = self._apply_extra_lists(
                add_extra_lists, context
            )
            added_files.update(extra_added)
            errors.extend(extra_errors)
            total_extra = sum(len(files) for files in extra_added.values())
            self._log(
                context,
                f"  [green]Added from Extra: {total_extra} files in {len(extra_added)} subdirs[/green]",
            )

        # Update context
        context.organized_files = added_files
        context.filtered_files = files_remaining
        
        # Track metadata about subdirectories (Myrient vs Extra for different handling)
        if not hasattr(context, 'organized_files_metadata'):
            context.organized_files_metadata = {}
        
        # Mark Myrient subdirectories (files should be COPIED to subdirs)
        for subdir_name in myrient_added.keys():
            context.organized_files_metadata[subdir_name] = {"type": "myrient", "operation": "copy"}
        
        # Mark Extra subdirectories (files should be MOVED to subdirs)
        for subdir_name in extra_added.keys():
            context.organized_files_metadata[subdir_name] = {"type": "extra", "operation": "move"}

        # Report errors if any
        if errors:
            self._log(context, f"[yellow]⚠ List Processing Warnings:[/yellow]")
            for error in errors:
                self._log(context, f"  [yellow]• {error}[/yellow]")

        duration = time.time() - start_time

        context.stats["apply_lists"] = {
            "deleted_files": len(deleted_files),
            "subdirectories": len(added_files),
            "files_in_subdirs": sum(len(files) for files in added_files.values()),
            "files_remaining": len(files_remaining),
            "errors": len(errors),
        }

        return StageResult(
            status=StageStatus.SUCCESS,
            message=f"Applied lists: {len(deleted_files)} deleted, {len(added_files)} subdirs created"
            + (f", {len(errors)} warnings" if errors else ""),
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
            # Use .name instead of .stem to preserve dots in extra list names
            name_parts = list_file.name.split(separator, 1)
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
        self, add_lists: Dict[str, Path], files: List[Path], context: StageContext, source_type: str = "myrient"
    ) -> tuple[Dict[str, List[Path]], List[Path], List[str]]:
        """Apply add lists to create subdirectories (Myrient source).
        
        This stage can "rescue" files that were filtered out. If a file is in
        an add list but not in the filtered set, we'll find it in the source
        directory and add it back to the working set.

        Args:
            add_lists: Dictionary of {list_name: list_file_path}
            files: Current file list
            context: Stage context
            source_type: "myrient" for archive source

        Returns:
            Tuple of (organized dict, rescued files list, list of error messages)
        """
        organized = {}
        rescued_files = []
        errors = []  # Files added back from source

        for list_name, list_file in add_lists.items():
            # Read files in list
            list_files = set()
            with open(list_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        list_files.add(line)

            # Find matching files in current filtered set
            matched_files = []
            matched_names = set()
            for file_path in files:
                filename = file_path.stem
                if filename in list_files or file_path.name in list_files:
                    matched_files.append(file_path)
                    matched_names.add(file_path.name)
            
            # Track ALL matched files for subdirectory organization
            # (These are games already in the filtered set)
            all_files_for_subdir = matched_files[:]
            
            # Check for files in list that weren't matched (filtered out)
            missing_files = list_files - matched_names
            if missing_files:
                self._log(
                    context,
                    f"  [yellow]Rescuing {len(missing_files)} filtered-out files for {list_name}[/yellow]",
                )
                
                # Try to find and rescue these files from source
                for missing_filename in missing_files:
                    source_file = context.source_dir / missing_filename
                    if source_file.exists():
                        # Symlink to work directory (more efficient than copying)
                        dest_file = context.work_dir / missing_filename
                        if not dest_file.exists():
                            import shutil
                            try:
                                dest_file.symlink_to(source_file)
                            except (OSError, NotImplementedError):
                                # Fallback to copy if symlink fails
                                shutil.copy2(source_file, dest_file)
                            
                            matched_files.append(dest_file)
                            rescued_files.append(dest_file)
                            all_files_for_subdir.append(dest_file)  # Add to subdir tracking
                            self._log(
                                context,
                                f"    ✓ Rescued: {missing_filename}",
                            )
                    else:
                        # File not found in source - track error
                        error_msg = f"{list_name}: '{missing_filename}' not found in source"
                        errors.append(error_msg)
                        self._log(
                            context,
                            f"    [red]✗ Not found in source: {missing_filename}[/red]",
                        )

            if all_files_for_subdir:
                # Track which subdirectory these files belong to (don't move yet!)
                # Convert hyphens to spaces (e.g., "Best-Games" -> "Best Games")
                display_name = list_name.replace("-", " ")
                subdir_prefix = context.platform_config.targets[0].organization.subdir_prefix or ""
                subdir_name = f"{subdir_prefix}{display_name}"
                
                # Store file paths for later organization (files stay in work_dir for now)
                organized[subdir_name] = all_files_for_subdir[:]
        
        # Add rescued files to the main file list so they continue through pipeline
        if rescued_files:
            self._log(
                context,
                f"  [green]✓ Rescued {len(rescued_files)} files total - they will be processed like other ROMs[/green]",
            )

        return organized, rescued_files, errors
    
    def _apply_extra_lists(
        self, extra_lists: Dict[str, Path], context: StageContext
    ) -> tuple[Dict[str, List[Path]], List[str]]:
        """Apply extra lists to add files from extra directory.
        
        Extra files are already in final format (e.g., pre-patched CHDs),
        so they're copied directly to subdirectories without transformation.

        Args:
            extra_lists: Dictionary of {list_name: list_file_path}
            context: Stage context

        Returns:
            Tuple of (organized dict, list of error messages)
        """
        organized = {}
        errors = []
        
        # Determine extra source directory - simplified to just use platform name
        extra_base = Path("/data/emu/source/extra")
        platform = context.platform_name
        extra_dir = extra_base / platform
        
        if not extra_dir.exists():
            self._log(
                context,
                f"  [yellow]⚠ Extra directory not found: {extra_dir}, skipping extra lists[/yellow]",
            )
            return organized
        
        self._log(context, f"  Using extra directory: {extra_dir}")

        for list_name, list_file in extra_lists.items():
            # Read files in list
            list_files = set()
            with open(list_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        list_files.add(line)

            # Find matching files in extra directory
            matched_files = []
            for filename in list_files:
                source_path = extra_dir / filename
                if source_path.exists():
                    # Copy file to work directory (not subdirectory yet - OrganizeStage will handle that)
                    dest_path = context.work_dir / filename
                    if not dest_path.exists():
                        import shutil
                        shutil.copy2(source_path, dest_path)
                        matched_files.append(dest_path)
                        self._log(
                            context,
                            f"    ✓ Added from extra: {filename}",
                        )
                else:
                    # File not found in extra - track error
                    error_msg = f"{list_name}: '{filename}' not found in {extra_dir}"
                    errors.append(error_msg)
                    self._log(
                        context,
                        f"    [red]✗ Not found in extra: {filename}[/red]",
                    )

            if matched_files:
                # Track which subdirectory these files belong to (don't move yet!)
                subdir_prefix = context.platform_config.targets[0].organization.subdir_prefix or ""
                display_name = list_name.replace("-", " ")
                subdir_name = f"{subdir_prefix}{display_name}"
                organized[subdir_name] = matched_files

        return organized, errors
