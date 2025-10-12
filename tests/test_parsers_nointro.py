"""Tests for No-Intro parser."""

import pytest
from pathlib import Path
from romgroomer.parsers.nointro import NoIntroParser
from romgroomer.models.rom import RomRegion, RomLanguage, RomKind


class TestNoIntroParser:
    """Test suite for No-Intro filename parser."""
    
    @pytest.fixture
    def parser(self) -> NoIntroParser:
        """Create parser instance."""
        return NoIntroParser()
    
    def test_simple_usa_rom(self, parser: NoIntroParser, tmp_path: Path) -> None:
        """Test parsing simple USA ROM."""
        rom_file = tmp_path / "Super Mario Bros. (USA).nes"
        rom_file.touch()
        
        rom = parser.parse(rom_file)
        
        assert rom.name == "Super Mario Bros."
        assert rom.regions == [RomRegion.USA]
        assert rom.languages == []
        assert rom.kind == RomKind.GAME
        assert rom.revision is None
        assert rom.version is None
    
    def test_multi_region_rom(self, parser: NoIntroParser, tmp_path: Path) -> None:
        """Test parsing ROM with multiple regions."""
        rom_file = tmp_path / "Legend of Zelda, The (USA, Europe).nes"
        rom_file.touch()
        
        rom = parser.parse(rom_file)
        
        assert rom.name == "Legend of Zelda, The"
        assert RomRegion.USA in rom.regions
        assert RomRegion.EUROPE in rom.regions
        assert len(rom.regions) == 2
    
    def test_multi_language_rom(self, parser: NoIntroParser, tmp_path: Path) -> None:
        """Test parsing ROM with multiple languages."""
        rom_file = tmp_path / "Final Fantasy (Japan) (En,Fr,De,Es,It).nes"
        rom_file.touch()
        
        rom = parser.parse(rom_file)
        
        assert rom.name == "Final Fantasy"
        assert rom.regions == [RomRegion.JAPAN]
        assert RomLanguage.ENGLISH in rom.languages
        assert RomLanguage.FRENCH in rom.languages
        assert RomLanguage.GERMAN in rom.languages
        assert RomLanguage.SPANISH in rom.languages
        assert RomLanguage.ITALIAN in rom.languages
        assert len(rom.languages) == 5
    
    def test_revision_rom(self, parser: NoIntroParser, tmp_path: Path) -> None:
        """Test parsing ROM with revision."""
        rom_file = tmp_path / "Pokemon Red (USA, Europe) (Rev A).gb"
        rom_file.touch()
        
        rom = parser.parse(rom_file)
        
        assert rom.name == "Pokemon Red"
        assert rom.revision == "Rev A"
    
    def test_version_rom(self, parser: NoIntroParser, tmp_path: Path) -> None:
        """Test parsing ROM with version."""
        rom_file = tmp_path / "Tetris (World) (v1.1).gb"
        rom_file.touch()
        
        rom = parser.parse(rom_file)
        
        assert rom.name == "Tetris"
        assert rom.version == "v1.1"
    
    def test_multi_disc_rom(self, parser: NoIntroParser, tmp_path: Path) -> None:
        """Test parsing multi-disc ROM."""
        rom_file = tmp_path / "Final Fantasy VII (USA) (Disc 1).bin"
        rom_file.touch()
        
        rom = parser.parse(rom_file)
        
        assert rom.name == "Final Fantasy VII"
        assert rom.disc_number == 1
        assert rom.disc_total is None
        
        # Test with total
        rom_file2 = tmp_path / "Final Fantasy VII (USA) (Disc 1 of 3).bin"
        rom_file2.touch()
        
        rom2 = parser.parse(rom_file2)
        assert rom2.disc_number == 1
        assert rom2.disc_total == 3
    
    def test_rom_with_tags(self, parser: NoIntroParser, tmp_path: Path) -> None:
        """Test parsing ROM with various tags."""
        rom_file = tmp_path / "Super Game Boy (World) (SGB Enhanced).gb"
        rom_file.touch()
        
        rom = parser.parse(rom_file)
        
        assert rom.name == "Super Game Boy"
        assert "SGB Enhanced" in rom.tags
    
    def test_application_kind(self, parser: NoIntroParser, tmp_path: Path) -> None:
        """Test parsing application ROM."""
        rom_file = tmp_path / "Game Boy Camera (USA, Europe) (Application).gb"
        rom_file.touch()
        
        rom = parser.parse(rom_file)
        
        assert rom.kind == RomKind.APPLICATION
        assert "Application" in rom.tags
    
    def test_demo_kind(self, parser: NoIntroParser, tmp_path: Path) -> None:
        """Test parsing demo ROM."""
        rom_file = tmp_path / "Sonic Demo (USA) (Demo).gen"
        rom_file.touch()
        
        rom = parser.parse(rom_file)
        
        assert rom.kind == RomKind.DEMO
        assert "Demo" in rom.tags
    
    def test_format_filename(self, parser: NoIntroParser, tmp_path: Path) -> None:
        """Test formatting ROM back to filename."""
        rom_file = tmp_path / "Super Mario Bros. (USA, Europe) (Rev 1).nes"
        rom_file.touch()
        
        rom = parser.parse(rom_file)
        formatted = parser.format_filename(rom)
        
        # Should produce similar filename (order may vary slightly)
        assert "Super Mario Bros." in formatted
        assert "(USA, Europe)" in formatted or "(Usa, Europe)" in formatted
        assert "(Rev 1)" in formatted
        assert ".nes" in formatted
    
    def test_complex_rom_name(self, parser: NoIntroParser, tmp_path: Path) -> None:
        """Test parsing ROM with complex name."""
        rom_file = tmp_path / "Legend of Zelda, The - A Link to the Past (USA).sfc"
        rom_file.touch()
        
        rom = parser.parse(rom_file)
        
        assert rom.name == "Legend of Zelda, The - A Link to the Past"
        assert rom.regions == [RomRegion.USA]
    
    def test_world_region(self, parser: NoIntroParser, tmp_path: Path) -> None:
        """Test parsing ROM with World region."""
        rom_file = tmp_path / "Tetris (World).gb"
        rom_file.touch()
        
        rom = parser.parse(rom_file)
        
        assert rom.regions == [RomRegion.WORLD]
    
    def test_rom_properties(self, parser: NoIntroParser, tmp_path: Path) -> None:
        """Test ROM property helpers."""
        rom_file = tmp_path / "Pokemon Red (USA, Europe) (En,Fr,De).gb"
        rom_file.touch()
        
        rom = parser.parse(rom_file)
        
        assert rom.has_multiple_regions is True
        assert rom.has_multiple_languages is True
        assert rom.primary_region == RomRegion.USA
        assert rom.primary_language == RomLanguage.ENGLISH
        assert rom.has_region(RomRegion.USA) is True
        assert rom.has_region(RomRegion.JAPAN) is False
        assert rom.has_language(RomLanguage.ENGLISH) is True
        assert rom.has_language(RomLanguage.JAPANESE) is False
