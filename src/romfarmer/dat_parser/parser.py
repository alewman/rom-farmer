"""XML DAT file parsers."""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from .models import DATDisk, DATFile, DATGame, DATRom, DATType, ROMStatus


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

        # Parse games (both <game> and <machine> elements for MAME compatibility)
        games = []
        for game_elem in root.findall("game"):
            game = self._parse_game(game_elem)
            if game:
                games.append(game)
        for game_elem in root.findall("machine"):
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
        elif "fbneo" in filename_lower or "finalburn" in name_lower:
            return DATType.FBNEO
        elif "hbmame" in filename_lower or "hbmame" in name_lower:
            return DATType.HBMAME
        elif "mame" in filename_lower or "mame" in name_lower:
            return DATType.MAME
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
        romof = game_elem.get("romof")  # Arcade: parent ROM reference
        sourcefile = game_elem.get("sourcefile")  # Arcade: driver source
        is_bios = game_elem.get("isbios") == "yes"
        is_device = game_elem.get("isdevice") == "yes"

        # Parse nested elements
        description = game_elem.findtext("description", game_name)
        category = game_elem.findtext("category")  # Retool-specific
        year = game_elem.findtext("year")
        manufacturer = game_elem.findtext("manufacturer")
        comment = game_elem.findtext("comment")  # Arcade: Bootleg, Hack, etc.

        # Parse driver status (arcade)
        driver_elem = game_elem.find("driver")
        driver_status = driver_elem.get("status") if driver_elem is not None else None

        # Parse ROMs
        roms = []
        for rom_elem in game_elem.findall("rom"):
            rom = self._parse_rom(rom_elem)
            if rom:
                roms.append(rom)

        # Parse disks/CHDs (MAME/FBNeo)
        disks = []
        for disk_elem in game_elem.findall("disk"):
            disk = self._parse_disk(disk_elem)
            if disk:
                disks.append(disk)

        return DATGame(
            name=game_name,
            roms=roms,
            disks=disks,
            description=description,
            category=category,
            cloneof=cloneof,
            romof=romof,
            year=year,
            manufacturer=manufacturer,
            comment=comment,
            driver_status=driver_status,
            sourcefile=sourcefile,
            is_bios=is_bios,
            is_device=is_device,
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

    def _parse_disk(self, disk_elem: ET.Element) -> Optional[DATDisk]:
        """Parse disk/CHD element.

        Args:
            disk_elem: XML disk element

        Returns:
            DATDisk object or None if invalid
        """
        disk_name = disk_elem.get("name")
        if not disk_name:
            return None

        # Parse optional attributes
        sha1 = disk_elem.get("sha1")
        md5 = disk_elem.get("md5")
        region = disk_elem.get("region")  # e.g., "cdrom", "gdrom", "ide:0:hdd"
        status = disk_elem.get("status", "good")
        merge = disk_elem.get("merge")  # Parent disk for clones

        return DATDisk(
            name=disk_name,
            sha1=sha1,
            md5=md5,
            region=region,
            status=status,
            merge=merge,
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
