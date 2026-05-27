"""
CLI commands for metadata testing and debugging.

Commands:
- test-dat: Test DAT manager and hash capture
- test-transform: Test transformation recording
"""

from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from ..metadata.database import MetadataDatabase
from ..metadata.dat_manager import DATManager
from ..metadata.hash_capture import SmartHashCapture
from ..metadata.transformation_recorder import TransformationRecorder

console = Console()


@click.command(name="test-dat")
@click.option(
    "--dat-dirs",
    "-d",
    type=click.Path(exists=True, path_type=Path),
    multiple=True,
    help="DAT directories to load (can specify multiple)",
)
@click.option(
    "--test-file",
    "-f",
    type=click.Path(exists=True, path_type=Path),
    help="Test file to hash",
)
@click.option(
    "--system",
    "-s",
    help="System name for DAT lookup",
)
@click.option(
    "--database",
    type=click.Path(path_type=Path),
    default="metadata/database/romfarmer.db",
    help="Path to metadata database",
)
def test_dat(
    dat_dirs: tuple,
    test_file: Optional[Path],
    system: Optional[str],
    database: Path,
):
    """
    Test DAT manager and hash capture system.
    
    This command loads DAT files and tests the 3-tier hash capture:
    1. DAT file lookup (instant)
    2. Hash cache (fast)
    3. Calculate (slow)
    
    Example:
    
        # Load DATs and show statistics
        rom-farmer metadata test-dat -d /path/to/dats/redump -d /path/to/dats/nointro
        
        # Test hash capture on a file
        rom-farmer metadata test-dat -d /path/to/dats/redump \\
            -f /path/to/stage/saturn/3D\ Baseball\ \(USA\).chd \\
            -s saturn
    """
    try:
        # Load DAT manager
        if dat_dirs:
            console.print(f"[cyan]Loading DAT files from {len(dat_dirs)} directories...[/cyan]")
            dat_manager = DATManager(list(dat_dirs))
            
            # Show DAT statistics
            console.print(f"\n[bold green]✓ DAT Manager Loaded[/bold green]")
            console.print(f"  Systems: {dat_manager.get_system_count()}")
            console.print(f"  Total Entries: {dat_manager.get_entry_count():,}")
            console.print(f"\n[bold]Available Systems:[/bold]")
            for sys in sorted(dat_manager.get_systems())[:20]:
                console.print(f"  - {sys}")
            if dat_manager.get_system_count() > 20:
                console.print(f"  ... and {dat_manager.get_system_count() - 20} more")
        else:
            console.print("[yellow]No DAT directories specified. Using cache/calculation only.[/yellow]")
            dat_manager = None
        
        # Test hash capture if file specified
        if test_file:
            console.print(f"\n[bold cyan]Testing Hash Capture[/bold cyan]")
            console.print(f"File: {test_file}")
            console.print(f"Size: {test_file.stat().st_size / (1024*1024):.1f} MB")
            
            if system:
                console.print(f"System: {system}")
            
            # Create database and hash capture
            db = MetadataDatabase(database)
            with db.get_session() as session:
                capture = SmartHashCapture(dat_manager, session)
                
                # Get hashes
                console.print("\n[cyan]Capturing hashes...[/cyan]")
                hashes = capture.get_source_hashes(test_file, system)
                
                # Show results
                console.print(f"\n[bold green]✓ Hash Capture Complete[/bold green]")
                
                if hashes.from_dat:
                    console.print(f"  [green]Source: DAT file ({hashes.dat_name})[/green]")
                elif hashes.from_cache:
                    console.print(f"  [yellow]Source: Hash cache[/yellow]")
                else:
                    console.print(f"  [red]Source: Calculated ({hashes.calculation_time:.1f}s)[/red]")
                
                console.print(f"\n  MD5:    {hashes.md5}")
                console.print(f"  SHA1:   {hashes.sha1}")
                console.print(f"  SHA256: {hashes.sha256}")
                console.print(f"  CRC32:  {hashes.crc32}")
                console.print(f"  Size:   {hashes.size:,} bytes")
                
                # Show performance stats
                console.print()
                capture.print_stats()
        
        elif dat_dirs:
            console.print("\n[yellow]Tip: Use --test-file to test hash capture on a ROM file[/yellow]")
    
    except FileNotFoundError as e:
        console.print(f"[red]✗ File not found:[/red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        raise click.Abort()


@click.command(name="test-transform")
@click.option(
    "--dat-dirs",
    "-d",
    type=click.Path(exists=True, path_type=Path),
    multiple=True,
    help="DAT directories to load",
)
@click.option(
    "--source-file",
    "-s",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Source file (before transformation)",
)
@click.option(
    "--final-file",
    "-f",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Final file (after transformation)",
)
@click.option(
    "--system",
    type=str,
    required=True,
    help="System name (e.g., 'saturn', 'xbox360')",
)
@click.option(
    "--tool",
    type=str,
    default="manual",
    help="Transformation tool name",
)
@click.option(
    "--version",
    type=str,
    default="unknown",
    help="Tool version",
)
@click.option(
    "--database",
    type=click.Path(path_type=Path),
    default="metadata/database/romfarmer.db",
    help="Path to metadata database",
)
def test_transform(
    dat_dirs: tuple,
    source_file: Path,
    final_file: Path,
    system: str,
    tool: str,
    version: str,
    database: Path,
):
    """
    Test transformation recording.
    
    This command simulates recording a ROM transformation. Use this to test
    the transformation tracking system before integrating it into your
    ROM processing workflow.
    
    Example:
    
        # Record a Saturn ISO → CHD transformation
        rom-farmer metadata test-transform \\
            -d /path/to/dats/redump \\
            -s /path/to/source/saturn/game.iso \\
            -f /path/to/stage/saturn/game.chd \\
            --system saturn \\
            --tool chdman \\
            --version 0.251
    
    This will:
    1. Look up source ISO hash in Redump DAT (instant!)
    2. Calculate CHD hash (or use cache)
    3. Store transformation: ISO hash → CHD hash
    4. Show statistics
    """
    try:
        # Load DAT manager if specified
        dat_manager = None
        if dat_dirs:
            console.print(f"[cyan]Loading DAT files...[/cyan]")
            dat_manager = DATManager(list(dat_dirs))
            console.print(f"[green]✓ Loaded {dat_manager.get_entry_count():,} entries[/green]")
        
        # Create database and recorder
        db = MetadataDatabase(database)
        
        with db.get_session() as session:
            recorder = TransformationRecorder(session, dat_manager)
            
            # Simulate a transformation
            console.print("\n[bold cyan]Simulating Transformation Recording...[/bold cyan]")
            
            with recorder.record_transformation(
                source_file=source_file,
                system=system,
                tool=tool,
                version=version,
                params={"test": True, "simulated": True}
            ) as transform:
                # In real workflow, processing would happen here
                # For testing, we just set the final file that already exists
                transform.set_final_file(final_file)
            
            # Show statistics
            console.print()
            recorder.print_stats()
            
            # Test reverse lookup
            console.print(f"\n[bold cyan]Testing Reverse Lookup...[/bold cyan]")
            found = recorder.find_source_hash(final_file)
            
            if found:
                console.print(f"[green]✓ Successfully found source hash for final file![/green]")
                console.print(f"  Source: {found.source_file_name}")
                console.print(f"  Final: {found.final_file_name}")
                console.print(f"  Tool: {found.transformation_tool} v{found.transformation_version}")
                console.print(f"  Duration: {found.transformation_duration_seconds:.1f}s")
    
    except FileNotFoundError as e:
        console.print(f"[red]✗ File not found:[/red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        raise click.Abort()
