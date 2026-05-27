# ROM Farmer PS3 Metadata Preservation

## Executive Summary

PS3 presents the **most complex transformation challenge** in ROM Farmer. Unlike Xbox where we simply convert ISO → XISO → SquashFS, PS3 games undergo:

1. **Decryption** (encrypted ISO → decrypted ISO)
2. **Extraction** (ISO → JB folder structure)
3. **Updates** (patches downloaded from Sony PSN)
4. **DLC** (additional content merged or copied)

After all these transformations, the final game folder is **completely unrecognizable** from the original Myrient source. Yet ROM Farmer still achieves metadata lookup by tracking the chain back to the **original Redump ISO hash inside the Myrient ZIP**.

---

## The PS3 Challenge

```mermaid
flowchart TD
    subgraph Myrient["Myrient Source"]
        A["Game (USA).zip"]
        B["Contains: Game.iso<br/>(Encrypted Redump)"]
    end
    
    subgraph Transform["Transformation Pipeline"]
        C["Decrypt with PS3Dec<br/>(disc key required)"]
        D["Extract to JB folder"]
        E["Apply Updates<br/>(from Sony PSN)"]
        F["Apply DLC<br/>(from NoPayStation)"]
    end
    
    subgraph Final["Your Final Game"]
        G["GameID.ps3/<br/>├─ PS3_GAME/<br/>│  ├─ PARAM.SFO<br/>│  ├─ USRDIR/<br/>│  └─ (updated files)<br/>└─ _PKG/<br/>   └─ (DLC packages)"]
    end
    
    subgraph Problem["The Problem"]
        H["❓ Original ZIP hash?<br/>❓ Decrypted ISO hash?<br/>❓ Folder hash?<br/>❓ Updated files hash?"]
    end
    
    A --> B --> C --> D --> E --> F --> G
    G -.-> H
    
    style Problem fill:#ffccbc
```

### What Changes at Each Step

| Step | Input | Output | What Changes |
|------|-------|--------|--------------|
| **Unzip** | `Game.zip` | `Game.iso` | Outer container removed |
| **Decrypt** | `Game.iso` (encrypted) | `Game_dec.iso` (decrypted) | Encryption removed, hash changes |
| **Extract** | `Game_dec.iso` | `GAMEID.ps3/` folder | Format completely different |
| **Updates** | Base game folder | Patched folder | Files replaced/added |
| **DLC** | Game + PKGs | Game + content | New files merged |

---

## The Solution: PARAM.SFO as the Anchor

ROM Farmer uses a clever trick: the **PARAM.SFO file** remains constant through updates and serves as the **folder identifier**.

```mermaid
flowchart LR
    subgraph Before["Before Updates"]
        A["GAMEID.ps3/"]
        B["PS3_GAME/"]
        C["PARAM.SFO<br/>MD5: xyz789"]
        D["USRDIR/<br/>(base files)"]
    end
    
    subgraph After["After Updates + DLC"]
        E["GAMEID.ps3/"]
        F["PS3_GAME/"]
        G["PARAM.SFO<br/>MD5: xyz789"]
        H["USRDIR/<br/>(patched files)"]
        I["_PKG/<br/>(DLC packages)"]
    end
    
    A --> B --> C
    B --> D
    
    E --> F --> G
    F --> H
    E --> I
    
    C -.->|"Same hash!"| G
    
    style C fill:#c8e6c9
    style G fill:#c8e6c9
```

### The Transformation Chain

```
Myrient ZIP (MD5: aaa111)
    └── Encrypted ISO (MD5: bbb222) ← Redump hash, ScreenScraper knows this!
            └── Decrypted ISO (MD5: ccc333)
                    └── PS3_GAME/PARAM.SFO (MD5: xyz789)
                            ↓
                    [Updates Applied - files change]
                    [DLC Added - more files]
                            ↓
                    PS3_GAME/PARAM.SFO (MD5: xyz789) ← Still the same!
```

---

## Transformation Recording

### What Gets Recorded

```mermaid
erDiagram
    ROMTransformation {
        int id PK
        string source_md5 "Decrypted ISO hash"
        string source_file_name "Game_dec.iso"
        string source_format "ps3-iso-decrypted"
        string final_md5 "PARAM.SFO hash"
        string final_file_name "GAMEID.ps3/PS3_GAME/PARAM.SFO"
        string final_format "ps3-folder"
        string transformation_tool "7zip"
        string transformation_params "extract"
    }
    
    PS3Update {
        string title_id "BLUS30982"
        string update_version "01.02"
        string source "Sony PSN"
        datetime applied_at
    }
    
    PS3DLC {
        string content_id "UP0006-BLUS30982_00-..."
        string name "Story Campaign DLC"
        string mode "extract or copy"
    }
```

### Code: Recording PS3 Folder Transformation

```python
def _record_folder_transformation(self, source_iso: Path, folder_path: Path):
    """Record PS3 folder transformation using PARAM.SFO as the link file."""
    
    # Hash the DECRYPTED source ISO (this came from Redump via Myrient)
    source_md5 = self._calculate_md5(source_iso)
    source_size = source_iso.stat().st_size
    
    # Hash PARAM.SFO as the "final" hash (folder identifier)
    # This remains constant even after updates/DLC!
    param_sfo = folder_path / "PS3_GAME" / "PARAM.SFO"
    final_md5 = self._calculate_md5(param_sfo)
    final_size = param_sfo.stat().st_size
    
    # Create transformation record
    transformation = ROMTransformation(
        # Source (decrypted ISO - we can look this up in Redump DAT!)
        source_md5=source_md5,
        source_file_size=source_size,
        source_file_name=source_iso.name,
        source_format='ps3-iso-decrypted',
        
        # Final (PARAM.SFO as folder identifier)
        final_md5=final_md5,
        final_file_size=final_size,
        final_file_name=f"{folder_path.name}/PS3_GAME/PARAM.SFO",
        final_format='ps3-folder',
        
        transformation_tool='7zip',
        transformation_params='{"format": "ps3-folder"}',
    )
    
    session.add(transformation)
    session.commit()
```

---

## The Complete PS3 Pipeline

```mermaid
sequenceDiagram
    participant M as Myrient ZIP
    participant D as DAT Lookup
    participant P as PS3Dec
    participant E as Extractor
    participant U as Update Stage
    participant L as DLC Stage
    participant T as Transformation Table
    participant S as ScreenScraper
    
    Note over M: The Last of Us (USA).zip<br/>Contains encrypted ISO
    
    M->>D: Lookup inner ISO hash in Redump DAT
    D-->>M: ✓ Found: MD5 bbb222<br/>(Redump - Sony PlayStation 3)
    
    M->>P: Decrypt with disc key
    Note over P: bbb222 (encrypted)<br/>→ ccc333 (decrypted)
    P->>T: Record: bbb222 → ccc333
    
    P->>E: Extract to JB folder
    Note over E: ccc333 (ISO)<br/>→ BCUS98174.ps3/
    E->>T: Record: ccc333 → PARAM.SFO hash (xyz789)
    
    E->>U: Apply Updates
    Note over U: Query Sony PSN<br/>Download patch PKGs<br/>Merge into USRDIR/
    Note over U: PARAM.SFO unchanged!
    
    U->>L: Apply DLC (optional)
    Note over L: Find matching DLC<br/>Extract or copy PKGs
    Note over L: PARAM.SFO still xyz789!
    
    Note over T: Chain recorded:<br/>bbb222 → ccc333 → xyz789
    
    Note over S: Later, during metadata scrape...
    
    L->>T: Lookup xyz789 (PARAM.SFO)
    T-->>L: Source: ccc333
    L->>T: Lookup ccc333
    T-->>L: Source: bbb222
    L->>S: Query with bbb222
    S-->>L: ✓ Found! "The Last of Us" metadata
```

---

## Updates: Sony PSN Integration

### How Updates Work

ROM Farmer queries **Sony's official update servers** to find and apply game patches:

```mermaid
flowchart TD
    subgraph GameFolder["Your Game Folder"]
        A["BCUS98174.ps3/"]
        B["PS3_GAME/"]
        C["PARAM.SFO<br/>TITLE_ID: BCUS98174"]
    end
    
    subgraph Sony["Sony PSN Servers"]
        D["https://a0.ww.np.dl.playstation.net<br/>/tpl/np/BCUS98174/BCUS98174-ver.xml"]
        E["Lists all available patches"]
    end
    
    subgraph Download["Patch Download"]
        F["Download PKG"]
        G["Decrypt PKG"]
        H["Merge files into USRDIR/"]
    end
    
    C -->|"Extract TITLE_ID"| D
    D --> E
    E --> F --> G --> H
    H -->|"Updates applied"| B
    
    style C fill:#c8e6c9
```

### Update Response Example

```xml
<?xml version="1.0" encoding="UTF-8"?>
<titlepatch titleid="BCUS98174">
    <tag name="BCUS98174-patch">
        <package version="01.02" size="123456789" 
                 sha1sum="abc123..." 
                 url="http://b0.ww.np.dl.playstation.net/tppkg/.../BCUS98174_T12.pkg">
            <paramsfo>
                <TITLE>The Last of Us™</TITLE>
            </paramsfo>
        </package>
    </tag>
</titlepatch>
```

### Why Updates Don't Break Metadata

| File | Before Update | After Update |
|------|--------------|--------------|
| `PARAM.SFO` | MD5: xyz789 | MD5: xyz789 ✓ |
| `EBOOT.BIN` | Original | **Patched** |
| `USRDIR/*.sprx` | Original | **Patched** |
| New files | - | **Added** |

**PARAM.SFO is read-only** - it contains game metadata (title, ID, version) but isn't modified by updates. The hash stays constant!

---

## DLC: Two Modes

### Mode 1: COPY (for RPCS3/Emulators)

DLC PKG files are copied to a `_PKG/` subfolder for the emulator to install:

```
BCUS98174.ps3/
├── PS3_GAME/
│   └── (game files)
└── _PKG/
    ├── BCUS98174-dlc1.pkg
    ├── BCUS98174-dlc1.rap  (license key)
    ├── BCUS98174-dlc2.pkg
    └── BCUS98174-dlc2.rap
```

### Mode 2: EXTRACT (for Real PS3/ps3netsrv)

DLC is decrypted and merged directly into the game folder:

```mermaid
flowchart TD
    subgraph DLC["DLC PKG"]
        A["BCUS98174-story-dlc.pkg"]
        B["Contains: USRDIR/"]
    end
    
    subgraph Game["Game Folder"]
        C["BCUS98174.ps3/"]
        D["PS3_GAME/"]
        E["USRDIR/"]
        F["(existing files)"]
        G["(new DLC files)"]
    end
    
    A --> B
    B -->|"Decrypt & Merge"| E
    E --> F
    E --> G
    
    style E fill:#fff9c4
```

### DLC Sources

| Source | Type | RAP Required | Notes |
|--------|------|--------------|-------|
| **NoPayStation** | PKG Database | Yes (in TSV) | Largest PS3 DLC database |
| **Local Archive** | Downloaded PKGs | Varies | User's own collection |

---

## Metadata Lookup Flow

### Step 1: Identify Game Folder

```python
def _extract_title_id(self, game_folder: Path) -> Optional[str]:
    """Extract TITLE_ID from PARAM.SFO."""
    param_sfo = game_folder / 'PS3_GAME' / 'PARAM.SFO'
    
    # Parse SFO binary format
    # Find TITLE_ID entry (e.g., "BCUS98174")
    return title_id
```

### Step 2: Hash PARAM.SFO

```python
# PARAM.SFO hash is our folder identifier
param_sfo = folder_path / "PS3_GAME" / "PARAM.SFO"
folder_hash = calculate_md5(param_sfo)
```

### Step 3: Follow Transformation Chain

```mermaid
flowchart TD
    A["PARAM.SFO hash:<br/>xyz789"] --> B{Lookup in<br/>transformations}
    
    B -->|"Found"| C["Source: ccc333<br/>(decrypted ISO)"]
    C --> D{Is ccc333 also<br/>a transformation?}
    
    D -->|"Yes"| E["Source: bbb222<br/>(encrypted ISO)"]
    D -->|"No"| F["Use ccc333 for scraping"]
    
    E --> G{Is bbb222 also<br/>a transformation?}
    G -->|"No"| H["Use bbb222 for scraping"]
    
    H --> I["Query ScreenScraper<br/>with Redump ISO hash"]
    I --> J["✓ Metadata found!"]
    
    style J fill:#c8e6c9
```

### Step 4: Query ScreenScraper

```python
# ScreenScraper knows the original Redump ISO hash
# Even though we have a patched folder with DLC!
result = screenscraper.query(
    md5=original_redump_iso_hash,  # bbb222
    system="ps3"
)
```

---

## Complete Example: The Last of Us

### Input

```
/path/to/source/myrient/ps3/The Last of Us (USA) (v1.00).zip
    └── The Last of Us (USA) (v1.00).iso  (encrypted, MD5: bbb222)
```

### Processing Steps

| Step | Action | Files | Hash |
|------|--------|-------|------|
| 1 | Unzip | Extract ISO from ZIP | - |
| 2 | Find key | Locate `The Last of Us (USA).dkey` | - |
| 3 | Decrypt | PS3Dec with disc key | ccc333 |
| 4 | Extract | 7zip to JB folder | - |
| 5 | Record | PARAM.SFO → xyz789 | xyz789 |
| 6 | Update | Sony PSN patch v1.11 | (files change) |
| 7 | DLC | Left Behind (optional) | (files added) |

### Transformation Records Created

```sql
-- Record 1: Encrypted → Decrypted (optional, if tracked)
INSERT INTO rom_transformations (source_md5, final_md5, tool)
VALUES ('bbb222', 'ccc333', 'PS3Dec');

-- Record 2: Decrypted ISO → Folder (via PARAM.SFO)
INSERT INTO rom_transformations (
    source_md5, source_format,
    final_md5, final_format, final_file_name
) VALUES (
    'ccc333', 'ps3-iso-decrypted',
    'xyz789', 'ps3-folder', 'BCUS98174.ps3/PS3_GAME/PARAM.SFO'
);
```

### Final Output

```
/path/to/output/ps3/The Last of Us (USA).ps3/
├── PS3_GAME/
│   ├── PARAM.SFO          ← MD5: xyz789 (unchanged!)
│   ├── ICON0.PNG
│   ├── PIC1.PNG
│   └── USRDIR/
│       ├── EBOOT.BIN      ← Patched to v1.11
│       ├── *.sprx         ← Patched
│       └── (game data)
└── _PKG/                   ← DLC (copy mode)
    ├── left-behind.pkg
    └── left-behind.rap
```

### Metadata Lookup

```
1. Your file: The Last of Us (USA).ps3/ (a folder!)
2. Hash PARAM.SFO: xyz789
3. Lookup xyz789 → Source: ccc333 (decrypted ISO)
4. Lookup ccc333 → Source: bbb222 (original Redump ISO)
5. Query ScreenScraper with bbb222
6. ✓ Result: "The Last of Us" - full metadata returned!
```

---

## Why This Works

```mermaid
mindmap
  root((PS3 Metadata<br/>Success))
    Stable Anchor
      PARAM.SFO never changes
      Contains TITLE_ID
      Hash stays constant through updates
    Chain Recording
      Each transformation step recorded
      Bidirectional lookup
      Multiple hashes linked
    Redump Integration
      Original ISO hash known
      ScreenScraper has Redump hashes
      DAT files provide instant lookup
    Smart Update Handling
      Updates only patch executables
      PARAM.SFO is metadata-only
      DLC adds files, doesn't replace core
```

### Key Insights

1. **PARAM.SFO is sacred** - Sony's design ensures this file contains metadata but isn't patched by updates

2. **Updates are additive** - Patches replace executables and add files, but don't touch the identification layer

3. **DLC is modular** - Whether copied (PKG mode) or extracted, DLC doesn't modify the base game identity

4. **Redump is the anchor** - The original encrypted ISO hash is what ScreenScraper knows, and we track back to it

---

## Summary: The PS3 Magic

| Challenge | Solution |
|-----------|----------|
| Game is decrypted | Record encrypted → decrypted transformation |
| Game is extracted to folder | Use PARAM.SFO hash as folder identifier |
| Updates change files | PARAM.SFO unchanged - use it as anchor |
| DLC adds content | Still same PARAM.SFO hash |
| Need metadata | Follow chain back to original Redump hash |

**Your PS3 game with updates and DLC still gets metadata because PARAM.SFO links back through the transformation chain to the original Redump ISO that ScreenScraper knows.**

---

## Code References

| Component | File | Purpose |
|-----------|------|---------|
| `TransformPS3Stage` | `src/romfarmer/stages/transform_ps3.py` | Full PS3 transformation pipeline |
| `ApplyPS3UpdatesStage` | `src/romfarmer/stages/apply_ps3_updates.py` | Update and DLC application |
| `SonyPSNClient` | `src/romfarmer/stages/apply_ps3_updates.py` | Query Sony servers for patches |
| `NoPayStationDatabase` | `src/romfarmer/stages/apply_ps3_updates.py` | DLC database lookup |
| `ROMTransformation` | `src/romfarmer/metadata/transformation.py` | Transformation chain storage |

---

*Generated for ROM Farmer v2.0*
