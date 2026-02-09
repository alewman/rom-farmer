# ROM Farmer Python - Complete Workflow

## Overview

This document describes the complete end-to-end workflow for ROM collection management, from initial DAT files to organized, validated ROM collections ready for emulation.

## Workflow Phases

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ROM GROOMER WORKFLOW                                │
└─────────────────────────────────────────────────────────────────────────────┘

Phase 1: INITIALIZATION
  ├─ Download DAT files (No-Intro, Redump)
  ├─ Configure system preferences
  └─ Setup directory structure

Phase 2: DAT PROCESSING
  ├─ Parse XML DAT files
  ├─ Extract game metadata (CRC, MD5, SHA1, regions)
  ├─ Store in database
  └─ Generate filter lists (1G1R, region, language)

Phase 3: ROM SCANNING
  ├─ Scan source directories
  ├─ Parse ROM filenames
  ├─ Hash ROM files
  ├─ Match against DAT database
  └─ Identify gaps and extras

Phase 4: ROM PROCESSING
  ├─ Extract archives (.zip, .7z, .rar)
  ├─ Convert formats (.bin/.cue → .chd)
  ├─ Create playlists (.m3u for multi-disc)
  ├─ Decrypt (PS3, Xbox360, Wii U)
  └─ Compress (PSP ISO → CSO)

Phase 5: ORGANIZATION
  ├─ Apply filters (1G1R, region, language)
  ├─ Organize by region
  ├─ Organize by kind (Games/Demos/Applications)
  ├─ Generate symlinks
  └─ Create organized directory structure

Phase 6: VALIDATION
  ├─ Verify hashes
  ├─ Check for missing games
  ├─ Validate file integrity
  ├─ Generate reports
  └─ Identify duplicates

Phase 7: SCRAPING & METADATA
  ├─ Fetch box art
  ├─ Download game descriptions
  ├─ Generate gamelist.xml (EmulationStation)
  └─ Update metadata
```

## Detailed Workflow

### Phase 1: Initialization

**User Actions:**
```bash
# Initialize configuration
romfarmer init

# Download DAT files
romfarmer dat download --source nointro --systems nes,snes,gb,gba
romfarmer dat download --source redump --systems psx,ps2,segacd

# Configure preferences
romfarmer config set --disc-format chd
romfarmer config set --region-priority usa,europe,japan
romfarmer config set --language-priority english
```

**System Actions:**
1. Create config directory: `~/.config/romfarmer/`
2. Create database: `romfarmer.db`
3. Download DAT files to: `~/.local/share/romfarmer/dats/`
4. Create directory structure:
   ```
   /roms/
   ├── source/        # Original ROM files
   ├── processed/     # Converted ROMs (CHD, etc.)
   └── organized/     # Final organized collection
       ├── by-region/
       ├── by-kind/
       └── by-language/
   ```

**Output:**
- Configuration file created
- DAT files downloaded
- Database initialized
- Directory structure ready

---

### Phase 2: DAT Processing

**User Actions:**
```bash
# Import DAT files
romfarmer dat import --source nointro --system nes
romfarmer dat import --source redump --system psx

# Apply Retool filters (1G1R)
romfarmer dat filter --system nes --filter 1g1r --region usa

# View DAT statistics
romfarmer dat stats --system nes
```

**System Actions:**
1. Parse XML DAT file
   ```python
   # Parse Logiqx XML
   dat = parse_dat_file("Nintendo - Nintendo Entertainment System (20241001).dat")
   # Extract games:
   # - name, description, region, language
   # - rom: name, size, crc, md5, sha1
   ```

2. Store in database
   ```python
   # Store each game
   for game in dat.games:
       db.add_game(
           system="nes",
           name=game.name,
           region=game.region,
           crc32=game.rom.crc,
           md5=game.rom.md5,
           sha1=game.rom.sha1,
           size=game.rom.size
       )
   ```

3. Apply filters (using Retool)
   ```python
   # Generate 1G1R filtered DAT
   retool --input nointro/nes.dat \
          --output nointro.retool.1g1r.usa/nes.dat \
          --1g1r --region usa
   ```

4. Create filter lists
   ```python
   # Generate inclusion/exclusion lists
   games_to_keep = filter_1g1r_usa(all_games)
   save_list("filters/nes.usa.1g1r.txt", games_to_keep)
   ```

**Output:**
- Games stored in database
- Filtered DAT files created
- Filter lists generated
- Statistics available

---

### Phase 3: ROM Scanning

**User Actions:**
```bash
# Scan source directory
romfarmer scan /data/roms/source/nes/ --system nes

# View scan results
romfarmer scan report --system nes

# List missing games
romfarmer scan missing --system nes --filter 1g1r-usa
```

**System Actions:**
1. Discover ROM files
   ```python
   # Find all ROM files
   for file in scan_directory("/data/roms/source/nes/"):
       if file.suffix in ['.nes', '.zip', '.7z']:
           roms.append(file)
   ```

2. Parse filenames
   ```python
   # Use No-Intro parser
   parser = get_parser('nointro')
   for rom_file in roms:
       rom = parser.parse(rom_file.name)
       # Extract: name, region, language, revision, tags
   ```

3. Hash files
   ```python
   # Calculate hashes
   for rom_file in roms:
       hashes = calculate_hashes(rom_file)
       # CRC32, MD5, SHA1
   ```

4. Match against database
   ```python
   # Find matching DAT entry
   for rom_file in roms:
       match = db.find_by_hash(
           crc32=rom.crc32,
           system='nes'
       )
       if match:
           rom.dat_match = match
           rom.verified = True
   ```

5. Generate reports
   ```python
   # Report statistics
   total_games = count_games_in_dat('nes', filter='1g1r-usa')
   found_games = count_matched_roms('nes')
   missing_games = total_games - found_games
   
   print(f"Collection: {found_games}/{total_games} ({percent}%)")
   print(f"Missing: {len(missing_games)} games")
   ```

**Output:**
- ROM inventory created
- Hash database populated
- Verification status per ROM
- Collection statistics
- Missing game list

---

### Phase 4: ROM Processing

**User Actions:**
```bash
# Process cartridge ROMs (simple extraction)
romfarmer process --system nes --profile nes /data/roms/source/nes/

# Process disc ROMs (extract + CHD + M3U)
romfarmer process --system psx --profile psx /data/roms/source/psx/

# Process with decryption (PS3)
romfarmer process --system ps3 --profile ps3_batocera /data/roms/source/ps3/

# Batch process multiple systems
romfarmer process --batch --systems nes,snes,gb,gba,psx,ps2
```

**System Actions:**

**Cartridge ROMs (NES, SNES, GB, GBA, etc.):**
```python
# Pipeline: extract_archive
processor = get_processor('nes')
result = processor.process(
    input_path=Path("Super Mario Bros (USA).zip"),
    output_dir=Path("/roms/processed/nes/")
)
# Output: Super Mario Bros (USA).nes
```

**Disc ROMs - Single Disc (PSX):**
```python
# Pipeline: extract_archive → bin_cue_to_chd
processor = get_processor('psx')
result = processor.process(
    input_path=Path("Metal Gear Solid (USA).zip"),
    output_dir=Path("/roms/processed/psx/")
)
# Output: Metal Gear Solid (USA).chd
```

**Disc ROMs - Multi-Disc (PSX):**
```python
# Pipeline: extract_archive → bin_cue_to_chd → create_m3u_playlist
# Process all 3 discs
for disc in [1, 2, 3]:
    processor.process(
        input_path=Path(f"FF VII (USA) (Disc {disc}).zip"),
        output_dir=Path("/roms/processed/psx/")
    )

# Output:
# - Final Fantasy VII (USA).m3u
# - Final Fantasy VII (USA) (Disc 1).chd
# - Final Fantasy VII (USA) (Disc 2).chd
# - Final Fantasy VII (USA) (Disc 3).chd
```

**Advanced - PS3 Decryption (Batocera):**
```python
# Pipeline: extract_archive → ps3_decrypt → ps3_to_squashfs
processor = get_processor('ps3_batocera')
result = processor.process(
    input_path=Path("Gran Turismo 5 (USA).pkg"),
    output_dir=Path("/roms/processed/ps3/")
)
# Output: Gran Turismo 5 (USA).sqfs (compressed)
```

**Advanced - PS3 for RPCS3:**
```python
# Pipeline: extract_archive → ps3_decrypt
# (no compression - RPCS3 wants folder format)
processor = get_processor('ps3_rpcs3')
result = processor.process(
    input_path=Path("Gran Turismo 5 (USA).pkg"),
    output_dir=Path("/roms/processed/ps3/")
)
# Output: Gran Turismo 5 (USA).jb/ (folder)
```

**Output:**
- Extracted ROM files
- Converted formats (CHD, CSO, SquashFS)
- Multi-disc playlists (.m3u)
- Decrypted games (PS3, Xbox360, Wii U)
- Processing logs and reports

---

### Phase 5: Organization

**User Actions:**
```bash
# Organize by region
romfarmer organize --system nes --by region --filter 1g1r-usa

# Organize by kind (Games/Demos/Applications)
romfarmer organize --system nes --by kind

# Organize by language
romfarmer organize --system psx --by language --languages english,japanese

# Use symlinks (don't duplicate files)
romfarmer organize --system nes --by region --symlink

# Generate complete organized collection
romfarmer organize --batch --all-systems --by region --filter 1g1r-usa
```

**System Actions:**

**Organize by Region:**
```python
# Create region-based organization
organizer = RegionOrganizer(
    region_priority=['usa', 'europe', 'japan']
)

for rom in processed_roms:
    if 'usa' in rom.regions:
        dest = Path("/roms/organized/by-region/usa/nes/")
    elif 'europe' in rom.regions:
        dest = Path("/roms/organized/by-region/europe/nes/")
    # ... etc
    
    # Create symlink or copy
    create_symlink(rom.path, dest / rom.filename)
```

**Directory Structure:**
```
/roms/organized/by-region/
├── usa/
│   ├── nes/
│   │   ├── Super Mario Bros (USA).nes
│   │   ├── The Legend of Zelda (USA).nes
│   │   └── ...
│   ├── snes/
│   ├── gb/
│   └── psx/
│       ├── Final Fantasy VII (USA).m3u
│       ├── Metal Gear Solid (USA).chd
│       └── ...
├── europe/
│   ├── nes/
│   ├── snes/
│   └── ...
└── japan/
    └── ...
```

**Organize by Kind:**
```python
# Organize by ROM kind/category
organizer = KindOrganizer()

for rom in processed_roms:
    if rom.kind == RomKind.GAME:
        dest = Path("/roms/organized/by-kind/Games/nes/")
    elif rom.kind == RomKind.DEMO:
        dest = Path("/roms/organized/by-kind/Demos/nes/")
    # ... etc
```

**Directory Structure:**
```
/roms/organized/by-kind/
├── Games/
│   ├── nes/
│   ├── snes/
│   └── ...
├── Demos/
│   ├── nes/
│   └── ...
├── Applications/
├── Educational/
└── Prerelease/
    └── ...
```

**Organize by Language:**
```python
# Organize multi-language ROMs
organizer = LanguageOrganizer(
    language_priority=['english', 'japanese', 'french']
)

for rom in processed_roms:
    if RomLanguage.ENGLISH in rom.languages:
        dest = Path("/roms/organized/by-language/english/psx/")
    # ... etc
```

**1G1R Filtering:**
```python
# Apply 1 Game 1 ROM filter
filter_config = FilterConfig(
    region_priority=['usa', 'europe', 'world', 'japan'],
    language_priority=['english'],
    prefer_revision='latest',
    exclude_kinds=[RomKind.DEMO, RomKind.PROMOTIONAL]
)

# For each game title, keep only the best ROM
organized_roms = apply_1g1r_filter(all_roms, filter_config)
```

**Output:**
- Organized directory structure
- Symlinks or copies
- EmulationStation-ready structure
- Filtered collections (1G1R)
- Organization reports

---

### Phase 6: Validation

**User Actions:**
```bash
# Validate entire collection
romfarmer validate --system nes

# Verify hashes against DAT
romfarmer validate --system psx --check-hashes

# Find duplicates
romfarmer validate --find-duplicates --system nes

# Check for corruption
romfarmer validate --integrity --system psx

# Generate validation report
romfarmer validate --report --output validation-report.html
```

**System Actions:**

**Hash Verification:**
```python
# Verify ROM hashes against DAT
validator = HashValidator()

for rom in collection:
    # Calculate hash
    calculated_hash = calculate_crc32(rom.path)
    
    # Compare with DAT
    dat_entry = db.find_game(rom.name, rom.system)
    
    if calculated_hash == dat_entry.crc32:
        rom.status = "VERIFIED"
    else:
        rom.status = "HASH_MISMATCH"
        issues.append(f"{rom.name}: Hash mismatch!")
```

**Collection Completeness:**
```python
# Check for missing games
validator = CollectionValidator(filter='1g1r-usa')

expected_games = db.get_filtered_games('nes', '1g1r-usa')
found_games = scan_organized_collection('nes')

missing = expected_games - found_games
extra = found_games - expected_games

print(f"Expected: {len(expected_games)}")
print(f"Found: {len(found_games)}")
print(f"Missing: {len(missing)}")
print(f"Extra: {len(extra)}")
```

**Duplicate Detection:**
```python
# Find duplicate ROMs by hash
duplicates = find_duplicates_by_hash(collection)

for hash_value, roms in duplicates.items():
    if len(roms) > 1:
        print(f"Duplicate found: {hash_value}")
        for rom in roms:
            print(f"  - {rom.path}")
```

**Integrity Checking:**
```python
# Check file integrity (can files be read?)
for rom in collection:
    try:
        # Try to open and read
        with rom.path.open('rb') as f:
            f.read(1024)  # Read first KB
        rom.integrity = "OK"
    except Exception as e:
        rom.integrity = "CORRUPTED"
        issues.append(f"{rom.name}: {e}")
```

**Generate Report:**
```python
# Create validation report
report = ValidationReport()
report.add_section("Collection Statistics", stats)
report.add_section("Hash Verification", hash_results)
report.add_section("Missing Games", missing_games)
report.add_section("Duplicates", duplicates)
report.add_section("Issues", issues)
report.save_html("validation-report.html")
```

**Output:**
- Validation status per ROM
- Hash verification results
- Missing game list
- Duplicate list
- Integrity report
- HTML/JSON reports

---

### Phase 7: Scraping & Metadata

**User Actions:**
```bash
# Scrape metadata from online sources
romfarmer scrape --system nes --source screenscraper

# Download box art
romfarmer scrape --system psx --media box-art,screenshot

# Generate EmulationStation gamelist.xml
romfarmer scrape --system nes --generate-gamelist

# Update existing metadata
romfarmer scrape --update --system snes
```

**System Actions:**

**Fetch Metadata:**
```python
# Scrape from ScreenScraper, TheGamesDB, etc.
scraper = ScreenScraper(api_key=config.api_key)

for rom in collection:
    metadata = scraper.fetch_game_data(
        game_name=rom.name,
        system='nes',
        rom_hash=rom.crc32
    )
    
    # Update database
    db.update_metadata(
        rom_id=rom.id,
        description=metadata.description,
        genre=metadata.genre,
        players=metadata.players,
        release_date=metadata.release_date,
        developer=metadata.developer,
        publisher=metadata.publisher
    )
```

**Download Media:**
```python
# Download box art, screenshots, videos
for rom in collection:
    # Box art (front cover)
    box_art_url = metadata.get_box_art_url()
    download_media(
        url=box_art_url,
        dest=Path(f"/roms/organized/nes/media/box-art/{rom.name}.png")
    )
    
    # Screenshot
    screenshot_url = metadata.get_screenshot_url()
    download_media(
        url=screenshot_url,
        dest=Path(f"/roms/organized/nes/media/screenshots/{rom.name}.png")
    )
```

**Generate EmulationStation gamelist.xml:**
```python
# Create gamelist.xml for EmulationStation
gamelist = GameListXML()

for rom in collection:
    gamelist.add_game(
        path=f"./{rom.filename}",
        name=rom.name,
        desc=rom.description,
        image=f"./media/box-art/{rom.name}.png",
        rating=rom.rating,
        releasedate=rom.release_date,
        developer=rom.developer,
        publisher=rom.publisher,
        genre=rom.genre,
        players=rom.players
    )

gamelist.save("/roms/organized/nes/gamelist.xml")
```

**Example gamelist.xml:**
```xml
<?xml version="1.0"?>
<gameList>
    <game>
        <path>./Super Mario Bros (USA).nes</path>
        <name>Super Mario Bros.</name>
        <desc>A classic platformer featuring Mario and Luigi...</desc>
        <image>./media/box-art/Super Mario Bros.png</image>
        <releasedate>19850913T000000</releasedate>
        <developer>Nintendo</developer>
        <publisher>Nintendo</publisher>
        <genre>Platform</genre>
        <players>2</players>
    </game>
    <!-- ... more games ... -->
</gameList>
```

**Output:**
- Game descriptions and metadata
- Box art images
- Screenshots
- Videos (optional)
- gamelist.xml files
- Updated database

---

## Complete Example Workflow

```bash
# 1. INITIALIZATION
romfarmer init
romfarmer dat download --source nointro --systems nes,snes,gb,gba,psx

# 2. DAT PROCESSING
romfarmer dat import --all
romfarmer dat filter --system nes --filter 1g1r --region usa

# 3. ROM SCANNING
romfarmer scan /data/roms/source/ --all-systems
romfarmer scan report --system nes

# 4. ROM PROCESSING
romfarmer process --batch --all-systems --parallel 4

# 5. ORGANIZATION
romfarmer organize --all-systems --by region --filter 1g1r-usa --symlink

# 6. VALIDATION
romfarmer validate --all-systems --check-hashes
romfarmer validate --report --output validation-report.html

# 7. SCRAPING
romfarmer scrape --all-systems --source screenscraper --generate-gamelist

# DONE! Collection ready for EmulationStation/Batocera/RetroPie
```

**Final Directory Structure:**
```
/roms/organized/by-region/usa/
├── nes/
│   ├── gamelist.xml
│   ├── media/
│   │   ├── box-art/
│   │   └── screenshots/
│   ├── Super Mario Bros (USA).nes
│   ├── The Legend of Zelda (USA).nes
│   └── ...
├── snes/
│   ├── gamelist.xml
│   ├── media/
│   └── ...
├── psx/
│   ├── gamelist.xml
│   ├── media/
│   ├── Final Fantasy VII (USA).m3u
│   ├── Final Fantasy VII (USA) (Disc 1).chd
│   ├── Final Fantasy VII (USA) (Disc 2).chd
│   ├── Final Fantasy VII (USA) (Disc 3).chd
│   └── ...
└── ...
```

**Ready to use in:**
- EmulationStation
- Batocera
- RetroPie
- RetroArch
- Any emulation frontend!

---

## Next Steps

Now that we have the complete workflow mapped out, we can prioritize implementation:

1. **Phase 2 (DAT Processing)** - Parse XML DATs, store in database
2. **Phase 3 (ROM Scanning)** - Hash files, match against DATs
3. **Phase 5 (Organization)** - Implement organizers (region, kind, language)
4. **Phase 6 (Validation)** - Hash verification, completeness checking
5. **Phase 7 (Scraping)** - Metadata fetching, gamelist.xml generation

The foundation (parsers, processors, database) is already solid! 🚀
