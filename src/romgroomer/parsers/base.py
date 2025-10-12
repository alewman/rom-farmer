"""Base parser abstract class for ROM filename parsing."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Type

from romgroomer.models.rom import Rom


class BaseParser(ABC):
    """
    Abstract base class for ROM filename parsers.
    
    Each parser implementation handles a specific naming convention
    (No-Intro, Redump, TOSEC, etc.) and extracts metadata from filenames.
    """
    
    # Parser metadata
    name: str = "base"
    description: str = "Base ROM parser"
    supported_extensions: set[str] = set()
    
    @abstractmethod
    def parse(self, filepath: Path) -> Rom:
        """
        Parse a ROM filename and extract metadata.
        
        Args:
            filepath: Path to ROM file
            
        Returns:
            Rom object with parsed metadata
            
        Raises:
            ValueError: If filename cannot be parsed
        """
        pass
    
    @abstractmethod
    def format_filename(self, rom: Rom, include_extension: bool = True) -> str:
        """
        Format a ROM object back into filename format.
        
        Args:
            rom: ROM object to format
            include_extension: Include file extension
            
        Returns:
            Formatted filename string
        """
        pass
    
    def can_parse(self, filepath: Path) -> bool:
        """
        Check if this parser can handle the given file.
        
        Args:
            filepath: Path to check
            
        Returns:
            True if parser can handle this file
        """
        ext = filepath.suffix.lower()
        return ext in self.supported_extensions if self.supported_extensions else True
    
    def validate(self, rom: Rom) -> bool:
        """
        Validate that ROM has required metadata.
        
        Args:
            rom: ROM to validate
            
        Returns:
            True if ROM is valid
        """
        return bool(rom.name and rom.filename)


# Parser registry
_PARSERS: Dict[str, Type[BaseParser]] = {}


def register_parser(name: str, parser_class: Type[BaseParser]) -> None:
    """
    Register a parser implementation.
    
    Args:
        name: Parser name (e.g., "nointro", "redump")
        parser_class: Parser class to register
    """
    _PARSERS[name] = parser_class


def get_parser(name: str) -> BaseParser:
    """
    Get a parser instance by name.
    
    Args:
        name: Parser name (e.g., "nointro", "redump")
        
    Returns:
        Parser instance
        
    Raises:
        ValueError: If parser not found
    """
    if name not in _PARSERS:
        available = ", ".join(_PARSERS.keys())
        raise ValueError(f"Parser '{name}' not found. Available: {available}")
    
    return _PARSERS[name]()


def get_parser_for_file(filepath: Path) -> Optional[BaseParser]:
    """
    Auto-detect appropriate parser for a file.
    
    Args:
        filepath: Path to ROM file
        
    Returns:
        Parser instance, or None if no parser can handle the file
    """
    for parser_class in _PARSERS.values():
        parser = parser_class()
        if parser.can_parse(filepath):
            return parser
    
    return None


def list_parsers() -> Dict[str, str]:
    """
    List all registered parsers.
    
    Returns:
        Dictionary of parser names to descriptions
    """
    return {
        name: parser_class().description
        for name, parser_class in _PARSERS.items()
    }
