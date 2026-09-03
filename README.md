# ROM Farmer

[![CI](https://github.com/alewman/rom-farmer/actions/workflows/ci.yml/badge.svg)](https://github.com/alewman/rom-farmer/actions/workflows/ci.yml)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

**A content-addressed build compiler for ROM collections, designed to be driven by an AI agent.**

You describe a collection — platforms, 1G1R rules, formats, a storage budget, a target device. ROM Farmer compiles that description into a deterministic plan, executes only the work that hasn't been done before, and emits a ready-to-play tree for Batocera, RetroBat, ROCKNIX, or any frontend you define.

```
You:        "Deploy PSX to my Batocera within 60 GB, prioritize RPGs"
Farm-Hand:  connects → scans target → plans budget → builds → deploys via SSH
```

> ROM Farmer exposes **41 [MCP](https://modelcontextprotocol.io) tools**. Any MCP client — VS Code Copilot, Claude Desktop, Cursor, Cline, Windsurf — can discover them and operate the whole system. A full CLI exists too; the agent is simply the primary operator.

---

## Why a compiler?

Every ROM manager today is a pipeline of steps that mutate files in place. ROM Farmer treats a collection as a *program* and a build as *compiling it for a target*:

- **The YAML is the source language.** Platforms, recipes, and target profiles compose declaratively.
- **The CAS is the object store.** Every artifact — extracted ROM, CHD, 7z, M3U — is stored once by SHA-256 and hardlinked into output trees. Build a second target and shared artifacts cost zero bytes.
- **SQLite is the action cache.** Each transform is keyed by `sha256(tool, tool_version, params, input hashes)`. Re-running a build re-derives the plan and skips every action already in the cache — resume is free, not a feature.
- **The plan is data.** `romfarmer plan run --explain` shows why every game was kept or dropped, pass by pass, before a single file is touched.

Five phases, each with one frozen input type and one frozen output type:

```
RESOLVE   YAML configs                         →  BuildManifest
CATALOG   manifest + sources + DATs + DB        →  Catalog        (GameUnits: multi-disc atomic, region, rating, generation)
PLAN      catalog → pure passes → lowering      →  BuildPlan      (Action DAG)
EXECUTE   plan + CAS + action cache             →  materialized artifacts in CAS
EMIT      artifacts + TargetProfile             →  output tree + gamelist.xml
```

Phases 1–3 never touch the filesystem. Only the executor and the emitter do.

| Concept | Lives in | What it is |
|---|---|---|
| **Pass** | `planner/passes/` | Pure `(Catalog, Manifest, CostModel) → Catalog`. DAT dedup, 1G1R, region, rating, curated lists, cross-generation dedup, budget knapsack. |
| **Lowering** | `planner/lowering/` | Per-platform rules that turn a `GameUnit` into an action chain: cartridge, disc, RVZ, WUX, XISO→SquashFS, PS3, arcade. |
| **Transform** | `engine/transforms/` | Cache-unaware tool adapters: `chdman`, `7z`, `mksquashfs`, `extract-xiso`, `dolphin-tool`, `ps3dec`, M3U. |
| **Emitter** | `targets/emitters/` | Hardlink materializer + frontend dialects (EmulationStation `gamelist.xml`, extras). |
| **TargetProfile** | `config/targets/*.yaml` | Declarative constraints: folder names, extensions, format preferences, media policy. Adding a device is YAML, not code. |

The compiler core (`ir/`, `engine/`, `planner/`, `analysis/`, `targets/`) is `mypy --strict` clean, guarded by import-linter contracts, and covered by invariant tests: *build twice ⇒ zero transforms run*; *plan is a pure function of (manifest, catalog)*; *no CAS hash ever leaks into an output filename*. External tools run under a pinned environment with reproducibility flags; `romfarmer doctor --determinism` runs each one twice and diffs the bytes, and CI does the same.

---

## Two AI layers

ROM Farmer separates **deterministic** work from **judgment** work, and keeps the boundary explicit.

### Farm-Hand — the operator (MCP)

The ChatOps layer that lets an agent run the system end to end:

- **SSH deployment** — connect to Batocera/ROCKNIX devices, analyze volumes, transfer with delta sync
- **Target analysis** — scan storage, capabilities, and existing collections remotely
- **Budget planning** — bin-pack platforms across volumes with tiered sizing
- **Skill system** — the agent captures completed workflows as reusable `SKILL.md` + `procedure.yaml` pairs, templatizes them, and replays them later. Bundled skills ship read-only; agent-created skills live in `config/farmhand/skills/` and shadow them by name.

### Budget optimizer — the critic (LangGraph, optional)

`pip install 'romfarmer[optimizer]'` adds an iterative loop: estimate a build's size → an LLM critic adjusts per-platform rating thresholds → re-estimate, until the build fits a target volume within tolerance. The stochastic part only ever produces *inputs* to the compiler; the plan itself stays deterministic and explainable.

---

## Quick start

### Install

```bash
git clone https://github.com/alewman/rom-farmer.git
cd rom-farmer
pip install -e ".[farmhand]"
romfarmer init          # scaffold config/, dats/, source/, output/
```

External tools are optional and only needed for the formats you use: `chdman` (CHD), `7z`, `mksquashfs`, `extract-xiso`, `dolphin-tool` (RVZ), `wit`/`wux`, `ps3dec`. See `install-tools.sh`.

### Connect an AI client

```json
{
  "mcpServers": {
    "romfarmer": {
      "command": "python3",
      "args": ["-m", "romfarmer.mcp_server"],
      "cwd": "/path/to/rom-farmer"
    }
  }
}
```

The agent reads `AI_TOOLBOX.md` for domain context and discovers the tools on its own.

```
"What platforms do I have in my collection?"
"Build a 1G1R English PSX set compressed to CHD"
"Connect to my Batocera at 10.10.20.183 and scan what's there"
"How much space would Saturn + Dreamcast + PSX take?"
"Deploy the top-rated PS2 games within 120 GB to my device"
```

### Or use the CLI

```bash
# Plan first — pure, no files touched
romfarmer plan run nointro-1g1r-eng-7z-retrobat --explain          # or a path to a build YAML

# Build (dry-run prints the action DAG; resume is implicit via the action cache)
romfarmer build run --name nointro-1g1r-eng-7z-retrobat --dry-run
romfarmer build run --name nointro-1g1r-eng-7z-retrobat --target rocknix-r36s --storage-budget 512gb

# DATs, collection, metadata
romfarmer dat import <file.dat>
romfarmer dat generate <source-dir> -n "Name" -r reference.dat -o out.dat
romfarmer scan directory <path>
romfarmer metadata import-arrm <gamelist.xml>

# Farm-Hand
romfarmer farmhand connect <host>
romfarmer farmhand scan --target <name>
romfarmer farmhand plan --target <name>
romfarmer farmhand deploy --target <name>
romfarmer farmhand skill list
```

---

## Configuration

A build composes **recipes** (how to process a family of platforms) with a **target** (where the output goes):

```yaml
# config/builds/nointro-1g1r-eng-7z-retrobat.yaml
name: nointro-1g1r-eng-7z-retrobat
target: retrobat-pc
recipes:
  - nointro-7z       # cartridge platforms → 7z
  - nointro-none     # platforms that need raw files (3DS, …)
output_base: /path/to/output/roms-retrobat

post_build:
  - name: genre-organization
    type: genre_organize
    options: { mode: hardlink, merge_small: 3 }
```

| Directory | Contents |
|---|---|
| `config/platforms/` | ~70 platform definitions (DAT patterns, extensions, disc/cart type) |
| `config/recipes/` | Processing recipes: `redump-chd`, `nointro-7z`, `nintendo-disc-rvz`, `xbox-xiso`, `ps3-jb`, `arcade-*`, … |
| `config/targets/` | Target profiles: `batocera-pc`, `batocera-steamdeck`, `retrobat-pc`, `rocknix-r36s` |
| `config/builds/` | Build specs that compose the above |
| `config/curations/` | Curated lists and AI-generated tiers/rescue lists |

The cost model learns real compression ratios from every build, so budget predictions improve over time.

---

## MCP tools (41)

| Category | Tools |
|---|---|
| **Collection** | `list_platforms`, `list_builds`, `get_build_status`, `get_platform_stats`, `query_collection`, `calculate_budget`, `get_compression_ratio` |
| **DAT files** | `dat_hardware_list`, `dat_hardware_games`, `dat_game_variants`, `dat_search` |
| **Clone lists** | `clonelist_diff`, `clonelist_validate`, `clonelist_patch`, `clonelist_metadata_generate` — Retool clone-list maintenance when DATs update |
| **Metadata** | `scraper_search`, `scraper_game_info`, `scraper_platforms`, `scraper_genres`, `scraper_top_rated` |
| **Wikipedia** | `wiki_search`, `wiki_game_info`, `wiki_get_section`, `wiki_stats`, `wiki_find_game` |
| **Farm-Hand** | `farmhand_connect`, `farmhand_scan_target`, `farmhand_analyze_fit`, `farmhand_generate_plan`, `farmhand_remote_exec`, `farmhand_get_target_info`, `farmhand_deploy_status` |
| **Skills** | `farmhand_skill_search`, `farmhand_skill_show`, `farmhand_skill_artifact`, `farmhand_skill_save`, `farmhand_skill_save_artifact`, `farmhand_skill_capture_start`, `farmhand_skill_capture_step`, `farmhand_skill_capture_finish`, `farmhand_skill_capture_cancel` |

Plus MCP resources (platform, build, and DAT configs) and prompts (`build_rom_collection`, `analyze_collection`, `recommend_games`).

---

## Supported platforms

| Family | Platforms |
|---|---|
| **Nintendo** | NES/FDS, SNES, N64, GameCube, Wii/WiiWare, Wii U, GB/GBC/GBA, DS, 3DS, Virtual Boy, Pokémon Mini |
| **Sony** | PSX, PS2, PS3 (JB folders + PSN updates), PSP, PSP Minis |
| **Sega** | SG-1000, Master System, Genesis, Mega CD, 32X, Saturn, Dreamcast, Game Gear |
| **Microsoft** | Xbox, Xbox 360 (XISO → SquashFS) |
| **Arcade** | MAME/HBMAME, FBNeo, Naomi/Naomi 2, Atomiswave, Model 2/3, Chihiro, Triforce, Lindbergh, Hikaru, Namco 246, TeknoParrot |
| **Other** | 3DO, PC Engine/SuperGrafx/CD, Neo Geo/CD/Pocket, WonderSwan, MSX, ColecoVision, Intellivision, Vectrex, Atari 2600/5200/7800/Jaguar/Lynx |

Sources follow No-Intro and Redump naming; Retool 1G1R DATs are supported directly.

---

## Project status

ROM Farmer is a working system that builds and deploys multi-terabyte collections daily, but it is a **single-maintainer project in active development**. What that means concretely:

- **Compiler core** (`ir`, `engine`, `planner`, `analysis`, `targets`): strict-typed, invariant-tested, stable contracts. `ActionKey` canonical form is frozen.
- **Validated end-to-end on real collections:** cartridge → 7z (full NES set), disc → CHD (single and multi-disc with M3U), arcade passthrough (Neo Geo: identical set to the previous pipeline), GameCube RVZ, Xbox XISO, Wii U WUX. **Not yet exercised through the compiler:** Xbox SquashFS (Batocera), PS3.
- **Operator layer** (`cli`, `mcp`, `farmhand`, `metadata`, `config`): broader, older, and less strictly typed. It works; it is being tightened incrementally.
- **Not yet done:** CAS garbage collection, a web UI, multi-file CUE/BIN passthrough (CHD is unaffected).
- Before a long build: `romfarmer doctor --build <name>` (seconds) then `romfarmer plan run <name> --explain`.
- Architecture decisions and their reasoning are recorded in [`docs/compiler-refactor/`](docs/compiler-refactor/), including what was considered and deliberately *not* built.

| | |
|---|---|
| Python modules | 180 (~45K lines) |
| Tests | 733 |
| MCP tools | 41 |
| Config | 144 YAML files |
| Platforms | ~70 definitions |

---

## Development

```bash
pip install -e ".[dev,farmhand]"
make check          # what CI runs: pytest, ruff, ruff format, import-linter, mypy --strict on the core
make test           # just the tests
make lint-fix       # auto-fix lint
```

Tests are hermetic — no ROMs, DATs, or external tools required. CI runs on Python 3.10, 3.12, and 3.13.

---

## How it compares

| | ROM Farmer | RomM | Igir |
|---|---|---|---|
| **Interface** | AI agent (MCP) + CLI | Web UI | CLI |
| **Model** | Content-addressed build compiler | Library manager | File copier/sorter |
| **Incremental** | Action cache keyed by input hashes | — | — |
| **Format transforms** | CHD, RVZ, XISO, SquashFS, 7z, WUX, PS3 | — | Archive only |
| **Storage budget** | Rating-priority knapsack + learned cost model | — | — |
| **Remote deploy** | SSH + multi-volume planning | — | — |
| **Metadata** | ScreenScraper, ARRM import, Wikipedia, MobyGames scores | IGDB, MobyGames | — |
| **Agent memory** | Skill capture + replay | — | — |

---

## License

MIT

## Acknowledgments

- **[No-Intro](https://no-intro.org)**, **[Redump](http://redump.org)**, and **[Retool](https://github.com/unexpectedpanda/retool)** — preservation DATs and 1G1R clone lists
- **[Model Context Protocol](https://modelcontextprotocol.io)** — the universal AI tool interface
- **[Bazel](https://bazel.build)** and **[Nix](https://nixos.org)** — the build-system ideas this borrows from, and the ones it deliberately doesn't
- **[Igir](https://github.com/smart-retro/igir)** — inspiration for ROM management workflows
- **[Voyager](https://voyager.minedojo.org)** — inspiration for auto-captured skill libraries
