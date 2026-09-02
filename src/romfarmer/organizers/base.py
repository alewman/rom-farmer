"""
Base organizer classes and types.

Provides the foundation for ROM organization with support for:
- Physical organization (moving/copying files)
- Virtual organization (creating symlinks)
- Dry-run mode for preview
"""

import logging
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class OrganizeMode(str, Enum):
    """How to organize files."""

    MOVE = "move"  # Move files (physical organization)
    COPY = "copy"  # Copy files (physical organization)
    SYMLINK = "symlink"  # Create symlinks (virtual organization)
    HARDLINK = "hardlink"  # Create hardlinks (zero-cost duplicates on same FS)


# Directories that contain metadata/media, not ROMs.
# Files inside these are always skipped by organizers.
METADATA_DIRS = frozenset(
    {
        "media",
        "images",
        "videos",
        "manuals",
        "thumbnails",
        "screenshots",
        "marquees",
        "boxart",
        "cartridges",
        "mix",
        "titles",
        "downloaded_images",
        "downloaded_videos",
    }
)


@dataclass
class OrganizeStats:
    """Statistics from an organization operation."""

    files_processed: int = 0
    files_moved: int = 0
    files_copied: int = 0
    symlinks_created: int = 0
    directories_created: int = 0
    errors: int = 0
    skipped: int = 0

    def __str__(self) -> str:
        """Return a human-readable summary."""
        lines = [
            f"Files processed: {self.files_processed}",
            f"Files moved: {self.files_moved}",
            f"Files copied: {self.files_copied}",
            f"Symlinks created: {self.symlinks_created}",
            f"Directories created: {self.directories_created}",
            f"Files skipped: {self.skipped}",
            f"Errors: {self.errors}",
        ]
        return "\n".join(lines)


class BaseOrganizer(ABC):
    """
    Base class for ROM organizers.

    Provides common functionality for organizing ROMs by different criteria
    (region, kind, language, etc.).

    Args:
        mode: How to organize files (move, copy, or symlink)
        dry_run: Preview changes without actually making them
        keep_in_place: List of values to keep in root (not organize)
        exclude_values: List of values to exclude from organization
    """

    def __init__(
        self,
        mode: OrganizeMode = OrganizeMode.MOVE,
        dry_run: bool = False,
        keep_in_place: list[str] | None = None,
        exclude_values: list[str] | None = None,
    ):
        self.mode = mode
        self.dry_run = dry_run
        self.keep_in_place = set(keep_in_place or [])
        self.exclude_values = set(exclude_values or [])
        self.stats = OrganizeStats()

    @abstractmethod
    def get_organization_value(self, filename: str) -> str | None:
        """
        Extract the organization value from a filename.

        For example:
        - RegionOrganizer extracts region: "Super Mario (USA).nes" -> "USA"
        - KindOrganizer extracts kind: "Demo (Demo).nes" -> "Demo"
        - LanguageOrganizer extracts language: "Game (En).nes" -> "En"

        Args:
            filename: The ROM filename

        Returns:
            The organization value, or None if not detected
        """
        pass

    @abstractmethod
    def get_organization_dir_name(self) -> str:
        """
        Get the directory name for this organization type.

        Returns:
            Directory name (e.g., "By Region", "By Kind", "By Language")
        """
        pass

    def should_organize(self, value: str) -> bool:
        """
        Check if a value should be organized.

        Args:
            value: The value to check

        Returns:
            True if the value should be organized, False if kept in place
        """
        # Excluded values are never organized
        if value in self.exclude_values:
            logger.debug(f"Skipping '{value}' (excluded)")
            return False

        # Values in keep_in_place stay in root
        if value in self.keep_in_place:
            logger.debug(f"Keeping '{value}' in place")
            return False

        return True

    def create_directory(self, path: Path) -> bool:
        """
        Create a directory if it doesn't exist.

        Args:
            path: Directory path to create

        Returns:
            True if directory was created, False if it already existed
        """
        if path.exists():
            return False

        if self.dry_run:
            logger.info(f"Would create directory: {path}")
            return True

        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {path}")
        self.stats.directories_created += 1
        return True

    def move_file(self, source: Path, dest_dir: Path) -> bool:
        """
        Move a file to a destination directory.

        Args:
            source: Source file path
            dest_dir: Destination directory

        Returns:
            True if successful, False otherwise
        """
        dest_file = dest_dir / source.name

        if dest_file.exists():
            logger.debug(f"Skipping {source.name} (already exists)")
            self.stats.skipped += 1
            return False

        if self.dry_run:
            logger.debug(f"Would move: {source} -> {dest_file}")
            return True

        try:
            # Create destination directory
            self.create_directory(dest_dir)

            # Move the file
            shutil.move(str(source), str(dest_file))
            logger.debug(f"Moved: {source.name} -> {dest_dir.name}/")
            self.stats.files_moved += 1
            return True

        except Exception as e:
            logger.error(f"Failed to move {source}: {e}")
            self.stats.errors += 1
            return False

    def copy_file(self, source: Path, dest_dir: Path) -> bool:
        """
        Copy a file to a destination directory.

        Args:
            source: Source file path
            dest_dir: Destination directory

        Returns:
            True if successful, False otherwise
        """
        dest_file = dest_dir / source.name

        if dest_file.exists():
            logger.debug(f"Skipping {source.name} (already exists)")
            self.stats.skipped += 1
            return False

        if self.dry_run:
            logger.debug(f"Would copy: {source} -> {dest_file}")
            return True

        try:
            # Create destination directory
            self.create_directory(dest_dir)

            # Copy the file
            shutil.copy2(str(source), str(dest_file))
            logger.debug(f"Copied: {source.name} -> {dest_dir.name}/")
            self.stats.files_copied += 1
            return True

        except Exception as e:
            logger.error(f"Failed to copy {source}: {e}")
            self.stats.errors += 1
            return False

    def create_symlink(self, source: Path, dest_dir: Path) -> bool:
        """
        Create a symlink in the destination directory.

        Args:
            source: Source file path
            dest_dir: Destination directory for symlink

        Returns:
            True if successful, False otherwise
        """
        dest_link = dest_dir / source.name

        if dest_link.exists():
            logger.debug(f"Skipping {source.name} (already exists)")
            self.stats.skipped += 1
            return False

        # Calculate relative path from symlink to source
        try:
            relative_path = source.resolve().relative_to(dest_dir.resolve())
        except ValueError:
            # Can't make relative path, use absolute
            relative_path = source.resolve()

        if self.dry_run:
            logger.debug(f"Would create symlink: {dest_link} -> {relative_path}")
            return True

        try:
            # Create destination directory
            self.create_directory(dest_dir)

            # Create symlink
            dest_link.symlink_to(relative_path)
            logger.debug(f"Created symlink: {dest_dir.name}/{source.name} -> {relative_path}")
            self.stats.symlinks_created += 1
            return True

        except Exception as e:
            logger.error(f"Failed to create symlink for {source}: {e}")
            self.stats.errors += 1
            return False

    def hardlink_file(self, source: Path, dest_dir: Path) -> bool:
        """
        Create a hardlink in the destination directory.

        Hardlinks are zero-cost on the same filesystem — the file appears
        in multiple places but uses no additional disk space. Ideal for
        organizing ROMs into multiple views (by region, language, etc.)
        without duplicating data.

        Args:
            source: Source file path
            dest_dir: Destination directory

        Returns:
            True if successful, False otherwise
        """
        import os

        dest_file = dest_dir / source.name

        if dest_file.exists():
            logger.debug(f"Skipping {source.name} (already exists)")
            self.stats.skipped += 1
            return False

        if self.dry_run:
            logger.debug(f"Would hardlink: {source} -> {dest_file}")
            return True

        try:
            self.create_directory(dest_dir)
            os.link(source, dest_file)
            logger.debug(f"Hardlinked: {source.name} -> {dest_dir.name}/")
            self.stats.files_copied += 1  # Count as copy in stats (file in two places)
            return True
        except OSError as e:
            logger.error(f"Failed to hardlink {source} (cross-filesystem?): {e}")
            self.stats.errors += 1
            return False

    def organize_file(self, source: Path, dest_dir: Path) -> bool:
        """
        Organize a file (or directory) based on the configured mode.

        Directories cannot be hardlinked; when the source is a directory
        a symlink is always created regardless of the configured mode.

        Args:
            source: Source file or directory path
            dest_dir: Destination directory

        Returns:
            True if successful, False otherwise
        """
        # Directories can't be hardlinked or copied atomically — use symlinks
        if source.is_dir():
            return self.create_symlink(source, dest_dir)

        if self.mode == OrganizeMode.MOVE:
            return self.move_file(source, dest_dir)
        elif self.mode == OrganizeMode.COPY:
            return self.copy_file(source, dest_dir)
        elif self.mode == OrganizeMode.SYMLINK:
            return self.create_symlink(source, dest_dir)
        elif self.mode == OrganizeMode.HARDLINK:
            return self.hardlink_file(source, dest_dir)
        else:
            logger.error(f"Unknown organize mode: {self.mode}")
            return False

    def _collect_rom_files(
        self,
        source_dir: Path,
        org_dir_name: str,
        recursive: bool = False,
        extensions: list[str] | None = None,
    ) -> list[Path]:
        """
        Collect ROM files eligible for organization.

        Skips:
        - Non-file entries (directories)
        - Files inside the target organization folder (e.g., ``By Genre/``)
        - Files inside any other known organization folder (``By Kind/``, etc.)
        - Files inside metadata/media directories (``media/``, ``images/``, etc.)
        - Files inside any existing subdirectory when ``recursive=False`` (default)

        The default ``recursive=False`` means only root-level files are
        processed.  Curated subdirectories like ``Best Games/`` or
        ``English Translations/`` are left untouched.
        """
        # All known organization directory names
        org_dir_names = {
            "By Genre",
            "By Kind",
            "By Language",
            "By Region",
            "By Letter",
            org_dir_name,
        }

        if recursive:
            files = list(source_dir.glob("**/*"))
        else:
            files = list(source_dir.glob("*"))

        # Normalize extensions
        if extensions:
            extensions = [
                ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in extensions
            ]
            files = [f for f in files if f.suffix.lower() in extensions]

        # Filter: files only, skip metadata and organization dirs
        result = []
        for f in files:
            if not f.is_file():
                continue

            # Get the path parts relative to source_dir
            try:
                rel = f.relative_to(source_dir)
            except ValueError:
                continue

            # Skip files inside organization directories
            if org_dir_names & set(rel.parts):
                continue

            # Skip files inside metadata/media directories
            if METADATA_DIRS & {p.lower() for p in rel.parts}:
                continue

            result.append(f)

        return result

    def _collect_rom_dirs(
        self,
        source_dir: Path,
        org_dir_name: str,
    ) -> list[Path]:
        """
        Collect root-level ROM directories eligible for organization.

        Used for directory-based ROM formats (e.g., PS3 JB folders with
        ``.ps3`` suffix, PS2 ISO folders, etc.) where each game is a
        directory rather than a single file.

        Skips organization directories (``By Genre/`` etc.), metadata
        directories, and any directory without a file-extension suffix
        (those are assumed to be curated subdirs, not ROM containers).
        """
        org_dir_names = {
            "By Genre",
            "By Kind",
            "By Language",
            "By Region",
            "By Letter",
            org_dir_name,
        }

        result = []
        for entry in source_dir.iterdir():
            if not entry.is_dir():
                continue

            name = entry.name

            # Skip organization and metadata directories
            if name in org_dir_names:
                continue
            if name.lower() in METADATA_DIRS:
                continue

            # Only treat directories with a suffix as ROM containers
            # (e.g. "007 - Blood Stone.ps3") — bare dirs are curated subdirs
            if not entry.suffix:
                continue

            result.append(entry)

        return result

    def organize(
        self,
        source_dir: Path,
        dest_dir: Path | None = None,
        recursive: bool = False,
        extensions: list[str] | None = None,
    ) -> OrganizeStats:
        """
        Organize ROMs in a directory.

        Args:
            source_dir: Directory containing ROMs to organize
            dest_dir: Base destination directory (defaults to source_dir)
            recursive: Whether to process subdirectories (default False —
                       only root-level files are organized; curated subdirs
                       like Best Games/ are left alone)
            extensions: File extensions to process (e.g., ['.nes', '.sfc'])
                       If None, processes all files

        Returns:
            OrganizeStats object with operation statistics
        """
        if dest_dir is None:
            dest_dir = source_dir

        # Reset stats
        self.stats = OrganizeStats()

        logger.info(f"Starting {self.__class__.__name__}")
        logger.info(f"Source: {source_dir}")
        logger.info(f"Mode: {self.mode.value}")
        logger.info(f"Dry run: {self.dry_run}")

        # Get organization directory name
        org_dir_name = self.get_organization_dir_name()

        # Collect eligible ROM files
        files = self._collect_rom_files(source_dir, org_dir_name, recursive, extensions)

        logger.info(f"Found {len(files)} file(s) to process")

        # Process each file
        for file_path in files:
            self.stats.files_processed += 1

            # Get organization value from filename
            value = self.get_organization_value(file_path.name)

            if value is None:
                logger.debug(f"No {org_dir_name} value detected: {file_path.name}")
                continue

            # Check if should organize this value
            if not self.should_organize(value):
                continue

            # Build destination path
            target_dir = dest_dir / org_dir_name / value

            # Organize the file
            self.organize_file(file_path, target_dir)

        logger.info(f"Organization complete: {self.stats}")
        return self.stats
