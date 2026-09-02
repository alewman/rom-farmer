"""
DAT file parser for Logiqx XML format.

Parses No-Intro and Redump DAT files to extract game metadata for validation
and collection management.
"""

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DatHeader:
    """DAT file header information."""

    name: str
    description: str
    version: str
    date: str | None = None
    author: str | None = None
    url: str | None = None
    comment: str | None = None

    def __str__(self) -> str:
        return f"{self.name} (v{self.version})"


@dataclass
class DatRelease:
    """Release information for a game."""

    name: str
    region: str
    language: str | None = None
    date: str | None = None
    default: bool = False


@dataclass
class DatRom:
    """ROM file information from DAT."""

    name: str
    size: int
    crc: str | None = None
    md5: str | None = None
    sha1: str | None = None
    sha256: str | None = None
    status: str | None = None  # verified, good, bad, etc.

    def __str__(self) -> str:
        return f"{self.name} (CRC: {self.crc or 'N/A'})"


@dataclass
class DatGame:
    """Game entry from DAT file."""

    name: str
    description: str
    roms: list[DatRom]
    releases: list[DatRelease]
    cloneof: str | None = None
    romof: str | None = None
    sampleof: str | None = None
    category: str | None = None

    @property
    def is_clone(self) -> bool:
        """Check if this is a clone/regional variant."""
        return self.cloneof is not None

    @property
    def is_parent(self) -> bool:
        """Check if this is a parent (not a clone)."""
        return self.cloneof is None

    @property
    def primary_region(self) -> str | None:
        """Get the primary region for this game."""
        if not self.releases:
            return None
        # Return first release region
        return self.releases[0].region

    def __str__(self) -> str:
        clone_info = f" (clone of {self.cloneof})" if self.is_clone else ""
        return f"{self.description}{clone_info}"


class DatParser:
    """
    Parser for Logiqx XML DAT files.

    Parses No-Intro and Redump DAT files to extract game and ROM metadata.

    Examples:
        >>> parser = DatParser()
        >>> dat = parser.parse(Path('/path/to/Nintendo - NES.dat'))
        >>> print(f"DAT: {dat.header}")
        >>> print(f"Games: {len(dat.games)}")
        >>>
        >>> # Iterate through games
        >>> for game in dat.games:
        ...     print(f"Game: {game.description}")
        ...     for rom in game.roms:
        ...         print(f"  ROM: {rom.name} (CRC: {rom.crc})")
    """

    def __init__(self):
        self.header: DatHeader | None = None
        self.games: list[DatGame] = []

    def parse(self, dat_path: Path) -> "DatParser":
        """
        Parse a DAT file.

        Args:
            dat_path: Path to the DAT file

        Returns:
            Self (for chaining)

        Raises:
            FileNotFoundError: If DAT file doesn't exist
            ET.ParseError: If XML is invalid
        """
        if not dat_path.exists():
            raise FileNotFoundError(f"DAT file not found: {dat_path}")

        logger.info(f"Parsing DAT file: {dat_path.name}")

        try:
            tree = ET.parse(dat_path)
            root = tree.getroot()

            # Parse header
            header_elem = root.find("header")
            if header_elem is not None:
                self.header = self._parse_header(header_elem)
                logger.debug(f"Parsed header: {self.header}")

            # Parse games
            self.games = []
            for game_elem in root.findall("game"):
                game = self._parse_game(game_elem)
                if game:
                    self.games.append(game)

            logger.info(f"Parsed {len(self.games)} games from {dat_path.name}")
            return self

        except ET.ParseError as e:
            logger.error(f"Failed to parse DAT file {dat_path}: {e}")
            raise

    def _parse_header(self, header_elem: ET.Element) -> DatHeader:
        """Parse header element."""
        return DatHeader(
            name=self._get_text(header_elem, "name", "Unknown"),
            description=self._get_text(header_elem, "description", ""),
            version=self._get_text(header_elem, "version", ""),
            date=self._get_text(header_elem, "date"),
            author=self._get_text(header_elem, "author"),
            url=self._get_text(header_elem, "url"),
            comment=self._get_text(header_elem, "comment"),
        )

    def _parse_game(self, game_elem: ET.Element) -> DatGame | None:
        """Parse game element."""
        name = game_elem.get("name")
        if not name:
            logger.warning("Game element missing 'name' attribute, skipping")
            return None

        # Parse description
        description = self._get_text(game_elem, "description", name)

        # Parse releases
        releases = []
        for release_elem in game_elem.findall("release"):
            release = self._parse_release(release_elem)
            if release:
                releases.append(release)

        # Parse ROMs
        roms = []
        for rom_elem in game_elem.findall("rom"):
            rom = self._parse_rom(rom_elem)
            if rom:
                roms.append(rom)

        # Parse disc elements (for Redump)
        for disc_elem in game_elem.findall("disc"):
            rom = self._parse_rom(disc_elem)
            if rom:
                roms.append(rom)

        return DatGame(
            name=name,
            description=description,
            roms=roms,
            releases=releases,
            cloneof=game_elem.get("cloneof"),
            romof=game_elem.get("romof"),
            sampleof=game_elem.get("sampleof"),
            category=self._get_text(game_elem, "category"),
        )

    def _parse_release(self, release_elem: ET.Element) -> DatRelease | None:
        """Parse release element."""
        name = release_elem.get("name")
        region = release_elem.get("region")

        if not name or not region:
            return None

        return DatRelease(
            name=name,
            region=region,
            language=release_elem.get("language"),
            date=release_elem.get("date"),
            default=release_elem.get("default") == "yes",
        )

    def _parse_rom(self, rom_elem: ET.Element) -> DatRom | None:
        """Parse ROM element."""
        name = rom_elem.get("name")
        size_str = rom_elem.get("size")

        if not name or not size_str:
            return None

        try:
            size = int(size_str)
        except ValueError:
            logger.warning(f"Invalid size for ROM {name}: {size_str}")
            return None

        return DatRom(
            name=name,
            size=size,
            crc=rom_elem.get("crc"),
            md5=rom_elem.get("md5"),
            sha1=rom_elem.get("sha1"),
            sha256=rom_elem.get("sha256"),
            status=rom_elem.get("status"),
        )

    def _get_text(self, parent: ET.Element, tag: str, default: str | None = None) -> str | None:
        """Get text content of a child element."""
        elem = parent.find(tag)
        if elem is not None and elem.text:
            return elem.text.strip()
        return default

    def get_games_by_region(self, region: str) -> list[DatGame]:
        """
        Get all games for a specific region.

        Args:
            region: Region code (USA, Europe, Japan, etc.)

        Returns:
            List of games with releases in that region
        """
        games = []
        for game in self.games:
            if any(release.region == region for release in game.releases):
                games.append(game)
        return games

    def get_parent_games(self) -> list[DatGame]:
        """Get all parent games (not clones)."""
        return [game for game in self.games if game.is_parent]

    def get_clone_games(self) -> list[DatGame]:
        """Get all clone games."""
        return [game for game in self.games if game.is_clone]

    def find_game_by_name(self, name: str) -> DatGame | None:
        """Find a game by exact name match."""
        for game in self.games:
            if game.name == name:
                return game
        return None

    def find_game_by_crc(self, crc: str) -> DatGame | None:
        """
        Find a game by ROM CRC.

        Args:
            crc: CRC32 checksum (hex string)

        Returns:
            Game containing a ROM with that CRC, or None
        """
        crc_lower = crc.lower()
        for game in self.games:
            for rom in game.roms:
                if rom.crc and rom.crc.lower() == crc_lower:
                    return game
        return None

    def get_statistics(self) -> dict[str, Any]:
        """
        Get statistics about the DAT file.

        Returns:
            Dictionary with various statistics
        """
        regions = set()
        for game in self.games:
            for release in game.releases:
                regions.add(release.region)

        return {
            "total_games": len(self.games),
            "parent_games": len(self.get_parent_games()),
            "clone_games": len(self.get_clone_games()),
            "total_roms": sum(len(game.roms) for game in self.games),
            "regions": sorted(regions),
            "region_count": len(regions),
        }
