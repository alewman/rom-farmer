"""Tests for 1G1R filtering."""

import pytest
from romfarmer.dat.filter import OneGameOneRomFilter, FilterStats
from romfarmer.catalog.database import DatGame, DatFile


@pytest.fixture
def sample_games():
    """Create sample games for testing."""
    dat_file = DatFile(
        id=1,
        name="Test DAT",
        description="Test",
        version="1.0",
    )
    
    games = [
        DatGame(id=1, dat_file_id=1, name="Super Mario Bros. (USA)", rom_name="smb_usa.nes", crc="12345678", size=40960, dat_file=dat_file),
        DatGame(id=2, dat_file_id=1, name="Super Mario Bros. (Europe)", rom_name="smb_eur.nes", crc="23456789", size=40960, dat_file=dat_file),
        DatGame(id=3, dat_file_id=1, name="Super Mario Bros. (Japan)", rom_name="smb_jpn.nes", crc="34567890", size=40960, dat_file=dat_file),
        DatGame(id=4, dat_file_id=1, name="The Legend of Zelda (USA)", rom_name="zelda_usa.nes", crc="45678901", size=131072, dat_file=dat_file),
        DatGame(id=5, dat_file_id=1, name="Metroid (USA)", rom_name="metroid_usa.nes", crc="56789012", size=131072, dat_file=dat_file),
    ]
    
    return games


class TestOneGameOneRomFilter:
    """Test 1G1R filtering functionality."""
    
    def test_filter_simple_duplicates(self, sample_games):
        """Test filtering simple duplicate games."""
        filter = OneGameOneRomFilter()
        
        # Filter the sample games (3 Mario Bros + 2 unique)
        filtered, stats = filter.filter_games(sample_games)
        
        # Should have 3 unique games (Mario, Zelda, Metroid)
        assert stats.unique_games == 3
        assert stats.filtered_games == 3
        assert stats.duplicates_removed == 2
        
        # Check game names
        game_names = {g.name for g in filtered}
        assert len(game_names) == 3
    
    def test_usa_priority_default(self, sample_games):
        """Test that USA region has highest priority by default."""
        filter = OneGameOneRomFilter()
        
        filtered, _ = filter.filter_games(sample_games)
        
        # Find the Mario game
        mario = next(g for g in filtered if "Mario" in g.name)
        assert mario.name == "Super Mario Bros. (USA)"
    
    def test_custom_region_priority(self):
        """Test custom region priority."""
        games = [
            DatGame(id=1, name="Game (USA)", rom_name="game_usa.rom", crc="111", size=1000),
            DatGame(id=2, name="Game (Europe)", rom_name="game_eur.rom", crc="222", size=1000),
            DatGame(id=3, name="Game (Japan)", rom_name="game_jpn.rom", crc="333", size=1000),
        ]
        
        # Prefer Japan > Europe > USA
        filter = OneGameOneRomFilter(region_priority=['Japan', 'Europe', 'USA'])
        filtered, _ = filter.filter_games(games)
        
        assert len(filtered) == 1
        assert filtered[0].name == "Game (Japan)"
    
    def test_world_region_priority(self):
        """Test that World region is prioritized correctly."""
        games = [
            DatGame(id=1, name="Game (USA)", rom_name="game_usa.rom", crc="111", size=1000),
            DatGame(id=2, name="Game (World)", rom_name="game_world.rom", crc="222", size=1000),
        ]
        
        filter = OneGameOneRomFilter()
        filtered, _ = filter.filter_games(games)
        
        # By default, USA (100) > World (95)
        assert filtered[0].name == "Game (USA)"
        
        # But can customize
        filter2 = OneGameOneRomFilter(region_priority=['World', 'USA'])
        filtered2, _ = filter2.filter_games(games)
        assert filtered2[0].name == "Game (World)"
    
    def test_multi_region_priority(self):
        """Test games with multiple regions."""
        games = [
            DatGame(id=1, name="Game (USA, Europe)", rom_name="game1.rom", crc="111", size=1000),
            DatGame(id=2, name="Game (Japan)", rom_name="game2.rom", crc="222", size=1000),
        ]
        
        filter = OneGameOneRomFilter()
        filtered, _ = filter.filter_games(games)
        
        # Multi-region with USA should win
        assert filtered[0].name == "Game (USA, Europe)"
    
    def test_language_priority(self):
        """Test language-based filtering."""
        games = [
            DatGame(id=1, name="Game (En)", rom_name="game_en.rom", crc="111", size=1000),
            DatGame(id=2, name="Game (Fr)", rom_name="game_fr.rom", crc="222", size=1000),
            DatGame(id=3, name="Game (De)", rom_name="game_de.rom", crc="333", size=1000),
        ]
        
        filter = OneGameOneRomFilter()
        filtered, _ = filter.filter_games(games)
        
        # English should have highest priority
        assert filtered[0].name == "Game (En)"
    
    def test_custom_language_priority(self):
        """Test custom language priority."""
        games = [
            DatGame(id=1, name="Game (En)", rom_name="game_en.rom", crc="111", size=1000),
            DatGame(id=2, name="Game (Ja)", rom_name="game_ja.rom", crc="222", size=1000),
        ]
        
        # Prefer Japanese
        filter = OneGameOneRomFilter(language_priority=['Ja', 'En'])
        filtered, _ = filter.filter_games(games)
        
        assert filtered[0].name == "Game (Ja)"
    
    def test_prefer_parents(self):
        """Test preferring parent ROMs over clones."""
        games = [
            DatGame(id=1, name="Game (USA)", rom_name="game.rom", crc="111", size=1000),
            DatGame(id=2, name="Game (USA) [!]", rom_name="game_verified.rom", crc="222", size=1000),
            DatGame(id=3, name="Game (USA) [a]", rom_name="game_alt.rom", crc="333", size=1000),
        ]
        
        filter = OneGameOneRomFilter(prefer_parents=True)
        filtered, _ = filter.filter_games(games)
        
        # Should select the parent without tags
        assert filtered[0].name == "Game (USA)"
        
        stats = filter.filter_games(games)[1]
        assert stats.parents_selected == 1
    
    def test_prefer_clones_when_disabled(self):
        """Test that clones can be selected when prefer_parents=False."""
        games = [
            DatGame(id=1, name="Game (USA)", rom_name="game.rom", crc="111", size=1000),
            DatGame(id=2, name="Game (USA) [!]", rom_name="game_verified.rom", crc="222", size=1000),
        ]
        
        filter = OneGameOneRomFilter(prefer_parents=False)
        filtered, _ = filter.filter_games(games)
        
        # With prefer_parents disabled, will select based on other criteria
        # (in this case, both have same region, so alphabetically first)
        assert len(filtered) == 1
    
    def test_revision_preference(self):
        """Test preferring later revisions."""
        games = [
            DatGame(id=1, name="Game (USA)", rom_name="game.rom", crc="111", size=1000),
            DatGame(id=2, name="Game (USA) (Rev 1)", rom_name="game_rev1.rom", crc="222", size=1000),
            DatGame(id=3, name="Game (USA) (Rev 2)", rom_name="game_rev2.rom", crc="333", size=1000),
        ]
        
        filter = OneGameOneRomFilter(prefer_later_revisions=True)
        filtered, _ = filter.filter_games(games)
        
        # Should select Rev 2
        assert filtered[0].name == "Game (USA) (Rev 2)"
    
    def test_revision_letters(self):
        """Test revision letters (Rev A, Rev B, etc.)."""
        games = [
            DatGame(id=1, name="Game (USA) (Rev A)", rom_name="game_reva.rom", crc="111", size=1000),
            DatGame(id=2, name="Game (USA) (Rev B)", rom_name="game_revb.rom", crc="222", size=1000),
        ]
        
        filter = OneGameOneRomFilter(prefer_later_revisions=True)
        filtered, _ = filter.filter_games(games)
        
        # Rev B > Rev A
        assert filtered[0].name == "Game (USA) (Rev B)"
    
    def test_version_numbers(self):
        """Test version numbers like v1.0, v1.1."""
        games = [
            DatGame(id=1, name="Game (USA) (v1.0)", rom_name="game_v10.rom", crc="111", size=1000),
            DatGame(id=2, name="Game (USA) (v1.1)", rom_name="game_v11.rom", crc="222", size=1000),
            DatGame(id=3, name="Game (USA) (v2.0)", rom_name="game_v20.rom", crc="333", size=1000),
        ]
        
        filter = OneGameOneRomFilter(prefer_later_revisions=True)
        filtered, _ = filter.filter_games(games)
        
        # v2.0 should win
        assert filtered[0].name == "Game (USA) (v2.0)"
    
    def test_disable_revision_preference(self):
        """Test disabling revision preference."""
        games = [
            DatGame(id=1, name="Game (USA)", rom_name="game.rom", crc="111", size=1000),
            DatGame(id=2, name="Game (USA) (Rev 2)", rom_name="game_rev2.rom", crc="222", size=1000),
        ]
        
        filter = OneGameOneRomFilter(prefer_later_revisions=False)
        filtered, _ = filter.filter_games(games)
        
        # Without revision preference, base version selected (alphabetically first)
        assert filtered[0].name == "Game (USA)"
    
    def test_base_name_extraction(self):
        """Test extracting base names from full names."""
        filter = OneGameOneRomFilter()
        
        test_cases = [
            ("Super Mario Bros. (USA)", "Super Mario Bros."),
            ("The Legend of Zelda (USA) (Rev 1)", "The Legend of Zelda"),
            ("Game (Europe) (En,Fr,De)", "Game"),
            ("Game [!] (USA)", "Game"),
            ("Game {Hack} (World)", "Game"),
        ]
        
        for full_name, expected_base in test_cases:
            base = filter._extract_base_name(full_name)
            assert base == expected_base, f"Failed for {full_name}: got {base}, expected {expected_base}"
    
    def test_complex_filtering_scenario(self):
        """Test complex scenario with multiple criteria."""
        games = [
            # Different regions
            DatGame(id=1, name="Game (USA) (Rev 1)", rom_name="g1.rom", crc="111", size=1000),
            DatGame(id=2, name="Game (Europe)", rom_name="g2.rom", crc="222", size=1000),
            DatGame(id=3, name="Game (Japan) (Rev 2)", rom_name="g3.rom", crc="333", size=1000),
            # Clone
            DatGame(id=4, name="Game (USA) [a]", rom_name="g4.rom", crc="444", size=1000),
            # Different game
            DatGame(id=5, name="Another Game (USA)", rom_name="g5.rom", crc="555", size=1000),
        ]
        
        filter = OneGameOneRomFilter(
            region_priority=['USA', 'Japan', 'Europe'],
            prefer_parents=True,
            prefer_later_revisions=True,
        )
        
        filtered, stats = filter.filter_games(games)
        
        # Should have 2 unique games
        assert stats.unique_games == 2
        assert stats.filtered_games == 2
        
        # First game should be USA Rev 1 (USA region prioritized over Japan Rev 2)
        game1 = next(g for g in filtered if "Game" in g.name and "Another" not in g.name)
        assert game1.name == "Game (USA) (Rev 1)"
        
        # Second game
        game2 = next(g for g in filtered if "Another" in g.name)
        assert game2.name == "Another Game (USA)"
    
    def test_empty_games_list(self):
        """Test filtering empty list."""
        filter = OneGameOneRomFilter()
        filtered, stats = filter.filter_games([])
        
        assert len(filtered) == 0
        assert stats.total_games == 0
        assert stats.unique_games == 0
    
    def test_single_game(self):
        """Test filtering single game."""
        games = [
            DatGame(id=1, name="Game (USA)", rom_name="game.rom", crc="111", size=1000),
        ]
        
        filter = OneGameOneRomFilter()
        filtered, stats = filter.filter_games(games)
        
        assert len(filtered) == 1
        assert stats.total_games == 1
        assert stats.unique_games == 1
        assert stats.filtered_games == 1
        assert stats.duplicates_removed == 0
    
    def test_statistics_accuracy(self, sample_games):
        """Test that statistics are accurate."""
        filter = OneGameOneRomFilter()
        _, stats = filter.filter_games(sample_games)
        
        assert stats.total_games == 5
        assert stats.unique_games == 3
        assert stats.filtered_games == 3
        assert stats.duplicates_removed == 2
        assert stats.parents_selected >= 0
        assert stats.clones_selected >= 0
        assert stats.parents_selected + stats.clones_selected == stats.filtered_games
    
    def test_clone_indicators(self):
        """Test various clone indicators."""
        clone_names = [
            "Game (USA) [!]",
            "Game (USA) [a]",
            "Game (USA) [b]",
            "Game (USA) [h]",
            "Game (USA) [t]",
            "Game (USA) [f]",
        ]
        
        filter = OneGameOneRomFilter()
        
        for name in clone_names:
            game = DatGame(id=1, name=name, rom_name="game.rom", crc="111", size=1000)
            assert not filter._is_parent(game), f"{name} should be detected as clone"
        
        # Parent should have no indicators
        parent = DatGame(id=1, name="Game (USA)", rom_name="game.rom", crc="111", size=1000)
        assert filter._is_parent(parent)
    
    def test_scoring_consistency(self):
        """Test that scoring is consistent and deterministic."""
        games = [
            DatGame(id=1, name="Game (USA)", rom_name="g1.rom", crc="111", size=1000),
            DatGame(id=2, name="Game (Europe)", rom_name="g2.rom", crc="222", size=1000),
        ]
        
        filter = OneGameOneRomFilter()
        
        # Score multiple times
        score1a = filter._score_game(games[0])
        score1b = filter._score_game(games[0])
        score2a = filter._score_game(games[1])
        score2b = filter._score_game(games[1])
        
        # Scores should be consistent
        assert score1a == score1b
        assert score2a == score2b
        
        # USA should score higher than Europe
        assert score1a > score2a
    
    def test_filter_by_dat_name(self):
        """Test filtering games from specific DAT."""
        dat1 = DatFile(id=1, name="DAT 1", description="First DAT", version="1.0")
        dat2 = DatFile(id=2, name="DAT 2", description="Second DAT", version="1.0")
        
        games = [
            DatGame(id=1, dat_file_id=1, name="Game (USA)", rom_name="g1.rom", crc="111", size=1000, dat_file=dat1),
            DatGame(id=2, dat_file_id=2, name="Game (USA)", rom_name="g2.rom", crc="222", size=1000, dat_file=dat2),
        ]
        
        filter = OneGameOneRomFilter()
        
        # Filter by DAT 1
        filtered, stats = filter.get_filtered_by_dat(games, dat_name="DAT 1")
        assert len(filtered) == 1
        assert filtered[0].dat_file.name == "DAT 1"
        
        # Filter by DAT 2
        filtered2, stats2 = filter.get_filtered_by_dat(games, dat_name="DAT 2")
        assert len(filtered2) == 1
        assert filtered2[0].dat_file.name == "DAT 2"
        
        # Filter all DATs
        filtered_all, stats_all = filter.get_filtered_by_dat(games, dat_name=None)
        assert len(filtered_all) == 1  # Should merge to one game
