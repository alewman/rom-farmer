"""Copy arcade ROMs and CHDs to output directory.

This stage handles arcade-specific file copying:
- ROM ZIPs copied/linked directly (no transformation)
- CHD files paired with their parent ROM
- Proper folder structure for MAME-style emulators

Arcade file structure:
    output/
        naomi.zip           # BIOS
        mvsc2.zip           # Game ROM
        mvsc2/
            gdl-0007a.chd   # Game disc (CHD in subfolder)

CHD requirements come from the DAT file's <disk> elements.
"""

import os
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .base import Stage, StageContext, StageResult, StageStatus


class CopyArcadeStage(Stage):
    """Copy arcade ROMs and CHDs to output directory."""

    def __init__(self):
        """Initialize arcade copy stage."""
        super().__init__("Copy Arcade")
        self._use_hardlinks = True

    def should_skip(self, context: StageContext) -> bool:
        """Skip if not an arcade platform."""
        config = getattr(context, 'platform_config', None) or getattr(context, 'config', None)
        platform_type = getattr(config, 'type', None) if config else None
        return platform_type != 'arcade'

    def validate_context(self, context: StageContext) -> str | None:
        """Validate context for arcade copying."""
        if not context.source_files:
            return "No source files to copy"
        if not context.output_dir:
            return "No output directory specified"
        return None

    def execute(self, context: StageContext) -> StageResult:
        """Execute arcade file copying.

        Args:
            context: Stage execution context

        Returns:
            StageResult with copy outcome
        """
        start_time = time.time()

        # Ensure output directory exists
        context.output_dir.mkdir(parents=True, exist_ok=True)

        # Get CHD source directories from config
        chd_sources = self._get_chd_sources(context)
        
        # Build CHD mapping from DAT (which games need CHDs)
        chd_requirements = self._get_chd_requirements(context)
        
        self._log_info(context, f"ROM source files: {len(context.source_files)}")
        self._log_info(context, f"CHD source dirs: {len(chd_sources)}")
        self._log_info(context, f"Games requiring CHDs: {len(chd_requirements)}")

        # Pre-check: identify games that require CHDs but don't have them
        games_missing_chds = set()
        for src_file in context.source_files:
            game_name = src_file.stem
            if game_name in chd_requirements:
                chd_src_dir = self._find_chd_source(game_name, chd_sources)
                if not chd_src_dir:
                    games_missing_chds.add(game_name)

        if games_missing_chds:
            self._log_warning(context, f"Excluding {len(games_missing_chds)} games with missing CHDs")

        # Copy ROM files (skip games with missing CHDs)
        roms_copied = 0
        roms_failed = 0
        roms_skipped_no_chd = 0
        
        for src_file in context.source_files:
            game_name = src_file.stem
            
            # Skip if this game requires CHDs but they're missing
            if game_name in games_missing_chds:
                roms_skipped_no_chd += 1
                self._log_debug(context, f"Skipping {game_name} - missing required CHDs")
                continue
            
            dst_file = context.output_dir / src_file.name
            if self._copy_file(src_file, dst_file, context):
                roms_copied += 1
            else:
                roms_failed += 1

        self._log_info(context, f"ROMs copied: {roms_copied}")
        if roms_skipped_no_chd:
            self._log_warning(context, f"ROMs skipped (missing CHDs): {roms_skipped_no_chd}")
        if roms_failed:
            self._log_warning(context, f"ROMs failed: {roms_failed}")

        # Copy CHDs for games that need them (only for games we copied)
        chds_copied = 0
        chds_failed = 0

        # Get selected games from context
        selected_games = getattr(context, 'selected_games', set())
        if not selected_games:
            # Fall back to source file stems
            selected_games = {f.stem for f in context.source_files}

        for game_name in selected_games:
            # Skip if game was excluded due to missing CHDs
            if game_name in games_missing_chds:
                continue
            
            if game_name not in chd_requirements:
                continue  # Game doesn't need CHDs
                
            # Find CHD source for this game (already verified it exists)
            chd_src_dir = self._find_chd_source(game_name, chd_sources)
            if not chd_src_dir:
                # This shouldn't happen since we pre-checked, but handle it anyway
                continue

            # Create output folder for CHDs
            chd_dst_dir = context.output_dir / game_name
            chd_dst_dir.mkdir(parents=True, exist_ok=True)

            # Copy all CHD files from source
            for chd_file in chd_src_dir.glob("*.chd"):
                dst_file = chd_dst_dir / chd_file.name
                if self._copy_file(chd_file, dst_file, context):
                    chds_copied += 1
                else:
                    chds_failed += 1

        if chd_requirements:
            self._log_info(context, f"CHDs copied: {chds_copied}")
            if chds_failed:
                self._log_warning(context, f"CHDs failed: {chds_failed}")

        duration = time.time() - start_time

        # Build summary message
        summary_parts = [f"Copied {roms_copied} ROMs"]
        if chds_copied:
            summary_parts.append(f"{chds_copied} CHDs")
        if roms_skipped_no_chd:
            summary_parts.append(f"skipped {roms_skipped_no_chd} (no CHD)")
        summary = ", ".join(summary_parts)

        return StageResult(
            status=StageStatus.SUCCESS if roms_failed == 0 else StageStatus.WARNING,
            message=summary,
            files_processed=len(context.source_files),
            files_matched=roms_copied,
            duration_seconds=duration,
            details={
                "roms_copied": roms_copied,
                "roms_failed": roms_failed,
                "roms_skipped_no_chd": roms_skipped_no_chd,
                "chds_copied": chds_copied,
                "chds_failed": chds_failed,
            },
        )

    def _copy_file(self, src: Path, dst: Path, context: StageContext) -> bool:
        """Copy a file using hardlink or regular copy.

        Args:
            src: Source file path
            dst: Destination file path
            context: Stage context for logging

        Returns:
            True if successful, False otherwise
        """
        try:
            if dst.exists():
                return True  # Already exists

            if self._use_hardlinks:
                try:
                    os.link(src, dst)
                    return True
                except OSError:
                    # Fall back to copy if hardlink fails (cross-device)
                    pass
            
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            self._log_error(context, f"Failed to copy {src.name}: {e}")
            return False

    def _get_chd_sources(self, context: StageContext) -> List[Path]:
        """Get CHD source directories from config.

        Args:
            context: Stage context

        Returns:
            List of CHD source directory paths
        """
        chd_dirs = []

        config = getattr(context, 'platform_config', None) or getattr(context, 'config', None)
        if config:
            # Check chd_sources config
            chd_sources = getattr(config, 'chd_sources', None)
            if chd_sources:
                for source in chd_sources:
                    # Handle both dict and SourceConfig objects
                    if hasattr(source, 'path'):
                        path = Path(source.path)
                    elif isinstance(source, dict):
                        path = Path(source.get('path', ''))
                    else:
                        continue
                    if path.exists():
                        chd_dirs.append(path)
            
            # Also check sources for myrient_chd type
            sources = getattr(config, 'sources', [])
            if sources:
                for source in sources:
                    # Handle both dict and SourceConfig objects
                    if hasattr(source, 'type'):
                        src_type = source.type or ''
                        src_path = Path(source.path) if source.path else None
                    elif isinstance(source, dict):
                        src_type = source.get('type', '')
                        src_path = Path(source.get('path', '')) if source.get('path') else None
                    else:
                        continue
                    
                    if src_path and 'chd' in str(src_type).lower() and src_path.exists():
                        chd_dirs.append(src_path)

        return chd_dirs

    def _get_chd_requirements(self, context: StageContext) -> Dict[str, List[str]]:
        """Get games that require CHDs from DAT file.

        Args:
            context: Stage context

        Returns:
            Dict mapping game name to list of required CHD names
        """
        requirements = {}

        # Get DAT from context
        dat = getattr(context, 'filtered_dat', None) or context.dat_file
        if not dat:
            return requirements

        for game in dat.games:
            # Check if game has disk/CHD requirements
            # This depends on how the DAT parser stores disk info
            disks = getattr(game, 'disks', None) or getattr(game, 'chds', None)
            if disks:
                requirements[game.name] = [d.name for d in disks]
            
            # Also check for disk elements in roms (some DAT formats)
            if hasattr(game, 'roms'):
                for rom in game.roms:
                    # Some parsers include disk info in roms
                    if hasattr(rom, 'region') and 'hdd' in str(getattr(rom, 'region', '')).lower():
                        if game.name not in requirements:
                            requirements[game.name] = []
                        requirements[game.name].append(rom.name)

        return requirements

    def _find_chd_source(self, game_name: str, chd_sources: List[Path]) -> Optional[Path]:
        """Find CHD source directory for a game.

        Args:
            game_name: Name of the game (e.g., "mvsc2")
            chd_sources: List of CHD source directories

        Returns:
            Path to CHD directory if found, None otherwise
        """
        for chd_root in chd_sources:
            # CHDs are typically in a subfolder named after the game
            game_chd_dir = chd_root / game_name
            if game_chd_dir.exists() and game_chd_dir.is_dir():
                # Check if it has CHD files
                if list(game_chd_dir.glob("*.chd")):
                    return game_chd_dir
        
        return None

    def _log_info(self, context: StageContext, message: str):
        """Log info message."""
        self._log(context, f"[cyan]{message}[/cyan]")

    def _log_warning(self, context: StageContext, message: str):
        """Log warning message."""
        self._log(context, f"[yellow]{message}[/yellow]")

    def _log_error(self, context: StageContext, message: str):
        """Log error message."""
        self._log(context, f"[red]{message}[/red]")

    def _log_debug(self, context: StageContext, message: str):
        """Log debug message."""
        self._log(context, f"[dim]{message}[/dim]")
