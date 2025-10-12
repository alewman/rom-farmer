"""
CLI commands for DAT file management.
"""

import click
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from romgroomer.catalog.database import RomGroomerDatabase
from romgroomer.dat.importer import DatImportService
from romgroomer.dat.filter import OneGameOneRomFilter


console = Console()


@click.group(name='dat')
def dat_group():
    """Manage DAT files (import, query, analyze)."""
    pass


@dat_group.command(name='import')
@click.argument('dat_files', type=click.Path(exists=True, path_type=Path), nargs=-1, required=True)
@click.option('--database', '-d', type=click.Path(path_type=Path), 
              help='Database file (default: romgroomer.db)')
@click.option('--update', '-u', is_flag=True, default=False,
              help='Update existing DATs instead of skipping')
def import_dats(dat_files, database, update):
    """
    Import one or more DAT files into the database.
    
    Examples:
        romgroomer dat import nointro.dat
        romgroomer dat import *.dat --update
        romgroomer dat import nointro.dat redump.dat -d custom.db
    """
    db_path = database or Path('romgroomer.db')
    db = RomGroomerDatabase(db_path)
    service = DatImportService(db)
    
    console.print(f"\n[bold blue]Importing {len(dat_files)} DAT file(s)...[/bold blue]\n")
    
    results = service.import_dats(list(dat_files), update_existing=update)
    
    # Display results
    table = Table(title="Import Results", box=box.ROUNDED)
    table.add_column("DAT Name", style="cyan")
    table.add_column("Status", style="yellow")
    table.add_column("Games", justify="right", style="green")
    table.add_column("Size", justify="right", style="blue")
    
    for result in results:
        status = result.get('status', 'success')
        if status == 'error':
            table.add_row(
                result['dat_name'],
                f"[red]{status}[/red]",
                "-",
                "-"
            )
        else:
            dat_name = result.get('dat_name', 'Unknown')
            games = result.get('games_imported', result.get('total_games', 0))
            size_mb = result.get('total_size', 0) / (1024 * 1024)
            
            status_str = "[green]imported[/green]" if status == 'success' else f"[yellow]{status}[/yellow]"
            table.add_row(
                dat_name,
                status_str,
                str(games),
                f"{size_mb:.1f} MB"
            )
    
    console.print(table)
    console.print()


@dat_group.command(name='list')
@click.option('--database', '-d', type=click.Path(path_type=Path),
              help='Database file (default: romgroomer.db)')
def list_dats(database):
    """
    List all imported DAT files.
    
    Examples:
        romgroomer dat list
        romgroomer dat list -d custom.db
    """
    db_path = database or Path('romgroomer.db')
    db = RomGroomerDatabase(db_path)
    service = DatImportService(db)
    
    dats = service.list_imported_dats()
    
    if not dats:
        console.print("\n[yellow]No DAT files imported yet.[/yellow]\n")
        return
    
    table = Table(title=f"Imported DATs ({len(dats)})", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="yellow")
    table.add_column("Author", style="magenta")
    table.add_column("Games", justify="right", style="green")
    table.add_column("Size", justify="right", style="blue")
    table.add_column("Imported", style="dim")
    
    for dat in dats:
        size_mb = (dat.total_size or 0) / (1024 * 1024)
        imported = dat.imported_at.strftime('%Y-%m-%d %H:%M') if dat.imported_at else 'Unknown'
        
        table.add_row(
            dat.name,
            dat.version or '-',
            dat.author or '-',
            str(dat.total_games or 0),
            f"{size_mb:.1f} MB",
            imported
        )
    
    console.print()
    console.print(table)
    console.print()


@dat_group.command(name='info')
@click.argument('dat_name')
@click.option('--database', '-d', type=click.Path(path_type=Path),
              help='Database file (default: romgroomer.db)')
def dat_info(dat_name, database):
    """
    Show detailed information about a DAT file.
    
    Examples:
        romgroomer dat info "Nintendo - NES"
        romgroomer dat info "Sony - PlayStation" -d custom.db
    """
    db_path = database or Path('romgroomer.db')
    db = RomGroomerDatabase(db_path)
    service = DatImportService(db)
    
    dat = service.get_dat_info(dat_name)
    
    if not dat:
        console.print(f"\n[red]DAT not found: {dat_name}[/red]\n")
        return
    
    # Build info text
    info_lines = [
        f"[bold cyan]Name:[/bold cyan] {dat.name}",
        f"[bold cyan]Description:[/bold cyan] {dat.description or 'N/A'}",
        f"[bold cyan]Version:[/bold cyan] {dat.version or 'N/A'}",
        f"[bold cyan]Author:[/bold cyan] {dat.author or 'N/A'}",
        f"[bold cyan]Date:[/bold cyan] {dat.date or 'N/A'}",
        "",
        f"[bold green]Total Games:[/bold green] {dat.total_games or 0:,}",
        f"[bold blue]Total Size:[/bold blue] {(dat.total_size or 0) / (1024 * 1024):.1f} MB",
        "",
        f"[bold yellow]Imported:[/bold yellow] {dat.imported_at.strftime('%Y-%m-%d %H:%M:%S') if dat.imported_at else 'Unknown'}",
        f"[bold yellow]Updated:[/bold yellow] {dat.updated_at.strftime('%Y-%m-%d %H:%M:%S') if dat.updated_at else 'N/A'}",
    ]
    
    panel = Panel(
        "\n".join(info_lines),
        title=f"DAT Information: {dat.name}",
        border_style="cyan",
        box=box.ROUNDED
    )
    
    console.print()
    console.print(panel)
    console.print()


@dat_group.command(name='games')
@click.argument('dat_name')
@click.option('--database', '-d', type=click.Path(path_type=Path),
              help='Database file (default: romgroomer.db)')
@click.option('--limit', '-n', type=int, default=50,
              help='Maximum number of games to display (default: 50)')
def list_games(dat_name, database, limit):
    """
    List games from a DAT file.
    
    Examples:
        romgroomer dat games "Nintendo - NES"
        romgroomer dat games "Sony - PlayStation" --limit 100
        romgroomer dat games "Sega - Genesis" -n 10 -d custom.db
    """
    db_path = database or Path('romgroomer.db')
    db = RomGroomerDatabase(db_path)
    service = DatImportService(db)
    
    games = service.get_dat_games(dat_name, limit=limit)
    
    if not games:
        console.print(f"\n[yellow]No games found in DAT: {dat_name}[/yellow]\n")
        return
    
    table = Table(
        title=f"Games in {dat_name} (showing {len(games)})",
        box=box.ROUNDED
    )
    table.add_column("Name", style="cyan", max_width=50)
    table.add_column("ROM", style="yellow", max_width=30)
    table.add_column("Size", justify="right", style="blue")
    table.add_column("CRC", style="green")
    
    for game in games:
        size_kb = (game.size or 0) / 1024
        size_mb = size_kb / 1024
        size_str = f"{size_mb:.1f} MB" if size_mb >= 1 else f"{size_kb:.1f} KB"
        
        table.add_row(
            game.name or 'Unknown',
            game.rom_name or '-',
            size_str,
            game.crc or '-'
        )
    
    console.print()
    console.print(table)
    
    # Show total count if limited
    total_count = service.get_statistics(dat_name).get('total_games', 0)
    if total_count > len(games):
        console.print(f"\n[dim]Showing {len(games)} of {total_count} games. Use --limit to see more.[/dim]")
    
    console.print()


@dat_group.command(name='search')
@click.argument('query')
@click.option('--database', '-d', type=click.Path(path_type=Path),
              help='Database file (default: romgroomer.db)')
@click.option('--dat', help='Search within specific DAT')
@click.option('--by-crc', is_flag=True, default=False,
              help='Search by CRC instead of name')
def search_games(query, database, dat, by_crc):
    """
    Search for games by name or CRC.
    
    Examples:
        romgroomer dat search "Super Mario"
        romgroomer dat search "3337ec46" --by-crc
        romgroomer dat search "Zelda" --dat "Nintendo - NES"
        romgroomer dat search "mario" --dat "Nintendo - SNES" -d custom.db
    """
    db_path = database or Path('romgroomer.db')
    db = RomGroomerDatabase(db_path)
    service = DatImportService(db)
    
    if by_crc:
        game = service.find_game_by_crc(query, dat_name=dat)
        games = [game] if game else []
        search_type = "CRC"
    else:
        games = service.find_games_by_name(query, dat_name=dat)
        search_type = "name"
    
    if not games:
        scope = f" in {dat}" if dat else ""
        console.print(f"\n[yellow]No games found matching {search_type} '{query}'{scope}[/yellow]\n")
        return
    
    scope_str = f" in {dat}" if dat else " (all DATs)"
    table = Table(
        title=f"Search Results for '{query}'{scope_str} ({len(games)} found)",
        box=box.ROUNDED
    )
    table.add_column("DAT", style="magenta", max_width=30)
    table.add_column("Game", style="cyan", max_width=40)
    table.add_column("ROM", style="yellow", max_width=30)
    table.add_column("CRC", style="green")
    table.add_column("Size", justify="right", style="blue")
    
    for game in games:
        size_kb = (game.size or 0) / 1024
        size_mb = size_kb / 1024
        size_str = f"{size_mb:.1f} MB" if size_mb >= 1 else f"{size_kb:.1f} KB"
        
        table.add_row(
            game.dat_file.name if game.dat_file else 'Unknown',
            game.name or 'Unknown',
            game.rom_name or '-',
            game.crc or '-',
            size_str
        )
    
    console.print()
    console.print(table)
    console.print()


@dat_group.command(name='delete')
@click.argument('dat_name')
@click.option('--database', '-d', type=click.Path(path_type=Path),
              help='Database file (default: romgroomer.db)')
@click.option('--yes', '-y', is_flag=True, default=False,
              help='Skip confirmation prompt')
def delete_dat(dat_name, database, yes):
    """
    Delete a DAT file and all its games from the database.
    
    Examples:
        romgroomer dat delete "Nintendo - NES"
        romgroomer dat delete "Sony - PlayStation" --yes
        romgroomer dat delete "Sega - Genesis" -y -d custom.db
    """
    db_path = database or Path('romgroomer.db')
    db = RomGroomerDatabase(db_path)
    service = DatImportService(db)
    
    # Check if DAT exists
    dat = service.get_dat_info(dat_name)
    if not dat:
        console.print(f"\n[red]DAT not found: {dat_name}[/red]\n")
        return
    
    # Confirm deletion
    if not yes:
        console.print(f"\n[yellow]This will delete:[/yellow]")
        console.print(f"  DAT: {dat.name}")
        console.print(f"  Games: {dat.total_games or 0:,}")
        console.print()
        
        if not click.confirm("Are you sure you want to delete this DAT?"):
            console.print("[dim]Cancelled.[/dim]\n")
            return
    
    # Delete
    success = service.delete_dat(dat_name)
    
    if success:
        console.print(f"\n[green]Successfully deleted DAT: {dat_name}[/green]\n")
    else:
        console.print(f"\n[red]Failed to delete DAT: {dat_name}[/red]\n")


@dat_group.command(name='stats')
@click.argument('dat_name', required=False)
@click.option('--database', '-d', type=click.Path(path_type=Path),
              help='Database file (default: romgroomer.db)')
def show_stats(dat_name, database):
    """
    Show statistics for a specific DAT or all DATs.
    
    Examples:
        romgroomer dat stats
        romgroomer dat stats "Nintendo - NES"
        romgroomer dat stats "Sony - PlayStation" -d custom.db
    """
    db_path = database or Path('romgroomer.db')
    db = RomGroomerDatabase(db_path)
    service = DatImportService(db)
    
    stats = service.get_statistics(dat_name)
    
    if not stats:
        if dat_name:
            console.print(f"\n[red]DAT not found: {dat_name}[/red]\n")
        else:
            console.print("\n[yellow]No DATs imported yet.[/yellow]\n")
        return
    
    # Build stats display
    title = f"Statistics: {dat_name}" if dat_name else "Overall Statistics"
    
    stats_lines = [
        f"[bold cyan]Total DATs:[/bold cyan] {stats.get('total_dats', 0):,}",
        f"[bold green]Total Games:[/bold green] {stats.get('total_games', 0):,}",
        f"[bold blue]Total Size:[/bold blue] {stats.get('total_size', 0) / (1024 * 1024 * 1024):.2f} GB",
    ]
    
    if 'average_game_size' in stats:
        avg_size_mb = stats['average_game_size'] / (1024 * 1024)
        stats_lines.append(f"[bold yellow]Average Game Size:[/bold yellow] {avg_size_mb:.1f} MB")
    
    panel = Panel(
        "\n".join(stats_lines),
        title=title,
        border_style="cyan",
        box=box.ROUNDED
    )
    
    console.print()
    console.print(panel)
    console.print()


@dat_group.command(name='filter')
@click.argument('dat_name')
@click.option('--database', '-d', type=click.Path(path_type=Path),
              help='Database file (default: romgroomer.db)')
@click.option('--regions', '-r', multiple=True,
              help='Region priority (e.g., -r USA -r Europe -r Japan)')
@click.option('--languages', '-l', multiple=True,
              help='Language priority (e.g., -l En -l Ja -l Fr)')
@click.option('--no-prefer-parents', is_flag=True, default=False,
              help='Don\'t prefer parent ROMs over clones')
@click.option('--no-prefer-revisions', is_flag=True, default=False,
              help='Don\'t prefer later revisions')
@click.option('--output', '-o', type=click.Path(path_type=Path),
              help='Output filtered game list to file')
def filter_1g1r(dat_name, database, regions, languages, no_prefer_parents, no_prefer_revisions, output):
    """
    Apply 1G1R (One Game One ROM) filtering to a DAT.
    
    Filters games to select the best version of each game based on:
    - Region priorities (default: USA > World > Europe > Japan)
    - Language priorities (default: En > Ja > Fr > De)
    - Parent vs Clone preference
    - Revision numbers
    
    Examples:
        romgroomer dat filter "Nintendo - NES"
        romgroomer dat filter "Sega - Genesis" -r Japan -r USA
        romgroomer dat filter "Sony - PlayStation" -l En -l Ja
        romgroomer dat filter "Nintendo - SNES" --no-prefer-revisions
        romgroomer dat filter "Nintendo - NES" -o filtered_games.txt
    """
    db_path = database or Path('romgroomer.db')
    db = RomGroomerDatabase(db_path)
    service = DatImportService(db)
    
    # Get games from DAT
    games = service.get_dat_games(dat_name, limit=None)
    
    if not games:
        console.print(f"\n[yellow]No games found in DAT: {dat_name}[/yellow]\n")
        return
    
    console.print(f"\n[bold blue]Filtering {len(games)} games from {dat_name}...[/bold blue]\n")
    
    # Create filter with custom preferences
    filter_config = {
        'prefer_parents': not no_prefer_parents,
        'prefer_later_revisions': not no_prefer_revisions,
    }
    
    if regions:
        filter_config['region_priority'] = list(regions)
    if languages:
        filter_config['language_priority'] = list(languages)
    
    filter_obj = OneGameOneRomFilter(**filter_config)
    
    # Apply filter
    filtered_games, stats = filter_obj.filter_games(games)
    
    # Display statistics
    stats_lines = [
        f"[bold cyan]Total Games:[/bold cyan] {stats.total_games:,}",
        f"[bold green]Unique Games:[/bold green] {stats.unique_games:,}",
        f"[bold yellow]Filtered Games:[/bold yellow] {stats.filtered_games:,}",
        f"[bold red]Duplicates Removed:[/bold red] {stats.duplicates_removed:,}",
        "",
        f"[bold blue]Parents Selected:[/bold blue] {stats.parents_selected:,}",
        f"[bold magenta]Clones Selected:[/bold magenta] {stats.clones_selected:,}",
    ]
    
    panel = Panel(
        "\n".join(stats_lines),
        title=f"1G1R Filter Results: {dat_name}",
        border_style="green",
        box=box.ROUNDED
    )
    
    console.print(panel)
    
    # Display sample of filtered games
    console.print(f"\n[bold]Sample of filtered games (first 20):[/bold]\n")
    
    table = Table(box=box.ROUNDED)
    table.add_column("Game", style="cyan", max_width=50)
    table.add_column("ROM", style="yellow", max_width=30)
    table.add_column("CRC", style="green")
    table.add_column("Size", justify="right", style="blue")
    
    for game in filtered_games[:20]:
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
    
    if len(filtered_games) > 20:
        console.print(f"\n[dim]Showing 20 of {len(filtered_games)} filtered games.[/dim]\n")
    
    # Write to output file if requested
    if output:
        try:
            with open(output, 'w') as f:
                for game in filtered_games:
                    f.write(f"{game.name}\t{game.rom_name}\t{game.crc}\n")
            console.print(f"[green]Filtered games written to: {output}[/green]\n")
        except Exception as e:
            console.print(f"[red]Failed to write output file: {e}[/red]\n")
