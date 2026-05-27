# Workflow Configuration

ROM Farmer workflows are defined in YAML files that specify a series of stages to process ROM collections. This document describes the workflow configuration format.

## Table of Contents

- [Overview](#overview)
- [Basic Structure](#basic-structure)
- [Configuration Options](#configuration-options)
- [Stage Types](#stage-types)
- [Media Type Filtering](#media-type-filtering)
- [Example Workflows](#example-workflows)

## Overview

A workflow is a YAML file that defines:
1. **Metadata**: Name, description, system information
2. **Variables**: Reusable configuration values
3. **Stages**: Sequential processing steps

Each stage produces output in a new directory, making the process **non-destructive** between stages.

## Basic Structure

```yaml
name: "nes-1g1r-english"
description: "Build NES 1G1R collection with English games only"
version: "1.0"

# System configuration
system:
  name: "Nintendo - Nintendo Entertainment System"
  dat: "Nintendo - Nintendo Entertainment System (Headerless)"
  platform: "nes"

# Reusable variables
variables:
  source_dir: "/path/to/source/nes"
  staging_dir: "/path/to/..."
  final_dir: "/path/to/roms/nes"
  
# Processing stages
stages:
  - name: "filter"
    type: "filter"
    input: "${source_dir}"
    output: "${staging_dir}/stage-1-filtered"
    config:
      regions: ["USA", "World", "Europe"]
      languages: ["En"]
      prefer_parent: true
      prefer_revisions: true
      
  - name: "organize"
    type: "organize"
    input: "${staging_dir}/stage-1-filtered"
    output: "${staging_dir}/stage-8-organized"
    config:
      structure: "region"
```

## Configuration Options

### Workflow Metadata

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique workflow identifier |
| `description` | string | No | Human-readable description |
| `version` | string | No | Workflow version (semver) |
| `author` | string | No | Workflow author |
| `tags` | list[string] | No | Tags for categorization |

### System Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `system.name` | string | Yes | System name (matches DAT) |
| `system.dat` | string | Yes | DAT name to use |
| `system.platform` | string | No | Platform code (nes, gb, ps1, etc.) |
| `system.media_types` | list[string] | No | Default media types to include (see below) |

### Variables

Variables use `${variable_name}` syntax and can be referenced in any string field:

```yaml
variables:
  source_dir: "/path/to/source/nes"
  regions: ["USA", "World"]
  
stages:
  - name: "filter"
    input: "${source_dir}"  # Expands to /path/to/source/nes
    config:
      regions: "${regions}"  # Expands to ["USA", "World"]
```

### Stage Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Stage identifier |
| `type` | string | Yes | Stage type (see below) |
| `input` | string | Yes | Input directory (or previous stage) |
| `output` | string | Yes | Output directory |
| `enabled` | boolean | No | Enable/disable stage (default: true) |
| `config` | object | No | Stage-specific configuration |

## Stage Types

### 1. Filter Stage

Apply 1G1R (One Game One ROM) filtering to reduce collection to best versions.

**Type:** `filter`

**Configuration:**
```yaml
- name: "filter"
  type: "filter"
  input: "${source_dir}"
  output: "${staging_dir}/stage-1-filtered"
  config:
    regions: ["USA", "World", "Europe"]  # Region priority order
    languages: ["En"]                     # Language priority
    prefer_parent: true                   # Prefer parent over clones
    prefer_revisions: true                # Prefer latest revisions
    exclude_bios: true                    # Exclude BIOS files
    exclude_proto: true                   # Exclude prototypes
    exclude_demo: true                    # Exclude demos
    exclude_beta: true                    # Exclude betas
```

### 2. Delete Stage

Remove problematic or unwanted ROMs based on exclude lists.

**Type:** `delete`

**Configuration:**
```yaml
- name: "delete"
  type: "delete"
  input: "${staging_dir}/stage-1-filtered"
  output: "${staging_dir}/stage-2-cleaned"
  config:
    exclude_lists:
      - "/path/to/..."
      - "/path/to/..."
    exclude_patterns:
      - "*[b]*"          # Bad dumps
      - "*[h]*"          # Hacks
      - "*(Unl)*"        # Unlicensed
```

### 3. Extract Stage

Decompress archived ROMs (ZIP, 7Z, RAR).

**Type:** `extract`

**Configuration:**
```yaml
- name: "extract"
  type: "extract"
  input: "${staging_dir}/stage-2-cleaned"
  output: "${staging_dir}/stage-3-extracted"
  config:
    formats: ["zip", "7z"]     # Archive formats to extract
    delete_archives: false     # Keep original archives
    prefer_largest: true       # If multiple files, keep largest
```

### 4. Process Stage

Transform ROMs (decrypt, convert, patch).

**Type:** `process`

**Configuration:**
```yaml
- name: "process"
  type: "process"
  input: "${staging_dir}/stage-3-extracted"
  output: "${staging_dir}/stage-4-processed"
  config:
    operations:
      - type: "decrypt"
        tool: "ps3dec"
        extensions: [".iso"]
      - type: "convert"
        from: ".bin"
        to: ".chd"
        tool: "chdman"
```

### 5. Enrich Stage

Add metadata and generate playlists (M3U for multi-disc games).

**Type:** `enrich`

**Configuration:**
```yaml
- name: "enrich"
  type: "enrich"
  input: "${staging_dir}/stage-4-processed"
  output: "${staging_dir}/stage-5-enriched"
  config:
    generate_m3u: true         # Create M3U playlists
    m3u_pattern: "*Disc*"      # Pattern to detect multi-disc
    add_metadata: true         # Add metadata files
    metadata_source: "arrm"    # Use ARRM metadata
```

### 6. Validate Stage

Scan and verify ROMs against DAT files.

**Type:** `validate`

**Configuration:**
```yaml
- name: "validate"
  type: "validate"
  input: "${staging_dir}/stage-5-enriched"
  output: "${staging_dir}/stage-6-validated"
  config:
    dat: "${system.dat}"
    strict: false              # Continue on errors
    report_missing: true       # Report missing ROMs
    report_extra: true         # Report unknown files
```

### 7. Collections Stage

Create special curated collections (Best Games, Translations, etc.).

**Type:** `collections`

**Configuration:**
```yaml
- name: "collections"
  type: "collections"
  input: "${staging_dir}/stage-6-validated"
  output: "${staging_dir}/stage-7-collections"
  config:
    collections:
      - name: "Best Games"
        list: "/path/to/..."
        method: "copy"         # or "symlink"
      - name: "English Translations"
        list: "/path/to/..."
        method: "copy"
    preserve_structure: true   # Don't reorganize into subfolders
```

### 8. Organize Stage

Organize ROMs into directory structure (regions, kinds, languages).

**Type:** `organize`

**Configuration:**
```yaml
- name: "organize"
  type: "organize"
  input: "${staging_dir}/stage-7-collections"
  output: "${staging_dir}/stage-8-organized"
  config:
    structure: "region"        # "region", "kind", "language", "flat"
    create_playlists: true     # Create per-folder playlists
```

### 9. Deploy Stage

Copy to final destination with metadata generation.

**Type:** `deploy`

**Configuration:**
```yaml
- name: "deploy"
  type: "deploy"
  input: "${staging_dir}/stage-8-organized"
  output: "${final_dir}"
  config:
    method: "copy"             # "copy", "move", "symlink"
    verify: true               # Verify copied files
    generate_gamelist: true    # Generate gamelist.xml
    media_types: ["mix"]       # Media types to include (see below)
```

## Media Type Filtering

ROM Farmer supports 9 media types from ScreenScraper/ARRM. You can control which media types are included in the final gamelist.xml and copied to the output directory.

### Supported Media Types

| Type | Description | Typical Size | Usage |
|------|-------------|--------------|-------|
| `image` | Title screen | ~700KB each | Main display image |
| `boxart` | Box art | ~230KB each | Box/cover art |
| `screenshot` | In-game screenshot | ~100KB each | Gameplay preview |
| `cartridge` | Cartridge/disc art | ~330KB each | Physical media art |
| `wheel` | Logo/wheel art | ~2KB each | Text logo |
| `marquee` | Marquee/banner | ~40KB each | Arcade marquee |
| `mix` | Composite image (ARRM) | ~2KB each | **All-in-one image** |
| `video` | Video preview | ~430KB each | Video preview |
| `manual` | PDF manual | ~460KB each | Game manual |

### Configuration Levels

Media types can be specified at three levels (in priority order):

1. **Stage level** (highest priority)
2. **System level** (default for system)
3. **Global default** (fallback)

#### Example: Stage-Level Configuration

```yaml
stages:
  - name: "deploy-full"
    type: "deploy"
    output: "${final_dir}/full"
    config:
      generate_gamelist: true
      media_types: "all"  # Include all 9 media types
      
  - name: "deploy-minimal"
    type: "deploy"
    output: "${final_dir}/minimal"
    config:
      generate_gamelist: true
      media_types: ["mix"]  # Only composite image
      
  - name: "deploy-portable"
    type: "deploy"
    output: "${final_dir}/portable"
    config:
      generate_gamelist: true
      media_types: ["mix", "screenshot", "wheel"]  # Lightweight set
      
  - name: "deploy-no-manuals"
    type: "deploy"
    output: "${final_dir}/no-manuals"
    config:
      generate_gamelist: true
      media_types:
        include: "all"
        exclude: ["manual", "video"]  # Everything except manuals/videos
```

#### Example: System-Level Configuration

```yaml
system:
  name: "Nintendo - Nintendo Entertainment System"
  dat: "Nintendo - Nintendo Entertainment System (Headerless)"
  platform: "nes"
  media_types: ["mix", "image", "screenshot"]  # Default for all stages
  
stages:
  - name: "deploy"
    type: "deploy"
    config:
      generate_gamelist: true
      # Uses system default: ["mix", "image", "screenshot"]
```

#### Example: Per-Platform Presets

```yaml
# Full-featured home console (plenty of storage)
system:
  platform: "ps2"
  media_types: "all"
  
# Handheld device (limited storage)
system:
  platform: "gba"
  media_types: ["mix"]  # Just composite image
  
# Emulation frontend (rich UI)
system:
  platform: "nes"
  media_types: ["image", "boxart", "screenshot", "video", "wheel", "mix"]
  
# Arcade cabinet (authentic)
system:
  platform: "mame"
  media_types: ["marquee", "screenshot", "video"]
```

### Special Values

- `"all"` - Include all 9 media types
- `"minimal"` - Include only `["mix"]`
- `"standard"` - Include `["image", "boxart", "screenshot", "wheel", "mix"]`
- `"no-videos"` - Include all except `["video"]`
- `"no-manuals"` - Include all except `["manual"]`
- `[]` - No media (gamelist.xml only)

### Include/Exclude Syntax

```yaml
media_types:
  include: "all"
  exclude: ["manual", "video"]  # Everything except these
```

### Storage Impact

Example for 658-game NES collection:

| Configuration | Estimated Size | Use Case |
|---------------|----------------|----------|
| `all` | ~2.4 GB | Full EmulationStation setup |
| `standard` | ~850 MB | Typical home console |
| `["mix", "screenshot"]` | ~180 MB | Handheld device |
| `["mix"]` | ~1.3 MB | **Minimal** (recommended for portables) |
| `[]` | ~50 KB | No media (gamelist only) |

## Example Workflows

### Example 1: Full-Featured NES Collection

```yaml
name: "nes-full-collection"
description: "Complete NES collection with all media"
version: "1.0"

system:
  name: "Nintendo - Nintendo Entertainment System"
  dat: "Nintendo - Nintendo Entertainment System (Headerless)"
  platform: "nes"
  media_types: "all"  # Default to all media types

variables:
  source_dir: "/path/to/source/nes"
  staging_dir: "/path/to/..."
  final_dir: "/path/to/roms/nes"

stages:
  - name: "filter"
    type: "filter"
    input: "${source_dir}"
    output: "${staging_dir}/stage-1-filtered"
    config:
      regions: ["USA", "World", "Europe"]
      languages: ["En"]
      prefer_parent: true
      prefer_revisions: true

  - name: "delete"
    type: "delete"
    input: "${staging_dir}/stage-1-filtered"
    output: "${staging_dir}/stage-2-cleaned"
    config:
      exclude_lists:
        - "/path/to/..."

  - name: "collections"
    type: "collections"
    input: "${staging_dir}/stage-2-cleaned"
    output: "${staging_dir}/stage-7-collections"
    config:
      collections:
        - name: "Best Games"
          list: "/path/to/..."
          method: "copy"

  - name: "organize"
    type: "organize"
    input: "${staging_dir}/stage-7-collections"
    output: "${staging_dir}/stage-8-organized"
    config:
      structure: "region"

  - name: "deploy"
    type: "deploy"
    input: "${staging_dir}/stage-8-organized"
    output: "${final_dir}"
    config:
      method: "copy"
      generate_gamelist: true
      media_types: "all"  # Include all 9 media types
```

### Example 2: Portable Device (Minimal Storage)

```yaml
name: "gba-portable-minimal"
description: "GBA collection for portable device (minimal storage)"
version: "1.0"

system:
  name: "Nintendo - Game Boy Advance"
  dat: "Nintendo - Game Boy Advance"
  platform: "gba"
  media_types: ["mix"]  # Just composite images

variables:
  source_dir: "/path/to/source/gba"
  staging_dir: "/path/to/..."
  final_dir: "/mnt/sdcard/roms/gba"

stages:
  - name: "filter"
    type: "filter"
    input: "${source_dir}"
    output: "${staging_dir}/stage-1-filtered"
    config:
      regions: ["USA", "World"]
      languages: ["En"]

  - name: "deploy"
    type: "deploy"
    input: "${staging_dir}/stage-1-filtered"
    output: "${final_dir}"
    config:
      method: "copy"
      generate_gamelist: true
      media_types: ["mix"]  # Only 1.3MB for 658 games!
```

### Example 3: Multi-Target Deployment

```yaml
name: "ps1-multi-target"
description: "PS1 collection with multiple deployment targets"
version: "1.0"

system:
  name: "Sony - PlayStation"
  dat: "Sony - PlayStation"
  platform: "ps1"

variables:
  source_dir: "/path/to/source/ps1"
  staging_dir: "/path/to/..."

stages:
  - name: "filter"
    type: "filter"
    input: "${source_dir}"
    output: "${staging_dir}/stage-1-filtered"
    config:
      regions: ["USA"]

  # Deploy to home theater PC (full media)
  - name: "deploy-htpc"
    type: "deploy"
    input: "${staging_dir}/stage-1-filtered"
    output: "/path/to/roms/ps1"
    config:
      generate_gamelist: true
      media_types: "all"

  # Deploy to handheld (lightweight)
  - name: "deploy-handheld"
    type: "deploy"
    input: "${staging_dir}/stage-1-filtered"
    output: "/mnt/handheld/ps1"
    config:
      generate_gamelist: true
      media_types: ["mix", "screenshot"]

  # Deploy to arcade cabinet (no manuals)
  - name: "deploy-arcade"
    type: "deploy"
    input: "${staging_dir}/stage-1-filtered"
    output: "/mnt/arcade/ps1"
    config:
      generate_gamelist: true
      media_types:
        include: "all"
        exclude: ["manual", "video"]
```

### Example 4: Saturn with Disc Processing

```yaml
name: "saturn-usa-1g1r"
description: "Saturn collection with disc processing and metadata"
version: "1.0"

system:
  name: "Sega - Saturn"
  dat: "Sega - Saturn"
  platform: "saturn"
  media_types: "standard"  # Standard media set

variables:
  source_dir: "/path/to/source/saturn"
  staging_dir: "/path/to/..."
  final_dir: "/path/to/roms/saturn"

stages:
  - name: "filter"
    type: "filter"
    input: "${source_dir}"
    output: "${staging_dir}/stage-1-filtered"
    config:
      regions: ["USA"]

  - name: "extract"
    type: "extract"
    input: "${staging_dir}/stage-1-filtered"
    output: "${staging_dir}/stage-3-extracted"
    config:
      formats: ["zip"]

  - name: "enrich"
    type: "enrich"
    input: "${staging_dir}/stage-3-extracted"
    output: "${staging_dir}/stage-5-enriched"
    config:
      generate_m3u: true
      m3u_pattern: "*Disc*"

  - name: "deploy"
    type: "deploy"
    input: "${staging_dir}/stage-5-enriched"
    output: "${final_dir}"
    config:
      generate_gamelist: true
      media_types: "standard"  # Standard set without manuals/videos
```

## Best Practices

### Storage Planning

1. **Test first**: Run workflow with `media_types: ["mix"]` to test
2. **Measure impact**: Check output size before deploying to target device
3. **Adjust per platform**: Use `"all"` for home consoles, `["mix"]` for handhelds

### Performance

1. **Reuse staging**: Stage-1-filtered output can be reused for multiple workflows
2. **Parallel deployments**: Multiple deploy stages can run from same input
3. **Incremental updates**: Only regenerate gamelist when metadata changes

### Organization

1. **One workflow per system**: Keep workflows system-specific
2. **Version control**: Store workflows in git repository
3. **Document changes**: Update workflow description when modifying

### Media Selection Guidelines

- **All media** (`"all"`): Home theater PCs, desktop emulation
- **Standard** (`"standard"`): Typical EmulationStation setup
- **Mix only** (`["mix"]`): Handhelds, limited storage devices
- **No manuals** (`exclude: ["manual"]`): Save space, most don't read them
- **No videos** (`exclude: ["video"]`): Save significant space (videos are largest)

## Next Steps

- See [WORKFLOWS.md](WORKFLOWS.md) for complete workflow examples
- See [CLI_REFERENCE.md](CLI_REFERENCE.md) for workflow commands
- See [METADATA.md](METADATA.md) for metadata management details
