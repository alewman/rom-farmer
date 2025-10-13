"""ROM file matcher for DAT entries."""

import zipfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from .models import DATFile, DATGame, DATRom


class MatchType(str, Enum):
    """Type of match found."""

    EXACT_FILENAME = "exact_filename"  # ZIP name matches ROM name exactly
    INNER_FILENAME = "inner_filename"  # File inside ZIP matches ROM name
    CRC_MATCH = "crc_match"  # CRC hash matches
    MD5_MATCH = "md5_match"  # MD5 hash matches
    SHA1_MATCH = "sha1_match"  # SHA1 hash matches
    NO_MATCH = "no_match"


@dataclass
class MatchResult:
    """Result of matching a file against a DAT."""

    file_path: Path
    match_type: MatchType
    dat_game: Optional[DATGame] = None
    dat_rom: Optional[DATRom] = None
    confidence: float = 0.0  # 0.0 to 1.0

    def is_matched(self) -> bool:
        """Check if file matched successfully."""
        return self.match_type != MatchType.NO_MATCH

    def get_expected_size(self) -> Optional[int]:
        """Get expected ROM size from DAT."""
        return self.dat_rom.size if self.dat_rom else None


class ROMMatcher:
    """Match ROM files against DAT entries."""

    def __init__(self, dat_file: DATFile):
        """Initialize matcher with parsed DAT.

        Args:
            dat_file: Parsed DATFile object
        """
        self.dat_file = dat_file
        self._build_indices()

    def _build_indices(self):
        """Build lookup indices for fast matching."""
        # Index by ROM name (for filename matching)
        self.rom_name_index: dict[str, tuple[DATGame, DATRom]] = {}
        for game in self.dat_file.games:
            for rom in game.roms:
                self.rom_name_index[rom.name] = (game, rom)

        # Index by CRC (for hash matching)
        self.crc_index: dict[str, tuple[DATGame, DATRom]] = {}
        for game in self.dat_file.games:
            for rom in game.roms:
                if rom.crc:
                    self.crc_index[rom.crc.lower()] = (game, rom)

        # Index by MD5
        self.md5_index: dict[str, tuple[DATGame, DATRom]] = {}
        for game in self.dat_file.games:
            for rom in game.roms:
                if rom.md5:
                    self.md5_index[rom.md5.lower()] = (game, rom)

        # Index by SHA1
        self.sha1_index: dict[str, tuple[DATGame, DATRom]] = {}
        for game in self.dat_file.games:
            for rom in game.roms:
                if rom.sha1:
                    self.sha1_index[rom.sha1.lower()] = (game, rom)

    def match_file(self, file_path: Path) -> MatchResult:
        """Match a file against the DAT.

        Matching strategy:
        1. For No-Intro ZIPs: Strip .zip, match against ROM name
        2. For No-Intro ZIPs: Check inner filename (should match)
        3. For extracted files: Match filename directly
        4. For hash-based: Match CRC/MD5/SHA1 (future enhancement)

        Args:
            file_path: Path to ROM file

        Returns:
            MatchResult with match information
        """
        if not file_path.exists():
            return MatchResult(
                file_path=file_path,
                match_type=MatchType.NO_MATCH,
                confidence=0.0,
            )

        # Strategy 1: ZIP filename matching (No-Intro)
        if file_path.suffix.lower() == ".zip":
            return self._match_zip_file(file_path)

        # Strategy 2: Direct filename matching (extracted files)
        return self._match_extracted_file(file_path)

    def _match_zip_file(self, zip_path: Path) -> MatchResult:
        """Match ZIP file against DAT.

        For No-Intro:
        - Myrient has: "Contra (USA).zip"
        - DAT expects: "Contra (USA).nes"
        - Match: Strip .zip, check if inner file matches

        Args:
            zip_path: Path to ZIP file

        Returns:
            MatchResult
        """
        # Get expected ROM name by stripping .zip
        rom_name_base = zip_path.stem  # "Contra (USA)"

        # Try matching inner file
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                namelist = zf.namelist()

                # Look for matching file inside ZIP
                for inner_name in namelist:
                    # Skip directories and hidden files
                    if inner_name.endswith("/") or inner_name.startswith("."):
                        continue

                    # Check if this inner file matches a ROM in DAT
                    if inner_name in self.rom_name_index:
                        game, rom = self.rom_name_index[inner_name]
                        return MatchResult(
                            file_path=zip_path,
                            match_type=MatchType.INNER_FILENAME,
                            dat_game=game,
                            dat_rom=rom,
                            confidence=1.0,
                        )

                # If no exact match, try fuzzy matching
                # (in case the inner filename doesn't exactly match the ZIP name)
                for inner_name in namelist:
                    if inner_name.endswith("/") or inner_name.startswith("."):
                        continue

                    # Check if ROM base name matches
                    inner_base = Path(inner_name).stem
                    if inner_base == rom_name_base:
                        # Found matching base name, try to find in DAT by base
                        for dat_rom_name, (game, rom) in self.rom_name_index.items():
                            if Path(dat_rom_name).stem == rom_name_base:
                                return MatchResult(
                                    file_path=zip_path,
                                    match_type=MatchType.INNER_FILENAME,
                                    dat_game=game,
                                    dat_rom=rom,
                                    confidence=0.9,  # Slightly lower confidence
                                )

        except (zipfile.BadZipFile, OSError):
            pass

        return MatchResult(
            file_path=zip_path,
            match_type=MatchType.NO_MATCH,
            confidence=0.0,
        )

    def _match_extracted_file(self, file_path: Path) -> MatchResult:
        """Match extracted file directly.

        Args:
            file_path: Path to extracted file

        Returns:
            MatchResult
        """
        filename = file_path.name

        # Try exact filename match
        if filename in self.rom_name_index:
            game, rom = self.rom_name_index[filename]
            return MatchResult(
                file_path=file_path,
                match_type=MatchType.EXACT_FILENAME,
                dat_game=game,
                dat_rom=rom,
                confidence=1.0,
            )

        return MatchResult(
            file_path=file_path,
            match_type=MatchType.NO_MATCH,
            confidence=0.0,
        )

    def match_by_hash(
        self,
        file_path: Path,
        crc: Optional[str] = None,
        md5: Optional[str] = None,
        sha1: Optional[str] = None,
    ) -> MatchResult:
        """Match file by hash.

        Args:
            file_path: Path to file
            crc: CRC32 hash (hex string)
            md5: MD5 hash (hex string)
            sha1: SHA1 hash (hex string)

        Returns:
            MatchResult
        """
        # Try CRC match first (fastest)
        if crc:
            crc_lower = crc.lower()
            if crc_lower in self.crc_index:
                game, rom = self.crc_index[crc_lower]
                return MatchResult(
                    file_path=file_path,
                    match_type=MatchType.CRC_MATCH,
                    dat_game=game,
                    dat_rom=rom,
                    confidence=1.0,
                )

        # Try MD5 match
        if md5:
            md5_lower = md5.lower()
            if md5_lower in self.md5_index:
                game, rom = self.md5_index[md5_lower]
                return MatchResult(
                    file_path=file_path,
                    match_type=MatchType.MD5_MATCH,
                    dat_game=game,
                    dat_rom=rom,
                    confidence=1.0,
                )

        # Try SHA1 match
        if sha1:
            sha1_lower = sha1.lower()
            if sha1_lower in self.sha1_index:
                game, rom = self.sha1_index[sha1_lower]
                return MatchResult(
                    file_path=file_path,
                    match_type=MatchType.SHA1_MATCH,
                    dat_game=game,
                    dat_rom=rom,
                    confidence=1.0,
                )

        return MatchResult(
            file_path=file_path,
            match_type=MatchType.NO_MATCH,
            confidence=0.0,
        )

    def get_matched_count(self, file_paths: list[Path]) -> int:
        """Count how many files match the DAT.

        Args:
            file_paths: List of file paths to check

        Returns:
            Number of matched files
        """
        matched = 0
        for file_path in file_paths:
            result = self.match_file(file_path)
            if result.is_matched():
                matched += 1
        return matched

    def get_unmatched_files(self, file_paths: list[Path]) -> list[Path]:
        """Get list of files that don't match the DAT.

        Args:
            file_paths: List of file paths to check

        Returns:
            List of unmatched file paths
        """
        unmatched = []
        for file_path in file_paths:
            result = self.match_file(file_path)
            if not result.is_matched():
                unmatched.append(file_path)
        return unmatched
