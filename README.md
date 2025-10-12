# ROM Groomer Python

Enterprise-grade ROM collection management system with database-backed organization, comprehensive validation, and extensible architecture.

## Features

- **Database-Backed Catalog**: SQLite database for fast queries and collection analysis
- **DAT File Support**: Full No-Intro and Redump DAT file parsing
- **Flexible Organization**: Configurable region, kind, and language-based organization
- **Symlink Management**: Intelligent symlink creation with collision detection
- **Rich Logging**: Beautiful console output with detailed file logging
- **Extensible Architecture**: Plugin-based system for parsers and organizers
- **Type Safety**: Full type hints with Pydantic models
- **Comprehensive Testing**: 95%+ code coverage

## Installation

```bash
# Development installation
cd rom-groomer-python
pip install -e ".[dev]"
```

## Quick Start

```bash
# Initialize configuration
romgroomer init

# Import DAT files
romgroomer catalog import-dat path/to/nointro.dat

# Organize ROMs
romgroomer organize --source /path/to/roms --dest /path/to/organized \
    --region usa --language-symlinks --exclude-regions usa

# Validate collection
romgroomer validate --source /path/to/organized --dat path/to/nointro.dat

# Query database
romgroomer catalog query --region usa --language en
```

## Configuration

Configuration is stored in `~/.config/romgroomer/config.yaml`:

```yaml
profiles:
  nes-usa:
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
