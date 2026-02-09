# Arcade System Support

ROM Farmer now supports arcade ROM management for MAME-compatible emulators including:

- **FBNeo** (FinalBurn Neo) - Primary arcade emulator
- **MAME** - Comprehensive arcade/computer emulation
- **HBMAME** - Homebrew/hack focused MAME fork
- **Sega Model 2** (via model2emu)
- **Sega Model 3** (via Supermodel)
- **Sega Naomi / Naomi 2** (via Flycast)
- **Sammy Atomiswave** (via Flycast)

## Quick Start

### 1. Download ROMs

Use the included rclone script to download from Myrient:

```bash
./tools/rclone-myrient.sh
```

Enable the arcade sections in the script for:
- FBNeo arcade ROMs (non-merged)
- MAME ROMs (non-merged) 
- MAME CHDs (merged)
- HBMAME (for hacks/homebrew)

### 2. Download DATs

FBNeo DAT (auto-fetched):
```bash
curl -L -o dats/fbneo/fbneo-arcade.dat \
  "https://raw.githubusercontent.com/libretro/FBNeo/master/dats/FinalBurn%20Neo%20(ClrMame%20Pro%20XML%2C%20Arcade%20only).dat"
```

MAME DAT: Download from [ProgettoSnaps](https://www.progettosnaps.net/dats/MAME/)

### 3. Build Filtered Set

```bash
# Use the platform config
rom-farmer build --platform fbneo
```

## Filter Modes

Arcade filtering uses specialized modes to handle the complex parent/clone relationships:

### STRICT Mode
- Working games only (driver_status = good)
- One version per game (best region)
- No hacks, bootlegs, or prototypes

### RELAXED Mode (Recommended)
- Working games only
- One version per game with regional variants
- **Essential hacks** included (Rainbow Edition, etc.)
- Prototypes included
- No generic bootlegs

### COMPLETE Mode
- All working games
- Multiple regional variants
- All hacks and bootlegs
- All prototypes

### ALL Mode
- Everything in the DAT
- Includes non-working games
- Maximum coverage

## Essential Hacks

The filter recognizes culturally important bootlegs/hacks that deserve preservation:

| Game | ROM Name | Type |
|------|----------|------|
| SF2 Rainbow Edition | sf2rb, sf2rb2... | Bootleg |
| Ms. Pac-Man | mspacman | Hack (became official) |
| SF2 Koryu | sf2koryu | Hack |
| Donkey Kong Rainbow | dkrainbow | Hack |
| JoJo Rainbow | jojobanrb | Hack |

## ROM Set Types

### Non-Merged (Recommended)
Each ZIP is self-contained with all required files. Best for:
- Simplicity (no parent dependencies)
- Selective collections
- Easy file management

### Merged
Parent ZIP contains all clones. Saves space but:
- Requires understanding of parent/clone relationships
- Can't easily remove single clones

### Split
Parent and clones in separate ZIPs but share files. Not recommended.

## Platform Configs

Example FBNeo config (`config/platforms/fbneo.yaml`):

```yaml
name: fbneo
type: arcade
emulator: fbneo

dat:
  source: fbneo_official
  file: dats/fbneo/fbneo-arcade.dat

arcade_filter:
  mode: relaxed
  include_hacks: true
  include_bootlegs: false  # Only essential bootlegs
  include_prototypes: true
  include_working_only: true
  region_priority:
    - world
    - usa
    - europe
    - japan

sources:
  - path: /data/emu/source/myrient.erista.me/files/FinalBurn Neo/arcade
    type: myrient

targets:
  - name: batocera
    output_path: output/1g1r-eng-7z-batocera/fbneo
    organization:
      style: flat
    enabled: true
```

## Clone Classification

The arcade classifier identifies these clone types:

| Type | Description | Default Handling |
|------|-------------|------------------|
| **Parent** | Original version | Always included |
| **Regional** | USA, Japan, World variants | Best region selected |
| **Revision** | Version updates (r1, r2) | Latest included |
| **Bootleg** | Unauthorized copies | Excluded (except essential) |
| **Hack** | Modified versions | Essential only |
| **Prototype** | Pre-release versions | Included |
| **Homebrew** | Fan-made games | Optional |
| **Demo** | Sample versions | Excluded |
| **BIOS** | System BIOS files | Always included |

## Module Reference

### ArcadeClassifier

Classifies games by clone type and importance:

```python
from romfarmer.arcade import ArcadeClassifier

classifier = ArcadeClassifier()
classification = classifier.classify(game)

print(f"Type: {classification.clone_type}")
print(f"Importance: {classification.importance}")
print(f"Working: {classification.is_working}")
```

### ArcadeFilter

Filters DAT files using arcade-specific rules:

```python
from romfarmer.arcade import ArcadeFilter, ArcadeFilterConfig, ArcadeFilterMode

config = ArcadeFilterConfig(
    mode=ArcadeFilterMode.RELAXED,
    include_hacks=True,
    include_working_only=True,
)

arcade_filter = ArcadeFilter(config=config)
results = arcade_filter.filter_dat(dat)

selected = [r for r in results if r.selected]
```

## Statistics

Typical filter results for FBNeo v1.0.0.03:

| Metric | Count |
|--------|-------|
| Total games | 8,072 |
| Working games | 7,996 |
| Selected (RELAXED) | ~2,650 |
| Parents | ~1,770 |
| Regional variants | ~460 |
| Essential hacks | ~20 |
| Prototypes | ~120 |

## Batocera Integration

ROM Farmer targets Batocera v41:
- FBNeo 1.0.0.3
- MAME 0.268
- Flycast (Naomi/Atomiswave)
- Model2emu
- Supermodel (Model 3)

Output paths match Batocera's expected folder structure:
- `roms/fbneo/` - FBNeo arcade
- `roms/mame/` - MAME arcade  
- `roms/naomi/` - Naomi games
- `roms/atomiswave/` - Atomiswave games
- `roms/model2/` - Model 2 games
- `roms/model3/` - Model 3 games
