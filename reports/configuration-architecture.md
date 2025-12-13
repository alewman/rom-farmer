# ROM Farmer Configuration Architecture

## Executive Summary

ROM Farmer uses a **layered configuration architecture** that separates concerns across multiple levels. This document analyzes the current architecture, identifies gaps, and proposes enhancements to support target-specific capabilities.

The key insight driving this proposal:

> **Targets currently have no identity.** They exist only as names with output paths. The system cannot answer questions like "Does RocknIX support PDF manuals?" or "What folder name does RocknIX use for Sega CD?"

---

## Current Architecture

### Configuration Layers

ROM Farmer currently has **7 distinct configuration layers**:

```
┌─────────────────────────────────────────────────────────────────┐
│                         BUILD LAYER                              │
│    (1tb-batocera-complete.yaml, rocknix-512gb.yaml)             │
│    "What do I want to build?"                                    │
├─────────────────────────────────────────────────────────────────┤
│                       PLATFORM LAYER                             │
│    (saturn.yaml, ps3.yaml, nes.yaml)                            │
│    "How do I process this system?"                               │
├────────────────────────┬────────────────────────────────────────┤
│    SELECTION LAYER     │         SOURCES LAYER                  │
│  (rating-budget-40gb)  │        (sources.yaml)                  │
│  "Which games?"        │     "Where are the ROMs?"              │
├────────────────────────┴────────────────────────────────────────┤
│                        LISTS LAYER                               │
│    (saturn-delete, saturn+Best-Games)                           │
│    "Human-curated additions/exclusions"                          │
├─────────────────────────────────────────────────────────────────┤
│                      DAT PATTERNS LAYER                          │
│    (dat_patterns.yaml)                                          │
│    "How do DAT files map to platforms?"                          │
├─────────────────────────────────────────────────────────────────┤
│                    TARGET (INLINE) LAYER                         │
│    (Embedded in platform configs)                                │
│    "Where does output go? What organization style?"              │
└─────────────────────────────────────────────────────────────────┘
```

### Layer Details

#### 1. Build Layer (`config/builds/`)

The orchestration layer that defines complete builds.

```yaml
# 1tb-batocera-complete.yaml
name: 1tb-batocera-complete
includes:
  - nointro-1g1r-eng-7z-batocera
  - redump-1g1r-eng-chd-batocera
excludes:
  - 3ds  # Skip unsupported platform
platforms: []
platform_overrides: {}
```

**Responsibilities:**
- Aggregate multiple sub-builds via `includes`
- Exclude platforms via `excludes`
- Override platform settings
- Define storage paths
- Configure parallel execution
- Post-build hooks and deployment

**Current Files:** 44 build configs

---

#### 2. Platform Layer (`config/platforms/`)

Per-platform processing configuration.

```yaml
# saturn.yaml
name: saturn
dat:
  source: redump_retool_1g1r_eng
  expected_count: 318
sources:
  - path: /data/emu/roms/saturn
extraction:
  enabled: true
  type: disc
compression:
  format: chd
multi_disc_handling: true
selection:
  strategy: rating_budget
  max_size_gb: 40.0
targets:
  - name: batocera
    output_path: /data/emu/output/batocera/saturn
    organization:
      style: flat
    metadata: true
  - name: rocknix
    output_path: /data/emu/output/rocknix/saturn
    organization:
      style: balanced
```

**Responsibilities:**
- DAT file configuration
- Source ROM locations
- Extraction settings (disc, cartridge, PS3, XISO, etc.)
- Compression format and parameters
- Multi-disc handling (M3U creation)
- Selection/filtering criteria
- **Target definitions (inline)**

**Current Files:** 49 platform configs

---

#### 3. Selection Layer (`config/selections/`)

Reusable selection criteria for filtering ROMs.

```yaml
# rating-budget-40gb.yaml
name: rating-budget-40gb
strategy: rating_budget
max_size_gb: 40.0
min_rating: 0.0

# usa-10.yaml
name: usa-10
strategy: first
limit: 10
pattern:
  type: glob
  value: "*USA*"
```

**Responsibilities:**
- Selection strategy (first, random, rating_budget, etc.)
- Size limits
- Rating thresholds
- Pattern matching
- Demo/beta exclusions

**Current Files:** 6 selection configs

---

#### 4. Sources Layer (`config/sources.yaml`)

Registry of source root paths.

```yaml
roots:
  myrient_nointro: /data/emu/source/myrient.erista.me/files/No-Intro
  myrient_redump: /data/emu/source/myrient.erista.me/files/Redump
  local: /data/emu/roms
```

**Responsibilities:**
- Define named source roots
- Allow platforms to reference by name instead of hardcoding paths

---

#### 5. Lists Layer (`/data/emu/lists/`)

Human-curated game lists.

```
saturn-delete       # Games to exclude
saturn+Best-Games   # Curated best games
saturn+Translations # Fan translations
megadrive+Hacks     # ROM hacks to include
```

**Responsibilities:**
- Game-by-game curation
- Region-specific selections
- Quality filtering beyond automated methods
- Translation and hack inclusion

**Current Files:** 100+ list files across all platforms

---

#### 6. DAT Patterns Layer (`config/dat_patterns.yaml`)

Maps platform names to DAT file patterns.

```yaml
saturn: "sega - saturn"
megadrive: "sega - mega drive - genesis"
3do: "3do - 3do interactive multiplayer"
```

**Responsibilities:**
- Platform name to DAT name mapping
- Support multiple DAT naming conventions

---

#### 7. Target Layer (Inline)

Currently embedded within platform configs, not standalone.

```yaml
# Inside platform config
targets:
  - name: batocera
    output_path: /data/emu/output/batocera/saturn
    organization:
      style: flat
    metadata: true
```

**Current Responsibilities (Limited):**
- Output path
- Organization style
- Metadata generation toggle
- Compression override (optional)

**⚠️ Missing Capabilities:**
- Media type support (no manuals on RocknIX)
- Compression format support (no 7z on some targets)
- Platform support (no PS3 on RocknIX)
- Folder name mapping (megacd → segacd)
- Subfolder mapping (pspminis under psp vs standalone)

---

## Data Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                           USER REQUEST                                │
│              romfarmer build run 1tb-batocera-complete               │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         BUILD RESOLUTION                              │
│                                                                       │
│  1tb-batocera-complete                                               │
│    ├── includes: nointro-1g1r-eng-7z-batocera                       │
│    │     └── platforms: [nes, snes, gb, gbc, gba, ...]             │
│    ├── includes: redump-1g1r-eng-chd-batocera                       │
│    │     └── platforms: [psx, saturn, dreamcast, ...]              │
│    └── excludes: [3ds]                                               │
│                                                                       │
│  Result: 37 unique platforms to process                              │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    PLATFORM PROCESSING LOOP                           │
│                                                                       │
│  For each platform (e.g., saturn):                                   │
│    1. Load platform config (saturn.yaml)                             │
│    2. Apply build overrides                                          │
│    3. Load DAT file                                                  │
│    4. Apply selection filters                                        │
│    5. Apply list files (delete, add)                                 │
│    6. Execute processing stages                                      │
│    7. For each target in platform:                                   │
│       - Organize to output path                                      │
│       - Generate metadata                                            │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Current Limitations

### Problem 1: Target Capabilities Unknown

The system has no way to know what a target can or cannot do.

```python
# Current: Hardcoded check buried in metadata.py
if context.target_name == 'rocknix' and media_type == 'manual':
    continue  # Skip manuals for RocknIX
```

**Issues:**
- Hardcoded logic scattered throughout codebase
- Adding new targets requires code changes
- No validation that builds request supported features

---

### Problem 2: Platform-Target Constraints Missing

The system can't prevent impossible combinations.

```yaml
# This will fail at runtime, not at config validation:
platforms:
  - ps3
targets:
  - name: rocknix  # RocknIX can't emulate PS3!
```

**Issues:**
- No early validation
- Wasted processing time
- Confusing error messages

---

### Problem 3: Folder Name Mapping Fragmented

Different targets use different folder names.

| Internal Name | Batocera | RocknIX |
|---------------|----------|---------|
| megacd | megacd | segacd |
| pspminis | psp/pspminis | pspminis |
| snes | snes | snes |

**Current workaround:** `platform_folder_map` in build configs

```yaml
storage:
  platform_folder_map:
    rocknix:
      megacd: segacd
```

**Issues:**
- Duplicated across builds
- Not validated
- Easy to forget

---

### Problem 4: Compression Format Fallback Missing

If a target doesn't support 7z, the build will produce unusable output.

**Current:** No validation or fallback

**Needed:** Automatic fallback to best supported format

---

### Problem 5: Platform Capabilities Underutilized

The `multi_disc_handling: false` for 3DO is a platform capability, but it's not clearly structured as such.

```yaml
# 3do.yaml
multi_disc_handling: false  # 3DO can't swap discs
```

**Issues:**
- Naming doesn't clearly indicate it's a hardware limitation
- Only one capability currently tracked
- Future capabilities would need ad-hoc fields

---

## Proposed Architecture

### New Layer: Target Definitions (`config/targets/`)

Create standalone target definition files that declare capabilities and constraints.

```
config/
├── builds/         # Build orchestrations
├── platforms/      # Platform configs
├── selections/     # Selection criteria
├── sources.yaml    # Source roots
├── targets/        # NEW: Target definitions
│   ├── batocera.yaml
│   ├── rocknix.yaml
│   ├── everdrive.yaml
│   └── retrodeck.yaml
└── ...
```

---

### Target Definition Schema

```yaml
# config/targets/rocknix.yaml
name: rocknix
description: "RocknIX for handheld devices (RG35XX, RGB10, etc.)"

# ═══════════════════════════════════════════════════════════════════
# MEDIA CAPABILITIES
# What media types the frontend can display
# ═══════════════════════════════════════════════════════════════════
media_support:
  - image       # Box art, screenshots, etc.
  - mix         # Combined artwork
  - wheel       # Logo wheels
  - marquee     # Marquee images
  - video       # Video previews
  # NOT supported: manual (no PDF viewer)

# ═══════════════════════════════════════════════════════════════════
# COMPRESSION SUPPORT
# What archive/compression formats the target can read
# ═══════════════════════════════════════════════════════════════════
compression_support:
  - zip         # Universal
  - chd         # Disc images
  - cso         # PSP compressed
  - pbp         # PSP format
  # NOT supported: 7z (fallback to zip)

compression_fallback:
  7z: zip       # If 7z requested, use zip instead

# ═══════════════════════════════════════════════════════════════════
# PLATFORM SUPPORT
# What systems this target can emulate
# ═══════════════════════════════════════════════════════════════════
platform_support:
  # Explicitly list supported platforms
  - nes
  - snes
  - gb
  - gbc
  - gba
  - megadrive
  - mastersystem
  - gamegear
  - psx
  - n64
  - saturn
  - dreamcast
  # Many more...

# Unsupported platforms (for documentation/validation)
platform_unsupported:
  - ps3         # Too demanding
  - xbox360     # Not possible
  - wiiu        # Not possible
  - 3ds         # Underpowered

# ═══════════════════════════════════════════════════════════════════
# FOLDER MAPPING
# Override folder names (internal → target)
# Only list differences from internal names
# ═══════════════════════════════════════════════════════════════════
folder_mapping:
  megacd: segacd
  pspminis: pspminis      # Top-level, not under psp
  # Everything else uses internal name

# ═══════════════════════════════════════════════════════════════════
# DEFAULTS
# Default settings when building for this target
# ═══════════════════════════════════════════════════════════════════
defaults:
  organization: balanced
  metadata: true
```

```yaml
# config/targets/batocera.yaml
name: batocera
description: "Batocera for x86_64 and high-powered ARM devices"

media_support:
  - image
  - mix
  - wheel
  - marquee
  - video
  - manual      # Has PDF viewer!
  - cartridge

compression_support:
  - zip
  - 7z          # Full support
  - chd
  - cso
  - rvz
  - squashfs
  - pbp

platform_support:
  - "*"         # Supports everything

folder_mapping:
  pspminis: psp/pspminis  # Under psp folder

defaults:
  organization: flat
  metadata: true
```

---

### Enhanced Platform Capabilities

Add a `capabilities` section to platform configs for hardware limitations.

```yaml
# config/platforms/3do.yaml
name: 3do

capabilities:
  disc_swap: false    # Hardware can't swap discs → no M3U

# ... rest of config
```

```yaml
# config/platforms/saturn.yaml  
name: saturn

capabilities:
  disc_swap: true     # Saturn supports disc swapping

# ... rest of config
```

---

### Decision Matrix

With both Platform and Target capabilities defined:

```
┌────────────────────────────────────────────────────────────────────┐
│                     DECISION MATRIX                                 │
├──────────────────┬─────────────────────┬──────────────────────────┤
│ Question         │ Defined In          │ Example                  │
├──────────────────┼─────────────────────┼──────────────────────────┤
│ Can swap discs?  │ Platform capability │ 3DO: no, Saturn: yes     │
│ Show manuals?    │ Target capability   │ RocknIX: no, Batocera: yes│
│ Run this system? │ Target capability   │ RocknIX can't run PS3    │
│ Use 7z format?   │ Target capability   │ RocknIX: no → use zip    │
│ Folder name?     │ Target mapping      │ megacd → segacd          │
└──────────────────┴─────────────────────┴──────────────────────────┘
```

---

### Updated Data Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                           USER REQUEST                                │
│              romfarmer build run rocknix-512gb                       │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      TARGET VALIDATION (NEW)                          │
│                                                                       │
│  Load target definition: config/targets/rocknix.yaml                 │
│                                                                       │
│  For each requested platform:                                        │
│    ├── ps3 requested                                                 │
│    │   └── Check: rocknix.platform_support                          │
│    │       └── ❌ NOT SUPPORTED → Skip with warning                 │
│    └── saturn requested                                              │
│        └── Check: rocknix.platform_support                          │
│            └── ✅ Supported → Continue                              │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│                   COMPRESSION RESOLUTION (NEW)                        │
│                                                                       │
│  Platform requests: 7z                                               │
│  Target supports: [zip, chd, cso]                                    │
│  Fallback defined: 7z → zip                                          │
│  Result: Use zip instead of 7z                                       │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    FOLDER NAME RESOLUTION (NEW)                       │
│                                                                       │
│  Internal platform: megacd                                           │
│  Target mapping: megacd → segacd                                     │
│  Output folder: /data/emu/output/rocknix/segacd                     │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      MEDIA FILTERING (NEW)                            │
│                                                                       │
│  Available media: [image, mix, wheel, video, manual]                 │
│  Target supports: [image, mix, wheel, video]                         │
│  Result: Copy all except manual                                      │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    PLATFORM CAPABILITY CHECK                          │
│                                                                       │
│  Platform: 3do                                                       │
│  Capability: disc_swap = false                                       │
│  Result: Skip M3U creation for 3DO                                   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Priority

### Phase 1: Target Definition Files (High Priority)
Create the target definition layer with media support and platform support.

1. Create Pydantic models for target definitions
2. Create `config/targets/batocera.yaml`
3. Create `config/targets/rocknix.yaml`
4. Create target loader
5. Wire into metadata stage (replace hardcoded manual check)
6. Add platform support validation

### Phase 2: Compression Handling (Medium Priority)
Add compression support and fallback logic.

1. Add `compression_support` to target schema
2. Add `compression_fallback` mapping
3. Wire into compression stage
4. Add validation warnings

### Phase 3: Folder Mapping (Medium Priority)
Centralize folder name mapping in targets.

1. Add `folder_mapping` to target schema
2. Wire into organize stage
3. Remove `platform_folder_map` from builds
4. Migrate existing configs

### Phase 4: Platform Capabilities (Lower Priority)
Formalize platform hardware capabilities.

1. Add `capabilities` section to platform schema
2. Rename `multi_disc_handling` to `capabilities.disc_swap`
3. Migrate existing platform configs
4. Document capability patterns

---

## Benefits

### Before (Current State)

```python
# Scattered hardcoded checks
if context.target_name == 'rocknix' and media_type == 'manual':
    continue

# Duplicated folder maps in each build
platform_folder_map:
  rocknix:
    megacd: segacd

# No validation - fails at runtime
platforms:
  - ps3  # Will break on RocknIX
```

### After (Proposed State)

```yaml
# Target capabilities declared once
# config/targets/rocknix.yaml
media_support: [image, mix, wheel, video]  # No manual
platform_support: [nes, snes, psx, ...]    # No PS3
folder_mapping:
  megacd: segacd
compression_fallback:
  7z: zip
```

```python
# Clean, declarative checks
if media_type not in target_config.media_support:
    continue

# Validated at config load time
if platform not in target_config.platform_support:
    logger.warning(f"Skipping {platform} - not supported by {target}")
```

---

## Migration Path

1. **Create target files** - No breaking changes, new functionality
2. **Add validation** - Warnings only at first
3. **Wire into stages** - Replace hardcoded checks one by one
4. **Remove legacy code** - Once targets are fully integrated
5. **Update docs** - Document the new architecture

---

## Summary

The proposed architecture introduces a **first-class Target layer** that:

- **Declares capabilities** instead of scattering hardcoded checks
- **Validates early** instead of failing at runtime
- **Centralizes mappings** instead of duplicating across builds
- **Enables fallbacks** instead of producing unusable output
- **Documents constraints** as code instead of tribal knowledge

This is foundational work that will make ROM Farmer more maintainable, extensible, and user-friendly.
