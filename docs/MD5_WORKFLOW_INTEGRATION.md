# MD5-Based DAT Matching - Complete Workflow Integration

## Yes! Your Existing Metadata Import Already Primes Everything

### The Complete Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    EXISTING ARRM Metadata Import                    │
│                   (You already run this normally!)                  │
└─────────────────────────────────────────────────────────────────────┘

STEP 1: Run ARRM on your collection
  ├─ ARRM scrapes ScreenScraper.fr for game metadata
  ├─ Generates gamelist.xml with MD5 hashes
  └─ Located at: /data/emu/roms/saturn/gamelist.xml

        <?xml version="1.0"?>
        <gameList>
          <provider>
            <System>saturn</System>
          </provider>
          <game>
            <path>./3D Lemmings (USA).chd</path>
            <name>3D Lemmings</name>
            <md5>a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4</md5>  ◄─── MD5 HERE!
            <desc>Guide the Lemmings...</desc>
            <rating>0.75</rating>
            ...
          </game>
        </gameList>

STEP 2: Import into RomGroomer database
  Command: romgroomer metadata import-arrm /data/emu/roms/saturn/gamelist.xml
  
  What happens:
  ├─ ARRMImporter parses gamelist.xml
  ├─ Extracts game metadata INCLUDING md5 field
  ├─ Creates ScrapedGame records in database
  └─ MD5 stored in scraped_games.md5 column (indexed!)

        ScrapedGame record:
        ┌──────────────────────────────────────────────┐
        │ id: 12345                                    │
        │ name: "3D Lemmings"                          │
        │ system: "saturn"                             │
        │ md5: "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"      │  ◄─── STORED!
        │ description: "Guide the Lemmings..."         │
        │ rating: 0.75                                 │
        │ ...                                          │
        └──────────────────────────────────────────────┘

STEP 3: Now DAT filtering can use these MD5s!
  
  When running DAT filter:
  ├─ Query database by game name
  ├─ Retrieve MD5 from ScrapedGame record
  ├─ Store in context.file_md5s[file_path] = md5
  └─ Filter stage automatically uses MD5-first matching!

        # Pre-filter hook (automatic with platform config)
        session = get_db_session()
        for file_path in context.source_files:
            game_name = file_path.stem
            game = session.query(ScrapedGame).filter(
                ScrapedGame.system == "ps3",
                ScrapedGame.name == game_name
            ).first()
            
            if game and game.md5:
                context.file_md5s[file_path] = game.md5  ◄─── USE IT!
```

## Database Structure

```
┌──────────────────────────────────────────────────────────────────────┐
│                    RomGroomer Metadata Database                      │
│                   (~/.local/share/romgroomer/...)                    │
└──────────────────────────────────────────────────────────────────────┘

TABLE: scraped_games
┌────────────┬──────────────────────────────────┬───────────┬──────────┐
│ id         │ name                             │ system    │ md5      │
├────────────┼──────────────────────────────────┼───────────┼──────────┤
│ 1001       │ 3D Lemmings                      │ saturn    │ a1b2c... │
│ 1002       │ Street Fighter Collection        │ saturn    │ f1e2d... │
│ 1003       │ Nights into Dreams...            │ saturn    │ 1a2b3... │
│ ...        │ ...                              │ ...       │ ...      │
│ 5001       │ Dragon Age II (USA, Asia)        │ ps3       │ 9x8y7... │
│ 5002       │ Fallout 3 (USA, Canada)          │ ps3       │ 6z5w4... │
│ 5003       │ Uncharted 2 - Among Thieves      │ ps3       │ 3v2u1... │
└────────────┴──────────────────────────────────┴───────────┴──────────┘
                                                                ▲
                                                                │
                                                    These MD5s are indexed
                                                    for fast lookup!
```

## Your Current Saturn Workflow (Already Works!)

```
┌─────────────────────────────────────────────────────────────────────┐
│              What You Did for Saturn (October 2025)                 │
└─────────────────────────────────────────────────────────────────────┘

Step 1: Built Saturn collection
  ├─ Converted CUE/BIN to CHD format
  ├─ Created M3U playlists for multi-disc games
  └─ Output: /data/emu/output/saturn/*.chd

Step 2: Ran ARRM metadata scraper
  ├─ ARRM scraped 332 Saturn games
  ├─ Calculated MD5 for each CHD file
  └─ Generated: /data/emu/output/saturn/gamelist.xml

Step 3: Imported metadata into RomGroomer
  ├─ Command: romgroomer metadata import-arrm gamelist.xml
  ├─ Imported 332 ScrapedGame records
  └─ Database now has MD5 for all 332 games!

Step 4: (Optional) Now can use for DAT filtering
  ├─ If you need to re-filter Saturn collection
  ├─ MD5s already in database
  └─ Automatic MD5-first matching available!

Result:
  ✓ Database primed with 332 Saturn MD5 hashes
  ✓ Ready for MD5-based DAT matching
  ✓ No additional work needed!
```

## PS3 Example (Your Use Case)

```
┌─────────────────────────────────────────────────────────────────────┐
│                PS3 Collection with Renamed Files                    │
└─────────────────────────────────────────────────────────────────────┘

SCENARIO: You imported PS3 metadata BEFORE Redump renamed files

Step 1: Initial import (October 2024)
  ├─ ARRM scraped PS3 collection
  ├─ Games had old names: "Dragon Age II (USA)"
  ├─ Imported to database with MD5: a1b2c3d4...
  └─ Database entry created

Step 2: Redump improves naming (October 2025)
  ├─ Redump updates: "Dragon Age II (USA)" → "Dragon Age II (USA, Asia)"
  ├─ Your rclone sync downloads new filename
  ├─ Same content, same MD5: a1b2c3d4...
  └─ But filename doesn't match database anymore!

Step 3: Re-run ARRM import (updates database)
  ├─ ARRM scrapes with new filenames
  ├─ Generates gamelist.xml with: "Dragon Age II (USA, Asia)"
  ├─ Import updates database: name changes, MD5 stays same
  └─ Database now has: name="Dragon Age II (USA, Asia)", md5=a1b2c3d4...

Step 4: Run DAT filter
  ├─ DAT still has old name: "Dragon Age II (USA)"
  ├─ Source file has new name: "Dragon Age II (USA, Asia).zip"
  ├─ Query database by new name → Get MD5: a1b2c3d4...
  ├─ Try MD5 match against DAT → SUCCESS!
  ├─ MD5 in DAT matches: a1b2c3d4... = a1b2c3d4...
  └─ File matched! No "missing file" warning!

RESULT:
  ✓ Renamed file automatically matched via MD5
  ✓ No false "missing file" warnings
  ✓ No need to update DAT file
  ✓ Seamless workflow!
```

## Command Examples

### Import Metadata (Primes MD5 Lookup)

```bash
# Saturn collection
romgroomer metadata import-arrm \
  /data/emu/output/saturn/gamelist.xml \
  --database ~/.local/share/romgroomer/metadata.db \
  --media-storage ~/.local/share/romgroomer/media

# PS3 collection
romgroomer metadata import-arrm \
  /data/emu/roms/ps3/gamelist.xml \
  --database ~/.local/share/romgroomer/metadata.db \
  --media-storage ~/.local/share/romgroomer/media

# Update existing records (when Redump renames files)
romgroomer metadata import-arrm \
  /data/emu/roms/ps3/gamelist.xml \
  --update  # Updates name, keeps MD5 if same file
```

### Verify MD5s Are Loaded

```bash
# Check database has MD5s
sqlite3 ~/.local/share/romgroomer/metadata.db \
  "SELECT COUNT(*) FROM scraped_games WHERE md5 IS NOT NULL;"

# Check specific game
sqlite3 ~/.local/share/romgroomer/metadata.db \
  "SELECT name, md5 FROM scraped_games WHERE name LIKE '%Dragon Age%';"
```

### Run DAT Filter (Uses MD5s Automatically)

```bash
# The filter stage will automatically:
# 1. Query database for MD5s
# 2. Try MD5 matching first
# 3. Fall back to name matching
# 4. Show statistics breakdown

romgroomer build run ps3-usa-1g1r
```

## Key Points

### ✅ What You Already Do

1. **Run ARRM** to scrape metadata
2. **Import metadata** to RomGroomer database
3. **MD5 hashes** are automatically stored

### ✅ What's Now Available

1. **DAT filter** can use those MD5s
2. **Renamed files** automatically matched
3. **Statistics** show MD5 vs name matches
4. **No extra work** - just enable the feature!

### ✅ When It Helps

1. **ROM distributor renames** (like your PS3 case)
2. **Region tag updates** (USA → USA, Asia)
3. **Title improvements** (Uncharted 2 → Uncharted 2 - Among Thieves)
4. **DAT out of date** (you have newer files than DAT)

### ✅ No Impact When

1. **Name matching works** (most files)
2. **First import** (no renames yet)
3. **MD5s not in database** (graceful fallback)

## Integration Options

### Option 1: Manual Pre-Filter Hook

Add to your build profile:

```python
def populate_md5s_from_metadata(context):
    """Load MD5s from metadata database before DAT filter."""
    from romgroomer.metadata.database import MetadataDatabase
    
    db = MetadataDatabase()
    session = db.get_session()
    
    for file_path in context.source_files:
        game_name = file_path.stem
        game = session.query(ScrapedGame).filter(
            ScrapedGame.system == context.platform_name,
            ScrapedGame.name == game_name
        ).first()
        
        if game and game.md5:
            context.file_md5s[file_path] = game.md5.lower()
    
    session.close()
```

### Option 2: Automatic Platform Config

Add to platform YAML:

```yaml
platform:
  name: ps3
  arrm_system_id: 52
  
  stages:
    - name: filter_dat
      enable_md5_matching: true  # Auto-loads from metadata DB
      
  hooks:
    pre_filter:
      - populate_md5s_from_metadata
```

### Option 3: Build Profile Hook

In your build profile:

```yaml
profiles:
  ps3-usa-1g1r:
    stages:
      - filter_dat:
          hooks:
            before: populate_md5s_from_metadata
```

## Summary

**YES!** Your existing metadata import workflow already primes everything:

1. ✅ **ARRM generates gamelist.xml** → Contains MD5 hashes
2. ✅ **Import to RomGroomer database** → MD5s stored in scraped_games.md5
3. ✅ **Query database before DAT filter** → Load MD5s into context.file_md5s
4. ✅ **Filter stage uses MD5-first matching** → Automatic fallback to names

**No additional scraping needed!** The MD5 hashes are already in your database from your normal workflow. Just add a pre-filter hook to load them into the context, and the enhanced DAT filter will automatically use MD5-first matching.

**For your PS3 case specifically:**
- Those "renamed" files already have MD5s in your database
- Add pre-filter hook to load them
- Filter automatically matches renamed files via MD5
- No more false "missing file" warnings! 🎉
