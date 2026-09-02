"""
CLI commands for DAT file management.
"""

from pathlib import Path

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from romfarmer.catalog.database import RomGroomerDatabase
from romfarmer.dat.filter import OneGameOneRomFilter
from romfarmer.dat.importer import DatImportService

console = Console()


@click.group(name="dat")
def dat_group():
    """Manage DAT files (import, query, analyze)."""
    pass


@dat_group.command(name="import")
@click.argument("dat_files", type=click.Path(exists=True, path_type=Path), nargs=-1, required=True)
@click.option(
    "--database",
    "-d",
    type=click.Path(path_type=Path),
    help="Database file (default: romfarmer.db)",
)
@click.option(
    "--update", "-u", is_flag=True, default=False, help="Update existing DATs instead of skipping"
)
def import_dats(dat_files, database, update):
    """
    Import one or more DAT files into the database.

    Examples:
        romfarmer dat import nointro.dat
        romfarmer dat import *.dat --update
        romfarmer dat import nointro.dat redump.dat -d custom.db
    """
    db_path = database or Path("romfarmer.db")
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
        status = result.get("status", "success")
        if status == "error":
            table.add_row(result["dat_name"], f"[red]{status}[/red]", "-", "-")
        else:
            dat_name = result.get("dat_name", "Unknown")
            games = result.get("games_imported", result.get("total_games", 0))
            size_mb = result.get("total_size", 0) / (1024 * 1024)

            status_str = (
                "[green]imported[/green]" if status == "success" else f"[yellow]{status}[/yellow]"
            )
            table.add_row(dat_name, status_str, str(games), f"{size_mb:.1f} MB")

    console.print(table)
    console.print()


@dat_group.command(name="list")
@click.option(
    "--database",
    "-d",
    type=click.Path(path_type=Path),
    help="Database file (default: romfarmer.db)",
)
def list_dats(database):
    """
    List all imported DAT files.

    Examples:
        romfarmer dat list
        romfarmer dat list -d custom.db
    """
    db_path = database or Path("romfarmer.db")
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
        imported = dat.imported_at.strftime("%Y-%m-%d %H:%M") if dat.imported_at else "Unknown"

        table.add_row(
            dat.name,
            dat.version or "-",
            dat.author or "-",
            str(dat.total_games or 0),
            f"{size_mb:.1f} MB",
            imported,
        )

    console.print()
    console.print(table)
    console.print()


@dat_group.command(name="info")
@click.argument("dat_name")
@click.option(
    "--database",
    "-d",
    type=click.Path(path_type=Path),
    help="Database file (default: romfarmer.db)",
)
def dat_info(dat_name, database):
    """
    Show detailed information about a DAT file.

    Examples:
        romfarmer dat info "Nintendo - NES"
        romfarmer dat info "Sony - PlayStation" -d custom.db
    """
    db_path = database or Path("romfarmer.db")
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
        box=box.ROUNDED,
    )

    console.print()
    console.print(panel)
    console.print()


@dat_group.command(name="games")
@click.argument("dat_name")
@click.option(
    "--database",
    "-d",
    type=click.Path(path_type=Path),
    help="Database file (default: romfarmer.db)",
)
@click.option(
    "--limit", "-n", type=int, default=50, help="Maximum number of games to display (default: 50)"
)
def list_games(dat_name, database, limit):
    """
    List games from a DAT file.

    Examples:
        romfarmer dat games "Nintendo - NES"
        romfarmer dat games "Sony - PlayStation" --limit 100
        romfarmer dat games "Sega - Genesis" -n 10 -d custom.db
    """
    db_path = database or Path("romfarmer.db")
    db = RomGroomerDatabase(db_path)
    service = DatImportService(db)

    games = service.get_dat_games(dat_name, limit=limit)

    if not games:
        console.print(f"\n[yellow]No games found in DAT: {dat_name}[/yellow]\n")
        return

    table = Table(title=f"Games in {dat_name} (showing {len(games)})", box=box.ROUNDED)
    table.add_column("Name", style="cyan", max_width=50)
    table.add_column("ROM", style="yellow", max_width=30)
    table.add_column("Size", justify="right", style="blue")
    table.add_column("CRC", style="green")

    for game in games:
        size_kb = (game.size or 0) / 1024
        size_mb = size_kb / 1024
        size_str = f"{size_mb:.1f} MB" if size_mb >= 1 else f"{size_kb:.1f} KB"

        table.add_row(game.name or "Unknown", game.rom_name or "-", size_str, game.crc or "-")

    console.print()
    console.print(table)

    # Show total count if limited
    total_count = service.get_statistics(dat_name).get("total_games", 0)
    if total_count > len(games):
        console.print(
            f"\n[dim]Showing {len(games)} of {total_count} games. Use --limit to see more.[/dim]"
        )

    console.print()


@dat_group.command(name="search")
@click.argument("query")
@click.option(
    "--database",
    "-d",
    type=click.Path(path_type=Path),
    help="Database file (default: romfarmer.db)",
)
@click.option("--dat", help="Search within specific DAT")
@click.option("--by-crc", is_flag=True, default=False, help="Search by CRC instead of name")
def search_games(query, database, dat, by_crc):
    """
    Search for games by name or CRC.

    Examples:
        romfarmer dat search "Super Mario"
        romfarmer dat search "3337ec46" --by-crc
        romfarmer dat search "Zelda" --dat "Nintendo - NES"
        romfarmer dat search "mario" --dat "Nintendo - SNES" -d custom.db
    """
    db_path = database or Path("romfarmer.db")
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
        console.print(
            f"\n[yellow]No games found matching {search_type} '{query}'{scope}[/yellow]\n"
        )
        return

    scope_str = f" in {dat}" if dat else " (all DATs)"
    table = Table(
        title=f"Search Results for '{query}'{scope_str} ({len(games)} found)", box=box.ROUNDED
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
            game.dat_file.name if game.dat_file else "Unknown",
            game.name or "Unknown",
            game.rom_name or "-",
            game.crc or "-",
            size_str,
        )

    console.print()
    console.print(table)
    console.print()


@dat_group.command(name="delete")
@click.argument("dat_name")
@click.option(
    "--database",
    "-d",
    type=click.Path(path_type=Path),
    help="Database file (default: romfarmer.db)",
)
@click.option("--yes", "-y", is_flag=True, default=False, help="Skip confirmation prompt")
def delete_dat(dat_name, database, yes):
    """
    Delete a DAT file and all its games from the database.

    Examples:
        romfarmer dat delete "Nintendo - NES"
        romfarmer dat delete "Sony - PlayStation" --yes
        romfarmer dat delete "Sega - Genesis" -y -d custom.db
    """
    db_path = database or Path("romfarmer.db")
    db = RomGroomerDatabase(db_path)
    service = DatImportService(db)

    # Check if DAT exists
    dat = service.get_dat_info(dat_name)
    if not dat:
        console.print(f"\n[red]DAT not found: {dat_name}[/red]\n")
        return

    # Confirm deletion
    if not yes:
        console.print("\n[yellow]This will delete:[/yellow]")
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


@dat_group.command(name="stats")
@click.argument("dat_name", required=False)
@click.option(
    "--database",
    "-d",
    type=click.Path(path_type=Path),
    help="Database file (default: romfarmer.db)",
)
def show_stats(dat_name, database):
    """
    Show statistics for a specific DAT or all DATs.

    Examples:
        romfarmer dat stats
        romfarmer dat stats "Nintendo - NES"
        romfarmer dat stats "Sony - PlayStation" -d custom.db
    """
    db_path = database or Path("romfarmer.db")
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

    if "average_game_size" in stats:
        avg_size_mb = stats["average_game_size"] / (1024 * 1024)
        stats_lines.append(f"[bold yellow]Average Game Size:[/bold yellow] {avg_size_mb:.1f} MB")

    panel = Panel("\n".join(stats_lines), title=title, border_style="cyan", box=box.ROUNDED)

    console.print()
    console.print(panel)
    console.print()


@dat_group.command(name="filter")
@click.argument("dat_name")
@click.option(
    "--database",
    "-d",
    type=click.Path(path_type=Path),
    help="Database file (default: romfarmer.db)",
)
@click.option(
    "--regions", "-r", multiple=True, help="Region priority (e.g., -r USA -r Europe -r Japan)"
)
@click.option(
    "--languages", "-l", multiple=True, help="Language priority (e.g., -l En -l Ja -l Fr)"
)
@click.option(
    "--no-prefer-parents", is_flag=True, default=False, help="Don't prefer parent ROMs over clones"
)
@click.option(
    "--no-prefer-revisions", is_flag=True, default=False, help="Don't prefer later revisions"
)
@click.option(
    "--output", "-o", type=click.Path(path_type=Path), help="Output filtered game list to file"
)
def filter_1g1r(
    dat_name, database, regions, languages, no_prefer_parents, no_prefer_revisions, output
):
    """
    Apply 1G1R (One Game One ROM) filtering to a DAT.

    Filters games to select the best version of each game based on:
    - Region priorities (default: USA > World > Europe > Japan)
    - Language priorities (default: En > Ja > Fr > De)
    - Parent vs Clone preference
    - Revision numbers

    Examples:
        romfarmer dat filter "Nintendo - NES"
        romfarmer dat filter "Sega - Genesis" -r Japan -r USA
        romfarmer dat filter "Sony - PlayStation" -l En -l Ja
        romfarmer dat filter "Nintendo - SNES" --no-prefer-revisions
        romfarmer dat filter "Nintendo - NES" -o filtered_games.txt
    """
    db_path = database or Path("romfarmer.db")
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
        "prefer_parents": not no_prefer_parents,
        "prefer_later_revisions": not no_prefer_revisions,
    }

    if regions:
        filter_config["region_priority"] = list(regions)
    if languages:
        filter_config["language_priority"] = list(languages)

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
        box=box.ROUNDED,
    )

    console.print(panel)

    # Display sample of filtered games
    console.print("\n[bold]Sample of filtered games (first 20):[/bold]\n")

    table = Table(box=box.ROUNDED)
    table.add_column("Game", style="cyan", max_width=50)
    table.add_column("ROM", style="yellow", max_width=30)
    table.add_column("CRC", style="green")
    table.add_column("Size", justify="right", style="blue")

    for game in filtered_games[:20]:
        size_kb = (game.size or 0) / 1024
        size_mb = size_kb / 1024
        size_str = f"{size_mb:.1f} MB" if size_mb >= 1 else f"{size_kb:.1f} KB"

        table.add_row(game.name or "Unknown", game.rom_name or "-", game.crc or "-", size_str)

    console.print(table)

    if len(filtered_games) > 20:
        console.print(f"\n[dim]Showing 20 of {len(filtered_games)} filtered games.[/dim]\n")

    # Write to output file if requested
    if output:
        try:
            with open(output, "w") as f:
                for game in filtered_games:
                    f.write(f"{game.name}\t{game.rom_name}\t{game.crc}\n")
            console.print(f"[green]Filtered games written to: {output}[/green]\n")
        except Exception as e:
            console.print(f"[red]Failed to write output file: {e}[/red]\n")


@dat_group.command(name="generate")
@click.argument("source_dir", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output DAT file path (default: dats/generated/<name>.dat)",
)
@click.option(
    "--name", "-n", type=str, help="DAT name (default: derived from source directory name)"
)
@click.option(
    "--reference",
    "-r",
    type=click.Path(exists=True, path_type=Path),
    multiple=True,
    help="Reference DAT to enrich from (can specify multiple)",
)
@click.option(
    "--hash-outer",
    is_flag=True,
    default=False,
    help="Compute MD5/SHA1/CRC of outer files (slow for large files)",
)
@click.option(
    "--hash-zip-contents",
    is_flag=True,
    default=False,
    help="Open ZIPs and record inner file metadata with CRC",
)
@click.option(
    "--crc-from-zip",
    is_flag=True,
    default=False,
    help="Extract CRC32 from ZIP central directory (instant, no I/O)",
)
@click.option("--recursive", is_flag=True, default=False, help="Scan subdirectories recursively")
@click.option(
    "--workers",
    "-w",
    type=int,
    default=None,
    help="Number of parallel workers for hashing (default: CPU count)",
)
def generate_dat(
    source_dir,
    output,
    name,
    reference,
    hash_outer,
    hash_zip_contents,
    crc_from_zip,
    recursive,
    workers,
):
    """Generate a DAT file from a source ROM directory.

    Scans a directory of ROM files and creates a standard Logiqx XML DAT.
    Optionally enriches entries by fuzzy-matching against reference DATs
    to borrow category, description, and other metadata.

    Examples:
        romfarmer dat generate /path/to/wii-u-wux/
        romfarmer dat generate /path/to/roms/ -n "Nintendo - Wii U (WUX)"
        romfarmer dat generate /path/to/roms/ -r existing.dat -o custom.dat
        romfarmer dat generate /path/to/roms/ --hash-zip-contents
    """
    from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

    from romfarmer.dat_parser.generator import (
        enrich_from_reference,
        scan_source_directory,
        write_dat_xml,
    )
    from romfarmer.dat_parser.parser import DATParser

    # Derive DAT name from source directory if not specified
    if not name:
        name = source_dir.name

    console.print(f"\n[bold blue]Generating DAT from:[/bold blue] {source_dir}")
    console.print(f"[bold blue]DAT name:[/bold blue] {name}\n")

    # Scan source directory
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning source files...", total=None)

        def on_scan_progress(current, total, filename):
            progress.update(
                task, total=total, completed=current, description=f"Scanning: {filename[:50]}"
            )

        games = scan_source_directory(
            source_dir,
            compute_hashes=hash_outer,
            hash_zip_contents=hash_zip_contents,
            crc_from_zip=crc_from_zip,
            recursive=recursive,
            workers=workers,
            progress_callback=on_scan_progress,
        )

    console.print(f"  [green]Found {len(games)} files[/green]")

    # Enrich from reference DATs
    total_enriched = 0
    for ref_path in reference:
        ref_path = Path(ref_path)
        console.print(f"\n[bold cyan]Enriching from reference:[/bold cyan] {ref_path.name}")

        # Handle ZIP-compressed reference DATs
        if ref_path.suffix.lower() == ".zip":
            import tempfile
            import zipfile

            with tempfile.TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(ref_path, "r") as zf:
                    dat_files = [f for f in zf.namelist() if f.endswith(".dat")]
                    if not dat_files:
                        console.print(f"  [red]No .dat file found in {ref_path.name}[/red]")
                        continue
                    zf.extract(dat_files[0], tmpdir)
                    extracted = Path(tmpdir) / dat_files[0]
                    parser = DATParser()
                    ref_dat = parser.parse(extracted)
        else:
            parser = DATParser()
            ref_dat = parser.parse(ref_path)

        console.print(f"  Reference contains {ref_dat.get_game_count()} games")

        matched, total = enrich_from_reference(games, ref_dat)
        total_enriched += matched
        console.print(
            f"  [green]Matched {matched}/{total} games ({matched * 100 // max(total, 1)}%)[/green]"
        )

    # Determine output path
    if not output:
        output = Path("dats/generated") / f"{name}.dat"

    # Write DAT
    written = write_dat_xml(
        games,
        output,
        dat_name=name,
    )

    # Summary
    console.print(f"\n[bold green]DAT generated:[/bold green] {written}")
    console.print(f"  Games: {len(games)}")
    total_size = sum(g.get_total_size() for g in games)
    if total_size > 0:
        console.print(f"  Total size: {total_size / (1024**3):.2f} GB")
    if total_enriched:
        console.print(f"  Enriched from reference: {total_enriched}")
    console.print()


# ── Clone list maintenance commands ──────────────────────────────────────


@dat_group.command(name="diff")
@click.argument("old_dat", type=click.Path(exists=True, path_type=Path))
@click.argument("new_dat", type=click.Path(exists=True, path_type=Path))
def diff_dats(old_dat, new_dat):
    """Compare two DAT versions by hash — detect renames, additions, removals.

    Uses SHA1 > MD5 > CRC to track games across versions. Games with the
    same hash but different names are renames (title corrections, region changes).

    Examples:
        romfarmer dat diff old-redump-wii.dat new-redump-wii.dat
        romfarmer dat diff dats/wii-2024.dat dats/wii-2026.dat
    """
    from romfarmer.dat_parser.clonelist import dat_diff
    from romfarmer.dat_parser.parser import DATParser

    parser = DATParser()
    console.print("\n[bold blue]Diffing DATs:[/bold blue]")
    console.print(f"  Old: {old_dat.name}")
    console.print(f"  New: {new_dat.name}\n")

    old_parsed = _parse_dat(parser, old_dat)
    new_parsed = _parse_dat(parser, new_dat)

    result = dat_diff(old_parsed, new_parsed)

    # Summary
    console.print(f"  Old: {result.old_count} games")
    console.print(f"  New: {result.new_count} games\n")

    if not result.has_changes:
        console.print("[green]No changes detected.[/green]\n")
        return

    # Renames
    if result.renames:
        table = Table(title=f"Renames ({len(result.renames)})", box=box.SIMPLE)
        table.add_column("Old Name", style="red")
        table.add_column("New Name", style="green")
        for r in result.renames:
            table.add_row(r.old_name, r.new_name)
        console.print(table)

    # Additions
    if result.additions:
        console.print(f"\n[bold green]Additions ({len(result.additions)}):[/bold green]")
        for name in result.additions[:20]:
            console.print(f"  + {name}")
        if len(result.additions) > 20:
            console.print(f"  ... and {len(result.additions) - 20} more")

    # Removals
    if result.removals:
        console.print(f"\n[bold red]Removals ({len(result.removals)}):[/bold red]")
        for name in result.removals[:20]:
            console.print(f"  - {name}")
        if len(result.removals) > 20:
            console.print(f"  ... and {len(result.removals) - 20} more")

    console.print()


@dat_group.command(name="clonelist-validate")
@click.argument("clonelist", type=click.Path(exists=True, path_type=Path))
@click.argument("dat_file", type=click.Path(exists=True, path_type=Path))
def validate_clonelist(clonelist, dat_file):
    """Validate a Retool clone list against a DAT — find broken searchTerms.

    Checks every searchTerm in the clone list against the DAT's game names.
    Reports unmatched terms with fuzzy suggestions for likely fixes.

    Examples:
        romfarmer dat clonelist-validate Nintendo\\ -\\ Wii.json redump-wii.dat
    """
    from romfarmer.dat_parser.clonelist import clonelist_validate
    from romfarmer.dat_parser.parser import DATParser

    parser = DATParser()
    console.print(f"\n[bold blue]Validating clone list:[/bold blue] {clonelist.name}")
    console.print(f"[bold blue]Against DAT:[/bold blue] {dat_file.name}\n")

    dat = _parse_dat(parser, dat_file)
    result = clonelist_validate(clonelist, dat)

    console.print(f"  Total searchTerms: {result.total_search_terms}")
    console.print(f"  Matched: {result.matched}")
    console.print(f"  Match rate: {result.match_rate:.1%}\n")

    if result.unmatched:
        table = Table(title=f"Unmatched ({len(result.unmatched)})", box=box.SIMPLE)
        table.add_column("Group", style="cyan")
        table.add_column("searchTerm", style="red")
        table.add_column("Suggestion", style="green")
        table.add_column("Sim", style="dim")
        for u in result.unmatched:
            table.add_row(
                u.group[:40],
                u.search_term,
                u.suggestion or "-",
                f"{u.similarity:.0%}" if u.suggestion else "",
            )
        console.print(table)
    else:
        console.print("[green]All searchTerms matched![/green]")

    console.print()


@dat_group.command(name="clonelist-patch")
@click.argument("clonelist", type=click.Path(exists=True, path_type=Path))
@click.argument("old_dat", type=click.Path(exists=True, path_type=Path))
@click.argument("new_dat", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output path (default: overwrite in place)",
)
@click.option("--dry-run", is_flag=True, default=False, help="Show patches without applying")
def patch_clonelist(clonelist, old_dat, new_dat, output, dry_run):
    """Auto-patch clone list searchTerms from DAT renames.

    Diffs two DAT versions to find renames, then updates matching
    searchTerms in the clone list. Dry-run shows proposed changes
    without writing.

    Examples:
        romfarmer dat clonelist-patch wii.json old.dat new.dat --dry-run
        romfarmer dat clonelist-patch wii.json old.dat new.dat -o patched.json
    """
    from romfarmer.dat_parser.clonelist import clonelist_patch, dat_diff
    from romfarmer.dat_parser.parser import DATParser

    parser = DATParser()
    console.print(f"\n[bold blue]Patching clone list:[/bold blue] {clonelist.name}")
    console.print(f"  Old DAT: {old_dat.name}")
    console.print(f"  New DAT: {new_dat.name}")
    if dry_run:
        console.print("  [yellow]DRY RUN — no files will be modified[/yellow]")
    console.print()

    old_parsed = _parse_dat(parser, old_dat)
    new_parsed = _parse_dat(parser, new_dat)

    diff_result = dat_diff(old_parsed, new_parsed)
    console.print(f"  DAT diff: {len(diff_result.renames)} renames found\n")

    if not diff_result.renames:
        console.print("[green]No renames to patch.[/green]\n")
        return

    out_path = output if output else None
    result = clonelist_patch(clonelist, diff_result, output_path=out_path, dry_run=dry_run)

    patches = result.patches_applied if not dry_run else result.patches_skipped
    if patches:
        table = Table(title=f"Patches ({'proposed' if dry_run else 'applied'})", box=box.SIMPLE)
        table.add_column("Group", style="cyan")
        table.add_column("Old", style="red")
        table.add_column("New", style="green")
        table.add_column("Reason", style="dim")
        for p in patches:
            table.add_row(p.group[:40], p.old_search_term, p.new_search_term, p.reason)
        console.print(table)
    else:
        console.print("[yellow]No matching searchTerms found for the renames.[/yellow]")

    console.print()


@dat_group.command(name="metadata-generate")
@click.argument("dat_file", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output JSON path")
def generate_metadata(dat_file, output):
    """Auto-generate Retool metadata JSON from DAT game names.

    Extracts language codes from filenames (e.g., (En,Fr,De)) or infers
    from region tags (USA → En, Japan → Ja). Output is Retool-compatible JSON.

    Examples:
        romfarmer dat metadata-generate redump-wii.dat -o wii-metadata.json
    """
    import json as _json

    from romfarmer.dat_parser.clonelist import metadata_generate, metadata_to_retool_json
    from romfarmer.dat_parser.parser import DATParser

    parser = DATParser()
    console.print(f"\n[bold blue]Generating metadata from:[/bold blue] {dat_file.name}\n")

    dat = _parse_dat(parser, dat_file)
    entries = metadata_generate(dat)
    retool_json = metadata_to_retool_json(entries)

    with_langs = sum(1 for e in entries if e.languages)
    console.print(f"  Total entries: {len(entries)}")
    console.print(f"  With languages: {with_langs} ({with_langs * 100 // max(len(entries), 1)}%)")

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w", encoding="utf-8") as f:
            _json.dump(retool_json, f, indent=2, ensure_ascii=False)
            f.write("\n")
        console.print(f"\n[green]Written to: {output}[/green]")
    else:
        # Show sample
        sample_keys = list(retool_json.keys())[:5]
        console.print("\n[bold]Sample:[/bold]")
        for key in sample_keys:
            console.print(f"  {key}: {retool_json[key]}")
        console.print("  ...")

    console.print()


# ── Shared helper ────────────────────────────────────────────────────────


def _parse_dat(parser, path):
    """Parse a DAT file, handling ZIPs."""
    if path.suffix.lower() == ".zip":
        import tempfile
        import zipfile

        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(path, "r") as zf:
                dat_files = [f for f in zf.namelist() if f.endswith(".dat")]
                if not dat_files:
                    console.print(f"[red]No .dat file in {path.name}[/red]")
                    raise SystemExit(1)
                zf.extract(dat_files[0], tmpdir)
                return parser.parse(Path(tmpdir) / dat_files[0])
    return parser.parse(path)
