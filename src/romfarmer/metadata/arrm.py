"""
ARRM (Advanced ROM Repository Manager) gamelist.xml importer.

This module imports metadata from ARRM-generated gamelist.xml files into
the ROM Farmer database. It handles all 9 media types and implements
content-addressable storage for deduplication.
"""

import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime

# ARRM embeds a numeric sort key as a prefix: "3595 =-  Game Name"
# Strip it on import so the database stores clean sortnames.
_ARRM_SORTNAME_RE = re.compile(r"^\d+\s+=-\s+")


def _clean_arrm_sortname(value: Optional[str], name: Optional[str] = None) -> Optional[str]:
    """Strip ARRM numeric sort prefix from sortname; return None if result equals name."""
    if not value:
        return value
    cleaned = _ARRM_SORTNAME_RE.sub("", value).strip()
    if name and cleaned == name:
        return None
    return cleaned or None

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)

from .database import (
    MetadataDatabase,
    ScrapedGame,
    MediaFile,
    GameMediaLink,
    MediaType,
)
from ..cas import ContentStore

console = Console()


@dataclass
class ImportStats:
    """Statistics from an import operation."""

    games_processed: int = 0
    games_imported: int = 0
    games_updated: int = 0
    games_skipped: int = 0
    media_files_total: int = 0
    media_files_new: int = 0
    media_files_deduplicated: int = 0
    media_bytes_total: int = 0
    media_bytes_saved: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class ARRMImporter:
    """
    Import ARRM gamelist.xml files into ROM Farmer database.

    This importer:
    - Parses ARRM gamelist.xml format
    - Imports game metadata (all fields)
    - Imports all 9 media types
    - Implements content-addressable storage
    - Deduplicates media files by hash
    - Supports smart updates (keep old data, replace with better)
    """

    def __init__(
        self,
        database: MetadataDatabase,
        store_dir: Path = Path("store"),
    ):
        """
        Initialize ARRM importer.

        Args:
            database: MetadataDatabase instance
            store_dir: Content-addressable store directory
        """
        self.database = database
        self.store = ContentStore(store_dir)

    def import_gamelist(
        self,
        gamelist_path: Path,
        roms_base_dir: Optional[Path] = None,
        update_existing: bool = True,
    ) -> ImportStats:
        """
        Import an ARRM gamelist.xml file.

        Args:
            gamelist_path: Path to gamelist.xml
            roms_base_dir: Base directory for resolving relative paths
                          (defaults to gamelist.xml parent directory)
            update_existing: Update existing games if found

        Returns:
            ImportStats with import results
        """
        if not gamelist_path.exists():
            raise FileNotFoundError(f"Gamelist not found: {gamelist_path}")

        if roms_base_dir is None:
            roms_base_dir = gamelist_path.parent

        console.print(f"[cyan]Importing:[/cyan] {gamelist_path}")
        console.print(f"[cyan]Base directory:[/cyan] {roms_base_dir}")

        stats = ImportStats()
        
        # Get gamelist modification time for timestamp tracking
        gamelist_mtime = datetime.fromtimestamp(gamelist_path.stat().st_mtime)

        # Parse XML
        try:
            tree = ET.parse(gamelist_path)
            root = tree.getroot()
        except ET.ParseError as e:
            stats.errors.append(f"XML parse error: {e}")
            return stats
        
        # Extract system name from provider section
        system_name = None
        provider = root.find("provider")
        if provider is not None:
            system_name = provider.findtext("system")
        
        # Fallback: extract from directory name if no provider section
        if not system_name:
            system_name = roms_base_dir.name
            
        if system_name:
            console.print(f"[cyan]System:[/cyan] {system_name}")

        # Get all game elements
        games = root.findall("game")
        console.print(f"[cyan]Found {len(games)} games in gamelist[/cyan]")

        # Import games with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
        ) as progress:
            task = progress.add_task("Importing games...", total=len(games))

            for game_elem in games:
                try:
                    self._import_game(
                        game_elem,
                        roms_base_dir,
                        stats,
                        update_existing,
                        system_name=system_name,
                        gamelist_path=str(gamelist_path),
                        gamelist_mtime=gamelist_mtime,
                    )
                except Exception as e:
                    game_name = game_elem.findtext("name", "Unknown")
                    error_msg = f"Error importing '{game_name}': {e}"
                    stats.errors.append(error_msg)
                    console.print(f"[yellow]⚠ {error_msg}[/yellow]")

                progress.update(task, advance=1)

        return stats

    def _import_game(
        self,
        game_elem: ET.Element,
        roms_base_dir: Path,
        stats: ImportStats,
        update_existing: bool,
        system_name: Optional[str] = None,
        gamelist_path: Optional[str] = None,
        gamelist_mtime: Optional[datetime] = None,
    ) -> None:
        """Import a single game from XML element."""
        stats.games_processed += 1

        # Extract metadata
        game_data = self._extract_game_metadata(game_elem, system_name)
        
        # Add source tracking
        game_data["source_gamelist_path"] = gamelist_path
        game_data["source_gamelist_mtime"] = gamelist_mtime

        if not game_data.get("md5"):
            stats.games_skipped += 1
            stats.errors.append(
                f"Skipping '{game_data.get('name')}': No MD5 hash"
            )
            return

        # Check if game exists
        with self.database.get_session() as session:
            existing_game = self.database.find_game_by_hash(
                md5=game_data.get("md5"),
                crc32=game_data.get("crc32"),
                sha1=game_data.get("sha1"),
            )

            if existing_game and not update_existing:
                stats.games_skipped += 1
                return

            if existing_game:
                # Smart update: only update if new source is newer or more complete
                if self._should_update_game(existing_game, game_data, gamelist_mtime):
                    game = session.merge(existing_game)
                    self._update_game_metadata(game, game_data)
                    stats.games_updated += 1
                else:
                    # Skip update - existing data is newer or better
                    stats.games_skipped += 1
                    # Merge to attach to this session
                    game = session.merge(existing_game)
            else:
                # Create new game
                game = ScrapedGame(**game_data)
                session.add(game)
                stats.games_imported += 1

            session.commit()
            session.refresh(game)

            # Import media files
            media_elements = self._extract_media_elements(game_elem)
            for media_type, media_path in media_elements.items():
                try:
                    self._import_media(
                        game,
                        media_type,
                        media_path,
                        roms_base_dir,
                        stats,
                    )
                except Exception as e:
                    error_msg = f"Error importing media '{media_type}' for '{game.name}': {e}"
                    stats.errors.append(error_msg)

            session.commit()

    def _extract_game_metadata(self, game_elem: ET.Element, system_name: Optional[str] = None) -> Dict:
        """Extract game metadata from XML element."""
        return {
            "md5": game_elem.findtext("md5"),
            "crc32": game_elem.findtext("crc32"),
            "sha1": game_elem.findtext("sha1"),
            "filename": game_elem.findtext("path"),
            "game_id": self._parse_int(game_elem.get("id")),
            "system": system_name,  # Use system from provider section
            "name": game_elem.findtext("name"),
            "sortname": _clean_arrm_sortname(
                game_elem.findtext("sortname"),
                game_elem.findtext("name"),
            ),
            "description": game_elem.findtext("desc"),
            "rating": self._parse_float(game_elem.findtext("rating")),
            "release_date": game_elem.findtext("releasedate"),
            "developer": game_elem.findtext("developer"),
            "publisher": game_elem.findtext("publisher"),
            "genre": game_elem.findtext("genre"),
            "genre_id": self._parse_int(game_elem.findtext("genreid")),
            "players": game_elem.findtext("players"),
            "region": game_elem.findtext("region"),
            "language": game_elem.findtext("lang"),
            "hidden": self._parse_bool(game_elem.findtext("hidden")),
            "favorite": self._parse_bool(game_elem.findtext("favorite")),
            "kidgame": self._parse_bool(game_elem.findtext("kidgame")),
            "playcount": self._parse_int(game_elem.findtext("playcount")),
            "lastplayed": self._parse_datetime(game_elem.findtext("lastplayed")),
        }

    def _parse_bool(self, value: Optional[str]) -> bool:
        """Parse boolean value from string."""
        if not value:
            return False
        return value.lower() in ("true", "yes", "1", "on")

    def _parse_datetime(self, value: Optional[str]) -> Optional[datetime]:
        """Parse datetime from gamelist format (YYYYMMDDTHHMMSS)."""
        if not value:
            return None
        try:
            return datetime.strptime(value, "%Y%m%dT%H%M%S")
        except ValueError:
            return None

    def _extract_media_elements(self, game_elem: ET.Element) -> Dict[str, str]:
        """Extract all media elements from game XML."""
        media_elements = {}

        for media_type in MediaType.all_types():
            media_path = game_elem.findtext(media_type)
            if media_path:
                media_elements[media_type] = media_path

        return media_elements

    def _import_media(
        self,
        game: ScrapedGame,
        media_type: str,
        media_path: str,
        roms_base_dir: Path,
        stats: ImportStats,
    ) -> None:
        """Import a media file with content-addressable storage."""
        # Resolve path
        if media_path.startswith("./"):
            media_path = media_path[2:]

        source_path = roms_base_dir / media_path

        if not source_path.exists():
            stats.errors.append(
                f"Media file not found: {source_path} (game: {game.name})"
            )
            return

        # Calculate file hash for content addressing
        file_hash = self.store.hash_file(source_path)
        file_size = source_path.stat().st_size
        file_mtime = datetime.fromtimestamp(source_path.stat().st_mtime)

        stats.media_files_total += 1
        stats.media_bytes_total += file_size

        # Check if media already exists
        with self.database.get_session() as session:
            # Reload game in this session
            game_in_session = session.query(ScrapedGame).filter(ScrapedGame.id == game.id).first()
            if not game_in_session:
                stats.errors.append(f"Game not found in session: {game.name}")
                return

            existing_media = (
                session.query(MediaFile)
                .filter(MediaFile.file_hash == file_hash)
                .first()
            )

            if existing_media:
                # Media already exists - deduplication!
                media_file = existing_media
                stats.media_files_deduplicated += 1
                stats.media_bytes_saved += file_size
            else:
                # Store in content-addressable store
                _, storage_path = self.store.put(
                    source_path, file_hash=file_hash
                )

                # Get media metadata based on type
                if media_type == 'video':
                    # Get comprehensive video metadata
                    video_meta = self._get_video_metadata(storage_path)
                    width = video_meta['width']
                    height = video_meta['height']
                    video_codec = video_meta['codec']
                    video_bitrate = video_meta['bitrate']
                    video_fps = video_meta['fps']
                    video_duration = video_meta['duration']
                    image_mode = None
                    has_transparency = None
                else:
                    # Get comprehensive image metadata
                    image_meta = self._get_image_metadata(storage_path)
                    width = image_meta['width']
                    height = image_meta['height']
                    image_mode = image_meta['mode']
                    has_transparency = image_meta['has_transparency']
                    video_codec = None
                    video_bitrate = None
                    video_fps = None
                    video_duration = None

                # Create media file record
                media_file = MediaFile(
                    file_hash=file_hash,
                    media_type=media_type,
                    file_path=str(storage_path),
                    file_size=file_size,
                    file_format=source_path.suffix.lstrip("."),
                    width=width,
                    height=height,
                    image_mode=image_mode,
                    has_transparency=has_transparency,
                    video_codec=video_codec,
                    video_bitrate=video_bitrate,
                    video_fps=video_fps,
                    video_duration=video_duration,
                    source_url=None,  # ARRM doesn't provide URL
                    source_file_mtime=file_mtime,  # Track source file modification time
                )
                session.add(media_file)
                session.flush()  # Assign ID to media_file
                stats.media_files_new += 1

            # Create link between game and media
            # Check if link already exists for THIS media type
            # Note: The same file can be linked with different media types
            # (e.g., mix and image might be the same file, wheel and marquee, etc.)
            existing_link = (
                session.query(GameMediaLink)
                .filter(
                    GameMediaLink.game_id == game_in_session.id,
                    GameMediaLink.media_type == media_type,
                )
                .first()
            )

            if not existing_link:
                link = GameMediaLink(
                    game_id=game_in_session.id,
                    media_file_id=media_file.id,
                    media_type=media_type,
                    priority=0,
                )
                session.add(link)
                media_file.increment_references()

            session.commit()

    def _get_storage_path(
        self, file_hash: str, media_type: str, extension: str
    ) -> Path:
        """Get storage path for a media file (delegates to ContentStore)."""
        return self.store.blob_path(file_hash, extension)

    def _get_image_metadata(self, image_path: Path) -> dict:
        """Get comprehensive image metadata."""
        try:
            from PIL import Image

            with Image.open(image_path) as img:
                has_transparency = img.mode in ('RGBA', 'LA', 'PA', 'P')
                # For P mode, check if there's actually transparency in the palette
                if img.mode == 'P' and 'transparency' not in img.info:
                    has_transparency = False
                
                return {
                    'width': img.width,
                    'height': img.height,
                    'mode': img.mode,
                    'has_transparency': has_transparency,
                }
        except (ImportError, Exception):
            return {
                'width': None,
                'height': None,
                'mode': None,
                'has_transparency': None,
            }

    def _get_image_dimensions(self, image_path: Path) -> tuple[Optional[int], Optional[int]]:
        """Get image dimensions (legacy method - use _get_image_metadata instead)."""
        metadata = self._get_image_metadata(image_path)
        return metadata['width'], metadata['height']

    def _get_video_metadata(self, video_path: Path) -> dict:
        """Get comprehensive video metadata using ffprobe."""
        try:
            import subprocess
            import json
            
            result = subprocess.run(
                ['ffprobe', '-v', 'quiet', '-print_format', 'json', 
                 '-show_streams', '-select_streams', 'v:0', str(video_path)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if 'streams' in data and len(data['streams']) > 0:
                    stream = data['streams'][0]
                    return {
                        'width': stream.get('width'),
                        'height': stream.get('height'),
                        'codec': stream.get('codec_name'),
                        'bitrate': int(stream['bit_rate']) if stream.get('bit_rate') else None,
                        'fps': stream.get('r_frame_rate'),
                        'duration': float(stream['duration']) if stream.get('duration') else None,
                    }
        except Exception:
            pass
        
        return {
            'width': None,
            'height': None,
            'codec': None,
            'bitrate': None,
            'fps': None,
            'duration': None,
        }

    def _get_video_dimensions(self, video_path: Path) -> tuple[Optional[int], Optional[int]]:
        """Get video dimensions using ffprobe (legacy method - use _get_video_metadata instead)."""
        metadata = self._get_video_metadata(video_path)
        return metadata['width'], metadata['height']

    def _get_media_dimensions(self, media_path: Path, media_type: str) -> tuple[Optional[int], Optional[int]]:
        """Get dimensions for image or video files."""
        if media_type == 'video':
            return self._get_video_dimensions(media_path)
        else:
            # For images (boxart, cartridge, image, screenshot, wheel, marquee, manual covers)
            return self._get_image_dimensions(media_path)

    def _update_game_metadata(self, game: ScrapedGame, new_data: Dict) -> None:
        """Update existing game with new metadata (smart update)."""
        # Update all fields, but only if new data is not None
        for key, value in new_data.items():
            if value is not None:
                setattr(game, key, value)

    def _should_update_game(
        self, 
        existing_game: ScrapedGame, 
        new_game_data: Dict, 
        new_source_mtime: Optional[datetime]
    ) -> bool:
        """
        Decide if we should update existing game with new data.
        
        Strategy:
        1. If no timestamp on existing game -> always update (legacy data)
        2. If new source is newer -> update
        3. If new source is older but more complete -> update
        4. Otherwise -> skip (keep existing)
        """
        # No existing timestamp? Always update (legacy import)
        if not existing_game.source_gamelist_mtime:
            return True
        
        # New source is newer? Update
        if new_source_mtime and new_source_mtime > existing_game.source_gamelist_mtime:
            return True
        
        # New source is same age or older, but has more complete data?
        if self._is_more_complete(new_game_data, existing_game):
            return True
        
        # Otherwise, keep existing (it's newer or equally complete)
        return False
    
    def _is_more_complete(self, new_data: Dict, existing_game: ScrapedGame) -> bool:
        """
        Check if new data is more complete than existing.
        
        Counts non-null fields in both and compares.
        """
        important_fields = [
            'name', 'description', 'rating', 'release_date', 
            'developer', 'publisher', 'genre', 'players', 'region',
            'favorite', 'hidden', 'kidgame', 'playcount', 'lastplayed', 'sortname'
        ]
        
        new_filled = sum(
            1 for field in important_fields 
            if new_data.get(field) and str(new_data[field]).strip()
        )
        
        existing_filled = sum(
            1 for field in important_fields
            if getattr(existing_game, field, None) and str(getattr(existing_game, field)).strip()
        )
        
        # Consider "more complete" if at least 2 more fields are filled
        return new_filled > existing_filled + 1

    def _extract_system_from_path(self, path: str) -> Optional[str]:
        """Extract system name from file path (if possible)."""
        # This is a simple heuristic - you might want to make this configurable
        # For now, we'll leave it None and let the user specify
        return None

    def _parse_int(self, value: Optional[str]) -> Optional[int]:
        """Safely parse integer."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def _parse_float(self, value: Optional[str]) -> Optional[float]:
        """Safely parse float."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None


def print_import_stats(stats: ImportStats) -> None:
    """Print import statistics in a nice format."""
    from rich.table import Table
    from rich.panel import Panel

    # Games table
    games_table = Table(title="Games")
    games_table.add_column("Metric", style="cyan")
    games_table.add_column("Count", style="green", justify="right")

    games_table.add_row("Processed", str(stats.games_processed))
    games_table.add_row("Imported", str(stats.games_imported))
    games_table.add_row("Updated", str(stats.games_updated))
    games_table.add_row("Skipped", str(stats.games_skipped))

    console.print(games_table)

    # Media table
    media_table = Table(title="Media Files")
    media_table.add_column("Metric", style="cyan")
    media_table.add_column("Count", style="green", justify="right")

    media_table.add_row("Total Media Links", str(stats.media_files_total))
    media_table.add_row("New Files", str(stats.media_files_new))
    media_table.add_row("Deduplicated", str(stats.media_files_deduplicated))

    console.print(media_table)

    # Storage savings
    if stats.media_bytes_saved > 0:
        savings_mb = stats.media_bytes_saved / (1024 * 1024)
        total_mb = stats.media_bytes_total / (1024 * 1024)
        savings_pct = (stats.media_bytes_saved / stats.media_bytes_total * 100)

        console.print(
            Panel(
                f"[green]Storage Savings:[/green]\n"
                f"  Saved: {savings_mb:.1f} MB\n"
                f"  Total: {total_mb:.1f} MB\n"
                f"  Deduplication: {savings_pct:.1f}%",
                title="💾 Deduplication",
            )
        )

    # Errors
    if stats.errors:
        console.print(f"\n[yellow]⚠ {len(stats.errors)} errors occurred:[/yellow]")
        for error in stats.errors[:10]:  # Show first 10
            console.print(f"  • {error}")
        if len(stats.errors) > 10:
            console.print(f"  ... and {len(stats.errors) - 10} more")
