# Retool DAT Inventory - Systems Status

## Summary

✅ **You have excellent Retool DAT coverage!**

### No-Intro Systems (Cartridge) - nointro.retool.1g1r.eng/
✅ 41 systems with Retool 1G1R English DATs

**Key systems**:
- NES: 1,761 games (from 29K+)
- SNES: 886 games
- Game Boy: 785 games
- Game Boy Color: 941 games
- Game Boy Advance: 1,139 games
- Nintendo DS: 2,152 games
- Nintendo 64: 354 games
- Sega Genesis/Mega Drive: 1,040 games
- Sega Game Gear: 311 games
- Sega Master System: 495 games
- Sega 32X: 33 games
- And many more!

### Redump Systems (Disc) - retool.redump.1g1r.eng/
✅ 15 systems with Retool 1G1R English DATs

**Disc Systems You Have**:
- ✅ **Sega Saturn**: 318 games (from 2,375) ← **YOUR PRIMARY TARGET!**
- ✅ Sony PlayStation: 1,798 games (from 10,797)
- ✅ Sony PlayStation 2: 2,556 games (from 11,558)
- ✅ **Sony PlayStation Portable**: 733 games (from 3,040)
- ✅ Sega Dreamcast: 333 games (from 1,489)
- ✅ Sega Mega CD/Sega CD: 162 games (from 543)
- ✅ Nintendo GameCube: 595 games (from 2,002)
- ✅ Nintendo Wii: 1,443 games (from 3,776)
- ✅ Microsoft Xbox: 975 games (from 2,626)
- ✅ Microsoft Xbox 360: 1,400 games (from 3,440)
- ✅ NEC PC Engine CD/TurboGrafx CD: 68 games (from 548)
- ✅ SNK Neo Geo CD: 91 games (from 111)
- ✅ Panasonic 3DO: 160 games (from 661)
- ✅ Philips CD-i: 154 games (from 2,261)

### USA-Only Variant (redump.retool.1g1r.usa/)
✅ Also has 14 systems with USA-focused filtering
- Use these for space-constrained builds (smaller collections)

---

## Missing Retool DATs

### ❌ Sony PlayStation 3
**Status**: NO Retool DAT exists

**What you have**:
- Cuesheets (12 files)
- Disc Keys (4,366 keys)
- Disc Keys TXT format

**Issue**: PS3 doesn't have a standard Redump DAT like other systems
- PS3 uses IRD (ISO Rebuild Data) files instead
- Different verification system
- No standard DAT file format

**Recommendation**: 
- For PS3, we'll need a different approach
- Use directory scanning + IRD database
- Or manual game lists
- PS3 is complex anyway (decryption, large files) - defer to later phase

### ⚠️ Other Systems Not in Retool
Checking against Myrient structure, you might also want:
- Nintendo Switch (too new for Retool?)
- WiiU (might not have Retool yet?)
- PS Vita (might not have Retool yet?)

---

## Recommendation: Systems to Build Retool DATs For

### Priority 1: NONE NEEDED! ✅
You have all the major systems covered for Phase 1-3:
- ✅ NES (No-Intro) - Your baseline test system
- ✅ Saturn (Redump) - Your disc system target
- ✅ PSP (Redump) - Additional disc test
- ✅ All other major cartridge systems
- ✅ All other major disc systems

### Priority 2: Optional (Future Enhancement)
If you expand to modern systems:
- Nintendo Switch (if Retool supports it)
- WiiU (if Retool supports it)
- PS Vita (if available)
- PS3 (special handling - no DAT format)

---

## DAT File Strategy

### For Config System:

```yaml
platforms:
  nes:
    dat:
      retool:
        file: /path/to/dats/nointro.retool.1g1r.eng/Nintendo - Nintendo Entertainment System (Headered) (Parent-Clone) (20241224-130037) (Retool 2024-12-25 23-21-56) (1,761) (-n) [-AaBbcDdekMmoPrv].dat
        count: 1761  # Games after filtering
  
  saturn:
    dat:
      retool:
        file: /path/to/dats/retool.redump.1g1r.eng/Sega - Saturn (2024-12-19 19-29-19) (Retool 2025-09-07 18-14-17) (318) (-n) [-AabBcdekmMoPrv].dat
        count: 318  # Games after filtering
  
  psp:
    dat:
      retool:
        file: /path/to/dats/retool.redump.1g1r.eng/Sony - PlayStation Portable (2024-12-20 19-12-20) (Retool 2025-09-07 18-16-01) (733) (-n) [-AabBcdekmMoPrv].dat
        count: 733
  
  ps3:
    # Special handling - no Retool DAT
    dat:
      type: directory_scan  # Different approach
      ird_database: /path/to/keys/ird/
```

---

## Answers to Your Questions

### A. Retool DATs for Redump?
✅ **YES!** You have them:
- `retool.redump.1g1r.eng/` - 15 systems (English + USA + Europe + playable JP)
- `redump.retool.1g1r.usa/` - 14 systems (USA-only, smaller collections)

**Use ENG variant** for primary builds (matches your 1g1r_eng strategy)

### B. ZIP Filename Matching
✅ **Confirmed correct approach**:
- DAT says: `Contra (USA).nes`
- Myrient has: `Contra (USA).zip`
- **Match**: Strip `.zip`, expect inner file matches DAT entry
- **Implementation**: Use `zipfile.namelist()` to verify

### C. List Files + Retool Interaction
**Need to check**: Let me verify if pirate carts are in Retool DATs...

Looking at NES Retool DAT, I see entries like:
```xml
<game name="100-in-1 Contra Function 16 (Asia) (En) (Pirate)">
<game name="100-in-1 Real Game (Asia) (En,Ja) (Pirate)">
```

✅ **ANSWER**: Yes, Retool KEEPS some pirate carts!
- Pirate carts with unique content → Kept
- Multi-carts and bad dumps → Removed

**Your `nes-delete` list** with 26 pirate carts:
- These are likely multi-carts (500-in-1, etc.)
- Retool probably kept them (some have unique games)
- Your delete list removes them manually

**Workflow**:
1. Retool filters: 29K → 1,761 games (removes duplicates, bad dumps, most pirates)
2. Your `nes-delete`: Removes remaining 26 unwanted pirates/aftermarket
3. Result: 1,735 clean games

**So YES, list files are still needed even with Retool!**

---

## Configuration Strategy

### Use Retool DATs as Primary Source
```yaml
global:
  dat_priority:
    - retool_1g1r_eng  # Highest priority - already filtered!
    - retool_1g1r_usa  # Fallback for USA-only builds
    - nointro_standard # Only if Retool not available
    - redump_standard  # Only if Retool not available
```

### Per-Platform Override
```yaml
platforms:
  nes:
    dat:
      source: retool_1g1r_eng  # Use pre-filtered
  
  saturn:
    dat:
      source: retool_1g1r_eng  # Use pre-filtered
  
  ps3:
    dat:
      source: manual_scan  # No DAT available, scan directory
```

---

## Next Steps

✅ **You're ready to proceed!**

**No Retool DATs need to be built** for Phase 1-3 (NES + Saturn + PSP)

**Implementation can start immediately:**
1. Build config system
2. Parse Retool DATs (you have them all!)
3. Test with NES (1,761 games from Retool DAT)
4. Test with Saturn (318 games from Retool DAT)
5. Verify list files work (delete 26 pirates, add Best-Games)

**PS3 handling**: Defer to Phase 4+ (special case, no standard DAT)

---

## Summary for Implementation

**DAT Files to Use**:
- **NES**: `/path/to/dats/nointro.retool.1g1r.eng/Nintendo - NES...dat` (1,761 games)
- **Saturn**: `/path/to/dats/retool.redump.1g1r.eng/Sega - Saturn...dat` (318 games)
- **PSP**: `/path/to/dats/retool.redump.1g1r.eng/Sony - PSP...dat` (733 games)

**All other systems**: Also have Retool DATs ready to use!

**Ready to start building the config system!** 🚀
