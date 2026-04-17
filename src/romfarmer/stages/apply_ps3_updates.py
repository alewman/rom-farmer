"""PS3 update application stage.

Applies game updates and DLC from NoPayStation PKG files to PS3 JB folders.
"""

import subprocess
import shutil
import tempfile
import sys
from pathlib import Path
from typing import Optional, Dict, List
import struct

from romfarmer.stages.base import Stage, StageContext, StageResult, StageStatus, StagePhase
from romfarmer.stages.ps3_utils import SonyPSNClient, NoPayStationDatabase

# Import Python PKG decrypter as fallback for problematic PKG files
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "tools" / "pkg_decrypt"))
try:
    from pkg_decrypt import PKGDecrypter
    HAS_PYTHON_DECRYPTER = True
except ImportError:
    HAS_PYTHON_DECRYPTER = False


class ApplyPS3UpdatesStage(Stage):
    PHASE = StagePhase.FINALIZE

    """Apply PS3 game updates from NoPayStation PKG archive."""
    
    def __init__(
        self,
        nps_database: str,
        pkg_archive: str,
        pkgrip_path: str = "/data/emu/rom-farmer/tools/pkgrip/src/pkgrip",
        apply_updates: bool = True,
        apply_dlc: bool = False,
        dlc_mode: str = "copy",
        use_sony_psn: bool = True,
    ):
        """Initialize stage.
        
        Args:
            nps_database: Path to PS3_DLCS.tsv database
            pkg_archive: Path to directory containing PKG files
            pkgrip_path: Path to pkgrip binary
            apply_updates: Whether to apply game updates
            apply_dlc: Whether to apply DLC content
            dlc_mode: DLC mode - "copy" (PKG to _PKG folder) or "extract" (merge to disc)
            use_sony_psn: Whether to query Sony PSN servers for updates (recommended)
        """
        super().__init__("Apply PS3 Updates")
        self.nps_database_path = Path(nps_database)
        self.pkg_archive_path = Path(pkg_archive)
        self.pkgrip_path = Path(pkgrip_path)
        self.apply_updates = apply_updates
        self.apply_dlc = apply_dlc
        self.dlc_mode = dlc_mode
        self.use_sony_psn = use_sony_psn
        
        # Load NoPayStation database for DLC
        self.database = NoPayStationDatabase(self.nps_database_path)
        
        # Initialize Sony PSN client for updates
        self.psn_client = SonyPSNClient() if use_sony_psn else None
    
    def execute(self, context: StageContext) -> StageResult:
        """Apply updates and DLC to PS3 game folders.
        
        Args:
            context: Stage context with game folders
            
        Returns:
            StageResult with update statistics
        """
        if not self.apply_updates and not self.apply_dlc:
            print("Update and DLC application disabled, skipping")
            return StageResult(
                status=StageStatus.SKIPPED,
                message="Update and DLC application disabled",
            )
        
        if not self.pkgrip_path.exists():
            print(f"pkgrip not found: {self.pkgrip_path}")
            print("Run: cd tools/pkgrip/src && make")
            return StageResult(
                status=StageStatus.SKIPPED,
                message="pkgrip tool not found",
            )
        
        # Find PS3 game folders (in output_dir where TransformPS3Stage puts them)
        game_folders = self._find_game_folders(context.output_dir)
        
        if not game_folders:
            print("No PS3 game folders found")
            return StageResult(
                status=StageStatus.SKIPPED,
                message="No game folders to process",
            )
        
        print(f"Found {len(game_folders)} PS3 game folders")
        
        updates_applied = 0
        updates_available = 0
        updates_failed = 0
        dlc_applied = 0
        dlc_available = 0
        dlc_failed = 0
        
        # Track failed packages for debugging
        failed_packages = []
        
        for game_folder in game_folders:
            # Extract title ID
            title_id = self._extract_title_id(game_folder)
            if not title_id:
                print(f"  Skipping {game_folder.name}: No TITLE_ID")
                continue
            
            # Initialize lists
            updates = []
            dlc_list = []
            
            # Find and apply updates
            if self.apply_updates:
                # Try NoPayStation database first
                nps_updates = self.database.find_updates_for_title(title_id)
                
                # Try Sony PSN servers for live updates
                psn_updates = []
                if self.psn_client:
                    psn_updates = self.psn_client.get_updates_for_title(title_id)
                
                # Combine both sources (NPS DLC + Sony updates)
                updates = nps_updates + psn_updates
                
                if updates:
                    updates_available += len(updates)
                    sources = []
                    if nps_updates:
                        sources.append(f"{len(nps_updates)} from NoPayStation")
                    if psn_updates:
                        sources.append(f"{len(psn_updates)} from Sony PSN")
                    source_info = ", ".join(sources)
                    print(f"  {game_folder.name} ({title_id}): {len(updates)} update(s) available ({source_info})")
                    
                    for update in updates:
                        success, error_msg = self._apply_update(game_folder, title_id, update)
                        if success:
                            updates_applied += 1
                        else:
                            updates_failed += 1
                            if error_msg:
                                failed_packages.append({
                                    'game': game_folder.name,
                                    'title_id': title_id,
                                    'package': update.get('Name', 'Unknown'),
                                    'type': 'UPDATE',
                                    'reason': error_msg
                                })
            
            # Find and apply DLC
            if self.apply_dlc:
                # For COPY mode, get ALL DLC (cosmetics, weapons, everything)
                # For EXTRACT mode, only get story DLC (large campaign content)
                if self.dlc_mode == "copy":
                    dlc_list = self.database.find_all_dlc_for_title(title_id)
                else:
                    dlc_list = self.database.find_dlc_for_title(title_id)
                
                if dlc_list:
                    dlc_available += len(dlc_list)
                    print(f"  {game_folder.name} ({title_id}): {len(dlc_list)} DLC(s) available")
                    
                    if self.dlc_mode == "extract":
                        print(f"    Mode: EXTRACT - DLC will be merged into game disc")
                        for dlc in dlc_list:
                            dlc_name = dlc.get('Name', 'Unknown')
                            print(f"    Processing DLC: {dlc_name}")
                            success, error_msg = self._apply_update(game_folder, title_id, dlc)
                            if success:
                                dlc_applied += 1
                                print(f"      ✓ DLC extracted and merged into disc")
                            else:
                                dlc_failed += 1
                                print(f"      ✗ DLC failed: {error_msg}")
                                if error_msg:
                                    failed_packages.append({
                                        'game': game_folder.name,
                                        'title_id': title_id,
                                        'package': dlc.get('Name', 'Unknown'),
                                        'type': 'DLC',
                                        'reason': error_msg
                                    })
                    else:  # mode == "copy"
                        print(f"    Mode: COPY - DLC PKG files will be copied to _PKG folder")
                        pkg_folder = game_folder / "_PKG"
                        pkg_folder.mkdir(exist_ok=True)
                        
                        for dlc in dlc_list:
                            dlc_name = dlc.get('Name', 'Unknown')
                            content_id = dlc.get('Content ID', '')
                            rap_key = dlc.get('RAP', '')
                            print(f"    Copying DLC: {dlc_name}")
                            
                            # Find PKG file
                            pkg_file = self._find_pkg_file(dlc_name, content_id, title_id)
                            
                            if pkg_file:
                                # Copy PKG to _PKG folder
                                dest_pkg = pkg_folder / pkg_file.name
                                shutil.copy2(pkg_file, dest_pkg)
                                print(f"      ✓ Copied: {pkg_file.name}")
                                
                                # Create RAP file if needed
                                if rap_key and rap_key not in ('NOT_NEEDED', 'MISSING'):
                                    rap_file = pkg_folder / f"{content_id}.rap"
                                    try:
                                        # RAP key is hex string, convert to binary
                                        rap_bytes = bytes.fromhex(rap_key)
                                        rap_file.write_bytes(rap_bytes)
                                        print(f"      ✓ Created license: {rap_file.name}")
                                    except Exception as e:
                                        print(f"      ⚠ License creation failed: {e}")
                                
                                dlc_applied += 1
                            else:
                                dlc_failed += 1
                                error_msg = "PKG file not found locally"
                                print(f"      ✗ {error_msg}")
                                failed_packages.append({
                                    'game': game_folder.name,
                                    'title_id': title_id,
                                    'package': dlc_name,
                                    'type': 'DLC',
                                    'reason': error_msg
                                })
            
            # Show status if nothing found
            if not updates and not dlc_list:
                print(f"  {game_folder.name}: No updates or DLC found")
        
        print("")
        print(f"Summary:")
        print(f"  Games scanned:     {len(game_folders)}")
        if self.apply_updates:
            print(f"  Updates available: {updates_available}")
            print(f"  Updates applied:   {updates_applied}")
            if updates_failed > 0:
                print(f"  Updates FAILED:    {updates_failed}")
        if self.apply_dlc:
            print(f"  DLC available:     {dlc_available}")
            print(f"  DLC applied:       {dlc_applied}")
            if self.dlc_mode == "copy":
                print(f"  DLC mode:          COPY (PKG files in _PKG folders for RPCS3)")
            else:
                print(f"  DLC mode:          EXTRACT (merged into disc for real PS3)")
            if dlc_failed > 0:
                print(f"  DLC FAILED:        {dlc_failed}")
        
        # Show detailed failure list
        if failed_packages:
            print("")
            print(f"⚠️  Failed Packages ({len(failed_packages)}):")
            print("=" * 80)
            for pkg in failed_packages:
                print(f"  [{pkg['type']}] {pkg['game']} ({pkg['title_id']})")
                print(f"       Package: {pkg['package']}")
                print(f"       Reason:  {pkg['reason']}")
                print("")
        
        total_applied = updates_applied + dlc_applied
        total_failed = updates_failed + dlc_failed
        message = f"Applied {updates_applied} updates, {dlc_applied} DLC to {len(game_folders)} games"
        if total_failed:
            message += f" ({total_failed} failed)"
        
        return StageResult(
            status=StageStatus.SUCCESS,
            message=message,
            files_processed=len(game_folders),
            files_matched=total_applied,
            files_failed=total_failed,
        )
    
    def _find_game_folders(self, working_dir: Path) -> List[Path]:
        """Find all PS3 game folders (*.ps3 directories).
        
        Args:
            working_dir: Directory to search
            
        Returns:
            List of game folder paths
        """
        folders = []
        
        for item in working_dir.iterdir():
            if item.is_dir() and item.name.endswith('.ps3'):
                # Verify it has PS3_GAME structure
                if (item / 'PS3_GAME' / 'PARAM.SFO').exists():
                    folders.append(item)
        
        return sorted(folders)
    
    def _extract_title_id(self, game_folder: Path) -> Optional[str]:
        """Extract TITLE_ID from PARAM.SFO.
        
        Args:
            game_folder: Game folder path
            
        Returns:
            str: Title ID or None
        """
        param_sfo = game_folder / 'PS3_GAME' / 'PARAM.SFO'
        
        if not param_sfo.exists():
            return None
        
        try:
            with open(param_sfo, 'rb') as f:
                data = f.read()
            
            # Parse PARAM.SFO to find TITLE_ID
            # Header format: magic(4) + version(4) + key_table_start(4) + data_table_start(4) + entries_count(4)
            if data[:4] != b'\x00PSF':
                return None
            
            key_table_start = struct.unpack('<I', data[8:12])[0]
            data_table_start = struct.unpack('<I', data[12:16])[0]
            entries_count = struct.unpack('<I', data[16:20])[0]
            
            # Parse entries
            for i in range(entries_count):
                entry_offset = 20 + (i * 16)
                key_offset = struct.unpack('<H', data[entry_offset:entry_offset+2])[0]
                data_offset = struct.unpack('<I', data[entry_offset+12:entry_offset+16])[0]
                
                # Read key name
                key_start = key_table_start + key_offset
                key_end = data.find(b'\x00', key_start)
                key_name = data[key_start:key_end].decode('utf-8', errors='ignore')
                
                if key_name == 'TITLE_ID':
                    # Read value
                    value_start = data_table_start + data_offset
                    value_end = data.find(b'\x00', value_start)
                    title_id = data[value_start:value_end].decode('utf-8', errors='ignore')
                    return title_id
            
            return None
        
        except Exception as e:
            print(f"Error reading PARAM.SFO: {e}")
            return None
    
    def _apply_update(self, game_folder: Path, title_id: str, update: Dict) -> bool:
        """Apply a single update to game folder.
        
        Args:
            game_folder: Game folder path
            title_id: Game title ID
            update: Update entry from database
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        update_name = update.get('Name', 'Unknown')
        content_id = update.get('Content ID', '')
        rap_key = update.get('RAP', '')
        pkg_url = update.get('PKG direct link', '')
        source = update.get('Source', 'NoPayStation')
        
        if rap_key == 'MISSING':
            error_msg = "RAP key missing"
            print(f"    {update_name}: {error_msg}, skipping")
            return False, error_msg
        
        # Find or download PKG file
        pkg_file = None
        
        # If we have a direct download URL (Sony PSN), download it
        if pkg_url and source == 'Sony PSN':
            pkg_file = self._download_pkg_from_url(pkg_url, title_id, update_name)
        else:
            # Find PKG file in local archive (NoPayStation)
            pkg_file = self._find_pkg_file(update_name, content_id, title_id)
        
        if not pkg_file:
            error_msg = "PKG file not available (not found locally or download failed)"
            print(f"    {update_name}: {error_msg}")
            return False, error_msg
        
        print(f"    Applying: {update_name} [{source}]")
        print(f"      PKG: {pkg_file.name}")
        if rap_key != 'NOT_NEEDED':
            print(f"      RAP: {rap_key[:16]}..." if len(rap_key) > 16 else f"      RAP: {rap_key}")
        
        # Extract PKG to temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Run pkg2zip
            success, extract_error = self._extract_pkg(pkg_file, rap_key, temp_path)
            
            if not success:
                error_msg = f"PKG extraction failed: {extract_error}"
                print(f"      ✗ {error_msg}")
                return False, error_msg
            
            # Merge extracted files into game folder
            merge_error = self._merge_update_files(temp_path, game_folder)
            if merge_error:
                error_msg = f"File merge failed: {merge_error}"
                print(f"      ✗ {error_msg}")
                return False, error_msg
        
        print(f"      ✓ Applied successfully")
        return True, None
    
    def _find_pkg_file(self, update_name: str, content_id: str, title_id: str) -> Optional[Path]:
        """Find PKG file in archive by update name, content ID, or title ID.
        
        Args:
            update_name: DLC/update name from database
            content_id: Content ID (e.g., "UP0006-BLUS31053_00-...")
            title_id: Title ID (e.g., "BLUS31053")
            
        Returns:
            Path to PKG file or None
        """
        # Search in both flat and packages/ subdirectory
        search_dirs = [
            self.pkg_archive_path,
            self.pkg_archive_path / 'packages'
        ]
        
        # Normalize update name for fuzzy matching (remove special chars)
        normalized_name = update_name.replace(':', '').replace('™', '').replace('®', '')
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            
            # Try finding by exact name match first
            exact_match = search_dir / f"{update_name}.pkg"
            if exact_match.exists():
                return exact_match
            
            # Try normalized name (e.g., "Aliens: Colonial Marines" → "Aliens Colonial Marines")
            normalized_match = search_dir / f"{normalized_name}.pkg"
            if normalized_match.exists():
                return normalized_match
            
            # Try fuzzy matching - check if most of the name matches
            for pkg_file in search_dir.glob('*.pkg'):
                pkg_name_normalized = pkg_file.stem.replace(':', '').replace('™', '').replace('®', '')
                
                # If normalized names are very similar, it's a match
                if normalized_name.lower() == pkg_name_normalized.lower():
                    return pkg_file
                
                # Also try matching by title ID in filename
                if title_id in pkg_file.name:
                    # Make sure it's actually related to this DLC by checking name similarity
                    name_words = set(normalized_name.lower().split())
                    file_words = set(pkg_name_normalized.lower().split())
                    common_words = name_words & file_words
                    
                    # If >60% of words match, consider it a match
                    if len(common_words) > len(name_words) * 0.6:
                        return pkg_file
        
        return None
    
    def _download_pkg_from_url(self, url: str, title_id: str, update_name: str) -> Optional[Path]:
        """Download PKG file from Sony PSN servers.
        
        Args:
            url: Direct download URL (e.g., http://b0.ww.np.dl.playstation.net/...)
            title_id: Game title ID (for caching)
            update_name: Update name (for filename)
            
        Returns:
            Path to downloaded PKG file, or None if failed
        """
        import requests
        
        # Create cache directory for Sony downloads
        cache_dir = self.pkg_archive_path / 'sony_psn_cache'
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename from URL (last part)
        filename = url.split('/')[-1]
        if not filename.endswith('.pkg'):
            filename = f"{title_id}_update.pkg"
        
        cached_file = cache_dir / filename
        
        # Use cached file if it exists
        if cached_file.exists():
            print(f"      Using cached PKG: {cached_file.name}")
            return cached_file
        
        # Download from Sony servers
        print(f"      Downloading from Sony PSN...")
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Get total size for progress
            total_size = int(response.headers.get('content-length', 0))
            total_mb = total_size / (1024 * 1024)
            
            # Download with progress
            downloaded = 0
            with open(cached_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            mb_done = downloaded / (1024 * 1024)
                            print(f"      Progress: {progress:.1f}% ({mb_done:.1f}/{total_mb:.1f} MB)", end='\r')
            
            print(f"\n      Downloaded: {cached_file.name} ({total_mb:.1f} MB)")
            return cached_file
            
        except Exception as e:
            print(f"      Download failed: {e}")
            if cached_file.exists():
                cached_file.unlink()  # Remove partial download
            return None
    
    def _extract_pkg(self, pkg_file: Path, rap_key: str, output_dir: Path) -> tuple[bool, Optional[str]]:
        """Extract PKG file using pkgrip, with Python decrypter fallback.
        
        Args:
            pkg_file: Path to PKG file
            rap_key: RAP key (hex string, not used by pkgrip)
            output_dir: Output directory
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        # Try pkgrip first (fast C implementation)
        pkgrip_success, pkgrip_error = self._extract_pkg_with_pkgrip(pkg_file, output_dir)
        if pkgrip_success:
            return True, None
        
        # Check if pkgrip detected an unknown/unsupported PKG format
        if pkgrip_error and "Unknown PKG" in pkgrip_error:
            # Don't try Python decrypter - it won't support it either
            return False, f"Unsupported PKG format (pkgrip: {pkgrip_error})"
        
        # Fall back to Python decrypter if pkgrip fails for other reasons
        if HAS_PYTHON_DECRYPTER:
            print(f"      Trying Python decrypter as fallback...")
            python_success, python_error = self._extract_pkg_with_python(pkg_file, output_dir)
            if python_success:
                return True, None
            return False, f"pkgrip failed ({pkgrip_error}), Python decrypter failed ({python_error})"
        else:
            return False, f"pkgrip failed ({pkgrip_error}), Python decrypter not available"
    
    def _extract_pkg_with_pkgrip(self, pkg_file: Path, output_dir: Path) -> tuple[bool, Optional[str]]:
        """Extract PKG using pkgrip (fast C tool).
        
        Args:
            pkg_file: Path to PKG file
            output_dir: Output directory
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            # Run pkgrip with timeout to catch hangs/segfaults
            result = subprocess.run(
                [str(self.pkgrip_path), str(pkg_file)],
                cwd=output_dir,
                capture_output=True,
                check=False,
                timeout=300  # 5 minute timeout
            )
            
            # Verify extraction produced output directory
            # pkgrip creates {TITLE_ID}_dec/ directory
            content_dirs = [d for d in output_dir.iterdir() if d.is_dir() and d.name.endswith('_dec')]
            if content_dirs:
                print(f"      DEBUG: pkgrip extracted to {content_dirs[0].name}")
                return True, None
            
            # If no directory but return code 0, something went wrong
            if result.returncode == 0:
                error_msg = "pkgrip completed but no output directory created"
                return False, error_msg
            
            # Return code indicates error - check both stdout and stderr for "Unknown PKG"
            stdout = result.stdout.decode('utf-8', errors='ignore').strip() if result.stdout else ""
            stderr = result.stderr.decode('utf-8', errors='ignore').strip() if result.stderr else ""
            
            # Check if it's an unknown PKG format
            if "Unknown PKG" in stdout or "Unknown PKG" in stderr:
                error_msg = "Unknown PKG detected"
                return False, error_msg
            
            # Other error
            error_output = stderr if stderr else stdout if stdout else "No error output"
            error_msg = f"exit code {result.returncode}: {error_output[:100]}"
            return False, error_msg
            
        except subprocess.TimeoutExpired:
            error_msg = "timeout after 5 minutes (possible hang/segfault)"
            return False, error_msg
        except Exception as e:
            error_msg = str(e)
            return False, error_msg
    
    def _extract_pkg_with_python(self, pkg_file: Path, output_dir: Path) -> tuple[bool, Optional[str]]:
        """Extract PKG using Python decrypter (slower but more robust).
        
        Args:
            pkg_file: Path to PKG file
            output_dir: Output directory
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        import signal
        
        class TimeoutError(Exception):
            pass
        
        def timeout_handler(signum, frame):
            raise TimeoutError("PKG extraction exceeded 2 hour timeout")
        
        try:
            # Set 2 hour timeout (7200 seconds)
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(7200)
            
            try:
                decrypter = PKGDecrypter(pkg_file)
                extracted_dir = decrypter.extract_pkg(output_dir=output_dir, verbose=False)
                
                # Cancel the alarm
                signal.alarm(0)
                
                if extracted_dir and extracted_dir.exists():
                    print(f"      DEBUG: Python decrypter extracted to {extracted_dir.name}")
                    return True, None
                else:
                    error_msg = "extraction produced no output directory"
                    return False, error_msg
            except TimeoutError as e:
                signal.alarm(0)
                error_msg = f"Python decrypter timeout (2 hours) - package too large or corrupted"
                print(f"      ✗ {error_msg}")
                return False, error_msg
                
        except Exception as e:
            signal.alarm(0)
            error_msg = str(e)
            return False, error_msg
    
    def _merge_update_files(self, extracted_dir: Path, game_folder: Path) -> Optional[str]:
        """Merge extracted update files into game folder.
        
        Args:
            extracted_dir: Directory with extracted PKG contents
            game_folder: Target game folder (.ps3 root)
            
        Returns:
            Error message if failed, None if successful
        """
        # pkg2zip/pkgrip extracts to a subdirectory with content ID name
        # Find the actual content directory
        content_dirs = [d for d in extracted_dir.iterdir() if d.is_dir()]
        
        if not content_dirs:
            error_msg = "No content directory found in extraction"
            print(f"      {error_msg}")
            return error_msg
        
        source_dir = content_dirs[0]
        print(f"      DEBUG: Merging from {source_dir.name}")
        
        # Update PKGs contain files that should go into PS3_GAME/
        # (PARAM.SFO, USRDIR/, ICON0.PNG, etc.)
        ps3_game_dir = game_folder / "PS3_GAME"
        if not ps3_game_dir.exists():
            error_msg = f"PS3_GAME directory not found in {game_folder.name}"
            print(f"      ERROR: {error_msg}")
            return error_msg
        
        # Copy all files/directories from source to PS3_GAME
        try:
            items_to_merge = list(source_dir.iterdir())
            print(f"      DEBUG: Found {len(items_to_merge)} items to merge into PS3_GAME")
            
            for item in items_to_merge:
                dest = ps3_game_dir / item.name  # Merge into PS3_GAME, not root
                
                if item.is_dir():
                    # Merge directories (USRDIR contains updated game files)
                    if dest.exists():
                        # Merge with existing directory
                        print(f"      DEBUG: Merging directory {item.name}")
                        self._merge_directory(item, dest)
                    else:
                        # Copy new directory
                        print(f"      DEBUG: Copying new directory {item.name}")
                        shutil.copytree(item, dest)
                else:
                    # Copy/overwrite files (PARAM.SFO, ICON0.PNG, etc.)
                    print(f"      DEBUG: Copying file {item.name}")
                    shutil.copy2(item, dest)
        except Exception as e:
            error_msg = f"File merge exception: {str(e)}"
            print(f"      ERROR: {error_msg}")
            return error_msg
        
        return None  # Success
    
    def _merge_directory(self, source: Path, dest: Path):
        """Recursively merge source directory into destination.
        
        Args:
            source: Source directory
            dest: Destination directory
        """
        for item in source.iterdir():
            dest_item = dest / item.name
            
            if item.is_dir():
                if dest_item.exists():
                    self._merge_directory(item, dest_item)
                else:
                    shutil.copytree(item, dest_item)
            else:
                # Overwrite files (updates replace old files)
                shutil.copy2(item, dest_item)
