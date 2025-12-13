# ROM Farmer Target Capabilities - Implementation Plan

## Overview

This document outlines the implementation plan for the Target Capabilities Architecture, transforming ROM Farmer from inline target definitions to a composed Frontend + Device + Target model.

**Estimated effort:** 3-4 focused sessions  
**Risk level:** Medium (fundamental architecture change, but no breaking external dependencies)

---

## Phase 1: Schema & Config Files (Foundation)

### 1.1 Create Pydantic Models

Create new schema files for the three new entity types.

**File:** `src/romfarmer/schemas/frontend.py`
- `FrontendPlatformConfig`: extensions, preferred_compression
- `FrontendConfig`: name, folder_mapping, media_support, platforms, compression_fallback, defaults

**File:** `src/romfarmer/schemas/device.py`
- `DisplayConfig`: resolution, aspect_ratio
- `MediaSizingConfig`: max_image_width, max_image_height, video_max_resolution
- `DeviceConfig`: name, display, media_sizing, unsupported_platforms

**File:** `src/romfarmer/schemas/target.py`
- `TargetConfig`: name, frontend, device, overrides

**File:** `src/romfarmer/schemas/build.py` (update existing)
- Add `type` field: "target" | "system"
- Add `storage_budget` field
- Add `profile` field  
- Add `platform_budgets` dict
- Add `selection_override` for test builds

### 1.2 Create Config Files

**Directory:** `config/frontends/`
- `batocera.yaml` - Full-featured frontend
- `rocknix.yaml` - Handheld-optimized frontend

**Directory:** `config/devices/`
- `pc.yaml` - Desktop, no limits
- `steamdeck.yaml` - Portable PC
- `r36s.yaml` - Budget handheld

**Directory:** `config/targets/`
- `batocera-pc.yaml`
- `batocera-steamdeck.yaml`
- `rocknix-r36s.yaml`

### 1.3 Create Config Loaders

**File:** `src/romfarmer/config/loaders.py` (new or extend existing)
- `load_frontend(name: str) -> FrontendConfig`
- `load_device(name: str) -> DeviceConfig`
- `load_target(name: str) -> TargetConfig`
- `load_composed_target(name: str) -> ComposedTarget` (resolves frontend + device)

---

## Phase 2: Build System Integration

### 2.1 Update Build Loader

**File:** `src/romfarmer/config/build_loader.py` (or equivalent)

- Detect build type from config (target vs system)
- Load composed target for target builds
- Validate platforms against target capabilities
- Compute output folder name

### 2.2 Update Build Context

**File:** `src/romfarmer/context.py` (or equivalent)

Add to `BuildContext`:
- `composed_target: ComposedTarget` - The resolved target
- `frontend: FrontendConfig` - Direct access to frontend
- `device: DeviceConfig` - Direct access to device
- `output_folder: str` - Computed output path

### 2.3 Platform Resolution

**File:** `src/romfarmer/resolver.py` (new)

- `resolve_platforms(build, target) -> list[str]`
  - Start with requested platforms
  - Filter by frontend support
  - Filter by device support
  - Return final list

### 2.4 Output Folder Computation

**File:** `src/romfarmer/output.py` (new or extend)

- Target builds: `{frontend}-{device}-{storage}-{profile}/`
- System builds: `{platform}-{compression}-{selection}/`

---

## Phase 3: Stage Integration

### 3.1 Compression Stage

**File:** `src/romfarmer/stages/compress.py`

- Get preferred compression from `frontend.platforms[platform].preferred_compression`
- Apply fallback if format not supported
- Remove hardcoded compression decisions

### 3.2 Organize Stage

**File:** `src/romfarmer/stages/organize.py`

- Get folder name from `frontend.folder_mapping.get(platform, platform)`
- Use computed output folder from context
- Remove `platform_folder_map` logic (now in frontend)

### 3.3 Metadata Stage

**File:** `src/romfarmer/stages/metadata.py`

- Filter media types by `frontend.media_support`
- Remove hardcoded: `if target == 'rocknix' and media == 'manual'`
- Apply device media sizing (future: after media transcoder built)

---

## Phase 4: Validation & Polish

### 4.1 Build Validation

**File:** `src/romfarmer/validation.py` (new)

- `validate_build(build_config) -> list[ValidationError]`
- Check target exists
- Check frontend exists  
- Check device exists
- Check all platforms supported
- Estimate storage usage vs budget

### 4.2 CLI Updates

**File:** `src/romfarmer/cli/build.py`

- Add `--validate-only` improvements (show target details)
- Add `--list-targets` command
- Add `--list-frontends` command
- Add `--list-devices` command

### 4.3 Migrate Existing Builds

- Update existing build configs to new format
- Remove old inline target definitions from platform configs
- Remove `platform_folder_map` from build configs
- Clean up or archive old configs

---

## Implementation Order

### Session 1: Foundation
1. ✅ Architecture document (done)
2. Create Pydantic schemas (frontend, device, target)
3. Create initial config files (batocera, rocknix, pc, r36s)
4. Create config loaders
5. Write unit tests for loaders

### Session 2: Build Integration  
1. Update build schema
2. Create composed target resolver
3. Update build context
4. Implement output folder computation
5. Test with `--validate-only`

### Session 3: Stage Integration
1. Update compress stage (use frontend.platforms)
2. Update organize stage (use frontend.folder_mapping)
3. Update metadata stage (use frontend.media_support)
4. Remove hardcoded checks
5. End-to-end test with real build

### Session 4: Polish & Migration
1. Implement full validation
2. Add CLI commands
3. Migrate existing build configs
4. Update documentation
5. Archive old configs

---

## Files to Create

| File | Purpose |
|------|---------|
| `src/romfarmer/schemas/frontend.py` | Frontend Pydantic models |
| `src/romfarmer/schemas/device.py` | Device Pydantic models |
| `src/romfarmer/schemas/target.py` | Target Pydantic models |
| `src/romfarmer/config/target_loader.py` | Load and compose targets |
| `src/romfarmer/validation.py` | Build validation |
| `config/frontends/batocera.yaml` | Batocera frontend config |
| `config/frontends/rocknix.yaml` | RocknIX frontend config |
| `config/devices/pc.yaml` | PC device config |
| `config/devices/steamdeck.yaml` | Steam Deck device config |
| `config/devices/r36s.yaml` | R36S device config |
| `config/targets/batocera-pc.yaml` | Batocera PC target |
| `config/targets/batocera-steamdeck.yaml` | Batocera Steam Deck target |
| `config/targets/rocknix-r36s.yaml` | RocknIX R36S target |

## Files to Modify

| File | Changes |
|------|---------|
| `src/romfarmer/schemas/build.py` | Add type, storage_budget, profile |
| `src/romfarmer/context.py` | Add composed_target, frontend, device |
| `src/romfarmer/stages/compress.py` | Use frontend.platforms for compression |
| `src/romfarmer/stages/organize.py` | Use frontend.folder_mapping |
| `src/romfarmer/stages/metadata.py` | Use frontend.media_support |
| `src/romfarmer/cli/build.py` | Add new commands |

## Files to Delete/Archive

| File | Action |
|------|--------|
| Inline targets in platform configs | Remove after migration |
| `platform_folder_map` in builds | Remove after migration |
| Old test build configs | Archive to `config/builds/archive/` |

---

## Risk Mitigation

### Risk: Breaking existing builds
**Mitigation:** Don't delete old configs until new system is fully tested. Keep both systems working during transition.

### Risk: Missing platform formats
**Mitigation:** Start with known platforms (from current builds), add more as needed. Validation will catch missing configs.

### Risk: Scope creep (media transcoding, etc.)
**Mitigation:** Media sizing in device config is for FUTURE use. Don't implement transcoding in this phase.

---

## Success Criteria

1. ✓ Can define new frontends without code changes
2. ✓ Can define new devices without code changes
3. ✓ Target = Frontend + Device composition works
4. ✓ Build validation catches unsupported platforms
5. ✓ Output folders follow `{frontend}-{device}-{storage}-{profile}/` pattern
6. ✓ No more hardcoded `if target == 'rocknix'` checks
7. ✓ Existing functionality preserved (same ROMs in output)

---

## Out of Scope (Future Work)

- Media transcoding/optimization
- Storage estimation
- Automatic platform performance testing
- Multi-target builds (single build → multiple targets)
- GUI for config editing
