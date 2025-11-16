# PS3 HYBRID Build System - Production Guide

## Overview

The HYBRID build system creates complete, self-contained PS3 game packages that work on **both real PS3 hardware and RPCS3 emulator**. Each game includes:

- ✅ Base game (decrypted from Redump source)
- ✅ Official updates (baked into game files)
- ✅ Major campaign DLC extracted to disc (for real PS3)
- ✅ ALL DLC PKG files in `_PKG/` folder (for RPCS3)
- ✅ RAP license files for DLC activation
- ✅ Auto-generated README.txt with usage instructions

## Quick Start

### Process Entire Library
\`\`\`bash
python3 build_ps3_hybrid_universal.py
\`\`\`

### Test with Letter Filtering (Recommended)
\`\`\`bash
# Process only games starting with 'A'
python3 build_ps3_hybrid_universal.py --filter A

# Process only games starting with 'B'
python3 build_ps3_hybrid_universal.py --filter B
\`\`\`

### Process Specific Game
\`\`\`bash
python3 build_ps3_hybrid_universal.py --game "Borderlands 2"
\`\`\`

### Dry Run (Preview Without Changes)
\`\`\`bash
python3 build_ps3_hybrid_universal.py --filter A --dry-run
\`\`\`

## Workflow Integration

### Current Pipeline
1. **Redump ISO** → `PS3Dec` → **Decrypted .ps3 folder**
2. **build_ps3_hybrid_universal.py** → **HYBRID package**
   - Applies updates from Sony PSN
   - Extracts campaign DLC to disc
   - Copies all PKG files to `_PKG/`
   - Creates RAP files
   - Generates README.txt

### Output Structure
\`\`\`
Game Name (USA).ps3/
├── PS3_DISC.SFB
├── PS3_GAME/
│   ├── PARAM.SFO           # Updated version
│   ├── USRDIR/
│   │   ├── EBOOT.BIN       # Updated executable
│   │   └── DLC/            # Campaign DLC (real PS3)
│   │       ├── ORCHID/
│   │       ├── IRIS/
│   │       └── ...
│   └── ...
├── _PKG/                    # For RPCS3 + optional PS3
│   ├── Game - DLC Name 1.pkg
│   ├── Game - DLC Name 2.pkg
│   ├── ...                  # All 23 DLC PKGs
│   └── RAPS/
│       ├── CONTENTID1.rap
│       ├── CONTENTID2.rap
│       └── ...              # All RAP files
└── README.txt               # Auto-generated guide

## Features

### Automatic Detection
- **Title ID**: Extracted from PARAM.SFO
- **Region**: Detected from title ID or folder name
- **Version**: Read from PARAM.SFO after updates
- **Game Name**: From folder name (no hardcoding!)

### Dynamic README
Every game gets a custom README with:
- Platform-specific installation instructions
- Complete PKG list with readable names
- RAP file installation guide
- Troubleshooting section
- Technical details (sizes, versions, etc.)

### Template-Based
- Template: `templates/README_HYBRID.txt`
- Placeholders filled automatically per game
- Works for entire PS3 library

### Smart DLC Detection
- **Campaign DLC**: Extracted to disc (keywords: CAMPAIGN, MISSION, EXPANSION, etc.)
- **ALL DLC**: PKG files copied to `_PKG/` folder
- **RAP Files**: Created from NoPayStation database

## Configuration

### Default Paths
\`\`\`python
--source /data/emu/ps3netsrv                              # .ps3 game folders
--pkg-archive /data/emu/source/nopaystation/downloads-ps3-dlc
--nps-database /data/emu/source/nopaystation/PS3_DLCS.tsv
\`\`\`

### Command Line Options
\`\`\`bash
--filter A              # Only process games starting with 'A'
--game "Uncharted"      # Only process games matching name
--dry-run               # Preview without modifications
--no-updates            # Skip update application
--no-dlc                # Skip DLC processing
\`\`\`

## Testing Strategy

### Phase 1: Letter-by-Letter Testing
\`\`\`bash
# Test 'A' games first
python3 build_ps3_hybrid_universal.py --filter A --dry-run
python3 build_ps3_hybrid_universal.py --filter A

# Then 'B' games
python3 build_ps3_hybrid_universal.py --filter B

# Continue through alphabet
\`\`\`

### Phase 2: Validation
For each batch:
1. Check README.txt is generated
2. Verify PKG files have readable names
3. Confirm RAP files created
4. Test one game on RPCS3
5. Test one game on real PS3 (if available)

### Phase 3: Full Library
\`\`\`bash
# After successful letter testing
python3 build_ps3_hybrid_universal.py
\`\`\`

## Example Output

### Borderlands 2
\`\`\`
📊 Statistics:
   Updates available: 1
   Updates applied: 1
   DLC available: 23
   Campaign DLC extracted: 4
   DLC PKGs copied: 23
   RAP files created: 23

Total Size: 14.43 GB
  - Base game: 8.94 GB
  - Updates: Baked in
  - Disc DLC: 4 campaigns
  - PKG files: 5.24 GB (23 PKGs)
  - RAP files: 23
\`\`\`

### The Last of Us
\`\`\`
📊 Statistics:
   Updates available: 1
   Updates applied: 1
   DLC available: 8
   Campaign DLC extracted: 1 (Left Behind)
   DLC PKGs copied: 8
   RAP files created: 8
\`\`\`

## Benefits Over _HYBRID Suffix

### Before (Hardcoded)
- ❌ `Borderlands 2 (USA)_HYBRID.ps3`
- ❌ Game-specific script
- ❌ Manual README creation
- ❌ Copy/paste for each game

### After (Universal)
- ✅ `Borderlands 2 (USA).ps3` (original name)
- ✅ Works on any PS3 game
- ✅ Auto-generated README
- ✅ Batch processing entire library
- ✅ Letter filtering for testing
- ✅ Template-based documentation

## Troubleshooting

### "No updates found"
- Normal for many games (not all have updates)
- Sony PSN may not have updates for older titles
- DLC processing will still work

### "PKG not found"
- DLC may not be in local archive
- Download fallback would trigger (not implemented in universal version)
- Game will still build with available DLC

### "No TITLE_ID found"
- Game folder may be incomplete
- Check that PARAM.SFO exists in PS3_GAME/
- May be a bad decrypt or incomplete download

## Next Steps

1. ✅ Test with letter filtering (`--filter A`)
2. ✅ Validate READMEs are generated correctly
3. ✅ Verify PKG names are readable
4. ✅ Test RPCS3 PKG installation
5. ✅ Batch process library letter-by-letter
6. 🔄 Integrate into main rom-groomer pipeline

## Success Criteria

✅ README.txt generated for every game
✅ PKG files have user-friendly names
✅ RAP files created correctly
✅ No `_HYBRID` suffix (uses original names)
✅ Works on entire PS3 library
✅ Letter filtering enables safe testing
✅ Dry-run prevents accidental changes
