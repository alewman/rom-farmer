"""Filter arcade ROMs using arcade-specific filtering.

This stage applies arcade-specific filtering rules:
- Working games only (driver_status = good)
- 1G1R selection with region priority
- Optional essential hacks/bootlegs
- BIOS inclusion

Different from console filtering:
- Uses parent/clone relationships from DAT
- Considers driver_status for working detection
- Handles cultural importance of certain bootlegs
"""

import time
from pathlib import Path
from typing import Dict, List, Optional

from .base import Stage, StageContext, StageResult, StageStatus, StagePhase
from ..dat_parser import DATFile, DATParser
from ..arcade.classifier import ArcadeClassifier
from ..arcade.filter import ArcadeFilter, ArcadeFilterConfig, ArcadeFilterMode


class FilterArcadeStage(Stage):
    PHASE = StagePhase.PLAN

    """Filter arcade ROMs using arcade-specific rules."""

    def __init__(self):
        """Initialize arcade filter stage."""
        super().__init__("Filter Arcade")

    def should_skip(self, context: StageContext) -> bool:
        """Skip if not an arcade platform."""
        # Check if this is an arcade platform
        platform_type = getattr(context.config, 'type', None) if context.config else None
        return platform_type != 'arcade'

    def validate_context(self, context: StageContext) -> str | None:
        """Validate context for arcade filtering."""
        if not context.source_dir.exists():
            return f"Source directory not found: {context.source_dir}"
        if not context.dat_file:
            return "DAT file required for arcade filtering"
        return None

    def execute(self, context: StageContext) -> StageResult:
        """Execute arcade filtering.

        Args:
            context: Stage execution context

        Returns:
            StageResult with filtering outcome
        """
        start_time = time.time()

        # Get arcade filter config from platform config
        arcade_config = self._get_arcade_config(context)
        
        self._log(context, f"[cyan]Arcade filter mode: {arcade_config.mode.value}[/cyan]")
        self._log(context, f"  Include hacks: {arcade_config.include_hacks}")
        self._log(context, f"  Include bootlegs: {arcade_config.include_bootlegs}")
        self._log(context, f"  Working only: {arcade_config.include_working_only}")

        # Create classifier and filter
        classifier = ArcadeClassifier()
        arcade_filter = ArcadeFilter(config=arcade_config, classifier=classifier)

        # Parse DAT if not already parsed
        dat = context.dat_file
        if not dat:
            return StageResult(
                status=StageStatus.FAILED,
                message="No DAT file available",
                duration_seconds=time.time() - start_time,
            )

        # Apply driver filter if configured (for systems like Naomi, Model2 that use MAME DAT)
        config = getattr(context, 'platform_config', None)
        driver_filter = None
        if config and hasattr(config, 'dat') and config.dat:
            driver_filter = getattr(config.dat, 'filter_driver', None)
        
        if driver_filter:
            # Filter games by driver/sourcefile
            original_count = len(dat.games)
            filtered_games = [
                game for game in dat.games
                if game.sourcefile and driver_filter.lower() in game.sourcefile.lower()
            ]
            self._log(context, f"[cyan]Driver filter: {driver_filter}[/cyan]")
            self._log(context, f"  Filtered {original_count:,} -> {len(filtered_games):,} games")
            
            # Create filtered DAT for arcade filter
            from ..dat_parser import DATFile
            dat = DATFile(
                name=dat.name,
                description=dat.description,
                version=dat.version,
                author=dat.author,
                dat_type=dat.dat_type,
                games=filtered_games,
                source_file=dat.source_file,
            )

        # Run filter
        self._log(context, f"[cyan]Filtering {len(dat.games)} games...[/cyan]")
        filter_results = arcade_filter.filter_dat(dat)

        # Count results
        selected = [r for r in filter_results if r.selected]
        rejected = [r for r in filter_results if not r.selected]
        
        self._log(context, f"  Selected: {len(selected):,} games")
        self._log(context, f"  Rejected: {len(rejected):,} games")

        # Store selected games in context for next stages
        context.selected_games = {r.game.name for r in selected}
        context.arcade_filter_results = filter_results
        
        # Create a filtered DAT for downstream stages
        context.filtered_dat = self._create_filtered_dat(dat, selected)

        # Log clone type breakdown
        from collections import Counter
        type_counts = Counter(r.classification.clone_type.value for r in selected)
        self._log(context, "[cyan]By clone type:[/cyan]")
        for clone_type, count in type_counts.most_common():
            self._log(context, f"  {clone_type}: {count:,}")

        # Filter source files to only selected games
        original_count = len(context.source_files)
        context.source_files = [
            f for f in context.source_files
            if f.stem in context.selected_games
        ]
        matched_count = len(context.source_files)

        self._log(context, f"[cyan]Source file matching:[/cyan]")
        self._log(context, f"  Source files: {original_count:,}")
        self._log(context, f"  Matched to selected games: {matched_count:,}")
        self._log(context, f"  Missing: {len(selected) - matched_count:,}")

        duration = time.time() - start_time

        return StageResult(
            status=StageStatus.SUCCESS,
            message=f"Selected {len(selected)} games from {len(dat.games)}",
            files_processed=original_count,
            files_matched=matched_count,
            duration_seconds=duration,
            details={
                "total_games": len(dat.games),
                "selected": len(selected),
                "rejected": len(rejected),
                "matched_files": matched_count,
                "missing_files": len(selected) - matched_count,
            },
        )

    def _get_arcade_config(self, context: StageContext) -> ArcadeFilterConfig:
        """Extract arcade filter config from platform config.

        Args:
            context: Stage context

        Returns:
            ArcadeFilterConfig for this platform
        """
        # Default config
        config = ArcadeFilterConfig()

        # Get from platform config if available (use platform_config first, then config)
        platform_cfg = getattr(context, 'platform_config', None) or getattr(context, 'config', None)
        if platform_cfg:
            arcade_section = getattr(platform_cfg, 'arcade_filter', None)
            if arcade_section:
                # Map mode string to enum
                mode_str = arcade_section.get('mode', 'relaxed')
                mode_map = {
                    'strict': ArcadeFilterMode.STRICT,
                    'relaxed': ArcadeFilterMode.RELAXED,
                    'complete': ArcadeFilterMode.COMPLETE,
                    'all': ArcadeFilterMode.ALL,
                }
                config.mode = mode_map.get(mode_str, ArcadeFilterMode.RELAXED)
                
                # Map boolean options
                config.include_hacks = arcade_section.get('include_hacks', True)
                config.include_bootlegs = arcade_section.get('include_bootlegs', False)
                config.include_prototypes = arcade_section.get('include_prototypes', True)
                config.include_homebrew = arcade_section.get('include_homebrew', False)
                config.include_working_only = arcade_section.get('include_working_only', True)
                
                # Region priority
                region_priority = arcade_section.get('region_priority', [])
                if region_priority:
                    config.region_priority = region_priority
            
            # Check DAT section for filter_driver, filter_romof, and exclude_romof
            dat_section = getattr(platform_cfg, 'dat', None)
            if dat_section:
                filter_driver = getattr(dat_section, 'filter_driver', None)
                if filter_driver:
                    config.filter_driver = filter_driver
                filter_romof = getattr(dat_section, 'filter_romof', None)
                if filter_romof:
                    config.filter_romof = filter_romof
                exclude_romof = getattr(dat_section, 'exclude_romof', None)
                if exclude_romof:
                    config.exclude_romof = exclude_romof

        return config

    def _create_filtered_dat(self, original_dat: DATFile, selected_results) -> DATFile:
        """Create a new DAT file with only selected games.

        Args:
            original_dat: Original DAT file
            selected_results: List of FilteredGame results that were selected

        Returns:
            New DATFile with only selected games
        """
        selected_names = {r.game.name for r in selected_results}
        filtered_games = [g for g in original_dat.games if g.name in selected_names]

        return DATFile(
            name=original_dat.name,
            description=f"{original_dat.description} (Filtered)",
            version=original_dat.version,
            author=original_dat.author,
            games=filtered_games,
            dat_type=original_dat.dat_type,
        )
