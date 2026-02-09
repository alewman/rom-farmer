"""Stage for converting Redump ISOs to XISO format for Xbox/Xbox 360.

Redump archives contain full disc images, but xemu/XEMU requires XISO format
which only contains the game partition. The extract-xiso tool handles this
conversion with the -r (rewrite) flag.

Output: .iso files in XISO format (can be further compressed to squashfs)
"""

import hashlib
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from .base import Stage, StageContext, StageResult, StageStatus
from ..metadata.transformation_recorder import TransformationRecorder


class ConvertXISOStage(Stage):
    """Convert Redump ISO files to XISO format.
    
    For Xbox and Xbox 360, Myrient/Redump provides full disc images.
    xemu requires XISO format (game partition only). This stage uses
    extract-xiso to convert ISOs in place.
    
    The extract-xiso -r flag rewrites the ISO filesystem structure,
    converting Redump format to XISO format. The original file is
    renamed to .iso.old and can be deleted.
    
    Tracks transformations in the database for hash management,
    enabling ScreenScraper lookups using original Redump hashes.
    """
    
    # Default path to extract-xiso tool
    DEFAULT_EXTRACT_XISO_PATH = Path("/data/emu/rom-farmer/tools/bin/extract-xiso")
    
    def __init__(self, extract_xiso_path: Optional[Path] = None, db_session: Optional[Session] = None):
        """Initialize the ConvertXISO stage.
        
        Args:
            extract_xiso_path: Path to extract-xiso executable
            db_session: Database session for transformation recording (optional)
        """
        super().__init__("Convert to XISO")
        self.extract_xiso_path = extract_xiso_path or self.DEFAULT_EXTRACT_XISO_PATH
        self.db_session = db_session
        self.transformation_recorder = TransformationRecorder(self.db_session) if self.db_session else None
    
    def execute(self, context: StageContext) -> StageResult:
        """Convert extracted ISOs to XISO format.
        
        Args:
            context: Stage context with extracted files
            
        Returns:
            StageResult with conversion statistics
        """
        # Find ISO files to convert (from extraction stage)
        iso_files = self._find_iso_files(context)
        
        if not iso_files:
            return StageResult(
                status=StageStatus.SKIPPED,
                message="No ISO files found to convert",
            )
        
        self._log_info(context, f"Converting {len(iso_files)} ISOs to XISO format...")
        
        # Verify extract-xiso exists
        if not self.extract_xiso_path.exists():
            return StageResult(
                status=StageStatus.FAILED,
                message=f"extract-xiso not found at {self.extract_xiso_path}",
            )
        
        converted_files: List[Path] = []
        failed_files: List[Path] = []
        
        for iso_file in iso_files:
            try:
                xiso_file = self._convert_to_xiso(iso_file, context)
                
                if xiso_file and xiso_file.exists():
                    converted_files.append(xiso_file)
                    size_gb = xiso_file.stat().st_size / 1e9
                    self._log_info(
                        context,
                        f"  ✓ {xiso_file.name} ({size_gb:.2f} GB)"
                    )
                else:
                    self._log_warning(context, f"  ✗ Failed: {iso_file.name}")
                    failed_files.append(iso_file)
                    
            except Exception as e:
                self._log_error(context, f"  ✗ Error converting {iso_file.name}: {e}")
                failed_files.append(iso_file)
        
        # Update context with converted files
        context.extracted_files = converted_files
        
        # Calculate total size
        total_size_gb = sum(f.stat().st_size for f in converted_files) / 1e9
        
        # Build result message
        message = f"Converted {len(converted_files)} files to XISO ({total_size_gb:.1f} GB)"
        if failed_files:
            message += f", {len(failed_files)} failed"
        
        return StageResult(
            status=StageStatus.SUCCESS if converted_files else StageStatus.FAILED,
            message=message,
            files_processed=len(iso_files),
            files_matched=len(converted_files),
            files_failed=len(failed_files),
        )
    
    def _find_iso_files(self, context: StageContext) -> List[Path]:
        """Find ISO files to convert from extraction stage or work directory.
        
        Args:
            context: Stage context
            
        Returns:
            List of ISO file paths
        """
        iso_files = []
        
        # Check extracted_files from previous stage
        if context.extracted_files:
            for f in context.extracted_files:
                if f.suffix.lower() == '.iso':
                    iso_files.append(f)
        
        # Also scan work directory for any ISOs
        if context.work_dir.exists():
            for f in context.work_dir.glob("*.iso"):
                if f not in iso_files:
                    iso_files.append(f)
        
        return iso_files
    
    def _calculate_md5(self, file_path: Path) -> str:
        """Calculate MD5 hash of a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            MD5 hash as hex string
        """
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192 * 1024), b''):  # 8MB chunks
                md5.update(chunk)
        return md5.hexdigest()
    
    def _convert_to_xiso(self, iso_file: Path, context: StageContext) -> Optional[Path]:
        """Convert a single Redump ISO to XISO format.
        
        Uses extract-xiso -r to rewrite the ISO in place.
        The original is renamed to .iso.old.
        Records transformation for hash management.
        
        Args:
            iso_file: Path to ISO file
            context: Stage context
            
        Returns:
            Path to converted XISO file, or None on failure
        """
        # Capture source hash BEFORE conversion for transformation tracking
        source_md5 = None
        source_size = None
        if self.db_session:
            self._log_info(context, f"  Hashing source ISO: {iso_file.name}")
            source_md5 = self._calculate_md5(iso_file)
            source_size = iso_file.stat().st_size
            self._log_info(context, f"    Source MD5: {source_md5[:16]}...")
        
        # Run extract-xiso -r to convert in place
        # -r = rewrite mode (converts Redump to XISO format)
        # IMPORTANT: Must run from the ISO's directory, as extract-xiso
        # creates output in the current working directory
        cmd = [
            str(self.extract_xiso_path),
            "-r",  # Rewrite mode
            str(iso_file.name)  # Use just filename, not full path
        ]
        
        self._log_info(context, f"  Converting: {iso_file.name}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout for large games
            cwd=iso_file.parent  # Run from the ISO's directory
        )
        
        if result.returncode != 0:
            self._log_error(context, f"extract-xiso failed: {result.stderr}")
            return None
        
        # After -r conversion, original is renamed to .iso.old
        # The .iso file is now in XISO format
        old_file = iso_file.with_suffix('.iso.old')
        
        if old_file.exists():
            # Delete the original Redump ISO
            old_file.unlink()
            self._log_info(context, f"    Removed original: {old_file.name}")
        
        # Verify the converted file exists
        if iso_file.exists():
            # Record transformation if we have database session
            if self.db_session and source_md5:
                self._record_transformation(
                    context, 
                    iso_file, 
                    source_md5, 
                    source_size
                )
            return iso_file
        
        return None
    
    def _record_transformation(
        self, 
        context: StageContext, 
        xiso_file: Path, 
        source_md5: str,
        source_size: int
    ):
        """Record transformation from Redump ISO to XISO.
        
        Args:
            context: Stage context
            xiso_file: Path to converted XISO file
            source_md5: MD5 hash of original Redump ISO
            source_size: Size of original Redump ISO
        """
        from ..metadata.transformation import ROMTransformation
        from ..metadata.database import ScrapedGame
        from sqlalchemy.exc import IntegrityError
        
        try:
            # Calculate final XISO hash
            self._log_info(context, f"  Hashing XISO: {xiso_file.name}")
            final_md5 = self._calculate_md5(xiso_file)
            final_size = xiso_file.stat().st_size
            self._log_info(context, f"    XISO MD5: {final_md5[:16]}...")
            
            # Check if transformation already exists
            existing = self.db_session.query(ROMTransformation).filter_by(
                source_md5=source_md5,
                final_md5=final_md5,
            ).first()
            
            if existing:
                # Update existing record
                existing.transformation_date = datetime.utcnow()
                existing.transformation_tool = 'extract-xiso'
                existing.transformation_version = '2.7.1'
                existing.transformation_params = {"format": "xiso", "mode": "rewrite"}
                self.db_session.commit()
                self._log_info(context, f"    ✓ Updated existing transform: {source_md5[:8]}... → {final_md5[:8]}...")
                return
            
            # Try to find game in database by source MD5
            game = self.db_session.query(ScrapedGame).filter_by(
                md5=source_md5
            ).first()
            
            game_id = game.id if game else None
            
            if game:
                self._log_info(context, f"    ✓ Found game: {game.name}")
            
            # Get platform name from context for source_dat field
            platform_name = context.platform_name if hasattr(context, 'platform_name') else 'xbox'
            source_dat = f"Redump - Microsoft {platform_name.replace('xbox', 'Xbox ').replace('360', '360').strip()}"
            
            # Create new transformation record (use correct column names from model)
            transformation = ROMTransformation(
                source_md5=source_md5,
                source_file_size=source_size,
                source_format='redump-iso',
                source_dat=source_dat,
                final_md5=final_md5,
                final_file_size=final_size,
                final_format='xiso',
                final_file_name=xiso_file.name,
                transformation_tool='extract-xiso',
                transformation_version='2.7.1',
                transformation_params={"format": "xiso", "mode": "rewrite"},
                transformation_date=datetime.utcnow(),
                game_id=game_id,
            )
            
            self.db_session.add(transformation)
            self.db_session.commit()
            
            compression_ratio = (final_size / source_size * 100) if source_size > 0 else 0
            self._log_info(
                context, 
                f"    ✓ Recorded: {source_md5[:8]}... → {final_md5[:8]}... ({compression_ratio:.0f}%)"
            )
            
        except IntegrityError as e:
            self.db_session.rollback()
            self._log_warning(context, f"    ⚠ Duplicate transformation record: {e}")
        except Exception as e:
            self.db_session.rollback()
            self._log_error(context, f"    ✗ Failed to record transformation: {e}")


class CompressSquashfsStage(Stage):
    """Compress XISO files to squashfs format.
    
    Batocera supports .iso.squashfs for Xbox games, providing significant
    space savings while maintaining read performance.
    
    Note: Extension must be .iso.squashfs (not just .squashfs)
    """
    
    def __init__(self):
        """Initialize the CompressSquashfs stage."""
        super().__init__("Compress to Squashfs")
    
    def execute(self, context: StageContext) -> StageResult:
        """Compress XISO files to squashfs format.
        
        Args:
            context: Stage context with converted XISO files
            
        Returns:
            StageResult with compression statistics
        """
        # Find XISO files to compress
        xiso_files = [f for f in context.extracted_files if f.suffix.lower() == '.iso']
        
        if not xiso_files:
            return StageResult(
                status=StageStatus.SKIPPED,
                message="No XISO files found to compress",
            )
        
        # Check if mksquashfs is available
        if not shutil.which('mksquashfs'):
            return StageResult(
                status=StageStatus.FAILED,
                message="mksquashfs not found in PATH",
            )
        
        self._log_info(context, f"Compressing {len(xiso_files)} XISO files to squashfs...")
        
        compressed_files: List[Path] = []
        failed_files: List[Path] = []
        original_size = 0
        compressed_size = 0
        
        for xiso_file in xiso_files:
            try:
                # Output file: game.iso.squashfs
                squashfs_file = xiso_file.with_suffix('.iso.squashfs')
                
                original_size += xiso_file.stat().st_size
                
                # Run mksquashfs
                cmd = [
                    'mksquashfs',
                    str(xiso_file),
                    str(squashfs_file),
                    '-comp', 'zstd',  # Use zstd compression
                    '-Xcompression-level', '19',  # High compression
                    '-noappend',  # Don't append to existing
                    '-quiet'
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=1800  # 30 minute timeout
                )
                
                if result.returncode == 0 and squashfs_file.exists():
                    compressed_size += squashfs_file.stat().st_size
                    compressed_files.append(squashfs_file)
                    
                    # Remove original XISO
                    xiso_file.unlink()
                    
                    ratio = squashfs_file.stat().st_size / (original_size / len(xiso_files)) * 100
                    self._log_info(
                        context,
                        f"  ✓ {squashfs_file.name} ({ratio:.0f}% of original)"
                    )
                else:
                    self._log_warning(context, f"  ✗ Failed: {xiso_file.name}")
                    failed_files.append(xiso_file)
                    
            except Exception as e:
                self._log_error(context, f"  ✗ Error: {xiso_file.name}: {e}")
                failed_files.append(xiso_file)
        
        # Update context
        context.extracted_files = compressed_files
        
        # Calculate stats
        if original_size > 0:
            ratio = (compressed_size / original_size) * 100
            saved_gb = (original_size - compressed_size) / 1e9
            message = f"Compressed {len(compressed_files)} files ({ratio:.0f}%, saved {saved_gb:.1f} GB)"
        else:
            message = f"Compressed {len(compressed_files)} files"
        
        if failed_files:
            message += f", {len(failed_files)} failed"
        
        return StageResult(
            status=StageStatus.SUCCESS if compressed_files else StageStatus.FAILED,
            message=message,
            files_processed=len(xiso_files),
            files_matched=len(compressed_files),
            files_failed=len(failed_files),
        )
