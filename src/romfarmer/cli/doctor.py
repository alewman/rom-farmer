"""``romfarmer doctor`` — environment and determinism checks.

``romfarmer doctor`` reports which external tools the transforms can find.
``romfarmer doctor --determinism`` runs each available transform twice on a
tiny synthetic fixture (with the input's mtime changed between runs) and
reports whether the output bytes are identical.  This is the empirical check
behind the reproducibility claim; the flag table in the transforms is only a
hypothesis until this passes on the operator's machine.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from romfarmer.engine.transforms.archive import ArchiveTransform
from romfarmer.engine.transforms.chd import CHDTransform
from romfarmer.engine.transforms.squashfs import SquashFSTransform
from romfarmer.ir.tool_impl import IMPL_VERSIONS
from romfarmer.planner.lowering.base import probe_tool_version

console = Console()

# Deterministic pseudo-random payload: same bytes on every machine, so the
# report can be compared across hosts.
_SEED = b"romfarmer-doctor"


def _payload(size: int) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < size:
        out += hashlib.sha256(_SEED + counter.to_bytes(4, "big")).digest()
        counter += 1
    return bytes(out[:size])


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass(frozen=True)
class _Probe:
    tool: str
    make_fixture: Callable[[Path], list[Path]]
    run: Callable[[list[Path], Path], list[Path]]


def _fixture_file(root: Path) -> list[Path]:
    p = root / "Game (USA).bin"
    p.write_bytes(_payload(300_000))
    return [p]


def _fixture_cue(root: Path) -> list[Path]:
    (root / "Game (USA).bin").write_bytes(_payload(2352 * 64))
    cue = root / "Game (USA).cue"
    cue.write_text('FILE "Game (USA).bin" BINARY\n  TRACK 01 MODE1/2352\n    INDEX 01 00:00:00\n')
    return [cue]


def _fixture_dir(root: Path) -> list[Path]:
    d = root / "Game (USA)"
    d.mkdir()
    (d / "default.xbe").write_bytes(_payload(100_000))
    (d / "data.bin").write_bytes(_payload(200_000))
    return [d]


_PROBES: list[_Probe] = [
    _Probe("7z", _fixture_file, lambda i, s: ArchiveTransform().run(i, {"format": "7z"}, s)),
    _Probe("7z (zip)", _fixture_file, lambda i, s: ArchiveTransform().run(i, {"format": "zip"}, s)),
    _Probe("chdman", _fixture_cue, lambda i, s: CHDTransform().run(i, {"mode": "createcd"}, s)),
    _Probe("mksquashfs", _fixture_dir, lambda i, s: SquashFSTransform().run(i, {}, s)),
]


def _touch_all(paths: list[Path]) -> None:
    """Bump mtimes so timestamp leaks show up as a hash difference."""
    later = time.time() + 86400
    for p in paths:
        targets = [p, *p.rglob("*")] if p.is_dir() else [p]
        for t in targets:
            os.utime(t, (later, later))


def _run_probe(probe: _Probe) -> tuple[str, str]:
    """Return (status, detail) for one transform."""
    with tempfile.TemporaryDirectory(prefix="romfarmer-doctor-") as tmp:
        root = Path(tmp)
        fixture_dir = root / "fixture"
        fixture_dir.mkdir()
        inputs = probe.make_fixture(fixture_dir)
        hashes: list[str] = []
        for n in (1, 2):
            scratch = root / f"scratch{n}"
            scratch.mkdir()
            try:
                outputs = probe.run(inputs, scratch)
            except Exception as exc:  # tool missing or failed — report, don't abort
                return "unavailable", str(exc)[:80]
            hashes.append(",".join(_sha256(o) for o in sorted(outputs)))
            _touch_all(inputs)
    if hashes[0] == hashes[1]:
        return "deterministic", hashes[0][:16]
    return "NON-DETERMINISTIC", f"{hashes[0][:16]} != {hashes[1][:16]}"


_TOOL_BINARIES = {
    "7z": ("7z", "7zz", "7za"),
    "chdman": ("chdman",),
    "mksquashfs": ("mksquashfs",),
    "extract-xiso": ("extract-xiso", "tools/bin/extract-xiso"),
    "dolphin-tool": ("dolphin-tool", "tools/bin/dolphin-tool"),
    "wit": ("wit", "tools/bin/wit"),
    "ps3dec": ("ps3dec", "tools/bin/ps3dec"),
}


def _locate(candidates: tuple[str, ...]) -> Path | None:
    for c in candidates:
        found = shutil.which(c)
        if found:
            return Path(found)
        if Path(c).exists():
            return Path(c).resolve()
    return None


def _check_builds(builds: tuple[str, ...]) -> int:
    """RESOLVE-only health check per platform; returns the number of problems."""
    import logging

    from romfarmer.new_orchestrator import NewBuildOrchestrator
    from romfarmer.planner.negotiation import negotiate_format_chain, negotiate_with_profile

    logging.disable(logging.WARNING)  # _find_dat_file warns; the table reports it
    problems = 0
    for build in builds:
        try:
            orch = NewBuildOrchestrator.from_config(build)
        except Exception as exc:
            console.print(f"[red]{build}: cannot load — {str(exc).splitlines()[-1][:160]}[/red]")
            problems += 1
            continue
        profile = orch._load_target_profile()
        table = Table(title=f"{build}  (target: {orch.build_spec.target})")
        for col in ("Platform", "Type", "Sources", "DAT", "Chain"):
            table.add_column(col)
        for r in orch.resolved_configs:
            srcs = [s.path for s in (r.sources or ()) if s.path is not None]
            missing = [p for p in srcs if not p.exists()]
            src_cell = (
                f"[red]{len(missing)}/{len(srcs)} missing[/red]" if missing else f"{len(srcs)} ok"
            )
            dat_needed = (
                r.dat is not None and "none" not in str(getattr(r.dat, "source", "")).lower()
            )
            dat_file = orch._find_dat_file(r) if dat_needed else None
            if not dat_needed:
                dat_cell = "[dim]n/a[/dim]"
            elif dat_file:
                dat_cell = dat_file.name[:48]
            else:
                dat_cell = "[red]missing[/red]"
            try:
                chain = negotiate_with_profile(r, profile) if profile else negotiate_format_chain(r)
                chain_cell = "→".join(chain)
            except Exception as exc:
                chain_cell = f"[red]{str(exc)[:70]}[/red]"
            bad = bool(missing) or (dat_needed and not dat_file) or chain_cell.startswith("[red]")
            problems += int(bad)
            table.add_row(r.platform, r.extraction_type.value, src_cell, dat_cell, chain_cell)
        console.print(table)
    console.print(
        f"\n{problems} problem(s)" if problems else "\n[green]all platforms resolve[/green]"
    )
    return 1 if problems else 0


@click.command("doctor")
@click.option(
    "--determinism", is_flag=True, help="Run each transform twice and compare output bytes."
)
@click.option(
    "--build",
    "builds",
    multiple=True,
    help="Check every platform of a build (source dirs, DAT, format negotiation). Repeatable.",
)
def doctor(determinism: bool, builds: tuple[str, ...]) -> None:
    """Check external tools, build configs and, optionally, byte-reproducibility."""
    if builds:
        raise click.exceptions.Exit(_check_builds(builds))

    table = Table(title="External tools", show_lines=False)
    table.add_column("Tool")
    table.add_column("Found")
    table.add_column("Version (as keyed)")
    table.add_column("impl", justify="right")
    for tool, candidates in _TOOL_BINARIES.items():
        path = _locate(candidates)
        version = probe_tool_version(str(path)) if path else "-"
        table.add_row(
            tool,
            str(path) if path else "[red]missing[/red]",
            version,
            str(IMPL_VERSIONS.get(tool, 1)),
        )
    console.print(table)

    if not determinism:
        return

    console.print()
    det = Table(title="Determinism (run twice, input mtime changed between runs)")
    det.add_column("Transform")
    det.add_column("Result")
    det.add_column("Detail")
    failures = 0
    for probe in _PROBES:
        status, detail = _run_probe(probe)
        color = {"deterministic": "green", "unavailable": "yellow"}.get(status, "red")
        if status == "NON-DETERMINISTIC":
            failures += 1
        det.add_row(probe.tool, f"[{color}]{status}[/{color}]", detail)
    det.add_row("extract-xiso", "[yellow]not probed[/yellow]", "requires a real XISO fixture")
    console.print(det)
    if failures:
        raise click.exceptions.Exit(1)
