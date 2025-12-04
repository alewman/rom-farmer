# Complex Systems Analysis

**Date:** October 13, 2025  
**Status:** Research Phase - Understanding Real-World File Formats

This document analyzes the complex transformation requirements for modern disc-based and digital distribution systems, based on actual Myrient archive inspection.

---

## Overview

While No-Intro systems (NES, SNES, Genesis, etc.) are straightforward ZIP→ROM extractions, modern systems require multi-step transformations with:
- **Decryption** (encrypted disc images)
- **Format conversion** (proprietary formats → emulator-friendly formats)
- **Multiple output options** depending on target device capabilities
- **Decryption keys** that must be managed separately
- **Digital downloads** (eShop, PSN, WiiWare) in addition to disc dumps

---

## Myrient Archive Structure - Findings

### Nintendo Wii (Redump)

**Source Directory:** `Redump/Nintendo - Wii - NKit RVZ [zstd-19-128k]`

**Format Discovery:**
```
Archive: *.zip (TorrentZipped)
  └─ *.rvz (RVZ compressed format - NKit processed)
```

**Example:**
- `$1,000,000 Pyramid, The (USA).zip` (294 MB)
  - Contains: `$1,000,000 Pyramid, The (USA).rvz` (310 MB uncompressed)

**Key Insights:**
- ✅ **Already compressed!** RVZ is Dolphin's native compressed format (zstd compression)
- ✅ **NKit processed** - cleaned/verified Wii dumps
- ❓ **Do we need to transform?** RVZ is already optimal for Dolphin
- 🤔 **Question:** Do targets support RVZ directly, or do we need ISO/WBFS?

**Potential Transforms:**
1. **RocknIX/Batocera (Dolphin):** Unzip → Keep RVZ ✅ (native support)
2. **Real Wii (USB Loader GX):** Unzip → RVZ → ISO → WBFS? (if needed)
3. **Real Wii (WiiFlow):** Unzip → RVZ → ISO? (if needed)

---

### Nintendo Wii U (Redump)

**Source Directory:** `Redump/Nintendo - Wii U - WUX`

**Format Discovery:**
```
Archive: *.zip (TorrentZipped)
  └─ *.wux (WUX compressed format - encrypted)
```

**Decryption Keys Directory:** `Redump/Nintendo - Wii U - Disc Keys`
```
Archive: *.zip (TorrentZipped)
  └─ *.key (16-byte disc key)
```

**Example:**
- `007 Legends (USA) (En,Fr).zip` (9.0 GB WUX file)
- `007 Legends (USA) (En,Fr).zip` (196 bytes key file)

**Key Insights:**
- 🔐 **Encrypted discs** - Need disc-specific keys
- 🗜️ **WUX format** - Compressed WUD (Wii U disc image)
- 🔑 **Keys stored separately** - Must match game to key file
- ⚠️ **Large files** - 9-15 GB per game (even compressed)

**Potential Transforms:**
1. **Cemu (PC emulator):**
   - Unzip WUX
   - Decompress: WUX → WUD (full disc image, ~23 GB)
   - Decrypt: WUD + key → decrypted WUD
   - Option A: Keep as WUD
   - Option B: Extract: WUD → folder structure (loadiine format)
   - Option C: Convert: folder → RPX (executable format)

2. **Real Wii U (loadiine/Haxchi):**
   - Unzip WUX
   - WUX → WUD → decrypt → folder structure

**Required Tools:**
- `wud-compress` (WUX ↔ WUD conversion) ✅ Already have in `tools/wud-compress/`
- `cdecrypt` or `CDecrypt_v2.0b` (decryption with keys)
- Key files from separate directory

**Challenges:**
- ❓ **Key management:** How to pair game ZIPs with key ZIPs?
- ❓ **Common keys:** Do we need `common.key`, `game.key` files in a known location?
- ❓ **Title keys vs disc keys:** Different encryption layers?
- ⚠️ **Storage:** Intermediate WUD files are ~23 GB each!

---

### Nintendo GameCube (Redump)

**Source Directory:** `Redump/Nintendo - GameCube - NKit RVZ [zstd-19-128k]`

**Format:** Same as Wii - RVZ compressed ISOs

**Key Insights:**
- ✅ **Same as Wii** - RVZ format, NKit processed
- ✅ **Dolphin native** - No transform needed for emulation
- ❓ **Real hardware:** Do we need ISO/GCM for GameCube loaders?

---

### Sony PlayStation 3 (Redump)

**Source Directory:** `Redump/Sony - PlayStation 3`

**Format Discovery:**
```
Archive: *.zip (TorrentZipped)
  └─ *.iso (encrypted PS3 disc image)
```

**Decryption Keys Directory:** `Redump/Sony - PlayStation 3 - Disc Keys`
```
Archive: *.zip (various formats)
  └─ *.dkey or *.txt (disc decryption keys)
```

**Also Available:** `Sony - PlayStation 3 - Disc Keys TXT` (text format keys)

**Example:**
- `007 - Blood Stone (USA) (En,Fr).zip` (6.3 GB)
  - Contains: `007 - Blood Stone (USA) (En,Fr).iso` (6.7 GB uncompressed)

**Key Insights:**
- 🔐 **Encrypted ISOs** - Need IRD files or disc keys
- 📦 **Large files** - 5-50 GB per game
- 🎮 **Multiple targets possible:**
  - Real PS3 (CFW) - Various formats
  - RPCS3 emulator (PC) - Folder or PKG format

**Potential Transforms:**

1. **RPCS3 Emulator:**
   - Unzip ISO
   - Decrypt: ISO + keys → decrypted ISO
   - Extract: ISO → folder structure (PARAM.SFO, EBOOT.BIN, etc.)
   - **Final:** `/PS3_GAME/` folder ✅

2. **Real PS3 (CFW - Folder Format):**
   - Same as RPCS3
   - Copy folder to `/dev_hdd0/GAMES/GAMEID/`
   - **Final:** Folder format (JB folders) ✅

3. **Real PS3 (CFW - ISO Format):**
   - Unzip ISO
   - Decrypt: ISO → decrypted ISO
   - **Final:** `.iso` file ✅

4. **Real PS3 (CFW - PKG Format):**
   - Unzip ISO
   - Decrypt: ISO → folder
   - Repackage: folder → `.pkg` (signed package)
   - **Final:** `.pkg` file ❓

**Required Tools:**
- `ps3dec` ✅ Already have in `tools/ps3dec/`
- IRD files (disc decryption data) - Do we have these?
- Keys from separate directory
- `make_self_npdrm` or similar for PKG creation?

**Challenges:**
- ❓ **IRD files:** Where are they? Do we need them in addition to keys?
- ❓ **Target-specific outputs:** 
  - RPCS3: Stop at folder structure
  - Real PS3: Which format? (folder vs ISO vs PKG)
- ❓ **Compression:** Can we compress final output? (e.g., `.iso.gz` or squashfs?)
- ⚠️ **Storage:** Games are 5-50 GB, intermediates double that!

---

## Digital Distribution Systems

### Nintendo eShop / WiiWare / Virtual Console

**Status:** Need to investigate

**Potential Sources:**
- Archive.org collections?
- NUSDownloader dumps?
- 3DS/Wii U CIA/WAD files?

**Questions:**
- ❓ Do we have these in the archive?
- ❓ What formats: WAD (Wii), CIA (3DS), NSP (Switch)?
- ❓ Do they need decryption?
- ❓ How to match to DAT files?

### PlayStation Network (PSN)

**Status:** Need to investigate

**Potential Formats:**
- `.pkg` files (signed packages)
- Rap files (license keys)

**Questions:**
- ❓ Do we have PSN content?
- ❓ PKG → folder extraction?
- ❓ License handling for PSN content?

---

## Key Management Strategy

### Challenge

Multiple systems require disc-specific decryption keys stored separately:
- **Wii U:** 16-byte `.key` files (one per disc)
- **PS3:** `.dkey` or `.txt` files with disc keys/IRD data

### Proposed Solution

```python
@dataclass
class KeyLocation:
    """Decryption key location for a system."""
    
    keys_directory: Path
    """Directory containing key files"""
    
    key_extension: str
    """File extension for keys (.key, .dkey, .txt)"""
    
    key_format: str
    """Format: 'binary', 'text', 'ird'"""
    
    common_keys_file: Optional[Path] = None
    """Common keys file if needed (Wii U common.key)"""
```

**Config Integration:**
```yaml
# Wii U config
platform:
  name: "wiiu"
  decryption:
    enabled: true
    disc_keys: "/data/emu/dats/wiiu-disc-keys/"
    common_keys: "/data/emu/keys/wiiu-common.key"
    key_format: "binary"
    
# PS3 config  
platform:
  name: "ps3"
  decryption:
    enabled: true
    disc_keys: "/data/emu/dats/ps3-disc-keys/"
    ird_directory: "/data/emu/dats/ps3-ird/"  # If needed
    key_format: "text"
```

**Key Matching Algorithm:**
1. Parse game filename: `007 Legends (USA) (En,Fr).zip`
2. Look for matching key file: `007 Legends (USA) (En,Fr).key`
3. If not found, try variations (remove region, remove revision, etc.)
4. If still not found, log warning and skip decryption

---

## Target-Specific Output Options

### Challenge

Different targets support different formats:
- **RPCS3:** Wants folder structure (`/PS3_GAME/`)
- **Real PS3 (Multiman):** Wants folder or ISO
- **Real PS3 (WebMan):** Wants ISO.gz (compressed)
- **Real PS3 (pkg installer):** Wants `.pkg` files

### Proposed Solution

**Target Configuration:**
```yaml
# RocknIX target - emulation focused
targets:
  - name: "rocknix"
    systems:
      ps3:
        format: "folder"  # Extract to folder
        compress: false
        
      wiiu:
        format: "wux"  # Keep compressed
        decrypt: true
        
      wii:
        format: "rvz"  # Keep RVZ (native Dolphin)

# Real Hardware target - CFW PS3
targets:
  - name: "ps3-cfw-multiman"
    systems:
      ps3:
        format: "iso"  # Decrypted ISO
        compress: false
        
  - name: "ps3-cfw-webman"
    systems:
      ps3:
        format: "iso"  # Decrypted ISO
        compress: "gzip"  # .iso.gz
        
  - name: "ps3-cfw-folder"
    systems:
      ps3:
        format: "folder"  # JB folder format
        compress: false
```

**Stage Implementation:**
```python
class TransformPS3Stage(Stage):
    """Transform PS3 ISOs based on target requirements."""
    
    def _get_target_format(self, context: StageContext) -> str:
        """Get desired output format from target config."""
        return context.platform_config.get_target_format(context.target_name)
    
    def _transform_ps3_game(
        self,
        source_zip: Path,
        target_format: str,
        keys_dir: Path,
        temp_dir: Path,
    ) -> FileTransformation:
        """Transform PS3 game through all required steps.
        
        Steps vary by target_format:
        - 'folder': unzip → decrypt → extract → folder
        - 'iso': unzip → decrypt → iso
        - 'pkg': unzip → decrypt → extract → repackage → pkg
        """
        transformation = FileTransformation(source_file=source_zip)
        
        # Step 1: Unzip
        iso_path = self._unzip(source_zip, temp_dir)
        transformation.add_step(TransformStep(...))
        
        # Step 2: Decrypt
        if target_format in ['folder', 'iso', 'pkg']:
            dec_iso = self._decrypt_ps3(iso_path, keys_dir, temp_dir)
            transformation.add_step(TransformStep(...))
        
        # Step 3: Format-specific handling
        if target_format == 'folder':
            folder = self._extract_ps3_iso(dec_iso, temp_dir)
            final = folder
        elif target_format == 'iso':
            final = dec_iso
        elif target_format == 'pkg':
            folder = self._extract_ps3_iso(dec_iso, temp_dir)
            pkg = self._create_pkg(folder, temp_dir)
            final = pkg
            
        transformation.final_file = final
        transformation.status = TransformStatus.SUCCESS
        return transformation
```

---

## Tool Requirements

### Already Have ✅

- `chdman` - CHD compression (Phase 4)
- `dolphin-tool` - RVZ/ISO conversion
- `extract-xiso` - Xbox/Xbox 360 ISO extraction
- `maxcso` - CSO/ZSO compression (PSP)
- `ps3dec` - PS3 decryption
- `wit` (Wiimms ISO Tools) - Wii ISO manipulation
- `wud-compress` - Wii U WUX/WUD conversion
- `xdvdfs-tools` - Xbox filesystem tools

### Need to Verify 🔍

- **Wii U decryption:** cdecrypt? CDecrypt_v2.0b? JWUDTool?
- **PS3 IRD files:** Do we have them? Where?
- **PS3 PKG creation:** make_self_npdrm? pkg_make?
- **Common keys:** Wii U common.key, PS3 keys, etc.

### May Need to Add ❓

- **NSZ** (Switch compression) - Already in `tools/nsz/`? ✅
- **CIA tools** (3DS) - makerom, ctrtool?
- **WAD tools** (Wii) - Wiimms WAD Tools?
- **PSN PKG tools** - pkg2zip, pkg_dec?

---

## Implementation Strategy (Phase 5)

### Approach: HYBRID with Target Branching

Based on our Transform Pipeline Architecture decision, we'll use:
- **One Transform Stage per system** (e.g., `TransformPS3Stage`, `TransformWiiUStage`)
- **Process files sequentially** (memory efficient)
- **Branch based on target format** (within the stage)
- **Track every step** with FileTransformation model

### Pseudo-Pipeline for PS3:

```
Pipeline:
  1. FilterDAT (match PS3 games)
  2. ApplyLists (filter unwanted)
  3. TransformPS3 (unzip → decrypt → format-specific transform)
     ├─ For target "rpcs3": → folder
     ├─ For target "ps3-iso": → .iso
     └─ For target "ps3-pkg": → .pkg
  4. Organize (target-specific structure)
```

### File Flow Example (PS3 - RPCS3 target):

```
Source: 007 - Blood Stone (USA) (En,Fr).zip (6.3 GB)
  ↓ [Step 1: Unzip]
Temp: 007 - Blood Stone (USA) (En,Fr).iso (6.7 GB)
  ↓ [Step 2: Decrypt with keys]
Temp: 007 - Blood Stone (USA) (En,Fr)_dec.iso (6.7 GB)
  ↓ [Step 3: Extract ISO → folder]
Output: BLUS30455/PS3_GAME/* (6.5 GB folder)
  ↓ [Cleanup temps]
Final: BLUS30455/ (6.5 GB) ✅

Storage peak: ~13 GB (zip + iso + dec_iso)
```

### File Flow Example (Wii U - Cemu target):

```
Source: 007 Legends (USA) (En,Fr).zip (9.0 GB)
  ↓ [Step 1: Unzip]
Temp: 007 Legends (USA) (En,Fr).wux (9.6 GB)
  ↓ [Step 2: Decompress WUX → WUD]
Temp: 007 Legends (USA) (En,Fr).wud (23 GB) ⚠️
  ↓ [Step 3: Decrypt with disc key]
Temp: 007 Legends (USA) (En,Fr)_dec.wud (23 GB)
  ↓ [Step 4: Extract to loadiine format]
Output: 007 Legends/code/* (20 GB folder)
  ↓ [Cleanup temps - DELETE 46 GB of temps!]
Final: 007 Legends/ (20 GB) ✅

Storage peak: ~62 GB (zip + wux + wud + dec_wud + folder) 😱
```

**This is why HYBRID approach is critical!** Process one game at a time, cleanup immediately.

---

## Research Questions

### High Priority 🔴

1. **Wii U Decryption:**
   - Which tool? cdecrypt? JWUDTool?
   - Do we need `common.key` file?
   - What's the complete decrypt command?

2. **PS3 IRD Files:**
   - Do we have them?
   - Are they required, or just the disc keys?
   - How to match IRD to ISO?

3. **Target Format Requirements:**
   - RPCS3: Confirmed folder format?
   - Real PS3: Which format per CFW? (Multiman vs WebMan vs Rebug)
   - Wii U on real hardware: Loadiine? Haxchi? What format?

4. **RVZ Format Support:**
   - Do RocknIX/Batocera support RVZ directly?
   - If yes, no transform needed! ✅
   - If no, need RVZ → ISO or RVZ → WBFS

### Medium Priority 🟡

5. **Digital Downloads:**
   - Do we have eShop/WiiWare/VC content?
   - Where are they? What format?
   - How to integrate with pipeline?

6. **Key File Pairing:**
   - Test filename matching algorithm
   - Handle region/revision variations
   - What to do when key missing?

7. **Compression Options:**
   - PS3: Can we use `.iso.gz` or squashfs?
   - Wii U: Keep as WUX or recompress differently?
   - Trade-off: Compression ratio vs load time

### Low Priority 🟢

8. **Xbox 360:**
   - What format in Myrient? ISO? GOD?
   - Decryption needed? (XGD3 encryption)
   - Final format: XISO? GOD? Extract-XISO format?

9. **Switch:**
   - NSP/XCI formats
   - Decryption keys (prod.keys, title.keys)
   - NSZ compression support

10. **3DS:**
    - CIA files
    - Decryption (requires console-specific keys)
    - Citra format requirements

---

## Next Steps

1. ✅ **Document current state** (this document)
2. 🔍 **Research Wii U decryption tools** - Test with sample file
3. 🔍 **Research PS3 IRD requirements** - Check if we have IRD files
4. 🎮 **Define target formats** - Survey emulator/CFW requirements
5. 🔑 **Implement key management** - KeyLocation model + config
6. 🛠️ **Implement TransformPS3Stage** - Start with simplest target (folder)
7. 🧪 **Test with real files** - Small PS3 game, verify complete flow
8. 📈 **Measure storage peaks** - Validate HYBRID approach savings
9. 🔄 **Extend to Wii U** - Apply learnings from PS3
10. 📚 **Update configs** - Add decryption, keys, target formats

---

## Storage Impact Analysis

### Worst Case Scenario (Batch Processing - Approach 2)

If we processed ALL files through each stage before moving to next:

**Example: 10 Wii U games**
- Source ZIPs: 10 × 10 GB = 100 GB
- Unzipped WUX: 10 × 10 GB = 100 GB
- Decompressed WUD: 10 × 23 GB = 230 GB ⚠️
- Decrypted WUD: 10 × 23 GB = 230 GB ⚠️
- Extracted folders: 10 × 20 GB = 200 GB
- **Total: 860 GB** (before cleanup!)

### HYBRID Approach (Sequential Processing)

Process one game completely before next:

**Example: 10 Wii U games**
- Source ZIPs: 100 GB (stays)
- Peak per game: 1 × (10 + 10 + 23 + 23 + 20) = 86 GB
- After game 1: cleanup → 20 GB output, start game 2
- **Peak: 100 GB (sources) + 86 GB (single game) = 186 GB**
- **Final: 100 GB (sources) + 200 GB (outputs) = 300 GB**

**Savings: 860 GB → 300 GB peak (65% reduction!)** 🎉

For PS3 collection (2000+ games, avg 10 GB each):
- Batch: ~40 TB peak! 😱
- HYBRID: ~10 TB peak ✅

**This validates our HYBRID architecture decision!**

---

## Summary

Modern disc-based systems are significantly more complex than cartridge systems:

**Challenges:**
- 🔐 Decryption required (separate key files)
- 🗜️ Multiple compression formats (RVZ, WUX, etc.)
- 📦 Large files (5-50 GB per game)
- 🎯 Target-specific output formats
- 💾 Storage constraints (TB-scale intermediate files)
- 🔑 Key management and pairing
- ❓ Digital downloads (different format entirely)

**Solutions:**
- ✅ HYBRID transform architecture (sequential processing)
- ✅ FileTransformation tracking (complete audit trail)
- ✅ Target-based format selection (in config)
- ✅ Immediate intermediate cleanup (storage efficient)
- 🔄 Flexible key management system (to be implemented)
- 🔄 Plugin system for additional formats (future)

**The path forward is clear, but requires careful research and testing for each system.**

---

*Document will be updated as we research and test each system.*
