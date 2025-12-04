"""Tests for extraction stage."""

import zipfile
from pathlib import Path

import pytest

from romfarmer.processors.base import ProcessingError
from romfarmer.processors.stages import ExtractArchiveStage


@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory for testing."""
    return tmp_path / "test_extract"


@pytest.fixture
def context(temp_dir):
    """Create processing context."""
    temp_dir.mkdir(parents=True, exist_ok=True)
    return {
        'temp_dir': temp_dir,
        'transformations': [],
    }


class TestExtractArchiveStage:
    """Test ExtractArchiveStage."""
    
    def test_can_process_zip(self):
        """Test detection of ZIP files."""
        stage = ExtractArchiveStage()
        
        assert stage.can_process(Path("game.zip"))
        assert not stage.can_process(Path("game.nes"))
        assert not stage.can_process(Path("game.txt"))
    
    def test_can_process_7z(self):
        """Test detection of 7z files."""
        stage = ExtractArchiveStage()
        
        assert stage.can_process(Path("game.7z"))
    
    def test_can_process_rar(self):
        """Test detection of RAR files."""
        stage = ExtractArchiveStage()
        
        assert stage.can_process(Path("game.rar"))
    
    @pytest.mark.asyncio
    async def test_skip_non_archive(self, context):
        """Test skipping non-archive files."""
        stage = ExtractArchiveStage()
        rom_file = context['temp_dir'] / "game.nes"
        rom_file.write_bytes(b"fake rom data")
        
        result = await stage.process(rom_file, context)
        
        # Should return same path
        assert result == rom_file
    
    @pytest.mark.asyncio
    async def test_extract_single_file_zip(self, context, tmp_path):
        """Test extracting ZIP with single file."""
        stage = ExtractArchiveStage()
        
        # Create test ZIP
        zip_path = tmp_path / "game.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("game.nes", b"fake rom data")
        
        result = await stage.process(zip_path, context)
        
        # Should extract to temp_dir/game.nes
        assert result.name == "game.nes"
        assert result.exists()
        assert result.read_bytes() == b"fake rom data"
    
    @pytest.mark.asyncio
    async def test_extract_multi_file_zip(self, context, tmp_path):
        """Test extracting ZIP with multiple files."""
        stage = ExtractArchiveStage()
        
        # Create test ZIP with multiple files
        zip_path = tmp_path / "game.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("game.bin", b"fake bin data")
            zf.writestr("game.cue", b"fake cue data")
        
        result = await stage.process(zip_path, context)
        
        # Should return directory
        assert result.is_dir()
        assert (result / "game.bin").exists()
        assert (result / "game.cue").exists()
    
    @pytest.mark.asyncio
    async def test_extract_nested_zip(self, context, tmp_path):
        """Test extracting ZIP with nested directories."""
        stage = ExtractArchiveStage()
        
        # Create test ZIP with nested structure
        zip_path = tmp_path / "game.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("folder/game.nes", b"fake rom data")
        
        result = await stage.process(zip_path, context)
        
        # Should extract nested file
        assert result.name == "game.nes"
        assert result.exists()
    
    @pytest.mark.asyncio
    async def test_extract_empty_zip(self, context, tmp_path):
        """Test extracting empty ZIP raises error."""
        stage = ExtractArchiveStage()
        
        # Create empty ZIP
        zip_path = tmp_path / "empty.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            pass  # Empty archive
        
        with pytest.raises(ProcessingError, match="Archive is empty"):
            await stage.process(zip_path, context)
    
    @pytest.mark.asyncio
    async def test_extract_invalid_zip(self, context, tmp_path):
        """Test extracting invalid ZIP raises error."""
        stage = ExtractArchiveStage()
        
        # Create invalid ZIP file
        zip_path = tmp_path / "invalid.zip"
        zip_path.write_bytes(b"not a zip file")
        
        with pytest.raises(ProcessingError, match="Invalid ZIP file"):
            await stage.process(zip_path, context)
    
    @pytest.mark.asyncio
    async def test_custom_extract_dir(self, context, tmp_path):
        """Test using custom extraction directory."""
        custom_dir = tmp_path / "custom_extract"
        stage = ExtractArchiveStage(extract_dir=custom_dir)
        
        # Create test ZIP
        zip_path = tmp_path / "game.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("game.nes", b"fake rom data")
        
        result = await stage.process(zip_path, context)
        
        # Should extract to custom directory
        assert result.parent == custom_dir
        assert result.exists()


class TestExtractArchiveStageIntegration:
    """Integration tests for extraction stage."""
    
    @pytest.mark.asyncio
    async def test_extract_real_world_structure(self, context, tmp_path):
        """Test extracting realistic ROM archive."""
        stage = ExtractArchiveStage()
        
        # Create realistic PSX game structure
        zip_path = tmp_path / "Final Fantasy VII (USA) (Disc 1).zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("Final Fantasy VII (USA) (Disc 1).bin", b"fake bin data" * 1000)
            zf.writestr("Final Fantasy VII (USA) (Disc 1).cue", 
                       b'FILE "Final Fantasy VII (USA) (Disc 1).bin" BINARY\n'
                       b'  TRACK 01 MODE2/2352\n'
                       b'    INDEX 01 00:00:00\n')
        
        result = await stage.process(zip_path, context)
        
        # Should extract both files
        assert result.is_dir()
        bin_file = result / "Final Fantasy VII (USA) (Disc 1).bin"
        cue_file = result / "Final Fantasy VII (USA) (Disc 1).cue"
        assert bin_file.exists()
        assert cue_file.exists()
        assert b"fake bin data" in bin_file.read_bytes()
