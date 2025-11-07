"""Pipeline orchestrator for running stages."""

import time
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from ..config import PlatformConfig
from ..dat_parser import DATFile, RetoolDATParser
from .base import Stage, StageContext, StageResult, StageStatus


class Pipeline:
    """Orchestrate execution of processing stages."""

    def __init__(
        self,
        platform_config: PlatformConfig,
        target_name: str,
        console: Optional[Console] = None,
    ):
        """Initialize pipeline.

        Args:
            platform_config: Platform configuration
            target_name: Target profile name
            console: Rich console for output
        """
        self.platform_config = platform_config
        self.target_name = target_name
        self.console = console or Console()
        self.stages: List[Stage] = []

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
    ) -> List[StageResult]:
        """Execute pipeline.

        Args:
            source_dir: Source ROM directory
            work_dir: Working directory for processing
            output_dir: Final output directory
            dat_file_path: Optional DAT file path

        Returns:
            List of stage results
        """
        start_time = time.time()

        # Display header
        self.console.print(
            Panel.fit(
                f"[bold white]ROM Groomer Pipeline[/bold white]\n"
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
        for src_dir in source_dirs:
            files = list(src_dir.glob("*.zip"))
            source_files.extend(files)
            self.console.print(f"  {src_dir.name}: {len(files):,} ZIP files")
        
        self.console.print(f"  [bold]Total: {len(source_files):,} ZIP files[/bold]")

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
            status_emoji = {
                StageStatus.SUCCESS: "✓",
                StageStatus.FAILED: "✗",
                StageStatus.SKIPPED: "⊘",
                StageStatus.PENDING: "⋯",
            }

            table.add_row(
                result.message.split(":")[0] if ":" in result.message else result.message[:40],
                f"{status_emoji.get(result.status, '?')} {result.status.value}",
                str(result.files_processed),
                f"{result.duration_seconds:.1f}s",
            )

        self.console.print(table)

        # Overall status
        success_count = sum(1 for r in results if r.status == StageStatus.SUCCESS)
        failed_count = sum(1 for r in results if r.status == StageStatus.FAILED)

        if failed_count > 0:
            self.console.print(
                f"\n[red]✗ Pipeline failed: {failed_count} stage(s) failed[/red]"
            )
        else:
            self.console.print(
                f"\n[green]✓ Pipeline completed: {success_count} stage(s) successful[/green]"
            )

        self.console.print(f"Total time: {total_time:.1f}s")
