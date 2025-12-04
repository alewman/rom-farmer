# Building MAME/chdman - Quick Start

## Why Build chdman?

Different versions of `chdman` create CHD files with different MD5 hashes, even from identical source files!

**Problem:** Your CHDs have hash `497af110...` but ScreenScraper knows `CC5F238D...`  
**Cause:** Different chdman versions or compression settings  
**Solution:** Build a specific version and document it in transformation database

---

## Quick Build

```bash
cd /data/emu/rom-farmer/tools/mame

# Step 1: Download MAME source (first time only)
./clone.sh

# Step 2: Build chdman
./build.sh

# Step 3: Use it!
../bin/chdman --version
```

---

## What clone.sh Does

1. **Clones MAME repository** from https://github.com/mamedev/mame/
   - Offers shallow clone (faster, ~500MB) or full clone (~1.5GB)
   - Shows recent release tags

2. **Records version info** in `VERSION.txt`
   - Git commit hash
   - Release tag (if on a release)
   - Build date

3. **Allows checkout of specific versions**
   - Can build older versions for reproducibility
   - Can track which version created which CHDs

---

## What build.sh Does

1. **Checks dependencies**
   - Verifies build tools installed (gcc, make, python3)
   - Checks for SDL2 libraries

2. **Builds chdman only** (not full MAME)
   - Uses `TOOLS=1` to build just chdman
   - Optimizes for your CPU (`-march=native`)
   - Takes 5-15 minutes

3. **Installs binary**
   - Copies to `tools/mame/build/chdman`
   - Creates symlink in `tools/bin/chdman`
   - Records build info in `BUILD_INFO.txt`

---

## Testing Hash Consistency

After building, test that conversions are consistent:

```bash
cd /data/emu/rom-farmer/tools/mame

# Convert a test ROM twice
../bin/chdman createcd -i test.cue -o test1.chd
../bin/chdman createcd -i test.cue -o test2.chd

# Verify hashes match
md5sum test1.chd test2.chd

# Should show IDENTICAL hashes!
# If different, something is wrong with the build
```

---

## Integration with rom-farmer

The transformation recorder will detect and record your chdman version:

```python
# Automatically recorded in database
transformation = ROMTransformation(
    source_file="NiGHTS Into Dreams (USA).cue",
    source_md5="09e69b286cb01c4ccd4b275dfed8b32b",
    final_file="NiGHTS Into Dreams (USA).chd",
    final_md5="YOUR_CHD_HASH_HERE",  # Will differ from others!
    tool="chdman",
    tool_version="0.267 (mame0267)",  # Detected automatically
    tool_path="/data/emu/rom-farmer/tools/bin/chdman",
    # ...
)
```

This lets you:
- **Debug** why hashes don't match ScreenScraper
- **Document** which tool version was used
- **Reproduce** conversions later with same version
- **Share** with community for consistency

---

## Why Different chdman Versions Create Different Hashes

### Compression Algorithm Changes
```
MAME 0.200: Uses LZMA compression
MAME 0.250: Improved LZMA with better compression
MAME 0.267: Optimized hunk size calculation
→ Same input, different output!
```

### Header Metadata
```
Older versions: Minimal metadata in CHD header
Newer versions: More game info stored
→ Different headers = different hashes
```

### Bug Fixes
```
MAME 0.240: Fixed audio track handling
→ Fixed versions create different CHDs than buggy versions
```

---

## Recommended Workflow

### For New Conversions

1. **Build latest chdman** (current = 0.267 as of Oct 2025)
2. **Test consistency** (convert same ROM twice)
3. **Document version** in transformation DB
4. **Stick with it** for all your conversions

### For Existing Collections

1. **Don't reconvert everything!** Your CHDs work fine
2. **Use CUE hash** for ScreenScraper queries (see MULTI_TIER_STRATEGY.md)
3. **Document current version** for future reference
4. **Only upgrade** if you have a specific reason

---

## Building Older Versions

If you need to match someone else's CHD hashes:

```bash
cd /data/emu/rom-farmer/tools/mame
./clone.sh

cd src

# List available versions
git tag --sort=-version:refname | head -20

# Checkout specific version
git checkout mame0251  # Example: MAME 0.251

cd ..
./build.sh

# Now test if your CHDs match!
```

---

## Dependencies

### Ubuntu/Debian
```bash
sudo apt-get install build-essential git python3 \
  libsdl2-dev libsdl2-ttf-dev libfontconfig-dev
```

### Fedora/RHEL
```bash
sudo dnf install gcc-c++ make git python3 \
  SDL2-devel SDL2_ttf-devel fontconfig-devel
```

### macOS
```bash
brew install sdl2 sdl2_ttf
xcode-select --install  # For compiler
```

---

## Troubleshooting

### "make: command not found"
```bash
sudo apt-get install build-essential
```

### "SDL2 not found"
```bash
sudo apt-get install libsdl2-dev libsdl2-ttf-dev
```

### Build fails with memory error
```bash
# Reduce parallel jobs
cd src
make TOOLS=1 OPTIMIZE=3 -j2  # Use only 2 cores instead of all
```

### Build succeeds but chdman crashes
```bash
# Try without native optimizations
cd src
make clean
make TOOLS=1 OPTIMIZE=3  # No -march=native
```

---

## See Also

- `tools/README.md` - Overview of tools management
- `docs/MULTI_TIER_STRATEGY.md` - Why CUE hashes solve the problem
- `docs/TRANSFORMATION_INTEGRATION.md` - How tool versions are tracked
- https://github.com/mamedev/mame - Upstream MAME project

---

## Fun Fact

The reason MAME includes `chdman` is because MAME emulates arcade machines that used CHD (Compressed Hunks of Data) format for their hard drives! The format was later adopted by other emulators for compressing CD-based console games.
