"""romfarmer plan — plan phase CLI with --explain support.

Usage::

    romfarmer plan --config path/to/build.yaml --explain
    romfarmer plan --config path/to/build.yaml --explain --platform psx

``--explain`` renders a per-pass delta table showing how many units each pass
removed and why (powered by ``PassTrace.removed``).

This command is intentionally read-only: it scans, plans, but does **not**
execute any transforms or write output files.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import click
from rich import box
from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    from romfarmer.analysis.knowledge import KnowledgeBase
    from romfarmer.ir.manifest import BuildManifest

logger = logging.getLogger(__name__)
console = Console()


@click.group("plan")
def plan_group() -> None:
    """Inspect and explain the planner's selection decisions."""


@plan_group.command("run")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True),
    required=True,
    help="Path to the build YAML config.",
)
@click.option(
    "--platform",
    "platform_name",
    default=None,
    help="Limit to a single platform (e.g. 'psx').",
)
@click.option(
    "--explain",
    "explain",
    is_flag=True,
    default=False,
    help="Show per-pass removal counts and sample reasons.",
)
@click.option(
    "--max-reasons",
    "max_reasons",
    default=5,
    show_default=True,
    help="Max sample reasons to show per pass (with --explain).",
)
@click.option(
    "--db",
    "db_path",
    type=click.Path(),
    default=None,
    help="Path to romfarmer.db metadata database.",
)
@click.option(
    "--size-data",
    "size_data_path",
    type=click.Path(),
    default="config/size_data.json",
    show_default=True,
    help="Path to size_data.json for CostModel priors.",
)
def plan_run(
    config_path: str,
    platform_name: str | None,
    explain: bool,
    max_reasons: int,
    db_path: str | None,
    size_data_path: str,
) -> None:
    """Run the planner and optionally explain each pass's decisions."""
    from romfarmer.analysis.catalog_builder import CatalogBuilder
    from romfarmer.analysis.knowledge import KnowledgeBase
    from romfarmer.ir.catalog import PlatformId
    from romfarmer.planner import CostModel, PassRunner, passes

    # ------------------------------------------------------------------ KB
    resolved_db = Path(db_path) if db_path else _find_db()
    kb = KnowledgeBase(resolved_db)

    # ------------------------------------------------------------------ CostModel
    sd_path = Path(size_data_path)
    cost_model = CostModel(
        size_data_path=sd_path if sd_path.exists() else None,
        knowledge_base=kb,
    )

    # ------------------------------------------------------------------ Config
    # For now we delegate to the existing config loader to build a manifest.
    manifest, source_dirs, dat_file = _load_plan_inputs(Path(config_path), platform_name, kb)

    if manifest is None:
        console.print("[red]Could not load build config.[/red]")
        raise SystemExit(1)

    # ------------------------------------------------------------------ Catalog
    platform = manifest.platform or PlatformId(platform_name or "unknown")
    source_dir = source_dirs.get(str(platform))
    if source_dir is None:
        console.print(f"[yellow]No source directory for platform {platform!r}[/yellow]")
        raise SystemExit(1)

    builder = CatalogBuilder(
        platform=platform,
        source_dir=source_dir,
        knowledge_base=kb,
        dat_file=dat_file,
    )
    with console.status(f"Building catalog for {platform}..."):
        catalog = builder.build()

    console.print(
        f"[green]Catalog built:[/green] {len(catalog.units)} units "
        f"({len(catalog.warnings)} warnings)"
    )

    # ------------------------------------------------------------------ Passes
    runner = PassRunner(
        passes=list(passes.DEFAULT_PASSES),
        manifest=manifest,
        kb=kb,
        cost_model=cost_model,
    )
    final_catalog, traces = runner.run(catalog)

    # ------------------------------------------------------------------ Output
    console.print(
        f"\n[bold]Selected:[/bold] {len(final_catalog.units)} / {len(catalog.units)} units"
    )

    if explain:
        _render_explain(catalog, traces, max_reasons)


def _render_explain(initial_catalog: object, traces: list, max_reasons: int) -> None:
    """Render the --explain table."""
    from romfarmer.ir.catalog import Catalog

    assert isinstance(initial_catalog, Catalog)

    table = Table(
        title="Plan — pass-by-pass explanation",
        box=box.ROUNDED,
        show_lines=True,
    )
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


def _find_db() -> Path | None:
    """Locate romfarmer.db in standard locations."""
    candidates = [
        Path("metadata/database/romfarmer.db"),
        Path.cwd() / "metadata" / "database" / "romfarmer.db",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def _load_plan_inputs(
    config_path: Path,
    platform_name: str | None,
    kb: KnowledgeBase,
) -> tuple[BuildManifest | None, dict[str, Path], object]:
    """Load the build YAML config and return (manifest, source_dirs, dat_file).

    This is a thin shim that reads the existing YAML config format and
    constructs a ``BuildManifest``.  It delegates to the existing config
    loaders to avoid duplicating YAML parsing logic.
    """
    from romfarmer.ir.catalog import PlatformId
    from romfarmer.ir.manifest import BuildManifest

    try:
        import yaml  # type: ignore[import]

        with open(config_path) as fh:
            raw = yaml.safe_load(fh)
    except Exception as exc:
        logger.error("Could not load config %s: %s", config_path, exc)
        return None, {}, None

    # Detect platform
    plat_raw = platform_name or raw.get("platform") or raw.get("system") or "unknown"
    platform = PlatformId(str(plat_raw).lower())

    # Source dir
    source_dirs: dict[str, Path] = {}
    src_raw = raw.get("source") or raw.get("source_dir") or raw.get("input")
    if src_raw:
        source_dirs[str(platform)] = Path(str(src_raw))

    # DAT file
    dat_file = None
    dat_raw = raw.get("dat") or (raw.get("dat_config") or {}).get("path")
    if dat_raw and Path(str(dat_raw)).exists():
        try:
            from romfarmer.dat_parser import DATParser  # type: ignore[import]

            dat_file = DATParser.parse(Path(str(dat_raw)))
        except Exception as exc:
            logger.warning("Could not parse DAT %s: %s", dat_raw, exc)

    # Build manifest from config fields
    selection = raw.get("selection") or {}
    rating_cfg = raw.get("rating_filter") or {}
    budget_gb = (selection.get("max_size_gb") or rating_cfg.get("max_size_gb")) or None

    manifest = BuildManifest(
        platform=platform,
        preferred_regions=tuple(
            selection.get("preferred_regions") or raw.get("preferred_regions") or []
        ),
        rating_min=rating_cfg.get("min_rating"),
        rating_top_n=rating_cfg.get("top_n"),
        budget_bytes=int(budget_gb * 1024**3) if budget_gb else None,
        safety_margin=float(raw.get("safety_margin", 0.05)),
        dat_filter=dat_file is not None,
    )
    return manifest, source_dirs, dat_file
