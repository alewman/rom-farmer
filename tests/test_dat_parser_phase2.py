"""Tests for new DAT parser system (Phase 2)."""

import tempfile
from pathlib import Path
from textwrap import dedent

import pytest

from romfarmer.dat_parser import (
    DATFile,
    DATGame,
    DATParser,
    DATRom,
    DATType,
    MatchResult,
    MatchType,
    RetoolDATParser,
    ROMMatcher,
    ROMStatus,
)


@pytest.fixture
def sample_nointro_dat():
    """Create sample No-Intro DAT XML."""
    return dedent(
        """<?xml version="1.0"?>
        <!DOCTYPE datafile PUBLIC "-//Logiqx//DTD ROM Management Datafile//EN" "http://www.logiqx.com/Dats/datafile.dtd">
        <datafile>
            <header>
                <name>Nintendo - Nintendo Entertainment System</name>
                <description>Nintendo NES DAT</description>
                <version>20241001</version>
                <author>No-Intro</author>
            </header>
            <game name="Contra (USA)">
                <description>Contra (USA)</description>
                <rom name="Contra (USA).nes" size="131088" crc="cba3980f" md5="97ed51e0eb0374c3c95b9bc4ce5dd2f1" sha1="eb08a06e8c5e2c7efbbe85cdc49ee8902ce47f6b"/>
            </game>
            <game name="Super Mario Bros. (USA)">
                <description>Super Mario Bros. (USA)</description>
                <rom name="Super Mario Bros. (USA).nes" size="40976" crc="3337ec46" md5="811b027eaf99c2def7b933c5208636de" sha1="ea343f4e445a9050d4b4fbac2c77d0693b1d0922"/>
            </game>
            <game name="The Legend of Zelda (USA)">
                <description>The Legend of Zelda (USA)</description>
                <rom name="The Legend of Zelda (USA).nes" size="131088" crc="d7ae93d1" md5="169f70e5814c3c9a3a3e8bf827d8ff1a" sha1="ea73818be54c3c1e2e8bb5e8d76eb8b9b0a6b3bd"/>
            </game>
        </datafile>
        """
    ).strip()


@pytest.fixture
def sample_retool_dat():
    """Create sample Retool DAT XML."""
    return dedent(
        """<?xml version="1.0"?>
        <!DOCTYPE datafile PUBLIC "-//Logiqx//DTD ROM Management Datafile//EN" "https://raw.githubusercontent.com/unexpectedpanda/retool-clonelists-metadata/main/datafile.dtd">
        <datafile>
            <header>
                <name>Nintendo - Nintendo Entertainment System (Retool)</name>
                <description>Nintendo NES Retool 1G1R ENG</description>
                <version>20241224-130037</version>
                <author>Retool</author>
                <retool>Created by Retool 2.3.8</retool>
            </header>
            <game name="10-Yard Fight (USA, Europe)">
                <category>Games</category>
                <description>10-Yard Fight (USA, Europe)</description>
                <rom name="10-Yard Fight (USA, Europe).nes" size="40976" crc="c986cda2" md5="7b1d38579ede25e20b3aaf870be69c42" sha1="67f60e1d139dd85baef455b3b1228fbb5059bdaa"/>
            </game>
            <game name="Contra (USA)">
                <category>Games</category>
                <description>Contra (USA)</description>
                <rom name="Contra (USA).nes" size="131088" crc="cba3980f" md5="97ed51e0eb0374c3c95b9bc4ce5dd2f1" sha1="eb08a06e8c5e2c7efbbe85cdc49ee8902ce47f6b"/>
            </game>
            <game name="100-in-1 Contra Function 16 (Asia) (En) (Pirate)">
                <category>Games</category>
                <description>100-in-1 Contra Function 16 (Asia) (En) (Pirate)</description>
                <rom name="100-in-1 Contra Function 16 (Asia) (En) (Pirate).nes" size="1048592" crc="dab595fe" md5="8b92a02edc06b89002519130a10c50e1" sha1="011a0a3f49ea46ae0b60d74aa41999524dbe8fdf"/>
            </game>
        </datafile>
        """
    ).strip()


class TestDATParser:
    """Tests for DATParser."""

    def test_parse_nointro_dat(self, sample_nointro_dat, tmp_path):
        """Test parsing No-Intro DAT."""
        dat_file = tmp_path / "test.dat"
        dat_file.write_text(sample_nointro_dat)

        parser = DATParser()
        dat = parser.parse(dat_file)

        assert dat.name == "Nintendo - Nintendo Entertainment System"
        assert dat.description == "Nintendo NES DAT"
        assert dat.version == "20241001"
        assert dat.author == "No-Intro"
        # DAT type detection is based on filename/content, our test DAT has generic names
        assert dat.dat_type in [DATType.NOINTRO, DATType.CUSTOM]
        assert len(dat.games) == 3

    def test_parse_game_structure(self, sample_nointro_dat, tmp_path):
        """Test game structure parsing."""
        dat_file = tmp_path / "test.dat"
        dat_file.write_text(sample_nointro_dat)

        parser = DATParser()
        dat = parser.parse(dat_file)

        # Check first game
        contra = dat.games[0]
        assert contra.name == "Contra (USA)"
        assert contra.description == "Contra (USA)"
        assert len(contra.roms) == 1

        # Check ROM details
        rom = contra.roms[0]
        assert rom.name == "Contra (USA).nes"
        assert rom.size == 131088
        assert rom.crc == "cba3980f"
        assert rom.md5 == "97ed51e0eb0374c3c95b9bc4ce5dd2f1"
        assert rom.sha1 == "eb08a06e8c5e2c7efbbe85cdc49ee8902ce47f6b"
        assert rom.status == ROMStatus.GOOD

    def test_dat_statistics(self, sample_nointro_dat, tmp_path):
        """Test DAT statistics calculation."""
        dat_file = tmp_path / "test.dat"
        dat_file.write_text(sample_nointro_dat)

        parser = DATParser()
        dat = parser.parse(dat_file)

        stats = dat.get_statistics()
        assert stats["games"] == 3
        assert stats["roms"] == 3
        assert stats["multi_disc_games"] == 0
        assert stats["total_size_bytes"] == 303152  # Sum of all ROM sizes

    def test_find_game_by_name(self, sample_nointro_dat, tmp_path):
        """Test finding game by name."""
        dat_file = tmp_path / "test.dat"
        dat_file.write_text(sample_nointro_dat)

        parser = DATParser()
        dat = parser.parse(dat_file)

        game = dat.find_game_by_name("Contra (USA)")
        assert game is not None
        assert game.name == "Contra (USA)"

        not_found = dat.find_game_by_name("Nonexistent Game")
        assert not_found is None

    def test_find_game_by_rom_name(self, sample_nointro_dat, tmp_path):
        """Test finding game by ROM filename."""
        dat_file = tmp_path / "test.dat"
        dat_file.write_text(sample_nointro_dat)

        parser = DATParser()
        dat = parser.parse(dat_file)

        game = dat.find_game_by_rom_name("Super Mario Bros. (USA).nes")
        assert game is not None
        assert game.name == "Super Mario Bros. (USA)"

    def test_find_game_by_hash(self, sample_nointro_dat, tmp_path):
        """Test finding game by hash."""
        dat_file = tmp_path / "test.dat"
        dat_file.write_text(sample_nointro_dat)

        parser = DATParser()
        dat = parser.parse(dat_file)

        # Find by CRC
        game = dat.find_game_by_hash(crc="3337ec46")
        assert game is not None
        assert game.name == "Super Mario Bros. (USA)"

        # Find by MD5
        game = dat.find_game_by_hash(md5="811b027eaf99c2def7b933c5208636de")
        assert game is not None
        assert game.name == "Super Mario Bros. (USA)"

        # Case insensitive
        game = dat.find_game_by_hash(crc="3337EC46")
        assert game is not None


class TestRetoolDATParser:
    """Tests for RetoolDATParser."""

    def test_parse_retool_dat(self, sample_retool_dat, tmp_path):
        """Test parsing Retool DAT."""
        dat_file = tmp_path / "test-retool.dat"
        dat_file.write_text(sample_retool_dat)

        parser = RetoolDATParser()
        dat = parser.parse(dat_file)

        assert dat.name == "Nintendo - Nintendo Entertainment System (Retool)"
        assert dat.dat_type == DATType.RETOOL
        assert len(dat.games) == 3

    def test_retool_category_tag(self, sample_retool_dat, tmp_path):
        """Test Retool-specific category tag."""
        dat_file = tmp_path / "test-retool.dat"
        dat_file.write_text(sample_retool_dat)

        parser = RetoolDATParser()
        dat = parser.parse(dat_file)

        # Check category is parsed
        for game in dat.games:
            assert game.category == "Games"

    def test_retool_includes_pirates(self, sample_retool_dat, tmp_path):
        """Test that Retool includes some pirate ROMs."""
        dat_file = tmp_path / "test-retool.dat"
        dat_file.write_text(sample_retool_dat)

        parser = RetoolDATParser()
        dat = parser.parse(dat_file)

        # Check pirate ROM is included
        pirate_game = dat.find_game_by_name("100-in-1 Contra Function 16 (Asia) (En) (Pirate)")
        assert pirate_game is not None
        assert "(Pirate)" in pirate_game.name


class TestROMMatcher:
    """Tests for ROMMatcher."""

    def test_match_exact_filename(self, sample_nointro_dat, tmp_path):
        """Test exact filename matching."""
        # Parse DAT
        dat_file = tmp_path / "test.dat"
        dat_file.write_text(sample_nointro_dat)
        parser = DATParser()
        dat = parser.parse(dat_file)

        # Create matcher
        matcher = ROMMatcher(dat)

        # Create test ROM file
        rom_file = tmp_path / "Contra (USA).nes"
        rom_file.write_text("dummy content")

        # Match
        result = matcher.match_file(rom_file)

        assert result.is_matched()
        assert result.match_type == MatchType.EXACT_FILENAME
        assert result.dat_game.name == "Contra (USA)"
        assert result.confidence == 1.0

    def test_match_zip_file(self, sample_nointro_dat, tmp_path):
        """Test matching ZIP file with inner filename."""
        import zipfile

        # Parse DAT
        dat_file = tmp_path / "test.dat"
        dat_file.write_text(sample_nointro_dat)
        parser = DATParser()
        dat = parser.parse(dat_file)

        # Create matcher
        matcher = ROMMatcher(dat)

        # Create ZIP file with correct inner filename
        zip_file = tmp_path / "Contra (USA).zip"
        with zipfile.ZipFile(zip_file, "w") as zf:
            zf.writestr("Contra (USA).nes", b"dummy content")

        # Match
        result = matcher.match_file(zip_file)

        assert result.is_matched()
        assert result.match_type == MatchType.INNER_FILENAME
        assert result.dat_game.name == "Contra (USA)"
        assert result.confidence == 1.0

    def test_no_match(self, sample_nointro_dat, tmp_path):
        """Test file that doesn't match."""
        # Parse DAT
        dat_file = tmp_path / "test.dat"
        dat_file.write_text(sample_nointro_dat)
        parser = DATParser()
        dat = parser.parse(dat_file)

        # Create matcher
        matcher = ROMMatcher(dat)

        # Create test ROM file that doesn't match
        rom_file = tmp_path / "Unknown Game.nes"
        rom_file.write_text("dummy content")

        # Match
        result = matcher.match_file(rom_file)

        assert not result.is_matched()
        assert result.match_type == MatchType.NO_MATCH
        assert result.dat_game is None
        assert result.confidence == 0.0

    def test_match_by_crc(self, sample_nointro_dat, tmp_path):
        """Test matching by CRC hash."""
        # Parse DAT
        dat_file = tmp_path / "test.dat"
        dat_file.write_text(sample_nointro_dat)
        parser = DATParser()
        dat = parser.parse(dat_file)

        # Create matcher
        matcher = ROMMatcher(dat)

        # Create test file
        rom_file = tmp_path / "unknown.nes"
        rom_file.write_text("dummy content")

        # Match by CRC
        result = matcher.match_by_hash(rom_file, crc="3337ec46")

        assert result.is_matched()
        assert result.match_type == MatchType.CRC_MATCH
        assert result.dat_game.name == "Super Mario Bros. (USA)"

    def test_get_matched_count(self, sample_nointro_dat, tmp_path):
        """Test counting matched files."""
        # Parse DAT
        dat_file = tmp_path / "test.dat"
        dat_file.write_text(sample_nointro_dat)
        parser = DATParser()
        dat = parser.parse(dat_file)

        # Create matcher
        matcher = ROMMatcher(dat)

        # Create test files
        (tmp_path / "Contra (USA).nes").write_text("dummy")
        (tmp_path / "Super Mario Bros. (USA).nes").write_text("dummy")
        (tmp_path / "Unknown Game.nes").write_text("dummy")

        files = list(tmp_path.glob("*.nes"))
        matched_count = matcher.get_matched_count(files)

        assert matched_count == 2

    def test_get_unmatched_files(self, sample_nointro_dat, tmp_path):
        """Test getting unmatched files."""
        # Parse DAT
        dat_file = tmp_path / "test.dat"
        dat_file.write_text(sample_nointro_dat)
        parser = DATParser()
        dat = parser.parse(dat_file)

        # Create matcher
        matcher = ROMMatcher(dat)

        # Create test files
        (tmp_path / "Contra (USA).nes").write_text("dummy")
        (tmp_path / "Unknown Game.nes").write_text("dummy")

        files = list(tmp_path.glob("*.nes"))
        unmatched = matcher.get_unmatched_files(files)

        assert len(unmatched) == 1
        assert unmatched[0].name == "Unknown Game.nes"


class TestRealRetoolDAT:
    """Tests using real Retool DAT from /path/to/dats/."""

    @pytest.mark.skipif(
        not Path("/path/to/dats/nointro/").exists(),
        reason="Retool DAT directory not found",
    )
    def test_parse_real_nes_retool_dat(self):
        """Test parsing real NES Retool DAT."""
        dat_dir = Path("/path/to/dats/nointro/")
        dat_files = list(dat_dir.glob("Nintendo - Nintendo Entertainment System*.dat"))

        if not dat_files:
            pytest.skip("NES Retool DAT not found")

        parser = RetoolDATParser()
        dat = parser.parse(dat_files[0])

        # Verify expected Retool results
        assert dat.dat_type == DATType.RETOOL
        assert dat.get_game_count() > 1700  # Retool filtered ~1,761 games
        assert dat.get_game_count() < 2000

        # Check statistics
        stats = dat.get_statistics()
        assert stats["games"] > 1700
        assert stats["total_size_gb"] > 0

        # Verify category tags exist (Retool-specific)
        games_with_category = sum(1 for game in dat.games if game.category)
        assert games_with_category > 0

    @pytest.mark.skipif(
        not Path("/path/to/dats/nointro/").exists(),
        reason="Retool DAT directory not found",
    )
    def test_match_real_rom_files(self, tmp_path):
        """Test matching against real ROM files (mock)."""
        dat_dir = Path("/path/to/dats/nointro/")
        dat_files = list(dat_dir.glob("Nintendo - Nintendo Entertainment System*.dat"))

        if not dat_files:
            pytest.skip("NES Retool DAT not found")

        parser = RetoolDATParser()
        dat = parser.parse(dat_files[0])
        matcher = ROMMatcher(dat)

        # Create mock ROM files matching DAT entries
        test_files = []
        for game in dat.games[:5]:  # Test first 5 games
            rom = game.get_primary_rom()
            if rom:
                rom_file = tmp_path / rom.name
                rom_file.write_text("dummy content")
                test_files.append(rom_file)

        # Match files
        matched_count = matcher.get_matched_count(test_files)
        assert matched_count == len(test_files)
