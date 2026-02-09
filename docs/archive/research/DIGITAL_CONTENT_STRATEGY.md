# Digital Content & Pre-Processed Files Strategy

**Date:** October 14, 2025  
**Purpose:** Document platform-specific situations where transformation is impractical

## Overview

Some platforms have content that either:
1. **Cannot be transformed** via CLI tools (GUI-only workflows)
2. **Should not be transformed** (pre-made versions are better)
3. **Require manual installation** (not direct-loadable files)

This document outlines our strategy for these "edge cases."

---

## Platform-Specific Strategies

### 1. Wii U - Pre-Processed WUA Files ✅

**Situation:**
- Redump provides WUX (encrypted disc images)
- No-Intro provides updates/DLC separately
- Creating WUA (combined format) requires complex GUI workflow in Cemu
- No reliable CLI tools exist

**Solution: Use Pre-Made WUA Files**
```yaml
# config/platforms/wiiu.yaml
sources:
  - path: /data/emu/share/roms-batocera/wiiu/
    type: pre_processed
    note: "Pre-made WUA files from Internet Archive"

# No transformation pipeline - files already in final format!
```

**Why This Works:**
- ✅ Pre-made WUAs include base + updates + DLC
- ✅ Already tested and working
- ✅ Saves days/weeks of complex tooling research
- ✅ Batocera/Cemu support is native
- 🚫 Transformation would require GUI interaction (impractical)

**Status:** Documented in `config/platforms/wiiu.yaml` as "dead end" 🚫

---

### 2. Wii Digital (WiiWare/VC/DLC) - Manual Install 📦

**Situation:**
- No-Intro provides WiiWare, Virtual Console, DLC as WAD files
- WADs require installation (not direct-loadable)
- Installation methods:
  - Dolphin: Tools → Install WAD (GUI)
  - Real Wii: WAD Manager (CFW required)
- No practical CLI automation

**Solution: Organize + Document**
```yaml
# config/platforms/wiiware.yaml (optional)
sources:
  - path: /data/emu/archive/No-Intro/Nintendo - Wii (Digital) (CDN)/
    type: manual_install
    note: "WAD files - user must install manually in Dolphin"

# Simple pipeline: organize, add README
# User handles installation
```

**Content Types:**

| Type | Value | Recommendation |
|------|-------|----------------|
| **WiiWare** | 🟡 Medium | Provide as optional collection |
| **Virtual Console** | 🔴 Low | Skip - use native system collections |
| **DLC** | 🔴 Low | Document only - manual per game |

**Why This Approach:**
- ✅ Current Redump RVZ retail games cover main library
- ✅ WiiWare adds some exclusive digital games
- 🚫 VC is redundant (have NES/SNES/etc. separately)
- 🚫 DLC too manual, not essential
- 📝 Document installation for interested users

**Status:** Documented in `docs/WII_DIGITAL_CONTENT_STRATEGY.md`

---

### 3. PS3 PKG Files - Future Enhancement 📋

**Situation:**
- PKG files contain updates, DLC, digital games
- RPCS3 can install PKGs programmatically
- Could be automated in future

**Solution: Phase 6 Enhancement**
```python
# Future: TransformPS3Stage with PKG support
def install_pkg(base_game_folder, pkg_file):
    # Use RPCS3 CLI to install PKG to game folder
    rpcs3_cli.install_pkg(pkg_file, base_game_folder)
```

**Status:** Deferred to Phase 6+

---

## Pattern: "Manual Install" Type

For content that can't be transformed automatically:

### Config Pattern
```yaml
name: platform_name
sources:
  - path: /path/to/content/
    type: manual_install  # ← Special type
    note: "Requires manual installation in emulator"

# Simple pipeline: organize only
# Add installation instructions as README
```

### Features:
- ✅ Organizes files
- ✅ Generates metadata
- ✅ Adds installation README
- 🚫 No transformation attempted
- 📝 Clear documentation for users

---

## Decision Matrix

When encountering new platform/content:

```
Can it be transformed via CLI tools?
├─ YES → Implement transformation stage
└─ NO → Check alternatives:
    ├─ Pre-made versions available?
    │  └─ YES → Use pre-processed (Wii U WUA)
    └─ NO → Check if installation needed:
        ├─ YES → Mark as manual_install (WiiWare WAD)
        └─ NO → Document in README
```

---

## Benefits of This Approach

### 1. Realistic Expectations
- Not all content can be automated
- Document limitations clearly
- Users know what to expect

### 2. Focus on High-Value
- Automate what's practical
- Document what's possible
- Skip what's redundant

### 3. Pragmatic Solutions
- Pre-made files > complex builds
- Manual install > no access
- Documentation > broken automation

### 4. Clean Architecture
- `type: pre_processed` for WUA files
- `type: manual_install` for WAD files  
- `type: myrient` for transformable content
- Clear separation of concerns

---

## File Organization

```
config/platforms/
├── wii.yaml              # Retail RVZ (automated ✅)
├── wiiware.yaml          # Digital WAD (manual 📦)
├── wiiu.yaml             # Pre-processed WUA (documented 🚫)
└── ps3.yaml              # Multi-target (automated ✅)

docs/
├── WII_DIGITAL_CONTENT_STRATEGY.md
├── PS3_TARGETS_AND_PS3NETSRV.md
└── DIGITAL_CONTENT_STRATEGY.md (this file)
```

---

## Summary

**Core Principle:** Automate what's practical, document what's not.

### Automated (Good ROI):
- ✅ Wii retail RVZ extraction
- ✅ PS3 decryption + multi-format
- ✅ Saturn CHD compression + M3U
- ✅ GameCube RVZ extraction

### Manual/Pre-processed (Practical):
- 📦 WiiWare WAD files (manual install)
- 🚫 Wii U WUA files (use pre-made)

### Skipped (Low ROI):
- ❌ Wii Virtual Console (redundant)
- ❌ Wii DLC (too manual)

This strategy ensures:
1. **Developer time** spent on high-value automation
2. **Users** get best experience (pre-made > complex builds)
3. **Documentation** clear about limitations
4. **Architecture** clean and maintainable

**Result:** Practical, working system that handles 90% of content automatically! 🎯
