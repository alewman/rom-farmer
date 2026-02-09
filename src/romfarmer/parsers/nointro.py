"""No-Intro filename parser with comprehensive tag support."""

import re
from pathlib import Path
from typing import Optional, Set, List, Tuple
from romfarmer.models.rom import Rom, RomRegion, RomLanguage, RomKind
from romfarmer.parsers.base import BaseParser, register_parser


class NoIntroParser(BaseParser):
    """
    Parser for No-Intro filename conventions.
    
    No-Intro format: Game Name (Region1, Region2) (Language1, Language2) (Tags) (Rev X) (Version).ext
    
    Examples:
        "Super Mario Bros. (USA).nes"
        "Legend of Zelda, The (USA, Europe).nes"
        "Pokemon Red (USA, Europe) (SGB Enhanced) (Rev A).gb"
        "Final Fantasy (Japan) (En,Fr,De,Es,It) (Rev 1).nes"
    """
    
    # Parser metadata
    name = "nointro"
    description = "No-Intro naming convention parser"
    supported_extensions = {
        # Cartridge-based
        ".nes", ".fds", ".smc", ".sfc", ".gb", ".gbc", ".gba",
        ".z64", ".n64", ".v64", ".gen", ".md", ".sms", ".gg",
        ".pce", ".ngp", ".ngc", ".ws", ".wsc", ".a26", ".a52",
        ".a78", ".lnx", ".j64", ".col", ".int", ".vec",
        # Compressed
        ".zip", ".7z", ".rar",
    }
    
    # Region patterns
    REGION_PATTERN = re.compile(r'\(([^)]+)\)')
    
    # Language codes in No-Intro format
    LANGUAGE_CODES = {
        "ar": RomLanguage.ARABIC,
        "zh": RomLanguage.CHINESE,
        "da": RomLanguage.DANISH,
        "nl": RomLanguage.DUTCH,
        "en": RomLanguage.ENGLISH,
        "fi": RomLanguage.FINNISH,
        "fr": RomLanguage.FRENCH,
        "de": RomLanguage.GERMAN,
        "el": RomLanguage.GREEK,
        "it": RomLanguage.ITALIAN,
        "ja": RomLanguage.JAPANESE,
        "ko": RomLanguage.KOREAN,
        "no": RomLanguage.NORWEGIAN,
        "pl": RomLanguage.POLISH,
        "pt": RomLanguage.PORTUGUESE,
        "ru": RomLanguage.RUSSIAN,
        "es": RomLanguage.SPANISH,
        "sv": RomLanguage.SWEDISH,
    }
    
    # Known tags that are not regions or languages
    KNOWN_TAGS = {
        "sgb enhanced", "cgb enhanced", "dmg-cgb", "dsi enhanced",
        "beta", "proto", "sample", "demo", "promo", "promotional",
        "unl", "licensed", "unlicensed", "pirate",
        "fixed", "hack", "translation", "aftermarket",
        "virtual console", "ique", "gamecube", "wii",
        "enhancement chip", "check program", "application",
        "bios", "program", "audio", "video", "multimedia",
    }
    
    def __init__(self):
        """Initialize parser."""
        pass
    
    def parse(self, filepath: Path) -> Rom:
        """
        Parse a ROM filename according to No-Intro conventions.
        
        Args:
            filepath: Path to ROM file
            
        Returns:
            Rom object with parsed metadata
        """
        filename = filepath.name
        name_without_ext = filepath.stem
        
        # Extract all parenthetical groups
        groups = self.REGION_PATTERN.findall(name_without_ext)
        
        # First group is usually regions, but could be part of name
        # Extract base name (everything before first parenthesis)
        match = re.match(r'^([^(]+)', name_without_ext)
        base_name = match.group(1).strip() if match else name_without_ext
        
        regions: List[RomRegion] = []
        languages: List[RomLanguage] = []
        tags: Set[str] = set()
        revision: Optional[str] = None
        version: Optional[str] = None
        disc_number: Optional[int] = None
        disc_total: Optional[int] = None
        disc_name: Optional[str] = None
        
        # Process each parenthetical group
        for group in groups:
            group_lower = group.lower().strip()
            
            # Check for revision (Rev X, Rev A)
            rev_match = re.match(r'rev(?:ision)?\s+([a-z0-9]+)', group_lower)
            if rev_match:
                revision = f"Rev {rev_match.group(1).upper()}"
                continue
            
            # Check for version (v1.0, v1.1)
            ver_match = re.match(r'v(\d+(?:\.\d+)*)', group_lower)
            if ver_match:
                version = f"v{ver_match.group(1)}"
                continue
            
            # Check for disc number (Disc 1, Disc 1 of 2)
            disc_match = re.match(r'disc\s+(\d+)(?:\s+of\s+(\d+))?(?:\s+-\s+(.+))?', group_lower)
            if disc_match:
                disc_number = int(disc_match.group(1))
                if disc_match.group(2):
                    disc_total = int(disc_match.group(2))
                if disc_match.group(3):
                    disc_name = disc_match.group(3).strip()
                continue
            
            # Check if it's a language code group (comma-separated codes)
            if self._is_language_group(group):
                langs = self._parse_languages(group)
                languages.extend(langs)
                continue
            
            # Check if it's a region group (comma-separated regions)
            parsed_regions = self._parse_regions(group)
            if parsed_regions:
                regions.extend(parsed_regions)
                continue
            
            # Check if it's a known tag
            if group_lower in self.KNOWN_TAGS:
                tags.add(group)
                continue
            
            # If none of the above, add as generic tag
            tags.add(group)
        
        # Determine kind from tags
        kind = RomKind.from_tags(tags)
        
        # Get file size
        size = filepath.stat().st_size if filepath.exists() else 0
        
        return Rom(
            path=filepath,
            filename=filename,
            size=size,
            name=base_name,
            regions=regions,
            languages=languages,
            kind=kind,
            revision=revision,
            version=version,
            tags=tags,
            disc_number=disc_number,
            disc_total=disc_total,
            disc_name=disc_name,
        )
    
    def _is_language_group(self, group: str) -> bool:
        """Check if a group contains language codes."""
        # Language groups are comma-separated 2-letter codes
        codes = [c.strip().lower() for c in group.split(',')]
        
        # Must have at least 2 codes and all must be valid language codes
        if len(codes) < 2:
            return False
        
        return all(c in self.LANGUAGE_CODES for c in codes)
    
    def _parse_languages(self, group: str) -> List[RomLanguage]:
        """Parse language codes from a group."""
        codes = [c.strip().lower() for c in group.split(',')]
        languages = []
        
        for code in codes:
            if code in self.LANGUAGE_CODES:
                languages.append(self.LANGUAGE_CODES[code])
        
        return languages
    
    def _parse_regions(self, group: str) -> List[RomRegion]:
        """Parse regions from a group."""
        region_strings = [r.strip() for r in group.split(',')]
        regions = []
        
        for region_str in region_strings:
            try:
                region = RomRegion.from_string(region_str)
                if region != RomRegion.UNKNOWN:
                    regions.append(region)
            except ValueError:
                # Not a valid region, might be a tag
                continue
        
        return regions
    
    def format_filename(self, rom: Rom, include_extension: bool = True) -> str:
        """
        Format a ROM object back into No-Intro filename format.
        
        Args:
            rom: ROM object to format
            include_extension: Include file extension
            
        Returns:
            Formatted filename string
        """
        parts = [rom.name]
        
        # Add regions
        if rom.regions:
            region_str = ", ".join(r.value.title() for r in rom.regions)
            parts.append(f"({region_str})")
        
        # Add languages
        if rom.languages:
            # Convert to codes
            lang_codes = []
            for lang in rom.languages:
                for code, language in self.LANGUAGE_CODES.items():
                    if language == lang:
                        lang_codes.append(code.upper())
                        break
            if lang_codes:
                parts.append(f"({','.join(lang_codes)})")
        
        # Add tags
        for tag in sorted(rom.tags):
            parts.append(f"({tag})")
        
        # Add revision
        if rom.revision:
            parts.append(f"({rom.revision})")
        
        # Add version
        if rom.version:
            parts.append(f"({rom.version})")
        
        # Add disc info
        if rom.disc_number is not None:
            if rom.disc_total is not None:
                disc_str = f"Disc {rom.disc_number} of {rom.disc_total}"
            else:
                disc_str = f"Disc {rom.disc_number}"
            
            if rom.disc_name:
                disc_str += f" - {rom.disc_name}"
            
            parts.append(f"({disc_str})")
        
        filename = " ".join(parts)
        
        if include_extension:
            filename += rom.extension
        
        return filename


# Register this parser
register_parser("nointro", NoIntroParser)
