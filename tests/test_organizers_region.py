"""Tests for the region organizer."""

from romfarmer.organizers import OrganizeMode, RegionOrganizer


class TestRegionOrganizer:
    """Test RegionOrganizer functionality."""

    def test_get_organization_value_single_region(self):
        """Test extracting single region from filename."""
        organizer = RegionOrganizer()

        assert organizer.get_organization_value("Super Mario Bros (USA).nes") == "USA"
        assert organizer.get_organization_value("Zelda (Europe).sfc") == "Europe"
        assert organizer.get_organization_value("Final Fantasy (Japan).nes") == "Japan"
        assert organizer.get_organization_value("World Game (World).nes") == "World"

    def test_get_organization_value_multi_region(self):
        """Test extracting from multi-region ROMs using priority."""
        organizer = RegionOrganizer(region_priority=["USA", "Europe", "Japan"])

        # USA is highest priority
        assert organizer.get_organization_value("Game (USA, Europe).nes") == "USA"

        # Europe is second priority
        assert organizer.get_organization_value("Game (Europe, Japan).nes") == "Europe"

        # Japan is third priority
        assert organizer.get_organization_value("Game (Japan, Asia).nes") == "Japan"

    def test_get_organization_value_no_region(self):
        """Test files without region information."""
        organizer = RegionOrganizer()

        assert organizer.get_organization_value("Game.nes") is None
        assert organizer.get_organization_value("Game (Demo).nes") is None
        assert organizer.get_organization_value("Game (Beta).nes") is None

    def test_get_organization_value_with_other_info(self):
        """Test extraction with other metadata present."""
        organizer = RegionOrganizer()

        assert organizer.get_organization_value("Game (USA) (Rev 1).nes") == "USA"
        assert organizer.get_organization_value("Game (Europe) (En,Fr,De).nes") == "Europe"
        assert organizer.get_organization_value("Game (Japan) (Demo).nes") == "Japan"

    def test_should_organize_with_keep_in_place(self):
        """Test keep_in_place functionality."""
        organizer = RegionOrganizer(keep_in_place=["USA", "World"])

        assert not organizer.should_organize("USA")  # Kept in place
        assert not organizer.should_organize("World")  # Kept in place
        assert organizer.should_organize("Europe")  # Should organize
        assert organizer.should_organize("Japan")  # Should organize

    def test_should_organize_with_exclude(self):
        """Test exclude_regions functionality."""
        organizer = RegionOrganizer(exclude_regions=["Japan", "Korea"])

        assert not organizer.should_organize("Japan")  # Excluded
        assert not organizer.should_organize("Korea")  # Excluded
        assert organizer.should_organize("USA")  # Not excluded
        assert organizer.should_organize("Europe")  # Not excluded

    def test_organize_move_mode(self, tmp_path):
        """Test organizing files by moving them."""
        # Create source directory with test files
        source_dir = tmp_path / "roms"
        source_dir.mkdir()

        # Create test ROM files
        (source_dir / "Mario (USA).nes").write_text("mario usa")
        (source_dir / "Zelda (Europe).nes").write_text("zelda eu")
        (source_dir / "FF (Japan).nes").write_text("ff jp")
        (source_dir / "World Game (World).nes").write_text("world")

        # Organize with USA and World kept in place
        organizer = RegionOrganizer(mode=OrganizeMode.MOVE, keep_in_place=["USA", "World"])
        stats = organizer.organize(source_dir)

        # Check stats
        assert stats.files_processed == 4
        assert stats.files_moved == 2  # Europe and Japan

        # Check files stayed in place
        assert (source_dir / "Mario (USA).nes").exists()
        assert (source_dir / "World Game (World).nes").exists()

        # Check files were moved
        assert not (source_dir / "Zelda (Europe).nes").exists()
        assert not (source_dir / "FF (Japan).nes").exists()

        # Check organization directories
        assert (source_dir / "By Region" / "Europe" / "Zelda (Europe).nes").exists()
        assert (source_dir / "By Region" / "Japan" / "FF (Japan).nes").exists()

    def test_organize_copy_mode(self, tmp_path):
        """Test organizing files by copying them."""
        source_dir = tmp_path / "roms"
        source_dir.mkdir()

        # Create test ROM file
        (source_dir / "Mario (Europe).nes").write_text("mario")

        # Organize by copying
        organizer = RegionOrganizer(mode=OrganizeMode.COPY)
        stats = organizer.organize(source_dir)

        # Check stats
        assert stats.files_processed == 1
        assert stats.files_copied == 1

        # Check original still exists
        assert (source_dir / "Mario (Europe).nes").exists()

        # Check copy was created
        assert (source_dir / "By Region" / "Europe" / "Mario (Europe).nes").exists()

    def test_organize_symlink_mode(self, tmp_path):
        """Test organizing files by creating symlinks."""
        source_dir = tmp_path / "roms"
        source_dir.mkdir()

        # Create test ROM file
        rom_file = source_dir / "Mario (Japan).nes"
        rom_file.write_text("mario")

        # Organize by symlinking
        organizer = RegionOrganizer(mode=OrganizeMode.SYMLINK)
        stats = organizer.organize(source_dir)

        # Check stats
        assert stats.files_processed == 1
        assert stats.symlinks_created == 1

        # Check original still exists
        assert rom_file.exists()

        # Check symlink was created
        symlink = source_dir / "By Region" / "Japan" / "Mario (Japan).nes"
        assert symlink.exists()
        assert symlink.is_symlink()

        # Check symlink points to original
        assert symlink.resolve() == rom_file.resolve()

    def test_organize_dry_run(self, tmp_path):
        """Test dry-run mode doesn't modify filesystem."""
        source_dir = tmp_path / "roms"
        source_dir.mkdir()

        # Create test ROM files
        (source_dir / "Mario (USA).nes").write_text("mario")
        (source_dir / "Zelda (Europe).nes").write_text("zelda")

        # Organize in dry-run mode
        organizer = RegionOrganizer(mode=OrganizeMode.MOVE, dry_run=True)
        stats = organizer.organize(source_dir)

        # Check stats show what would happen
        assert stats.files_processed == 2

        # Check files weren't actually moved
        assert (source_dir / "Mario (USA).nes").exists()
        assert (source_dir / "Zelda (Europe).nes").exists()

        # Check organization directories weren't created
        assert not (source_dir / "By Region").exists()

    def test_organize_with_extensions_filter(self, tmp_path):
        """Test organizing only specific file extensions."""
        source_dir = tmp_path / "roms"
        source_dir.mkdir()

        # Create test files with different extensions
        (source_dir / "Mario (USA).nes").write_text("nes")
        (source_dir / "Zelda (USA).sfc").write_text("sfc")
        (source_dir / "FF (USA).txt").write_text("txt")

        # Organize only .nes files
        organizer = RegionOrganizer(mode=OrganizeMode.MOVE)
        stats = organizer.organize(source_dir, extensions=[".nes"])

        # Only .nes file should be processed
        assert stats.files_processed == 1

        # .txt and .sfc should remain
        assert (source_dir / "Zelda (USA).sfc").exists()
        assert (source_dir / "FF (USA).txt").exists()

    def test_organize_recursive(self, tmp_path):
        """Test recursive organization."""
        source_dir = tmp_path / "roms"
        subdir = source_dir / "subdir"
        subdir.mkdir(parents=True)

        # Create files in different directories
        (source_dir / "Mario (USA).nes").write_text("mario")
        (subdir / "Zelda (Europe).nes").write_text("zelda")

        # Organize recursively
        organizer = RegionOrganizer(mode=OrganizeMode.MOVE)
        stats = organizer.organize(source_dir, recursive=True)

        # Both files should be processed
        assert stats.files_processed == 2

        # Both should be organized
        assert (source_dir / "By Region" / "USA" / "Mario (USA).nes").exists()
        assert (source_dir / "By Region" / "Europe" / "Zelda (Europe).nes").exists()

    def test_organize_non_recursive(self, tmp_path):
        """Test non-recursive organization."""
        source_dir = tmp_path / "roms"
        subdir = source_dir / "subdir"
        subdir.mkdir(parents=True)

        # Create files in different directories
        (source_dir / "Mario (USA).nes").write_text("mario")
        (subdir / "Zelda (Europe).nes").write_text("zelda")

        # Organize non-recursively
        organizer = RegionOrganizer(mode=OrganizeMode.MOVE)
        stats = organizer.organize(source_dir, recursive=False)

        # Only root file should be processed
        assert stats.files_processed == 1

        # Only root file should be organized
        assert (source_dir / "By Region" / "USA" / "Mario (USA).nes").exists()

        # Subdir file should remain
        assert (subdir / "Zelda (Europe).nes").exists()
