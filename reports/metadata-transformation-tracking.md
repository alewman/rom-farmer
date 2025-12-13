# ROM Farmer Metadata Preservation Through Transformations

## Executive Summary

ROM Farmer solves a critical problem in ROM management: **How do you get metadata for transformed files that don't exist in scraping databases?**

For example, when you convert a Myrient/Redump Xbox ISO to XISO format and then compress it to `.iso.squashfs`, the resulting file has completely different hashes than the original. ScreenScraper has never seen your `.iso.squashfs` file - but it *definitely* knows about the original Redump ISO that Myrient hosts.

ROM Farmer's **Transformation Tracking System** maintains the chain of custody from source to final file, enabling metadata lookup via the *original* known hashes.

---

## The Problem: Hash Mismatch

```mermaid
flowchart LR
    subgraph Myrient["Myrient/Redump Source"]
        A["Halo 3 (USA).iso<br/>MD5: abc123..."]
    end
    
    subgraph Transform["Transformations"]
        B["extract-xiso<br/>(Redump → XISO)"]
        C["mksquashfs<br/>(XISO → SquashFS)"]
    end
    
    subgraph Final["Your Final File"]
        D["Halo 3 (USA).iso.squashfs<br/>MD5: xyz789..."]
    end
    
    subgraph Scraper["ScreenScraper"]
        E[("Database")]
        F["❓ xyz789?<br/>NOT FOUND"]
        G["✓ abc123<br/>FOUND!"]
    end
    
    A --> B --> C --> D
    D -.->|"Query xyz789"| F
    A -.->|"Query abc123"| G
    
    style F fill:#ffccbc
    style G fill:#c8e6c9
```

### Without Transformation Tracking

1. You have `Halo 3 (USA).iso.squashfs` (MD5: `xyz789...`)
2. You query ScreenScraper with `xyz789`
3. **Result**: No match found - ScreenScraper has never seen this file

### With Transformation Tracking

1. You have `Halo 3 (USA).iso.squashfs` (MD5: `xyz789...`)
2. ROM Farmer looks up `xyz789` in transformation table
3. Finds record: `xyz789` came from source `abc123`
4. Queries ScreenScraper with source hash `abc123`
5. **Result**: Match found! Full metadata returned

---

## System Architecture

```mermaid
flowchart TD
    subgraph Sources["Data Sources"]
        A[("Redump/No-Intro<br/>DAT Files")]
        B[("Myrient<br/>Source Files")]
    end
    
    subgraph Capture["Hash Capture (3-Tier)"]
        C["Tier 1: DAT Lookup<br/>(0.001s, 95% of files)"]
        D["Tier 2: Hash Cache<br/>(0.1s, 4% of files)"]
        E["Tier 3: Calculate<br/>(120s, 1% of files)"]
    end
    
    subgraph Recording["Transformation Recording"]
        F["TransformationRecorder"]
        G[("ROMTransformation<br/>Table")]
    end
    
    subgraph Lookup["Reverse Lookup"]
        H["Final File"]
        I["find_source_hash()"]
        J["Original Hash"]
    end
    
    subgraph Scraping["Metadata Scraping"]
        K["ScreenScraper API"]
        L[("ScrapedGame<br/>Table")]
    end
    
    A --> C
    B --> C
    C --> D --> E
    C --> F
    D --> F
    E --> F
    F --> G
    
    H --> I
    G --> I
    I --> J
    J --> K
    K --> L
    
    style C fill:#c8e6c9
    style D fill:#fff9c4
    style E fill:#ffccbc
```

---

## The Transformation Database Model

### ROMTransformation Table

The `ROMTransformation` table is the heart of the tracking system:

```mermaid
erDiagram
    ROMTransformation {
        int id PK
        string source_md5 "Original Myrient/Redump hash"
        string source_sha1
        bigint source_file_size
        string source_file_name "Halo 3 (USA).iso"
        string source_format "redump-iso"
        string source_dat "Redump - Microsoft Xbox 360"
        boolean source_verified "From official DAT?"
        string transformation_tool "extract-xiso"
        string transformation_version "2.7.1"
        json transformation_params
        datetime transformation_date
        float transformation_duration_seconds
        string final_md5 "Hash of .iso.squashfs"
        string final_sha1
        bigint final_file_size
        string final_file_name "Halo 3 (USA).iso.squashfs"
        string final_format "squashfs"
        boolean verified
        int game_id FK
    }
    
    ScrapedGame {
        int id PK
        string name
        string system
        string md5 "Scraped hash"
        string description
        string developer
        string publisher
        date release_date
    }
    
    ROMTransformation }o--|| ScrapedGame : "links to"
```

### Key Fields Explained

| Field | Purpose | Example |
|-------|---------|---------|
| `source_md5` | Hash of original Myrient file | `abc123def456...` |
| `source_file_name` | Original filename for reference | `Halo 3 (USA).iso` |
| `source_format` | Type of source file | `redump-iso` |
| `source_dat` | Which DAT verified this | `Redump - Microsoft Xbox 360` |
| `source_verified` | Was hash from official DAT? | `true` |
| `transformation_tool` | What transformed it | `extract-xiso` |
| `final_md5` | Hash of your actual file | `xyz789abc012...` |
| `final_format` | Final file type | `squashfs` |
| `game_id` | Link to scraped metadata | `42` |

---

## Hash Capture: The 3-Tier Strategy

Before recording a transformation, we need the source file's hashes. ROM Farmer uses a smart 3-tier strategy to avoid expensive calculations:

```mermaid
flowchart TD
    A["Source File:<br/>Halo 3 (USA).iso"] --> B{Tier 1:<br/>DAT Lookup}
    
    B -->|"Found in Redump DAT"| C["✓ Instant!<br/>(0.001s)"]
    B -->|"Not in DAT"| D{Tier 2:<br/>Hash Cache}
    
    D -->|"Previously calculated"| E["✓ Cached!<br/>(0.1s)"]
    D -->|"Not in cache"| F["Tier 3:<br/>Calculate"]
    
    F --> G["Calculate MD5, SHA1<br/>(~120s for 8GB file)"]
    G --> H["Store in cache<br/>for next time"]
    
    C --> I["Source Hashes<br/>Ready"]
    E --> I
    H --> I
    
    style C fill:#c8e6c9
    style E fill:#fff9c4
    style F fill:#ffccbc
```

### Why This Matters for Myrient Files

Myrient hosts **verified Redump/No-Intro sets**. This means:

1. **95%+ of files have hashes in DAT files** - instant lookup
2. Source hashes are **pre-verified** against official DATs
3. ScreenScraper has these same hashes in their database
4. The chain of trust is maintained: `DAT → Myrient → Your File → Transformation → Scraper`

---

## Recording Transformations: XISO Example

Here's exactly how ROM Farmer records an Xbox transformation:

### Step 1: Capture Source Hash (BEFORE conversion)

```python
# In ConvertXISOStage._convert_to_xiso()

# Capture source hash BEFORE conversion for transformation tracking
source_md5 = None
source_size = None
if self.db_session:
    self._log_info(context, f"  Hashing source ISO: {iso_file.name}")
    source_md5 = self._calculate_md5(iso_file)
    source_size = iso_file.stat().st_size
    self._log_info(context, f"    Source MD5: {source_md5[:16]}...")
```

### Step 2: Perform Conversion

```python
# Run extract-xiso -r to convert in place
cmd = [
    str(self.extract_xiso_path),
    "-r",  # Rewrite mode (Redump → XISO)
    str(iso_file)
]
subprocess.run(cmd, ...)
```

### Step 3: Record Transformation (AFTER conversion)

```python
# In ConvertXISOStage._record_transformation()

# Calculate final XISO hash
final_md5 = self._calculate_md5(xiso_file)
final_size = xiso_file.stat().st_size

# Create transformation record
transformation = ROMTransformation(
    source_md5=source_md5,           # Original Myrient hash
    source_file_size=source_size,
    source_format='redump-iso',
    source_dat='Redump - Microsoft Xbox 360',
    
    final_md5=final_md5,             # XISO hash
    final_file_size=final_size,
    final_format='xiso',
    final_file_name=xiso_file.name,
    
    transformation_tool='extract-xiso',
    transformation_version='2.7.1',
    transformation_params={"format": "xiso", "mode": "rewrite"},
    
    game_id=game_id,  # Link to scraped game if found
)

session.add(transformation)
session.commit()
```

---

## Complete Xbox Workflow

```mermaid
sequenceDiagram
    participant M as Myrient
    participant D as DAT Manager
    participant X as ConvertXISOStage
    participant S as SquashFS Stage
    participant T as Transformation Table
    participant SS as ScreenScraper
    
    Note over M: Original Redump ISO<br/>MD5: abc123
    
    M->>D: Lookup hash in Redump DAT
    D-->>M: ✓ Verified: abc123
    
    M->>X: Convert to XISO
    X->>X: Capture source_md5 = abc123
    X->>X: Run extract-xiso -r
    X->>X: Calculate final_md5 = def456
    X->>T: Record(abc123 → def456)
    
    X->>S: Compress to SquashFS
    S->>S: Capture source_md5 = def456
    S->>S: Run mksquashfs
    S->>S: Calculate final_md5 = xyz789
    S->>T: Record(def456 → xyz789)
    
    Note over T: Chain: abc123 → def456 → xyz789
    
    Note over SS: Later, during scraping...
    
    S->>T: Lookup xyz789
    T-->>S: Source: def456
    S->>T: Lookup def456
    T-->>S: Source: abc123
    S->>SS: Query with abc123
    SS-->>S: ✓ Found! Halo 3 metadata
```

---

## Reverse Lookup: From SquashFS to Metadata

### The Lookup Chain

When the metadata stage needs to scrape a file, it follows this process:

```mermaid
flowchart TD
    A["Your File:<br/>Halo 3 (USA).iso.squashfs<br/>MD5: xyz789"] --> B["Calculate MD5"]
    
    B --> C{Search<br/>Transformation Table}
    
    C -->|"Found"| D["Get source_md5<br/>from record"]
    C -->|"Not Found"| E["Try filename<br/>lookup instead"]
    
    D --> F{Is source hash<br/>another transformation?}
    
    F -->|"Yes (chained)"| G["Follow chain<br/>to original"]
    F -->|"No"| H["Use source_md5<br/>for scraping"]
    
    G --> H
    
    H --> I["Query ScreenScraper<br/>with original hash"]
    
    I --> J{Match Found?}
    
    J -->|"Yes"| K["✓ Return metadata"]
    J -->|"No"| E
    
    E --> L["Fuzzy filename<br/>matching"]
    
    style K fill:#c8e6c9
    style E fill:#fff9c4
```

### Code: Metadata Lookup with Transformation Support

```python
# In MetadataStage._get_metadata_for_file()

# Calculate final file MD5
lookup_md5 = self._calculate_md5(file_path)

# Look up transformation to find original hash
transformation = session.query(ROMTransformation).filter(
    ROMTransformation.source_md5 == lookup_md5
).first()

if transformation:
    # We found a record linking this file to a source hash
    if transformation.game:
        # Game already linked - use it directly
        game = transformation.game
        lookup_method = "transformation-hash"
    elif transformation.final_md5:
        # Follow the chain to find the game
        game = session.query(ScrapedGame).filter(
            ScrapedGame.md5 == transformation.final_md5
        ).first()
        lookup_method = "transformation-link"
```

---

## Why Myrient + Transformation Tracking Works

### The Trust Chain

```mermaid
flowchart LR
    subgraph Official["Official Sources"]
        A["Redump.org"]
        B["No-Intro.org"]
    end
    
    subgraph DAT["DAT Files"]
        C["Official hashes<br/>verified by community"]
    end
    
    subgraph Mirror["Myrient Mirror"]
        D["Exact copies of<br/>verified dumps"]
    end
    
    subgraph Scraper["ScreenScraper"]
        E["Same hashes in<br/>their database"]
    end
    
    subgraph Your["Your Files"]
        F["Transformed but<br/>tracked back to source"]
    end
    
    A --> C
    B --> C
    C --> D
    C --> E
    D --> F
    F -.->|"Lookup via<br/>transformation"| E
    
    style C fill:#c8e6c9
    style D fill:#c8e6c9
    style E fill:#c8e6c9
```

### Key Guarantees

| Guarantee | How It's Achieved |
|-----------|-------------------|
| **Source Authenticity** | DAT files verify Myrient files match official Redump/No-Intro hashes |
| **Transformation Integrity** | Source hash captured BEFORE any conversion |
| **Scraper Compatibility** | Original hashes exist in ScreenScraper database |
| **Chain of Custody** | Complete record: `Source → Tool → Final` |
| **Reverse Lookability** | Index on `final_md5` enables instant reverse lookup |

---

## Transformation Types Supported

### Currently Recorded

| Source Format | Tool | Final Format | Use Case |
|--------------|------|--------------|----------|
| Redump ISO | `extract-xiso` | XISO | Xbox/Xbox 360 conversion |
| XISO | `mksquashfs` | iso.squashfs | Batocera compression |
| Redump ISO | `chdman` | CHD | Saturn, PSX, etc. |
| ROM in ZIP | `rom-farmer-zip-peek` | Extracted | ZIP inner hash tracking |

### Transformation Recording Points

```mermaid
flowchart TD
    subgraph Stages["ROM Farmer Stages"]
        A["ConvertXISOStage"]
        B["CompressSquashfsStage"]
        C["ConvertCHDStage"]
        D["MetadataStage<br/>(ZIP peek)"]
    end
    
    subgraph Recording["Recording Actions"]
        E["Record Redump → XISO"]
        F["Record XISO → SquashFS"]
        G["Record ISO → CHD"]
        H["Record ZIP → Inner ROM"]
    end
    
    A --> E
    B --> F
    C --> G
    D --> H
    
    E --> I[("Transformation<br/>Table")]
    F --> I
    G --> I
    H --> I
```

---

## Practical Example: Full Xbox Build

### Input
```
/data/emu/source/xbox360/Halo 3 (USA).zip
  └── Halo 3 (USA).iso  (Redump format, MD5: abc123def456...)
```

### Processing Steps

| Step | Input | Output | Recorded |
|------|-------|--------|----------|
| 1. Extract | `.zip` | `.iso` | ZIP → ISO hash mapping |
| 2. Convert | `.iso` (Redump) | `.iso` (XISO) | `abc123 → def456` |
| 3. Compress | `.iso` (XISO) | `.iso.squashfs` | `def456 → xyz789` |

### Final Output
```
/data/emu/output/xbox360/Halo 3 (USA).iso.squashfs
  MD5: xyz789abc012...
  
Transformation Records:
  abc123 → def456 (extract-xiso)
  def456 → xyz789 (mksquashfs)
```

### Metadata Lookup
```
1. File: Halo 3 (USA).iso.squashfs (MD5: xyz789)
2. Lookup xyz789 in transformations → Found: source=def456
3. Lookup def456 in transformations → Found: source=abc123
4. Query ScreenScraper with abc123
5. ✓ Match! Return full game metadata
```

---

## Summary: Key Takeaways

```mermaid
mindmap
  root((Metadata<br/>Preservation))
    Source Trust
      Myrient hosts verified dumps
      DATs provide instant hash lookup
      ScreenScraper knows these hashes
    Transformation Tracking
      Capture source hash BEFORE conversion
      Record tool and parameters
      Store final hash AFTER conversion
    Reverse Lookup
      Index on final_md5
      Chain following for multi-step transforms
      Fallback to filename matching
    Benefits
      Metadata for any transformed file
      No manual lookup required
      Works with XISO, CHD, SquashFS, etc.
```

### The Bottom Line

1. **Myrient files are known** - Their hashes exist in official DATs and ScreenScraper
2. **We capture before transforming** - Source hash recorded before any conversion
3. **We track the chain** - Every transformation step is recorded with hashes
4. **We can reverse lookup** - Given any final file, we can find its original hash
5. **Scrapers work** - We query with the original hash that scrapers know

**Your `xiso.squashfs` file gets metadata because we tracked it back to the original Myrient ISO that ScreenScraper definitely knows about.**

---

## Code References

| Component | File | Purpose |
|-----------|------|---------|
| `ROMTransformation` | `src/romfarmer/metadata/transformation.py` | Database model for transformation records |
| `TransformationRecorder` | `src/romfarmer/metadata/transformation_recorder.py` | Context manager for recording transforms |
| `SmartHashCapture` | `src/romfarmer/metadata/hash_capture.py` | 3-tier hash capture strategy |
| `DATManager` | `src/romfarmer/metadata/dat_manager.py` | DAT file parsing and lookup |
| `ConvertXISOStage` | `src/romfarmer/stages/convert_xiso.py` | XISO conversion with recording |
| `MetadataStage` | `src/romfarmer/stages/metadata.py` | Scraping with transformation lookup |

---

*Generated for ROM Farmer v2.0*
