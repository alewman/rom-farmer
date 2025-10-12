"""
CLI commands for metadata management.

Commands:
- import-arrm: Import ARRM gamelist.xml
- generate: Generate gamelist.xml for ROM directory
- info: Show metadata database statistics
- list: List games in database
"""

from pathlib import Path
from typing import Optional, List

import click
from rich.console import Console
from rich.table import Table

from ..metadata.database import MetadataDatabase
from ..metadata.arrm import ARRMImporter, print_import_stats
from ..metadata.generator import GamelistGenerator, print_generation_stats

console = Console()


@click.group(name="metadata")
def metadata_group():
    """Manage game metadata and media files."""
    pass


@metadata_group.command(name="import-arrm")
@click.argument("gamelist_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--database",
    "-d",
    type=click.Path(path_type=Path),
    default="metadata/database/romgroomer.db",
    help="Path to metadata database",
)
@click.option(
    "--media-storage",
    "-m",
    type=click.Path(path_type=Path),
    default="metadata/media",
    help="Directory for content-addressable media storage",
)
@click.option(
    "--roms-base-dir",
    "-b",
    type=click.Path(exists=True, path_type=Path),
    help="Base directory for resolving relative paths (default: gamelist parent)",
)
@click.option(
    "--update/--no-update",
    default=True,
    help="Update existing games if found",
)
def import_arrm(
    gamelist_path: Path,
    database: Path,
    media_storage: Path,
    roms_base_dir: Optional[Path],
    update: bool,
):
    """
    Import ARRM gamelist.xml into metadata database.

    This command imports game metadata and media files from ARRM-generated
    gamelist.xml files. Media files are deduplicated using content-addressable
    storage, so clones share the same media files.

    Example:

        rom-groomer metadata import-arrm /data/emu/share/usa.1g1r/vectrex/gamelist.xml

    The importer will:
    - Parse gamelist.xml
    - Import game metadata (name, description, ratings, etc.)
    - Import all 9 media types (image, boxart, screenshot, etc.)
    - Deduplicate media files by hash
    - Store in content-addressable storage

    Time: ~30 seconds for 30-game collection, ~5 minutes for 658-game collection
    """
    try:
        # Create database and importer
        db = MetadataDatabase(database)
        importer = ARRMImporter(db, media_storage)

        # Import gamelist
        stats = importer.import_gamelist(
            gamelist_path,
            roms_base_dir,
            update_existing=update,
        )

        # Print results
        print_import_stats(stats)

        if stats.errors:
            console.print(
                f"\n[yellow]⚠ Import completed with {len(stats.errors)} errors[/yellow]"
            )
            raise click.Abort()

        console.print("\n[green]✓ Import completed successfully![/green]")

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise click.Abort()


@metadata_group.command(name="generate")
@click.argument("roms_dir", type=click.Path(exists=True, path_type=Path))
@click.argument("output_dir", type=click.Path(path_type=Path))
@click.option(
    "--database",
    "-d",
    type=click.Path(exists=True, path_type=Path),
    default="metadata/database/romgroomer.db",
    help="Path to metadata database",
)
@click.option(
    "--media-types",
    "-t",
    help='Media types to include (comma-separated or "all", "minimal", "standard")',
)
@click.option(
    "--no-copy-media",
    is_flag=True,
    help="Don't copy media files (gamelist only)",
)
@click.option(
    "--media-subdir",
    default="media",
    help="Subdirectory name for media files",
)
def generate(
    roms_dir: Path,
    output_dir: Path,
    database: Path,
    media_types: Optional[str],
    no_copy_media: bool,
    media_subdir: str,
):
    """
    Generate gamelist.xml for ROM directory.

    This command scans a ROM directory, matches files to the metadata database
    by hash, and generates a gamelist.xml with optional media files.

    Example:

        # Generate with all media types
        rom-groomer metadata generate /data/emu/roms/nes /data/emu/output/nes

        # Generate with minimal media (just mix image)
        rom-groomer metadata generate /data/emu/roms/nes /data/emu/output/nes --media-types minimal

        # Generate with specific types
        rom-groomer metadata generate /data/emu/roms/nes /data/emu/output/nes --media-types image,boxart,screenshot

        # Generate without copying media
        rom-groomer metadata generate /data/emu/roms/nes /data/emu/output/nes --no-copy-media

    Media type options:
    - "all": All 9 media types (~2.4 GB for 658 games)
    - "minimal": Just mix image (~1.3 MB for 658 games)
    - "standard": Standard set (image, boxart, screenshot, wheel, mix)
    - "no-videos": All except videos
    - "no-manuals": All except manuals
    - Comma-separated: Specific types (e.g., "image,boxart,screenshot")

    Time: ~10 seconds for 658-game collection
    """
    try:
        # Parse media types
        if media_types:
            if media_types in ["all", "minimal", "standard", "no-videos", "no-manuals"]:
                media_types_list = media_types
            else:
                media_types_list = [t.strip() for t in media_types.split(",")]
        else:
            media_types_list = None

        # Create database and generator
        db = MetadataDatabase(database)
        generator = GamelistGenerator(db)

        # Generate gamelist
        stats = generator.generate_gamelist(
            roms_dir,
            output_dir,
            media_types=media_types_list,
            copy_media=not no_copy_media,
            media_subdir=media_subdir,
        )

        # Print results
        print_generation_stats(stats)

        if stats.roms_unmatched > 0:
            console.print(
                f"\n[yellow]⚠ {stats.roms_unmatched} ROMs not found in database[/yellow]"
            )

        console.print("\n[green]✓ Generation completed successfully![/green]")

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise click.Abort()


@metadata_group.command(name="info")
@click.option(
    "--database",
    "-d",
    type=click.Path(exists=True, path_type=Path),
    default="metadata/database/romgroomer.db",
    help="Path to metadata database",
)
def info(database: Path):
    """
    Show metadata database statistics.

    Example:

        rom-groomer metadata info
    """
    try:
        db = MetadataDatabase(database)
        stats = db.get_stats()

        # Create info table
        table = Table(title="Metadata Database Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")

        table.add_row("Total Games", str(stats["total_games"]))
        table.add_row("Total Media Files", str(stats["total_media_files"]))
        table.add_row("Total Media Links", str(stats["total_media_links"]))
        table.add_row(
            "Average References per File",
            f"{stats['avg_references_per_file']:.1f}",
        )
        table.add_row("", "")  # Separator

        table.add_row("Total Media Size", f"{stats['total_size_mb']:.1f} MB")
        table.add_row("Savings from Deduplication", f"{stats['savings_mb']:.1f} MB")
        table.add_row(
            "Deduplication Rate",
            f"{stats['savings_percent']:.1f}%",
        )

        console.print(table)

        if stats["savings_percent"] > 0:
            console.print(
                f"\n[green]✓ Deduplication saved {stats['savings_mb']:.1f} MB "
                f"({stats['savings_percent']:.1f}%)[/green]"
            )

    except FileNotFoundError:
        console.print(f"[red]✗ Database not found:[/red] {database}")
        console.print(
            "[yellow]Run 'rom-groomer metadata import-arrm' first to create the database[/yellow]"
        )
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise click.Abort()


@metadata_group.command(name="list")
@click.option(
    "--database",
    "-d",
    type=click.Path(exists=True, path_type=Path),
    default="metadata/database/romgroomer.db",
    help="Path to metadata database",
)
@click.option(
    "--system",
    "-s",
    help="Filter by system name",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=50,
    help="Maximum number of games to show",
)
def list_games(database: Path, system: Optional[str], limit: int):
    """
    List games in metadata database.

    Example:

        rom-groomer metadata list
        rom-groomer metadata list --system "Nintendo - Nintendo Entertainment System"
        rom-groomer metadata list --limit 100
    """
    try:
        db = MetadataDatabase(database)

        with db.get_session() as session:
            from ..metadata.database import ScrapedGame

            query = session.query(ScrapedGame)

            if system:
                query = query.filter(ScrapedGame.system == system)

            query = query.order_by(ScrapedGame.name)
            query = query.limit(limit)

            games = query.all()

            if not games:
                console.print("[yellow]No games found in database[/yellow]")
                return

            # Create games table
            table = Table(title=f"Games in Database (showing {len(games)})")
            table.add_column("Name", style="cyan")
            table.add_column("System", style="yellow")
            table.add_column("Region", style="green")
            table.add_column("Media", style="magenta", justify="right")

            for game in games:
                media_count = len(game.media_links)
                table.add_row(
                    game.name or "Unknown",
                    game.system or "Unknown",
                    game.region or "Unknown",
                    str(media_count),
                )

            console.print(table)

            # Show total count
            total = session.query(ScrapedGame).count()
            if total > limit:
                console.print(
                    f"\n[yellow]Showing {len(games)} of {total} games. "
                    f"Use --limit to show more.[/yellow]"
                )

    except FileNotFoundError:
        console.print(f"[red]✗ Database not found:[/red] {database}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise click.Abort()
