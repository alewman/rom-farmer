# PS3/PSP PKG Decrypter

Python implementation of Mathieulh's PS3 PSP PKG Decrypter & Extractor.

## Overview

This tool decrypts and extracts PS3 and PSP PKG files (game packages, DLC, add-ons). It's a pure Python port of the original C# application, designed for Linux compatibility.

## Features

- Decrypt PS3 and PSP PKG files
- Extract PKG contents to directory structure
- No external dependencies except pycryptodome
- Command-line interface
- Python API for integration

## Installation

```bash
# Install dependencies
pip install pycryptodome

# Make executable
chmod +x pkg_decrypt.py
```

## Usage

### Command Line

```bash
# Extract PKG file
python3 pkg_decrypt.py game.pkg

# Extract to specific directory
python3 pkg_decrypt.py game.pkg -o /output/dir

# Verbose output
python3 pkg_decrypt.py game.pkg -v

# Decrypt only (don't extract)
python3 pkg_decrypt.py game.pkg --decrypt-only
```

### Python API

```python
from pathlib import Path
from pkg_decrypt import PKGDecrypter

# Extract PKG
pkg = PKGDecrypter(Path('game.pkg'))
output_dir = pkg.extract_pkg(verbose=True)

# Just decrypt
decrypted_file = pkg.decrypt_pkg()
```

## Supported Formats

- **PS3 PKG**: Game packages, DLC, add-ons (content type 0x01)
- **PSP PKG**: Game packages, DLC (content type 0x02)
- **Retail only**: Debug PKG files are not supported

## Technical Details

### Encryption

PKG files use AES-128-ECB encryption with platform-specific keys:

- **PS3 Key**: `2E 7B 71 D7 C9 C9 A1 4E A3 22 1F 18 88 28 B8 F8`
- **PSP Key**: `07 F2 C6 82 90 B5 0D 2C 33 81 8D 70 9B 60 E6 2B`

The file-specific key at offset 0x70 is encrypted with the platform key to generate XOR keys for decryption.

### File Structure

```
PKG Header:
  0x00: Magic (0x7F 'P' 'K' 'G')
  0x04: Finalized flag (0x80 = retail)
  0x07: PKG type (0x01 = PS3, 0x02 = PSP)
  0x24: Encrypted data start offset
  0x2C: Encrypted data length
  0x70: PKG file key (16 bytes)
```

## Credits

- **Original C# version**: Mathieulh
- **Python port**: ROM Groomer project
- **Algorithm**: Reversed from PS3 firmware

## License

Free to use and modify (with original author's blessing). See original README for details.

## Notes

- RAP keys are NOT needed for PKG decryption (only for content activation on PS3)
- This extracts the PKG contents regardless of license status
- Game packages (content type 0x4) contain actual game data
- Some PKG files may still require additional processing on PS3
