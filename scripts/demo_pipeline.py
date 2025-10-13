#!/usr/bin/env python3
"""Demo: Complete No-Intro pipeline with NES ROMs.

This demonstrates Phase 3:
1. Load platform config (NES)
2. Parse Retool DAT (1,761 games)
3. Filter source ZIPs against DAT
4. Apply list files (delete unwanted, organize into subdirs)
5. Organize with target style (balanced/minimal)
6. Generate final collection

This is a DRY RUN with first 20 ROMs to avoid touching the background hash job!
"""

from pathlib import Path
import tempfile
import shutil

from rich.console import Console

from romgroomer.config import load_platform_config
from romgroomer.stages import FilterDATStage, ApplyListsStage, OrganizeStage
from romgroomer.stages.pipeline import Pipeline

console = Console()


def main():
    """Run NES pipeline demo."""
    console.print(
        "\n[bold cyan]═══════════════════════════════════════════[/bold cyan]"
    )
    console.print("[bold white]  ROM Groomer Phase 3 Demo: NES Pipeline [/bold white]")
    console.print("[bold cyan]═══════════════════════════════════════════[/bold cyan]\n")

    # Load NES config
    console.print("[cyan]Loading NES platform configuration...[/cyan]")
    platform = load_platform_config("nes")
    console.print(f"  Platform: {platform.name}")
    console.print(f"  System Type: {platform.system_type.value}")
    console.print(f"  Expected Games: {platform.dat.expected_count:,}")

    # Find DAT file
    dat_dir = Path("/data/emu/dats/nointro.retool.1g1r.eng/")
    dat_files = list(dat_dir.glob("Nintendo - Nintendo Entertainment System*.dat"))

    if not dat_files:
        console.print("[red]✗ NES Retool DAT not found![/red]")
        return

    dat_file = dat_files[0]
    console.print(f"  DAT File: {dat_file.name}")

    # Find source directory
    source_base = Path("/data/emu/archive/archive.myrient.erista.me/files/No-Intro")
    source_dir = source_base / "Nintendo - Nintendo Entertainment System (Headered)"

    if not source_dir.exists():
        console.print(f"[red]✗ Source directory not found: {source_dir}[/red]")
        return

    console.print(f"  Source: {source_dir}")

    # Create temporary working directories
    with tempfile.TemporaryDirectory(prefix="romgroomer_demo_") as temp_base:
        temp_path = Path(temp_base)
        work_dir = temp_path / "work"
        output_dir = temp_path / "output"

        console.print(f"  Work Dir: {work_dir}")
        console.print(f"  Output Dir: {output_dir}")

        # DRY RUN: Copy just first 20 ZIPs to temp location
        console.print("\n[yellow]DRY RUN: Using first 20 ZIPs only[/yellow]")
        temp_source = temp_path / "source"
        temp_source.mkdir()

        source_zips = sorted(source_dir.glob("*.zip"))[:20]
        for zip_file in source_zips:
            shutil.copy2(zip_file, temp_source)

        console.print(f"  Copied {len(source_zips)} ZIPs to temp source")

        # Create pipeline
        pipeline = Pipeline(
            platform_config=platform,
            target_name="rocknix",
            console=console,
        )

        # Add stages
        pipeline.add_stage(FilterDATStage())
        pipeline.add_stage(ApplyListsStage())
        pipeline.add_stage(OrganizeStage())

        # Execute
        console.print("\n[bold green]Starting Pipeline...[/bold green]\n")
        results = pipeline.execute(
            source_dir=temp_source,
            work_dir=work_dir,
            output_dir=output_dir,
            dat_file_path=dat_file,
        )

        # Show final structure
        console.print("\n[bold cyan]Final Output Structure:[/bold cyan]")
        show_tree(output_dir, console, max_depth=2)

        # Cleanup info
        console.print(
            f"\n[dim]Temporary files will be automatically cleaned up: {temp_base}[/dim]"
        )


def show_tree(path: Path, console: Console, max_depth: int = 2, _depth: int = 0, _prefix: str = ""):
    """Show directory tree structure.

    Args:
        path: Directory to show
        console: Rich console
        max_depth: Maximum depth to show
        _depth: Current depth (internal)
        _prefix: Prefix for indentation (internal)
    """
    if _depth > max_depth:
        return

    if _depth == 0:
        console.print(f"[cyan]{path}/[/cyan]")

    items = sorted(path.iterdir())
    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        connector = "└── " if is_last else "├── "
        new_prefix = _prefix + ("    " if is_last else "│   ")

        if item.is_dir():
            count = len(list(item.iterdir()))
            console.print(f"{_prefix}{connector}[cyan]{item.name}/[/cyan] ({count} items)")
            if _depth < max_depth:
                show_tree(item, console, max_depth, _depth + 1, new_prefix)
        else:
            size_mb = item.stat().st_size / (1024 * 1024)
            console.print(f"{_prefix}{connector}{item.name} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
