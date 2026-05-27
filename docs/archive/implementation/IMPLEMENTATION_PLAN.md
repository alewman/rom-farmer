# Implementation Plan - ROM Farmer Config System

## Based on Final Clarifications (2025-10-13)

### Key Decisions Made

#### 1. Multiple Targets Support
✅ **YES** - Support multiple outputs per platform in config
✅ **ALSO** - Support specialized configs like `snes-everdrive.yaml` when workflow differs significantly
✅ **Goal**: Top-level command `romfarmer build rocknix-512gb` builds entire collection

#### 2. No Transformation for No-Intro
✅ No-Intro ZIPs stay zipped (no extraction, no compression, no hash hooks)
✅ Hash pre-calc job populates HashCache, but processing doesn't use it
✅ Only Redump systems need transformation tracking

#### 3. Retool DATs
✅ Retool already does the filtering! (29K ROMs → 1.7K ROMs for NES)
✅ Our job: Parse Retool DAT, match filenames, copy matching ZIPs
✅ Retool removes bad dumps, selects best versions, applies 1G1R + language filters
✅ **Location**: `/path/to/dats/nointro.retool.1g1r.eng/`

#### 4. Stage Ordering
✅ **No-Intro**: Filter (Retool DAT) → Apply Lists → Organize → Deploy
✅ **Redump**: Filter (Retool DAT) → Extract → Apply Lists → Compress → Organize → Deploy

#### 5. Everdrive Best-Games
✅ Best-Games/ and other list subdirectories: **NOT subdivided** alphabetically
✅ Regular games: Alphabetically grouped (A-E/, F-M/, etc.)
✅ Won't have enough list games to need subdivision

#### 6. Config Scope
✅ Build **full config schema** for NES as baseline
✅ This is the foundation - get it right first

---

## DAT File Understanding

### Standard No-Intro DAT
```xml
<game name="Contra (USA)">
  <rom name="Contra (USA).nes" size="131088" crc="cba3980" .../>
</game>
<game name="Contra (Europe)">
  <rom name="Contra (Europe).nes" size="131088" crc="9df6e4f" .../>
</game>
<game name="Contra (Japan)">
  <rom name="Contra (Japan).nes" size="131088" crc="a8bf89" .../>
</game>
<!-- 5,000+ more games, all regions, all versions -->
```

**Total**: ~29,548 lines for NES

### Retool Filtered DAT (1g1r.eng)
```xml
<game name="Contra (USA)">
  <category>Games</category>
  <rom name="Contra (USA).nes" size="131088" crc="cba3980" .../>
</game>
<!-- Only 1,761 games - already filtered! -->
<!-- - One game per region group (1G1R)
     - English language priority
     - Best version selected (Rev 1 over Rev 0 if better)
     - Bad dumps removed
     - Japanese shmups included -->
```

**Total**: ~8,820 lines for NES (1,761 games)

**Our Task**: 
1. Parse Retool DAT → get list of 1,761 "good" ROM names
2. Scan Myrient source → find matching ZIPs
3. Copy matching ZIPs to filtered stage
4. Done! Retool did the hard work for us.

---

## PS3 .jb vs .sqfs

### What are these formats?

**JB Format** (`.jb` folder):
- Extracted, decrypted PS3 game structure
- Compatible with: RPCS3, Retrobat, generic PS3 emulators
- Large size (uncompressed folders)

**SquashFS** (`.sqfs` file):
- Compressed filesystem (like a compressed folder)
- Batocera-specific optimization
- Smaller size, faster loading
- Created FROM .jb folder using `mksquashfs`

### Workflow:
```
PS3 encrypted ISO (40GB)
  ↓ PS3Dec
.jb folder (38GB uncompressed)
  ↓ mksquashfs (Batocera only)
.sqfs file (22GB compressed) ← Batocera target
```

**Config Implication**:
```yaml
platforms:
  ps3:
    stages:
      - extract_archive
      - decrypt_ps3      # → .jb folder
      - compress_sqfs    # ← Only for Batocera target!
    
    outputs:
      batocera:
        format: sqfs     # Run compress_sqfs stage
      
      retrobat:
        format: jb       # Stop at .jb, skip compress_sqfs
```

---

## Space Management

✅ **User handles manually** via config choices
✅ Tool does NOT auto-calculate or auto-select platforms
✅ User explicitly enables/disables platforms in config
✅ User chooses filter strategies (usa-only vs 1g1r_eng) to control size

Example:
```yaml
# User manually controls this for 512GB build
platforms:
  nes: enabled: true      # Small, always include
  saturn: 
    enabled: true
    filter: usa_only      # Smaller than 1g1r_eng
  ps3: enabled: false     # Too large, skip
```

---

## Implementation Schedule

### Phase 1: Config System (Days 1-2)
**Goal**: Load and validate YAML configs

**Files to Create**:
```
src/romfarmer/config/
  ├── __init__.py
  ├── models.py          # Pydantic models
  ├── loader.py          # YAML loader
  ├── validator.py       # Path validation
  └── profiles.py        # Target profiles
```

**Deliverable**: Can load `config/platforms/nes.yaml` and validate it

---

### Phase 2: DAT Parser (Days 2-3)
**Goal**: Parse No-Intro and Retool DATs

**Files to Create**:
```
src/romfarmer/dat/
  ├── __init__.py
  ├── parser.py          # XML DAT parser
  ├── nointro.py         # No-Intro specific
  ├── retool.py          # Retool specific
  └── matcher.py         # Match ZIPs to DAT entries
```

**Deliverable**: Parse Retool NES DAT → list of 1,761 ROM names

---

### Phase 3: No-Intro Processing (Days 3-5)
**Goal**: Complete NES end-to-end workflow

**Files to Update**:
```
src/romfarmer/processors/stages.py
  - FilterDATStage       # Match ZIPs to Retool DAT
  - ApplyListsStage      # Handle -, +, . patterns
  - OrganizeStage        # Rich/Balanced/Minimal organization
```

**Test With**: Real NES data
- Source: `/path/to/source/No-Intro/Nintendo - NES/`
- Retool DAT: `/path/to/dats/nointro.retool.1g1r.eng/Nintendo - NES...dat`
- Lists: `/path/to/...`, `nes+Best-Games`, `nes.English-Translations`

**Deliverable**: 
- Stage 1: ~1,761 filtered ZIPs
- Stage 2: ~1,735 ZIPs (after deletes) + Best-Games/ + Translations/
- Stage 3: Organized for Batocera

---

### Phase 4: Redump/Saturn (Days 6-8)
**Goal**: Add disc system support with compression

**New Stages**:
```
src/romfarmer/processors/stages.py
  - ExtractArchiveStage  # Extract .cue + .bin from ZIP
  - CompressCHDStage     # chdman createcd
```

**Test With**: Real Saturn data
- Source: `/path/to/source/Redump/Sega - Saturn/`
- DAT: `/path/to/dats/redump.retool.1g1r.usa/Sega - Saturn...dat` (if exists)

**Deliverable**: Saturn ZIPs → extracted → CHD files

---

### Phase 5: Multiple Targets (Days 9-10)
**Goal**: Support Batocera, RocknIX, Everdrive outputs

**Organization Logic**:
- **Rich** (Batocera): Deep subdirs (language, genre, list names)
- **Balanced** (RocknIX): Alphabetical groups + list names
- **Minimal** (Everdrive): Smart alphabetical (50 files/group) + Best-Games only

**Deliverable**: Same source → 3 different target organizations

---

### Phase 6: Master Build System (Days 11-12)
**Goal**: `romfarmer build rocknix-512gb` command

**Files to Create**:
```
src/romfarmer/builder/
  ├── __init__.py
  ├── master.py          # Master build orchestrator
  ├── platform.py        # Per-platform builder
  └── targets.py         # Target-specific logic
```

**Deliverable**: Process multiple platforms from master config

---

## Current Status

✅ **Database schema** complete (ROMTransformation, HashCache)
✅ **Compression tools** ready (9 systems verified)
✅ **Hooks system** integrated
✅ **Hash pre-calc job** running (102K archives)

🚧 **Next**: Start Phase 1 - Config System

---

## Config File Structure (Final Design)

### Directory Layout
```
config/
  ├── global.yaml               # Global settings
  ├── targets/
  │   ├── rocknix-512gb.yaml   # Master build config
  │   ├── batocera-1tb.yaml
  │   └── everdrive-all.yaml
  └── platforms/
      ├── nes.yaml             # Full NES config
      ├── snes.yaml
      ├── saturn.yaml
      └── ps3.yaml
```

### Example: config/platforms/nes.yaml (Full)
```yaml
platform: nes
description: "Nintendo Entertainment System"
type: nointro

source:
  primary:
    path: /path/to/source/No-Intro/Nintendo - Nintendo Entertainment System
  extra:
    path: /path/to/source/extra/nes

lists:
  directory: /path/to/...
  files:
    - nes-delete
    - nes+Best-Games
    - nes.English-Translations

dat:
  retool:
    file: /path/to/dats/nointro.retool.1g1r.eng/Nintendo - Nintendo Entertainment System (Headered) (Parent-Clone) (20241224-130037) (Retool 2024-12-25 23-21-56) (1,761) (-n) [-AaBbcDdekMmoPrv].dat

stages:
  - filter_dat      # Match ZIPs to Retool DAT
  - apply_lists     # Delete/add from lists
  - organize        # Target-specific organization

outputs:
  batocera:
    path: /path/to/...
    organization: rich
    metadata: true
  
  rocknix:
    path: /path/to/...
    organization: balanced
    metadata: true
  
  everdrive_n8:
    path: /mnt/everdrive/nes
    organization: minimal
    metadata: false
```

### Example: config/targets/rocknix-512gb.yaml
```yaml
name: rocknix-512gb
description: "RocknIX 512GB SD Card Build"

output:
  base: /path/to/...

platforms:
  - platform: nes
    enabled: true
    target: rocknix
  
  - platform: snes
    enabled: true
    target: rocknix
  
  - platform: saturn
    enabled: true
    target: rocknix
    overrides:
      filter_strategy: usa_only  # Smaller collection
  
  - platform: ps3
    enabled: false  # Too large for 512GB
```

---

## Questions Remaining

### A. Retool DAT for Redump?
Do Retool DATs exist for Redump systems (Saturn, PSP, PS3)?

Looking at `/path/to/dats/`:
- `nointro.retool.1g1r.eng/` ✅ exists
- `redump.retool.1g1r.usa/` ⚠️ exists but only has 1 file
- `retool.redump.1g1r.eng/` ⚠️ exists but empty

**Question**: Should we use standard Redump DATs for disc systems, or do Retool versions exist?

### B. Filename Matching
How strict should ZIP filename matching be?

**Example**:
- DAT says: `Contra (USA).nes`
- Myrient has: `Contra (USA).zip` containing `Contra (USA).nes`

**Assumption**: Strip `.zip` and match the inner filename from DAT

**Confirm?**

### C. List Files with Retool
If Retool already filters to 1,761 games, and `nes-delete` has 26 pirate carts...

**Question**: Are those 26 pirate carts IN the Retool DAT? Or already filtered out by Retool?

If Retool already removed them, then `nes-delete` won't find them to delete.

**Need to verify**: Does Retool keep pirate carts in the filtered DAT?

---

## Ready to Start?

I'm ready to begin Phase 1 (Config System) unless you have more clarifications!

**Confirm**:
1. ✅ DAT understanding correct? (Parse Retool DAT, match ZIPs)
2. ✅ .jb vs .sqfs understanding correct? (Stage stops at different points per target)
3. ✅ Space management correct? (User handles manually)
4. ❓ Answer questions A, B, C above?

Let me know and I'll start building! 🚀
