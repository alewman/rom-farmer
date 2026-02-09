# Xbox Platforms & Tools Guide

## ⚠️ CRITICAL: Xbox vs Xbox 360 are DIFFERENT!

This is a **common confusion** - here's what you need to know:

---

## 🎮 Original Xbox (2001-2006)

**Tool: extract-xiso** ✅ (BUILT and ready!)

### What It Is
- First Xbox console
- Pentium III processor
- DVD drive with custom XISO format
- Games: Halo, Halo 2, Ninja Gaiden, etc.

### File Formats
- **XISO** - Custom Xbox ISO format
- **ISO** - Standard ISO that can be converted to XISO
- Uses custom Microsoft file system (not ISO 9660)

### Tool: extract-xiso

**Status:** ✅ Built and ready!
**Location:** `tools/bin/extract-xiso`
**Version:** v2.7.1 (build-202505152050)

**What it does:**
```bash
# Create XISO from extracted game directory
extract-xiso -c game_directory -o game.iso

# Extract XISO to directory  
extract-xiso game.iso

# Rewrite/optimize XISO
extract-xiso -r game.iso

# List XISO contents
extract-xiso -l game.iso
```

**Why needed:**
- Xbox DVDs use custom XISO format
- Different from standard ISO 9660/UDF
- Includes security sectors and special partitioning
- default.xbe executable format

---

## 🎮 Xbox 360 (2005-2016)

**Tool: DIFFERENT TOOLS NEEDED** ⚠️

### What It Is
- Second Xbox console (successor to original Xbox)
- PowerPC processor (completely different architecture!)
- DVD drive with XGD2/XGD3 format
- Games: Halo 3, Gears of War, Red Dead Redemption, etc.

### File Formats
- **ISO** - Standard ISO 9660 format (NOT XISO!)
- **GOD** - Games on Demand (digital downloads)
- **XBLA** - Xbox Live Arcade games
- Different disc formats: XGD2, XGD3, XGD4

### Tools Needed for Xbox 360

**extract-xiso DOES NOT work for Xbox 360!**

Instead, you need:

#### 1. **Xbox Backup Creator (XBC)**
- Windows only
- Can create/extract Xbox 360 ISOs
- Handles XGD2/XGD3 formats
- URL: https://github.com/Freeza/Xbox-Backup-Creator

#### 2. **extract-xiso for Xbox 360** (different tool!)
- There's a separate Xbox 360 version
- NOT the same as original Xbox tool
- Less commonly used

#### 3. **xdvdfs-tools**
- Linux/cross-platform
- Can extract Xbox 360 file systems
- URL: https://github.com/antangelo/xdvdfs

#### 4. **wxPirs** / **Velocity**
- For GOD/XBLA packages
- Extract/repack digital content

---

## 📊 Quick Comparison

| Feature | Original Xbox | Xbox 360 |
|---------|--------------|----------|
| **Released** | 2001 | 2005 |
| **CPU** | Intel Pentium III | PowerPC Xenon |
| **Format** | XISO (custom) | ISO 9660 + XGD |
| **Tool** | extract-xiso ✅ | XBC / xdvdfs-tools ❌ |
| **Executable** | default.xbe | default.xex |
| **Compatible?** | NO - completely different! | NO - completely different! |

---

## 🎯 What We Have Built

### ✅ Original Xbox Support
- extract-xiso v2.7.1 built and ready
- Can create/extract XISO files
- Transformation tracking ready
- ScreenScraper integration ready

### ❌ Xbox 360 Support (NOT YET)
- Need different tools (XBC or xdvdfs-tools)
- Different file formats
- Different transformation strategy
- Would require separate tool integration

---

## 🔧 Adding Xbox 360 Support (Future Work)

If you want Xbox 360 support, here are the options:

### Option 1: xdvdfs-tools (Linux-friendly)
```bash
cd tools
mkdir xdvdfs-tools
# Create clone.sh and build.sh
# Clone from: https://github.com/antangelo/xdvdfs
```

**Pros:**
- Open source
- Cross-platform (Rust-based)
- Active development
- Can extract Xbox 360 file systems

**Cons:**
- Newer tool, less mature
- May not handle all XGD formats

### Option 2: Xbox Backup Creator (XBC)
**Pros:**
- Most popular tool
- Handles all Xbox 360 formats
- Well-tested

**Cons:**
- Windows only (would need Wine)
- Not open source
- Harder to automate

### Option 3: extract-xiso-360
**Pros:**
- Similar name to original tool
- Designed for Xbox 360

**Cons:**
- Less actively maintained
- Harder to find reliable source

---

## 💡 Recommendation

### For Original Xbox: ✅ You're all set!
```bash
# Use extract-xiso (already built)
tools/bin/extract-xiso game.iso
```

### For Xbox 360: Need to decide
1. **Do you have Xbox 360 games to process?**
   - If YES: Let's add xdvdfs-tools support
   - If NO: Wait until needed

2. **Are they already in ISO format?**
   - If YES: May not need special tools
   - If NO: Need extraction tools

3. **What's your priority?**
   - Saturn/original Xbox first
   - Xbox 360 can wait

---

## 🎮 Example: What Each Tool Does

### Original Xbox (extract-xiso)
```bash
# You have: Halo (USA).iso (XISO format)
extract-xiso -l "Halo (USA).iso"
# Lists: default.xbe, *.xpr files, etc.

# Extract it
extract-xiso "Halo (USA).iso"
# Creates: Halo (USA)/ directory with game files

# Create new XISO
extract-xiso -c "Halo (USA)" -o "Halo (USA).iso"
```

### Xbox 360 (would need different tool)
```bash
# You have: Halo 3 (USA).iso (standard ISO format)
# extract-xiso WON'T WORK!

# Would need something like:
xdvdfs-tools extract "Halo 3 (USA).iso" output_dir/
# OR
xbox-backup-creator.exe /extract "Halo 3 (USA).iso"
```

---

## 🔍 How to Tell Which Xbox You Have

### File Indicators

**Original Xbox:**
- Contains `default.xbe` files
- XISO format (special structure)
- Directory structure: game files in root
- File sizes: 50MB - 7GB (DVD5/DVD9)

**Xbox 360:**
- Contains `default.xex` files
- Standard ISO 9660 format (usually)
- XGD2/XGD3 format indicators
- File sizes: 6-8GB (DVD9)
- May see "XBOX360" in volume label

### Quick Test
```bash
# Try to mount as regular ISO
sudo mount -o loop game.iso /mnt

# If it mounts and you see files:
# - default.xex = Xbox 360 ✅
# - default.xbe = Original Xbox ✅

# If it won't mount:
# - Probably XISO (Original Xbox)
# - Need extract-xiso
```

---

## 📝 Summary

**The Answer to Your Question:**

> "This tool does work for xbox 360 too right?"

**NO** - extract-xiso is for **original Xbox only**.

**What we built:**
- ✅ extract-xiso v2.7.1 - Original Xbox (2001-2006)
- ❌ Xbox 360 tools - Not built yet (different console, different tools)

**What you need:**
- For original Xbox games: Use extract-xiso (ready now!)
- For Xbox 360 games: Need to add xdvdfs-tools or similar

**Next steps:**
1. Identify which Xbox games you have (original vs 360)
2. If Xbox 360, decide which tool to integrate
3. Build that tool following same pattern as extract-xiso

Want to add Xbox 360 support? Just let me know! The infrastructure is ready - we'd just clone xdvdfs-tools and create build scripts like we did for extract-xiso and MAME.

---

## 🔗 See Also

- `tools/extract-xiso/README.md` - Original Xbox quick start
- `tools/README.md` - Tools infrastructure overview
- `docs/MULTI_TIER_STRATEGY.md` - Transformation tracking strategy
- https://github.com/XboxDev/extract-xiso - Original Xbox tool (what we built)
- https://github.com/antangelo/xdvdfs - Xbox 360 option (not built yet)
