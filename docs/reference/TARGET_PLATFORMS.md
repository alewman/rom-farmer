# Target Platform Capabilities

This document defines what each target platform supports, guiding our build configurations.

## Target Platforms Overview

| Target | Type | Primary Use | UI Quality | Storage |
|--------|------|-------------|------------|---------|
| Batocera | Full Linux | Home theater PC, dedicated cabinets | Excellent (EmulationStation) | Large (HDD/SSD) |
| RocknIX | Embedded Linux | Handheld consoles (Anbernic, Powkiddy) | Good (EmulationStation) | Medium (SD card) |
| RetroPie | Raspberry Pi | DIY builds, Pi systems | Good (EmulationStation) | Medium (SD card) |
| Recalbox | Full Linux | Simplified setup | Good (EmulationStation) | Medium |
| Everdrive | Cartridge | Real hardware flash carts | None (console menu) | Small (SD card) |

---

## Batocera

**Homepage:** https://batocera.org/  
**Target Device:** x86_64 PCs, ARM SBCs  
**EmulationStation:** Yes (enhanced fork)

### System Name Conventions
```
saturn          ✅
segacd          ✅ (NOT megacd)
pcenginecd      ✅
dreamcast       ✅
nes             ✅
snes            ✅
genesis         ✅
n64             ✅
ps1             ✅
ps2             ✅
ps3             ✅
gamecube        ✅
wii             ✅
```

### Metadata Support
**gamelist.xml Fields:**
- ✅ `name` - Game title
- ✅ `desc` - Full description (unlimited length)
- ✅ `developer` - Developer name
- ✅ `publisher` - Publisher name
- ✅ `genre` - Genre categories
- ✅ `releasedate` - YYYYMMDDTHHMMSS format
- ✅ `players` - Player count (e.g., "1-4")
- ✅ `rating` - 0.0-1.0 scale
- ✅ `region` - Region code
- ✅ `lang` - Language codes

**Media Types:**
- ✅ `image` - Title screen (PNG/JPG)
- ✅ `wheel` - Logo wheel art
- ✅ `marquee` - Arcade marquee
- ✅ `boxart` - Box art (displayed)
- ✅ `screenshot` - In-game screenshot
- ✅ `video` - MP4 preview videos
- ✅ `manual` - PDF manuals (viewable in UI)
- ✅ `cartridge` - Cartridge/disc art
- ✅ `mix` - Composite images

### Organization
- **Preferred:** Flat (single directory per system)
- **Reason:** EmulationStation has excellent filtering/search
- **Max files per directory:** Unlimited (tested with 10,000+)
- **Subdirectories:** Supported but not necessary

### File Formats
| System | Preferred | Alternate | Notes |
|--------|-----------|-----------|-------|
| Saturn | CHD | CUE/BIN | CHD strongly preferred |
| Sega CD | CHD | CUE/BIN | CHD strongly preferred |
| Dreamcast | CHD | CUE/GDI | GDI for rare cases |
| PS1 | CHD | CUE/BIN | CHD strongly preferred |
| N64 | Z64 | N64, V64 | Big-endian preferred |
| NES | NES | ZIP | Uncompressed |
| SNES | SFC | SMC, ZIP | SFC preferred |

---

## RocknIX

**Homepage:** https://rocknix.org/  
**Target Device:** Anbernic RG*, Powkiddy X55, Retroid Pocket  
**EmulationStation:** Yes

### System Name Conventions
```
saturn          ✅
segacd          ✅
tg16cd          ✅ (NOT pcenginecd)
dreamcast       ✅
nes             ✅
snes            ✅
genesis         ✅
n64             ✅
psx             ✅ (NOT ps1)
```

### Metadata Support
**gamelist.xml Fields:**
- ✅ `name`
- ✅ `desc` - **Limited to ~500 chars** (small screen)
- ✅ `developer`
- ✅ `publisher`
- ✅ `genre`
- ✅ `releasedate`
- ✅ `players`
- ✅ `rating`
- ❌ `region` - Not displayed
- ❌ `lang` - Not displayed

**Media Types:**
- ✅ `image` - Title screen
- ✅ `wheel` - Logo wheel
- ✅ `marquee` - Marquee art
- ⚠️ `video` - Supported but **drains battery**
- ❌ `manual` - **Not supported** (no PDF viewer)
- ✅ `screenshot` - Screenshot

### Organization
- **Preferred:** Balanced (alphabetical grouping: A-D, E-H, etc.)
- **Reason:** SD card performance on handheld
- **Max files per directory:** ~100-200 recommended
- **Subdirectories:** Strongly recommended for 200+ games

### File Formats
| System | Preferred | Notes |
|--------|-----------|-------|
| Saturn | CHD | Only format supported |
| Sega CD | CHD | Only format supported |
| PS1 | CHD | Only format supported |
| N64 | Z64 | No ZIP support |
| NES | NES | Uncompressed only |

---

## RetroPie

**Homepage:** https://retropie.org.uk/  
**Target Device:** Raspberry Pi 3/4/5  
**EmulationStation:** Yes

### System Name Conventions
```
saturn          ✅
segacd          ✅
pcenginecd      ✅
dreamcast       ✅
nes             ✅
snes            ✅
megadrive       ✅ (NOT genesis)
n64             ✅
psx             ✅
```

### Metadata Support
**gamelist.xml Fields:**
- ✅ `name`
- ✅ `desc`
- ✅ `developer`
- ✅ `publisher`
- ✅ `genre`
- ✅ `releasedate`
- ✅ `players`
- ✅ `rating`
- ⚠️ `image` - Required, others optional

**Media Types:**
- ✅ `image`
- ✅ `marquee`
- ⚠️ `video` - Heavy on Pi 3/4
- ❌ `manual` - No built-in viewer

### Organization
- **Preferred:** Flat
- **Max files per directory:** ~500 recommended
- **Notes:** Pi 3/4 can lag with 1000+ files

---

## Everdrive (Cartridge Mode)

**Type:** Flash cartridge for real hardware  
**Examples:** Everdrive N8, Everdrive GBA, Mega Everdrive Pro  
**UI:** On-cart menu system

### System Name Conventions
- N/A (uses real hardware)

### Metadata Support
- ❌ **None** - Filename only
- Some models show: filename, size, date

### Organization
- **Required:** Folders (hardware limitation)
- **Max files per directory:** **50** (Everdrive N8)
- **Max files per directory:** **100** (Mega Everdrive Pro)
- **Naming:** Short filenames preferred (8.3 on older models)
- **Structure:** Must use Sort2Folders or similar

### File Formats
| System | Format | Notes |
|--------|--------|-------|
| NES | NES | No headers, no ZIP |
| SNES | SFC/SMC | Must be correct format |
| Genesis | MD/BIN | Must match region |
| GBA | GBA | No compression |

---

## Recalbox

**Homepage:** https://www.recalbox.com/  
**Target Device:** x86, Pi, ARM  
**EmulationStation:** Yes

### System Name Conventions
```
saturn          ✅
segacd          ✅
pcenginecd      ✅
dreamcast       ✅
```

### Metadata Support
- Similar to RetroPie
- `gamelist.xml` standard format
- Media support varies by version

---

## Implementation Recommendations

### Per-Target Profiles

Create these configuration profiles:

```yaml
# config/target_profiles/batocera.yaml
name: batocera
capabilities:
  metadata:
    fields: [name, desc, developer, publisher, genre, releasedate, players, rating, region, lang]
    media: [image, wheel, marquee, video, manual, boxart, screenshot, cartridge, mix]
  organization:
    preferred_style: flat
    max_files_flat: 10000
  file_formats:
    saturn: [chd]
    segacd: [chd]
    pcenginecd: [chd]

# config/target_profiles/rocknix.yaml
name: rocknix
capabilities:
  metadata:
    fields: [name, desc, developer, publisher, genre, releasedate, players, rating]
    media: [image, wheel, marquee, screenshot]
    desc_max_length: 500
  organization:
    preferred_style: balanced
    max_files_per_dir: 150
  file_formats:
    saturn: [chd]
    segacd: [chd]
    tg16cd: [chd]
  system_aliases:
    pcenginecd: tg16cd
    psx: ps1

# config/target_profiles/everdrive.yaml
name: everdrive
capabilities:
  metadata:
    fields: []
    media: []
  organization:
    preferred_style: minimal
    max_files_per_dir: 50
    naming_convention: short
  file_formats:
    nes: [nes]
    snes: [sfc]
```

### Next Steps

1. ✅ Document target capabilities (this file)
2. 🔨 Create target profile YAML configs
3. 🔨 Update metadata stage to respect target profiles
4. 🔨 Update organize stage to enforce file limits
5. 🔨 Add system name aliasing per target
6. 🔨 Test Saturn build for Batocera + RocknIX

---

## Research Needed

- [ ] Verify RocknIX manual support (may have changed)
- [ ] Test Batocera performance with 10,000+ files
- [ ] Document RetroArch netplay metadata requirements
- [ ] Check if newer Everdrives support metadata
- [ ] Verify MiSTer system names and capabilities
