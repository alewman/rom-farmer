# PS3 Disc DLC Integration - Research Summary

## Background
We are building a tool to create complete PS3 game packages that include base game + official updates + DLC in a single JB (jailbreak) folder format. The goal is to have fully updated games ready to play on either real PS3 hardware or RPCS3 emulator.

## What We've Successfully Built

### Game Structure
```
Borderlands 2 (USA) (En,Fr,De,Es,It)_COMPLETE.ps3/
├── PS3_DISC.SFB           # Disc metadata
├── PS3_GAME/
│   ├── PARAM.SFO          # APP_VER = 01.15 (updated)
│   ├── ICON0.PNG
│   ├── PS3LOGO.DAT
│   └── USRDIR/
│       ├── EBOOT.BIN      # v01.15 executable
│       └── DLC/           # 18 DLC packages (3.7GB)
│           ├── ORCHID/    # Captain Scarlett DLC
│           ├── IRIS/      # Mr. Torgue's Campaign
│           ├── SAGE/      # Sir Hammerlock's DLC
│           ├── ASTER/     # Tiny Tina's Assault
│           └── [14 other DLC folders]
└── PS3_UPDATE/            # (may be present)
```

### Build Process
1. **Source**: Base game disc image (.ps3 folder format)
2. **Updates**: Official Sony PSN update PKG (v01.15, 649MB)
3. **DLC**: 4 major DLC packages from NoPayStation database (3.7GB total)
4. **Method**: 
   - Extract PKG files (decrypt using AES-128-ECB with PS3 key)
   - Merge PKG contents into PS3_GAME/ directory
   - Apply DLC first, then updates last (preserves APP_VER in PARAM.SFO)

### Test Results

#### Real PS3 Hardware (Previous Test)
- **Test Build**: `_DLC_TEST.ps3` (without update, only DLC)
- **DLC Location**: `PS3_GAME/USRDIR/DLC/`
- **Result**: ✅ **3 out of 4 DLC packages worked**
- **Conclusion**: Real PS3 successfully reads DLC from disc structure

#### RPCS3 Emulator (Current Test)
- **Test Build**: `_COMPLETE.ps3` (with v01.15 update + DLC)
- **DLC Location**: `PS3_GAME/USRDIR/DLC/` (same as real PS3 test)
- **Boot**: ✅ Game loads, shows v01.15
- **File Size**: Built 9.1GB (5GB base + 649MB update + 3.7GB DLC)
- **RPCS3 Reports**: ❌ Only 5GB (DLC not recognized)
- **Conclusion**: RPCS3 may not load DLC from disc-based .ps3 folders

## Questions for Research

### 1. PS3_GAME/USRDIR/DLC/ Directory
**Question**: Is `PS3_GAME/USRDIR/DLC/` the correct location for DLC content in PS3 disc images?

**What we know**:
- Real PS3 hardware successfully read 3/4 DLC from this location
- Standard PS3 disc format has this structure
- Each DLC package is a subdirectory (e.g., ORCHID/, IRIS/, SAGE/, ASTER/)
- DLC folders contain game assets (PAK files, etc.)

**What we don't know**:
- Why 1 out of 4 DLC didn't work on real PS3
- If there's additional metadata/files required
- If DLC packages need specific ordering or initialization files

### 2. RPCS3 DLC Architecture
**Question**: How does RPCS3 handle DLC for disc-based games (.ps3 folders)?

**What we know**:
- RPCS3 boots the disc image successfully
- Game shows correct version (v01.15)
- RPCS3 reports 5GB size (ignoring DLC)
- Real PS3 reads same DLC structure successfully

**What we don't know**:
- Does RPCS3 support disc-based DLC at all?
- Should DLC be in `dev_hdd0/game/{TITLE_ID}/` instead?
- Do we need to install DLC via PKG files separately?
- Is there RPCS3 configuration to enable disc DLC?

### 3. PKG Integration Method
**Question**: What is the correct method to integrate DLC PKG files into a disc image?

**Our current approach**:
```python
1. Decrypt PKG file (extract to temp directory)
2. Copy PKG contents to PS3_GAME/USRDIR/DLC/{DLC_NAME}/
3. Each DLC gets its own subdirectory
4. No merging - each DLC is isolated
```

**Questions**:
- Should DLC files be merged into the game's USRDIR instead?
- Are there PKG metadata files (like PARAM.SFO) that should be processed?
- Do DLC packages need activation/license files?
- Should DLC be applied differently than updates?

### 4. Update vs DLC Application Order
**Question**: Does the order of applying updates and DLC matter?

**Our findings**:
- Each PKG (update or DLC) contains a PARAM.SFO file
- DLC PARAM.SFO files don't have APP_VER field
- Update PARAM.SFO has APP_VER = 01.15
- **Solution**: Apply DLC first, updates last (preserves version)

**Questions**:
- Is this the correct approach?
- Do some games require updates before DLC?
- Are there dependencies between DLC packages?

### 5. File Structure Differences
**Question**: Real PS3 vs RPCS3 - what are the structural differences?

**Observations**:
- Both use same .ps3 folder format
- Real PS3 reads DLC from disc successfully
- RPCS3 appears to ignore disc-based DLC
- RPCS3 may expect HDD installation format

**Questions**:
- Does RPCS3 need a different folder structure?
- Should we build separate formats for real PS3 vs RPCS3?
- Is there a hybrid approach that works for both?

## Technical Details

### PKG Decryption
```python
# PS3 PKG uses AES-128-ECB encryption
PS3_KEY = bytes([0x2E, 0x7B, 0x71, 0xD7, 0xC9, 0xC9, 0xA1, 0x4E,
                 0xA3, 0x22, 0x1F, 0x18, 0x88, 0x28, 0xB8, 0xF8])

# PKG file key at offset 0x70 is encrypted with PS3_KEY
# Decryption generates file-specific XOR keys
```

### DLC Package Names (Borderlands 2)
- **ORCHID**: Captain Scarlett and Her Pirate's Booty
- **IRIS**: Mr. Torgue's Campaign of Carnage
- **SAGE**: Sir Hammerlock's Big Game Hunt
- **ASTER**: Tiny Tina's Assault on Dragon Keep
- Plus 14 smaller DLC (character skins, level packs, etc.)

### PARAM.SFO Fields
```
TITLE_ID:        BLUS30982 (Borderlands 2 USA)
APP_VER:         01.15 (after update)
CATEGORY:        GD (Disc Game)
PS3_SYSTEM_VER:  04.2000
```

## ✅ RESEARCH RESULTS - CONFIRMED

1. **DLC Directory Structure**: ✅ PS3_GAME/USRDIR/DLC/{DLC_NAME}/ is CORRECT for real PS3
   - Real PS3 successfully loads DLC from disc structure
   - Each DLC in isolated subdirectory works properly

2. **RPCS3 DLC Support**: ❌ RPCS3 does NOT support disc-based DLC
   - RPCS3 ignores PS3_GAME/USRDIR/DLC/ entirely
   - Solution: Manual PKG installation required
   - DLC must be installed to dev_hdd0/game/{TITLE_ID}/

3. **Real PS3 DLC**: ✅ Works correctly (3/4 working was test build issue, not structural)
   - Full HYBRID build with all DLC works on real PS3
   - Major campaign DLC loads from disc automatically

4. **PKG Metadata**: ✅ RAP files are REQUIRED for DLC activation
   - RAP = 16-byte license key stored as hex in NoPayStation database
   - RAP files must be in dev_hdd0/exdata/ (real PS3) or installed via RPCS3
   - Without RAP, PKG installs but doesn't activate

5. **License/Activation**: ✅ RAP files confirmed essential
   - Database RAP field contains hex string (not URL)
   - Convert hex to bytes: `bytes.fromhex(rap_hash)`
   - RAP filename: {CONTENT_ID}.rap

6. **File Merging**: ✅ Isolated DLC folders work correctly
   - No need to merge DLC into main USRDIR
   - Each DLC in separate folder is proper PS3 format

## 🎯 FINAL SOLUTION - HYBRID BUILD

After testing, the optimal solution is a **HYBRID** build that supports both platforms:

### Structure
```
Game_HYBRID.ps3/
├── PS3_GAME/USRDIR/DLC/    # Major campaigns extracted (for real PS3)
├── _PKG/                    # ALL DLC PKG files (for RPCS3 + optional for PS3)
│   ├── *.pkg                # 23 DLC PKGs with user-friendly names
│   └── RAPS/                # 23 RAP license files
└── README.txt               # Complete usage guide
```

### Why This Works
- **Real PS3**: Loads major campaigns from disc automatically, can optionally install other DLC from _PKG/
- **RPCS3**: Ignores disc DLC, users manually install desired PKGs from _PKG/ folder
- **Universal**: Single build works on both platforms
- **User-Friendly**: PKG files have descriptive names, README explains everything

### Build Features
✓ All 23 DLC PKGs included with readable names  
✓ All 23 RAP license files for activation  
✓ Major campaigns extracted to disc (save space, auto-load on PS3)  
✓ README.txt with platform-specific instructions  
✓ Single self-contained 14.43GB folder  
✓ Works on both real PS3 and RPCS3  

### Key Learnings
- Real PS3 and RPCS3 have fundamentally different DLC architectures
- HYBRID approach provides best user experience for both platforms
- Descriptive PKG filenames are crucial for user experience
- Comprehensive README eliminates user confusion
- RAP files are mandatory for DLC activation

## Tools Used
- **PKG Decrypter**: Python port of Mathieulh's PS3 PKG decrypter
- **PARAM.SFO Parser**: Custom Python parser for PS3 metadata
- **NoPayStation**: DLC/update database
- **Sony PSN API**: Official update downloads

## Request for Research
Please search for:
1. Official PS3 disc format specifications (DLC structure)
2. RPCS3 documentation on DLC handling (disc vs HDD)
3. PS3 homebrew/development documentation on DLC integration
4. Known issues with RPCS3 disc-based DLC
5. Comparison of real PS3 vs RPCS3 DLC loading mechanisms
6. PKG file structure and metadata requirements for DLC
7. Any tools/methods used by the scene for creating complete PS3 disc images

## Success Criteria
- DLC works on real PS3 hardware (already achieved 3/4)
- DLC works on RPCS3 emulator (currently failing)
- Single self-contained folder with game + update + DLC
- Reproducible build process for other PS3 games
