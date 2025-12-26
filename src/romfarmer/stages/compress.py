"""Compress disc images to CHD format."""

import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from sqlalchemy.orm import Session

from .base import Stage, StageContext, StageResult, StageStatus
from .disc_models import CueSheet
from ..metadata.transformation_recorder import TransformationRecorder
from ..cache import CacheManager, CacheConfig


class CompressCHDStage(Stage):
    """Compress disc images (CUE/BIN, ISO) to CHD format.
    
    Uses chdman to convert disc images to compressed CHD format.
    Supports both CD images (createcd) and DVD/PS2 images (createdvd).
    Tracks transformations for hash management.
    
    Supports ROM caching for build acceleration - if a CHD for a given
    source file already exists in cache, it will be linked instead of rebuilt.
    """
    
    def __init__(
        self, 
        chdman_path: Optional[Path] = None, 
        db_session: Optional[Session] = None,
        cache_manager: Optional[CacheManager] = None,
    ):
        """Initialize compression stage.
        
        Args:
            chdman_path: Path to chdman binary (auto-detected if None)
            db_session: Database session for transformation recording (optional)
            cache_manager: ROM cache manager (optional, enables caching)
        """
        super().__init__("Compress to CHD")
        self.chdman_path = chdman_path or self._find_chdman()
        self.db_session = db_session
        self.transformation_recorder = TransformationRecorder(self.db_session) if self.db_session else None
        self.cache_manager = cache_manager
        
        # Stats for cache hits/misses
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Cache parameters for CHD compression
        self._cache_params = {
            'format': 'chd',
            'compression': 'lzma',
        }
    
    def _calculate_source_md5(self, disc_path: Path) -> Optional[str]:
        """Calculate MD5 hash of source disc for cache lookup.
        
        For CUE files, hashes the largest BIN file (ARRM behavior).
        For ISO files, hashes the ISO directly.
        
        Args:
            disc_path: Path to CUE or ISO file
            
        Returns:
            MD5 hex string or None if failed
        """
        import hashlib
        import re
        
        try:
            if disc_path.suffix.lower() == '.cue':
                # Parse CUE to find BIN files
                bin_files: List[Path] = []
                with open(disc_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if line.strip().upper().startswith('FILE'):
                            match = re.search(r'FILE\s+"([^"]+)"', line, re.IGNORECASE)
                            if match:
                                bin_name = match.group(1)
                                bin_path = disc_path.parent / bin_name
                                if bin_path.exists():
                                    bin_files.append(bin_path)
                
                if not bin_files:
                    return None
                
                # Hash the largest BIN file (ARRM behavior)
                largest_bin = max(bin_files, key=lambda p: p.stat().st_size)
                target_file = largest_bin
            else:
                # ISO - hash the file directly
                target_file = disc_path
            
            # Calculate MD5
            hash_md5 = hashlib.md5()
            with open(target_file, 'rb') as f:
                for chunk in iter(lambda: f.read(8192 * 1024), b''):  # 8MB chunks
                    hash_md5.update(chunk)
            
            return hash_md5.hexdigest()
            
        except Exception:
            return None
    
    def _find_chdman(self) -> Optional[Path]:
        """Find chdman binary.
        
        Returns:
            Path to chdman or None if not found
        """
        # Check in tools directory
        tools_chdman = Path(__file__).parent.parent.parent.parent / "tools" / "bin" / "chdman"
        if tools_chdman.exists():
            return tools_chdman
        
        # Check system PATH
        system_chdman = shutil.which("chdman")
        if system_chdman:
            return Path(system_chdman)
        
        return None
    
    def should_skip(self, context: StageContext) -> bool:
        """Skip if no files to compress or no chdman.
        
        Args:
            context: Stage context
            
        Returns:
            True if should skip
        """
        # Check if there are files to compress
        has_extracted = bool(context.extracted_files)
        
        # Check if there are pre-cached outputs (from CachePreCheckStage)
        has_cached = hasattr(context, 'cached_outputs') and bool(context.cached_outputs)
        
        # Skip only if no files AND no cached outputs
        if not has_extracted and not has_cached:
            return True
        
        # If we have cached outputs but nothing to compress, we still need to run
        # to populate compressed_files with the cached outputs
        if not has_extracted and has_cached:
            return False
        
        if not self.chdman_path:
            self._log_error(context, "chdman not found, cannot compress discs")
            return True
        
        return False
    
    def validate_context(self, context: StageContext) -> bool:
        """Validate context has required data.
        
        Args:
            context: Stage context
            
        Returns:
            True if valid
        """
        if not self.chdman_path or not self.chdman_path.exists():
            self._log_error(context, f"chdman not found at {self.chdman_path}")
            return False
        
        return True
    
    def execute(self, context: StageContext) -> StageResult:
        """Compress disc images to CHD.
        
        Args:
            context: Stage context
            
        Returns:
            Stage result
        """
        if self.should_skip(context):
            return StageResult(
                status=StageStatus.SKIPPED,
                message="No files to compress or chdman not found",
            )
        
        compressed_files: List[Path] = []
        
        # Include any files already cached by CachePreCheckStage
        if hasattr(context, 'cached_outputs') and context.cached_outputs:
            cached_count = len(context.cached_outputs)
            compressed_files.extend(context.cached_outputs)
            self._cache_hits += cached_count
            self._log_info(context, f"  Including {cached_count} pre-cached files (skipped extraction)")
        
        # If all files were pre-cached, we're done - no compression needed
        if not context.extracted_files:
            context.compressed_files = compressed_files
            return StageResult(
                status=StageStatus.SUCCESS,
                message=f"All {len(compressed_files)} files from cache (extraction skipped)",
                files_processed=len(compressed_files),
                files_matched=self._cache_hits,
            )
        
        # Need chdman for actual compression
        if not self.validate_context(context):
            return StageResult(
                status=StageStatus.FAILED,
                message="chdman validation failed",
                error="chdman not found or not executable",
            )
        
        self._log_info(context, f"Compressing {len(context.extracted_files)} discs to CHD...")
        
        failed = 0
        
        for disc_path in context.extracted_files:
            try:
                # Determine output CHD path
                chd_path = disc_path.with_suffix('.chd')
                source_md5: Optional[str] = None
                cache_hit = False
                
                # Check cache if enabled
                if self.cache_manager:
                    source_md5 = self._calculate_source_md5(disc_path)
                    if source_md5:
                        cache_result = self.cache_manager.get(
                            source_md5=source_md5,
                            format='chd',
                            params=self._cache_params,
                        )
                        if cache_result.hit:
                            # Cache hit - link instead of compressing
                            try:
                                linked_path = self.cache_manager.link_to(
                                    cache_result.cache_path,
                                    chd_path,
                                )
                                if linked_path and linked_path.exists():
                                    self._cache_hits += 1
                                    cache_hit = True
                                    self._log_info(context, f"  ✓ Cache hit: {disc_path.name} → linked from cache")
                                    
                                    # Clean up source files since we're using cached CHD
                                    if disc_path.suffix.lower() == '.cue':
                                        self._cleanup_source_files(context, disc_path)
                                    else:
                                        if disc_path.exists():
                                            disc_path.unlink()
                                    
                                    compressed_files.append(linked_path)
                                    continue  # Skip to next disc
                            except Exception as link_err:
                                self._log_warning(context, f"  Cache link failed: {link_err}, will rebuild")
                
                # Cache miss or no cache - compress normally
                if disc_path.suffix.lower() == '.cue':
                    chd_path = self._compress_cue_to_chd(context, disc_path)
                elif disc_path.suffix.lower() == '.iso':
                    chd_path = self._compress_iso_to_chd(context, disc_path)
                else:
                    self._log_warning(context, f"Unknown disc format: {disc_path.suffix}")
                    failed += 1
                    continue
                
                if chd_path and chd_path.exists():
                    compressed_files.append(chd_path)
                    
                    # Store in cache if enabled
                    if self.cache_manager and source_md5:
                        try:
                            # Get ZIP identity for fast pre-check on future builds
                            zip_crc32 = None
                            zip_content_size = None
                            if hasattr(context, 'zip_identity_map') and disc_path in context.zip_identity_map:
                                zip_crc32, zip_content_size = context.zip_identity_map[disc_path]
                            
                            self.cache_manager.store(
                                source_md5=source_md5,
                                source_file=disc_path,
                                built_file=chd_path,
                                format='chd',
                                params=self._cache_params,
                                tool_name='chdman',
                                zip_crc32=zip_crc32,
                                zip_content_size=zip_content_size,
                            )
                            self._cache_misses += 1
                            self._log_info(context, f"  ✓ Stored in cache: {disc_path.name}")
                        except Exception as cache_err:
                            self._log_warning(context, f"  Cache store failed: {cache_err}")
                    
                    # Record transformation if recorder is available
                    if self.transformation_recorder:
                        try:
                            self._record_transformation(context, disc_path, chd_path)
                        except Exception as e:
                            self._log_warning(context, f"Failed to record transformation: {e}")
                    
                    # Clean up source files after successful compression and recording
                    if disc_path.suffix.lower() == '.cue':
                        self._cleanup_source_files(context, disc_path)
                    else:
                        # For ISO, just delete the ISO file
                        if disc_path.exists():
                            disc_path.unlink()
                            self._log_info(context, f"  Cleaned up: {disc_path.name}")
                else:
                    self._log_error(context, f"Failed to create CHD for {disc_path.name}")
                    failed += 1
            except Exception as e:
                self._log_error(context, f"Failed to compress {disc_path.name}: {e}")
                failed += 1
        
        # Update context
        context.compressed_files = compressed_files
        
        # Build message with cache stats
        if self.cache_manager:
            message = f"Compressed {len(compressed_files)} discs to CHD (cache: {self._cache_hits} hits, {self._cache_misses} misses)"
        else:
            message = f"Compressed {len(compressed_files)} discs to CHD"
        
        return StageResult(
            status=StageStatus.SUCCESS,
            message=message,
            files_processed=len(context.extracted_files),
            files_matched=len(compressed_files),
            files_failed=failed,
            details={
                "compressed": [str(p) for p in compressed_files],
                "format": "chd",
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
            }
        )
    
    def _compress_cue_to_chd(self, context, cue_path: Path) -> Optional[Path]:
        """Compress CUE/BIN to CHD using chdman createcd.
        
        Args:
            cue_path: Path to CUE file
            
        Returns:
            Path to created CHD or None if failed
        """
        # Output CHD has same name as CUE
        chd_path = cue_path.with_suffix('.chd')
        
        try:
            # Run chdman createcd (for CD images)
            cmd = [
                str(self.chdman_path),
                'createcd',
                '-i', str(cue_path),
                '-o', str(chd_path),
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )
            
            if result.returncode != 0:
                self._log_error(context, f"chdman failed for {cue_path.name}:")
                self._log_error(context, result.stderr)
                return None
            
            return chd_path
            
        except Exception as e:
            self._log_error(context, f"Exception running chdman: {e}")
            return None
    
    def _compress_iso_to_chd(self, context, iso_path: Path) -> Optional[Path]:
        """Compress ISO to CHD using chdman createdvd.
        
        Args:
            iso_path: Path to ISO file
            
        Returns:
            Path to created CHD or None if failed
        """
        # Output CHD has same name as ISO
        chd_path = iso_path.with_suffix('.chd')
        
        try:
            # Run chdman createdvd (for DVD/PS2 images)
            cmd = [
                str(self.chdman_path),
                'createdvd',
                '-i', str(iso_path),
                '-o', str(chd_path),
                '-c', 'lzma',  # Use LZMA compression for best ratio
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )
            
            if result.returncode != 0:
                self._log_error(context, f"chdman failed for {iso_path.name}:")
                self._log_error(context, result.stderr)
                return None
            
            return chd_path
            
        except Exception as e:
            self._log_error(context, f"Exception running chdman: {e}")
            return None
    
    def _get_bin_total_size(self, cue_path: Path) -> int:
        """Calculate total size of BIN files referenced by CUE.
        
        Args:
            cue_path: Path to CUE file
            
        Returns:
            Total size of all BIN files in bytes
        """
        total_size = 0
        cue_dir = cue_path.parent
        import re
        
        try:
            with open(cue_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if line.strip().upper().startswith('FILE'):
                        # Parse: FILE "filename.bin" BINARY
                        match = re.search(r'FILE\s+"([^"]+)"', line, re.IGNORECASE)
                        if match:
                            bin_name = match.group(1)
                            bin_path = cue_dir / bin_name
                            if bin_path.exists():
                                total_size += bin_path.stat().st_size
        except Exception as e:
            # If we can't parse CUE, return CUE file size as fallback
            total_size = cue_path.stat().st_size
        
        return total_size
    
    def _get_primary_bin_file(self, cue_path: Path) -> Optional[Path]:
        """Get the primary (largest) BIN file referenced by CUE.
        
        For SINGLE-TRACK discs (1 BIN), ARRM hashes the BIN file.
        For MULTI-TRACK discs (2+ BINs), ARRM hashes the CUE file.
        
        This function returns the primary BIN file for single-track discs,
        or None for multi-track discs (caller should hash CUE instead).
        
        Args:
            cue_path: Path to CUE file
            
        Returns:
            Path to BIN file for single-track, None for multi-track
        """
        cue_dir = cue_path.parent
        import re
        
        bin_files = []
        try:
            with open(cue_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if line.strip().upper().startswith('FILE'):
                        # Parse: FILE "filename.bin" BINARY
                        match = re.search(r'FILE\s+"([^"]+)"', line, re.IGNORECASE)
                        if match:
                            bin_name = match.group(1)
                            bin_path = cue_dir / bin_name
                            if bin_path.exists():
                                bin_files.append(bin_path)
        except Exception:
            pass
        
        # Single-track: return the BIN file (ARRM hashes BIN)
        if len(bin_files) == 1:
            return bin_files[0]
        
        # Multi-track: return None (caller should hash CUE instead)
        # ARRM hashes the CUE file for multi-track discs
        return None
    
    def _get_source_file_for_hash(self, cue_path: Path) -> Path:
        """Get the correct file to hash for ARRM compatibility.
        
        ARRM/ScreenScraper hashing rules:
        - Single-track (1 BIN): Hash the BIN file
        - Multi-track (2+ BINs): Hash the CUE file
        
        Args:
            cue_path: Path to CUE file
            
        Returns:
            Path to file that should be hashed
        """
        primary_bin = self._get_primary_bin_file(cue_path)
        if primary_bin:
            return primary_bin  # Single-track: hash BIN
        return cue_path  # Multi-track: hash CUE
    
    def _record_transformation(self, context, cue_path: Path, chd_path: Path):
        """Record transformation from CUE to CHD.
        
        Args:
            cue_path: Path to source CUE file
            chd_path: Path to final CHD file
        """
        from ..metadata.hash_capture import SmartHashCapture, SourceHashInfo
        from ..metadata.transformation import ROMTransformation
        from ..metadata.database import ScrapedGame
        from datetime import datetime
        from sqlalchemy.exc import IntegrityError
        
        try:
            # Initialize hash capture
            hash_capture = SmartHashCapture(dat_manager=None, session=self.db_session)
            
            # Calculate total BIN file size (what actually gets compressed)
            bin_total_size = self._get_bin_total_size(cue_path)
            
            # Get the correct file to hash for ARRM compatibility
            # Single-track: hash BIN, Multi-track: hash CUE
            source_file_path = self._get_source_file_for_hash(cue_path)
            is_multitrack = (source_file_path == cue_path)
            
            self._log_info(context, f"Recording transformation for {source_file_path.name} ({'CUE-multitrack' if is_multitrack else 'BIN-singletrack'})...")
            
            source_hashes = hash_capture.get_source_hashes(source_file_path, system=None)
            # Override size with total BIN size for accurate compression ratio
            source_hashes = SourceHashInfo(
                md5=source_hashes.md5,
                sha1=source_hashes.sha1,
                sha256=source_hashes.sha256,
                crc32=source_hashes.crc32,
                size=bin_total_size,  # Use total BIN size
                from_dat=source_hashes.from_dat,
                dat_name=source_hashes.dat_name,
                from_cache=source_hashes.from_cache,
            )
            
            # Hash final CHD file (no DAT lookup, just calculate)
            final_hashes = hash_capture.get_source_hashes(chd_path, system=None)
            
            # Check if transformation already exists
            existing = self.db_session.query(ROMTransformation).filter_by(
                source_md5=source_hashes.md5,
                final_md5=final_hashes.md5,
            ).first()
            
            if existing:
                # Update existing record
                existing.transformation_date = datetime.utcnow()
                existing.transformation_tool = 'chdman'
                existing.transformation_version = 'mame'
                existing.transformation_params = '{"format": "chd", "compression": "lzma"}'
                self.db_session.commit()
                self._log_info(context, f"  ✓ Updated existing: {source_hashes.md5[:8]}... → {final_hashes.md5[:8]}...")
                return
            
            # Try to find game in database by source MD5
            self._log_info(context, f"  Looking up game by MD5: {source_hashes.md5[:16]}...")
            
            try:
                game = self.db_session.query(ScrapedGame).filter_by(
                    md5=source_hashes.md5
                ).first()
                
                if game:
                    self._log_info(context, f"    ✓ Found game: {game.name} (system: {game.system}, id: {game.id})")
                else:
                    self._log_info(context, f"    ⚠ No game found with this MD5")
                    # Try searching by filename as fallback
                    game_name = cue_path.stem
                    self._log_info(context, f"    Trying fallback search by name: {game_name}")
                    game = self.db_session.query(ScrapedGame).filter(
                        ScrapedGame.system == 'saturn',  # TODO: make this dynamic based on platform
                        ScrapedGame.name.like(f'%{game_name}%')
                    ).first()
                    if game:
                        self._log_info(context, f"    ✓ Found via fallback: {game.name} (MD5 in DB: {game.md5[:16]}...)")
                    else:
                        self._log_info(context, f"    ✗ Fallback also failed - transformation will have no game link")
            except Exception as lookup_error:
                self._log_warning(context, f"    ✗ Exception during game lookup: {lookup_error}")
                game = None
            
            # Create transformation record
            transformation = ROMTransformation(
                # Source file info
                source_md5=source_hashes.md5,
                source_sha1=source_hashes.sha1,
                source_crc32=source_hashes.crc32,
                source_file_size=source_hashes.size,  # ADD FILE SIZE!
                source_file_name=source_file_path.name,
                source_format=source_file_path.suffix.lstrip('.').lower(),
                
                # Transformation metadata
                transformation_tool='chdman',
                transformation_version='mame',  # Could parse version from chdman output
                transformation_params='{"format": "chd", "compression": "lzma"}',
                transformation_date=datetime.utcnow(),
                
                # Final file info
                final_md5=final_hashes.md5,
                final_sha1=final_hashes.sha1,
                final_crc32=final_hashes.crc32,
                final_file_size=final_hashes.size,  # ADD FILE SIZE!
                final_file_name=chd_path.name,
                final_format='chd',
                
                # Link to game if found
                game_id=game.id if game else None,
            )
            
            self.db_session.add(transformation)
            
            try:
                self.db_session.commit()
                self._log_info(context, f"  ✓ Recorded: {source_hashes.md5[:8]}... → {final_hashes.md5[:8]}...")
            except IntegrityError:
                # Duplicate constraint violation - rollback and continue
                self.db_session.rollback()
                self._log_info(context, f"  ⚠ Transformation already exists (skipped)")
            
        except Exception as e:
            # Rollback on any error to prevent session poisoning
            self.db_session.rollback()
            self._log_warning(context, f"Failed to record transformation: {e}")
            # Don't fail the whole process if transformation recording fails
    
    def _cleanup_source_files(self, context, cue_path: Path):
        """Clean up CUE and BIN files after successful compression.
        
        Args:
            cue_path: Path to CUE file
        """
        try:
            # Parse CUE to find BIN files
            bin_files: List[Path] = []
            
            with open(cue_path, 'r', encoding='utf-8', errors='ignore') as f:
                import re
                for line in f:
                    if line.strip().upper().startswith('FILE'):
                        match = re.search(r'FILE\s+"([^"]+)"', line, re.IGNORECASE)
                        if match:
                            bin_name = match.group(1)
                            bin_path = cue_path.parent / bin_name
                            bin_files.append(bin_path)
            
            # Delete CUE file
            if cue_path.exists():
                cue_path.unlink()
                self._log_info(context, f"  Cleaned up: {cue_path.name}")
            
            # Delete BIN files
            for bin_path in bin_files:
                if bin_path.exists():
                    bin_path.unlink()
                    
        except Exception as e:
            self._log_warning(context, f"Failed to cleanup source files: {e}")
