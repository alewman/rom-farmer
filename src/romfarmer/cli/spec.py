"""``romfarmer spec`` — the SPEC seam from the command line.

romfarmer spec lower <build>          # legacy build → Spec YAML (+ hash), freezes lists/ into artifacts/
romfarmer spec validate <spec.yaml>   # loud validation + resolve every platform
romfarmer spec hash <spec.yaml>
"""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

console = Console()


@click.group("spec")
def spec_group() -> None:
    """Author, validate and hash build Specs (the seam above the compiler)."""


@spec_group.command("lower")
@click.argument("build")
@click.option(
    "--out",
    type=click.Path(path_type=Path),
    help="Write YAML here (default: artifacts/specs/<hash>.yaml)",
)
@click.option("--no-freeze-lists", is_flag=True, help="Do not freeze lists/ into curated artifacts")
def spec_lower(build: str, out: Path | None, no_freeze_lists: bool) -> None:
    """Lower a legacy config/builds/<BUILD>.yaml into a frozen Spec."""
    from romfarmer.core.paths import get_paths
    from romfarmer.driver.spec_io import dump_spec, save_spec
    from romfarmer.driver.spec_resolve import spec_from_build
    from romfarmer.ir.spec import SpecError

    try:
        spec = spec_from_build(build, freeze_lists=not no_freeze_lists)
    except SpecError as exc:
        console.print(f"[red]{exc}[/red]")
        raise SystemExit(1) from exc
    if out is not None:
        out.write_text(dump_spec(spec))
        path = out
    else:
        path = save_spec(spec, Path(get_paths().workspace_root) / "artifacts" / "specs")
    console.print(f"[green]spec_hash[/green] {spec.spec_hash()}  → {path}")


@spec_group.command("validate")
@click.argument("spec_file", type=click.Path(exists=True, path_type=Path))
def spec_validate(spec_file: Path) -> None:
    """Validate SPEC_FILE and RESOLVE every platform (no source scan)."""
    from romfarmer.core.paths import get_paths
    from romfarmer.driver.spec_io import load_spec
    from romfarmer.driver.spec_resolve import resolve_build
    from romfarmer.ir.spec import SpecError

    ws = Path(get_paths().workspace_root)
    try:
        spec = load_spec(spec_file)
        builds = resolve_build(spec, ws / "config", workspace_root=ws)
    except SpecError as exc:
        console.print(f"[red]{exc}[/red]")
        raise SystemExit(1) from exc
    console.print(f"[green]ok[/green] spec_hash={spec.spec_hash()}  platforms={len(builds)}")
    for rb in builds:
        m = rb.manifest
        console.print(
            f"  {rb.platform:14s} chain={'→'.join(rb.chain):12s} dat={'yes' if rb.dat_file else 'no ':3s} "
            f"1g1r={'dat' if not m.one_g_one_r else 'pass'} rating_min={m.rating_min} budget={m.budget_bytes}"
        )


@spec_group.command("hash")
@click.argument("spec_file", type=click.Path(exists=True, path_type=Path))
def spec_hash(spec_file: Path) -> None:
    """Print the spec_hash of SPEC_FILE."""
    from romfarmer.driver.spec_io import load_spec

    click.echo(load_spec(spec_file).spec_hash())


@spec_group.command("summary")
@click.argument("spec_file", type=click.Path(exists=True, path_type=Path))
@click.option("--json", "as_json", is_flag=True, help="Emit the compact JSON the agent reads")
def spec_summary(spec_file: Path, as_json: bool) -> None:
    """INVENTORY (once) + dry-run PLAN → PlanSummary for SPEC_FILE.  Moves zero bytes."""
    import json as _json

    from romfarmer.core.paths import get_paths
    from romfarmer.driver.session import PlanSession
    from romfarmer.driver.spec_io import load_spec
    from romfarmer.ir.spec import SpecError

    ws = Path(get_paths().workspace_root)
    try:
        spec = load_spec(spec_file)
        session = PlanSession(ws, ws / "config")
        summary = session.dry_run(spec)
    except SpecError as exc:
        console.print(f"[red]{exc}[/red]")
        raise SystemExit(1) from exc
    if as_json:
        click.echo(summary.to_json())
        return
    d = summary.to_dict()
    console.print(
        f"[cyan]spec[/cyan] {d['spec_hash'][:12]}  total p50={d['bytes_total_p50'] / 1e9:.1f} GB "
        f"p90={(d['bytes_total_p90'] or 0) / 1e9:.1f} GB  headroom p50="
        f"{(d['headroom_p50'] or 0) / 1e9:.1f} GB  trimmed={d['budget_trimmed_units']}"
    )
    for w in d["warnings"]:
        console.print(f"  [yellow]! {w}[/yellow]")
    for p in d["platforms"]:
        console.print(
            f"  {p['platform']:12s} {'→'.join(p['chain']):10s} tier={p['tier'] or '?'} "
            f"{p['units_out']:5d}/{p['units_in']:<5d} rated={p['rated_fraction']:.0%} "
            f"p50={p['bytes_est_p50'] / 1e9:6.2f}GB p90={(p['bytes_est_p90'] or 0) / 1e9:6.2f}GB  "
            f"q50={p['rating_quantiles'].get('p50', 0):.2f}  {p['prediction'][:40]}"
        )
        for w in p.get("warnings", []):
            console.print(f"      [yellow]! {w}[/yellow]")
    click.echo(f"\n({len(_json.dumps(d))} bytes of JSON)")
