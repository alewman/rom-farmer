"""Data models for NoPayStation content."""

from dataclasses import dataclass, field
from typing import Optional, List
from pathlib import Path
from datetime import datetime
import json


@dataclass
class ContentEntry:
    """Single content entry from NoPayStation database.
    
    Represents a single row from any NPS database (games, DLC, updates, themes, etc.).
    Provides unified interface across all platforms.
    """
    
    # Identity
    platform: str              # ps3, vita, psp, psx, psm
    content_type: str          # games, dlc, updates, themes, demos, avatars
    title_id: str              # Base game identifier (e.g., PCSE00065)
    content_id: str            # Specific content ID (e.g., UP2058-PCSE00065_00-GAME000000000001)
    name: str                  # Human-readable name
    region: Optional[str]      # USA, EUR, JPN, ASI (extracted from Content ID)
    
    # Download information
    pkg_url: str              # Direct download URL
    license_key: Optional[str]  # RAP (hex) for PS3/PSP, zRIF (base64) for Vita/PSM
    
    # Verification
    file_size: int             # File size in bytes
    sha256: Optional[str]      # SHA256 hash (uppercase hex)
    
    # Metadata
    version: Optional[str] = None     # Game/update version
    min_firmware: Optional[str] = None  # Minimum firmware required
    
    def __post_init__(self):
        """Validate and normalize fields."""
        # Ensure platform is lowercase
        self.platform = self.platform.lower()
        
        # Ensure content_type is lowercase
        self.content_type = self.content_type.lower()
        
        # Uppercase SHA256 for consistency
        if self.sha256:
            self.sha256 = self.sha256.upper()
    
    def is_free(self) -> bool:
        """Check if content is free (no license key required)."""
        return not self.license_key or self.license_key in ('MISSING', 'NOT_NEEDED', '')
    
    def uses_zrif(self) -> bool:
        """Check if license uses zRIF format (Vita/PSM)."""
        return self.platform in ('vita', 'psm')
    
    def uses_rap(self) -> bool:
        """Check if license uses RAP format (PS3/PSP)."""
        return self.platform in ('ps3', 'psp')
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'platform': self.platform,
            'content_type': self.content_type,
            'title_id': self.title_id,
            'content_id': self.content_id,
            'name': self.name,
            'region': self.region,
            'pkg_url': self.pkg_url,
            'license_key': self.license_key,
            'file_size': self.file_size,
            'sha256': self.sha256,
            'version': self.version,
            'min_firmware': self.min_firmware,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ContentEntry':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class TitleBundle:
    """Complete collection for a Title ID (base game + DLC + updates + themes).
    
    Represents all content related to a single game, organized by type.
    Used for dependency resolution (--complete flag).
    """
    
    title_id: str
    platform: str
    region: str
    
    # Content organized by type
    base_game: Optional[ContentEntry] = None
    dlc: List[ContentEntry] = field(default_factory=list)
    updates: List[ContentEntry] = field(default_factory=list)
    themes: List[ContentEntry] = field(default_factory=list)
    demos: List[ContentEntry] = field(default_factory=list)
    avatars: List[ContentEntry] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate bundle."""
        # Ensure platform/region consistency
        self.platform = self.platform.lower()
        if self.region:
            self.region = self.region.upper()
    
    def get_all_content(self) -> List[ContentEntry]:
        """Get all content entries as flat list."""
        result = []
        if self.base_game:
            result.append(self.base_game)
        result.extend(self.dlc)
        result.extend(self.updates)
        result.extend(self.themes)
        result.extend(self.demos)
        result.extend(self.avatars)
        return result
    
    def get_total_size(self) -> int:
        """Calculate total download size in bytes."""
        return sum(entry.file_size for entry in self.get_all_content())
    
    def get_display_name(self) -> str:
        """Get displayable name for this bundle."""
        if self.base_game:
            return self.base_game.name
        elif self.dlc:
            return self.dlc[0].name.split(' - ')[0]  # Extract game name from DLC
        else:
            return self.title_id
    
    def count_by_type(self) -> dict:
        """Get count of content by type."""
        return {
            'base_game': 1 if self.base_game else 0,
            'dlc': len(self.dlc),
            'updates': len(self.updates),
            'themes': len(self.themes),
            'demos': len(self.demos),
            'avatars': len(self.avatars),
        }
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'title_id': self.title_id,
            'platform': self.platform,
            'region': self.region,
            'base_game': self.base_game.to_dict() if self.base_game else None,
            'dlc': [entry.to_dict() for entry in self.dlc],
            'updates': [entry.to_dict() for entry in self.updates],
            'themes': [entry.to_dict() for entry in self.themes],
            'demos': [entry.to_dict() for entry in self.demos],
            'avatars': [entry.to_dict() for entry in self.avatars],
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TitleBundle':
        """Create from dictionary."""
        return cls(
            title_id=data['title_id'],
            platform=data['platform'],
            region=data['region'],
            base_game=ContentEntry.from_dict(data['base_game']) if data.get('base_game') else None,
            dlc=[ContentEntry.from_dict(e) for e in data.get('dlc', [])],
            updates=[ContentEntry.from_dict(e) for e in data.get('updates', [])],
            themes=[ContentEntry.from_dict(e) for e in data.get('themes', [])],
            demos=[ContentEntry.from_dict(e) for e in data.get('demos', [])],
            avatars=[ContentEntry.from_dict(e) for e in data.get('avatars', [])],
        )


@dataclass
class DownloadMetadata:
    """Metadata for downloaded content (stored in .nps-metadata.json)."""
    
    platform: str
    region: str
    title_id: str
    
    # Download tracking
    base_game: Optional[dict] = None  # {content_id, name, size, downloaded, verified}
    dlc: List[dict] = field(default_factory=list)
    updates: List[dict] = field(default_factory=list)
    themes: List[dict] = field(default_factory=list)
    
    last_sync: Optional[str] = None  # ISO timestamp
    
    def save(self, output_path: Path):
        """Save metadata to JSON file."""
        data = {
            'platform': self.platform,
            'region': self.region,
            'title_id': self.title_id,
            'base_game': self.base_game,
            'dlc': self.dlc,
            'updates': self.updates,
            'themes': self.themes,
            'last_sync': self.last_sync or datetime.now().isoformat(),
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls, metadata_path: Path) -> 'DownloadMetadata':
        """Load metadata from JSON file."""
        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return cls(
            platform=data['platform'],
            region=data['region'],
            title_id=data['title_id'],
            base_game=data.get('base_game'),
            dlc=data.get('dlc', []),
            updates=data.get('updates', []),
            themes=data.get('themes', []),
            last_sync=data.get('last_sync'),
        )
