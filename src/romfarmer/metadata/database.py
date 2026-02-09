"""
Database models for metadata management.

This module defines SQLAlchemy models for storing scraped game metadata
and media files with content-addressable storage for deduplication.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Float,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class MediaType(str, Enum):
    """Supported media types from ScreenScraper/ARRM."""

    IMAGE = "image"  # Title screen
    BOXART = "boxart"  # Box art
    SCREENSHOT = "screenshot"  # In-game screenshot
    CARTRIDGE = "cartridge"  # Cartridge/disc art
    WHEEL = "wheel"  # Logo/wheel art
    MARQUEE = "marquee"  # Marquee/banner
    MIX = "mix"  # Composite image (ARRM-generated)
    VIDEO = "video"  # Video preview
    MANUAL = "manual"  # PDF manual

    @classmethod
    def all_types(cls) -> list[str]:
        """Return all media types."""
        return [t.value for t in cls]

    @classmethod
    def standard_types(cls) -> list[str]:
        """Return standard media types (excluding manuals and videos)."""
        return [
            cls.IMAGE.value,
            cls.BOXART.value,
            cls.SCREENSHOT.value,
            cls.WHEEL.value,
            cls.MIX.value,
        ]

    @classmethod
    def minimal_types(cls) -> list[str]:
        """Return minimal media types (just mix image)."""
        return [cls.MIX.value]


class ScrapedGame(Base):
    """
    Scraped game metadata from ScreenScraper.fr (via ARRM).

    This model stores comprehensive game information including metadata
    and links to deduplicated media files. Games are tracked by their
    hashes, allowing files to be reorganized without losing metadata.
    """

    __tablename__ = "scraped_games"

    # Primary key
    id = Column(Integer, primary_key=True)

        # File identifiers (for matching ROMs)
    md5 = Column(String(32), index=True)  # Primary matching hash
    crc32 = Column(String(8), index=True)
    sha1 = Column(String(40))
    filename = Column(String(512))  # Original filename

    # ScreenScraper IDs
    game_id = Column(Integer)  # ScreenScraper game ID
    rom_id = Column(Integer)  # ScreenScraper ROM ID

    # System information
    system = Column(String(128), index=True)  # System name (e.g., "nes")
    
    # Source tracking (for smart updates)
    source_gamelist_path = Column(String(1024))  # Path to source gamelist.xml
    source_gamelist_mtime = Column(DateTime)  # Modification time of source gamelist

    # Game metadata
    name = Column(String(512))  # Display name
    sortname = Column(String(512))  # Sort name
    description = Column(Text)  # Game description
    rating = Column(Float)  # Rating (0.0-1.0)
    release_date = Column(String(32))  # Release date (YYYYMMDD format)
    developer = Column(String(256))  # Developer
    publisher = Column(String(256))  # Publisher
    genre = Column(String(256))  # Genre
    genre_id = Column(Integer)  # ScreenScraper genre ID
    players = Column(String(32))  # Player count (e.g., "1-2")
    region = Column(String(128))  # Region codes (e.g., "us,wor")
    language = Column(String(128))  # Language codes (e.g., "en,ja")
    hidden = Column(Boolean, default=False)  # EmulationStation hidden flag
    favorite = Column(Boolean, default=False)  # EmulationStation favorite flag
    kidgame = Column(Boolean, default=False)  # EmulationStation kid-friendly flag
    playcount = Column(Integer, default=0)  # Number of times played
    lastplayed = Column(DateTime)  # Last played timestamp

    # Metadata versioning
    metadata_version = Column(Integer, default=1)  # Version for updates
    scraped_at = Column(DateTime, default=datetime.utcnow)  # First scraped
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source = Column(String(64), default="arrm")  # Metadata source

    # Relationships
    media_links = relationship(
        "GameMediaLink",
        back_populates="game",
        cascade="all, delete-orphan",
    )
    transformations = relationship(
        "ROMTransformation",
        back_populates="game",
        cascade="all, delete-orphan",
    )

    # Indexes for fast lookups
    __table_args__ = (
        Index("idx_hash_lookup", "md5", "crc32", "sha1"),
        Index("idx_system_name", "system", "name"),
    )

    def __repr__(self) -> str:
        return f"<ScrapedGame(name='{self.name}', system='{self.system}', md5='{self.md5}')>"


class MediaFile(Base):
    """
    Deduplicated media file storage.

    Media files are stored using content-addressable storage (like Git).
    Each unique file is stored once based on its hash, and multiple games
    can reference the same media file. This provides:
    - Deduplication: Clones share the same media
    - Integrity: Files verified by hash
    - Efficiency: Reduced storage and bandwidth
    """

    __tablename__ = "media_files"

    # Primary key
    id = Column(Integer, primary_key=True)

    # Content addressing
    file_hash = Column(String(64), unique=True, nullable=False, index=True)
    media_type = Column(String(32), nullable=False, index=True)

    # File storage
    file_path = Column(String(1024), nullable=False)  # Path in storage
    file_size = Column(Integer, nullable=False)  # Size in bytes
    file_format = Column(String(32))  # Extension (png, jpg, mp4, pdf)

    # Image metadata (for images only)
    width = Column(Integer)
    height = Column(Integer)
    image_mode = Column(String(16))  # Color mode (RGB, RGBA, L, etc.)
    has_transparency = Column(Boolean)  # True if image has alpha channel

    # Video metadata (for videos only)
    video_codec = Column(String(32))  # Video codec (h264, vp9, etc.)
    video_bitrate = Column(Integer)  # Video bitrate in bits/second
    video_fps = Column(String(16))  # Frame rate (e.g., "30/1", "59.94")
    video_duration = Column(Float)  # Duration in seconds

    # Source tracking
    source_url = Column(String(1024))  # Original URL from ScreenScraper
    source_file_mtime = Column(DateTime)  # Modification time of source file
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Reference counting (for cleanup)
    reference_count = Column(Integer, default=0)

    # Relationships
    game_links = relationship(
        "GameMediaLink",
        back_populates="media_file",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (Index("idx_media_type_hash", "media_type", "file_hash"),)

    def __repr__(self) -> str:
        return f"<MediaFile(type='{self.media_type}', hash='{self.file_hash[:8]}...', refs={self.reference_count})>"

    @property
    def storage_path(self) -> Path:
        """Get the storage path for this media file."""
        return Path(self.file_path)

    def increment_references(self) -> None:
        """Increment the reference count."""
        self.reference_count += 1

    def decrement_references(self) -> None:
        """Decrement the reference count."""
        if self.reference_count > 0:
            self.reference_count -= 1


class GameMediaLink(Base):
    """
    Many-to-many relationship between games and media files.

    This table links games to their media files, allowing:
    - One game to have multiple media types
    - Multiple games to share the same media file (deduplication)
    - Priority ordering when multiple media of same type exist
    """

    __tablename__ = "game_media_links"

    # Composite primary key
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("scraped_games.id"), nullable=False)
    media_file_id = Column(Integer, ForeignKey("media_files.id"), nullable=False)

    # Media role
    media_type = Column(String(32), nullable=False)  # Type for this link
    priority = Column(Integer, default=0)  # Priority when multiple exist

    # Relationships
    game = relationship("ScrapedGame", back_populates="media_links")
    media_file = relationship("MediaFile", back_populates="game_links")

    # Constraints
    # Allow same media file to be used with different media types
    # (e.g., mix and image can be the same file)
    __table_args__ = (
        UniqueConstraint("game_id", "media_file_id", "media_type", name="uq_game_media_type"),
        Index("idx_game_media_type", "game_id", "media_type"),
    )

    def __repr__(self) -> str:
        return f"<GameMediaLink(game_id={self.game_id}, type='{self.media_type}', priority={self.priority})>"


class DatGameEntry(Base):
    """
    Game entry from DAT files (No-Intro, Redump, FBNeo, MAME).
    
    Stores parent-clone relationships, hardware info, and video specs
    that complement the scraped metadata from ScreenScraper.
    """
    
    __tablename__ = "dat_games"
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # ROM identification
    name = Column(String(256), nullable=False, index=True)  # ROM name (e.g., "sf2ce")
    description = Column(String(1024))  # Full title
    
    # Parent-clone relationships
    cloneof = Column(String(256), index=True)  # Parent ROM name
    romof = Column(String(256))  # ROM parent (for merged sets)
    
    # Temporal info
    year = Column(String(8))
    manufacturer = Column(String(256))
    
    # Hardware/driver info
    sourcefile = Column(String(256), index=True)  # Driver source (e.g., "capcom/d_cps1.cpp")
    hardware = Column(String(64), index=True)  # Extracted hardware name (e.g., "cps1")
    hardware_family = Column(String(64), index=True)  # Hardware family (e.g., "capcom")
    driver_status = Column(String(32), default="good")  # good, imperfect, preliminary
    
    # Video specs
    video_type = Column(String(16))  # raster, vector
    video_orientation = Column(String(16))  # horizontal, vertical
    video_width = Column(Integer)
    video_height = Column(Integer)
    video_aspect_x = Column(Integer)
    video_aspect_y = Column(Integer)
    video_refresh = Column(Float)
    
    # Metadata
    comment = Column(String(256))  # Bootleg, Prototype, etc.
    category = Column(String(128))
    
    # ROM identification (first ROM)
    rom_crc = Column(String(8), index=True)
    rom_size = Column(Integer)
    
    # Source DAT info
    dat_name = Column(String(256))
    dat_type = Column(String(32), index=True)  # fbneo, mame, nointro, redump
    
    # Timestamps
    imported_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_dat_hardware", "dat_type", "hardware"),
        Index("idx_dat_cloneof", "dat_type", "cloneof"),
        UniqueConstraint("dat_type", "name", name="uq_dat_game"),
    )
    
    def __repr__(self) -> str:
        return f"<DatGameEntry(name='{self.name}', hardware='{self.hardware}', cloneof='{self.cloneof}')>"
    
    @property
    def is_parent(self) -> bool:
        return self.cloneof is None
    
    @property
    def is_clone(self) -> bool:
        return self.cloneof is not None
    
    @property
    def is_bootleg(self) -> bool:
        if self.comment and 'bootleg' in self.comment.lower():
            return True
        if self.description and 'bootleg' in self.description.lower():
            return True
        return False
    
    @property
    def resolution(self) -> str:
        if self.video_width and self.video_height:
            return f"{self.video_width}x{self.video_height}"
        return ""
    
    @property
    def aspect_ratio(self) -> str:
        if self.video_aspect_x and self.video_aspect_y:
            return f"{self.video_aspect_x}:{self.video_aspect_y}"
        return ""


class MetadataDatabase:
    """
    High-level interface for metadata database operations.

    This class provides convenience methods for:
    - Importing ARRM gamelist.xml files
    - Storing and retrieving game metadata
    - Managing deduplicated media files
    - Generating gamelist.xml files
    - Smart updates (keep old data, replace with better)
    """

    def __init__(self, db_path: Path):
        """
        Initialize metadata database.

        Args:
            db_path: Path to SQLite database file
        """
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self):
        """Get a new database session."""
        return self.Session()

    def find_game_by_hash(
        self,
        md5: Optional[str] = None,
        crc32: Optional[str] = None,
        sha1: Optional[str] = None,
    ) -> Optional[ScrapedGame]:
        """
        Find a game by any of its hashes.

        Args:
            md5: MD5 hash
            crc32: CRC32 hash
            sha1: SHA1 hash

        Returns:
            ScrapedGame if found, None otherwise (with relationships loaded)
        """
        from sqlalchemy.orm import joinedload
        
        with self.get_session() as session:
            query = session.query(ScrapedGame).options(
                joinedload(ScrapedGame.media_links).joinedload(GameMediaLink.media_file)
            )

            if md5:
                result = query.filter(ScrapedGame.md5 == md5).first()
                if result:
                    # Force load relationships before detaching
                    _ = result.media_links  # Trigger lazy load
                    for link in result.media_links:
                        _ = link.media_file  # Ensure nested relationships loaded
                    session.expunge(result)  # Detach from session but keep data
                    return result

            if crc32:
                result = query.filter(ScrapedGame.crc32 == crc32).first()
                if result:
                    # Force load relationships before detaching
                    _ = result.media_links
                    for link in result.media_links:
                        _ = link.media_file
                    session.expunge(result)
                    return result

            if sha1:
                result = query.filter(ScrapedGame.sha1 == sha1).first()
                if result:
                    # Force load relationships before detaching
                    _ = result.media_links
                    for link in result.media_links:
                        _ = link.media_file
                    session.expunge(result)
                    return result

            return None

    def find_or_create_media(
        self,
        file_hash: str,
        media_type: str,
        file_path: Path,
        file_size: int,
        **kwargs,
    ) -> MediaFile:
        """
        Find existing media file or create new one.

        This implements content-addressable storage - if a file with
        the same hash already exists, we reuse it (deduplication).

        Args:
            file_hash: Content hash of the file
            media_type: Type of media (image, boxart, etc.)
            file_path: Path where file is stored
            file_size: Size in bytes
            **kwargs: Additional metadata (width, height, etc.)

        Returns:
            MediaFile (existing or newly created)
        """
        with self.get_session() as session:
            # Try to find existing media
            media = (
                session.query(MediaFile)
                .filter(MediaFile.file_hash == file_hash)
                .first()
            )

            if media:
                # Existing media found - increment references
                media.increment_references()
                session.commit()
                return media

            # Create new media file
            media = MediaFile(
                file_hash=file_hash,
                media_type=media_type,
                file_path=str(file_path),
                file_size=file_size,
                file_format=file_path.suffix.lstrip("."),
                **kwargs,
            )
            session.add(media)
            session.commit()
            return media

    def get_game_media(
        self,
        game: ScrapedGame,
        media_types: Optional[list[str]] = None,
    ) -> dict[str, MediaFile]:
        """
        Get media files for a game, optionally filtered by type.

        Args:
            game: Game to get media for (should have media_links loaded)
            media_types: List of media types to include (None = all)

        Returns:
            Dictionary mapping media type to MediaFile
        """
        result = {}

        for link in game.media_links:
            if media_types is None or link.media_type in media_types:
                result[link.media_type] = link.media_file

        return result

    def get_average_compression_ratio(
        self,
        platform: Optional[str] = None,
        output_format: Optional[str] = None,
        min_samples: int = 5
    ) -> Optional[float]:
        """
        Calculate average compression ratio from historical transformations.
        
        Queries the rom_transformations table to find the average ratio of
        final_file_size / source_file_size for a given platform and format.
        
        Args:
            platform: Platform name to filter by (e.g., "saturn", "psx")
            output_format: Output format to filter by (e.g., "chd", "cso")
            min_samples: Minimum number of samples required for reliable average
        
        Returns:
            Average compression ratio (0.0-1.0), or None if insufficient data
            
        Example:
            ratio = db.get_average_compression_ratio("saturn", "chd")
            # Returns 0.68 meaning CHD is 68% of source ISO size
        """
        from sqlalchemy import func
        from .transformation import ROMTransformation
        
        with self.get_session() as session:
            query = session.query(
                func.avg(
                    ROMTransformation.final_file_size * 1.0 / ROMTransformation.source_file_size
                ).label('avg_ratio'),
                func.count(ROMTransformation.id).label('sample_count')
            )
            
            # Filter out transformations with missing size data
            query = query.filter(
                ROMTransformation.source_file_size > 0,
                ROMTransformation.final_file_size > 0
            )
            
            # Apply platform filter (if specified)
            if platform:
                # Join with ScrapedGame to filter by system
                query = query.join(
                    ScrapedGame,
                    ROMTransformation.game_id == ScrapedGame.id
                ).filter(
                    ScrapedGame.system == platform
                )
            
            # Apply format filter (if specified)
            if output_format:
                query = query.filter(
                    ROMTransformation.final_format == output_format
                )
            
            result = query.first()
            
            if result and result.sample_count >= min_samples:
                return result.avg_ratio
            
            return None

    def get_stats(self) -> dict:
        """
        Get database statistics.

        Returns:
            Dictionary with counts and sizes
        """
        with self.get_session() as session:
            total_games = session.query(ScrapedGame).count()
            total_media = session.query(MediaFile).count()
            total_links = session.query(GameMediaLink).count()

            # Calculate total media size
            total_size = (
                session.query(MediaFile)
                .with_entities(MediaFile.file_size)
                .all()
            )
            total_bytes = sum(row[0] for row in total_size if row[0])

            # Calculate deduplication savings
            # If we had no deduplication, each link would need a separate file
            potential_size = total_links * (total_bytes / max(total_media, 1))
            savings = potential_size - total_bytes if total_media > 0 else 0
            savings_percent = (
                (savings / potential_size * 100) if potential_size > 0 else 0
            )

            return {
                "total_games": total_games,
                "total_media_files": total_media,
                "total_media_links": total_links,
                "total_size_bytes": total_bytes,
                "total_size_mb": total_bytes / (1024 * 1024),
                "potential_size_bytes": potential_size,
                "savings_bytes": savings,
                "savings_mb": savings / (1024 * 1024),
                "savings_percent": savings_percent,
                "avg_references_per_file": (
                    total_links / total_media if total_media > 0 else 0
                ),
            }

    def get_games_for_platform(self, platform: str) -> list[ScrapedGame]:
        """
        Get all games for a specific platform/system.
        
        Args:
            platform: System name (e.g., "megadrive", "psx", "snes")
            
        Returns:
            List of ScrapedGame objects for that platform
        """
        with self.get_session() as session:
            games = session.query(ScrapedGame).filter(
                ScrapedGame.system == platform
            ).all()
            
            # Detach from session
            for g in games:
                session.expunge(g)
            
            return games

    def search_games(
        self,
        platform: Optional[str] = None,
        query: Optional[str] = None,
        genre: Optional[str] = None,
        developer: Optional[str] = None,
        publisher: Optional[str] = None,
        min_rating: Optional[float] = None,
        limit: int = 50,
        deduplicate: bool = True,
        title_only: bool = False,
    ) -> list[ScrapedGame]:
        """
        Search for games with flexible filtering.
        
        Args:
            platform: Filter by system (e.g., "megadrive", "psx")
            query: Search in name/description (fuzzy)
            genre: Filter by genre (partial match)
            developer: Filter by developer (partial match)
            publisher: Filter by publisher (partial match)
            min_rating: Minimum rating (0.0-1.0)
            limit: Maximum results to return
            deduplicate: If True, show only one entry per game_id (default True)
            title_only: If True, only search in title, not description (default False)
            
        Returns:
            List of matching ScrapedGame objects
        """
        with self.get_session() as session:
            q = session.query(ScrapedGame)
            
            if platform:
                q = q.filter(ScrapedGame.system == platform)
            
            if query:
                search_pattern = f"%{query}%"
                if title_only:
                    # Only search in name - more precise
                    q = q.filter(ScrapedGame.name.ilike(search_pattern))
                else:
                    # Search in name and description
                    q = q.filter(
                        (ScrapedGame.name.ilike(search_pattern)) |
                        (ScrapedGame.description.ilike(search_pattern))
                    )
            
            if genre:
                q = q.filter(ScrapedGame.genre.ilike(f"%{genre}%"))
            
            if developer:
                q = q.filter(ScrapedGame.developer.ilike(f"%{developer}%"))
            
            if publisher:
                q = q.filter(ScrapedGame.publisher.ilike(f"%{publisher}%"))
            
            if min_rating is not None:
                q = q.filter(ScrapedGame.rating >= min_rating)
            
            # Order by rating (best first), then name
            q = q.order_by(ScrapedGame.rating.desc().nullslast(), ScrapedGame.name)
            
            # Get more results if deduplicating (we'll filter down)
            fetch_limit = limit * 5 if deduplicate else limit
            all_games = q.limit(fetch_limit).all()
            
            if deduplicate:
                # Keep only one entry per game_id (preferring US/World regions)
                seen_game_ids = set()
                games = []
                region_priority = ['us', 'wor', 'eu', 'jp']  # Preference order
                
                # First pass: group by game_id
                by_game_id = {}
                for g in all_games:
                    gid = g.game_id or g.name  # Fallback to name if no game_id
                    if gid not in by_game_id:
                        by_game_id[gid] = []
                    by_game_id[gid].append(g)
                
                # Second pass: pick best variant per game_id
                for gid, variants in by_game_id.items():
                    if len(games) >= limit:
                        break
                    
                    # Sort variants by region priority
                    def region_sort_key(game):
                        region = (game.region or '').lower()
                        for i, r in enumerate(region_priority):
                            if r in region:
                                return i
                        return len(region_priority)  # Unknown regions last
                    
                    variants.sort(key=region_sort_key)
                    best = variants[0]
                    session.expunge(best)
                    games.append(best)
            else:
                games = all_games[:limit]
                for g in games:
                    session.expunge(g)
            
            return games

    def get_game_variants(
        self,
        game_id: int,
        platform: Optional[str] = None,
    ) -> list[ScrapedGame]:
        """
        Get all regional/revision variants of a game by its game_id.
        
        Args:
            game_id: ScreenScraper game ID
            platform: Optional system filter
            
        Returns:
            List of all variants (different regions, revisions)
        """
        with self.get_session() as session:
            q = session.query(ScrapedGame).filter(ScrapedGame.game_id == game_id)
            
            if platform:
                q = q.filter(ScrapedGame.system == platform)
            
            q = q.order_by(ScrapedGame.region, ScrapedGame.name)
            
            games = q.all()
            for g in games:
                session.expunge(g)
            
            return games

    def get_game_by_name(
        self,
        name: str,
        platform: Optional[str] = None,
    ) -> Optional[ScrapedGame]:
        """
        Find a game by exact or close name match.
        
        Args:
            name: Game name to search for
            platform: Optional system filter
            
        Returns:
            Best matching ScrapedGame, or None
        """
        with self.get_session() as session:
            q = session.query(ScrapedGame)
            
            # Try exact match first
            if platform:
                q = q.filter(ScrapedGame.system == platform)
            
            exact = q.filter(ScrapedGame.name == name).first()
            if exact:
                session.expunge(exact)
                return exact
            
            # Try case-insensitive
            result = q.filter(ScrapedGame.name.ilike(name)).first()
            if result:
                session.expunge(result)
                return result
            
            # Try partial match
            result = q.filter(ScrapedGame.name.ilike(f"%{name}%")).first()
            if result:
                session.expunge(result)
                return result
            
            return None

    def get_platforms(self) -> list[dict]:
        """
        Get all platforms with game counts.
        
        Returns:
            List of dicts with platform name and count
        """
        from sqlalchemy import func
        
        with self.get_session() as session:
            results = session.query(
                ScrapedGame.system,
                func.count(ScrapedGame.id).label('count')
            ).group_by(ScrapedGame.system).order_by(func.count(ScrapedGame.id).desc()).all()
            
            return [
                {"platform": r[0], "game_count": r[1]}
                for r in results
            ]

    def get_genres(self, platform: Optional[str] = None) -> list[dict]:
        """
        Get all genres with game counts.
        
        Args:
            platform: Optional platform filter
            
        Returns:
            List of dicts with genre and count
        """
        from sqlalchemy import func
        
        with self.get_session() as session:
            q = session.query(
                ScrapedGame.genre,
                func.count(ScrapedGame.id).label('count')
            )
            
            if platform:
                q = q.filter(ScrapedGame.system == platform)
            
            results = q.filter(
                ScrapedGame.genre.isnot(None),
                ScrapedGame.genre != ''
            ).group_by(ScrapedGame.genre).order_by(func.count(ScrapedGame.id).desc()).all()
            
            return [
                {"genre": r[0], "game_count": r[1]}
                for r in results
            ]

    # ==================== DAT FILE METHODS ====================
    
    def import_dat_file(self, dat_path: Path, replace: bool = False) -> dict:
        """
        Import games from a DAT file into the database.
        
        Args:
            dat_path: Path to DAT file
            replace: If True, replace existing entries for this DAT
            
        Returns:
            Dict with import statistics
        """
        import re
        from .dat_parser import DatParser
        
        parser = DatParser(dat_path)
        
        stats = {
            "dat_name": None,
            "dat_type": None,
            "total": 0,
            "imported": 0,
            "updated": 0,
            "skipped": 0,
        }
        
        with self.get_session() as session:
            # Delete existing entries if replacing
            if replace and parser.dat_name:
                deleted = session.query(DatGameEntry).filter(
                    DatGameEntry.dat_name == parser.dat_name
                ).delete()
                session.commit()
                stats["deleted"] = deleted
            
            for game in parser.parse():
                stats["total"] += 1
                stats["dat_name"] = parser.dat_name
                stats["dat_type"] = parser.dat_type
                
                # Check if entry already exists
                existing = session.query(DatGameEntry).filter(
                    DatGameEntry.dat_type == parser.dat_type,
                    DatGameEntry.name == game.name
                ).first()
                
                if existing and not replace:
                    stats["skipped"] += 1
                    continue
                
                # Extract hardware from sourcefile
                hardware = None
                hardware_family = None
                if game.sourcefile:
                    match = re.search(r'd_(\w+)\.cpp', game.sourcefile)
                    if match:
                        hardware = match.group(1)
                    parts = game.sourcefile.split('/')
                    if len(parts) >= 2:
                        hardware_family = parts[0]
                
                entry = DatGameEntry(
                    name=game.name,
                    description=game.description,
                    cloneof=game.cloneof,
                    romof=game.romof,
                    year=game.year,
                    manufacturer=game.manufacturer,
                    sourcefile=game.sourcefile,
                    hardware=hardware,
                    hardware_family=hardware_family,
                    driver_status=game.driver_status,
                    comment=game.comment,
                    category=game.category,
                    rom_crc=game.rom_crc,
                    rom_size=game.rom_size,
                    dat_name=parser.dat_name,
                    dat_type=parser.dat_type,
                )
                
                # Add video specs if present
                if game.video:
                    entry.video_type = game.video.type
                    entry.video_orientation = game.video.orientation
                    entry.video_width = game.video.width
                    entry.video_height = game.video.height
                    entry.video_aspect_x = game.video.aspect_x
                    entry.video_aspect_y = game.video.aspect_y
                    entry.video_refresh = game.video.refresh
                
                if existing:
                    # Update existing
                    for key, value in entry.__dict__.items():
                        if not key.startswith('_') and key != 'id':
                            setattr(existing, key, value)
                    stats["updated"] += 1
                else:
                    session.add(entry)
                    stats["imported"] += 1
                
                # Commit in batches
                if stats["total"] % 1000 == 0:
                    session.commit()
            
            session.commit()
        
        return stats
    
    def get_hardware_games(
        self,
        hardware: str,
        dat_type: str = "fbneo",
        parents_only: bool = False,
    ) -> list[DatGameEntry]:
        """
        Get all games for a specific hardware/driver.
        
        Args:
            hardware: Hardware name (e.g., "cps1", "neogeo")
            dat_type: DAT type to search
            parents_only: If True, only return parent games (no clones)
            
        Returns:
            List of DatGameEntry objects
        """
        with self.get_session() as session:
            q = session.query(DatGameEntry).filter(
                DatGameEntry.dat_type == dat_type,
                DatGameEntry.hardware == hardware
            )
            
            if parents_only:
                q = q.filter(DatGameEntry.cloneof.is_(None))
            
            return q.order_by(DatGameEntry.description).all()
    
    def get_dat_game_variants(
        self,
        game_name: str,
        dat_type: str = "fbneo",
    ) -> dict:
        """
        Get a game and all its variants/clones from DAT data.
        
        Args:
            game_name: ROM name to search for
            dat_type: DAT type to search
            
        Returns:
            Dict with parent and clones
        """
        with self.get_session() as session:
            # Find the game
            target = session.query(DatGameEntry).filter(
                DatGameEntry.dat_type == dat_type,
                DatGameEntry.name == game_name
            ).first()
            
            if not target:
                # Try partial match
                target = session.query(DatGameEntry).filter(
                    DatGameEntry.dat_type == dat_type,
                    DatGameEntry.name.ilike(f"%{game_name}%")
                ).first()
            
            if not target:
                return {"parent": None, "clones": [], "target": None}
            
            # Find root parent
            parent = target
            while parent.cloneof:
                parent_game = session.query(DatGameEntry).filter(
                    DatGameEntry.dat_type == dat_type,
                    DatGameEntry.name == parent.cloneof
                ).first()
                if parent_game:
                    parent = parent_game
                else:
                    break
            
            # Find all clones
            clones = session.query(DatGameEntry).filter(
                DatGameEntry.dat_type == dat_type,
                DatGameEntry.cloneof == parent.name
            ).order_by(DatGameEntry.name).all()
            
            # Convert to dicts to avoid detached instance issues
            def to_dict(g):
                return {
                    "name": g.name,
                    "description": g.description,
                    "year": g.year,
                    "manufacturer": g.manufacturer,
                    "hardware": g.hardware,
                    "hardware_family": g.hardware_family,
                    "driver_status": g.driver_status,
                    "cloneof": g.cloneof,
                    "video_width": g.video_width,
                    "video_height": g.video_height,
                    "video_orientation": g.video_orientation,
                    "is_bootleg": g.is_bootleg,
                    "comment": g.comment,
                }
            
            return {
                "parent": to_dict(parent),
                "clones": [to_dict(c) for c in clones],
                "target": to_dict(target),
                "clone_count": len(clones),
            }
    
    def get_hardware_list(self, dat_type: str = "fbneo") -> list[dict]:
        """
        Get all hardware types with game counts.
        
        Args:
            dat_type: DAT type to query
            
        Returns:
            List of dicts with hardware name and counts
        """
        from sqlalchemy import func, case
        
        with self.get_session() as session:
            results = session.query(
                DatGameEntry.hardware,
                DatGameEntry.hardware_family,
                func.count(DatGameEntry.id).label('total'),
                func.sum(
                    case((DatGameEntry.cloneof.is_(None), 1), else_=0)
                ).label('parents'),
            ).filter(
                DatGameEntry.dat_type == dat_type,
                DatGameEntry.hardware.isnot(None)
            ).group_by(
                DatGameEntry.hardware,
                DatGameEntry.hardware_family
            ).order_by(func.count(DatGameEntry.id).desc()).all()
            
            return [
                {
                    "hardware": r[0],
                    "family": r[1],
                    "total_games": r[2],
                    "parent_games": r[3],
                    "clone_games": r[2] - r[3],
                }
                for r in results
            ]
    
    def search_dat_games(
        self,
        query: str,
        dat_type: str = "fbneo",
        hardware: Optional[str] = None,
        parents_only: bool = False,
        limit: int = 50,
    ) -> list[dict]:
        """
        Search DAT games by name or description.
        
        Args:
            query: Search query
            dat_type: DAT type to search
            hardware: Optional hardware filter
            parents_only: If True, only return parents
            limit: Max results
            
        Returns:
            List of matching games as dicts
        """
        with self.get_session() as session:
            q = session.query(DatGameEntry).filter(
                DatGameEntry.dat_type == dat_type,
                (DatGameEntry.name.ilike(f"%{query}%")) |
                (DatGameEntry.description.ilike(f"%{query}%"))
            )
            
            if hardware:
                q = q.filter(DatGameEntry.hardware == hardware)
            
            if parents_only:
                q = q.filter(DatGameEntry.cloneof.is_(None))
            
            results = q.order_by(DatGameEntry.description).limit(limit).all()
            
            return [
                {
                    "name": g.name,
                    "description": g.description,
                    "year": g.year,
                    "manufacturer": g.manufacturer,
                    "hardware": g.hardware,
                    "cloneof": g.cloneof,
                    "is_parent": g.is_parent,
                    "driver_status": g.driver_status,
                    "resolution": g.resolution,
                    "orientation": g.video_orientation,
                }
                for g in results
            ]
