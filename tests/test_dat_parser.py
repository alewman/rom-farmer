"""Tests for DAT file parsing."""

import pytest
from pathlib import Path
from romfarmer.dat import DatParser, DatHeader, DatGame, DatRom, DatRelease


# Sample DAT XML for testing
SAMPLE_DAT_XML = """<?xml version="1.0"?>
<!DOCTYPE datafile PUBLIC "-//Logiqx//DTD ROM Management Datafile//EN" "http://www.logiqx.com/Dats/datafile.dtd">
<datafile>
    <header>
        <name>Nintendo - NES</name>
        <description>Nintendo - NES (Parent-Clone)</description>
        <version>20241101-131442</version>
        <date>20241101-131442</date>
        <author>No-Intro</author>
        <url>https://www.no-intro.org</url>
    </header>
    <game name="Super Mario Bros (USA)">
        <description>Super Mario Bros (USA)</description>
        <release name="Super Mario Bros (USA)" region="USA"/>
        <rom name="Super Mario Bros (USA).nes" size="40960" crc="3337ec46" md5="811b027eaf99c2def7b933c5208636de" sha1="ea343f4e445a9050d4b4fbac2c77d0693b1d0922"/>
    </game>
    <game name="Super Mario Bros (Europe)" cloneof="Super Mario Bros (USA)">
        <description>Super Mario Bros (Europe)</description>
        <release name="Super Mario Bros (Europe)" region="EUR"/>
        <rom name="Super Mario Bros (Europe).nes" size="40960" crc="8b2e3e8e" md5="cf202f6f9a5cad92c2abd58c3ca80a42" sha1="69e87d82e01514a45e7b4eaa02fcfa3a0fce435e"/>
    </game>
    <game name="Zelda (USA)">
        <description>Legend of Zelda, The (USA)</description>
        <release name="Legend of Zelda, The (USA)" region="USA"/>
        <rom name="Legend of Zelda, The (USA).nes" size="131072" crc="337bd74f" md5="10f0f18f9a7f1e80f2ce2f05bca0b5a5" sha1="0a50033f2b3a9bd81e8f42c3e7e7f63b7e0d2cb4" status="verified"/>
    </game>
    <game name="Multi Region Game (USA, Europe)">
        <description>Multi Region Game (USA, Europe)</description>
        <release name="Multi Region Game (USA)" region="USA"/>
        <release name="Multi Region Game (Europe)" region="EUR"/>
        <rom name="Multi Region Game (USA, Europe).nes" size="32768" crc="12345678" md5="abcdef1234567890abcdef1234567890" sha1="1234567890abcdef1234567890abcdef12345678"/>
    </game>
</datafile>
"""


class TestDatParser:
    """Test DatParser functionality."""
    
    def test_parse_header(self, tmp_path):
        """Test parsing DAT header."""
        dat_file = tmp_path / "test.dat"
        dat_file.write_text(SAMPLE_DAT_XML)
        
        parser = DatParser()
        parser.parse(dat_file)
        
        assert parser.header is not None
        assert parser.header.name == "Nintendo - NES"
        assert parser.header.description == "Nintendo - NES (Parent-Clone)"
        assert parser.header.version == "20241101-131442"
        assert parser.header.date == "20241101-131442"
        assert parser.header.author == "No-Intro"
        assert parser.header.url == "https://www.no-intro.org"
    
    def test_parse_games(self, tmp_path):
        """Test parsing game entries."""
        dat_file = tmp_path / "test.dat"
        dat_file.write_text(SAMPLE_DAT_XML)
        
        parser = DatParser()
        parser.parse(dat_file)
        
        assert len(parser.games) == 4
        
        # Check first game
        game1 = parser.games[0]
        assert game1.name == "Super Mario Bros (USA)"
        assert game1.description == "Super Mario Bros (USA)"
        assert game1.is_parent
        assert not game1.is_clone
    
    def test_parse_clone_game(self, tmp_path):
        """Test parsing clone games."""
        dat_file = tmp_path / "test.dat"
        dat_file.write_text(SAMPLE_DAT_XML)
        
        parser = DatParser()
        parser.parse(dat_file)
        
        # Find clone game
        clone_game = parser.games[1]
        assert clone_game.name == "Super Mario Bros (Europe)"
        assert clone_game.cloneof == "Super Mario Bros (USA)"
        assert clone_game.is_clone
        assert not clone_game.is_parent
    
    def test_parse_roms(self, tmp_path):
        """Test parsing ROM entries."""
        dat_file = tmp_path / "test.dat"
        dat_file.write_text(SAMPLE_DAT_XML)
        
        parser = DatParser()
        parser.parse(dat_file)
        
        game = parser.games[0]
        assert len(game.roms) == 1
        
        rom = game.roms[0]
        assert rom.name == "Super Mario Bros (USA).nes"
        assert rom.size == 40960
        assert rom.crc == "3337ec46"
        assert rom.md5 == "811b027eaf99c2def7b933c5208636de"
        assert rom.sha1 == "ea343f4e445a9050d4b4fbac2c77d0693b1d0922"
    
    def test_parse_rom_with_status(self, tmp_path):
        """Test parsing ROM with status attribute."""
        dat_file = tmp_path / "test.dat"
        dat_file.write_text(SAMPLE_DAT_XML)
        
        parser = DatParser()
        parser.parse(dat_file)
        
        # Zelda game has verified status
        zelda = parser.games[2]
        rom = zelda.roms[0]
        assert rom.status == "verified"
    
    def test_parse_releases(self, tmp_path):
        """Test parsing release information."""
        dat_file = tmp_path / "test.dat"
        dat_file.write_text(SAMPLE_DAT_XML)
        
        parser = DatParser()
        parser.parse(dat_file)
        
        game = parser.games[0]
        assert len(game.releases) == 1
        
        release = game.releases[0]
        assert release.name == "Super Mario Bros (USA)"
        assert release.region == "USA"
    
    def test_parse_multi_region_releases(self, tmp_path):
        """Test parsing game with multiple region releases."""
        dat_file = tmp_path / "test.dat"
        dat_file.write_text(SAMPLE_DAT_XML)
        
        parser = DatParser()
        parser.parse(dat_file)
        
        # Multi region game
        game = parser.games[3]
        assert len(game.releases) == 2
        
        regions = {r.region for r in game.releases}
        assert "USA" in regions
        assert "EUR" in regions
    
    def test_primary_region(self, tmp_path):
        """Test getting primary region from game."""
        dat_file = tmp_path / "test.dat"
        dat_file.write_text(SAMPLE_DAT_XML)
        
        parser = DatParser()
        parser.parse(dat_file)
        
        game = parser.games[0]
        assert game.primary_region == "USA"
    
    def test_get_parent_games(self, tmp_path):
        """Test filtering parent games."""
        dat_file = tmp_path / "test.dat"
        dat_file.write_text(SAMPLE_DAT_XML)
        
        parser = DatParser()
        parser.parse(dat_file)
        
        parents = parser.get_parent_games()
        assert len(parents) == 3  # Mario USA, Zelda, Multi Region
        
        # Europe version is a clone, should not be in parents
        parent_names = {g.name for g in parents}
        assert "Super Mario Bros (USA)" in parent_names
        assert "Super Mario Bros (Europe)" not in parent_names
    
    def test_get_clone_games(self, tmp_path):
        """Test filtering clone games."""
        dat_file = tmp_path / "test.dat"
        dat_file.write_text(SAMPLE_DAT_XML)
        
        parser = DatParser()
        parser.parse(dat_file)
        
        clones = parser.get_clone_games()
        assert len(clones) == 1
        assert clones[0].name == "Super Mario Bros (Europe)"
    
    def test_get_games_by_region(self, tmp_path):
        """Test filtering games by region."""
        dat_file = tmp_path / "test.dat"
        dat_file.write_text(SAMPLE_DAT_XML)
        
        parser = DatParser()
        parser.parse(dat_file)
        
        usa_games = parser.get_games_by_region("USA")
        assert len(usa_games) == 3  # Mario USA, Zelda, Multi Region
        
        eur_games = parser.get_games_by_region("EUR")
        assert len(eur_games) == 2  # Mario Europe, Multi Region
    
    def test_find_game_by_name(self, tmp_path):
        """Test finding game by exact name."""
        dat_file = tmp_path / "test.dat"
        dat_file.write_text(SAMPLE_DAT_XML)
        
        parser = DatParser()
        parser.parse(dat_file)
        
        game = parser.find_game_by_name("Zelda (USA)")
        assert game is not None
        assert game.description == "Legend of Zelda, The (USA)"
        
        # Non-existent game
        missing = parser.find_game_by_name("Nonexistent Game")
        assert missing is None
    
    def test_find_game_by_crc(self, tmp_path):
        """Test finding game by ROM CRC."""
        dat_file = tmp_path / "test.dat"
        dat_file.write_text(SAMPLE_DAT_XML)
        
        parser = DatParser()
        parser.parse(dat_file)
        
        # Find by CRC
        game = parser.find_game_by_crc("3337ec46")
        assert game is not None
        assert game.name == "Super Mario Bros (USA)"
        
        # Case insensitive
        game2 = parser.find_game_by_crc("3337EC46")
        assert game2 is not None
        assert game2.name == "Super Mario Bros (USA)"
        
        # Non-existent CRC
        missing = parser.find_game_by_crc("99999999")
        assert missing is None
    
    def test_get_statistics(self, tmp_path):
        """Test getting DAT statistics."""
        dat_file = tmp_path / "test.dat"
        dat_file.write_text(SAMPLE_DAT_XML)
        
        parser = DatParser()
        parser.parse(dat_file)
        
        stats = parser.get_statistics()
        
        assert stats['total_games'] == 4
        assert stats['parent_games'] == 3
        assert stats['clone_games'] == 1
        assert stats['total_roms'] == 4
        assert stats['region_count'] == 2
        assert set(stats['regions']) == {'USA', 'EUR'}
    
    def test_parse_nonexistent_file(self, tmp_path):
        """Test parsing non-existent file raises error."""
        parser = DatParser()
        
        with pytest.raises(FileNotFoundError):
            parser.parse(tmp_path / "nonexistent.dat")
    
    def test_parse_invalid_xml(self, tmp_path):
        """Test parsing invalid XML raises error."""
        dat_file = tmp_path / "invalid.dat"
        dat_file.write_text("<?xml version='1.0'?><invalid>broken<xml>")
        
        parser = DatParser()
        
        with pytest.raises(Exception):  # ET.ParseError
            parser.parse(dat_file)
    
    def test_header_string_representation(self):
        """Test DatHeader string representation."""
        header = DatHeader(
            name="Test DAT",
            description="Test Description",
            version="1.0",
        )
        
        assert str(header) == "Test DAT (v1.0)"
    
    def test_rom_string_representation(self):
        """Test DatRom string representation."""
        rom = DatRom(
            name="test.nes",
            size=1024,
            crc="12345678",
        )
        
        assert str(rom) == "test.nes (CRC: 12345678)"
        
        # ROM without CRC
        rom_no_crc = DatRom(name="test2.nes", size=2048)
        assert "N/A" in str(rom_no_crc)
    
    def test_game_string_representation(self):
        """Test DatGame string representation."""
        game = DatGame(
            name="Test Game",
            description="Test Game (USA)",
            roms=[],
            releases=[],
        )
        
        assert str(game) == "Test Game (USA)"
        
        # Clone game
        clone = DatGame(
            name="Test Game Clone",
            description="Test Game (Europe)",
            roms=[],
            releases=[],
            cloneof="Test Game",
        )
        
        assert "clone of Test Game" in str(clone)
