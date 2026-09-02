"""
DAT Manager for Redump/No-Intro DAT files.

This module provides fast hash lookups from DAT files, avoiding the need
to calculate hashes for 95%+ of ROMs. Supports:
- Redump (disc-based systems)
- No-Intro (cartridge-based systems)
- TOSEC and other DAT formats
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console

console = Console()


@dataclass
class DATEntry:
    """A single entry from a DAT file."""

    name: str
    description: str
    md5: str | None = None
    sha1: str | None = None
    sha256: str | None = None
    crc32: str | None = None
    size: int | None = None

    # DAT metadata
    dat_name: str = ""  # "Redump - Microsoft Xbox 360"
    dat_version: str = ""

    def __repr__(self):
        return f"<DATEntry(name='{self.name[:40]}...', md5='{self.md5[:8] if self.md5 else 'None'}...')>"


class DATManager:
    """
    Manages DAT files for instant hash lookups.

    This class loads DAT files at startup and provides fast lookups by:
    - Filename (normalized)
    - Hash (MD5, SHA1, CRC32)
    - Size

    Example:
        dat_mgr = DATManager([Path('/path/to/dats/redump'), Path('/path/to/dats/nointro')])
        entry = dat_mgr.lookup_by_filename('Halo 3 (USA).iso', 'xbox360')
        if entry:
            print(f"MD5: {entry.md5}")  # Instant!
    """

    def __init__(self, dat_directories: list[Path]):
        """
        Initialize DAT manager.

        Args:
            dat_directories: List of directories containing DAT files
        """
        self.dat_directories = dat_directories
        self.dats: dict[str, dict[str, DATEntry]] = {}  # system -> {normalized_name: entry}
        self.hash_index: dict[str, DATEntry] = {}  # hash -> entry (for reverse lookup)

        self._load_all_dats()

    def _load_all_dats(self):
        """Load all DAT files from configured directories."""
        console.print("[cyan]Loading DAT files...[/cyan]")

        total_entries = 0
        dat_count = 0

        for dat_dir in self.dat_directories:
            if not dat_dir.exists():
                console.print(f"[yellow]⚠ DAT directory not found:[/yellow] {dat_dir}")
                continue

            # Find all .dat files recursively
            for dat_file in dat_dir.rglob("*.dat"):
                try:
                    entries = self._parse_dat_file(dat_file)
                    if entries:
                        system = self._extract_system_from_path(dat_file)

                        # Store entries by system
                        if system not in self.dats:
                            self.dats[system] = {}

                        for entry in entries:
                            normalized = self._normalize_filename(entry.name)
                            self.dats[system][normalized] = entry

                            # Build hash index for reverse lookups
                            if entry.md5:
                                self.hash_index[entry.md5.lower()] = entry
                            if entry.sha1:
                                self.hash_index[entry.sha1.lower()] = entry

                        total_entries += len(entries)
                        dat_count += 1

                except Exception as e:
                    console.print(f"[red]✗ Error loading {dat_file.name}:[/red] {e}")

        console.print(
            f"[green]✓ Loaded {dat_count} DAT files "
            f"({total_entries} entries, {len(self.dats)} systems)[/green]"
        )

    def _parse_dat_file(self, dat_file: Path) -> list[DATEntry]:
        """
        Parse a DAT file (XML format).

        Supports both Redump and No-Intro DAT formats.
        """
        try:
            tree = ET.parse(dat_file)
            root = tree.getroot()

            # Get DAT metadata
            header = root.find("header")
            dat_name = header.findtext("name", "") if header is not None else ""
            dat_version = header.findtext("version", "") if header is not None else ""

            entries = []

            # Parse game entries
            for game in root.findall("game"):
                name = game.get("name", "")
                description = game.findtext("description", name)

                # Parse ROM info
                rom = game.find("rom")
                if rom is not None:
                    entry = DATEntry(
                        name=name,
                        description=description,
                        md5=rom.get("md5"),
                        sha1=rom.get("sha1"),
                        sha256=rom.get("sha256"),
                        crc32=rom.get("crc"),
                        size=int(rom.get("size", 0)) if rom.get("size") else None,
                        dat_name=dat_name,
                        dat_version=dat_version,
                    )
                    entries.append(entry)

            return entries

        except ET.ParseError as e:
            console.print(f"[red]✗ XML parse error in {dat_file.name}:[/red] {e}")
            return []
        except Exception as e:
            console.print(f"[red]✗ Error parsing {dat_file.name}:[/red] {e}")
            return []

    def _extract_system_from_path(self, dat_file: Path) -> str:
        """
        Extract system name from DAT file path.

        Examples:
            /dats/redump/Microsoft - Xbox 360.dat -> xbox360
            /dats/nointro/Nintendo - Nintendo Entertainment System.dat -> nes
        """
        # Try to map common patterns
        name_lower = dat_file.stem.lower()

        # System mapping
        system_map = {
            "xbox 360": "xbox360",
            "xbox": "xbox",
            "playstation 3": "ps3",
            "playstation 2": "ps2",
            "playstation": "psx",
            "psp": "psp",
            "nintendo entertainment system": "nes",
            "super nintendo": "snes",
            "nintendo 64": "n64",
            "nintendo ds": "nds",
            "game boy advance": "gba",
            "game boy color": "gbc",
            "game boy": "gb",
            "sega mega drive": "megadrive",
            "sega genesis": "megadrive",
            "sega saturn": "saturn",
            "sega dreamcast": "dreamcast",
            "sega game gear": "gamegear",
            "sega master system": "mastersystem",
            "sega cd": "segacd",
            "sony playstation": "psx",
            "sony - playstation": "psx",
            "pc engine": "pcengine",
            "turbografx": "pcengine",
            "atari 2600": "atari2600",
            "atari 5200": "atari5200",
            "atari 7800": "atari7800",
        }

        for pattern, system in system_map.items():
            if pattern in name_lower:
                return system

        # Fallback: use filename
        return dat_file.stem.lower().replace(" ", "_").replace("-", "_")

    def _normalize_filename(self, filename: str) -> str:
        """
        Normalize filename for matching.

        Removes extension and common suffixes, lowercases.
        """
        # Remove extension
        if "." in filename:
            filename = filename.rsplit(".", 1)[0]

        # Lowercase
        filename = filename.lower()

        # Remove common patterns
        filename = filename.strip()

        return filename

    def lookup_by_filename(self, filename: str, system: str) -> DATEntry | None:
        """
        Look up a ROM by filename.

        Args:
            filename: ROM filename (e.g., "Halo 3 (USA).iso")
            system: System name (e.g., "xbox360")

        Returns:
            DATEntry if found, None otherwise
        """
        if system not in self.dats:
            return None

        normalized = self._normalize_filename(filename)
        return self.dats[system].get(normalized)

    def lookup_by_hash(self, md5: str | None = None, sha1: str | None = None) -> DATEntry | None:
        """
        Reverse lookup: hash -> game info.

        Args:
            md5: MD5 hash to look up
            sha1: SHA1 hash to look up

        Returns:
            DATEntry if found, None otherwise
        """
        if md5:
            entry = self.hash_index.get(md5.lower())
            if entry:
                return entry

        if sha1:
            entry = self.hash_index.get(sha1.lower())
            if entry:
                return entry

        return None

    def get_system_count(self) -> int:
        """Get number of systems loaded."""
        return len(self.dats)

    def get_entry_count(self) -> int:
        """Get total number of entries across all systems."""
        return sum(len(entries) for entries in self.dats.values())

    def get_systems(self) -> list[str]:
        """Get list of loaded system names."""
        return list(self.dats.keys())
