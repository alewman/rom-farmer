# Phase 4: Redump/Saturn Processing (Days 6-8)

## Overview
Handle disc-based systems (Redump) with special focus on Saturn multi-disc games.

## Key Requirements

### 1. Multi-Disc Handling
- **M3U Creation**: For multi-disc games, create `.m3u` playlist files
  - List all disc CHDs for the game
  - Use first disc's metadata (name, region, etc.)
  - Example: `Panzer Dragoon Saga (USA) (Disc 1).chd` + Disc 2-4 → `Panzer Dragoon Saga (USA).m3u`

### 2. Metadata & Images
- **Use First Disc**: All metadata should come from Disc 1
  - Game title: From first disc
  - Region/language: From first disc
  - Scraper metadata: First disc only
- **Images for gamelist.xml**:
  - Box art / screenshots for first disc
  - M3U playlists: Use first disc's images
  - Single-disc games: Standard image handling

### 3. Extraction & Compression Pipeline
```
Source ZIP → Extract → Parse CUE → Compress BINs → Create CHD → Create M3U (if multi-disc)
```

## Stages to Implement

### ExtractArchiveStage
**Purpose**: Extract ZIP archives containing disc images

**Input**: 
- Source ZIPs matched by FilterDATStage
- Example: `Panzer Dragoon Saga (USA) (Disc 1).zip`

**Processing**:
1. Extract to temp directory
2. Parse `.cue` sheets
3. Validate `.bin` files exist
4. Track disc relationships (detect Disc 1, 2, 3, etc.)

**Output**:
- Extracted `.cue` + `.bin` files in work directory
- Disc metadata (which discs belong to which game)

**Context Updates**:
```python
context.extracted_files: List[Path]
context.disc_groups: Dict[str, List[Path]]  # Game base name → list of discs
```

### CompressCHDStage
**Purpose**: Convert BIN/CUE to CHD format

**Input**: Extracted disc images from ExtractArchiveStage

**Processing**:
1. For each `.cue` file:
   - Run `chdman createcd -i "game.cue" -o "game.chd"`
   - Verify CHD created successfully
   - Calculate hashes (CRC/MD5/SHA1)
   - Record transformation in ROMTransformation table

**Output**:
- `.chd` files in work directory
- Hash metadata stored

**Context Updates**:
```python
context.compressed_files: List[Path]
context.transformations: List[ROMTransformation]
```

### CreateM3UStage
**Purpose**: Create M3U playlists for multi-disc games

**Input**: CHD files from CompressCHDStage

**Processing**:
1. Group CHDs by game base name
   - `Panzer Dragoon Saga (USA) (Disc 1).chd` → base: `Panzer Dragoon Saga (USA)`
2. For each game with multiple discs:
   - Create `{base_name}.m3u` file
   - List all disc CHDs in order
   - Use relative paths
3. Single-disc games: No M3U needed

**M3U Format**:
```
Panzer Dragoon Saga (USA) (Disc 1).chd
Panzer Dragoon Saga (USA) (Disc 2).chd
Panzer Dragoon Saga (USA) (Disc 3).chd
Panzer Dragoon Saga (USA) (Disc 4).chd
```

**Output**:
- `.m3u` files for multi-disc games
- Updated file lists

**Context Updates**:
```python
context.m3u_files: List[Path]
context.disc_metadata: Dict[str, DiscMetadata]  # Track first disc for metadata
```

## Disc Metadata Structure

```python
@dataclass
class DiscMetadata:
    """Metadata for a disc-based game."""
    
    game_base_name: str  # "Panzer Dragoon Saga (USA)"
    first_disc_path: Path  # Path to Disc 1 CHD
    all_discs: List[Path]  # All disc CHDs in order
    disc_count: int  # Total number of discs
    
    # Metadata from first disc only
    title: str  # Clean title from first disc
    region: str  # USA, Europe, Japan, etc.
    language: Optional[str]
    
    # For gamelist.xml later
    needs_m3u: bool  # True if multi-disc
    primary_file: Path  # M3U if multi-disc, CHD if single
```

## Implementation Plan

### Day 6: ExtractArchiveStage
- [ ] Create `src/romgroomer/stages/extract.py`
- [ ] Implement ZIP extraction
- [ ] Parse CUE sheets
- [ ] Detect disc relationships
- [ ] Group multi-disc games
- [ ] Tests with real Saturn ZIPs

### Day 7: CompressCHDStage
- [ ] Create `src/romgroomer/stages/compress.py`
- [ ] Integrate chdman (already installed in tools/)
- [ ] Compress BIN/CUE → CHD
- [ ] Calculate and store hashes
- [ ] Track transformations
- [ ] Tests with real Saturn discs

### Day 8: CreateM3UStage + Integration
- [ ] Create `src/romgroomer/stages/m3u.py`
- [ ] Implement M3U generation
- [ ] Track first disc metadata
- [ ] Update Pipeline for Redump systems
- [ ] End-to-end Saturn demo
- [ ] Tests with multi-disc games

## Saturn-Specific Pipeline

For Saturn (system_type=COMPLEX):
```python
pipeline = Pipeline()
pipeline.add_stage(FilterDATStage())      # Match against Retool DAT
pipeline.add_stage(ApplyListsStage())     # Delete unwanted, create subdirs
pipeline.add_stage(ExtractArchiveStage()) # Extract ZIPs → CUE/BIN
pipeline.add_stage(CompressCHDStage())    # Compress → CHD
pipeline.add_stage(CreateM3UStage())      # Create M3U for multi-disc
pipeline.add_stage(OrganizeStage())       # Organize final files
```

## Example Saturn Game

**Input** (Myrient source):
```
Panzer Dragoon Saga (USA) (Disc 1).zip
Panzer Dragoon Saga (USA) (Disc 2).zip
Panzer Dragoon Saga (USA) (Disc 3).zip
Panzer Dragoon Saga (USA) (Disc 4).zip
```

**After ExtractArchiveStage**:
```
work/
  Panzer Dragoon Saga (USA) (Disc 1).cue
  Panzer Dragoon Saga (USA) (Disc 1).bin
  Panzer Dragoon Saga (USA) (Disc 2).cue
  Panzer Dragoon Saga (USA) (Disc 2).bin
  ... (Discs 3-4)
```

**After CompressCHDStage**:
```
work/
  Panzer Dragoon Saga (USA) (Disc 1).chd
  Panzer Dragoon Saga (USA) (Disc 2).chd
  Panzer Dragoon Saga (USA) (Disc 3).chd
  Panzer Dragoon Saga (USA) (Disc 4).chd
```

**After CreateM3UStage**:
```
work/
  Panzer Dragoon Saga (USA).m3u          <- Primary file for gamelist.xml
  Panzer Dragoon Saga (USA) (Disc 1).chd
  Panzer Dragoon Saga (USA) (Disc 2).chd
  Panzer Dragoon Saga (USA) (Disc 3).chd
  Panzer Dragoon Saga (USA) (Disc 4).chd
```

**After OrganizeStage** (BALANCED):
```
output/P/
  Panzer Dragoon Saga (USA).m3u
  Panzer Dragoon Saga (USA) (Disc 1).chd
  Panzer Dragoon Saga (USA) (Disc 2).chd
  Panzer Dragoon Saga (USA) (Disc 3).chd
  Panzer Dragoon Saga (USA) (Disc 4).chd
```

**gamelist.xml entry** (Phase 6):
```xml
<game>
  <path>./P/Panzer Dragoon Saga (USA).m3u</path>
  <name>Panzer Dragoon Saga</name>
  <image>./images/Panzer Dragoon Saga (USA) (Disc 1).png</image>
  <!-- Metadata from Disc 1 -->
</game>
```

## Configuration Integration

Update `SystemType` in `config/models.py`:
```python
class SystemType(str, Enum):
    SIMPLE = "simple"      # No extraction (NES, SNES, GB, GBA)
    MEDIUM = "medium"      # Extract but no compression (N64)
    COMPLEX = "complex"    # Extract + compress + M3U (Saturn, PS1, SegaCD)
```

Saturn config (`platforms/saturn.yaml`):
```yaml
system_type: complex
extract_archives: true
multi_disc_handling: true  # Enable M3U creation

targets:
  - name: batocera
    compression:
      format: chd
      create_m3u: true
    metadata:
      use_first_disc: true
      scrape_first_disc_only: true
```

## Hash Tracking

For transformations (important for your existing system):
```python
# Record: ZIP → CUE/BIN → CHD
transformation = ROMTransformation(
    original_file="Panzer Dragoon Saga (USA) (Disc 1).zip",
    original_crc="abc123",
    transformed_file="Panzer Dragoon Saga (USA) (Disc 1).chd",
    transformed_crc="def456",
    transformation_type="zip_to_chd",
    tool="chdman",
    tool_version="0.251",
)
```

## Testing Strategy

1. **Unit Tests**: Each stage individually
2. **Integration Test**: Full Saturn pipeline
3. **Real Data Test**: 
   - Single-disc game (e.g., Daytona USA)
   - Multi-disc game (e.g., Panzer Dragoon Saga - 4 discs)
   - Verify M3U creation
   - Verify first disc metadata

## Success Criteria

✅ Extract Saturn ZIPs successfully
✅ Compress to CHD with hash tracking
✅ Create M3U for multi-disc games
✅ Track first disc for metadata
✅ Pipeline processes 318 Saturn games
✅ All tests passing
✅ Ready for gamelist.xml generation (Phase 6)

## Notes

- **chdman** already installed in `/data/emu/rom-groomer-python/tools/`
- **Disc detection**: Parse "(Disc 1)", "(Disc 2)" from filenames
- **M3U priority**: M3U is the "primary" file, CHDs are dependencies
- **Metadata consistency**: Always use Disc 1 for scraping/images
- **Organization**: Keep M3U + all CHDs together in same directory
