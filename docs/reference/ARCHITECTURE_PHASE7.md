# ROM Farmer Architecture - Phase 7 Complete

## Complete System Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  $ ./romfarmer build run batocera-complete                          │
│                                                                       │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      CLI LAYER (build.py)                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Commands: run | status | resume | list | clean                      │
│  • Parses arguments                                                   │
│  • Validates input                                                    │
│  • Displays rich output                                               │
│                                                                       │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│               BUILD ORCHESTRATOR (build_orchestrator.py)             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Responsibilities:                                                    │
│  • Load build config (batocera-complete.yaml)                        │
│  • Validate system (storage, tools, configs)                         │
│  • Create/load BuildState (.build_state_{name}.yaml)                 │
│  • Sequential platform processing                                    │
│  • Progress tracking (completed/failed/remaining)                    │
│  • Error handling (stop_on_error setting)                            │
│  • Resume capability (skip completed platforms)                      │
│  • Cleanup and verification                                          │
│  • Generate completion report                                        │
│                                                                       │
│  For each platform in [saturn, wii, ps3, ...]:                       │
│    └── Call PlatformProcessor                                        │
│                                                                       │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│            PLATFORM PROCESSOR (platform_processor.py)                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Responsibilities:                                                    │
│  • Load platform config (config/platforms/{name}.yaml)               │
│  • Apply build overrides (targets, compression, enabled)             │
│  • Check if enabled                                                  │
│  • Get source/work/output directories                                │
│                                                                       │
│  For each target in [batocera, rocknix, ...]:                        │
│    └── Call _process_target()                                        │
│                                                                       │
│  _process_target() ⭐ NEW IN PHASE 7:                                │
│    1. Determine system_type (SIMPLE/MEDIUM/COMPLEX/VERY_COMPLEX)     │
│    2. Create Pipeline instance                                       │
│    3. Add stages based on complexity                                 │
│    4. Find DAT file                                                  │
│    5. Execute pipeline                                               │
│    6. Aggregate results                                              │
│                                                                       │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│            STAGE ROUTING ⭐ NEW IN PHASE 7                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─── SIMPLE (Cartridge) ──────────────────────────────────┐        │
│  │  Platforms: NES, SNES, Genesis, GB, GBC, GBA, N64       │        │
│  │  Stages: FilterDAT → ApplyLists → Organize              │        │
│  └──────────────────────────────────────────────────────────┘        │
│                                                                       │
│  ┌─── MEDIUM (CD-ROM) ──────────────────────────────────────┐       │
│  │  Platforms: PS1, Saturn, Dreamcast, Sega CD             │        │
│  │  Stages: FilterDAT → ApplyLists → ExtractArchive →      │        │
│  │          CompressCHD → CreateM3U → Organize              │        │
│  └──────────────────────────────────────────────────────────┘        │
│                                                                       │
│  ┌─── COMPLEX (Wii/GameCube) ───────────────────────────────┐       │
│  │  Platforms: Wii, GameCube                                │        │
│  │  Stages: FilterDAT → ApplyLists → UnzipRVZ → Organize   │        │
│  └──────────────────────────────────────────────────────────┘        │
│                                                                       │
│  ┌─── VERY_COMPLEX (Multi-target) ──────────────────────────┐       │
│  │  Platforms: PS3 (Xbox 360 future)                        │        │
│  │  Stages: FilterDAT → ApplyLists → TransformPS3 →        │        │
│  │          Organize                                         │        │
│  │  Output: 4 formats (rpcs3, ps3netsrv, cfw, batocera)    │        │
│  └──────────────────────────────────────────────────────────┘        │
│                                                                       │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PIPELINE (pipeline.py)                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Responsibilities:                                                    │
│  • Hold list of stages                                               │
│  • Create StageContext (directories, DAT, files, console)            │
│  • Execute stages sequentially                                       │
│  • Collect StageResults                                              │
│  • Display progress (Rich console)                                   │
│  • Stop on failure (configurable)                                    │
│  • Generate pipeline summary                                         │
│                                                                       │
│  For each stage in [FilterDAT, ExtractArchive, ...]:                 │
│    └── stage.execute(context)                                        │
│                                                                       │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STAGES (stages/*.py)                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─ FilterDATStage ──────────────────────────────────────┐          │
│  │  Match files against DAT (1G1R filtering)             │          │
│  │  Input: source ZIPs | Output: matched list            │          │
│  └────────────────────────────────────────────────────────┘          │
│                                                                       │
│  ┌─ ApplyListsStage ──────────────────────────────────────┐         │
│  │  Apply delete/add lists (manual overrides)            │          │
│  │  Input: matched list | Output: filtered list          │          │
│  └────────────────────────────────────────────────────────┘          │
│                                                                       │
│  ┌─ ExtractArchiveStage ──────────────────────────────────┐         │
│  │  Unzip archives to temp                                │          │
│  │  Input: ZIPs | Output: extracted files                │          │
│  └────────────────────────────────────────────────────────┘          │
│                                                                       │
│  ┌─ CompressCHDStage ─────────────────────────────────────┐         │
│  │  Convert BIN/CUE → CHD (chdman)                        │          │
│  │  Input: BIN/CUE | Output: CHD                          │          │
│  └────────────────────────────────────────────────────────┘          │
│                                                                       │
│  ┌─ CreateM3UStage ───────────────────────────────────────┐         │
│  │  Generate M3U playlists for multi-disc                 │          │
│  │  Input: CHDs | Output: .m3u files                      │          │
│  └────────────────────────────────────────────────────────┘          │
│                                                                       │
│  ┌─ UnzipRVZStage ────────────────────────────────────────┐         │
│  │  Extract RVZ files (dolphin-tool)                      │          │
│  │  Input: RVZ ZIPs | Output: RVZ files                   │          │
│  └────────────────────────────────────────────────────────┘          │
│                                                                       │
│  ┌─ TransformPS3Stage ────────────────────────────────────┐         │
│  │  Decrypt + multi-target transform (PS3Dec)             │          │
│  │  Input: encrypted ISOs | Output: 4 formats             │          │
│  └────────────────────────────────────────────────────────┘          │
│                                                                       │
│  ┌─ OrganizeStage ────────────────────────────────────────┐         │
│  │  Copy to output with organization                      │          │
│  │  Input: processed files | Output: organized files      │          │
│  └────────────────────────────────────────────────────────┘          │
│                                                                       │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       OUTPUT                                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  /path/to/output/batocera/                                          │
│    ├── saturn/                                                       │
│    │   ├── Game 1.chd                                                │
│    │   ├── Game 2 (Disc 1).chd                                       │
│    │   ├── Game 2 (Disc 2).chd                                       │
│    │   └── Game 2.m3u                                                │
│    ├── wii/                                                          │
│    │   ├── Game 1.rvz                                                │
│    │   └── Game 2.rvz                                                │
│    └── ps3/                                                          │
│        ├── Game 1.ps3/                                               │
│        │   └── PS3_GAME/...                                          │
│        └── Game 2.ps3/                                               │
│            └── PS3_GAME/...                                          │
│                                                                       │
│  Build state: .build_state_batocera-complete.yaml                    │
│  Progress tracking: completed/failed/remaining                       │
│  Resume capability: Skip completed platforms                         │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow Example: Saturn Processing

```
1. USER
   $ ./romfarmer build run batocera-complete

2. CLI
   → Parse command
   → Validate build name
   → Create BuildOrchestrator

3. BUILD ORCHESTRATOR
   → Load config/builds/batocera-complete.yaml
   → Read platforms: [saturn, wii, gamecube, ps3, ...]
   → Create/load .build_state_batocera-complete.yaml
   → Process platform: "saturn"

4. PLATFORM PROCESSOR
   → Load config/platforms/saturn.yaml
   → System type: MEDIUM
   → Targets: [rocknix, batocera]
   → Apply overrides: none
   → Process target: "rocknix"

5. STAGE ROUTING ⭐ NEW
   → Detect: system_type = MEDIUM
   → Create Pipeline
   → Add stages:
      1. FilterDATStage
      2. ApplyListsStage
      3. ExtractArchiveStage
      4. CompressCHDStage
      5. CreateM3UStage
      6. OrganizeStage
   → Find DAT: /path/to/dats/.../Saturn.dat

6. PIPELINE
   → Create StageContext:
      - source_dir: /path/to/emu/.../Saturn/
      - work_dir: /path/to/temp/saturn/
      - output_dir: /path/to/output/rocknix/saturn/
      - dat_file: Saturn.dat
   → Execute each stage

7. STAGES (Sequential execution)
   
   FilterDATStage:
     Input:  150 ZIP files
     Output: 120 matched (1G1R filtered)
   
   ApplyListsStage:
     Input:  120 matched
     Output: 118 after deletes (2 removed by list)
   
   ExtractArchiveStage:
     Input:  118 ZIPs
     Output: 118 × BIN/CUE files extracted to work_dir
   
   CompressCHDStage:
     Input:  118 × BIN/CUE
     Output: 118 × CHD files (45GB → 23GB)
   
   CreateM3UStage:
     Input:  118 CHD files
     Output: 12 M3U playlists (for multi-disc games)
   
   OrganizeStage:
     Input:  118 CHD + 12 M3U
     Output: Copy to /path/to/output/rocknix/saturn/

8. RESULTS
   → Aggregate: 118 games processed, 23GB output
   → Return to PlatformProcessor
   → Process next target: "batocera" (repeat 4-7)
   → Return to BuildOrchestrator
   → Update BuildState: saturn = completed
   → Process next platform: "wii"
```

## Phase 7 Innovation: Intelligent Routing ⭐

**Before Phase 7:**
Manual pipeline configuration required for each platform.

**After Phase 7:**
Automatic stage selection based on `system_type`:

```python
# Saturn config says:
system_type: medium

# System automatically knows:
pipeline.add_stage(FilterDATStage())
pipeline.add_stage(ApplyListsStage())
pipeline.add_stage(ExtractArchiveStage())
pipeline.add_stage(CompressCHDStage())
pipeline.add_stage(CreateM3UStage())
pipeline.add_stage(OrganizeStage())
```

**Result:** Adding new platforms is trivial!

```yaml
# new_platform.yaml
name: dreamcast
system_type: medium  # That's it! Auto-routes to 6 stages
```

## System Status: Phase 7 Complete ✅

```
┌────────────────────────────────────────────────┐
│  Component               │  Status             │
├────────────────────────────────────────────────┤
│  CLI                     │  ✅ Working         │
│  BuildOrchestrator       │  ✅ Working         │
│  PlatformProcessor       │  ✅ Working         │
│  Stage Routing           │  ⭐ NEW - Working  │
│  Pipeline                │  ✅ Working         │
│  Stages (8 types)        │  ✅ Working         │
│  Config System           │  ✅ Working         │
│  DAT Discovery           │  ⭐ NEW - Working  │
│  State Persistence       │  ✅ Working         │
│  Resume Capability       │  ✅ Working         │
│  Multi-target Output     │  ✅ Working         │
│  Progress Tracking       │  ✅ Working         │
│  Error Handling          │  ✅ Working         │
└────────────────────────────────────────────────┘

Next: Phase 8 - Validate with real ROMs! 🚀
```
