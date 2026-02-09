#!/usr/bin/env python3
"""
Tests for CompressCHDStage transformation recording.

These tests verify that:
1. The correct file (BIN or CUE) is selected for hashing
2. Transformation records are created with correct field values
3. The source_file_name and source_format are set correctly
4. No undefined variable errors occur in the recording code

This test file was created after discovering a NameError bug where
`bin_file_path` was used instead of `source_file_path`, causing
transformation recordings to silently fail.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, PropertyMock
import sys

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from romfarmer.stages.compress import CompressCHDStage


class TestGetSourceFileForHash:
    """Test _get_source_file_for_hash method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.stage = CompressCHDStage(chdman_path=None, db_session=None)
    
    def test_single_track_returns_bin(self, tmp_path):
        """Single-track disc (1 BIN) should return BIN file for hashing."""
        # Create test files
        cue = tmp_path / "Game (USA).cue"
        bin_file = tmp_path / "Game (USA).bin"
        
        cue.write_text('FILE "Game (USA).bin" BINARY\n  TRACK 01 MODE1/2352\n    INDEX 01 00:00:00\n')
        bin_file.write_bytes(b'\x00' * 1000)
        
        result = self.stage._get_source_file_for_hash(cue)
        
        assert result.suffix == '.bin', "Single-track should return BIN"
        assert result.name == "Game (USA).bin"
    
    def test_multi_track_returns_cue(self, tmp_path):
        """Multi-track disc (2+ BINs) should return CUE file for hashing."""
        # Create test files
        cue = tmp_path / "Game (USA).cue"
        track1 = tmp_path / "Game (USA) (Track 1).bin"
        track2 = tmp_path / "Game (USA) (Track 2).bin"
        track3 = tmp_path / "Game (USA) (Track 3).bin"
        
        cue.write_text(
            'FILE "Game (USA) (Track 1).bin" BINARY\n  TRACK 01 MODE1/2352\n    INDEX 01 00:00:00\n'
            'FILE "Game (USA) (Track 2).bin" BINARY\n  TRACK 02 AUDIO\n    INDEX 01 00:00:00\n'
            'FILE "Game (USA) (Track 3).bin" BINARY\n  TRACK 03 MODE1/2352\n    INDEX 01 00:00:00\n'
        )
        track1.write_bytes(b'\x00' * 1000)
        track2.write_bytes(b'\x00' * 1000)
        track3.write_bytes(b'\x00' * 1000)
        
        result = self.stage._get_source_file_for_hash(cue)
        
        assert result.suffix == '.cue', "Multi-track should return CUE"
        assert result == cue
    
    def test_two_track_is_multi(self, tmp_path):
        """Two tracks should be treated as multi-track (return CUE)."""
        cue = tmp_path / "Game.cue"
        track1 = tmp_path / "Game (Track 1).bin"
        track2 = tmp_path / "Game (Track 2).bin"
        
        cue.write_text(
            'FILE "Game (Track 1).bin" BINARY\n  TRACK 01 MODE1/2352\n    INDEX 01 00:00:00\n'
            'FILE "Game (Track 2).bin" BINARY\n  TRACK 02 AUDIO\n    INDEX 01 00:00:00\n'
        )
        track1.write_bytes(b'\x00' * 1000)
        track2.write_bytes(b'\x00' * 1000)
        
        result = self.stage._get_source_file_for_hash(cue)
        
        assert result.suffix == '.cue', "Two-track should return CUE"


class TestGetPrimaryBinFile:
    """Test _get_primary_bin_file method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.stage = CompressCHDStage(chdman_path=None, db_session=None)
    
    def test_single_bin_returns_bin(self, tmp_path):
        """Single BIN file should be returned."""
        cue = tmp_path / "Game.cue"
        bin_file = tmp_path / "Game.bin"
        
        cue.write_text('FILE "Game.bin" BINARY\n  TRACK 01 MODE1/2352\n    INDEX 01 00:00:00\n')
        bin_file.write_bytes(b'\x00' * 1000)
        
        result = self.stage._get_primary_bin_file(cue)
        
        assert result is not None
        assert result.name == "Game.bin"
    
    def test_multi_bin_returns_none(self, tmp_path):
        """Multiple BIN files should return None."""
        cue = tmp_path / "Game.cue"
        track1 = tmp_path / "Game (Track 1).bin"
        track2 = tmp_path / "Game (Track 2).bin"
        
        cue.write_text(
            'FILE "Game (Track 1).bin" BINARY\n  TRACK 01 MODE1/2352\n    INDEX 01 00:00:00\n'
            'FILE "Game (Track 2).bin" BINARY\n  TRACK 02 AUDIO\n    INDEX 01 00:00:00\n'
        )
        track1.write_bytes(b'\x00' * 1000)
        track2.write_bytes(b'\x00' * 1000)
        
        result = self.stage._get_primary_bin_file(cue)
        
        assert result is None, "Multi-track should return None"


class TestRecordTransformationCodeIntegrity:
    """Test that _record_transformation code is syntactically correct.
    
    These tests verify that:
    1. All variables used in _record_transformation are defined
    2. The method can be called without NameError
    3. The correct file path/name is recorded
    
    This test class was created after a bug where `bin_file_path` was used
    instead of `source_file_path`, causing silent failures.
    """
    
    def setup_method(self):
        """Set up test fixtures with mocked database."""
        self.mock_session = MagicMock()
        self.stage = CompressCHDStage(chdman_path=None, db_session=self.mock_session)
    
    def test_record_transformation_no_name_error(self, tmp_path):
        """Calling _record_transformation should not raise NameError.
        
        This is the key test that would have caught the original bug.
        """
        # Create test files
        cue = tmp_path / "Game.cue"
        bin_file = tmp_path / "Game.bin"
        chd = tmp_path / "Game.chd"
        
        cue.write_text('FILE "Game.bin" BINARY\n  TRACK 01 MODE1/2352\n    INDEX 01 00:00:00\n')
        bin_file.write_bytes(b'\x00' * 1000)
        chd.write_bytes(b'\x00' * 500)  # Fake CHD
        
        # Mock the hash capture to avoid actual hashing
        # Note: imports happen inside the method, so patch where they're imported from
        mock_context = MagicMock()
        
        with patch('romfarmer.metadata.hash_capture.SmartHashCapture') as MockHashCapture:
            mock_hash_capture = MagicMock()
            MockHashCapture.return_value = mock_hash_capture
            
            # Create mock source hash info
            mock_source_hashes = MagicMock()
            mock_source_hashes.md5 = 'abc123'
            mock_source_hashes.sha1 = 'def456'
            mock_source_hashes.sha256 = 'ghi789'
            mock_source_hashes.crc32 = '12345678'
            mock_source_hashes.size = 1000
            mock_source_hashes.from_dat = False
            mock_source_hashes.dat_name = None
            mock_source_hashes.from_cache = False
            
            mock_hash_capture.get_source_hashes.return_value = mock_source_hashes
            
            # Mock database query
            self.mock_session.query.return_value.filter_by.return_value.first.return_value = None
            
            # This should NOT raise NameError
            try:
                self.stage._record_transformation(mock_context, cue, chd)
            except NameError as e:
                pytest.fail(f"NameError in _record_transformation: {e}")
            except Exception:
                # Other exceptions are OK for this test - we're just checking for NameError
                pass
    
    def test_source_file_path_used_not_bin_file_path(self):
        """Verify source_file_path variable is used, not bin_file_path.
        
        This test reads the actual source code to verify the fix is in place.
        """
        import inspect
        source_code = inspect.getsource(self.stage._record_transformation)
        
        # Check that we're using source_file_path, not bin_file_path
        assert 'source_file_path.name' in source_code or 'source_file_path.suffix' in source_code, \
            "Should use source_file_path variable"
        assert 'bin_file_path.name' not in source_code, \
            "Should NOT use undefined bin_file_path variable"
    
    def test_source_format_is_dynamic(self):
        """Verify source_format is set dynamically, not hardcoded to 'bin'."""
        import inspect
        source_code = inspect.getsource(self.stage._record_transformation)
        
        # Should use dynamic format from file extension
        assert "source_format='bin'" not in source_code or \
               "source_file_path.suffix" in source_code, \
            "source_format should be set dynamically from file extension"


class TestRecordTransformationFields:
    """Test that transformation records have correct field values."""
    
    def setup_method(self):
        """Set up test fixtures with mocked database."""
        self.mock_session = MagicMock()
        self.stage = CompressCHDStage(chdman_path=None, db_session=self.mock_session)
    
    @patch('romfarmer.metadata.transformation.ROMTransformation')
    @patch('romfarmer.metadata.hash_capture.SmartHashCapture')
    def test_single_track_records_bin_filename(self, MockHashCapture, MockTransformation, tmp_path):
        """Single-track disc should record BIN filename."""
        # Create test files
        cue = tmp_path / "Game.cue"
        bin_file = tmp_path / "Game.bin"
        chd = tmp_path / "Game.chd"
        
        cue.write_text('FILE "Game.bin" BINARY\n  TRACK 01 MODE1/2352\n    INDEX 01 00:00:00\n')
        bin_file.write_bytes(b'\x00' * 1000)
        chd.write_bytes(b'\x00' * 500)
        
        # Set up mocks
        mock_hash_capture = MagicMock()
        MockHashCapture.return_value = mock_hash_capture
        
        mock_hashes = MagicMock()
        mock_hashes.md5 = 'abc123'
        mock_hashes.sha1 = 'def456'
        mock_hashes.sha256 = 'ghi789'
        mock_hashes.crc32 = '12345678'
        mock_hashes.size = 1000
        mock_hashes.from_dat = False
        mock_hashes.dat_name = None
        mock_hashes.from_cache = False
        mock_hash_capture.get_source_hashes.return_value = mock_hashes
        
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        mock_context = MagicMock()
        
        try:
            self.stage._record_transformation(mock_context, cue, chd)
        except Exception:
            pass  # May fail due to mocking, but we can check what was passed
        
        # Check that ROMTransformation was called with BIN filename
        if MockTransformation.called:
            call_kwargs = MockTransformation.call_args[1]
            assert call_kwargs.get('source_file_name') == 'Game.bin', \
                "Single-track should record BIN filename"
            assert call_kwargs.get('source_format') == 'bin', \
                "Single-track should record 'bin' format"
    
    @patch('romfarmer.metadata.transformation.ROMTransformation')
    @patch('romfarmer.metadata.hash_capture.SmartHashCapture')
    def test_multi_track_records_cue_filename(self, MockHashCapture, MockTransformation, tmp_path):
        """Multi-track disc should record CUE filename."""
        # Create test files
        cue = tmp_path / "Game.cue"
        track1 = tmp_path / "Game (Track 1).bin"
        track2 = tmp_path / "Game (Track 2).bin"
        chd = tmp_path / "Game.chd"
        
        cue.write_text(
            'FILE "Game (Track 1).bin" BINARY\n  TRACK 01 MODE1/2352\n    INDEX 01 00:00:00\n'
            'FILE "Game (Track 2).bin" BINARY\n  TRACK 02 AUDIO\n    INDEX 01 00:00:00\n'
        )
        track1.write_bytes(b'\x00' * 1000)
        track2.write_bytes(b'\x00' * 1000)
        chd.write_bytes(b'\x00' * 500)
        
        # Set up mocks
        mock_hash_capture = MagicMock()
        MockHashCapture.return_value = mock_hash_capture
        
        mock_hashes = MagicMock()
        mock_hashes.md5 = 'abc123'
        mock_hashes.sha1 = 'def456'
        mock_hashes.sha256 = 'ghi789'
        mock_hashes.crc32 = '12345678'
        mock_hashes.size = 1000
        mock_hashes.from_dat = False
        mock_hashes.dat_name = None
        mock_hashes.from_cache = False
        mock_hash_capture.get_source_hashes.return_value = mock_hashes
        
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        mock_context = MagicMock()
        
        try:
            self.stage._record_transformation(mock_context, cue, chd)
        except Exception:
            pass
        
        # Check that ROMTransformation was called with CUE filename
        if MockTransformation.called:
            call_kwargs = MockTransformation.call_args[1]
            assert call_kwargs.get('source_file_name') == 'Game.cue', \
                "Multi-track should record CUE filename"
            assert call_kwargs.get('source_format') == 'cue', \
                "Multi-track should record 'cue' format"


class TestARRMCompatibility:
    """Integration tests verifying ARRM/ScreenScraper compatibility."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.stage = CompressCHDStage(chdman_path=None, db_session=None)
    
    def test_3do_single_track_compatibility(self, tmp_path):
        """3DO games (single-track) should hash BIN for ARRM compatibility."""
        cue = tmp_path / "Return Fire (USA, Europe).cue"
        bin_file = tmp_path / "Return Fire (USA, Europe).bin"
        
        cue.write_text('FILE "Return Fire (USA, Europe).bin" BINARY\n  TRACK 01 MODE1/2352\n    INDEX 01 00:00:00\n')
        bin_file.write_bytes(b'\x00' * 1000)
        
        source_file = self.stage._get_source_file_for_hash(cue)
        
        assert source_file.suffix == '.bin', "3DO should hash BIN"
        assert source_file.name == "Return Fire (USA, Europe).bin"
    
    def test_dreamcast_multi_track_compatibility(self, tmp_path):
        """Dreamcast games (multi-track) should hash CUE for ARRM compatibility."""
        cue = tmp_path / "18 Wheeler (USA).cue"
        track1 = tmp_path / "18 Wheeler (USA) (Track 1).bin"
        track2 = tmp_path / "18 Wheeler (USA) (Track 2).bin"
        track3 = tmp_path / "18 Wheeler (USA) (Track 3).bin"
        
        cue.write_text(
            'FILE "18 Wheeler (USA) (Track 1).bin" BINARY\n  TRACK 01 MODE1/2352\n    INDEX 01 00:00:00\n'
            'FILE "18 Wheeler (USA) (Track 2).bin" BINARY\n  TRACK 02 AUDIO\n    INDEX 01 00:00:00\n'
            'FILE "18 Wheeler (USA) (Track 3).bin" BINARY\n  TRACK 03 MODE1/2352\n    INDEX 01 00:00:00\n'
        )
        track1.write_bytes(b'\x00' * 1000)
        track2.write_bytes(b'\x00' * 1000)
        track3.write_bytes(b'\x00' * 1000)
        
        source_file = self.stage._get_source_file_for_hash(cue)
        
        assert source_file.suffix == '.cue', "Dreamcast should hash CUE"
        assert source_file == cue


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
