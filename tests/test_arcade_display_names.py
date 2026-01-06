"""Tests for arcade display name generation.

This module tests the arcade-specific display name logic in the metadata stage.
Arcade games use DAT descriptions for display names and parent game names
for sorting, which groups game families together while showing unique names.
"""

import pytest
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List
from unittest.mock import MagicMock

from src.romfarmer.stages.metadata import GenerateMetadataStage


# ============================================================================
# Test Fixtures
# ============================================================================

@dataclass
class MockDATGame:
    """Mock DATGame for testing."""
    name: str
    description: Optional[str] = None
    cloneof: Optional[str] = None


@dataclass
class MockDATFile:
    """Mock DATFile for testing."""
    name: str
    games: List[MockDATGame] = field(default_factory=list)


@dataclass
class MockPlatformConfig:
    """Mock platform config for testing."""
    name: str


class MockContext:
    """Mock stage context for testing."""
    def __init__(self, platform_name: str = "fbneo", dat: Optional[MockDATFile] = None):
        self.platform_config = MockPlatformConfig(name=platform_name)
        self.filtered_dat = dat
        self.dat_file = None


@pytest.fixture
def stage():
    """Create a fresh GenerateMetadataStage instance."""
    return GenerateMetadataStage()


@pytest.fixture
def sample_1942_dat():
    """Create a sample DAT with 1942 game family."""
    return MockDATFile(
        name="FBNeo - Arcade Games",
        games=[
            MockDATGame(name="1942", description="1942 (Revision B)", cloneof=None),
            MockDATGame(name="1942a", description="1942 (Revision A)", cloneof="1942"),
            MockDATGame(name="1942c64", description="1942 (C64 Music)", cloneof="1942"),
            MockDATGame(name="1942h", description="Supercharger 1942", cloneof="1942"),
        ]
    )


@pytest.fixture
def sample_sf2_dat():
    """Create a sample DAT with Street Fighter II family."""
    return MockDATFile(
        name="FBNeo - Arcade Games",
        games=[
            MockDATGame(name="sf2", description="Street Fighter II - The World Warrior", cloneof=None),
            MockDATGame(name="sf2ce", description="Street Fighter II' - Champion Edition", cloneof="sf2"),
            MockDATGame(name="sf2hf", description="Street Fighter II' Turbo - Hyper Fighting", cloneof="sf2"),
            MockDATGame(name="sf2rb", description="Street Fighter II - Rainbow Edition", cloneof="sf2"),
        ]
    )


# ============================================================================
# Arcade System Detection Tests
# ============================================================================

class TestIsArcadeSystem:
    """Tests for _is_arcade_system method."""
    
    def test_fbneo_is_arcade(self, stage):
        """FBNeo is an arcade system."""
        context = MockContext(platform_name="fbneo")
        assert stage._is_arcade_system(context) is True
    
    def test_mame_is_arcade(self, stage):
        """MAME is an arcade system."""
        context = MockContext(platform_name="mame")
        assert stage._is_arcade_system(context) is True
    
    def test_neogeo_is_arcade(self, stage):
        """Neo Geo is an arcade system."""
        context = MockContext(platform_name="neogeo")
        assert stage._is_arcade_system(context) is True
    
    def test_naomi_is_arcade(self, stage):
        """Naomi is an arcade system."""
        context = MockContext(platform_name="naomi")
        assert stage._is_arcade_system(context) is True
    
    def test_snes_is_not_arcade(self, stage):
        """SNES is NOT an arcade system."""
        context = MockContext(platform_name="snes")
        assert stage._is_arcade_system(context) is False
    
    def test_psx_is_not_arcade(self, stage):
        """PlayStation is NOT an arcade system."""
        context = MockContext(platform_name="psx")
        assert stage._is_arcade_system(context) is False
    
    def test_case_insensitive(self, stage):
        """Platform detection is case-insensitive."""
        context = MockContext(platform_name="FBNeo")
        assert stage._is_arcade_system(context) is True
        
        context = MockContext(platform_name="MAME")
        assert stage._is_arcade_system(context) is True


# ============================================================================
# Arcade Display Info Tests
# ============================================================================

class TestGetArcadeDisplayInfo:
    """Tests for _get_arcade_display_info method."""
    
    def test_parent_game_display_info(self, stage, sample_1942_dat):
        """Parent game returns description and its own name as sortname."""
        context = MockContext(platform_name="fbneo", dat=sample_1942_dat)
        file_path = Path("/output/1942.zip")
        
        result = stage._get_arcade_display_info(context, file_path)
        
        assert result is not None
        display_name, sortname = result
        assert display_name == "1942 (Revision B)"
        assert sortname == "1942"  # Parent uses its own name for sorting
    
    def test_clone_game_display_info(self, stage, sample_1942_dat):
        """Clone game returns description and parent name as sortname."""
        context = MockContext(platform_name="fbneo", dat=sample_1942_dat)
        file_path = Path("/output/1942c64.zip")
        
        result = stage._get_arcade_display_info(context, file_path)
        
        assert result is not None
        display_name, sortname = result
        assert display_name == "1942 (C64 Music)"
        assert sortname == "1942"  # Clone uses parent name for sorting
    
    def test_hack_game_display_info(self, stage, sample_1942_dat):
        """Hack game returns unique description and parent name as sortname."""
        context = MockContext(platform_name="fbneo", dat=sample_1942_dat)
        file_path = Path("/output/1942h.zip")
        
        result = stage._get_arcade_display_info(context, file_path)
        
        assert result is not None
        display_name, sortname = result
        assert display_name == "Supercharger 1942"  # Unique name!
        assert sortname == "1942"  # Still groups with 1942 family
    
    def test_game_not_in_dat_returns_none(self, stage, sample_1942_dat):
        """Game not in DAT returns None."""
        context = MockContext(platform_name="fbneo", dat=sample_1942_dat)
        file_path = Path("/output/notexist.zip")
        
        result = stage._get_arcade_display_info(context, file_path)
        
        assert result is None
    
    def test_no_dat_returns_none(self, stage):
        """No DAT available returns None."""
        context = MockContext(platform_name="fbneo", dat=None)
        file_path = Path("/output/1942.zip")
        
        result = stage._get_arcade_display_info(context, file_path)
        
        assert result is None
    
    def test_game_without_description_uses_name(self, stage):
        """Game without description falls back to name."""
        dat = MockDATFile(
            name="Test DAT",
            games=[MockDATGame(name="testgame", description=None, cloneof=None)]
        )
        context = MockContext(platform_name="fbneo", dat=dat)
        file_path = Path("/output/testgame.zip")
        
        result = stage._get_arcade_display_info(context, file_path)
        
        assert result is not None
        display_name, sortname = result
        assert display_name == "testgame"  # Falls back to name
        assert sortname == "testgame"


# ============================================================================
# Sorting Tests
# ============================================================================

class TestArcadeSorting:
    """Tests for proper sorting/grouping of arcade games."""
    
    def test_game_families_group_together(self, stage, sample_1942_dat):
        """All games in a family share the same sortname."""
        context = MockContext(platform_name="fbneo", dat=sample_1942_dat)
        
        files = [
            Path("/output/1942.zip"),
            Path("/output/1942a.zip"),
            Path("/output/1942c64.zip"),
            Path("/output/1942h.zip"),
        ]
        
        sortnames = set()
        for file_path in files:
            result = stage._get_arcade_display_info(context, file_path)
            assert result is not None
            _, sortname = result
            sortnames.add(sortname)
        
        # All 4 games should have the same sortname
        assert len(sortnames) == 1
        assert sortnames == {"1942"}
    
    def test_different_families_have_different_sortnames(self, stage):
        """Different game families have different sortnames."""
        dat = MockDATFile(
            name="FBNeo",
            games=[
                MockDATGame(name="1942", description="1942", cloneof=None),
                MockDATGame(name="1943", description="1943", cloneof=None),
                MockDATGame(name="sf2", description="Street Fighter II", cloneof=None),
            ]
        )
        context = MockContext(platform_name="fbneo", dat=dat)
        
        files = [
            Path("/output/1942.zip"),
            Path("/output/1943.zip"),
            Path("/output/sf2.zip"),
        ]
        
        sortnames = []
        for file_path in files:
            result = stage._get_arcade_display_info(context, file_path)
            assert result is not None
            _, sortname = result
            sortnames.append(sortname)
        
        # Each game should have its own sortname
        assert sortnames == ["1942", "1943", "sf2"]
    
    def test_all_display_names_unique(self, stage, sample_sf2_dat):
        """All display names in a family are unique."""
        context = MockContext(platform_name="fbneo", dat=sample_sf2_dat)
        
        files = [
            Path("/output/sf2.zip"),
            Path("/output/sf2ce.zip"),
            Path("/output/sf2hf.zip"),
            Path("/output/sf2rb.zip"),
        ]
        
        display_names = []
        for file_path in files:
            result = stage._get_arcade_display_info(context, file_path)
            assert result is not None
            display_name, _ = result
            display_names.append(display_name)
        
        # All display names should be unique
        assert len(display_names) == len(set(display_names))


# ============================================================================
# Caching Tests  
# ============================================================================

class TestDATCaching:
    """Tests for DAT lookup caching."""
    
    def test_dat_lookup_is_cached(self, stage, sample_1942_dat):
        """DAT game lookup is cached for performance."""
        context = MockContext(platform_name="fbneo", dat=sample_1942_dat)
        
        # First lookup
        stage._get_arcade_display_info(context, Path("/output/1942.zip"))
        
        # Check cache was created
        assert hasattr(stage, '_dat_game_lookup')
        assert len(stage._dat_game_lookup) == 4
        assert "1942" in stage._dat_game_lookup
        assert "1942h" in stage._dat_game_lookup
    
    def test_cache_invalidated_on_dat_change(self, stage, sample_1942_dat, sample_sf2_dat):
        """Cache is invalidated when DAT changes."""
        context1 = MockContext(platform_name="fbneo", dat=sample_1942_dat)
        context2 = MockContext(platform_name="fbneo", dat=sample_sf2_dat)
        
        # First lookup with 1942 DAT
        stage._get_arcade_display_info(context1, Path("/output/1942.zip"))
        assert "1942" in stage._dat_game_lookup
        
        # Second lookup with SF2 DAT - cache should update
        stage._get_arcade_display_info(context2, Path("/output/sf2.zip"))
        assert "sf2" in stage._dat_game_lookup
        assert "1942" not in stage._dat_game_lookup  # Old entries gone


# ============================================================================
# Integration-like Tests
# ============================================================================

class TestRealWorldScenarios:
    """Tests simulating real-world usage scenarios."""
    
    def test_1942_family_after_1g1r_plus_hacks(self, stage):
        """Simulate 1942 family after 1G1R filter + hacks."""
        # After 1G1R + hacks, we'd have:
        # - 1942 (parent, best version)
        # - 1942c64 (hack - C64 music)
        # - 1942h (hack - Supercharger)
        dat = MockDATFile(
            name="FBNeo Filtered",
            games=[
                MockDATGame(name="1942", description="1942 (Revision B)", cloneof=None),
                MockDATGame(name="1942c64", description="1942 (C64 Music)", cloneof="1942"),
                MockDATGame(name="1942h", description="Supercharger 1942", cloneof="1942"),
            ]
        )
        context = MockContext(platform_name="fbneo", dat=dat)
        
        results = []
        for rom in ["1942", "1942c64", "1942h"]:
            info = stage._get_arcade_display_info(context, Path(f"/output/{rom}.zip"))
            assert info is not None
            results.append((info[0], info[1]))  # (display_name, sortname)
        
        # Verify grouping
        assert all(r[1] == "1942" for r in results)
        
        # Verify unique names
        display_names = [r[0] for r in results]
        assert len(display_names) == len(set(display_names))
        
        # Verify expected names
        assert "1942 (Revision B)" in display_names
        assert "1942 (C64 Music)" in display_names
        assert "Supercharger 1942" in display_names
