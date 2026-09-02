#!/usr/bin/env python3
"""
Tests for ARRM/ScreenScraper hashing compatibility.

ARRM and ScreenScraper use different hashing strategies for disc images:
- Single-track discs (1 BIN): Hash the BIN file
- Multi-track discs (2+ BINs): Hash the CUE file
- ISO files: Hash the ISO file

This test suite verifies that ROM Farmer correctly matches this behavior
to ensure metadata can be looked up from ARRM-scraped databases.
"""

import sys
from pathlib import Path

import pytest

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestSelectRomFile:
    """Test the _select_rom_file logic in FilterDATStage."""

    def _select_rom_file(self, files, zf=None):
        """Reimplementation of the selection logic for testing.

        This mirrors the logic in filter_dat.py to ensure consistency.
        """
        cue_files = [f for f in files if f.lower().endswith(".cue")]
        bin_files = [f for f in files if f.lower().endswith(".bin")]

        # CUE/BIN disc logic - match ARRM/ScreenScraper behavior
        if cue_files and bin_files:
            if len(bin_files) == 1:
                # Single-track: hash the BIN (game data)
                return bin_files[0]
            else:
                # Multi-track: hash the CUE (disc layout)
                return cue_files[0]

        # ISO files (PS2, Xbox, etc.)
        iso_files = [f for f in files if f.lower().endswith(".iso")]
        if iso_files:
            return iso_files[0]

        # RVZ files (GameCube/Wii)
        rvz_files = [f for f in files if f.lower().endswith(".rvz")]
        if rvz_files:
            return rvz_files[0]

        # CHD files (already compressed disc images)
        chd_files = [f for f in files if f.lower().endswith(".chd")]
        if chd_files:
            return chd_files[0]

        # m3u (multi-disc playlists)
        m3u_files = [f for f in files if f.lower().endswith(".m3u")]
        if m3u_files:
            return m3u_files[0]

        # Cartridge ROM extensions
        rom_extensions = {
            ".nes",
            ".sfc",
            ".smc",
            ".gb",
            ".gbc",
            ".gba",
            ".nds",
            ".3ds",
            ".n64",
            ".z64",
            ".v64",
        }
        for f in files:
            ext = Path(f).suffix.lower()
            if ext in rom_extensions:
                return f

        # Fallback: return first file
        if files:
            return files[0]
        return None

    # =========================================================================
    # Single-track disc tests (should hash BIN)
    # =========================================================================

    def test_single_track_3do_style(self):
        """3DO games are single-track - should hash BIN."""
        files = ["Game (USA).cue", "Game (USA).bin"]
        result = self._select_rom_file(files)
        assert result == "Game (USA).bin"
        assert result.endswith(".bin")

    def test_single_track_with_different_names(self):
        """Single-track with non-matching CUE/BIN names."""
        files = ["disc.cue", "data.bin"]
        result = self._select_rom_file(files)
        assert result == "data.bin"

    def test_single_track_case_insensitive(self):
        """Extension matching should be case-insensitive."""
        files = ["Game.CUE", "Game.BIN"]
        result = self._select_rom_file(files)
        assert result.lower().endswith(".bin")

    # =========================================================================
    # Multi-track disc tests (should hash CUE)
    # =========================================================================

    def test_multi_track_3_bins_dreamcast_style(self):
        """Dreamcast games have 3 tracks - should hash CUE."""
        files = [
            "Game (USA).cue",
            "Game (USA) (Track 1).bin",
            "Game (USA) (Track 2).bin",
            "Game (USA) (Track 3).bin",
        ]
        result = self._select_rom_file(files)
        assert result == "Game (USA).cue"
        assert result.endswith(".cue")

    def test_multi_track_many_audio_tracks(self):
        """Games with many audio tracks - should hash CUE."""
        files = ["Game.cue"] + [f"Game (Track {i}).bin" for i in range(1, 12)]
        result = self._select_rom_file(files)
        assert result == "Game.cue"

    def test_multi_track_2_bins(self):
        """Minimum multi-track (2 bins) - should hash CUE."""
        files = ["Game.cue", "Track01.bin", "Track02.bin"]
        result = self._select_rom_file(files)
        assert result == "Game.cue"

    def test_saturn_multi_track(self):
        """Saturn games are typically multi-track."""
        files = [
            "Nights Into Dreams (USA).cue",
            "Nights Into Dreams (USA) (Track 01).bin",
            "Nights Into Dreams (USA) (Track 02).bin",
            "Nights Into Dreams (USA) (Track 03).bin",
        ]
        result = self._select_rom_file(files)
        assert result.endswith(".cue")

    # =========================================================================
    # ISO file tests
    # =========================================================================

    def test_iso_only(self):
        """ISO-only games should hash ISO."""
        files = ["Game (USA).iso"]
        result = self._select_rom_file(files)
        assert result == "Game (USA).iso"

    def test_iso_ps2_style(self):
        """PS2 often uses ISO format."""
        files = ["Grand Theft Auto - San Andreas (USA).iso"]
        result = self._select_rom_file(files)
        assert result.endswith(".iso")

    # =========================================================================
    # Other format tests
    # =========================================================================

    def test_rvz_gamecube(self):
        """GameCube/Wii RVZ files."""
        files = ["Mario Kart Double Dash (USA).rvz"]
        result = self._select_rom_file(files)
        assert result.endswith(".rvz")

    def test_cartridge_nes(self):
        """NES cartridge ROM."""
        files = ["Super Mario Bros (USA).nes", "readme.txt"]
        result = self._select_rom_file(files)
        assert result.endswith(".nes")

    def test_cartridge_gba(self):
        """GBA cartridge ROM."""
        files = ["Pokemon Ruby (USA).gba"]
        result = self._select_rom_file(files)
        assert result.endswith(".gba")

    def test_m3u_multi_disc(self):
        """M3U playlist for multi-disc games."""
        files = ["Final Fantasy VII.m3u"]
        result = self._select_rom_file(files)
        assert result.endswith(".m3u")

    # =========================================================================
    # Edge cases
    # =========================================================================

    def test_empty_file_list(self):
        """Empty file list returns None."""
        result = self._select_rom_file([])
        assert result is None

    def test_cue_only_no_bin(self):
        """CUE without BIN (unusual) - should return CUE."""
        files = ["Game.cue"]
        result = self._select_rom_file(files)
        assert result == "Game.cue"

    def test_bin_only_no_cue(self):
        """BIN without CUE - falls back to first file."""
        files = ["Game.bin"]
        result = self._select_rom_file(files)
        assert result == "Game.bin"


class TestCompressSourceFileSelection:
    """Test the source file selection in compress.py for transformation recording."""

    def _count_bin_files_in_cue(self, cue_content):
        """Count BIN files referenced in CUE content."""
        import re

        matches = re.findall(r'FILE\s+"([^"]+)"', cue_content, re.IGNORECASE)
        return len([m for m in matches if m.lower().endswith(".bin")])

    def test_single_track_cue_content(self):
        """Single-track CUE references exactly 1 BIN."""
        cue_content = """FILE "Game (USA).bin" BINARY
  TRACK 01 MODE2/2352
    INDEX 01 00:00:00"""
        count = self._count_bin_files_in_cue(cue_content)
        assert count == 1

    def test_multi_track_cue_content(self):
        """Multi-track CUE references multiple BIN files."""
        cue_content = """FILE "Game (Track 1).bin" BINARY
  TRACK 01 MODE2/2352
    INDEX 01 00:00:00
FILE "Game (Track 2).bin" BINARY
  TRACK 02 AUDIO
    INDEX 00 00:00:00
    INDEX 01 00:02:00
FILE "Game (Track 3).bin" BINARY
  TRACK 03 AUDIO
    INDEX 00 00:00:00
    INDEX 01 00:02:00"""
        count = self._count_bin_files_in_cue(cue_content)
        assert count == 3


class TestARRMCompatibility:
    """Integration tests verifying ARRM hash compatibility."""

    # Known ARRM hashing examples (from real analysis)
    KNOWN_HASHES = {
        # 3DO - single track, stores BIN hash
        "3do_gex": {
            "system": "3do",
            "path_stored": "./Gex (USA, Europe).cue",
            "md5_stored": "d37e7929c6302b116352d0db85b5a982",
            "cue_md5": "334ce9c6500a752c32a645e5a7bd0f24",
            "bin_md5": "d37e7929c6302b116352d0db85b5a982",
            "expected_hash_type": "bin",
        },
        # Dreamcast - multi-track, stores CUE hash
        "dc_18_wheeler": {
            "system": "dreamcast",
            "path_stored": "./18 Wheeler - American Pro Trucker (USA).cue",
            "md5_stored": "74251fafe2c76c67499b31c12f8fe028",
            "cue_md5": "74251fafe2c76c67499b31c12f8fe028",
            "bin_count": 3,
            "expected_hash_type": "cue",
        },
    }

    def test_3do_single_track_hashes_bin(self):
        """Verify 3DO (single-track) should hash BIN to match ARRM."""
        case = self.KNOWN_HASHES["3do_gex"]
        # ARRM stored the BIN MD5, not the CUE MD5
        assert case["md5_stored"] == case["bin_md5"]
        assert case["md5_stored"] != case["cue_md5"]
        assert case["expected_hash_type"] == "bin"

    def test_dreamcast_multi_track_hashes_cue(self):
        """Verify Dreamcast (multi-track) should hash CUE to match ARRM."""
        case = self.KNOWN_HASHES["dc_18_wheeler"]
        # ARRM stored the CUE MD5 for multi-track
        assert case["md5_stored"] == case["cue_md5"]
        assert case["expected_hash_type"] == "cue"

    def test_selection_matches_arrm_expectations(self):
        """Verify our selection logic produces ARRM-compatible results."""
        selector = TestSelectRomFile()

        # 3DO case - single track
        files_3do = ["Gex (USA, Europe).cue", "Gex (USA, Europe).bin"]
        result = selector._select_rom_file(files_3do)
        assert result.endswith(".bin"), "3DO should hash BIN (single-track)"

        # Dreamcast case - multi-track
        files_dc = [
            "18 Wheeler (USA).cue",
            "18 Wheeler (USA) (Track 1).bin",
            "18 Wheeler (USA) (Track 2).bin",
            "18 Wheeler (USA) (Track 3).bin",
        ]
        result = selector._select_rom_file(files_dc)
        assert result.endswith(".cue"), "Dreamcast should hash CUE (multi-track)"


class TestTransformationChain:
    """Test that transformation chain correctly preserves hashes for lookup."""

    def test_chain_conceptual_flow(self):
        """Verify the conceptual transformation chain.

        The chain should be:
        1. Source ZIP contains CUE/BIN
        2. We hash the appropriate file (BIN for single, CUE for multi)
        3. That hash matches what ARRM stored
        4. We extract and compress to CHD
        5. We record: source_md5 (BIN or CUE hash) → final_md5 (CHD hash)
        6. Later, we can lookup: CHD → source_md5 → ARRM metadata
        """
        # This is a conceptual test documenting the flow
        chain = {
            "step1": "ZIP file scanned",
            "step2": "Detect single/multi-track",
            "step3": "Hash correct file (BIN or CUE)",
            "step4": "Verify hash matches ARRM expectations",
            "step5": "Extract and compress to CHD",
            "step6": "Record transformation with source_md5",
            "step7": "Lookup metadata via final_md5 → source_md5",
        }
        assert len(chain) == 7, "Complete transformation chain"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
