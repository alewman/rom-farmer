"""
Genre-based ROM organizer.

Organizes ROMs by genre (Action, RPG, Sports, etc.) using metadata from the
ScreenScraper/ARRM database. Unlike other organizers that parse filenames,
this one queries the metadata DB to look up genre information.
"""

import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Set

from .base import BaseOrganizer, OrganizeMode, OrganizeStats

logger = logging.getLogger(__name__)

# Top-level genre normalization: map raw ScreenScraper genre prefixes
# to clean folder names. Handles the "/" sub-genres by extracting the
# primary category, then normalizes naming.
GENRE_ALIASES: Dict[str, str] = {
    "Action Rpg": "Action RPG",
    "Beat'em Up": "Beat-em-Up",
    "Shoot'em Up": "Shoot-em-Up",
    "Role Playing Game": "RPG",
    "Music And Dancing": "Music",
    "Asiatic Board Game": "Board Game",
    "Lightgun Shooter": "Shooter",
    "Playing Cards": "Card Game",
    "Casino": "Casino",
    "Casual Game": "Casual",
    "Various": "Other",
}


def _normalize_genre(raw_genre: str) -> str:
    """
    Extract a clean top-level genre from a raw ScreenScraper genre string.

    ScreenScraper genres look like:
        "Action / Adventure, Beat'em Up, Action"
        "Platform / Fighter Scrolling, Platform"
        "Racing"

    Strategy: take the first entry (before comma), then the top-level
    category (before /), strip whitespace, and apply alias normalization.
    """
    # Take first genre before comma
    primary = raw_genre.split(",")[0].strip()
    # Take top-level before /
    top = primary.split("/")[0].strip()
    # Apply aliases
    return GENRE_ALIASES.get(top, top)


class GenreOrganizer(BaseOrganizer):
    """
    Organize ROMs by genre using metadata DB lookups.

    Queries the ScreenScraper/ARRM metadata database to find genre info
    for each ROM, then organizes into genre-specific directories.

    The genre is determined by matching ROM filenames (stems) against
    the ``scraped_games`` table. The raw multi-part genre string from
    ScreenScraper is normalized to a clean top-level category.

    Examples:
        >>> organizer = GenreOrganizer(
        ...     metadata_db=Path("metadata/database/romfarmer.db"),
        ...     system="nes",
        ...     mode=OrganizeMode.HARDLINK,
        ... )
        >>> stats = organizer.organize(Path("/roms/nes"))

        # Results in:
        # /roms/nes/By Genre/Action/Contra (USA).nes
        # /roms/nes/By Genre/RPG/Final Fantasy (USA).nes
        # /roms/nes/By Genre/Platformer/Super Mario Bros (USA).nes

    Args:
        metadata_db: Path to the romfarmer.db SQLite database
        system: Platform/system name for DB lookups (e.g., "nes", "snes")
        mode: How to organize files (move, copy, symlink, or hardlink)
        dry_run: Preview changes without actually making them
        keep_in_place: Genres to keep in root directory
        exclude_genres: Genres to exclude from organization
        merge_small: Merge genres with fewer than this many games into "Other"
    """

    def __init__(
        self,
        metadata_db: Path,
        system: str,
        mode: OrganizeMode = OrganizeMode.MOVE,
        dry_run: bool = False,
        keep_in_place: Optional[List[str]] = None,
        exclude_genres: Optional[List[str]] = None,
        merge_small: int = 0,
    ):
        super().__init__(
            mode=mode,
            dry_run=dry_run,
            keep_in_place=keep_in_place,
            exclude_values=exclude_genres,
        )
        self.metadata_db = metadata_db
        self.system = system
        self.merge_small = merge_small

        # Built during organize() — maps filename stem → normalized genre
        self._genre_lookup: Dict[str, str] = {}

    def get_organization_dir_name(self) -> str:
        return "By Genre"

    def get_organization_value(self, filename: str) -> Optional[str]:
        """Look up genre for a filename from the pre-built lookup table."""
        stem = Path(filename).stem
        return self._genre_lookup.get(stem)

    def _build_genre_lookup(self, file_stems: Set[str]) -> None:
        """
        Query the metadata DB and build a stem → genre mapping.

        Uses raw SQLite for a single bulk query rather than loading
        the full ORM — avoids importing the entire metadata stack
        and is much faster for large sets.
        """
        if not self.metadata_db.exists():
            logger.warning(f"Metadata DB not found: {self.metadata_db}")
            return

        conn = sqlite3.connect(str(self.metadata_db))
        try:
            cursor = conn.execute(
                "SELECT filename, genre FROM scraped_games "
                "WHERE system = ? AND genre IS NOT NULL",
                (self.system,),
            )

            for db_filename, raw_genre in cursor:
                if not db_filename or not raw_genre:
                    continue
                db_stem = Path(db_filename).stem
                if db_stem in file_stems:
                    self._genre_lookup[db_stem] = _normalize_genre(raw_genre)

            logger.info(
                f"Genre lookup: {len(self._genre_lookup)}/{len(file_stems)} "
                f"files matched in DB for system '{self.system}'"
            )
        finally:
            conn.close()

        # Optionally merge small genres into "Other"
        if self.merge_small > 0:
            self._merge_small_genres()

    def _merge_small_genres(self) -> None:
        """Merge genres with few entries into 'Other'."""
        from collections import Counter

        counts = Counter(self._genre_lookup.values())
        small_genres = {g for g, c in counts.items() if c < self.merge_small}

        if small_genres:
            merged = 0
            for stem, genre in self._genre_lookup.items():
                if genre in small_genres:
                    self._genre_lookup[stem] = "Other"
                    merged += 1
            logger.info(
                f"Merged {len(small_genres)} small genres "
                f"({merged} files) into 'Other'"
            )

    def organize(
        self,
        source_dir: Path,
        dest_dir: Optional[Path] = None,
        recursive: bool = False,
        extensions: Optional[List[str]] = None,
    ) -> OrganizeStats:
        """
        Organize ROMs by genre.

        Overrides the base to build the genre lookup table before
        processing files. Uses _collect_rom_files() for consistent
        filtering (skips media/, curated subdirs, etc.).
        """
        if dest_dir is None:
            dest_dir = source_dir

        # Reset stats
        self.stats = OrganizeStats()

        logger.info(f"Starting GenreOrganizer for system '{self.system}'")
        logger.info(f"Source: {source_dir}")
        logger.info(f"Mode: {self.mode.value}")

        org_dir_name = self.get_organization_dir_name()

        # Collect eligible ROM files (skips media/, org dirs, curated subdirs)
        files = self._collect_rom_files(source_dir, org_dir_name, recursive, extensions)

        # Also collect root-level ROM directories (e.g. PS3 JB .ps3 folders).
        # These are directory-based game containers where each dir IS the ROM.
        # We always check for both; genre org handles each type appropriately
        # (hardlinks for files, symlinks for dirs since dirs can't be hardlinked).
        dirs = self._collect_rom_dirs(source_dir, org_dir_name)

        entries: List[Path] = files + dirs
        logger.info(
            f"Found {len(files)} file(s) and {len(dirs)} dir(s) to process"
        )

        # Build the genre lookup from DB
        entry_stems = {f.stem for f in entries}
        self._build_genre_lookup(entry_stems)

        if not self._genre_lookup:
            logger.warning("No genre data found — nothing to organize")
            return self.stats

        # Process each entry (organize_file handles dirs via symlink)
        for entry_path in entries:
            self.stats.files_processed += 1

            value = self.get_organization_value(entry_path.name)
            if value is None:
                continue

            if not self.should_organize(value):
                continue

            target_dir = dest_dir / org_dir_name / value
            self.organize_file(entry_path, target_dir)

        logger.info(f"Genre organization complete: {self.stats}")
        return self.stats
