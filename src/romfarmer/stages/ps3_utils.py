"""PS3 utilities for NoPayStation and Sony PSN integration.

This module provides:
- SonyPSNClient: Query Sony PSN servers for game updates
- NoPayStationDatabase: Parse and search NoPayStation TSV databases
"""

import csv
from pathlib import Path
from typing import Dict, List


class SonyPSNClient:
    """Query Sony PSN servers directly for PS3 game updates."""
    
    def __init__(self):
        """Initialize PSN client."""
        self.base_url = "https://a0.ww.np.dl.playstation.net/tpl/np"
    
    def get_updates_for_title(self, title_id: str) -> List[Dict]:
        """Query Sony servers for game updates.
        
        Args:
            title_id: PS3 title ID (e.g., "BLUS30982")
            
        Returns:
            List of update entries with PKG URLs
        """
        import requests
        import xml.etree.ElementTree as ET
        
        url = f"{self.base_url}/{title_id}/{title_id}-ver.xml"
        
        try:
            # Sony uses self-signed certs, disable verification
            response = requests.get(url, verify=False, timeout=10)
            
            if response.status_code != 200:
                return []
            
            # Parse XML response
            root = ET.fromstring(response.text)
            updates = []
            
            for package in root.findall('.//package'):
                version = package.get('version')
                size = package.get('size')
                sha1sum = package.get('sha1sum')
                pkg_url = package.get('url')
                
                if not pkg_url:
                    continue
                
                # Get title from PARAM.SFO
                title_elem = package.find('.//paramsfo/TITLE')
                title = title_elem.text if title_elem is not None else f"Update {version}"
                
                updates.append({
                    'Title ID': title_id,
                    'Name': title.strip(),
                    'PKG direct link': pkg_url,
                    'File Size': size,
                    'SHA1': sha1sum,
                    'RAP': 'NOT_NEEDED',  # Updates don't need RAP keys
                    'Version': version,
                    'Source': 'Sony PSN'
                })
            
            return updates
            
        except Exception as e:
            print(f"    PSN query error for {title_id}: {e}")
            return []


class NoPayStationDatabase:
    """Parse and search NoPayStation TSV database."""
    
    def __init__(self, tsv_path: Path):
        """Initialize database.
        
        Args:
            tsv_path: Path to PS3_DLCS.tsv file
        """
        self.tsv_path = Path(tsv_path)
        self.entries: List[Dict] = []
        self._load()
    
    def _load(self):
        """Load and parse TSV file."""
        if not self.tsv_path.exists():
            print(f"NoPayStation database not found: {self.tsv_path}")
            return
        
        print(f"Loading NoPayStation database: {self.tsv_path.name}")
        
        with open(self.tsv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                self.entries.append(row)
        
        print(f"  Loaded {len(self.entries)} DLC/update entries")
    
    def find_updates_for_title(self, title_id: str) -> List[Dict]:
        """Find all updates for a given title ID.
        
        Args:
            title_id: PS3 title ID (e.g., "BLUS31053")
            
        Returns:
            List of update entries (may be empty)
        """
        results = []
        
        for entry in self.entries:
            entry_title_id = entry.get('Title ID', '')
            name = entry.get('Name', '').lower()
            
            # Match title ID and filter for updates
            if entry_title_id == title_id:
                # Check if it's an update (not cosmetic DLC)
                if self._is_update(name, entry):
                    results.append(entry)
        
        return results
    
    def find_dlc_for_title(self, title_id: str) -> List[Dict]:
        """Find story/campaign DLC for a title ID.
        
        Args:
            title_id: PS3 title ID (e.g., "BLUS30982")
            
        Returns:
            List of DLC entries (may be empty)
        """
        results = []
        
        for entry in self.entries:
            entry_title_id = entry.get('Title ID', '')
            name = entry.get('Name', '')
            
            # Match title ID and filter for story DLC
            if entry_title_id == title_id:
                if self._is_story_dlc(name, entry):
                    results.append(entry)
        
        return results
    
    def find_all_dlc_for_title(self, title_id: str) -> List[Dict]:
        """Find ALL DLC for a title ID (story, cosmetic, characters, etc).
        
        Args:
            title_id: PS3 title ID (e.g., "BLUS30982")
            
        Returns:
            List of ALL DLC entries (may be empty)
        """
        results = []
        
        for entry in self.entries:
            entry_title_id = entry.get('Title ID', '')
            
            # Match title ID - include ALL DLC (no filtering)
            if entry_title_id == title_id:
                # Skip if missing RAP (can't activate)
                rap = entry.get('RAP', '')
                if rap and rap != 'MISSING':
                    results.append(entry)
        
        return results
    
    def _is_story_dlc(self, name: str, entry: Dict) -> bool:
        """Check if entry is story/campaign DLC (not cosmetic).
        
        Args:
            name: DLC name
            entry: Database entry dict
            
        Returns:
            bool: True if this looks like story DLC
        """
        name_lower = name.lower()
        
        # Skip if RAP key is missing
        rap = entry.get('RAP', '')
        if rap == 'MISSING':
            return False
        
        # Check file size - story DLC is typically large (>100MB)
        file_size = entry.get('File Size', '')
        if not file_size or not file_size.isdigit():
            return False
        
        size_bytes = int(file_size)
        if size_bytes < 100 * 1024 * 1024:  # Less than 100MB = likely not story content
            return False
        
        # Skip cosmetic keywords
        cosmetic_keywords = [
            'costume', 'skin', 'outfit', 'pack',
            'weapon pack', 'map pack', 'theme', 'avatar',
            'emblem', 'decal', 'paint', 'music', 'soundtrack',
            'madness', 'supremacy', 'domination'  # Borderlands skin packs
        ]
        
        has_cosmetic_keyword = any(keyword in name_lower for keyword in cosmetic_keywords)
        if has_cosmetic_keyword:
            return False
        
        # Story DLC keywords
        story_keywords = [
            'campaign', 'mission', 'chapter', 'episode',
            'expansion', 'assault', 'quest', 'adventure',
            'pirates', 'dragon keep', 'torgue', 'hammerlock',  # Borderlands
            'scarlett', 'tina', 'carnage', 'big game hunt'
        ]
        
        has_story_keyword = any(keyword in name_lower for keyword in story_keywords)
        
        # Large size + story keyword = story DLC
        if has_story_keyword:
            return True
        
        # Large size alone (>500MB) is probably story content
        if size_bytes > 500 * 1024 * 1024:
            return True
        
        return False
    
    def _is_update(self, name: str, entry: Dict) -> bool:
        """Check if entry is a game update/patch (not cosmetic DLC).
        
        Args:
            name: DLC/update name
            entry: Database entry dict
            
        Returns:
            bool: True if this looks like an update/patch
        """
        name_lower = name.lower()
        
        # Skip if RAP key is missing (can't decrypt)
        rap = entry.get('RAP', '')
        if rap == 'MISSING':
            return False
        
        # Check file size first - skip tiny license files (<1MB)
        file_size = entry.get('File Size', '')
        if file_size and file_size.isdigit():
            size_bytes = int(file_size)
            if size_bytes < 1 * 1024 * 1024:  # Less than 1MB = license file
                return False
        
        # Keywords that indicate updates/patches
        update_keywords = [
            'update', 'patch', 'system data',
            'compatibility pack', 'online pass'
        ]
        
        # Keywords that indicate cosmetic DLC (skip these)
        cosmetic_keywords = [
            'costume', 'skin', 'outfit', 'character pack',
            'weapon pack', 'map pack', 'theme', 'avatar',
            'emblem', 'decal', 'paint', 'music', 'soundtrack'
        ]
        
        # Check for update keywords
        has_update_keyword = any(keyword in name_lower for keyword in update_keywords)
        
        # Check for cosmetic keywords
        has_cosmetic_keyword = any(keyword in name_lower for keyword in cosmetic_keywords)
        
        # It's an update if it has update keywords and NOT cosmetic keywords
        if has_update_keyword and not has_cosmetic_keyword:
            return True
        
        return False
