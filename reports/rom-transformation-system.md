# ROM Farmer Transformation System Analysis

*Generated: December 6, 2025*

## Executive Summary

The ROM Farmer transformation system converts raw ROM archives into optimized, organized collections ready for emulation frontends. It operates as a **stage-based pipeline** that:

- **Filters** source ROMs against DAT files and selection criteria
- **Extracts** archives based on platform type (cartridge, disc, RVZ, PS3, XISO)
- **Compresses** extracted content to optimal formats (CHD, 7z, RVZ)
- **Organizes** output with frontend-specific structures
- **Generates** metadata (gamelist.xml) for EmulationStation/Batocera

---

## Table of Contents

1. [Pipeline Architecture](#1-pipeline-architecture)
2. [Stage Context & Data Flow](#2-stage-context--data-flow)
3. [Filtering Stages](#3-filtering-stages)
4. [Extraction Stages](#4-extraction-stages)
5. [Compression Stages](#5-compression-stages)
6. [Organization Stages](#6-organization-stages)
7. [Platform-Specific Pipelines](#7-platform-specific-pipelines)
8. [Selection Strategies](#8-selection-strategies)
9. [List System](#9-list-system)

---

## 1. Pipeline Architecture

### Overview

The transformation system uses a **Pipeline** class that executes stages sequentially, passing a shared **StageContext** between them.

```mermaid
flowchart TB
    subgraph Input["Input"]
        SRC[(Source ROMs<br/>ZIP archives)]
        DAT[(DAT File<br/>Retool 1G1R)]
        DB[(Metadata DB<br/>ARRM scraped)]
    end
    
    subgraph Pipeline["Stage Pipeline"]
        direction TB
        F1[FilterDATStage]
        F2[Filter1G1RStage]
        F3[SelectionFilter]
        F4[ApplyListsStage]
        E1[Extraction Stage]
        C1[Compression Stage]
        M1[CreateM3UStage]
        O1[OrganizeStage]
        G1[GenerateMetadataStage]
        
        F1 --> F2 --> F3 --> F4
        F4 --> E1 --> C1 --> M1
        M1 --> O1 --> G1
    end
    
    subgraph Output["Output"]
        OUT[(Organized ROMs)]
        XML[(gamelist.xml)]
        MEDIA[(Media Files)]
    end
    
    SRC --> F1
    DAT --> F1
    DB --> F3
    G1 --> OUT
    G1 --> XML
    G1 --> MEDIA
```

### Stage Base Class

All stages inherit from the `Stage` abstract base class:

```python
class Stage(ABC):
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def execute(self, context: StageContext) -> StageResult:
        """Execute the stage and return results."""
        pass
    
    def should_skip(self, context: StageContext) -> bool:
        """Check if stage should be skipped."""
        return False
```

### Stage Result

Each stage returns a `StageResult` with execution details:

| Field | Type | Description |
|-------|------|-------------|
| `status` | StageStatus | SUCCESS, FAILED, SKIPPED, PENDING |
| `message` | str | Human-readable summary |
| `files_processed` | int | Files handled by stage |
| `files_matched` | int | Files passing stage criteria |
| `files_failed` | int | Files that failed processing |
| `duration_seconds` | float | Execution time |
| `error` | Exception | Error if failed |
| `details` | Dict | Stage-specific data |

---

## 2. Stage Context & Data Flow

### StageContext Structure

The `StageContext` is the primary data structure flowing through the pipeline:

```mermaid
classDiagram
    class StageContext {
        +platform_name: str
        +platform_config: PlatformConfig
        +target_name: str
        +source_dir: Path
        +work_dir: Path
        +output_dir: Path
        +dat_file: DATFile
        +files: FileSet
        +hashes: FileHashes
        +discs: DiscProcessing
        +stats: Dict
    }
    
    class FileSet {
        +source: List~Path~
        +matched: List~Path~
        +filtered: List~Path~
        +extracted: List~Path~
        +compressed: List~Path~
        +organized: Dict~str,List~
        +m3u: List~Path~
    }
    
    class FileHashes {
        +source_md5: Dict~Path,str~
        +rom_md5: Dict~Path,str~
        +get_md5(path) str
    }
    
    class DiscProcessing {
        +games: Dict~str,DiscGame~
        +cue_sheets: Dict~str,Any~
        +get_multi_disc_games() List
    }
    
    StageContext --> FileSet
    StageContext --> FileHashes
    StageContext --> DiscProcessing
```

### Data Flow Through Pipeline

```mermaid
flowchart LR
    subgraph Files["File Lists"]
        source["source_files<br/>2,847 ZIPs"]
        matched["matched_files<br/>2,500 matched DAT"]
        filtered["filtered_files<br/>500 selected"]
        extracted["extracted_files<br/>500 ROMs"]
        compressed["compressed_files<br/>500 CHDs"]
        organized["organized_files<br/>subdirs + files"]
    end
    
    subgraph Stages
        S1[FilterDAT]
        S2[Selection]
        S3[Extract]
        S4[Compress]
        S5[Organize]
    end
    
    source --> S1 --> matched
    matched --> S2 --> filtered
    filtered --> S3 --> extracted
    extracted --> S4 --> compressed
    compressed --> S5 --> organized
```

---

## 3. Filtering Stages

### FilterDATStage

Matches source ZIP files against a Retool DAT file using MD5 hashes.

```mermaid
flowchart TB
    subgraph Input
        ZIP[Source ZIPs]
        DAT[Retool DAT]
        DB[(Metadata DB)]
    end
    
    subgraph Process["FilterDATStage"]
        LOAD[Load MD5s from DB]
        CALC[Calculate missing MD5s]
        MATCH[Match against DAT entries]
        LINK[Create symlinks in work_dir]
    end
    
    subgraph Output
        MATCHED[matched_files]
        HASHES[file_md5s]
    end
    
    ZIP --> LOAD
    DB --> LOAD
    LOAD --> CALC --> MATCH
    DAT --> MATCH
    MATCH --> LINK --> MATCHED
    CALC --> HASHES
```

**Key features:**
- Loads pre-computed MD5s from ARRM database (fast)
- Falls back to calculating MD5s (slow but accurate)
- For ZIPs: extracts and hashes the ROM content, not the ZIP
- Creates symlinks in work_dir to avoid copying data

### Filter1G1RStage

Applies 1G1R (One Game One ROM) filtering when no DAT file is available.

| Feature | Behavior |
|---------|----------|
| Region priority | USA > World > Europe > Japan |
| Revision preference | Latest revision preferred |
| Language preference | English preferred |
| Clone handling | Keep parent, remove clones |

### SelectionFilter

Applies selection strategies to reduce ROM count based on quality, size, or testing needs.

**Strategies:**

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `RATING_BUDGET` | Best-rated games within size budget | Production builds |
| `FIRST` | First N files alphabetically | Testing (A-D games) |
| `LAST` | Last N files alphabetically | Testing (W-Z games) |
| `RANDOM` | Random N files with seed | Reproducible testing |
| `SMALLEST` | N smallest files | Quick testing |
| `LARGEST` | N largest files | Stress testing |
| `ALPHABETICAL` | First N sorted | Predictable subset |

```mermaid
flowchart TB
    subgraph Input
        FILES[filtered_files<br/>2,500 games]
        CONFIG[SelectionConfig]
        METADATA[(Metadata DB<br/>ratings)]
    end
    
    subgraph Strategies
        RB["RATING_BUDGET<br/>Top-rated in 40GB"]
        RAND["RANDOM<br/>10 random games"]
        FIRST["FIRST<br/>First 50 alphabetically"]
    end
    
    subgraph Output
        SELECTED[filtered_files<br/>N selected]
    end
    
    FILES --> RB & RAND & FIRST
    CONFIG --> RB & RAND & FIRST
    METADATA --> RB
    RB & RAND & FIRST --> SELECTED
```

---

## 4. Extraction Stages

The system uses different extraction stages based on platform type:

```mermaid
flowchart TB
    subgraph ExtractionRouting["Extraction Type Routing"]
        CONFIG[ExtractionConfig.type]
    end
    
    CONFIG --> |CARTRIDGE| CART[ExtractArchiveStage<br/>Extract ROM from ZIP]
    CONFIG --> |DISC| DISC[ExtractArchiveStage<br/>Extract CUE/BIN]
    CONFIG --> |RVZ| RVZ[UnzipRVZStage<br/>Extract RVZ from ZIP]
    CONFIG --> |PS3| PS3[ExtractPS3Stage<br/>Decrypt + Extract JB]
    CONFIG --> |XISO| XISO[ExtractArchiveStage<br/>+ ConvertXISOStage]
    
    CART --> |".nes, .sfc, .gba"| ROM[Extracted ROMs]
    DISC --> |".cue + .bin"| CUE[CUE/BIN Files]
    RVZ --> |".rvz"| RVZF[RVZ Files]
    PS3 --> |"PARAM.SFO + USRDIR/"| JB[JB Folder]
    XISO --> |".iso (XISO format)"| XISOF[XISO Files]
```

### ExtractArchiveStage

Handles both cartridge and disc extraction:

**Cartridge Mode:**
1. Extract ROM file from ZIP
2. Calculate MD5 of extracted ROM
3. Store MD5 for metadata matching
4. Set timestamp to No-Intro standard (1996-12-24 23:32:00)

**Disc Mode:**
1. Extract CUE/BIN files from ZIP
2. Parse CUE sheet for metadata
3. Detect multi-disc games (Disc 1, Disc 2, etc.)
4. Group discs by base game name

### UnzipRVZStage

For Wii/GameCube games in Dolphin's native RVZ format:

```
Input:  Game (USA).zip → contains Game (USA).rvz
Output: work_dir/Game (USA).rvz (no conversion needed!)
```

**Why RVZ?**
- Dolphin's native compressed format
- Uses zstd compression
- No conversion needed - use directly!
- Better compression than ISO

### ExtractPS3Stage

Complex pipeline for PS3 games:

```mermaid
flowchart TB
    subgraph Input
        ZIP["Redump ZIP<br/>BLUS30982.zip"]
        KEYS[(Keys Directory<br/>.dkey files)]
    end
    
    subgraph Extraction
        E1[Extract encrypted ISO]
        E2[Find matching .dkey]
        E3[Decrypt with PS3Dec]
        E4[Extract JB folder with 7z]
        E5[Clean up temp files]
    end
    
    subgraph Output
        JB["JB Folder Structure<br/>BLUS30982/"]
        SFB[PS3_DISC.SFB]
        GAME[PS3_GAME/]
        UPDATE[PS3_UPDATE/]
    end
    
    ZIP --> E1 --> E2
    KEYS --> E2
    E2 --> E3 --> E4 --> E5 --> JB
    JB --> SFB & GAME & UPDATE
```

### ConvertXISOStage

For Xbox/Xbox 360 Redump images:

```mermaid
flowchart LR
    subgraph Input
        REDUMP["Redump ISO<br/>(Full disc image)"]
    end
    
    subgraph Convert
        XISO["extract-xiso -r<br/>(Rewrite mode)"]
    end
    
    subgraph Output
        XISOF["XISO Format<br/>(Game partition only)"]
    end
    
    REDUMP --> XISO --> XISOF
```

**Why convert?**
- Redump contains full disc image with padding
- xemu requires XISO format (game partition only)
- XISO is typically 20-40% smaller

---

## 5. Compression Stages

### CompressCHDStage

Converts disc images to MAME's CHD format:

```mermaid
flowchart TB
    subgraph Input
        CUE[CUE/BIN Files]
        ISO[ISO Files]
    end
    
    subgraph CHDMAN
        CD["chdman createcd<br/>(CD images)"]
        DVD["chdman createdvd<br/>(DVD images)"]
    end
    
    subgraph Output
        CHD[".chd Files"]
    end
    
    CUE --> CD --> CHD
    ISO --> DVD --> CHD
```

**CHD benefits:**
- Lossless compression (30-70% size reduction)
- Single file per disc (no CUE+BIN pairs)
- Widely supported by emulators
- Includes integrity verification

**Transformation recording:**
- Records original MD5 → CHD MD5 mapping
- Enables ScreenScraper lookup using original hash

### CompressArchiveStage

Compresses cartridge ROMs to archive formats:

| Format | Tool | Compression | Use Case |
|--------|------|-------------|----------|
| 7z | 7z | LZMA2 (highest) | Maximum compression |
| ZIP | zip | Deflate | Wide compatibility |
| NONE | - | Raw files | No compression |

**Standard timestamp:**
- All archived files use 1996-12-24 23:32:00 UTC
- Enables reproducible/deterministic builds
- Matches No-Intro/TOSEC standards

### CompressSquashfsStage

For Xbox games requiring squashfs format:

```
Input:  Game.iso (XISO format)
Output: Game.squashfs (compressed filesystem)
```

Used when target device requires squashfs (some ARM devices).

---

## 6. Organization Stages

### CreateM3UStage

Creates M3U playlists for multi-disc games:

```mermaid
flowchart TB
    subgraph Input
        D1["Game (Disc 1).chd"]
        D2["Game (Disc 2).chd"]
        D3["Game (Disc 3).chd"]
    end
    
    subgraph Process
        GROUP[Group by base name]
        SORT[Sort by disc number]
        CREATE[Create M3U file]
    end
    
    subgraph Output
        M3U["Game.m3u"]
        META["DiscMetadata<br/>primary_file = .m3u<br/>first_disc = Disc 1"]
    end
    
    D1 & D2 & D3 --> GROUP --> SORT --> CREATE --> M3U & META
```

**M3U file content:**
```
Game (Disc 1).chd
Game (Disc 2).chd
Game (Disc 3).chd
```

**Metadata output:**
- `primary_file`: M3U path (used in gamelist.xml)
- `first_disc_path`: Disc 1 CHD (for metadata lookup)
- `needs_m3u`: True for multi-disc games

### OrganizeStage

Organizes ROMs into target-specific structures:

```mermaid
flowchart TB
    subgraph Styles["Organization Styles"]
        FLAT["FLAT<br/>All files in root"]
        BALANCED["BALANCED<br/>A-E, F-M, N-Z folders"]
        MINIMAL["MINIMAL<br/>Max 50 files/folder"]
        RICH["RICH<br/>Deep structure + metadata"]
    end
    
    subgraph FLAT_Ex["FLAT Output"]
        F1["/roms/saturn/"]
        F2["├── Game A.chd"]
        F3["├── Game B.chd"]
        F4["└── Game Z.chd"]
    end
    
    subgraph BALANCED_Ex["BALANCED Output"]
        B1["/roms/saturn/"]
        B2["├── A-E/"]
        B3["│   ├── Game A.chd"]
        B4["│   └── Game E.chd"]
        B5["├── F-M/"]
        B6["└── N-Z/"]
    end
    
    FLAT --> FLAT_Ex
    BALANCED --> BALANCED_Ex
```

**Organization styles:**

| Style | Structure | Target |
|-------|-----------|--------|
| FLAT | All files in one directory | Batocera, general |
| BALANCED | Alphabetical groups (A-E, F-M, N-Z) | Large collections |
| MINIMAL | Max N files per folder | Everdrive/flash carts |
| RICH | Deep metadata structure | EmulationStation |

### GenerateMetadataStage

Creates gamelist.xml for EmulationStation/Batocera:

```mermaid
flowchart TB
    subgraph Input
        FILES[Organized Files]
        DISC_META[Disc Metadata]
        DB[(Metadata DB)]
    end
    
    subgraph Process
        SCAN[Scan output files]
        LOOKUP[Lookup metadata]
        COPY_MEDIA[Copy media files]
        BUILD_XML[Build XML entries]
    end
    
    subgraph Output
        XML["gamelist.xml"]
        IMAGES["/media/images/"]
        VIDEOS["/media/videos/"]
    end
    
    FILES --> SCAN
    DISC_META --> SCAN
    SCAN --> LOOKUP
    DB --> LOOKUP
    LOOKUP --> COPY_MEDIA --> BUILD_XML
    BUILD_XML --> XML
    COPY_MEDIA --> IMAGES & VIDEOS
```

**Multi-disc handling:**
- Shows M3U file in gamelist (playable)
- Hides individual CHDs (hidden="true")
- Uses Disc 1 metadata for title/image

**Media directory structure:**
```
/roms/saturn/
├── gamelist.xml
├── media/
│   ├── images/
│   │   ├── Game A-image.png
│   │   └── Game B-image.png
│   ├── videos/
│   ├── marquees/
│   ├── thumbnails/
│   ├── wheels/
│   └── manuals/
├── Game A.chd
└── Game B.m3u
```

---

## 7. Platform-Specific Pipelines

Different platforms require different stage combinations:

### Cartridge Systems (NES, SNES, GB, GBA)

```mermaid
flowchart LR
    F1[FilterDAT] --> F2[Selection]
    F2 --> F3[ApplyLists]
    F3 --> E1["Extract<br/>(CARTRIDGE)"]
    E1 --> C1["Compress<br/>(7z)"]
    C1 --> O1[Organize]
    O1 --> M1[Metadata]
```

**Output:** `Game (USA).7z` containing `Game (USA).sfc`

### Disc Systems (Saturn, PSX, SegaCD)

```mermaid
flowchart LR
    F1[FilterDAT] --> F2[Selection]
    F2 --> F3[ApplyLists]
    F3 --> E1["Extract<br/>(DISC)"]
    E1 --> C1["Compress<br/>(CHD)"]
    C1 --> M3U[CreateM3U]
    M3U --> O1[Organize]
    O1 --> M1[Metadata]
```

**Output:** `Game (USA).chd` or `Game (USA).m3u` + multiple CHDs

### Nintendo Disc (GameCube, Wii)

```mermaid
flowchart LR
    F1[FilterDAT] --> F2[Selection]
    F2 --> E1["UnzipRVZ"]
    E1 --> O1[Organize]
    O1 --> M1[Metadata]
```

**Output:** `Game (USA).rvz` (no compression stage needed!)

### Xbox/Xbox 360

```mermaid
flowchart LR
    F1[FilterDAT] --> F2[Selection]
    F2 --> E1["Extract<br/>(DISC)"]
    E1 --> X1[ConvertXISO]
    X1 --> O1[Organize]
    O1 --> M1[Metadata]
```

**Output:** `Game (USA).iso` (XISO format)

### PlayStation 3

```mermaid
flowchart LR
    F1[FilterDAT] --> F2[Selection]
    F2 --> E1["ExtractPS3<br/>(decrypt + extract)"]
    E1 --> O1[Organize]
    O1 --> M1[Metadata]
```

**Output:** `BLUS30982/` folder with JB structure

---

## 8. Selection Strategies

### Rating Budget Strategy

The most sophisticated selection strategy for production builds:

```mermaid
flowchart TB
    subgraph Input
        FILES[2,500 games]
        RATINGS[(Metadata DB<br/>ScreenScraper ratings)]
        BUDGET[max_size_gb: 40]
    end
    
    subgraph Process
        LOOKUP[Lookup ratings]
        ESTIMATE[Estimate compressed sizes]
        SORT[Sort by rating DESC]
        SELECT[Select until budget filled]
        ATOMIC[Keep multi-disc games atomic]
    end
    
    subgraph Output
        SELECTED["~200 top-rated games<br/>fitting in 40GB"]
    end
    
    FILES --> LOOKUP
    RATINGS --> LOOKUP
    LOOKUP --> ESTIMATE
    BUDGET --> ESTIMATE
    ESTIMATE --> SORT --> SELECT --> ATOMIC --> SELECTED
```

**Compression ratio estimation:**

The system uses historical compression ratios to estimate final sizes:

| Platform | Default Ratio | Actual (learned) |
|----------|--------------|------------------|
| Saturn | 0.65 | 0.58-0.72 |
| PSX | 0.70 | 0.65-0.75 |
| PS2 | 0.75 | 0.70-0.80 |
| Dreamcast | 0.68 | 0.60-0.75 |
| GameCube | 0.72 | 0.65-0.78 |

### Test Mode Strategies

For quick testing without processing entire libraries:

```yaml
# First 10 games alphabetically
selection:
  strategy: first
  limit: 10

# Random 10 games (reproducible)
selection:
  strategy: random
  limit: 10
  seed: 42

# 5% of collection starting at 50%
selection:
  strategy: first
  percentage: 5
  offset: 50  # Start at M-N games
```

---

## 9. List System

### ApplyListsStage

Provides fine-grained control over ROM selection:

```mermaid
flowchart TB
    subgraph ListTypes["List File Types"]
        DEL["{platform}-delete<br/>Remove unwanted ROMs"]
        ADD_M["{platform}+{name}<br/>Add from Myrient source"]
        ADD_E["{platform}.{name}<br/>Add from extras directory"]
    end
    
    subgraph Examples
        DEL --> EX1["nes-delete<br/>26 pirate carts"]
        ADD_M --> EX2["saturn+Best-Games<br/>Create _Best-Games/ subdir"]
        ADD_E --> EX3["gba.Translations<br/>Add fan translations"]
    end
```

### List File Format

Plain text, one game per line (partial matching):

```
# saturn+Best-Games
Panzer Dragoon Saga
Radiant Silvergun
Guardian Heroes
Dragon Force
Shining Force III
```

### Subdirectory Creation

Lists create organized subdirectories:

```
/roms/saturn/
├── gamelist.xml
├── _Best-Games/
│   ├── Panzer Dragoon Saga.chd
│   └── Radiant Silvergun.chd
├── _Translations/
│   └── Lunar - Silver Star Story.chd
├── Game A.chd
└── Game B.chd
```

**Subdirectory behavior:**

| List Type | Operation | Example |
|-----------|-----------|---------|
| `+` (Myrient) | COPY transformed files | Source flows through pipeline |
| `.` (Extra) | MOVE pre-transformed files | Already in final format |

---

## Summary

ROM Farmer's transformation system provides:

| Capability | Implementation |
|------------|----------------|
| **Flexible filtering** | DAT matching, 1G1R, selection strategies |
| **Multi-format extraction** | Cartridge, disc, RVZ, PS3, XISO |
| **Optimal compression** | CHD for disc, 7z for cartridge, RVZ passthrough |
| **Multi-disc support** | M3U playlists with atomic selection |
| **Frontend integration** | gamelist.xml with media files |
| **Quality selection** | Rating-based budgeting |
| **List-based curation** | Delete, add, organize into subdirs |

The pipeline architecture enables ROM Farmer to process collections from source archives to fully-organized, metadata-rich output directories ready for any emulation frontend.
