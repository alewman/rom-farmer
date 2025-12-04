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
import hashlib
import zipfile

import click
from rich.console import Console
from rich.table import Table

from ..metadata.database import MetadataDatabase
from ..metadata.arrm import ARRMImporter, print_import_stats
from ..metadata.generator import GamelistGenerator, print_generation_stats
from ..metadata.dat_manager import DATManager
from ..metadata.hash_capture import SmartHashCapture
from ..metadata.transformation_recorder import TransformationRecorder

console = Console()


# Helper functions for generate-gamelist (must be at module level for multiprocessing)
def calculate_md5_from_zip(zip_path: Path) -> tuple[str, str, str]:
    """Calculate MD5 of the data file inside a ZIP, return .cue path for ARRM.
    
    For CD-based games (.cue/.bin pairs):
    - Hashes the .bin file (actual data for matching)
    - Returns the .cue filename (what ARRM expects)
    - Caller will create zero-byte .cue file
    
    For cartridge systems with .bin files:
    - .bin files are just binary data (BIOS, firmware, etc.)
    - Returns the .bin filename directly (no .cue creation)
    
    Returns (filename, md5_hash, data_extension) or (filename, None, None) on error
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Get all files (exclude directories)
            all_files = [f for f in zf.namelist() if not f.endswith('/')]
            if not all_files:
                return (str(zip_path.name), None, None)
            
            # Find data files to hash (actual game data)
            # Check for cartridge ROMs first (higher priority than .bin)
            cart_files = [f for f in all_files if any(f.lower().endswith(ext) for ext in ['.nds', '.3ds', '.gba', '.gbc', '.gb', '.nes', '.sfc', '.smd'])]
            cue_files = [f for f in all_files if f.lower().endswith('.cue')]
            bin_files = [f for f in all_files if f.lower().endswith('.bin')]
            iso_files = [f for f in all_files if f.lower().endswith('.iso')]
            chd_files = [f for f in all_files if f.lower().endswith('.chd')]
            
            # Determine which file to hash and whether this is a CD-based system
            hash_file = None
            is_cd_system = False
            
            if cart_files:
                # Cartridge ROM (highest priority)
                hash_file = cart_files[0]
                is_cd_system = False
            elif cue_files and bin_files:
                # CD-based system with .cue/.bin pair
                hash_file = bin_files[0]
                is_cd_system = True
            elif bin_files and not cart_files:
                # Standalone .bin file (could be BIOS/firmware on cartridge system)
                # If there's only a .bin file and no cart ROMs, treat as binary data (not CD)
                hash_file = bin_files[0]
                is_cd_system = False
            elif iso_files:
                hash_file = iso_files[0]
                is_cd_system = True
            elif chd_files:
                hash_file = chd_files[0]
                is_cd_system = True
            else:
                hash_file = all_files[0]
                is_cd_system = False
            
            # Calculate MD5 of the data file
            md5_hash = hashlib.md5()
            with zf.open(hash_file) as f:
                while chunk := f.read(8192 * 1024):  # 8MB chunks
                    md5_hash.update(chunk)
            
            # Determine what filename to return for the path
            # For .bin files on CD-based systems, return .cue filename
            # For everything else, return the actual filename
            if is_cd_system and hash_file.lower().endswith('.bin'):
                # Create .cue filename from .bin filename (CD-based system)
                cue_filename = hash_file[:-4] + '.cue'
                data_ext = '.bin'
            else:
                # Use the actual file (ISO, CHD, cartridge ROM, or standalone .bin)
                cue_filename = hash_file
                data_ext = Path(hash_file).suffix
            
            return (cue_filename, md5_hash.hexdigest(), data_ext)
    except Exception as e:
        return (str(zip_path.name), None, None)


def calculate_md5_from_file(file_path: Path) -> tuple[str, str]:
    """Calculate MD5 of a raw file (ISO, CHD, etc)."""
    try:
        md5_hash = hashlib.md5()
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192 * 1024):  # 8MB chunks
                md5_hash.update(chunk)
        return (str(file_path.name), md5_hash.hexdigest())
    except Exception as e:
        return (str(file_path.name), None)


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
    default="metadata/database/romfarmer.db",
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

        rom-farmer metadata import-arrm /data/emu/share/usa.1g1r/vectrex/gamelist.xml

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
    default="metadata/database/romfarmer.db",
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
        rom-farmer metadata generate /data/emu/roms/nes /data/emu/output/nes

        # Generate with minimal media (just mix image)
        rom-farmer metadata generate /data/emu/roms/nes /data/emu/output/nes --media-types minimal

        # Generate with specific types
        rom-farmer metadata generate /data/emu/roms/nes /data/emu/output/nes --media-types image,boxart,screenshot

        # Generate without copying media
        rom-farmer metadata generate /data/emu/roms/nes /data/emu/output/nes --no-copy-media

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
    default="metadata/database/romfarmer.db",
    help="Path to metadata database",
)
def info(database: Path):
    """
    Show metadata database statistics.

    Example:

        rom-farmer metadata info
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
            "[yellow]Run 'rom-farmer metadata import-arrm' first to create the database[/yellow]"
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
    default="metadata/database/romfarmer.db",
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

        rom-farmer metadata list
        rom-farmer metadata list --system "Nintendo - Nintendo Entertainment System"
        rom-farmer metadata list --limit 100
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


@metadata_group.command(name="test-dat")
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
        rom-farmer metadata test-dat -d /data/emu/dats/redump -d /data/emu/dats/nointro
        
        # Test hash capture on a file
        rom-farmer metadata test-dat -d /data/emu/dats/redump \\
            -f /data/emu/stage/eng.1g1r/saturn/3D\ Baseball\ \(USA\).chd \\
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


@metadata_group.command(name="test-transform")
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
            -d /data/emu/dats/redump \\
            -s /data/emu/source/saturn/game.iso \\
            -f /data/emu/stage/eng.1g1r/saturn/game.chd \\
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
            
            # In a real workflow, you'd do:
            #   with recorder.record_transformation(...) as transform:
            #       final_file = process_rom(source_file)
            #       transform.set_final_file(final_file)
            #
            # But for testing, we already have both files:
            
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


@metadata_group.command(name="generate-gamelist")
@click.argument("roms_dir", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--system",
    "-s",
    required=True,
    help="System name (e.g., ps3, nes, saturn)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output path for gamelist.xml (default: <roms_dir>/gamelist.xml)",
)
@click.option(
    "--workers",
    "-w",
    type=int,
    default=None,
    help="Number of parallel workers (default: CPU count)",
)
@click.option(
    "--save-interval",
    type=int,
    default=100,
    help="Save progress every N files (default: 100)",
)
@click.option(
    "--incremental/--full",
    default=True,
    help="Only calculate missing MD5s (default) or recalculate all",
)
def generate_gamelist(
    roms_dir: Path, 
    system: str, 
    output: Optional[Path], 
    workers: Optional[int],
    save_interval: int,
    incremental: bool,
):
    """
    Generate minimal gamelist.xml with MD5 hashes for ARRM.

    This command scans a ROM directory, calculates MD5 hashes for files inside ZIPs,
    and generates a minimal gamelist.xml that ARRM can use for faster scraping.
    
    Uses multi-core processing to hash multiple files in parallel.
    
    CRASH RECOVERY: Saves progress periodically. If interrupted, re-run with
    --incremental (default) to resume from where it left off.

    Example:

        # Generate for PS3 ROMs (auto-detect CPU count, save every 100 files)
        rom-farmer metadata generate-gamelist /data/emu/roms/ps3 --system ps3

        # Use 16 workers, save every 50 files
        rom-farmer metadata generate-gamelist /data/emu/roms/ps3 --system ps3 --workers 16 --save-interval 50

        # Force recalculate all MD5s (ignore existing)
        rom-farmer metadata generate-gamelist /data/emu/roms/ps3 --system ps3 --full

    The generated gamelist.xml contains:
    - <path>: Relative path to ROM ZIP file
    - <md5>: MD5 hash of the first file inside the ZIP (ISO/CUE/BIN)
    
    ARRM will then enrich this file with full metadata using MD5-based matching.
    
    IMPORTANT: This is a MASSIVE operation for large disc systems!
    - PS3 (1,246 games, ~20GB avg): ~16-20 HOURS with 16 cores (~7-10 DAYS with 1 core)
    - PS2 (2,530 games, ~4GB avg): ~8-10 hours with 16 cores
    - Saturn/SegaCD (~600MB avg): ~30-60 minutes with 16 cores
    
    We're decompressing and hashing ~25TB of data for PS3!
    
    Progress auto-saves every 100 files. Safe to Ctrl+C and resume with --incremental.
    Recommended: Run in screen/tmux session for overnight processing.
    """
    import xml.etree.ElementTree as ET
    import xml.dom.minidom as minidom
    import multiprocessing
    from concurrent.futures import ProcessPoolExecutor, as_completed
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    
    def load_existing_gamelist(output_path: Path) -> dict:
        """Load existing gamelist.xml and return dict of path -> md5."""
        if not output_path.exists():
            return {}
        
        try:
            tree = ET.parse(output_path)
            root = tree.getroot()
            
            existing = {}
            for game in root.findall("game"):
                path_elem = game.find("path")
                md5_elem = game.find("md5")
                if path_elem is not None and md5_elem is not None:
                    existing[path_elem.text] = md5_elem.text
            
            return existing
        except Exception as e:
            console.print(f"[yellow]⚠ Could not load existing gamelist.xml: {e}[/yellow]")
            return {}
    
    def save_gamelist(output_path: Path, system: str, games: list):
        """Save gamelist.xml to disk."""
        # Create root element
        root = ET.Element("gameList")
        
        # Add provider info
        provider = ET.SubElement(root, "provider")
        ET.SubElement(provider, "system").text = system
        ET.SubElement(provider, "software").text = "ROM Farmer"
        ET.SubElement(provider, "web").text = "https://github.com/user/rom-farmer-python"
        
        # Add games (sorted)
        sorted_games = sorted(games, key=lambda g: g["path"])
        for idx, game_info in enumerate(sorted_games, start=1):
            game = ET.SubElement(root, "game")
            ET.SubElement(game, "path").text = game_info["path"]
            
            # Extract name from filename (remove ./ prefix and extension)
            filename = game_info["path"].replace("./", "")
            # Remove common extensions for display name (but keep .cue/.m3u in path)
            for ext in [".iso", ".chd", ".nds", ".3ds", ".gba", ".gbc", ".gb", ".nes", ".sfc", ".smd", ".bin", ".img"]:
                if filename.lower().endswith(ext):
                    filename = filename[:-len(ext)]
                    break
            # Also strip .cue for name display
            if filename.lower().endswith(".cue"):
                filename = filename[:-4]
            ET.SubElement(game, "name").text = filename
            
            # Add sortname with zero-padded index (ARRM format)
            sortname = f"{idx:04d} =-  {filename}"
            ET.SubElement(game, "sortname").text = sortname
            
            # Add genreid (0 = unknown, ARRM will populate)
            ET.SubElement(game, "genreid").text = "0"
            
            ET.SubElement(game, "md5").text = game_info["md5"]
        
        # Pretty print XML
        xml_str = ET.tostring(root, encoding="unicode")
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ")
        
        # Remove extra blank lines
        lines = [line for line in pretty_xml.split("\n") if line.strip()]
        pretty_xml = "\n".join(lines)
        
        # Write to file (with backup)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create backup if file exists
        if output_path.exists():
            backup_path = output_path.with_suffix(output_path.suffix + ".bak")
            output_path.rename(backup_path)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(pretty_xml)
    
    try:
        # Determine output path
        if output is None:
            output = roms_dir / "gamelist.xml"
        
        # Determine worker count (default to 8, or CPU count if less)
        if workers is None:
            workers = min(8, multiprocessing.cpu_count())
        
        # Load existing gamelist (for incremental mode)
        existing_md5s = {}
        if incremental and output.exists():
            console.print(f"[cyan]Loading existing gamelist.xml for incremental update...[/cyan]")
            existing_md5s = load_existing_gamelist(output)
            if existing_md5s:
                console.print(f"[green]Found {len(existing_md5s)} existing MD5 hashes[/green]")
        
        # Scan for ROM files (ZIP or ISO/CHD/CUE)
        console.print(f"[cyan]Scanning {roms_dir} for ROM files...[/cyan]")
        
        # Try common ROM formats
        rom_files = []
        for pattern in ["*.zip", "*.iso", "*.chd", "*.cue"]:
            rom_files.extend(roms_dir.glob(pattern))
        rom_files = sorted(set(rom_files))  # Remove duplicates
        
        if not rom_files:
            console.print(f"[yellow]⚠ No ROM files found in {roms_dir}[/yellow]")
            console.print(f"[yellow]  Supported: .zip, .iso, .chd, .cue[/yellow]")
            raise click.Abort()
        
        # Detect file type
        is_zipped = rom_files[0].suffix == ".zip"
        console.print(f"[green]Found {len(rom_files)} {rom_files[0].suffix} files[/green]")
        
        # Determine which files need processing
        files_to_process = []
        games = []
        
        for rom_file in rom_files:
            rel_path = f"./{rom_file.name}"
            if incremental and rel_path in existing_md5s:
                # Already have MD5, keep it
                games.append({
                    "path": rel_path,
                    "md5": existing_md5s[rel_path],
                })
            else:
                # Need to calculate MD5
                files_to_process.append(rom_file)
        
        if incremental and existing_md5s:
            console.print(f"[cyan]Incremental mode: {len(files_to_process)} files need MD5 calculation[/cyan]")
            console.print(f"[cyan]Skipping {len(existing_md5s)} files with existing MD5s[/cyan]")
        
        if not files_to_process:
            console.print(f"[green]✓ All files already have MD5 hashes![/green]")
            console.print(f"[green]  Use --full to recalculate all MD5s[/green]")
            return
        
        console.print(f"[cyan]Using {workers} parallel workers[/cyan]")
        console.print(f"[cyan]Auto-saving every {save_interval} files[/cyan]")
        
        # Calculate MD5s with multi-core processing
        console.print(f"\n[cyan]Calculating MD5 hashes (extracting files from ZIPs)...[/cyan]")
        console.print(f"[yellow]⚠ LARGE OPERATION: Decompressing + hashing ISOs[/yellow]")
        console.print(f"[yellow]  PS3 games are 5-50GB each (avg ~20GB)[/yellow]")
        console.print(f"[yellow]  Estimated: {len(files_to_process) * 50 / workers / 60:.0f}-{len(files_to_process) * 80 / workers / 60:.0f} minutes ({len(files_to_process) * 50 / workers / 3600:.1f}-{len(files_to_process) * 80 / workers / 3600:.1f} hours)[/yellow]")
        console.print(f"[cyan]💾 Auto-saving every {save_interval} files - safe to Ctrl+C and resume![/cyan]\n")
        
        processed_count = 0
        import time
        start_time = time.time()
        last_save_time = start_time
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Hashing files...", total=len(files_to_process))
            
            with ProcessPoolExecutor(max_workers=workers) as executor:
                # Submit all tasks (use appropriate hash function based on file type)
                hash_function = calculate_md5_from_zip if is_zipped else calculate_md5_from_file
                futures = {executor.submit(hash_function, rom_file): rom_file 
                          for rom_file in files_to_process}
                
                # Process results as they complete
                for future in as_completed(futures):
                    rom_file = futures[future]
                    
                    if is_zipped:
                        filename, md5_hash, data_ext = future.result()
                        
                        # For .bin files, create zero-byte .cue file to trick ARRM
                        if md5_hash and data_ext == '.bin':
                            cue_path = roms_dir / filename
                            if not cue_path.exists():
                                cue_path.touch()  # Create zero-byte file
                        
                        # For .3ds files, create zero-byte .3ds file for ARRM compatibility
                        # (ZIPs contain full .3ds files but emulators can't load from ZIP due to size)
                        if md5_hash and data_ext == '.3ds':
                            tds_path = roms_dir / filename
                            if not tds_path.exists():
                                tds_path.touch()  # Create zero-byte file
                    else:
                        filename, md5_hash = future.result()
                    
                    if md5_hash:
                        games.append({
                            "path": f"./{filename}",
                            "md5": md5_hash,
                        })
                        processed_count += 1
                        
                        # Show progress every 10 files
                        if processed_count % 10 == 0:
                            elapsed = time.time() - start_time
                            rate = processed_count / (elapsed / 60) if elapsed > 0 else 0
                            progress.console.print(f"[dim]  ✓ {filename[:60]}... ({processed_count}/{len(files_to_process)}, {rate:.1f}/min)[/dim]")
                        
                        # Periodic save (every 100 files OR every 5 minutes)
                        current_time = time.time()
                        time_since_save = current_time - last_save_time
                        should_save = (processed_count % save_interval == 0) or (time_since_save >= 300)  # 300 seconds = 5 minutes
                        
                        if should_save:
                            elapsed = time.time() - start_time
                            rate = processed_count / (elapsed / 60)  # games per minute
                            remaining_games = len(files_to_process) - processed_count
                            eta_minutes = remaining_games / rate if rate > 0 else 0
                            save_gamelist(output, system, games)
                            last_save_time = current_time
                            save_reason = "100 files" if processed_count % save_interval == 0 else "5 min"
                            progress.console.print(
                                f"[green]💾 SAVED ({save_reason}): {len(games)} total | "
                                f"Rate: {rate:.2f}/min | "
                                f"ETA: {eta_minutes:.0f} min ({eta_minutes/60:.1f} hrs) | "
                                f"Elapsed: {elapsed/3600:.1f} hrs[/green]"
                            )
                    
                    progress.update(task, advance=1)
        
        # Final save
        console.print(f"\n[cyan]Saving final gamelist.xml...[/cyan]")
        save_gamelist(output, system, games)
        
        # Success!
        console.print(f"\n[green]✓ Generated gamelist.xml with {len(games)} games[/green]")
        console.print(f"[green]  Output: {output}[/green]")
        console.print(f"\n[cyan]Next steps:[/cyan]")
        console.print(f"  1. Run ARRM on {roms_dir}")
        console.print(f"  2. ARRM will use MD5 hashes for faster/accurate scraping")
        console.print(f"  3. Import enriched gamelist: ./romfarmer metadata import-arrm {output}")
        
    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        raise click.Abort()
        
    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        raise click.Abort()
