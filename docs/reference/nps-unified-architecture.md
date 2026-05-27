# NoPayStation Unified Sync Architecture

## Executive Summary

A unified, hierarchical system for discovering, downloading, and organizing PlayStation content across all platforms (PS3, PS Vita, PSP, PSX, PSM) with multi-dimensional filtering and intelligent dependency resolution.

---

## Design Principles

1. **Hierarchical Organization**: Platform → Type → Region → Title
2. **Smart Search**: Fuzzy matching with relationship awareness
3. **Dependency Resolution**: Automatic discovery of base game + DLC + updates
4. **Idempotent Operations**: Re-runnable without re-downloads
5. **Unified Interface**: Single tool for all platforms/types

---

## Data Model

### Hierarchy Dimensions

```
Platform (5 options)
├── PS3        - PlayStation 3
├── Vita       - PlayStation Vita
├── PSP        - PlayStation Portable
├── PSX        - PlayStation 1 (Classics)
└── PSM        - PlayStation Mobile

Content Type (6 options per platform)
├── Games      - Base games
├── DLC        - Downloadable content
├── Updates    - Game patches
├── Themes     - UI themes
├── Demos      - Demo versions
└── Avatars    - Profile avatars (PS3 only)

Region (4 primary regions)
├── USA        - North America (UP*, UC*)
├── EUR        - Europe (EP*)
├── JPN        - Japan (HP*, JP*, NP*)
└── ASI        - Asia (KP*)

Title Identity
├── Title ID   - Base game identifier (e.g., PCSE00065)
├── Content ID - Specific content (e.g., UP2058-PCSE00065_00-GAME000000000001)
└── Name       - Human-readable title
```

### License Key Mapping

| Platform | Column | Format | Tool |
|----------|--------|--------|------|
| PS3      | RAP    | 32-char hex | Direct .rap creation |
| Vita     | zRIF   | Base64 | pkg2zip extraction |
| PSP      | RAP    | 32-char hex | pkg2zip -d flag |
| PSX      | -      | None needed | pkg2zip direct |
| PSM      | zRIF   | Base64 | pkg2zip -a flag |

---

## Proposed CLI Interface

### Example: "I want the Vita version of the US Dr Who game with all DLC and updates"

```bash
# Smart search with automatic dependency resolution
nps sync --platform vita --region USA --search "doctor who" --with-dlc --with-updates

# Explicit specification
nps sync --platform vita --type games,dlc,updates --region USA --title-id PCSE00103

# Just the base game
nps sync --platform vita --type games --region USA --title-id PCSE00103

# All Pinball Arcade DLC (including Doctor Who tables)
nps sync --platform vita --type dlc --region USA --title-id PCSE00065
```

### Full Command Syntax

```bash
nps sync [OPTIONS]

Platform Selection:
  --platform {ps3,vita,psp,psx,psm}    Platform (default: ps3)
  
Content Type Selection (multiple allowed):
  --type {games,dlc,updates,themes,demos,avatars}
  --all-types                          All content types
  
Region Filtering:
  --region {USA,EUR,JPN,ASI}           Region filter
  --all-regions                        All regions
  
Search & Filtering:
  --search TEXT                        Fuzzy search game names
  --title-id ID                        Exact Title ID (e.g., PCSE00065)
  --content-id ID                      Exact Content ID
  
Dependency Resolution:
  --with-dlc                           Include all DLC for matched games
  --with-updates                       Include all updates for matched games
  --with-themes                        Include all themes for matched games
  --complete                           Same as --with-dlc --with-updates
  
Execution Control:
  --dry-run                            Preview without downloading
  --verify-only                        Check existing files
  --redownload                         Force re-download
  --verbose, -v                        Detailed output
```

---

## Directory Structure

### Organized by Platform → Type → Region → Title

```
/path/to/source/nopaystation/
├── databases/                    # TSV database files
│   ├── PS3_GAMES.tsv
│   ├── PS3_DLCS.tsv
│   ├── PSV_GAMES.tsv
│   └── ...
│
├── packages/                     # Downloaded PKG files
│   ├── ps3/
│   │   ├── games/
│   │   │   ├── usa/
│   │   │   │   ├── BLUS31627-Call_of_Duty_Black_Ops_III/
│   │   │   │   │   ├── base/
│   │   │   │   │   │   └── Call of Duty Black Ops III [UP0002-BLUS31627_00-CODBO3FULLGAMENA].pkg
│   │   │   │   │   ├── dlc/
│   │   │   │   │   │   ├── Awakening Map Pack [UP0002-BLUS31627_00-CODBO3AWAKENING0].pkg
│   │   │   │   │   │   └── Eclipse Map Pack [UP0002-BLUS31627_00-CODBO3ECLIPSE000].pkg
│   │   │   │   │   ├── updates/
│   │   │   │   │   │   └── Update 1.28 [UP0002-BLUS31627_00-...].pkg
│   │   │   │   │   └── .nps-metadata.json
│   │   │   │   └── BLUS30453-Super_Street_Fighter_IV/
│   │   │   ├── eur/
│   │   │   └── jpn/
│   │   ├── dlc/           # Orphaned DLC (no base game)
│   │   ├── themes/
│   │   └── avatars/
│   │
│   ├── vita/
│   │   ├── games/
│   │   │   ├── usa/
│   │   │   │   ├── PCSE00103-Doctor_Who_The_Eternity_Clock/
│   │   │   │   │   ├── base/
│   │   │   │   │   │   └── Doctor Who The Eternity Clock [UP2066-PCSE00103_00-DOCTORWHO0000000].pkg
│   │   │   │   │   └── .nps-metadata.json
│   │   │   │   └── PCSE00065-Pinball_Arcade/
│   │   │   │       ├── base/
│   │   │   │       │   └── Pinball Arcade [UP2058-PCSE00065_00-GAME000000000001].pkg
│   │   │   │       ├── dlc/
│   │   │   │       │   ├── Doctor Who [UP2058-PCSE00065_00-ADDCONT000000054].pkg
│   │   │   │       │   ├── Doctor Who Master of Time [UP2058-PCSE00065_00-ADDCONT000000057].pkg
│   │   │   │       │   └── Doctor Who Pro [UP2058-PCSE00065_00-ADDCONTPRO000054].pkg
│   │   │   │       └── .nps-metadata.json
│   │   │   ├── eur/
│   │   │   └── jpn/
│   │   └── dlc/
│   │
│   ├── psp/
│   ├── psx/
│   └── psm/
│
└── licenses/                     # License files
    ├── ps3/
    │   └── *.rap                # PS3 RAP files (by Content ID)
    └── vita/
        └── *.rif                # Vita RIF files (extracted from zRIF)
```

### Metadata File Format (.nps-metadata.json)

```json
{
  "platform": "vita",
  "region": "USA",
  "title_id": "PCSE00065",
  "base_game": {
    "name": "Pinball Arcade",
    "content_id": "UP2058-PCSE00065_00-GAME000000000001",
    "file_size": 1073741824,
    "sha256": "abc123...",
    "downloaded": "2025-11-15T10:30:00Z",
    "verified": true
  },
  "dlc": [
    {
      "name": "Doctor Who",
      "content_id": "UP2058-PCSE00065_00-ADDCONT000000054",
      "file_size": 52428800,
      "downloaded": "2025-11-15T10:35:00Z",
      "verified": true
    }
  ],
  "updates": [],
  "last_sync": "2025-11-15T10:40:00Z"
}
```

---

## Search & Dependency Resolution

### Title ID Relationship

All content sharing the same **Title ID** belongs together:

```
Title ID: PCSE00065
├── Base Game:  Pinball Arcade
├── DLC (5):    Doctor Who, Master of Time, Doctor Who Pro, Custom Ball Pack, Pro Upgrade
└── Updates:    (none in database)

Title ID: PCSE00103
├── Base Game:  Doctor Who: The Eternity Clock
├── DLC:        (none in database)
└── Updates:    (check PSV_UPDATES.tsv)
```

### Search Algorithm

```python
def search_content(query: str, platform: str, region: str = None):
    """
    1. Fuzzy match game names in platform_GAMES.tsv
    2. Extract Title IDs from matches
    3. Find all related content (DLC, updates) via Title ID
    4. Filter by region if specified
    5. Return hierarchical result set
    """
    
    # Example: search "doctor who" on vita USA
    # Returns:
    # - PCSE00103: Doctor Who: The Eternity Clock (base game)
    # - PCSE00065: Pinball Arcade (base game) + 5 Doctor Who DLC
    # - PCSE00491: Minecraft (base game) + 2 Doctor Who skin DLC
```

---

## Implementation Architecture

### Class Structure

```python
class NPSDatabase:
    """Unified database access across all platforms/types"""
    
    def __init__(self, database_dir: Path):
        self.databases = self._load_all_databases()
        self._build_indices()
    
    def search(self, query: str, platform: str = None, 
               content_type: str = None, region: str = None) -> List[ContentEntry]
        """Fuzzy search with filters"""
    
    def get_by_title_id(self, title_id: str, platform: str) -> TitleBundle
        """Get base game + all related content"""
    
    def get_by_content_id(self, content_id: str) -> ContentEntry
        """Get specific content"""


class ContentEntry:
    """Single database entry"""
    platform: str
    content_type: str
    title_id: str
    content_id: str
    name: str
    region: str
    pkg_url: str
    license_key: str  # RAP or zRIF
    file_size: int
    sha256: str


class TitleBundle:
    """Complete collection for a Title ID"""
    title_id: str
    platform: str
    region: str
    base_game: Optional[ContentEntry]
    dlc: List[ContentEntry]
    updates: List[ContentEntry]
    themes: List[ContentEntry]
    
    def download_all(self, output_dir: Path):
        """Download all content in bundle"""


class NPSSync:
    """Download and organize content"""
    
    def __init__(self, db: NPSDatabase, output_dir: Path):
        self.db = db
        self.output_dir = output_dir
    
    def sync(self, entries: List[ContentEntry], 
             resolve_dependencies: bool = False):
        """Download entries and optionally their dependencies"""
    
    def _organize_output(self, entry: ContentEntry) -> Path:
        """Calculate output path: platform/type/region/title/"""
    
    def _create_license(self, entry: ContentEntry):
        """Create RAP or extract zRIF based on platform"""
```

---

## Example Workflows

### Workflow 1: Download Doctor Who content on Vita (USA)

```bash
# User command
nps sync --platform vita --region USA --search "doctor who" --complete

# System executes:
# 1. Search PSV_GAMES.tsv for "doctor who" → PCSE00103, PCSE00065, PCSE00491
# 2. For each Title ID:
#    - Find base game in PSV_GAMES.tsv
#    - Find all DLC in PSV_DLCS.tsv
#    - Find all updates in PSV_UPDATES.tsv
# 3. Filter by region USA (UP* Content IDs)
# 4. Download to structured directories:
#    packages/vita/games/usa/PCSE00103-Doctor_Who_The_Eternity_Clock/
#    packages/vita/games/usa/PCSE00065-Pinball_Arcade/dlc/
#    packages/vita/games/usa/PCSE00491-Minecraft/dlc/
# 5. Extract zRIF licenses using pkg2zip
# 6. Create metadata files
```

**Output:**
```
✓ Found 3 matching titles:
  • Doctor Who: The Eternity Clock (PCSE00103)
    - Base game: 1.2 GB
    
  • Pinball Arcade (PCSE00065) - 5 Doctor Who DLC
    - Doctor Who table
    - Doctor Who: Master of Time
    - Doctor Who Pro
    - Doctor Who Custom ball pack
    - Doctor Who Pro Upgrade
    
  • Minecraft (PCSE00491) - 2 Doctor Who DLC
    - Doctor Who Skins Volume I
    - Doctor Who Skins Volume II

Total: 1 base game + 7 DLC = 8 packages (1.8 GB)

Download? [Y/n]
```

### Workflow 2: Download all PS3 USA DLC only

```bash
nps sync --platform ps3 --type dlc --region USA

# Downloads ~6,287 DLC packages to:
# packages/ps3/dlc/usa/
# With RAP files in licenses/ps3/
```

### Workflow 3: Build complete Call of Duty Black Ops III collection

```bash
nps sync --platform ps3 --title-id BLUS31627 --complete

# Downloads:
# - Base game
# - All DLC (map packs, zombies, etc.)
# - All updates
# Organized in: packages/ps3/games/usa/BLUS31627-Call_of_Duty_Black_Ops_III/
```

---

## Migration Path

### Phase 1: Refactor Current Tool
1. Rename `sync_nps_dlc.py` → `nps_sync.py`
2. Extract database logic → `nps_database.py`
3. Extract download logic → `nps_downloader.py`
4. Add content type detection from filename

### Phase 2: Add Multi-Type Support
1. Support all content types (games, dlc, updates, themes, demos, avatars)
2. Unified output directory structure
3. Metadata file creation

### Phase 3: Add Search & Dependencies
1. Fuzzy search implementation
2. Title ID relationship mapping
3. Automatic dependency resolution

### Phase 4: Add Vita/PSP/PSX Support
1. zRIF extraction via pkg2zip
2. Platform-specific handling
3. Complete database coverage

### Phase 5: Polish & Integration
1. Build pipeline integration
2. Web UI (optional)
3. Performance optimization

---

## Performance Considerations

### Indexing
- Build in-memory indices at startup:
  - `title_id_index: Dict[str, List[ContentEntry]]`
  - `content_id_index: Dict[str, ContentEntry]`
  - `name_index: Dict[str, List[ContentEntry]]` (for fuzzy search)

### Caching
- Cache database parsing (pickle/JSON)
- Cache search results
- Incremental sync (only process new entries)

### Parallelization
- Download multiple packages concurrently
- Verify existing files in parallel
- zRIF extraction in parallel

---

## CLI Examples Reference

```bash
# Simple searches
nps search "metal gear"                    # Search all platforms
nps search "persona" --platform vita       # Platform-specific
nps search "final fantasy" --region JPN    # Japan releases only

# Targeted downloads
nps sync --title-id BLUS31627             # Specific game
nps sync --platform vita --type games --region USA --all  # All USA Vita games
nps sync --search "resident evil" --platform ps3 --complete  # RE + DLC + updates

# Maintenance
nps verify                                # Verify all downloads
nps verify --platform vita                # Verify Vita only
nps update-databases                      # Refresh TSV files from NPS
nps stats                                 # Show collection statistics

# Advanced
nps sync --content-id "UP9000-PCSE00065_00-ADDCONT000000054"  # Exact DLC
nps export-list --platform ps3 --region USA > my-collection.txt
nps sync --from-file my-collection.txt
```

---

## Benefits of This Architecture

1. **User-Friendly**: Natural language queries ("doctor who vita usa")
2. **Complete**: Automatic discovery of related content
3. **Organized**: Hierarchical storage by platform/type/region
4. **Efficient**: Idempotent, resumable, parallel downloads
5. **Flexible**: Fine-grained control when needed
6. **Extensible**: Easy to add new platforms/features
7. **Maintainable**: Clean separation of concerns
8. **Discoverable**: Search before download

---

## Next Steps

1. **Review & Feedback**: Validate architecture against use cases
2. **Prototype**: Build minimal search + download for one platform
3. **Iterate**: Expand to full feature set
4. **Test**: Verify with real-world scenarios
5. **Deploy**: Integrate with existing build pipeline
6. **Document**: User guide + developer docs
