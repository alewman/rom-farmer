"""PS3 utilities for PARAM.SFO parsing, NoPayStation, and Sony PSN integration.

This module provides:
- parse_param_sfo(): Parse PS3 PARAM.SFO binary files
- SonyPSNClient: Query Sony PSN servers for game updates
- NoPayStationDatabase: Parse and search NoPayStation TSV databases
"""

import csv
import hashlib
import struct
from pathlib import Path
from typing import Dict, List, Optional


def parse_param_sfo(sfo_path: Path) -> Dict[str, object]:
    """Parse a PS3 PARAM.SFO file and return its key-value pairs.

    PARAM.SFO is a small binary file present in every PS3 game at
    ``PS3_GAME/PARAM.SFO``.  Fields of interest include:

    - ``TITLE_ID`` – unique 9-character game/region identifier (e.g. ``BLUS30289``)
    - ``TITLE``    – game display title
    - ``VERSION``  – title version
    - ``APP_VER``  – application version

    Args:
        sfo_path: Path to PARAM.SFO

    Returns:
        Dict mapping field name (str) to value (str or int).

    Raises:
        ValueError: If file is not a valid PARAM.SFO.
        FileNotFoundError: If the file does not exist.
    """
    sfo_path = Path(sfo_path)
    data = sfo_path.read_bytes()

    # Header: magic(4) version(4) key_table_start(4) data_table_start(4) num_entries(4)
    if len(data) < 20:
        raise ValueError(f"File too small to be PARAM.SFO: {sfo_path}")
    magic, _version, key_table_start, data_table_start, num_entries = struct.unpack_from('<IIIII', data, 0)
    if magic != 0x46535000:  # "\x00PSF"
        raise ValueError(f"Not a PARAM.SFO file (bad magic {magic:#010x}): {sfo_path}")

    result: Dict[str, object] = {}
    for i in range(num_entries):
        entry_offset = 20 + i * 16
        key_offset, data_fmt, data_len, _data_max_len, data_offset = struct.unpack_from('<HHIII', data, entry_offset)

        # Key: null-terminated UTF-8 string in the key table
        key_abs = key_table_start + key_offset
        key = data[key_abs:].split(b'\x00')[0].decode('utf-8')

        val_abs = data_table_start + data_offset
        if data_fmt == 0x0204:  # UTF-8 string
            val: object = data[val_abs: val_abs + data_len - 1].decode('utf-8', errors='replace')
        elif data_fmt == 0x0404:  # uint32
            val = struct.unpack_from('<I', data, val_abs)[0]
        else:
            val = data[val_abs: val_abs + data_len]

        result[key] = val

    return result


def get_param_sfo_md5(param_sfo_path: Path) -> str:
    """Return the MD5 hex digest of a PARAM.SFO file.

    This is used as the ``final_md5`` key in :class:`ROMTransformation` records
    for PS3 folder-format games, since a folder has no single file hash.
    PARAM.SFO is small (~1 KB), unique per game release, and stable across
    hardlink copies.

    Args:
        param_sfo_path: Path to PARAM.SFO

    Returns:
        32-character lowercase hex MD5 string.
    """
    md5 = hashlib.md5()
    with open(param_sfo_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5.update(chunk)
    return md5.hexdigest()


def find_param_sfo(ps3_folder: Path) -> Optional[Path]:
    """Return the PARAM.SFO path inside a PS3 game folder, or None.

    Searches the canonical location ``PS3_GAME/PARAM.SFO`` first,
    then falls back to a recursive search for resilience.

    Args:
        ps3_folder: Root folder of a PS3 JB game (e.g. ``Game.ps3/``).

    Returns:
        Path to PARAM.SFO, or None if not found.
    """
    canonical = ps3_folder / "PS3_GAME" / "PARAM.SFO"
    if canonical.exists():
        return canonical
    # Fallback: search one level deeper (some rips have an extra wrapper dir)
    for candidate in ps3_folder.rglob("PARAM.SFO"):
        return candidate
    return None


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
