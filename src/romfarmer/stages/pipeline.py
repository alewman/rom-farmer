"""Pipeline orchestrator for running stages."""

import time
from pathlib import Path
from typing import Any, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from ..config import PlatformConfig
from ..dat_parser import DATFile, RetoolDATParser
from ..utils.output_naming import apply_output_naming
from .base import Stage, StageContext, StageResult, StageStatus


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
    ) -> List[StageResult]:
        """Execute pipeline.

        Args:
            source_dir: Source ROM directory
            work_dir: Working directory for processing
            output_dir: Final output directory (may be modified with descriptive naming)
            dat_file_path: Optional DAT file path
            dat_name: Optional DAT configuration name for output naming

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

        # Execute stages
        results = []
        for i, stage in enumerate(self.stages, 1):
            self.console.print(
                f"\n[bold cyan]Stage {i}/{len(self.stages)}: {stage.name}[/bold cyan]"
            )

            try:
                result = stage.execute(context)
                results.append(result)

                # Display result
                if result.status == StageStatus.SUCCESS:
                    self.console.print(f"  [green]{result.get_summary()}[/green]")
                elif result.status == StageStatus.SKIPPED:
                    self.console.print(f"  [yellow]{result.get_summary()}[/yellow]")
                elif result.status == StageStatus.FAILED:
                    self.console.print(f"  [red]{result.get_summary()}[/red]")
                    break  # Stop on failure

            except Exception as e:
                self.console.print(f"  [red]Error: {e}[/red]")
                results.append(
                    StageResult(
                        status=StageStatus.FAILED,
                        message=f"Stage failed: {stage.name}",
                        error=e,
                    )
                )
                break

        # Display summary
        total_time = time.time() - start_time
        self._display_summary(results, total_time)

        return results

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
