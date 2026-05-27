# Wii U Format Discovery: WUA (Wii U Archive)

**Date:** October 13, 2025  
**Status:** Format Validation

## What is WUA?

**WUA (Wii U Archive)** is a compressed, single-file format for Wii U games created by the Cemu emulator team.

### Key Features

- ✅ **Single file** - Much better than folder structures!
- ✅ **Zstandard compression** - Modern, fast, high compression ratio
- ✅ **Native Cemu support** - Load directly, no extraction needed
- ✅ **Includes everything** - Game + updates + DLC in one file
- ✅ **Already decrypted** - No keys needed!

### File Verification

```bash
$ file "007 Legends (USA).wua"
Zstandard compressed data (v0.8+), Dictionary ID: None
```

**Confirmed:** WUA files are zstd-compressed archives.

---

## WUA vs Other Formats

### Format Comparison

| Format | Size (example) | Load Time | Cemu Support | Storage Efficient |
|--------|---------------|-----------|--------------|-------------------|
| **WUA** | 8.3 GB | Fast ✅ | Native ✅ | Excellent ✅ |
| WUX | 9.0 GB | Slow (must decompress) | Indirect | Good |
| WUD | 23 GB | N/A (must decrypt) | No | Poor ❌ |
| Folder | 20 GB | Fast | Yes | Poor ❌ |

**WUA is the ideal format for Batocera/Cemu!** ✅

---

## Myrient → WUA Transformation

### The Challenge

**Myrient provides:**
- WUX files (compressed, encrypted)
- Separate disc key files

**We need:**
- WUA files (compressed, decrypted, single file)

### Transformation Pipeline

```
Myrient ZIP (9 GB)
  ↓ [unzip]
WUX file (9 GB, encrypted)
  ↓ [wux2wud - decompress]
WUD file (23 GB, encrypted) ⚠️
  ↓ [decrypt with disc key]
WUD file (23 GB, decrypted)
  ↓ [wud2wua - compress to WUA]
WUA file (8 GB, decrypted) ✅

Peak storage: ~41 GB per game!
```

### Required Tools

1. **wud-compress** ✅ (have it)
   - WUX → WUD decompression
   
2. **Decryption tool** 🔍 (need to find)
   - cdecrypt
   - CDecrypt
   - JWUDTool
   
3. **WUA creation tool** 🔍 (need to find)
   - Likely part of Cemu tools
   - Or standalone converter

---

## Tool Research: WUA Creation

### Option 1: Cemu Built-in

Cemu emulator may have WUA creation built-in:
```bash
# Hypothetical command (need to verify)
cemu --convert-to-wua input.wud output.wua
```

### Option 2: Standalone Tool

There may be a standalone `wud2wua` or similar tool:
```bash
# Hypothetical (need to research)
wud2wua input.wud output.wua
```

### Option 3: Python/zstd

WUA is just zstd compression, we could potentially:
```python
import zstandard as zstd

# Compress WUD to WUA using zstd
with open("game.wud", "rb") as f_in:
    with open("game.wua", "wb") as f_out:
        cctx = zstd.ZstdCompressor(level=19)  # Max compression
        cctx.copy_stream(f_in, f_out)
```

But this may not match Cemu's exact WUA format structure.

---

## User's Current Setup

**Working WUA Files:**
- Located: `/path/to/output/share/roms-batocera/wiiu/`
- Example: `The Legend of Zelda - Breath of the Wild (USA) (DLC) (v208).wua`
- Confirmed working in Batocera/Cemu ✅

**This proves:**
- ✅ Batocera DOES support Wii U (via Cemu)
- ✅ WUA is the target format we need
- ✅ DLC and updates can be included in WUA
- 🎯 **We need to figure out how to create WUA files from Myrient's WUX files**

---

## Revised Wii U Priority

**Previous assessment:** Optional, lower priority  
**New assessment:** ⬆️ **Should Support** - WUA format makes it practical!

**Reasons:**
1. ✅ Batocera supports it (confirmed by user)
2. ✅ Single-file format (easier to manage than folders)
3. ✅ Better compression than WUX
4. ✅ User has working examples

**Challenges:**
1. 🔍 Find/build WUA creation tool
2. 🔍 Find Wii U decryption tool
3. ⚠️ High storage requirements during processing (~40 GB peak per game)
4. 🔑 Key management (disc keys + common keys)

---

## Research Tasks

### High Priority 🔴

1. **Find WUA creation tool**
   - Check Cemu documentation
   - Search for wud2wua converter
   - Test Python/zstd approach if no tool exists

2. **Find Wii U decryption tool**
   - cdecrypt (most common)
   - JWUDTool (Java-based, has CLI)
   - Verify it works with Linux

3. **Test complete pipeline**
   - Get small Wii U game from Myrient
   - Extract WUX
   - Decompress to WUD
   - Decrypt WUD
   - Convert to WUA
   - Verify in Cemu/Batocera

### Medium Priority 🟡

4. **Key management**
   - Common key file location
   - Disc key pairing algorithm
   - Handle missing keys gracefully

5. **Storage optimization**
   - Process one game at a time (HYBRID approach)
   - Immediate cleanup of intermediates
   - Estimate full collection storage impact

---

## Updated Phase 5 Plan

### Phase 5A: Wii/GameCube (1-2 days) ✅
- Simple unzip of RVZ files
- No transformation needed
- **Start here - quick win!**

### Phase 5B: PS3 (1 week) 🎮
- Key matching
- PS3Dec integration
- ISO extraction
- **Main effort**

### Phase 5C: Wii U (1-2 weeks) 🎯
- **Upgraded to "Should Support"!**
- Research WUA creation tools
- Implement decryption
- Handle storage constraints
- **Worth doing after PS3**

---

## Example: Breath of the Wild

**User's file:**
```
The Legend of Zelda - Breath of the Wild (USA) (DLC) (v208).wua
```

**Filename breakdown:**
- Base game: The Legend of Zelda - Breath of the Wild
- Region: USA
- Includes: DLC content
- Version: v208 (update 208)

**This single file contains:**
- Base game ✅
- All updates (v208) ✅
- All DLC ✅

**Perfect! This is exactly what we want to create from Myrient's WUX files!**

---

## Next Steps

1. ✅ **Document WUA format** (this document)
2. 🔍 **Research WUA creation** - Check Cemu docs, forums, tools
3. 🔍 **Research Wii U decryption** - Find Linux-compatible tool
4. 🧪 **Test with sample** - Small Wii U game, full pipeline
5. 📈 **Measure storage** - Validate HYBRID approach necessity
6. 🛠️ **Implement TransformWiiUStage** - After PS3 is working
7. 📚 **Update configs** - Add Wii U with WUA target format

---

**The WUA discovery changes everything - Wii U is now a practical target!** ✅
