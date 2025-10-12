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
                    session.expunge(result)  # Detach from session but keep data
                    return result

            if crc32:
                result = query.filter(ScrapedGame.crc32 == crc32).first()
                if result:
                    session.expunge(result)
                    return result

            if sha1:
                result = query.filter(ScrapedGame.sha1 == sha1).first()
                if result:
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
