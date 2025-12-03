# Configuration Examples

This directory contains example configuration files for ROM Groomer builds.

## Structure

- `builds/` - Master build configurations (e.g., rocknix-512gb.yaml)
- `platforms/` - Platform-specific configurations (e.g., nes.yaml, saturn.yaml)

## File Format

All configuration files use YAML format with environment variable substitution.

### Environment Variables

You can use environment variables in configs:
```yaml
workspace: ${EMU_ROOT}/rom-groomer-python
dat_directory: ${EMU_ROOT}/dats
```

### Relative Paths

Relative paths are resolved from the config root directory:
```yaml
output_path: ../output/rocknix/nes  # Resolves to /data/emu/rom-groomer-python/output/rocknix/nes
```

## Usage

```python
from romgroomer.config import load_build_config, load_platform_config

# Load master build
build = load_build_config("rocknix-512gb")

# Load platform config
platform = load_platform_config("nes")
```

## Validation

All configs are validated using Pydantic:
- Required fields must be present
- File paths must exist (or parent directories for outputs)
- Enum values must be valid
- System types must match extraction settings
- DAT counts are validated if specified

## Naming Conventions

Please refer to `../../NAMING-CONVENTIONS.md` for detailed rules on naming output directories.
**Key Rule**: Output paths must follow the pattern `/data/emu/output/{prefix}{filter}-{region}-{format}-{target}/{platform}`.
