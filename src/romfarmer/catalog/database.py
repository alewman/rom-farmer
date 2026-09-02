"""Database models and schema using SQLAlchemy."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import (
    Session,
    declarative_base,
    relationship,
    sessionmaker,
)
from sqlalchemy.pool import StaticPool

Base = declarative_base()


class DatFile(Base):
    """DAT file metadata."""

    __tablename__ = "dat_files"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text)
    version = Column(String(100))
    author = Column(String(255))
    date = Column(String(50))

    # Tracking
    imported_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Statistics
    total_games = Column(Integer, default=0)
    total_size = Column(Integer, default=0)

    # Relationships
    games = relationship("DatGame", back_populates="dat_file", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<DatFile(name='{self.name}', version='{self.version}')>"


class DatGame(Base):
    """Game entry from DAT file."""

    __tablename__ = "dat_games"

    id = Column(Integer, primary_key=True)
    dat_file_id = Column(Integer, ForeignKey("dat_files.id"), nullable=False, index=True)

    # Game information
    name = Column(String(512), nullable=False, index=True)
    description = Column(Text)
    category = Column(String(100), index=True)

    # ROM information
    rom_name = Column(String(512), nullable=False, index=True)
    size = Column(Integer, nullable=False)
    crc = Column(String(8), nullable=False, index=True)
    md5 = Column(String(32), index=True)
    sha1 = Column(String(40), index=True)

    # Relationships
    dat_file = relationship("DatFile", back_populates="games")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_dat_crc", "dat_file_id", "crc"),
        Index("idx_dat_name", "dat_file_id", "name"),
    )

    def __repr__(self) -> str:
        return f"<DatGame(name='{self.name}', crc='{self.crc}')>"


class RomFile(Base):
    """ROM file in collection."""

    __tablename__ = "rom_files"

    id = Column(Integer, primary_key=True)

    # File information
    path = Column(String(1024), nullable=False, unique=True, index=True)
    filename = Column(String(512), nullable=False, index=True)
    size = Column(Integer, nullable=False)

    # Parsed metadata
    name = Column(String(512), nullable=False, index=True)
    regions = Column(String(255))  # Comma-separated
    languages = Column(String(255))  # Comma-separated
    kind = Column(String(50), index=True)

    # Tags and attributes
    revision = Column(String(50))
    version = Column(String(50))
    tags = Column(Text)  # JSON array

    # Multi-disc information
    disc_number = Column(Integer)
    disc_total = Column(Integer)
    disc_name = Column(String(255))

    # Hashes
    crc32 = Column(String(8), index=True)
    md5 = Column(String(32), index=True)
    sha1 = Column(String(40), index=True)

    # DAT matching
    dat_file_id = Column(Integer, ForeignKey("dat_files.id"), index=True)
    dat_game_id = Column(Integer, ForeignKey("dat_games.id"), index=True)
    verified = Column(Boolean, default=False)
    verification_date = Column(DateTime)

    # Tracking
    scanned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    dat_file = relationship("DatFile")
    dat_game = relationship("DatGame")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_rom_region_kind", "regions", "kind"),
        Index("idx_rom_crc", "crc32"),
        Index("idx_rom_verified", "verified", "dat_file_id"),
    )

    def __repr__(self) -> str:
        return f"<RomFile(name='{self.name}', path='{self.path}')>"


class OrganizationLog(Base):
    """Log of organization operations."""

    __tablename__ = "organization_logs"

    id = Column(Integer, primary_key=True)

    # Operation information
    operation_type = Column(String(50), nullable=False)  # organize, validate, etc.
    profile_name = Column(String(100))
    source_path = Column(String(1024))
    dest_path = Column(String(1024))

    # Statistics
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    skipped_files = Column(Integer, default=0)
    error_files = Column(Integer, default=0)

    # Timing
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)

    # Status
    status = Column(String(20), nullable=False)  # running, completed, failed
    error_message = Column(Text)

    def __repr__(self) -> str:
        return f"<OrganizationLog(type='{self.operation_type}', status='{self.status}')>"


class RomGroomerDatabase:
    """
    Database manager for ROM Farmer catalog.

    Provides high-level interface for database operations with
    connection pooling, transaction management, and query helpers.
    """

    def __init__(self, db_path: str = ":memory:", echo: bool = False):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file (or :memory: for in-memory)
            echo: Echo SQL statements to stdout
        """
        if db_path == ":memory:":
            # Use StaticPool for in-memory databases
            self.engine = create_engine(
                f"sqlite:///{db_path}",
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=echo,
            )
        else:
            self.engine = create_engine(
                f"sqlite:///{db_path}",
                echo=echo,
            )

        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)

        # Create all tables
        Base.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    def close(self) -> None:
        """Close database connection."""
        self.engine.dispose()

    # DAT file operations

    def add_dat_file(self, session: Session, dat: DatFile) -> DatFile:
        """Add or update DAT file."""
        existing = session.query(DatFile).filter_by(name=dat.name).first()
        if existing:
            # Update existing
            for key, value in dat.__dict__.items():
                if not key.startswith("_"):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            return existing
        else:
            session.add(dat)
            return dat

    def get_dat_file(self, session: Session, name: str) -> DatFile | None:
        """Get DAT file by name."""
        return session.query(DatFile).filter_by(name=name).first()

    def list_dat_files(self, session: Session) -> list[DatFile]:
        """List all DAT files."""
        return session.query(DatFile).order_by(DatFile.name).all()

    def add_dat_game(self, session: Session, game: DatGame) -> DatGame:
        """Add DAT game entry."""
        session.add(game)
        return game

    def find_game_by_crc(
        self, session: Session, crc: str, dat_file_id: int | None = None
    ) -> DatGame | None:
        """
        Find game by ROM CRC.

        Args:
            session: Database session
            crc: CRC32 checksum (hex string)
            dat_file_id: Optional DAT file ID to search within

        Returns:
            First matching game, or None
        """
        from sqlalchemy.orm import joinedload

        query = (
            session.query(DatGame).options(joinedload(DatGame.dat_file)).filter_by(crc=crc.lower())
        )
        if dat_file_id:
            query = query.filter_by(dat_file_id=dat_file_id)
        return query.first()

    def find_games_by_name(
        self, session: Session, name: str, dat_file_id: int | None = None
    ) -> list[DatGame]:
        """
        Find games by name (partial match).

        Args:
            session: Database session
            name: Game name to search for
            dat_file_id: Optional DAT file ID to search within

        Returns:
            List of matching games
        """
        from sqlalchemy.orm import joinedload

        query = (
            session.query(DatGame)
            .options(joinedload(DatGame.dat_file))
            .filter(DatGame.name.like(f"%{name}%"))
        )
        if dat_file_id:
            query = query.filter_by(dat_file_id=dat_file_id)
        return query.all()

    def get_dat_games(
        self, session: Session, dat_file_id: int, limit: int | None = None
    ) -> list[DatGame]:
        """
        Get games for a DAT file.

        Args:
            session: Database session
            dat_file_id: DAT file ID
            limit: Optional limit on number of results

        Returns:
            List of games
        """
        query = session.query(DatGame).filter_by(dat_file_id=dat_file_id).order_by(DatGame.name)
        if limit:
            query = query.limit(limit)
        return query.all()

    # ROM file operations

    def add_rom_file(self, session: Session, rom: RomFile) -> RomFile:
        """Add or update ROM file."""
        existing = session.query(RomFile).filter_by(path=rom.path).first()
        if existing:
            # Update existing
            for key, value in rom.__dict__.items():
                if not key.startswith("_"):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            return existing
        else:
            session.add(rom)
            return rom

    def get_rom_file(self, session: Session, path: str) -> RomFile | None:
        """Get ROM file by path."""
        return session.query(RomFile).filter_by(path=path).first()

    def find_rom_by_crc(self, session: Session, crc: str) -> list[RomFile]:
        """Find ROM files by CRC."""
        return session.query(RomFile).filter_by(crc32=crc).all()

    def find_rom_by_name(self, session: Session, name: str) -> list[RomFile]:
        """Find ROM files by name (partial match)."""
        return session.query(RomFile).filter(RomFile.name.like(f"%{name}%")).all()

    # Query helpers

    def get_statistics(self, session: Session) -> dict:
        """Get database statistics."""
        return {
            "total_dat_files": session.query(DatFile).count(),
            "total_dat_games": session.query(DatGame).count(),
            "total_rom_files": session.query(RomFile).count(),
            "verified_roms": session.query(RomFile).filter_by(verified=True).count(),
            "total_operations": session.query(OrganizationLog).count(),
        }
