"""Plugin-aware pipeline executor.

Replaces the legacy Pipeline class with a plugin-first orchestrator
that uses the registry for plugin discovery and the event bus for
cross-cutting concerns.

The PluginPipeline:
1. Accepts plugins (or resolves them from registry)
2. Validates I/O contracts before execution
3. Emits events at every lifecycle point
4. Delegates to each plugin's execute() method
5. Provides the same rich console output as the legacy Pipeline

It is backward-compatible: StageAdapter-wrapped stages work identically
to how they did in the legacy Pipeline.
"""

from __future__ import annotations

import time
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..stages.base import StageContext, StageResult, StageStatus
from .protocol import Plugin, PluginMeta, PluginValidationError
from .registry import PluginRegistry
from .events import (
    Event,
    EventBus,
    PipelineEvent,
    StageEvent,
)

logger = logging.getLogger(__name__)


class PluginPipeline:
    """Execute a sequence of plugins with event bus integration.

    Example::

        registry = PluginRegistry()
        register_builtin_plugins(registry)

        bus = EventBus()
        bus.on("stage.*", lambda e: print(f"{e.source}: {e.name}"))

        pipeline = PluginPipeline(
            plugins=registry.resolve_order(platform="nes"),
            event_bus=bus,
        )
        results = pipeline.execute(context)
    """

    def __init__(
        self,
        plugins: Optional[Sequence[Plugin]] = None,
        registry: Optional[PluginRegistry] = None,
        event_bus: Optional[EventBus] = None,
        console: Optional[Console] = None,
        platform: Optional[str] = None,
        validate_contracts: bool = True,
    ):
        """Initialize pipeline.

        Provide either `plugins` (explicit ordered list) or `registry`
        + `platform` (auto-resolve from registry).

        Args:
            plugins: Explicit ordered list of plugins to execute
            registry: Plugin registry for auto-resolution
            event_bus: Event bus for lifecycle events (optional)
            console: Rich console for output (optional)
            platform: Platform name for registry auto-resolution
            validate_contracts: Whether to validate I/O contracts
        """
        self._event_bus = event_bus or EventBus()
        self._console = console or Console()
        self._validate = validate_contracts

        if plugins is not None:
            self._plugins = list(plugins)
        elif registry is not None:
            self._plugins = registry.resolve_order(platform=platform)
        else:
            self._plugins = []

    @property
    def plugins(self) -> List[Plugin]:
        """Ordered list of plugins."""
        return list(self._plugins)

    @property
    def event_bus(self) -> EventBus:
        """The event bus for this pipeline."""
        return self._event_bus

    def add_plugin(self, plugin: Plugin) -> None:
        """Add a plugin to the end of the pipeline.

        Args:
            plugin: Plugin to add
        """
        self._plugins.append(plugin)

    def execute(self, context: StageContext) -> List[StageResult]:
        """Execute all plugins in order.

        Args:
            context: Mutable pipeline context

        Returns:
            List of StageResult objects (one per plugin)
        """
        start_time = time.time()
        results: List[StageResult] = []
        total = len(self._plugins)

        # Set console on context if not already set
        if context.console is None:
            context.console = self._console

        # ── Pipeline Start ────────────────────────────────────────────────
        self._display_header(context, total)
        self._event_bus.emit(Event(
            name=PipelineEvent.PIPELINE_START.value,
            source="pipeline",
            metadata={
                "platform": context.platform_name,
                "plugin_count": total,
                "plugins": [p.meta.name for p in self._plugins],
            },
        ))

        # ── Execute Each Plugin ───────────────────────────────────────────
        for i, plugin in enumerate(self._plugins, 1):
            meta = plugin.meta
            self._console.print(
                f"\n[bold cyan]Stage {i}/{total}: {meta.name}[/bold cyan]"
            )

            # Check should_skip
            try:
                if plugin.should_skip(context):
                    result = StageResult(
                        status=StageStatus.SKIPPED,
                        message=f"{meta.name}: skipped",
                    )
                    results.append(result)
                    self._console.print(f"  [yellow]{result.get_summary()}[/yellow]")
                    self._event_bus.emit(StageEvent(
                        name=PipelineEvent.STAGE_SKIP.value,
                        source=meta.name,
                        stage_name=meta.name,
                        stage_index=i,
                        total_stages=total,
                        platform=context.platform_name,
                    ))
                    continue
            except Exception:
                pass  # If should_skip fails, proceed with execution

            # Validate context
            if self._validate:
                try:
                    error = plugin.validate(context)
                    if error:
                        result = StageResult(
                            status=StageStatus.FAILED,
                            message=f"{meta.name}: validation failed — {error}",
                        )
                        results.append(result)
                        self._console.print(f"  [red]{result.get_summary()}[/red]")
                        break
                except Exception:
                    pass  # If validate fails, proceed with execution

            # Emit stage start
            self._event_bus.emit(StageEvent(
                name=PipelineEvent.STAGE_START.value,
                source=meta.name,
                stage_name=meta.name,
                stage_index=i,
                total_stages=total,
                platform=context.platform_name,
            ))

            # Execute
            stage_start = time.time()
            try:
                result = plugin.execute(context)
                result.duration_seconds = time.time() - stage_start
                results.append(result)

                # Display result
                if result.status == StageStatus.SUCCESS:
                    self._console.print(f"  [green]{result.get_summary()}[/green]")
                elif result.status == StageStatus.SKIPPED:
                    self._console.print(f"  [yellow]{result.get_summary()}[/yellow]")
                elif result.status == StageStatus.FAILED:
                    self._console.print(f"  [red]{result.get_summary()}[/red]")

                # Emit stage end
                self._event_bus.emit(StageEvent(
                    name=PipelineEvent.STAGE_END.value,
                    source=meta.name,
                    stage_name=meta.name,
                    stage_index=i,
                    total_stages=total,
                    platform=context.platform_name,
                    duration=result.duration_seconds,
                    files_processed=result.files_processed,
                ))

                # Stop on failure
                if result.status == StageStatus.FAILED:
                    self._event_bus.emit(StageEvent(
                        name=PipelineEvent.STAGE_ERROR.value,
                        source=meta.name,
                        stage_name=meta.name,
                        error=result.error,
                    ))
                    break

            except Exception as e:
                duration = time.time() - stage_start
                self._console.print(f"  [red]Error: {e}[/red]")
                result = StageResult(
                    status=StageStatus.FAILED,
                    message=f"Plugin failed: {meta.name}",
                    error=e,
                    duration_seconds=duration,
                )
                results.append(result)

                self._event_bus.emit(StageEvent(
                    name=PipelineEvent.STAGE_ERROR.value,
                    source=meta.name,
                    stage_name=meta.name,
                    error=e,
                    duration=duration,
                ))
                break

        # ── Pipeline End ──────────────────────────────────────────────────
        total_time = time.time() - start_time
        has_failure = any(
            r.status == StageStatus.FAILED
            for r in results
            if hasattr(r, "status")
        )

        self._event_bus.emit(Event(
            name=(
                PipelineEvent.PIPELINE_ERROR.value
                if has_failure
                else PipelineEvent.PIPELINE_END.value
            ),
            source="pipeline",
            metadata={
                "duration": total_time,
                "stages_run": len(results),
                "success": not has_failure,
            },
        ))

        self._display_summary(results, total_time)
        return results

    # ── Display helpers ───────────────────────────────────────────────────

    def _display_header(self, context: StageContext, plugin_count: int) -> None:
        """Display pipeline startup header."""
        self._console.print(
            Panel.fit(
                f"[bold white]ROM Farmer Plugin Pipeline[/bold white]\n"
                f"Platform: {context.platform_name}\n"
                f"Target: {context.target_name}\n"
                f"Plugins: {plugin_count}",
                border_style="blue",
            )
        )

    def _display_summary(
        self, results: List[StageResult], total_time: float
    ) -> None:
        """Display pipeline execution summary."""
        self._console.print("\n" + "=" * 70)
        self._console.print("[bold]Plugin Pipeline Summary[/bold]")

        table = Table(show_header=True)
        table.add_column("Plugin", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Files", justify="right")
        table.add_column("Time", justify="right")

        status_emoji = {
            StageStatus.SUCCESS: "✓",
            StageStatus.FAILED: "✗",
            StageStatus.SKIPPED: "⊘",
            StageStatus.PENDING: "⋯",
        }

        for result in results:
            if not hasattr(result, "status"):
                continue

            stage_name = (
                result.message.split(":")[0]
                if ":" in result.message
                else result.message[:40]
            )

            table.add_row(
                stage_name,
                f"{status_emoji.get(result.status, '?')} {result.status.value}",
                str(result.files_processed),
                f"{result.duration_seconds:.1f}s",
            )

        self._console.print(table)

        valid_results = [r for r in results if hasattr(r, "status")]
        success_count = sum(
            1 for r in valid_results if r.status == StageStatus.SUCCESS
        )
        failed_count = sum(
            1 for r in valid_results if r.status == StageStatus.FAILED
        )

        if failed_count > 0:
            self._console.print(
                f"\n[red]✗ Pipeline failed: {failed_count} plugin(s) failed[/red]"
            )
        else:
            self._console.print(
                f"\n[green]✓ Pipeline completed: {success_count} plugin(s) successful[/green]"
            )

        self._console.print(f"Total time: {total_time:.1f}s")
