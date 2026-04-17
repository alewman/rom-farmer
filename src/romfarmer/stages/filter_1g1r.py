"""Filter ROMs using 1G1R logic without a DAT file."""

import time
from pathlib import Path
from typing import List, Dict

from ..dat.filter import OneGameOneRomFilter
from ..catalog.database import DatGame
from .base import Stage, StageContext, StageResult, StageStatus, StagePhase


class Filter1G1RStage(Stage):
    PHASE = StagePhase.PLAN

    """Filter source ROM files using 1G1R logic without a DAT file.
    
    This stage is useful for:
    1. Systems where no DAT file is available
    2. "Private" or homebrew collections not in standard DATs
    3. Quick builds where strict DAT matching isn't required
    
    It parses filenames to determine:
    - Region (USA, Europe, Japan, etc.)
    - Language (En, Fr, De, etc.)
    - Revision (Rev 1, v1.1, etc.)
    
    And selects the best version of each game based on preferences.
    """

    def __init__(self):
        """Initialize 1G1R filter stage."""
        super().__init__("Filter 1G1R (No-DAT)")

    def should_skip(self, context: StageContext) -> bool:
        """Skip if DAT file is present (FilterDATStage handles that) or no source files."""
        # Only run if NO DAT file is present
        return context.dat_file is not None or not context.source_files

    def execute(self, context: StageContext) -> StageResult:
        """Execute 1G1R filtering.

        Args:
            context: Stage context with source files

        Returns:
            StageResult with filtering results
        """
        start_time = time.time()

        if self.should_skip(context):
            return StageResult(
                status=StageStatus.SKIPPED,
                message="Skipped (DAT file present or no source files)",
            )

        self._log(context, f"[cyan]Filtering {len(context.source_files)} files using 1G1R logic...[/cyan]")

        # Convert source files to DatGame objects for the filter
        games: List[DatGame] = []
        file_map: Dict[str, Path] = {}  # Map game name back to source path

        for file_path in context.source_files:
            # Create a mock DatGame from the filename
            # We use the filename stem as the game name and description
            name = file_path.stem
            game = DatGame(
                name=name,
                description=name,
                rom_name=file_path.name,
                size=file_path.stat().st_size,
                # We don't have CRC/MD5/SHA1 from a DAT, but that's fine for this filter
            )
            games.append(game)
            file_map[name] = file_path

        # Initialize the filter
        # We use default priorities for now, but could pull from config if available
        rom_filter = OneGameOneRomFilter(
            prefer_parents=True,
            prefer_later_revisions=True
        )

        # Run the filter
        filtered_games, stats = rom_filter.filter_games(games)

        self._log(context, f"  Total unique games: {stats.unique_games}")
        self._log(context, f"  Selected games: {len(filtered_games)}")
        self._log(context, f"  Duplicates removed: {stats.duplicates_removed}")

        # Process the results
        context.filtered_files = []
        files_processed = 0
        
        # Create symlinks in work directory
        for game in filtered_games:
            source_path = file_map.get(game.name)
            if source_path and source_path.exists():
                dest_path = context.work_dir / source_path.name
                
                # Create symlink (or copy if symlink fails)
                if not dest_path.exists():
                    try:
                        dest_path.symlink_to(source_path)
                    except (OSError, NotImplementedError):
                        import shutil
                        shutil.copy2(source_path, dest_path)
                
                context.filtered_files.append(dest_path)
                files_processed += 1

        duration = time.time() - start_time
        
        return StageResult(
            status=StageStatus.SUCCESS,
            message=f"Filtered {len(context.source_files)} -> {len(context.filtered_files)} files",
            files_processed=len(context.source_files),
            files_matched=len(context.filtered_files),
            files_skipped=stats.duplicates_removed,
            duration_seconds=duration,
        )
