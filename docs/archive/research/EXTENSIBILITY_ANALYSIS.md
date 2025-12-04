# Architecture Extensibility Analysis

**Date:** October 14, 2025  
**Purpose:** Verify that multi-source and advanced features can be added without breaking existing code

---

## TL;DR: Architecture is Highly Extensible ✅

**Your concern:** "I know that sometimes adding a feature blows the whole existing app up in bad ways if the app wasn't built with extensibility in mind"

**Assessment:** This app was built with **excellent extensibility** - adding multi-source, PS Minis, PKG integration, etc. will be **clean additions** not architectural rewrites.

---

## Core Design Principles

### 1. Stage-Based Pipeline Architecture ✅

**Pattern:** Each processing step is an independent Stage

```python
class Stage(ABC):
    """Base class for processing stages."""
    
    @abstractmethod
    def execute(self, context: StageContext) -> StageResult:
        """Execute the stage."""
        pass
```

**Why extensible:**
- ✅ Adding new stage types = just create new class
- ✅ Stages don't know about each other (loose coupling)
- ✅ Pipeline orchestrates, stages process
- ✅ Can insert stages anywhere in pipeline

**Examples:**
```python
# Current stages:
FilterDATStage      # Step 1: Filter by DAT
ApplyListsStage     # Step 2: Apply include/exclude lists
ExtractArchiveStage # Step 3: Unzip files
CompressCHDStage    # Step 4: Compress to CHD
CreateM3UStage      # Step 5: Create playlists
OrganizeStage       # Step 6: Organize output

# Future stages (EASY TO ADD):
MergeSourcesStage   # NEW: Combine multiple sources
InstallPKGStage     # NEW: PS3 PKG integration
ConvertPSPStage     # NEW: ISO → CSO/CHD
```

**Impact of adding new stage:** ✅ ZERO impact on existing stages

---

### 2. StageContext: Shared State Container ✅

**Pattern:** All data passed through context object

```python
@dataclass
class StageContext:
    """Context passed between stages."""
    
    # Platform info
    platform_name: str
    platform_config: Any
    target_name: str
    
    # Working directories
    source_dir: Path
    work_dir: Path
    output_dir: Path
    
    # Files being processed
    source_files: List[Path]
    matched_files: List[Path]
    filtered_files: List[Path]
    organized_files: Dict[str, List[Path]]
    
    # Disc processing (Phase 4)
    extracted_files: List[Path]
    compressed_files: List[Path]
    m3u_files: List[Path]
    disc_groups: Dict[str, Any]
    disc_metadata: Dict[str, Any]
    
    # Complex transformations (Phase 5)
    transformations: List[Any]
    
    # Statistics
    stats: Dict[str, Any]
```

**Why extensible:**
- ✅ Adding new data fields = just add to dataclass
- ✅ Backward compatible (existing stages ignore new fields)
- ✅ Default values prevent breakage (`field(default_factory=list)`)
- ✅ Stages read what they need, ignore the rest

**Multi-source extension (EASY):**
```python
@dataclass
class StageContext:
    # ... existing fields ...
    
    # NEW: Multi-source support (Phase 7)
    secondary_sources: Dict[str, List[Path]] = field(default_factory=dict)
    """Secondary source files keyed by source name (PS Minis, DLC, etc.)"""
    
    merged_files: List[Path] = field(default_factory=list)
    """Files created by merging multiple sources"""
```

**Impact of adding fields:** ✅ ZERO impact on existing stages (they ignore new fields)

---

### 3. YAML-Based Configuration ✅

**Pattern:** All platform logic in config files, not code

```yaml
# config/platforms/saturn.yaml
name: saturn
system_type: complex

sources:
  - path: /data/emu/archive/.../Sega - Saturn
    type: myrient

compression:
  format: chd
  tool: /usr/bin/chdman
  verify: true

targets:
  - name: batocera
    output_path: /data/emu/output/batocera/saturn
    enabled: true
```

**Why extensible:**
- ✅ New platforms = new YAML file (no code changes)
- ✅ New config options = add to YAML schema
- ✅ Code reads config dynamically

**Multi-source extension (EASY):**
```yaml
# config/platforms/psp.yaml (FUTURE)
name: psp

sources:
  primary:
    - path: /data/emu/archive/.../Sony - PlayStation Portable
      type: myrient
      format: iso
  
  secondary:
    - name: psminis
      path: /data/emu/source/psminis
      type: myrient
      format: iso
      target_subfolder: psp-minis  # Batocera: psp/psp-minis/
    
    - name: dlc
      path: /data/emu/source/psp-dlc
      type: extra
      merge_with_primary: true

targets:
  - name: batocera
    output_path: /data/emu/output/batocera/psp
    subfolder_support: true  # NEW: Enable subfolder organization
```

**Impact of adding multi-source config:** ✅ Existing platforms ignore new fields

---

### 4. Platform-Specific Stages ✅

**Pattern:** Custom stages for complex systems

```python
# src/romfarmer/stages/transform_ps3.py
class TransformPS3Stage(Stage):
    """PS3-specific transformation stage."""
    
    def __init__(self, target_name: str):
        super().__init__(f"transform_ps3_{target_name}")
        self.target_name = target_name
    
    def execute(self, context: StageContext) -> StageResult:
        # PS3-specific logic here
        pass
```

**Why extensible:**
- ✅ Complex systems get custom stages
- ✅ Simple systems use generic stages
- ✅ No impact on other platforms

**Future additions (EASY):**
```python
# NEW: src/romfarmer/stages/merge_sources.py
class MergeSourcesStage(Stage):
    """Merge content from multiple source directories."""
    
    def execute(self, context: StageContext) -> StageResult:
        # 1. Scan primary sources
        # 2. Scan secondary sources
        # 3. Match by game name/ID
        # 4. Merge where applicable
        # 5. Update context.merged_files
        pass

# NEW: src/romfarmer/stages/install_pkg.py
class InstallPKGStage(Stage):
    """Install PS3 PKG files to JB folders."""
    
    def execute(self, context: StageContext) -> StageResult:
        # 1. Find matching PKG files
        # 2. Extract PKG content
        # 3. Merge into base game folder
        # 4. Update transformations
        pass

# NEW: src/romfarmer/stages/compress_psp.py
class CompressPSPStage(Stage):
    """Convert PSP ISO to CSO/CHD."""
    
    def execute(self, context: StageContext) -> StageResult:
        # Similar to CompressCHDStage but uses maxcso
        pass
```

**Impact:** ✅ ZERO - existing stages unaffected

---

### 5. Target-Specific Output ✅

**Pattern:** Each target has its own configuration

```yaml
targets:
  - name: batocera
    output_path: /data/emu/output/batocera/saturn
    organization:
      style: rich
      create_subdirs: true
    enabled: true
  
  - name: rocknix
    output_path: /data/emu/output/rocknix/saturn
    organization:
      style: balanced
    enabled: false
```

**Why extensible:**
- ✅ Different targets get different output structures
- ✅ Target-specific features in config, not code
- ✅ Adding new targets = add to YAML

**Multi-folder extension (EASY):**
```yaml
targets:
  - name: batocera
    output_path: /data/emu/output/batocera/psp
    organization:
      style: rich
      subfolders:  # NEW: Target-specific subfolder rules
        - source: psminis
          subfolder: psp-minis
          merge: false
  
  - name: rocknix
    output_path: /data/emu/output/rocknix/psp
    organization:
      style: balanced
      subfolders:  # NEW: Different structure for RocknIX
        - source: psminis
          separate_folder: /data/emu/output/rocknix/psp-minis
          merge: false
```

---

## Extension Point Analysis

### Adding Multi-Source Support

**What needs to change:**

1. **StageContext** (src/romfarmer/stages/base.py)
   ```python
   # ADD these fields:
   secondary_sources: Dict[str, List[Path]] = field(default_factory=dict)
   merged_files: List[Path] = field(default_factory=list)
   ```
   **Impact:** ✅ Backward compatible (default values)

2. **PlatformConfig** (needs schema update)
   ```python
   # ADD support for:
   sources:
     primary: List[SourceConfig]
     secondary: List[SecondarySourceConfig]
   ```
   **Impact:** ✅ Backward compatible (if missing, treat as single source)

3. **New Stage** (src/romfarmer/stages/merge_sources.py)
   ```python
   class MergeSourcesStage(Stage):
       """NEW stage to merge multiple sources"""
   ```
   **Impact:** ✅ ZERO - doesn't affect existing stages

4. **Pipeline** (src/romfarmer/stages/pipeline.py)
   ```python
   # ADD stage to pipeline if multi-source config exists:
   if platform_config.has_secondary_sources():
       pipeline.add_stage(MergeSourcesStage())
   ```
   **Impact:** ✅ Conditional - only runs if configured

**Existing platforms affected:** ✅ NONE (they don't have secondary sources configured)

---

### Adding PSP with PS Minis

**What needs to change:**

1. **Create psp.yaml** (config/platforms/psp.yaml)
   ```yaml
   # NEW platform config with multi-source
   sources:
     primary: [...]
     secondary:
       - name: psminis
         path: /data/emu/source/psminis
   ```
   **Impact:** ✅ New file, no changes to existing configs

2. **Use existing stages:**
   - FilterDATStage ✅ (works as-is)
   - ApplyListsStage ✅ (works as-is)
   - ExtractArchiveStage ✅ (works as-is)
   - MergeSourcesStage ✅ (NEW, optional)
   - CompressPSPStage ✅ (NEW, like CompressCHDStage)
   - OrganizeStage ✅ (works as-is)

3. **Organize stage enhancement:**
   ```python
   # ADD subfolder support in OrganizeStage
   if target_config.has_subfolder_config():
       # Place files in target-specific subfolders
       for source_name, files in context.secondary_sources.items():
           subfolder = target_config.get_subfolder(source_name)
           # Place in psp/psp-minis/ or separate psp-minis/
   ```
   **Impact:** ✅ Backward compatible (only if subfolder_support configured)

**Existing platforms affected:** ✅ NONE

---

### Adding PS3 PKG Integration

**What needs to change:**

1. **StageContext** (add PKG tracking)
   ```python
   pkg_files: List[Path] = field(default_factory=list)
   pkg_installations: Dict[str, Any] = field(default_factory=dict)
   ```
   **Impact:** ✅ Backward compatible

2. **ps3.yaml** (add PKG source)
   ```yaml
   sources:
     primary:
       - path: /data/emu/archive/.../Sony - PlayStation 3
     pkg:  # NEW: Optional PKG files
       - path: /data/emu/source/ps3-pkg
         type: pkg
         merge_with_base: true
   ```
   **Impact:** ✅ Existing PS3 configs ignore this (optional)

3. **New stage** (src/romfarmer/stages/install_pkg.py)
   ```python
   class InstallPKGStage(Stage):
       """Install PKG files to base game folders"""
   ```
   **Impact:** ✅ ZERO - optional stage

4. **TransformPS3Stage enhancement:**
   ```python
   # AFTER base game folder created, IF PKG files found:
   if context.pkg_files:
       # Extract and merge PKG content
       pass
   ```
   **Impact:** ✅ Backward compatible (if no PKG files, skip)

**Existing platforms affected:** ✅ NONE (only PS3 uses TransformPS3Stage)

---

## Real-World Extension Scenarios

### Scenario 1: Add PSP with Multi-Source (Phase 7)

**Steps:**
1. ✅ Create `config/platforms/psp.yaml` (NEW FILE)
2. ✅ Create `src/romfarmer/stages/merge_sources.py` (NEW FILE)
3. ✅ Create `src/romfarmer/stages/compress_psp.py` (NEW FILE)
4. ✅ Update `StageContext` to add `secondary_sources` field (BACKWARD COMPATIBLE)
5. ✅ Update `OrganizeStage` to support subfolder routing (BACKWARD COMPATIBLE)

**Files changed:** 3 NEW, 2 MODIFIED (backward compatible changes)  
**Platforms affected:** NONE (PSP is new, Saturn/Wii/GC/PS3 unaffected)  
**Risk level:** ✅ LOW - isolated changes

---

### Scenario 2: Add PS3 PKG Integration (Phase 8)

**Steps:**
1. ✅ Update `config/platforms/ps3.yaml` to add PKG source (OPTIONAL FIELD)
2. ✅ Create `src/romfarmer/stages/install_pkg.py` (NEW FILE)
3. ✅ Update `StageContext` to add `pkg_files` field (BACKWARD COMPATIBLE)
4. ✅ Update `TransformPS3Stage` to merge PKG content (CONDITIONAL LOGIC)

**Files changed:** 1 NEW, 3 MODIFIED (backward compatible changes)  
**Platforms affected:** NONE (only PS3, conditional on PKG source configured)  
**Risk level:** ✅ LOW - isolated to PS3 pipeline

---

### Scenario 3: Add SNES with Satellaview (Phase 9)

**Steps:**
1. ✅ Create `config/platforms/snes.yaml` (NEW FILE)
2. ✅ Use existing `MergeSourcesStage` (already built for PSP)
3. ✅ Configure subfolder routing in target config

**Files changed:** 1 NEW  
**Platforms affected:** NONE  
**Risk level:** ✅ VERY LOW - reuses existing multi-source infrastructure

---

## Architecture Strengths

### ✅ Loose Coupling
- Stages are independent
- Context is the only shared state
- Adding stages doesn't affect existing ones

### ✅ High Cohesion
- Each stage has one clear responsibility
- Platform-specific logic isolated to platform-specific stages
- Generic stages reused across platforms

### ✅ Configuration-Driven
- Platform logic in YAML, not Python
- New platforms = new config files
- No code recompilation needed

### ✅ Backward Compatibility
- New fields have default values
- Optional features are conditional
- Existing configs continue working

### ✅ Testability
- Each stage testable independently
- Mock StageContext for unit tests
- Pipeline integration tests

---

## Potential Pain Points (Minimal)

### 1. StageContext Growth
**Risk:** Context object could become bloated with many fields

**Mitigation:**
- ✅ Already organized by category (files, disc processing, transformations)
- ✅ Use nested dataclasses if needed (e.g., `MultiSourceData`)
- ✅ Fields are optional with defaults

**Severity:** 🟡 LOW - manageable with refactoring

---

### 2. Pipeline Complexity
**Risk:** Pipeline setup could get complex with conditional stages

**Mitigation:**
- ✅ Pipeline builder pattern already in place
- ✅ Conditional stage addition based on config
- ✅ Each platform defines its own pipeline

**Severity:** 🟡 LOW - already handled well

---

### 3. Target-Specific Organization
**Risk:** Different targets need different folder structures

**Mitigation:**
- ✅ OrganizeStage already supports multiple styles
- ✅ Target config defines output structure
- ✅ Adding subfolder support is straightforward extension

**Severity:** 🟢 VERY LOW - architecture designed for this

---

## Conclusion

### Your Question: "Can we add features later without blowing up the app?"

**Answer: YES! ✅**

**Why:**

1. **Stage-based architecture** = Add stages without touching existing ones
2. **Context-based state** = Add fields without breaking existing code
3. **Config-driven platforms** = Add platforms without code changes
4. **Loose coupling** = Changes isolated to specific modules
5. **Backward compatibility** = Default values prevent breakage

### Specific Extensions You Asked About:

| Feature | Implementation Difficulty | Risk to Existing Code |
|---------|--------------------------|----------------------|
| **Multi-source (PSP/SNES)** | 🟢 Easy | 🟢 None |
| **PS Minis subfolder** | 🟢 Easy | 🟢 None |
| **PS3 PKG integration** | 🟡 Medium | 🟢 None |
| **Target-specific subfolders** | 🟢 Easy | 🟢 None |
| **CISO → CHD conversion** | 🟢 Easy | 🟢 None |

### Recommendation:

**✅ Proceed with Phase 6 Master Build NOW**

**Why:**
- Architecture is solid for future extensions
- Multi-source, PKG, PSP can be added cleanly later
- No risk of "blowing up" existing platforms
- Better to have working master build, then enhance

**Phase 6 Focus:**
- Master build orchestrator
- Process Saturn, Wii, GameCube, PS3
- Get `romfarmer build batocera-complete` working
- Prove the architecture with 4 diverse platforms

**Phase 7+ Enhancements:**
- PSP with PS Minis (multi-source pattern)
- PS3 PKG integration (optional enhancement)
- SNES with Satellaview (reuses multi-source)
- More simple platforms (NES, Genesis, N64, GBA)

### The Bottom Line:

**Your concern is valid** - some architectures are brittle and extensions break everything.

**This architecture is NOT brittle** - it was designed with exactly this concern in mind:
- ✅ Extensible by design
- ✅ Backward compatible by default
- ✅ Loosely coupled
- ✅ Configuration-driven
- ✅ Stage-based (add without breaking)

**You can confidently finish the main application!** 🎉

The multi-source, PKG, and other features will be **clean additions**, not architectural rewrites.
