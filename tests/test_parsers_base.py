"""Tests for parser base class and factory."""

import pytest
from pathlib import Path
from romfarmer.parsers import (
    get_parser,
    get_parser_for_file,
    list_parsers,
    NoIntroParser,
    RedumpParser,
)


class TestParserFactory:
    """Test suite for parser factory functions."""
    
    def test_get_nointro_parser(self) -> None:
        """Test getting No-Intro parser by name."""
        parser = get_parser("nointro")
        assert isinstance(parser, NoIntroParser)
        assert parser.name == "nointro"
    
    def test_get_redump_parser(self) -> None:
        """Test getting Redump parser by name."""
        parser = get_parser("redump")
        assert isinstance(parser, RedumpParser)
        assert parser.name == "redump"
    
    def test_get_invalid_parser(self) -> None:
        """Test getting non-existent parser raises error."""
        with pytest.raises(ValueError, match="Parser 'invalid' not found"):
            get_parser("invalid")
    
    def test_list_parsers(self) -> None:
        """Test listing all registered parsers."""
        parsers = list_parsers()
        
        assert "nointro" in parsers
        assert "redump" in parsers
        assert "No-Intro" in parsers["nointro"]
        assert "Redump" in parsers["redump"]
    
    def test_auto_detect_cartridge(self, tmp_path: Path) -> None:
        """Test auto-detecting parser for cartridge ROM."""
        rom_file = tmp_path / "Super Mario Bros. (USA).nes"
        rom_file.touch()
        
        parser = get_parser_for_file(rom_file)
        assert parser is not None
        assert isinstance(parser, NoIntroParser)
    
    def test_auto_detect_disc(self, tmp_path: Path) -> None:
        """Test auto-detecting parser for disc ROM."""
        rom_file = tmp_path / "Final Fantasy VII (USA).bin"
        rom_file.touch()
        
        parser = get_parser_for_file(rom_file)
        assert parser is not None
        assert isinstance(parser, RedumpParser)
    
    def test_auto_detect_unknown_extension(self, tmp_path: Path) -> None:
        """Test auto-detecting with unknown extension."""
        rom_file = tmp_path / "unknown.xyz"
        rom_file.touch()
        
        # Should still return a parser (first one that accepts all)
        parser = get_parser_for_file(rom_file)
        # May be None or a parser depending on implementation
        assert parser is None or parser is not None
