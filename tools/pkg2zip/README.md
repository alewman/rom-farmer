# pkg2zip

PKG file extraction tool for PS3/PSP/PSVita packages.

## Purpose

Extract and decrypt Sony PKG files (PlayStation Network packages) for use with:
- **PS3:** Extract DLC and updates for jailbroken PS3 / RPCS3
- **PSP:** Extract games and DLC
- **PSVita:** Extract games and DLC

## Source

- **GitHub:** https://github.com/lusid1/pkg2zip
- **License:** Public Domain
- **Language:** C

## Features

- Decrypt PKG files using RAP/zRIF keys
- Extract to folder structure or ZIP
- PSP CSO compression support
- Fast C implementation

## Build Instructions

```bash
# First time setup
./clone.sh    # Clone source repository
./build.sh    # Build pkg2zip

# Updates
cd src && git pull
cd .. && ./build.sh
```

## Usage

```bash
# Extract PKG file (requires RAP key)
pkg2zip -x game.pkg "RAP_KEY_HEX_STRING"

# List PKG contents
pkg2zip -l game.pkg

# PSP: Create CSO instead of ISO
pkg2zip -x -c9 game.pkg "RAP_KEY"

# PSP: Extract as EBOOT.PBP
pkg2zip -x -p game.pkg "RAP_KEY"
```

## Integration with ROM Farmer

This tool will be used for:
1. **PS3 DLC/Update Installation:** Extract PKG files from NoPayStation archives
2. **PSP Minis:** Convert PKG to ISO/EBOOT
3. **Automated Patching:** Apply game updates during PS3 builds

## NoPayStation Keys

RAP keys are provided in NoPayStation TSV databases:
- `PS3_GAMES.tsv` - PS3 game licenses
- `PS3_DLCS.tsv` - PS3 DLC and update licenses
- `PSP_GAMES.tsv` - PSP game licenses

## Notes

- PKG files are encrypted with Sony's keys
- RAP/zRIF keys are license files extracted from real consoles
- For PS3, RAP keys are 32-character hex strings
- Some PKG files may have "MISSING" keys in database
