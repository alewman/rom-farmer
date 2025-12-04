"""PS3 ISO extraction and decryption stage."""

import shutil
import subprocess
from pathlib import Path
from typing import Optional

from .base import Stage, StageContext, StageResult, StageStatus


class ExtractPS3Stage(Stage):
    """
    Extract and decrypt PS3 games from Redump archives.
    
    Pipeline:
    1. Extract encrypted ISO from ZIP
    2. Find matching disc key (.dkey file)
    3. Decrypt ISO using PS3Dec
    4. Extract decrypted ISO to JB folder format using 7z
    
    Output: {game_name}/ folder with PS3_DISC.SFB, PS3_GAME/, PS3_UPDATE/
    (Target-specific naming like .ps3 suffix added in organize stage)
    """

    def __init__(
        self,
        keys_directory: Path,
        ps3dec_path: Optional[str] = None
    ):
        """
        Initialize PS3 extraction stage.
        
        Args:
            keys_directory: Directory containing .dkey files
            ps3dec_path: Path to PS3Dec tool (defaults to tools/bin/ps3dec)
        """
        super().__init__("PS3 Extraction")
        self.keys_directory = keys_directory
        self.ps3dec_path = ps3dec_path or str(
            Path(__file__).parent.parent.parent / "tools" / "bin" / "ps3dec"
        )
        
        if not Path(self.ps3dec_path).exists():
            raise FileNotFoundError(f"PS3Dec not found: {self.ps3dec_path}")
        if not self.keys_directory.exists():
            raise FileNotFoundError(f"Keys directory not found: {self.keys_directory}")

    def execute(self, context: StageContext) -> StageResult:
        """
        Extract and decrypt PS3 games.
        
        Args:
            context: Stage context
            
        Returns:
            StageResult with extraction results
        """
        # Get files to process (from DAT/rating filter, or fall back to all source ZIPs)
        source_files = context.filtered_files or context.matched_files or context.source_files
        if not source_files:
            self._log(context, "[yellow]No files to extract[/yellow]")
            return StageResult(
                status=StageStatus.SUCCESS,
                message="No files to extract",
                files_processed=0
            )

        self._log(context, f"[cyan]Extracting and decrypting {len(source_files)} PS3 games...[/cyan]")
        
        extracted_count = 0
        failed_count = 0
        
        for zip_file in source_files:
            if not zip_file.exists():
                self._log(context, f"[yellow]  Warning: {zip_file.name} not found[/yellow]")
                continue
                
            try:
                # Extract and decrypt this game
                game_folder = self._process_game(zip_file, context)
                if game_folder:
                    extracted_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                self._log(context, f"[red]  Error processing {zip_file.name}: {e}[/red]")
                failed_count += 1

        # Update context with extracted game folders
        context.filtered_files = list(context.work_dir.glob("*/"))
        
        self._log(context, f"[green]  Extracted: {extracted_count} games[/green]")
        if failed_count > 0:
            self._log(context, f"[yellow]  Failed: {failed_count} games[/yellow]")

        return StageResult(
            status=StageStatus.SUCCESS if failed_count == 0 else StageStatus.WARNING,
            message=f"Extracted {extracted_count} PS3 games ({failed_count} failed)",
            files_processed=extracted_count
        )

    def _process_game(self, zip_file: Path, context: StageContext) -> Optional[Path]:
        """
        Process a single PS3 game: extract, decrypt, extract to JB format.
        
        Args:
            zip_file: Source ZIP file
            context: Stage context
            
        Returns:
            Path to extracted game folder, or None if failed
        """
        game_name = zip_file.stem
        work_dir = context.work_dir
        
        # Step 1: Extract encrypted ISO from ZIP
        self._log(context, f"  Processing: {game_name}")
        
        try:
            result = subprocess.run(
                ["unzip", "-q", "-o", str(zip_file), "-d", str(work_dir)],
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            self._log(context, f"[red]    Failed to extract ZIP: {e.stderr}[/red]")
            return None
        
        # Find the extracted ISO
        iso_file = work_dir / f"{game_name}.iso"
        if not iso_file.exists():
            self._log(context, f"[red]    ISO not found after extraction: {iso_file.name}[/red]")
            return None
        
        # Step 2: Find disc key
        key = self._find_disc_key(game_name, work_dir)
        if not key:
            self._log(context, f"[red]    Disc key not found for {game_name}[/red]")
            iso_file.unlink()
            return None
        
        # Step 3: Decrypt ISO
        dec_iso = work_dir / f"{game_name}.dec.iso"
        if not self._decrypt_iso(iso_file, dec_iso, key, context):
            iso_file.unlink()
            return None
        
        # Clean up encrypted ISO
        iso_file.unlink()
        
        # Step 4: Extract decrypted ISO to JB folder format
        game_folder = work_dir / game_name
        if not self._extract_to_jb(dec_iso, game_folder, context):
            dec_iso.unlink()
            return None
        
        # Clean up decrypted ISO
        dec_iso.unlink()
        
        # Delete original ZIP
        zip_file.unlink()
        
        self._log(context, f"[green]    ✓ {game_name}[/green]")
        return game_folder

    def _find_disc_key(self, game_name: str, work_dir: Path) -> Optional[str]:
        """
        Find disc key for a game.
        
        Args:
            game_name: Game name (without extension)
            work_dir: Working directory for temp extraction
            
        Returns:
            32-character hex key string, or None if not found
        """
        # Look for matching .dkey file (might be in a ZIP)
        key_zip = self.keys_directory / f"{game_name}.zip"
        
        if not key_zip.exists():
            return None
        
        # Extract key file to temp location
        try:
            subprocess.run(
                ["unzip", "-q", "-o", str(key_zip), "-d", str(work_dir)],
                capture_output=True,
                check=True
            )
            
            key_file = work_dir / f"{game_name}.dkey"
            if key_file.exists():
                key = key_file.read_text().strip()[:32]  # First 32 hex chars
                key_file.unlink()  # Clean up
                return key
                
        except subprocess.CalledProcessError:
            pass
        
        return None

    def _decrypt_iso(
        self, 
        iso_file: Path, 
        dec_iso: Path, 
        key: str,
        context: StageContext
    ) -> bool:
        """
        Decrypt PS3 ISO using PS3Dec.
        
        Args:
            iso_file: Encrypted ISO file
            dec_iso: Output decrypted ISO file
            key: 32-character hex disc key
            context: Stage context
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = subprocess.run(
                [self.ps3dec_path, "d", "key", key, str(iso_file), str(dec_iso)],
                capture_output=True,
                text=True,
                check=True
            )
            return dec_iso.exists()
            
        except subprocess.CalledProcessError as e:
            self._log(context, f"[red]    Decryption failed: {e.stderr}[/red]")
            return False

    def _extract_to_jb(
        self, 
        dec_iso: Path, 
        game_folder: Path,
        context: StageContext
    ) -> bool:
        """
        Extract decrypted ISO to JB folder format using 7z.
        
        Args:
            dec_iso: Decrypted ISO file
            game_folder: Target folder for extraction
            context: Stage context
            
        Returns:
            True if successful, False otherwise
        """
        try:
            game_folder.mkdir(parents=True, exist_ok=True)
            
            result = subprocess.run(
                ["7z", "x", f"-o{game_folder}", str(dec_iso), "-y"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Verify expected structure
            if (game_folder / "PS3_DISC.SFB").exists() and \
               (game_folder / "PS3_GAME").exists():
                return True
            else:
                self._log(context, "[red]    Invalid JB structure after extraction[/red]")
                return False
                
        except subprocess.CalledProcessError as e:
            self._log(context, f"[red]    Extraction failed: {e.stderr}[/red]")
            return False
