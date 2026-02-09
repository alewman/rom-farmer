# Troubleshooting Guide

Common issues and solutions for ROM Farmer.

## Table of Contents

- [Installation Issues](#installation-issues)
- [DAT Import Issues](#dat-import-issues)
- [Scanning Issues](#scanning-issues)
- [Organization Issues](#organization-issues)
- [Performance Issues](#performance-issues)
- [Database Issues](#database-issues)
- [FAQ](#faq)

## Installation Issues

### Python Version Error

**Problem:**
```
ERROR: Python 3.10 or higher is required
```

**Solution:**
```bash
# Check Python version
python --version  # or python3 --version

# Install Python 3.10+ if needed
# Ubuntu/Debian:
sudo apt install python3.10

# macOS:
brew install python@3.10

# Use specific Python version
python3.10 -m venv venv
source venv/bin/activate
pip install -e .
```

### Module Not Found Error

**Problem:**
```
ModuleNotFoundError: No module named 'romfarmer'
```

**Solution:**
```bash
# Ensure you're in the correct directory
cd /data/emu/rom-farmer

# Activate virtual environment
source venv/bin/activate

# Install in editable mode
pip install -e .

# If still failing, reinstall
pip uninstall romfarmer
pip install -e .
```

### Permission Denied

**Problem:**
```
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied
```

**Solution:**
```bash
# DON'T use sudo with pip!
# Instead, use a virtual environment:

python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### Missing Dependencies

**Problem:**
```
ERROR: Could not find a version that satisfies the requirement pydantic>=2.5
```

**Solution:**
```bash
# Update pip
pip install --upgrade pip

# Install dependencies explicitly
pip install pydantic sqlalchemy click rich pytest

# Then install ROM Farmer
pip install -e .
```

## DAT Import Issues

### XML Parsing Error

**Problem:**
```
ERROR: Failed to parse DAT file: not well-formed (invalid token)
```

**Solutions:**

1. **Verify DAT file integrity:**
   ```bash
   # Check if file is valid XML
   xmllint --noout path/to/file.dat
   
   # Or use Python
   python3 -c "import xml.etree.ElementTree as ET; ET.parse('path/to/file.dat')"
   ```

2. **Re-download DAT file** - May be corrupted

3. **Check DAT format** - ROM Farmer supports Logiqx XML format only
   ```xml
   <!-- Valid format starts with: -->
   <?xml version="1.0"?>
   <!DOCTYPE datafile PUBLIC "-//Logiqx//DTD ROM Management Datafile//EN" "http://www.logiqx.com/Dats/datafile.dtd">
   <datafile>
   ```

### DAT Already Imported

**Problem:**
```
WARNING: DAT 'Nintendo - Game Boy' already imported
```

**Solution:**
```bash
# Use --update flag to re-import
rom-farmer dat import path/to/file.dat --update

# Or delete and re-import
rom-farmer dat delete "Nintendo - Game Boy" --force
rom-farmer dat import path/to/file.dat
```

### No Games Found in DAT

**Problem:**
```
ERROR: No games found in DAT file
```

**Causes:**
1. DAT file is empty or corrupted
2. DAT file is not Logiqx XML format
3. Games are in unsupported format

**Solution:**
```bash
# Check DAT structure
head -50 path/to/file.dat

# Look for <game> tags:
grep -c "<game" path/to/file.dat

# Should show number > 0
```

### Import Takes Too Long

**Problem:** Import stuck or taking hours

**Solutions:**
```bash
# 1. Check database isn't locked
rm ~/.config/romfarmer/romfarmer.db-journal

# 2. Import with progress disabled
rom-farmer dat import file.dat --no-progress

# 3. Check disk space
df -h ~/.config/romfarmer/

# 4. Try importing to new database
mv ~/.config/romfarmer/romfarmer.db{,.backup}
rom-farmer dat import file.dat
```

## Scanning Issues

### Scan Finds No Files

**Problem:**
```
Files scanned: 0
```

**Solutions:**

1. **Check path is correct:**
   ```bash
   ls -la /path/to/roms
   ```

2. **Check for hidden files:**
   ```bash
   rom-farmer scan directory /path/to/roms --show-hidden
   ```

3. **Check file extensions:**
   ```bash
   # ROM Farmer looks for common extensions
   # .gb, .gba, .nes, .snes, .bin, .iso, .chd, etc.
   
   # See what files are there
   find /path/to/roms -type f | head -20
   ```

### CRC32 Mismatches

**Problem:**
```
⚠ CRC32 mismatches: 15
```

**Common Causes:**

1. **Bad dumps or corrupted files**
   ```bash
   # Verify specific file
   rom-farmer scan verify /path/to/suspicious.rom --show-all-hashes
   
   # Compare with expected
   rom-farmer dat search "System Name" "game name"
   ```

2. **Headered vs headerless ROMs**
   - Some systems (NES, SNES) have header bytes
   - DAT may expect headerless, your ROMs may have headers
   - Solution: Remove headers with appropriate tools

3. **Outdated DAT file**
   ```bash
   # Update DAT to latest version
   rom-farmer dat delete "System Name"
   rom-farmer dat import /path/to/newest.dat
   ```

4. **Wrong DAT file**
   - Ensure you're using the correct region DAT
   - No-Intro vs Redump (cartridge vs disc)

### Scan is Very Slow

**Problem:** Scanning 500 ROMs takes 30+ minutes

**Solutions:**

1. **Use more threads:**
   ```bash
   # Default is 4, try more
   rom-farmer scan directory /roms --threads 8
   
   # Or match your CPU cores
   rom-farmer scan directory /roms --threads 16
   ```

2. **Skip validation for quick check:**
   ```bash
   # Just list files, no CRC calculation
   rom-farmer scan directory /roms
   ```

3. **Check disk performance:**
   ```bash
   # Test read speed
   dd if=/path/to/large.rom of=/dev/null bs=1M count=100
   
   # If slow, disk may be failing or networked
   ```

4. **Reduce chunk size for slow disks:**
   ```bash
   # Edit config.yaml
   scanner:
     chunk_size: 524288  # 512KB instead of 1MB
   ```

### Files Not Matching DAT

**Problem:** Many files showing as "Not in DAT"

**Solutions:**

1. **Check filenames match No-Intro format:**
   ```bash
   # No-Intro format: Game Name (Region) (Extra).ext
   # Examples:
   # ✓ Pokemon - Red Version (USA).gb
   # ✓ Super Mario Bros. (World).nes
   # ✗ pokemon_red.gb
   # ✗ smb1.nes
   ```

2. **Rename ROMs to match DAT:**
   ```bash
   # Use a ROM renaming tool first
   # Or check what DAT expects:
   rom-farmer dat games "System Name" | grep -i "game name"
   ```

3. **Verify you have correct DAT:**
   ```bash
   rom-farmer dat info "System Name"
   # Check version and date
   ```

## Organization Issues

### Files Not Being Organized

**Problem:**
```
Files organized: 0
```

**Solutions:**

1. **Check ROM filenames contain region tags:**
   ```bash
   # Organization requires parseable filenames
   # Must have region tags like (USA), (Europe), etc.
   ls /path/to/roms | grep -E "\([A-Za-z]+\)"
   ```

2. **Use --keep-in-place to see unmatched files:**
   ```bash
   rom-farmer organize region /roms \
       --output /organized \
       --keep-in-place
   
   # Unmatched files go to /organized/unmatched/
   ```

3. **Check exclude patterns:**
   ```bash
   # Make sure you're not excluding everything
   rom-farmer organize region /roms --output /organized --dry-run
   ```

### Duplicate Files Created

**Problem:** Same file appearing in multiple locations

**Causes:**
1. Using copy mode with overlapping organization runs
2. Files matching multiple patterns

**Solutions:**
```bash
# 1. Use symlink mode to avoid duplicates
rom-farmer organize region /roms \
    --output /organized \
    --mode symlink

# 2. Clean up and start fresh
rm -rf /organized
rom-farmer organize region /roms --output /organized --mode copy

# 3. Use move mode (careful!)
rom-farmer organize region /roms --output /organized --mode move
```

### Permission Denied During Organization

**Problem:**
```
ERROR: Permission denied: /organized/USA/game.rom
```

**Solutions:**
```bash
# 1. Check output directory permissions
ls -ld /organized

# 2. Create directory with correct permissions
mkdir -p /organized
chmod 755 /organized

# 3. Check source file permissions
ls -l /roms/game.rom

# 4. Run with appropriate user
# Don't use sudo unless necessary
```

### Symlinks Not Working

**Problem:** Symlinks created but don't work

**Solutions:**

1. **Check filesystem supports symlinks:**
   ```bash
   # Test symlink creation
   ln -s /roms/test.rom /tmp/test-link.rom
   ls -l /tmp/test-link.rom
   
   # FAT32, exFAT don't support symlinks
   # NTFS requires special permissions on Windows
   ```

2. **Use absolute paths:**
   ```bash
   # ROM Farmer uses absolute paths by default
   # If issues, verify:
   readlink /organized/USA/game.rom
   # Should show full path like /roms/game.rom
   ```

3. **Check source files exist:**
   ```bash
   # Broken symlink if source moved/deleted
   find /organized -xtype l  # Find broken symlinks
   ```

## Performance Issues

### High Memory Usage

**Problem:** ROM Farmer using several GB of RAM

**Solutions:**

1. **Reduce parallel threads:**
   ```bash
   rom-farmer scan directory /roms --threads 2
   ```

2. **Process smaller batches:**
   ```bash
   # Scan directories separately
   rom-farmer scan directory /roms/A-M
   rom-farmer scan directory /roms/N-Z
   ```

3. **Reduce chunk size:**
   ```bash
   # Edit config.yaml
   scanner:
     chunk_size: 262144  # 256KB
   ```

### Database Growing Too Large

**Problem:** romfarmer.db is several GB

**Causes:**
- Many DATs imported
- Large game catalogs

**Solutions:**

```bash
# 1. Check database size
du -h ~/.config/romfarmer/romfarmer.db

# 2. Remove unused DATs
rom-farmer dat list
rom-farmer dat delete "Unused DAT Name"

# 3. Vacuum database to reclaim space
sqlite3 ~/.config/romfarmer/romfarmer.db "VACUUM;"

# 4. Start fresh if needed
mv ~/.config/romfarmer/romfarmer.db{,.old}
# Re-import only needed DATs
```

### CPU Usage at 100%

**Problem:** ROM Farmer pegging CPU

**Expected Behavior:**
- Scanning with validation is CPU-intensive (hash calculation)
- Should use all cores with multi-threading

**If Problematic:**
```bash
# Reduce threads to leave cores for other tasks
rom-farmer scan directory /roms --threads 2

# Or use nice to lower priority
nice -n 19 rom-farmer scan directory /roms --validate
```

## Database Issues

### Database Locked

**Problem:**
```
ERROR: database is locked
```

**Solutions:**

```bash
# 1. Close other ROM Farmer instances
pkill -f rom-farmer

# 2. Remove lock file
rm ~/.config/romfarmer/romfarmer.db-journal

# 3. Wait a moment and retry
sleep 5
rom-farmer dat list

# 4. If persistent, database may be corrupted
mv ~/.config/romfarmer/romfarmer.db{,.corrupted}
# Database will be recreated on next run
```

### Database Corrupted

**Problem:**
```
ERROR: database disk image is malformed
```

**Solutions:**

```bash
# 1. Try to repair
sqlite3 ~/.config/romfarmer/romfarmer.db ".recover" | \
    sqlite3 romfarmer-recovered.db

# 2. If repair fails, start fresh
mv ~/.config/romfarmer/romfarmer.db{,.backup-$(date +%Y%m%d)}
# Database recreated on next run

# 3. Re-import DATs
rom-farmer dat import ~/dats/*.dat
```

### Can't Find Database

**Problem:**
```
ERROR: Database not found
```

**Solution:**
```bash
# Database created automatically on first run
# Check expected location:
ls -la ~/.config/romfarmer/

# If directory doesn't exist, create it:
mkdir -p ~/.config/romfarmer/

# Run any command to initialize:
rom-farmer dat list
```

## FAQ

### Q: Which DAT files should I use?

**A:** 
- **Cartridge systems** (NES, SNES, GB, GBA, Genesis, etc.): Use **No-Intro** DATs
- **Disc systems** (PlayStation, Saturn, Dreamcast, etc.): Use **Redump** DATs
- Download from:
  - No-Intro: https://datomatic.no-intro.org/
  - Redump: http://redump.org/downloads/

### Q: What's the difference between parent and clone ROMs?

**A:**
- **Parent**: The main release, usually the first version
- **Clone**: Variants like different regions, revisions, or languages
- **Example:**
  - Parent: `Super Mario Bros. (World)`
  - Clone: `Super Mario Bros. (USA)`
  - Clone: `Super Mario Bros. (Europe)`
  - Clone: `Super Mario Bros. (Japan)`

### Q: Should I keep clones or use 1G1R?

**A:**
- **Keep all** if you want a complete collection
- **Use 1G1R** if you want just one best version of each game
- **Hybrid**: Keep specific regions (e.g., USA + Japan) but filter out others

### Q: How do I update my DATs?

**A:**
```bash
# Download new DAT files from No-Intro/Redump
# Re-import with --update flag
rom-farmer dat import ~/dats/new.dat --update
```

### Q: Can I use ROM Farmer with RomM, Emudeck, or RetroPie?

**A:**
- **Yes!** ROM Farmer organizes files that work with any frontend
- Use `--mode symlink` to create organized views without duplicating files
- Frontends can scan the organized directories

### Q: How do I handle multi-disc games?

**A:**
- Current: Organize normally, multi-disc detection in filenames
- Future: Automatic M3U playlist generation planned
- Keep disc images together in same directory

### Q: What if my ROMs have different names than the DAT?

**A:**
- ROM Farmer validates by CRC32, not filename
- Use `scan verify` to check individual files
- Consider renaming tools like:
  - Universal ROM Cleaner
  - ROM Vault
  - Advanced ROM Renamer

### Q: Can I run ROM Farmer on a NAS or network share?

**A:**
- **Yes**, but scanning will be slower due to network latency
- Increase threads may not help over network
- Consider running ROM Farmer on the NAS itself

### Q: How much disk space do I need?

**A:**
- **Database**: ~10-50MB per DAT (varies by system)
- **Organization (copy mode)**: 2x your ROM collection size
- **Organization (symlink mode)**: Negligible (just symlinks)
- **Organization (move mode)**: Same as original

### Q: Is ROM Farmer safe to use?

**A:**
- ✅ Use `--dry-run` to preview changes
- ✅ Use `--mode copy` for safety
- ✅ All operations are logged
- ✅ Comprehensive test suite (201 tests)
- ⚠️ Always backup before bulk operations

### Q: Can I contribute to ROM Farmer?

**A:**
- **Yes!** Contributions welcome
- Check GitHub issues for open tasks
- Add tests for new features
- Follow existing code style

### Q: Where can I get help?

**A:**
- Read the docs: `/docs/`
- Check GitHub Issues
- Ask in GitHub Discussions
- Review the test files for examples

### Q: What Python version do I need?

**A:**
- **Minimum**: Python 3.10
- **Recommended**: Python 3.11 or 3.12
- Check: `python3 --version`

### Q: Can ROM Farmer fix corrupted ROMs?

**A:**
- **No** - ROM Farmer can only *detect* corrupted files
- Re-download bad ROMs from legitimate sources
- Use hardware dumpers for physical cartridges

## Getting Help

If you're still stuck:

1. **Check the logs:**
   ```bash
   tail -100 ~/.config/romfarmer/logs/romfarmer.log
   ```

2. **Run with verbose logging:**
   ```bash
   rom-farmer --verbose scan directory /roms
   ```

3. **Create an issue on GitHub:**
   - Include ROM Farmer version
   - Include error messages
   - Include relevant logs
   - Describe steps to reproduce

4. **Ask in GitHub Discussions:**
   - Questions about workflows
   - Best practices
   - Feature requests

## Related Documentation

- [Installation Guide](INSTALLATION.md) - Setup instructions
- [User Guide](USER_GUIDE.md) - Command reference
- [Workflow Guide](WORKFLOWS.md) - End-to-end examples
- [DAT Files Guide](DAT_FILES.md) - Working with DATs
