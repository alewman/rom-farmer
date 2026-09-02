"""
1G1R (One Game One ROM) filtering for ROM collections.

Filters DAT game entries to select the best version of each game based on:
- Region priorities (USA > Europe > Japan > World, etc.)
- Language preferences
- Parent vs Clone relationships
- Version/revision preferences
"""

from collections import defaultdict
from dataclasses import dataclass

from romfarmer.catalog.database import DatGame


@dataclass
class FilterStats:
    """Statistics from 1G1R filtering."""

    total_games: int = 0
    unique_games: int = 0
    filtered_games: int = 0
    parents_selected: int = 0
    clones_selected: int = 0
    duplicates_removed: int = 0


class OneGameOneRomFilter:
    """
    Filter DAT games to select one ROM per game based on preferences.

    This implements the "1G1R" (One Game One ROM) concept popular in ROM
    collecting communities, reducing collections to one version of each game.
    """

    # Default region priority (higher score = higher priority)
    DEFAULT_REGION_PRIORITY = {
        "USA": 100,
        "World": 95,
        "Europe": 90,
        "Japan": 85,
        "Asia": 80,
        "Korea": 75,
        "China": 70,
        "Brazil": 65,
        "Australia": 60,
        "Germany": 55,
        "France": 54,
        "Spain": 53,
        "Italy": 52,
        "Netherlands": 51,
        "Sweden": 50,
        "Canada": 45,
        "Unknown": 0,
    }

    # Default language priority
    DEFAULT_LANGUAGE_PRIORITY = {
        "En": 100,  # English
        "Ja": 85,  # Japanese
        "Fr": 80,  # French
        "De": 75,  # German
        "Es": 70,  # Spanish
        "It": 65,  # Italian
        "Pt": 60,  # Portuguese
        "Nl": 55,  # Dutch
        "Sv": 50,  # Swedish
        "No": 45,  # Norwegian
        "Da": 40,  # Danish
        "Fi": 35,  # Finnish
        "Zh": 30,  # Chinese
        "Ko": 25,  # Korean
    }

    def __init__(
        self,
        region_priority: list[str] | None = None,
        language_priority: list[str] | None = None,
        prefer_parents: bool = True,
        prefer_later_revisions: bool = True,
    ):
        """
        Initialize the 1G1R filter.

        Args:
            region_priority: Ordered list of preferred regions (highest first)
            language_priority: Ordered list of preferred languages (highest first)
            prefer_parents: If True, prefer parent ROMs over clones when scores tie
            prefer_later_revisions: If True, prefer later revisions (Rev 2 > Rev 1)
        """
        self.prefer_parents = prefer_parents
        self.prefer_later_revisions = prefer_later_revisions

        # Build region priority map
        if region_priority:
            self.region_priority = {region: 100 - i * 5 for i, region in enumerate(region_priority)}
        else:
            self.region_priority = self.DEFAULT_REGION_PRIORITY.copy()

        # Build language priority map
        if language_priority:
            self.language_priority = {lang: 100 - i * 5 for i, lang in enumerate(language_priority)}
        else:
            self.language_priority = self.DEFAULT_LANGUAGE_PRIORITY.copy()

    def filter_games(self, games: list[DatGame]) -> tuple[list[DatGame], FilterStats]:
        """
        Filter games to one ROM per unique game.

        Args:
            games: List of DatGame entries to filter

        Returns:
            Tuple of (filtered games list, statistics)
        """
        stats = FilterStats(total_games=len(games))

        # Group games by base name (removing region/language/version tags)
        game_groups = self._group_games_by_base_name(games)
        stats.unique_games = len(game_groups)

        # Select best game from each group
        filtered = []
        for _base_name, group in game_groups.items():
            best_game = self._select_best_game(group)
            filtered.append(best_game)

            # Update stats
            if self._is_parent(best_game):
                stats.parents_selected += 1
            else:
                stats.clones_selected += 1

        stats.filtered_games = len(filtered)
        stats.duplicates_removed = stats.total_games - stats.filtered_games

        return filtered, stats

    def _group_games_by_base_name(self, games: list[DatGame]) -> dict[str, list[DatGame]]:
        """
        Group games by their base name (without region/language/version tags).

        For example:
        - "Super Mario Bros. (USA)" -> "Super Mario Bros."
        - "Super Mario Bros. (Europe)" -> "Super Mario Bros."
        - "Super Mario Bros. (Japan)" -> "Super Mario Bros."
        """
        groups = defaultdict(list)

        for game in games:
            base_name = self._extract_base_name(game.name or "")
            groups[base_name].append(game)

        return dict(groups)

    def _extract_base_name(self, name: str) -> str:
        """
        Extract the base game name without region/language/version tags.

        Removes patterns like:
        - (USA), (Europe), (Japan), etc.
        - (En), (En,Fr), etc.
        - (Rev 1), (Rev A), (Beta), (Proto), etc.
        - [!], [a], [b], etc.
        """
        # Remove parenthetical tags
        import re

        # Common patterns to remove
        patterns = [
            r"\([^)]*\)",  # Anything in parentheses
            r"\[[^\]]*\]",  # Anything in brackets
            r"\{[^}]*\}",  # Anything in braces
        ]

        result = name
        for pattern in patterns:
            result = re.sub(pattern, "", result)

        # Clean up extra whitespace
        result = " ".join(result.split())
        result = result.strip(" -,")

        return result

    def _select_best_game(self, games: list[DatGame]) -> DatGame:
        """
        Select the best game from a group based on scoring criteria.

        Scoring factors (in order of importance):
        1. Region priority
        2. Language priority
        3. Parent vs Clone (if prefer_parents=True)
        4. Revision number (if prefer_later_revisions=True)
        5. Alphabetical (for ties)
        """
        if len(games) == 1:
            return games[0]

        # Score each game
        scored_games = [(self._score_game(game), game) for game in games]

        # Sort by score (descending), then by name (ascending) for ties
        scored_games.sort(key=lambda x: (-x[0], x[1].name or ""))

        return scored_games[0][1]

    def _score_game(self, game: DatGame) -> int:
        """
        Calculate a score for a game based on preferences.

        Higher score = more preferred.
        """
        score = 0
        name = game.name or ""

        # Region score (most important, weight: 1000)
        region_score = self._get_region_score(name)
        score += region_score * 1000

        # Language score (weight: 100)
        language_score = self._get_language_score(name)
        score += language_score * 100

        # Parent vs Clone score (weight: 10)
        if self.prefer_parents and self._is_parent(game):
            score += 10

        # Revision score (weight: 1)
        if self.prefer_later_revisions:
            revision_score = self._get_revision_score(name)
            score += revision_score

        return score

    def _get_region_score(self, name: str) -> int:
        """Extract region from name and return priority score."""
        import re

        # Look for region tags like (USA), (Europe), etc.
        region_match = re.search(r"\(([^)]+)\)", name)
        if not region_match:
            return self.region_priority.get("Unknown", 0)

        region_tag = region_match.group(1)

        # Handle multi-region (e.g., "USA, Europe")
        regions = [r.strip() for r in region_tag.split(",")]

        # Return highest priority region
        max_score = 0
        for region in regions:
            score = self.region_priority.get(region, 0)
            max_score = max(max_score, score)

        return max_score

    def _get_language_score(self, name: str) -> int:
        """Extract language from name and return priority score."""
        import re

        # Look for language tags like (En), (En,Fr), etc.
        lang_match = re.search(r"\(([A-Z][a-z](?:,[A-Z][a-z])*)\)", name)
        if not lang_match:
            return 0

        lang_tag = lang_match.group(1)
        languages = [lang.strip() for lang in lang_tag.split(",")]

        # Return highest priority language
        max_score = 0
        for lang in languages:
            score = self.language_priority.get(lang, 0)
            max_score = max(max_score, score)

        return max_score

    def _get_revision_score(self, name: str) -> int:
        """Extract revision number and return score."""
        import re

        # Look for revision patterns like (Rev 1), (Rev A), (v1.1), etc.
        patterns = [
            r"Rev\s+(\d+)",
            r"Rev\s+([A-Z])",
            r"v(\d+)\.(\d+)",
            r"v(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                # Convert to numeric score
                if pattern.startswith("Rev\\s+([A-Z])"):
                    # Rev A=1, Rev B=2, etc.
                    return ord(match.group(1).upper()) - ord("A") + 1
                elif "\\." in pattern:
                    # v1.1 = 11, v2.3 = 23
                    major = int(match.group(1))
                    minor = int(match.group(2))
                    return major * 10 + minor
                else:
                    # Simple number
                    return int(match.group(1))

        return 0

    def _is_parent(self, game: DatGame) -> bool:
        """
        Check if a game is a parent (not a clone).

        Parent games typically don't have tags like [a], [b], [!], etc.
        """
        name = game.name or ""

        # Check for clone indicators
        clone_indicators = ["[a]", "[b]", "[c]", "[!]", "[h]", "[t]", "[f]", "[p]", "[o]"]
        for indicator in clone_indicators:
            if indicator.lower() in name.lower():
                return False

        return True

    def get_filtered_by_dat(
        self,
        games: list[DatGame],
        dat_name: str | None = None,
    ) -> tuple[list[DatGame], FilterStats]:
        """
        Filter games from a specific DAT or all DATs.

        Args:
            games: List of games to filter
            dat_name: Optional DAT name to filter within

        Returns:
            Tuple of (filtered games, statistics)
        """
        # Filter by DAT if specified
        if dat_name:
            games = [g for g in games if g.dat_file and g.dat_file.name == dat_name]

        return self.filter_games(games)
