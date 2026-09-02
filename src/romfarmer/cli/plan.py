"""romfarmer plan — RESOLVE + CATALOG + PLAN for a build, with --explain.

Usage::

    romfarmer plan run smoke-nes-7z --explain
    romfarmer plan run config/builds/redump-1g1r-eng-chd-retrobat.yaml --platform psx --explain

Runs exactly the RESOLVE / CATALOG / PLAN phases that ``romfarmer build run``
would (same passes, same manifest, same format negotiation), so the
``--explain`` table is a faithful prediction of the build.  Read-only: no
transforms are executed and no output files are written.
"""

from __future__ import annotations

import logging
from pathlib import Path

import click
from rich import box
from rich.console import Console
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()


@click.group("plan")
def plan_group() -> None:
    """Inspect and explain the planner's selection decisions."""


@plan_group.command("run")
@click.argument("build")
@click.option("--platform", "platform_name", default=None, help="Limit to one platform (e.g. psx).")
@click.option("--explain", is_flag=True, help="Show per-pass removal counts and sample reasons.")
@click.option("--max-reasons", default=5, show_default=True, help="Sample reasons per pass.")
@click.option(
    "--test-sample", type=int, default=None, help="Apply the seeded sample pass a test build would."
)
@click.option("--seed", type=int, default=0, show_default=True, help="Seed for --test-sample.")
def plan_run(
    build: str,
    platform_name: str | None,
    explain: bool,
    max_reasons: int,
    test_sample: int | None,
    seed: int,
) -> None:
    """Plan BUILD — a name in config/builds/ or a path to a build YAML."""
    from romfarmer.analysis.knowledge import KnowledgeBase
    from romfarmer.ir.catalog import PlatformId
    from romfarmer.new_orchestrator import NewBuildOrchestrator, run_catalog, run_plan
    from romfarmer.planner import CostModel
    from romfarmer.planner.negotiation import negotiate_format_chain, negotiate_with_profile

    build_name = Path(build).stem if build.endswith((".yaml", ".yml")) else build
    try:
        orchestrator = NewBuildOrchestrator.from_config(
            build_name, platform_filter=[platform_name] if platform_name else None
        )
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise SystemExit(1) from exc

    if test_sample:
        orchestrator._test_sample = test_sample
        orchestrator._test_seed = seed

    resolved_list = orchestrator.resolved_configs
    if platform_name:
        resolved_list = [r for r in resolved_list if r.platform == platform_name]
        if not resolved_list:
            console.print(f"[red]Platform {platform_name!r} is not in build {build_name!r}[/red]")
            raise SystemExit(1)

    db_path = Path("metadata/database/romfarmer.db")
    kb = KnowledgeBase(db_path if db_path.exists() else None)
    sd_path = Path("config/size_data.json")
    cost_model = CostModel(size_data_path=sd_path if sd_path.exists() else None, knowledge_base=kb)
    profile = orchestrator._load_target_profile()

    console.print(
        f"[cyan]Build:[/cyan] {build_name}  [cyan]Target:[/cyan] {orchestrator.build_spec.target}  "
        f"[cyan]Platforms:[/cyan] {len(resolved_list)}"
    )

    total_in = total_out = 0
    for resolved in resolved_list:
        source_dir = resolved.sources[0].path if resolved.sources else None
        if source_dir is None:
            console.print(f"[yellow]{resolved.platform}: no source directory — skipped[/yellow]")
            continue
        dat_file = orchestrator._find_dat_file(resolved)
        chain = (
            negotiate_with_profile(resolved, profile)
            if profile is not None
            else negotiate_format_chain(resolved)
        )
        manifest = orchestrator._build_manifest(
            resolved, PlatformId(resolved.platform), dat_file=dat_file
        )

        with console.status(f"Cataloging {resolved.platform}..."):
            catalog = run_catalog(resolved, source_dir=source_dir, dat_file=dat_file, kb=kb)
        planned = run_plan(catalog, manifest, cost_model=cost_model, kb=kb, chain=chain)

        n_in, n_out = len(catalog.units), len(planned.catalog.units)
        total_in += n_in
        total_out += n_out
        dat_note = "" if dat_file else "  [yellow](no DAT)[/yellow]"
        console.print(
            f"\n[bold]{resolved.platform}[/bold]  chain={'→'.join(chain)}  "
            f"[green]{n_out}[/green] / {n_in} units{dat_note}"
        )
        if explain:
            _render_explain(list(planned.traces), max_reasons)

    if len(resolved_list) > 1:
        console.print(f"\n[bold]Total:[/bold] {total_out} / {total_in} units selected")


def _render_explain(traces: list, max_reasons: int) -> None:
    """Render the --explain table."""
    table = Table(box=box.ROUNDED, show_lines=True)
    table.add_column("Pass", style="cyan", no_wrap=True)
    table.add_column("Removed", justify="right", style="red")
    table.add_column("Sample reasons", overflow="fold")

    for trace in traces:
        n = len(trace.removed)
        if n == 0:
            sample = "[dim](no-op)[/dim]"
        else:
            lines = [f"• {reason}" for _, reason in trace.removed[:max_reasons]]
            if n > max_reasons:
                lines.append(f"  [dim]... and {n - max_reasons} more[/dim]")
            sample = "\n".join(lines)
        table.add_row(trace.pass_name, str(n) if n else "—", sample)

    console.print(table)
