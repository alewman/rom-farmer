"""Tests for processor profiles."""

import pytest

from romgroomer.processors.profiles import (
    PlatformProfile,
    get_profile,
    list_profiles,
    register_profile,
)


class TestPlatformProfile:
    """Test PlatformProfile dataclass."""
    
    def test_create_profile(self):
        """Test creating a platform profile."""
        profile = PlatformProfile(
            name="test_system",
            description="Test System",
            parser_type="nointro",
            stages=["extract_archive"],
            output_format=".rom",
        )
        
        assert profile.name == "test_system"
        assert profile.description == "Test System"
        assert profile.parser_type == "nointro"
        assert profile.stages == ["extract_archive"]
        assert profile.output_format == ".rom"
        assert profile.stage_config == {}
    
    def test_profile_with_stage_config(self):
        """Test profile with stage-specific configuration."""
        profile = PlatformProfile(
            name="test_system",
            description="Test System",
            parser_type="nointro",
            stages=["extract_archive", "convert"],
            output_format=".rom",
            stage_config={
                "convert": {
                    "format": "custom",
                    "compression": 9,
                }
            },
        )
        
        assert profile.stage_config["convert"]["format"] == "custom"
        assert profile.stage_config["convert"]["compression"] == 9


class TestGetProfile:
    """Test get_profile function."""
    
    def test_get_nes_profile(self):
        """Test getting NES profile."""
        profile = get_profile("nes")
        
        assert profile.name == "nes"
        assert profile.description == "Nintendo Entertainment System"
        assert profile.parser_type == "nointro"
        assert "extract_archive" in profile.stages
        assert profile.output_format == ".nes"
    
    def test_get_gba_profile(self):
        """Test getting GBA profile."""
        profile = get_profile("gba")
        
        assert profile.name == "gba"
        assert profile.description == "Game Boy Advance"
        assert profile.parser_type == "nointro"
        assert profile.output_format == ".gba"
    
    def test_get_psx_profile(self):
        """Test getting PSX profile."""
        profile = get_profile("psx")
        
        assert profile.name == "psx"
        assert profile.description == "PlayStation 1"
        assert profile.parser_type == "redump"
        assert "extract_archive" in profile.stages
    
    def test_get_unknown_profile(self):
        """Test getting unknown profile raises error."""
        with pytest.raises(ValueError, match="Unknown profile: unknown_system"):
            get_profile("unknown_system")
    
    def test_error_message_shows_available_profiles(self):
        """Test error message includes available profiles."""
        with pytest.raises(ValueError) as exc_info:
            get_profile("invalid")
        
        assert "Available profiles:" in str(exc_info.value)
        assert "nes" in str(exc_info.value)


class TestListProfiles:
    """Test list_profiles function."""
    
    def test_list_all_profiles(self):
        """Test listing all profiles."""
        profiles = list_profiles()
        
        assert len(profiles) > 0
        assert any(p.name == "nes" for p in profiles)
        assert any(p.name == "gba" for p in profiles)
        assert any(p.name == "psx" for p in profiles)
    
    def test_list_profiles_with_filter(self):
        """Test listing profiles with system filter."""
        # Get all Game Boy profiles
        gb_profiles = list_profiles("gb")
        
        assert len(gb_profiles) >= 2  # gb, gbc, gba
        assert all(p.name.startswith("gb") for p in gb_profiles)
        assert any(p.name == "gb" for p in gb_profiles)
        assert any(p.name == "gbc" for p in gb_profiles)
        assert any(p.name == "gba" for p in gb_profiles)
    
    def test_list_profiles_no_matches(self):
        """Test listing profiles with no matches."""
        profiles = list_profiles("nonexistent")
        
        assert len(profiles) == 0


class TestRegisterProfile:
    """Test register_profile function."""
    
    def test_register_new_profile(self):
        """Test registering a new profile."""
        custom_profile = PlatformProfile(
            name="custom_test_system",
            description="Custom Test System",
            parser_type="nointro",
            stages=["extract_archive"],
            output_format=".custom",
        )
        
        register_profile(custom_profile)
        
        # Should be able to retrieve it
        retrieved = get_profile("custom_test_system")
        assert retrieved.name == "custom_test_system"
        assert retrieved.description == "Custom Test System"
    
    def test_register_overwrites_existing(self):
        """Test registering profile overwrites existing one."""
        original = get_profile("nes")
        original_description = original.description
        
        # Register new profile with same name
        custom_nes = PlatformProfile(
            name="nes",
            description="Modified NES Profile",
            parser_type="nointro",
            stages=["extract_archive"],
            output_format=".nes",
        )
        
        register_profile(custom_nes)
        
        # Should get modified version
        modified = get_profile("nes")
        assert modified.description == "Modified NES Profile"
        
        # Restore original (for other tests)
        register_profile(original)


class TestBuiltInProfiles:
    """Test built-in platform profiles."""
    
    def test_cartridge_profiles(self):
        """Test all cartridge-based profiles."""
        cartridge_systems = ["nes", "snes", "gb", "gbc", "gba", "nds", "genesis", "gamegear"]
        
        for system in cartridge_systems:
            profile = get_profile(system)
            assert profile.parser_type == "nointro"
            assert "extract_archive" in profile.stages
            assert len(profile.output_format) > 0
    
    def test_disc_profiles(self):
        """Test all disc-based profiles."""
        disc_systems = ["psx", "segacd", "pcenginecd"]
        
        for system in disc_systems:
            profile = get_profile(system)
            assert profile.parser_type == "redump"
            assert "extract_archive" in profile.stages
    
    def test_all_profiles_have_required_fields(self):
        """Test all profiles have required fields."""
        for profile in list_profiles():
            assert len(profile.name) > 0
            assert len(profile.description) > 0
            assert len(profile.parser_type) > 0
            assert len(profile.stages) > 0
            assert len(profile.output_format) > 0
