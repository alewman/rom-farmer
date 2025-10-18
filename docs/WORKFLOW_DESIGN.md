# ROM Groomer Workflow Design

## Overview

This document outlines the complete workflow for transforming raw ROM collections from multiple sources (Myrient No-Intro, Redump, etc.) into organized, optimized, and metadata-rich collections ready for use in Batocera/EmulationStation.

## Current State

### What We Have Built

1. **Database Schema** (Phase 1 ✅)
   - `HashCache` - Pre-calculated hashes for 102K+ source files
   - `ROMTransformation` - Source → Final transformation tracking
   - `ScrapedGame` - Metadata from ScreenScraper/ARRM
   - `MediaFile` - Deduplicated media storage

2. **Compression Tools** (✅)
   - 9 disc compression systems (Saturn, PSP, Xbox, Xbox 360, PS3, Wii U, Wii/GC, Switch)
   - All tested and verified working
   - Binary size: ~30 MB total
   - Average compression: 59% space savings

3. **Hooks System** (Just Completed ✅)
   - `HashCaptureHook` - Automatic hash calculation/caching
   - `TransformationTrackingHook` - Database recording
   - `ProgressMonitorHook` - Real-time feedback
   - `ValidationHook` - File validation

4. **Hash Pre-calculation Job** (Running in Background ✅)
   - Processing 102,159 ZIP archives from Myrient
   - Extracting inner files and calculating CRC32/MD5/SHA1
   - Storing as `archive.zip::inner_file.rom` in HashCache
   - ~15-30 hours estimated completion

### What We Need

1. **Configuration System** - YAML files defining source→destination mappings
2. **Source Registry** - Track multiple Myrient source directories
3. **Platform Profiles** - Extended profiles for complex workflows
4. **Batch Processor** - Process entire collections
5. **DAT Integration** - Filter/validate against No-Intro/Redump DATs
6. **Conflict Resolution** - Handle duplicates from multiple sources
7. **Metadata Pipeline** - Auto-scrape during processing

## The Big Picture: Source to Final

### Simple Case: No-Intro Cartridge Systems

**Example: NES (Nintendo Entertainment System)**

```
SOURCE:
  /data/emu/source/myrient.erista.me/files/No-Intro/Nintendo - Nintendo Entertainment System/
    ├── Game1 (USA).zip → Game1 (USA).nes (CRC32: abc123, MD5: def456)
    ├── Game1 (Europe).zip → Game1 (Europe).nes (CRC32: xyz789)
    └── Game2 (USA).zip → Game2 (USA).nes

FILTER (1G1R - USA preference):
  ✓ Game1 (USA).nes - Keep (USA preferred)
  ✗ Game1 (Europe).nes - Skip (USA exists)
  ✓ Game2 (USA).nes - Keep

PROCESS:
  1. Extract .nes from .zip
  2. Calculate hash (or use cached from pre-calc job)
  3. Copy to output
  4. No compression needed (cartridge ROM)

OUTPUT:
  /data/emu/flash/nes/
    ├── Game1 (USA).nes
    └── Game2 (USA).nes
```

**Workflow Steps:**
1. Read source directory
2. Parse filenames with No-Intro parser
3. Apply 1G1R filter (DAT-based)
4. Extract from ZIP
5. Verify hash against HashCache
6. Copy to output
7. Record in database (if needed for tracking)

**Complexity: LOW**
- No compression
- No multi-disc
- Simple file copy
- Fast processing

---

### Medium Case: Disc Systems with Compression

**Example: Sega Saturn**

```
SOURCE:
  /data/emu/source/myrient.erista.me/files/Redump/Sega - Mega CD & Sega CD/
    ├── Panzer Dragoon (USA).zip
    │   ├── Panzer Dragoon (USA).cue
    │   ├── Panzer Dragoon (USA) (Track 1).bin
    │   ├── Panzer Dragoon (USA) (Track 2).bin
    │   └── ... (20 tracks total)

FILTER (1G1R - USA preference):
  ✓ Panzer Dragoon (USA) - Keep

PROCESS:
  1. Extract all .cue + .bin files from .zip
  2. Calculate hashes for .cue file (source hash)
     - Check HashCache first (from pre-calc job)
     - If not cached, calculate and store
  3. Run chdman createcd:
     - Input: .cue file
     - Output: .chd file
     - Parameters: default compression
  4. Calculate hash for .chd (final hash)
  5. Record transformation:
     - Source: Panzer Dragoon (USA).cue (MD5: abc123)
     - Tool: chdman v0.251
     - Final: Panzer Dragoon (USA).chd (MD5: xyz789)
     - Duration: 45 seconds
  6. Cleanup temp files (.cue + .bin)

OUTPUT:
  /data/emu/flash/saturn/
    └── Panzer Dragoon (USA).chd

DATABASE:
  HashCache:
    - source.cue: MD5, SHA1, CRC32, size, mtime
    - final.chd: MD5, SHA1, CRC32, size, mtime
  
  ROMTransformation:
    - source_md5: abc123 (from .cue)
    - final_md5: xyz789 (from .chd)
    - transformation_tool: "extract → chdman"
    - transformation_duration: 45.0
```

**Workflow Steps:**
1. Read source directory
2. Parse filenames with Redump parser
3. Apply 1G1R filter
4. Extract .cue + .bin from ZIP
5. **Hash capture hook** - Check HashCache for source
6. **Compression stage** - Run chdman
7. **Hash capture hook** - Calculate final hash
8. **Transformation tracking hook** - Record to database
9. Cleanup temp files
10. Move to output

**Complexity: MEDIUM**
- Compression required
- Multi-track disc handling
- Hash tracking important (for ScreenScraper)
- Transformation recording

---

### Complex Case: Encrypted Disc Systems

**Example: Sony PlayStation 3**

```
SOURCE:
  /data/emu/source/myrient.erista.me/files/Redump/Sony - PlayStation 3/
    ├── Uncharted 2 (USA).zip
    │   └── Uncharted 2 (USA).iso (encrypted, 40GB)

DECRYPT (Required for RPCS3):
  1. Extract .iso from .zip
  2. Run PS3Dec to decrypt:
     - Input: encrypted .iso
     - Output: decrypted folder structure
     - Requires: /keys/ps3_disc.key

PROCESS:
  1. Extract encrypted .iso
  2. Decrypt with PS3Dec
  3. Create .pkg or folder for RPCS3
  4. Calculate hashes at each step
  5. Record multi-step transformation

OUTPUT:
  /data/emu/flash/ps3/
    └── Uncharted 2 (USA)/
        ├── PS3_GAME/
        ├── PS3_DISC.SFB
        └── ... (decrypted structure)

DATABASE:
  ROMTransformation:
    - source_md5: abc123 (encrypted .iso)
    - transformation_tool: "extract → PS3Dec → organize"
    - final_md5: xyz789 (decrypted folder hash - special handling)
    - transformation_duration: 180.0
```

**Workflow Steps:**
1. Read source directory
2. Parse filenames
3. Apply filter
4. Extract encrypted .iso
5. **Decryption stage** - Run PS3Dec with keys
6. **Organization stage** - Structure for RPCS3
7. Hash tracking (special handling for folders)
8. Record multi-step transformation
9. Cleanup

**Complexity: HIGH**
- Decryption required
- Key management
- Multiple transformation steps
- Folder output (not single file)
- Large files (40GB+)
- Emulator-specific structure

---

### Very Complex Case: Multi-Source Merging

**Example: Combining Multiple Sources for PSP**

```
SOURCE 1 (Primary):
  /data/emu/source/myrient.erista.me/files/Redump/Sony - PlayStation Portable/
    ├── Game1 (USA).zip → Game1 (USA).iso
    ├── Game2 (Europe).zip → Game2 (Europe).iso
    └── Game3 (USA).zip → Game3 (USA).iso

SOURCE 2 (Secondary - DLC, Updates):
  /data/emu/source/pspdlc/
    ├── Game1_DLC.zip
    └── Game3_Update_v1.2.zip

SOURCE 3 (Community Patches):
  /data/emu/source/patches/
    └── Game2_UndubPatch.zip

MERGE STRATEGY:
  For each game:
    1. Process primary ISO from Redump (highest priority)
    2. Check for DLC/updates in secondary sources
    3. Check for patches in tertiary sources
    4. Combine if found, otherwise just primary

PROCESS (Game1 Example):
  1. Extract Game1 (USA).iso from SOURCE 1
  2. Hash original: MD5 abc123
  3. Find Game1_DLC.zip in SOURCE 2
  4. Extract DLC files
  5. Compress to .cso with DLC included
  6. Hash final: MD5 xyz789
  7. Record transformation linking all sources

OUTPUT:
  /data/emu/flash/psp/
    ├── Game1 (USA) [+DLC].cso
    ├── Game2 (Europe) [Undub].cso
    └── Game3 (USA) [+Update].cso

DATABASE:
  ROMTransformation (Game1):
    - source_md5: abc123 (original ISO)
    - source_md5_secondary: def456 (DLC)
    - transformation_tool: "extract → merge_dlc → maxcso"
    - transformation_params: {"dlc_source": "pspdlc/Game1_DLC.zip"}
    - final_md5: xyz789
```

**Workflow Steps:**
1. Scan all source directories
2. Build source registry with priorities
3. For each game:
   - Parse primary source
   - Search secondary sources for matching content
   - Resolve conflicts (prefer primary, merge if possible)
4. Process with multi-source awareness
5. Track all source hashes
6. Record complex transformation chain

**Complexity: VERY HIGH**
- Multiple source directories
- Source priority system
- Content matching across sources
- Merge/conflict resolution
- Complex transformation chains
- Metadata from multiple origins

---

## Configuration File Design

### Top-Level Config

```yaml
# config/grooming-profile.yaml

# Global settings
global:
  database: metadata/database/romgroomer.db
  temp_dir: /tmp/romgroomer
  parallel_jobs: 4
  keep_intermediates: false
  
  # Hash pre-calculation (already running)
  hash_cache:
    enabled: true
    check_before_processing: true

# Source directories with priorities
sources:
  - name: myrient_nointro
    type: nointro
    priority: 100  # Highest priority
    path: /data/emu/source/myrient.erista.me/files/No-Intro
    
  - name: myrient_redump
    type: redump
    priority: 90
    path: /data/emu/source/myrient.erista.me/files/Redump
    
  - name: dlc_updates
    type: supplemental
    priority: 50
    path: /data/emu/source/dlc_and_updates
    
  - name: community_patches
    type: supplemental
    priority: 30
    path: /data/emu/source/patches

# Output directory structure
output:
  base_dir: /data/emu/flash
  structure: flat  # or 'organized' (subdirs by region/genre)
  naming: cleaned  # or 'original', 'arrm' (ScreenScraper naming)

# DAT files for filtering
dats:
  directory: /data/emu/dats
  filter_mode: 1g1r  # or 'all', 'parent_only', 'custom'
  region_priority:
    - USA
    - World
    - Europe
    - Japan
  language_priority:
    - En  # English
    - Es  # Spanish
    - Fr  # French

# Processing profiles per platform
platforms:
  # ============================================================================
  # SIMPLE: No-Intro Cartridge Systems
  # ============================================================================
  
  nes:
    enabled: true
    source: myrient_nointro/Nintendo - Nintendo Entertainment System
    output: nes
    parser: nointro
    dat: nointro/Nintendo - Nintendo Entertainment System.dat
    
    stages:
      - extract_archive
      - validate_dat
      - copy_to_output
    
    hooks:
      - hash_capture
      - validation
      - progress
    
    filters:
      1g1r: true
      regions: [USA, World, Europe]
      exclude_patterns:
        - "*Beta*"
        - "*Proto*"
        - "*Sample*"
  
  # ============================================================================
  # MEDIUM: Disc Systems with Compression
  # ============================================================================
  
  saturn:
    enabled: true
    source: myrient_redump/Sega - Saturn
    output: saturn
    parser: redump
    dat: redump/Sega - Saturn.dat
    
    stages:
      - extract_archive      # .zip → .cue + .bin files
      - compress_chd         # .cue → .chd
    
    hooks:
      - hash_capture         # Before and after compression
      - transformation_tracking  # Record source → final
      - progress
      - validation
    
    stage_config:
      compress_chd:
        compression: default
        processors: 4
    
    filters:
      1g1r: true
      regions: [USA, World, Europe, Japan]
  
  psp:
    enabled: true
    source: myrient_redump/Sony - PlayStation Portable
    output: psp
    parser: redump
    dat: redump/Sony - PlayStation Portable.dat
    
    stages:
      - extract_archive      # .zip → .iso
      - compress_cso         # .iso → .cso
    
    hooks:
      - hash_capture
      - transformation_tracking
      - progress
    
    stage_config:
      compress_cso:
        level: 9             # Maximum compression
    
    filters:
      1g1r: true
      regions: [USA, Europe]
  
  # ============================================================================
  # COMPLEX: Encrypted Systems
  # ============================================================================
  
  ps3:
    enabled: true
    source: myrient_redump/Sony - PlayStation 3
    output: ps3
    parser: redump
    emulator: rpcs3
    
    stages:
      - extract_archive
      - decrypt_ps3          # Requires keys
      - organize_rpcs3       # Structure for emulator
    
    keys:
      disc_key: /data/emu/keys/ps3_disc.key
      ird_database: /data/emu/keys/ird
    
    hooks:
      - hash_capture
      - transformation_tracking
      - validation
      - progress
    
    stage_config:
      decrypt_ps3:
        verify_signature: true
      organize_rpcs3:
        folder_structure: true
        extract_pkg: false
    
    filters:
      1g1r: true
      regions: [USA, Europe]
      size_limit: 50GB       # Skip games > 50GB
  
  # ============================================================================
  # VERY COMPLEX: Multi-Source Merging
  # ============================================================================
  
  psp_complete:
    enabled: false  # Advanced profile
    description: "PSP with DLC, updates, and patches merged"
    
    sources:
      primary:
        name: myrient_redump
        path: Sony - PlayStation Portable
      secondary:
        - name: dlc_updates
          path: PSP_DLC
          match_pattern: "{game_name}_*"
        - name: community_patches
          path: PSP_Patches
          match_pattern: "{game_name}_Patch*"
    
    output: psp
    parser: redump
    
    stages:
      - extract_archive
      - merge_secondary_sources  # NEW STAGE
      - compress_cso
    
    stage_config:
      merge_secondary_sources:
        strategy: combine      # or 'replace', 'skip'
        verify_compatibility: true
        track_all_hashes: true
    
    hooks:
      - hash_capture
      - multi_source_tracking  # NEW HOOK
      - transformation_tracking
      - progress
    
    filters:
      1g1r: true
      regions: [USA, Europe]

# ============================================================================
# Metadata and Scraping
# ============================================================================

metadata:
  enabled: true
  
  # Use cached hashes for ScreenScraper queries
  use_transformation_tracking: true
  
  scraping:
    provider: screenscraper
    api_key: ${SCREENSCRAPER_API_KEY}
    
    # Query with source hash from ROMTransformation
    query_strategy: source_hash  # or 'final_hash', 'both'
    
    # Auto-scrape during processing or separate batch job?
    mode: separate  # or 'inline'
    
    media_types:
      - boxart
      - screenshot
      - wheel
      - video
    
    media_output: metadata/media
  
  gamelist:
    generate: true
    format: emulationstation
    output: "{platform}/gamelist.xml"
    include_media_paths: true

# ============================================================================
# Advanced Features
# ============================================================================

advanced:
  # Verify against official DATs
  dat_validation:
    enabled: true
    fail_on_mismatch: false
    report_unknown: true
  
  # Backup before destructive operations
  backup:
    enabled: false
    location: /data/emu/backups
  
  # Resume interrupted batch processing
  resume:
    enabled: true
    state_file: .romgroomer_state.json
  
  # Parallel processing
  parallel:
    enabled: true
    max_workers: 4
    per_platform: true  # Run platforms in parallel
  
  # Statistics and reporting
  reporting:
    enabled: true
    output: logs/processing_report.json
    include_metrics: true
```

---

## Implementation Plan

### Phase 1: Configuration System ✅ (Next Priority)

**Files to Create:**
```
src/romgroomer/config/
  ├── __init__.py
  ├── models.py           # Pydantic models for config validation
  ├── loader.py           # YAML loader with env var substitution
  ├── validator.py        # Validate paths, check sources exist
  └── defaults.py         # Default config templates
```

**Features:**
- Pydantic models for type safety
- YAML loading with `${ENV_VAR}` support
- Config validation (paths exist, DATs found, etc.)
- Multiple config support (dev, prod, testing)

**Example Usage:**
```python
from romgroomer.config import load_config

config = load_config('config/grooming-profile.yaml')

# Access configuration
for platform in config.platforms:
    if platform.enabled:
        process_platform(platform)
```

---

### Phase 2: Source Registry

**Files to Create:**
```
src/romgroomer/sources/
  ├── __init__.py
  ├── registry.py         # Source tracking and priority management
  ├── scanner.py          # Scan source directories
  ├── matcher.py          # Match files across sources
  └── resolver.py         # Resolve conflicts
```

**Features:**
- Track multiple source directories with priorities
- Scan and index available files
- Match content across sources (by name, hash, etc.)
- Resolve conflicts (which source wins)
- Cache scanned results for performance

**Example Usage:**
```python
from romgroomer.sources import SourceRegistry

registry = SourceRegistry(config.sources)
await registry.scan_all()

# Find all sources for a game
sources = registry.find_sources("Panzer Dragoon (USA)")

# Get primary source
primary = sources.get_primary()

# Get supplemental sources (DLC, patches)
supplements = sources.get_supplements()
```

---

### Phase 3: Extended Platform Profiles

**Files to Update:**
```
src/romgroomer/processors/
  ├── profiles.py         # Add fields for keys, emulator, etc.
  └── stages.py           # Add new stages
```

**New Stages:**
```python
class DecryptPS3Stage(ProcessingStage):
    """Decrypt PS3 disc images."""
    
class MergeSecondarySourcesStage(ProcessingStage):
    """Merge DLC, updates, patches from secondary sources."""
    
class OrganizeForEmulatorStage(ProcessingStage):
    """Organize files for specific emulator (RPCS3, Xenia, etc.)."""
    
class ValidateDATStage(ProcessingStage):
    """Validate against No-Intro/Redump DAT files."""
```

---

### Phase 4: Batch Processor

**Files to Create:**
```
src/romgroomer/batch/
  ├── __init__.py
  ├── processor.py        # Main batch processing orchestrator
  ├── scheduler.py        # Job scheduling and parallel execution
  ├── progress.py         # Progress tracking across batch
  └── resume.py           # Resume interrupted batches
```

**Features:**
- Process entire platforms
- Parallel processing (per-platform or per-file)
- Progress tracking and ETA
- Resume capability
- Error handling and retry
- Statistics collection

**Example Usage:**
```python
from romgroomer.batch import BatchProcessor

processor = BatchProcessor(config)

# Process specific platforms
await processor.process_platforms(['nes', 'saturn', 'psp'])

# Or process all enabled
await processor.process_all()

# Resume interrupted batch
await processor.resume()
```

---

### Phase 5: DAT Integration

**Files to Create:**
```
src/romgroomer/dat/
  ├── __init__.py
  ├── parser.py           # Parse No-Intro/Redump XML DATs
  ├── filter.py           # 1G1R filtering logic
  ├── validator.py        # Validate files against DAT
  └── matcher.py          # Match files to DAT entries
```

**Features:**
- Parse No-Intro/Redump DAT files
- 1G1R filtering with region/language priority
- Hash-based validation
- Parent/clone handling
- BIOS/device exclusion

**Example Usage:**
```python
from romgroomer.dat import DATManager, Filter1G1R

dat = DATManager.load('dats/nointro/Nintendo - NES.dat')
filter_1g1r = Filter1G1R(
    region_priority=['USA', 'World', 'Europe'],
    language_priority=['En'],
)

# Get filtered game list
games = filter_1g1r.filter(dat.games)

# Validate file
is_valid = dat.validate_file('Game (USA).nes', hash_md5='abc123')
```

---

### Phase 6: Metadata Pipeline Integration

**Files to Update:**
```
src/romgroomer/processors/builtin_hooks.py
```

**New Hook:**
```python
class ScreenScraperHook(Hook):
    """Auto-scrape metadata using ScreenScraper API."""
    
    async def after_pipeline(self, context: HookContext):
        """Scrape after successful processing."""
        
        # Get source hash from transformation tracking
        transformation = self.db.get_transformation_by_final_hash(
            context.metadata['final_hashes']['md5']
        )
        
        if transformation:
            # Query ScreenScraper with SOURCE hash
            # (what they know about, not our compressed file)
            metadata = await self.screenscraper.query(
                md5=transformation.source_md5,
                platform=context.platform,
            )
            
            if metadata:
                # Save to database
                self.db.store_metadata(metadata)
                
                # Download media
                await self.download_media(metadata)
```

---

## Complete Workflow Example

Let's walk through the entire process for **Sega Saturn**:

### 1. Configuration

```yaml
# config/saturn-profile.yaml
platforms:
  saturn:
    enabled: true
    source: myrient_redump/Sega - Saturn
    output: /data/emu/flash/saturn
    dat: redump/Sega - Saturn.dat
    
    stages:
      - extract_archive
      - validate_dat
      - compress_chd
    
    hooks:
      - hash_capture
      - transformation_tracking
      - screenscraper
      - progress
    
    filters:
      1g1r: true
      regions: [USA, World, Europe, Japan]
```

### 2. Execution

```bash
# CLI command
romgroomer process saturn --config config/saturn-profile.yaml

# Or batch process all platforms
romgroomer batch --config config/grooming-profile.yaml
```

### 3. Internal Flow

```python
# 1. Load configuration
config = load_config('config/saturn-profile.yaml')
platform_config = config.platforms['saturn']

# 2. Setup sources
source_dir = Path('/data/emu/source/myrient.erista.me/files/Redump/Sega - Saturn')

# 3. Load DAT for filtering
dat = DATManager.load(platform_config.dat)
filter_1g1r = Filter1G1R(regions=platform_config.filters.regions)
games_to_process = filter_1g1r.filter(dat.games)

# 4. Setup pipeline
registry = HookRegistry()
registry.register('hash', HashCaptureHook(db), priority=10)
registry.register('track', TransformationTrackingHook(db), priority=20)
registry.register('scraper', ScreenScraperHook(db, api), priority=30)
registry.register('progress', ProgressMonitorHook(), priority=5)

stages = {
    'extract_archive': ExtractArchiveStage(),
    'validate_dat': ValidateDATStage(dat),
    'compress_chd': CompressCHDStage(),
}

processor = PipelineProcessor(profile, stages, hooks=registry)

# 5. Process each game
for game in games_to_process:
    source_file = source_dir / f"{game.name}.zip"
    
    result = await processor.process(
        input_path=source_file,
        output_dir=Path(platform_config.output),
    )
    
    # Result includes:
    # - Final file path
    # - Hashes stored in HashCache
    # - Transformation recorded in ROMTransformation
    # - Metadata scraped and stored
    # - Media downloaded

# 6. Generate gamelist.xml
generator = GamelistGenerator(db)
generator.generate(
    platform='saturn',
    output=Path(platform_config.output) / 'gamelist.xml'
)
```

### 4. Database State After Processing

```
HashCache:
  - Panzer Dragoon (USA).cue: MD5 abc123, calculated 0.5s
  - Panzer Dragoon (USA).chd: MD5 xyz789, calculated 1.2s

ROMTransformation:
  - source_md5: abc123
  - source_file_name: Panzer Dragoon (USA).cue
  - transformation_tool: extract → chdman
  - transformation_duration: 45.0
  - final_md5: xyz789
  - final_file_name: Panzer Dragoon (USA).chd

ScrapedGame:
  - source_md5: abc123  (linked via transformation!)
  - name: Panzer Dragoon
  - platform: Sega Saturn
  - region: USA
  - developer: Team Andromeda
  - publisher: Sega
  - release_date: 1995-05-11
  
MediaFile:
  - content_hash: cafe1234 (deduplicated)
  - media_type: boxart
  - format: png
  
GameMediaLink:
  - game_id: (Panzer Dragoon)
  - media_id: (boxart)
```

### 5. Final Output

```
/data/emu/flash/saturn/
  ├── Panzer Dragoon (USA).chd
  ├── gamelist.xml
  └── media/
      ├── images/
      │   ├── Panzer Dragoon (USA)-boxart.png
      │   └── Panzer Dragoon (USA)-screenshot.png
      └── videos/
          └── Panzer Dragoon (USA)-video.mp4
```

---

## Priority Roadmap

### Immediate (This Week)

1. **Configuration System** ⭐ HIGH PRIORITY
   - Create config models (Pydantic)
   - YAML loader
   - Validation
   - Example configs

2. **Simple Platform Test** ⭐ HIGH PRIORITY
   - Process NES end-to-end
   - Verify hooks work
   - Confirm database writes
   - Test with real files

3. **DAT Integration** ⭐ HIGH PRIORITY
   - Parse No-Intro DAT
   - Implement 1G1R filter
   - Test with NES

### Near Term (Next 2 Weeks)

4. **Source Registry**
   - Multi-source tracking
   - Priority resolution
   - Conflict handling

5. **Batch Processor**
   - Process entire platforms
   - Progress tracking
   - Resume capability

6. **Extended Profiles**
   - PS3 decryption stage
   - Multi-source merge stage
   - Emulator-specific organization

### Medium Term (Next Month)

7. **ScreenScraper Hook**
   - Auto-scrape with source hashes
   - Media download
   - Gamelist generation

8. **More Compression Tools**
   - PS2 (iso.gz)
   - Dreamcast (GDI → CHD)
   - Neo Geo CD

9. **CLI Improvements**
   - Better progress display
   - Interactive mode
   - Dry-run support

---

## Questions to Answer

Before we build the configuration system, let's clarify:

### 1. Source Organization

**Current State:**
```
/data/emu/source/myrient.erista.me/files/
  ├── No-Intro/
  │   ├── Nintendo - Nintendo Entertainment System/
  │   ├── Sega - Master System - Mark III/
  │   └── ...
  └── Redump/
      ├── Sega - Saturn/
      ├── Sony - PlayStation Portable/
      └── ...
```

**Questions:**
- Are there other source directories besides Myrient?
- Do you want to support multiple Myrient mirrors?
- Are DLC/updates/patches in separate directories?

### 2. Output Organization

**Questions:**
- Flat structure (`/flash/nes/*.nes`) or organized (`/flash/nes/USA/*.nes`)?
- Keep region tags in filenames or strip them?
- Separate directories per emulator (RPCS3 vs Batocera PS3)?

### 3. DAT Filtering

**Questions:**
- Always use 1G1R or sometimes want full sets?
- Region priority always USA → World → Europe → Japan?
- Language filtering needed (English, Spanish, etc.)?
- Include prototypes/betas/samples or exclude?

### 4. Processing Strategy

**Questions:**
- Process one platform at a time or multiple in parallel?
- In-place processing or copy-then-process?
- Keep originals or destructive?
- Verify before/after processing?

### 5. Metadata Strategy

**Questions:**
- Scrape during processing (inline) or separate batch afterward?
- Download all media types or just essentials (boxart + screenshot)?
- Generate gamelists per-platform or one master?
- Use existing ARRM data or re-scrape?

---

## My Recommendations

Based on the current state and goals:

### Start Simple, Build Complexity

**Phase 1: NES End-to-End** (This Week)
- Simplest case: No compression, no multi-disc, no encryption
- Proves config → DAT → filter → process → output works
- Tests hooks integration with real files
- Builds confidence before complexity

**Phase 2: Saturn** (Next Week)
- Adds compression (CHD)
- Tests transformation tracking
- Validates hash caching performance
- Still manageable complexity

**Phase 3: PSP with DLC** (Week 3)
- Multi-source handling
- Merge strategies
- Complex transformation chains
- Prepares for PS3

**Phase 4: PS3** (Week 4)
- Full complexity
- Decryption
- Key management
- Emulator-specific

### Configuration Philosophy

**Keep it Declarative:**
```yaml
# What you want, not how to do it
platforms:
  saturn:
    source: redump/Sega - Saturn
    output: flash/saturn
    format: chd
    filter: 1g1r_usa
```

**Layer Complexity:**
```yaml
# Simple config for simple needs
platforms:
  nes:
    enabled: true

# Complex config when needed
platforms:
  ps3:
    decryption:
      required: true
      keys: /keys/ps3
```

**Validate Early:**
- Check paths exist before starting
- Verify DATs are valid
- Test tools are available
- Estimate disk space needed

---

## Next Steps

What would you like to tackle first?

**Option A: Configuration System** (Recommended)
- Build the foundation
- Define the contract
- Makes everything else easier

**Option B: Simple Test First**
- Process a few NES games manually
- Verify hooks work end-to-end
- Then build config around proven flow

**Option C: DAT Integration**
- Parse No-Intro DAT
- Implement 1G1R filter
- Critical for multi-region collections

**Option D: Discuss More**
- Answer the questions above
- Clarify priorities
- Refine the design

I recommend **Option A** → build config system, then immediately test with NES (Option B) to validate it works. This gives us a solid foundation and proves the design with real data.

What do you think?
