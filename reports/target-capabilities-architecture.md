# ROM Farmer Target Capabilities Architecture

## Revision History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2024-12-06 | 2.0 | Claude + User | Complete redesign: Frontend/Device/Target composition model |

---

## Executive Summary

ROM Farmer's target system is being redesigned to use a **composition model**:

```
Target = Frontend + Device + Storage
```

This enables:
- **Declarative builds** that validate constraints before processing
- **Flexible composition** - same frontend on different devices, same device with different frontends
- **Intelligent defaults** - compression, media sizing, folder structure determined by target capabilities
- **Two build modes** - Target builds (multi-system, for devices) and System builds (single platform, specialized)

---

## The Composition Model

### Core Entities

```
┌─────────────────────────────────────────────────────────────────┐
│                        TARGET CONFIG                             │
│  Composed from: Frontend + Device                               │
│  Examples: rocknix-r36s, batocera-pc, batocera-steamdeck        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌────────────────────┐    ┌────────────────────┐             │
│   │   FRONTEND CONFIG  │    │   DEVICE CONFIG    │             │
│   │                    │    │                    │             │
│   │ • Folder mapping   │    │ • Display resolution│             │
│   │ • Platform formats │    │ • CPU capability   │             │
│   │ • Media support    │    │ • Unsupported      │             │
│   │ • Emulator limits  │    │   platforms        │             │
│   │                    │    │                    │             │
│   │ Examples:          │    │ Examples:          │             │
│   │ • batocera         │    │ • r36s             │             │
│   │ • rocknix          │    │ • steamdeck        │             │
│   │ • retrodeck        │    │ • pc               │             │
│   └────────────────────┘    └────────────────────┘             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Constraint Resolution

When building for a target, constraints are resolved from both frontend and device:

| Constraint | Source | Resolution |
|------------|--------|------------|
| Platform supported? | Frontend + Device | Must be supported by BOTH |
| Compression format | Frontend | Use frontend's preferred per-platform |
| Folder names | Frontend | Use frontend's folder mapping |
| Media types | Frontend | Skip unsupported media types |
| Media sizing | Device | Scale to device resolution |
| Can run system? | Device | Skip if device CPU can't handle it |

**Example: Saturn on RocknIX-R36S**

1. Frontend (RocknIX): Saturn supported ✓, use CHD, folder = `saturn`
2. Device (R36S): Saturn supported ✓, resolution 640x480 → scale media
3. Result: Build Saturn with CHD, scale images to 320px max

**Example: PS3 on RocknIX-R36S**

1. Frontend (RocknIX): PS3 supported ✓ (it has configs for it)
2. Device (R36S): PS3 NOT supported ✗ (CPU can't emulate)
3. Result: Skip PS3 silently

---

## Configuration Structure

### Directory Layout

```
config/
├── builds/              # Build definitions (target OR system builds)
│   ├── r36s-complete.yaml
│   ├── r36s-test-10games.yaml
│   ├── pc-complete.yaml
│   ├── saturn-chd-all.yaml        # System build
│   └── fds-zip-japanese.yaml      # System build
│
├── frontends/           # Software capabilities
│   ├── batocera.yaml
│   ├── rocknix.yaml
│   └── retrodeck.yaml
│
├── devices/             # Hardware constraints
│   ├── r36s.yaml
│   ├── steamdeck.yaml
│   └── pc.yaml
│
├── targets/             # Composed frontend + device
│   ├── batocera-pc.yaml
│   ├── batocera-steamdeck.yaml
│   └── rocknix-r36s.yaml
│
├── platforms/           # Platform definitions (existing)
├── selections/          # Selection criteria (existing)
├── sources.yaml         # Source roots (existing)
└── dat_patterns.yaml    # DAT mapping (existing)
```

---

## Schema Definitions

### Frontend Config (`config/frontends/`)

```yaml
# config/frontends/batocera.yaml
name: batocera
description: "Batocera Linux - Full-featured retro gaming distribution"

# ═══════════════════════════════════════════════════════════════════
# FOLDER MAPPING
# Maps internal platform names to frontend folder names
# Only list differences from internal names
# ═══════════════════════════════════════════════════════════════════
folder_mapping:
  # CD-based systems
  megacd: megacd
  segacd: megacd           # Alias
  pcecd: pcenginecd
  
  # Subfolders
  pspminis: psp/pspminis
  
  # Most platforms use internal name (nes → nes, snes → snes)

# ═══════════════════════════════════════════════════════════════════
# MEDIA SUPPORT
# What media types the frontend can display
# ═══════════════════════════════════════════════════════════════════
media_support:
  - image       # Box art, screenshots
  - mix         # Combined artwork
  - wheel       # Logo wheels  
  - marquee     # Marquee images
  - video       # Video previews
  - manual      # PDF manuals (Batocera has PDF viewer)
  - cartridge   # 3D cartridge renders

# ═══════════════════════════════════════════════════════════════════
# PLATFORM CONFIGURATIONS
# Per-platform: supported extensions, preferred compression
# Extensions are what the frontend's emulator can open
# ═══════════════════════════════════════════════════════════════════
platforms:
  # Cartridge systems - most support compression
  nes:
    extensions: [.nes, .zip, .7z]
    preferred_compression: 7z
  
  snes:
    extensions: [.sfc, .smc, .zip, .7z]
    preferred_compression: 7z
  
  gb:
    extensions: [.gb, .zip, .7z]
    preferred_compression: 7z
  
  gba:
    extensions: [.gba, .zip, .7z]
    preferred_compression: 7z
  
  megadrive:
    extensions: [.md, .bin, .gen, .zip, .7z]
    preferred_compression: 7z
  
  n64:
    extensions: [.n64, .z64, .v64, .zip, .7z]
    preferred_compression: 7z
  
  # Disc systems - use CHD
  psx:
    extensions: [.chd, .cue, .bin, .pbp]
    preferred_compression: chd
  
  saturn:
    extensions: [.chd, .cue, .bin]
    preferred_compression: chd
  
  dreamcast:
    extensions: [.chd, .gdi, .cdi]
    preferred_compression: chd
  
  ps2:
    extensions: [.chd, .iso, .cso]
    preferred_compression: chd
  
  gamecube:
    extensions: [.rvz, .iso, .gcz]
    preferred_compression: rvz
  
  wii:
    extensions: [.rvz, .iso, .wbfs]
    preferred_compression: rvz
  
  # Handhelds
  psp:
    extensions: [.iso, .cso, .pbp]
    preferred_compression: cso
  
  3ds:
    extensions: [.3ds, .3dsx, .cia, .cxi]
    preferred_compression: none    # Citra can't decompress
  
  nds:
    extensions: [.nds, .zip, .7z]
    preferred_compression: 7z
  
  # Special systems
  ps3:
    extensions: [folder]           # PS3 uses folder structure
    preferred_compression: none

# ═══════════════════════════════════════════════════════════════════
# GLOBAL COMPRESSION FALLBACK
# If a format isn't supported, fall back to these
# ═══════════════════════════════════════════════════════════════════
compression_fallback:
  7z: zip                          # If 7z not supported, use zip

# ═══════════════════════════════════════════════════════════════════
# DEFAULTS
# ═══════════════════════════════════════════════════════════════════
defaults:
  organization: flat
  metadata: true
```

```yaml
# config/frontends/rocknix.yaml
name: rocknix
description: "RocknIX - Lightweight distribution for handheld devices"

folder_mapping:
  megacd: segacd           # RocknIX uses "segacd" not "megacd"
  pcecd: pcenginecd
  pspminis: pspminis       # Top-level, not under psp

media_support:
  - image
  - mix  
  - wheel
  - marquee
  - video
  # NO manual - no PDF viewer

platforms:
  # Cartridge systems
  nes:
    extensions: [.nes, .zip]       # No 7z support
    preferred_compression: zip
  
  snes:
    extensions: [.sfc, .smc, .zip]
    preferred_compression: zip
  
  gb:
    extensions: [.gb, .zip]
    preferred_compression: zip
  
  gba:
    extensions: [.gba, .zip]
    preferred_compression: zip
  
  # Disc systems
  psx:
    extensions: [.chd, .pbp]
    preferred_compression: chd
  
  saturn:
    extensions: [.chd]
    preferred_compression: chd
  
  # 3DS - same limitation (Citra)
  3ds:
    extensions: [.3ds, .3dsx, .cia]
    preferred_compression: none

compression_fallback:
  7z: zip

defaults:
  organization: balanced
  metadata: true
```

---

### Device Config (`config/devices/`)

```yaml
# config/devices/r36s.yaml
name: r36s
description: "R36S handheld - RK3326 chipset"

# ═══════════════════════════════════════════════════════════════════
# DISPLAY
# ═══════════════════════════════════════════════════════════════════
display:
  resolution: [640, 480]
  aspect_ratio: "4:3"

# ═══════════════════════════════════════════════════════════════════
# MEDIA SIZING
# Optimal media dimensions for this device
# Prevents wasting storage on oversized images
# ═══════════════════════════════════════════════════════════════════
media_sizing:
  max_image_width: 320             # Downscale images larger than this
  max_image_height: 240
  video_max_resolution: 480p
  video_max_bitrate_kbps: 1500

# ═══════════════════════════════════════════════════════════════════
# UNSUPPORTED PLATFORMS
# Systems this device's CPU cannot emulate adequately
# Discovered through testing - start empty, add as you discover
# ═══════════════════════════════════════════════════════════════════
unsupported_platforms:
  - ps2        # Way too demanding
  - ps3        # Impossible
  - xbox       # Too demanding
  - xbox360    # Impossible
  - gamecube   # Too demanding (test first!)
  - wii        # Too demanding
  - wiiu       # Impossible
  - switch     # Impossible
  # - n64      # Actually works for most games
  # - psp      # Works for most games
  # - saturn   # Works but some games struggle
```

```yaml
# config/devices/steamdeck.yaml
name: steamdeck
description: "Steam Deck - AMD APU, x86_64"

display:
  resolution: [1280, 800]
  aspect_ratio: "16:10"

media_sizing:
  max_image_width: 640
  max_image_height: 480
  video_max_resolution: 720p
  video_max_bitrate_kbps: 3000

unsupported_platforms:
  # Steam Deck can run almost everything
  - switch     # Needs more work, borderline
```

```yaml
# config/devices/pc.yaml
name: pc
description: "Desktop PC - No hardware constraints"

display:
  resolution: [1920, 1080]
  aspect_ratio: "16:9"

media_sizing:
  max_image_width: 1024
  max_image_height: 768
  video_max_resolution: 1080p
  video_max_bitrate_kbps: 5000

unsupported_platforms: []          # PC can run everything
```

---

### Target Config (`config/targets/`)

Targets compose a frontend and device:

```yaml
# config/targets/rocknix-r36s.yaml
name: rocknix-r36s
description: "RocknIX on R36S handheld"

frontend: rocknix
device: r36s

# Optional: target-specific overrides
overrides:
  # Override frontend/device defaults if needed
  # platforms:
  #   n64:
  #     enabled: false  # Disable even though device supports it
```

```yaml
# config/targets/batocera-pc.yaml
name: batocera-pc
description: "Batocera on desktop PC"

frontend: batocera
device: pc
```

```yaml
# config/targets/batocera-steamdeck.yaml
name: batocera-steamdeck
description: "Batocera on Steam Deck"

frontend: batocera
device: steamdeck
```

---

### Build Configs (`config/builds/`)

#### Target Builds (Multi-System)

```yaml
# config/builds/r36s-complete.yaml
name: r36s-complete
description: "Complete build for R36S with 512GB storage"

# Build type: target (multi-system, for a device)
type: target

target: rocknix-r36s
storage_budget: 512gb
profile: complete

# Platform selection
platforms: all                     # All supported platforms

# Platform-specific budgets for large libraries
platform_budgets:
  3ds: 50gb
  psx: 80gb
  ps2: 0gb                         # Skip (device can't run it anyway)
  # NoIntro platforms: no limit (they all fit)

# Selection defaults
selection_defaults:
  strategy: rating_budget
  min_rating: 0.5
```

```yaml
# config/builds/r36s-test-10games.yaml
name: r36s-test-10games
description: "Test build - 10 games per system for hardware testing"

type: target

target: rocknix-r36s
storage_budget: 512gb
profile: test-10games

platforms: all

# Override selection for testing
selection_override:
  strategy: first
  limit: 10
```

```yaml
# config/builds/pc-complete.yaml
name: pc-complete
description: "Complete build for Batocera PC - unlimited storage"

type: target

target: batocera-pc
storage_budget: unlimited
profile: complete

platforms: all

selection_defaults:
  strategy: all                    # Keep everything
```

#### System Builds (Single Platform)

```yaml
# config/builds/saturn-chd-all.yaml
name: saturn-chd-all
description: "All Saturn games in CHD format"

# Build type: system (single platform)
type: system

platform: saturn
compression: chd
selection: all

# Output: output/saturn-chd-all/
```

```yaml
# config/builds/fds-zip-japanese.yaml
name: fds-zip-japanese
description: "Japanese Famicom Disk System collection"

type: system

platform: fds
compression: zip
selection: japanese

# Output: output/fds-zip-japanese/
```

---

## Output Folder Naming

### Target Builds

Output folder is automatically computed:

```
{frontend}-{device}-{storage}-{profile}/
```

Examples:
- `rocknix-r36s-512gb-complete/`
- `rocknix-r36s-512gb-test-10games/`
- `batocera-pc-unlimited-complete/`
- `batocera-steamdeck-1tb-favorites/`

Inside, the folder structure matches the frontend:
```
rocknix-r36s-512gb-complete/
├── roms/
│   ├── nes/
│   ├── snes/
│   ├── segacd/              # RocknIX folder name
│   └── ...
└── images/                   # If metadata enabled
```

### System Builds

Output folder includes compression:

```
{platform}-{compression}-{selection}/
```

Examples:
- `saturn-chd-all/`
- `fds-zip-japanese/`
- `nes-7z-top30/`

---

## Validation Rules

When a build is loaded, ROM Farmer validates:

### Target Build Validation

1. **Target exists** - `targets/{target}.yaml` must exist
2. **Frontend exists** - Referenced frontend config must exist
3. **Device exists** - Referenced device config must exist
4. **Platforms supported** - Each requested platform must be:
   - Supported by frontend (has platform config)
   - Supported by device (not in `unsupported_platforms`)
5. **Storage reasonable** - Estimated size should fit in budget

### System Build Validation

1. **Platform exists** - Platform config must exist
2. **Compression valid** - Must be a known format
3. **Selection exists** - Selection config must exist or be inline

### Validation Actions

| Validation Failure | Action |
|-------------------|--------|
| Platform unsupported by device | Skip silently |
| Platform unsupported by frontend | Error |
| Compression unsupported | Fall back to supported format |
| Media type unsupported | Skip that media type |
| Target doesn't exist | Error |

---

## Processing Pipeline

### Target Build Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  romfarmer build run r36s-complete                              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. LOAD BUILD CONFIG                                            │
│     builds/r36s-complete.yaml                                   │
│     → target: rocknix-r36s, storage: 512gb, profile: complete   │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. LOAD TARGET CONFIG (composed)                                │
│     targets/rocknix-r36s.yaml                                   │
│     → frontend: rocknix, device: r36s                           │
│                                                                  │
│     Load frontends/rocknix.yaml                                 │
│     → folder_mapping, media_support, platform formats           │
│                                                                  │
│     Load devices/r36s.yaml                                      │
│     → display, media_sizing, unsupported_platforms              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. RESOLVE PLATFORMS                                            │
│     Requested: all                                               │
│     Frontend supports: [nes, snes, psx, saturn, ps2, ...]       │
│     Device unsupported: [ps2, ps3, gamecube, ...]               │
│                                                                  │
│     Result: [nes, snes, psx, saturn, n64, psp, ...]             │
│             (intersection of supported - unsupported)            │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. FOR EACH PLATFORM                                            │
│                                                                  │
│     saturn:                                                      │
│     ├── Get compression: frontend.platforms.saturn.preferred    │
│     │   → chd                                                   │
│     ├── Get folder: frontend.folder_mapping.saturn              │
│     │   → "saturn"                                              │
│     ├── Get extensions: frontend.platforms.saturn.extensions    │
│     │   → [.chd]                                                │
│     ├── Get selection: build.selection_defaults                 │
│     │   → rating_budget, budget from platform_budgets           │
│     └── Process platform...                                     │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. ORGANIZE OUTPUT                                              │
│                                                                  │
│     Output folder: output/rocknix-r36s-512gb-complete/          │
│     Structure:                                                   │
│     └── roms/                                                   │
│         ├── nes/                                                │
│         ├── snes/                                               │
│         ├── saturn/                                             │
│         └── ...                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Migration from Current System

### Current State

- Targets are inline in platform configs
- Folder mapping is in build configs (`platform_folder_map`)
- Media filtering is hardcoded (`if target == 'rocknix' and media == 'manual'`)
- No device concept
- No validation

### Migration Steps

1. **Create frontend configs** - Extract from current inline targets
2. **Create device configs** - New concept, start with known devices
3. **Create target configs** - Compose frontend + device
4. **Update build configs** - Reference targets, add storage/profile
5. **Wire into pipeline** - Load composed configs, use for decisions
6. **Remove legacy code** - Delete hardcoded checks, inline targets

### Backwards Compatibility

**Not supported.** This is a fundamental architecture change. Existing build configs will need migration. Since this is a personal project in active development, maintaining backwards compatibility would add complexity without benefit.

---

## Implementation Plan

See separate document: `reports/implementation-plan.md`

---

## Benefits Summary

| Before | After |
|--------|-------|
| Targets have no identity | Targets are composed from Frontend + Device |
| Hardcoded media filtering | Declarative media_support in frontend |
| Folder mapping duplicated in builds | Centralized in frontend config |
| No device awareness | Device defines CPU limits, display resolution |
| No validation | Validate platforms, compression, storage at build time |
| Output folders inconsistent | Computed: `{frontend}-{device}-{storage}-{profile}/` |
| One build type | Target builds (multi-system) + System builds (single) |
| No storage budgets | Per-platform budgets for large libraries |

---

## Appendix: Example Complete Configs

### Full Example: R36S Build

```yaml
# === frontends/rocknix.yaml (excerpt) ===
name: rocknix
folder_mapping:
  megacd: segacd
media_support: [image, mix, wheel, video]
platforms:
  saturn:
    extensions: [.chd]
    preferred_compression: chd

# === devices/r36s.yaml ===
name: r36s
display:
  resolution: [640, 480]
media_sizing:
  max_image_width: 320
unsupported_platforms: [ps2, ps3, gamecube, wii]

# === targets/rocknix-r36s.yaml ===
name: rocknix-r36s
frontend: rocknix
device: r36s

# === builds/r36s-complete.yaml ===
name: r36s-complete
type: target
target: rocknix-r36s
storage_budget: 512gb
profile: complete
platforms: all
platform_budgets:
  psx: 80gb
  3ds: 50gb
```

**Result:**
- Output folder: `output/rocknix-r36s-512gb-complete/`
- Saturn: CHD format, `roms/saturn/` folder
- Media: Images scaled to 320px max, no manuals
- PS2/PS3: Skipped (device can't run)
- PSX: Best 80GB by rating
