# ROM Farmer

**The first AI-native ROM collection manager.** Point your AI coding agent at this workspace and manage terabytes of retro gaming ROMs through natural language.

```
You: "Deploy PSX to my batocera within 60GB, prioritize RPGs"
Farm-Hand: connects → scans target → plans budget → builds collection → deploys via SSH
```

ROM Farmer is a production-grade pipeline for curating, building, and deploying ROM collections across 30+ platforms. **Farm-Hand** is its AI operator layer — a ChatOps system that turns your AI assistant into a ROM collection expert that learns and improves with every workflow.

> **This project is designed to be driven by an AI agent.** It exposes 37 [MCP](https://modelcontextprotocol.io) tools for any compatible client — VS Code Copilot, Claude Desktop, Cursor, Windsurf, Cline, or any of the [100+ MCP clients](https://modelcontextprotocol.io/clients). Your AI reads the toolbox, discovers the tools, and operates the system on your behalf.

---

## Why AI-Native?

Every ROM manager today — RomM, Igir, Retool, clrmamepro — assumes a human operator clicking through UIs or memorizing CLI flags. ROM Farmer inverts this:

| Traditional | ROM Farmer |
|---|---|
| Memorize CLI flags for 30+ platforms | Describe what you want in plain English |
| Write one-off shell scripts | Agent captures workflows as reusable skills |
| Manually SSH into devices | Farm-Hand connects, scans, and deploys |
| Re-discover approaches each session | Skills compound — the agent remembers |
| Web UI or nothing | Any MCP-compatible AI client |

The ROM domain is uniquely suited to AI operation: it requires deep knowledge of DAT standards, region/language priorities, compression formats, disc handling quirks, platform-specific gotchas, and storage budgeting — exactly the kind of institutional knowledge an agent can accumulate and apply systematically.

---

## Quick Start

### 1. Install

```bash
git clone https://github.com/alewman/rom-farmer.git
cd rom-farmer
pip install -e ".[farmhand]"
```

### 2. Connect Your AI

Add to your MCP client configuration (Claude Desktop, VS Code, etc.):

```json
{
  "mcpServers": {
    "romfarmer": {
      "command": "python3",
      "args": ["-m", "romfarmer.mcp_server"],
      "cwd": "/path/to/rom-farmer",
      "env": {
        "PYTHONPATH": "/path/to/rom-farmer/src"
      }
    }
  }
}
```

### 3. Start Prompting

```
"What platforms do I have in my collection?"
"Build a 1G1R English PSX set compressed to CHD"
"Connect to my batocera at 10.10.20.183 and scan what's there"
"How much space would Saturn + Dreamcast + PSX take?"
"Show me the curated essentials list for Saturn"
"Deploy the top-rated PS2 games within 120GB to my device"
```

The agent discovers the MCP tools automatically, reads `AI_TOOLBOX.md` for domain context, and operates the full pipeline.

---

## Architecture

ROM Farmer has two layers: the **data/pipeline engine** and the **AI operator**.

```
┌─────────────────────────────────────────────────────────────┐
│  Your AI Agent (Copilot / Claude / Cursor / Cline / ...)    │
│  Reads AI_TOOLBOX.md → discovers 37 MCP tools → operates    │
├─────────────────────────────────────────────────────────────┤
│  Farm-Hand (ChatOps Layer)                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐  │
│  │ SSH +    │ │ Analyzer │ │ Planner  │ │ Skill System  │  │
│  │ Deployer │ │ (target) │ │ (budget) │ │ (learn+reuse) │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ROM Farmer (Data + Pipeline Engine)                         │
│  ┌────────┐ ┌────────┐ ┌──────────┐ ┌────────┐ ┌────────┐ │
│  │ DAT    │ │ Build  │ │ 21-Stage │ │ Cache  │ │ Meta-  │ │
│  │ Files  │ │ System │ │ Pipeline │ │ + CAS  │ │ data   │ │
│  └────────┘ └────────┘ └──────────┘ └────────┘ └────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### ROM Farmer — The Engine

The core pipeline that curates and builds ROM collections:

- **DAT Management** — Import and query No-Intro, Redump, and TOSEC DAT files
- **1G1R Filtering** — Keep one game, one region with configurable priorities
- **21-Stage Pipeline** — Filter → Select → Cache → Extract → Compress → Organize → Metadata
- **Format Transforms** — BIN/CUE→CHD, RVZ extraction, XISO conversion, SquashFS, 7z, CSO
- **Budget Selection** — "Fit the best games in N gigabytes" with compression prediction
- **Multi-Disc Atomicity** — Never splits disc sets (Disc 1 without Disc 2)
- **ROM Cache + CAS** — Content-addressable store with hardlinks avoids re-processing
- **Metadata Scraping** — ScreenScraper API + Wikipedia + gamelist.xml generation
- **30+ Platforms** — NES through PS3, including arcade (FBNeo/MAME/Naomi/Atomiswave)

### Farm-Hand — The AI Operator

The agent-facing layer that makes ROM Farmer conversational:

- **SSH Deployment** — Connect to Batocera/RockNIX devices, analyze volumes, transfer ROMs
- **Target Analysis** — Scan storage, capabilities, existing collections on remote devices
- **Budget Planning** — Optimal platform allocation across volumes with tiered sizing
- **Skill System** — Reusable agent procedures that compound over time (see below)
- **9 Skill MCP Tools** — Search, show, capture, save, and manage skills programmatically

---

## The Skill System

Farm-Hand learns. When the agent completes a workflow — deploying a platform, setting up symlinks, curating a game list — it can capture that workflow as a **skill**: a markdown contract (`SKILL.md`) paired with a machine-readable procedure (`procedure.yaml`) and optional artifacts (scripts, game lists, configs).

```
skills/
├── scan-and-plan/              # First-run target discovery
│   ├── SKILL.md                # What, when, why (YAML frontmatter + markdown)
│   └── procedure.yaml          # Step-by-step (MCP calls, shell, SSH, conditionals)
├── deploy-platform-budget/     # Deploy within storage budget
├── batocera-dual-volume-setup/ # Multi-disk Batocera with symlinks
│   ├── SKILL.md
│   ├── procedure.yaml
│   ├── setup-rom-symlinks.sh   # Artifact: reusable shell script
│   └── verify-symlinks.sh
└── curated-essentials-list/    # Culturally important games
    ├── SKILL.md
    ├── procedure.yaml
    └── essentials/
        ├── saturn.yaml         # Artifact: curated game list
        └── psx.yaml
```

**Dual-path resolution**: bundled skills ship with the project (read-only); agent-created skills live in `config/farmhand/skills/` (read-write) and shadow bundled ones by name.

**Auto-capture**: the agent records its actions during a workflow, then distills them into a templatized procedure where concrete values become `{{parameters}}`. Next time, it replaces parameters and replays.

```bash
romfarmer farmhand skill list            # Browse available skills
romfarmer farmhand skill show <name>     # Full details + procedure
romfarmer farmhand skill search "budget" # Text search
romfarmer farmhand skill cat <name> <file>   # Read any artifact
```

Each builder's Farm-Hand develops a unique skill library tailored to their collection, their devices, and their preferences.

---

## MCP Tools (37)

The MCP server exposes everything the agent needs:

| Category | Tools | Purpose |
|---|---|---|
| **Collection** | `list_platforms`, `list_builds`, `get_build_status`, `get_platform_stats`, `query_collection`, `calculate_budget`, `get_compression_ratio` | Query and manage ROM collection and builds |
| **DAT Files** | `dat_hardware_list`, `dat_hardware_games`, `dat_game_variants`, `dat_search` | Search and query imported DAT databases |
| **Metadata** | `scraper_search`, `scraper_game_info`, `scraper_platforms`, `scraper_genres`, `scraper_top_rated` | ScreenScraper API for game info and ratings |
| **Wikipedia** | `wiki_search`, `wiki_game_info`, `wiki_get_section`, `wiki_stats`, `wiki_find_game` | Wikipedia game research and context |
| **Farm-Hand** | `farmhand_connect`, `farmhand_scan_target`, `farmhand_analyze_fit`, `farmhand_generate_plan`, `farmhand_remote_exec`, `farmhand_get_target_info`, `farmhand_deploy_status` | SSH deployment to remote targets |
| **Skills** | `farmhand_skill_search`, `farmhand_skill_show`, `farmhand_skill_artifact`, `farmhand_skill_save`, `farmhand_skill_save_artifact`, `farmhand_skill_capture_*` | Skill system — search, create, capture workflows |

Plus **resources** (platform configs, build configs, DAT files) and **prompts** (build_rom_collection, analyze_collection, recommend_games).

---

## Build Pipeline

ROM Farmer's declarative YAML build system processes ROMs through 21 stages:

| Phase | Stages | What happens |
|---|---|---|
| **Filter** | PreFilter, FilterDAT, Filter1G1R, FilterArcade | Narrow the source collection |
| **Select** | FilterRating, SelectionFilter, ApplyLists | Choose the best games within budget |
| **Cache** | CachePreCheck | Skip already-processed ROMs |
| **Extract** | ExtractArchive, ExtractPS3, UnzipRVZ, TransformPS3 | Unpack source formats |
| **Compress** | ConvertXISO, CompressSquashfs, CompressCHD, CompressArchive | Target format conversion |
| **Organize** | CreateM3U, CopyArcade, Organize | Structure output + multi-disc playlists |
| **Metadata** | GenerateMetadata | gamelist.xml + scraped media |
| **Hooks** | ApplyPS3Updates | Platform-specific post-processing |

Builds are configured via YAML composing platform recipes and target profiles:

```yaml
# config/builds/batocera-nuc.yaml
spec:
  name: batocera-nuc-build
  target: batocera
  platforms:
    saturn:
      recipe: saturn-redump-1g1r-chd
      budget_gb: 25
    psx:
      recipe: psx-redump-1g1r-chd
      budget_gb: 60
```

The system learns actual compression ratios from each build, improving budget predictions over time.

---

## Supported Platforms

30+ platforms including:

| Category | Platforms |
|---|---|
| **Nintendo** | NES, SNES, N64, GameCube, Wii, Game Boy, GBA, DS, 3DS, Virtual Boy |
| **Sony** | PSX, PS2, PS3, PSP |
| **Sega** | Master System, Genesis, Saturn, Dreamcast, Mega CD, Game Gear |
| **Other** | 3DO, PC Engine CD, Neo Geo, Atari (2600/5200/7800/Jaguar/Lynx) |
| **Arcade** | FBNeo, MAME, Naomi, Atomiswave, Model 2/3 |
| **Microsoft** | Xbox (XISO) |

---

## CLI Reference

While the AI agent is the primary operator, ROM Farmer has a full CLI for direct use:

```bash
# Build management
romfarmer build run --name <build>       # Run a build
romfarmer build status --name <build>    # Check progress
./build-wizard                           # Interactive build wizard

# DAT files
romfarmer dat import <dat-file>          # Import DAT file
romfarmer dat search <name> <query>      # Search games

# Collection
romfarmer scan directory <path>          # Scan ROMs
romfarmer metadata scrape <path>         # Scrape game metadata

# Farm-Hand
romfarmer farmhand connect <host>        # Connect to target
romfarmer farmhand scan --target <name>  # Scan remote device
romfarmer farmhand plan --target <name>  # Generate deployment plan
romfarmer farmhand deploy --target <name> # Deploy to target
romfarmer farmhand skill list            # Browse skills
```

---

## Project Stats

| Metric | Value |
|---|---|
| Source files | 161 Python modules |
| Lines of code | ~47,000 |
| Tests | 632 |
| MCP tools | 37 |
| Pipeline stages | 21 |
| Config files | 174 YAML |
| Bundled skills | 4 (with artifacts) |
| Supported platforms | 30+ |

---

## Requirements

- **Python 3.10+**
- **An MCP-compatible AI client** — VS Code Copilot, Claude Desktop, Cursor, Cline, Windsurf, or [any MCP client](https://modelcontextprotocol.io/clients)
- **Optional**: `chdman` (CHD), `7z` (archives), `dolphin-tool` (RVZ), `ps3dec` (PS3)
- **Optional**: `paramiko` for Farm-Hand SSH (`pip install 'romfarmer[farmhand]'`)

## Development

```bash
pip install -e ".[dev,farmhand]"    # Install with dev + farmhand deps
make test                            # Run full test suite (632 tests)
python3 -m pytest tests/ -v         # Verbose output
ruff check src/                     # Lint
```

## How It Compares

| | ROM Farmer | RomM | Igir |
|---|---|---|---|
| **Interface** | AI agent (MCP) | Web UI | CLI flags |
| **AI/MCP** | 37 tools + skill system | None | None |
| **Build pipeline** | 21 declarative stages | Manual | Copy/move/link |
| **Remote deploy** | SSH + budget planning | No | No |
| **Learning** | Skill capture + reuse | No | No |
| **Format transforms** | CHD, XISO, CSO, RVZ, SquashFS, 7z | No | Archive only |
| **Metadata** | ScreenScraper + Wikipedia | IGDB + MobyGames | No |

ROM Farmer is the first ROM management tool built for AI operation.

---

## License

MIT

## Acknowledgments

- **[No-Intro](https://no-intro.org)** and **[Redump](http://redump.org)** — ROM preservation DAT files
- **[Model Context Protocol](https://modelcontextprotocol.io)** — The universal AI tool interface
- **[Igir](https://github.com/smart-retro/igir)** — Inspiration for ROM management workflows
- **[OpenClaw](https://github.com/openclaw)** — Inspiration for the skill system format
- **[Voyager](https://voyager.minedojo.org)** — Inspiration for auto-capture skill libraries
