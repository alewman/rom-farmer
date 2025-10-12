# ROM Groomer Python - Development Guide

## Project Architecture

ROM Groomer Python is built with enterprise-grade practices and extensibility in mind. This document outlines the architecture, design decisions, and development workflow.

## Core Principles

1. **Type Safety**: Full type hints with Pydantic models
2. **Testability**: 95%+ code coverage with pytest
3. **Extensibility**: Plugin-based parsers and organizers
4. **Performance**: Database-backed catalog for fast queries
5. **User Experience**: Rich CLI with beautiful output

## Architecture Layers

### 1. Models Layer (`romgroomer.models`)

**Purpose**: Type-safe data structures using Pydantic

**Key Components**:
- `Rom`: Complete ROM metadata with validation
- `RomRegion`: Enum for standardized regions
- `RomLanguage`: Enum for standardized languages
- `RomKind`: Enum for ROM categories
- `DatGame`: DAT file game entries
- `OrganizationResult`: Results from organization operations

**Design Decisions**:
- Pydantic for automatic validation and serialization
- Enums for controlled vocabularies
- Property methods for computed values
- Validator methods for data cleaning

### 2. Parsers Layer (`romgroomer.parsers`)

**Purpose**: Extract metadata from filenames and DAT files

**Current Parsers**:
- `NoIntroParser`: No-Intro filename conventions
- `RedumpParser`: Redump filename conventions (TODO)
- `DatParser`: XML DAT file parsing (TODO)

**Extension Pattern**:
```python
class BaseParser(ABC):
    @abstractmethod
    def parse(self, filepath: Path) -> Rom:
        """Parse ROM file and return metadata."""
        pass
    
    @abstractmethod
    def format_filename(self, rom: Rom) -> str:
        """Format ROM metadata back to filename."""
        pass
```

### 3. Organizers Layer (`romgroomer.organizers`)

**Purpose**: Organize ROMs according to rules

**Planned Organizers**:
- `RegionOrganizer`: Organize by region folders
- `KindOrganizer`: Organize by kind (Applications, etc.)
- `LanguageOrganizer`: Create language symlinks
- `MultiDiscOrganizer`: Handle multi-disc sets

**Extension Pattern**:
```python
class BaseOrganizer(ABC):
    @abstractmethod
    def organize(
        self, 
        rom: Rom, 
        dest: Path,
        profile: OrganizationProfile
    ) -> OrganizationResult:
        """Organize a single ROM."""
        pass
```

### 4. Catalog Layer (`romgroomer.catalog`)

**Purpose**: Database operations for ROM catalog

**Key Components**:
- `RomGroomerDatabase`: Main database interface
- SQLAlchemy models: `DatFile`, `DatGame`, `RomFile`, `OrganizationLog`
- Query helpers for common operations

**Schema Design**:
- Normalized schema for efficiency
- Indexes on common query fields (CRC, name, region)
- Cascade deletes for data integrity
- Timestamps for audit trail

### 5. Core Layer (`romgroomer.core`)

**Purpose**: Infrastructure and configuration

**Key Components**:
- `RomGroomerLogger`: Rich logging with file output
- `RomGroomerConfig`: YAML configuration with profiles
- `OrganizationProfile`: Profile-based organization settings

**Features**:
- Structured logging with context
- Configuration profiles for different systems
- Hierarchical config (system → user → CLI)

### 6. CLI Layer (`romgroomer.cli`)

**Purpose**: Command-line interface using Click

**Commands**:
- `romgroomer init`: Initialize configuration
- `romgroomer organize`: Organize ROMs
- `romgroomer validate`: Validate against DAT
- `romgroomer catalog`: Catalog operations
- `romgroomer profile`: Profile management

## Development Workflow

### Setting Up Development Environment

```bash
# Clone repository
cd rom-groomer-python

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install in development mode
pip install -e ".[dev]"

# Verify installation
romgroomer --help
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run specific test file
pytest tests/test_parsers_nointro.py

# Run with verbose output
pytest -v

# Run and show print statements
pytest -s
```

### Code Quality

```bash
# Format code with black
black src/ tests/

# Lint code with ruff
ruff check src/ tests/

# Fix linting issues
ruff check --fix src/ tests/

# Type check with mypy
mypy src/
```

### Testing Guidelines

1. **Test Coverage**: Aim for 95%+ coverage
2. **Test Organization**: One test file per module
3. **Fixtures**: Use pytest fixtures for setup
4. **Naming**: `test_<function>_<scenario>`
5. **Assertions**: Clear, specific assertions
6. **Edge Cases**: Test boundary conditions

Example test structure:
```python
class TestNoIntroParser:
    @pytest.fixture
    def parser(self) -> NoIntroParser:
        return NoIntroParser()
    
    def test_simple_usa_rom(self, parser: NoIntroParser) -> None:
        """Test parsing simple USA ROM."""
        # Arrange
        rom_file = Path("Super Mario Bros. (USA).nes")
        
        # Act
        rom = parser.parse(rom_file)
        
        # Assert
        assert rom.name == "Super Mario Bros."
        assert rom.regions == [RomRegion.USA]
```

## Configuration System

### Configuration Hierarchy

1. **System Config**: `/etc/romgroomer/config.yaml`
2. **User Config**: `~/.config/romgroomer/config.yaml`
3. **Environment Variables**: `ROMGROOMER_*`
4. **CLI Arguments**: Command-line flags

### Example Configuration

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
  path: ~/.local/share/romgroomer/catalog.db
  echo: false

logging:
  level: INFO
  enable_file_logging: true

parallel_workers: 4
verify_hashes: true
```

## Database Schema

### Tables

1. **dat_files**: DAT file metadata
2. **dat_games**: Games from DAT files
3. **rom_files**: ROM files in collection
4. **organization_logs**: Operation history

### Key Relationships

- `dat_files` → `dat_games` (one-to-many)
- `rom_files` → `dat_files` (many-to-one, optional)
- `rom_files` → `dat_games` (many-to-one, optional)

### Indexes

- `dat_games(dat_file_id, crc)`: Fast CRC lookups
- `rom_files(crc32)`: Fast ROM matching
- `rom_files(regions, kind)`: Organization queries

## Extension Points

### Adding a New Parser

1. Create new parser class extending `BaseParser`
2. Implement `parse()` and `format_filename()` methods
3. Add tests in `tests/test_parsers_<name>.py`
4. Register in parser factory

### Adding a New Organizer

1. Create new organizer class extending `BaseOrganizer`
2. Implement `organize()` method
3. Add configuration options to `OrganizationProfile`
4. Add tests and documentation

### Adding a New CLI Command

1. Add command function with `@cli.command()` decorator
2. Use Click options for arguments
3. Access logger and config from context
4. Add help text and examples

## Performance Considerations

1. **Parallel Processing**: Use `parallel_workers` for batch operations
2. **Database Pooling**: Connection pool for concurrent access
3. **Batch Operations**: Commit multiple changes together
4. **Lazy Loading**: Load ROM data on-demand
5. **Progress Bars**: Use Rich progress for long operations

## Logging Best Practices

```python
# Use structured logging
logger.info(f"Processing ROM: [path]{rom.path}[/path]")

# Use sections for major operations
logger.section("Organizing ROMs")

# Use success for completion
logger.success(f"Organized {count} ROMs")

# Use progress bars for iterations
with logger.progress("Processing ROMs", total=len(roms)) as progress:
    for rom in roms:
        # Process ROM
        progress.advance(task_id)
```

## Migration from Bash

The Python implementation is designed to coexist with bash scripts:

1. Bash scripts remain as high-level entry points
2. Python provides core functionality
3. Gradual migration: one feature at a time
4. Same configuration and behavior

## Future Enhancements

- [ ] Web UI for collection management
- [ ] REST API for programmatic access
- [ ] Parallel DAT file processing
- [ ] Advanced duplicate detection
- [ ] Collection statistics and reports
- [ ] Automatic ROM download from verified sources
- [ ] Integration with emulator frontends
- [ ] Cloud storage backend support

## Contributing

1. Fork the repository
2. Create feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Format code with black
6. Submit pull request

## Resources

- [Click Documentation](https://click.palletsprojects.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [pytest Documentation](https://docs.pytest.org/)
