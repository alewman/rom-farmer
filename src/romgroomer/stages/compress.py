"""Compress disc images to CHD format."""

import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from sqlalchemy.orm import Session

from .base import Stage, StageContext, StageResult, StageStatus
from .disc_models import CueSheet
from ..metadata.transformation_recorder import TransformationRecorder


class CompressCHDStage(Stage):
    """Compress disc images (CUE/BIN, ISO) to CHD format.
    
    Uses chdman to convert disc images to compressed CHD format.
    Supports both CD images (createcd) and DVD/PS2 images (createdvd).
    Tracks transformations for hash management.
    """
    
    def __init__(self, chdman_path: Optional[Path] = None, db_session: Optional[Session] = None):
        """Initialize compression stage.
        
        Args:
            chdman_path: Path to chdman binary (auto-detected if None)
            db_session: Database session for transformation recording (optional)
        """
        super().__init__("Compress to CHD")
        self.chdman_path = chdman_path or self._find_chdman()
        self.db_session = db_session
        self.transformation_recorder = TransformationRecorder(self.db_session) if self.db_session else None
    
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
        if not context.extracted_files:
            return True
        
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
        
        if not self.validate_context(context):
            return StageResult(
                status=StageStatus.FAILED,
                message="chdman validation failed",
                error="chdman not found or not executable",
            )
        
        self._log_info(context, f"Compressing {len(context.extracted_files)} discs to CHD...")
        
        compressed_files: List[Path] = []
        failed = 0
        
        for disc_path in context.extracted_files:
            try:
                # Determine disc type and compress accordingly
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
        
        try:
            with open(cue_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if line.strip().startswith('FILE'):
                        # Parse: FILE "filename.bin" BINARY
                        parts = line.strip().split('"')
                        if len(parts) >= 2:
                            bin_name = parts[1]
                            bin_path = cue_dir / bin_name
                            if bin_path.exists():
                                total_size += bin_path.stat().st_size
        except Exception as e:
            # If we can't parse CUE, return CUE file size as fallback
            total_size = cue_path.stat().st_size
        
        return total_size
    
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
            self._log_info(context, f"Recording transformation for {cue_path.name}...")
            
            # Initialize hash capture
            hash_capture = SmartHashCapture(dat_manager=None, session=self.db_session)
            
            # Calculate total BIN file size (what actually gets compressed)
            bin_total_size = self._get_bin_total_size(cue_path)
            
            # Hash source CUE file (no DAT lookup for CUE files, use cache if available)
            source_hashes = hash_capture.get_source_hashes(cue_path, system=None)
            # Override size with actual BIN size for accurate compression ratio
            source_hashes = SourceHashInfo(
                md5=source_hashes.md5,
                sha1=source_hashes.sha1,
                sha256=source_hashes.sha256,
                crc32=source_hashes.crc32,
                size=bin_total_size,  # Use BIN size, not CUE size!
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
                source_file_name=cue_path.name,
                source_format='cue',
                
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
