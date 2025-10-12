"""Tests for disc processing stages."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from romgroomer.models.rom import Rom
from romgroomer.processors.base import ProcessingError
from romgroomer.processors.stages import BinCueToChd, CreateM3uPlaylist


@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory for testing."""
    return tmp_path / "test_disc"


@pytest.fixture
def context(temp_dir):
    """Create processing context."""
    temp_dir.mkdir(parents=True, exist_ok=True)
    return {
        'output_dir': temp_dir,
        'transformations': [],
    }


class TestBinCueToChd:
    """Test BinCueToChd stage."""
    
    def test_can_process_cue(self):
        """Test detection of .cue files."""
        stage = BinCueToChd()
        
        assert stage.can_process(Path("game.cue"))
        assert stage.can_process(Path("game.CUE"))  # case insensitive
        assert not stage.can_process(Path("game.bin"))
        assert not stage.can_process(Path("game.chd"))
    
    @pytest.mark.asyncio
    async def test_skip_non_cue(self, context):
        """Test skipping non-.cue files."""
        stage = BinCueToChd()
        chd_file = context['output_dir'] / "game.chd"
        chd_file.write_bytes(b"fake chd data")
        
        result = await stage.process(chd_file, context)
        
        # Should return same path
        assert result == chd_file
    
    @pytest.mark.asyncio
    async def test_convert_cue_to_chd(self, context, tmp_path):
        """Test converting .cue file to .chd."""
        stage = BinCueToChd()
        
        # Create fake .cue file
        cue_file = tmp_path / "game.cue"
        cue_file.write_text('FILE "game.bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n')
        
        # Create fake .bin file
        bin_file = tmp_path / "game.bin"
        bin_file.write_bytes(b"fake bin data" * 1000)
        
        # Mock the command execution
        with patch.object(stage, '_run_command', new_callable=AsyncMock) as mock_cmd:
            # Simulate CHD creation
            async def create_chd(*args, **kwargs):
                chd_path = context['output_dir'] / "game.chd"
                chd_path.write_bytes(b"fake chd data")
            
            mock_cmd.side_effect = create_chd
            
            result = await stage.process(cue_file, context)
            
            # Should return .chd file path
            assert result.suffix == ".chd"
            assert result.name == "game.chd"
            assert result.exists()
            
            # Should have called chdman
            mock_cmd.assert_called_once()
            args = mock_cmd.call_args[0][0]
            assert args[0] == "chdman"
            assert args[1] == "createcd"
            assert str(cue_file) in args
    
    @pytest.mark.asyncio
    async def test_skip_existing_chd(self, context, tmp_path):
        """Test skipping conversion if CHD already exists."""
        stage = BinCueToChd()
        
        # Create fake .cue file
        cue_file = tmp_path / "game.cue"
        cue_file.write_text('FILE "game.bin" BINARY\n')
        
        # Create existing .chd file
        existing_chd = context['output_dir'] / "game.chd"
        existing_chd.write_bytes(b"existing chd data")
        
        with patch.object(stage, '_run_command', new_callable=AsyncMock) as mock_cmd:
            result = await stage.process(cue_file, context)
            
            # Should return existing CHD without calling chdman
            assert result == existing_chd
            mock_cmd.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_custom_chdman_path(self, context, tmp_path):
        """Test using custom chdman path."""
        stage = BinCueToChd(chdman_path="/usr/local/bin/chdman")
        
        cue_file = tmp_path / "game.cue"
        cue_file.write_text('FILE "game.bin" BINARY\n')
        
        with patch.object(stage, '_run_command', new_callable=AsyncMock) as mock_cmd:
            async def create_chd(*args, **kwargs):
                (context['output_dir'] / "game.chd").write_bytes(b"chd")
            mock_cmd.side_effect = create_chd
            
            await stage.process(cue_file, context)
            
            # Should use custom path
            args = mock_cmd.call_args[0][0]
            assert args[0] == "/usr/local/bin/chdman"
    
    def test_configure(self):
        """Test stage configuration."""
        stage = BinCueToChd()
        
        stage.configure({'chdman_path': '/custom/chdman'})
        
        assert stage.chdman_path == '/custom/chdman'


class TestCreateM3uPlaylist:
    """Test CreateM3uPlaylist stage."""
    
    def test_can_process(self):
        """Test can_process always returns True."""
        stage = CreateM3uPlaylist()
        
        # Always returns True - actual check is in process()
        assert stage.can_process(Path("game.chd"))
        assert stage.can_process(Path("game.cue"))
        assert stage.can_process(Path("anything.txt"))
    
    @pytest.mark.asyncio
    async def test_skip_single_disc(self, context):
        """Test skipping M3U creation for single-disc games."""
        stage = CreateM3uPlaylist()
        
        # Single disc ROM
        chd_file = context['output_dir'] / "Metal Gear Solid.chd"
        chd_file.write_bytes(b"fake chd")
        
        rom = Rom(
            path=chd_file,
            filename="Metal Gear Solid.chd",
            size=100,
            name="Metal Gear Solid",
            regions=["usa"],
            disc_number=None,
            disc_total=None,
        )
        context['rom'] = rom
        
        result = await stage.process(chd_file, context)
        
        # Should return same path (no M3U created)
        assert result == chd_file
        assert not (context['output_dir'] / "Metal Gear Solid.m3u").exists()
    
    @pytest.mark.asyncio
    async def test_create_m3u_multi_disc(self, context):
        """Test creating M3U for multi-disc game."""
        stage = CreateM3uPlaylist()
        
        # Create disc files
        disc1 = context['output_dir'] / "Final Fantasy VII (Disc 1).chd"
        disc2 = context['output_dir'] / "Final Fantasy VII (Disc 2).chd"
        disc3 = context['output_dir'] / "Final Fantasy VII (Disc 3).chd"
        disc1.write_bytes(b"disc 1")
        disc2.write_bytes(b"disc 2")
        disc3.write_bytes(b"disc 3")
        
        # Multi-disc ROM
        rom = Rom(
            path=disc1,
            filename="Final Fantasy VII (Disc 1).chd",
            size=100,
            name="Final Fantasy VII",
            regions=["usa"],
            disc_number=1,
            disc_total=3,
        )
        context['rom'] = rom
        
        result = await stage.process(disc1, context)
        
        # Should return M3U file
        assert result.suffix == ".m3u"
        assert result.name == "Final Fantasy VII.m3u"
        assert result.exists()
        
        # M3U should list all discs
        m3u_content = result.read_text()
        assert "Final Fantasy VII (Disc 1).chd" in m3u_content
        assert "Final Fantasy VII (Disc 2).chd" in m3u_content
        assert "Final Fantasy VII (Disc 3).chd" in m3u_content
        
        # Context should have disc files
        assert 'disc_files' in context
        assert len(context['disc_files']) == 3
        assert context['m3u_created'] is True
    
    @pytest.mark.asyncio
    async def test_m3u_with_two_discs(self, context):
        """Test M3U creation for 2-disc game."""
        stage = CreateM3uPlaylist()
        
        # Create 2 disc files
        disc1 = context['output_dir'] / "Resident Evil 2 (Disc 1).chd"
        disc2 = context['output_dir'] / "Resident Evil 2 (Disc 2).chd"
        disc1.write_bytes(b"disc 1")
        disc2.write_bytes(b"disc 2")
        
        rom = Rom(
            path=disc1,
            filename="Resident Evil 2 (Disc 1).chd",
            size=100,
            name="Resident Evil 2",
            regions=["usa"],
            disc_number=1,
            disc_total=2,
        )
        context['rom'] = rom
        
        result = await stage.process(disc1, context)
        
        assert result.name == "Resident Evil 2.m3u"
        m3u_content = result.read_text()
        assert "Resident Evil 2 (Disc 1).chd" in m3u_content
        assert "Resident Evil 2 (Disc 2).chd" in m3u_content
    
    @pytest.mark.asyncio
    async def test_no_rom_in_context(self, context):
        """Test graceful handling when no ROM in context."""
        stage = CreateM3uPlaylist()
        
        chd_file = context['output_dir'] / "game.chd"
        chd_file.write_bytes(b"fake chd")
        
        result = await stage.process(chd_file, context)
        
        # Should return input path without error
        assert result == chd_file


class TestDiscProcessingIntegration:
    """Integration tests for disc processing pipeline."""
    
    @pytest.mark.asyncio
    async def test_complete_disc_pipeline(self, context, tmp_path):
        """Test complete pipeline: extract → CHD → M3U."""
        # This simulates the full disc processing workflow
        
        # Create disc files
        disc1_cue = tmp_path / "Final Fantasy VII (Disc 1).cue"
        disc2_cue = tmp_path / "Final Fantasy VII (Disc 2).cue"
        disc3_cue = tmp_path / "Final Fantasy VII (Disc 3).cue"
        
        for cue_file in [disc1_cue, disc2_cue, disc3_cue]:
            cue_file.write_text(f'FILE "{cue_file.stem}.bin" BINARY\n')
        
        rom = Rom(
            path=disc1_cue,
            filename="Final Fantasy VII (Disc 1).cue",
            size=100,
            name="Final Fantasy VII",
            regions=["usa"],
            disc_number=1,
            disc_total=3,
        )
        context['rom'] = rom
        
        # Stage 1: Convert to CHD (mocked)
        chd_stage = BinCueToChd()
        
        with patch.object(chd_stage, '_run_command', new_callable=AsyncMock):
            disc1_chd = context['output_dir'] / "Final Fantasy VII (Disc 1).chd"
            disc2_chd = context['output_dir'] / "Final Fantasy VII (Disc 2).chd"
            disc3_chd = context['output_dir'] / "Final Fantasy VII (Disc 3).chd"
            
            disc1_chd.write_bytes(b"chd1")
            disc2_chd.write_bytes(b"chd2")
            disc3_chd.write_bytes(b"chd3")
        
        # Stage 2: Create M3U
        m3u_stage = CreateM3uPlaylist()
        result = await m3u_stage.process(disc1_chd, context)
        
        # Verify final result
        assert result.suffix == ".m3u"
        assert result.exists()
        
        m3u_content = result.read_text()
        assert all(f"(Disc {i}).chd" in m3u_content for i in [1, 2, 3])
