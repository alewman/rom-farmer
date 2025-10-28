#!/usr/bin/env python3
"""
Example: PS3 DAT filtering with MD5 matching

This script demonstrates how to use MD5-based DAT matching to handle
renamed files in the Redump PS3 collection.

Problem: Redump improved region naming (USA → USA, Asia), causing files
to fail filename-based DAT matching even though content is identical.

Solution: Pre-load MD5 hashes from ARRM database, then filter using
MD5-first matching with filename fallback.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from romgroomer.catalog.database import get_db_session, ScrapedGame
from romgroomer.config import load_platform_config
from romgroomer.dat_parser import RetoolDATParser
from romgroomer.stages import FilterDATStage, StageContext
from rich.console import Console


def populate_md5s_from_arrm(context: StageContext, system_id: int, console: Console):
    """
    Load MD5 hashes from ARRM database for PS3 games.
    
    Args:
        context: Stage context with source_files populated
        system_id: ARRM system ID (52 for PS3)
        console: Rich console for output
    """
    console.print("[cyan]Loading MD5 hashes from ARRM database...[/cyan]")
    
    session = get_db_session()
    loaded = 0
    
    for file_path in context.source_files:
        # Extract game name from ZIP filename
        # Example: "Dragon Age II (USA, Asia).zip" → "Dragon Age II (USA, Asia)"
        game_name = file_path.stem
        
        # Query ARRM database
        game = session.query(ScrapedGame).filter(
            ScrapedGame.system_id == system_id,
            ScrapedGame.name == game_name
        ).first()
        
        if game and game.md5:
            context.file_md5s[file_path] = game.md5.lower()
            loaded += 1
    
    session.close()
    
    console.print(f"  [green]Loaded {loaded:,} MD5 hashes from ARRM[/green]")
    console.print(f"  [yellow]Missing {len(context.source_files) - loaded:,} MD5s[/yellow]")


def main():
    """Run PS3 DAT filtering with MD5 matching."""
    console = Console()
    
    # Paths
    source_dir = Path("/data/emu/source/ps3")
    work_dir = Path("/data/emu/work/ps3-md5-test")
    output_dir = Path("/data/emu/output/ps3-md5-test")
    dat_file_path = Path("/data/emu/dats/redump/Sony - PlayStation 3.dat")
    
    # Validate paths
    if not source_dir.exists():
        console.print(f"[red]Error: Source directory not found: {source_dir}[/red]")
        return 1
    
    if not dat_file_path.exists():
        console.print(f"[red]Error: DAT file not found: {dat_file_path}[/red]")
        return 1
    
    # Load config
    console.print("[cyan]Loading PS3 configuration...[/cyan]")
    config = load_platform_config("ps3")
    
    # Parse DAT file
    console.print(f"[cyan]Parsing DAT file: {dat_file_path.name}[/cyan]")
    parser = RetoolDATParser()
    dat_file = parser.parse(dat_file_path)
    console.print(f"  [green]Games in DAT: {dat_file.get_game_count():,}[/green]")
    
    # Scan source files
    console.print(f"[cyan]Scanning source directory: {source_dir}[/cyan]")
    source_files = list(source_dir.glob("*.zip"))
    console.print(f"  [green]Found: {len(source_files):,} ZIP files[/green]")
    
    # Create directories
    work_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create context
    context = StageContext(
        platform_name="ps3",
        platform_config=config,
        target_name="ps3-usa-md5",
        source_dir=source_dir,
        work_dir=work_dir,
        output_dir=output_dir,
        dat_file=dat_file,
        source_files=source_files,
    )
    
    # Populate MD5s from ARRM (PS3 system_id = 52)
    populate_md5s_from_arrm(context, system_id=52, console=console)
    
    # Run filter stage
    console.print("\n[cyan]Running DAT filter with MD5 matching...[/cyan]")
    filter_stage = FilterDATStage()
    result = filter_stage.execute(context)
    
    # Display results
    console.print("\n[bold green]Results:[/bold green]")
    stats = context.stats["dat_filter"]
    console.print(f"  Source files: {stats['source_files']:,}")
    console.print(f"  Matched: {stats['matched_files']:,} ({stats['match_rate']:.1f}%)")
    
    if stats['hash_matched'] > 0:
        console.print(f"    [cyan]MD5 matched: {stats['hash_matched']:,}[/cyan]")
        console.print(f"      (These files were likely renamed since DAT was created)")
    
    if stats['name_matched'] > 0:
        console.print(f"    [cyan]Name matched: {stats['name_matched']:,}[/cyan]")
    
    if stats['unmatched_files'] > 0:
        console.print(f"  [yellow]Unmatched: {stats['unmatched_files']:,}[/yellow]")
        console.print(f"    (These may need investigation)")
    
    console.print(f"\n[green]Filtered files written to: {work_dir}[/green]")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
