# Tools Source Directory

This directory contains source code for various ROM management tools that we build and maintain.

## Why Build From Source?

Building tools from source ensures:
- **Consistent versions** across systems
- **Latest features** and bug fixes
- **Understanding** why CHD/XISO/CSO hashes differ between versions
- **Control** over build options and optimizations

## Tools Managed Here

### MAME (includes chdman)
- **Purpose:** CHD (Compressed Hunks of Data) creation/extraction
- **Source:** https://github.com/mamedev/mame/
- **Binary:** `chdman` (CHD manipulation tool)
- **Why:** Different chdman versions create different CHD hashes!

### Future Tools
- **xdvdfs:** Xbox ISO to XISO conversion
- **maxcso:** PSP ISO to CSO compression
- **wit:** Wii ISO tools (WBFS, RVZ)
- **dolphin-tool:** GameCube/Wii RVZ conversion

## Directory Structure

```
tools/
├── README.md              (this file)
├── build.sh               (master build script)
├── mame/                  (MAME source)
│   ├── clone.sh          (clone/update script)
│   ├── build.sh          (build script)
│   └── src/              (git clone of mamedev/mame)
├── xdvdfs/               (future)
├── maxcso/               (future)
└── bin/                  (built binaries)
    ├── chdman -> ../mame/build/chdman
    └── ...
```

## Quick Start

### Build MAME/chdman

```bash
cd tools/mame
./clone.sh    # Clone MAME source (first time only)
./build.sh    # Build chdman
```

### Use Built Tools

```bash
# Binaries are symlinked in tools/bin/
export PATH="/data/emu/rom-groomer-python/tools/bin:$PATH"

# Or use directly
/data/emu/rom-groomer-python/tools/bin/chdman --version
```

## Version Tracking

Each tool directory should track:
- Git commit hash used for build
- Build date
- Compiler version
- Build options used

This helps debug "why do my CHDs have different hashes?" issues!

## CHD Hash Consistency

**Why different chdman versions create different hashes:**

1. **Compression algorithm changes** - New versions improve compression
2. **Hunk size optimization** - Different defaults over time
3. **Metadata handling** - How game info is stored in CHD header
4. **Bug fixes** - Fixes that change output format

**Solution:** Build a specific version and stick with it for consistency!

## Integration with rom-groomer

The `rom-groomer` tool will:
1. Detect which `chdman` version is being used
2. Record tool version in transformation database
3. Use this for debugging hash mismatches
4. Recommend specific versions for consistency

Example transformation record:
```python
ROMTransformation(
    source_file="NiGHTS Into Dreams (USA).cue",
    tool="chdman",
    tool_version="0.251 (mame0251)",
    tool_path="/data/emu/rom-groomer-python/tools/bin/chdman",
    # ...
)
```

## Best Practices

1. **Tag your builds** - Record git commit hash
2. **Test consistency** - Convert same ROM twice, verify hashes match
3. **Document changes** - Note why you're upgrading a tool
4. **Keep old versions** - For reproducing historical conversions
5. **Share configs** - Document build options for reproducibility

## Building on Different Systems

### Linux (Ubuntu/Debian)
```bash
sudo apt-get install build-essential git libsdl2-dev libsdl2-ttf-dev \
  libfontconfig-dev libpulse-dev qtbase5-dev qtchooser qt5-qmake \
  qtbase5-dev-tools
```

### macOS
```bash
brew install sdl2 sdl2_ttf
```

### Performance Builds
```bash
# For faster chdman (optimize for your CPU)
export OPTIMIZE=3
export ARCHOPTS="-march=native"
```

## Troubleshooting

**Build fails with "command not found":**
- Install build dependencies (see above)

**chdman crashes or produces errors:**
- Check input file format (needs CUE+BIN, not just BIN)
- Verify sufficient disk space
- Try different compression level

**Hashes don't match ScreenScraper:**
- Record your chdman version in transformation DB
- Use CUE hash instead (see MULTI_TIER_STRATEGY.md)
- Community may have used different chdman version

## Future Enhancements

1. **Automated builds** - GitHub Actions to build on new releases
2. **Version detection** - Auto-detect installed tool versions
3. **Upgrade warnings** - Warn before changing tool versions
4. **Binary distribution** - Pre-built binaries for common platforms
5. **Docker images** - Reproducible build environments

## See Also

- `docs/TRANSFORMATION_INTEGRATION.md` - How tools integrate with rom-groomer
- `docs/MULTI_TIER_STRATEGY.md` - Why tool versions matter for scraping
- `src/romgroomer/metadata/transformation_recorder.py` - Records tool versions
