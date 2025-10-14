"""Transform PS3 ISOs for various targets.

Supports multiple output formats:
- folder: Extracted PS3_GAME structure (RPCS3, CFW)
- iso: Decrypted ISO (CFW, ps3netsrv)
- iso.gz: Compressed decrypted ISO (ps3netsrv space-saving)
"""

import gzip
import shutil
import subprocess
import time
import zipfile
from pathlib import Path
from typing import Optional

from ..stages.base import Stage, StageContext, StageResult, StageStatus
from ..stages.transform_models import (
    FileTransformation,
    TransformStatus,
    TransformStep,
    TransformType,
)


class TransformPS3Stage(Stage):
    """Transform PS3 ISOs for various targets.
    
    This stage handles the complete PS3 game transformation pipeline:
    1. Unzip encrypted ISO from Myrient archive
    2. Find matching disc key (.dkey file)
    3. Decrypt ISO using PS3Dec
    4. Output in target-specific format:
       - folder: Extract to PS3_GAME structure (RPCS3 preferred)
       - iso: Decrypted ISO file (CFW compatible)
       - iso.gz: Gzip compressed ISO (ps3netsrv space-saving)
    
    Supports multiple targets simultaneously (e.g., RPCS3 + ps3netsrv).
    """
    
    def __init__(self):
        """Initialize the Transform PS3 stage."""
        super().__init__("Transform PS3")
        self.ps3dec_path = self._find_ps3dec()
    
    def _find_ps3dec(self) -> Path:
        """Find PS3Dec binary.
        
        Returns:
            Path to PS3Dec executable
            
        Raises:
            FileNotFoundError: If PS3Dec not found
        """
        candidates = [
            Path("/data/emu/bin/PS3Dec"),
            Path("/usr/local/bin/PS3Dec"),
            Path("/usr/bin/PS3Dec"),
            Path.home() / "bin" / "PS3Dec",
        ]
        
        for path in candidates:
            if path.exists() and path.is_file():
                # Verify it's executable
                if not path.stat().st_mode & 0o111:
                    path.chmod(path.stat().st_mode | 0o111)
                return path
        
        raise FileNotFoundError(
            "PS3Dec not found! Please install it to /data/emu/bin/PS3Dec"
        )
    
    def execute(self, context: StageContext) -> StageResult:
        """Transform all matched PS3 games.
        
        Args:
            context: Stage context with matched files and config
            
        Returns:
            StageResult with transformation statistics
        """
        import tempfile
        
        self._log_info(context, "Transforming PS3 games...")
        
        # Get configuration
        if not hasattr(context.platform_config, 'decryption'):
            self._log_error(context, "No decryption config found for PS3")
            return StageResult(
                status=StageStatus.FAILED,
                message="No decryption configuration",
            )
        
        keys_dir = Path(context.platform_config.decryption.disc_keys_dir)
        if not keys_dir.exists():
            self._log_error(context, f"Disc keys directory not found: {keys_dir}")
            return StageResult(
                status=StageStatus.FAILED,
                message=f"Disc keys not found: {keys_dir}",
            )
        
        # Get target format
        target = next(
            (t for t in context.platform_config.targets if t.name == context.target_name),
            None
        )
        if not target:
            self._log_error(context, f"Target not found: {context.target_name}")
            return StageResult(
                status=StageStatus.FAILED,
                message=f"Target not found: {context.target_name}",
            )
        
        # Get target format based on target name
        # rpcs3/ps3-cfw → folder format
        # ps3netsrv → .iso.gz format
        target_format = "iso" if context.target_name == "ps3netsrv" else "folder"
        target_compression = "gzip" if context.target_name == "ps3netsrv" else None
        
        self._log_info(context, f"Target format: {target_format}")
        if target_compression:
            self._log_info(context, f"Compression: {target_compression}")
        
        # Transform each game
        transformations = []
        successful = 0
        failed = 0
        
        for zip_file in context.matched_files:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                try:
                    self._log_info(context, f"Processing: {zip_file.name}")
                    
                    transformation = self._transform_ps3_game(
                        zip_file=zip_file,
                        target_format=target_format,
                        target_compression=target_compression,
                        keys_dir=keys_dir,
                        temp_dir=temp_path,
                        output_dir=context.output_dir,
                    )
                    
                    transformations.append(transformation)
                    
                    if transformation.status == TransformStatus.SUCCESS:
                        successful += 1
                        self._log_info(context, f"  ✓ {transformation.get_summary()}")
                    else:
                        failed += 1
                        self._log_error(context, f"  ✗ {transformation.get_summary()}")
                    
                except Exception as e:
                    self._log_error(context, f"  ✗ Failed: {e}")
                    failed += 1
                    
                    # Create failed transformation record
                    transformation = FileTransformation(source_file=zip_file)
                    transformation.status = TransformStatus.FAILED
                    transformation.error = str(e)
                    transformations.append(transformation)
        
        # Update context
        context.transformations = transformations
        
        # Build result message
        message = f"Transformed {successful} PS3 games"
        if failed:
            message += f", {failed} failed"
        
        return StageResult(
            status=StageStatus.SUCCESS if successful > 0 else StageStatus.FAILED,
            message=message,
            files_processed=len(context.matched_files),
            files_matched=successful,
            files_failed=failed,
        )
    
    def _transform_ps3_game(
        self,
        zip_file: Path,
        target_format: str,
        target_compression: Optional[str],
        keys_dir: Path,
        temp_dir: Path,
        output_dir: Path,
    ) -> FileTransformation:
        """Transform single PS3 game through all steps.
        
        Args:
            zip_file: Source ZIP file
            target_format: Output format ('folder', 'iso')
            target_compression: Compression type ('gzip' or None)
            keys_dir: Directory containing disc keys
            temp_dir: Temporary directory for processing
            output_dir: Final output directory
            
        Returns:
            FileTransformation with complete transformation record
        """
        transformation = FileTransformation(source_file=zip_file)
        transformation.status = TransformStatus.IN_PROGRESS
        
        try:
            # Step 1: Unzip encrypted ISO
            start = time.time()
            iso_path = self._unzip_iso(zip_file, temp_dir)
            transformation.add_step(TransformStep(
                step_type=TransformType.UNZIP,
                input_file=zip_file,
                output_file=iso_path,
                tool="zipfile",
                status=TransformStatus.SUCCESS,
                duration_seconds=time.time() - start,
            ))
            
            # Step 2: Find disc key
            start = time.time()
            disc_key = self._find_disc_key(zip_file.stem, keys_dir)
            
            # Step 3: Decrypt with PS3Dec
            start = time.time()
            dec_iso_path = self._decrypt_ps3_iso(iso_path, disc_key, temp_dir)
            transformation.add_step(TransformStep(
                step_type=TransformType.DECRYPT_PS3,
                input_file=iso_path,
                output_file=dec_iso_path,
                tool="PS3Dec",
                status=TransformStatus.SUCCESS,
                duration_seconds=time.time() - start,
            ))
            
            # Step 4: Format-specific handling
            if target_format == "folder":
                # Extract to folder structure
                start = time.time()
                folder_path = self._extract_ps3_iso(dec_iso_path, output_dir)
                transformation.add_step(TransformStep(
                    step_type=TransformType.EXTRACT_ISO,
                    input_file=dec_iso_path,
                    output_file=folder_path,
                    tool="7zip",
                    status=TransformStatus.SUCCESS,
                    duration_seconds=time.time() - start,
                ))
                transformation.final_file = folder_path
                
            elif target_format == "iso":
                if target_compression == "gzip":
                    # Compress for ps3netsrv
                    start = time.time()
                    gz_file = self._compress_gzip(dec_iso_path, output_dir, zip_file.stem)
                    transformation.add_step(TransformStep(
                        step_type=TransformType.COMPRESS_CHD,  # Reuse compression type
                        input_file=dec_iso_path,
                        output_file=gz_file,
                        tool="gzip",
                        status=TransformStatus.SUCCESS,
                        duration_seconds=time.time() - start,
                    ))
                    transformation.final_file = gz_file
                else:
                    # Plain decrypted ISO
                    final_iso = output_dir / f"{zip_file.stem}.iso"
                    shutil.move(dec_iso_path, final_iso)
                    transformation.final_file = final_iso
            
            transformation.status = TransformStatus.SUCCESS
            
        except Exception as e:
            transformation.status = TransformStatus.FAILED
            transformation.error = str(e)
        
        return transformation
    
    def _unzip_iso(self, zip_file: Path, temp_dir: Path) -> Path:
        """Extract ISO from ZIP archive.
        
        Args:
            zip_file: Path to ZIP file
            temp_dir: Temporary directory for extraction
            
        Returns:
            Path to extracted ISO file
            
        Raises:
            ValueError: If no ISO found in ZIP
        """
        with zipfile.ZipFile(zip_file, 'r') as zf:
            iso_files = [f for f in zf.namelist() if f.lower().endswith('.iso')]
            
            if not iso_files:
                raise ValueError(f"No ISO found in {zip_file}")
            
            iso_name = iso_files[0]
            zf.extract(iso_name, temp_dir)
            
            return temp_dir / iso_name
    
    def _find_disc_key(self, game_name: str, keys_dir: Path) -> str:
        """Find matching disc key file.
        
        Tries multiple filename variations to match game to key.
        
        Args:
            game_name: Base game name (ZIP stem)
            keys_dir: Directory containing key ZIPs
            
        Returns:
            32-character hex disc key
            
        Raises:
            FileNotFoundError: If no matching key found
        """
        # Try exact match first
        key_zip = keys_dir / f"{game_name}.zip"
        
        if not key_zip.exists():
            # Try without revision markers
            base_name = game_name.replace(" (Rev 1)", "").replace(" (Rev 2)", "")
            key_zip = keys_dir / f"{base_name}.zip"
        
        if not key_zip.exists():
            raise FileNotFoundError(f"No disc key found for {game_name}")
        
        # Extract and read .dkey file
        with zipfile.ZipFile(key_zip, 'r') as zf:
            dkey_files = [f for f in zf.namelist() if f.endswith('.dkey')]
            
            if not dkey_files:
                raise ValueError(f"No .dkey file in {key_zip}")
            
            dkey_content = zf.read(dkey_files[0]).decode('ascii').strip()
            
            # Validate format (32 hex characters)
            if len(dkey_content) != 32:
                raise ValueError(f"Invalid disc key length: {len(dkey_content)}")
            
            return dkey_content
    
    def _decrypt_ps3_iso(self, iso_path: Path, disc_key: str, temp_dir: Path) -> Path:
        """Decrypt PS3 ISO using PS3Dec.
        
        Args:
            iso_path: Path to encrypted ISO
            disc_key: 32-character hex disc key
            temp_dir: Temporary directory
            
        Returns:
            Path to decrypted ISO
            
        Raises:
            RuntimeError: If decryption fails
        """
        dec_iso_path = temp_dir / f"{iso_path.stem}_dec.iso"
        
        cmd = [
            str(self.ps3dec_path),
            "d",           # decrypt mode
            "key",         # key type
            disc_key,      # 32-char hex key
            str(iso_path),
            str(dec_iso_path),
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"PS3Dec failed: {result.stderr}")
        
        if not dec_iso_path.exists():
            raise RuntimeError("Decrypted ISO not created")
        
        return dec_iso_path
    
    def _extract_ps3_iso(self, iso_path: Path, output_dir: Path) -> Path:
        """Extract PS3 ISO to folder structure.
        
        Creates JB folder format:
        GAMEID/
            PS3_GAME/
                PARAM.SFO
                EBOOT.BIN
                USRDIR/
        
        Args:
            iso_path: Path to decrypted ISO
            output_dir: Output directory
            
        Returns:
            Path to game folder
            
        Raises:
            RuntimeError: If extraction fails
        """
        # Extract to temp location first
        temp_extract = output_dir / f"{iso_path.stem}_temp"
        temp_extract.mkdir(parents=True, exist_ok=True)
        
        # Use 7zip to extract ISO
        cmd = ["7z", "x", str(iso_path), f"-o{temp_extract}", "-y"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"7zip extraction failed: {result.stderr}")
        
        # Find PS3_GAME directory
        ps3_game_dirs = list(temp_extract.rglob("PS3_GAME"))
        if not ps3_game_dirs:
            raise RuntimeError("No PS3_GAME directory found in ISO")
        
        # Get parent directory (game root)
        game_root = ps3_game_dirs[0].parent
        
        # Try to read game ID from PARAM.SFO
        param_sfo = game_root / "PS3_GAME" / "PARAM.SFO"
        if param_sfo.exists():
            try:
                game_id = self._read_game_id_from_param_sfo(param_sfo)
            except Exception:
                # Fallback to filename
                game_id = iso_path.stem.replace("_dec", "")
        else:
            game_id = iso_path.stem.replace("_dec", "")
        
        # Move to final location with game ID
        final_dir = output_dir / game_id
        if final_dir.exists():
            shutil.rmtree(final_dir)
        
        shutil.move(str(game_root), str(final_dir))
        
        # Cleanup temp
        shutil.rmtree(temp_extract, ignore_errors=True)
        
        return final_dir
    
    def _read_game_id_from_param_sfo(self, param_sfo_path: Path) -> str:
        """Read game ID from PARAM.SFO file.
        
        Args:
            param_sfo_path: Path to PARAM.SFO
            
        Returns:
            Game ID (e.g., "BLUS30455")
        """
        # Simple parser - reads TITLE_ID field from PARAM.SFO
        # PARAM.SFO is a binary format, but TITLE_ID is ASCII
        
        with open(param_sfo_path, 'rb') as f:
            data = f.read()
        
        # Look for TITLE_ID string
        title_id_marker = b'TITLE_ID'
        pos = data.find(title_id_marker)
        
        if pos == -1:
            raise ValueError("TITLE_ID not found in PARAM.SFO")
        
        # Game ID typically appears shortly after TITLE_ID marker
        # Look for pattern like "BLUS30455" (9 characters: 4 letters + 5 digits)
        search_region = data[pos:pos+100]
        
        import re
        matches = re.findall(b'[A-Z]{4}[0-9]{5}', search_region)
        
        if matches:
            return matches[0].decode('ascii')
        
        raise ValueError("Could not parse game ID from PARAM.SFO")
    
    def _compress_gzip(self, iso_path: Path, output_dir: Path, base_name: str) -> Path:
        """Compress decrypted ISO to .iso.gz for ps3netsrv.
        
        Args:
            iso_path: Path to decrypted ISO
            output_dir: Output directory
            base_name: Base name for output file
            
        Returns:
            Path to .iso.gz file
        """
        gz_path = output_dir / f"{base_name}.iso.gz"
        
        with open(iso_path, 'rb') as f_in:
            with gzip.open(gz_path, 'wb', compresslevel=6) as f_out:
                shutil.copyfileobj(f_in, f_out, length=1024*1024)  # 1MB chunks
        
        return gz_path
