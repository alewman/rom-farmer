# Content-Addressable Store (CAS) Design for ROM Farmer

**Date:** February 5, 2026  
**Status:** Design Proposal  
**Authors:** Human + AI collaborative design

---

## Overview

Replace the current directory-based output system with a **Content-Addressable Store** where every build artifact is stored by its content hash. Builds become lightweight manifest files that map human-readable paths to hash references. Deployments (Batocera share, external drives) are materialized as hard links from the CAS.

This enables unlimited build configurations with near-zero additional disk cost.

---

## Architecture

```
                     ┌──────────────────────────────┐
                     │     Source Files (51TB)       │
                     │  /data/emu/source/            │
                     │  Immutable inputs (Myrient,   │
                     │  Archive.org, No-Intro, etc.) │
                     └──────────────┬───────────────┘
                                    │
                          Pipeline Config (YAML)
                          defines transformations
                                    │
                                    ▼
                     ┌──────────────────────────────┐
                     │   Content-Addressable Store   │
                     │  /data/emu/rom-farmer/cas/    │
                     │                               │
                     │  ab/ab3def4567890abc...chd    │
                     │  cd/cdef123456789012...7z     │
                     │  ef/ef9876543210fedc...rvz    │
                     │                               │
                     │  (Hash-addressed blobs,       │
                     │   one copy per unique file)   │
                     └──────┬──────────┬─────────────┘
                            │          │
              Manifest A    │          │    Manifest B
           (4tb-nuc.json)   │          │  (512gb-handheld.json)
                            │          │
                            ▼          ▼
               ┌─────────────┐   ┌─────────────┐
               │  Deployment  │   │  Deployment  │
               │  (NUC share) │   │  (SD card)   │
               │  Hard links  │   │  rsync copy  │
               └─────────────┘   └─────────────┘
```

---

## Components

### 1. CAS Store

**Location:** `/data/emu/rom-farmer/cas/`

**Structure:** Git-style sharded by first 2 hex chars of hash:

```
cas/
├── 00/
│   ├── 00a1b2c3d4e5f6...chd
│   └── 009f8e7d6c5b4a...7z
├── 01/
│   └── 01fedcba987654...chd
├── ...
└── ff/
    └── ff1234567890ab...rvz
```

**File naming:** `{md5_hash}.{extension}`

The extension is preserved for two reasons:
- Emulators/Batocera may need it for file type detection
- Human debugging (you can see it's a CHD at a glance)

**Why MD5?** ROM Farmer already uses MD5 throughout:
- DAT files use MD5 for verification
- ScreenScraper uses MD5 for game lookup
- The `rom_transformations` table already stores source and output MD5 hashes
- No additional hashing needed — the pipeline already computes it

**Immutability:** Files in the CAS are write-once. Once a hash exists, it is never modified.
Set files to read-only after ingest: `chmod 444 cas/ab/ab3def...chd`

### 2. Manifests

**Location:** `/data/emu/rom-farmer/manifests/`

**Format:** JSON (fast to parse, easy to diff, version-controllable)

```json
{
  "name": "4tb-nuc-batocera",
  "created": "2026-02-05T14:30:00Z",
  "build_config": "config/builds/4tb-nuc-batocera.yaml",
  "description": "4TB NUC complete build - all tiers",
  "stats": {
    "total_files": 15234,
    "total_bytes": 3891234567890,
    "platforms": 45
  },
  "entries": {
    "saturn/Panzer Dragoon Saga (USA) (Disc 1).chd": {
      "hash": "ab3def4567890abcdef1234567890abc",
      "size": 412345678,
      "platform": "saturn"
    },
    "saturn/Panzer Dragoon Saga (USA) (Disc 2).chd": {
      "hash": "bc4ef05678901bcdef2345678901bcd",
      "size": 398765432,
      "platform": "saturn"
    },
    "saturn/Panzer Dragoon Saga (USA).m3u": {
      "hash": "cd5f016789012cdef3456789012cde",
      "size": 89,
      "platform": "saturn"
    },
    "nes/Legend of Zelda, The (USA) (Rev 1).7z": {
      "hash": "de6g127890123def4567890123def0",
      "size": 98765,
      "platform": "nes"
    }
  }
}
```

**Key properties:**
- A manifest is a **complete snapshot** — everything needed for a deployment
- Manifests are small (15K entries × ~150 bytes ≈ 2MB)
- Manifests can be diffed: "4tb-nuc v2 added 30 PS2 games, removed 5 sports titles"
- Manifests are version-controllable (commit to git)

**Manifest operations:**
- `manifest diff A B` — show what changed between two manifests
- `manifest merge A B` — combine two manifests (union)
- `manifest subtract A B` — everything in A that's not in B
- `manifest stats A` — size, platform breakdown, game counts

### 3. Deployments

A deployment materializes a manifest into a directory structure.

**Local deployment (hard links):**
```
deploy local 4tb-nuc-batocera --target /data/emu/share/roms-batocera/
```

Creates:
```
share/roms-batocera/
├── saturn/
│   ├── Panzer Dragoon Saga (USA) (Disc 1).chd  → hard link to cas/ab/ab3def...chd
│   ├── Panzer Dragoon Saga (USA) (Disc 2).chd  → hard link to cas/bc/bc4ef0...chd
│   ├── Panzer Dragoon Saga (USA).m3u            → hard link to cas/cd/cd5f01...m3u
│   └── ...
├── nes/
│   ├── Legend of Zelda, The (USA) (Rev 1).7z    → hard link to cas/de/de6g12...7z
│   └── ...
└── ...
```

**Remote deployment (rsync/copy):**
```
deploy remote 512gb-handheld --target /media/sdcard/roms/
```

Uses rsync with `--link-dest` or straight copy for cross-filesystem targets.

**Deployment state file:** Each deployment directory gets a `.rom-farmer-deploy.json`:
```json
{
  "manifest": "4tb-nuc-batocera",
  "manifest_hash": "abc123...",
  "deployed_at": "2026-02-05T15:00:00Z",
  "deployment_type": "hardlink",
  "cas_path": "/data/emu/rom-farmer/cas",
  "file_count": 15234
}
```

This enables:
- `deploy update` — diff current deployment vs latest manifest, add/remove links
- `deploy verify` — check all hard links still resolve and match expected hashes
- `deploy destroy` — remove all deployed hard links cleanly

### 4. Metadata Overlay

Metadata (gamelist.xml, media files) is deployed alongside ROMs:

```
share/roms-batocera/saturn/
├── Panzer Dragoon Saga (USA) (Disc 1).chd   ← hard link from CAS
├── gamelist.xml                               ← generated from database
└── media/
    ├── image/
    │   └── Panzer Dragoon Saga-image.png      ← hard link from media CAS
    ├── video/
    │   └── Panzer Dragoon Saga-video.mp4      ← hard link from media CAS
    └── ...
```

The media files already use a CAS-like system in the metadata database. This unifies both systems:
- ROM artifacts → `cas/`
- Media artifacts → `metadata/media/` (existing content-addressed store)
- Both are deployed as hard links by the same deploy command

---

## Lifecycle

### Ingest (Build Pipeline → CAS)

The build pipeline's final stage changes from "copy to output directory" to "ingest into CAS":

```python
def ingest_to_cas(file_path: Path, cas_root: Path) -> str:
    """Move a built artifact into the CAS. Returns the hash."""
    md5 = calculate_md5(file_path)
    shard = md5[:2]
    extension = file_path.suffix
    cas_path = cas_root / shard / f"{md5}{extension}"
    
    if cas_path.exists():
        # Already in CAS (dedup!) — verify and discard
        assert calculate_md5(cas_path) == md5, "Hash collision!"
        file_path.unlink()
        return md5
    
    # New artifact — move into CAS
    cas_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(file_path), str(cas_path))
    cas_path.chmod(0o444)  # Read-only, immutable
    return md5
```

### Build (Config → Manifest)

A build run produces a manifest instead of a directory tree:

```python
def build_manifest(build_config: BuildConfig) -> Manifest:
    """Run pipeline, ingest artifacts, produce manifest."""
    manifest = Manifest(name=build_config.name)
    
    for platform in build_config.platforms:
        for game_file in run_pipeline(platform):
            hash = ingest_to_cas(game_file.path, CAS_ROOT)
            manifest.add(
                path=f"{platform.name}/{game_file.name}",
                hash=hash,
                size=game_file.size,
                platform=platform.name
            )
    
    manifest.save(MANIFEST_DIR / f"{build_config.name}.json")
    return manifest
```

### Deploy (Manifest → Hard Links)

```python
def deploy_local(manifest: Manifest, target: Path, cas_root: Path):
    """Materialize a manifest as hard links."""
    for entry_path, entry in manifest.entries.items():
        source = cas_root / entry.hash[:2] / f"{entry.hash}{Path(entry_path).suffix}"
        dest = target / entry_path
        
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        if dest.exists():
            # Check if already correct hard link
            if os.path.samefile(source, dest):
                continue  # Already deployed
            dest.unlink()  # Wrong file, remove
        
        os.link(str(source), str(dest))
    
    # Clean up files in target not in manifest
    for existing_file in walk_files(target):
        rel_path = existing_file.relative_to(target)
        if str(rel_path) not in manifest.entries:
            existing_file.unlink()  # Orphan, remove
```

### Update (Manifest Diff → Incremental Deploy)

```python
def deploy_update(old_manifest: Manifest, new_manifest: Manifest, target: Path):
    """Incremental update — only add/remove changed files."""
    added = set(new_manifest.entries) - set(old_manifest.entries)
    removed = set(old_manifest.entries) - set(new_manifest.entries)
    changed = {k for k in set(new_manifest.entries) & set(old_manifest.entries)
               if new_manifest.entries[k].hash != old_manifest.entries[k].hash}
    
    for path in removed:
        (target / path).unlink()
    
    for path in added | changed:
        deploy_single(new_manifest.entries[path], target, CAS_ROOT)
    
    print(f"Added: {len(added)}, Removed: {len(removed)}, Changed: {len(changed)}")
```

### Garbage Collection

CAS files with no manifest references can be cleaned up:

```python
def gc(cas_root: Path, manifest_dir: Path):
    """Remove CAS files not referenced by any manifest."""
    # Collect all hashes referenced by any manifest
    referenced = set()
    for manifest_file in manifest_dir.glob("*.json"):
        manifest = Manifest.load(manifest_file)
        for entry in manifest.entries.values():
            referenced.add(entry.hash)
    
    # Walk CAS and find orphans
    orphans = []
    for cas_file in walk_cas(cas_root):
        hash = cas_file.stem
        if hash not in referenced:
            orphans.append(cas_file)
    
    print(f"Found {len(orphans)} orphaned files ({sum_size(orphans)} bytes)")
    # Optionally delete or move to trash
```

---

## Migration Path

### Phase 1: Build CAS from Existing Output (one-time)

The 16TB of existing output can be migrated incrementally:

```bash
# For each platform in each build output:
romfarmer cas ingest output/1g1r-eng-chd-batocera/saturn/ --platform saturn

# This:
# 1. Hashes each file (or uses known hash from rom_transformations table)
# 2. Hard-links into CAS (no copy needed if same filesystem!)
# 3. Records in manifest
```

**Critical optimization:** Use existing hashes from `rom_transformations` table instead of re-hashing 16TB. The pipeline already computed MD5 for every file during the compress/verify stages.

**Migration is non-destructive:** Since we hard-link (not move) during migration, the old output directories remain intact. They just happen to share inodes with the CAS. Once migration is verified, old output dirs can be deleted (the CAS hard links keep the files alive).

### Phase 2: Pipeline Outputs to CAS

Modify the pipeline's copy/output stage to ingest into CAS instead of writing to output directories.

### Phase 3: Deploy from Manifests

Implement the deploy command and rebuild the Batocera share from a manifest.

---

## Space Analysis

### Current (directory-based)

```
output/1g1r-eng-chd-batocera/saturn/Game.chd     (File A, inode 1001)
output/1g1r-eng-raw-batocera/saturn/Game.bin      (File B, inode 1002)  ← different format, different file
share/roms-batocera/saturn/Game.chd               (File C, inode 1003)  ← COPY of A, wastes space!
```

If the same CHD appears in two builds, it exists twice: **2× disk usage**.

### Proposed (CAS-based)

```
cas/ab/ab3def...chd                               (File A, inode 1001)
share/roms-batocera/saturn/Game.chd               (hard link, inode 1001)  ← same inode, 0 extra bytes
share/roms-handheld/saturn/Game.chd               (hard link, inode 1001)  ← same inode, 0 extra bytes
```

Three "copies" of the same CHD but only **1× disk usage**.

### Estimated Savings

| Scenario | Current | With CAS | Savings |
|---|---|---|---|
| CHD output + raw output (same games, different formats) | 8.4 TB | 8.4 TB | 0 (different content) |
| CHD output + Batocera share (same files, copies) | 4.1 TB + 4 TB copy | 4.1 TB + 0 | ~4 TB |
| NUC build + handheld build (overlapping games) | 4 TB + 1 TB | 4 TB + 0 | ~1 TB |
| Multiple build variants over time | Grows linearly | Grows only for unique new artifacts | Significant |

**Key insight:** The savings aren't primarily from dedup of identical files (though that's nice). The real win is that **deployments are free** — creating a new build view costs only the manifest file (2MB), not TB of copies.

---

## Comparison with Alternatives

### Alternative A: Symlinks Instead of Hard Links

| Aspect | Hard Links | Symlinks |
|---|---|---|
| Works across filesystems | ❌ No | ✅ Yes |
| Survives source rename/move | ✅ Yes (same inode) | ❌ No (broken link) |
| Emulator compatibility | ✅ Transparent | ⚠️ Some emulators don't follow |
| Batocera compatibility | ✅ Native file | ⚠️ May not resolve over network |
| Disk usage reporting | ⚠️ Shows full size per link | ✅ Shows link size only |
| Deletion safety | ✅ CAS file survives until all links gone | ❌ Deleting source breaks all links |

**Verdict:** Hard links are correct for same-filesystem deployments (Batocera NUC). Symlinks are fallback for cross-filesystem (external drives).

### Alternative B: Simple Output Directory + Hard Links (my Gap 2 proposal)

| Aspect | Simple Link | CAS |
|---|---|---|
| Complexity | Low | Medium |
| Multi-build support | Poor (tied to directory structure) | Excellent |
| Dedup across builds | None | Automatic |
| Integrity verification | None | Hash-based |
| Manifest diffing | None | Built-in |
| Migration effort | Easy | Medium (one-time) |
| Long-term flexibility | Limited | Excellent |

**Verdict:** CAS is more work upfront but strictly superior for a project managing terabytes across multiple build targets.

### Alternative C: ZFS/Btrfs Dedup

| Aspect | Filesystem Dedup | CAS |
|---|---|---|
| Requires specific filesystem | ✅ Yes (ZFS/Btrfs) | ❌ No (works on ext4) |
| Dedup granularity | Block-level | File-level |
| Explicit control | No (background process) | Yes (manifests) |
| Cross-system deployment | No | Yes (rsync manifests) |
| Build reproducibility | No (just saves space) | Yes (manifests are snapshots) |

**Verdict:** Filesystem dedup is complementary but doesn't solve the manifest/deployment problem. CAS gives you both dedup AND build management.

---

## Database Integration

### Existing Tables (already in romfarmer.db)

The `rom_transformations` table already tracks:
```sql
source_hash  →  output_hash  →  compression_ratio  →  tool_version  →  timing
```

This means:
1. **No re-hashing needed during migration** — query `rom_transformations` for output hashes
2. **CAS lookups are instant** — "do we have this game as CHD?" → check if hash exists in CAS
3. **Compression prediction improves** — CAS provides ground truth for ratio calculations

### New Table: `cas_entries`

```sql
CREATE TABLE cas_entries (
    hash TEXT PRIMARY KEY,          -- MD5 hash (content address)
    extension TEXT NOT NULL,        -- .chd, .7z, .rvz, .m3u, etc.
    size INTEGER NOT NULL,          -- File size in bytes
    platform TEXT,                  -- Platform name (for quick queries)
    cas_path TEXT NOT NULL,         -- Relative path within CAS (ab/ab3def...chd)
    ingested_at TIMESTAMP,          -- When added to CAS
    source_hash TEXT,               -- Original source file hash (for provenance)
    transform_config TEXT,          -- Compression/format config used
    verified_at TIMESTAMP           -- Last integrity verification
);
```

### New Table: `manifests`

```sql
CREATE TABLE manifests (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,      -- e.g., "4tb-nuc-batocera"
    build_config TEXT,              -- Path to build YAML
    created_at TIMESTAMP,
    total_files INTEGER,
    total_bytes INTEGER,
    manifest_path TEXT              -- Path to JSON manifest file
);
```

### New Table: `manifest_entries`

```sql
CREATE TABLE manifest_entries (
    manifest_id INTEGER REFERENCES manifests(id),
    display_path TEXT NOT NULL,     -- e.g., "saturn/Panzer Dragoon Saga (Disc 1).chd"
    cas_hash TEXT REFERENCES cas_entries(hash),
    platform TEXT,
    PRIMARY KEY (manifest_id, display_path)
);
```

This enables queries like:
- "Which manifests include this game?" → find all builds containing a specific hash
- "What's different between two manifests?" → JOIN and compare
- "How much unique data does this manifest add?" → hashes not in any other manifest
- "What's the total unique storage?" → COUNT(DISTINCT hash) from all manifest_entries

---

## CLI Commands

```bash
# === CAS Management ===
romfarmer cas status                          # Show CAS stats (total files, size, health)
romfarmer cas ingest <path> --platform <p>    # Add files to CAS
romfarmer cas verify [--fix]                  # Verify all CAS hashes, optionally fix
romfarmer cas gc [--dry-run]                  # Garbage collect unreferenced files

# === Manifest Management ===
romfarmer manifest list                       # List all manifests with stats
romfarmer manifest create <name> --from-build <config>   # Build + create manifest
romfarmer manifest create <name> --from-dir <path>       # Create from existing directory
romfarmer manifest diff <a> <b>               # Show differences between manifests
romfarmer manifest stats <name>               # Detailed stats (platforms, sizes, genres)
romfarmer manifest merge <a> <b> --output <c> # Combine two manifests

# === Deployment ===
romfarmer deploy <manifest> --target <path>   # Deploy manifest as hard links
romfarmer deploy <manifest> --target <path> --method copy  # Deploy as copies (cross-fs)
romfarmer deploy update <manifest> --target <path>         # Incremental update
romfarmer deploy verify --target <path>       # Verify deployment integrity
romfarmer deploy destroy --target <path>      # Remove all deployed files
romfarmer deploy status --target <path>       # Show what's deployed

# === Build (modified to output manifests) ===
romfarmer build run <config>                  # Run build → ingest to CAS → create manifest
romfarmer build run <config> --manifest-only  # Just create manifest from existing CAS
```

---

## Implementation Phases

### Phase 1: CAS Core + Migration (Week 1-2)

1. Create `src/romfarmer/cas/` module:
   - `store.py` — CAS operations (ingest, lookup, verify, gc)
   - `manifest.py` — Manifest operations (create, diff, merge, load/save)
   - `deploy.py` — Deployment operations (deploy, update, verify, destroy)
   - `models.py` — Pydantic models for manifest entries

2. Migrate existing output to CAS:
   - Use `rom_transformations` table for known hashes (avoid re-hashing)
   - Hard-link (not copy) from output dirs to CAS — non-destructive
   - Create manifests for each existing build output

3. Add `cas_entries`, `manifests`, `manifest_entries` tables to database

### Phase 2: Pipeline Integration (Week 2-3)

1. Modify pipeline's final stage to ingest into CAS
2. Build command produces manifest as output
3. Remove "output directory" concept — builds go directly to CAS + manifest

### Phase 3: Deploy Command (Week 3-4)

1. Implement `romfarmer deploy` with hard link support
2. Metadata overlay (gamelist.xml + media hard links)
3. Deploy state tracking and incremental updates
4. Rebuild Batocera share from manifest

### Phase 4: MCP Integration (Week 4+)

1. Expose CAS operations as MCP tools in zelda-mcp
2. "Create a 4TB build with the best Saturn and PS1 games" → manifest → deploy
3. Collection scoring operates on manifests
4. "What would this build look like?" → manifest preview without deployment

---

## Open Questions

1. **Hash algorithm:** MD5 is already used throughout. SHA-256 is more robust but slower and longer filenames. **Recommendation: stick with MD5** — collision risk is negligible for ROM files and consistency with existing DAT/scraper infrastructure matters more.

2. **CAS location:** Same filesystem as source and share is required for hard links. `/data/emu/rom-farmer/cas/` keeps it within the project. Alternative: `/data/emu/cas/` as a top-level peer. **Recommendation: `/data/emu/rom-farmer/cas/`** — keeps it under project management.

3. **M3U files:** M3U playlists are tiny text files generated during the build. Should they go in CAS? **Recommendation: Yes** — they're build artifacts too, and having them in manifests means deployments are complete without extra generation steps.

4. **Gamelist.xml:** These are generated per-platform and change when metadata is updated. Should they go in CAS? **Recommendation: No** — generate them at deploy time from the database. They're not transformations, they're views of metadata.

5. **Maximum CAS size:** With all platforms in all formats, the CAS could grow very large. **Recommendation: GC policy** — keep only artifacts referenced by at least one manifest. Delete old builds' manifests to trigger GC of their unique artifacts.

---

*This design transforms ROM Farmer from a "build and copy" system into a "build once, deploy anywhere" system. The CAS is the single source of truth for all artifacts, and manifests are the single source of truth for all builds.*
