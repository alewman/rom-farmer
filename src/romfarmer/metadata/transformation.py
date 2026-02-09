"""
ROM Transformation Tracking

Tracks the transformation chain from source ROMs (Redump, No-Intro) to final
processed files (XISO, CHD, CSO, etc.). This enables smart scraping by
maintaining hash relationships between original and processed files.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


class ROMTransformation(Base):
    """
    Tracks the transformation from source ROM to final processed file.
    
    This allows us to query ScreenScraper with source hashes (what they know)
    even when we have processed files (XISO, CHD, etc.) that have different hashes.
    
    Example:
        Source: Halo 3 (USA).iso (MD5: abc123, from Redump)
        Tool: extract-xiso v2.5.0
        Final: Halo 3 (USA).xiso (MD5: xyz789)
        
        When scraping the XISO file, we can look up xyz789 in this table,
        find the source hash abc123, and query ScreenScraper with that.
    """
    __tablename__ = "rom_transformations"
    
    id = Column(Integer, primary_key=True)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Source File (what ScreenScraper knows about)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    source_md5 = Column(String(32), index=True, nullable=False)
    source_sha1 = Column(String(40))
    source_sha256 = Column(String(64))
    source_crc32 = Column(String(8))
    source_file_size = Column(BigInteger)
    source_file_name = Column(String(512))
    
    # Source format and DAT info
    source_format = Column(String(32))  # "redump-iso", "nointro-zip", etc.
    source_dat = Column(String(128))    # "Redump - Microsoft Xbox 360", "No-Intro - NES"
    source_verified = Column(Boolean, default=False)  # From official DAT?
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Transformation Metadata
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    transformation_tool = Column(String(64), nullable=False)     # "extract-xiso", "maxcso", "chdman"
    transformation_version = Column(String(32))                  # "v2.5.0"
    transformation_params = Column(JSON)                         # {"compression": 9, "level": "max"}
    transformation_date = Column(DateTime, default=datetime.utcnow)
    transformation_host = Column(String(128))                    # For debugging/tracking
    
    # Performance metrics
    transformation_duration_seconds = Column(Float)              # How long it took
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Final File (what you actually have)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    final_md5 = Column(String(32), index=True, nullable=False)  # Not unique - multiple sources can → same final
    final_sha1 = Column(String(40))
    final_sha256 = Column(String(64))
    final_crc32 = Column(String(8))
    final_file_size = Column(BigInteger)
    final_file_name = Column(String(512))
    final_format = Column(String(32))      # "xiso", "cso", "chd", "rvz"
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Verification & Community
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    verified = Column(Boolean, default=False)                    # Has this been verified?
    verification_count = Column(Integer, default=0)              # How many users confirmed
    community_reported = Column(Boolean, default=False)          # From community DB?
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Relationships
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    game_id = Column(Integer, ForeignKey("scraped_games.id"))
    game = relationship("ScrapedGame", back_populates="transformations")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Indexes for fast lookup
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    __table_args__ = (
        # Unique constraint: same source → same final (prevent duplicates)
        UniqueConstraint('source_md5', 'final_md5', name='uq_source_final'),
        
        # Fast lookup by source hash (for generating transformations)
        Index('idx_source_hash', 'source_md5', 'source_format'),
        
        # Fast lookup by final hash (for finding source when scraping)
        Index('idx_final_hash', 'final_md5', 'final_format'),
        
        # Fast lookup by tool/version (for analysis)
        Index('idx_tool_version', 'transformation_tool', 'transformation_version'),
        
        # Fast lookup for verified transformations
        Index('idx_verified', 'verified', 'source_verified'),
    )
    
    def __repr__(self):
        return (
            f"<ROMTransformation("
            f"source={self.source_md5[:8]}..., "
            f"tool={self.transformation_tool}, "
            f"final={self.final_md5[:8]}..."
            f")>"
        )


class HashCache(Base):
    """
    Cache calculated hashes to avoid recalculation.
    
    Only needed for files NOT in DAT files. Most files (95%+) will have
    hashes instantly available from Redump/No-Intro DATs.
    """
    __tablename__ = "hash_cache"
    
    id = Column(Integer, primary_key=True)
    
    # File identity (cache key)
    file_path = Column(String(1024), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    file_mtime = Column(DateTime, nullable=False)  # Modification time
    
    # Cached hashes
    md5 = Column(String(32), index=True)
    sha1 = Column(String(40))
    sha256 = Column(String(64))
    crc32 = Column(String(8))
    
    # Cache metadata
    calculated_at = Column(DateTime, default=datetime.utcnow)
    calculation_time_seconds = Column(Float)
    
    # Indexes for fast lookups
    __table_args__ = (
        # Lookup by file identity
        Index('idx_cache_file_identity', 'file_path', 'file_size', 'file_mtime'),
        
        # Reverse lookup by hash
        Index('idx_cache_hash_lookup', 'md5', 'sha1'),
    )
    
    def __repr__(self):
        return (
            f"<HashCache("
            f"file={self.file_path[-50:]}, "
            f"md5={self.md5[:8] if self.md5 else 'None'}..."
            f")>"
        )


class ZipContentCache(Base):
    """
    Cache mapping ZIP file identity → contained file MD5.
    
    For torrentzipped archives (Myrient, etc.), we can read the CRC32 from
    the ZIP header instantly without decompression. This table caches the
    expensive MD5 calculation of the contained file, keyed by the fast-to-read
    ZIP metadata.
    
    This provides ~69x speedup for large disc-based systems:
    - Without cache: ~40 min (calculate MD5 for 2000+ GB of ISOs)
    - With cache: ~35 sec (read ZIP headers + DB lookup)
    
    Example:
        ZIP: "007 - Nightfire (USA).zip" (1.2GB)
        Content CRC32: 0c702336 (instant to read from header)
        Content MD5: 9fa391e006b4103160f7eb9059d641cf (slow to calculate)
        
        First run: Calculate MD5, store in cache
        Future runs: Read CRC32 → lookup MD5 → instant!
    """
    __tablename__ = "zip_content_cache"
    
    id = Column(Integer, primary_key=True)
    
    # ZIP file identity (for cache invalidation if file changes)
    zip_path = Column(String(1024), nullable=False)
    zip_size = Column(BigInteger, nullable=False)
    
    # Content identity from ZIP header (cache key - instant to read)
    content_filename = Column(String(512), nullable=False)
    content_crc32 = Column(String(8), nullable=False)  # Hex string, e.g., "0c702336"
    content_size = Column(BigInteger, nullable=False)  # Uncompressed size
    
    # Cached hash of contained file (expensive to calculate)
    content_md5 = Column(String(32), nullable=False, index=True)
    
    # Cache metadata
    calculated_at = Column(DateTime, default=datetime.utcnow)
    calculation_time_seconds = Column(Float)
    
    # Indexes for fast lookups
    __table_args__ = (
        # Primary lookup: CRC32 + size (unique for torrentzipped files)
        Index('idx_zip_content_lookup', 'content_crc32', 'content_size'),
        
        # Secondary: by zip path for cache management
        Index('idx_zip_path', 'zip_path'),
        
        # Unique constraint: same CRC32 + size should have same MD5
        UniqueConstraint('content_crc32', 'content_size', name='uq_content_identity'),
    )
    
    def __repr__(self):
        return (
            f"<ZipContentCache("
            f"crc32={self.content_crc32}, "
            f"md5={self.content_md5[:8]}..."
            f")>"
        )
