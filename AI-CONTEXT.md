# AI Context Guide for ROM Groomer Python

**Last Updated:** October 26, 2025  
**Purpose:** Guide future AI assistants working on this project

---

## Project Overview

**ROM Groomer Python** is a comprehensive ROM collection management system that:
- Matches ROMs against DAT files (No-Intro, Redump)
- Applies filters (1G1R - One Game One Region)
- Transforms formats (ZIP → CHD compression for disc images)
- Generates M3U playlists for multi-disc games
- Scrapes and generates metadata (gamelist.xml + media) for EmulationStation/Batocera
- Manages curated collections with delete/keep lists

**⚠️ IMPORTANT:** This project has extensive functionality already implemented. Before proposing to build a feature, check if it already exists!

---

## Key Project Locations

### Entry Points
- **CLI:** `python3 -m romgroomer` - Main command interface
- **Main Module:** `src/romgroomer/__main__.py` - CLI entry point
- **Build System:** `src/romgroomer/commands/build.py` - Orchestrates full builds

### Core Components

#### 1. **Build Pipeline** (`src/romgroomer/stages/`)
The build system runs 7 sequential stages:
1. `match.py` - Match source files to DAT files
2. `delete.py` - Apply delete lists (curated exclusions)
3. `transform.py` - Convert formats (e.g., BIN/CUE → CUE only)
4. `compress.py` - CHD compression for disc images
5. `m3u.py` - Generate M3U playlists for multi-disc games
6. `copy.py` - Copy files to output directory
7. `metadata.py` - Generate gamelist.xml and scrape media

**Each stage is self-contained and can be skipped if not needed.**

#### 2. **Metadata System** (`src/romgroomer/metadata/`)
- `scraper.py` - Scrapes from ScreenScraper.fr API
- `generator.py` - Generates gamelist.xml from database
- `database.py` - SQLAlchemy models for metadata storage
- Database location: `metadata/database/romgroomer.db`

#### 3. **Configuration** (`config/`)
- `builds/*.yaml` - Build configurations per platform/target
- `platforms/*.yaml` - Platform-specific settings (DAT sources, compression, targets)

#### 4. **Lists** (`/data/emu/lists/`)
- `{platform}-delete` - Games to exclude from builds
- `{platform}-keep` - Games to always include (overrides filters)

---

## Critical Design Decisions

### Output Folder Naming Convention

**Format:** `{platform}-{source}-{filter}-{format}-{target}`

**Example:** `saturn-redump-1g1r-eng-chd-batocera`

**Components:**
- `platform`: System name (saturn, psx, nes, etc.)
- `source`: DAT source (redump, nointro)
- `filter`: Selection filter (1g1r-eng, 1g1r-usa, all)
- `format`: File format (chd, zip, 7z)
- `target`: Destination system (batocera, rocknix, arrm)

**Rationale:**
- **Descriptive:** Folder name tells you exactly what's inside
- **Consistent:** Same pattern across all platforms
- **No redundancy:** CHD is always level 9 (max compression), so no need for "chd9"
- **Professional:** Clear for humans and future AI

**Examples:**
```
saturn-redump-1g1r-eng-chd-batocera/
psx-redump-1g1r-usa-chd-batocera/
nes-nointro-1g1r-usa-batocera/
```

### Compression Settings

**All CHD compression uses:**
- Level: 9 (maximum)
- Codec: lzma (best compression)

This is the standard, not configurable per-build. No need to specify "level 9" in folder names.

### DAT Variants

**1G1R (One Game One Region) Filters:**
- `1g1r-usa`: USA releases only (~280 games for Saturn)
- `1g1r-eng`: English language releases from any region - USA + Europe + Australia + Japanese games with English support (~318 games for Saturn)
- `1g1r-all`: All languages, one per region

**Current Saturn uses:** `1g1r-eng` for broader English coverage

---

## Common Workflows

### Running a Full Build
```bash
cd /data/emu/rom-groomer-python
python3 -m romgroomer build config/builds/saturn-full-eng.yaml
```

### Regenerating Metadata Only
```bash
python3 -m romgroomer metadata generate /data/emu/output/saturn /data/emu/output/saturn
```

### Scraping Metadata to Database
```bash
python3 -m romgroomer metadata scrape --platform saturn --dat-file /path/to/saturn.dat
```

---

## Important Implementation Notes

### M3U Playlist Generation

**Location:** `src/romgroomer/stages/m3u.py`

**Disc Pattern Matching:**
```python
# Updated regex handles revision tags like (R), (Rev 1), etc.
self.disc_pattern = re.compile(r'\(Disc (\d+)\)(?:\s*\([^)]+\))?', re.IGNORECASE)
```

**Examples matched:**
- `Game (USA) (Disc 1).chd` → Base: `Game (USA)`
- `Game (USA) (Disc 1) (R).chd` → Base: `Game (USA)` ✅ Fixed Oct 26, 2025
- `Game (USA) (Disc 2).chd` → Base: `Game (USA)`

Both discs grouped into single M3U.

### Metadata Format (ARRM Standard)

**Location:** `src/romgroomer/metadata/generator.py`

**Field Order (critical for ARRM compatibility):**
```xml
<game>
  <path>./file.chd</path>
  <name>Game Name</name>
  <sortname>0001 =- Game Name</sortname>
  <desc>Description</desc>
  <rating>0.8</rating>
  <releasedate>19951231T000000</releasedate>
  <developer>Developer</developer>
  <publisher>Publisher</publisher>
  <genre>Genre</genre>
  <genreid>123</genreid>
  <players>1-2</players>
  <md5>hash</md5>
  <region>us</region>
  <lang>en</lang>
  <!-- Media elements in ARRM order -->
  <image>./media/image/Game-image.png</image>
  <wheel>./media/wheel/Game-wheel.png</wheel>
  <boxart>./media/boxart/Game-boxart.png</boxart>
  <screenshot>./media/screenshot/Game-screenshot.jpg</screenshot>
  <cartridge>./media/cartridge/Game-cartridge.png</cartridge>
  <mix>./media/mix/Game-mix.png</mix>
  <marquee>./media/marquee/Game-marquee.png</marquee>
  <video>./media/video/Game-video.mp4</video>
  <manual>./media/manual/Game-manual.pdf</manual>
</game>
```

**Key points:**
- Media paths use singular folders: `image/` not `images/`
- Media filenames include type suffix: `Game-image.png` not `Game.png`
- ARRM media order is fixed (not alphabetical)

### M3U Metadata Matching

**Location:** `src/romgroomer/metadata/generator.py:264-311`

M3U playlists inherit metadata from first disc:
1. Read .m3u file contents
2. Extract first disc filename
3. Calculate MD5 hash of first disc .cue file
4. Query database for metadata by hash
5. Create game entry with .m3u as path

---

## Future Features (Planned, Not Implemented)

### Phase 2: Budget-Based Collection Curation

**Concept:** Generate "best-of" collections within size constraints using ScreenScraper ratings.

**Example Use Case:**
```yaml
# config/devices/rocknix-rg406v-512gb.yaml
device: RG406V
storage: 512GB
usable: 470GB

platforms:
  complete_sets:  # Small systems - include everything
    - nes
    - snes
    
  best_of:  # Large systems - curated by rating
    psp: 60GB      # Top ~120 PSP games
    psx: 50GB      # Top ~80 PS1 games
    saturn: 25GB   # Top ~98 Saturn games
```

**Implementation Notes:**
- Use rating field from metadata (0.0-1.0 scale)
- Sort games by rating (descending)
- Pack games into budget (knapsack algorithm)
- Copy selected ROMs + metadata + media

### Phase 3: Media Optimization Profiles

**Concept:** Transform media to device-appropriate sizes/quality.

**Example:**
```yaml
# config/media-profiles/rocknix-handheld.yaml
profile: rocknix-handheld
video:
  max_width: 640
  max_height: 480
  bitrate: 1000k
  codec: h264
image:
  max_width: 640
  quality: 85
  format: jpg
```

**Strategy:**
- Archive tier: Full quality from ScreenScraper (master copy)
- Desktop tier: High quality for TV/monitors (1080p)
- Handheld tier: Optimized for small screens (480p, ~75% size reduction)

**Tools needed:** imagemagick, ffmpeg, optipng

---

## Common Pitfalls for AI Assistants

1. **Don't reinvent existing features** - Check `python3 -m romgroomer --help` first
2. **Metadata generation is separate from builds** - Stage 7 generates metadata during full builds, but can also run standalone
3. **Delete lists use source format** - `saturn-delete` lists `.zip` files (pre-compression), not `.chd` files
4. **M3U creation happens during builds** - Not during metadata-only regeneration (Stage 5 of full pipeline)
5. **Database is the source of truth** - Metadata comes from `romgroomer.db`, not scraped live each time
6. **1G1R filters are pre-applied in DATs** - Retool already filtered to one game per region before we process

---

## Getting Help

**Check these in order:**
1. `python3 -m romgroomer --help` - See all commands
2. `python3 -m romgroomer [command] --help` - Command-specific help
3. `config/builds/*.yaml` - Example build configurations
4. `src/romgroomer/stages/` - Understand the pipeline
5. This document - Design decisions and context

---

## Questions to Ask Before Building Features

1. **Does this feature already exist?** Check CLI commands first
2. **Which stage does this belong in?** Don't add to wrong part of pipeline
3. **Is this needed now or later?** Focus on current goals (e.g., Saturn production-ready)
4. **Does this fit the architecture?** Follow existing patterns

---

*This document should be updated when major design decisions are made.*
