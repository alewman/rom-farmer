# DAT Files Guide

Everything you need to know about working with DAT files in ROM Farmer.

## Table of Contents

- [What are DAT Files?](#what-are-dat-files)
- [DAT Sources](#dat-sources)
- [DAT Formats](#dat-formats)
- [Obtaining DAT Files](#obtaining-dat-files)
- [Importing DATs](#importing-dats)
- [Understanding DAT Contents](#understanding-dat-contents)
- [1G1R Filtering](#1g1r-filtering)
- [Best Practices](#best-practices)

## What are DAT Files?

DAT files are XML databases that catalog known good ROM dumps. They contain:

- **Game names** in standardized format
- **File hashes** (CRC32, MD5, SHA1) for verification
- **File sizes** for validation
- **Region information** (USA, Europe, Japan, etc.)
- **Language information** (En, Ja, Fr, De, etc.)
- **Version information** (Rev 1, v1.0, etc.)
- **Parent-clone relationships** (original vs variants)

### Why Use DAT Files?

1. **Verify authenticity**: Confirm ROMs match known good dumps
2. **Detect bad dumps**: Find corrupted or modified files
3. **Organize collections**: Use standardized naming
4. **Find missing games**: Compare your collection to complete sets
5. **Filter duplicates**: Apply 1G1R (One Game One ROM) filtering

## DAT Sources

### No-Intro

**Best for**: Cartridge-based systems

**Systems covered:**
- Nintendo: NES, SNES, GB, GBC, GBA, N64, DS, 3DS
- Sega: Master System, Genesis/Mega Drive, Game Gear, Saturn
- Sony: PlayStation Portable
- Atari: 2600, 5200, 7800, Lynx, Jaguar
- NEC: TurboGrafx-16/PC Engine
- SNK: Neo Geo Pocket
- And many more...

**Website**: https://datomatic.no-intro.org/

**Characteristics:**
- Focuses on unmodified, official releases
- Excludes hacks, translations, and homebrew
- Standardized naming conventions
- Regular updates (monthly releases)
- Parent-clone relationship tracking

### Redump

**Best for**: Disc-based systems

**Systems covered:**
- Sony: PlayStation, PlayStation 2, PSP (UMD)
- Sega: Saturn, Dreamcast, Mega CD
- NEC: PC Engine CD, TurboGrafx CD
- Nintendo: GameCube, Wii
- Microsoft: Xbox, Xbox 360
- And more...

**Website**: http://redump.org/

**Characteristics:**
- Focuses on optical disc preservation
- Includes checksums for disc images and tracks
- Multiple dump methods supported
- Regional variants cataloged
- Multi-disc game tracking

### TOSEC

**Best for**: Comprehensive collections including homebrews

**Characteristics:**
- Includes commercial, homebrew, demos, etc.
- Less strict verification than No-Intro/Redump
- Broader scope but less standardized

**Note**: ROM Farmer is optimized for No-Intro/Redump Logiqx XML format.

## DAT Formats

### Logiqx XML (Supported)

ROM Farmer supports the standard Logiqx XML format used by No-Intro and Redump.

**Structure:**
```xml
<?xml version="1.0"?>
<!DOCTYPE datafile PUBLIC "-//Logiqx//DTD ROM Management Datafile//EN" 
    "http://www.logiqx.com/Dats/datafile.dtd">
<datafile>
    <header>
        <name>Nintendo - Game Boy</name>
        <description>Nintendo Game Boy ROMs</description>
        <version>20230915</version>
        <author>No-Intro</author>
    </header>
    <game name="Pokemon - Red Version (USA)">
        <description>Pokemon - Red Version (USA)</description>
        <rom name="Pokemon - Red Version (USA).gb" 
             size="1048576" 
             crc="3d45c1ee" 
             md5="3d45c1ee9b80b4d6a83e5c1a3f4a8b2c"
             sha1="d9e5cf6b3a2f8c7e1b4a5d9c8b7a6e5f4d3c2b1a"/>
    </game>
    <!-- More games... -->
</datafile>
```

### Other Formats (Not Supported)

- **ClrMamePro**: Different format, needs conversion
- **RomCenter**: Different format, needs conversion
- **MAME XML**: Game-specific format

**Converting to Logiqx**: Use tools like DatUtil or RomVault to convert.

## Obtaining DAT Files

### No-Intro DATs

1. **Visit**: https://datomatic.no-intro.org/
2. **Navigate** to "DAT-o-MATIC" section
3. **Select** your system (e.g., "Nintendo - Game Boy")
4. **Choose** "Daily" (most recent) or "Standard" (stable)
5. **Download** the `.dat` file

**Recommended DATs for popular systems:**
```bash
# Nintendo
Nintendo - Game Boy.dat
Nintendo - Game Boy Color.dat
Nintendo - Game Boy Advance.dat
Nintendo - Nintendo Entertainment System.dat
Nintendo - Super Nintendo Entertainment System.dat

# Sega
Sega - Master System - Mark III.dat
Sega - Mega Drive - Genesis.dat
Sega - Game Gear.dat

# Sony
Sony - PlayStation Portable.dat
```

### Redump DATs

1. **Visit**: http://redump.org/downloads/
2. **Select** system category
3. **Download** appropriate `.dat` file

**Recommended for disc systems:**
```bash
Sony - PlayStation.dat
Sony - PlayStation 2.dat
Sega - Dreamcast.dat
Sega - Saturn.dat
Nintendo - GameCube.dat
```

### Organizing DAT Files

Create a organized DAT library:

```bash
mkdir -p ~/dats/{nointro,redump,tosec}

# Store by source
~/dats/nointro/Nintendo - Game Boy.dat
~/dats/nointro/Sega - Genesis.dat
~/dats/redump/Sony - PlayStation.dat
```

## Importing DATs

### Basic Import

```bash
# Single DAT
rom-farmer dat import ~/dats/nointro/Nintendo\ -\ Game\ Boy.dat

# Multiple DATs
rom-farmer dat import ~/dats/nointro/*.dat

# With verbose output
rom-farmer dat import ~/dats/nointro/Nintendo\ -\ Game\ Boy.dat --verbose
```

### Updating DATs

When a new version is released:

```bash
# Re-import with --update flag
rom-farmer dat import ~/dats/nointro/Nintendo\ -\ Game\ Boy.dat --update
```

This will:
- Remove old games from previous version
- Import new games from current version
- Update game information
- Preserve database integrity

### Verifying Import

```bash
# List all imported DATs
rom-farmer dat list

# Check specific DAT details
rom-farmer dat info "Nintendo - Game Boy"

# View game count
rom-farmer dat stats
```

## Understanding DAT Contents

### Parent-Clone Relationships

Games have parent-clone hierarchies:

**Example: Super Mario Bros.**
- **Parent**: `Super Mario Bros. (World)`
- **Clones**:
  - `Super Mario Bros. (USA)`
  - `Super Mario Bros. (Europe)`
  - `Super Mario Bros. (Japan)`
  - `Super Mario Bros. (USA, Europe) (Rev 1)`

**Why it matters:**
- Parents are usually the "main" version
- Clones are regional variants or revisions
- 1G1R filtering prefers parents over clones

### Region Tags

Common region codes in DAT files:

| Tag | Region |
|-----|--------|
| `(World)` | Released worldwide |
| `(USA)` | United States |
| `(Europe)` | Europe |
| `(Japan)` | Japan |
| `(USA, Europe)` | Released in multiple regions |
| `(En)` | English language |
| `(Ja)` | Japanese language |
| `(Asia)` | Asian release |
| `(Australia)` | Australia |
| `(Germany)` | Germany |
| `(France)` | France |

### Revision Tags

Version and revision markers:

| Tag | Meaning |
|-----|---------|
| `(Rev 1)`, `(Rev 2)` | Hardware revision |
| `(v1.0)`, `(v1.1)` | Software version |
| `(Beta)` | Pre-release beta version |
| `(Proto)` | Prototype version |
| `(Demo)` | Demo version |
| `(Sample)` | Sample/preview version |

### Special Tags

Other important markers:

| Tag | Meaning |
|-----|---------|
| `[BIOS]` | System BIOS file |
| `[!]` | Verified good dump |
| `[b]` | Bad dump |
| `[h]` | Hack |
| `[t]` | Translation |
| `[o]` | Overdump |

**Note**: No-Intro DATs only include verified good dumps, so `[b]`, `[h]`, `[t]` typically won't appear.

### Multi-Disc Games

Disc-based games with multiple discs:

```
Final Fantasy VII (USA) (Disc 1)
Final Fantasy VII (USA) (Disc 2)
Final Fantasy VII (USA) (Disc 3)
```

These are separate entries in the DAT but represent one game.

## 1G1R Filtering

1G1R (One Game One ROM) filtering reduces your collection to the best version of each game.

### How 1G1R Works

ROM Farmer applies weighted scoring:

1. **Region priority** (weight: 1000x)
   - Highest priority region gets best score
   - Example: USA=1000, World=999, Europe=998, Japan=997

2. **Language priority** (weight: 100x)
   - Preferred language gets bonus
   - Example: En=100, Ja=99, Fr=98

3. **Parent vs Clone** (weight: 10x)
   - Parents score higher than clones
   - Ensures "main" version selected

4. **Revision** (weight: 1x)
   - Newer revisions score higher
   - Rev 2 > Rev 1, v1.1 > v1.0

### Default 1G1R Settings

```bash
rom-farmer dat filter "Nintendo - Game Boy" \
    --regions USA,World,Europe,Japan \
    --languages En,Ja,Fr,De \
    --prefer-parent \
    --prefer-revisions
```

**Default priorities:**
- **Regions**: USA → World → Europe → Japan → Others
- **Languages**: English → Japanese → French → German → Others
- **Parent preferred**: Yes
- **Latest revision**: Yes

### Customizing 1G1R

**USA-only collection:**
```bash
rom-farmer dat filter "Nintendo - Game Boy" \
    --regions USA \
    --output gb_usa.txt
```

**Europe-first collection:**
```bash
rom-farmer dat filter "Nintendo - Game Boy" \
    --regions Europe,World,USA \
    --output gb_europe.txt
```

**Japan-focused collection:**
```bash
rom-farmer dat filter "Nintendo - Game Boy" \
    --regions Japan,World \
    --languages Ja,En \
    --output gb_japan.txt
```

**Multi-language collection:**
```bash
rom-farmer dat filter "Nintendo - Game Boy" \
    --regions World,USA,Europe \
    --languages En,Es,Fr,De,It \
    --output gb_multi.txt
```

### 1G1R Results

**Example: Pokemon Red**

Before 1G1R:
```
Pokemon - Red Version (USA)
Pokemon - Red Version (Europe)
Pokemon - Red Version (Australia)
Pokemon - Red Version (USA) (Rev 1)
Pokemon - Red Version (Japan)
```

After 1G1R (USA priority):
```
Pokemon - Red Version (USA) (Rev 1)  ← Kept (USA region + latest revision)
```

**Why kept:**
- USA region (highest priority)
- Rev 1 (latest revision)
- Parent ROM

### Verifying 1G1R Results

```bash
# Apply filter
rom-farmer dat filter "Nintendo - Game Boy" \
    --regions USA,World \
    --output gb_1g1r.txt

# Check what was filtered out
grep "filtered out" gb_1g1r.txt

# Scan collection against filtered list
rom-farmer scan missing ~/roms/gb \
    --dat "Nintendo - Game Boy" \
    --filter-1g1r
```

## Best Practices

### DAT Management

1. **Keep DATs organized:**
   ```bash
   ~/dats/
   ├── nointro/
   │   ├── Nintendo - Game Boy.dat
   │   └── Sega - Genesis.dat
   └── redump/
       └── Sony - PlayStation.dat
   ```

2. **Update regularly:**
   - Check for new DAT versions monthly
   - No-Intro releases updated DATs regularly
   - Re-import with `--update` flag

3. **Document your DAT versions:**
   ```bash
   rom-farmer dat list > ~/dats/imported_$(date +%Y%m%d).txt
   ```

### Collection Building

1. **Import DAT first:**
   ```bash
   rom-farmer dat import system.dat
   ```

2. **Scan existing collection:**
   ```bash
   rom-farmer scan directory ~/roms --validate
   ```

3. **Apply 1G1R if desired:**
   ```bash
   rom-farmer dat filter "System Name" --output filtered.txt
   ```

4. **Find missing games:**
   ```bash
   rom-farmer scan missing ~/roms --filter-1g1r
   ```

### Validation Strategy

1. **Initial validation:**
   ```bash
   # Full scan with CRC checking
   rom-farmer scan directory ~/roms \
       --dat "System" --validate
   ```

2. **Regular checks:**
   ```bash
   # Monthly validation
   rom-farmer scan directory ~/roms \
       --dat "System" --validate \
       --output ~/reports/$(date +%Y%m%d).txt
   ```

3. **Quick checks:**
   ```bash
   # Just count files, no CRC
   rom-farmer scan directory ~/roms
   ```

### Multiple DATs

For complete libraries:

```bash
#!/bin/bash
# Import all Nintendo DATs
for dat in ~/dats/nointro/Nintendo*.dat; do
    rom-farmer dat import "$dat" --update
done

# Generate 1G1R for each
for dat in ~/dats/nointro/Nintendo*.dat; do
    system=$(basename "$dat" .dat)
    rom-farmer dat filter "$system" \
        --output "~/lists/${system}_1g1r.txt"
done
```

### Disc-Based Systems

Special considerations:

```bash
# Use Redump DATs
rom-farmer dat import ~/dats/redump/Sony\ -\ PlayStation.dat

# Validate disc images
rom-farmer scan directory ~/roms/psx \
    --dat "Sony - PlayStation" \
    --validate

# Keep multi-disc games together
rom-farmer organize kind ~/roms/psx \
    --output ~/organized/psx \
    --keep-in-place
```

## Advanced Topics

### Custom Region Priorities

Create region sets for specific needs:

**North America focus:**
```bash
--regions USA,Canada,Mexico,World
```

**PAL regions:**
```bash
--regions Europe,Australia,World
```

**Japanese imports:**
```bash
--regions Japan,Asia,World
```

### Mixing DAT Sources

Can you use No-Intro and Redump together?

**Yes**, but:
- Import separately
- Don't mix cartridge and disc DATs for same system
- Keep organized by source

### Excluding Unwanted Games

Use 1G1R to filter, then manually exclude:

```bash
# Generate 1G1R list
rom-farmer dat filter "System" --output all_games.txt

# Edit to remove unwanted (sports, etc.)
vim all_games.txt

# Use as reference for collection building
```

## Resources

### DAT Resources

- **No-Intro**: https://datomatic.no-intro.org/
- **Redump**: http://redump.org/
- **Logiqx**: http://www.logiqx.com/ (DAT format specification)
- **DAT-o-MATIC**: https://datomatic.no-intro.org/

### Tools

- **ROM Farmer**: This tool!
- **CLRMamePro**: Windows ROM management
- **ROM Vault**: .NET-based ROM management
- **Universal ROM Cleaner**: ROM renaming utility

### Community

- **No-Intro Forum**: Discussion and support
- **Redump Forum**: Disc preservation community
- **/r/Roms**: Reddit community (follow rules!)

## Next Steps

Now that you understand DAT files:

1. Download DATs for your systems
2. Import into ROM Farmer
3. Scan and validate your collection
4. Apply 1G1R filtering if desired
5. Organize your curated collection

See also:
- [User Guide](USER_GUIDE.md) - Complete command reference
- [Workflow Guide](WORKFLOWS.md) - End-to-end examples
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues
