"""NoPayStation database loader and query interface.

Provides unified access to all NoPayStation TSV databases across platforms.
Handles platform-specific differences (RAP vs zRIF) and builds indices for fast lookups.
"""

import csv
from pathlib import Path
from typing import List, Dict, Optional, Set
from collections import defaultdict

from .nps_models import ContentEntry, TitleBundle


class NPSDatabase:
    """Unified database access for NoPayStation content.
    
    Loads and indexes TSV databases for fast querying across all platforms.
    Supports: PS3, Vita, PSP, PSX, PSM
    Content types: Games, DLC, Updates, Themes, Demos, Avatars
    """
    
    # Region mapping: Content ID prefix → Region code
    REGION_MAP = {
        'UP': 'USA', 'UC': 'USA',  # PS3/Vita USA
        'EP': 'EUR',                # PS3/Vita Europe
        'HP': 'JPN', 'JP': 'JPN', 'NP': 'JPN',  # PS3/Vita Japan
        'KP': 'ASI',                # PS3/Vita Asia
    }
    
    # Database file mapping: (platform, type) → filename
    DATABASE_FILES = {
        ('ps3', 'games'): 'PS3_GAMES.tsv',
        ('ps3', 'dlc'): 'PS3_DLCS.tsv',
        ('ps3', 'updates'): 'PS3_UPDATES.tsv',
        ('ps3', 'themes'): 'PS3_THEMES.tsv',
        ('ps3', 'avatars'): 'PS3_AVATARS.tsv',
        
        ('vita', 'games'): 'PSV_GAMES.tsv',
        ('vita', 'dlc'): 'PSV_DLCS.tsv',
        ('vita', 'updates'): 'PSV_UPDATES.tsv',
        ('vita', 'themes'): 'PSV_THEMES.tsv',
        ('vita', 'demos'): 'PSV_DEMOS.tsv',
        
        ('psp', 'games'): 'PSP_GAMES.tsv',
        ('psp', 'dlc'): 'PSP_DLCS.tsv',
        ('psp', 'updates'): 'PSP_UPDATES.tsv',
        ('psp', 'themes'): 'PSP_THEMES.tsv',
        
        ('psx', 'games'): 'PSX_GAMES.tsv',
        
        ('psm', 'games'): 'PSM_GAMES.tsv',
    }
    
    def __init__(self, database_dir: Path):
        """Initialize database loader.
        
        Args:
            database_dir: Directory containing TSV database files
        """
        self.database_dir = Path(database_dir)
        
        # Storage
        self.entries: List[ContentEntry] = []
        
        # Indices for fast lookup
        self.title_id_index: Dict[str, List[ContentEntry]] = defaultdict(list)
        self.content_id_index: Dict[str, ContentEntry] = {}
        self.name_index: Dict[str, List[ContentEntry]] = defaultdict(list)
        
        # Platform/type tracking
        self.platforms_loaded: Set[str] = set()
        self.types_loaded: Set[str] = set()
    
    def load_platform(self, platform: str, types: Optional[List[str]] = None):
        """Load databases for a specific platform.
        
        Args:
            platform: Platform name (ps3, vita, psp, psx, psm)
            types: Content types to load (games, dlc, updates, etc.)
                   If None, loads all available types for platform
        """
        platform = platform.lower()
        
        # Determine which types to load
        if types is None:
            # Load all types available for this platform
            types_to_load = [
                content_type
                for (p, content_type) in self.DATABASE_FILES.keys()
                if p == platform
            ]
        else:
            types_to_load = [t.lower() for t in types]
        
        # Load each database
        for content_type in types_to_load:
            db_key = (platform, content_type)
            if db_key not in self.DATABASE_FILES:
                print(f"  Warning: No database for {platform}/{content_type}")
                continue
            
            filename = self.DATABASE_FILES[db_key]
            db_path = self.database_dir / filename
            
            if not db_path.exists():
                print(f"  Warning: Database not found: {db_path}")
                continue
            
            self._load_database_file(db_path, platform, content_type)
        
        # Build indices after loading
        self._build_indices()
        
        self.platforms_loaded.add(platform)
    
    def _load_database_file(self, db_path: Path, platform: str, content_type: str):
        """Load a single TSV database file.
        
        Args:
            db_path: Path to TSV file
            platform: Platform name
            content_type: Content type
        """
        print(f"  Loading {db_path.name}...", end=' ')
        
        count = 0
        with open(db_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            
            for row in reader:
                # Extract common fields
                title_id = row.get('Title ID', '').strip()
                content_id = row.get('Content ID', '').strip()
                name = row.get('Name', '').strip()
                pkg_url = row.get('PKG direct link', '').strip()
                
                # Skip entries without essential fields
                if not (title_id and content_id and name and pkg_url):
                    continue
                
                # Extract region from Content ID
                region = self._get_region_from_content_id(content_id)
                
                # Get license key (platform-dependent)
                if platform in ('vita', 'psm'):
                    license_key = row.get('zRIF', '').strip()
                else:  # ps3, psp, psx
                    license_key = row.get('RAP', '').strip()
                
                # Parse file size
                file_size_str = row.get('File Size', '0').strip()
                try:
                    file_size = int(file_size_str) if file_size_str else 0
                except ValueError:
                    file_size = 0
                
                # Get SHA256
                sha256 = row.get('SHA256', '').strip()
                
                # Get optional fields
                version = row.get('App Version') or row.get('Version')
                min_firmware = row.get('Minimum Firmware') or row.get('FW')
                
                # Create entry
                entry = ContentEntry(
                    platform=platform,
                    content_type=content_type,
                    title_id=title_id,
                    content_id=content_id,
                    name=name,
                    region=region,
                    pkg_url=pkg_url,
                    license_key=license_key if license_key else None,
                    file_size=file_size,
                    sha256=sha256 if sha256 else None,
                    version=version,
                    min_firmware=min_firmware,
                )
                
                self.entries.append(entry)
                count += 1
        
        print(f"{count:,} entries")
        self.types_loaded.add(content_type)
    
    def _build_indices(self):
        """Build lookup indices for fast querying."""
        self.title_id_index.clear()
        self.content_id_index.clear()
        self.name_index.clear()
        
        for entry in self.entries:
            # Index by Title ID
            self.title_id_index[entry.title_id].append(entry)
            
            # Index by Content ID
            self.content_id_index[entry.content_id] = entry
            
            # Index by name (normalized for fuzzy search)
            normalized_name = self._normalize_name(entry.name)
            self.name_index[normalized_name].append(entry)
    
    def _normalize_name(self, name: str) -> str:
        """Normalize name for fuzzy matching."""
        # Remove special characters, lowercase, collapse whitespace
        normalized = name.lower()
        normalized = normalized.replace('®', '').replace('™', '').replace('©', '')
        normalized = normalized.replace(':', ' ').replace('-', ' ')
        normalized = ' '.join(normalized.split())
        return normalized
    
    def _get_region_from_content_id(self, content_id: str) -> Optional[str]:
        """Extract region from Content ID prefix.
        
        Args:
            content_id: Content ID (e.g., UP2058-PCSE00065_00-GAME000000000001)
            
        Returns:
            Region code (USA, EUR, JPN, ASI) or None
        """
        if not content_id or len(content_id) < 2:
            return None
        
        prefix = content_id[:2].upper()
        return self.REGION_MAP.get(prefix)
    
    def get_by_title_id(self, title_id: str, platform: Optional[str] = None) -> List[ContentEntry]:
        """Get all content for a Title ID.
        
        Args:
            title_id: Title ID to search for
            platform: Optional platform filter
            
        Returns:
            List of matching entries
        """
        results = self.title_id_index.get(title_id, [])
        
        if platform:
            platform = platform.lower()
            results = [e for e in results if e.platform == platform]
        
        return results
    
    def get_by_content_id(self, content_id: str) -> Optional[ContentEntry]:
        """Get entry by exact Content ID.
        
        Args:
            content_id: Content ID to search for
            
        Returns:
            Matching entry or None
        """
        return self.content_id_index.get(content_id)
    
    def search(
        self,
        query: str,
        platform: Optional[str] = None,
        content_type: Optional[str] = None,
        region: Optional[str] = None,
        limit: int = 50
    ) -> List[ContentEntry]:
        """Search for content by name.
        
        Args:
            query: Search query (fuzzy matched)
            platform: Optional platform filter
            content_type: Optional type filter
            region: Optional region filter
            limit: Maximum results
            
        Returns:
            List of matching entries, sorted by relevance
        """
        normalized_query = self._normalize_name(query)
        query_words = set(normalized_query.split())
        
        # Search name index
        matches = []
        for name, entries in self.name_index.items():
            # Check if query words appear in name
            name_words = set(name.split())
            if query_words & name_words:  # Intersection
                score = len(query_words & name_words) / len(query_words)
                matches.extend([(entry, score) for entry in entries])
        
        # Apply filters
        if platform:
            platform = platform.lower()
            matches = [(e, s) for e, s in matches if e.platform == platform]
        
        if content_type:
            content_type = content_type.lower()
            matches = [(e, s) for e, s in matches if e.content_type == content_type]
        
        if region:
            region = region.upper()
            matches = [(e, s) for e, s in matches if e.region == region]
        
        # Sort by score and limit
        matches.sort(key=lambda x: x[1], reverse=True)
        results = [entry for entry, score in matches[:limit]]
        
        return results
    
    def build_title_bundle(self, title_id: str, platform: str, region: Optional[str] = None) -> Optional[TitleBundle]:
        """Build complete TitleBundle for a Title ID.
        
        Gathers all related content (base game, DLC, updates, etc.)
        
        Args:
            title_id: Title ID
            platform: Platform
            region: Optional region filter
            
        Returns:
            TitleBundle or None if no content found
        """
        entries = self.get_by_title_id(title_id, platform)
        
        if not entries:
            return None
        
        # Filter by region if specified
        if region:
            region = region.upper()
            entries = [e for e in entries if e.region == region]
            
            if not entries:
                return None
        
        # Use region from first entry if not specified
        if not region:
            region = entries[0].region
        
        # Organize by type
        bundle = TitleBundle(
            title_id=title_id,
            platform=platform,
            region=region,
        )
        
        for entry in entries:
            if entry.content_type == 'games':
                bundle.base_game = entry
            elif entry.content_type == 'dlc':
                bundle.dlc.append(entry)
            elif entry.content_type == 'updates':
                bundle.updates.append(entry)
            elif entry.content_type == 'themes':
                bundle.themes.append(entry)
            elif entry.content_type == 'demos':
                bundle.demos.append(entry)
            elif entry.content_type == 'avatars':
                bundle.avatars.append(entry)
        
        return bundle
    
    def get_stats(self) -> dict:
        """Get database statistics.
        
        Returns:
            Statistics dict
        """
        stats = {
            'total_entries': len(self.entries),
            'platforms': list(self.platforms_loaded),
            'types': list(self.types_loaded),
            'by_platform': defaultdict(int),
            'by_type': defaultdict(int),
            'by_region': defaultdict(int),
        }
        
        for entry in self.entries:
            stats['by_platform'][entry.platform] += 1
            stats['by_type'][entry.content_type] += 1
            if entry.region:
                stats['by_region'][entry.region] += 1
        
        return dict(stats)
