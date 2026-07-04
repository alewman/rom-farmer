"""Pipeline orchestrator for running stages."""

import re
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from ..config import PlatformConfig
from ..dat_parser import DATFile, RetoolDATParser
from ..utils.output_naming import apply_output_naming
from .base import Stage, StageContext, StageResult, StageStatus, StagePhase


# Disc number suffix for multi-disc grouping (e.g., "Final Fantasy IX (Disc 1)")
_DISC_SUFFIX_RE = re.compile(r'\s*\(Disc\s+\d+\)', re.IGNORECASE)


def _group_by_game(files: List[Path]) -> Dict[str, List[Path]]:
    """Group source files by game, keeping multi-disc games together.

    Strips "(Disc N)" suffixes from the filename stem so all discs of a
    multi-disc game land in the same bucket. This is essential because
    per-game execution would otherwise split a multi-disc game across
    iterations, breaking M3U generation and doubling decryption work for
    shared inter-disc content.

    Args:
        files: Source file paths (typically zip archives)

    Returns:
        Ordered dict mapping group name -> list of files in that group
    """
    groups: Dict[str, List[Path]] = {}
    for f in files:
        stem = f.stem
        group_name = _DISC_SUFFIX_RE.sub('', stem).strip()
        groups.setdefault(group_name, []).append(f)
    return groups


class Pipeline:
    """Orchestrate execution of processing stages."""

    def __init__(
        self,
        platform_config: PlatformConfig,
        target_name: str,
        console: Optional[Console] = None,
        letter_filter: Optional[str] = None,
        region_filter: Optional[List[str]] = None,
        language_filter: Optional[List[str]] = None,
        composed_target: Optional[Any] = None,
        tier: Optional[int] = None,
        tier_strategy: Optional[str] = None,
    ):
        """Initialize pipeline.

        Args:
            platform_config: Platform configuration
            target_name: Target profile name
            console: Rich console for output
            letter_filter: Filter by first letter (e.g., 'A', 'B')
            region_filter: Filter by region tags (e.g., ['USA', 'World'])
            language_filter: Filter by language tags (e.g., ['En', 'Eng'])
            composed_target: ComposedTarget for target builds (frontend + device info)
            tier: Platform tier (1-5) from tier system
            tier_strategy: Selection strategy ('always_include', 'best_of', etc.)
        """
        self.platform_config = platform_config
        self.target_name = target_name
        self.console = console or Console()
        self.stages: List[Stage] = []
        self.composed_target = composed_target  # For target builds
        self.tier = tier
        self.tier_strategy = tier_strategy
        
        # Pre-filter settings
        self.letter_filter = letter_filter
        self.region_filter = region_filter
        self.language_filter = language_filter

    def add_stage(self, stage: Stage):
        """Add stage to pipeline.

        Args:
            stage: Stage to add
        """
        self.stages.append(stage)

    def execute(
        self,
        source_dir: Path,
        work_dir: Path,
        output_dir: Path,
        dat_file_path: Optional[Path] = None,
        dat_name: Optional[str] = None,
        prefiltered_files: Optional[List[Path]] = None,
    ) -> List[StageResult]:
        """Execute pipeline.

        Args:
            source_dir: Source ROM directory
            work_dir: Working directory for processing
            output_dir: Final output directory (may be modified with descriptive naming)
            dat_file_path: Optional DAT file path
            dat_name: Optional DAT configuration name for output naming
            prefiltered_files: When provided by the new IR planner path, PLAN
                stages are skipped and these files are used as ``filtered_files``
                directly.  The EXECUTE and FINALIZE stages run unchanged.
                Set by ``new_orchestrator._process_platform`` when
                ``ROMFARMER_LEGACY`` is not ``"1"``.

        Returns:
            List of stage results
        """
        start_time = time.time()
        
        # Apply descriptive output naming if filters are active
        if self.letter_filter or self.region_filter or self.language_filter:
            original_output = output_dir
            output_dir = apply_output_naming(
                base_output_dir=output_dir.parent,
                target_name=self.target_name,
                dat_name=dat_name,
                letter_filter=self.letter_filter,
                region_filter=self.region_filter,
                language_filter=self.language_filter,
            )
            if original_output != output_dir:
                self.console.print(
                    f"[cyan]Output directory: {output_dir.name}[/cyan]"
                )

        # Display header
        self.console.print(
            Panel.fit(
                f"[bold white]ROM Farmer Pipeline[/bold white]\n"
                f"Platform: {self.platform_config.name}\n"
                f"Target: {self.target_name}\n"
                f"Stages: {len(self.stages)}",
                border_style="blue",
            )
        )

        # Prepare directories
        work_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load DAT file if provided
        dat_file = None
        if dat_file_path and dat_file_path.exists():
            self.console.print(f"\n[cyan]Loading DAT file: {dat_file_path.name}[/cyan]")
            parser = RetoolDATParser()
            dat_file = parser.parse(dat_file_path)
            self.console.print(
                f"  Games in DAT: {dat_file.get_game_count():,}"
            )
        elif self.platform_config.dat and self.platform_config.dat.file:
            # Auto-load DAT from config if not explicitly provided
            dat_path = Path(self.platform_config.dat.source) / self.platform_config.dat.file
            if dat_path.exists():
                self.console.print(f"\n[cyan]Loading DAT from config: {dat_path.name}[/cyan]")
                parser = RetoolDATParser()
                dat_file = parser.parse(dat_path)
                self.console.print(
                    f"  Games in DAT: {dat_file.get_game_count():,}"
                )
            else:
                self.console.print(f"  [yellow]Warning: DAT file not found: {dat_path}[/yellow]")

        # Scan source files from all configured source directories
        source_files = []
        source_dirs = []
        
        # Get all source directories from platform config
        if self.platform_config.sources:
            for source_config in self.platform_config.sources:
                src_path = Path(source_config.path)
                if src_path.exists():
                    source_dirs.append(src_path)
                else:
                    self.console.print(f"  [yellow]Warning: Source directory not found: {src_path}[/yellow]")
        else:
            # Fallback to passed source_dir parameter (for backwards compatibility)
            source_dirs = [source_dir]
        
        # Scan all source directories
        self.console.print(f"\n[cyan]Scanning {len(source_dirs)} source director{'y' if len(source_dirs) == 1 else 'ies'}:[/cyan]")
        
        # Determine file pattern based on extraction config
        # If extraction is disabled, scan all files (WADs, ISOs, etc.)
        # Otherwise, scan for ZIP archives
        extraction_enabled = True
        if hasattr(self.platform_config, 'extraction'):
            ext_cfg = self.platform_config.extraction
            if hasattr(ext_cfg, 'enabled'):
                extraction_enabled = ext_cfg.enabled
            elif hasattr(ext_cfg, 'value') and ext_cfg.value == 'none':
                extraction_enabled = False
        
        if extraction_enabled:
            scan_pattern = "*.zip"
            scan_label = "ZIP files"
        else:
            scan_pattern = "*"
            scan_label = "files"
        
        for src_dir in source_dirs:
            if scan_pattern == "*":
                files = [f for f in src_dir.glob(scan_pattern) if f.is_file()]
            else:
                files = list(src_dir.glob(scan_pattern))
            source_files.extend(files)
            self.console.print(f"  {src_dir.name}: {len(files):,} {scan_label}")
        
        self.console.print(f"  [bold]Total: {len(source_files):,} {scan_label}[/bold]")

        # Create context
        context = StageContext(
            platform_name=self.platform_config.name,
            platform_config=self.platform_config,
            target_name=self.target_name,
            source_dir=source_dir,
            work_dir=work_dir,
            output_dir=output_dir,
            dat_file=dat_file,
            source_files=source_files,
            console=self.console,
            letter_filter=self.letter_filter,
            region_filter=self.region_filter,
            language_filter=self.language_filter,
            composed_target=self.composed_target,  # Pass composed target for target builds
            tier=self.tier,
            tier_strategy=self.tier_strategy,
        )

        # Execute stages in three phases: PLAN -> EXECUTE (per-game) -> FINALIZE
        results: List[StageResult] = []
        plan_stages = [s for s in self.stages if s.PHASE == StagePhase.PLAN]
        execute_stages = [s for s in self.stages if s.PHASE == StagePhase.EXECUTE]
        finalize_stages = [s for s in self.stages if s.PHASE == StagePhase.FINALIZE]

        self.console.print(
            f"\n[dim]Phases: {len(plan_stages)} plan, "
            f"{len(execute_stages)} per-game, "
            f"{len(finalize_stages)} finalize[/dim]"
        )

        # ── PLAN phase ────────────────────────────────────────────────────
        # When the new IR planner path provides pre-filtered files, skip all
        # legacy PLAN stages and inject the result directly.
        if prefiltered_files is not None:
            context.filtered_files = list(prefiltered_files)
            self.console.print(
                f"[dim]  PLAN phase skipped (IR planner path): "
                f"{len(prefiltered_files)} pre-selected files[/dim]"
            )
            plan_failed = False
        else:
            # Metadata-only stages that see the full collection.
            plan_failed = self._run_stages_once(
                plan_stages, context, results, phase_label="PLAN", start_index=0
            )

        # ── EXECUTE phase (per-game loop) ─────────────────────────────────
        # Disk-heavy stages run one game at a time so peak work_dir usage
        # stays bounded regardless of platform size.
        exec_failed = False
        if not plan_failed and execute_stages:
            exec_failed = self._run_per_game(
                execute_stages, context, results, start_index=len(plan_stages)
            )

        # ── FINALIZE phase ────────────────────────────────────────────────
        # Batch post-processing on the aggregated per-game outputs.
        if not plan_failed and not exec_failed:
            self._run_stages_once(
                finalize_stages, context, results,
                phase_label="FINALIZE",
                start_index=len(plan_stages) + len(execute_stages),
            )

        # Display summary
        total_time = time.time() - start_time
        self._display_summary(results, total_time)

        return results

    def _run_stages_once(
        self,
        stages: List[Stage],
        context: StageContext,
        results: List[StageResult],
        phase_label: str,
        start_index: int,
    ) -> bool:
        """Run a batch of stages sequentially on the given context.

        Returns:
            True if a stage failed (caller should stop).
        """
        total = len(self.stages)
        for offset, stage in enumerate(stages):
            idx = start_index + offset + 1
            self.console.print(
                f"\n[bold cyan]Stage {idx}/{total} [{phase_label}]: {stage.name}[/bold cyan]"
            )
            try:
                result = stage.execute(context)
                results.append(result)
                self._print_result(result)
                if result.status == StageStatus.FAILED:
                    return True
            except Exception as e:
                self.console.print(f"  [red]Error: {e}[/red]")
                results.append(StageResult(
                    status=StageStatus.FAILED,
                    message=f"Stage failed: {stage.name}",
                    error=e,
                ))
                return True
        return False

    def _run_per_game(
        self,
        execute_stages: List[Stage],
        context: StageContext,
        results: List[StageResult],
        start_index: int,
    ) -> bool:
        """Run EXECUTE stages in a per-game loop to bound peak work_dir size.

        Groups filtered_files into game groups (multi-disc games handled together),
        then for each group:
          1. Create an isolated per-game sub-context with work_dir=<work>/_pergame/<id>
          2. Run all EXECUTE stages on that sub-context
          3. Merge output file lists back into the parent context
          4. Leave any remaining work files in place (organize/finalize picks them up)

        Returns:
            True if any per-game iteration failed hard enough to abort.
        """
        filtered = list(context.filtered_files)
        if not filtered:
            self.console.print("\n[yellow]No files to execute per-game on.[/yellow]")
            return False

        groups = _group_by_game(filtered)
        self.console.print(
            f"\n[bold magenta]── Per-game execution: "
            f"{len(groups)} game(s), {len(execute_stages)} stage(s) each ──[/bold magenta]"
        )

        # Aggregate fields collected from per-game sub-contexts.
        agg_extracted: List[Path] = []
        agg_compressed: List[Path] = []
        agg_m3u: List[Path] = []
        agg_zip_identity: Dict[Path, tuple] = {}
        agg_disc_groups: Dict[str, Any] = {}
        agg_disc_metadata: Dict[str, Any] = {}
        agg_rom_md5: Dict[Path, str] = {}
        agg_file_md5: Dict[Path, str] = {}

        per_game_results: List[StageResult] = []
        failed_games = 0

        # Shared per-game work root (cleaned on successful exit).
        pergame_root = context.work_dir / "_pergame"
        pergame_root.mkdir(parents=True, exist_ok=True)

        for game_idx, (group_name, group_files) in enumerate(groups.items(), 1):
            # Per-game work dir isolated so one game's intermediates don't
            # pile up with another's.
            safe_id = f"g{game_idx:05d}"
            game_work = pergame_root / safe_id
            game_work.mkdir(parents=True, exist_ok=True)

            if game_idx == 1 or game_idx % 25 == 0 or game_idx == len(groups):
                self.console.print(
                    f"  [dim]game {game_idx}/{len(groups)}: {group_name} "
                    f"({len(group_files)} file(s))[/dim]"
                )

            # Build a sub-context that shares immutable platform config
            # but has per-game file lists + work_dir.
            sub = StageContext(
                platform_name=context.platform_name,
                platform_config=context.platform_config,
                target_name=context.target_name,
                source_dir=context.source_dir,
                work_dir=game_work,
                output_dir=context.output_dir,
                composed_target=context.composed_target,
                tier=context.tier,
                tier_strategy=context.tier_strategy,
                dat_file=context.dat_file,
                source_files=group_files,
                filtered_files=group_files,
                console=context.console,
                letter_filter=context.letter_filter,
                region_filter=context.region_filter,
                language_filter=context.language_filter,
            )

            game_failed = False
            for stage in execute_stages:
                try:
                    result = stage.execute(sub)
                    per_game_results.append(result)
                    if result.status == StageStatus.FAILED:
                        self.console.print(
                            f"  [red]✗ {group_name}: {stage.name} failed: "
                            f"{result.error or result.message}[/red]"
                        )
                        game_failed = True
                        break
                except Exception as e:
                    self.console.print(
                        f"  [red]✗ {group_name}: {stage.name} raised: {e}[/red]"
                    )
                    per_game_results.append(StageResult(
                        status=StageStatus.FAILED,
                        message=f"{stage.name} (game={group_name})",
                        error=e,
                    ))
                    game_failed = True
                    break

            if game_failed:
                failed_games += 1
                # Clean up this game's work dir to avoid wasting disk.
                shutil.rmtree(game_work, ignore_errors=True)
                continue

            # Merge per-game outputs back to parent context.
            agg_extracted.extend(sub.extracted_files)
            agg_compressed.extend(sub.compressed_files)
            agg_m3u.extend(sub.m3u_files)
            agg_zip_identity.update(sub.zip_identity_map)
            agg_disc_groups.update(sub.disc_groups)
            agg_disc_metadata.update(sub.disc_metadata)
            agg_rom_md5.update(sub.rom_md5_map)
            agg_file_md5.update(sub.file_md5s)

        # Collapse per-game stage results into one summary row per stage.
        # (Reporting every per-game StageResult would overwhelm the summary.)
        stage_summaries: Dict[str, Dict[str, Any]] = {}
        for r in per_game_results:
            key = r.message.split(" (game=")[0]
            agg = stage_summaries.setdefault(key, {
                "success": 0, "failed": 0, "skipped": 0,
                "files_processed": 0, "files_matched": 0,
                "duration": 0.0,
            })
            agg["files_processed"] += r.files_processed
            agg["files_matched"] += r.files_matched
            agg["duration"] += r.duration_seconds
            if r.status == StageStatus.SUCCESS:
                agg["success"] += 1
            elif r.status == StageStatus.FAILED:
                agg["failed"] += 1
            elif r.status == StageStatus.SKIPPED:
                agg["skipped"] += 1

        total_stages = len(self.stages)
        for offset, stage in enumerate(execute_stages):
            idx = start_index + offset + 1
            agg = stage_summaries.get(stage.name, {
                "success": 0, "failed": 0, "skipped": 0,
                "files_processed": 0, "files_matched": 0, "duration": 0.0,
            })
            status = StageStatus.SUCCESS if agg["failed"] == 0 else StageStatus.FAILED
            msg = (f"{stage.name}: {agg['success']} ok, "
                   f"{agg['failed']} failed, {agg['skipped']} skipped "
                   f"across {len(groups)} game(s)")
            results.append(StageResult(
                status=status,
                message=msg,
                files_processed=agg["files_processed"],
                files_matched=agg["files_matched"],
                duration_seconds=agg["duration"],
            ))
            self.console.print(
                f"\n[bold cyan]Stage {idx}/{total_stages} [PER-GAME]: "
                f"{stage.name}[/bold cyan]"
            )
            self.console.print(f"  [green]{msg}[/green]")

        # Commit aggregated outputs to parent context for FINALIZE.
        context.extracted_files = agg_extracted
        context.compressed_files = agg_compressed
        context.m3u_files = agg_m3u
        context.zip_identity_map = agg_zip_identity
        context.disc_groups = agg_disc_groups
        context.disc_metadata = agg_disc_metadata
        context.rom_md5_map = agg_rom_md5
        context.file_md5s = agg_file_md5

        if failed_games:
            self.console.print(
                f"\n[yellow]{failed_games} game(s) failed during per-game "
                f"execution; continuing with {len(groups) - failed_games} "
                f"successful game(s).[/yellow]"
            )

        return False  # soft-failures don't abort the whole pipeline

    def _print_result(self, result: StageResult) -> None:
        """Print a single stage result with appropriate styling."""
        if result.status == StageStatus.SUCCESS:
            self.console.print(f"  [green]{result.get_summary()}[/green]")
        elif result.status == StageStatus.SKIPPED:
            self.console.print(f"  [yellow]{result.get_summary()}[/yellow]")
        elif result.status == StageStatus.FAILED:
            self.console.print(f"  [red]{result.get_summary()}[/red]")

    def _display_summary(self, results: List[StageResult], total_time: float):
        """Display pipeline execution summary.

        Args:
            results: Stage results
            total_time: Total execution time
        """
        self.console.print("\n" + "=" * 70)
        self.console.print("[bold]Pipeline Summary[/bold]")

        table = Table(show_header=True)
        table.add_column("Stage", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Files", justify="right")
        table.add_column("Time", justify="right")

        for result in results:
            # Handle both StageResult and StageContext objects
            if isinstance(result, StageContext):
                # Skip StageContext objects in summary
                continue
            
            status_emoji = {
                StageStatus.SUCCESS: "✓",
                StageStatus.FAILED: "✗",
                StageStatus.SKIPPED: "⊘",
                StageStatus.PENDING: "⋯",
            }

            # Extract stage name from message
            stage_name = result.message.split(":")[0] if hasattr(result, 'message') and ":" in result.message else result.message[:40] if hasattr(result, 'message') else "Unknown"
            
            table.add_row(
                stage_name,
                f"{status_emoji.get(result.status, '?')} {result.status.value}",
                str(result.files_processed),
                f"{result.duration_seconds:.1f}s",
            )

        self.console.print(table)

        # Overall status - filter out StageContext objects
        valid_results = [r for r in results if hasattr(r, 'status')]
        success_count = sum(1 for r in valid_results if r.status == StageStatus.SUCCESS)
        failed_count = sum(1 for r in valid_results if r.status == StageStatus.FAILED)

        if failed_count > 0:
            self.console.print(
                f"\n[red]✗ Pipeline failed: {failed_count} stage(s) failed[/red]"
            )
        else:
            self.console.print(
                f"\n[green]✓ Pipeline completed: {success_count} stage(s) successful[/green]"
            )

        self.console.print(f"Total time: {total_time:.1f}s")
