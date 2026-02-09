#!/usr/bin/env python3
"""Demo script for Saturn multi-disc processing with M3U creation.

This demonstrates Phase 4: Redump/Saturn pipeline with:
- ZIP extraction
- CHD compression
- M3U creation for multi-disc games
- Metadata from first disc
"""

import shutil
import tempfile
from pathlib import Path

from rich.console import Console
from rich.tree import Tree

from romfarmer.config.loader import load_platform_config
from romfarmer.dat_parser import RetoolDATParser
from romfarmer.stages import (
    ApplyListsStage,
    CompressCHDStage,
    CreateM3UStage,
    ExtractArchiveStage,
    FilterDATStage,
    OrganizeStage,
    Pipeline,
)


def find_saturn_dat() -> Path:
    """Find Saturn Retool DAT file."""
    dat_dir = Path("/data/emu/dats/redump.retool.1g1r.usa")
    
    # Look for Saturn DAT
    dats = list(dat_dir.glob("Sega - Saturn*.dat"))
    if not dats:
        raise FileNotFoundError(f"No Saturn DAT found in {dat_dir}")
    
    return dats[0]


def find_saturn_source() -> Path:
    """Find Saturn source directory."""
    # Myrient archive
    source = Path("/data/emu/archive/archive.myrient.erista.me/files/Redump/Sega - Saturn")
    
    if not source.exists():
        raise FileNotFoundError(f"Saturn source not found: {source}")
    
    return source


def main():
    """Run Saturn demo pipeline."""
    console = Console()
    
    console.print("\n[bold cyan]═══ Phase 4 Demo: Saturn Multi-Disc Processing ═══[/bold cyan]\n")
    
    # Load Saturn config
    console.print("[yellow]Loading Saturn configuration...[/yellow]")
    saturn_config = load_platform_config("saturn")
    
    console.print(f"[green]✓[/green] System type: {saturn_config.system_type.value}")
    console.print(f"[green]✓[/green] Extract archives: {saturn_config.extract_archives}")
    console.print(f"[green]✓[/green] Multi-disc handling: {saturn_config.multi_disc_handling}")
    
    # Find Retool DAT
    console.print("\n[yellow]Finding Saturn Retool DAT...[/yellow]")
    dat_path = find_saturn_dat()
    console.print(f"[green]✓[/green] Found: {dat_path.name}")
    
    # Find source directory
    console.print("\n[yellow]Finding Saturn source ROMs...[/yellow]")
    source_dir = find_saturn_source()
    console.print(f"[green]✓[/green] Source: {source_dir}")
    
    # Count available ZIPs
    all_zips = list(source_dir.glob("*.zip"))
    console.print(f"[green]✓[/green] Found {len(all_zips):,} Saturn ZIPs")
    
    # For demo, use a small subset - look for multi-disc games
    multi_disc_zips = [
        z for z in all_zips
        if "(Disc" in z.name or "(Disk" in z.name
    ][:10]  # First 10 multi-disc ZIPs
    
    if not multi_disc_zips:
        console.print("[yellow]No multi-disc games found, using first 3 ZIPs[/yellow]")
        multi_disc_zips = all_zips[:3]
    
    console.print(f"[cyan]Demo will process {len(multi_disc_zips)} ZIPs for testing[/cyan]")
    for zip_file in multi_disc_zips:
        console.print(f"  • {zip_file.name}")
    
    # Create temporary directories
    temp_base = Path(tempfile.mkdtemp(prefix="saturn_demo_"))
    console.print(f"\n[dim]Using temp directory: {temp_base}[/dim]")
    
    try:
        # Create work directories
        source_copy = temp_base / "source"
        work_dir = temp_base / "work"
        output_dir = temp_base / "output"
        
        source_copy.mkdir()
        work_dir.mkdir()
        output_dir.mkdir()
        
        # Copy demo ZIPs to temp
        console.print("\n[yellow]Copying demo ZIPs to temp directory...[/yellow]")
        for zip_file in multi_disc_zips:
            shutil.copy2(zip_file, source_copy)
        
        # Create pipeline for Saturn (Redump system)
        console.print("\n[bold]Creating Saturn processing pipeline...[/bold]")
        pipeline = Pipeline(
            platform_config=saturn_config,
            target_name=saturn_config.targets[0].name,
            console=console,
        )
        
        # Create database session for transformation recording
        from romfarmer.metadata.database import MetadataDatabase
        from pathlib import Path as ImportedPath
        db = MetadataDatabase(ImportedPath(__file__).parent.parent / "metadata" / "database" / "romfarmer.db")
        db_session = db.get_session()
        
        # Add stages in order
        pipeline.add_stage(FilterDATStage())
        pipeline.add_stage(ApplyListsStage())
        pipeline.add_stage(ExtractArchiveStage())
        pipeline.add_stage(CompressCHDStage(db_session=db_session))  # Pass db_session!
        pipeline.add_stage(CreateM3UStage())
        pipeline.add_stage(OrganizeStage())
        
        console.print(f"[green]✓[/green] Pipeline configured with {len(pipeline.stages)} stages")
        
        # Execute pipeline
        console.print("\n[bold cyan]═══ Executing Pipeline ═══[/bold cyan]\n")
        
        results = pipeline.execute(
            source_dir=source_copy,
            work_dir=work_dir,
            output_dir=output_dir,
            dat_file_path=dat_path,
        )
        
        # Show final output structure
        console.print("\n[bold]Final Output Structure:[/bold]")
        tree = Tree(f"[bold]{output_dir}[/bold]")
        
        for item in sorted(output_dir.rglob("*")):
            if item.is_file():
                rel_path = item.relative_to(output_dir)
                size_mb = item.stat().st_size / (1024 * 1024)
                
                # Highlight M3U files
                if item.suffix == ".m3u":
                    tree.add(f"[bold yellow]{rel_path}[/bold yellow] ({size_mb:.2f} MB) ⭐ PRIMARY")
                elif item.suffix == ".chd":
                    tree.add(f"[cyan]{rel_path}[/cyan] ({size_mb:.2f} MB)")
                else:
                    tree.add(f"{rel_path} ({size_mb:.2f} MB)")
        
        console.print(tree)
        
        # Show M3U contents
        m3u_files = list(output_dir.rglob("*.m3u"))
        if m3u_files:
            console.print(f"\n[bold]M3U Playlist Files ({len(m3u_files)}):[/bold]")
            for m3u in m3u_files:
                console.print(f"\n[yellow]{m3u.name}[/yellow]:")
                with open(m3u, 'r') as f:
                    for line in f:
                        console.print(f"  [dim]→[/dim] {line.strip()}")
        
    finally:
        # Cleanup temp directory
        console.print(f"\n[dim]Cleaning up temp directory: {temp_base}[/dim]")
        shutil.rmtree(temp_base, ignore_errors=True)
    
    console.print("\n[bold green]✓ Saturn demo complete![/bold green]\n")


if __name__ == "__main__":
    main()
