"""Tests for DAT import service."""

import pytest
from pathlib import Path
from romgroomer.dat.importer import DatImportService
from romgroomer.catalog.database import RomGroomerDatabase


# Sample DAT XML for testing
SAMPLE_DAT_XML = """<?xml version="1.0"?>
<!DOCTYPE datafile PUBLIC "-//Logiqx//DTD ROM Management Datafile//EN" "http://www.logiqx.com/Dats/datafile.dtd">
<datafile>
    <header>
        <name>Nintendo - NES (Test)</name>
        <description>Nintendo - NES Test DAT</description>
        <version>1.0</version>
        <date>20241011</date>
        <author>Test Author</author>
    </header>
    <game name="Super Mario Bros (USA)">
        <description>Super Mario Bros (USA)</description>
        <release name="Super Mario Bros (USA)" region="USA"/>
        <rom name="Super Mario Bros (USA).nes" size="40960" crc="3337ec46" md5="811b027eaf99c2def7b933c5208636de" sha1="ea343f4e445a9050d4b4fbac2c77d0693b1d0922"/>
    </game>
    <game name="Zelda (USA)">
        <description>Legend of Zelda, The (USA)</description>
        <release name="Legend of Zelda, The (USA)" region="USA"/>
        <rom name="Legend of Zelda, The (USA).nes" size="131072" crc="337bd74f" md5="10f0f18f9a7f1e80f2ce2f05bca0b5a5" sha1="0a50033f2b3a9bd81e8f42c3e7e7f63b7e0d2cb4"/>
    </game>
    <game name="Multi Disc Game">
        <description>Multi Disc Game (USA)</description>
        <rom name="Disc 1.bin" size="1024" crc="11111111" md5="abc123" sha1="def456"/>
        <rom name="Disc 2.bin" size="2048" crc="22222222" md5="abc456" sha1="def789"/>
    </game>
</datafile>
"""


@pytest.fixture
def db():
    """Create in-memory database for testing."""
    database = RomGroomerDatabase(":memory:")
    yield database
    database.close()


@pytest.fixture
def service(db):
    """Create import service."""
    return DatImportService(db)


@pytest.fixture
def dat_file(tmp_path):
    """Create temporary DAT file."""
    dat_path = tmp_path / "test.dat"
    dat_path.write_text(SAMPLE_DAT_XML)
    return dat_path


class TestDatImportService:
    """Test DatImportService functionality."""
    
    def test_import_dat(self, service, dat_file):
        """Test importing a DAT file."""
        stats = service.import_dat(dat_file)
        
        assert stats['dat_name'] == "Nintendo - NES (Test)"
        assert stats['dat_version'] == "1.0"
        assert stats['games_imported'] == 4  # 1 + 1 + 2 (multi-disc)
        assert not stats['already_exists']
    
    def test_import_dat_updates_existing(self, service, dat_file):
        """Test updating an existing DAT."""
        # Import once
        stats1 = service.import_dat(dat_file)
        assert stats1['games_imported'] == 4
        
        # Import again (should update)
        stats2 = service.import_dat(dat_file, update_existing=True)
        assert stats2['games_imported'] == 4
        assert stats2['already_exists']
        
        # Should still have 4 games (not 8)
        games = service.get_dat_games("Nintendo - NES (Test)")
        assert len(games) == 4
    
    def test_import_dat_skip_existing(self, service, dat_file):
        """Test skipping existing DAT when update_existing=False."""
        # Import once
        stats1 = service.import_dat(dat_file)
        assert stats1['games_imported'] == 4
        
        # Try to import again with update_existing=False
        stats2 = service.import_dat(dat_file, update_existing=False)
        assert stats2['already_exists']
        assert stats2['games_imported'] == 0
        assert stats2['games_skipped'] == 3  # 3 parsed games
    
    def test_import_multiple_dats(self, service, tmp_path):
        """Test importing multiple DAT files."""
        # Create two DAT files
        dat1 = tmp_path / "dat1.dat"
        dat1.write_text(SAMPLE_DAT_XML)
        
        dat2_xml = SAMPLE_DAT_XML.replace("Nintendo - NES (Test)", "Nintendo - SNES (Test)")
        dat2 = tmp_path / "dat2.dat"
        dat2.write_text(dat2_xml)
        
        # Import both
        results = service.import_dats([dat1, dat2])
        
        assert len(results) == 2
        assert results[0]['dat_name'] == "Nintendo - NES (Test)"
        assert results[1]['dat_name'] == "Nintendo - SNES (Test)"
    
    def test_list_imported_dats(self, service, dat_file):
        """Test listing imported DATs."""
        # Initially empty
        dats = service.list_imported_dats()
        assert len(dats) == 0
        
        # Import DAT
        service.import_dat(dat_file)
        
        # Should have one DAT
        dats = service.list_imported_dats()
        assert len(dats) == 1
        assert dats[0].name == "Nintendo - NES (Test)"
    
    def test_get_dat_info(self, service, dat_file):
        """Test getting DAT information."""
        # Import DAT
        service.import_dat(dat_file)
        
        # Get info
        dat_info = service.get_dat_info("Nintendo - NES (Test)")
        assert dat_info is not None
        assert dat_info.name == "Nintendo - NES (Test)"
        assert dat_info.version == "1.0"
        assert dat_info.author == "Test Author"
        assert dat_info.total_games == 4
        
        # Non-existent DAT
        missing = service.get_dat_info("Nonexistent")
        assert missing is None
    
    def test_get_dat_games(self, service, dat_file):
        """Test getting games from a DAT."""
        # Import DAT
        service.import_dat(dat_file)
        
        # Get all games
        games = service.get_dat_games("Nintendo - NES (Test)")
        assert len(games) == 4
        
        # Check game details
        game_names = {g.name for g in games}
        assert "Super Mario Bros (USA)" in game_names
        assert "Zelda (USA)" in game_names
        assert "Multi Disc Game" in game_names
    
    def test_get_dat_games_with_limit(self, service, dat_file):
        """Test getting limited number of games."""
        service.import_dat(dat_file)
        
        # Get only 2 games
        games = service.get_dat_games("Nintendo - NES (Test)", limit=2)
        assert len(games) == 2
    
    def test_find_game_by_crc(self, service, dat_file):
        """Test finding game by CRC."""
        service.import_dat(dat_file)
        
        # Find by CRC
        game = service.find_game_by_crc("3337ec46")
        assert game is not None
        assert game.name == "Super Mario Bros (USA)"
        assert game.rom_name == "Super Mario Bros (USA).nes"
        
        # Case insensitive
        game2 = service.find_game_by_crc("3337EC46")
        assert game2 is not None
        
        # Non-existent CRC
        missing = service.find_game_by_crc("99999999")
        assert missing is None
    
    def test_find_game_by_crc_within_dat(self, service, tmp_path):
        """Test finding game by CRC within specific DAT."""
        # Create two DATs with same CRC
        dat1 = tmp_path / "dat1.dat"
        dat1.write_text(SAMPLE_DAT_XML)
        
        dat2_xml = SAMPLE_DAT_XML.replace("Nintendo - NES (Test)", "Nintendo - SNES (Test)")
        dat2 = tmp_path / "dat2.dat"
        dat2.write_text(dat2_xml)
        
        service.import_dat(dat1)
        service.import_dat(dat2)
        
        # Find in specific DAT
        game = service.find_game_by_crc("3337ec46", dat_name="Nintendo - SNES (Test)")
        assert game is not None
        assert game.dat_file.name == "Nintendo - SNES (Test)"
    
    def test_find_games_by_name(self, service, dat_file):
        """Test finding games by name."""
        service.import_dat(dat_file)
        
        # Partial match
        games = service.find_games_by_name("Mario")
        assert len(games) == 1
        assert games[0].name == "Super Mario Bros (USA)"
        
        # Multiple matches
        games = service.find_games_by_name("USA")
        assert len(games) == 2  # Mario and Zelda
    
    def test_delete_dat(self, service, dat_file):
        """Test deleting a DAT."""
        # Import DAT
        service.import_dat(dat_file)
        
        # Verify it exists
        dats = service.list_imported_dats()
        assert len(dats) == 1
        
        # Delete it
        result = service.delete_dat("Nintendo - NES (Test)")
        assert result is True
        
        # Verify it's gone
        dats = service.list_imported_dats()
        assert len(dats) == 0
        
        # Games should be gone too (cascade delete)
        games = service.get_dat_games("Nintendo - NES (Test)")
        assert len(games) == 0
        
        # Deleting non-existent DAT returns False
        result = service.delete_dat("Nonexistent")
        assert result is False
    
    def test_get_statistics_specific_dat(self, service, dat_file):
        """Test getting statistics for specific DAT."""
        service.import_dat(dat_file)
        
        stats = service.get_statistics("Nintendo - NES (Test)")
        assert stats['dat_name'] == "Nintendo - NES (Test)"
        assert stats['version'] == "1.0"
        assert stats['total_games'] == 4
        assert stats['total_size'] == 40960 + 131072 + 1024 + 2048
        assert 'imported_at' in stats
        assert 'updated_at' in stats
    
    def test_get_statistics_overall(self, service, tmp_path):
        """Test getting overall statistics."""
        # Create and import multiple DATs
        dat1 = tmp_path / "dat1.dat"
        dat1.write_text(SAMPLE_DAT_XML)
        
        dat2_xml = SAMPLE_DAT_XML.replace("Nintendo - NES (Test)", "Nintendo - SNES (Test)")
        dat2 = tmp_path / "dat2.dat"
        dat2.write_text(dat2_xml)
        
        service.import_dat(dat1)
        service.import_dat(dat2)
        
        stats = service.get_statistics()
        assert stats['total_dats'] == 2
        assert stats['total_games'] == 8  # 4 games × 2 DATs
    
    def test_import_dat_without_header(self, service, tmp_path):
        """Test importing DAT without header raises error."""
        dat_file = tmp_path / "noheader.dat"
        dat_file.write_text("""<?xml version="1.0"?>
        <datafile>
            <game name="Test">
                <rom name="test.nes" size="1024" crc="12345678"/>
            </game>
        </datafile>
        """)
        
        with pytest.raises(ValueError, match="has no header"):
            service.import_dat(dat_file)
    
    def test_crc_stored_lowercase(self, service, dat_file):
        """Test that CRC values are stored in lowercase."""
        service.import_dat(dat_file)
        
        # Get game
        game = service.find_game_by_crc("3337ec46")
        assert game is not None
        assert game.crc == "3337ec46"  # Lowercase
        
        # Should find with uppercase too
        game2 = service.find_game_by_crc("3337EC46")
        assert game2 is not None
