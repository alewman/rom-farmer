"""
ROM Cache Database Models

SQLAlchemy model for tracking cached ROM transformations.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from ..metadata.database import Base


class ROMCache(Base):
    """
    Cached ROM transformation entry.
    
    Stores transformed ROM files (CHD, RVZ, 7z, etc.) keyed by source hash
    and transformation parameters. This enables:
    
    1. Build acceleration: Skip re-processing files we've already built
    2. Disk savings: Hardlink outputs to cached files instead of copying
    3. Cross-build sharing: Same CHD works for .eng and .all builds
    
    Cache Key = (source_md5, format, params_hash)
    
    Example:
        source_md5='abc123', format='chd', params_hash='lzma_default'
        → cache/chd/ab/abc123_lzma_default.chd
    """
    
    __tablename__ = "rom_cache"
    
    id = Column(Integer, primary_key=True)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Cache Key (unique identifier for this cached file)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    source_md5 = Column(String(32), nullable=False, index=True)
    format = Column(String(16), nullable=False)  # 'chd', 'rvz', '7z', 'cso', 'xiso'
    params_hash = Column(String(32), nullable=False)  # Hash of compression params
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Compression/Transformation Details
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    compression_params = Column(Text)  # JSON: {"codec": "lzma", "level": 9}
    tool_name = Column(String(64))  # 'chdman', '7z', 'dolphin-tool'
    tool_version = Column(String(64))  # 'mame0262', '24.09'
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Cached File Info
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    cache_path = Column(String(512), nullable=False)  # Relative: 'chd/ab/abc123_lzma.chd'
    final_md5 = Column(String(32))  # For integrity verification
    final_size = Column(BigInteger)  # File size in bytes
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Source Info (for debugging/display)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    source_filename = Column(String(512))  # Original filename for display
    source_size = Column(BigInteger)  # Original file size
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Timestamps
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    created_date = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Constraints and Indexes
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    __table_args__ = (
        # Unique cache key
        UniqueConstraint('source_md5', 'format', 'params_hash', name='uq_cache_key'),
        # Index for cache lookups
        Index('ix_cache_lookup', 'source_md5', 'format', 'params_hash'),
        # Index for finding unused entries (for pruning)
        Index('ix_cache_last_used', 'last_used'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<ROMCache(source_md5={self.source_md5[:8]}..., "
            f"format={self.format}, path={self.cache_path})>"
        )
    
    @property
    def cache_key(self) -> str:
        """Return the unique cache key."""
        return f"{self.source_md5}_{self.format}_{self.params_hash}"
