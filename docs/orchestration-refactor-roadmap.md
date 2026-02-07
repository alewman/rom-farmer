# Orchestration Refactor — Sprint Roadmap

**Date**: 2026-02-07
**Branch**: `refactor/declarative-orchestration` (from `512aa35`)
**Goal**: Replace the current imperative override-based build system with a declarative, composable architecture

---

## The Problem

The current system has three structural flaws:

1. **Platform configs carry build concerns.** `saturn.yaml` hardcodes output paths,
   organization styles, and target profiles — things that change per-build. Every
   build overrides them anyway, making the platform config's version dead code.

2. **Overrides instead of composition.** To say "all 26 cartridge platforms get 7z
   compression," you write the same override block 26 times. The system forces you
   to think in terms of *per-platform patches* when you're actually thinking in terms
   of *categories and rules*.

3. **One model serves three purposes.** `BuildConfig` is a 30+ field god object
   with most fields `Optional`, serving target builds, system builds, and legacy
   builds simultaneously. Test builds require copying 40 lines of boilerplate
   just to say "run Saturn with 10 games."

The root cause: the config system was designed platform-first ("here's everything
about Saturn") when builds are actually *rule-first* ("all disc platforms get CHD,
all cartridge platforms get 7z, deploy to Batocera").

---

## The Design

### Core Principle: Separate WHAT from HOW from WHERE

Every piece of configuration belongs to exactly one of three layers:

| Layer | Question | Changes when... | Example |
|-------|----------|-----------------|---------|
| **Platform** | *What is this system?* | Never (intrinsic facts) | Saturn uses disc extraction, has multi-disc games |
| **Recipe** | *How should it be processed?* | You change build goals | Compress to CHD, select top 40GB by rating |
| **Target** | *Where is it going?* | You change deployment | Batocera on PC, flat folders, 7z-capable |

### New Config Structure

```
config/
├── platforms/          # WHAT — immutable facts about each system
│   ├── saturn.yaml     #   extraction: disc, multi_disc: true, sources: [...]
│   ├── nes.yaml        #   extraction: cartridge, sources: [...]
│   └── ...
│
├── recipes/            # HOW — reusable processing templates
│   ├── nointro-7z.yaml       #   platforms: [nes, snes, gb, ...], compress: 7z
│   ├── redump-chd.yaml       #   platforms: [psx, saturn, ...], compress: chd
│   ├── nintendo-disc-rvz.yaml
│   ├── arcade-fbneo.yaml
│   └── test-sample-10.yaml   #   selection: {strategy: random, limit: 10}
│
├── targets/            # WHERE — deployment destinations
│   ├── batocera-pc.yaml       #   frontend: batocera, device: pc
│   ├── rocknix-r36s.yaml      #   frontend: rocknix, device: r36s
│   └── ...
│
├── frontends/          # (unchanged) software capabilities
├── devices/            # (unchanged) hardware constraints
├── platform_tiers.yaml # (unchanged) budget prioritization
├── generations.yaml    # (unchanged) cross-platform dedup
└── sources.yaml        # (unchanged) source root paths
```

### What Each File Looks Like

#### Platform (stripped to intrinsic facts only)

```yaml
# config/platforms/saturn.yaml
name: saturn
extraction: disc          # How to get game files out of archives
multi_disc: true          # Has multi-disc games
dat_source: redump        # Which DAT collection (redump vs nointro)
dat_pattern: "sega - saturn"  # How to find the DAT file
sources:
  - root: local
    subdir: saturn
```

Every field here is an *immutable fact about the Saturn hardware and its ROM
distribution*. Nothing about compression, organization, output paths, or
build preferences. ~15 lines instead of ~80.

#### Recipe (reusable processing template)

```yaml
# config/recipes/redump-chd.yaml
name: redump-chd
description: "Redump disc platforms → CHD compression"

# Which platforms this recipe applies to
platforms:
  - 3do
  - dreamcast
  - megacd
  - neogeocd
  - pcenginecd
  - ps2
  - psp
  - pspminis
  - psx
  - saturn

# Processing options (these ARE the build choices)
dat_filter: retool_1g1r_eng    # Which DAT variant
compression: chd               # Output format
lists: true                    # Apply keep/delete lists
```

```yaml
# config/recipes/test-10.yaml
name: test-10
description: "10 random games per platform (testing)"
selection:
  strategy: random
  limit: 10
  seed: 42
```

A recipe answers: "for these platforms, what processing choices do I want?"
Recipes compose — a build can stack them.

#### Build (declarative intent)

```yaml
# config/builds/batocera-1tb.yaml
name: batocera-1tb
target: batocera-pc

recipes:
  - nointro-7z           # All cartridge platforms → 7z
  - redump-chd           # All disc platforms → CHD
  - nintendo-disc-rvz    # GC/Wii/WiiU → RVZ
  - arcade-fbneo         # FBNeo curated arcade

exclude: [3ds]           # Skip 3DS for this build
```

That's it. ~10 lines to declare a complete 1TB multi-platform build. No
`platform_overrides`, no `includes`, no `settings` boilerplate.

#### Test Build (trivially derived)

```yaml
# config/builds/test-saturn-10.yaml
name: test-saturn-10
target: batocera-pc
recipes:
  - redump-chd
  - test-10              # Stacks on top: limits to 10 games
platforms: [saturn]      # Only process Saturn
```

6 lines. No more copying 50 lines of boilerplate for test builds.

### How Recipe Composition Works

When a build references multiple recipes, they compose with clear precedence:

1. **Platform selection**: Union of all recipe platform lists, minus `exclude`
2. **Processing options**: Later recipes override earlier ones for overlapping platforms
3. **Platform intrinsics**: Always come from the platform config (extraction type, sources)
4. **Target constraints**: Applied last (device unsupported list, frontend compression fallback)

For each platform in the build, the effective configuration is:

```
platform intrinsics (saturn.yaml)
  + recipe processing choices (redump-chd.yaml)
  + recipe overrides (test-10.yaml stacks selection on top)
  + target constraints (batocera-pc: flat org, 7z fallback, etc.)
  = fully resolved pipeline spec
```

### Pipeline Assembly Becomes Declarative

Instead of 200 lines of if/elif in `_process_target()`, the resolved config
directly implies the pipeline:

```
extraction: disc  →  [FilterDAT, Filter1G1R, ApplyLists, Extract, CompressCHD, M3U, Organize, Metadata]
extraction: cart  →  [FilterDAT, Filter1G1R, ApplyLists, Extract, Compress7z,       Organize, Metadata]
extraction: rvz   →  [FilterDAT, Filter1G1R, ApplyLists, UnzipRVZ,                  Organize, Metadata]
extraction: ps3   →  [FilterDAT, Filter1G1R, ApplyLists, ExtractPS3,                Organize, Metadata]
extraction: xiso  →  [FilterDAT, Filter1G1R, ApplyLists, Extract, ConvertXISO,      Organize, Metadata]
type: arcade      →  [FilterArcade, ApplyLists, CopyArcade,                                  Metadata]
```

Selection and cache-precheck stages insert themselves when the resolved config
has `selection` or `cache` settings. This is a lookup table, not branching logic.

### Output Path Derivation

No more hardcoded `output_path` in configs. Output paths are *derived*:

```
{output_base} / {build_name} / {frontend_folder_name}
```

Example: `output/batocera-1tb/saturn/`

The frontend provides folder mapping (Saturn → "saturn", Atari Jaguar → "jaguar").
The build provides the base. No config needs to state this.

---

## Migration Strategy

### What Gets Preserved (valuable config data)

- **68 platform configs**: Stripped to intrinsics. All source paths, DAT patterns,
  extraction types, multi-disc flags are preserved.
- **Frontend configs**: Unchanged (folder mapping, extensions, compression prefs).
- **Device configs**: Unchanged (unsupported platforms, display info).
- **Target configs**: Unchanged (frontend + device composition).
- **Platform tiers**: Unchanged.
- **Generations**: Unchanged.
- **Sources**: Unchanged.
- **Lists**: Unchanged (keep/delete files are not part of config).

### What Gets Replaced

- **59 build configs → ~15 builds + ~8 recipes**:
  - 29 test builds → 2-3 test recipes (`test-10`, `test-3`, `test-1`) that
    stack onto any build
  - Remaining test YAML files archived to `config/builds/archive/`
  - Production builds rewritten as recipe-based declarations
- **`platform_overrides` blocks → recipe platform lists**: The 26-line YAML
  anchor blocks in `nointro-1g1r-eng-7z-batocera.yaml` become a single recipe.
- **`targets` field in platform configs → removed**: Output routing derived
  from build + target.
- **`BuildConfig` god object → split models**: `BuildSpec`, `RecipeSpec`,
  `ResolvedPlatformConfig` (the fully-composed result)

### Backward Compatibility Period

Old `BuildConfig` model stays loadable during migration. A compatibility shim
detects old-format configs (presence of `platform_overrides` or `includes`) and
translates them to the new model. This lets us migrate incrementally.

---

## Sprint Plan (7 Steps)

### Step 1: Slim Platform Configs
**Files**: `config/platforms/*.yaml`, `src/romfarmer/config/models.py`
**Tests**: Update `test_config.py`

Strip platform configs to intrinsics only:
- Keep: `name`, `type`, `emulator`, `metadata_system`, `dat_source`+`dat_pattern`,
  `sources`, `chd_sources`, `extraction` (type only), `multi_disc`, `updates` (PS3)
- Remove: `targets`, `compression`, `selection`, `rating_filter`, `lists`,
  `custom_stages`, `enabled`, `system_type`, `extract_archives`
- Move `dat.source` → `dat_source` (simple string), `dat.file` → `dat_pattern`
- Rename `ExtractionConfig` to just the type enum (enabled is always true if type != none)

Create `SlimPlatformConfig` Pydantic model alongside old `PlatformConfig`.
Old model stays for backward compat during migration.

**Estimated size**: ~200 lines of model code + 68 YAML rewrites (scriptable)

### Step 2: Create Recipe Model and Loader
**Files**: `src/romfarmer/config/recipe.py`, `config/recipes/*.yaml`
**Tests**: New `test_recipe.py`

New Pydantic model `RecipeSpec`:
```python
class RecipeSpec(BaseModel):
    name: str
    description: str = ""
    platforms: list[str] = []          # Empty = "all platforms in the build"
    dat_filter: str = "retool_1g1r_eng"
    compression: str = "none"
    selection: SelectionConfig | None = None
    lists: bool = True
    arcade_filter: dict | None = None  # For arcade recipes
```

Create initial recipes from existing build configs:
- `nointro-7z` (from `nointro-1g1r-eng-7z-batocera.yaml`)
- `redump-chd` (from `redump-1g1r-eng-chd-batocera.yaml`)
- `nintendo-disc-rvz` (from `nintendo-disc-1g1r-eng-rvz-batocera.yaml`)
- `arcade-fbneo`, `arcade-mame`, `arcade-sega`
- `ps3-jb` (PS3-specific)
- `xbox-xiso` (Xbox-specific)
- `test-10`, `test-3`, `test-1` (test recipes with selection limits)

Recipe loader with validation (platforms must exist, compression must be valid
for extraction type).

**Estimated size**: ~150 lines model + ~80 lines loader + ~10 YAML files

### Step 3: Create New BuildSpec Model
**Files**: `src/romfarmer/config/build_spec.py`
**Tests**: New `test_build_spec.py`

New Pydantic model `BuildSpec`:
```python
class BuildSpec(BaseModel):
    name: str
    description: str = ""
    target: str                        # Target name (batocera-pc, rocknix-r36s)
    recipes: list[str]                 # Recipe names, applied in order
    platforms: list[str] | None = None # Override: only process these platforms
    exclude: list[str] = []            # Remove these platforms
    selection: SelectionConfig | None = None  # Global selection override
    generation_filter: str | None = None
    storage_budget: str | None = None  # "512gb", "1tb", "unlimited"
    post_build: list[dict] = []
    deploy: dict | None = None
```

Key: `BuildSpec` is small and declarative. No `platform_overrides`, no `includes`,
no `settings` boilerplate, no `storage` paths.

**Estimated size**: ~80 lines model + ~50 lines loader

### Step 4: Config Resolver (The Composition Engine)
**Files**: `src/romfarmer/config/resolver.py`
**Tests**: New `test_resolver.py` (most critical tests)

This is the heart of the new system. Given a `BuildSpec`, it produces a
`ResolvedPlatformConfig` for each platform in the build.

```python
class ResolvedPlatformConfig:
    """Fully resolved config for one platform in one build."""
    platform: str
    extraction_type: ExtractionType
    compression: CompressionFormat
    dat_filter: str
    dat_pattern: str
    sources: list[SourceConfig]
    selection: SelectionConfig | None
    multi_disc: bool
    apply_lists: bool
    output_dir: Path
    folder_name: str          # From frontend mapping
    organization: str         # From frontend default
    metadata: bool
    # ... PS3/Xbox specifics when applicable
```

Resolution algorithm:
```
for each platform in (union of recipe platforms) - excludes:
    1. Load SlimPlatformConfig (intrinsic facts)
    2. Stack recipes in order (later wins for overlapping fields)
    3. Apply target constraints (frontend compression fallback, folder mapping)
    4. Apply device filter (skip unsupported platforms)
    5. Apply budget/tier constraints
    6. Derive output path
    → emit ResolvedPlatformConfig
```

**Estimated size**: ~250 lines resolver + ~200 lines tests

### Step 5: Pipeline Builder (Declarative Stage Assembly)
**Files**: `src/romfarmer/stages/builder.py`
**Tests**: New `test_pipeline_builder.py`

Replace the 200-line if/elif chain in `_process_target()` with a declarative
pipeline builder:

```python
def build_pipeline(resolved: ResolvedPlatformConfig, cache: CacheManager | None) -> Pipeline:
    """Build a processing pipeline from a resolved config."""
    stages = []

    # Filtering (always first)
    if resolved.is_arcade:
        stages.append(FilterArcadeStage())
    else:
        stages.append(FilterDATStage())
        stages.append(Filter1G1RStage())

    # Selection (if configured)
    if resolved.selection:
        stages.append(SelectionFilter(selection=resolved.selection, ...))

    # Lists
    if resolved.apply_lists:
        stages.append(ApplyListsStage())

    # Extraction + Compression (lookup table)
    stages.extend(EXTRACTION_STAGES[resolved.extraction_type](resolved, cache))

    # Output
    if resolved.is_arcade:
        stages.append(CopyArcadeStage())
    else:
        stages.append(OrganizeStage())

    stages.append(GenerateMetadataStage())
    return Pipeline(stages)
```

The extraction stage lookup table:
```python
EXTRACTION_STAGES = {
    ExtractionType.CARTRIDGE: lambda r, c: _cartridge_stages(r, c),
    ExtractionType.DISC:      lambda r, c: _disc_stages(r, c),
    ExtractionType.RVZ:       lambda r, c: [UnzipRVZStage()],
    ExtractionType.PS3:       lambda r, c: [ExtractPS3Stage(...)],
    ExtractionType.XISO:      lambda r, c: [ExtractArchiveStage(), ConvertXISOStage(...)],
    ExtractionType.NONE:      lambda r, c: [],
}
```

**Estimated size**: ~120 lines builder + ~100 lines tests

### Step 6: New Orchestrator
**Files**: `src/romfarmer/orchestrator.py` (replaces `build_orchestrator.py`)
**Tests**: Update existing orchestrator tests

Simplified orchestrator that:
1. Loads `BuildSpec`
2. Calls resolver to get `ResolvedPlatformConfig` per platform
3. Calls pipeline builder for each
4. Executes pipelines sequentially (with tier ordering, budget tracking)
5. Runs post-build hooks (generation filter, jdupes, deploy)

Most of the existing orchestrator logic (state management, budget tracking,
tier ordering, generation filter, post-build hooks) is preserved. What changes
is *how configs are loaded and composed* — that's steps 1-4.

The old `PlatformProcessor` class gets replaced by the resolver + pipeline
builder working together. The 757-line file shrinks to ~200 lines.

**Estimated size**: ~400 lines (vs 981 current) + test updates

### Step 7: Migration and Cleanup
**Files**: Config YAMLs, old model files, CLI commands

- Archive old build configs: `config/builds/archive/`
- Write new build configs using recipe references
- Write migration script to convert old platform configs to slim format
- Update CLI `build run` command to detect and load either format
- Remove backward-compat shim after all configs migrated
- Update `pyproject.toml` entry points
- Final test pass: all 372 tests pass (with config test rewrites)

**Estimated size**: Migration script + ~15 new YAML builds + test updates

---

## Key Recipes to Create (from existing production builds)

| Recipe | Source | Platforms | Key Settings |
|--------|--------|-----------|-------------|
| `nointro-7z` | nointro-1g1r-eng-7z-batocera | 28 cartridge platforms | extract=cart, compress=7z, dat=retool_1g1r_eng |
| `nointro-zip` | nointro-1g1r-eng-7z-rocknix | Same 28 platforms | extract=cart, compress=zip, dat=retool_1g1r_eng |
| `nointro-none` | (new) | 3ds only | extract=cart, compress=none |
| `redump-chd` | redump-1g1r-eng-chd-batocera | 10 disc platforms | extract=disc, compress=chd, dat=redump_retool_1g1r_eng |
| `nintendo-disc-rvz` | nintendo-disc-rvz-batocera | gc, wii, wiiu | extract=rvz, compress=rvz |
| `ps3-jb` | ps3-test | ps3 | extract=ps3, compress=none |
| `xbox-xiso` | xbox-full | xbox, xbox360 | extract=xiso, compress=none |
| `arcade-fbneo` | arcade-fbneo-batocera | fbneo | type=arcade, dat=fbneo |
| `arcade-mame` | arcade-mame-batocera | mame, hbmame | type=arcade, dat=mame |
| `arcade-sega` | arcade-sega-batocera | naomi, model2, etc. | type=arcade |
| `test-10` | (new) | (any) | selection: random, limit: 10, seed: 42 |
| `test-3` | (new) | (any) | selection: random, limit: 3, seed: 42 |
| `test-1` | (new) | (any) | selection: first, limit: 1 |

## Key Builds to Create (replacing 59 existing)

| Build | Target | Recipes | Notes |
|-------|--------|---------|-------|
| `batocera-1tb` | batocera-pc | nointro-7z, redump-chd, nintendo-disc-rvz, arcade-fbneo | Main production build |
| `batocera-full` | batocera-pc | nointro-7z, redump-chd, nintendo-disc-rvz, ps3-jb, xbox-xiso, arcade-fbneo, arcade-mame, arcade-sega | Everything |
| `batocera-512gb` | batocera-pc | nointro-7z, redump-chd, nintendo-disc-rvz | exclude: [ps2, 3ds] |
| `rocknix-r36s` | rocknix-r36s | nointro-zip, redump-chd | Device limits auto-exclude |
| `saturn-chd` | batocera-pc | redump-chd | platforms: [saturn] |
| `psx-chd` | batocera-pc | redump-chd | platforms: [psx] |
| `gen5-dedupe` | batocera-pc | redump-chd | generation_filter: gen5 |
| `gen6-dedupe` | batocera-pc | redump-chd, xbox-xiso | generation_filter: gen6 |
| `test-saturn` | batocera-pc | redump-chd, test-10 | platforms: [saturn] |
| `test-nes` | batocera-pc | nointro-7z, test-10 | platforms: [nes] |
| `test-quick` | batocera-pc | nointro-7z, test-1 | platforms: [gb] — fastest possible |

---

## What Stays Unchanged

- **Stage implementations**: All 25+ stage files (`extract.py`, `compress.py`, etc.)
  keep their current interfaces. Only how they're *assembled* changes.
- **StageContext / Pipeline**: The context dataclass and pipeline runner stay.
- **Frontend/Device/Target**: Already well-designed, no changes needed.
- **CAS store**: Completely orthogonal to this refactor.
- **MCP server**: Orthogonal (queries DB, not build configs).
- **Cache system**: Stays, just wired differently in pipeline builder.
- **Lists**: Keep/delete files unchanged.
- **DAT parser**: Unchanged.
- **Metadata/scraper**: Unchanged.

## Risk Mitigation

- **Step 1 (slim platforms) is independently valuable** — even without
  recipes, cleaner platform configs make the whole system easier to understand.
- **Old BuildConfig stays loadable** throughout migration — no big-bang cutover.
- **Each step has its own tests** — we validate at every stage.
- **Production builds are rewritten last** (Step 7) — the system works on old
  configs until we're confident in the new format.
- **Git checkpoint before each step** — easy rollback.

## Success Criteria

After this sprint:

1. **A test build is 6 lines of YAML**, not 50
2. **A full production build is ~10 lines**, not 120
3. **Adding a new platform** means writing one ~15-line YAML (intrinsics only),
   then adding its name to an existing recipe's platform list
4. **The pipeline assembly logic** is a ~30-line lookup table, not a 200-line
   if/elif chain
5. **Platform configs contain zero build-specific information** — no output paths,
   no compression settings, no target profiles
6. **All 372 tests pass** (with config-specific tests rewritten for new models)

---

## Estimated Effort

| Step | Description | Est. Lines Changed | Depends On |
|------|-------------|-------------------|------------|
| 1 | Slim platform configs | ~400 code + 68 YAML | — |
| 2 | Recipe model + loader | ~250 code + 10 YAML | — |
| 3 | BuildSpec model | ~150 code | — |
| 4 | Config resolver | ~450 code + tests | 1, 2, 3 |
| 5 | Pipeline builder | ~220 code + tests | 4 |
| 6 | New orchestrator | ~400 code + tests | 4, 5 |
| 7 | Migration + cleanup | ~50 code + 25 YAML | 1-6 |

Steps 1, 2, 3 can be done in parallel. Step 4 is the critical path.
Steps 5 and 6 can be done together once 4 is solid.

Total: ~1,900 lines of new code (replacing ~2,700 lines of old code) + config YAMLs.
