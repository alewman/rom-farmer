# Cross-Platform Generation Deduplication (1G1Gen)

## Overview

The **1 Game 1 Generation** (1G1Gen) feature implements cross-platform deduplication for disc-based console systems. When enabled, games that appear on multiple platforms in the same console generation are deduplicated based on platform priority, significantly reducing storage requirements while preserving platform exclusives.

## Problem it Solves

For multi-platform console generations, many games were released on multiple systems:
- **Grand Theft Auto: Vice City** (PS2, Xbox, GameCube) - Same game, 3x space
- **Tony Hawk Pro Skater** series (multiple versions across platforms)
- **FIFA, NBA, NHL** sports titles (annual releases on all platforms)

Without deduplication, you end up with:
- 3 versions of the same game taking up 8-12 GB
- 600+ duplicate games in Gen 6 alone
- Massive storage waste on space-constrained devices

With 1G1Gen:
- Keep the **best version** (highest priority platform)
- Lower priority platforms become **"exclusives only"**
- **30-50% space savings** per generation

## Supported Generations

All disc-based systems are supported (cartridge/handheld systems excluded):

### Gen 4 CD (1988-1996)
- **Priority**: Sega CD > PCEngine CD > Neo Geo CD
- Small libraries (~200-500 games each), minimal overlap

### Gen 5 (1993-2005) 
- **Priority**: PSX > Saturn
- Expected savings: 15-20% (~100-120 duplicate games)

### Gen 6 (1998-2013)
- **Priority**: PS2 > GameCube > Xbox > Dreamcast
- Expected savings: 40-50% (~600-800 duplicate games)
- **Biggest space savings generation**

### Gen 7 (2005-2017)
- **Priority**: PS3 > Xbox 360 > Wii
- Expected savings: 30-40% (~400-600 duplicate games)
- Games are large (5-15 GB each), huge total savings

## How It Works

### 1. Per-Platform 1G1R Filtering (Existing)
Each platform is processed independently first:
```
PSX:    Extract → Filter 1G1R → CHD → output/gen5-dedupe-batocera/psx/    (1,798 games)
Saturn: Extract → Filter 1G1R → CHD → output/gen5-dedupe-batocera/saturn/ (318 games)
```

### 2. Game Name Normalization
Games are matched across platforms by normalizing names:
```
Original names:
- "Grand Theft Auto - Vice City (USA)"                      [PS2]
- "Grand Theft Auto - Vice City (USA) (En,Fr,De,Es,It)"    [Xbox]
  
Normalized:
- "Grand Theft Auto Vice City" | USA → Match! Same game
```

Normalization handles:
- Region markers: (USA), (Europe), (Japan), (World)
- Language markers: (En,Fr,De)
- Revision markers: (Rev 1), (v1.1)
- Disc markers: (Disc 1 of 2)
- Roman numerals: III → 3, VII → 7
- Punctuation: colons, dashes, quotes

### 3. Cross-Platform Deduplication
For each game found on multiple platforms:
```
"Grand Theft Auto Vice City (USA)":
  - Found on: PS2, Xbox, GameCube
  - Priority: PS2 (1) > GameCube (2) > Xbox (3)
  - Action: Keep PS2 version, remove Xbox and GameCube versions
```

### 4. Result
Lower priority platforms become "exclusives only":
```
PS2:       2,556 games (unchanged - highest priority)
GameCube:  ~250 games (exclusives: Zelda, Metroid, etc.)
Xbox:      ~200 games (exclusives: Halo, Fable, etc.)
```

## Configuration

### Build Configuration

Create a generation-dedupe build config in `config/builds/`:

```yaml
name: gen5-dedupe-batocera
description: "Gen 5 with PSX priority (PSX full + Saturn exclusives)"

# Platforms in priority order
platforms:
  - psx      # Priority 1
  - saturn   # Priority 2

# Enable generation filter
generation_filter:
  enabled: true
  generation: gen5  # Use gen5, gen6, gen7, or gen4cd
  
  # Optional: Rescue specific games
  rescue_lists:
    saturn:  # Keep these Saturn games even if on PSX
      - "Panzer Dragoon Saga"
      - "Radiant Silvergun"

# Platform overrides (same as normal builds)
platform_overrides:
  psx:
    # ... normal PSX config
  saturn:
    # ... normal Saturn config
```

### Output Folder Naming

Generation dedupe builds use distinct output folders:
```
Standard build:  output/1g1r-eng-7z-batocera/psx/
Gen dedupe build: output/gen5-dedupe-batocera/psx/
                         ^^^^^^^^^^^^^
                         Clear indicator that gen dedup was applied
```

This makes it obvious which builds have cross-platform deduplication applied.

## Usage

### Run a Generation Build

```bash
# Via build-wizard
python3 build-wizard --config config/builds/gen5-dedupe-batocera.yaml

# Or via romgroomer CLI
romgroomer build gen5-dedupe-batocera
```

### Test with Small Subset First

Before processing full libraries, test with a small subset:

```yaml
# Add selection override to limit to 10 games per platform
selection_override:
  strategy: first
  count: 10
  sort_by: name
```

This lets you validate the matching logic before committing to a full build.

## Platform Priorities Explained

### Why These Priorities?

**Gen 5: PSX > Saturn**
- PSX had superior 3D performance and larger library
- Saturn excelled at 2D/arcade ports (different games anyway)
- Saturn exclusives are high quality (Panzer Dragoon, etc.)

**Gen 6: PS2 > GameCube > Xbox > Dreamcast**
- PS2 dominated the market (largest library, best 3rd-party support)
- GameCube had exceptional Nintendo exclusives
- Xbox had strong exclusives (Halo, Fable) but many PS2 ports
- Dreamcast died early, mostly exclusive library already

**Gen 7: PS3 > Xbox 360 > Wii**
- PS3/360 had very similar multi-platform libraries
- PS3 emulation (RPCS3) more mature than 360 (Xenia)
- Wii library very different (motion controls)

### Can I Change Priorities?

Yes! Edit `config/generations.yaml` and change the `priority` values:

```yaml
platforms:
  - name: gamecube
    priority: 1  # Change to make GameCube highest priority
  - name: ps2
    priority: 2  # PS2 becomes second
```

Or create custom generation definitions for specific needs.

## Rescue Lists

Rescue lists protect specific games from removal, even if they exist on a higher-priority platform. This is useful for:

1. **Superior ports**: Xbox version might be technically better
2. **Different content**: Some games differ significantly between platforms
3. **Personal preference**: You prefer a specific version

```yaml
generation_filter:
  enabled: true
  generation: gen6
  rescue_lists:
    xbox:
      - "Star Wars Knights of the Old Republic"  # Xbox version has extras
      - "Halo Combat Evolved"  # Obviously Xbox exclusive anyway
    gamecube:
      - "Resident Evil 4"  # GameCube version is the original
```

Games in rescue lists will NOT be removed during deduplication.

## Expected Results

### Generation 5 (PSX > Saturn)
```
Before:  PSX (1,798) + Saturn (318) = 2,116 games
After:   PSX (1,798) + Saturn (~220) = ~2,020 games
Savings: ~100 games, ~6 GB (small gen, less overlap)
```

### Generation 6 (PS2 > GC > Xbox > DC)
```
Before:  PS2 (2,556) + GC (595) + Xbox (975) + DC (250) = 4,376 games
After:   PS2 (2,556) + GC (~250) + Xbox (~200) + DC (~200) = ~3,200 games
Savings: ~1,200 games, ~2-3 TB
**This is where the biggest savings happen**
```

### Generation 7 (PS3 > 360 > Wii)
```
Before:  PS3 (1,300) + 360 (1,200) + Wii (1,200) = 3,700 games
After:   PS3 (1,300) + 360 (~300) + Wii (~800) = ~2,400 games
Savings: ~1,300 games, ~8-10 TB (games are HUGE in this gen)
```

## Verification

After running a generation build, check the results:

```bash
# Check game counts
ls output/gen6-dedupe-batocera/ps2/*.chd | wc -l    # Should be ~2,556
ls output/gen6-dedupe-batocera/xbox/*.iso | wc -l   # Should be ~200

# Check for expected exclusives
ls output/gen6-dedupe-batocera/xbox/ | grep -i halo     # Should exist
ls output/gen6-dedupe-batocera/xbox/ | grep -i "gta"   # Should NOT exist (on PS2)

# Check sizes
du -sh output/gen6-dedupe-batocera/ps2/
du -sh output/gen6-dedupe-batocera/xbox/
```

## Troubleshooting

### "Generation filter skipped: no game files found"

The filter couldn't find game files. Check:
1. Did the platform builds complete successfully?
2. Are game files in the right format? (CHD, RVZ, ISO)
3. Is the output path correct in platform configs?

### Games not matching across platforms

Some games have different names on different platforms. Check logs for:
```
DEBUG: Normalized game: "Final Fantasy 7 USA" [psx]
DEBUG: Normalized game: "Final Fantasy VII USA" [ps2]
       ^^ These should match but don't due to roman numeral
```

The normalizer handles most cases, but you may need to add rescue lists for edge cases.

### Too many/few games removed

If deduplication is too aggressive or not aggressive enough:
1. Check `config/generations.yaml` - are priorities correct?
2. Use rescue lists to protect specific games
3. Review normalization logic in `game_normalizer.py`

## Implementation Details

**Files:**
- `config/generations.yaml` - Generation definitions
- `src/romfarmer/cross_platform/game_normalizer.py` - Name normalization
- `src/romfarmer/stages/filter_generation.py` - Deduplication stage
- `src/romfarmer/config/models.py` - Config models
- `src/romfarmer/build_orchestrator.py` - Integration

**Flow:**
1. BuildOrchestrator processes all platforms normally
2. After all platforms complete, calls `_run_generation_filter()`
3. Generation filter loads platform output files
4. Normalizes all game names
5. Finds cross-platform duplicates
6. Removes lower-priority versions
7. Respects rescue lists

## Future Enhancements

Potential improvements:
- **Metadata-based matching**: Use game IDs from ScreenScraper
- **Size-aware deduplication**: Keep smaller version if quality identical
- **Regional variants**: Handle (USA) vs (Europe) intelligently
- **Web UI**: Visualize which games were kept/removed
- **Dry-run mode**: Preview what would be removed before committing

## Questions?

This is a new feature (implemented Jan 2026). If you encounter issues or have suggestions, please file an issue with:
- Build config used
- Platform game counts (before/after)
- Example games that matched/didn't match
- Logs from the generation filter stage
