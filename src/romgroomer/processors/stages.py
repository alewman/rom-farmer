"""Processing stages for ROM transformation."""

import zipfile
from pathlib import Path
from typing import Optional

from .base import ProcessingError, ProcessingStage


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
