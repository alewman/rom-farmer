"""
Gamelist.xml generator for EmulationStation.

This module generates gamelist.xml files from the ROM Groomer metadata database,
with support for media type filtering and smart file matching.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, List, Dict, Set
from dataclasses import dataclass
import hashlib

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)

from .database import MetadataDatabase, ScrapedGame, MediaType

console = Console()


@dataclass
class GenerationStats:
    """Statistics from gamelist generation."""

    roms_found: int = 0
    roms_matched: int = 0
    roms_unmatched: int = 0
    media_links_created: int = 0
    media_files_copied: int = 0
    media_bytes_copied: int = 0


class GamelistGenerator:
    """
    Generate EmulationStation gamelist.xml files.

    This generator:
    - Scans ROM directory for files
    - Matches ROMs to database by hash
    - Generates gamelist.xml with metadata
    - Filters media types based on configuration
    - Copies media files to output directory
    - Creates relative paths for portability
    """

    def __init__(self, database: MetadataDatabase):
        """
        Initialize gamelist generator.

        Args:
            database: MetadataDatabase instance
        """
        self.database = database

    def generate_gamelist(
        self,
        roms_dir: Path,
        output_dir: Path,
        media_types: Optional[List[str]] = None,
        copy_media: bool = True,
        media_subdir: str = "media",
        system_name: Optional[str] = None,
    ) -> GenerationStats:
        """
        Generate gamelist.xml for a ROM directory.

        Args:
            roms_dir: Directory containing ROM files
            output_dir: Directory to write gamelist.xml and media
            media_types: List of media types to include (None = all)
            copy_media: Copy media files to output directory
            media_subdir: Subdirectory name for media files
            system_name: System name for filtering (optional)

        Returns:
            GenerationStats with generation results
        """
        console.print(f"[cyan]Generating gamelist for:[/cyan] {roms_dir}")
        console.print(f"[cyan]Output directory:[/cyan] {output_dir}")

        stats = GenerationStats()

        # Resolve media types
        media_types = self._resolve_media_types(media_types)
        console.print(f"[cyan]Media types:[/cyan] {', '.join(media_types)}")

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        media_output_dir = output_dir / media_subdir

        # Scan ROM directory
        rom_files = self._scan_rom_directory(roms_dir)
        stats.roms_found = len(rom_files)
        console.print(f"[cyan]Found {stats.roms_found} ROM files[/cyan]")

        # Build gamelist XML
        root = ET.Element("gameList")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
        ) as progress:
            task = progress.add_task("Matching ROMs...", total=len(rom_files))

            for rom_file in rom_files:
                # Calculate hash and match to database
                md5_hash = self._calculate_md5(rom_file)
                game = self.database.find_game_by_hash(md5=md5_hash)
                
                # If no direct match, try transformation lookup
                if not game:
                    game = self._find_game_via_transformation(md5_hash)

                if game:
                    stats.roms_matched += 1

                    # Add game to XML
                    game_elem = self._create_game_element(
                        game,
                        rom_file,
                        roms_dir,
                        media_types,
                        media_subdir,
                    )
                    root.append(game_elem)

                    # Copy media files
                    if copy_media:
                        media_copied = self._copy_game_media(
                            game,
                            media_types,
                            media_output_dir,
                            rom_file,
                        )
                        stats.media_links_created += len(media_copied)
                        stats.media_files_copied += len(set(media_copied.values()))
                        stats.media_bytes_copied += sum(
                            Path(p).stat().st_size
                            for p in set(media_copied.values())
                            if Path(p).exists()
                        )
                else:
                    stats.roms_unmatched += 1

                progress.update(task, advance=1)

        # Write gamelist.xml
        self._write_gamelist(root, output_dir / "gamelist.xml")

        return stats

    def _resolve_media_types(
        self, media_types: Optional[List[str]]
    ) -> List[str]:
        """
        Resolve media types configuration to list of types.

        Handles special values:
        - None or "all": All media types
        - "minimal": Just mix
        - "standard": Standard set
        - "no-videos": All except videos
        - "no-manuals": All except manuals
        - List: Use as-is
        - Dict with include/exclude: Apply filters
        """
        if media_types is None or media_types == "all":
            return MediaType.all_types()

        if media_types == "minimal":
            return MediaType.minimal_types()

        if media_types == "standard":
            return MediaType.standard_types()

        if media_types == "no-videos":
            return [t for t in MediaType.all_types() if t != MediaType.VIDEO.value]

        if media_types == "no-manuals":
            return [t for t in MediaType.all_types() if t != MediaType.MANUAL.value]

        if isinstance(media_types, dict):
            # Handle include/exclude syntax
            include = media_types.get("include", "all")
            exclude = media_types.get("exclude", [])

            if include == "all":
                types = MediaType.all_types()
            else:
                types = include if isinstance(include, list) else [include]

            # Remove excluded types
            types = [t for t in types if t not in exclude]
            return types

        if isinstance(media_types, list):
            return media_types

        # Fallback to all
        return MediaType.all_types()

    def _scan_rom_directory(self, roms_dir: Path) -> List[Path]:
        """Scan directory for ROM files."""
        rom_extensions = {
            # Cartridge ROMs
            ".zip",
            ".7z",
            ".nes",
            ".sfc",
            ".smc",
            ".gb",
            ".gbc",
            ".gba",
            ".n64",
            ".z64",
            ".v64",
            ".md",
            ".smd",
            ".gen",
            ".sms",
            ".gg",
            ".pce",
            ".ws",
            ".wsc",
            ".ngp",
            ".ngc",
            ".a26",
            ".a52",
            ".a78",
            ".col",
            ".vec",
            ".lnx",
            # Disc images
            ".iso",
            ".cue",
            ".bin",
            ".chd",
            ".ccd",
            ".mds",
            ".img",
            # Playlists
            ".m3u",
        }

        rom_files = []
        for file_path in roms_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in rom_extensions:
                rom_files.append(file_path)

        return sorted(rom_files)
    
    def _find_game_via_transformation(self, final_md5: str) -> Optional[ScrapedGame]:
        """
        Find game by looking up transformation chain.
        
        When a ROM has been transformed (e.g., CUE → CHD), the metadata is stored
        with the original file's hash. This method looks up the transformation to
        find the source hash, then matches that to the game.
        
        Args:
            final_md5: MD5 hash of the transformed file (e.g., CHD)
            
        Returns:
            ScrapedGame if found via transformation, None otherwise
        """
        from .transformation import ROMTransformation
        
        # Get a session from the database
        session = self.database.get_session()
        
        # Look up transformation by final MD5
        transformation = session.query(ROMTransformation).filter_by(
            final_md5=final_md5
        ).first()
        
        if transformation and transformation.source_md5:
            # Found transformation, now look up game by source MD5
            return self.database.find_game_by_hash(md5=transformation.source_md5)
        
        return None

    def _calculate_md5(self, file_path: Path) -> str:
        """
        Calculate MD5 hash of a file.
        
        For archives (ZIP, 7Z), extracts and hashes the ROM inside.
        This matches ARRM's behavior and allows matching to ScreenScraper.
        """
        import zipfile
        import py7zr
        
        # Check if it's an archive
        if file_path.suffix.lower() == ".zip":
            return self._calculate_md5_from_zip(file_path)
        elif file_path.suffix.lower() == ".7z":
            return self._calculate_md5_from_7z(file_path)
        else:
            # Regular file - hash directly
            md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    md5.update(chunk)
            return md5.hexdigest()
    
    def _calculate_md5_from_zip(self, zip_path: Path) -> str:
        """Extract ROM from ZIP and calculate MD5."""
        import zipfile
        
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                # Find the ROM file (skip directories and system files)
                rom_files = [
                    f for f in zf.namelist()
                    if not f.endswith("/")
                    and not f.startswith("__MACOSX")
                    and not f.startswith(".")
                ]
                
                if not rom_files:
                    # No ROM found, hash the ZIP itself
                    console.print(f"[yellow]⚠ No ROM found in {zip_path.name}, hashing ZIP[/yellow]")
                    return self._hash_file_directly(zip_path)
                
                # Use the first (usually only) ROM file
                rom_file = rom_files[0]
                
                # Extract and hash
                rom_data = zf.read(rom_file)
                return hashlib.md5(rom_data).hexdigest()
                
        except zipfile.BadZipFile:
            console.print(f"[yellow]⚠ Bad ZIP file {zip_path.name}, hashing directly[/yellow]")
            return self._hash_file_directly(zip_path)
    
    def _calculate_md5_from_7z(self, archive_path: Path) -> str:
        """Extract ROM from 7Z and calculate MD5."""
        try:
            import py7zr
            
            with py7zr.SevenZipFile(archive_path, "r") as archive:
                # Get list of files
                rom_files = [
                    f for f in archive.getnames()
                    if not f.endswith("/")
                    and not f.startswith("__MACOSX")
                    and not f.startswith(".")
                ]
                
                if not rom_files:
                    console.print(f"[yellow]⚠ No ROM found in {archive_path.name}, hashing 7Z[/yellow]")
                    return self._hash_file_directly(archive_path)
                
                # Extract first ROM
                rom_file = rom_files[0]
                extracted = archive.read([rom_file])
                rom_data = extracted[rom_file].read()
                
                return hashlib.md5(rom_data).hexdigest()
                
        except ImportError:
            console.print(f"[yellow]⚠ py7zr not installed, hashing 7Z directly[/yellow]")
            return self._hash_file_directly(archive_path)
        except Exception as e:
            console.print(f"[yellow]⚠ Error extracting 7Z {archive_path.name}: {e}[/yellow]")
            return self._hash_file_directly(archive_path)
    
    def _hash_file_directly(self, file_path: Path) -> str:
        """Hash a file directly (fallback)."""
        md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                md5.update(chunk)
        return md5.hexdigest()

    def _create_game_element(
        self,
        game: ScrapedGame,
        rom_file: Path,
        roms_dir: Path,
        media_types: List[str],
        media_subdir: str,
    ) -> ET.Element:
        """Create XML element for a game."""
        game_elem = ET.Element("game")

        if game.game_id:
            game_elem.set("id", str(game.game_id))

        # Add metadata fields
        self._add_text_element(game_elem, "path", f"./{rom_file.relative_to(roms_dir)}")
        self._add_text_element(game_elem, "name", game.name)
        self._add_text_element(game_elem, "sortname", game.sortname)
        self._add_text_element(game_elem, "desc", game.description)

        if game.rating is not None:
            self._add_text_element(game_elem, "rating", f"{game.rating:.2f}")

        self._add_text_element(game_elem, "releasedate", game.release_date)
        self._add_text_element(game_elem, "developer", game.developer)
        self._add_text_element(game_elem, "publisher", game.publisher)
        self._add_text_element(game_elem, "genre", game.genre)

        if game.genre_id:
            self._add_text_element(game_elem, "genreid", str(game.genre_id))

        self._add_text_element(game_elem, "players", game.players)
        self._add_text_element(game_elem, "md5", game.md5)
        self._add_text_element(game_elem, "region", game.region)

        # Add media elements (filtered by media_types)
        game_media = self.database.get_game_media(game, media_types)
        for media_type, media_file in game_media.items():
            # Get filename from storage path
            storage_path = Path(media_file.file_path)
            filename = f"{rom_file.stem}-{media_type}{storage_path.suffix}"
            relative_path = f"./{media_subdir}/{media_type}/{filename}"

            self._add_text_element(game_elem, media_type, relative_path)

        return game_elem

    def _add_text_element(
        self, parent: ET.Element, tag: str, text: Optional[str]
    ) -> None:
        """Add text element to parent if text is not None."""
        if text is not None and text != "":
            elem = ET.SubElement(parent, tag)
            elem.text = str(text)

    def _copy_game_media(
        self,
        game: ScrapedGame,
        media_types: List[str],
        media_output_dir: Path,
        rom_file: Path,
    ) -> Dict[str, Path]:
        """
        Copy media files for a game to output directory.

        Returns:
            Dictionary mapping media type to output path
        """
        import shutil

        copied_media = {}
        game_media = self.database.get_game_media(game, media_types)

        for media_type, media_file in game_media.items():
            # Create media type subdirectory
            type_dir = media_output_dir / media_type
            type_dir.mkdir(parents=True, exist_ok=True)

            # Determine output filename (use rom_file stem to match XML paths)
            storage_path = Path(media_file.file_path)
            output_filename = f"{rom_file.stem}-{media_type}{storage_path.suffix}"
            output_path = type_dir / output_filename

            # Copy file if not already exists
            if not output_path.exists():
                shutil.copy2(storage_path, output_path)

            copied_media[media_type] = output_path

        return copied_media

    def _write_gamelist(self, root: ET.Element, output_path: Path) -> None:
        """Write gamelist XML to file with pretty formatting."""
        # Pretty print XML
        self._indent_xml(root)

        tree = ET.ElementTree(root)
        tree.write(
            output_path,
            encoding="utf-8",
            xml_declaration=True,
        )

        console.print(f"[green]✓ Gamelist written:[/green] {output_path}")

    def _indent_xml(self, elem: ET.Element, level: int = 0) -> None:
        """Add indentation to XML for pretty printing."""
        indent = "\n" + "  " * level
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                self._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent


def print_generation_stats(stats: GenerationStats) -> None:
    """Print generation statistics in a nice format."""
    from rich.table import Table
    from rich.panel import Panel

    # ROMs table
    roms_table = Table(title="ROMs")
    roms_table.add_column("Metric", style="cyan")
    roms_table.add_column("Count", style="green", justify="right")

    roms_table.add_row("Found", str(stats.roms_found))
    roms_table.add_row("Matched", str(stats.roms_matched))
    roms_table.add_row("Unmatched", str(stats.roms_unmatched))

    match_rate = (
        (stats.roms_matched / stats.roms_found * 100) if stats.roms_found > 0 else 0
    )
    roms_table.add_row("Match Rate", f"{match_rate:.1f}%")

    console.print(roms_table)

    # Media table
    media_table = Table(title="Media")
    media_table.add_column("Metric", style="cyan")
    media_table.add_column("Count", style="green", justify="right")

    media_table.add_row("Links Created", str(stats.media_links_created))
    media_table.add_row("Files Copied", str(stats.media_files_copied))

    if stats.media_bytes_copied > 0:
        size_mb = stats.media_bytes_copied / (1024 * 1024)
        media_table.add_row("Total Size", f"{size_mb:.1f} MB")

    console.print(media_table)

    # Success message
    if stats.roms_matched > 0:
        console.print(
            Panel(
                f"[green]✓ Generated gamelist for {stats.roms_matched} games[/green]",
                title="Success",
            )
        )
    else:
        console.print(
            Panel(
                "[yellow]⚠ No games matched in database[/yellow]",
                title="Warning",
            )
        )
