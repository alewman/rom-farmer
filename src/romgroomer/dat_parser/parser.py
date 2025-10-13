"""XML DAT file parsers."""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from .models import DATFile, DATGame, DATRom, DATType, ROMStatus


class DATParser:
    """Parser for Logiqx XML DAT files (No-Intro/Redump standard format)."""

    def __init__(self):
        """Initialize parser."""
        self.dat_type = DATType.NOINTRO

    def parse(self, dat_file: Path) -> DATFile:
        """Parse DAT file.

        Args:
            dat_file: Path to DAT XML file

        Returns:
            Parsed DATFile object

        Raises:
            FileNotFoundError: If DAT file doesn't exist
            ET.ParseError: If XML is malformed
        """
        if not dat_file.exists():
            raise FileNotFoundError(f"DAT file not found: {dat_file}")

        tree = ET.parse(dat_file)
        root = tree.getroot()

        # Parse header
        header = root.find("header")
        dat_name = header.findtext("name", "") if header is not None else ""
        dat_description = header.findtext("description") if header is not None else None
        dat_version = header.findtext("version") if header is not None else None
        dat_author = header.findtext("author") if header is not None else None

        # Detect DAT type from filename or content
        dat_type = self._detect_dat_type(dat_file, dat_name)

        # Parse games
        games = []
        for game_elem in root.findall("game"):
            game = self._parse_game(game_elem)
            if game:
                games.append(game)

        return DATFile(
            name=dat_name,
            description=dat_description,
            version=dat_version,
            author=dat_author,
            dat_type=dat_type,
            games=games,
            source_file=dat_file,
        )

    def _detect_dat_type(self, dat_file: Path, dat_name: str) -> DATType:
        """Detect DAT type from filename or name."""
        filename_lower = dat_file.name.lower()
        name_lower = dat_name.lower()

        if "retool" in filename_lower or "retool" in name_lower:
            return DATType.RETOOL
        elif "redump" in filename_lower or "redump" in name_lower:
            return DATType.REDUMP
        elif "no-intro" in filename_lower or "nointro" in name_lower:
            return DATType.NOINTRO
        else:
            return DATType.CUSTOM

    def _parse_game(self, game_elem: ET.Element) -> Optional[DATGame]:
        """Parse game element.

        Args:
            game_elem: XML game element

        Returns:
            DATGame object or None if invalid
        """
        game_name = game_elem.get("name")
        if not game_name:
            return None

        # Parse optional attributes
        cloneof = game_elem.get("cloneof")

        # Parse nested elements
        description = game_elem.findtext("description", game_name)
        category = game_elem.findtext("category")  # Retool-specific
        year = game_elem.findtext("year")
        manufacturer = game_elem.findtext("manufacturer")

        # Parse ROMs
        roms = []
        for rom_elem in game_elem.findall("rom"):
            rom = self._parse_rom(rom_elem)
            if rom:
                roms.append(rom)

        return DATGame(
            name=game_name,
            roms=roms,
            description=description,
            category=category,
            cloneof=cloneof,
            year=year,
            manufacturer=manufacturer,
        )

    def _parse_rom(self, rom_elem: ET.Element) -> Optional[DATRom]:
        """Parse ROM element.

        Args:
            rom_elem: XML rom element

        Returns:
            DATRom object or None if invalid
        """
        rom_name = rom_elem.get("name")
        size_str = rom_elem.get("size")

        if not rom_name or not size_str:
            return None

        try:
            size = int(size_str)
        except ValueError:
            return None

        # Parse optional hashes
        crc = rom_elem.get("crc")
        md5 = rom_elem.get("md5")
        sha1 = rom_elem.get("sha1")
        sha256 = rom_elem.get("sha256")

        # Parse status
        status_str = rom_elem.get("status", "good")
        try:
            status = ROMStatus(status_str.lower())
        except ValueError:
            status = ROMStatus.GOOD

        return DATRom(
            name=rom_name,
            size=size,
            crc=crc,
            md5=md5,
            sha1=sha1,
            sha256=sha256,
            status=status,
        )


class RetoolDATParser(DATParser):
    """Parser for Retool-enhanced DAT files.

    Retool DATs are Logiqx XML with additional features:
    - <category> tag for game categorization
    - Pre-filtered (1G1R + language + best versions applied)
    - Bad dumps removed
    - Some pirate/aftermarket ROMs included if they have unique content
    """

    def __init__(self):
        """Initialize Retool parser."""
        super().__init__()
        self.dat_type = DATType.RETOOL

    def _detect_dat_type(self, dat_file: Path, dat_name: str) -> DATType:
        """Always return RETOOL for RetoolDATParser."""
        return DATType.RETOOL
