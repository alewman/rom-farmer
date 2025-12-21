"""Filter ROMs against DAT file stage."""

import hashlib
import os
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sqlalchemy.exc import IntegrityError

from ..dat_parser import DATFile, ROMMatcher
from ..metadata.database import MetadataDatabase
from ..metadata.transformation import ZipContentCache
from .base import Stage, StageContext, StageResult, StageStatus


class FilterDATStage(Stage):
    """Filter source ROM files against DAT file.

    For No-Intro:
    - Match ZIP files against Retool DAT entries
    - Copy matched ZIPs to work directory (no extraction!)
    - Track unmatched files for reporting

    For Redump:
    - Match ZIP files against Retool DAT entries
    - Mark for extraction in next stage
    """

    def __init__(self):
        """Initialize DAT filter stage."""
        super().__init__("Filter DAT")

    def should_skip(self, context: StageContext) -> bool:
        """Skip if no DAT file. If source files exist, pass them through."""
        # If we have source files but no DAT, skip this stage but allow pipeline to continue
        # This enables DAT-less workflows (e.g., using metadata database only)
        return context.dat_file is None

    def validate_context(self, context: StageContext) -> str | None:
        """Validate context."""
        if not context.source_dir.exists():
            return f"Source directory not found: {context.source_dir}"
        if not context.work_dir.exists():
            context.work_dir.mkdir(parents=True, exist_ok=True)
        return None

    def _populate_md5s(self, context: StageContext) -> None:
        """Populate MD5 hashes for source files.
        
        Loads MD5s from database first, then calculates for missing files.
        """
        self._log(context, "[cyan]Loading MD5 hashes...[/cyan]")
        
        # Try to load from database first
        db_md5s = self._load_md5s_from_database(context)
        if db_md5s:
            context.file_md5s.update(db_md5s)
            self._log(context, f"  Loaded {len(db_md5s):,} MD5s from database")
        
        # Calculate MD5s for files not in database
        missing_files = [f for f in context.source_files if f not in context.file_md5s]
        if missing_files:
            self._log(context, f"  Calculating MD5s for {len(missing_files):,} files...")
            calculated = self._calculate_md5s(missing_files, context)
            context.file_md5s.update(calculated)
            self._log(context, f"  Calculated {len(calculated):,} MD5s")
        
        self._log(context, f"  Total MD5s available: {len(context.file_md5s):,}")

    def _load_md5s_from_database(self, context: StageContext) -> Dict[Path, str]:
        """Load MD5 hashes from metadata database.
        
        Returns:
            Dictionary mapping file paths to MD5 hashes
        """
        try:
            # Try multiple possible database locations
            db_paths = [
                Path("metadata/database/romfarmer.db"),
                Path.cwd() / "metadata" / "database" / "romfarmer.db",
                Path(__file__).parent.parent.parent / "metadata" / "database" / "romfarmer.db",
            ]
            
            db_path = None
            for path in db_paths:
                if path.exists():
                    db_path = path
                    break
            
            if not db_path:
                self._log(context, "  [yellow]Warning: Database not found, skipping MD5 lookup[/yellow]")
                return {}
            
            from ..metadata.database import ScrapedGame
            
            db = MetadataDatabase(db_path)
            session = db.get_session()
            md5_map = {}
            
            try:
                # Query database for files in this system
                system = context.platform_name
                games = session.query(ScrapedGame).filter(
                    ScrapedGame.system == system,
                    ScrapedGame.md5.isnot(None)
                ).all()
                
                # Build mapping: filename -> MD5
                # The filename field contains paths like "./filename.zip", so strip "./"
                db_entries = {}
                for game in games:
                    if game.filename:
                        # Strip "./" prefix from ARRM paths
                        clean_filename = game.filename.lstrip("./")
                        db_entries[clean_filename] = game.md5
                
                # Match source files to database entries
                for file_path in context.source_files:
                    # Try exact name match
                    if file_path.name in db_entries:
                        md5_map[file_path] = db_entries[file_path.name]
                
                return md5_map
                
            finally:
                session.close()
            
        except Exception as e:
            self._log(context, f"  [yellow]Warning: Could not load MD5s from database: {e}[/yellow]")
            return {}

    def _calculate_md5s(self, files: List[Path], context: StageContext) -> Dict[Path, str]:
        """Calculate MD5 hashes for ROM files in parallel.
        
        For ZIP files, extracts the ROM and calculates its MD5.
        Uses ThreadPoolExecutor for parallel hash calculation.
        
        Returns:
            Dictionary mapping file paths to MD5 hashes
        """
        md5_map = {}
        
        # Use CPU count for workers, but cap at 8 to avoid overwhelming I/O
        num_workers = min(os.cpu_count() or 4, 8)
        
        def calc_hash(file_path: Path) -> tuple:
            """Calculate hash for a single file, return (path, hash) tuple."""
            try:
                md5_hash = self._calculate_file_md5(file_path)
                return (file_path, md5_hash)
            except Exception as e:
                return (file_path, None, str(e))
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {executor.submit(calc_hash, fp): fp for fp in files}
            
            for future in as_completed(futures):
                result = future.result()
                if len(result) == 2:
                    file_path, md5_hash = result
                    if md5_hash:
                        md5_map[file_path] = md5_hash
                else:
                    file_path, _, error = result
                    self._log(context, f"  [yellow]Warning: Failed to calculate MD5 for {file_path.name}: {error}[/yellow]")
        
        return md5_map

    def _calculate_file_md5(self, file_path: Path) -> Optional[str]:
        """Calculate MD5 hash of a file.
        
        For ZIP files, extracts and hashes the ROM content.
        For other files, hashes the file directly.
        """
        if file_path.suffix.lower() == '.zip':
            return self._calculate_md5_from_zip(file_path)
        else:
            # For non-ZIP files, hash directly
            md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    md5.update(chunk)
            return md5.hexdigest()

    def _calculate_md5_from_zip(self, zip_path: Path) -> Optional[str]:
        """Extract ROM from ZIP and calculate MD5.
        
        Uses a 2-tier caching strategy:
        1. Check ZipContentCache using CRC32 from ZIP header (instant)
        2. If cache miss, calculate MD5 and store in cache
        
        For CD-based systems (.cue/.bin pairs), prioritizes .cue files
        to match Redump DAT standards and ARRM/ScreenScraper expectations.
        
        Returns:
            MD5 hash of the ROM content, or None if extraction failed
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Get list of files, excluding directories
                files = [f for f in zf.namelist() if not f.endswith('/')]
                
                if not files:
                    return None
                
                # Select which file to hash (priority order)
                rom_file = self._select_rom_file(files, zf)
                if not rom_file:
                    return None
                
                # Get ZIP header info (instant - no decompression)
                info = zf.getinfo(rom_file)
                content_crc32 = f"{info.CRC:08x}"
                content_size = info.file_size
                zip_size = zip_path.stat().st_size
                
                # Try cache lookup first (instant!)
                cached_md5 = self._lookup_zip_content_cache(content_crc32, content_size)
                if cached_md5:
                    return cached_md5
                
                # Cache miss - calculate MD5 (slow)
                start_time = time.time()
                md5 = hashlib.md5()
                with zf.open(rom_file) as f:
                    for chunk in iter(lambda: f.read(1024 * 1024), b''):  # 1MB chunks
                        md5.update(chunk)
                
                content_md5 = md5.hexdigest()
                calc_time = time.time() - start_time
                
                # Store in cache for future lookups
                self._store_zip_content_cache(
                    zip_path=str(zip_path),
                    zip_size=zip_size,
                    content_filename=rom_file,
                    content_crc32=content_crc32,
                    content_size=content_size,
                    content_md5=content_md5,
                    calc_time=calc_time
                )
                
                return content_md5
                
        except Exception as e:
            return None
    
    def _select_rom_file(self, files: List[str], zf: zipfile.ZipFile) -> Optional[str]:
        """Select which file to hash from ZIP contents.
        
        Priority order:
        1. .cue (CD-based systems - Redump standard)
        2. .m3u (multi-disc playlists)
        3. Cartridge ROMs (.nes, .sfc, .gba, etc.)
        4. Disc images (.iso, .rvz, .chd)
        5. .bin (CD data - only if no .cue exists)
        """
        # Find .cue files first (CD-based systems)
        cue_files = [f for f in files if f.lower().endswith('.cue')]
        if cue_files:
            return cue_files[0]
        
        # Try m3u (multi-disc)
        m3u_files = [f for f in files if f.lower().endswith('.m3u')]
        if m3u_files:
            return m3u_files[0]
        
        # Try cartridge ROM extensions
        rom_extensions = {'.nes', '.sfc', '.smc', '.gb', '.gbc', '.gba', '.nds', '.3ds', '.n64', '.z64', '.v64'}
        for f in files:
            ext = Path(f).suffix.lower()
            if ext in rom_extensions:
                return f
        
        # Try disc images (including RVZ for GameCube/Wii)
        disc_extensions = {'.iso', '.rvz', '.chd'}
        for f in files:
            ext = Path(f).suffix.lower()
            if ext in disc_extensions:
                return f
        
        # Fallback: use largest file (likely .bin for CD systems)
        if len(files) == 1:
            return files[0]
        return max(files, key=lambda f: zf.getinfo(f).file_size)
    
    def _get_db_session(self):
        """Get a database session for cache operations."""
        try:
            db_paths = [
                Path("metadata/database/romfarmer.db"),
                Path.cwd() / "metadata" / "database" / "romfarmer.db",
                Path(__file__).parent.parent.parent / "metadata" / "database" / "romfarmer.db",
            ]
            
            for path in db_paths:
                if path.exists():
                    db = MetadataDatabase(path)
                    return db.get_session()
            return None
        except Exception:
            return None
    
    def _lookup_zip_content_cache(self, content_crc32: str, content_size: int) -> Optional[str]:
        """Lookup MD5 in ZipContentCache using CRC32 + size.
        
        This is the fast path - CRC32 is read from ZIP header instantly.
        """
        session = self._get_db_session()
        if not session:
            return None
        
        try:
            cached = session.query(ZipContentCache).filter(
                ZipContentCache.content_crc32 == content_crc32,
                ZipContentCache.content_size == content_size
            ).first()
            
            if cached:
                return cached.content_md5
            return None
        except Exception:
            return None
        finally:
            session.close()
    
    def _store_zip_content_cache(
        self,
        zip_path: str,
        zip_size: int,
        content_filename: str,
        content_crc32: str,
        content_size: int,
        content_md5: str,
        calc_time: float
    ) -> None:
        """Store calculated MD5 in ZipContentCache for future lookups."""
        session = self._get_db_session()
        if not session:
            return
        
        try:
            cache_entry = ZipContentCache(
                zip_path=zip_path,
                zip_size=zip_size,
                content_filename=content_filename,
                content_crc32=content_crc32,
                content_size=content_size,
                content_md5=content_md5,
                calculated_at=datetime.utcnow(),
                calculation_time_seconds=calc_time
            )
            session.add(cache_entry)
            session.commit()
        except IntegrityError:
            # Already exists (race condition with parallel workers)
            session.rollback()
        except Exception:
            session.rollback()
        finally:
            session.close()

    def execute(self, context: StageContext) -> StageResult:
        """Execute DAT filtering.

        Args:
            context: Stage context with DAT and source files

        Returns:
            StageResult with matched files
        """
        start_time = time.time()

        # Validate
        error = self.validate_context(context)
        if error:
            return StageResult(
                status=StageStatus.FAILED,
                message="Validation failed",
                error=ValueError(error),
            )

        if self.should_skip(context):
            return StageResult(
                status=StageStatus.SKIPPED,
                message="No DAT file or source files",
            )

        self._log(context, f"[cyan]Filtering against DAT: {context.dat_file.name}[/cyan]")
        self._log(context, f"  Games in DAT: {context.dat_file.get_game_count():,}")
        self._log(context, f"  Source files: {len(context.source_files):,}")

        # Populate MD5 hashes for better matching
        self._populate_md5s(context)

        # Create matcher
        matcher = ROMMatcher(context.dat_file)
        
        # Check if fuzzy name matching is enabled (for RVZ/NKit where hashes don't match)
        use_fuzzy_fallback = False
        if context.platform_config and context.platform_config.dat:
            match_method = getattr(context.platform_config.dat, 'match_method', 'hash')
            use_fuzzy_fallback = (match_method == 'fuzzy_name')
            if use_fuzzy_fallback:
                self._log(context, "  [cyan]Match method: fuzzy_name (hash → name fallback)[/cyan]")

        # Match files
        matched_files = []
        unmatched_files = []
        hash_matched = 0
        name_matched = 0
        hash_rejected = 0  # Files with hash but no match

        for file_path in context.source_files:
            result = None
            
            # PRIORITY 1: Hash-based matching (most accurate)
            if hasattr(context, 'file_md5s') and file_path in context.file_md5s:
                md5 = context.file_md5s[file_path]
                result = matcher.match_by_hash(file_path, md5=md5)
                if result.is_matched():
                    hash_matched += 1
                    matched_files.append(file_path)
                    continue
                
                # Hash available but no match
                # If fuzzy_name enabled, try filename matching as fallback
                if use_fuzzy_fallback:
                    result = matcher.match_file(file_path)
                    if result.is_matched():
                        name_matched += 1
                        matched_files.append(file_path)
                        continue
                
                # No match by either method
                hash_rejected += 1
                unmatched_files.append(file_path)
                continue
            
            # PRIORITY 2: Filename matching (fallback for files without hashes)
            # Only used when MD5 hash is not available
            result = matcher.match_file(file_path)
            if result.is_matched():
                name_matched += 1
                matched_files.append(file_path)
            else:
                unmatched_files.append(file_path)

        # Copy matched files to work directory (for No-Intro, these stay as ZIPs)
        copied_files = []
        for file_path in matched_files:
            dest_path = context.work_dir / file_path.name
            if not dest_path.exists():
                # For now, create symlink (copy in production)
                try:
                    dest_path.symlink_to(file_path)
                    copied_files.append(dest_path)
                except OSError:
                    # If symlink fails, try copy
                    import shutil
                    shutil.copy2(file_path, dest_path)
                    copied_files.append(dest_path)
            else:
                copied_files.append(dest_path)

        # Update context
        context.matched_files = copied_files
        context.filtered_files = copied_files

        # Statistics
        duration = time.time() - start_time
        match_rate = (len(matched_files) / len(context.source_files) * 100) if context.source_files else 0

        context.stats["dat_filter"] = {
            "source_files": len(context.source_files),
            "matched_files": len(matched_files),
            "unmatched_files": len(unmatched_files),
            "match_rate": match_rate,
            "copied_files": len(copied_files),
            "hash_matched": hash_matched,
            "name_matched": name_matched,
            "hash_rejected": hash_rejected,
        }

        self._log(
            context,
            f"  [green]Matched: {len(matched_files):,} ({match_rate:.1f}%)[/green]",
        )
        if hash_matched > 0:
            self._log(
                context,
                f"    [cyan]MD5 matched: {hash_matched:,}[/cyan]",
            )
        if hash_rejected > 0:
            self._log(
                context,
                f"    [yellow]MD5 rejected: {hash_rejected:,} (wrong version)[/yellow]",
            )
        if name_matched > 0:
            self._log(
                context,
                f"    [cyan]Name matched: {name_matched:,}[/cyan]",
            )
        self._log(
            context,
            f"  [yellow]Unmatched: {len(unmatched_files):,}[/yellow]",
        )

        return StageResult(
            status=StageStatus.SUCCESS,
            message=f"Filtered {len(matched_files):,} ROMs from {len(context.source_files):,} files",
            files_processed=len(context.source_files),
            files_matched=len(matched_files),
            files_skipped=len(unmatched_files),
            duration_seconds=duration,
            details={
                "matched": [f.name for f in matched_files[:10]],  # Sample
                "unmatched": [f.name for f in unmatched_files[:10]],  # Sample
                "match_rate": match_rate,
            },
        )
