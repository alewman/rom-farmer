"""
DAT import service.

Handles importing DAT files into the database for efficient querying
and ROM validation.
"""

import logging
from datetime import datetime
from pathlib import Path

from ..catalog.database import DatFile, DatGame, RomGroomerDatabase
from ..dat import DatParser

logger = logging.getLogger(__name__)


class DatImportService:
    """
    Service for importing DAT files into the database.

    Provides high-level interface for:
    - Parsing DAT files
    - Storing in database
    - Updating existing DATs
    - Querying imported data

    Example:
        >>> service = DatImportService(db)
        >>> stats = service.import_dat(Path('/path/to/Nintendo - NES.dat'))
        >>> print(f"Imported {stats['games_imported']} games")
    """

    def __init__(self, database: RomGroomerDatabase):
        """
        Initialize import service.

        Args:
            database: Database instance
        """
        self.db = database

    def import_dat(
        self,
        dat_path: Path,
        update_existing: bool = True,
    ) -> dict:
        """
        Import a DAT file into the database.

        Args:
            dat_path: Path to DAT file
            update_existing: If True, update existing DAT; if False, skip

        Returns:
            Dictionary with import statistics
        """
        logger.info(f"Importing DAT file: {dat_path.name}")

        # Parse DAT file
        parser = DatParser()
        parser.parse(dat_path)

        if not parser.header:
            raise ValueError(f"DAT file has no header: {dat_path}")

        session = self.db.get_session()
        try:
            # Check if DAT already exists
            existing_dat = self.db.get_dat_file(session, parser.header.name)

            if existing_dat and not update_existing:
                logger.info(f"DAT already exists and update_existing=False: {parser.header.name}")
                return {
                    "dat_name": parser.header.name,
                    "already_exists": True,
                    "games_imported": 0,
                    "games_updated": 0,
                    "games_skipped": len(parser.games),
                }

            # Create or update DAT file record
            if existing_dat:
                logger.info(f"Updating existing DAT: {parser.header.name}")
                dat_file = existing_dat
                dat_file.description = parser.header.description
                dat_file.version = parser.header.version
                dat_file.author = parser.header.author
                dat_file.date = parser.header.date
                dat_file.updated_at = datetime.utcnow()

                # Delete existing games (will re-import)
                session.query(DatGame).filter_by(dat_file_id=dat_file.id).delete()
                session.flush()
            else:
                logger.info(f"Creating new DAT: {parser.header.name}")
                dat_file = DatFile(
                    name=parser.header.name,
                    description=parser.header.description,
                    version=parser.header.version,
                    author=parser.header.author,
                    date=parser.header.date,
                )
                session.add(dat_file)
                session.flush()  # Get ID

            # Import games
            games_imported = 0
            total_size = 0

            for parsed_game in parser.games:
                # Each game may have multiple ROMs (multi-disc, etc.)
                for rom in parsed_game.roms:
                    dat_game = DatGame(
                        dat_file_id=dat_file.id,
                        name=parsed_game.name,
                        description=parsed_game.description,
                        category=parsed_game.category,
                        rom_name=rom.name,
                        size=rom.size,
                        crc=rom.crc.lower() if rom.crc else None,
                        md5=rom.md5.lower() if rom.md5 else None,
                        sha1=rom.sha1.lower() if rom.sha1 else None,
                    )
                    session.add(dat_game)
                    games_imported += 1
                    total_size += rom.size

            # Update statistics
            dat_file.total_games = games_imported
            dat_file.total_size = total_size

            session.commit()

            logger.info(f"Successfully imported {games_imported} games from {dat_path.name}")

            return {
                "dat_name": parser.header.name,
                "dat_version": parser.header.version,
                "games_imported": games_imported,
                "total_size": total_size,
                "already_exists": existing_dat is not None,
            }

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to import DAT {dat_path}: {e}")
            raise
        finally:
            session.close()

    def import_dats(
        self,
        dat_paths: list[Path],
        update_existing: bool = True,
    ) -> list[dict]:
        """
        Import multiple DAT files.

        Args:
            dat_paths: List of DAT file paths
            update_existing: If True, update existing DATs

        Returns:
            List of import statistics for each DAT
        """
        results = []

        for dat_path in dat_paths:
            try:
                stats = self.import_dat(dat_path, update_existing=update_existing)
                results.append(stats)
            except Exception as e:
                logger.error(f"Failed to import {dat_path}: {e}")
                results.append(
                    {
                        "dat_name": dat_path.name,
                        "error": str(e),
                    }
                )

        return results

    def list_imported_dats(self) -> list[DatFile]:
        """
        List all imported DAT files.

        Returns:
            List of DatFile records
        """
        session = self.db.get_session()
        try:
            return self.db.list_dat_files(session)
        finally:
            session.close()

    def get_dat_info(self, dat_name: str) -> DatFile | None:
        """
        Get information about an imported DAT.

        Args:
            dat_name: Name of the DAT file

        Returns:
            DatFile record, or None if not found
        """
        session = self.db.get_session()
        try:
            return self.db.get_dat_file(session, dat_name)
        finally:
            session.close()

    def get_dat_games(
        self,
        dat_name: str,
        limit: int | None = None,
    ) -> list[DatGame]:
        """
        Get games from an imported DAT.

        Args:
            dat_name: Name of the DAT file
            limit: Optional limit on number of results

        Returns:
            List of DatGame records
        """
        session = self.db.get_session()
        try:
            dat_file = self.db.get_dat_file(session, dat_name)
            if not dat_file:
                return []

            return self.db.get_dat_games(session, dat_file.id, limit=limit)
        finally:
            session.close()

    def find_game_by_crc(
        self,
        crc: str,
        dat_name: str | None = None,
    ) -> DatGame | None:
        """
        Find a game by ROM CRC.

        Args:
            crc: CRC32 checksum (hex string)
            dat_name: Optional DAT name to search within

        Returns:
            First matching DatGame, or None
        """
        session = self.db.get_session()
        try:
            dat_file_id = None
            if dat_name:
                dat_file = self.db.get_dat_file(session, dat_name)
                if dat_file:
                    dat_file_id = dat_file.id

            return self.db.find_game_by_crc(session, crc, dat_file_id=dat_file_id)
        finally:
            session.close()

    def find_games_by_name(
        self,
        name: str,
        dat_name: str | None = None,
    ) -> list[DatGame]:
        """
        Find games by name (partial match).

        Args:
            name: Game name to search for
            dat_name: Optional DAT name to search within

        Returns:
            List of matching DatGame records
        """
        session = self.db.get_session()
        try:
            dat_file_id = None
            if dat_name:
                dat_file = self.db.get_dat_file(session, dat_name)
                if dat_file:
                    dat_file_id = dat_file.id

            return self.db.find_games_by_name(session, name, dat_file_id=dat_file_id)
        finally:
            session.close()

    def delete_dat(self, dat_name: str) -> bool:
        """
        Delete an imported DAT and all its games.

        Args:
            dat_name: Name of the DAT file

        Returns:
            True if deleted, False if not found
        """
        session = self.db.get_session()
        try:
            dat_file = self.db.get_dat_file(session, dat_name)
            if not dat_file:
                return False

            logger.info(f"Deleting DAT: {dat_name}")
            session.delete(dat_file)
            session.commit()
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete DAT {dat_name}: {e}")
            raise
        finally:
            session.close()

    def get_statistics(self, dat_name: str | None = None) -> dict:
        """
        Get statistics about imported DAT(s).

        Args:
            dat_name: Optional DAT name for specific stats

        Returns:
            Dictionary with statistics
        """
        session = self.db.get_session()
        try:
            if dat_name:
                # Stats for specific DAT
                dat_file = self.db.get_dat_file(session, dat_name)
                if not dat_file:
                    return {}

                return {
                    "dat_name": dat_file.name,
                    "version": dat_file.version,
                    "total_games": dat_file.total_games,
                    "total_size": dat_file.total_size,
                    "imported_at": dat_file.imported_at,
                    "updated_at": dat_file.updated_at,
                }
            else:
                # Overall stats
                total_dats = session.query(DatFile).count()
                total_games = session.query(DatGame).count()

                return {
                    "total_dats": total_dats,
                    "total_games": total_games,
                }
        finally:
            session.close()
