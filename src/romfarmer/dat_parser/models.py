"""Data models for DAT files."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class ROMStatus(str, Enum):
    """ROM status in DAT."""

    GOOD = "good"
    BAD = "bad"
    VERIFIED = "verified"
    UNVERIFIED = "unverified"


class DATType(str, Enum):
    """Type of DAT file."""

    NOINTRO = "nointro"
    REDUMP = "redump"
    RETOOL = "retool"
    CUSTOM = "custom"


@dataclass
class DATRom:
    """ROM entry in DAT file."""

    name: str
    size: int
    crc: Optional[str] = None
    md5: Optional[str] = None
    sha1: Optional[str] = None
    sha256: Optional[str] = None
    status: ROMStatus = ROMStatus.GOOD

    def __post_init__(self):
        """Normalize hashes to lowercase."""
        if self.crc:
            self.crc = self.crc.lower()
        if self.md5:
            self.md5 = self.md5.lower()
        if self.sha1:
            self.sha1 = self.sha1.lower()
        if self.sha256:
            self.sha256 = self.sha256.lower()


@dataclass
class DATGame:
    """Game entry in DAT file."""

    name: str
    roms: list[DATRom] = field(default_factory=list)
    description: Optional[str] = None
    category: Optional[str] = None  # Retool-specific
    cloneof: Optional[str] = None
    year: Optional[str] = None
    manufacturer: Optional[str] = None
    region: Optional[str] = None

    def get_primary_rom(self) -> Optional[DATRom]:
        """Get primary ROM (first ROM, or only ROM)."""
        return self.roms[0] if self.roms else None

    def is_multi_disc(self) -> bool:
        """Check if game has multiple discs."""
        return len(self.roms) > 1

    def get_total_size(self) -> int:
        """Get total size of all ROMs."""
        return sum(rom.size for rom in self.roms)


@dataclass
class DATFile:
    """Parsed DAT file."""

    name: str
    description: Optional[str] = None
    version: Optional[str] = None
    author: Optional[str] = None
    dat_type: DATType = DATType.NOINTRO
    games: list[DATGame] = field(default_factory=list)
    source_file: Optional[Path] = None

    def get_game_count(self) -> int:
        """Get total number of games."""
        return len(self.games)

    def get_rom_count(self) -> int:
        """Get total number of ROMs (multi-disc games count as multiple)."""
        return sum(len(game.roms) for game in self.games)

    def find_game_by_name(self, name: str) -> Optional[DATGame]:
        """Find game by exact name match."""
        for game in self.games:
            if game.name == name:
                return game
        return None

    def find_game_by_rom_name(self, rom_name: str) -> Optional[DATGame]:
        """Find game by ROM filename."""
        for game in self.games:
            for rom in game.roms:
                if rom.name == rom_name:
                    return game
        return None

    def find_game_by_hash(
        self, crc: Optional[str] = None, md5: Optional[str] = None, sha1: Optional[str] = None
    ) -> Optional[DATGame]:
        """Find game by ROM hash."""
        if crc:
            crc = crc.lower()
        if md5:
            md5 = md5.lower()
        if sha1:
            sha1 = sha1.lower()

        for game in self.games:
            for rom in game.roms:
                if crc and rom.crc == crc:
                    return game
                if md5 and rom.md5 == md5:
                    return game
                if sha1 and rom.sha1 == sha1:
                    return game
        return None

    def get_total_size(self) -> int:
        """Get total size of all ROMs in DAT."""
        return sum(game.get_total_size() for game in self.games)

    def get_statistics(self) -> dict:
        """Get DAT statistics."""
        multi_disc_count = sum(1 for game in self.games if game.is_multi_disc())

        return {
            "games": self.get_game_count(),
            "roms": self.get_rom_count(),
            "multi_disc_games": multi_disc_count,
            "total_size_bytes": self.get_total_size(),
            "total_size_gb": round(self.get_total_size() / (1024**3), 2),
        }
