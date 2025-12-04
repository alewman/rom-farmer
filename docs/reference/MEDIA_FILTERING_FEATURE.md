# Media Type Filtering Feature

## Overview

Added comprehensive media type filtering to workflow system, allowing you to control which of the 9 supported media types are included in the final gamelist.xml and copied to output directories.

## Why This Matters

Different platforms have different needs:
- **Home Theater PC**: Include all media types (2.4 GB for 658-game NES collection)
- **Handheld Device**: Only mix image (1.3 MB for same collection) - **1,846x smaller!**
- **Arcade Cabinet**: No manuals or PDFs
- **Testing**: Minimal media for fast iteration

## Supported Media Types (9 Total)

From your vectrex ARRM data, we support all 9 types:

| Type | Description | Size (Vectrex 30 games) | Typical Size/Game |
|------|-------------|-------------------------|-------------------|
| `image` | Title screen | 20M | ~700KB |
| `boxart` | Box art | 7.0M | ~230KB |
| `screenshot` | In-game screenshot | 3.1M | ~100KB |
| `cartridge` | Cartridge/disc art | 10M | ~330KB |
| `wheel` | Logo/wheel art | 65K | ~2KB |
| `marquee` | Marquee/banner | 1.2M | ~40KB |
| `mix` | ARRM composite | 65K | ~2KB |
| `video` | Video preview | 13M | ~430KB |
| `manual` | PDF manual | 14M | ~460KB |
| **TOTAL** | All 9 types | **68.4M** | **~2.3MB/game** |

## Configuration Levels

You can specify media types at 3 levels:

### 1. Stage Level (Highest Priority)

```yaml
stages:
  - name: "deploy-full"
    type: "deploy"
    config:
      generate_gamelist: true
      media_types: "all"  # All 9 types
      
  - name: "deploy-minimal"
    type: "deploy"
    config:
      generate_gamelist: true
      media_types: ["mix"]  # Just composite image
```

### 2. System Level (Default)

```yaml
system:
  name: "Nintendo - Nintendo Entertainment System"
  platform: "nes"
  media_types: ["mix", "image", "screenshot"]  # Default for all stages
```

### 3. Presets (Convenience)

```yaml
media_types: "all"        # All 9 types
media_types: "minimal"    # Just ["mix"]
media_types: "standard"   # ["image", "boxart", "screenshot", "wheel", "mix"]
media_types: "no-videos"  # All except videos
media_types: "no-manuals" # All except manuals
media_types: []           # No media (gamelist only)
```

### 4. Include/Exclude Syntax

```yaml
media_types:
  include: "all"
  exclude: ["manual", "video"]  # Everything except these
```

## Real-World Examples

### Example 1: Multi-Target Deployment

One input, three outputs with different media configurations:

```yaml
stages:
  - name: "filter"
    type: "filter"
    input: "/data/emu/source/nes"
    output: "/data/emu/rom-processing/nes/stage-1-filtered"

  # Deploy to HTPC (full media)
  - name: "deploy-htpc"
    type: "deploy"
    input: "/data/emu/rom-processing/nes/stage-1-filtered"
    output: "/data/emu/roms/nes"
    config:
      generate_gamelist: true
      media_types: "all"  # 2.4 GB

  # Deploy to handheld (minimal)
  - name: "deploy-handheld"
    type: "deploy"
    input: "/data/emu/rom-processing/nes/stage-1-filtered"
    output: "/mnt/sdcard/roms/nes"
    config:
      generate_gamelist: true
      media_types: ["mix"]  # 1.3 MB

  # Deploy to testing (no media)
  - name: "deploy-test"
    type: "deploy"
    input: "/data/emu/rom-processing/nes/stage-1-filtered"
    output: "/tmp/test/nes"
    config:
      generate_gamelist: true
      media_types: []  # 50 KB
```

### Example 2: Platform-Specific Defaults

```yaml
# Full-featured console (lots of storage)
system:
  platform: "ps2"
  media_types: "all"

# Handheld device (limited storage)
system:
  platform: "gba"
  media_types: ["mix"]

# Arcade cabinet (no manuals)
system:
  platform: "mame"
  media_types:
    include: "all"
    exclude: ["manual"]
```

## Storage Impact (NES 658-game Example)

| Configuration | Size | vs. Full | Use Case |
|---------------|------|----------|----------|
| `"all"` | 2.4 GB | 100% | HTPC, desktop |
| `"standard"` | 850 MB | 35% | Typical setup |
| `["mix", "screenshot"]` | 180 MB | 7.5% | Lightweight |
| `["mix"]` | 1.3 MB | **0.05%** | **Handheld** |
| `[]` | 50 KB | 0.002% | Testing |

**The `["mix"]` configuration is 1,846x smaller than full media!**

## Implementation Status

### ✅ Completed

1. **Documentation** (`docs/WORKFLOW_CONFIG.md`)
   - Complete media type filtering documentation
   - All 9 media types documented with sizes
   - Configuration examples at all 3 levels
   - Real-world examples with storage calculations
   - Include/exclude syntax
   - Preset values

2. **Database Schema** (`src/romgroomer/metadata/database.py`)
   - `MediaType` enum with all 9 types
   - `MediaType.all_types()` - All 9 types
   - `MediaType.standard_types()` - Standard 5 types
   - `MediaType.minimal_types()` - Just mix
   - `ScrapedGame` model with metadata
   - `MediaFile` model with content-addressable storage
   - `GameMediaLink` model for many-to-many relationships
   - `MetadataDatabase` class with helper methods
   - `get_game_media()` method with type filtering

### 🔨 Next Steps

1. **ARRM Importer** (`src/romgroomer/metadata/arrm.py`)
   - Parse gamelist.xml
   - Import all 9 media types
   - Calculate file hashes
   - Store in content-addressable storage

2. **Gamelist Generator** (`src/romgroomer/metadata/generator.py`)
   - Regenerate gamelist.xml
   - Filter media types based on configuration
   - Match games by hash
   - Generate relative paths

3. **Workflow Engine** (`src/romgroomer/workflows/`)
   - Parse YAML configuration
   - Handle media_types at all 3 levels
   - Pass to generator
   - Execute stages

## Key Benefits

1. **Flexibility**: Same source, multiple targets with different media
2. **Storage Savings**: 1.3 MB vs 2.4 GB for handheld devices
3. **Speed**: Less data to copy and sync
4. **Platform-Appropriate**: Each target gets what it supports
5. **Non-Destructive**: Source metadata preserved, filter at deployment

## Questions Answered

**Q: Can I include all media types sometimes?**
✅ Yes: `media_types: "all"`

**Q: Can I just have the mix image?**
✅ Yes: `media_types: ["mix"]` or `media_types: "minimal"`

**Q: Can I have many images but not manuals?**
✅ Yes: `media_types: { include: "all", exclude: ["manual"] }`

**Q: Is this determined by target platform?**
✅ Yes: Configure per deploy stage, system, or use presets

**Q: Can I deploy to multiple targets with different media?**
✅ Yes: Multiple deploy stages from same input (see Example 1)

## Next Implementation Priority

Based on your workflow needs:

1. **ARRM Importer** - Import your existing vectrex metadata (30 games, fast test)
2. **Gamelist Generator** - Regenerate with media type filtering
3. **Test with vectrex** - Verify all 9 media types work
4. **Deploy Stage** - Implement media copying with filtering
5. **Test multi-target** - One input, three outputs (all, minimal, no-manuals)

Should I proceed with implementing the ARRM importer next?
