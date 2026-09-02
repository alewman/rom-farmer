"""
Cross-platform game name normalization for 1G1Gen matching.

This module provides utilities for normalizing game names across different platforms
to identify the same game released on multiple systems. It strips platform-specific
metadata, normalizes title variations, and extracts key identifying information.

Example:
    >>> normalizer = GameNameNormalizer()
    >>> psx_game = normalizer.normalize("Grand Theft Auto (USA)", "psx")
    >>> ps2_game = normalizer.normalize("Grand Theft Auto (USA)", "ps2")
    >>> psx_game.match_key() == ps2_game.match_key()
    True  # Same game across platforms!
"""

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class NormalizedGame:
    """Normalized game for cross-platform matching.

    Attributes:
        original_name: Original game name from DAT file
        normalized_name: Cleaned name for matching
        platform: Platform identifier (psx, ps2, saturn, etc.)
        region: Detected region code (USA, Europe, Japan, World)
        year: Release year if present in name
        revision: Revision number (0 if none)
        file_path: Path to the actual game file
    """

    original_name: str
    normalized_name: str
    platform: str
    region: str | None = None
    year: str | None = None
    revision: int = 0
    file_path: str | None = None

    def match_key(self) -> str:
        """Get key for matching across platforms.

        Games with the same match_key are considered the same game
        on different platforms.

        Returns:
            Lowercase string: "normalized_name|region"
        """
        key = self.normalized_name
        # Include region in match key to avoid matching different regional releases
        # "Final Fantasy VII (USA)" should match across platforms
        # but not match "Final Fantasy VII (Japan)"
        if self.region:
            key = f"{key}|{self.region}"
        return key.lower()

    def __repr__(self) -> str:
        return f"NormalizedGame({self.platform}: {self.normalized_name} [{self.region}])"


class GameNameNormalizer:
    """Normalize game names for cross-platform matching.

    This class handles the complex task of identifying the same game across
    different platforms. It:
    - Strips region/language markers
    - Normalizes punctuation and whitespace
    - Handles title variations (III vs 3, The vs no The)
    - Extracts metadata (region, year, revision)
    """

    # Regex patterns for metadata extraction and stripping
    REGION_PATTERN = re.compile(
        r"\((USA?|Europe|Japan|World|Asia|Korea|En|Fr|De|Es|It|Pt|Nl|Sv|No|Da|Fi|Zh|Ja|Ko|Ru|Pl|Tr)\)",
        re.IGNORECASE,
    )
    LANGUAGE_PATTERN = re.compile(r"\(([A-Z][a-z](,[A-Z][a-z])*)\)")
    REVISION_PATTERN = re.compile(r"\((Rev|Version|v)[\s\.]?(\d+|[A-Z])\)", re.IGNORECASE)
    DISC_PATTERN = re.compile(r"\(Disc\s+\d+(\s+of\s+\d+)?\)", re.IGNORECASE)
    PLATFORM_HINTS = re.compile(
        r"\((?:PS2|Xbox|GC|GameCube|PSX|PlayStation|Saturn)\s+(?:Exclusive|Only|Version)\)",
        re.IGNORECASE,
    )
    YEAR_PATTERN = re.compile(r"\b(19\d{2}|20\d{2})\b")

    # Additional patterns for cleaning
    SUBTITLE_SEPARATOR = re.compile(r"[:\-–—]")  # Various dash types
    QUOTES_PATTERN = re.compile(r'[\'"`]')
    BRACKETS_PATTERN = re.compile(r"\[[^\]]*\]")  # [!], [b], [T+Eng], etc.
    PARENS_CLEANUP = re.compile(r"\(\s*\)")  # Empty parentheses

    # Roman numeral to arabic conversion
    ROMAN_NUMERALS = {
        r"\bI\b": "1",
        r"\bII\b": "2",
        r"\bIII\b": "3",
        r"\bIV\b": "4",
        r"\bV\b": "5",
        r"\bVI\b": "6",
        r"\bVII\b": "7",
        r"\bVIII\b": "8",
        r"\bIX\b": "9",
        r"\bX\b": "10",
        r"\bXI\b": "11",
        r"\bXII\b": "12",
    }

    # Common title variations to normalize
    TITLE_NORMALIZATIONS = {
        r"\bThe\s+": "",  # "The Legend" -> "Legend"
        r"\bA\s+": "",  # "A Bug's Life" -> "Bug's Life"
        r"\bAn\s+": "",  # "An American Tail" -> "American Tail"
        r"&": "and",  # "Tom & Jerry" -> "Tom and Jerry"
    }

    @classmethod
    def normalize(
        cls, game_name: str, platform: str, file_path: str | None = None
    ) -> NormalizedGame:
        """Normalize a game name for cross-platform matching.

        Args:
            game_name: Original game name from DAT file
            platform: Platform identifier (psx, ps2, saturn, gamecube, xbox, etc.)
            file_path: Optional path to the actual game file

        Returns:
            NormalizedGame with extracted metadata and cleaned name
        """
        original = game_name
        normalized = game_name

        # Extract metadata BEFORE stripping
        region = cls._extract_region(game_name)
        year = cls._extract_year(game_name)
        revision = cls._extract_revision(game_name)

        logger.debug(f"Normalizing: {game_name} ({platform})")

        # Strip brackets (Good Dump markers, translations, etc.)
        # [!], [b], [T+Eng], [h], [f], etc.
        normalized = cls.BRACKETS_PATTERN.sub("", normalized)

        # Strip region markers
        normalized = cls.REGION_PATTERN.sub("", normalized)

        # Strip language markers
        normalized = cls.LANGUAGE_PATTERN.sub("", normalized)

        # Strip revision markers
        normalized = cls.REVISION_PATTERN.sub("", normalized)

        # Strip disc markers (multi-disc games)
        normalized = cls.DISC_PATTERN.sub("", normalized)

        # Strip platform hints
        normalized = cls.PLATFORM_HINTS.sub("", normalized)

        # Normalize Roman numerals to Arabic numbers
        # "Final Fantasy VII" -> "Final Fantasy 7"
        for roman, arabic in cls.ROMAN_NUMERALS.items():
            normalized = re.sub(roman, arabic, normalized)

        # Apply title normalizations
        for pattern, replacement in cls.TITLE_NORMALIZATIONS.items():
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)

        # Normalize punctuation (colons, dashes, quotes)
        normalized = cls.SUBTITLE_SEPARATOR.sub(" ", normalized)
        normalized = cls.QUOTES_PATTERN.sub("", normalized)

        # Clean up empty parentheses
        normalized = cls.PARENS_CLEANUP.sub("", normalized)

        # Normalize whitespace
        normalized = re.sub(r"\s+", " ", normalized).strip()

        # Final cleanup - remove trailing/leading punctuation
        normalized = normalized.strip(" .-,")

        result = NormalizedGame(
            original_name=original,
            normalized_name=normalized,
            platform=platform,
            region=region,
            year=year,
            revision=revision,
            file_path=file_path,
        )

        logger.debug(f"  -> {result.normalized_name} | {result.region} | key={result.match_key()}")

        return result

    @staticmethod
    def _extract_region(name: str) -> str | None:
        """Extract region code from game name.

        Returns:
            Region code (USA, Europe, Japan, World) or None
        """
        # Look for common region patterns
        patterns = [
            (r"\(USA?\)", "USA"),
            (r"\(U\)", "USA"),
            (r"\(Europe\)", "Europe"),
            (r"\(E\)", "Europe"),
            (r"\(Japan\)", "Japan"),
            (r"\(J\)", "Japan"),
            (r"\(World\)", "World"),
            (r"\(W\)", "World"),
        ]

        for pattern, region in patterns:
            if re.search(pattern, name, re.IGNORECASE):
                return region

        return None

    @staticmethod
    def _extract_year(name: str) -> str | None:
        """Extract year if present in game name.

        Returns:
            Year as string (e.g., "2001") or None
        """
        match = re.search(r"\b(19\d{2}|20\d{2})\b", name)
        return match.group(1) if match else None

    @staticmethod
    def _extract_revision(name: str) -> int:
        """Extract revision number from game name.

        Handles:
        - (Rev 1), (Rev A)
        - (Version 1.1)
        - (v1.2)

        Returns:
            Revision number (0 if none, 1 for Rev A, 2 for Rev B, etc.)
        """
        match = re.search(r"\((Rev|Version|v)[\s\.]?(\d+|[A-Z])\)", name, re.IGNORECASE)
        if match:
            rev_str = match.group(2)
            if rev_str.isdigit():
                return int(rev_str)
            elif rev_str.isalpha():
                # Rev A = 1, Rev B = 2, etc.
                return ord(rev_str.upper()) - ord("A") + 1
        return 0
