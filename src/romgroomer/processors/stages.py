"""Processing stages for ROM transformation."""

import zipfile
from pathlib import Path
from typing import Optional

from .base import ProcessingError, ProcessingStage
from ..models.rom import Rom


class ExtractArchiveStage(ProcessingStage):
    """Extract archived ROM files.
    
    Supports:
        - .zip files (built-in)
        - .7z files (requires 7z command)
        - .rar files (requires unrar command)
    
    Example:
        >>> stage = ExtractArchiveStage()
        >>> context = {'temp_dir': Path('/tmp/roms')}
        >>> output = await stage.process(Path('game.zip'), context)
        >>> print(output)
        /tmp/roms/game.nes
    """
    
    def __init__(self, extract_dir: Optional[Path] = None):
        """Initialize extraction stage.
        
        Args:
            extract_dir: Optional extraction directory (overrides context temp_dir)
        """
        self.extract_dir = extract_dir
    
    async def process(self, input_path: Path, context: dict) -> Path:
        """Extract archive and return path to extracted file.
        
        Args:
            input_path: Archive file to extract
            context: Processing context with temp_dir
            
        Returns:
            Path to extracted file (or directory if multiple files)
            
        Raises:
            ProcessingError: If extraction fails
        """
        if not self.can_process(input_path):
            return input_path
        
        # Determine extraction directory
        extract_dir = self.extract_dir or context['temp_dir']
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract based on format
        if input_path.suffix == '.zip':
            extracted = await self._extract_zip(input_path, extract_dir)
        elif input_path.suffix == '.7z':
            extracted = await self._extract_7z(input_path, extract_dir)
        elif input_path.suffix == '.rar':
            extracted = await self._extract_rar(input_path, extract_dir)
        else:
            return input_path
        
        return extracted
    
    def can_process(self, input_path: Path) -> bool:
        """Check if input is an archive file.
        
        Args:
            input_path: Path to check
            
        Returns:
            True if input is a supported archive format
        """
        return input_path.suffix in ['.zip', '.7z', '.rar']
    
    async def _extract_zip(self, archive_path: Path, extract_dir: Path) -> Path:
        """Extract ZIP archive.
        
        Args:
            archive_path: Path to ZIP file
            extract_dir: Directory to extract into
            
        Returns:
            Path to extracted file (or directory if multiple files)
            
        Raises:
            ProcessingError: If extraction fails
        """
        try:
            with zipfile.ZipFile(archive_path, 'r') as zf:
                # Get list of files (excluding directories)
                files = [name for name in zf.namelist() if not name.endswith('/')]
                
                if not files:
                    raise ProcessingError(f"Archive is empty: {archive_path}")
                
                # Extract all files
                zf.extractall(extract_dir)
                
                # If single file, return its path
                if len(files) == 1:
                    return extract_dir / files[0]
                
                # Multiple files - return directory
                return extract_dir
        
        except zipfile.BadZipFile as e:
            raise ProcessingError(f"Invalid ZIP file: {archive_path}") from e
        except Exception as e:
            raise ProcessingError(f"Failed to extract ZIP: {e}") from e
    
    async def _extract_7z(self, archive_path: Path, extract_dir: Path) -> Path:
        """Extract 7z archive using 7z command.
        
        Args:
            archive_path: Path to 7z file
            extract_dir: Directory to extract into
            
        Returns:
            Path to extracted file (or directory if multiple files)
            
        Raises:
            ProcessingError: If extraction fails
        """
        try:
            # Run 7z extraction
            await self._run_command([
                '7z',
                'x',  # extract with full paths
                str(archive_path),
                f'-o{extract_dir}',  # output directory
                '-y',  # yes to all prompts
            ])
            
            # Find extracted files
            extracted_files = [
                f for f in extract_dir.rglob('*')
                if f.is_file() and not f.name.startswith('.')
            ]
            
            if not extracted_files:
                raise ProcessingError(f"No files extracted from: {archive_path}")
            
            # Return single file or directory
            if len(extracted_files) == 1:
                return extracted_files[0]
            return extract_dir
        
        except FileNotFoundError:
            raise ProcessingError("7z command not found. Please install p7zip.")
        except Exception as e:
            raise ProcessingError(f"Failed to extract 7z: {e}") from e
    
    async def _extract_rar(self, archive_path: Path, extract_dir: Path) -> Path:
        """Extract RAR archive using unrar command.
        
        Args:
            archive_path: Path to RAR file
            extract_dir: Directory to extract into
            
        Returns:
            Path to extracted file (or directory if multiple files)
            
        Raises:
            ProcessingError: If extraction fails
        """
        try:
            # Run unrar extraction
            await self._run_command([
                'unrar',
                'x',  # extract with full paths
                str(archive_path),
                str(extract_dir),
                '-y',  # yes to all prompts
            ])
            
            # Find extracted files
            extracted_files = [
                f for f in extract_dir.rglob('*')
                if f.is_file() and not f.name.startswith('.')
            ]
            
            if not extracted_files:
                raise ProcessingError(f"No files extracted from: {archive_path}")
            
            # Return single file or directory
            if len(extracted_files) == 1:
                return extracted_files[0]
            return extract_dir
        
        except FileNotFoundError:
            raise ProcessingError("unrar command not found. Please install unrar.")
        except Exception as e:
            raise ProcessingError(f"Failed to extract RAR: {e}") from e


class BinCueToChd(ProcessingStage):
    """Convert .bin/.cue disc images to .chd format.
    
    CHD (Compressed Hunks of Data) is a compressed format that:
    - Saves significant disk space (50-70% compression)
    - Preserves all disc data (lossless)
    - Supported by most emulators (RetroArch, PCSX2, etc.)
    
    Requires chdman tool (from MAME).
    
    Example:
        >>> stage = BinCueToChd()
        >>> context = {'output_dir': Path('/roms/psx')}
        >>> output = await stage.process(Path('game.cue'), context)
        >>> print(output)
        /roms/psx/game.chd
    """
    
    def __init__(self, chdman_path: str = "chdman"):
        """Initialize CHD conversion stage.
        
        Args:
            chdman_path: Path to chdman executable (default: "chdman" in PATH)
        """
        self.chdman_path = chdman_path
    
    async def process(self, input_path: Path, context: dict) -> Path:
        """Convert disc image to CHD format.
        
        Args:
            input_path: Path to .cue file (with associated .bin file)
            context: Processing context with output_dir
            
        Returns:
            Path to created .chd file
            
        Raises:
            ProcessingError: If conversion fails
        """
        if not self.can_process(input_path):
            return input_path
        
        # Determine output path
        output_dir = context.get('output_dir', input_path.parent)
        output_file = output_dir / f"{input_path.stem}.chd"
        
        # Skip if CHD already exists
        if output_file.exists():
            return output_file
        
        try:
            # Run chdman to create CHD
            await self._run_command([
                self.chdman_path,
                "createcd",
                "-i", str(input_path),  # Input .cue file
                "-o", str(output_file),  # Output .chd file
            ])
            
            return output_file
        
        except FileNotFoundError:
            raise ProcessingError(
                f"chdman not found. Please install MAME tools.\n"
                f"Path: {self.chdman_path}"
            )
        except Exception as e:
            raise ProcessingError(f"Failed to convert to CHD: {e}") from e
    
    def can_process(self, input_path: Path) -> bool:
        """Check if input is a .cue file.
        
        Args:
            input_path: Path to check
            
        Returns:
            True if input is a .cue file
        """
        return input_path.suffix.lower() == '.cue'
    
    def configure(self, config: dict) -> None:
        """Configure CHD conversion.
        
        Args:
            config: Configuration dict with optional 'chdman_path'
        """
        if 'chdman_path' in config:
            self.chdman_path = config['chdman_path']


class CreateM3uPlaylist(ProcessingStage):
    """Create .m3u playlist for multi-disc games.
    
    M3U playlists allow emulators to:
    - Show multi-disc game as single entry
    - Support disc swapping during gameplay
    - Maintain game saves across discs
    
    Example:
        >>> stage = CreateM3uPlaylist()
        >>> context = {
        ...     'rom': Rom(title="Final Fantasy VII", disc_number=1, disc_total=3),
        ...     'output_dir': Path('/roms/psx'),
        ... }
        >>> output = await stage.process(Path('FF7_Disc1.chd'), context)
        >>> print(output)
        /roms/psx/Final Fantasy VII.m3u
    """
    
    async def process(self, input_path: Path, context: dict) -> Path:
        """Create M3U playlist for multi-disc game.
        
        Args:
            input_path: Path to first disc file
            context: Processing context with rom and output_dir
            
        Returns:
            Path to created .m3u file, or input_path if single disc
            
        Raises:
            ProcessingError: If playlist creation fails
        """
        rom = context.get('rom')
        
        # Only create M3U for multi-disc games
        if not rom or not rom.disc_total or rom.disc_total <= 1:
            return input_path
        
        output_dir = context.get('output_dir', input_path.parent)
        
        # Create M3U filename (without disc number)
        m3u_filename = f"{rom.name}.m3u"
        m3u_file = output_dir / m3u_filename
        
        # Find all disc files for this game
        disc_files = self._find_disc_files(rom, output_dir, input_path.suffix)
        
        if not disc_files:
            raise ProcessingError(f"No disc files found for {rom.name}")
        
        # Create M3U playlist
        try:
            with m3u_file.open('w') as f:
                for disc_file in sorted(disc_files):
                    # Write relative filename
                    f.write(f"{disc_file.name}\n")
            
            # Store disc files in context
            context['disc_files'] = disc_files
            context['m3u_created'] = True
            
            return m3u_file
        
        except Exception as e:
            raise ProcessingError(f"Failed to create M3U playlist: {e}") from e
    
    def can_process(self, input_path: Path) -> bool:
        """Check if M3U creation is possible.
        
        Always returns True - the process() method checks rom.disc_total.
        
        Args:
            input_path: Path to check
            
        Returns:
            True (actual check happens in process())
        """
        return True
    
    def _find_disc_files(
        self,
        rom: Rom,
        output_dir: Path,
        extension: str
    ) -> list[Path]:
        """Find all disc files for a game.
        
        Args:
            rom: ROM metadata with title
            output_dir: Directory containing disc files
            extension: File extension to look for (.chd, .cue, etc.)
            
        Returns:
            List of disc file paths, sorted by disc number
        """
        disc_files = []
        
        # Look for files matching the game title pattern
        pattern = f"{rom.name}*{extension}"
        for file_path in output_dir.glob(pattern):
            disc_files.append(file_path)
        
        return disc_files

