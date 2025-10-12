# ROM Groomer

A powerful Python-based ROM collection management tool that helps you organize, validate, and optimize your retro gaming ROM libraries using DAT files from No-Intro and Redump.

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

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/rom-groomer-python.git
cd rom-groomer-python

# Install dependencies
pip install -e .

# Verify installation
rom-groomer --help
```

### Basic Workflow

```bash
# 1. Import a DAT file
rom-groomer dat import /path/to/Nintendo\ -\ Game\ Boy.dat

# 2. Filter to 1G1R (One Game One ROM)
rom-groomer dat filter "Nintendo - Game Boy" --regions USA,World,Europe \
    --output filtered_games.txt

# 3. Scan your ROM collection
rom-groomer scan directory /path/to/roms/gb \
    --dat "Nintendo - Game Boy" --validate

# 4. Find missing games
rom-groomer scan missing /path/to/roms/gb \
    --dat "Nintendo - Game Boy" --output missing_games.txt

# 5. Organize your ROMs
rom-groomer organize region /path/to/roms/gb \
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
rom-groomer dat import <dat-file>           # Import DAT file
rom-groomer dat list                        # List imported DATs
rom-groomer dat info <dat-name>             # Show DAT details
rom-groomer dat games <dat-name>            # List games in DAT
rom-groomer dat search <dat-name> <query>   # Search for games
rom-groomer dat filter <dat-name>           # Filter to 1G1R
rom-groomer dat stats                       # Show statistics
rom-groomer dat delete <dat-name>           # Delete DAT
```

### ROM Scanning

```bash
rom-groomer scan directory <path>           # Scan ROM directory
rom-groomer scan missing <path>             # Find missing games
rom-groomer scan verify <file>              # Verify single ROM
```

### ROM Organization

```bash
rom-groomer organize region <path>          # Organize by region
rom-groomer organize kind <path>            # Organize by type
rom-groomer organize language <path>        # Organize by language
rom-groomer organize all <path>             # Run all organizers
```

## Requirements

- Python 3.10 or higher
- SQLite 3
- Optional: chdman (for CHD conversion)
- Optional: 7-Zip (for archive processing)

## Configuration

ROM Groomer creates configuration and database files in:

- **Linux/macOS**: `~/.config/romgroomer/`
- **Windows**: `%APPDATA%\romgroomer\`

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
pytest --cov=src/romgroomer --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Project Structure

```
rom-groomer-python/
├── src/romgroomer/          # Main source code
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

- Report bugs: [GitHub Issues](https://github.com/yourusername/rom-groomer-python/issues)
- Ask questions: [GitHub Discussions](https://github.com/yourusername/rom-groomer-python/discussions)
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
romgroomer/
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
