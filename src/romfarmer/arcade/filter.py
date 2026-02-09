"""Arcade-aware 1G1R filter.

Provides filtering modes for arcade systems:
- Strict 1G1R: Only parents, best regional variant per game
- Relaxed 1G1R: Parents + essential hacks + best regional variants
- Working Only: Filter out non-working games (preliminary drivers)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from ..dat_parser.models import ArcadeCloneType, DATFile, DATGame
from .classifier import ArcadeClassification, ArcadeClassifier, CloneImportance


class ArcadeFilterMode(str, Enum):
    """Filtering mode for arcade games."""

    STRICT = "strict"  # Parents only, one per game
    RELAXED = "relaxed"  # Parents + essential/recommended clones
    COMPLETE = "complete"  # All working games
    ALL = "all"  # Everything including non-working


@dataclass
class ArcadeFilterConfig:
    """Configuration for arcade filtering."""

    mode: ArcadeFilterMode = ArcadeFilterMode.RELAXED
    include_working_only: bool = True
    include_bootlegs: bool = False
    include_hacks: bool = True  # Include culturally important hacks
    include_prototypes: bool = True
    include_homebrew: bool = False
    include_demos: bool = False
    preferred_regions: list[str] = None  # Order of preference
    filter_driver: str = None  # Filter by driver/sourcefile (e.g., 'neogeo')
    filter_romof: str = None  # Filter by romof/BIOS (e.g., 'naomi2' for Naomi 2 games)
    exclude_romof: list[str] = None  # Exclude games with these BIOS dependencies

    def __post_init__(self):
        if self.preferred_regions is None:
            self.preferred_regions = ["World", "USA", "Europe", "Asia", "Japan"]


@dataclass
class FilteredGame:
    """Result of filtering a game."""

    game: DATGame
    classification: ArcadeClassification
    selected: bool
    reason: str


class ArcadeFilter:
    """Filter arcade games based on 1G1R rules and preferences."""

    def __init__(
        self,
        config: Optional[ArcadeFilterConfig] = None,
        classifier: Optional[ArcadeClassifier] = None,
    ):
        """Initialize arcade filter.

        Args:
            config: Filter configuration
            classifier: Arcade classifier instance
        """
        self.config = config or ArcadeFilterConfig()
        self.classifier = classifier or ArcadeClassifier()

    def filter_dat(self, dat: DATFile) -> list[FilteredGame]:
        """Filter all games in a DAT file.

        Args:
            dat: Parsed DAT file

        Returns:
            List of FilteredGame results
        """
        # Pre-filter: exclude device entries (not actual games)
        games_to_filter = [
            g for g in dat.games
            if not g.is_device and not (g.sourcefile and g.sourcefile.startswith('devices/'))
        ]
        
        # Pre-filter by driver if specified
        if self.config.filter_driver:
            driver_pattern = self.config.filter_driver.lower()
            games_to_filter = [
                g for g in games_to_filter
                if g.sourcefile and driver_pattern in g.sourcefile.lower()
            ]
        
        # Pre-filter by romof (BIOS dependency) if specified
        if self.config.filter_romof:
            romof_pattern = self.config.filter_romof.lower()
            games_to_filter = [
                g for g in games_to_filter
                if g.romof and g.romof.lower() == romof_pattern
            ]
        
        # Exclude games with specific BIOS dependencies
        if self.config.exclude_romof:
            exclude_patterns = [p.lower() for p in self.config.exclude_romof]
            games_to_filter = [
                g for g in games_to_filter
                if not g.romof or g.romof.lower() not in exclude_patterns
            ]
        
        # Classify all games
        classified = [
            (game, self.classifier.classify(game))
            for game in games_to_filter
        ]

        # Group by parent
        parent_groups: dict[str, list[tuple[DATGame, ArcadeClassification]]] = {}

        for game, classification in classified:
            parent_name = game.cloneof or game.name
            if parent_name not in parent_groups:
                parent_groups[parent_name] = []
            parent_groups[parent_name].append((game, classification))

        # Filter each group
        results = []
        for parent_name, group in parent_groups.items():
            group_results = self._filter_group(parent_name, group)
            results.extend(group_results)

        return results

    def _filter_group(
        self,
        parent_name: str,
        group: list[tuple[DATGame, ArcadeClassification]],
    ) -> list[FilteredGame]:
        """Filter a group of games (parent + clones).

        Args:
            parent_name: Name of parent ROM
            group: List of (game, classification) tuples

        Returns:
            List of FilteredGame results
        """
        results = []

        # Separate by clone type
        parent = None
        regionals = []
        revisions = []
        hacks = []
        bootlegs = []
        prototypes = []
        homebrew = []
        demos = []
        bios = []

        for game, classification in group:
            if classification.clone_type == ArcadeCloneType.PARENT:
                parent = (game, classification)
            elif classification.clone_type == ArcadeCloneType.REGIONAL:
                regionals.append((game, classification))
            elif classification.clone_type == ArcadeCloneType.REVISION:
                revisions.append((game, classification))
            elif classification.clone_type == ArcadeCloneType.HACK:
                hacks.append((game, classification))
            elif classification.clone_type == ArcadeCloneType.BOOTLEG:
                bootlegs.append((game, classification))
            elif classification.clone_type == ArcadeCloneType.PROTOTYPE:
                prototypes.append((game, classification))
            elif classification.clone_type == ArcadeCloneType.HOMEBREW:
                homebrew.append((game, classification))
            elif classification.clone_type == ArcadeCloneType.DEMO:
                demos.append((game, classification))
            elif classification.clone_type == ArcadeCloneType.BIOS:
                bios.append((game, classification))

        # Always include BIOS
        for game, classification in bios:
            results.append(FilteredGame(
                game=game,
                classification=classification,
                selected=True,
                reason="BIOS required",
            ))

        # Select parent or best regional variant
        selected_main = self._select_best_main(parent, regionals, revisions)
        if selected_main:
            game, classification = selected_main
            # Check if working
            if self.config.include_working_only and not classification.is_working:
                results.append(FilteredGame(
                    game=game,
                    classification=classification,
                    selected=False,
                    reason="Non-working (preliminary driver)",
                ))
            else:
                results.append(FilteredGame(
                    game=game,
                    classification=classification,
                    selected=True,
                    reason="Best version selected",
                ))

        # Add rejected main variants
        all_main = [parent] if parent else []
        all_main.extend(regionals)
        all_main.extend(revisions)
        for game, classification in all_main:
            if selected_main and game.name == selected_main[0].name:
                continue  # Already added
            results.append(FilteredGame(
                game=game,
                classification=classification,
                selected=False,
                reason=f"Alternative {classification.clone_type.value} variant",
            ))

        # Handle hacks based on config
        for game, classification in hacks:
            if self.config.mode == ArcadeFilterMode.ALL:
                selected = True
                reason = "All mode - including all"
            elif self.config.mode == ArcadeFilterMode.COMPLETE:
                selected = classification.is_working
                reason = "Working hack" if selected else "Non-working hack"
            elif self.config.include_hacks:
                # When include_hacks=True, include ALL hacks (not just essential/recommended)
                # This gives users all variations so they can see what's available
                selected = classification.is_working if self.config.include_working_only else True
                if classification.importance in (CloneImportance.ESSENTIAL, CloneImportance.RECOMMENDED):
                    reason = f"Important hack ({classification.importance.value})"
                else:
                    reason = "Hack included (include_hacks=True)"
            else:
                selected = False
                reason = "Hack filtered out"

            results.append(FilteredGame(
                game=game,
                classification=classification,
                selected=selected,
                reason=reason,
            ))

        # Handle bootlegs
        for game, classification in bootlegs:
            # Essential/recommended bootlegs (like Rainbow Edition) included with hacks
            if classification.importance in (CloneImportance.ESSENTIAL, CloneImportance.RECOMMENDED):
                if self.config.include_hacks or self.config.mode in (
                    ArcadeFilterMode.COMPLETE,
                    ArcadeFilterMode.ALL,
                ):
                    selected = classification.is_working if self.config.include_working_only else True
                    reason = f"Important bootleg ({classification.importance.value})"
                else:
                    selected = False
                    reason = "Important bootleg but hacks disabled"
            elif self.config.include_bootlegs or self.config.mode == ArcadeFilterMode.ALL:
                selected = classification.is_working if self.config.include_working_only else True
                reason = "Bootleg included"
            else:
                selected = False
                reason = "Bootleg filtered out"

            results.append(FilteredGame(
                game=game,
                classification=classification,
                selected=selected,
                reason=reason,
            ))

        # Handle prototypes
        for game, classification in prototypes:
            if self.config.include_prototypes or self.config.mode in (
                ArcadeFilterMode.COMPLETE,
                ArcadeFilterMode.ALL,
            ):
                selected = classification.is_working if self.config.include_working_only else True
                reason = "Prototype included"
            else:
                selected = False
                reason = "Prototype filtered out"

            results.append(FilteredGame(
                game=game,
                classification=classification,
                selected=selected,
                reason=reason,
            ))

        # Handle homebrew
        for game, classification in homebrew:
            # Quality homebrew (RECOMMENDED) included when include_homebrew=True
            if classification.importance == CloneImportance.RECOMMENDED:
                if self.config.include_homebrew or self.config.mode in (
                    ArcadeFilterMode.COMPLETE,
                    ArcadeFilterMode.ALL,
                ):
                    selected = classification.is_working if self.config.include_working_only else True
                    reason = "Quality homebrew included"
                else:
                    selected = False
                    reason = "Quality homebrew filtered (enable include_homebrew)"
            elif self.config.mode == ArcadeFilterMode.ALL:
                selected = classification.is_working if self.config.include_working_only else True
                reason = "All homebrew included (ALL mode)"
            else:
                selected = False
                reason = "Homebrew filtered out"

            results.append(FilteredGame(
                game=game,
                classification=classification,
                selected=selected,
                reason=reason,
            ))

        # Handle demos
        for game, classification in demos:
            if self.config.include_demos or self.config.mode == ArcadeFilterMode.ALL:
                selected = classification.is_working if self.config.include_working_only else True
                reason = "Demo included"
            else:
                selected = False
                reason = "Demo filtered out"

            results.append(FilteredGame(
                game=game,
                classification=classification,
                selected=selected,
                reason=reason,
            ))

        return results

    def _select_best_main(
        self,
        parent: Optional[tuple[DATGame, ArcadeClassification]],
        regionals: list[tuple[DATGame, ArcadeClassification]],
        revisions: list[tuple[DATGame, ArcadeClassification]],
    ) -> Optional[tuple[DATGame, ArcadeClassification]]:
        """Select the best main version of a game.

        Priority:
        1. Preferred region (World > USA > Europe > Asia > Japan)
        2. Latest revision
        3. Working status
        4. Parent if no better option

        Args:
            parent: Parent game tuple or None
            regionals: List of regional variant tuples
            revisions: List of revision tuples

        Returns:
            Best game tuple or None
        """
        candidates = []

        if parent:
            candidates.append(parent)
        candidates.extend(regionals)
        candidates.extend(revisions)

        if not candidates:
            return None

        # Score each candidate
        def score_candidate(item: tuple[DATGame, ArcadeClassification]) -> tuple:
            game, classification = item

            # Working status is most important
            working_score = 1 if classification.is_working else 0

            # Region priority
            region_score = self.classifier.get_region_priority(classification.region)

            # Prefer latest revision
            revision_score = 0
            if classification.revision:
                # Extract number from revision
                import re
                match = re.search(r'\d+', classification.revision)
                if match:
                    revision_score = int(match.group())

            # Parent gets slight bonus (it's the "official" version)
            parent_score = 1 if classification.clone_type == ArcadeCloneType.PARENT else 0

            return (working_score, region_score, revision_score, parent_score)

        # Sort by score (highest first)
        candidates.sort(key=score_candidate, reverse=True)

        return candidates[0]

    def get_statistics(self, results: list[FilteredGame]) -> dict:
        """Get filtering statistics.

        Args:
            results: List of FilteredGame results

        Returns:
            Statistics dictionary
        """
        total = len(results)
        selected = sum(1 for r in results if r.selected)
        rejected = total - selected

        # Count by clone type
        by_type = {}
        for r in results:
            ct = r.classification.clone_type.value
            if ct not in by_type:
                by_type[ct] = {"total": 0, "selected": 0}
            by_type[ct]["total"] += 1
            if r.selected:
                by_type[ct]["selected"] += 1

        # Count non-working
        non_working = sum(1 for r in results if not r.classification.is_working)

        return {
            "total_games": total,
            "selected": selected,
            "rejected": rejected,
            "non_working": non_working,
            "by_clone_type": by_type,
        }
