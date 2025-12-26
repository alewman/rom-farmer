# ROM Farmer

A powerful Python-based ROM collection management tool that helps you organize, validate, and optimize your retro gaming ROM libraries using DAT files from No-Intro and Redump.

## 🚀 Project Status

**Current Phase:** Phase 7 COMPLETE ✅ (Stage Integration)  
**Next Phase:** Phase 8 - Real-world validation  
**Target:** ROM Farmer 1.0 (21 platforms)

### Master Build System Progress

✅ **Phase 1-3:** Foundation (DAT parsing, filtering, config system)  
✅ **Phase 4:** Saturn/Redump CD processing (CHD, M3U)  
✅ **Phase 5A:** Wii/GameCube RVZ processing  
✅ **Phase 5B:** PS3 multi-target transformation  
✅ **Phase 6A:** Build configuration system  
✅ **Phase 6B:** Build orchestrator + CLI  
✅ **Phase 6C:** Platform processor integration  
✅ **Phase 7:** Intelligent stage routing  
⏳ **Phase 8:** End-to-end validation (next)

**Platforms Currently Working:**
- Sega Saturn (BIN/CUE → CHD + M3U)
- Nintendo Wii (RVZ extraction)
- Nintendo GameCube (RVZ extraction)
- Sony PlayStation 3 (ISO decrypt → 4 target formats)

**Build System Features:**
- Multi-platform orchestration
- Intelligent stage routing (SIMPLE/MEDIUM/COMPLEX/VERY_COMPLEX)
- Resume capability (handle interruptions)
- State persistence
- Multi-target output (one source → multiple formats)
- Override system (customize per build)

## Features

✨ **DAT File Management**
- Import and manage Logiqx XML DAT files (No-Intro, Redump)
- Support for parent-clone relationships
- Multi-region and multi-language ROM tracking
- Database-backed catalog with fast searching

🎯 **1G1R Filtering (One Game One ROM)**
- Intelligent filtering to keep the best version of each game
- Customizable region priorities (default: USA → World → Europe → Japan)
- Language preference support
- Parent ROM preference over clones
- Revision awareness (keeps latest versions)

🔍 **ROM Scanning & Validation**
- Parallel scanning with multi-threading
- CRC32, MD5, and SHA1 hash verification
- Match ROMs against imported DAT files
- Identify missing games from your collection
- Verify individual ROM files

📁 **ROM Organization**
- Organize by region (USA, Europe, Japan, etc.)
- Organize by ROM type (cartridge, disc, BIOS)
- Organize by language
- Multiple operation modes: MOVE, COPY, SYMLINK
- Keep-in-place option for non-matching files
- Pattern-based exclusions

🗜️ **Archive Processing**
- Extract archives (ZIP, 7Z, RAR) for processing
- Automatic cleanup of extracted files
- Support for nested archives

💿 **Disc Processing**
- Convert BIN/CUE to CHD format
- Generate M3U playlists for multi-disc games
- Apply patches (BPS, IPS, UPS, XDELTA)

🔗 **ARRM/ScreenScraper Compatibility**
- Automatic hash selection matching ARRM behavior
- Transformation chain tracking (source → compressed)
- Metadata lookup via MD5 chain for converted ROMs

## Technical Reference

### ARRM Hashing Behavior for Disc Systems

When working with CUE/BIN disc images, ARRM and ScreenScraper use different hashing strategies based on the disc type. ROM Farmer matches this behavior exactly to ensure metadata compatibility.

| Disc Type | Path Stored | MD5 Hashed | Reason |
|-----------|-------------|------------|--------|
| **Single-track** (1 .bin) | `.cue` | **BIN file** | CUE is trivial; BIN contains game data |
| **Multi-track** (2+ .bin) | `.cue` | **CUE file** | CUE describes disc layout |
| **ISO** | `.iso` | **ISO file** | Self-contained format |

**System Patterns:**

| System | Typical Format | Hash Method |
|--------|----------------|-------------|
| 3DO | Single-track | BIN |
| Dreamcast | Multi-track | CUE |
| Saturn | Multi-track | CUE |
| Mega CD | Mostly multi | CUE (mostly) |
| PC Engine CD | Mostly multi | CUE (mostly) |
| PS2 | Mixed | Detect & adapt |

This ensures that when ROM Farmer compresses CUE/BIN → CHD, the transformation chain correctly links back to metadata that ARRM has already scraped.

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/rom-farmer.git
cd rom-farmer

# Install dependencies
pip install -e .

# Verify installation
rom-farmer --help
```

### Basic Workflow

```bash
# 1. Import a DAT file
rom-farmer dat import /path/to/Nintendo\ -\ Game\ Boy.dat

# 2. Filter to 1G1R (One Game One ROM)
rom-farmer dat filter "Nintendo - Game Boy" --regions USA,World,Europe \
    --output filtered_games.txt

# 3. Scan your ROM collection
rom-farmer scan directory /path/to/roms/gb \
    --dat "Nintendo - Game Boy" --validate

# 4. Find missing games
rom-farmer scan missing /path/to/roms/gb \
    --dat "Nintendo - Game Boy" --output missing_games.txt

# 5. Organize your ROMs
rom-farmer organize region /path/to/roms/gb \
    --output /path/to/organized/gb --mode copy
```

## Documentation

- **[Installation Guide](docs/INSTALLATION.md)** - Detailed setup instructions
- **[User Guide](docs/USER_GUIDE.md)** - Complete command reference and examples
- **[Workflow Guide](docs/WORKFLOWS.md)** - End-to-end collection management workflows
- **[DAT Files Guide](docs/DAT_FILES.md)** - Working with No-Intro and Redump DATs
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

## Command Reference

### DAT Management

```bash
rom-farmer dat import <dat-file>           # Import DAT file
rom-farmer dat list                        # List imported DATs
rom-farmer dat info <dat-name>             # Show DAT details
rom-farmer dat games <dat-name>            # List games in DAT
rom-farmer dat search <dat-name> <query>   # Search for games
rom-farmer dat filter <dat-name>           # Filter to 1G1R
rom-farmer dat stats                       # Show statistics
rom-farmer dat delete <dat-name>           # Delete DAT
```

### ROM Scanning

```bash
rom-farmer scan directory <path>           # Scan ROM directory
rom-farmer scan missing <path>             # Find missing games
rom-farmer scan verify <file>              # Verify single ROM
```

### ROM Organization

```bash
rom-farmer organize region <path>          # Organize by region
rom-farmer organize kind <path>            # Organize by type
rom-farmer organize language <path>        # Organize by language
rom-farmer organize all <path>             # Run all organizers
```

## Requirements

- Python 3.10 or higher
- SQLite 3
- Optional: chdman (for CHD conversion)
- Optional: 7-Zip (for archive processing)

## Configuration

ROM Farmer creates configuration and database files in:

- **Linux/macOS**: `~/.config/romfarmer/`
- **Windows**: `%APPDATA%\romfarmer\`

Default configuration:

```yaml
# Default region priorities for 1G1R filtering
regions:
  - USA
  - World
  - Europe
  - Japan

# Default language priorities
languages:
  - En
  - Ja
  - Fr
  - De

# Scanner settings
scanner:
  threads: 4              # Parallel scanning threads
  chunk_size: 1048576     # File reading chunk size (1MB)

# Organization settings
organizer:
  default_mode: copy      # copy, move, or symlink
  keep_in_place: false    # Keep unmatched files in place
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=src/romfarmer --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Project Structure

```
rom-farmer/
├── src/romfarmer/          # Main source code
│   ├── catalog/             # Database models and operations
│   ├── cli/                 # Command-line interface
│   ├── core/                # Configuration and logging
│   ├── dat/                 # DAT parsing, filtering, importing
│   ├── models/              # Data models
│   ├── organizers/          # ROM organization logic
│   ├── parsers/             # Filename parsing
│   ├── processors/          # Archive and disc processing
│   └── scanner/             # ROM scanning and validation
├── tests/                   # Test suite (201 tests)
├── docs/                    # Documentation
└── pyproject.toml           # Project configuration
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

[Your License Here]

## Acknowledgments

- **No-Intro**: For maintaining accurate ROM DAT files
- **Redump**: For disc preservation DAT files
- **Igir**: Inspiration for ROM management workflows
- **Click**: Excellent CLI framework
- **Rich**: Beautiful terminal formatting

## Support

- Report bugs: [GitHub Issues](https://github.com/yourusername/rom-farmer/issues)
- Ask questions: [GitHub Discussions](https://github.com/yourusername/rom-farmer/discussions)
- Documentation: [docs/](docs/)

---

**Status**: ✅ Production Ready | **Tests**: 201 passing | **Coverage**: 63% overall, 83-98% on core modules
    regions: [usa, world]
    organize_languages: false
    
  nes-eng:
    regions: [europe, australia, world]
    organize_languages: true
    exclude_language_regions: [usa]
```

## Architecture

```
romfarmer/
├── cli/          # Click-based CLI interface
├── core/         # Configuration and logging
├── parsers/      # No-Intro, Redump, DAT parsers
├── organizers/   # Region, kind, language organizers
├── validators/   # Collection validation
├── catalog/      # Database models and queries
├── models/       # Pydantic data models
└── utils/        # Utilities and helpers
```

## Development

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov

# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type check
mypy src/
```

## Migration from Bash

The bash scripts remain available as high-level wrappers. Python implementation provides:

- 10x faster DAT file parsing
- SQL queries over collections
- Proper error handling and recovery
- Comprehensive test coverage
- Type safety and IDE support

## License

MIT
