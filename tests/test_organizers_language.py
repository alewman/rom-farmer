"""Tests for the language organizer."""

from romfarmer.organizers import LanguageOrganizer, OrganizeMode


class TestLanguageOrganizer:
    """Test LanguageOrganizer functionality."""

    def test_get_organization_value_single_language(self):
        """Test extracting single language from filename."""
        organizer = LanguageOrganizer(use_full_names=False)

        assert organizer.get_organization_value("Game (USA) (En).nes") == "En"
        assert organizer.get_organization_value("Game (Japan) (Ja).nes") == "Ja"
        assert organizer.get_organization_value("Game (France) (Fr).nes") == "Fr"
        assert organizer.get_organization_value("Game (Germany) (De).nes") == "De"

    def test_get_organization_value_full_names(self):
        """Test returning full language names."""
        organizer = LanguageOrganizer(use_full_names=True)

        assert organizer.get_organization_value("Game (En).nes") == "English"
        assert organizer.get_organization_value("Game (Ja).nes") == "Japanese"
        assert organizer.get_organization_value("Game (Fr).nes") == "French"
        assert organizer.get_organization_value("Game (De).nes") == "German"
        assert organizer.get_organization_value("Game (Es).nes") == "Spanish"
        assert organizer.get_organization_value("Game (It).nes") == "Italian"

    def test_get_organization_value_multi_language(self):
        """Test extracting from multi-language ROMs using priority."""
        organizer = LanguageOrganizer(
            language_priority=["En", "Es", "Fr", "De"], use_full_names=False
        )

        # English is highest priority
        assert organizer.get_organization_value("Game (En,Fr).nes") == "En"

        # Spanish is second priority
        assert organizer.get_organization_value("Game (Es,It).nes") == "Es"

        # French is third priority
        assert organizer.get_organization_value("Game (Fr,De).nes") == "Fr"

    def test_get_organization_value_no_language(self):
        """Test files without language information."""
        organizer = LanguageOrganizer()

        assert organizer.get_organization_value("Game.nes") is None
        assert organizer.get_organization_value("Game (USA).nes") is None
        assert organizer.get_organization_value("Game (Demo).nes") is None

    def test_get_organization_value_with_other_info(self):
        """Test extraction with other metadata present."""
        organizer = LanguageOrganizer(use_full_names=False)

        assert organizer.get_organization_value("Game (USA) (Rev 1) (En).nes") == "En"
        assert organizer.get_organization_value("Game (Europe) (Demo) (En,Fr).nes") == "En"
        assert organizer.get_organization_value("Game (Beta) (Ja).nes") == "Ja"

    def test_should_organize_with_keep_in_place(self):
        """Test keep_in_place functionality."""
        organizer = LanguageOrganizer(keep_in_place=["En", "Es"], use_full_names=False)

        assert not organizer.should_organize("En")  # Kept in place
        assert not organizer.should_organize("Es")  # Kept in place
        assert organizer.should_organize("Fr")  # Should organize
        assert organizer.should_organize("De")  # Should organize

    def test_should_organize_with_exclude(self):
        """Test exclude_languages functionality."""
        organizer = LanguageOrganizer(
            exclude_languages=["En"],  # English is default, often excluded
            use_full_names=False,
        )

        assert not organizer.should_organize("En")  # Excluded
        assert organizer.should_organize("Fr")  # Not excluded
        assert organizer.should_organize("Ja")  # Not excluded

    def test_organize_symlink_mode(self, tmp_path):
        """Test organizing files by creating symlinks (typical use case)."""
        source_dir = tmp_path / "roms"
        source_dir.mkdir()

        # Create test ROM files
        en_file = source_dir / "Game (USA) (En).nes"
        fr_file = source_dir / "Game (France) (Fr).nes"
        ja_file = source_dir / "Game (Japan) (Ja).nes"

        en_file.write_text("english")
        fr_file.write_text("french")
        ja_file.write_text("japanese")

        # Organize with English excluded (it's the default)
        organizer = LanguageOrganizer(mode=OrganizeMode.SYMLINK, exclude_languages=["En"])
        stats = organizer.organize(source_dir)

        # Check stats
        assert stats.files_processed == 3
        assert stats.symlinks_created == 2  # Fr and Ja

        # Check originals still exist
        assert en_file.exists()
        assert fr_file.exists()
        assert ja_file.exists()

        # Check English was not organized (excluded)
        assert not (source_dir / "By Language" / "English").exists()

        # Check symlinks were created for Fr and Ja
        fr_symlink = source_dir / "By Language" / "French" / "Game (France) (Fr).nes"
        ja_symlink = source_dir / "By Language" / "Japanese" / "Game (Japan) (Ja).nes"

        assert fr_symlink.exists()
        assert fr_symlink.is_symlink()
        assert fr_symlink.resolve() == fr_file.resolve()

        assert ja_symlink.exists()
        assert ja_symlink.is_symlink()
        assert ja_symlink.resolve() == ja_file.resolve()

    def test_organize_move_mode(self, tmp_path):
        """Test organizing files by moving them."""
        source_dir = tmp_path / "roms"
        source_dir.mkdir()

        # Create test ROM files
        (source_dir / "Game (En).nes").write_text("english")
        (source_dir / "Game (Fr).nes").write_text("french")
        (source_dir / "Game (De).nes").write_text("german")

        # Organize by moving
        organizer = LanguageOrganizer(mode=OrganizeMode.MOVE)
        stats = organizer.organize(source_dir)

        # Check stats
        assert stats.files_processed == 3
        assert stats.files_moved == 3

        # Check files were moved
        assert not (source_dir / "Game (En).nes").exists()
        assert not (source_dir / "Game (Fr).nes").exists()
        assert not (source_dir / "Game (De).nes").exists()

        # Check organization directories
        assert (source_dir / "By Language" / "English" / "Game (En).nes").exists()
        assert (source_dir / "By Language" / "French" / "Game (Fr).nes").exists()
        assert (source_dir / "By Language" / "German" / "Game (De).nes").exists()

    def test_organize_copy_mode(self, tmp_path):
        """Test organizing files by copying them."""
        source_dir = tmp_path / "roms"
        source_dir.mkdir()

        # Create test ROM file
        (source_dir / "Game (Ja).nes").write_text("japanese")

        # Organize by copying
        organizer = LanguageOrganizer(mode=OrganizeMode.COPY)
        stats = organizer.organize(source_dir)

        # Check stats
        assert stats.files_processed == 1
        assert stats.files_copied == 1

        # Check original still exists
        assert (source_dir / "Game (Ja).nes").exists()

        # Check copy was created
        assert (source_dir / "By Language" / "Japanese" / "Game (Ja).nes").exists()

    def test_organize_multiple_languages(self, tmp_path):
        """Test organizing different language ROMs."""
        source_dir = tmp_path / "roms"
        source_dir.mkdir()

        # Create test ROM files with different languages
        (source_dir / "English1 (En).nes").write_text("en1")
        (source_dir / "English2 (En).nes").write_text("en2")
        (source_dir / "French1 (Fr).nes").write_text("fr1")
        (source_dir / "Japanese1 (Ja).nes").write_text("ja1")
        (source_dir / "Spanish1 (Es).nes").write_text("es1")

        # Organize all with symlinks
        organizer = LanguageOrganizer(mode=OrganizeMode.SYMLINK)
        stats = organizer.organize(source_dir)

        # Check all were processed
        assert stats.files_processed == 5
        assert stats.symlinks_created == 5

        # Check organization structure
        assert (source_dir / "By Language" / "English" / "English1 (En).nes").exists()
        assert (source_dir / "By Language" / "English" / "English2 (En).nes").exists()
        assert (source_dir / "By Language" / "French" / "French1 (Fr).nes").exists()
        assert (source_dir / "By Language" / "Japanese" / "Japanese1 (Ja).nes").exists()
        assert (source_dir / "By Language" / "Spanish" / "Spanish1 (Es).nes").exists()

    def test_organize_dry_run(self, tmp_path):
        """Test dry-run mode doesn't modify filesystem."""
        source_dir = tmp_path / "roms"
        source_dir.mkdir()

        # Create test ROM file
        (source_dir / "Game (Fr).nes").write_text("french")

        # Organize in dry-run mode
        organizer = LanguageOrganizer(mode=OrganizeMode.SYMLINK, dry_run=True)
        stats = organizer.organize(source_dir)

        # Check stats show what would happen
        assert stats.files_processed == 1

        # Check file still exists
        assert (source_dir / "Game (Fr).nes").exists()

        # Check organization directory wasn't created
        assert not (source_dir / "By Language").exists()

    def test_organize_with_code_names(self, tmp_path):
        """Test organizing using language codes instead of full names."""
        source_dir = tmp_path / "roms"
        source_dir.mkdir()

        # Create test ROM file
        (source_dir / "Game (Fr).nes").write_text("french")

        # Organize with codes
        organizer = LanguageOrganizer(mode=OrganizeMode.MOVE, use_full_names=False)
        organizer.organize(source_dir)

        # Check organization uses code
        assert (source_dir / "By Language" / "Fr" / "Game (Fr).nes").exists()
        assert not (source_dir / "By Language" / "French").exists()
