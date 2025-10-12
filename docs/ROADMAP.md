# ROM Groomer - Implementation Roadmap

## Current Status: Phase 0, 1, 2a, 2b Complete ✅

```
┌─────────────────────────────────────────────────────────────────────┐
│                    IMPLEMENTATION PROGRESS                          │
├─────────────────────────────────────────────────────────────────────┤
│ ✅ Phase 0: Project Structure (100%)                                │
│ ✅ Phase 1: Core Infrastructure (100%)                              │
│    ├─ Logging System                                                │
│    ├─ Configuration System                                          │
│    ├─ Database Models                                               │
│    ├─ ROM Models                                                    │
│    ├─ No-Intro Parser                                               │
│    ├─ Redump Parser                                                 │
│    └─ CLI Framework                                                 │
│ ✅ Phase 2a: Processor Framework (100%)                             │
│    ├─ Base Processor Classes                                        │
│    ├─ Pipeline Processor                                            │
│    ├─ Platform Profiles (11 systems)                                │
│    └─ Extract Archive Stage                                         │
│ ✅ Phase 2b: Disc Processing (100%)                                 │
│    ├─ BinCueToChd Stage                                             │
│    ├─ CreateM3uPlaylist Stage                                       │
│    └─ Updated Disc Profiles                                         │
│ ⏳ Phase 2c: Advanced Workflows (0%)                                │
│ ⏳ Phase 3: Organization Engine (0%)                                │
│ ⏳ Phase 4: DAT Processing (0%)                                     │
│ ⏳ Phase 5: ROM Scanning (0%)                                       │
│ ⏳ Phase 6: Validation System (0%)                                  │
│ ⏳ Phase 7: Scraping & Metadata (0%)                                │
└─────────────────────────────────────────────────────────────────────┘
```

## What to Build Next?

### Option A: Complete Phase 2 (Advanced Processing)
**Focus**: PS3, Xbox 360, Wii U decryption workflows

**Pros:**
- Completes the processing pipeline
- Handles advanced systems
- Useful for modern emulation

**Cons:**
- More complex (requires external tools)
- Not everyone needs these systems
- Can be added later

**Implementation:**
- PS3DecryptStage + PS3ToSquashFS
- Xbox360DecryptStage
- WiiUDecryptStage
- IsoToCso (PSP compression)
- Advanced profiles

---

### Option B: Organization Engine (Phase 3)
**Focus**: Organize processed ROMs by region, kind, language

**Pros:**
- High user value (everyone needs organization)
- Builds on existing parsers
- Relatively straightforward

**Cons:**
- Requires DAT database to be useful
- Best with validation

**Implementation:**
- RegionOrganizer
- KindOrganizer
- LanguageOrganizer
- FilterConfig (1G1R support)
- Symlink/copy strategies

---

### Option C: DAT Processing (Phase 4)
**Focus**: Parse XML DAT files, populate database

**Pros:**
- Foundation for validation and organization
- Enables hash verification
- Required for completeness checking

**Cons:**
- XML parsing can be tedious
- Large DAT files (performance considerations)

**Implementation:**
- XML DAT parser (Logiqx format)
- DAT database schema
- DAT import commands
- Filter generation (1G1R, region, language)

---

### Option D: ROM Scanning (Phase 5)
**Focus**: Scan directories, hash files, match against DATs

**Pros:**
- Enables validation
- Collection inventory
- Missing game detection

**Cons:**
- Requires DAT database
- Hashing can be slow for large collections

**Implementation:**
- Directory scanner
- Hash calculator (CRC32, MD5, SHA1)
- DAT matcher
- Collection statistics
- Missing game reports

---

## Recommended Order

Based on user value and dependencies:

### **Priority 1: Organization Engine (Phase 3)** 🥇
- Most immediate value
- Works with what we have
- Can use basic filtering without DAT database initially

### **Priority 2: DAT Processing (Phase 4)** 🥈
- Enables advanced organization
- Required for validation
- Foundation for hash verification

### **Priority 3: ROM Scanning (Phase 5)** 🥉
- Completes the inventory system
- Enables validation
- Collection reporting

### **Priority 4: Validation System (Phase 6)**
- Hash verification
- Completeness checking
- Duplicate detection

### **Priority 5: Advanced Processing (Phase 2c)**
- PS3/Xbox360/Wii U support
- For advanced users
- Can be added anytime

### **Priority 6: Scraping & Metadata (Phase 7)**
- Final polish
- EmulationStation integration
- Nice-to-have

---

## Implementation Plan

### Milestone 1: Basic Organization (Week 1)
```
✅ Phase 0 & 1 Complete
✅ Phase 2a & 2b Complete
→ Phase 3: Organization Engine
  ├─ RegionOrganizer (organize by region)
  ├─ KindOrganizer (organize by kind)
  ├─ LanguageOrganizer (organize by language)
  ├─ FilterConfig (basic filtering)
  └─ CLI commands (romgroomer organize)
```

**Deliverable**: Can organize processed ROMs by region/kind/language

### Milestone 2: DAT Database (Week 2)
```
→ Phase 4: DAT Processing
  ├─ XML DAT parser
  ├─ DAT database models
  ├─ DAT import commands
  ├─ Filter generation
  └─ DAT statistics
```

**Deliverable**: Can import DAT files and query game database

### Milestone 3: Collection Inventory (Week 3)
```
→ Phase 5: ROM Scanning
  ├─ Directory scanner
  ├─ Hash calculator
  ├─ DAT matcher
  ├─ Collection statistics
  └─ Missing game reports
```

**Deliverable**: Complete collection inventory and reporting

### Milestone 4: Validation (Week 4)
```
→ Phase 6: Validation System
  ├─ Hash validator
  ├─ Collection validator
  ├─ Duplicate detector
  ├─ Integrity checker
  └─ Validation reports
```

**Deliverable**: Full validation and verification system

### Milestone 5: Advanced Features (Week 5+)
```
→ Phase 2c: Advanced Processing (PS3, Xbox360, Wii U)
→ Phase 7: Scraping & Metadata
```

**Deliverable**: Complete feature set

---

## Feature Dependency Graph

```
┌──────────────────┐
│ Phase 0 & 1      │
│ (Foundation)     │
└────────┬─────────┘
         │
         ├─────────────────────────────┐
         │                             │
         ▼                             ▼
┌──────────────────┐         ┌──────────────────┐
│ Phase 2a & 2b    │         │ Phase 4          │
│ (Processing)     │         │ (DAT Processing) │
└────────┬─────────┘         └────────┬─────────┘
         │                             │
         │                             │
         ├─────────────┬───────────────┤
         │             │               │
         ▼             ▼               ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Phase 3          │ │ Phase 5          │ │ Phase 6          │
│ (Organization)   │ │ (ROM Scanning)   │ │ (Validation)     │
└────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
         │                     │                     │
         │                     │                     │
         └─────────────────────┴─────────────────────┘
                               │
                               ▼
                    ┌──────────────────┐
                    │ Phase 7          │
                    │ (Scraping)       │
                    └──────────────────┘
```

**Key:**
- **No dependencies**: Phase 0, 1 (done), Phase 4
- **Light dependencies**: Phase 2a/b (done), Phase 3
- **Heavy dependencies**: Phase 5, 6, 7

---

## What Should We Build First?

Based on the workflow and dependencies, I recommend:

### **Start with Phase 3: Organization Engine** 🎯

**Why:**
1. **Immediate value**: Users can organize their processed ROMs right now
2. **Low complexity**: Builds on existing parsers and models
3. **Independent**: Doesn't require DAT database (can use basic filtering)
4. **Demonstrates value**: Shows the system working end-to-end

**What we'll build:**
```python
# RegionOrganizer
organizer = RegionOrganizer(
    region_priority=['usa', 'europe', 'japan'],
    use_symlinks=True
)
organizer.organize(
    source_dir=Path("/roms/processed/nes/"),
    dest_dir=Path("/roms/organized/by-region/")
)

# Result:
# /roms/organized/by-region/usa/nes/
# /roms/organized/by-region/europe/nes/
# /roms/organized/by-region/japan/nes/
```

**Tests we'll write:**
- Organize by region (USA, Europe, Japan)
- Organize by kind (Games, Demos, Applications)
- Organize by language (English, Japanese, etc.)
- Symlink vs copy strategies
- Filter configurations
- Multi-region ROM handling

**User commands:**
```bash
romgroomer organize --system nes --by region
romgroomer organize --system psx --by kind
romgroomer organize --batch --all-systems --by region
```

---

## Decision Time! 🎲

What should we build next?

**A)** Phase 3: Organization Engine (recommended)
**B)** Phase 4: DAT Processing
**C)** Phase 2c: Advanced Processing (PS3, Xbox360, Wii U)
**D)** Something else?

I'm ready to implement whichever you choose! 💪
