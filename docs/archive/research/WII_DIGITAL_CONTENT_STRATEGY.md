# Wii Digital Content Strategy

**Date:** October 14, 2025  
**Status:** Recommendation for handling WiiWare, Virtual Console, and DLC

## The Situation

### What You Currently Have (Working):
**Redump Physical Discs** via Myrient
- Format: RVZ (NKit processed)
- Content: Base retail games only
- Count: ~1,200 USA games (1G1R filtered)
- Status: ✅ Working in rom-farmer (Phase 5A)

### What's Also Available (Not Currently Used):
**No-Intro Digital CDN** - `Nintendo - Wii (Digital) (CDN)`
- WiiWare games (digital-only titles)
- Virtual Console games (NES, SNES, etc. on Wii)
- DLC content for retail games
- Format: WAD files (Wii installable packages)

---

## Understanding Wii Digital Content

### 1. WiiWare
**Digital-only games released on Wii Shop Channel**

Examples:
- World of Goo
- Cave Story
- LostWinds
- Art Style series

**Value:** Some excellent exclusive games not available on disc

### 2. Virtual Console
**Classic games re-released on Wii**

Systems included:
- NES
- SNES  
- N64
- Genesis
- TurboGrafx-16
- Neo Geo
- Commodore 64
- Master System
- And more!

**Value:** Convenient but... you probably have these systems separately already

### 3. DLC
**Downloadable content for retail games**

Examples:
- Rock Band song packs
- Just Dance song packs
- Mario Kart Wii channels

**Value:** Enhances base games but not essential

---

## Wii Digital Content Challenges

### Format: WAD Files
WAD = Wii Application Distribution

**Problem:** WADs require installation, not direct loading

### Installation Methods:

**Option 1: Real Wii (CFW Required)**
```
1. Copy WAD to SD card
2. Use WAD Manager on Wii
3. Install to Wii system menu
4. Launch from menu
```
✅ Works on real hardware  
❌ Manual per-game process  
❌ Requires CFW  

**Option 2: Dolphin Emulator**
```
1. Dolphin → Tools → Install WAD
2. Select WAD file
3. Dolphin installs to NAND
4. Shows in system menu
```
✅ Works in emulator  
❌ Still manual per game  
❌ NAND management required  

**Option 3: Conversion Tools?**
Some tools exist to convert WAD → other formats, but:
- Inconsistent results
- Not well documented
- May not work with all games
- Legal gray area

---

## Recommendation: Selective Approach

### Priority 1: Focus on Retail Discs ✅
**What you're doing now is perfect:**
- Redump RVZ files = complete retail library
- These are the "main" Wii games people want
- Easy to manage (just extract RVZ)
- No installation hassles

### Priority 2: WiiWare - Separate Collection (Optional)
**If you want WiiWare games:**

1. **Keep separate from retail games**
   ```
   /data/emu/output/batocera/wii/        # Retail RVZ
   /data/emu/output/batocera/wiiware/    # Digital WAD
   ```

2. **Document installation process**
   - Provide WAD files
   - User installs via Dolphin
   - Not automated

3. **Add to rom-farmer as "manual" type**
   ```yaml
   # config/platforms/wiiware.yaml
   name: wiiware
   system_type: simple
   
   sources:
     - path: /data/emu/archive/No-Intro/Nintendo - Wii (Digital) (CDN)/
       type: manual_install
       note: "WAD files require installation in Dolphin"
   
   # No transformation - just organize and provide
   targets:
     - name: batocera
       output_path: /data/emu/output/batocera/wiiware/
       organization:
         style: rich
       metadata: true
       note: "User must install WADs manually in Dolphin"
   ```

### Priority 3: Virtual Console - Skip ❌
**Don't bother with VC:**
- You already have NES, SNES, N64, Genesis collections
- Running them natively is better than in Wii emulator
- Wii VC = "emulator within emulator" = worse performance
- Not worth the complexity

### Priority 4: DLC - Document Only 📝
**For DLC:**
- Document which games have DLC available
- Provide WAD files if requested
- User can install manually if desired
- Not worth automating

---

## Practical Implementation

### Current Setup (Keep As-Is):
```yaml
# config/platforms/wii.yaml
name: wii
sources:
  - path: .../Redump/Nintendo - Wii - NKit RVZ/
    type: myrient
```
✅ This handles all retail games perfectly

### Optional Addition (WiiWare):
```yaml
# config/platforms/wiiware.yaml (new file)
name: wiiware
system_type: simple

sources:
  - path: /data/emu/archive/No-Intro/Nintendo - Wii (Digital) (CDN)/WiiWare/
    type: manual_install
    description: "WiiWare games - WAD files"

# Simple pipeline: filter, organize, document
# No transformation (WADs stay as WADs)
targets:
  - name: batocera
    output_path: /data/emu/output/batocera/wiiware/
    organization:
      style: rich
    metadata: true
    
# Add README explaining installation
install_instructions: |
  WiiWare games are distributed as WAD files.
  
  To use in Dolphin:
  1. Open Dolphin
  2. Tools → Install WAD
  3. Select WAD file
  4. Game appears in system menu
  
  To use on real Wii (CFW):
  1. Copy WAD to SD card
  2. Use WAD Manager
  3. Install to system
```

---

## Comparison: What's Worth It?

| Content Type | Worth Automating? | Recommendation |
|--------------|-------------------|----------------|
| **Retail Discs** | ✅ YES | Already done! (Phase 5A) |
| **WiiWare** | 🟡 MAYBE | Optional separate collection |
| **Virtual Console** | ❌ NO | Use native collections instead |
| **DLC** | ❌ NO | Document only, manual install |

---

## My Recommendation

### Do This:
1. ✅ **Keep using Redump RVZ** for retail games (what you have now)
2. 📝 **Document WiiWare availability** in README
3. 📦 **Optionally provide WiiWare WADs** as separate collection
4. 📖 **Provide installation guide** for users who want WiiWare

### Don't Do This:
1. ❌ Don't try to automate WAD installation (not practical)
2. ❌ Don't include Virtual Console (use native collections)
3. ❌ Don't automate DLC (manual per-game, not worth it)

---

## Summary

**Your current approach is optimal:**
- Redump RVZ = All retail Wii games ✅
- Easy extraction, no conversion needed ✅
- Works great in Dolphin/Batocera ✅

**WiiWare is a "nice to have":**
- Some exclusive digital games worth preserving
- But requires manual installation
- Keep as separate optional collection
- Document but don't automate

**This is the practical solution!** 🎯

Would you like me to:
1. Create a simple `wiiware.yaml` config as "manual install" type?
2. Skip WiiWare entirely and document in README?
3. Something else?
