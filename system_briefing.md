# ROM Farmer — Architectural Briefing Document

**Generated:** 2026-07-03 | **Codebase State:** post-Feb 2026 declarative refactor, plugin branch not yet merged to main

---

## 1. COMPONENT INVENTORY & RESPONSIBILITIES

### Entry Points & Orchestration

| Module | Path | Responsibility |
|--------|------|----------------|
| `__main__.py` | `src/romfarmer/__main__.py` | Click CLI root; entry point for `romfarmer` command |
| `NewBuildOrchestrator` | `src/romfarmer/new_orchestrator.py` | **Primary orchestrator.** Loads a `BuildSpec`, resolves it via `ConfigResolver`, drives per-platform pipeline execution, manages build state persistence (`state/.build_state_<name>.yaml`), budget tracking, and post-build hooks. ~400 lines replacing 1,738 lines of legacy code. |
| `build_orchestrator.py` | `src/romfarmer/build_orchestrator.py` | **Legacy orchestrator.** Still used for some older build configs. Retains imperative `platform_overrides` logic. Should be treated as dead code for new work. |
| `platform_processor.py` | `src/romfarmer/platform_processor.py` | **Legacy single-platform executor.** Replaced by `stages/builder.py` + `stages/pipeline.py`. Contains a known TODO: "Implement output verification". |
| `build_models.py` | `src/romfarmer/build_models.py` | `BuildState` and `BuildStatus` dataclasses for build resume capability. |
| `build_loader.py` | `src/romfarmer/build_loader.py` | Loads legacy `BuildConfig` YAML format (pre-refactor builds). |

### CLI Layer (`src/romfarmer/cli/`)

| Module | Responsibility |
|--------|----------------|
| `build.py` | `romfarmer build run/clean/list` — primary user-facing commands. Routes to `NewBuildOrchestrator` or legacy path. |
| `cache.py` | `romfarmer cache stats/clean/list` — inspect/manage ROM transformation cache. |
| `cas.py` | `romfarmer cas verify/stats` — CAS integrity inspection. |
| `dat.py` | `romfarmer dat list/info` — DAT file management. |
| `lists.py` | `romfarmer lists diff/validate` — curated list file management. |
| `plugin.py` | `romfarmer plugin list/contracts/graph` — plugin system introspection (branch feature). |
| `metadata_commands.py` | `romfarmer metadata scrape/import` — ARRM metadata import commands. |
| `organize.py` | `romfarmer organize` — standalone organize command. |
| `scores.py` | `romfarmer scores` — rating score inspection. |
| `generation.py` | `romfarmer generation` — cross-platform generation deduplication commands. |
| `scan.py` | `romfarmer scan` — source directory scanner. |
| `farmhand.py` | `romfarmer farmhand` — farmhand integration commands. |
| `banner.py` | Startup banner; lists all active features for user confirmation. |

### Configuration Layer (`src/romfarmer/config/`)

This is the **declarative heart** of the refactored system. Config is composed in layers:

| Module | Responsibility |
|--------|----------------|
| `build_spec.py` | `BuildSpec` — top-level YAML model. Declares `target`, `recipes[]`, optional `platforms[]`, `exclude[]`, `storage_budget`, and `output_base`. |
| `slim_platform.py` | `SlimPlatformConfig` — **intrinsic platform facts only**: source paths, DAT reference, extraction type, multi-disc, PS3/Xbox quirks. Explicitly excludes compression settings, output paths, and selection config (those are recipe/target concerns). |
| `recipe.py` | `RecipeSpec` — reusable pipeline recipe. Declares which platforms to include, plus overridable build choices (compression, selection, lists). |
| `resolver.py` | `ConfigResolver` — **composition engine**. Merges `SlimPlatformConfig` + stacked `RecipeSpec` entries + `ComposedTarget` constraints into a `ResolvedPlatformConfig`. Single platform, fully resolved, no further lookups. |
| `target.py` | `TargetConfig` + `ComposedTarget` — a target is a frontend+device pair. `ComposedTarget` is the runtime representation after loading both. Used for folder naming, compression preferences, media filtering, and platform support gating. |
| `frontend.py` | `FrontendConfig` — folder name mapping, per-platform extension support, preferred compression per platform, compression fallback rules, media types. Models Batocera, RocknIX, etc. |
| `device.py` | `DeviceConfig` — display resolution, media sizing constraints, `unsupported_platforms[]` list (CPU capability limits). Models R36S, Steam Deck, PC. |
| `models.py` | Core enums and Pydantic models: `CompressionFormat`, `ExtractionType`, `OrganizationStyle`, `SelectionStrategy`, `SelectionConfig`, `DATSource`, etc. |
| `loader.py` / `new_loader.py` | YAML loading for legacy and new config formats respectively. |
| `overrides.py` | Per-platform override merging logic. |
| `generation_loader.py` / `tiers_loader.py` | Load `config/generations.yaml` and `config/platform_tiers.yaml`. |
| `target_loader.py` | Composes frontend + device YAMLs into a `ComposedTarget`. |

**Config file tree (`config/`):**

```
config/
├── builds/       YAML: BuildSpec per named build (e.g., batocera-1tb.yaml)
├── platforms/    YAML: SlimPlatformConfig per platform (e.g., saturn.yaml)
├── recipes/      YAML: RecipeSpec — reusable pipeline choices
├── targets/      YAML: TargetConfig — frontend+device pairings
├── frontends/    YAML: FrontendConfig (batocera.yaml, rocknix.yaml, etc.)
├── devices/      YAML: DeviceConfig (r36s.yaml, steamdeck.yaml, pc.yaml)
├── selections/   YAML: Named SelectionConfig presets
├── scopes/       YAML: Legacy selection scopes (pre-refactor)
├── curations/    YAML: Curated game lists
├── dat_patterns.yaml   — DAT filename glob patterns
├── generations.yaml    — Cross-platform generation groupings + priorities
├── platform_tiers.yaml — Tier 1–5 classifications + strategy per tier
└── size_data.json      — Historical compression ratios (platform → ratio)
```

### Pipeline Stages (`src/romfarmer/stages/`)

All stages inherit `Stage(ABC)` and operate on a shared `StageContext` dataclass. Stages declare a `PHASE` (`PLAN`, `EXECUTE`, `FINALIZE`). The pipeline executor runs all `PLAN` stages on the full collection first, then runs `EXECUTE` stages per-game-group (capping peak disk usage), then runs `FINALIZE` stages on the aggregated result.

**`StageContext`** is the primary data transport:
- Domain objects: `FileSet` (source/matched/filtered/extracted/compressed/organized/m3u), `FileHashes` (source_md5, rom_md5), `DiscProcessing` (games, cue_sheets), `PreFilters`, `ProcessingStats`, `Transformation[]`
- Legacy flat fields: `source_files`, `matched_files`, `filtered_files`, `extracted_files`, `compressed_files`, `m3u_files` — all deprecated but still in active use. New domain objects exist but most stages still write the flat fields.

| Stage Class | File | Phase | Responsibility |
|-------------|------|-------|----------------|
| `PreFilterStage` | `pre_filter.py` | PLAN | Zero-I/O filename-only filter by letter, region tags, language tags. Runs before MD5 hashing to minimize I/O. |
| `FilterDATStage` | `filter_dat.py` | PLAN | MD5-match source ZIPs against Retool/No-Intro/Redump DAT entries. Creates symlinks in `work_dir`. Uses thread pool for parallel hashing. Loads MD5s from database first to avoid re-hashing. Fuzzy name fallback with difflib dedup. |
| `Filter1G1RStage` | `filter_1g1r.py` | PLAN | DAT-free 1G1R from filename parsing. Only runs when no DAT is present. |
| `FilterArcadeStage` | `filter_arcade.py` | PLAN | Arcade-specific filtering: parent/clone relationships, driver_status, region priority, working-only gate, optional hacks/bootlegs. |
| `FilterRatingStage` | `filter_rating.py` | PLAN | Filter by minimum rating threshold from metadata DB. |
| `SelectionFilter` | `filter_selection.py` | PLAN | **"Budget loop" selection.** 7 strategies (RATING_BUDGET, FIRST, LAST, RANDOM, SMALLEST, LARGEST, ALPHABETICAL). Multi-disc atomicity: always selects all discs of a game together. `RATING_BUDGET` queries `romfarmer.db` for ratings, uses historical or default compression ratios to predict output size, selects highest-rated games until budget exhausted. |
| `FilterGenerationStage` | `filter_generation.py` | PLAN | Cross-platform "1G1Gen" deduplication. Normalizes game names, keeps game on highest-priority platform in generation, removes from lower-priority. Respects rescue lists and auto-rescues curated `_Best-Games` subdirectory contents. |
| `ApplyListsStage` | `apply_lists.py` | PLAN | Applies curated list files: `{platform}-delete` removes ROMs, `{platform}+{name}` adds from Myrient as subdirectory, `{platform}.{name}` adds from extra sources. Also gates on `tier_strategy`: if `best_of`, filters to `{platform}+Best-Games` list. |
| `CachePreCheckStage` | `cache_precheck.py` | EXECUTE | **CAS fast path.** Reads ZIP central directory headers (no extraction) to get CRC32+size identity. Looks up in `CacheManager` by ZIP identity. Cache hit → hardlinks CHD/RVZ/etc. from CAS to output, removes from processing queue. Cache miss → passes through. |
| `ExtractArchiveStage` | `extract.py` | EXECUTE | Extracts ZIP archives. DISC mode: extracts CUE/BIN or ISO, groups multi-disc by base name. CARTRIDGE mode: extracts ROM files, calculates ROM MD5 for metadata lookup. |
| `ExtractPS3Stage` | `extract_ps3.py` | EXECUTE | Unzips PS3 ISO from Myrient archive. |
| `UnzipRVZStage` | `unzip_rvz.py` | EXECUTE | Extracts `.rvz` from ZIP archives. No conversion — RVZ is Dolphin native format. |
| `UnzipWUXStage` | `unzip_wux.py` | EXECUTE | Extracts `.wux` from ZIP archives. No conversion — WUX is Cemu native format. |
| `TransformPS3Stage` | `transform_ps3.py` | EXECUTE | Full PS3 decryption pipeline: unzip encrypted ISO → find `.dkey` file → PS3Dec decrypt → output as folder (JB), ISO, or ISO.gz. Uses `TreeStore` (CAS extension) for folder deduplication. |
| `ConvertXISOStage` | `convert_xiso.py` | EXECUTE | Converts Redump full-disc Xbox ISOs to XISO format (game partition only) via `extract-xiso -r`. CAS-backed: skips if hash already cached. |
| `CompressCHDStage` | `compress.py` | EXECUTE | Calls `chdman createcd`/`createdvd` to produce CHD. CAS-backed: checks by source MD5 before invoking chdman. Records transformation in DB. |
| `CompressArchiveStage` | `compress_archive.py` | EXECUTE | Recompresses extracted ROMs to 7z or ZIP using LZMA2. Standard timestamp `1996-12-24 23:32:00` for reproducible builds. CAS-backed. |
| `CompressSquashFSStage` | *(referenced in models)* | EXECUTE | SquashFS compression for Xbox/Batocera. |
| `CacheStoreStage` | `cache_store.py` | EXECUTE | After extraction (no-transform path: RVZ, raw ROMs), ingests files into CAS and replaces work-dir copies with hardlinks. Counterpart to `CachePreCheckStage`. |
| `CASIngestStage` | `cas_ingest.py` | PLAN | For platforms with `ExtractionType.NONE` (WADs, pre-compiled ISOs), ingests source files directly into CAS. Used to make multi-frontend builds zero-copy. |
| `CreateM3UStage` | `m3u.py` | FINALIZE | Groups CHDs by base name, creates `.m3u` playlist files for multi-disc games. Single-disc games get metadata but no M3U. |
| `CopyArcadeStage` | `copy_arcade.py` | FINALIZE | Copies arcade ROM sets (which don't go through the extract/compress pipeline) to output. |
| `OrganizeStage` | `organize.py` | FINALIZE | **Target-specific file placement.** Four `OrganizationStyle` modes: `FLAT` (all files in one dir), `BALANCED` (alphabetical groups, RocknIX), `MINIMAL` (sort2folders with max 50 files/group, Everdrive), `RICH` (deep subdirs, Batocera). Uses hardlink-then-delete for zero-copy moves on same filesystem. |
| `GenerateMetadataStage` | `metadata.py` | FINALIZE | Produces `gamelist.xml` for EmulationStation. Queries `romfarmer.db` by MD5/CRC32 for scraped metadata. M3U games: M3U is visible, individual CHDs are hidden. Supports device-specific video transcode and image downscale. PS3 JB folder detection via `PS3_GAME/PARAM.SFO` sentinel. |
| `ApplyPS3UpdatesStage` | `apply_ps3_updates.py` | FINALIZE | Applies PS3 updates/DLC from NoPayStation PKG archive. Queries Sony PSN live API for update manifests. **Known bug**: sometimes returns `StageResult` instead of `StageContext`. |
| `EmitExtrasStage` | `emit_extras.py` | FINALIZE | Sorts DLC/update WADs/PKGs into destination subdirs, emits per-frontend install scripts from templates. Used for Wii NAND content, PS3 DLC. |

**Pipeline builder (`stages/builder.py`):** Lookup table mapping `ExtractionType` → ordered list of stage factory functions. Replaces the 200-line if/elif chain in the legacy `PlatformProcessor`. Current pipelines: `_cartridge_stages`, `_disc_stages`, `_rvz_stages`, `_wux_stages`, `_ps3_stages`, `_xiso_stages`, `_arcade_stages`, `_no_extraction_stages`.

### Content-Addressable Storage (`src/romfarmer/cas/`)

> **CAS is where "build once, link everywhere" lives.**

| Module | Responsibility |
|--------|----------------|
| `store.py` | `ContentStore` — SHA-256 hashed blob store. Layout: `store/{hash[:2]}/{hash[2:]}.{ext}`. Atomic temp+rename writes. `put_hardlink()` for zero-copy on same ZFS pool. 256-bucket prefix sharding. |
| `tree.py` | `TreeStore` + `TreeManifest` + `TreeEntry` — extends CAS to folder-based outputs (PS3 JB, ScummVM, Daphne, etc.). Manifest is a sorted JSON of `{path, sha256, size}` entries; its own SHA-256 is the tree hash. Enables full deduplication of shared files across folder outputs. |
| `migrate.py` | CAS migration utilities (schema/layout changes). |
| `relink.py` | Re-establishes hardlinks from CAS after filesystem changes. |

### ROM Cache Layer (`src/romfarmer/cache/`)

> **Cache is the transformation-keyed index on top of CAS.**

| Module | Responsibility |
|--------|----------------|
| `manager.py` | `CacheManager` — SQLite-backed index of `(source_md5, format, params_hash) → cache_path`. Two lookup methods: by source MD5 (post-extraction) and by ZIP identity `(CRC32, content_size)` (pre-extraction). `link_to()` hardlinks cached file to output path. `store()` calls `ContentStore.put_hardlink()` then records entry in DB. |
| `models.py` | `ROMCache` SQLAlchemy model (per-file cache entries). `TreeCache` model (per-folder tree entries). |
| `config.py` | `CacheConfig` — enabled flag, `cache_dir`, `CacheLinkMode` (hardlink/copy/symlink), `CacheVerifyLevel`. Loaded from env vars. `CacheResult` dataclass (hit, cache_path, entry, message). |

### Metadata Layer (`src/romfarmer/metadata/`)

| Module | Responsibility |
|--------|----------------|
| `database.py` | SQLAlchemy models: `ScrapedGame` (metadata + md5/crc32/sha1 index), `MediaFile` (CAS-stored images/videos), `GameMediaLink`, `ROMTransformation`. Single unified `romfarmer.db`. |
| `transformation.py` | `ROMTransformation` model — records source hash, tool, version, params, output hash, timing. Powers the "learn actual compression ratios" loop. |
| `transformation_recorder.py` | `TransformationRecorder` — context manager wrapping transformation recording. Calls `SmartHashCapture` to get source hashes from DAT or by calculation. |
| `hash_capture.py` | `SmartHashCapture` — tries DAT first for source hashes, falls back to computing MD5/CRC32/SHA1 directly. Caches computed hashes in DB. |
| `dat_manager.py` | Wrapper around DAT file access for metadata context. |
| `generator.py` | `gamelist.xml` generation logic (also called from `GenerateMetadataStage`). |
| `arrm.py` | ARRM metadata importer — reads ARRM-generated `gamelist.xml` files and imports scraped data into `romfarmer.db`. |
| `external_scores.py` | Imports external rating scores (Letterboxd, OpenCritic, etc.) into DB. |
| `graph_db.py` | Graph database layer for game relationships. |
| `wiki_search.py` | Wikipedia/wiki search for game descriptions. |

### DAT Layer (`src/romfarmer/dat/`, `src/romfarmer/dat_parser/`)

| Module | Responsibility |
|--------|----------------|
| `dat_parser/` | `RetoolDATParser` — parses Logiqx XML DAT format. `DATFile` and `DATGame` models. `ROMMatcher` — MD5-based and fuzzy-name-based matching. |
| `dat/filter.py` | `OneGameOneRomFilter` — filename-based 1G1R without a DAT. Parses region/language/revision tags from No-Intro filename conventions. |
| `dat/importer.py` | DAT file import utilities. |

### Plugin System (`src/romfarmer/plugins/`) — *unmerged branch*

| Module | Responsibility |
|--------|----------------|
| `protocol.py` | `Plugin` Protocol (structural typing, not ABC). `PluginMeta` (name, version, capability, requires/provides frozensets, priority, platforms). `PluginCapability` enum (SCAN/FILTER/SELECT/EXTRACT/COMPRESS/ORGANIZE/METADATA/CACHE/VALIDATE/HOOK). |
| `events.py` | `EventBus` — synchronous, priority-ordered, wildcard-matching event dispatch. |
| `registry.py` | `PluginRegistry` — discovers, validates, and stores plugins. |
| `adapter.py` | `StageAdapter` — wraps all 21 legacy `Stage` subclasses into `Plugin` protocol with zero code changes. 9 no-arg stages auto-register; 12 need constructor config. |
| `catalog.py` | Introspects plugins for `contracts` (I/O table) and `graph` (data flow). |
| `builder.py` | Assembles plugin pipelines respecting capability phase order and `requires`/`provides` dependencies. |
| `pipeline.py` | Plugin-based pipeline executor. |

### Utilities

| Module | Responsibility |
|--------|----------------|
| `utils/storage_budget.py` | `BudgetTracker` — tracks accumulated output size per platform against a global budget. `compute_storage_budget()` parses human-readable budget strings ("1.5TB"). |
| `utils/output_naming.py` | `apply_output_naming()` — generates descriptive output directory names: `{platform}-{source}-{filter}-{format}-{target}`. |
| `cross_platform/game_normalizer.py` | `GameNameNormalizer` — normalizes game titles for cross-platform matching (strips `(Disc N)`, region tags, punctuation, common subtitle patterns). |
| `core/paths.py` | `PathResolver` / `get_paths()` — single source of truth for all workspace-relative paths. Avoids hardcoded path strings scattered across modules. |
| `core/hashing.py` | `calculate_md5()` utility. |
| `parsers/` | No-Intro/Redump filename parser — extracts region, language, revision, demo flags from parenthetical tags. |
| `arcade/classifier.py` | `ArcadeClassifier` — classifies arcade ROMs into parent/clone/bootleg/hack/prototype. |
| `arcade/filter.py` | `ArcadeFilter` — applies classification to build a filtered game set. |
| `scanner/` | Source directory scanner (for `romfarmer scan`). |
| `catalog/` | `DatGame` model used by Filter1G1RStage. |
| `web/` | HTTP utilities for metadata scraping. |
| `farmhand/` | Farmhand integration (curated list management assistant). |
| `mcp/` | MCP server tools exposing collection/dat/scraper/wiki to AI assistants. |
| `ai/` | AI-specific utilities. |

### Configuration Files (non-YAML)

| File | Responsibility |
|------|----------------|
| `config/dat_patterns.yaml` | Glob patterns for auto-detecting DAT files from source type enum. |
| `config/generations.yaml` | Console generation groupings (gen5, gen6, gen7) with platform priority lists for 1G1Gen dedup. |
| `config/platform_tiers.yaml` | Tier 1–5 platform classifications. Tier 1 = tiny essentials (always include), Tier 5 = massive/PC-only (skip unless budget allows). Per-tier strategy: `always_include`, `best_of`, `best_of_extended`, `skip`. |
| `config/size_data.json` | Historical or estimated compressed sizes per platform, used for budget pre-planning. |
| `lists/` | Curated text files: `{platform}-delete`, `{platform}+Best-Games`, `{platform}+{Collection}`, etc. |
| `dats/` | DAT files organized by source and filter level: `nointro.retool.1g1r.eng/`, `redump.retool.1g1r.eng/`, `dats/fbneo/`, etc. |
| `templates/` | Install script templates for extras platforms (Wii NAND install, PS3 DLC install). |
| `tools/bin/` | Compiled binaries: `chdman`, `extract-xiso`, `ps3dec`, `pkg2zip`. |

---

## 2. DATA MUTATION & WORKFLOW PIPELINE

### Canonical ROM Journey: PlayStation 1 disc game → Batocera on Steam Deck

**Source state:** `Crash Bandicoot (USA).zip` (containing `Crash Bandicoot (USA).cue` + 2 × `.bin`) in `/source/psx/`.

---

#### Phase 0 — Orchestration Setup

1. `romfarmer build run --name batocera-steamdeck` invokes `NewBuildOrchestrator.from_config("batocera-steamdeck")`.
2. Orchestrator loads `config/builds/batocera-steamdeck.yaml` → `BuildSpec` (target: `batocera-steamdeck`, recipes: `[redump-disc-eng, batocera-metadata]`, storage_budget: `2TB`).
3. `ConfigResolver.resolve()` loads `SlimPlatformConfig` for `psx`, stacks recipes, applies `ComposedTarget(batocera + steamdeck)` constraints → `ResolvedPlatformConfig(platform="psx", extraction_type=DISC, compression=CHD, multi_disc=True, folder_name="psx", ...)`.
4. `BudgetTracker` initialized with 2 TB limit. `CacheManager` opened against `metadata/database/romfarmer.db`.
5. `build_pipeline(resolved)` called → returns a `Pipeline` with stages assembled by `_disc_stages()`: `[CachePreCheckStage(chd), ExtractArchiveStage, CompressCHDStage, CreateM3UStage]` prepended with PLAN stages.

---

#### Phase 1 — PLAN Stages (full collection, no heavy I/O)

**Stage 1: `PreFilterStage`** *(PLAN)*

- Input: 8,000 PSX ZIP filenames scanned from `/source/psx/`.
- Action: Strip files not matching configured region (`USA`, `World`, `En`). No file I/O — pure filename string matching against `(USA)`, `(World)`, `(En)`, etc.
- Output: `context.source_files` reduced to ~2,000 ZIP paths.
- State change: `StageContext.source_files` list mutated in place.

**Stage 2: `FilterDATStage`** *(PLAN)*

- Input: ~2,000 ZIP paths.
- Action:
  1. Load MD5 hashes from `romfarmer.db` `scraped_games` table for known filenames (avoids re-hashing already-seen files).
  2. Compute MD5 for remaining ZIPs using thread pool (parallel hashing).
  3. Each MD5 looked up in `RetoolDATParser`-parsed DAT file (loaded from `dats/redump.retool.1g1r.eng/`).
  4. Match: `ROMMatcher.match(zip_md5)` → `DATGame` with canonical name, size, region.
  5. Fuzzy-name fallback if no hash match.
  6. `_dedup_by_dat_entry()` ensures at most one source ZIP per DAT game (exact stem match wins over similarity score).
  7. Matched ZIPs symlinked into `work_dir/psx-tmp/`.
- Output: `context.matched_files` = list of symlinks to matched ZIPs. Unmatched files reported but not fatal.
- DB write: New MD5s stored in `scraped_games.md5` for future cache lookup.

**Stage 3: `SelectionFilter`** *(PLAN, strategy=RATING_BUDGET)*

- Input: `context.filtered_files` (falls back to `matched_files`) — ~1,900 game ZIPs.
- Action:
  1. `_group_multi_disc_games()`: regex `\(Disc \d+\)` groups multi-disc games into atomic units (e.g., `Final Fantasy VII` → 3 disc files in one group).
  2. Query `romfarmer.db` `scraped_games` for `(system='psx', md5=...)` → rating float per game.
  3. `_get_compression_ratio()`: queries `ROMTransformation` table for `AVG(output_size/input_size) WHERE platform='psx' AND output_format='chd' AND sample_count>=5`. Falls back to `DEFAULT_COMPRESSION_RATIOS["psx"] = 0.70`.
  4. Adjusts budget: `adjusted_source_budget = max_size_gb / compression_ratio * 0.95`. E.g., 100 GB output target → 100/0.70*0.95 = ~136 GB source budget.
  5. Sorts game groups by rating descending. Iterates, accumulating `source_size`. Stops when budget exhausted.
  6. Multi-disc atomicity: all discs of a group are selected or none.
  7. Unselected ZIP symlinks deleted from `work_dir`.
- Output: `context.filtered_files` reduced to selected subset.
- **This is the "budget loop."** The ratio learning is the mechanism by which actual historical build data feeds future selection accuracy.

**Stage 4: `ApplyListsStage`** *(PLAN)*

- Input: `context.filtered_files`.
- Action:
  1. Load `lists/psx-delete` → remove any listed titles.
  2. Load `lists/psx+PlayStation-Classics` (if present) → add those ZIPs from source to `context.organized_files["PlayStation-Classics"]` subdirectory.
  3. Load `lists/psx.Translated` (if present) → copy from extra source dir into `_Translated/` subdirectory.
  4. If `tier_strategy == "best_of"`: pre-filter main collection to titles in `lists/psx+Best-Games` before the delete step.
- Output: `context.filtered_files` (main set), `context.organized_files` (subdirectory map).

---

#### Phase 2 — EXECUTE Stages (per-game-group loop)

For each game group (single game or multi-disc set), a sub-context is created and the EXECUTE stages run. `work_dir` holds only the current game's files at any moment — caps peak disk use.

**Stage 5: `CachePreCheckStage`** *(EXECUTE)*

- Input: ZIP file(s) for this game group.
- Action:
  1. Opens ZIP central directory (no extraction) to read `(CRC32, uncompressed_size, internal_filename)` of the largest file (or the `.cue` file for disc games).
  2. Calls `CacheManager.get_by_zip_identity(zip_crc32, zip_content_size, format="chd", params={"format":"chd","compression":"lzma"})`.
  3. DB query: `SELECT cache_path FROM rom_cache WHERE zip_crc32=? AND zip_content_size=? AND format=? AND params_hash=?`.
  4. If hit: `cache_manager.link_to(cache_path, work_dir/Game.chd)` — atomic hardlink from CAS blob.
  5. Hit: remove this ZIP from `filtered_files`, add CHD path to `context.cached_outputs`.
  6. Miss: leave ZIP in `filtered_files`.
- This stage can reduce extraction+compression work to zero for repeat builds.

**Stage 6: `ExtractArchiveStage`** *(EXECUTE)* — only if cache miss

- Input: ZIP files remaining in `filtered_files`.
- Action:
  1. Opens ZIP, finds `.cue` file and all referenced `.bin` files.
  2. Extracts to `work_dir/psx-tmp/GameTitle/`, preserving CUE/BIN structure.
  3. Groups disc files by base name (regex `\(Disc \d+\)` stripped) for multi-disc detection.
  4. Creates `IsoDisc` or `CueSheet` objects encoding the disc structure.
  5. Sets standard extraction timestamp: `1996-12-24 23:32:00` UTC (reproducible builds).
- Output: `context.extracted_files` = list of `.cue` paths (each pointing at its `.bin` siblings).

**Stage 7: `CompressCHDStage`** *(EXECUTE)* — only if cache miss

- Input: `context.extracted_files` (CUE paths), plus any pre-cached CHDs in `context.cached_outputs`.
- Action:
  1. For each CUE: `_calculate_source_md5()` — MD5 of the largest BIN file (matching ARRM convention).
  2. Check `CacheManager.get(source_md5, format="chd", params={"format":"chd","compression":"lzma"})` — secondary cache check by MD5 (in case ZIP identity wasn't available).
  3. If miss: invoke `chdman createcd -i {cue} -o {game}.chd`. Blocks until complete.
  4. `TransformationRecorder.record_transformation(source_file, system="psx", tool="chdman", ...)` context manager:
     - Captures source hashes before compression.
     - After `chdman` completes: `transform.set_final_file(game.chd)` → computes CHD MD5.
     - Saves `ROMTransformation` row to DB: `(source_md5, source_size, output_md5, output_size, tool, version, duration_s)`.
  5. `CacheManager.store(source_md5, cache_params, built_file=game.chd)` → hardlinks CHD into `CAS/{hash[:2]}/{hash[2:]}.chd`, writes `ROMCache` DB row keyed by MD5 AND by `(zip_crc32, zip_content_size)`.
  6. Delete extracted CUE/BIN files from `work_dir`.
- Output: `context.compressed_files` = CHD paths in `work_dir`.
- **DB writes:** `ROMTransformation` row (source→output mapping), `ROMCache` row (MD5→CAS path + ZIP identity→CAS path). The `ROMTransformation` rows are what the selection loop reads for future compression ratio calculations.

**Stage 8: `CreateM3UStage`** *(FINALIZE)*

- Input: `context.compressed_files` (CHD files).
- Action:
  1. Groups CHDs by base name (strips `(Disc N)` suffix).
  2. Multi-disc game: creates `GameTitle.m3u` listing all disc CHDs (relative paths).
  3. Populates `context.disc_metadata[base_name]` = `DiscMetadata(discs, m3u_path)` for metadata stage.
  4. Single-disc game: creates `DiscMetadata` with `m3u_file=None`.
- Output: `context.m3u_files` = list of `.m3u` paths. `context.disc_metadata` dict.

---

#### Phase 3 — FINALIZE Stages

**Stage 9: `OrganizeStage`** *(FINALIZE)*

- Input: `context.compressed_files` (CHDs + M3Us), `context.organized_files` (subdirectory map from ApplyLists).
- Action (RICH style for Batocera):
  1. Creates `output/psx-redump-1g1r-eng-chd-batocera/` directory.
  2. For each CHD/M3U: `_link_or_copy(src, dest)` — tries `os.link()` (hardlink, zero-copy); falls back to `shutil.copy2()` for cross-filesystem.
  3. For subdirectories: creates `output/.../psx-redump.../PlayStation-Classics/` and links files there.
- Output: Files in `output/` directory. `work_dir` is cleaned up by orchestrator after this stage.

**Stage 10: `GenerateMetadataStage`** *(FINALIZE)*

- Input: Scans `context.output_dir` for CHD/M3U/ISO/etc. files (depth 1 only to avoid duplicate subdirectory entries).
- Action:
  1. Iterates output files.
  2. For each: `_get_game_metadata(context, file_path)` → queries `romfarmer.db` for `ScrapedGame` by MD5/CRC32. Falls back to fuzzy name match.
  3. For M3U files: uses first-disc metadata (title, image, description, rating).
  4. For CHD files pointed to by M3U: adds them as `hidden=true` entries so EmulationStation doesn't show duplicates.
  5. Media files: `MediaFile` records in DB point to CAS paths. Rehydrated by hardlinking from CAS to `output/.../media/image/GameTitle.png`.
  6. Device-specific downscale: if `DeviceConfig.media_sizing.max_image_width < scraped_image_width`, transcodes via image converter.
  7. Writes `output/.../gamelist.xml`.
- Output: `gamelist.xml` + `media/` directory populated.

---

#### Post-Build

- `BudgetTracker.record_actual(platform, output_size_bytes)` — updates running total.
- `shutil.rmtree(work_dir)` — temp files cleaned.
- `BuildState` updated: `psx` added to `completed_platforms`, saved to `state/.build_state_batocera-steamdeck.yaml`.
- If jdupes post-hook configured: `jdupes -r -L output/` to hardlink any remaining identical files.
- If rsync deployment configured: `rsync -avz output/ target:/roms/`.

---

### Format Routing by ExtractionType

| ExtractionType | Pipeline Sequence | Output Format |
|---------------|-------------------|---------------|
| `DISC` + CHD | `CachePreCheck` → `Extract` → `CompressCHD` → `CreateM3U` | `.chd` + `.m3u` |
| `DISC` (no compress) | `CachePreCheck` → `Extract` → `CacheStore` | `.cue` + `.bin` or `.iso` |
| `CARTRIDGE` + 7z/zip | `CachePreCheck` → `Extract` → `CompressArchive` | `.7z` or `.zip` |
| `CARTRIDGE` (no compress) | `CachePreCheck` → `Extract` → `CacheStore` | raw ROM (`.nes`, `.gba`, etc.) |
| `RVZ` | `CachePreCheck` → `UnzipRVZ` → `CacheStore` | `.rvz` |
| `WUX` | `CachePreCheck` → `UnzipWUX` → `CacheStore` | `.wux` |
| `XISO` | `CachePreCheck` → `Extract` → `ConvertXISO` → `CompressSquashFS`? | `.iso` (XISO) |
| `PS3` | `ExtractPS3` → `TransformPS3` (decrypt → JB folder) → `ApplyPS3Updates` | `GameTitle.ps3/` folder |
| `NONE` | `CASIngest` → `EmitExtras` (or `Organize`) | source file as-is |

---

### Batocera vs. RocknIX vs. Everdrive Handling

The same source files and compression go through identical PLAN + EXECUTE stages. Target differences are applied **only in FINALIZE**:

| Axis | Batocera | RocknIX | Everdrive |
|------|----------|---------|-----------|
| `OrganizationStyle` | `RICH` (deep subdirs, media alongside ROMs) | `BALANCED` (alphabetical A-E, F-M groups) | `MINIMAL` (sort2folders, ≤50 files/group) |
| Compression | CHD for discs, 7z for carts (frontend config) | Same as Batocera (same emulators) | `NONE` — real hardware reads uncompressed ROMs |
| Metadata | `gamelist.xml` + full media scrape | `gamelist.xml` + reduced media | No metadata — Everdrive reads raw filenames |
| Folder names | `psx`, `snes`, `megadrive` | Frontend-specific via `folder_mapping` | Flat directory, no subdirs |
| Device filter | Steam Deck: PS3/PS2 supported | R36S: PS2/PS3/GameCube in `unsupported_platforms` | N/A — not a frontend device config |

The `OrganizeStage.execute()` reads `target_config.organization.style` (resolved from `ComposedTarget → FrontendConfig → FrontendDefaults.organization`) to select the correct layout algorithm. Everdrive's `MINIMAL` style is the only branch with explicit file-count capping (`max_files_per_group=50` from target YAML).

---

## 3. COUPLING & LEAKY ABSTRACTIONS

### 3.1 `StageContext` — the "god object"

`StageContext` is a flat `@dataclass` with ~30 fields. The Feb 2026 refactor added structured domain objects (`FileSet`, `FileHashes`, `DiscProcessing`, `PreFilters`) but **all 21 stages still read and write the legacy flat fields** (`source_files`, `matched_files`, `filtered_files`, `extracted_files`, `compressed_files`, etc.). The domain objects exist but are not used. Both sets of fields are in-flight simultaneously with `__post_init__` syncing only `pre_filters` from the legacy letter/region/language fields. Every new stage added to the system must now reason about two parallel schemas and decide which one to use.

**Specific symptom:** `GenerateMetadataStage` reads both `context.disc_metadata` (legacy) and constructs its own file scan from `context.output_dir.rglob(pattern)`, coupling metadata generation to filesystem state rather than to the in-memory `FileSet.organized` domain object.

### 3.2 Platform-Specific Logic Scattered Across Stages

**PS3 special-casing leaks throughout the system:**
- `ApplyPS3UpdatesStage` exists as a `FINALIZE` stage but the detection of whether to invoke it is encoded in the stage itself, not in the resolver. The resolver emits a `PS3Config` on `ResolvedPlatformConfig`, but `ApplyPS3UpdatesStage` is only added to the pipeline in `_ps3_stages()` — correct. However, `TransformPS3Stage` hardcodes `target_format = "folder"`, ignoring any target-level preference for ISO or ISO.gz output. The per-target format choice is not plumbed from `ResolvedPlatformConfig` into the stage.
- `ApplyPS3UpdatesStage` sometimes returns `StageResult` instead of `StageContext` (documented known bug). This is a type error that silently corrupts pipeline continuation.
- `ps3_utils.py` (`SonyPSNClient`, `NoPayStationDatabase`) live inside `stages/`, coupling PSN API calls to the stage execution layer instead of living in a dedicated `ps3/` domain module.

**Xbox special-casing:**
- `ConvertXISOStage` exists as a proper stage. However, the decision to apply SquashFS compression **after** XISO conversion is not reflected in the `ResolvedPlatformConfig.compression` chain: an Xbox build requires `ExtractionType.XISO` then `CompressionFormat.SQUASHFS`, and `_xiso_stages()` in the builder must manually chain these. The resolver does not produce a single `compression` value that correctly models this two-step Xbox path.

**Arcade detection leaks:**
- `FilterArcadeStage.should_skip()` checks `getattr(context.config, 'type', None) != 'arcade'` using `context.config` (the old `PlatformConfig`), not `context.platform_config` or `ResolvedPlatformConfig.is_arcade`. There are two `config` attributes in the context from different eras.
- Driver-based MAME filtering (`filter_driver`, `filter_romof` on `DATReference`) is intrinsic platform data, but the filtering itself is implemented in `FilterArcadeStage.execute()` by iterating `dat.games` and checking `game.sourcefile` — mixing the "what driver does this MAME game belong to" lookup directly into the filter stage rather than having the DAT loader pre-filter by driver.

### 3.3 Heuristic Compression Ratio Logic

`SelectionFilter._get_compression_ratio()` and `_select_by_rating_budget()` encode a `DEFAULT_COMPRESSION_RATIOS` dict of 14 platform→float mappings. These are described as "conservative/intentionally pessimistic." The fallback logic is:
1. Query `ROMTransformation` table for `AVG` where `sample_count >= 5`.
2. Else use `DEFAULT_COMPRESSION_RATIOS[self.platform]`.
3. Else use `0.85` (hardcoded ultimate fallback).

The `platform` and `output_format` are passed as constructor args to `SelectionFilter` but the platform matching uses raw string equality against the `DEFAULT_COMPRESSION_RATIOS` keys — no normalization, no enum. A platform named `"sega-cd"` instead of `"segacd"` silently falls through to the 0.85 fallback. The `size_data.json` in `config/` is a second independently maintained compression ratio table that is not consulted here, creating two out-of-sync sources of truth.

### 3.4 Budget Logic Split Across Two Orchestrators

`NewBuildOrchestrator._initialize_budget_tracking()` and `build_orchestrator.py::BuildOrchestrator._initialize_budget_tracking()` are nearly identical methods in two classes. The new orchestrator's `_get_tier_strategy()` method correctly uses `platform_tiers.get_strategy_for_tier()`, but the legacy orchestrator uses different tier logic. Builds using the legacy `BuildConfig` format cannot benefit from tier-based selection.

### 3.5 Loose `StageContext` Field Access Patterns

Several stages use `getattr(context, 'platform_config', None)` or `getattr(context, 'config', None)` defensively because the context evolved through two config eras. `FilterArcadeStage` reads `context.config` (old `PlatformConfig`), while most new stages read `context.platform_config` (also `PlatformConfig` but a different instantiation path). Some stages reference `context.composed_target` (new), some reference `context.platform_config.targets[0]` (old). The `OrganizeStage` does `target_config = context.platform_config.targets[0]` — this is the old API and will break for any `ResolvedPlatformConfig` that doesn't have a `.targets[]` attribute.

### 3.6 The `organized_files_metadata` Shadow Dict

`ApplyListsStage` writes `context.organized_files_metadata` — a dict of `{subdir_name: {"type": "myrient"|"extra", "operation": "copy"|"move"}}` — directly onto the context with `if not hasattr(context, 'organized_files_metadata'): context.organized_files_metadata = {}`. This is dynamic attribute injection onto a dataclass, bypassing the declared schema entirely. `OrganizeStage` presumably reads this dict but it is not a declared field of `StageContext`, making the coupling invisible at the type level.

### 3.7 Filesystem as Intermediate State

The pipeline uses symlinks in `work_dir` as a soft-delete mechanism: `FilterDATStage` creates symlinks for matched files; subsequent PLAN stages "filter out" files by deleting symlinks. This means the filtered state is encoded in the filesystem rather than purely in `context.filtered_files`. If a stage forgets to update `context.filtered_files` after deleting a symlink (or vice versa), the two representations diverge silently. `SelectionFilter` deletes symlinks **and** updates `context.filtered_files`, but this dual-write requirement is undocumented and is not enforced by the base class.

### 3.8 `GenerateMetadataStage` File Discovery

`GenerateMetadataStage.execute()` contains a hardcoded list of 40+ file extension glob patterns to discover output files. This list includes platform-specific raw ROM extensions (`.vb`, `.pce`, `.vec`, `.col`, `.int`, etc.) that should be declared in the frontend's `platforms[].extensions` config, not hardcoded in a stage. Adding a new platform that uses an unlisted extension silently produces empty metadata. There is a second discovery path for PS3 JB folders (checking for `PS3_GAME/PARAM.SFO` sentinel) — this is correct, but it is inline in the same method with no abstraction boundary.

### 3.9 Transformation DB — MD5 vs. CRC32 Mismatch Risk

`FilterDATStage` does MD5 matching. `CachePreCheckStage` does CRC32+size matching from ZIP headers. `CompressCHDStage` does MD5 matching for the secondary cache check. `ROMCache` table stores both paths but they are written by different stages at different times. If `CachePreCheckStage` gets a hit and skips extraction, `CompressCHDStage` never writes the MD5-keyed `ROMCache` row — only the ZIP-identity row exists. A subsequent build that hashes the same source without going through CachePreCheck (e.g., a non-ZIP source) will miss the cache even though the CHD exists in CAS.

---

*End of briefing. Total component count: ~60 Python modules, 21 pipeline stages, 6 config object layers, 2 CAS subsystems (blob + tree), 1 unified SQLite DB.*
