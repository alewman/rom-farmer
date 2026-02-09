# MCP Server Context for ROM Farmer

**Purpose:** Context document for building an MCP (Model Context Protocol) server that exposes ROM Farmer functionality to AI assistants.

**Last Updated:** January 31, 2026

---

## 🎯 MCP Server Goals

An MCP server for ROM Farmer would expose ROM collection management capabilities to AI assistants, enabling:

1. **Build Management** - Trigger and monitor ROM builds
2. **Collection Queries** - Search and analyze ROM collections  
3. **Metadata Operations** - Scrape, query, and generate metadata
4. **DAT Operations** - Manage DAT files and filtering
5. **Storage Analysis** - Budget calculations and compression estimates

---

## 🏗️ ROM Farmer Architecture Overview

### Core Components (for MCP exposure)

```
romfarmer/
├── build_orchestrator.py    # Multi-platform build coordination
├── platform_processor.py    # Single-platform pipeline execution
├── stages/                  # Pipeline stages (7 total)
│   ├── base.py             # StageContext, StageResult, StageStatus
│   ├── pipeline.py         # Pipeline execution
│   ├── filter_dat.py       # Match files to DAT entries
│   ├── filter_selection.py # Selection strategies (rating_budget, etc.)
│   ├── apply_lists.py      # Include/exclude/rescue lists
│   ├── extract.py          # Archive extraction
│   ├── compress.py         # CHD/CSO/RVZ compression
│   ├── m3u.py              # Multi-disc playlist generation
│   └── metadata.py         # Scraping and gamelist.xml
├── metadata/
│   ├── database.py         # SQLAlchemy models + queries
│   ├── scraper.py          # ScreenScraper API client
│   └── generator.py        # gamelist.xml generation
├── config/
│   ├── models.py           # Pydantic config models
│   └── loader.py           # YAML config loading
├── core/
│   ├── hashing.py          # System-aware MD5/CRC32/SHA1
│   ├── paths.py            # Path resolution
│   └── logger.py           # Rich-based logging
└── cli/
    ├── __init__.py         # Click CLI groups
    ├── build.py            # Build commands
    └── quick.py            # Interactive wizard
```

### Key Data Models

#### StageContext (pipeline state)
```python
@dataclass
class StageContext:
    platform_name: str
    platform_config: PlatformConfig
    target_name: str
    source_dir: Path
    work_dir: Path
    output_dir: Path
    composed_target: Optional[ComposedTarget]
    tier: Optional[int]  # 1-5 priority tier
    tier_strategy: Optional[str]  # 'always_include', 'best_of', 'skip'
    files: FileSet
    hashes: FileHashes
    discs: DiscProcessing
    processing_stats: ProcessingStats
```

#### BuildConfig (from YAML)
```python
class BuildConfig(BaseModel):
    name: str
    description: Optional[str]
    platforms: List[str]
    storage: StorageConfig
    output_naming: OutputNamingConfig
    # For target builds:
    target: Optional[str]
    storage_budget: Optional[str]  # "64GB", "128GB", etc.
```

#### PlatformConfig (from YAML)
```python
class PlatformConfig(BaseModel):
    name: str
    sources: List[SourceConfig]
    dat_source: DATSource
    extraction: ExtractionConfig
    compression: CompressionConfig
    organization: OrganizationConfig
    selection: Optional[SelectionConfig]
```

---

## 🔧 MCP Tools to Implement

### Tier 1: Essential Operations

| Tool | Description | Input | Output |
|------|-------------|-------|--------|
| `list_platforms` | List configured platforms | - | Platform names, configs |
| `list_builds` | List available build configs | - | Build names, descriptions |
| `get_build_status` | Check build progress | build_name | Status, progress % |
| `query_collection` | Search ROM database | platform, query | Matching ROMs |
| `get_platform_stats` | Platform ROM counts/sizes | platform | Stats summary |

### Tier 2: Build Operations

| Tool | Description | Input | Output |
|------|-------------|-------|--------|
| `start_build` | Start a build | build_name | Build ID, status |
| `cancel_build` | Cancel running build | build_id | Confirmation |
| `resume_build` | Resume interrupted build | build_name | Resume status |
| `validate_build` | Verify build completion | build_name | Validation report |

### Tier 3: Metadata Operations

| Tool | Description | Input | Output |
|------|-------------|-------|--------|
| `scrape_metadata` | Scrape from ScreenScraper | platform, rom_hashes | Metadata results |
| `generate_gamelist` | Generate gamelist.xml | platform, output_dir | File path |
| `lookup_game` | Get game metadata | hash or name | Game metadata |
| `get_compression_ratio` | Get compression stats | platform | Historical ratios |

### Tier 4: Analysis Operations

| Tool | Description | Input | Output |
|------|-------------|-------|--------|
| `calculate_budget` | Estimate output size | platform, budget_gb | Selection count |
| `find_missing_roms` | Compare vs DAT | platform, source_dir | Missing list |
| `analyze_duplicates` | Find duplicate ROMs | source_dir | Duplicate groups |
| `suggest_selection` | AI-assisted curation | platform, budget | Recommended list |

---

## 📊 Resource Endpoints for MCP

### Static Resources

| Resource | URI Pattern | Description |
|----------|-------------|-------------|
| Platform Configs | `romfarmer://platforms/{name}` | Platform YAML config |
| Build Configs | `romfarmer://builds/{name}` | Build YAML config |
| DAT Files | `romfarmer://dats/{platform}` | DAT file info |
| Lists | `romfarmer://lists/{platform}/{type}` | Keep/delete lists |

### Dynamic Resources

| Resource | URI Pattern | Description |
|----------|-------------|-------------|
| Build State | `romfarmer://state/builds/{name}` | Current build state |
| Collection Stats | `romfarmer://stats/{platform}` | ROM collection stats |
| Recent Logs | `romfarmer://logs/recent` | Recent operation logs |

---

## 🔄 MCP Prompts to Implement

### Build Prompts

```yaml
build_rom_collection:
  description: "Build a ROM collection for a target device"
  arguments:
    - platform: Platform to build (saturn, psx, etc.)
    - target: Target device (batocera, rocknix, etc.)
    - budget: Storage budget (64GB, 128GB, unlimited)
```

### Analysis Prompts

```yaml
analyze_collection:
  description: "Analyze ROM collection health"
  arguments:
    - platform: Platform to analyze
    
recommend_games:
  description: "Get game recommendations for budget"
  arguments:
    - platform: Platform name
    - budget_gb: Storage budget in GB
    - preferences: User preferences (genres, ratings)
```

---

## 🏃 Implementation Path

### Phase 1: Foundation
1. Create MCP server skeleton with FastMCP or mcp-python
2. Implement `list_platforms`, `list_builds`, `get_build_status`
3. Add static resource endpoints for configs
4. Basic error handling and logging

### Phase 2: Read Operations  
1. `query_collection` - Search ROM database
2. `get_platform_stats` - Collection statistics
3. `lookup_game` - Individual game metadata
4. `find_missing_roms` - DAT comparison

### Phase 3: Build Operations
1. `start_build` - Async build execution
2. Build progress notifications (MCP notifications)
3. `cancel_build`, `resume_build` support
4. Build state persistence

### Phase 4: AI-Enhanced Features
1. `suggest_selection` - AI-powered game curation
2. Natural language collection queries
3. Smart budget optimization
4. Genre/quality balancing

---

## 🔌 Integration Points

### Database Access
```python
# Metadata database for game info
from romfarmer.metadata.database import MetadataDB
db = MetadataDB("metadata/database/romfarmer.db")

# Query games
games = db.get_games_for_platform("saturn")
ratio = db.get_average_compression_ratio("saturn", "chd")
```

### Build Execution
```python
from romfarmer.build_orchestrator import BuildOrchestrator

# Load and run build
orchestrator = BuildOrchestrator.from_config("batocera-full")
result = orchestrator.run()
```

### Hashing (for lookups)
```python
from romfarmer.core.hashing import calculate_md5

# System-aware hashing (arcade vs cartridge vs disc)
md5 = calculate_md5(rom_path, "saturn")
```

---

## 📁 Key File Locations

| Purpose | Path |
|---------|------|
| Platform configs | `config/platforms/*.yaml` |
| Build configs | `config/builds/*.yaml` |
| Selection presets | `config/selections/*.yaml` |
| DAT files | `dats/` |
| Metadata DB | `metadata/database/romfarmer.db` |
| Build state | `.build_state_*.yaml` |
| Logs | `logs/` |
| Keep/delete lists | `lists/{platform}-keep`, `lists/{platform}-delete` |

---

## ⚡ Key Considerations for MCP

### Async Operations
- Builds can take hours (Wii CHD compression)
- MCP server needs async task management
- Progress notifications via MCP notification channel
- Cancellation support for long-running operations

### File Size Awareness
- ROM collections are TERABYTES
- DAT files can be large (100MB+)
- Avoid returning full file contents
- Use summaries, counts, and pagination

### Platform-Specific Behavior
- Different hashing per system (arcade vs cartridge)
- Different compression per format
- Different organization per target
- MCP tools should be platform-aware

### Error Recovery
- Builds can be interrupted
- State persistence is critical
- Resume capability for large operations
- Clear error messages for AI

---

## 🧪 Testing Strategy

### Unit Tests
- Tool input/output validation
- Config parsing
- Hash calculations

### Integration Tests
- Small platform builds (5-10 ROMs)
- Database queries
- Metadata scraping (mock API)

### End-to-End Tests
- Full build workflow
- Progress tracking
- State persistence

---

## 📚 Related Documentation

- [README.md](README.md) - Project overview
- [AI.md](AI.md) - Comprehensive AI context
- [AI-CONTEXT.md](AI-CONTEXT.md) - Quick reference for AI
- [BUILD-WIZARD.md](BUILD-WIZARD.md) - Interactive build guide
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design

---

## 🔮 Future Enhancements

### MCP Server Extensions
- **Subscriptions** - Real-time build progress
- **Batch Operations** - Multi-platform builds
- **Collaborative Curation** - Share curated lists
- **Cloud Integration** - Remote source support

### AI Integration
- **Natural Language Builds** - "Build a 64GB Saturn collection with the best RPGs"
- **Smart Recommendations** - Based on play history
- **Conflict Resolution** - Multi-disc handling, duplicates
- **Quality Assessment** - ROM verification, hash matching

---

## ✅ Ready for MCP Development

This document provides the foundation for building an MCP server that exposes ROM Farmer's capabilities. The architecture is modular, the data models are well-defined, and the tooling is production-ready.

**Next Steps:**
1. Choose MCP framework (FastMCP recommended)
2. Create server skeleton
3. Implement Tier 1 tools
4. Add resource endpoints
5. Test with Claude Desktop

**ROM Farmer is ready to serve.** 🌾
