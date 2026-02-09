"""
CLI commands for ROM scanning and validation.
"""

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import box

from romfarmer.catalog.database import RomGroomerDatabase
from romfarmer.scanner import RomScanner


console = Console()


@click.group(name='scan')
def scan_group():
    """Scan and validate ROM collections."""
    pass


@scan_group.command(name='directory')
@click.argument('directory', type=click.Path(exists=True, path_type=Path))
@click.option('--database', '-d', type=click.Path(path_type=Path),
              help='Database file (default: romfarmer.db)')
@click.option('--dat', help='Validate against specific DAT')
@click.option('--recursive/--no-recursive', default=True,
              help='Scan subdirectories recursively (default: recursive)')
@click.option('--extensions', '-e', multiple=True,
              help='File extensions to scan (e.g., -e .nes -e .sfc)')
@click.option('--md5', is_flag=True, default=False,
              help='Calculate MD5 hashes (slower)')
@click.option('--sha1', is_flag=True, default=False,
              help='Calculate SHA1 hashes (slower)')
@click.option('--workers', '-w', type=int, default=4,
              help='Number of parallel workers (default: 4)')
@click.option('--report', '-r', type=click.Path(path_type=Path),
              help='Output report to file')
@click.option('--show-unmatched', is_flag=True, default=False,
              help='Show unmatched files in output')
def scan_directory(directory, database, dat, recursive, extensions, md5, sha1, workers, report, show_unmatched):
    """
    Scan a directory for ROM files and validate against DAT.
    
    Examples:
        romfarmer scan directory /path/to/roms
        romfarmer scan directory /roms --dat "Nintendo - NES"
        romfarmer scan directory /roms --recursive --md5 --sha1
        romfarmer scan directory /roms -e .nes -e .sfc --workers 8
        romfarmer scan directory /roms --report scan_report.txt
    """
    db_path = database or Path('romfarmer.db')
    
    # Check if database exists
    if not db_path.exists():
        console.print(f"\n[red]Database not found: {db_path}[/red]")
        console.print("[yellow]Please import DAT files first using: romfarmer dat import[/yellow]\n")
        return
    
    db = RomGroomerDatabase(db_path)
    
    # Create scanner with options
    scanner_options = {
        'database': db,
        'calculate_md5': md5,
        'calculate_sha1': sha1,
        'num_workers': workers,
    }
    
    if extensions:
        scanner_options['extensions'] = set(extensions)
    
    scanner = RomScanner(**scanner_options)
    
    # Scan with progress indicator
    console.print(f"\n[bold blue]Scanning directory: {directory}[/bold blue]")
    console.print(f"[dim]Recursive: {recursive} | Workers: {workers} | DAT: {dat or 'All'}[/dim]\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning files...", total=None)
        
        results, stats = scanner.scan_directory(directory, recursive=recursive, dat_name=dat)
        
        progress.update(task, completed=True)
    
    # Display statistics
    _display_scan_statistics(stats)
    
    # Display matched files
    matched = [r for r in results if r.is_matched]
    if matched:
        _display_matched_files(matched)
    
    # Display unmatched files if requested
    if show_unmatched:
        unmatched = [r for r in results if not r.is_matched]
        if unmatched:
            _display_unmatched_files(unmatched)
    
    # Generate and save report if requested
    if report:
        report_text = scanner.generate_report(results, stats, output_path=report)
        console.print(f"\n[green]Report saved to: {report}[/green]\n")


@scan_group.command(name='missing')
@click.argument('dat_name')
@click.argument('directory', type=click.Path(exists=True, path_type=Path))
@click.option('--database', '-d', type=click.Path(path_type=Path),
              help='Database file (default: romfarmer.db)')
@click.option('--recursive/--no-recursive', default=True,
              help='Scan subdirectories recursively (default: recursive)')
@click.option('--limit', '-n', type=int, default=50,
              help='Maximum missing games to display (default: 50)')
@click.option('--output', '-o', type=click.Path(path_type=Path),
              help='Output missing games list to file')
def find_missing(dat_name, directory, database, recursive, limit, output):
    """
    Find games missing from your collection.
    
    Scans your ROM directory and compares against a DAT to identify
    which games you don't have.
    
    Examples:
        romfarmer scan missing "Nintendo - NES" /path/to/roms
        romfarmer scan missing "Sega - Genesis" /roms --limit 100
        romfarmer scan missing "Sony - PlayStation" /roms -o missing.txt
    """
    db_path = database or Path('romfarmer.db')
    
    if not db_path.exists():
        console.print(f"\n[red]Database not found: {db_path}[/red]\n")
        return
    
    db = RomGroomerDatabase(db_path)
    scanner = RomScanner(db)
    
    console.print(f"\n[bold blue]Finding missing games for: {dat_name}[/bold blue]")
    console.print(f"[dim]Scanning: {directory}[/dim]\n")
    
    # Scan directory
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning collection...", total=None)
        results, stats = scanner.scan_directory(directory, recursive=recursive, dat_name=dat_name)
        progress.update(task, completed=True)
    
    # Find missing games
    missing = scanner.find_missing_games(dat_name, results)
    
    if not missing:
        console.print(f"\n[green]✓ No missing games! Your collection is complete![/green]\n")
        return
    
    # Display summary
    total_games = stats.files_matched + len(missing)
    completion_rate = (stats.files_matched / total_games * 100) if total_games > 0 else 0
    
    summary_lines = [
        f"[bold cyan]Games in DAT:[/bold cyan] {total_games:,}",
        f"[bold green]Games Found:[/bold green] {stats.files_matched:,}",
        f"[bold red]Games Missing:[/bold red] {len(missing):,}",
        f"[bold yellow]Completion:[/bold yellow] {completion_rate:.1f}%",
    ]
    
    panel = Panel(
        "\n".join(summary_lines),
        title=f"Collection Status: {dat_name}",
        border_style="yellow",
        box=box.ROUNDED
    )
    
    console.print()
    console.print(panel)
    console.print()
    
    # Display missing games
    console.print(f"[bold]Missing Games (showing {min(limit, len(missing))} of {len(missing)}):[/bold]\n")
    
    table = Table(box=box.ROUNDED)
    table.add_column("Game", style="cyan", max_width=50)
    table.add_column("ROM File", style="yellow", max_width=30)
    table.add_column("CRC", style="red")
    table.add_column("Size", justify="right", style="blue")
    
    for game in missing[:limit]:
        size_kb = (game.size or 0) / 1024
        size_mb = size_kb / 1024
        size_str = f"{size_mb:.1f} MB" if size_mb >= 1 else f"{size_kb:.1f} KB"
        
        table.add_row(
            game.name or 'Unknown',
            game.rom_name or '-',
            game.crc or '-',
            size_str
        )
    
    console.print(table)
    
    if len(missing) > limit:
        console.print(f"\n[dim]... and {len(missing) - limit} more missing games. Use --limit to see more.[/dim]")
    
    console.print()
    
    # Write to output file if requested
    if output:
        try:
            with open(output, 'w') as f:
                for game in missing:
                    f.write(f"{game.name}\t{game.rom_name}\t{game.crc}\t{game.size}\n")
            console.print(f"[green]Missing games list written to: {output}[/green]\n")
        except Exception as e:
            console.print(f"[red]Failed to write output file: {e}[/red]\n")


@scan_group.command(name='verify')
@click.argument('file_path', type=click.Path(exists=True, path_type=Path))
@click.option('--database', '-d', type=click.Path(path_type=Path),
              help='Database file (default: romfarmer.db)')
@click.option('--dat', help='Validate against specific DAT')
@click.option('--md5', is_flag=True, default=False,
              help='Calculate MD5 hash')
@click.option('--sha1', is_flag=True, default=False,
              help='Calculate SHA1 hash')
def verify_file(file_path, database, dat, md5, sha1):
    """
    Verify a single ROM file against DAT.
    
    Calculates hashes and checks if the file matches any game in the database.
    
    Examples:
        romfarmer scan verify /path/to/game.nes
        romfarmer scan verify game.sfc --dat "Nintendo - SNES"
        romfarmer scan verify game.gba --md5 --sha1
    """
    db_path = database or Path('romfarmer.db')
    
    if not db_path.exists():
        console.print(f"\n[red]Database not found: {db_path}[/red]\n")
        return
    
    db = RomGroomerDatabase(db_path)
    scanner = RomScanner(db, calculate_md5=md5, calculate_sha1=sha1)
    
    console.print(f"\n[bold blue]Verifying file: {file_path.name}[/bold blue]\n")
    
    # Scan single file
    with Progress(
        SpinnerColumn(),
        TextColumn("Calculating hashes..."),
        console=console,
    ) as progress:
        task = progress.add_task("Processing", total=None)
        result = scanner._scan_file(file_path, dat_name=dat)
        progress.update(task, completed=True)
    
    if not result:
        console.print("[red]Failed to scan file[/red]\n")
        return
    
    # Display file info
    info_lines = [
        f"[bold cyan]File:[/bold cyan] {result.file_path.name}",
        f"[bold cyan]Size:[/bold cyan] {result.file_size:,} bytes ({result.file_size / 1024:.2f} KB)",
        f"[bold cyan]CRC32:[/bold cyan] {result.crc32}",
    ]
    
    if result.md5:
        info_lines.append(f"[bold cyan]MD5:[/bold cyan] {result.md5}")
    if result.sha1:
        info_lines.append(f"[bold cyan]SHA1:[/bold cyan] {result.sha1}")
    
    console.print("\n".join(info_lines))
    console.print()
    
    # Display match status
    if result.is_matched and result.matched_game:
        console.print(f"[bold green]✓ MATCH FOUND![/bold green]\n")
        
        match_lines = [
            f"[bold cyan]Game:[/bold cyan] {result.matched_game.name}",
            f"[bold cyan]DAT:[/bold cyan] {result.dat_name}",
            f"[bold cyan]ROM:[/bold cyan] {result.matched_game.rom_name}",
        ]
        
        if result.matched_game.description:
            match_lines.append(f"[bold cyan]Description:[/bold cyan] {result.matched_game.description}")
        
        panel = Panel(
            "\n".join(match_lines),
            title="Match Details",
            border_style="green",
            box=box.ROUNDED
        )
        
        console.print(panel)
    else:
        console.print(f"[bold yellow]⚠ No match found in database[/bold yellow]\n")
        console.print("[dim]This file doesn't match any known ROM in your imported DATs.[/dim]")
    
    console.print()


def _display_scan_statistics(stats):
    """Display scan statistics in a panel."""
    stats_lines = [
        f"[bold cyan]Files Scanned:[/bold cyan] {stats.total_files_scanned:,}",
        f"[bold blue]Total Size:[/bold blue] {stats.total_bytes_scanned / (1024**3):.2f} GB",
        f"[bold green]Files Matched:[/bold green] {stats.files_matched:,}",
        f"[bold yellow]Files Unmatched:[/bold yellow] {stats.files_unmatched:,}",
        f"[bold magenta]Unique Games:[/bold magenta] {stats.unique_games_found:,}",
        "",
        f"[bold]Match Rate:[/bold] {stats.files_matched / max(stats.total_files_scanned, 1) * 100:.1f}%",
        f"[bold]Scan Time:[/bold] {stats.scan_duration_seconds:.2f}s",
    ]
    
    panel = Panel(
        "\n".join(stats_lines),
        title="Scan Results",
        border_style="cyan",
        box=box.ROUNDED
    )
    
    console.print()
    console.print(panel)
    console.print()


def _display_matched_files(matched_results, limit=20):
    """Display matched files in a table."""
    console.print(f"[bold green]✓ Matched Files (showing {min(limit, len(matched_results))} of {len(matched_results)}):[/bold green]\n")
    
    table = Table(box=box.ROUNDED)
    table.add_column("File", style="yellow", max_width=30)
    table.add_column("Game", style="cyan", max_width=40)
    table.add_column("DAT", style="magenta", max_width=25)
    table.add_column("CRC", style="green")
    
    for result in matched_results[:limit]:
        table.add_row(
            result.file_path.name,
            result.matched_game.name if result.matched_game else '-',
            result.dat_name or '-',
            result.crc32
        )
    
    console.print(table)
    
    if len(matched_results) > limit:
        console.print(f"\n[dim]... and {len(matched_results) - limit} more matched files.[/dim]")
    
    console.print()


def _display_unmatched_files(unmatched_results, limit=20):
    """Display unmatched files in a table."""
    console.print(f"[bold yellow]⚠ Unmatched Files (showing {min(limit, len(unmatched_results))} of {len(unmatched_results)}):[/bold yellow]\n")
    
    table = Table(box=box.ROUNDED)
    table.add_column("File", style="yellow", max_width=40)
    table.add_column("CRC", style="red")
    table.add_column("Size", justify="right", style="blue")
    
    for result in unmatched_results[:limit]:
        size_mb = result.file_size / (1024**2)
        size_str = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{result.file_size / 1024:.2f} KB"
        
        table.add_row(
            result.file_path.name,
            result.crc32,
            size_str
        )
    
    console.print(table)
    
    if len(unmatched_results) > limit:
        console.print(f"\n[dim]... and {len(unmatched_results) - limit} more unmatched files.[/dim]")
    
    console.print()
