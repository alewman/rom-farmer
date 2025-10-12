# ROM Groomer User Guide

Complete reference for all ROM Groomer commands and features.

## Table of Contents

- [Overview](#overview)
- [DAT Management](#dat-management)
- [ROM Scanning](#rom-scanning)
- [ROM Organization](#rom-organization)
- [Advanced Usage](#advanced-usage)
- [Tips and Best Practices](#tips-and-best-practices)

## Overview

ROM Groomer is organized into three main command groups:

1. **`dat`**: Manage DAT files (import, filter, search)
2. **`scan`**: Scan and validate ROM collections
3. **`organize`**: Organize ROMs by region, type, or language

### Getting Help

```bash
# General help
rom-groomer --help

# Help for a command group
rom-groomer dat --help

# Help for a specific command
rom-groomer dat import --help
```

## DAT Management

DAT files (from No-Intro, Redump) define known good ROM dumps. ROM Groomer imports these into a local database for validation and filtering.

### Import DAT Files

Import a single DAT file:

```bash
rom-groomer dat import /path/to/Nintendo\ -\ Game\ Boy.dat
```

Import multiple DAT files:

```bash
# Import all DAT files in a directory
rom-groomer dat import /path/to/dats/*.dat

# Import specific systems
rom-groomer dat import \
    ~/dats/Nintendo*.dat \
    ~/dats/Sega*.dat
```

**Options:**
- `--update`: Update existing DAT if already imported
- `--verbose`: Show detailed import progress

**Example output:**
```
Importing DAT: Nintendo - Game Boy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:02
✓ Imported 1,040 games from 'Nintendo - Game Boy'
```

### List Imported DATs

```bash
rom-groomer dat list
```

**Example output:**
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━┓
┃ DAT File                 ┃ Version ┃ Games   ┃ Imported  ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━┩
│ Nintendo - Game Boy      │ 20230915│ 1,040   │ 2025-10-11│
│ Nintendo - Game Boy Adv. │ 20230920│ 2,720   │ 2025-10-11│
│ Sega - Mega Drive        │ 20230910│ 1,235   │ 2025-10-10│
└──────────────────────────┴─────────┴─────────┴───────────┘
```

### Show DAT Information

Get detailed information about an imported DAT:

```bash
rom-groomer dat info "Nintendo - Game Boy"
```

**Example output:**
```
╭─────────────────────────────────────────────╮
│ DAT: Nintendo - Game Boy                    │
├─────────────────────────────────────────────┤
│ Name:        Nintendo - Game Boy            │
│ Description: Nintendo Game Boy ROMs         │
│ Version:     20230915                       │
│ Author:      No-Intro                       │
│                                             │
│ Total Games:   1,040                        │
│ Parent Games:  874                          │
│ Clone Games:   166                          │
│                                             │
│ Regions:                                    │
│   USA:     412                              │
│   Europe:  338                              │
│   Japan:   245                              │
│   World:    45                              │
│                                             │
│ Imported: 2025-10-11 14:30:22              │
╰─────────────────────────────────────────────╯
```

### List Games in DAT

List all games from a DAT:

```bash
rom-groomer dat games "Nintendo - Game Boy"
```

**Options:**
- `--limit N`: Show only N games (default: 50)
- `--offset N`: Skip first N games
- `--region REGION`: Filter by region (USA, Europe, Japan, etc.)
- `--output FILE`: Export to text file

**Examples:**

```bash
# List first 100 games
rom-groomer dat games "Nintendo - Game Boy" --limit 100

# List only USA region games
rom-groomer dat games "Nintendo - Game Boy" --region USA

# Export all games to file
rom-groomer dat games "Nintendo - Game Boy" --limit 0 --output gb_games.txt
```

### Search for Games

Search for specific games by name:

```bash
rom-groomer dat search "Nintendo - Game Boy" "pokemon"
```

**Example output:**
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Game Name                      ┃ Region  ┃ CRC32      ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━┩
│ Pokemon - Red Version (USA)    │ USA     │ 3d45c1ee   │
│ Pokemon - Blue Version (USA)   │ USA     │ d6da8a1a   │
│ Pokemon - Yellow Version (USA) │ USA     │ 7d527d62   │
│ Pokemon - Gold Version (USA)   │ USA     │ a6924ce1   │
│ Pokemon - Silver Version (USA) │ USA     │ 49a84b95   │
└────────────────────────────────┴─────────┴────────────┘
```

### Filter to 1G1R (One Game One ROM)

Filter a DAT to keep only the best version of each game:

```bash
rom-groomer dat filter "Nintendo - Game Boy" \
    --regions USA,World,Europe,Japan \
    --languages En,Ja \
    --prefer-parent
```

**Options:**
- `--regions`: Comma-separated region priority (default: USA,World,Europe,Japan)
- `--languages`: Comma-separated language priority (default: En,Ja,Fr,De,Es)
- `--prefer-parent`: Prefer parent ROMs over clones (recommended)
- `--prefer-revisions`: Prefer newer revisions
- `--output FILE`: Export filtered list to file

**Example output:**
```
Applying 1G1R filter to 'Nintendo - Game Boy'...

Region priorities:   USA → World → Europe → Japan
Language priorities: En → Ja

Before filtering: 1,040 games
After filtering:    658 games (37% reduction)

Top games kept:
  ✓ Pokemon - Red Version (USA)
  ✓ The Legend of Zelda - Link's Awakening (USA)
  ✓ Super Mario Land (World)
  ✓ Tetris (World)
  ...

Games filtered out:
  ✗ Pokemon - Red Version (Europe)   [Lower region priority]
  ✗ Pokemon - Red Version (Japan)    [Lower region priority]
  ✗ Tetris (USA, Europe) (Rev 1)     [Clone of parent]
  ...

Filtered list saved to: filtered_games.txt
```

### DAT Statistics

View statistics across all imported DATs:

```bash
rom-groomer dat stats
```

**Example output:**
```
╭───────────────────────────────────────╮
│ ROM Groomer Database Statistics      │
├───────────────────────────────────────┤
│ Total DAT files:        8             │
│ Total games:            12,845        │
│ Unique CRC32 hashes:    11,923        │
│                                       │
│ By System:                            │
│   Nintendo:            6,420          │
│   Sega:                3,214          │
│   Sony:                2,155          │
│   Other:               1,056          │
│                                       │
│ Database size:         45.2 MB        │
│ Last import:           2025-10-11     │
╰───────────────────────────────────────╯
```

### Delete DAT

Remove a DAT from the database:

```bash
rom-groomer dat delete "Nintendo - Game Boy"
```

**Options:**
- `--force`: Skip confirmation prompt

## ROM Scanning

Scan ROM files and directories to validate against imported DATs.

### Scan Directory

Scan a directory of ROMs:

```bash
rom-groomer scan directory /path/to/roms/gb
```

**Options:**
- `--dat NAME`: Validate against specific DAT
- `--validate`: Calculate and check CRC32 hashes
- `--recursive`: Scan subdirectories (default: true)
- `--threads N`: Number of parallel threads (default: 4)
- `--output FILE`: Export scan report

**Examples:**

```bash
# Basic scan (lists files only)
rom-groomer scan directory /roms/gb

# Scan with validation
rom-groomer scan directory /roms/gb \
    --dat "Nintendo - Game Boy" \
    --validate

# Fast scan with 8 threads
rom-groomer scan directory /roms/gb \
    --dat "Nintendo - Game Boy" \
    --validate \
    --threads 8

# Export report
rom-groomer scan directory /roms/gb \
    --dat "Nintendo - Game Boy" \
    --validate \
    --output scan_report.txt
```

**Example output:**
```
Scanning: /roms/gb
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:15

Scan Results:
┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Metric                  ┃ Count  ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ Files scanned           │ 425    │
│ Matched to DAT          │ 412    │
│ Not in DAT              │ 13     │
│ CRC32 validated         │ 412    │
│ CRC32 mismatches        │ 0      │
└─────────────────────────┴────────┘

Matched Games (top 10):
  ✓ Pokemon - Red Version (USA)
  ✓ Pokemon - Blue Version (USA)
  ✓ The Legend of Zelda - Link's Awakening (USA)
  ✓ Super Mario Land (World)
  ...

Unmatched Files:
  ✗ some-homebrew-game.gb
  ✗ test-rom-v2.gb
  ...

Scan completed in 15.3 seconds
```

### Find Missing Games

Compare your collection against a DAT to find missing games:

```bash
rom-groomer scan missing /path/to/roms/gb \
    --dat "Nintendo - Game Boy"
```

**Options:**
- `--dat NAME`: DAT to compare against (required)
- `--filter-1g1r`: Only check for 1G1R filtered games
- `--region REGION`: Filter by region
- `--output FILE`: Export missing games list

**Examples:**

```bash
# Find all missing games
rom-groomer scan missing /roms/gb \
    --dat "Nintendo - Game Boy"

# Find missing USA games only
rom-groomer scan missing /roms/gb \
    --dat "Nintendo - Game Boy" \
    --region USA

# Find missing from 1G1R set
rom-groomer scan missing /roms/gb \
    --dat "Nintendo - Game Boy" \
    --filter-1g1r

# Export to file
rom-groomer scan missing /roms/gb \
    --dat "Nintendo - Game Boy" \
    --output missing_games.txt
```

**Example output:**
```
Analyzing collection against 'Nintendo - Game Boy'...

Collection: 412 games found
DAT:        1,040 games total
Missing:    628 games (60.4%)

Missing Games (top 20):
  • Aladdin (USA)
  • Batman - The Video Game (USA)
  • Bomberman GB (USA)
  • Castlevania II - Belmont's Revenge (USA)
  ...

By Region:
  USA:     245 missing
  Europe:  198 missing
  Japan:   185 missing

Missing games list saved to: missing_games.txt
```

### Verify Single ROM

Verify a single ROM file:

```bash
rom-groomer scan verify /path/to/game.gb
```

**Options:**
- `--dat NAME`: Check against specific DAT
- `--show-all-hashes`: Display MD5 and SHA1 in addition to CRC32

**Example output:**
```
Verifying: Pokemon - Red Version (USA).gb

File Information:
  Size:        1,048,576 bytes (1.0 MB)
  CRC32:       3d45c1ee
  MD5:         3d45c1ee9b80b4d6a83e5c1a3f4a8b2c
  SHA1:        d9e5cf6b3a...

DAT Match:
  ✓ Matched: Pokemon - Red Version (USA)
  Game:      Pokemon - Red Version
  Region:    USA
  CRC32:     3d45c1ee ✓ MATCH

Status: ✓ VERIFIED
```

## ROM Organization

Organize your ROM collection by region, type, or language.

### Organize by Region

Sort ROMs into region-based subdirectories:

```bash
rom-groomer organize region /path/to/roms/gb \
    --output /path/to/organized/gb
```

**Options:**
- `--output PATH`: Destination directory (required)
- `--mode MODE`: Operation mode: `copy`, `move`, or `symlink` (default: copy)
- `--keep-in-place`: Keep files that don't match patterns
- `--exclude PATTERN`: Exclude files matching pattern (can be repeated)
- `--dry-run`: Preview changes without executing

**Example structure created:**
```
/path/to/organized/gb/
├── USA/
│   ├── Pokemon - Red Version (USA).gb
│   ├── Zelda - Link's Awakening (USA).gb
│   └── ...
├── Europe/
│   ├── Super Mario Land (Europe).gb
│   └── ...
├── Japan/
│   ├── Final Fantasy Legend (Japan).gb
│   └── ...
└── World/
    ├── Tetris (World).gb
    └── ...
```

**Examples:**

```bash
# Copy ROMs to organized structure
rom-groomer organize region /roms/gb --output /organized/gb --mode copy

# Move ROMs (faster, reorganizes in place)
rom-groomer organize region /roms/gb --output /organized/gb --mode move

# Create symlinks (useful for multiple views)
rom-groomer organize region /roms/gb --output /organized/gb --mode symlink

# Preview without changes
rom-groomer organize region /roms/gb --output /organized/gb --dry-run

# Exclude BIOS and sample files
rom-groomer organize region /roms/gb --output /organized/gb \
    --exclude "*[BIOS]*" --exclude "*Sample*"
```

### Organize by Type

Sort ROMs by type (cartridge, disc, BIOS, etc.):

```bash
rom-groomer organize kind /path/to/roms \
    --output /path/to/organized
```

**Example structure:**
```
/path/to/organized/
├── Cartridge/
│   ├── game1.gb
│   └── game2.gba
├── Disc/
│   ├── game1.chd
│   └── game2.cue
├── BIOS/
│   └── bios.bin
└── Other/
    └── readme.txt
```

### Organize by Language

Sort ROMs by language:

```bash
rom-groomer organize language /path/to/roms \
    --output /path/to/organized
```

**Example structure:**
```
/path/to/organized/
├── En/           # English
├── Ja/           # Japanese
├── Fr/           # French
├── De/           # German
├── Multi/        # Multi-language
└── Unknown/
```

### Organize All

Run all organizers in sequence:

```bash
rom-groomer organize all /path/to/roms \
    --output /path/to/organized
```

This creates a structure like:
```
/path/to/organized/
└── by-region/
    └── USA/
        └── by-kind/
            └── Cartridge/
                └── by-language/
                    └── En/
                        └── game.gb
```

## Advanced Usage

### Batch Processing

Process multiple systems:

```bash
#!/bin/bash
SYSTEMS=("gb" "gba" "gbc" "nes" "snes")

for system in "${SYSTEMS[@]}"; do
    echo "Processing $system..."
    
    # Import DAT
    rom-groomer dat import ~/dats/${system}.dat
    
    # Scan collection
    rom-groomer scan directory ~/roms/$system \
        --dat "$system" --validate
    
    # Organize
    rom-groomer organize region ~/roms/$system \
        --output ~/organized/$system
done
```

### 1G1R Workflow

Create a curated 1G1R collection:

```bash
# 1. Import DAT
rom-groomer dat import "Nintendo - Game Boy.dat"

# 2. Filter to 1G1R
rom-groomer dat filter "Nintendo - Game Boy" \
    --regions USA,World \
    --output gb_1g1r.txt

# 3. Scan collection to find matches
rom-groomer scan directory /roms/gb \
    --dat "Nintendo - Game Boy" \
    --validate

# 4. Find what's missing from 1G1R set
rom-groomer scan missing /roms/gb \
    --dat "Nintendo - Game Boy" \
    --filter-1g1r \
    --output gb_missing.txt

# 5. Organize validated ROMs
rom-groomer organize region /roms/gb \
    --output /curated/gb --mode copy
```

### Pipeline Integration

Use ROM Groomer in automated pipelines:

```bash
# Exit with error if validation fails
rom-groomer scan directory /roms/gb \
    --dat "Nintendo - Game Boy" \
    --validate || exit 1

# Export reports for analysis
rom-groomer scan directory /roms/gb \
    --validate \
    --output /reports/scan_$(date +%Y%m%d).txt

# Generate missing games report
rom-groomer scan missing /roms/gb \
    --dat "Nintendo - Game Boy" \
    --output /reports/missing_$(date +%Y%m%d).txt
```

## Tips and Best Practices

### Performance Optimization

1. **Use more threads for large collections:**
   ```bash
   rom-groomer scan directory /roms --threads 8
   ```

2. **Skip validation for quick scans:**
   ```bash
   # Fast scan without CRC calculation
   rom-groomer scan directory /roms
   ```

3. **Use symlinks for multiple organizations:**
   ```bash
   # Create different views without duplicating files
   rom-groomer organize region /roms --output /views/by-region --mode symlink
   rom-groomer organize kind /roms --output /views/by-type --mode symlink
   ```

### Safety Measures

1. **Always use --dry-run first:**
   ```bash
   rom-groomer organize region /roms --output /organized --dry-run
   ```

2. **Use copy mode until confident:**
   ```bash
   # Safer than move
   rom-groomer organize region /roms --output /organized --mode copy
   ```

3. **Keep backups before batch operations:**
   ```bash
   # Backup before organizing
   tar czf roms_backup_$(date +%Y%m%d).tar.gz /roms
   ```

### DAT Management

1. **Update DATs regularly:**
   ```bash
   # Re-import with --update flag
   rom-groomer dat import ~/dats/*.dat --update
   ```

2. **Filter DATs for your needs:**
   ```bash
   # Create focused collections
   rom-groomer dat filter "Nintendo - Game Boy" \
       --regions USA --output gb_usa_only.txt
   ```

3. **Export game lists for reference:**
   ```bash
   rom-groomer dat games "Nintendo - Game Boy" \
       --limit 0 --output gb_complete.txt
   ```

### Collection Maintenance

1. **Regular validation:**
   ```bash
   # Weekly validation script
   rom-groomer scan directory /roms \
       --dat "Nintendo - Game Boy" \
       --validate \
       --output /reports/weekly_$(date +%Y%m%d).txt
   ```

2. **Track missing games:**
   ```bash
   rom-groomer scan missing /roms \
       --dat "Nintendo - Game Boy" \
       --output /reports/missing.txt
   ```

3. **Remove duplicates after 1G1R filter:**
   ```bash
   # Filter DAT, then scan to identify extras
   rom-groomer dat filter "Nintendo - Game Boy" --output gb_1g1r.txt
   rom-groomer scan directory /roms --dat "Nintendo - Game Boy"
   # Manually review and remove non-1G1R files
   ```

## Next Steps

- Read the [Workflow Guide](WORKFLOWS.md) for end-to-end examples
- Check [Troubleshooting](TROUBLESHOOTING.md) for common issues
- See [DAT Files Guide](DAT_FILES.md) for DAT management details
