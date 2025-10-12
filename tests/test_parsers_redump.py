"""Tests for Redump parser."""

import pytest
from pathlib import Path
from romgroomer.parsers.redump import RedumpParser
from romgroomer.models.rom import RomRegion, RomLanguage, RomKind


class TestRedumpParser:
    """Test suite for Redump filename parser."""
    
    @pytest.fixture
    def parser(self) -> RedumpParser:
        """Create parser instance."""
        return RedumpParser()
    
    def test_simple_usa_disc(self, parser: RedumpParser, tmp_path: Path) -> None:
        """Test parsing simple USA disc."""
        rom_file = tmp_path / "Final Fantasy VII (USA) (Disc 1).bin"
        rom_file.touch()
        
        rom = parser.parse(rom_file)
        
        assert rom.name == "Final Fantasy VII"
        assert rom.regions == [RomRegion.USA]
        assert rom.disc_number == 1
        assert rom.kind == RomKind.GAME
    
    def test_multi_region_disc(self, parser: RedumpParser, tmp_path: Path) -> None:
        """Test parsing multi-region disc."""
        rom_file = tmp_path / "Metal Gear Solid (USA, Europe).bin"
        rom_file.touch()
        
        rom = parser.parse(rom_file)
        
        assert rom.name == "Metal Gear Solid"
        assert RomRegion.USA in rom.regions
        assert RomRegion.EUROPE in rom.regions
    
    def test_multi_language_disc(self, parser: RedumpParser, tmp_path: Path) -> None:
        """Test parsing multi-language disc."""
        rom_file = tmp_path / "Gran Turismo (Europe) (En,Fr,De,Es,It).bin"
        rom_file.touch()
        
        rom = parser.parse(rom_file)
        
        assert rom.name == "Gran Turismo"
        assert RomLanguage.ENGLISH in rom.languages
        assert RomLanguage.FRENCH in rom.languages
        assert RomLanguage.GERMAN in rom.languages
        assert len(rom.languages) == 5
    
    def test_revision_disc(self, parser: RedumpParser, tmp_path: Path) -> None:
        """Test parsing disc with revision."""
        rom_file = tmp_path / "Castlevania - Symphony of the Night (USA) (Rev 1).bin"
        rom_file.touch()
        
        rom = parser.parse(rom_file)
        
        assert rom.name == "Castlevania - Symphony of the Night"
        assert rom.revision == "Rev 1"
    
    def test_multi_disc_game(self, parser: RedumpParser, tmp_path: Path) -> None:
        """Test parsing multi-disc game."""
        rom_file1 = tmp_path / "Final Fantasy VIII (USA) (Disc 1).bin"
        rom_file2 = tmp_path / "Final Fantasy VIII (USA) (Disc 2).bin"
        rom_file1.touch()
        rom_file2.touch()
        
        rom1 = parser.parse(rom_file1)
        rom2 = parser.parse(rom_file2)
        
        assert rom1.name == "Final Fantasy VIII"
        assert rom1.disc_number == 1
        assert rom2.disc_number == 2
    
    def test_disc_with_name(self, parser: RedumpParser, tmp_path: Path) -> None:
        """Test parsing disc with named disc."""
        rom_file = tmp_path / "Game (USA) (Disc 1 - Install).bin"
        rom_file.touch()
        
        rom = parser.parse(rom_file)
        
        assert rom.disc_number == 1
        assert rom.disc_name == "install"  # Normalized to lowercase
    
    def test_demo_disc(self, parser: RedumpParser, tmp_path: Path) -> None:
        """Test parsing demo disc."""
        rom_file = tmp_path / "PlayStation Demo (USA) (Demo).bin"
        rom_file.touch()
        
        rom = parser.parse(rom_file)
        
        assert rom.kind == RomKind.DEMO
        assert "Demo" in rom.tags
    
    def test_format_filename(self, parser: RedumpParser, tmp_path: Path) -> None:
        """Test formatting disc back to filename."""
        rom_file = tmp_path / "Final Fantasy VII (USA) (Disc 1).bin"
        rom_file.touch()
        
        rom = parser.parse(rom_file)
        formatted = parser.format_filename(rom)
        
        assert "Final Fantasy VII" in formatted
        assert "(USA)" in formatted or "(Usa)" in formatted
        assert "(Disc 1)" in formatted
        assert ".bin" in formatted
    
    def test_can_parse_bin(self, parser: RedumpParser, tmp_path: Path) -> None:
        """Test that parser recognizes .bin files."""
        rom_file = tmp_path / "test.bin"
        assert parser.can_parse(rom_file) is True
    
    def test_can_parse_cue(self, parser: RedumpParser, tmp_path: Path) -> None:
        """Test that parser recognizes .cue files."""
        rom_file = tmp_path / "test.cue"
        assert parser.can_parse(rom_file) is True
    
    def test_can_parse_iso(self, parser: RedumpParser, tmp_path: Path) -> None:
        """Test that parser recognizes .iso files."""
        rom_file = tmp_path / "test.iso"
        assert parser.can_parse(rom_file) is True
    
    def test_parser_metadata(self, parser: RedumpParser) -> None:
        """Test parser metadata."""
        assert parser.name == "redump"
        assert "Redump" in parser.description
        assert ".bin" in parser.supported_extensions
        assert ".cue" in parser.supported_extensions
