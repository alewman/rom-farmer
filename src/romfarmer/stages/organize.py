"""Organize ROMs into target structure stage."""

import time
from pathlib import Path
from typing import Dict, List

from ..config import OrganizationStyle
from .base import Stage, StageContext, StageResult, StageStatus


class OrganizeStage(Stage):
    """Organize ROMs into final structure for target system.

    Organization styles:
    - RICH: Deep subdirectories, full metadata (Batocera)
    - BALANCED: Alphabetical grouping (A-E, F-M, etc.) (RocknIX)
    - MINIMAL: sort2folders logic, max 50 files/group (Everdrive)
    - FLAT: All files in one directory
    """

    def __init__(self):
        """Initialize organize stage."""
        super().__init__("Organize")

    def should_skip(self, context: StageContext) -> bool:
        """Skip if no files to organize."""
        has_files = (
            context.compressed_files
            or context.extracted_files
            or context.filtered_files
            or context.organized_files
        )
        return not has_files

    def execute(self, context: StageContext) -> StageResult:
        """Execute organization.

        Args:
            context: Stage context with filtered files

        Returns:
            StageResult with organized structure
        """
        start_time = time.time()

        if self.should_skip(context):
            return StageResult(
                status=StageStatus.SKIPPED,
                message="No files to organize",
            )

        target_config = context.platform_config.targets[0]  # First target
        org_style = target_config.organization.style

        self._log(
            context,
            f"[cyan]Organizing with style: {org_style.value}[/cyan]",
        )

        # Create output directory structure
        context.output_dir.mkdir(parents=True, exist_ok=True)

        files_organized = 0

        # Determine which files to organize (use most recent stage output)
        # Priority: compressed_files > extracted_files > filtered_files
        files_to_organize = (
            context.compressed_files
            or context.extracted_files
            or context.filtered_files
        )

        # Add M3U files to the list of files to organize
        m3u_files = getattr(context, 'm3u_files', None)
        if m3u_files:
            files_to_organize = list(files_to_organize) + list(m3u_files)

        # Organize main files (not in subdirectories)
        if files_to_organize:
            if org_style == OrganizationStyle.FLAT:
                files_organized += self._organize_flat(
                    files_to_organize, context.output_dir, context
                )
            elif org_style == OrganizationStyle.BALANCED:
                files_organized += self._organize_balanced(
                    files_to_organize, context.output_dir, context
                )
            elif org_style == OrganizationStyle.MINIMAL:
                files_organized += self._organize_minimal(
                    files_to_organize,
                    context.output_dir,
                    target_config.organization.max_files_per_group,
                    context,
                )
            else:  # RICH
                files_organized += self._organize_rich(
                    files_to_organize, context.output_dir, context
                )

        # Organize subdirectory files (from list files)
        if context.organized_files:
            # Get metadata about subdirectories (if available)
            subdir_metadata = getattr(context, 'organized_files_metadata', {})
            
            for subdir_name, original_files in context.organized_files.items():
                subdir_path = context.output_dir / subdir_name
                subdir_path.mkdir(parents=True, exist_ok=True)
                
                # Get operation type (copy for Myrient, move for Extra)
                metadata = subdir_metadata.get(subdir_name, {"operation": "move"})
                operation = metadata.get("operation", "move")
                
                if operation == "copy":
                    # Myrient lists: Find transformed files by stem and COPY
                    # Original files are .zip but now they might be:
                    # - .chd/.m3u (disc systems)
                    # - .zip/.7z (cartridge systems)
                    # - .rvz (GameCube/Wii)
                    for original_path in original_files:
                        stem = original_path.stem  # "Game (USA)" from "Game (USA).zip"
                        
                        # Find matching transformed files in output_dir
                        # Search recursively since files might be in alphabetical subdirs (A-E, F-M, etc.)
                        matches = list(context.output_dir.glob(f"**/{stem}.*"))
                        
                        for match in matches:
                            # Support various output formats:
                            # - Disc: .chd, .m3u, .iso, .cso
                            # - Cartridge (compressed): .zip, .7z
                            # - Cartridge (raw): .j64 (Jaguar), .n64, .z64, .v64, .gb, .gbc, .gba, .nes, .sfc, .smd, .gen, .32x
                            # - Other: .rvz (GameCube/Wii)
                            valid_extensions = {
                                '.chd', '.m3u', '.iso', '.cso',  # Disc formats
                                '.zip', '.7z',  # Compressed archives
                                '.rvz',  # GameCube/Wii
                                '.j64', '.n64', '.z64', '.v64',  # N64/Jaguar
                                '.gb', '.gbc', '.gba',  # Game Boy
                                '.nes', '.sfc', '.smc',  # NES/SNES
                                '.smd', '.gen', '.bin', '.32x', '.gg', '.sms',  # Sega
                                '.vb',  # Virtual Boy
                                '.vec', '.col', '.ngp', '.ngc', '.int',  # Other
                            }
                            if match.suffix.lower() in valid_extensions:
                                dest_path = subdir_path / match.name
                                if not dest_path.exists():
                                    import shutil
                                    shutil.copy2(match, dest_path)
                                    files_organized += 1
                                    self._log(context, f"  Copied to {subdir_name}/: {match.name}")
                else:
                    # Extra lists: MOVE files (already in final format)
                    for file_path in original_files:
                        if file_path.exists():
                            dest_path = subdir_path / file_path.name
                            if not dest_path.exists():
                                file_path.rename(dest_path)
                                files_organized += 1
                                self._log(context, f"  Moved to {subdir_name}/: {file_path.name}")
                        else:
                            self._log(context, f"  [yellow]⚠ File not found: {file_path}[/yellow]")

        duration = time.time() - start_time

        context.stats["organize"] = {
            "style": org_style.value,
            "files_organized": files_organized,
            "subdirectories": len(context.organized_files),
        }

        return StageResult(
            status=StageStatus.SUCCESS,
            message=f"Organized {files_organized} files using {org_style.value} style",
            files_processed=files_organized,
            duration_seconds=duration,
        )

    def _organize_flat(
        self, files: List[Path], output_dir: Path, context: StageContext
    ) -> int:
        """Organize files flat (all in one directory).

        Args:
            files: Files to organize
            output_dir: Output directory
            context: Stage context

        Returns:
            Number of files organized
        """
        import shutil
        count = 0
        for file_path in files:
            dest_path = output_dir / file_path.name
            if not dest_path.exists():
                # If source is a symlink, copy the actual file content
                if file_path.is_symlink():
                    shutil.copy2(file_path.resolve(), dest_path)
                else:
                    file_path.rename(dest_path)
                count += 1
        return count

    def _organize_balanced(
        self, files: List[Path], output_dir: Path, context: StageContext
    ) -> int:
        """Organize files with balanced alphabetical grouping.

        Creates groups like: 0-9, A-E, F-M, N-Z

        Args:
            files: Files to organize
            output_dir: Output directory
            context: Stage context

        Returns:
            Number of files organized
        """
        # Simple balanced grouping
        groups = {
            "#": [],  # Numbers and symbols
            "A-E": [],
            "F-M": [],
            "N-Z": [],
        }

        for file_path in files:
            first_char = file_path.name[0].upper()

            if first_char.isdigit() or not first_char.isalpha():
                groups["#"].append(file_path)
            elif first_char <= "E":
                groups["A-E"].append(file_path)
            elif first_char <= "M":
                groups["F-M"].append(file_path)
            else:
                groups["N-Z"].append(file_path)

        count = 0
        for group_name, group_files in groups.items():
            if not group_files:
                continue

            group_dir = output_dir / group_name
            group_dir.mkdir(parents=True, exist_ok=True)

            for file_path in group_files:
                dest_path = group_dir / file_path.name
                if not dest_path.exists():
                    # If source is a symlink, copy the actual file content
                    if file_path.is_symlink():
                        import shutil
                        shutil.copy2(file_path.resolve(), dest_path)
                    else:
                        file_path.rename(dest_path)
                    count += 1

        self._log(
            context,
            f"  Created {len([g for g in groups.values() if g])} groups",
        )
        return count

    def _organize_minimal(
        self,
        files: List[Path],
        output_dir: Path,
        max_per_group: int,
        context: StageContext,
    ) -> int:
        """Organize files with minimal grouping (sort2folders logic).

        Creates smart groups to keep each group under max_per_group files.

        Args:
            files: Files to organize
            output_dir: Output directory
            max_per_group: Maximum files per group
            context: Stage context

        Returns:
            Number of files organized
        """
        # Sort files alphabetically
        sorted_files = sorted(files, key=lambda f: f.name.upper())

        # Count files by first character
        char_counts = {}
        for file_path in sorted_files:
            first_char = file_path.name[0].upper()
            if not first_char.isalpha():
                first_char = "#"
            char_counts[first_char] = char_counts.get(first_char, 0) + 1

        # Create groups
        groups = {}
        current_group = []
        current_group_name = ""
        current_count = 0

        for file_path in sorted_files:
            first_char = file_path.name[0].upper()
            if not first_char.isalpha():
                first_char = "#"

            # Start new group if needed
            if current_count >= max_per_group or not current_group_name:
                if current_group:
                    groups[current_group_name] = current_group

                current_group = []
                current_group_name = first_char
                current_count = 0

            # Add to current group
            current_group.append(file_path)
            current_count += 1

            # Extend group name if still same starting character
            if not current_group_name.endswith(f"-{first_char}"):
                if current_group_name != first_char:
                    current_group_name = f"{current_group_name}-{first_char}"

        # Add last group
        if current_group:
            groups[current_group_name] = current_group

        # Create directories and move files
        count = 0
        for group_name, group_files in groups.items():
            group_dir = output_dir / group_name
            group_dir.mkdir(parents=True, exist_ok=True)

            for file_path in group_files:
                dest_path = group_dir / file_path.name
                if not dest_path.exists():
                    # If source is a symlink, copy the actual file content
                    if file_path.is_symlink():
                        import shutil
                        shutil.copy2(file_path.resolve(), dest_path)
                    else:
                        file_path.rename(dest_path)
                    count += 1

        self._log(
            context,
            f"  Created {len(groups)} groups (max {max_per_group} files/group)",
        )
        return count

    def _organize_rich(
        self, files: List[Path], output_dir: Path, context: StageContext
    ) -> int:
        """Organize files with rich metadata structure.

        Creates per-letter subdirectories: A/, B/, C/, etc.

        Args:
            files: Files to organize
            output_dir: Output directory
            context: Stage context

        Returns:
            Number of files organized
        """
        import shutil
        count = 0
        for file_path in files:
            first_char = file_path.name[0].upper()
            if not first_char.isalpha():
                first_char = "#"

            letter_dir = output_dir / first_char
            letter_dir.mkdir(parents=True, exist_ok=True)

            dest_path = letter_dir / file_path.name
            if not dest_path.exists():
                # If source is a symlink, copy the actual file content
                if file_path.is_symlink():
                    shutil.copy2(file_path.resolve(), dest_path)
                else:
                    file_path.rename(dest_path)
                count += 1

        return count
