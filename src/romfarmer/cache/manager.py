"""
ROM Cache Manager

Manages cached transformed ROM files to accelerate builds and save disk space.
"""

import hashlib
import json
import logging
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, Tuple

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import ROMCache
from .config import CacheLinkMode, CacheVerifyLevel, CacheConfig, CacheResult
from ..metadata.database import Base

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages ROM transformation cache.
    
    Usage:
        cache = CacheManager(config)
        
        # Check cache before building
        result = cache.get(source_md5, format='chd', params={'codec': 'lzma'})
        if result.hit:
            cache.link_to(result.cache_path, output_path)
        else:
            # Build the file...
            cache.store(source_md5, built_file, format='chd', params={'codec': 'lzma'})
    """
    
    def __init__(
        self,
        config: Optional[CacheConfig] = None,
        session: Optional[Session] = None,
        db_path: Optional[Path] = None,
    ):
        """Initialize cache manager.
        
        Args:
            config: Cache configuration (loads from env if None)
            session: SQLAlchemy session (creates new one if None)
            db_path: Database path (uses config.cache_dir/cache.db if None)
        """
        self.config = config or CacheConfig.from_env()
        
        # Ensure cache directory exists
        self.config.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up database
        if session:
            self.session = session
            self._owns_session = False
        else:
            db_path = db_path or (self.config.cache_dir / "cache.db")
            db_path.parent.mkdir(parents=True, exist_ok=True)
            engine = create_engine(f"sqlite:///{db_path}", echo=False)
            Base.metadata.create_all(engine)
            SessionLocal = sessionmaker(bind=engine)
            self.session = SessionLocal()
            self._owns_session = True
        
        # Cache for tool versions
        self._tool_versions: Dict[str, str] = {}
    
    def close(self):
        """Close database session if we own it."""
        if self._owns_session and self.session:
            self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Core Cache Operations
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def get_by_filename(
        self,
        source_filename: str,
        source_size: int,
        format: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> CacheResult:
        """Look up a cached file by source filename and size (fast pre-check).
        
        This allows cache lookup WITHOUT extracting archives, by reading
        the internal filename from ZIP headers.
        
        Args:
            source_filename: Name of source file (e.g., 'Game.bin')
            source_size: Size of source file in bytes
            format: Output format ('chd', 'rvz', '7z', etc.)
            params: Compression parameters
            
        Returns:
            CacheResult with hit=True if cached file found and valid
        """
        if not self.config.enabled:
            return CacheResult(hit=False, message="Cache disabled")
        
        params_hash = self._hash_params(params)
        
        # Look up by filename + size + format + params
        entry = self.session.query(ROMCache).filter_by(
            source_filename=source_filename,
            source_size=source_size,
            format=format,
            params_hash=params_hash,
        ).first()
        
        if not entry:
            return CacheResult(hit=False, message="Not in cache (by filename)")
        
        # Verify cached file exists
        cache_path = self.config.cache_dir / entry.cache_path
        if not self._verify_cached_file(entry, cache_path):
            logger.warning(f"Cache entry invalid, removing: {entry.cache_path}")
            self.session.delete(entry)
            self.session.commit()
            return CacheResult(hit=False, message="Cached file missing or invalid")
        
        # Update last used timestamp
        entry.last_used = datetime.utcnow()
        self.session.commit()
        
        return CacheResult(
            hit=True,
            cache_path=cache_path,
            entry=entry,
            message="Cache hit (by filename)",
        )
    
    def get_by_zip_identity(
        self,
        zip_crc32: str,
        zip_content_size: int,
        format: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> CacheResult:
        """Look up a cached file by ZIP identity (CRC32 + content size).
        
        This allows cache lookup WITHOUT extracting archives, by reading
        the CRC32 and uncompressed size from ZIP headers (instant).
        
        For torrentzipped archives (Myrient, etc.), CRC32 is stable and
        can uniquely identify contents.
        
        Args:
            zip_crc32: CRC32 from ZIP header, e.g., "2578c3f9"
            zip_content_size: Uncompressed size from ZIP header
            format: Output format ('chd', 'rvz', '7z', etc.)
            params: Compression parameters
            
        Returns:
            CacheResult with hit=True if cached file found and valid
        """
        if not self.config.enabled:
            return CacheResult(hit=False, message="Cache disabled")
        
        params_hash = self._hash_params(params)
        
        # Look up by ZIP identity + format + params
        entry = self.session.query(ROMCache).filter_by(
            source_zip_crc32=zip_crc32,
            source_zip_content_size=zip_content_size,
            format=format,
            params_hash=params_hash,
        ).first()
        
        if not entry:
            return CacheResult(hit=False, message="Not in cache (by ZIP identity)")
        
        # Verify cached file exists
        cache_path = self.config.cache_dir / entry.cache_path
        if not self._verify_cached_file(entry, cache_path):
            logger.warning(f"Cache entry invalid, removing: {entry.cache_path}")
            self.session.delete(entry)
            self.session.commit()
            return CacheResult(hit=False, message="Cached file missing or invalid")
        
        # Update last used timestamp
        entry.last_used = datetime.utcnow()
        self.session.commit()
        
        return CacheResult(
            hit=True,
            cache_path=cache_path,
            entry=entry,
            message="Cache hit (by ZIP identity)",
        )

    def get(
        self,
        source_md5: str,
        format: str,
        params: Optional[Dict[str, Any]] = None,
        tool_name: Optional[str] = None,
    ) -> CacheResult:
        """Look up a cached file.
        
        Args:
            source_md5: MD5 hash of source file
            format: Output format ('chd', 'rvz', '7z', etc.)
            params: Compression parameters
            tool_name: Tool used (for version checking)
            
        Returns:
            CacheResult with hit=True if cached file found and valid
        """
        if not self.config.enabled:
            return CacheResult(hit=False, message="Cache disabled")
        
        params_hash = self._hash_params(params)
        
        # Look up in database
        entry = self.session.query(ROMCache).filter_by(
            source_md5=source_md5,
            format=format,
            params_hash=params_hash,
        ).first()
        
        if not entry:
            return CacheResult(hit=False, message="Not in cache")
        
        # Check tool version if configured
        if self.config.check_tool_version and tool_name:
            current_version = self.get_tool_version(tool_name)
            if current_version and entry.tool_version != current_version:
                logger.debug(
                    f"Cache version mismatch: {entry.tool_version} vs {current_version}"
                )
                return CacheResult(
                    hit=False,
                    message=f"Tool version changed: {entry.tool_version} → {current_version}"
                )
        
        # Verify cached file exists
        cache_path = self.config.cache_dir / entry.cache_path
        if not self._verify_cached_file(entry, cache_path):
            # Clean up stale entry
            logger.warning(f"Cache entry invalid, removing: {entry.cache_path}")
            self.session.delete(entry)
            self.session.commit()
            return CacheResult(hit=False, message="Cached file missing or invalid")
        
        # Update last used timestamp
        entry.last_used = datetime.utcnow()
        self.session.commit()
        
        return CacheResult(
            hit=True,
            cache_path=cache_path,
            entry=entry,
            message="Cache hit",
        )
    
    def store(
        self,
        source_md5: str,
        source_file: Path,
        built_file: Path,
        format: str,
        params: Optional[Dict[str, Any]] = None,
        tool_name: Optional[str] = None,
        tool_version: Optional[str] = None,
        zip_crc32: Optional[str] = None,
        zip_content_size: Optional[int] = None,
    ) -> CacheResult:
        """Store a built file in the cache.
        
        Args:
            source_md5: MD5 hash of source file
            source_file: Path to source file (for metadata)
            built_file: Path to the built file to cache
            format: Output format ('chd', 'rvz', '7z', etc.)
            params: Compression parameters
            tool_name: Tool used for transformation
            tool_version: Tool version (auto-detected if None)
            zip_crc32: CRC32 from original ZIP header (for fast pre-check)
            zip_content_size: Uncompressed size from original ZIP header
            
        Returns:
            CacheResult with cached file path
        """
        if not self.config.enabled:
            return CacheResult(hit=False, message="Cache disabled")
        
        if not built_file.exists():
            return CacheResult(hit=False, message="Built file does not exist")
        
        params_hash = self._hash_params(params)
        
        # Determine cache path
        # Use nested directories for filesystem performance: ab/abc123_params.chd
        prefix = source_md5[:2]
        cache_subdir = self.config.cache_dir / format / prefix
        cache_subdir.mkdir(parents=True, exist_ok=True)
        
        cache_filename = f"{source_md5}_{params_hash}.{format}"
        cache_path = cache_subdir / cache_filename
        relative_path = f"{format}/{prefix}/{cache_filename}"
        
        # Get tool version
        if tool_name and not tool_version:
            tool_version = self.get_tool_version(tool_name)
        
        # Calculate final file hash and size
        final_md5 = self._calculate_md5(built_file)
        final_size = built_file.stat().st_size
        source_size = source_file.stat().st_size if source_file.exists() else None
        
        # Atomic write: copy to temp, then rename
        temp_path = cache_path.with_suffix('.tmp')
        try:
            shutil.copy2(built_file, temp_path)
            temp_path.rename(cache_path)
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            raise RuntimeError(f"Failed to store in cache: {e}") from e
        
        # Create or update database entry
        entry = self.session.query(ROMCache).filter_by(
            source_md5=source_md5,
            format=format,
            params_hash=params_hash,
        ).first()
        
        if entry:
            # Update existing entry
            entry.cache_path = relative_path
            entry.final_md5 = final_md5
            entry.final_size = final_size
            entry.tool_name = tool_name
            entry.tool_version = tool_version
            entry.compression_params = json.dumps(params) if params else None
            entry.source_filename = source_file.name
            entry.source_size = source_size
            entry.source_zip_crc32 = zip_crc32
            entry.source_zip_content_size = zip_content_size
            entry.last_used = datetime.utcnow()
        else:
            # Create new entry
            entry = ROMCache(
                source_md5=source_md5,
                format=format,
                params_hash=params_hash,
                cache_path=relative_path,
                final_md5=final_md5,
                final_size=final_size,
                tool_name=tool_name,
                tool_version=tool_version,
                compression_params=json.dumps(params) if params else None,
                source_filename=source_file.name,
                source_size=source_size,
                source_zip_crc32=zip_crc32,
                source_zip_content_size=zip_content_size,
            )
            self.session.add(entry)
        
        self.session.commit()
        
        logger.info(f"Cached: {source_file.name} → {relative_path}")
        
        return CacheResult(
            hit=True,
            cache_path=cache_path,
            entry=entry,
            message="Stored in cache",
        )
    
    def link_to(
        self,
        cache_path: Path,
        output_path: Path,
        mode: Optional[CacheLinkMode] = None,
    ) -> bool:
        """Link or copy cached file to output location.
        
        Args:
            cache_path: Path to cached file
            output_path: Desired output path
            mode: Link mode (uses config default if None)
            
        Returns:
            True if successful
        """
        mode = mode or self.config.link_mode
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Remove existing file if present
        if output_path.exists() or output_path.is_symlink():
            output_path.unlink()
        
        try:
            if mode == CacheLinkMode.HARDLINK:
                try:
                    os.link(cache_path, output_path)
                    logger.debug(f"Hardlinked: {output_path.name}")
                    return True
                except OSError:
                    # Fall back to copy if hardlink fails (cross-filesystem)
                    logger.debug("Hardlink failed, falling back to copy")
                    shutil.copy2(cache_path, output_path)
                    return True
            
            elif mode == CacheLinkMode.SYMLINK:
                os.symlink(cache_path.resolve(), output_path)
                logger.debug(f"Symlinked: {output_path.name}")
                return True
            
            else:  # COPY
                shutil.copy2(cache_path, output_path)
                logger.debug(f"Copied: {output_path.name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to link {cache_path} to {output_path}: {e}")
            return False
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Tool Version Detection
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def get_tool_version(self, tool_name: str) -> Optional[str]:
        """Get version string for a tool.
        
        Args:
            tool_name: Tool name ('chdman', '7z', 'dolphin-tool', etc.)
            
        Returns:
            Version string or None if not detectable
        """
        if tool_name in self._tool_versions:
            return self._tool_versions[tool_name]
        
        version = None
        
        try:
            if tool_name == "chdman":
                result = subprocess.run(
                    ["chdman"], capture_output=True, text=True, timeout=5
                )
                # Parse: "chdman - MAME Compressed Hunks of Data (CHD) manager 0.262"
                output = result.stdout + result.stderr
                import re
                match = re.search(r'(\d+\.\d+)', output)
                if match:
                    version = f"mame{match.group(1).replace('.', '')}"
            
            elif tool_name == "7z":
                result = subprocess.run(
                    ["7z"], capture_output=True, text=True, timeout=5
                )
                import re
                match = re.search(r'(\d+\.\d+)', result.stdout)
                if match:
                    version = match.group(1)
            
            elif tool_name == "dolphin-tool":
                result = subprocess.run(
                    ["dolphin-tool", "--version"], capture_output=True, text=True, timeout=5
                )
                version = result.stdout.strip()
            
            # Add more tools as needed
            
        except Exception as e:
            logger.debug(f"Could not detect {tool_name} version: {e}")
        
        self._tool_versions[tool_name] = version
        return version
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Cache Statistics and Maintenance
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        total_entries = self.session.query(ROMCache).count()
        
        # Group by format
        from sqlalchemy import func
        format_stats = self.session.query(
            ROMCache.format,
            func.count(ROMCache.id),
            func.sum(ROMCache.final_size),
        ).group_by(ROMCache.format).all()
        
        formats = {}
        total_size = 0
        chd_count = 0
        rvz_count = 0
        z7_count = 0
        
        for fmt, count, size in format_stats:
            formats[fmt] = {"count": count, "size": size or 0}
            total_size += size or 0
            if fmt == 'chd':
                chd_count = count
            elif fmt == 'rvz':
                rvz_count = count
            elif fmt == '7z':
                z7_count = count
        
        # Get tool versions used
        tool_versions = {}
        tool_stats = self.session.query(
            ROMCache.tool_name,
            ROMCache.tool_version,
        ).distinct().all()
        for tool, version in tool_stats:
            if tool and version:
                tool_versions[tool] = version
        
        return {
            "enabled": self.config.enabled,
            "cache_dir": str(self.config.cache_dir),
            "link_mode": self.config.link_mode.value,
            "verify_level": self.config.verify_level.value,
            "total_entries": total_entries,
            "total_size": total_size,
            "total_size_bytes": total_size,
            "total_size_human": self._human_size(total_size),
            "formats": formats,
            "chd_count": chd_count,
            "rvz_count": rvz_count,
            "7z_count": z7_count,
            "tool_versions": tool_versions,
        }
    
    def verify_all(self) -> Dict[str, list]:
        """Verify all cached files exist.
        
        Returns:
            Dict with 'valid', 'invalid', and 'missing' lists
        """
        valid = []
        invalid = []
        missing = []
        
        for entry in self.session.query(ROMCache).all():
            cache_path = self.config.cache_dir / entry.cache_path
            if not cache_path.exists():
                missing.append(entry.cache_key)
            elif not self._verify_cached_file(entry, cache_path):
                invalid.append(entry.cache_key)
            else:
                valid.append(entry.cache_key)
        
        return {"valid": valid, "invalid": invalid, "missing": missing}
    
    def get_old_entries(self, days: int = 90) -> list:
        """Get cache entries older than specified days.
        
        Args:
            days: Age threshold in days
            
        Returns:
            List of old ROMCache entries
        """
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        return self.session.query(ROMCache).filter(
            ROMCache.last_used < cutoff
        ).all()
    
    def prune(self, days: int = 90) -> int:
        """Remove cache entries older than specified days.
        
        Args:
            days: Age threshold in days
            
        Returns:
            Number of entries removed
        """
        entries = self.get_old_entries(days)
        count = len(entries)
        
        for entry in entries:
            cache_path = self.config.cache_dir / entry.cache_path
            if cache_path.exists():
                cache_path.unlink()
            self.session.delete(entry)
        
        self.session.commit()
        return count
    
    def clear(self, format: Optional[str] = None) -> int:
        """Clear cache entries.
        
        Args:
            format: Only clear entries of this format (all if None)
            
        Returns:
            Number of entries removed
        """
        query = self.session.query(ROMCache)
        if format:
            query = query.filter_by(format=format)
        
        entries = query.all()
        count = len(entries)
        
        for entry in entries:
            # Delete file
            cache_path = self.config.cache_dir / entry.cache_path
            if cache_path.exists():
                cache_path.unlink()
            # Delete DB entry
            self.session.delete(entry)
        
        self.session.commit()
        
        return count
    
    def remove_orphans(self) -> int:
        """Remove DB entries for missing files.
        
        Returns:
            Number of orphan entries removed
        """
        removed = 0
        for entry in self.session.query(ROMCache).all():
            cache_path = self.config.cache_dir / entry.cache_path
            if not cache_path.exists():
                self.session.delete(entry)
                removed += 1
        
        self.session.commit()
        return removed
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Private Helpers
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _hash_params(self, params: Optional[Dict[str, Any]]) -> str:
        """Create a stable hash of compression parameters."""
        if not params:
            return "default"
        
        # Sort keys for stable ordering
        sorted_json = json.dumps(params, sort_keys=True)
        return hashlib.md5(sorted_json.encode()).hexdigest()[:16]
    
    def _verify_cached_file(self, entry: ROMCache, cache_path: Path) -> bool:
        """Verify a cached file based on verify level."""
        if self.config.verify_level == CacheVerifyLevel.NONE:
            return True
        
        if not cache_path.exists():
            return False
        
        if self.config.verify_level == CacheVerifyLevel.EXISTS:
            return True
        
        if self.config.verify_level == CacheVerifyLevel.SIZE:
            return cache_path.stat().st_size == entry.final_size
        
        if self.config.verify_level == CacheVerifyLevel.MD5:
            return self._calculate_md5(cache_path) == entry.final_md5
        
        return True
    
    def _calculate_md5(self, file_path: Path) -> str:
        """Calculate MD5 hash of a file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _human_size(self, size_bytes: int) -> str:
        """Convert bytes to human readable string."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if abs(size_bytes) < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
