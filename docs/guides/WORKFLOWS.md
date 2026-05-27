# ROM Farmer Workflows

Complete end-to-end workflows for common ROM management scenarios.

## Table of Contents

- [Workflow 1: Building a 1G1R Collection](#workflow-1-building-a-1g1r-collection)
- [Workflow 2: Validating Existing Collection](#workflow-2-validating-existing-collection)
- [Workflow 3: Multi-System Organization](#workflow-3-multi-system-organization)
- [Workflow 4: Collection Maintenance](#workflow-4-collection-maintenance)
- [Workflow 5: Region-Specific Collection](#workflow-5-region-specific-collection)
- [Workflow 6: Disc-Based System Management](#workflow-6-disc-based-system-management)

## Workflow 1: Building a 1G1R Collection

**Goal**: Create a curated "One Game, One ROM" collection with only the best version of each game.

**Time**: ~30 minutes for typical collection (500-1000 ROMs)

### Step 1: Obtain DAT Files

Download current DAT files from No-Intro or Redump:
- No-Intro: https://datomatic.no-intro.org/
- Redump: http://redump.org/downloads/

```bash
# Organize your DAT files
mkdir -p ~/dats/nointro
mkdir -p ~/dats/redump

# Example: Download Nintendo Game Boy DAT
# Place in ~/dats/nointro/Nintendo - Game Boy.dat
```

### Step 2: Import DAT into Database

```bash
cd /path/to/rom-farmer

# Import the DAT file
rom-farmer dat import ~/dats/nointro/Nintendo\ -\ Game\ Boy.dat

# Verify import
rom-farmer dat info "Nintendo - Game Boy"
```

**Expected output:**
```
╭─────────────────────────────────────────────╮
│ DAT: Nintendo - Game Boy                    │
├─────────────────────────────────────────────┤
│ Total Games:   1,040                        │
│ Parent Games:  874                          │
│ Clone Games:   166                          │
│ Imported: 2025-10-11                        │
╰─────────────────────────────────────────────╯
```

### Step 3: Apply 1G1R Filtering

Filter to keep only the best version of each game:

```bash
# Apply 1G1R filter with your preferences
rom-farmer dat filter "Nintendo - Game Boy" \
    --regions USA,World,Europe \
    --languages En \
    --prefer-parent \
    --prefer-revisions \
    --output ~/lists/gb_1g1r_games.txt
```

**Understanding the filter:**
- `--regions USA,World,Europe`: Prefer USA releases, then World, then Europe
- `--languages En`: Prefer English language ROMs
- `--prefer-parent`: Choose parent ROMs over clone variants
- `--prefer-revisions`: Keep the latest revision (Rev 2 over Rev 1)

**Expected output:**
```
Before filtering: 1,040 games
After filtering:    658 games (37% reduction)

Filtered list saved to: ~/lists/gb_1g1r_games.txt
```

### Step 4: Scan Your Current Collection

Scan your existing ROMs to see what you have:

```bash
# Scan with validation
rom-farmer scan directory ~/roms/gb \
    --dat "Nintendo - Game Boy" \
    --validate \
    --threads 8 \
    --output ~/reports/gb_scan_$(date +%Y%m%d).txt
```

**Expected output:**
```
Scanning: ~/roms/gb
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:45

Files scanned:    842
Matched to DAT:   798
Not in DAT:       44
CRC32 validated:  798
CRC32 mismatches: 0
```

### Step 5: Identify Missing Games

Find what's missing from your 1G1R set:

```bash
rom-farmer scan missing ~/roms/gb \
    --dat "Nintendo - Game Boy" \
    --filter-1g1r \
    --output ~/lists/gb_missing.txt
```

**Expected output:**
```
Collection: 798 games found
1G1R Set:   658 games needed
You have:   587 games from 1G1R set (89.2%)
Missing:    71 games from 1G1R set (10.8%)

Missing games list saved to: ~/lists/gb_missing.txt
```

### Step 6: Organize Your Collection

Create an organized directory structure:

```bash
# Preview organization
rom-farmer organize region ~/roms/gb \
    --output ~/organized/gb \
    --mode copy \
    --dry-run

# If preview looks good, execute
rom-farmer organize region ~/roms/gb \
    --output ~/organized/gb \
    --mode copy
```

**Result:**
```
~/organized/gb/
├── USA/          (412 ROMs)
├── World/        (45 ROMs)
├── Europe/       (198 ROMs)
├── Japan/        (143 ROMs)
└── unmatched/    (44 ROMs)
```

### Step 7: Clean Up Non-1G1R ROMs (Optional)

Remove ROMs not in your 1G1R set:

```bash
# Generate list of ROMs to keep
rom-farmer dat filter "Nintendo - Game Boy" \
    --regions USA,World,Europe \
    --output ~/lists/gb_keep.txt

# Use the list to identify duplicates
# (Manual review recommended before deletion)
```

### Summary

You now have:
- ✅ Imported and filtered DAT file
- ✅ Validated ROM collection
- ✅ Organized directory structure
- ✅ List of missing games to acquire
- ✅ 1G1R curated collection

## Workflow 2: Validating Existing Collection

**Goal**: Verify ROM authenticity and identify bad dumps or corrupted files.

**Time**: ~15 minutes for 500 ROMs

### Step 1: Import DAT

```bash
rom-farmer dat import ~/dats/nointro/Sega\ -\ Mega\ Drive\ -\ Genesis.dat
```

### Step 2: Full Validation Scan

```bash
rom-farmer scan directory ~/roms/genesis \
    --dat "Sega - Mega Drive - Genesis" \
    --validate \
    --threads 8 \
    --output ~/reports/genesis_validation_$(date +%Y%m%d).txt
```

### Step 3: Review Results

Check the output for:
- **CRC32 mismatches**: Corrupted or bad dumps
- **Files not in DAT**: Hacks, homebrew, or unknown dumps
- **Missing games**: Gaps in your collection

**Good result:**
```
✓ Files scanned: 852
✓ Matched to DAT: 852
✓ CRC32 validated: 852
✓ CRC32 mismatches: 0
```

**Problem result:**
```
⚠ Files scanned: 852
⚠ Matched to DAT: 845
⚠ Not in DAT: 7
⚠ CRC32 mismatches: 3

CRC Mismatches:
  ✗ Sonic the Hedgehog 2 (USA).bin
    Expected: a90d2e9f
    Got:      b91e3fa0
```

### Step 4: Fix Issues

**For CRC mismatches:**
```bash
# Verify single file
rom-farmer scan verify ~/roms/genesis/Sonic\ 2.bin \
    --dat "Sega - Mega Drive - Genesis"

# If corrupted, re-acquire the ROM
```

**For unknown files:**
```bash
# Review unmatched files
grep "Not in DAT" ~/reports/genesis_validation_*.txt

# Decide: keep (homebrew), delete (bad dump), or research
```

## Workflow 3: Multi-System Organization

**Goal**: Organize multiple systems in a consistent structure.

**Time**: Variable (can run overnight for large collections)

### Automated Script

Create `organize_all.sh`:

```bash
#!/bin/bash
set -e

# Configuration
ROM_BASE=~/roms
ORG_BASE=~/organized
DAT_BASE=~/dats/nointro
REPORT_BASE=~/reports

# Systems to process
SYSTEMS=(
    "Nintendo - Game Boy:gb"
    "Nintendo - Game Boy Advance:gba"
    "Nintendo - Game Boy Color:gbc"
    "Nintendo - Nintendo Entertainment System:nes"
    "Nintendo - Super Nintendo Entertainment System:snes"
    "Sega - Master System - Mark III:sms"
    "Sega - Mega Drive - Genesis:genesis"
)

# Create directories
mkdir -p "$ORG_BASE" "$REPORT_BASE"

for system_info in "${SYSTEMS[@]}"; do
    # Parse system info
    IFS=':' read -r system_name system_dir <<< "$system_info"
    
    echo "=================================================="
    echo "Processing: $system_name"
    echo "=================================================="
    
    # Import DAT
    echo "1. Importing DAT..."
    rom-farmer dat import "$DAT_BASE/${system_name}.dat" --update
    
    # Scan collection
    echo "2. Scanning collection..."
    rom-farmer scan directory "$ROM_BASE/$system_dir" \
        --dat "$system_name" \
        --validate \
        --threads 8 \
        --output "$REPORT_BASE/${system_dir}_scan_$(date +%Y%m%d).txt"
    
    # Find missing games
    echo "3. Identifying missing games..."
    rom-farmer scan missing "$ROM_BASE/$system_dir" \
        --dat "$system_name" \
        --filter-1g1r \
        --output "$REPORT_BASE/${system_dir}_missing.txt"
    
    # Organize ROMs
    echo "4. Organizing ROMs..."
    rom-farmer organize region "$ROM_BASE/$system_dir" \
        --output "$ORG_BASE/$system_dir" \
        --mode copy
    
    echo "✓ $system_name complete!"
    echo ""
done

echo "=================================================="
echo "All systems processed!"
echo "=================================================="
echo "Reports in: $REPORT_BASE"
echo "Organized ROMs in: $ORG_BASE"
```

Run the script:

```bash
chmod +x organize_all.sh
./organize_all.sh
```

## Workflow 4: Collection Maintenance

**Goal**: Regular maintenance to keep your collection validated and up-to-date.

**Frequency**: Weekly or monthly

### Weekly Validation Script

Create `weekly_check.sh`:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
REPORT_DIR=~/reports/weekly

mkdir -p "$REPORT_DIR"

echo "ROM Farmer Weekly Validation - $DATE"
echo "======================================="

# Update all DATs
echo "Updating DAT files..."
rom-farmer dat import ~/dats/nointro/*.dat --update

# Validate all systems
for system_dir in ~/organized/*; do
    system=$(basename "$system_dir")
    echo "Validating $system..."
    
    rom-farmer scan directory "$system_dir" \
        --validate \
        --output "$REPORT_DIR/${system}_${DATE}.txt"
done

# Generate summary
echo ""
echo "Validation complete! Reports in: $REPORT_DIR"
```

### Monthly Missing Games Report

```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
REPORT_DIR=~/reports/monthly

mkdir -p "$REPORT_DIR"

echo "ROM Farmer Missing Games Report - $DATE"
echo "=========================================="

for system_dir in ~/organized/*; do
    system=$(basename "$system_dir")
    dat_name=$(rom-farmer dat list | grep -i "$system" | head -1 | awk '{print $1}')
    
    if [ -n "$dat_name" ]; then
        echo "Checking $system..."
        rom-farmer scan missing "$system_dir" \
            --dat "$dat_name" \
            --filter-1g1r \
            --output "$REPORT_DIR/${system}_missing_${DATE}.txt"
    fi
done

echo "Reports saved to: $REPORT_DIR"
```

## Workflow 5: Region-Specific Collection

**Goal**: Build a collection with only specific regions (e.g., USA-only).

### Step 1: Import and Filter DAT

```bash
# Import DAT
rom-farmer dat import ~/dats/nointro/Nintendo\ -\ Game\ Boy\ Advance.dat

# Filter to USA only
rom-farmer dat filter "Nintendo - Game Boy Advance" \
    --regions USA \
    --output ~/lists/gba_usa_only.txt
```

### Step 2: Scan Current Collection

```bash
rom-farmer scan directory ~/roms/gba \
    --dat "Nintendo - Game Boy Advance" \
    --validate
```

### Step 3: Organize by Region

```bash
rom-farmer organize region ~/roms/gba \
    --output ~/organized/gba_by_region \
    --mode copy
```

### Step 4: Keep Only USA ROMs

```bash
# Copy only USA ROMs to final location
cp -r ~/organized/gba_by_region/USA/* ~/curated/gba/

# Verify
rom-farmer scan directory ~/curated/gba \
    --dat "Nintendo - Game Boy Advance" \
    --validate
```

## Workflow 6: Disc-Based System Management

**Goal**: Manage disc-based systems (PlayStation, Saturn, etc.) with multi-disc support.

### Step 1: Import Redump DAT

```bash
# Redump DATs for disc systems
rom-farmer dat import ~/dats/redump/Sony\ -\ PlayStation.dat
```

### Step 2: Scan Disc Collection

```bash
rom-farmer scan directory ~/roms/psx \
    --dat "Sony - PlayStation" \
    --validate \
    --threads 4
```

### Step 3: Identify Multi-Disc Games

```bash
# Search for multi-disc games
rom-farmer dat search "Sony - PlayStation" "disc" | grep -i "disc 2"
```

### Step 4: Organize Disc Images

```bash
# Organize while preserving disc sets
rom-farmer organize region ~/roms/psx \
    --output ~/organized/psx \
    --mode copy \
    --keep-in-place
```

### Step 5: Generate M3U Playlists (Future Feature)

```bash
# Will generate .m3u playlists for multi-disc games
# Example: Final Fantasy VII (USA).m3u containing:
#   Final Fantasy VII (USA) (Disc 1).chd
#   Final Fantasy VII (USA) (Disc 2).chd
#   Final Fantasy VII (USA) (Disc 3).chd
```

## Best Practices Summary

### Before Starting
- ✅ Backup your ROM collection
- ✅ Download current DAT files
- ✅ Test commands with --dry-run first
- ✅ Start with one system before batch processing

### During Processing
- ✅ Use --validate to catch bad dumps
- ✅ Export reports for record-keeping
- ✅ Use --threads to speed up scanning
- ✅ Review unmatched files manually

### After Processing
- ✅ Verify organized structure
- ✅ Keep DATs updated regularly
- ✅ Run periodic validation scans
- ✅ Document your preferences

### Safety
- ⚠️ Use `--mode copy` until confident
- ⚠️ Never delete ROMs without validation
- ⚠️ Keep unmatched files for review
- ⚠️ Test workflows on small sets first

## Troubleshooting Workflows

### "Too many CRC mismatches"
```bash
# Re-download the DAT file (may be outdated)
rom-farmer dat delete "System Name"
rom-farmer dat import ~/dats/newest.dat

# Re-scan
rom-farmer scan directory ~/roms --validate
```

### "Missing games but I have them"
```bash
# Files may have wrong names
# Scan without DAT to see all files
rom-farmer scan directory ~/roms

# Check actual filenames
ls -la ~/roms

# Verify individual file
rom-farmer scan verify ~/roms/game.bin
```

### "Scan is too slow"
```bash
# Increase threads
rom-farmer scan directory ~/roms --threads 16

# Skip validation for quick overview
rom-farmer scan directory ~/roms
```

### "Organization created duplicates"
```bash
# Use symlink mode instead
rom-farmer organize region ~/roms \
    --output ~/organized \
    --mode symlink
```

## Next Steps

Now that you understand the workflows:

1. **Start small**: Test with one system first
2. **Automate**: Create scripts for regular tasks
3. **Document**: Keep notes on your preferences
4. **Share**: Help others with your workflows

See also:
- [User Guide](USER_GUIDE.md) - Complete command reference
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues
- [DAT Files Guide](DAT_FILES.md) - DAT management details
