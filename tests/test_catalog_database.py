"""Tests for database operations."""

import pytest
from datetime import datetime
from romgroomer.catalog.database import (
    RomGroomerDatabase,
    DatFile,
    DatGame,
    RomFile,
    OrganizationLog,
)


class TestRomGroomerDatabase:
    """Test suite for database operations."""
    
    @pytest.fixture
    def db(self) -> RomGroomerDatabase:
        """Create in-memory database for testing."""
        return RomGroomerDatabase(":memory:")
    
    def test_database_initialization(self, db: RomGroomerDatabase) -> None:
        """Test database is initialized correctly."""
        with db.get_session() as session:
            stats = db.get_statistics(session)
        
        assert stats["total_dat_files"] == 0
        assert stats["total_dat_games"] == 0
        assert stats["total_rom_files"] == 0
    
    def test_add_dat_file(self, db: RomGroomerDatabase) -> None:
        """Test adding DAT file."""
        with db.get_session() as session:
            dat = DatFile(
                name="Nintendo - Nintendo Entertainment System",
                description="NES DAT",
                version="20241224",
                total_games=1761,
            )
            
            added = db.add_dat_file(session, dat)
            session.commit()
            
            assert added.id is not None
            assert added.name == "Nintendo - Nintendo Entertainment System"
            
            # Verify it's in database
            retrieved = db.get_dat_file(session, added.name)
            assert retrieved is not None
            assert retrieved.name == added.name
    
    def test_update_dat_file(self, db: RomGroomerDatabase) -> None:
        """Test updating existing DAT file."""
        with db.get_session() as session:
            dat = DatFile(
                name="Test DAT",
                version="1.0",
                total_games=100,
            )
            
            added = db.add_dat_file(session, dat)
            session.commit()
            
            # Update with new version
            dat2 = DatFile(
                name="Test DAT",
                version="2.0",
                total_games=150,
            )
            
            updated = db.add_dat_file(session, dat2)
            session.commit()
            
            # Should be same record, updated
            assert updated.id == added.id
            assert updated.version == "2.0"
            assert updated.total_games == 150
    
    def test_add_dat_game(self, db: RomGroomerDatabase) -> None:
        """Test adding game to DAT."""
        with db.get_session() as session:
            dat = DatFile(name="Test DAT", version="1.0")
            dat = db.add_dat_file(session, dat)
            session.commit()
            
            game = DatGame(
                dat_file_id=dat.id,
                name="Super Mario Bros.",
                rom_name="Super Mario Bros. (USA).nes",
                size=40960,
                crc="3337ec46",
                md5="811b027eaf99c2def7b933c5208636de",
                sha1="ea343f4e445a9050d4b4fbac2c77d0693b1d0922",
            )
            
            session.add(game)
            session.commit()
            
            # Verify relationship
            assert game.dat_file.name == "Test DAT"
            assert len(dat.games) == 1
            assert dat.games[0].name == "Super Mario Bros."
    
    def test_add_rom_file(self, db: RomGroomerDatabase) -> None:
        """Test adding ROM file."""
        with db.get_session() as session:
            rom = RomFile(
                path="/roms/nes/Super Mario Bros. (USA).nes",
                filename="Super Mario Bros. (USA).nes",
                size=40960,
                name="Super Mario Bros.",
                regions="usa",
                kind="Games",
                crc32="3337ec46",
            )
            
            added = db.add_rom_file(session, rom)
            session.commit()
            
            assert added.id is not None
            
            # Retrieve by path
            retrieved = db.get_rom_file(session, added.path)
            assert retrieved is not None
            assert retrieved.name == "Super Mario Bros."
    
    def test_find_rom_by_crc(self, db: RomGroomerDatabase) -> None:
        """Test finding ROM by CRC."""
        with db.get_session() as session:
            rom1 = RomFile(
                path="/roms/nes/mario.nes",
                filename="mario.nes",
                size=40960,
                name="Super Mario Bros.",
                crc32="3337ec46",
            )
            
            rom2 = RomFile(
                path="/roms/nes/mario_copy.nes",
                filename="mario_copy.nes",
                size=40960,
                name="Super Mario Bros.",
                crc32="3337ec46",
            )
            
            db.add_rom_file(session, rom1)
            db.add_rom_file(session, rom2)
            session.commit()
            
            # Find by CRC
            found = db.find_rom_by_crc(session, "3337ec46")
            assert len(found) == 2
            assert all(r.crc32 == "3337ec46" for r in found)
    
    def test_find_rom_by_name(self, db: RomGroomerDatabase) -> None:
        """Test finding ROM by name."""
        with db.get_session() as session:
            rom = RomFile(
                path="/roms/nes/mario.nes",
                filename="mario.nes",
                size=40960,
                name="Super Mario Bros.",
            )
            
            db.add_rom_file(session, rom)
            session.commit()
            
            # Find by partial name
            found = db.find_rom_by_name(session, "Mario")
            assert len(found) == 1
            assert found[0].name == "Super Mario Bros."
    
    def test_organization_log(self, db: RomGroomerDatabase) -> None:
        """Test creating organization log."""
        with db.get_session() as session:
            log = OrganizationLog(
                operation_type="organize",
                profile_name="nes-usa",
                source_path="/source",
                dest_path="/dest",
                total_files=100,
                processed_files=95,
                skipped_files=3,
                error_files=2,
                started_at=datetime.utcnow(),
                status="completed",
            )
            
            session.add(log)
            session.commit()
            
            # Verify statistics
            stats = db.get_statistics(session)
            assert stats["total_operations"] == 1
    
    def test_cascade_delete_dat_games(self, db: RomGroomerDatabase) -> None:
        """Test that deleting DAT file cascades to games."""
        with db.get_session() as session:
            dat = DatFile(name="Test DAT", version="1.0")
            dat = db.add_dat_file(session, dat)
            session.commit()
            
            game = DatGame(
                dat_file_id=dat.id,
                name="Test Game",
                rom_name="test.nes",
                size=1024,
                crc="12345678",
            )
            session.add(game)
            session.commit()
            
            # Delete DAT
            session.delete(dat)
            session.commit()
            
            # Games should be deleted too
            stats = db.get_statistics(session)
            assert stats["total_dat_files"] == 0
            assert stats["total_dat_games"] == 0
    
    def test_database_statistics(self, db: RomGroomerDatabase) -> None:
        """Test database statistics."""
        with db.get_session() as session:
            # Add some data
            dat = DatFile(name="Test DAT", version="1.0")
            dat = db.add_dat_file(session, dat)
            session.commit()
            
            game = DatGame(
                dat_file_id=dat.id,
                name="Test Game",
                rom_name="test.nes",
                size=1024,
                crc="12345678",
            )
            session.add(game)
            session.commit()
            
            rom = RomFile(
                path="/test.nes",
                filename="test.nes",
                size=1024,
                name="Test Game",
                verified=True,
            )
            db.add_rom_file(session, rom)
            session.commit()
            
            stats = db.get_statistics(session)
            assert stats["total_dat_files"] == 1
            assert stats["total_dat_games"] == 1
            assert stats["total_rom_files"] == 1
            assert stats["verified_roms"] == 1
