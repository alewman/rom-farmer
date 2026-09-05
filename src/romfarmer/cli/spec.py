"""``romfarmer spec`` — the SPEC seam from the command line.

romfarmer spec lower <build>          # legacy build → Spec YAML (+ hash), freezes lists/ into artifacts/
romfarmer spec validate <spec.yaml>   # loud validation + resolve every platform
romfarmer spec hash <spec.yaml>
romfarmer spec run <spec.yaml>        # RESOLVE→CATALOG→PLAN→EXECUTE→EMIT — the EXECUTE door
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


@spec_group.command("run")
@click.argument("spec_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--validate-only", is_flag=True, help="Validate + RESOLVE only (no source scan, no files)."
)
@click.option(
    "--dry-run", "dry_run", is_flag=True, help="RESOLVE→CATALOG→PLAN and stop. No files written."
)
@click.option("--output-dir", type=click.Path(path_type=Path), help="Override the staging directory.")
@click.option("--yes", "-y", is_flag=True, help="Skip the confirmation prompt.")
def spec_run(
    spec_file: Path,
    validate_only: bool,
    dry_run: bool,
    output_dir: Path | None,
    yes: bool,
) -> None:
    """Run SPEC_FILE: RESOLVE -> CATALOG -> PLAN -> EXECUTE -> EMIT, to a staging directory.

    This is the deterministic door across the SPEC boundary: everything it
    does follows from the frozen Spec alone, with no model call in the path.
    It only ever writes under the staging directory (default
    ``output/spec-<hash12>``) and stamps a ``spec_manifest.json`` there with
    the ``spec_hash`` this output was built from.  It never touches a
    physical device — that is the separate, explicitly gated ``--deploy``
    step on the legacy build path.
    """
    from romfarmer.core.paths import get_paths
    from romfarmer.driver.spec_io import load_spec
    from romfarmer.driver.spec_resolve import resolve_build
    from romfarmer.ir.spec import SpecError
    from romfarmer.new_orchestrator import run_spec

    ws = Path(get_paths().workspace_root)
    try:
        spec = load_spec(spec_file)
        builds = resolve_build(spec, ws / "config", workspace_root=ws, output_base=output_dir)
    except SpecError as exc:
        console.print(f"[red]{exc}[/red]")
        raise SystemExit(1) from exc

    out_base = output_dir or ws / "output" / f"spec-{spec.spec_hash()[:12]}"
    console.print(f"[cyan]spec_hash[/cyan] {spec.spec_hash()}")
    console.print(f"[cyan]staging[/cyan]   {out_base}")
    console.print(f"[cyan]platforms[/cyan] {', '.join(rb.platform for rb in builds)}")

    if validate_only:
        console.print("[green]ok[/green] — RESOLVE passed for every platform")
        return

    if not dry_run and not yes:
        if not click.confirm(
            f"\nRun EXECUTE and write to {out_base}?", default=True
        ):
            console.print("[yellow]cancelled[/yellow]")
            return

    report = run_spec(spec, ws / "config", workspace_root=ws, output_base=output_dir, dry_run=dry_run)

    for p in report.platforms:
        if p.planned_only:
            console.print(f"  [yellow]{p.platform:14s} [dry-run] {p.terminal_count} units planned[/yellow]")
            continue
        console.print(
            f"  {p.platform:14s} chain={'→'.join(p.chain):10s} "
            f"{p.terminal_count} units  {p.actual_bytes / 1e9:.2f} GB"
            + (f"  [red]{len(p.failed_units)} failed[/red]" if p.failed_units else "")
            + (f"  [yellow]{p.budget_stopped} budget-stopped[/yellow]" if p.budget_stopped else "")
        )

    if dry_run:
        console.print("[yellow]--dry-run complete — no files written[/yellow]")
        return

    manifest_path = report.write_provenance(spec)
    console.print(
        f"[green]done[/green] {report.total_actual_bytes / 1e9:.2f} GB written to {report.output_base}"
    )
    console.print(f"[green]provenance[/green] {manifest_path}")


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
