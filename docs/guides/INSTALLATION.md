# Installation Guide

This guide covers installation and setup of ROM Farmer on various platforms.

## System Requirements

- **Python**: 3.10 or higher
- **SQLite**: 3.x (usually included with Python)
- **Operating System**: Linux, macOS, or Windows
- **Disk Space**: ~100MB for installation, additional space for ROM catalogs
- **RAM**: Minimum 512MB, recommended 2GB+ for large collections

## Optional Dependencies

- **chdman**: For CHD disc format conversion
- **7-Zip (7z)**: For processing 7Z archives
- **unrar**: For processing RAR archives

## Installation Methods

### Method 1: Install from Source (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/rom-farmer.git
cd rom-farmer

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .

# Verify installation
rom-farmer --version
rom-farmer --help
```

### Method 2: Install for Development

```bash
# Clone and navigate
git clone https://github.com/yourusername/rom-farmer.git
cd rom-farmer

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install with development dependencies
pip install -e ".[dev]"

# Verify tests work
pytest

# Run with coverage
pytest --cov=src/romfarmer
```

## Platform-Specific Setup

### Linux (Debian/Ubuntu)

```bash
# Install Python and dependencies
sudo apt update
sudo apt install python3.10 python3-pip python3-venv git

# Install optional tools
sudo apt install p7zip-full unrar chdman

# Follow Method 1 installation above
```

### Linux (Fedora/RHEL)

```bash
# Install Python and dependencies
sudo dnf install python3.10 python3-pip git

# Install optional tools
sudo dnf install p7zip p7zip-plugins unrar

# For chdman, compile from MAME source or use Flatpak
flatpak install flathub org.mamedev.MAME

# Follow Method 1 installation above
```

### macOS

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.10

# Install optional tools
brew install p7zip chdman

# Follow Method 1 installation above
```

### Windows

1. **Install Python**:
   - Download Python 3.10+ from [python.org](https://www.python.org/downloads/)
   - Run installer and check "Add Python to PATH"
   - Verify: Open Command Prompt and run `python --version`

2. **Install Git** (optional):
   - Download from [git-scm.com](https://git-scm.com/download/win)
   - Or use GitHub Desktop

3. **Install ROM Farmer**:
   ```cmd
   # Clone repository (or download ZIP)
   git clone https://github.com/yourusername/rom-farmer.git
   cd rom-farmer

   # Create virtual environment
   python -m venv venv
   venv\Scripts\activate

   # Install
   pip install -e .

   # Verify
   rom-farmer --help
   ```

4. **Optional Tools**:
   - Install [7-Zip](https://www.7-zip.org/) for archive support
   - Add 7z.exe to PATH for command-line access

## Configuration

ROM Farmer creates configuration and database files in:

- **Linux/macOS**: `~/.config/romfarmer/`
- **Windows**: `%APPDATA%\romfarmer\`

### Default Configuration

On first run, ROM Farmer creates:

```
~/.config/romfarmer/
├── config.yaml          # Configuration file
├── romfarmer.db        # SQLite database
└── logs/                # Log files
```

### Configuration File

Edit `config.yaml` to customize:

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

# Logging
logging:
  level: INFO            # DEBUG, INFO, WARNING, ERROR
  file: logs/romfarmer.log
```

## Verifying Installation

Run these commands to verify everything is working:

```bash
# Check version
rom-farmer --version

# List available commands
rom-farmer --help

# List DAT commands
rom-farmer dat --help

# Check database
rom-farmer dat list

# Run test scan (should report 0 ROMs found)
rom-farmer scan directory /tmp/test-roms --dry-run
```

## Updating

### Update from Git

```bash
cd rom-farmer
git pull origin main
pip install -e . --upgrade
```

### Update Dependencies

```bash
pip install -e . --upgrade --upgrade-strategy eager
```

## Uninstalling

```bash
# Uninstall the package
pip uninstall romfarmer

# Remove configuration (optional)
rm -rf ~/.config/romfarmer/

# Remove source (if installed from git)
cd ..
rm -rf rom-farmer/
```

## Troubleshooting

### Python Version Issues

```bash
# Check Python version
python --version  # Should be 3.10+

# If you have multiple Python versions
python3.10 -m venv venv
source venv/bin/activate
pip install -e .
```

### Permission Errors

```bash
# Don't use sudo with pip in virtual environment
# Instead, ensure virtual environment is activated:
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

### Missing Dependencies

```bash
# Reinstall all dependencies
pip install -e . --force-reinstall
```

### Database Issues

```bash
# Reset database (WARNING: loses all imported DATs)
rm ~/.config/romfarmer/romfarmer.db

# ROM Farmer will recreate on next run
rom-farmer dat list
```

### Import Errors

If you see import errors like `ModuleNotFoundError`:

```bash
# Ensure you're in the correct directory
cd rom-farmer

# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall in editable mode
pip install -e .
```

## Next Steps

Once installation is complete:

1. Read the [User Guide](USER_GUIDE.md) for command details
2. Follow the [Workflow Guide](WORKFLOWS.md) for end-to-end examples
3. Check [Troubleshooting Guide](TROUBLESHOOTING.md) if you encounter issues

## Getting Help

- Check existing [GitHub Issues](https://github.com/yourusername/rom-farmer/issues)
- Read the [FAQ](TROUBLESHOOTING.md#faq)
- Ask in [GitHub Discussions](https://github.com/yourusername/rom-farmer/discussions)
