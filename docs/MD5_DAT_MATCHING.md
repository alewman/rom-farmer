# MD5-Based DAT Matching

## Overview

The DAT filter stage now supports **dual-mode matching**:
1. **MD5 hash matching** (primary, handles renamed files)
2. **Filename matching** (fallback, traditional approach)

This solves the problem when ROM distributors (like Redump) improve their naming conventions, causing previously matched files to fail filename-based matching even though the content is identical.

## The Problem

When Redump updates region naming:
- Old name: `Dragon Age II (USA).zip`
- New name: `Dragon Age II (USA, Asia).zip`
- Same content, same MD5, but filename doesn't match DAT anymore

Without MD5 matching, you'd need to:
1. Get a new DAT file (if available)
2. Re-filter your entire collection
3. Deal with "missing" files that are actually just renamed

## The Solution

MD5 matching looks up files by their hash instead of name:
- Fast hash comparison (MD5 already calculated during metadata import)
- Immune to filename changes
- Falls back to name matching for new/unknown files

## How It Works

### Stage Flow

```
FilterDATStage:
  For each source file:
    1. Check if MD5 is available in context.file_md5s
    2. If yes: Try matcher.match_by_hash(md5=...)
    3. If no match: Try matcher.match_file() (name-based)
    4. Track statistics: hash_matched vs name_matched
```

### Context Setup

The `StageContext` includes an optional `file_md5s` dictionary:

```python
@dataclass
class StageContext:
    # ... other fields ...
    
    # File hashes (optional, for MD5-based DAT matching)
    file_md5s: Dict[Path, str] = field(default_factory=dict)
    """MD5 hashes for source files (from ARRM or computed)"""
```

### Populating MD5s

**Option 1: From ARRM Metadata (Redump systems)**

```python
from romgroomer.catalog.database import get_db_session, ScrapedGame

def populate_md5s_from_arrm(context: StageContext):
    """Load MD5 hashes from ARRM database."""
    session = get_db_session()
    
    for file_path in context.source_files:
        # Extract game name from ZIP filename
        game_name = file_path.stem  # "Dragon Age II (USA, Asia)"
        
        # Query ARRM database
        game = session.query(ScrapedGame).filter(
            ScrapedGame.system_id == context.platform_config.arrm_system_id,
            ScrapedGame.name == game_name
        ).first()
        
        if game and game.md5:
            context.file_md5s[file_path] = game.md5.lower()
    
    session.close()
```

**Option 2: Compute MD5s On-The-Fly**

```python
import hashlib
import zipfile

def populate_md5s_computed(context: StageContext):
    """Compute MD5 hashes for source files."""
    for file_path in context.source_files:
        if file_path.suffix.lower() == '.zip':
            # For ZIPs, hash the inner file (matches DAT behavior)
            try:
                with zipfile.ZipFile(file_path, 'r') as zf:
                    namelist = [n for n in zf.namelist() 
                               if not n.endswith('/') and not n.startswith('.')]
                    if namelist:
                        inner_file = namelist[0]
                        with zf.open(inner_file) as f:
                            md5 = hashlib.md5(f.read()).hexdigest()
                            context.file_md5s[file_path] = md5
            except (zipfile.BadZipFile, OSError):
                pass
```

## Usage Example

### Before Running Pipeline

```python
from romgroomer.stages import FilterDATStage, Pipeline
from romgroomer.config import load_platform_config

# Create pipeline
config = load_platform_config("ps3")
pipeline = Pipeline(config, target_name="ps3-usa")

# Add filter stage
filter_stage = FilterDATStage()
pipeline.add_stage(filter_stage)

# Run pipeline (context created internally)
results = pipeline.execute(
    source_dir=Path("/data/emu/source/ps3"),
    work_dir=Path("/data/emu/work/ps3"),
    output_dir=Path("/data/emu/output/ps3"),
    dat_file_path=Path("/data/emu/dats/redump/Sony - PlayStation 3.dat")
)
```

### Custom Pipeline with MD5 Pre-Loading

```python
from romgroomer.stages import FilterDATStage, StageContext
from romgroomer.catalog.database import get_db_session, ScrapedGame
from pathlib import Path

# Create context manually
context = StageContext(
    platform_name="ps3",
    platform_config=config,
    target_name="ps3-usa",
    source_dir=Path("/data/emu/source/ps3"),
    work_dir=Path("/data/emu/work/ps3"),
    output_dir=Path("/data/emu/output/ps3"),
    dat_file=dat_file,
    source_files=list(Path("/data/emu/source/ps3").glob("*.zip"))
)

# Populate MD5s from ARRM
session = get_db_session()
for file_path in context.source_files:
    game_name = file_path.stem
    game = session.query(ScrapedGame).filter(
        ScrapedGame.system_id == 52,  # PS3
        ScrapedGame.name == game_name
    ).first()
    if game and game.md5:
        context.file_md5s[file_path] = game.md5.lower()
session.close()

# Run filter stage
filter_stage = FilterDATStage()
result = filter_stage.execute(context)

# Check statistics
stats = context.stats["dat_filter"]
print(f"MD5 matched: {stats['hash_matched']}")
print(f"Name matched: {stats['name_matched']}")
print(f"Unmatched: {stats['unmatched_files']}")
```

## Statistics Output

The filter stage now reports:

```
Filter DAT
  Games in DAT: 4,893
  Source files: 4,850
  Matched: 4,845 (99.9%)
    MD5 matched: 95
    Name matched: 4,750
  Unmatched: 5
```

This tells you:
- **95 files** were matched by MD5 (likely renamed since DAT was created)
- **4,750 files** were matched by name (standard flow)
- **5 files** couldn't be matched (may need investigation)

## Performance Considerations

### MD5 Lookup Cost

- **ARRM pre-loaded**: O(1) dictionary lookup (nearly free)
- **On-the-fly computation**: ~100MB/sec (depends on file size)

### Recommendation

For **Redump systems** (disc-based):
- Use ARRM pre-loaded MD5s (already calculated during scrape)
- No additional cost during filtering

For **No-Intro systems** (cartridge-based):
- Name matching is usually sufficient
- MD5 pre-loading optional (ARRM also has these)

## Integration with Existing Code

The enhancement is **backward compatible**:
- If `context.file_md5s` is empty: Pure name-based matching (original behavior)
- If `context.file_md5s` is populated: MD5-first matching with name fallback
- No changes needed to existing pipeline code

## Future Enhancements

Potential improvements:
1. Auto-populate MD5s from ARRM when platform has `arrm_system_id`
2. Cache computed MD5s to database for future runs
3. Support CRC32/SHA1 matching for non-Redump systems
4. Add "renamed file report" showing old→new name mappings

## Example: PS3 Redump Updates

Recent Redump PS3 improvements (October 2025):

```
Before:
- Dragon Age II (USA).zip
- Fallout 3 (USA).zip
- Uncharted 2 (USA).zip

After:
- Dragon Age II (USA, Asia).zip
- Fallout 3 (USA, Canada).zip  
- Uncharted 2 - Among Thieves (USA).zip

Result with MD5 matching:
- All 3 files matched via MD5 hash
- Zero "missing files" false positives
- No need to re-download or update DAT
```

## Technical Details

### Matcher Implementation

The `ROMMatcher` class (in `src/romgroomer/dat_parser/matcher.py`) provides:

```python
class ROMMatcher:
    def match_file(self, file_path: Path) -> MatchResult:
        """Name-based matching (original)"""
        
    def match_by_hash(
        self,
        file_path: Path,
        crc: Optional[str] = None,
        md5: Optional[str] = None,
        sha1: Optional[str] = None,
    ) -> MatchResult:
        """Hash-based matching (new feature)"""
```

Both methods return a `MatchResult` with:
- `match_type`: EXACT_FILENAME, MD5_MATCH, etc.
- `dat_game`: Matched game from DAT
- `dat_rom`: Matched ROM entry
- `confidence`: 0.0 to 1.0

### Hash Indices

The matcher builds indices at initialization:

```python
def _build_indices(self):
    # Index by MD5
    self.md5_index: dict[str, tuple[DATGame, DATRom]] = {}
    for game in self.dat_file.games:
        for rom in game.roms:
            if rom.md5:
                self.md5_index[rom.md5.lower()] = (game, rom)
```

Lookup is O(1) dictionary access.

## See Also

- `src/romgroomer/stages/filter_dat.py` - Filter implementation
- `src/romgroomer/dat_parser/matcher.py` - Matching logic
- `src/romgroomer/stages/base.py` - StageContext definition
- `docs/ARRM_MD5_CUE_DISCOVERY.md` - CUE file MD5 documentation
