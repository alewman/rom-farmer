# ROM Farmer Python - Quick Start Guide

Get up and running with ROM Farmer Python in 5 minutes!

## Prerequisites

- Python 3.10 or higher
- pip package manager
- Git (optional, for version control)

## Installation

### Option 1: Development Installation (Recommended)

```bash
# Navigate to the project
cd /path/to/rom-farmer

# Create a virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev]"
```

### Option 2: User Installation

```bash
# Install from source
pip install /path/to/rom-farmer
```

## Verify Installation

```bash
# Check that romfarmer command is available
romfarmer --help

# Should output the main help text
```

## First Steps

### 1. Initialize Configuration

```bash
romfarmer init
```

This creates:
- Configuration file at `~/.config/romfarmer/config.yaml`
- Database directory at `~/.local/share/romfarmer/`
- Default organization profiles (NES, Saturn, All)

### 2. View Configuration

```bash
# Check the created configuration
cat ~/.config/romfarmer/config.yaml

# List available profiles
romfarmer profile list
```

### 3. Check Database

```bash
# View catalog statistics (currently empty)
romfarmer catalog stats
```

## Using the Parser (Python API)

```python
from pathlib import Path
from romfarmer.parsers.nointro import NoIntroParser

# Create parser
parser = NoIntroParser()

# Parse a ROM filename
rom = parser.parse(Path("Super Mario Bros. (USA).nes"))

# Access parsed data
print(f"Name: {rom.name}")
print(f"Region: {rom.primary_region}")
print(f"Size: {rom.size} bytes")
print(f"Kind: {rom.kind}")

# Format back to filename
formatted = parser.format_filename(rom)
print(f"Formatted: {formatted}")
```

### Example Output

```
Name: Super Mario Bros.
Region: RomRegion.USA
Size: 40960 bytes
Kind: RomKind.GAME
Formatted: Super Mario Bros. (Usa).nes
```

## Using the Database (Python API)

```python
from romfarmer.catalog.database import RomGroomerDatabase, DatFile

# Connect to database
db = RomGroomerDatabase("~/.local/share/romfarmer/catalog.db")

# Add a DAT file
with db.get_session() as session:
    dat = DatFile(
        name="Nintendo - Nintendo Entertainment System",
        version="20241224",
        total_games=1761,
    )
    db.add_dat_file(session, dat)
    session.commit()
    
    # Query statistics
    stats = db.get_statistics(session)
    print(f"Total DAT files: {stats['total_dat_files']}")

# Close database
db.close()
```

## Development Workflow

### Running Tests

```bash
# Run all tests
make test

# Or directly with pytest
pytest -v

# Run with coverage report
make test-cov
```

### Code Quality

```bash
# Format code
make format

# Lint code
make lint

# Type check
make type-check

# Run all checks
make all
```

### Project Structure

```
rom-farmer/
├── src/romfarmer/          # Source code
│   ├── catalog/             # Database operations
│   ├── cli/                 # Command-line interface
│   ├── core/                # Configuration and logging
│   ├── models/              # Data models
│   └── parsers/             # Filename parsers
├── tests/                   # Test suite
├── pyproject.toml           # Project configuration
├── Makefile                 # Convenience commands
└── README.md                # Documentation
```

## Configuration

### Default Configuration File

`~/.config/romfarmer/config.yaml`:

```yaml
version: "2.0.0"

profiles:
  nes-usa:
    regions: [usa, world]
    organize_languages: false
    organize_kinds: true
    
  nes-eng:
    regions: [europe, australia, world]
    organize_languages: true
    exclude_language_regions: [usa]
    organize_kinds: true

database:
  path: ~/.local/share/romfarmer/catalog.db
  echo: false

logging:
  level: INFO
  enable_file_logging: true

parallel_workers: 4
verify_hashes: true
```

### Customizing Profiles

Edit the config file to add your own profiles:

```yaml
profiles:
  my-custom-profile:
    name: my-custom-profile
    regions: [japan, usa]
    organize_languages: true
    exclude_language_regions: []
    organize_kinds: true
    keep_in_root_regions: []
    keep_in_root_kinds: []
```

## Example: Parsing Multiple ROMs

```python
from pathlib import Path
from romfarmer.parsers.nointro import NoIntroParser
from romfarmer.models.rom import RomRegion, RomLanguage

# Initialize parser
parser = NoIntroParser()

# List of ROM files
rom_files = [
    "Super Mario Bros. (USA).nes",
    "Legend of Zelda, The (USA, Europe).nes",
    "Final Fantasy (Japan) (En,Fr,De).nes",
]

# Parse all ROMs
roms = [parser.parse(Path(f)) for f in rom_files]

# Filter by region
usa_roms = [r for r in roms if r.has_region(RomRegion.USA)]
print(f"USA ROMs: {len(usa_roms)}")

# Filter by language
english_roms = [r for r in roms if r.has_language(RomLanguage.ENGLISH)]
print(f"English ROMs: {len(english_roms)}")

# Multi-region ROMs
multi_region = [r for r in roms if r.has_multiple_regions]
print(f"Multi-region ROMs: {len(multi_region)}")
```

## Logging

ROM Farmer provides beautiful logging output:

```python
from romfarmer.core.logger import get_logger

# Get logger
logger = get_logger()

# Log messages
logger.section("Processing ROMs")
logger.info("Processing ROM: [path]/roms/mario.nes[/path]")
logger.success("Processed 100 ROMs")
logger.warning("Skipped 5 ROMs")
logger.error("Failed to process 2 ROMs")

# Progress bar
with logger.progress("Processing", total=100) as progress:
    task = progress.add_task("Processing ROMs", total=100)
    for i in range(100):
        # Do work
        progress.advance(task)
```

### Log Files

Logs are automatically saved to:
- `~/.local/share/romfarmer/logs/romfarmer_YYYYMMDD_HHMMSS.log`

Each log file includes:
- Timestamp for each message
- Log level (DEBUG, INFO, WARNING, ERROR)
- Module and function name
- Line number
- Full message with context

## Common Tasks

### Check Parser with Real ROM

```bash
# Create a test ROM file
mkdir -p /tmp/test-roms
touch "/tmp/test-roms/Super Mario Bros. (USA).nes"

# Parse it in Python
python3 << 'EOF'
from pathlib import Path
from romfarmer.parsers.nointro import NoIntroParser

parser = NoIntroParser()
rom = parser.parse(Path("/tmp/test-roms/Super Mario Bros. (USA).nes"))
print(f"✓ Parsed: {rom.name}")
print(f"✓ Region: {rom.primary_region}")
print(f"✓ Kind: {rom.kind}")
EOF
```

### View Test Coverage Report

```bash
# Generate coverage report
make test-cov

# Open HTML report in browser
xdg-open htmlcov/index.html  # Linux
# or
open htmlcov/index.html       # macOS
```

## Troubleshooting

### Command Not Found: romfarmer

```bash
# Ensure package is installed
pip list | grep romfarmer

# Reinstall if needed
pip install -e ".[dev]"
```

### Import Errors

```bash
# Check Python path
python3 -c "import sys; print('\n'.join(sys.path))"

# Verify installation
python3 -c "import romfarmer; print(romfarmer.__version__)"
```

### Database Errors

```bash
# Remove and reinitialize database
rm ~/.local/share/romfarmer/catalog.db
romfarmer init
```

## Next Steps

1. **Read DEVELOPMENT.md** - Comprehensive architecture guide
2. **Read STATUS.md** - Current implementation status
3. **Explore tests/** - See usage examples
4. **Check the roadmap** - See what's coming next

## Getting Help

- Check the documentation in `README.md` and `DEVELOPMENT.md`
- Review test files in `tests/` for usage examples
- Examine the bash implementation in the rom-farmer directory

## Contributing

ROM Farmer Python is designed to be extensible:

1. **Add a parser**: Extend `BaseParser` for new naming conventions
2. **Add an organizer**: Extend `BaseOrganizer` for new organization strategies
3. **Add tests**: All contributions should include tests
4. **Follow style**: Use `black` for formatting, `ruff` for linting

---

**You're ready to go!** 🚀

The foundation is solid, the tests are passing, and the CLI is functional. Now you can start building the organization and validation logic on top of this enterprise-grade foundation.
