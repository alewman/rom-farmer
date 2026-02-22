# AI Toolbox — ROM Farmer

**Last Updated:** February 2026
**Purpose:** Concise, accurate reference for AI assistants. Deep context comes from Engram — call `session_start(project="rom-farmer")` first.

---

## What This Project Does

**ROM Farmer** (`romfarmer`) is a production-grade ROM collection manager that:
- Matches ROMs against DAT files (No-Intro, Redump, TOSEC)
- Applies 1G1R filtering (one game, one region)
- Transforms formats (CHD, XISO, CSO, RVZ, SquashFS, 7z)
- Generates M3U playlists for multi-disc games
- Scrapes metadata (gamelist.xml + media) for EmulationStation/Batocera
- Manages curated collections with include/exclude lists
- Uses a Content-Addressable Store and ROM cache with hardlinks
- Supports budget-based selection with compression prediction

This handles **terabytes** of data across **30+ platforms**. Builds take hours. Be precise.

---

## Quick Commands

```bash
# Install
cd /data/emu/rom-farmer && pip install -e .

# Run tests (440+ passing, ~10,500 lines)
make test
# or: python3 -m pytest tests/ -v

# CLI help
romfarmer --help
romfarmer build --help

# Run a build
romfarmer build run --name <build-name>    # configs in config/builds/*.yaml

# Quick test build (~3 min)
romfarmer build run --name nes-full-eng

# Interactive wizard
./build-wizard

# Plugin system
romfarmer plugin list          # show registered plugins
romfarmer plugin contracts     # I/O contracts table
romfarmer plugin graph         # data flow graph

# Clean build state
romfarmer build clean --name <build-name>
```

---

## Architecture (as of Feb 2026)

### Declarative Pipeline
The project was refactored in Feb 2026 from imperative scripts to a **declarative YAML-driven build pipeline**. Build configs compose platform recipes + target profiles.

### Source Layout
```
src/romfarmer/
├── cli/                 # Click CLI commands (build, cache, dat, lists, plugin, metadata, organize)
├── stages/              # 21 pipeline stages (the core)
├── plugins/             # Plugin system (Protocol-based, EventBus, StageAdapter)
├── cache/               # ROM cache with hardlinks + Content-Addressable Store
├── config/              # Pydantic config models + YAML loader
├── mcp/                 # MCP server tools (collection, dat, scraper, wiki)
├── metadata/            # Scraping, gamelist.xml generation, database
├── models/              # Pydantic data models (Rom, DatGame, etc.)
├── parsers/             # No-Intro/Redump filename parsers
├── dat/                 # DAT file management
├── build_orchestrator.py    # Legacy multi-platform orchestrator
├── new_orchestrator.py      # New declarative BuildSpec orchestrator
├── platform_processor.py    # Single-platform pipeline execution
└── mcp_server.py            # MCP server entry point
```

### 21 Pipeline Stages (in execution order)
| Phase | Priority | Stage | What it does |
|-------|----------|-------|-------------|
| Filter | 10 | PreFilter | Letter/region/language pre-filtering |
| Filter | 20 | FilterDAT | Match against DAT files |
| Filter | 20 | Filter1G1R | 1G1R filtering (mutually exclusive with FilterDAT) |
| Filter | 20 | FilterArcade | Arcade-specific filtering |
| Select | 30 | FilterRating | Rating-based selection |
| Select | 30 | SelectionFilter | Strategy-based selection (7 strategies) |
| Select | 40 | ApplyLists | Include/exclude/rescue lists |
| Cache | 45 | CachePreCheck | Check ROM cache for hits |
| Extract | 50 | ExtractArchive | Unzip archives |
| Extract | 50 | ExtractPS3 | PS3-specific extraction |
| Extract | 50 | UnzipRVZ | GameCube/Wii RVZ extraction |
| Extract | 50 | TransformPS3 | PS3 transformation |
| Compress | 55 | ConvertXISO | Xbox XISO conversion |
| Compress | 60 | CompressSquashfs | SquashFS compression (Xbox/Batocera) |
| Compress | 60 | CompressCHD | CHD compression (disc platforms) |
| Compress | 60 | CompressArchive | 7z/zip compression (cartridge platforms) |
| Organize | 70 | CreateM3U | Multi-disc M3U playlists |
| Organize | 80 | CopyArcade | Arcade file copy |
| Organize | 80 | Organize | Final output structure + list subdirectories |
| Metadata | 90 | GenerateMetadata | gamelist.xml + media scraping |
| Hooks | 95 | ApplyPS3Updates | PS3 updates/DLC |

### Plugin System (branch: refactor/plugin-architecture, not yet merged to main)
- Uses `typing.Protocol` (structural typing), not ABC
- `EventBus` — synchronous, priority-based, wildcard matching
- `StageAdapter` wraps all 21 legacy stages with zero code changes
- 9 no-arg stages auto-register; 12 need constructor config
- CLI: `romfarmer plugin list|contracts|graph`

### Build Configs
```
config/
├── builds/       # Build orchestration YAML (compose recipes + targets)
├── platforms/    # Platform-specific settings
├── recipes/      # Reusable pipeline recipes
├── targets/      # Target device profiles (batocera, rocknix)
└── selections/   # Selection strategy presets
```

### Key Databases
- **romfarmer.db** — Unified SQLite: scraped games, transformations, media
- **ROM cache** — Content-addressable store with hardlinks (avoids re-processing)

---

## Domain Knowledge

### Output Folder Convention
`{platform}-{source}-{filter}-{format}-{target}` — e.g., `saturn-redump-1g1r-eng-chd-batocera`

### Compression Ratios (approximate)
| Platform | Ratio | Notes |
|----------|-------|-------|
| Saturn/Sega CD | 0.62–0.65 | Excellent (binary + audio) |
| PSX | 0.70 | Good |
| PS2 | 0.75 | Decent |
| GameCube/Wii | 0.70–0.72 | Mini-DVDs |
| Xbox | 0.80 | XISO removes padding |
| PSP | 0.85 | Already compressed UMD |
| PS3 | 0.90 | Large Blu-rays |

The system **learns actual ratios** from each build and stores them in the transformations table.

### Multi-Disc Atomicity
Multi-disc games are **always kept together**. Never select disc 1 without disc 2. Selection operates on groups.

### Critical Gotchas
- `cache/` directory is .gitignored — use `git add -f` for source files there
- `--platforms` CLI flag does NOT work with new declarative BuildSpec format (known issue)
- Always `romfarmer build clean --name <build>` before a fresh run to clear stale state
- Screenscraper tests (4) fail without live API access — skip or mock in CI
- The CLI is `romfarmer` (not `romgroomer`) — renamed during the Feb 2026 refactor

---

## Known Issues
- `--platforms` flag only filters for legacy BuildConfig, not new BuildSpec format
- One TODO in `platform_processor.py`: "Implement output verification"
- 4 screenscraper tests need live API access
- ApplyPS3UpdatesStage sometimes returns StageResult instead of StageContext

---

## Working With This Project

### Before proposing a feature
Check if it already exists: `romfarmer --help` and explore the stages/CLI.

### Testing pattern
```bash
make test                              # full suite
python3 -m pytest tests/test_X.py -v   # specific file
python3 -m pytest -k "test_name" -v    # specific test
```

### Build testing
Use small/fast configs for iteration:
- `nes-full-eng` — quick single-platform (~3 min)
- Use `strategy: smallest, limit: 5` for fast iteration

### Code conventions
- Type hints everywhere, Pydantic for config models
- Rich library for CLI output
- Stages are self-contained, follow the `Stage` base class pattern
- `StageContext` is the shared state object passed through the pipeline
