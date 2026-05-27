# ROM Grooming Workflow - Requirements & Design (FINAL)

## Executive Summary

Based on our discussion and analysis of the existing bash-based system, here's the complete workflow design for the Python rewrite.

---

## Core Workflow Stages

### Stage 0: SOURCE (Myrient Archives)
**Location**: `/path/to/source/myrient/`
**Content**: Original ZIP archives from Myrient (No-Intro + Redump)
**State**: Read-only, never modified

### Stage 1: EXTRACTED (Raw ROMs)
**Location**: `/path/to/stage/01-extracted/{platform}/`
**Process**: Extract all ROMs from ZIP archives
**Output**: Raw ROM files (unfiltered)
**Purpose**: Checkpoint before filtering

### Stage 2: FILTERED (DAT-based filtering applied)
**Location**: `/path/to/stage/02-filtered/{platform}/`
**Process**: 
- Apply 1G1R.eng filter (or usa-only for tiny systems)
- Use Retool DATs for better game selection
- Remove unwanted regions/languages
**Output**: Curated ROM set based on DAT priorities
**Purpose**: Clean collection before additions/deletions

### Stage 3: MODIFIED (List-based add/delete)
**Location**: `/path/to/stage/03-modified/{platform}/`
**Process**: 
- Delete unwanted ROMs (`{system}-delete` lists)
- Add Best Games (`{system}+Best-Games` from Myrient)
- Add extras (`{system}.English-Translations` from extra sources)
**Output**: Final ROM selection
**Purpose**: Manual curation on top of DAT filtering

### Stage 4: PROCESSED (Compressed/Converted)
**Location**: `/path/to/stage/04-processed/{platform}/`
**Process**: 
- Compress to CHD, CSO, RVZ, NSZ, etc.
- Decrypt (PS3, Xbox 360)
- Transform for emulator requirements
**Output**: Emulator-ready files
**Purpose**: Optimization and format conversion

### Stage 5: ORGANIZED (Target structure)
**Location**: `/path/to/stage/05-organized/{platform}/`
**Process**: 
- Organize for target system (Batocera, RocknIX, Everdrive)
- Create subdirectories (sort2folders.sh logic)
- Apply naming conventions
**Output**: Final directory structure
**Purpose**: Ready for deployment

### Stage 6: FINAL (Deployed)
**Location**: Target system (e.g., `/path/to/...{platform}/`)
**Process**: Copy/rsync to final destination
**Output**: Production ROM collection
**Purpose**: Actual usable collection

---

## List File System (Existing Pattern to Preserve)

### Three Types of List Files

#### 1. Delete Lists: `{system}-{name}`
**Examples**: 
- `nes-delete`
- `snes-Problematic-Games`
- `psx-Remove-Demos`

**Purpose**: Remove specific ROMs after DAT filtering
**Applied**: Stage 2 → Stage 3
**Why**: DAT files don't know about newer pirate carts, bad aftermarket ROMs, etc.

**Example `nes-delete`:**
```
BullyBoy 500-in-1 (World) (Aftermarket) (Pirate).zip
CoolBoy 400-in-1 Real Game (World) (Aftermarket) (Pirate).zip
Munchie Attack (World) (Aftermarket) (Unl).zip
```

#### 2. Add from Myrient: `{system}+{name}`
**Examples**: 
- `nes+Best-Games`
- `sega32x+Hidden-Gems`
- `snes+SNES-Classic-Edition-USA`

**Purpose**: Add specific ROMs that were filtered out but you want
**Source**: Myrient archive (original source)
**Applied**: Stage 3 (creates subdirectory with list name)
**Output Structure**:
```
/stage/03-modified/nes/
  ├── [filtered games...]
  └── Best-Games/
      ├── Contra (USA).zip
      ├── Mega Man 2 (USA).zip
      └── [other best games...]
```

**Example `nes+Best-Games`:**
```
Adventures of Lolo (USA).zip
Batman - The Video Game (USA).zip
Castlevania III - Dracula's Curse (USA).zip
Contra (USA).zip
Mega Man 2 (USA).zip
Super Mario Bros. 3 (USA) (Rev 1).zip
```

#### 3. Add from Extra: `{system}.{name}`
**Examples**: 
- `nes.English-Translations`
- `sega32x.Best-Games`
- `snes.Homebrew-Collection`

**Purpose**: Add ROMs from custom/extra sources (not in Myrient)
**Source**: `/path/to/source/extra/{system}/`
**Applied**: Stage 3 (creates subdirectory with list name)
**Output Structure**:
```
/stage/03-modified/nes/
  ├── [filtered games...]
  └── English-Translations/
      ├── Final Fantasy III (Japan) [English v1.0].zip
      └── [other translations...]
```

### List File Format
- One filename per line
- Exact match (case-sensitive)
- Include file extension
- Empty lines ignored
- No wildcards

---

## Target System Requirements

### Batocera (No Limits - Rich Organization)
**Structure**: Deep subdirectories with rich organization
```
/flash/nes/
  ├── By Language/
  │   ├── En/
  │   ├── Ja/
  │   └── Multi/
  ├── By Genre/
  │   ├── Action/
  │   ├── RPG/
  │   └── Puzzle/
  ├── Best-Games/
  └── English-Translations/
```

**Features**:
- Long filenames OK
- Deep directory nesting
- Full metadata (gamelist.xml with all media)
- No practical limits

### RocknIX (Modest Limits - Balanced)
**Structure**: Moderate organization
```
/flash/nes/
  ├── A-E/
  ├── F-M/
  ├── N-S/
  ├── T-Z/
  ├── Best-Games/
  └── Translations/
```

**Features**:
- Reasonable filename lengths
- 2-3 levels of subdirectories
- Essential metadata only
- ~1000-2000 games per system

### Everdrive (Severe Limits - Minimal)
**Structure**: Flat or minimal subdirectories
```
/nes/
  ├── #-C/
  ├── D-M/
  ├── N-Z/
  └── Best/
```

**Features**:
- Limit total files per directory (~100-200)
- Short paths preferred
- Use `sort2folders.sh` logic for alphabetical grouping
- Minimal metadata
- May need filename truncation
- Use jdupes for deduplication across systems

**sort2folders.sh Logic**:
- Analyzes file distribution by first character
- Creates smart groups (e.g., #-C, D-F, G-M, N-S, T-Z)
- Default: max 50 files per group
- Handles numbers/symbols as "#" (alphabetically first)
- Sub-letter splitting for massive collections (Sa-Sg/, Sh-So/)

---

## DAT Filtering Strategy

### Primary Strategy: 1G1R.eng
**Definition**: One Game, One ROM - English-language focused

**Selection Priority**:
1. USA releases
2. World releases (usually English)
3. Europe releases with English
4. Japanese shmups (minimal text - identified by Retool)

**Tools**:
- Retool DATs (better curation than raw No-Intro)
- Region tags: `(USA)`, `(World)`, `(Europe)`, `(En)`
- Language detection from filenames

**Why**: Sweet spot - gets the games people want without overwhelming collections

### Alternative Strategy: usa-only
**For**: Very tiny systems (Everdrive with severe limits)
**Selection**: Only USA + World releases
**Output**: Smaller collection, easier to navigate

### Retool Integration
**What Retool Does**:
- Identifies better ROM versions (e.g., Mega Man X Rev 1 vs bad dump original)
- Tags Japanese shmups that are playable without knowing Japanese
- Curates "best versions" of multi-release games

**How We Use It**:
- Retool DATs for filtering decisions
- Manual "Best Games" lists supplement Retool recommendations
- Retool unknown for Redump disc images (disc-based systems)

---

## Source Directory Structure

### Myrient (Primary - Canonical)
```
/path/to/source/myrient/
  ├── No-Intro/
  │   ├── Nintendo - Nintendo Entertainment System/
  │   │   ├── Game1 (USA).zip
  │   │   └── ...
  │   └── Sega - Master System/
  └── Redump/
      ├── Sega - Saturn/
      └── Sony - PlayStation Portable/
```

**Priority**: 100 (highest)
**Type**: Canonical source
**Filter**: Apply 1G1R.eng or usa-only

### Extra Sources (Supplemental)
```
/path/to/source/extra/
  ├── nes/
  │   ├── translations/
  │   │   └── Final Fantasy III [English].zip
  │   └── homebrew/
  └── snes/
      └── romhacks/
```

**Priority**: 50-75 (medium)
**Type**: Supplemental
**Filter**: Manual lists only (`.` pattern)

### Best Games (Manual Curation)
**Source**: Either from Myrient (via `+` lists) or Extra (via `.` lists)
**Priority**: Depends on source
**Purpose**: Curated collections beyond DAT filtering

---

## Configuration File Design

```yaml
# config/nes-batocera.yaml

global:
  database: metadata/database/romfarmer.db
  temp_dir: /tmp/romfarmer
  
  # Stage management
  stages:
    base_dir: /path/to/...
    keep_all: true  # Keep all stages until proven reliable
    auto_resume: true
    state_file: .romfarmer_state.json

# Source directories
sources:
  myrient_nointro:
    type: canonical
    priority: 100
    base_path: /path/to/source/myrient/No-Intro
  
  extra:
    type: supplemental
    priority: 50
    base_path: /path/to/source/extra

# List files for manual curation
lists:
  directory: /path/to/...
  # Patterns: {system}-{name} = delete
  #           {system}+{name} = add from Myrient
  #           {system}.{name} = add from extra

# DAT configuration
dats:
  directory: /path/to/...
  
  # Retool DATs for better curation
  retool:
    enabled: true
    directory: /path/to/dats/retool
  
  # Filter strategies
  strategies:
    1g1r_eng:
      description: "USA + English EUR + JP shmups"
      regions: [USA, World, Europe, Japan]
      languages: [En]
      prefer_regions: [USA, World]
      use_retool: true
    
    usa_only:
      description: "USA + World only (tiny systems)"
      regions: [USA, World]
      use_retool: true

# Platform: NES (Simple - Cartridge System)
platforms:
  nes:
    enabled: true
    description: "Nintendo Entertainment System"
    
    # Sources
    source:
      primary:
        source: myrient_nointro
        subpath: Nintendo - Nintendo Entertainment System
        filter_strategy: 1g1r_eng
      
      # List-based additions
      lists:
        - nes-delete              # Remove pirate carts
        - nes+Best-Games          # Add best games from Myrient
        - nes.English-Translations  # Add translations from extra
    
    # DAT validation
    dat: nointro/Nintendo - Nintendo Entertainment System.dat
    
    # Processing stages
    stages:
      - extract_archive       # Stage 1
      - filter_dat            # Stage 2
      - apply_lists           # Stage 3 (delete + add)
      - organize_for_target   # Stage 5 (no compression for cartridge)
    
    # Hooks
    hooks:
      - hash_capture
      - validation
      - progress
    
    # Output configuration
    output:
      target: batocera
      path: /path/to/...
      
      # Organization strategy for Batocera
      organization:
        type: rich  # Deep subdirectories
        subdirs:
          - type: language
            source: metadata
          - type: genre
            source: metadata
          - type: list_name
            source: lists  # Best-Games/, English-Translations/
    
    # Metadata
    metadata:
      source: existing  # Use pre-scraped ARRM data
      fallback: none    # Don't scrape new games yet (no dev account)
      gamelist: true
      media_types: [boxart, screenshot, wheel]

# Platform: Saturn (Medium - Disc with Compression)
platforms:
  saturn:
    enabled: true
    description: "Sega Saturn"
    
    source:
      primary:
        source: myrient_redump
        subpath: Sega - Saturn
        filter_strategy: 1g1r_eng
      
      lists:
        - saturn-delete
        - saturn+Best-Games
    
    dat: redump/Sega - Saturn.dat
    
    stages:
      - extract_archive
      - filter_dat
      - apply_lists
      - compress_chd          # Stage 4 (compression)
      - organize_for_target
    
    stage_config:
      compress_chd:
        compression: default
        processors: 4
    
    hooks:
      - hash_capture          # Before & after compression
      - transformation_tracking  # Link source → CHD
      - progress
    
    output:
      target: batocera
      path: /path/to/...
      organization:
        type: rich
        subdirs:
          - type: language
          - type: list_name
    
    metadata:
      source: existing
      fallback: none
      gamelist: true

# Platform: NES for Everdrive (Minimal - Flat Structure)
platforms:
  nes_everdrive:
    enabled: false  # Manual enable for specific builds
    description: "NES for Everdrive flashcart"
    
    source:
      primary:
        source: myrient_nointro
        subpath: Nintendo - Nintendo Entertainment System
        filter_strategy: usa_only  # Smaller collection
      
      lists:
        - nes-delete
        - nes+Best-Games
    
    dat: nointro/Nintendo - Nintendo Entertainment System.dat
    
    stages:
      - extract_archive
      - filter_dat
      - apply_lists
      - organize_for_target
    
    output:
      target: everdrive
      path: /path/to/...
      
      # Minimal organization for flashcart
      organization:
        type: minimal
        max_files_per_dir: 50
        alphabetical_grouping: true  # Use sort2folders.sh logic
        subdirs:
          - type: list_name  # Only Best-Games/ subdirectory
    
    metadata:
      source: none  # No metadata for flashcarts
      gamelist: false
```

---

## Processing Stages Implementation

### Stage 1: Extract Archive
```python
class ExtractArchiveStage(ProcessingStage):
    """Extract ROM files from ZIP/7z archives."""
    
    async def process(self, input_path: Path, context: dict) -> Path:
        # Extract to stage/01-extracted/{platform}/
        output_dir = context['stage_dir'] / '01-extracted' / context['platform']
        
        # Extract ZIP
        extracted_files = self.extract_zip(input_path, output_dir)
        
        return extracted_files[0]  # Return first file (or all for multi-disc)
```

### Stage 2: Filter DAT
```python
class FilterDATStage(ProcessingStage):
    """Apply 1G1R filtering based on DAT file."""
    
    async def process(self, input_path: Path, context: dict) -> Path:
        # Read from stage/01-extracted/
        # Apply 1G1R.eng filtering
        # Output to stage/02-filtered/
        
        dat = self.load_dat(context['dat_file'])
        filter_strategy = context['filter_strategy']  # 1g1r_eng or usa_only
        
        filtered_games = self.apply_filter(dat, filter_strategy)
        
        # Copy only filtered games to output
        output_dir = context['stage_dir'] / '02-filtered' / context['platform']
        for game in filtered_games:
            shutil.copy(input_path / game, output_dir / game)
        
        return output_dir
```

### Stage 3: Apply Lists
```python
class ApplyListsStage(ProcessingStage):
    """Apply delete/add lists for manual curation."""
    
    async def process(self, input_path: Path, context: dict) -> Path:
        # Read from stage/02-filtered/
        # Apply list files
        # Output to stage/03-modified/
        
        output_dir = context['stage_dir'] / '03-modified' / context['platform']
        
        # Copy all filtered files first
        shutil.copytree(input_path, output_dir)
        
        # Process delete lists: {system}-delete
        for delete_list in context['delete_lists']:
            self.apply_delete_list(output_dir, delete_list)
        
        # Process add lists from Myrient: {system}+{name}
        for add_list in context['add_myrient_lists']:
            list_name = add_list.stem.split('+')[1]  # Extract "Best-Games"
            subdir = output_dir / list_name
            subdir.mkdir(exist_ok=True)
            self.apply_add_list(subdir, add_list, myrient_source)
        
        # Process add lists from extra: {system}.{name}
        for add_list in context['add_extra_lists']:
            list_name = add_list.stem.split('.')[1]  # Extract "English-Translations"
            subdir = output_dir / list_name
            subdir.mkdir(exist_ok=True)
            self.apply_add_list(subdir, add_list, extra_source)
        
        return output_dir
    
    def apply_delete_list(self, directory: Path, list_file: Path):
        """Delete files listed in delete list."""
        with open(list_file) as f:
            for line in f:
                filename = line.strip()
                if not filename:
                    continue
                file_path = directory / filename
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Deleted: {filename}")
    
    def apply_add_list(self, target_dir: Path, list_file: Path, source_dir: Path):
        """Add files from list (symlink or copy)."""
        with open(list_file) as f:
            for line in f:
                filename = line.strip()
                if not filename:
                    continue
                source_file = source_dir / filename
                target_file = target_dir / filename
                if source_file.exists():
                    # Create symlink (or copy for portability)
                    target_file.symlink_to(source_file)
                    logger.info(f"Added: {filename}")
```

### Stage 4: Compress (if needed)
```python
class CompressCHDStage(ProcessingStage):
    """Compress disc images to CHD format."""
    
    async def process(self, input_path: Path, context: dict) -> Path:
        # Read from stage/03-modified/
        # Compress to CHD
        # Output to stage/04-processed/
        
        output_dir = context['stage_dir'] / '04-processed' / context['platform']
        output_file = output_dir / f"{input_path.stem}.chd"
        
        # Run chdman
        await self.run_chdman(input_path, output_file)
        
        return output_file
```

### Stage 5: Organize for Target
```python
class OrganizeForTargetStage(ProcessingStage):
    """Organize files for target system."""
    
    async def process(self, input_path: Path, context: dict) -> Path:
        # Read from stage/03-modified/ or stage/04-processed/
        # Organize based on target system
        # Output to stage/05-organized/
        
        target_type = context['output']['target']  # batocera, rocknix, everdrive
        output_dir = context['stage_dir'] / '05-organized' / context['platform']
        
        if target_type == 'batocera':
            # Rich organization with subdirectories
            self.organize_rich(input_path, output_dir, context)
        
        elif target_type == 'everdrive':
            # Minimal organization with sort2folders logic
            self.organize_minimal(input_path, output_dir, context)
        
        return output_dir
    
    def organize_minimal(self, source: Path, dest: Path, context: dict):
        """Apply sort2folders.sh logic for flashcarts."""
        max_files = context['output']['organization']['max_files_per_dir']
        
        # Analyze file distribution
        file_groups = self.calculate_smart_groups(source, max_files)
        
        # Create subdirectories and move files
        for group_name, files in file_groups.items():
            group_dir = dest / group_name
            group_dir.mkdir(exist_ok=True)
            for file in files:
                shutil.copy(file, group_dir / file.name)
```

---

## Stage Checkpointing & Resume

### State Tracking
```python
# .romfarmer_state.json
{
  "platform": "nes",
  "last_run": "2025-10-12T10:30:00",
  "completed_stages": {
    "extract_archive": {
      "completed": true,
      "timestamp": "2025-10-12T10:15:00",
      "file_count": 1500,
      "output": "/path/to/stage/01-extracted/nes"
    },
    "filter_dat": {
      "completed": true,
      "timestamp": "2025-10-12T10:20:00",
      "file_count": 450,
      "output": "/path/to/stage/02-filtered/nes"
    },
    "apply_lists": {
      "completed": false,
      "timestamp": null
    }
  },
  "current_stage": "apply_lists",
  "errors": []
}
```

### Resume Logic
```python
class BatchProcessor:
    async def process_platform(self, platform_config):
        state = self.load_state(platform_config.name)
        
        for stage_name in platform_config.stages:
            if state.is_completed(stage_name):
                # Ask user if they want to re-run
                if not self.prompt_rerun(stage_name):
                    logger.info(f"Skipping completed stage: {stage_name}")
                    continue
            
            # Run stage
            stage = self.stages[stage_name]
            result = await stage.process(input_path, context)
            
            # Save state
            state.mark_completed(stage_name, result)
            self.save_state(state)
```

---

## Metadata Strategy

### Current Approach (Phase 1)
**Source**: Pre-scraped ARRM data (existing gamelist.xml files)
**Coverage**: Good for common games
**Limitation**: No ScreenScraper dev account yet

### Future Approach (Phase 2)
**Bulk Pre-population**:
1. Run bulk ScreenScraper job on all Myrient source files
2. Query with SOURCE hashes (from HashCache)
3. Store in ScrapedGame table
4. Download media to content-addressable storage

**On-the-fly Lookup**:
- For unknown games (patches, hacks, homebrew)
- Fuzzy matching (e.g., "Contra [30 Lives]" → lookup "Contra")
- Community database fallback
- Manual override file for special cases

### Metadata Linking
```python
# Use ROMTransformation to link compressed files to source hashes
transformation = db.get_transformation_by_final_hash(chd_md5)
source_md5 = transformation.source_md5

# Query ScreenScraper with SOURCE hash (what they know about)
metadata = screenscraper.query(md5=source_md5, platform='saturn')
```

---

## Implementation Priority

### Week 1: Configuration System + Simple Test
1. Build config models (Pydantic)
2. YAML loader with validation
3. Test with NES (simplest case)
4. Verify all stages work end-to-end

### Week 2: List File System
1. Implement ApplyListsStage
2. Support `-` delete pattern
3. Support `+` add from Myrient
4. Support `.` add from extra
5. Test with real list files

### Week 3: DAT Integration
1. Parse No-Intro/Redump DAT files
2. Implement 1G1R.eng filter
3. Integrate Retool DATs
4. Test with multiple regions

### Week 4: Target Organization
1. Implement organize_rich (Batocera)
2. Implement organize_minimal (Everdrive)
3. Port sort2folders.sh logic to Python
4. Test with different targets

### Week 5: Disc Systems
1. Test with Saturn (CHD compression)
2. Test with PSP (CSO compression)
3. Verify transformation tracking works
4. Hash caching performance testing

### Week 6: Complex Systems
1. PS3 decryption stage
2. Multi-disc handling
3. Emulator-specific organization
4. Full integration testing

---

## Questions Answered

### Q: How to handle deletes?
**A**: List files with `-` pattern, processed in Stage 3 AFTER DAT filtering but BEFORE compression

### Q: How to add extra games?
**A**: List files with `+` (from Myrient) or `.` (from extra), creates subdirectories with list name

### Q: Stage workflow correct?
**A**: Yes! Extract → Filter → Modify → Process → Organize → Deploy

### Q: Keep all stages?
**A**: Yes, for now (have 3TB space). Later can cleanup when proven reliable.

### Q: Batocera structure?
**A**: Rich organization with deep subdirectories (language, genre, list names)

### Q: Everdrive limits?
**A**: Use sort2folders.sh logic - max 50 files per alphabetical group, minimal subdirs

### Q: Europe games?
**A**: Region tag `(Europe)` or `(En)` identifies English EUR games

### Q: Japanese shmups?
**A**: Retool DATs identify them

### Q: Best Games source?
**A**: Manual curation, either from Myrient (`+` lists) or extra (`.` lists)

### Q: Multiple same-region versions?
**A**: Retool DATs handle this (prefer Rev 1 over bad dumps, etc.)

### Q: Metadata strategy?
**A**: Use existing ARRM data for now, bulk ScreenScraper run later (when dev account acquired)

---

## Success Criteria

✅ **Stage 1 Complete** when:
- Can process NES end-to-end
- All 6 stages work
- List files applied correctly
- Output matches expected structure

✅ **Stage 2 Complete** when:
- Saturn with CHD compression works
- Transformation tracking verified
- Hash caching works

✅ **Stage 3 Complete** when:
- Multiple targets (Batocera, Everdrive) working
- sort2folders logic ported
- Organization correct for each target

✅ **Production Ready** when:
- All cartridge systems working
- All disc systems working
- Complex systems (PS3, Xbox 360) working
- Can process full collection reliably
- Intermediate stages can be safely deleted

---

## Next Steps

**Immediate**: Start building configuration system with Pydantic models

**Question for you**: Should we start with a minimal config for NES and expand, or design the full config structure upfront?

I recommend: **Minimal first** - Get NES working end-to-end with basic config, then expand the config schema as we add complexity. This validates the design before we commit to it.

What do you think?
