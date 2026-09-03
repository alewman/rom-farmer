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
