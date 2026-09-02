"""Arcade game classifier for clone type detection.

Classifies arcade games into categories:
- Parent: Original/main version
- Regional: USA, Japan, World, Europe variants
- Revision: Version updates (r1, r2, etc.)
- Bootleg: Unauthorized copies
- Hack: Modified versions (Rainbow Edition, turbo hacks, etc.)
- Prototype: Pre-release versions
- Homebrew: Fan-made games
- Demo: Demo/sample versions
"""

import re
from dataclasses import dataclass
from enum import Enum

from ..dat_parser.models import ArcadeCloneType, DATGame


class CloneImportance(str, Enum):
    """Cultural/historical importance of a clone."""

    ESSENTIAL = "essential"  # Must include (famous hacks like Rainbow Edition)
    RECOMMENDED = "recommended"  # Good to include if space allows
    OPTIONAL = "optional"  # Include only for completeness
    SKIP = "skip"  # Generally skip (low-quality bootlegs, broken hacks)


@dataclass
class ArcadeClassification:
    """Classification result for an arcade game."""

    clone_type: ArcadeCloneType
    importance: CloneImportance
    region: str | None = None
    revision: str | None = None
    is_working: bool = True
    notes: str | None = None


# Famous hacks/bootlegs that are culturally important and should be preserved
# Note: Many "hacks" in arcade history were actually bootleg boards
ESSENTIAL_HACKS = {
    # Street Fighter II - Rainbow Edition (iconic bootleg, legendary in arcades)
    "sf2rb",
    "sf2rb2",
    "sf2rb3",
    "sf2rb4",
    "sf2rb5",
    "sf2rb6",
    # Street Fighter II - Other famous mods
    "sf2koryu",
    "sf2koryu2",
    "sf2koryu3",  # Koryu (Korean hack)
    "sf2m1",
    "sf2m2",
    "sf2m3",
    "sf2m4",
    "sf2m5",
    "sf2m6",
    "sf2m7",  # Magic variants
    "sf2yyc",
    "sf2yyc2",  # YYC
    # Ms. Pac-Man (originally a hack kit, became official)
    "mspacman",
    "mspacmab",
    "mspacmat",
    # Pac-Man Plus
    "pacplus",
    # Donkey Kong hacks
    "dkong3b",  # Bootleg
    "dkrainbow",  # Rainbow
    # JoJo Rainbow Edition (popular modern hack)
    "jojobanrb",
    # Various other famous bootlegs/hacks
    "1943kai",  # 1943 Kai
}

# Quality Neo-Geo homebrew that are complete games (not demos)
QUALITY_HOMEBREW = {
    # Commercial quality releases
    "xenocrisis",  # Xeno Crisis - Full commercial game
    "lasthope",  # Last Hope - Full shmup
    "b2b",  # Bang Bang Busters - Commercial release
    "ironclad",  # Ironclad (commercial, also called Brikin'ger)
    "sbp",  # Super Bubble Pop
    "frogfeast",  # Frog Feast - Full game
    # Quality conversions/ports
    "shinobing",  # Shinobi Neo Geo - Complete conversion
    "goldnaxeng",  # Golden Axe Neo Geo - Complete conversion
    "cabalng",  # Cabal Neo Geo - Complete conversion
    "karnovng",  # Karnov Neo Geo - Complete conversion
    "columnsn",  # Columns Neo Geo
    "neopang",  # Neo Pang - Complete puzzle game
    "neotet",  # NeoGeo 2-Player Tetris
    "looptrsp",  # Looptris Plus
    "hypernoid",  # Hypernoid - Complete game
    "neo2048",  # Neo 2048 - Complete puzzle
    "knightsch",  # Knight's Chance
    "timesup",  # Time's UP! - Complete game
    "gladmort",  # GladMort - Complete game
    "poknight",  # Poker Night
    "yoyoshkn",  # Yo-Yo Shuriken
}

# Regional priority order (higher = better for English speakers)
REGION_PRIORITY = {
    "world": 100,
    "usa": 90,
    "us": 90,
    "europe": 80,
    "euro": 80,
    "asia": 70,
    "japan": 60,
    "korea": 50,
    "taiwan": 40,
    "hong kong": 40,
    "hispanic": 30,
    "brazil": 30,
}


class ArcadeClassifier:
    """Classifier for arcade game variants."""

    def __init__(
        self,
        essential_hacks: set[str] | None = None,
        quality_homebrew: set[str] | None = None,
    ):
        """Initialize classifier.

        Args:
            essential_hacks: Set of ROM names considered essential hacks.
                            Defaults to built-in list.
            quality_homebrew: Set of ROM names for quality homebrew games.
                             Defaults to built-in list.
        """
        self.essential_hacks = essential_hacks or ESSENTIAL_HACKS
        self.quality_homebrew = quality_homebrew or QUALITY_HOMEBREW

    def classify(self, game: DATGame) -> ArcadeClassification:
        """Classify an arcade game.

        Args:
            game: DATGame to classify

        Returns:
            ArcadeClassification with clone type, importance, etc.
        """
        # Check if it's a working game
        is_working = game.driver_status in (None, "good", "imperfect")

        # BIOS/Device detection (always first)
        if game.is_bios:
            return ArcadeClassification(
                clone_type=ArcadeCloneType.BIOS,
                importance=CloneImportance.ESSENTIAL,
                is_working=is_working,
            )

        # Check comment for homebrew/demo even for parents
        # This allows filtering out homebrew/demo parent games
        comment = (game.comment or "").lower()

        # Homebrew parent games - distinguish complete games from demos
        if not game.cloneof and "homebrew" in comment:
            # Check if it's a demo
            if "demo" in comment or "tech-demo" in comment or "techdemo" in comment:
                return ArcadeClassification(
                    clone_type=ArcadeCloneType.DEMO,  # Treat demo homebrew as DEMO
                    importance=CloneImportance.SKIP,
                    is_working=is_working,
                    notes="Homebrew demo",
                )
            # Check if it's quality homebrew
            importance = CloneImportance.OPTIONAL
            if game.name in self.quality_homebrew:
                importance = CloneImportance.RECOMMENDED
            # Complete homebrew game
            return ArcadeClassification(
                clone_type=ArcadeCloneType.HOMEBREW,
                importance=importance,
                is_working=is_working,
                notes="Complete homebrew",
            )

        # Demo parent games (non-homebrew demos)
        if not game.cloneof and "demo" in comment:
            return ArcadeClassification(
                clone_type=ArcadeCloneType.DEMO,
                importance=CloneImportance.SKIP,
                is_working=is_working,
                notes="Demo parent",
            )

        # Regular parent detection
        if not game.cloneof:
            return ArcadeClassification(
                clone_type=ArcadeCloneType.PARENT,
                importance=CloneImportance.ESSENTIAL,
                is_working=is_working,
            )

        # Classify based on comment field (for clones)
        clone_type, importance = self._classify_from_comment(game)

        # Override importance for essential hacks
        if game.name in self.essential_hacks:
            importance = CloneImportance.ESSENTIAL

        # Extract region if it's a regional variant
        region = self._extract_region(game)
        if region and clone_type == ArcadeCloneType.REGIONAL:
            # Adjust importance based on region
            if region.lower() in ("world", "usa", "us"):
                importance = CloneImportance.RECOMMENDED
            elif region.lower() in ("europe", "euro"):
                importance = CloneImportance.RECOMMENDED

        # Extract revision
        revision = self._extract_revision(game)

        return ArcadeClassification(
            clone_type=clone_type,
            importance=importance,
            region=region,
            revision=revision,
            is_working=is_working,
        )

    def _classify_from_comment(self, game: DATGame) -> tuple[ArcadeCloneType, CloneImportance]:
        """Classify based on comment field.

        Args:
            game: DATGame to classify

        Returns:
            Tuple of (ArcadeCloneType, CloneImportance)
        """
        comment = (game.comment or "").lower()
        desc = (game.description or "").lower()

        # Check for specific types in order of priority
        if "bootleg" in comment:
            # Bootlegs with sound/graphics issues are lower priority
            if "no sound" in comment or "imperfect" in comment:
                return ArcadeCloneType.BOOTLEG, CloneImportance.SKIP
            return ArcadeCloneType.BOOTLEG, CloneImportance.OPTIONAL

        if "hack" in comment:
            return ArcadeCloneType.HACK, CloneImportance.OPTIONAL

        # Check description for hack indicators
        # These are modified versions with alternate content (music, graphics, gameplay)
        hack_indicators = [
            "music)",  # e.g., "1942 (C64 Music)"
            "supercharger",  # e.g., "Supercharger 1942"
            "turbo",  # e.g., "Super Turbo" hacks
            "rainbow",  # e.g., "Rainbow Edition"
            "bootleg",  # Sometimes in description
        ]
        if any(indicator in desc for indicator in hack_indicators):
            return ArcadeCloneType.HACK, CloneImportance.OPTIONAL

        if "prototype" in comment:
            return ArcadeCloneType.PROTOTYPE, CloneImportance.RECOMMENDED

        if "homebrew" in comment:
            return ArcadeCloneType.HOMEBREW, CloneImportance.OPTIONAL

        if "demo" in comment:
            return ArcadeCloneType.DEMO, CloneImportance.OPTIONAL

        if "bios" in comment:
            return ArcadeCloneType.BIOS, CloneImportance.ESSENTIAL

        # No comment - likely a regional or revision clone
        region = self._extract_region(game)
        if region:
            return ArcadeCloneType.REGIONAL, CloneImportance.RECOMMENDED

        revision = self._extract_revision(game)
        if revision:
            return ArcadeCloneType.REVISION, CloneImportance.RECOMMENDED

        # Default: treat as regional variant
        return ArcadeCloneType.REGIONAL, CloneImportance.OPTIONAL

    def _extract_region(self, game: DATGame) -> str | None:
        """Extract region from game name or description.

        Args:
            game: DATGame to extract region from

        Returns:
            Region string or None
        """
        name = game.name.lower()
        desc = (game.description or "").lower()

        # Check common regional suffixes in ROM names
        region_patterns = [
            (r"[_-]?(usa?|us)$", "USA"),
            (r"[_-]?(jpn?|japan)$", "Japan"),
            (r"[_-]?(eur?|europe)$", "Europe"),
            (r"[_-]?(asia?)$", "Asia"),
            (r"[_-]?(world|wld)$", "World"),
            (r"[_-]?(korea?|kor)$", "Korea"),
            (r"[_-]?(taiwan|tw)$", "Taiwan"),
            (r"[_-]?(hispanic|hisp)$", "Hispanic"),
            (r"[_-]?(brazil|br)$", "Brazil"),
        ]

        for pattern, region in region_patterns:
            if re.search(pattern, name):
                return region

        # Check description for region in parentheses
        desc_patterns = [
            (r"\(usa\)", "USA"),
            (r"\(us\)", "USA"),
            (r"\(japan\)", "Japan"),
            (r"\(europe\)", "Europe"),
            (r"\(world\)", "World"),
            (r"\(asia\)", "Asia"),
            (r"\(korea\)", "Korea"),
        ]

        for pattern, region in desc_patterns:
            if re.search(pattern, desc):
                return region

        return None

    def _extract_revision(self, game: DATGame) -> str | None:
        """Extract revision from game name.

        Args:
            game: DATGame to extract revision from

        Returns:
            Revision string or None
        """
        name = game.name.lower()

        # Check for revision patterns
        rev_patterns = [
            (r"r(\d+)$", r"r\1"),  # sf2r1 -> r1
            (r"rev(\d+)$", r"rev\1"),  # sf2rev1 -> rev1
            (r"v(\d+)$", r"v\1"),  # sf2v1 -> v1
            (r"(\d+)$", r"\1"),  # sf2ce1 -> 1 (version number at end)
        ]

        for pattern, _replacement in rev_patterns:
            match = re.search(pattern, name)
            if match:
                return match.group(0)

        return None

    def get_region_priority(self, region: str | None) -> int:
        """Get priority score for a region.

        Higher score = better for English-speaking users.

        Args:
            region: Region string

        Returns:
            Priority score (0-100)
        """
        if not region:
            return 50  # Unknown region gets middle priority

        return REGION_PRIORITY.get(region.lower(), 50)


def classify_arcade_game(game: DATGame) -> ArcadeClassification:
    """Convenience function to classify a single game.

    Args:
        game: DATGame to classify

    Returns:
        ArcadeClassification
    """
    classifier = ArcadeClassifier()
    return classifier.classify(game)
