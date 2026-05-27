# Tool Research: Native Linux CLI Tools for ROM Transformation

**Date:** October 13, 2025  
**Status:** Research & Validation

This document catalogs the native Linux CLI tools needed for complex system transformations, focusing on what Batocera and Retrobat actually support.

---

## Target Platforms: Batocera & Retrobat

**Key Decision:** We only need to support what these two retro gaming distributions can actually use.

### What They Support

Both Batocera and Retrobat are based on EmulationStation frontends with backend emulators:
- **PS3:** RPCS3 emulator
- **Wii:** Dolphin emulator
- **Wii U:** Cemu emulator (PC) - **Note:** Not typically on Batocera/Retrobat (requires Windows/Linux PC)
- **GameCube:** Dolphin emulator
- **Xbox 360:** Xenia emulator (limited support, Windows primarily)

**This simplifies our requirements significantly!**

---

## PS3 - Sony PlayStation 3

### What We Have

**Source Files (Myrient):**
- `*.zip` → `*.iso` (encrypted PS3 disc image, 5-50 GB)
- Disc keys: `*.zip` → `*.dkey` (32-char hex string)

**Example `.dkey` file:**
```
EDCCF3B4617BDDC5F4F33E26D98031AC
```

### What is IRD?

**IRD (ISO Rebuild Data)** files contain:
- Complete disc metadata
- Hash information for verification
- Region information
- Sometimes the disc key itself

**Do we need them?** 
- ❌ **NO!** We already have the disc keys as `.dkey` files
- IRD files were primarily used to:
  1. Rebuild ISOs from decrypted files
  2. Extract disc keys (we already have these)
  3. Verify disc integrity

**Since Myrient provides both encrypted ISOs AND separate disc keys, we can decrypt directly without IRD files!**

### What RPCS3 Needs

RPCS3 (the PS3 emulator on Batocera/Retrobat) can load:
1. **Folder format** (extracted game) - PREFERRED ✅
   - `/dev_hdd0/game/BLUS12345/` structure
   - Contains: PARAM.SFO, EBOOT.BIN, USRDIR/, etc.
2. **Decrypted ISO** - Also works
3. **PKG files** - Can install these! ✅

### What are PKG Files?

**PKG = PlayStation Package File**
- Signed/encrypted game packages
- Can contain:
  - Full games (retail or PSN downloads)
  - Game updates/patches
  - DLC content
- RPCS3 can install PKG files directly!

**Your PKG Collection:**
- If you have PKG files, RPCS3 can use them!
- PKG files might be:
  - Full game dumps (useful!)
  - Game updates (very useful! These patch the base game)
  - DLC (useful if we want complete editions)

**Can we use PKG files WITH ISOs?**
- ✅ **YES!** Common workflow:
  1. Install base game from decrypted ISO
  2. Install update PKG on top
  3. Result: Updated game with latest patches!

### PS3 Tool: PS3Dec

**Location:** `/path/to/bin/PS3Dec`

**Usage:**
```bash
# Decrypt a PS3 ISO using disc key
PS3Dec d key <32_char_hex_key> input.iso output.iso

# Example:
PS3Dec d key EDCCF3B4617BDDC5F4F33E26D98031AC \
    "007 - Blood Stone (USA).iso" \
    "007 - Blood Stone (USA)_dec.iso"
```

**Perfect! This is exactly what we need!** ✅

### PS3 Transformation Pipeline

```
Myrient ZIP (6.3 GB)
  ↓ [unzip]
Encrypted ISO (6.7 GB)
  ↓ [PS3Dec with .dkey]
Decrypted ISO (6.7 GB)
  ↓ [extract ISO filesystem]
Game Folder (6.5 GB)
  └─ BLUS30455/
      ├─ PS3_GAME/
      │   ├─ PARAM.SFO
      │   ├─ EBOOT.BIN
      │   └─ USRDIR/
      └─ PS3_UPDATE/ (if present)
```

**For Batocera/RPCS3:**
- Stop at **decrypted ISO** (simpler) OR
- Extract to **folder** (RPCS3 preferred format)

### ISO Extraction Tool

Need a tool to extract PS3 ISO filesystem. Options:

1. **7zip** - Can extract ISO files ✅
   ```bash
   7z x "game_dec.iso" -o"BLUS30455/"
   ```

2. **mount + cp** - Linux native ✅
   ```bash
   mkdir /tmp/ps3mount
   sudo mount -o loop "game_dec.iso" /tmp/ps3mount
   cp -r /tmp/ps3mount/* output_dir/
   sudo umount /tmp/ps3mount
   ```

3. **xorriso** - ISO manipulation tool ✅
   ```bash
   xorriso -osirrox on -indev "game_dec.iso" -extract / output_dir/
   ```

**Recommendation: 7zip** (already commonly installed, no root needed)

### PKG Installation

If you have PKG files (updates/DLC), RPCS3 has a CLI:
```bash
rpcs3 --installpkg game_update.pkg
```

But this requires RPCS3 to be running, so likely not suitable for build pipeline.

**Better approach:** Document that PKG files should be manually installed in RPCS3 after setup.

---

## Wii - Nintendo Wii

### What We Have

**Source Files (Myrient):**
- `*.zip` → `*.rvz` (NKit RVZ compressed format)

**RVZ = Dolphin's compressed format** (similar to CHD for discs)
- Uses zstd compression
- Dolphin emulator loads RVZ natively ✅
- No decompression needed!

### What Dolphin/Batocera Needs

**Supported formats:**
- ✅ **RVZ** - Native support (Dolphin 5.0+)
- ✅ **ISO** - Uncompressed
- ✅ **WBFS** - Wii Backup File System (older format)
- ✅ **GCZ** - Dolphin's older compressed format
- ✅ **CISO/CSO** - Compact ISO format

### Wii Transformation Pipeline

```
Myrient ZIP (1.5 GB)
  ↓ [unzip]
RVZ file (1.5 GB) ✅ DONE!
```

**No further transformation needed!** Dolphin loads RVZ directly!

### If Conversion Needed

If for some reason we need ISO (e.g., real Wii hardware loaders):

**Tool: dolphin-tool** ✅ Already have it!

**Location:** `/path/to/rom-farmer/tools/dolphin-tool/`

```bash
# RVZ → ISO
dolphin-tool convert -f iso -i input.rvz -o output.iso

# ISO → RVZ
dolphin-tool convert -f rvz -i input.iso -o output.rvz
```

But for Batocera/Retrobat: **Just unzip and use RVZ directly!** ✅

---

## GameCube - Nintendo GameCube

### What We Have

**Source Files (Myrient):**
- `*.zip` → `*.rvz` (NKit RVZ compressed format)

**Same as Wii!** Dolphin handles GameCube too.

### GameCube Transformation Pipeline

```
Myrient ZIP
  ↓ [unzip]
RVZ file ✅ DONE!
```

**No transformation needed!** ✅

---

## Wii U - Nintendo Wii U

### Reality Check: Batocera/Retrobat Support

**Cemu emulator requirements:**
- Needs powerful PC (x86-64)
- OpenGL/Vulkan support
- High RAM (8+ GB)

**Batocera support:**
- ⚠️ **Limited** - Only on x86-64 builds (not ARM/SBCs)
- Not typically used on handhelds
- May require manual setup

**Retrobat support:**
- ✅ **YES** - Retrobat is Windows-based, includes Cemu

**Decision:** 
- Wii U is **lower priority** for Batocera
- Focus on Retrobat support
- May skip Wii U initially, add later

### If We Implement Wii U

**Source Files (Myrient):**
- `*.zip` → `*.wux` (compressed WUD, encrypted)
- Disc keys: `*.zip` → `*.key` (16-byte binary key)

**Tool: wud-compress** ✅ Already have it!

**Location:** `/path/to/rom-farmer/tools/wud-compress/`

```bash
# Decompress WUX → WUD
wud-compress -d input.wux output.wud
```

**Decryption Tool:** Need to research
- **cdecrypt** (common tool)
- **JWUDTool** (Java-based, has CLI)
- **CDecrypt** (Windows, but might work with Wine)

**Transformation:**
```
ZIP (9 GB) → WUX (9 GB) → WUD (23 GB) → Decrypt → Loadiine folder
```

**Massive storage impact!** This is Phase 5+ work.

---

## Xbox 360 - Microsoft Xbox 360

### Reality Check: Batocera/Retrobat Support

**Xenia emulator:**
- Windows-only (primarily)
- Xenia Canary (Linux fork exists but experimental)
- Very demanding (needs powerful PC)

**Batocera support:**
- ❌ **NO** - Xenia not included
- Too demanding for SBCs

**Retrobat support:**
- ⚠️ **Limited** - Can add Xenia manually, not default

**Decision:**
- Xbox 360 is **low priority**
- Xenia is not stable enough for automated pipeline
- Consider as future enhancement

---

## Tool Inventory & Installation

### Already Have ✅

1. **PS3Dec** - `/path/to/bin/PS3Dec`
   - PS3 ISO decryption ✅
   
2. **dolphin-tool** - `/path/to/rom-farmer/tools/dolphin-tool/`
   - Wii/GameCube RVZ/ISO conversion ✅
   
3. **wud-compress** - `/path/to/rom-farmer/tools/wud-compress/`
   - Wii U WUX/WUD conversion ✅
   
4. **chdman** - (from MAME tools)
   - CHD compression (already using in Phase 4) ✅

5. **7zip** - System package
   - ISO extraction, general archives ✅

### Need to Check

1. **xorriso** - ISO extraction tool
   ```bash
   sudo apt-get install xorriso
   ```
   
2. **cdecrypt** - Wii U decryption (if we implement Wii U)
   - Need to research installation

### Don't Need

- ❌ IRD files - Not needed, have disc keys
- ❌ PKG creation tools - Not building PKGs, just using them
- ❌ Xenia tools - Not supporting Xbox 360 yet

---

## Simplified System Priorities

Based on Batocera/Retrobat support:

### Tier 1 - Must Support ✅
1. **Wii** - Just unzip RVZ, done! (EASY)
2. **GameCube** - Just unzip RVZ, done! (EASY)
3. **PS3** - Unzip → decrypt → extract (MEDIUM)

### Tier 2 - Should Support 🟡
4. **Wii U** - Complex, storage-heavy (HARD)
   - Only for Retrobat x86-64 builds
   - Requires decryption research

### Tier 3 - Future/Optional 🔵
5. **Xbox 360** - Emulation not mature (SKIP for now)
6. **Switch** - Requires Yuzu/Ryujinx (Future)
7. **3DS** - Requires Citra (Future)

---

## Digital Downloads - eShop / WiiWare / VC / PSN

### Your Question: "If I can use them, I will download the complete collections"

**Answer:** It depends on emulator support!

### Virtual Console (VC) ROMs

**What they are:**
- NES/SNES/N64/etc games packaged for Wii/Wii U
- Usually in WAD format (Wii) or encrypted format (Wii U)

**Can we use them?**
- ❌ **NO** - Just use original No-Intro ROMs instead!
- VC versions often have emulation wrapper
- Original ROMs work better in modern emulators
- No benefit to using VC dumps

### WiiWare / DSiWare

**What they are:**
- Original games for download (not retro games)
- WAD format (Wii), TAD format (DSi)

**Can we use them?**
- ⚠️ **MAYBE** - If you want to play WiiWare games on Dolphin
- Would need WAD extraction tools
- Lower priority (not retro systems)

### Nintendo eShop (3DS/Wii U/Switch)

**Formats:**
- 3DS: CIA files
- Wii U: Encrypted format
- Switch: NSP/XCI files

**Can we use them?**
- **3DS (CIA):** ✅ YES - Citra emulator supports CIA
- **Wii U:** ⚠️ Complex - overlaps with disc library
- **Switch:** ✅ YES - Yuzu/Ryujinx support NSP/XCI

**Recommendation:**
- **3DS/Switch:** Worth getting if you want to support those systems
- **Wii U eShop:** Skip - focus on disc library

### PSN (PlayStation Network)

**Your PKG files:**

**Can we use them?**
- ✅ **YES for PS3!** - RPCS3 installs PKG files
- These are likely:
  - Game updates (patch ISOs)
  - DLC content
  - Digital-only games

**Value:**
- **High value!** Game updates fix bugs, add features
- Can combine with ISO base game
- Digital-only PSN games work too

**Workflow:**
1. Process PS3 ISOs (base games) → folders
2. Document available PKG files (updates/DLC)
3. User installs PKGs in RPCS3 to patch games

**Or simpler:** Process PKG files into folders too!

```bash
# RPCS3 can extract PKG to folder
# (would need to research exact command)
```

---

## Updated PS3 Strategy with PKG Support

### Option 1: ISOs Only (Simpler)
```
ZIP → ISO → decrypt → folder
```

### Option 2: ISOs + PKG Updates (Better!)
```
Base Game:
  ZIP → ISO → decrypt → folder → BLUS30455/

Game Update:
  PKG → install/extract → merge into BLUS30455/
  
Result: Updated game with patches ✅
```

### Option 3: PKG Files Directly
```
Some games might only have PKG (PSN digital-only)
  PKG → extract → folder ✅
```

**Recommendation:** Start with Option 1 (ISOs), add PKG support later when we understand PKG extraction better.

---

## Revised Phase 5 Implementation Plan

### Phase 5A: Nintendo Disc Systems (EASY) ✅

**Wii + GameCube:**
```python
class UnzipRVZStage(Stage):
    """Just unzip the RVZ files. That's it!"""
    
    def execute(self, context: StageContext) -> StageResult:
        for zip_file in context.matched_files:
            # Extract RVZ
            with zipfile.ZipFile(zip_file) as zf:
                zf.extractall(context.work_dir)
            
            # RVZ is ready to use!
            rvz_file = context.work_dir / zip_file.stem / "*.rvz"
            context.final_files.append(rvz_file)
```

**Effort:** 1-2 days (mostly testing)

### Phase 5B: PlayStation 3 (MEDIUM) 🎮

**PS3 ISO Processing:**
```python
class TransformPS3Stage(Stage):
    """Transform PS3 ISOs for RPCS3."""
    
    def _transform_ps3_game(self, zip_file, keys_dir, temp_dir):
        # Step 1: Unzip ISO
        iso = self._unzip_iso(zip_file, temp_dir)
        
        # Step 2: Find matching .dkey file
        dkey = self._find_disc_key(zip_file.stem, keys_dir)
        
        # Step 3: Decrypt with PS3Dec
        dec_iso = self._decrypt_ps3(iso, dkey, temp_dir)
        
        # Step 4: Extract to folder (using 7zip)
        folder = self._extract_iso(dec_iso, context.output_dir)
        
        # Step 5: Cleanup temps
        iso.unlink()
        dec_iso.unlink()
        
        return folder  # Game folder ready for RPCS3
```

**Effort:** 1 week (key matching, tool integration, testing)

### Phase 5C: Wii U (HARD) - OPTIONAL 🔮

**Wii U Processing:**
- Requires decryption tool research
- Massive storage impact (~60 GB per game peak)
- Only useful for Retrobat x86-64

**Decision:** Skip for initial release, add later if needed

### Phase 5D: Digital Content (FUTURE) 📦

**PKG file support:**
- Research PKG extraction tools
- Add as Phase 6 enhancement

---

## Summary & Next Steps

### What We Learned

1. ✅ **PS3 disc keys are simple hex strings** - No IRD files needed!
2. ✅ **PS3Dec tool exists and works** - `/path/to/bin/PS3Dec`
3. ✅ **Wii/GameCube need NO transformation** - RVZ is native format!
4. ✅ **PKG files are valuable** - Game updates and digital content
5. ✅ **Target is Batocera/Retrobat only** - Simplifies requirements
6. ⚠️ **Wii U is complex** - Lower priority, Retrobat only
7. ❌ **Xbox 360 not ready** - Skip for now

### Immediate Next Steps (Phase 5)

1. **Wii/GameCube (Quick Win!):**
   - Implement simple unzip stage
   - Test with sample RVZ files
   - Estimate: 1-2 days ✅

2. **PS3 (Main Work):**
   - Implement key matching algorithm
   - Integrate PS3Dec
   - Implement ISO extraction (7zip)
   - Test full pipeline
   - Estimate: 1 week 🎮

3. **Documentation:**
   - Document PKG file locations for users
   - Create manual PKG installation guide
   - Update system support matrix

### Future Phases

- **Phase 6:** PKG file processing (updates/DLC)
- **Phase 7:** Wii U support (if needed)
- **Phase 8:** Switch/3DS (if emulators mature)

---

**The path is clear: Wii/GameCube first (easy), then PS3 (medium), Wii U later (hard)!**
