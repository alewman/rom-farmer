"""Data models for DAT files."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ROMStatus(str, Enum):
    """ROM status in DAT."""

    GOOD = "good"
    BAD = "bad"
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    NODUMP = "nodump"


class DriverStatus(str, Enum):
    """Driver emulation status (MAME/FBNeo)."""

    GOOD = "good"  # Fully working
    IMPERFECT = "imperfect"  # Minor issues
    PRELIMINARY = "preliminary"  # Major issues, may not work
    PROTECTION = "protection"  # Unemulated protection
    UNKNOWN = "unknown"


class ArcadeCloneType(str, Enum):
    """Type of arcade clone/variant."""

    PARENT = "parent"  # Original/main version
    REGIONAL = "regional"  # Regional variant (USA, Japan, World, etc.)
    REVISION = "revision"  # Version/revision (r1, r2, etc.)
    BOOTLEG = "bootleg"  # Unauthorized copy
    HACK = "hack"  # Modified version (speed hacks, character edits)
    PROTOTYPE = "prototype"  # Pre-release version
    HOMEBREW = "homebrew"  # Fan-made game
    DEMO = "demo"  # Demo/sample version
    BIOS = "bios"  # BIOS-only entry


class DATType(str, Enum):
    """Type of DAT file."""

    NOINTRO = "nointro"
    REDUMP = "redump"
    RETOOL = "retool"
    MAME = "mame"
    FBNEO = "fbneo"
    HBMAME = "hbmame"
    CUSTOM = "custom"


@dataclass
class DATRom:
    """ROM entry in DAT file."""

    name: str
    size: int
    crc: str | None = None
    md5: str | None = None
    sha1: str | None = None
    sha256: str | None = None
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
class DATDisk:
    """Disk/CHD entry in DAT file (MAME/FBNeo)."""

    name: str
    sha1: str | None = None
    md5: str | None = None
    region: str | None = None  # e.g., "cdrom", "ide:0:hdd", "gdrom"
    status: str = "good"  # good, nodump, baddump
    merge: str | None = None  # Parent disk to merge with

    def __post_init__(self):
        """Normalize hashes to lowercase."""
        if self.sha1:
            self.sha1 = self.sha1.lower()
        if self.md5:
            self.md5 = self.md5.lower()


@dataclass
class DATGame:
    """Game entry in DAT file."""

    name: str
    roms: list[DATRom] = field(default_factory=list)
    disks: list[DATDisk] = field(default_factory=list)  # CHD/disk requirements
    description: str | None = None
    category: str | None = None  # Retool-specific
    cloneof: str | None = None
    romof: str | None = None  # Arcade: parent ROM set reference
    year: str | None = None
    manufacturer: str | None = None
    region: str | None = None
    # Arcade-specific fields
    comment: str | None = None  # Bootleg, Hack, Prototype, etc.
    driver_status: str | None = None  # good, imperfect, preliminary
    sourcefile: str | None = None  # Driver source file
    is_bios: bool = False  # Is this a BIOS entry
    is_device: bool = False  # Is this a device entry

    def get_primary_rom(self) -> DATRom | None:
        """Get primary ROM (first ROM, or only ROM)."""
        return self.roms[0] if self.roms else None

    def has_chd(self) -> bool:
        """Check if game requires CHD/disk files."""
        return len(self.disks) > 0

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
    description: str | None = None
    version: str | None = None
    author: str | None = None
    dat_type: DATType = DATType.NOINTRO
    games: list[DATGame] = field(default_factory=list)
    source_file: Path | None = None

    def get_game_count(self) -> int:
        """Get total number of games."""
        return len(self.games)

    def get_rom_count(self) -> int:
        """Get total number of ROMs (multi-disc games count as multiple)."""
        return sum(len(game.roms) for game in self.games)

    def find_game_by_name(self, name: str) -> DATGame | None:
        """Find game by exact name match."""
        for game in self.games:
            if game.name == name:
                return game
        return None

    def find_game_by_rom_name(self, rom_name: str) -> DATGame | None:
        """Find game by ROM filename."""
        for game in self.games:
            for rom in game.roms:
                if rom.name == rom_name:
                    return game
        return None

    def find_game_by_hash(
        self, crc: str | None = None, md5: str | None = None, sha1: str | None = None
    ) -> DATGame | None:
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
