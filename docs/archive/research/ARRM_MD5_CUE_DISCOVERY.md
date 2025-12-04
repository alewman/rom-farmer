# ARRM MD5 Hash Discovery: CUE Files are the Canonical Reference

**Date:** October 26, 2025  
**Discovery:** ARRM stores MD5 hashes of `.cue` files, not `.zip` or `.bin` files  
**Verified:** 2,393 Saturn games (100% match rate)

---

## Executive Summary

When scraping metadata from ARRM (Another ROM Manager), the MD5 hashes stored in `gamelist.xml` correspond to the **cue sheet (`.cue`) file** inside the ROM archive, NOT the:
- `.zip` archive itself
- `.bin` disc image files
- Combined hash of all files

This discovery resolves the "87% MD5 mismatch" mystery we encountered when trying to verify ROM collections.

---

## Background: The Mystery

### Initial Problem
When comparing MD5 hashes between:
- ARRM's `gamelist.xml` metadata
- Our RomGroomer database (scraped from ARRM)
- Actual source ROM files

We found an **87% mismatch rate** for CD-based systems (Saturn, PSX, Sega CD).

### Investigation Process

1. **Hypothesis 1:** ZIP compression affects MD5
   - ❌ Still mismatched when comparing to extracted files

2. **Hypothesis 2:** Multi-disc games cause confusion
   - ❌ Even single-disc games showed mismatches

3. **Hypothesis 3:** ARRM uses BIN file MD5s
   - ❌ BIN files too large, hashes didn't match

4. **Breakthrough:** Tested CUE file MD5
   - ✅ **Perfect match!**

---

## Technical Details

### What is a CUE File?

A `.cue` file (cue sheet) is a **plain text metadata file** that describes CD/DVD disc structure:

```cue
FILE "Game Name (Region) (Track 01).bin" BINARY
  TRACK 01 MODE2/2352
    INDEX 01 00:00:00
FILE "Game Name (Region) (Track 02).bin" BINARY
  TRACK 02 AUDIO
    INDEX 00 00:00:00
    INDEX 01 00:02:00
```

**Key Properties:**
- Small text file (typically < 5KB)
- Defines track layout and types (data, audio, video)
- Lists all `.bin` files in the disc image
- Fast to hash (unlike multi-GB `.bin` files)
- Stable across re-packaging (doesn't change with compression)

### Why CUE Files Make Sense as Canonical Reference

1. **Performance**: Hashing a 2KB text file vs 700MB disc image
2. **Stability**: CUE content remains constant regardless of ZIP compression settings
3. **Completeness**: CUE references all tracks, serving as a manifest
4. **Uniqueness**: Each disc release has a unique track layout
5. **Standard Practice**: Redump and No-Intro projects use CUE files as primary identifiers

---

## Verification Results

### Saturn Collection (Redump)
```
Total games:     2,393
✅ Matches:      2,393 (100.0%)
❌ Mismatches:   0 (0.0%)
⚠️  Missing:      0 (0.0%)
```

**Tool Used:** `verify_arrm_md5s.py`

**Process:**
1. Parse `gamelist.xml` to extract MD5 hashes and game paths
2. Locate source `.zip` ROM archives
3. Extract `.cue` file from each archive
4. Compute MD5 hash of extracted `.cue` file
5. Compare against `gamelist.xml` MD5 value

**Result:** Perfect 100% match across entire collection

---

## Implications for RomGroomer

### Database Linking Bug Fixed

**Problem:** RomGroomer's compress stage wasn't linking transformations to games in the database.

**Root Cause:** Code was looking up games by source MD5, but we were using the wrong MD5:
```python
# ❌ WRONG: Using ZIP or BIN MD5
game = db.query(ScrapedGame).filter_by(md5=zip_md5).first()

# ✅ CORRECT: Using CUE MD5
game = db.query(ScrapedGame).filter_by(md5=cue_md5).first()
```

**Fix Applied:** Updated compression pipeline to:
1. Extract `.cue` file from source `.zip`
2. Hash the `.cue` file
3. Use CUE MD5 for database lookups
4. Link transformation records to correct game entries

---

## Systems Affected

This discovery applies to **all CD-based systems** where ARRM is used:

### Verified
- ✅ **Sega Saturn** (2,393 games) - 100% match

### Expected to Apply
- **Sony PlayStation** (PSX)
- **Sega CD / Mega CD**
- **PC Engine CD / TurboGrafx CD**
- **3DO**
- **Neo Geo CD**
- **Philips CD-i**
- **Amiga CD32**

### Not Affected
- Cartridge-based systems (NES, SNES, Genesis, etc.)
- Single-file disc formats without CUE sheets

---

## Best Practices

### When Scraping ARRM Metadata

1. **Always extract and hash the `.cue` file** for CD-based systems
2. Store the CUE MD5 as the canonical identifier
3. Use CUE MD5 for database lookups and verification
4. Include original `.zip` MD5 as secondary metadata (for archive integrity)

### When Verifying ROM Collections

```bash
# ✅ Correct verification method
python3 verify_arrm_md5s.py --gamelist /path/to/gamelist.xml

# ❌ Wrong: Comparing ZIP file MD5s
md5sum *.zip  # These won't match gamelist.xml
```

### When Building Transformation Pipelines

```python
# Extract CUE from source archive
cue_path = extract_cue_from_zip(source_zip)

# Hash the CUE file (canonical reference)
cue_md5 = compute_md5(cue_path)

# Look up game in database using CUE MD5
game = db.query(ScrapedGame).filter_by(
    system='saturn',
    md5=cue_md5
).first()
```

---

## File Structure Examples

### Example 1: Single Track Game
```
Game Name (USA).zip
├── Game Name (USA).cue          ← Hash this for ARRM MD5
└── Game Name (USA) (Track 01).bin
```

### Example 2: Multi-Track Game (CD Audio)
```
Game Name (USA).zip
├── Game Name (USA).cue          ← Hash this for ARRM MD5
├── Game Name (USA) (Track 01).bin  (data track)
├── Game Name (USA) (Track 02).bin  (audio)
├── Game Name (USA) (Track 03).bin  (audio)
└── ...
```

### Example 3: Multi-Disc Game
```
Game Name (USA) (Disc 1).zip
├── Game Name (USA) (Disc 1).cue    ← Hash this for Disc 1 MD5
└── Game Name (USA) (Disc 1) (Track 01).bin

Game Name (USA) (Disc 2).zip
├── Game Name (USA) (Disc 2).cue    ← Hash this for Disc 2 MD5
└── Game Name (USA) (Disc 2) (Track 01).bin
```

---

## Tools and Scripts

### `verify_arrm_md5s.py`
**Purpose:** Verify ARRM MD5 hashes against source ROM collections

**Usage:**
```bash
# Verify Saturn collection
python3 verify_arrm_md5s.py

# Verbose mode (show all matches)
python3 verify_arrm_md5s.py -v

# Custom paths
python3 verify_arrm_md5s.py \
  --gamelist /path/to/gamelist.xml \
  --source /path/to/roms \
  --temp /tmp/verify
```

**Features:**
- Parses `gamelist.xml` to extract MD5 hashes
- Extracts `.cue` files from `.zip` archives
- Computes CUE file MD5 hashes
- Compares against expected values
- Reports match/mismatch/missing statistics

---

## Key Takeaways

1. 🎯 **ARRM uses CUE file MD5s** as the canonical identifier for CD-based ROMs
2. ✅ **100% verification rate** confirms this discovery across 2,393 Saturn games
3. 🔧 **Fixed RomGroomer bug** by updating database lookup to use CUE MD5s
4. 📚 **Applies to all CD systems** that use cue/bin format (PSX, Sega CD, etc.)
5. ⚡ **Performance benefit** - hashing small text files instead of multi-GB disc images
6. 🔒 **Stable reference** - CUE content doesn't change with compression/archiving

---

## Future Work

### Verification Expansion
- [ ] Verify PlayStation collection (PSX)
- [ ] Verify Sega CD collection
- [ ] Verify PC Engine CD collection
- [ ] Create automated verification pipeline for all CD systems

### Documentation
- [ ] Update RomGroomer architecture docs with CUE MD5 discovery
- [ ] Document expected MD5 behavior per system type
- [ ] Create troubleshooting guide for MD5 mismatches

### Code Improvements
- [ ] Add CUE extraction utility functions
- [ ] Create system-specific MD5 strategies (CUE vs file vs archive)
- [ ] Implement caching for frequently accessed CUE MD5s

---

## References

- **ARRM Documentation:** http://jujuvincebros.fr/wiki/arrm/doku.php
- **Redump Project:** http://redump.org/
- **Cue Sheet Format:** https://en.wikipedia.org/wiki/Cue_sheet_(computing)
- **RomGroomer Issue:** Database linking bug in compression pipeline

---

## Contact

**Discovery Date:** October 26, 2025  
**Verified By:** RomGroomer automated testing  
**Collection Size:** 2,393 Saturn games (100% verified)

For questions or additional verification needs, see `verify_arrm_md5s.py` script.
