"""
Filter games across platforms within a generation (1G1Gen).

This stage implements "1 Game 1 Generation" deduplication, which removes games
that appear on multiple platforms in the same console generation, keeping only
the version from the highest priority platform.

This is designed for disc-based systems where games were commonly ported across
platforms (PSX/Saturn, PS2/GC/Xbox, PS3/360/Wii). It significantly reduces storage
requirements for multi-platform builds while preserving platform exclusives.

Example Gen 6 (PS2 > GameCube > Xbox):
    Input:
        - PS2: 2,556 games
        - GameCube: 595 games  
        - Xbox: 975 games
        Total: 4,126 games
        
    After 1G1Gen filtering:
        - PS2: 2,556 games (unchanged - highest priority)
        - GameCube: ~250 games (exclusives only)
        - Xbox: ~200 games (exclusives only)
        Total: ~3,000 games
        Savings: ~2.3 TB
"""

import time
from pathlib import Path
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from collections import defaultdict
import logging

from ..cross_platform.game_normalizer import GameNameNormalizer, NormalizedGame
from .base import Stage, StageContext, StageResult, StageStatus, StagePhase

logger = logging.getLogger(__name__)


@dataclass
class GenerationConfig:
    """Configuration for a console generation.
    
    Attributes:
        name: Generation identifier (gen5, gen6, gen7, etc.)
        label: Human-readable label
        platforms: List of platform names in priority order (first = highest priority)
        enabled: Whether this generation filter is enabled
    """
    
    name: str
    label: str
    platforms: List[str]  # Ordered by priority (first = highest)
    enabled: bool = True


class FilterGenerationStage(Stage):
    PHASE = StagePhase.PLAN

    """Filter games across platforms within a generation (1G1Gen).
    
    This stage runs AFTER per-platform 1G1R filtering as a post-processing step.
    Each platform has already selected its best versions; now we deduplicate
    across platforms based on priority.
    
    Workflow:
        1. Load all output files from each platform in the generation
        2. Normalize game names to identify cross-platform matches
        3. For each game that exists on multiple platforms:
           - Keep the version from the highest priority platform
           - Remove versions from lower priority platforms
        4. Respect rescue lists (don't remove rescued games)
        
    Result: Lower priority platforms become "exclusives only" builds.
    """
    
    def __init__(self, generation_config: GenerationConfig, rescue_lists: Optional[Dict[str, Set[str]]] = None):
        """Initialize generation filter stage.
        
        Args:
            generation_config: Generation configuration with platform priorities
            rescue_lists: Optional dict of platform -> set of rescued game names
        """
        super().__init__(f"Filter Generation: {generation_config.label}")
        self.generation_config = generation_config
        self.normalizer = GameNameNormalizer()
        self.rescue_lists = rescue_lists or {}
        
        logger.info(f"Initialized generation filter: {generation_config.name}")
        logger.info(f"  Platform priority: {' > '.join(generation_config.platforms)}")
        if self.rescue_lists:
            total_rescued = sum(len(games) for games in self.rescue_lists.values())
            logger.info(f"  Rescue lists loaded: {total_rescued} protected games")
    
    def should_skip(self, context: StageContext) -> bool:
        """Skip if generation filtering not enabled or only one platform."""
        return (
            not self.generation_config.enabled or
            len(self.generation_config.platforms) < 2
        )
    
    def execute(self, context: StageContext) -> StageResult:
        """Execute generation-based filtering.
        
        Args:
            context: Stage context (generation filters use different context)
            
        Returns:
            StageResult with filtering statistics
        """
        start_time = time.time()
        
        if self.should_skip(context):
            return StageResult(
                status=StageStatus.SKIPPED,
                message="Generation filtering disabled or single platform"
            )
        
        self._log(context, f"[cyan]Filtering games across generation platforms...[/cyan]")
        self._log(context, f"  Generation: {self.generation_config.label}")
        self._log(context, f"  Platform priority: {' > '.join(self.generation_config.platforms)}")
        
        # Load game files from all platforms in this generation
        platform_files = self._load_platform_files(context)
        
        if not platform_files:
            return StageResult(
                status=StageStatus.SKIPPED,
                message="No game files found for generation platforms"
            )
        
        # Normalize all game names for cross-platform matching
        normalized_games = self._normalize_all_games(platform_files)
        
        # Find games that appear on multiple platforms
        duplicates = self._find_cross_platform_duplicates(normalized_games)
        
        self._log(context, f"  Found {len(duplicates)} games across multiple platforms")
        
        # Determine which games to remove based on platform priority
        to_remove = self._select_games_to_remove(duplicates)
        
        # Apply rescue lists — swap keeper so rescued platform keeps the game
        # and the original keeper's version is removed instead
        to_remove = self._apply_rescue_lists(to_remove, normalized_games, duplicates)
        
        # Remove the selected game files
        removed_count = self._remove_games(context, to_remove)
        
        # Log detailed statistics
        self._log_statistics(context, platform_files, duplicates, to_remove)
        
        duration = time.time() - start_time
        
        return StageResult(
            status=StageStatus.SUCCESS,
            message=f"Removed {removed_count} duplicate games across platforms",
            files_processed=sum(len(files) for files in platform_files.values()),
            files_matched=removed_count,
            duration_seconds=duration
        )
    
    def _load_platform_files(self, context: StageContext) -> Dict[str, List[Path]]:
        """Load game files from each platform's output directory.
        
        Args:
            context: Stage context with output directory information
            
        Returns:
            Dict mapping platform name -> list of game file paths
        """
        platform_files = {}
        
        # Get base output directory from context
        # This should be the generation build output, e.g., output/gen5-dedupe-batocera/
        base_output = getattr(context, 'generation_output_dir', context.output_dir)
        
        for platform in self.generation_config.platforms:
            # Look for platform subdirectory
            platform_dir = base_output / platform
            
            if not platform_dir.exists():
                logger.warning(f"Platform directory not found: {platform_dir}")
                continue
            
            # Find game files (CHD, RVZ, ISO, etc.)
            game_files = []
            for pattern in ['*.chd', '*.rvz', '*.iso', '*.xiso', '*.cue', '*.m3u']:
                game_files.extend(platform_dir.glob(pattern))
            
            # Also handle folder-based platforms (PS3, etc.)
            if not game_files:
                subdirs = [
                    d for d in platform_dir.iterdir()
                    if d.is_dir() and d.name not in ('Best Games', '_Best Games')
                ]
                if subdirs:
                    game_files = subdirs
            
            if game_files:
                platform_files[platform] = game_files
                logger.info(f"  {platform}: {len(game_files)} games")
            else:
                logger.warning(f"  {platform}: No game files found")
        
        return platform_files
    
    def _normalize_all_games(
        self,
        platform_files: Dict[str, List[Path]]
    ) -> Dict[str, List[NormalizedGame]]:
        """Normalize all game names for cross-platform matching.
        
        Args:
            platform_files: Dict of platform -> game file paths
            
        Returns:
            Dict mapping platform -> list of normalized games
        """
        normalized = {}
        
        for platform, files in platform_files.items():
            platform_games = []
            for file_path in files:
                # Use stem to strip extension (.iso, .chd, .ps3, etc.)
                game_name = file_path.stem
                
                # Normalize the game name
                normalized_game = self.normalizer.normalize(
                    game_name,
                    platform,
                    str(file_path)
                )
                platform_games.append(normalized_game)
            
            normalized[platform] = platform_games
            logger.debug(f"Normalized {len(platform_games)} games for {platform}")
        
        return normalized
    
    def _find_cross_platform_duplicates(
        self,
        normalized_games: Dict[str, List[NormalizedGame]]
    ) -> Dict[str, Dict[str, NormalizedGame]]:
        """Find games that exist on multiple platforms.
        
        Args:
            normalized_games: Dict of platform -> normalized games
            
        Returns:
            Dict mapping match_key -> {platform: NormalizedGame}
            Only includes games that appear on 2+ platforms.
        """
        # Build index: match_key -> {platform: game}
        game_index: Dict[str, Dict[str, NormalizedGame]] = defaultdict(dict)
        
        for platform, games in normalized_games.items():
            for game in games:
                match_key = game.match_key()
                game_index[match_key][platform] = game
        
        # Filter to only duplicates (appear on 2+ platforms)
        duplicates = {
            match_key: platforms
            for match_key, platforms in game_index.items()
            if len(platforms) >= 2
        }
        
        logger.info(f"Found {len(duplicates)} cross-platform duplicate games")
        
        # Log some examples for debugging
        if duplicates:
            examples = list(duplicates.items())[:5]
            logger.debug("Example duplicates:")
            for match_key, platforms in examples:
                platform_list = ', '.join(platforms.keys())
                logger.debug(f"  {match_key}: {platform_list}")
        
        return duplicates
    
    def _select_games_to_remove(
        self,
        duplicates: Dict[str, Dict[str, NormalizedGame]]
    ) -> Set[Path]:
        """Determine which game files to remove based on platform priority.
        
        For each duplicate game:
        - Keep the version from the highest priority platform
        - Mark lower priority versions for removal
        
        Args:
            duplicates: Dict of match_key -> {platform: NormalizedGame}
            
        Returns:
            Set of file paths to remove
        """
        to_remove = set()
        
        for match_key, platforms in duplicates.items():
            # Find highest priority platform that has this game
            keeper_platform = None
            for priority_platform in self.generation_config.platforms:
                if priority_platform in platforms:
                    keeper_platform = priority_platform
                    break
            
            if not keeper_platform:
                logger.warning(f"No keeper platform found for {match_key}")
                continue
            
            # Remove all versions except the keeper
            keeper_game = platforms[keeper_platform]
            logger.debug(f"Keeping {match_key} from {keeper_platform}: {keeper_game.original_name}")
            
            for platform, game in platforms.items():
                if platform != keeper_platform:
                    # Mark this game file for removal
                    if game.file_path:
                        file_path = Path(game.file_path)
                        to_remove.add(file_path)
                        logger.debug(f"  Removing {platform} version: {game.original_name}")
        
        logger.info(f"Selected {len(to_remove)} files for removal")
        return to_remove
    
    def _apply_rescue_lists(
        self,
        to_remove: Set[Path],
        normalized_games: Dict[str, List[NormalizedGame]],
        duplicates: Dict[str, Dict[str, NormalizedGame]],
    ) -> Set[Path]:
        """Apply rescue lists — swap keeper so the best version survives.

        When a game is rescued on platform B, the original keeper (platform A)
        is removed instead, so only ONE copy of each game remains per generation.

        Args:
            to_remove: Set of file paths marked for removal
            normalized_games: All normalized games by platform
            duplicates: Cross-platform duplicate groups

        Returns:
            Updated removal set with swaps applied
        """
        if not self.rescue_lists:
            return to_remove
        
        rescued_count = 0
        
        # Build reverse lookup: file_path -> (normalized_game, match_key)
        file_to_game = {}
        for platform, games in normalized_games.items():
            for game in games:
                if game.file_path:
                    file_to_game[Path(game.file_path)] = game
        
        # Check each file marked for removal against rescue lists
        for file_path in list(to_remove):
            game = file_to_game.get(file_path)
            if not game:
                continue
            
            # Check if this game is in the rescue list for its platform
            platform_rescues = self.rescue_lists.get(game.platform, set())
            
            # Check both normalized and original name
            if not (game.normalized_name.lower() in platform_rescues or
                    game.original_name.lower() in platform_rescues):
                continue
            
            # Found a rescue — swap: keep this game, remove the original keeper
            to_remove.discard(file_path)
            rescued_count += 1
            
            # Find the duplicate group this game belongs to
            match_key = game.match_key()
            dup_group = duplicates.get(match_key, {})
            
            # Find the current keeper (highest priority platform in this group)
            for priority_platform in self.generation_config.platforms:
                if priority_platform in dup_group:
                    keeper_game = dup_group[priority_platform]
                    if keeper_game.file_path and priority_platform != game.platform:
                        keeper_path = Path(keeper_game.file_path)
                        to_remove.add(keeper_path)
                        logger.info(
                            f"Rescued {game.platform}/{game.original_name} — "
                            f"removing {priority_platform} version instead"
                        )
                    break
        
        if rescued_count > 0:
            logger.info(f"Rescued {rescued_count} games (swapped keeper platform)")
        
        return to_remove
    
    def _remove_games(self, context: StageContext, to_remove: Set[Path]) -> int:
        """Remove the selected game files.
        
        Args:
            context: Stage context
            to_remove: Set of file paths to remove
            
        Returns:
            Number of files actually removed
        """
        removed_count = 0
        
        for file_path in to_remove:
            try:
                if file_path.exists():
                    if file_path.is_dir():
                        # Folder-based game (PS3, etc.) — remove entire tree
                        import shutil
                        shutil.rmtree(file_path)
                        removed_count += 1
                        logger.debug(f"Removed directory: {file_path.name}")
                    else:
                        # Also remove associated files (CUE for BIN, M3U for multi-disc, etc.)
                        associated_files = self._find_associated_files(file_path)
                        
                        # Remove main file
                        file_path.unlink()
                        removed_count += 1
                        logger.debug(f"Removed: {file_path.name}")
                        
                        # Remove associated files
                        for assoc_file in associated_files:
                            if assoc_file.exists():
                                assoc_file.unlink()
                                logger.debug(f"  Removed associated: {assoc_file.name}")
                else:
                    logger.warning(f"File not found for removal: {file_path}")
            except Exception as e:
                logger.error(f"Error removing {file_path}: {e}")
        
        return removed_count
    
    def _find_associated_files(self, file_path: Path) -> List[Path]:
        """Find associated files for a game (CUE, M3U, metadata, etc.).
        
        Args:
            file_path: Main game file path
            
        Returns:
            List of associated file paths
        """
        associated = []
        base_name = file_path.stem
        parent_dir = file_path.parent
        
        # Look for common associated files
        patterns = [
            f"{base_name}.cue",
            f"{base_name}.m3u",
            f"{base_name}.txt",  # Metadata/readme
            f"{base_name}.xml",  # Metadata
            f"{base_name}.jpg",  # Box art
            f"{base_name}.png",  # Box art
        ]
        
        for pattern in patterns:
            assoc_file = parent_dir / pattern
            if assoc_file.exists() and assoc_file != file_path:
                associated.append(assoc_file)
        
        return associated
    
    def _log_statistics(
        self,
        context: StageContext,
        platform_files: Dict[str, List[Path]],
        duplicates: Dict[str, Dict[str, NormalizedGame]],
        to_remove: Set[Path]
    ):
        """Log detailed statistics about the filtering.
        
        Args:
            context: Stage context
            platform_files: Original platform files
            duplicates: Found duplicates
            to_remove: Files marked for removal
        """
        total_before = sum(len(files) for files in platform_files.values())
        total_after = total_before - len(to_remove)
        percentage_removed = (len(to_remove) / total_before * 100) if total_before > 0 else 0
        
        self._log(context, f"[green]Generation filtering complete:[/green]")
        self._log(context, f"  Total games before: {total_before}")
        self._log(context, f"  Cross-platform duplicates: {len(duplicates)}")
        self._log(context, f"  Games removed: {len(to_remove)} ({percentage_removed:.1f}%)")
        self._log(context, f"  Unique games after: {total_after}")
        
        # Per-platform breakdown
        self._log(context, f"  Per-platform results:")
        for platform in self.generation_config.platforms:
            files = platform_files.get(platform, [])
            before = len(files)
            
            # Count how many from this platform were removed
            removed = sum(1 for path in to_remove if path.parent.name == platform)
            after = before - removed
            percentage = (after / before * 100) if before > 0 else 0
            
            self._log(context, f"    {platform:12s}: {before:4d} -> {after:4d} ({percentage:5.1f}% retained)")
