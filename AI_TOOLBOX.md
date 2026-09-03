# AI Toolbox — ROM Farmer

**Last Updated:** September 2026
**Purpose:** Concise, accurate reference for AI assistants. Deep context comes from Engram — call `session_start(project="rom-farmer")` first.

---

## What This Project Does

**ROM Farmer** (`romfarmer`) is a content-addressed build compiler for ROM collections:
- Matches ROMs against DAT files (No-Intro, Redump, Retool 1G1R)
- Selects games via pure planner passes (DAT dedup, 1G1R, region, rating, curated lists, cross-generation dedup, storage budget)
- Lowers each game into a transform chain (CHD, 7z/zip, RVZ, WUX, XISO→SquashFS, PS3, M3U) keyed by input hashes
- Executes only actions missing from the SQLite action cache; artifacts live once in a SHA-256 CAS and are hardlinked into output trees
- Emits frontend-specific trees + `gamelist.xml` for Batocera, RetroBat, ROCKNIX (target profiles are YAML)
- Deploys to devices over SSH (Farm-Hand) and exposes 41 MCP tools for agent operation

This handles **terabytes** of data across **~70 platforms**. Builds take hours. Be precise.

---

## Quick Commands

```bash
# Install (activate .venv first)
cd /path/to/rom-farmer && pip install -e ".[dev,farmhand]"

# Quality gates — identical to CI
make check                       # pytest + ruff + ruff format --check + import-linter + mypy --strict core
make test                        # 733 tests, hermetic (no ROMs/DATs/tools needed; real-tool tests skip if tools absent)
make lint-fix                    # auto-fix lint
romfarmer doctor [--determinism] # tool availability/versions; run each transform twice and compare bytes
romfarmer doctor --build <name>  # RESOLVE-only: every platform's source dirs, DAT, negotiated chain (run before long builds)

# Plan without touching disk (pure) — explains every pass's decisions
romfarmer plan run <build> --explain [--platform psx] [--test-sample N --seed S]   # <build> = name or YAML path

# Build
romfarmer build run --name <build> --dry-run          # print the Action DAG, write nothing
romfarmer build run --name <build>                    # resume is implicit: action cache skips done work
romfarmer build run --name <build> --target rocknix-r36s --storage-budget 512gb
romfarmer build list | status | clean --name <build>

# DATs / collection / metadata
romfarmer dat import <file.dat> | search | diff | clonelist-validate | generate
romfarmer scan directory <path>
romfarmer metadata import-arrm <gamelist.xml>
romfarmer cas --help ; romfarmer cache --help

# Farm-Hand
romfarmer farmhand connect <host> | scan | plan | deploy | status --target <name>
romfarmer farmhand skill list | show | search | cat
```

---

## Architecture (as of the July 2026 compiler refactor)

Five phases, each with one frozen input type and one frozen output type. Phases 1–3 never touch the filesystem.

```
RESOLVE   YAML configs                     → BuildManifest      config/, new_orchestrator.py
CATALOG   manifest + sources + DATs + DB    → Catalog (GameUnits) analysis/catalog_builder.py (+ file_digest_cache)
PLAN      catalog → passes → lowering       → BuildPlan (Actions) planner/passes/, planner/lowering/
EXECUTE   plan + CAS + action cache         → artifacts in CAS    engine/executor.py, engine/transforms/
EMIT      artifacts + TargetProfile         → output tree         targets/emitters/, targets/profiles/
```

The driver is `new_orchestrator.py` — `run_catalog / run_plan / run_execute / run_emit` are typed phase functions; the driver owns logging, state, and per-platform error policy. Phases raise; the driver is the only try/except.

### Source Layout
```
src/romfarmer/
├── ir/            # Frozen IR: Identity, GameUnit, Catalog, Action/ActionKey, BuildPlan, LayoutPlan, BuildManifest, tool_impl
├── analysis/      # CATALOG: CatalogBuilder, KnowledgeBase (DB reads), FileDigestCache
├── planner/       # PLAN: passes/ (pure), lowering/ (per-platform action chains), costmodel, negotiation
├── engine/        # EXECUTE: Executor, ActionCache (SQLite), ScratchDir, transforms/ (chdman, 7z, squashfs, xiso, rvz, wux, ps3, m3u)
├── targets/       # EMIT: TargetProfile loader, emitters (generic hardlink materializer, ES gamelist, extras)
├── new_orchestrator.py  # Driver composing the five phases
├── config/        # Pydantic models + loaders: builds, recipes, platforms, targets (frontend × device), tiers
├── cli/           # Click groups: build, plan, dat, scan, metadata, cas, cache, lists, farmhand, generation, scores, web, …
├── mcp/           # MCP server (server.py) + tool modules: collection, dat, clonelist, scraper, wiki, farmhand, farmhand_skills
├── farmhand/      # SSH deploy: models, ssh, analyzer, planner, deployer, skills/, optimizer/ (LangGraph + LLM critic)
├── metadata/      # romfarmer.db (SQLAlchemy), ARRM import, gamelist generation, external scores, wiki search
├── cas/           # ContentStore + TreeStore (blob/tree CAS)
├── cache/         # Legacy ROM cache manager (still used by `romfarmer cache`)
├── dat/ dat_parser/  # DAT import/filter (SQLAlchemy) and DAT XML parser/matcher/clonelist/generator
├── ai/            # Generation model + Haiku-driven curation/rescue lists (Copilot SDK)
└── mcp_server.py  # `python -m romfarmer.mcp_server` entry point
```

### Strictness tiers (enforced in CI)
- **Compiler core** `ir/ engine/ analysis/ planner/ targets/`: `mypy --strict` clean; import-linter forbids importing legacy modules (`config`, `cache`, `core`, `metadata`) from `ir` and `planner.passes`. Keep it that way.
- **Everything else**: ruff-clean and formatted, not yet strictly typed. Whole-package mypy has ~800 errors — a ratchet target, not a gate.

### Invariants (tests/test_invariants.py — do not break)
1. Second identical build executes **zero** transforms.
2. `run_plan` is deterministic for the same (manifest, catalog).
3. No output filename matches `^[0-9a-f]{64}` (no CAS hash leaks).
4. build(A∪B) outputs ≡ build(A) ∪ build(B) on disjoint fixtures.
5. No duplicate logical name / inode among top-level outputs.
6. gamelist emitted iff the target profile declares it.

### Frozen contracts
- **`ActionKey`** = `sha256(canonical JSON of (tool, tool_version, params: str→str, input sha256s))`. Never change the shape. To invalidate a tool's cache, bump its entry in `ir/tool_impl.py::IMPL_VERSIONS` (appends `+iN` to `tool_version`). Changing any transform default, subprocess flag, or `pinned_env()` **requires** that bump. All external tools run under `pinned_env()` (`LC_ALL=C TZ=UTC SOURCE_DATE_EPOCH=0`); 7z uses `-mtm=off -mmt=4`, mksquashfs `-all-root -no-xattrs -processors 4`.
- Transform registry (`new_orchestrator._build_default_transforms`) must contain every `Action.tool` lowering emits: `source-copy passthrough unzip compress-7z compress-zip chdman unzip-rvz unzip-wux extract-xiso mksquashfs ps3dec m3u-create`. `validate_plan` fails the platform at PLAN otherwise. Inputs are materialised under their declared `logical_name` (archive member names and chdman sniffing depend on it).
- Design record + rejected ideas: `docs/compiler-refactor/07-fable5-review.md` (Part III lists what NOT to build: ExecutionSupervisor, knapsack optimizers, GC, ontology dedup, key schema versions).

### Config
```
config/
├── builds/       # BuildSpec YAML: name, target, recipes[], output_base, post_build hooks
├── recipes/      # redump-chd, nointro-7z/zip/none, nintendo-disc-rvz, nintendo-wiiu-wux, xbox-xiso, ps3-jb, arcade-*, teknoparrot
├── platforms/    # ~70 platform definitions (DAT pattern, extensions, extraction type)
├── targets/      # batocera-pc, batocera-steamdeck, retrobat-pc, rocknix-r36s  (= frontends/ × devices/)
├── frontends/ devices/   # Composable halves of a target
├── curations/    # Curated lists, AI tiers, rescue lists
├── farmhand/     # targets/ (SSH creds, gitignored), profiles/, skills/ (user skills)
├── generations.yaml platform_tiers.yaml size_data.json sources.yaml dat_patterns.yaml
```

### Databases
- **`metadata/romfarmer.db`** — scraped games, transformations/telemetry, action_cache, artifact_aliases, file_digest_cache. WAL, `busy_timeout=30000`.
- **CAS** — `store/` (gitignored). Ingest is rename-into-CAS with unique tmp names; cache hits verify the blob exists (self-healing).

---

## Domain Knowledge

### Output Folder Convention
`{platform}-{source}-{filter}-{format}-{target}` — e.g., `saturn-redump-1g1r-eng-chd-batocera`

### Compression Ratios (priors; the CostModel learns actuals per build)
| Platform | Ratio | Notes |
|----------|-------|-------|
| Saturn/Sega CD | 0.62–0.65 | Excellent (binary + audio) |
| PSX | 0.70 | Good |
| PS2 | 0.75 | Decent |
| GameCube/Wii | 0.70–0.72 | Mini-DVDs |
| Xbox | 0.80 | XISO removes padding |
| PSP | 0.85 | Already compressed UMD |
| PS3 | 0.90 | Large Blu-rays |

### Multi-Disc Atomicity
A `GameUnit` owns all its discs. Selection operates on units; a failed disc fails the unit; M3U is a declared plan output.

### Budget policy
Greedy rating-descending first-fit. This is a *curation policy*, not a failed optimizer — do not replace with a knapsack. Executor stops launching units when actual bytes ≥ budget (`budget-stop`), converting over-runs into safe under-fills.

### Critical Gotchas
- `romfarmer plan run --explain` before any long build. Plans are cheap; builds are hours.
- `extract-xiso -r` destroys the source ISO in place — source hashes are computed before conversion.
- `core/paths.py` loads `.env` at import time. Tests that read env vars must `monkeypatch.delenv`.
- Ruff respects `.gitignore`; `.gitignore` rules must be anchored (`/cache/`, not `cache/`) or they hide source.
- `scripts/manual-checks/` are operator scripts that need live credentials — never move them back into `tests/`.

---

## Known Issues / Open Work
- Chains validated on real data via smoke builds (`config/builds/smoke-*.yaml`, outputs under `output/`): 7z (`smoke-nes-7z`, full set), CHD incl. multi-disc/M3U (`smoke-psx-chd`), arcade passthrough (`smoke-neogeo`, 445/445 parity with legacy), RVZ (`smoke-gamecube-rvz`), XISO (`smoke-xbox-xiso`, emits `.iso` like legacy), WUX (`smoke-wiiu-wux`). **Unvalidated:** XISO→SquashFS (batocera xbox), PS3. Run one with `--test-sample N --seed S --yes` before trusting a full build of that chain.
- CostModel telemetry reads legacy `rom_transformations`; compiler builds do not write it yet, so ratios come from `_HARDCODED_PRIORS` only (xbox/xbox360 priors were measured from the legacy library).
- CAS garbage collection is deferred by design (see 07 Q10).
- Two config loaders exist: `config/new_loader.py` (primary, used by the orchestrator) and `config/loader.py` (legacy; `cli/lists.py`, `mcp/collection.py`). Consolidation pending.
- `web/` (FastAPI) is scaffolding, not a shipped UI.
- Multi-file **passthrough** of CUE/BIN (`cue_bin` chain, no CHD) declares one output; only the cue is emitted. CHD chains are unaffected (chdman consumes the zip directly).
- `extract-xiso` is not covered by `doctor --determinism` (needs a real XISO fixture).

---

## Working With This Project

- **Verify-then-commit.** `make check` must pass before every commit. Commit per logical change.
- **Before proposing a feature**, check `romfarmer --help`, `docs/compiler-refactor/`, and Engram — much has been designed and deliberately rejected.
- **Adding a platform quirk** → a lowering rule in `planner/lowering/`, never a special case in the driver.
- **Adding a target device** → YAML in `config/devices/` + `config/targets/`; emitter code only for a new frontend dialect.
- **Adding a transform** → `engine/transforms/`, register in the orchestrator's tool table, add to `ir/tool_impl.py::IMPL_VERSIONS`, add a golden ActionKey test.
- **Fast iteration**: `--dry-run`, `--test-sample N --seed S`, single `--platform` in `plan run`. Smoke builds: `smoke-nes-7z` (cartridge/7z), `smoke-psx-chd` (disc/CHD) — outputs stay under `output/`.
- **Source paths**: platform YAMLs use `${ROMFARMER_SOURCE_ROOT}` (Myrient layout) and `${ROMFARMER_ARCHIVE_ROOT}`; set them in `.env`. Never hardcode a machine path in `config/`.
- Code conventions: type hints everywhere, Pydantic for config, frozen dataclasses in `ir/`, Rich for CLI output, `ruff format` (100 cols).
