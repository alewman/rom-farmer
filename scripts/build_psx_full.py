#!/usr/bin/env python3
"""Full PSX build - process all 10,870 games with CHD compression and metadata."""

import shutil
import sys
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from romgroomer.config.loader import load_platform_config
from romgroomer.dat_parser import RetoolDATParser
from romgroomer.stages import (
    ApplyListsStage,
    CompressCHDStage,
    CreateM3UStage,
    ExtractArchiveStage,
    FilterDATStage,
    OrganizeStage,
    Pipeline,
)
from romgroomer.metadata.database import MetadataDatabase


def main():
    """Run full PSX build."""
    console = Console()
    
    console.print("\n[bold cyan]═══ Full PSX Build - All 10,870 Games ═══[/bold cyan]\n")
    
    # Paths
    source_dir = Path("/data/emu/source/myrient.erista.me/files/Redump/Sony - PlayStation")
    work_dir = Path("/data/emu/temp/psx-full-build")
    output_dir = Path("/data/emu/output/psx-full")
    dat_path = Path("/data/emu/dats/redump.retool.1g1r.usa/Sony - PlayStation (2024-12-20 19-04-10) (Retool 2025-02-20 22-15-31) (1,476) (-dn) [-AaBbcdekmMoPrv].dat")
    
    # Database for transformation recording
    db_path = Path(__file__).parent.parent / "metadata" / "database" / "romgroomer.db"
    
    console.print(f"[yellow]Source:[/yellow] {source_dir}")
    console.print(f"[yellow]Output:[/yellow] {output_dir}")
    console.print(f"[yellow]DAT:[/yellow] 1G1R USA (1,476 games)")
    console.print(f"[yellow]Database:[/yellow] {db_path}")
    
    # Count source files
    source_zips = list(source_dir.glob("*.zip"))
    console.print(f"[green]✓[/green] Found {len(source_zips):,} PSX ZIPs\n")
    
    # Create directories
    work_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load PSX config
    console.print("[yellow]Loading PSX configuration...[/yellow]")
    psx_config = load_platform_config("psx")
    
    # Create database session for transformation recording
    console.print("[yellow]Connecting to metadata database...[/yellow]")
    db = MetadataDatabase(db_path)
    db_session = db.get_session()
    
    # Create pipeline
    console.print("\n[bold]Creating PSX processing pipeline...[/bold]")
    pipeline = Pipeline(
        platform_config=psx_config,
        target_name=psx_config.targets[0].name,
        console=console,
    )
    
    # Add stages with database session for CHD compression
    pipeline.add_stage(FilterDATStage())
    pipeline.add_stage(ApplyListsStage())
    pipeline.add_stage(ExtractArchiveStage())
    pipeline.add_stage(CompressCHDStage(db_session=db_session))  # Pass DB session!
    pipeline.add_stage(CreateM3UStage())
    pipeline.add_stage(OrganizeStage())
    
    console.print(f"[green]✓[/green] Pipeline configured with {len(pipeline.stages)} stages")
    
    # Log start time
    start_time = datetime.now()
    console.print(f"\n[bold cyan]═══ Starting Build at {start_time.strftime('%Y-%m-%d %H:%M:%S')} ═══[/bold cyan]\n")
    
    # Execute pipeline
    try:
        results = pipeline.execute(
            source_dir=source_dir,
            work_dir=work_dir,
            output_dir=output_dir,
            dat_file_path=dat_path,
        )
        
        # Calculate duration
        end_time = datetime.now()
        duration = end_time - start_time
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)
        
        console.print(f"\n[bold green]✓ Full PSX build completed![/bold green]")
        console.print(f"  Duration: {hours}h {minutes}m")
        console.print(f"  Output: {output_dir}")
        
        # Count output files
        chd_files = list(output_dir.rglob("*.chd"))
        m3u_files = list(output_dir.rglob("*.m3u"))
        
        console.print(f"\n[bold]Final Results:[/bold]")
        console.print(f"  CHD files: {len(chd_files):,}")
        console.print(f"  M3U playlists: {len(m3u_files):,}")
        
        # Calculate total size
        total_size = sum(f.stat().st_size for f in chd_files)
        total_gb = total_size / (1024**3)
        console.print(f"  Total size: {total_gb:.1f} GB")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Build interrupted by user[/yellow]")
        return 1
    except Exception as e:
        console.print(f"\n[red]Build failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db_session.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
