"""Tests for the kind organizer."""

import pytest
from pathlib import Path
from romfarmer.organizers import KindOrganizer, OrganizeMode


class TestKindOrganizer:
    """Test KindOrganizer functionality."""
    
    def test_get_organization_value_demo(self):
        """Test extracting demo kind from filename."""
        organizer = KindOrganizer()
        
        assert organizer.get_organization_value("Game (USA) (Demo).nes") == "Demo"
        assert organizer.get_organization_value("Kiosk Demo (Kiosk).nes") == "Demo"
    
    def test_get_organization_value_beta(self):
        """Test extracting beta/prototype kind."""
        organizer = KindOrganizer()
        
        assert organizer.get_organization_value("Game (Beta).nes") == "Beta"
        assert organizer.get_organization_value("Game (Proto).nes") == "Beta"
        assert organizer.get_organization_value("Game (Prototype).nes") == "Beta"
    
    def test_get_organization_value_translation(self):
        """Test extracting translation kind."""
        organizer = KindOrganizer()
        
        assert organizer.get_organization_value("Game (Japan) (T+Eng).nes") == "Translation"
        assert organizer.get_organization_value("Game (T-Eng).nes") == "Translation"
    
    def test_get_organization_value_homebrew(self):
        """Test extracting homebrew kind."""
        organizer = KindOrganizer()
        
        assert organizer.get_organization_value("Cool Game (Homebrew).nes") == "Homebrew"
    
    def test_get_organization_value_unlicensed(self):
        """Test extracting unlicensed kind."""
        organizer = KindOrganizer()
        
        assert organizer.get_organization_value("Game (Unlicensed).nes") == "Unlicensed"
    
    def test_get_organization_value_pirate(self):
        """Test extracting pirate kind."""
        organizer = KindOrganizer()
        
        assert organizer.get_organization_value("Game (Pirate).nes") == "Pirate"
    
    def test_get_organization_value_no_kind(self):
        """Test files without kind information."""
        organizer = KindOrganizer()
        
        assert organizer.get_organization_value("Game.nes") is None
        assert organizer.get_organization_value("Game (USA).nes") is None
        assert organizer.get_organization_value("Game (Rev 1).nes") is None
    
    def test_get_organization_value_with_other_info(self):
        """Test extraction with other metadata present."""
        organizer = KindOrganizer()
        
        assert organizer.get_organization_value("Game (USA) (Rev 1) (Demo).nes") == "Demo"
        assert organizer.get_organization_value("Game (Europe) (Beta) (En).nes") == "Beta"
        assert organizer.get_organization_value("Game (Proto) (En,Fr).nes") == "Beta"
    
    def test_custom_markers(self):
        """Test adding custom kind markers."""
        organizer = KindOrganizer(
            custom_markers={
                "Special": ["Special Edition", "SE"],
                "Limited": ["Limited"],
            }
        )
        
        assert organizer.get_organization_value("Game (Special Edition).nes") == "Special"
        assert organizer.get_organization_value("Game (SE).nes") == "Special"
        assert organizer.get_organization_value("Game (Limited).nes") == "Limited"
    
    def test_should_organize_with_keep_in_place(self):
        """Test keep_in_place functionality."""
        organizer = KindOrganizer(keep_in_place=["Demo", "Beta"])
        
        assert not organizer.should_organize("Demo")  # Kept in place
        assert not organizer.should_organize("Beta")  # Kept in place
        assert organizer.should_organize("Homebrew")  # Should organize
        assert organizer.should_organize("Translation")  # Should organize
    
    def test_should_organize_with_exclude(self):
        """Test exclude_kinds functionality."""
        organizer = KindOrganizer(exclude_kinds=["Pirate", "Unlicensed"])
        
        assert not organizer.should_organize("Pirate")  # Excluded
        assert not organizer.should_organize("Unlicensed")  # Excluded
        assert organizer.should_organize("Demo")  # Not excluded
        assert organizer.should_organize("Beta")  # Not excluded
    
    def test_organize_move_mode(self, tmp_path):
        """Test organizing files by moving them."""
        source_dir = tmp_path / "roms"
        source_dir.mkdir()
        
        # Create test ROM files
        (source_dir / "Game (USA).nes").write_text("regular game")
        (source_dir / "Demo (USA) (Demo).nes").write_text("demo")
        (source_dir / "Beta (USA) (Beta).nes").write_text("beta")
        (source_dir / "Homebrew (Homebrew).nes").write_text("homebrew")
        
        # Organize with Demo kept in place
        organizer = KindOrganizer(
            mode=OrganizeMode.MOVE,
            keep_in_place=["Demo"]
        )
        stats = organizer.organize(source_dir)
        
        # Check stats (only 3 files have kind markers, 1 is kept in place)
        assert stats.files_processed == 4
        assert stats.files_moved == 2  # Beta and Homebrew
        
        # Check regular game and demo stayed in place
        assert (source_dir / "Game (USA).nes").exists()
        assert (source_dir / "Demo (USA) (Demo).nes").exists()
        
        # Check files were moved
        assert not (source_dir / "Beta (USA) (Beta).nes").exists()
        assert not (source_dir / "Homebrew (Homebrew).nes").exists()
        
        # Check organization directories
        assert (source_dir / "By Kind" / "Beta" / "Beta (USA) (Beta).nes").exists()
        assert (source_dir / "By Kind" / "Homebrew" / "Homebrew (Homebrew).nes").exists()
    
    def test_organize_copy_mode(self, tmp_path):
        """Test organizing files by copying them."""
        source_dir = tmp_path / "roms"
        source_dir.mkdir()
        
        # Create test ROM file
        (source_dir / "Game (Beta).nes").write_text("beta")
        
        # Organize by copying
        organizer = KindOrganizer(mode=OrganizeMode.COPY)
        stats = organizer.organize(source_dir)
        
        # Check stats
        assert stats.files_processed == 1
        assert stats.files_copied == 1
        
        # Check original still exists
        assert (source_dir / "Game (Beta).nes").exists()
        
        # Check copy was created
        assert (source_dir / "By Kind" / "Beta" / "Game (Beta).nes").exists()
    
    def test_organize_symlink_mode(self, tmp_path):
        """Test organizing files by creating symlinks."""
        source_dir = tmp_path / "roms"
        source_dir.mkdir()
        
        # Create test ROM file
        rom_file = source_dir / "Game (Demo).nes"
        rom_file.write_text("demo")
        
        # Organize by symlinking
        organizer = KindOrganizer(mode=OrganizeMode.SYMLINK)
        stats = organizer.organize(source_dir)
        
        # Check stats
        assert stats.files_processed == 1
        assert stats.symlinks_created == 1
        
        # Check original still exists
        assert rom_file.exists()
        
        # Check symlink was created
        symlink = source_dir / "By Kind" / "Demo" / "Game (Demo).nes"
        assert symlink.exists()
        assert symlink.is_symlink()
        
        # Check symlink points to original
        assert symlink.resolve() == rom_file.resolve()
    
    def test_organize_multiple_kinds(self, tmp_path):
        """Test organizing different kinds of ROMs."""
        source_dir = tmp_path / "roms"
        source_dir.mkdir()
        
        # Create test ROM files with different kinds
        (source_dir / "Demo1 (Demo).nes").write_text("demo1")
        (source_dir / "Demo2 (Demo).nes").write_text("demo2")
        (source_dir / "Beta1 (Beta).nes").write_text("beta1")
        (source_dir / "Proto1 (Proto).nes").write_text("proto1")
        (source_dir / "Homebrew1 (Homebrew).nes").write_text("homebrew1")
        
        # Organize all
        organizer = KindOrganizer(mode=OrganizeMode.MOVE)
        stats = organizer.organize(source_dir)
        
        # Check all were processed
        assert stats.files_processed == 5
        assert stats.files_moved == 5
        
        # Check organization structure
        assert (source_dir / "By Kind" / "Demo" / "Demo1 (Demo).nes").exists()
        assert (source_dir / "By Kind" / "Demo" / "Demo2 (Demo).nes").exists()
        assert (source_dir / "By Kind" / "Beta" / "Beta1 (Beta).nes").exists()
        assert (source_dir / "By Kind" / "Beta" / "Proto1 (Proto).nes").exists()  # Proto -> Beta
        assert (source_dir / "By Kind" / "Homebrew" / "Homebrew1 (Homebrew).nes").exists()
    
    def test_organize_dry_run(self, tmp_path):
        """Test dry-run mode doesn't modify filesystem."""
        source_dir = tmp_path / "roms"
        source_dir.mkdir()
        
        # Create test ROM file
        (source_dir / "Game (Demo).nes").write_text("demo")
        
        # Organize in dry-run mode
        organizer = KindOrganizer(mode=OrganizeMode.MOVE, dry_run=True)
        stats = organizer.organize(source_dir)
        
        # Check stats show what would happen
        assert stats.files_processed == 1
        
        # Check file wasn't actually moved
        assert (source_dir / "Game (Demo).nes").exists()
        
        # Check organization directory wasn't created
        assert not (source_dir / "By Kind").exists()
