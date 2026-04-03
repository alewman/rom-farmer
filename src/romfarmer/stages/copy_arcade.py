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

When a ``cache_manager`` is provided, every file (ROM ZIP and CHD) is
routed through CAS:
  - First build: hash → store in CAS → hardlink CAS → output
  - Second build: fast lookup → hardlink CAS → output  (instant)
This makes the CAS store self-contained for arcade sets and enables
zero-cost multi-frontend builds.
"""

import hashlib
import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .base import Stage, StageContext, StageResult, StageStatus


class CopyArcadeStage(Stage):
    """Copy arcade ROMs and CHDs to output directory."""

    _PASSTHROUGH_PARAMS = {"compression": "passthrough"}

    def __init__(self, cache_manager: Optional[Any] = None):
        """Initialize arcade copy stage.

        Args:
            cache_manager: Optional ROM cache for CAS-backed copies.
                When provided, every file is routed through CAS so that
                multi-frontend builds are instant hardlinks.
        """
        super().__init__("Copy Arcade")
        self._use_hardlinks = True
        self.cache_manager = cache_manager
        self._cas_hits = 0
        self._cas_stored = 0

    def should_skip(self, context: StageContext) -> bool:
        """Skip if not an arcade platform."""
        config = getattr(context, 'platform_config', None) or getattr(context, 'config', None)
        platform_type = getattr(config, 'type', None) if config else None
        return platform_type != 'arcade'

    def validate_context(self, context: StageContext) -> str | None:
        """Validate context for arcade copying."""
        if not context.source_files and not context.extracted_files:
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

        # Build ROM file list — prefer recompressed .7z (from work_dir)
        # over original .zip when both exist for the same game.
        rom_files = self._build_rom_file_list(context)

        # Get CHD source directories from config
        chd_sources = self._get_chd_sources(context)
        
        # Build CHD mapping from DAT (which games need CHDs)
        chd_requirements = self._get_chd_requirements(context)
        
        self._log_info(context, f"ROM source files: {len(rom_files)}")
        self._log_info(context, f"CHD source dirs: {len(chd_sources)}")
        self._log_info(context, f"Games requiring CHDs: {len(chd_requirements)}")

        # Pre-check: identify games that require CHDs but don't have them
        games_missing_chds = set()
        for src_file in rom_files:
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
        
        for src_file in rom_files:
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
            # Fall back to ROM file stems (covers both source and recompressed)
            selected_games = {f.stem for f in rom_files}

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
        if self._cas_hits:
            summary_parts.append(f"{self._cas_hits} from CAS")
        if self._cas_stored:
            summary_parts.append(f"{self._cas_stored} stored in CAS")
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
                "cas_hits": self._cas_hits,
                "cas_stored": self._cas_stored,
            },
        )

    def _copy_file(self, src: Path, dst: Path, context: StageContext) -> bool:
        """Copy a file, routing through CAS when a cache_manager is set.

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

            if self.cache_manager:
                return self._copy_via_cas(src, dst, context)
            return self._direct_copy(src, dst)
        except Exception as e:
            self._log_error(context, f"Failed to copy {src.name}: {e}")
            return False

    def _direct_copy(self, src: Path, dst: Path) -> bool:
        """Hardlink or copy without CAS (original behaviour)."""
        if self._use_hardlinks:
            try:
                os.link(src, dst)
                return True
            except OSError:
                pass
        shutil.copy2(src, dst)
        return True

    def _copy_via_cas(
        self, src: Path, dst: Path, context: StageContext,
    ) -> bool:
        """Copy through CAS: fast lookup → store on miss → link to output."""
        fmt = src.suffix.lstrip(".").lower() or "bin"
        params = self._PASSTHROUGH_PARAMS

        # ── Fast path: filename + size (no hashing) ──────────────────
        try:
            src_size = src.stat().st_size
            result = self.cache_manager.get_by_filename(
                source_filename=src.name,
                source_size=src_size,
                format=fmt,
                params=params,
            )
            if result.hit:
                if self.cache_manager.link_to(result.cache_path, dst):
                    self._cas_hits += 1
                    return True
        except Exception:
            pass  # fall through to slow path

        # ── Slow path: compute MD5, check/store ──────────────────────
        try:
            md5 = self._calculate_md5(src)
            if not md5:
                return self._direct_copy(src, dst)

            result = self.cache_manager.get(
                source_md5=md5, format=fmt, params=params,
            )
            if result.hit:
                if self.cache_manager.link_to(result.cache_path, dst):
                    self._cas_hits += 1
                    return True

            # Store in CAS, then link to output
            store_result = self.cache_manager.store(
                source_md5=md5,
                source_file=src,
                built_file=src,
                format=fmt,
                params=params,
                tool_name="passthrough",
            )
            if store_result.hit and store_result.cache_path:
                if self.cache_manager.link_to(store_result.cache_path, dst):
                    self._cas_stored += 1
                    return True
        except Exception as e:
            self._log_warning(
                context, f"  CAS failed for {src.name}: {e}",
            )

        # CAS completely failed — fall back to direct copy
        return self._direct_copy(src, dst)

    @staticmethod
    def _calculate_md5(file_path: Path) -> Optional[str]:
        """Calculate MD5 hash of a file."""
        try:
            h = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192 * 1024), b""):
                    h.update(chunk)
            return h.hexdigest()
        except Exception:
            return None

    @staticmethod
    def _build_rom_file_list(context: StageContext) -> List[Path]:
        """Build the ROM file list, preferring recompressed files.

        When RecompressArcadeStage runs first, it puts .7z files in
        ``extracted_files`` and residual .zips in ``source_files``.
        We merge both, preferring the .7z when a game appears in both.
        When no recompression occurred, ``extracted_files`` is empty and
        we fall back entirely to ``source_files``.
        """
        recompressed = {f.stem: f for f in (context.extracted_files or [])}
        rom_files: List[Path] = []
        seen_stems: set = set()

        # Recompressed files take priority
        for f in recompressed.values():
            rom_files.append(f)
            seen_stems.add(f.stem)

        # Then any source files not superseded by recompressed versions
        for f in (context.source_files or []):
            if f.stem not in seen_stems:
                rom_files.append(f)
                seen_stems.add(f.stem)

        return rom_files

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
