"""Pydantic models for ROM data structures."""

from enum import Enum
from pathlib import Path
from typing import Optional, List, Set
from pydantic import BaseModel, Field, field_validator


class RomRegion(str, Enum):
    """Standard ROM regions based on No-Intro conventions."""
    
    ARGENTINA = "argentina"
    ASIA = "asia"
    AUSTRALIA = "australia"
    BRAZIL = "brazil"
    CANADA = "canada"
    CHINA = "china"
    DENMARK = "denmark"
    EUROPE = "europe"
    FINLAND = "finland"
    FRANCE = "france"
    GERMANY = "germany"
    GREECE = "greece"
    HONG_KONG = "hong kong"
    ITALY = "italy"
    JAPAN = "japan"
    KOREA = "korea"
    LATIN_AMERICA = "latin america"
    NETHERLANDS = "netherlands"
    NORWAY = "norway"
    POLAND = "poland"
    RUSSIA = "russia"
    SCANDINAVIA = "scandinavia"
    SPAIN = "spain"
    SWEDEN = "sweden"
    TAIWAN = "taiwan"
    UK = "uk"
    UNKNOWN = "unknown"
    USA = "usa"
    WORLD = "world"
    
    @classmethod
    def from_string(cls, value: str) -> "RomRegion":
        """Convert string to RomRegion, handling variations."""
        value_lower = value.lower().strip()
        
        # Direct match
        try:
            return cls(value_lower)
        except ValueError:
            pass
        
        # Common variations
        variations = {
            "us": cls.USA,
            "united states": cls.USA,
            "eu": cls.EUROPE,
            "jp": cls.JAPAN,
            "kr": cls.KOREA,
            "cn": cls.CHINA,
            "tw": cls.TAIWAN,
            "hk": cls.HONG_KONG,
            "au": cls.AUSTRALIA,
            "ca": cls.CANADA,
            "gb": cls.UK,
            "united kingdom": cls.UK,
            "de": cls.GERMANY,
            "fr": cls.FRANCE,
            "es": cls.SPAIN,
            "it": cls.ITALY,
            "nl": cls.NETHERLANDS,
            "se": cls.SWEDEN,
            "no": cls.NORWAY,
            "dk": cls.DENMARK,
            "fi": cls.FINLAND,
            "pl": cls.POLAND,
            "ru": cls.RUSSIA,
        }
        
        return variations.get(value_lower, cls.UNKNOWN)


class RomLanguage(str, Enum):
    """Standard ROM languages based on No-Intro conventions."""
    
    ARABIC = "arabic"
    CHINESE = "chinese"
    DANISH = "danish"
    DUTCH = "dutch"
    ENGLISH = "english"
    FINNISH = "finnish"
    FRENCH = "french"
    GERMAN = "german"
    GREEK = "greek"
    ITALIAN = "italian"
    JAPANESE = "japanese"
    KOREAN = "korean"
    NORWEGIAN = "norwegian"
    POLISH = "polish"
    PORTUGUESE = "portuguese"
    RUSSIAN = "russian"
    SPANISH = "spanish"
    SWEDISH = "swedish"
    
    @classmethod
    def from_code(cls, code: str) -> Optional["RomLanguage"]:
        """Convert language code to RomLanguage."""
        code_lower = code.lower().strip()
        
        code_map = {
            "ar": cls.ARABIC,
            "zh": cls.CHINESE,
            "da": cls.DANISH,
            "nl": cls.DUTCH,
            "en": cls.ENGLISH,
            "fi": cls.FINNISH,
            "fr": cls.FRENCH,
            "de": cls.GERMAN,
            "el": cls.GREEK,
            "it": cls.ITALIAN,
            "ja": cls.JAPANESE,
            "ko": cls.KOREAN,
            "no": cls.NORWEGIAN,
            "pl": cls.POLISH,
            "pt": cls.PORTUGUESE,
            "ru": cls.RUSSIAN,
            "es": cls.SPANISH,
            "sv": cls.SWEDISH,
        }
        
        return code_map.get(code_lower)


class RomKind(str, Enum):
    """ROM kind/category based on No-Intro tags."""
    
    GAME = "Games"
    APPLICATION = "Applications"
    AUDIO = "Audio"
    DEMO = "Demos"
    EDUCATIONAL = "Educational"
    MULTIMEDIA = "Multimedia"
    PRERELEASE = "Prerelease"
    PROMOTIONAL = "Promotional"
    VIDEO = "Video"
    
    @classmethod
    def from_tags(cls, tags: Set[str]) -> "RomKind":
        """Determine kind from ROM tags."""
        tags_lower = {tag.lower() for tag in tags}
        
        # Check for specific kinds
        if any(t in tags_lower for t in ["application", "check program", "enhancement chip"]):
            return cls.APPLICATION
        if any(t in tags_lower for t in ["audio", "music"]):
            return cls.AUDIO
        if any(t in tags_lower for t in ["demo", "sample"]):
            return cls.DEMO
        if "educational" in tags_lower:
            return cls.EDUCATIONAL
        if "multimedia" in tags_lower:
            return cls.MULTIMEDIA
        if any(t in tags_lower for t in ["prerelease", "proto", "beta", "sample"]):
            return cls.PRERELEASE
        if any(t in tags_lower for t in ["promo", "promotional"]):
            return cls.PROMOTIONAL
        if "video" in tags_lower:
            return cls.VIDEO
        
        return cls.GAME


class Rom(BaseModel):
    """
    Comprehensive ROM model with metadata.
    
    This model represents a single ROM file with all its metadata,
    including regions, languages, tags, hashes, etc.
    """
    
    # File information
    path: Path = Field(description="Full path to ROM file")
    filename: str = Field(description="Original filename")
    size: int = Field(description="File size in bytes")
    
    # Parsed metadata
    name: str = Field(description="Game name (without tags)")
    regions: List[RomRegion] = Field(default_factory=list, description="ROM regions")
    languages: List[RomLanguage] = Field(default_factory=list, description="ROM languages")
    kind: RomKind = Field(default=RomKind.GAME, description="ROM kind/category")
    
    # Tags and attributes
    revision: Optional[str] = Field(default=None, description="Revision (Rev 1, Rev A, etc)")
    version: Optional[str] = Field(default=None, description="Version (v1.0, v1.1, etc)")
    tags: Set[str] = Field(default_factory=set, description="Additional tags")
    
    # Multi-disc information
    disc_number: Optional[int] = Field(default=None, description="Disc number for multi-disc sets")
    disc_total: Optional[int] = Field(default=None, description="Total discs in set")
    disc_name: Optional[str] = Field(default=None, description="Disc name/label")
    
    # Hashes (from DAT files)
    crc32: Optional[str] = Field(default=None, description="CRC32 hash")
    md5: Optional[str] = Field(default=None, description="MD5 hash")
    sha1: Optional[str] = Field(default=None, description="SHA1 hash")
    
    # DAT file information
    dat_name: Optional[str] = Field(default=None, description="Source DAT file name")
    dat_description: Optional[str] = Field(default=None, description="Description from DAT")
    category: Optional[str] = Field(default=None, description="Category from DAT")
    
    @field_validator("path")
    @classmethod
    def validate_path(cls, v: Path) -> Path:
        """Ensure path is absolute."""
        return v.resolve()
    
    @property
    def extension(self) -> str:
        """Get file extension."""
        return self.path.suffix.lower()
    
    @property
    def has_multiple_regions(self) -> bool:
        """Check if ROM has multiple regions."""
        return len(self.regions) > 1
    
    @property
    def has_multiple_languages(self) -> bool:
        """Check if ROM has multiple languages."""
        return len(self.languages) > 1
    
    @property
    def is_multi_disc(self) -> bool:
        """Check if ROM is part of a multi-disc set."""
        return self.disc_number is not None and self.disc_total is not None
    
    @property
    def primary_region(self) -> Optional[RomRegion]:
        """Get primary region (first in list)."""
        return self.regions[0] if self.regions else None
    
    @property
    def primary_language(self) -> Optional[RomLanguage]:
        """Get primary language (first in list)."""
        return self.languages[0] if self.languages else None
    
    def has_region(self, region: RomRegion) -> bool:
        """Check if ROM includes a specific region."""
        return region in self.regions
    
    def has_language(self, language: RomLanguage) -> bool:
        """Check if ROM includes a specific language."""
        return language in self.languages
    
    def has_tag(self, tag: str) -> bool:
        """Check if ROM has a specific tag (case-insensitive)."""
        tag_lower = tag.lower()
        return any(t.lower() == tag_lower for t in self.tags)


class DatGame(BaseModel):
    """Game entry from a DAT file."""
    
    name: str = Field(description="Game name")
    description: Optional[str] = Field(default=None, description="Game description")
    category: Optional[str] = Field(default=None, description="Game category")
    
    # ROM information
    rom_name: str = Field(description="ROM filename")
    size: int = Field(description="ROM size in bytes")
    crc: str = Field(description="CRC32 hash")
    md5: Optional[str] = Field(default=None, description="MD5 hash")
    sha1: Optional[str] = Field(default=None, description="SHA1 hash")
    
    # DAT metadata
    dat_name: str = Field(description="Source DAT name")
    dat_version: Optional[str] = Field(default=None, description="DAT version")


class OrganizationResult(BaseModel):
    """Result of ROM organization operation."""
    
    rom: Rom = Field(description="ROM that was organized")
    destination: Path = Field(description="Final destination path")
    symlinks: List[Path] = Field(default_factory=list, description="Symlinks created")
    skipped: bool = Field(default=False, description="Whether ROM was skipped")
    skip_reason: Optional[str] = Field(default=None, description="Reason for skipping")
    error: Optional[str] = Field(default=None, description="Error message if failed")
