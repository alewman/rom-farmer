# ROM List Files

This directory contains list files that control ROM processing during the organization workflow. List files use specific naming patterns with delimiters to determine how ROMs are processed.

## File Naming Convention

List files follow the pattern: `{system}{delimiter}{list-name}`

Where:
- **{system}**: The gaming system (e.g., `nes`, `snes`, `sega32x`, `psx`)
- **{delimiter}**: One of three special characters that determines processing behavior
- **{list-name}**: Descriptive name for the list (spaces replaced with hyphens)

## Three Processing Strategies

### 1. Delete Strategy: `-` (Minus/Hyphen)

**Purpose**: Remove problematic or unwanted ROMs from the collection

**Naming Pattern**: `{system}-{list-name}`

**Examples**:
- `nes-Problematic-Games`
- `snes-Delete-Homebrew`
- `psx-Remove-Demos`

**Processing**: 
- Executed in **Step 3** (Delete Problematic ROMs)
- Removes files listed in the file from the filtered ROM directory
- Happens **before** copying to organization directory (efficient deletion)

**Use Cases**:
- Remove known problematic ROMs that cause emulator crashes
- Delete unwanted categories (demos, betas, pirate carts)
- Clean up ROM sets by removing duplicates or bad dumps

---

### 2. Add from Myrient: `+` (Plus)

**Purpose**: Add additional ROMs from the main myrient source archive

**Naming Pattern**: `{system}+{list-name}`

**Examples**:
- `nes+Best-Games`
- `sega32x+Hidden-Gems`
- `psx+Must-Play-RPGs`

**Processing**:
- Executed in **Step 7** (Add Extra Games)
- Links ROMs from the myrient source directory (`/data/emu/source/myrient.erista.me/files/...`)
- Creates symbolic links in organized collection under `{list-name}` subdirectory

**Use Cases**:
- Create curated "Best Games" collections
- Add games that were filtered out but are worth keeping
- Create themed collections (RPGs, Platformers, etc.)

---

### 3. Add from Extra: `.` (Dot/Period)

**Purpose**: Add ROMs from custom/extra sources (homebrew, hacks, translations)

**Naming Pattern**: `{system}.{list-name}`

**Examples**:
- `sega32x.Best-Games`
- `nes.English-Translations`
- `snes.Homebrew-Collection`

**Processing**:
- Executed in **Step 7** (Add Extra Games)
- Links ROMs from the extra directory (`/data/emu/source/extra/{system}/`)
- Creates symbolic links in organized collection under `{list-name}` subdirectory

**Use Cases**:
- Add homebrew games not available in myrient
- Include ROM hacks and fan translations
- Add custom or modified ROMs
- Include games from other sources

## File Format

Each list file contains one ROM filename per line:

```
Game Title (Region) (Version).zip
Another Game (USA).zip
Third Game (Japan).zip
```

**Important Notes**:
- Filenames must match exactly (case-sensitive)
- Include file extensions (.zip, .7z, etc.)
- Empty lines are ignored
- No wildcards or patterns - exact filenames only

## Processing Order

1. **Step 3**: Process `-` files (deletion from filtered directory)
2. **Step 4**: Copy filtered ROMs to organization directory
3. **Step 7**: Process `+` files (add from myrient) and `.` files (add from extra)

## Directory Structure Impact

After processing, your organized ROM collection will have this structure:

```
/data/emu/org/{system}.{filter}/
├── By Language/
│   ├── En/
│   ├── Ja/
│   └── ...
├── Best Games/              # From +Best-Games list
├── Homebrew Collection/     # From .Homebrew-Collection list
└── English Translations/    # From .English-Translations list
```

## Example Workflow

For NES ROMs:

1. **`nes-Problematic-Games`**: Remove 26 problematic pirate/aftermarket ROMs
2. **`nes+Best-Games`**: Add 50 must-play games from myrient archive
3. **`nes.Homebrew-Collection`**: Add 10 homebrew games from extra directory

Result: Clean NES collection with language organization plus curated subcollections.

## Best Practices

- **Be specific with names**: Use descriptive list names that clearly indicate content
- **Keep lists focused**: Create multiple smaller lists rather than one large list
- **Test with small lists**: Verify behavior with a few ROMs before creating large lists
- **Document your choices**: Consider keeping notes about why certain ROMs were included/excluded

## Troubleshooting

- **Files not found**: Check exact filename matching (case-sensitive)
- **No files deleted**: ROMs may have already been filtered out in Step 2
- **Links not created**: Verify source directories exist and contain the listed files
- **Wrong directory**: Ensure list filename follows correct naming pattern
