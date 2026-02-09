# Future Tools Roadmap

This document outlines additional tools needed to complete the ROM grooming toolkit.

## Current Status: 6 Systems Complete ✅

- ✅ Saturn (chdman)
- ✅ PSP (maxcso)
- ✅ Original Xbox (extract-xiso)
- ✅ Xbox 360 (xdvdfs-tools)
- ✅ PS3 (ps3dec + chdman)
- ✅ Wii U (wud-compress)

---

## 🎯 HIGH PRIORITY - Disc-Based Systems

### 1. Xbox 360 Digital Games Tools (XBLA/Arcade/GOD)
**Status**: 🔴 Not Built
**Priority**: ⭐⭐⭐⭐ High (if you have digital Xbox 360 games)
**Tools Needed**: Multiple tools for different formats

**Xbox 360 Digital Game Formats**:

1. **XBLA (Xbox Live Arcade)**
   - Small downloadable games (50MB-2GB)
   - Formats: `.xbla`, extracted folders
   - Examples: Geometry Wars, Castle Crashers, Braid

2. **GOD (Games on Demand)**
   - Full retail games as digital downloads
   - Format: Single `.god` file or folder structure
   - Examples: Full retail games (4-7GB)

3. **DLC (Downloadable Content)**
   - Game add-ons, map packs
   - Formats: Various

4. **XBLIG (Xbox Live Indie Games)**
   - Smaller indie titles
   - Less common format

**Required Tools**:

**a) Xbox 360 Content Extraction/Conversion**
   - **No specific tool needed** - Xenia emulator loads these directly!
   - Files are typically in folder format with these key files:
     - `default.xex` - Main executable
     - Content files in standard structure

**b) xbox360_marketplace_extractor**
   - Repository: Various community tools
   - Purpose: Extract/convert marketplace content
   - Format conversions

**c) XM360 (Xbox Marketplace Tool)**
   - Windows tool (Wine on Linux)
   - Purpose: Manage digital content
   - Download/organize marketplace games

**File Formats You'll See**:
```
XBLA Game Structure:
  game_folder/
    ├── default.xex       (Main executable)
    ├── Content/          (Game assets)
    ├── $(GameMediaID)/   (Title update files)
    └── Headers/          (Metadata)

GOD Format:
  Game.god              (Single file)
  Or extracted folder with same structure as XBLA
```

**Xenia Emulator Support**:
- ✅ Loads `.xex` files directly
- ✅ Loads GOD files
- ✅ Loads XBLA folders
- ✅ No conversion needed!

**Do You Need Special Tools?**

**Short Answer**: Probably NO! 🎉

**If your files are**:
- ✅ **Folders with default.xex** → Load directly in Xenia
- ✅ **GOD files** → Load directly in Xenia
- ✅ **Already extracted** → No tools needed!

**You ONLY need tools if**:
- ❌ Files are encrypted/locked
- ❌ Files are in proprietary format
- ❌ Need to extract from marketplace downloads
- ❌ Need to convert between formats

**Recommendation**:
1. **Try loading directly in Xenia first**
2. If it works → No tools needed!
3. If it fails → Then we'll build extraction tools

**Space Considerations**:
- XBLA games are already small (50MB-2GB)
- GOD files may benefit from 7zip compression for storage
- No special compression format needed

**Transformation Tracking**:
- Track original file hashes
- No format conversion needed (unlike disc ISOs)
- Simpler than disc-based games!

---

### 2. wit/Wiimms ISO Tools (Wii & GameCube)
**Status**: 🔴 Not Built
**Priority**: ⭐⭐⭐⭐⭐ CRITICAL
**Repository**: https://github.com/Wiimm/wiimms-iso-tools

**Formats**:
- ISO → WBFS (Wii Backup File System)
- ISO → WDF (Wiimm's Disc Format)
- ISO → CISO (Compressed ISO)
- ISO → WIA (Wii Image Archive)
- Extract/create GameCube/Wii ISOs

**Why Critical**:
- Wii/GameCube are extremely popular
- Large collections (50-100+ games common)
- ISOs are 1.4-4.7GB each (uncompressed)
- WBFS saves 30-40% space
- RVZ saves 60-70% space (even better!)

**Space Savings**:
- Wii ISO (4.7GB) → WBFS (3.2GB) = 32% saved
- Wii ISO (4.7GB) → RVZ (1.5GB) = 68% saved! 🎯

**Use Cases**:
- Convert ISO to WBFS for Dolphin
- Convert ISO to RVZ for maximum compression
- Scrub unused data from ISOs
- Verify disc integrity

**Build Complexity**: Medium (C, custom Makefile)

---

### 2. dolphin-tool (GameCube/Wii - Modern RVZ Format)
**Status**: 🔴 Not Built
**Priority**: ⭐⭐⭐⭐⭐ CRITICAL
**Repository**: Part of Dolphin Emulator (https://github.com/dolphin-emu/dolphin)

**Formats**:
- ISO → RVZ (best compression!)
- GCM → RVZ
- WBFS → RVZ
- Extract RVZ

**Why Critical**:
- RVZ is the BEST format for GameCube/Wii
- 60-70% compression (better than WBFS!)
- Lossless and fast
- Official Dolphin format
- Future-proof

**Space Savings**:
- GameCube ISO (1.4GB) → RVZ (450MB) = 68% saved!
- Wii ISO (4.7GB) → RVZ (1.5GB) = 68% saved!

**Use Cases**:
- Convert existing ISOs/WBFS to RVZ
- Best format for long-term storage
- Dolphin native support

**Build Complexity**: High (C++, CMake, large project)
**Note**: May need to extract just the tool, not full Dolphin

---

### 3. nkit (GameCube/Wii - Alternative Format)
**Status**: 🔴 Not Built
**Priority**: ⭐⭐⭐ Medium
**Repository**: https://github.com/extremscorner/nkit (community fork)

**Formats**:
- ISO → NKit (recoverable format)
- NKit → ISO
- Works with GameCube/Wii

**Why Useful**:
- Can recover original ISO from NKit
- Includes recovery data
- Smaller than ISO, verifiable

**Space Savings**:
- Similar to WBFS (30-40%)

**Use Cases**:
- Archival format with recovery capability
- Alternative to RVZ

**Build Complexity**: Medium (C#/.NET or native)

---

## 🎮 MEDIUM PRIORITY - Additional Disc Systems

### 4. redumper (Multi-System Disc Dumping)
**Status**: 🔴 Not Built
**Priority**: ⭐⭐⭐⭐ High
**Repository**: https://github.com/superg/redumper

**Formats**:
- Dump PS1/PS2/PSP/Saturn/Dreamcast discs
- Create proper .cue files
- Generate checksums
- Redump-compatible outputs

**Why Important**:
- Create your own verified dumps
- Generate proper cue sheets
- Checksum verification
- Redump database compatible

**Use Cases**:
- Dump your own disc collection
- Verify existing dumps
- Create proper BIN/CUE sets

**Build Complexity**: Medium (C++, CMake)

---

### 5. cdrdao (CD Disc Operations)
**Status**: 🟡 May be available via apt
**Priority**: ⭐⭐⭐ Medium
**Repository**: https://cdrdao.sourceforge.net/

**Formats**:
- Create BIN/TOC files
- Convert TOC to CUE
- CD-ROM operations

**Why Useful**:
- Working with CD-ROM images
- Format conversions
- Disc analysis

**Install**: `sudo apt-get install cdrdao`

---

### 6. binmerge (CUE/BIN Tools)
**Status**: 🔴 Not Built
**Priority**: ⭐⭐ Low
**Repository**: Various implementations

**Formats**:
- Merge multiple BIN files
- Split single BIN files
- Fix CUE sheets

**Why Useful**:
- Clean up messy multi-bin dumps
- Standardize to single BIN format
- Fix broken CUE files

**Build Complexity**: Low (Python/Bash scripts available)

---

## 📦 COMPRESSION & ARCHIVING UTILITIES

### 7. 7zip Command Line (p7zip)
**Status**: 🟡 Should be installed
**Priority**: ⭐⭐⭐⭐ High
**Install**: `sudo apt-get install p7zip-full`

**Why Critical**:
- Extract .7z, .zip, .rar archives
- Compress ROM sets for backup
- Industry standard

**Use Cases**:
- Extract downloaded ROM packs
- Compress processed collections
- Backup ROM sets

---

### 8. unrar
**Status**: 🟡 Check if installed
**Priority**: ⭐⭐⭐ Medium
**Install**: `sudo apt-get install unrar`

**Why Useful**:
- Many ROM sets distributed as .rar
- Extract multi-part archives
- Handle old archive formats

---

### 9. xz-utils
**Status**: 🟡 Check if installed
**Priority**: ⭐⭐ Low
**Install**: `sudo apt-get install xz-utils`

**Why Useful**:
- Extract .xz compressed files
- Some ROM sets use this format

---

## 🔍 HASH & VERIFICATION TOOLS

### 10. rhash (Multi-Hash Calculator)
**Status**: 🔴 Not Built
**Priority**: ⭐⭐⭐⭐ High
**Repository**: https://github.com/rhash/RHash
**Install**: `sudo apt-get install rhash`

**Why Critical**:
- Calculate MD5, SHA1, SHA256, CRC32 in one pass
- Faster than multiple hash tools
- Batch processing support
- SFV file generation

**Use Cases**:
- Generate all hashes at once
- Verify ROM collections
- Create verification files
- Integration with transformation tracking

**Performance**:
- Much faster than running md5sum, sha1sum separately
- Optimized multi-threaded hashing

---

### 11. cfv (Checksum File Verifier)
**Status**: 🔴 Not Built
**Priority**: ⭐⭐⭐ Medium
**Install**: `sudo apt-get install cfv`

**Why Useful**:
- Verify SFV, MD5, CRC files
- Batch verification
- Create verification files

---

## 🎨 METADATA & SCRAPING TOOLS

### 12. ImageMagick (Image Processing)
**Status**: 🟡 Check if installed
**Priority**: ⭐⭐⭐⭐ High
**Install**: `sudo apt-get install imagemagick`

**Why Critical**:
- Resize/convert box art
- Generate thumbnails
- Image format conversions
- Batch processing

**Use Cases**:
- Optimize scraped artwork
- Generate preview images
- Convert formats for EmulationStation

---

### 13. FFmpeg (Video/Audio Processing)
**Status**: 🟡 Check if installed
**Priority**: ⭐⭐⭐ Medium
**Install**: `sudo apt-get install ffmpeg`

**Why Useful**:
- Generate video previews
- Extract audio from games
- Convert video formats
- Create snapshots from video

**Use Cases**:
- Process game trailers
- Create video previews
- Audio format conversions

---

## 🛠️ ROM-SPECIFIC UTILITIES

### 14. nsz (Nintendo Switch Compression)
**Status**: 🔴 Not Built
**Priority**: ⭐⭐⭐⭐ High (if you have Switch games)
**Repository**: https://github.com/nicoboss/nsz

**Formats**:
- NSP → NSZ (compressed)
- XCI → XCZ (compressed)
- Decompress back to original

**Why Important**:
- Switch games are HUGE (5-30GB+)
- 20-30% compression typical
- Lossless compression
- Works with all Switch emulators

**Space Savings**:
- 10GB NSP → 7GB NSZ = 30% saved
- Critical for large Switch collections

**Build Complexity**: Low (Python)

---

### 15. xdelta (ROM Patching)
**Status**: 🟡 Check if installed
**Priority**: ⭐⭐⭐ Medium
**Install**: `sudo apt-get install xdelta3`

**Why Useful**:
- Apply ROM patches
- Create patches
- Translation patches
- Bug fix patches

**Use Cases**:
- Apply fan translations
- Apply game fixes
- Create custom patches

---

### 16. flips (Floating IPS - ROM Patcher)
**Status**: 🔴 Not Built
**Priority**: ⭐⭐ Low
**Repository**: https://github.com/Alcaro/Flips

**Formats**:
- Apply IPS patches
- Apply UPS patches
- Apply BPS patches

**Why Useful**:
- Standard ROM patching tool
- GUI + CLI available
- Multiple patch formats

---

### 17. rom-tools (NES/SNES Header Tools)
**Status**: 🔴 Not Built
**Priority**: ⭐⭐ Low
**Various Tools**:
- `ucon64` - Universal ROM tool
- `nsrt` - SNES ROM Tool
- ROM header fixers

**Why Useful**:
- Fix ROM headers
- Remove copier headers
- Verify ROM format
- Database matching

---

## 🗄️ DATABASE & DAT TOOLS

### 18. clrmamepro (DAT Management)
**Status**: 🔴 Not Available on Linux (Windows only)
**Priority**: ⭐⭐⭐ Medium
**Alternative**: RomVault, DatUtil

**Why Important**:
- Verify ROM sets against DATs
- Rebuild ROM sets
- Fix naming
- Organize collections

**Linux Alternative**: We may need to build our own DAT tools

---

### 19. DatUtil (DAT File Converter)
**Status**: 🔴 Not Built
**Priority**: ⭐⭐⭐ Medium

**Why Useful**:
- Convert between DAT formats
- Merge DAT files
- Split DAT files
- DAT analysis

---

### 20. retool (1G1R Filtering)
**Status**: 🟡 Already using XML output
**Priority**: ⭐⭐⭐⭐ High
**Repository**: https://github.com/unexpectedpanda/retool

**Why Critical**:
- 1G1R (1 Game 1 ROM) filtering
- Region priority
- Clone detection
- Already generating DATs in `dats/` folder!

**Use Cases**:
- Filter ROM collections
- Remove duplicates
- Region preference
- Clone management

**Note**: We already have retool XML outputs in `dats/retool/`!

---

## 🔧 SYSTEM UTILITIES

### 21. parallel (GNU Parallel)
**Status**: 🟡 Check if installed
**Priority**: ⭐⭐⭐⭐ High
**Install**: `sudo apt-get install parallel`

**Why Critical**:
- Parallelize ROM processing
- Batch compression
- Multi-core utilization
- Speed up mass operations

**Use Cases**:
```bash
# Compress 100 ISOs in parallel
ls *.iso | parallel tools/bin/maxcso {}
```

---

### 22. pv (Pipe Viewer)
**Status**: 🟡 Check if installed
**Priority**: ⭐⭐⭐ Medium
**Install**: `sudo apt-get install pv`

**Why Useful**:
- Show progress bars
- Monitor throughput
- Estimate completion time
- Better UX for long operations

---

### 23. jq (JSON Processor)
**Status**: 🟡 Should be installed
**Priority**: ⭐⭐⭐⭐ High
**Install**: `sudo apt-get install jq`

**Why Critical**:
- Process JSON data
- Parse API responses
- Query metadata
- Script automation

**Use Cases**:
- Parse ScreenScraper JSON responses
- Process metadata files
- Data transformation

---

### 24. xmlstarlet (XML Processor)
**Status**: 🟡 Check if installed
**Priority**: ⭐⭐⭐ Medium
**Install**: `sudo apt-get install xmlstarlet`

**Why Useful**:
- Process XML files
- Parse gamelist.xml
- Query DAT files
- XML transformations

---

## 🐍 PYTHON LIBRARIES (Already in requirements.txt?)

### 25. Additional Python Dependencies
**Priority**: ⭐⭐⭐⭐ High

Check if needed:
```python
# Hashing
hashlib          # Built-in ✅
xxhash           # Fast hashing
crcmod           # CRC calculations

# Image processing
Pillow           # Image manipulation
wand             # ImageMagick wrapper

# Archive handling
py7zr            # 7zip support
rarfile          # RAR support

# Disc format handling
pycdio           # CD-ROM library
iso9660          # ISO filesystem

# Database
sqlalchemy       # Already have ✅
alembic          # Database migrations

# API/Web
requests         # HTTP client ✅
aiohttp          # Async HTTP
beautifulsoup4   # HTML parsing

# CLI
rich             # Beautiful terminal output
click            # CLI framework ✅
tqdm             # Progress bars

# Data processing
pandas           # Data analysis (if needed)
lxml             # XML processing
```

---

## 📊 PRIORITY SUMMARY

### IMMEDIATE (Build These Next):
1. ⭐⭐⭐⭐⭐ **wit/Wiimms** - Wii/GameCube (critical!)
2. ⭐⭐⭐⭐⭐ **dolphin-tool** - RVZ format (best compression!)
3. ⭐⭐⭐⭐ **rhash** - Multi-hash calculator
4. ⭐⭐⭐⭐ **nsz** - Switch compression (if you have Switch games)

### HIGH PRIORITY:
5. ⭐⭐⭐⭐ **redumper** - Disc dumping/verification
6. ⭐⭐⭐⭐ **ImageMagick** - Image processing
7. ⭐⭐⭐⭐ **GNU Parallel** - Batch processing

### MEDIUM PRIORITY:
8. ⭐⭐⭐ **nkit** - Alternative GC/Wii format
9. ⭐⭐⭐ **cfv** - Checksum verification
10. ⭐⭐⭐ **xdelta3** - ROM patching

### LOW PRIORITY:
11. ⭐⭐ **flips** - IPS patching
12. ⭐⭐ **rom-tools** - Header utilities
13. ⭐⭐ **binmerge** - BIN/CUE tools

---

## 🎯 RECOMMENDED BUILD ORDER

### Phase 1: Complete Disc-Based Systems ✅
- ✅ Saturn (chdman)
- ✅ PSP (maxcso)
- ✅ Xbox (extract-xiso)
- ✅ Xbox 360 (xdvdfs-tools)
- ✅ PS3 (ps3dec + chdman)
- ✅ Wii U (wud-compress)

### Phase 2: Wii/GameCube Support ⏭️ NEXT!
- 🔴 Build wit/Wiimms ISO Tools
- 🔴 Build dolphin-tool (or extract from Dolphin)
- 🔴 Test with sample Wii/GameCube ISOs

### Phase 3: Hash & Verification Tools
- 🔴 Install/build rhash
- 🔴 Integrate with transformation tracking
- 🔴 Batch hashing scripts

### Phase 4: Switch Support (Optional)
- 🔴 Build nsz (if you have Switch collection)
- 🔴 Test NSP → NSZ compression

### Phase 5: Additional Utilities
- 🔴 Install system utilities (parallel, pv, jq)
- 🔴 Set up image processing (ImageMagick)
- 🔴 Add Python libraries as needed

### Phase 6: Advanced Features
- 🔴 ROM patching tools (xdelta, flips)
- 🔴 DAT management tools
- 🔴 Dumping tools (redumper)

---

## 💾 EXPECTED SPACE SAVINGS WITH ALL TOOLS

### Complete Collection Example (All Systems):

| System | Games | Uncompressed | Compressed | Saved | % |
|--------|-------|--------------|------------|-------|---|
| Saturn | 20 | 13GB | 3.6GB | 9.4GB | 72% |
| PSP | 50 | 60GB | 26GB | 34GB | 57% |
| Xbox | 10 | 40GB | 40GB | 0GB | 0% |
| Xbox 360 | 10 | 70GB | 35GB | 35GB | 50% |
| PS3 | 10 | 200GB | 100GB | 100GB | 50% |
| Wii U | 10 | 160GB | 104GB | 56GB | 35% |
| **Wii** | **50** | **235GB** | **75GB** | **160GB** | **68%** |
| **GameCube** | **50** | **70GB** | **22GB** | **48GB** | **69%** |
| Switch | 20 | 300GB | 210GB | 90GB | 30% |

**TOTAL**: 1,148GB → 615GB  
**TOTAL SAVED**: 533GB (46% overall)

**With Wii/GameCube (RVZ)**: Saves an additional **208GB**! 🎯

---

## 🚀 QUICK INSTALL CHECKLIST

### System Utilities (Check & Install):
```bash
# Check what's installed
which 7z p7zip unrar xz rhash cfv parallel pv jq xmlstarlet convert ffmpeg

# Install missing tools
sudo apt-get update
sudo apt-get install -y \
    p7zip-full \
    unrar \
    xz-utils \
    rhash \
    cfv \
    parallel \
    pv \
    jq \
    xmlstarlet \
    imagemagick \
    ffmpeg \
    xdelta3 \
    cdrdao
```

### Python Libraries (Check & Install):
```bash
# Check current environment
pip list | grep -E 'xxhash|Pillow|py7zr|rarfile|aiohttp|beautifulsoup4|rich|tqdm|lxml'

# Install if needed
pip install xxhash Pillow py7zr rarfile aiohttp beautifulsoup4 rich tqdm lxml
```

---

## 📝 NOTES

### Build Complexity Legend:
- **Low**: Simple compile, few dependencies
- **Medium**: Standard build process, some deps
- **High**: Complex build, many dependencies, or large project

### Priority Legend:
- ⭐⭐⭐⭐⭐ **CRITICAL**: Must have, widely used
- ⭐⭐⭐⭐ **HIGH**: Very useful, common scenarios
- ⭐⭐⭐ **MEDIUM**: Nice to have, specific use cases
- ⭐⭐ **LOW**: Optional, niche scenarios

### Status Legend:
- ✅ **Complete**: Built and ready
- 🟡 **Available**: May be installed via package manager
- 🔴 **Not Built**: Needs to be built/installed

---

## 🎯 NEXT SESSION RECOMMENDATION

**Build wit/Wiimms ISO Tools and dolphin-tool next!**

Wii and GameCube are:
- Extremely popular platforms
- Large collections common (50-100+ games)
- RVZ format saves 60-70% space (HUGE savings!)
- Essential for complete disc toolkit

**Expected impact**: Save ~200GB on typical Wii/GameCube collection! 💰

---

This roadmap will be updated as tools are built and priorities change.
