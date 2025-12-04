# ROM Groomer Quick Reference

Essential commands and workflows for quick reference.

## Installation

```bash
cd /data/emu/rom-groomer-python
pip install -e .
rom-groomer --help
```

## Common Commands

### Import DAT
```bash
rom-groomer dat import ~/dats/Nintendo\ -\ Game\ Boy.dat
```

### List Imported DATs
```bash
rom-groomer dat list
```

### Filter to 1G1R
```bash
rom-groomer dat filter "Nintendo - Game Boy" \
    --regions USA,World,Europe \
    --output gb_1g1r.txt
```

### Scan Collection
```bash
rom-groomer scan directory ~/roms/gb \
    --dat "Nintendo - Game Boy" \
    --validate
```

### Find Missing Games
```bash
rom-groomer scan missing ~/roms/gb \
    --dat "Nintendo - Game Boy" \
    --output missing.txt
```

### Organize by Region
```bash
rom-groomer organize region ~/roms/gb \
    --output ~/organized/gb \
    --mode copy
```

## Quick Workflows

### Build 1G1R Collection
```bash
# 1. Import
rom-groomer dat import system.dat

# 2. Filter
rom-groomer dat filter "System" --regions USA,World --output 1g1r.txt

# 3. Scan
rom-groomer scan directory ~/roms --validate

# 4. Find missing
rom-groomer scan missing ~/roms --filter-1g1r --output missing.txt

# 5. Organize
rom-groomer organize region ~/roms --output ~/organized --mode copy
```

### Validate Collection
```bash
# Full validation
rom-groomer scan directory ~/roms \
    --dat "System" \
    --validate \
    --output report.txt
```

### Update DATs
```bash
# Re-import with --update
rom-groomer dat import ~/dats/*.dat --update
```

## Option Reference

### DAT Filter Options
- `--regions USA,World,Europe,Japan` - Region priority
- `--languages En,Ja,Fr,De` - Language priority
- `--prefer-parent` - Prefer parent ROMs
- `--prefer-revisions` - Prefer newer revisions
- `--output FILE` - Save filtered list

### Scan Options
- `--dat NAME` - Validate against DAT
- `--validate` - Calculate CRC32
- `--threads N` - Parallel threads (default: 4)
- `--output FILE` - Save report

### Organize Options
- `--output PATH` - Destination directory
- `--mode copy|move|symlink` - Operation mode
- `--keep-in-place` - Keep unmatched files
- `--exclude PATTERN` - Exclude pattern
- `--dry-run` - Preview only

## Safety Tips

✅ **DO:**
- Use `--dry-run` first
- Start with `--mode copy`
- Backup before bulk operations
- Export reports with `--output`
- Use `--validate` to check authenticity

⚠️ **DON'T:**
- Use `--mode move` without testing
- Delete files without validation
- Skip backups on important collections
- Run commands without `--dry-run` first

## Common Issues

### Import fails
```bash
# Re-download DAT, verify it's Logiqx XML format
head -5 file.dat  # Should show XML header
```

### Scan finds no files
```bash
# Check path
ls -la /path/to/roms

# Check recursive is enabled (default: yes)
```

### CRC mismatches
```bash
# Verify single file
rom-groomer scan verify /path/to/file.rom

# May be bad dump, re-acquire
```

### Slow scanning
```bash
# Use more threads
rom-groomer scan directory /roms --threads 8

# Skip validation for quick check
rom-groomer scan directory /roms
```

## File Locations

- **Config**: `~/.config/romgroomer/config.yaml`
- **Database**: `~/.config/romgroomer/romgroomer.db`
- **Logs**: `~/.config/romgroomer/logs/`

## Getting Help

```bash
# Command help
rom-groomer --help
rom-groomer dat --help
rom-groomer scan --help

# Documentation
ls docs/
# Read: USER_GUIDE.md, WORKFLOWS.md, TROUBLESHOOTING.md
```

## Resources

- **No-Intro DATs**: https://datomatic.no-intro.org/
- **Redump DATs**: http://redump.org/downloads/
- **Full Documentation**: `docs/USER_GUIDE.md`
- **Workflows**: `docs/WORKFLOWS.md`
- **Troubleshooting**: `docs/TROUBLESHOOTING.md`
