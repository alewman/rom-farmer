# PS3 Target Formats & ps3netsrv Support

**Date:** October 13, 2025  
**Status:** Implementation Planning

## Overview

PS3 games can be used in multiple ways, and we need to support various target formats:
1. **RPCS3 emulator** (PC/Batocera) - Folder format preferred
2. **Real PS3 (ps3netsrv)** - Network streaming to jailbroken PS3
3. **Real PS3 (local storage)** - Direct CFW installation

---

## ps3netsrv - Network Game Server

### What is ps3netsrv?

**ps3netsrv** is a network server that streams PS3 games to a jailbroken PS3 console over the network. The PS3 connects to the server and mounts games as if they were on local storage.

### Supported Formats

ps3netsrv supports multiple game formats:

1. **ISO format** (.iso) - Decrypted PS3 disc images
   - Most compatible
   - Can be played directly
   - Large file size (~6-50 GB per game)

2. **Folder format** (JB folders)
   - Game extracted to folder structure
   - `/GAMEID/PS3_GAME/` format
   - Same size as ISO when extracted
   - More flexible (can mix base game + updates)

3. **ISO.gz format** (.iso.gz) - Compressed decrypted ISOs
   - Gzipped ISO files
   - Saves storage space (~30-50% compression)
   - ps3netsrv decompresses on-the-fly
   - Slightly slower loading

### Directory Structure

Typical ps3netsrv directory layout:
```
/data/ps3netsrv/
├── GAMES/
│   ├── BLUS30455/                    # Folder format (Uncharted)
│   │   ├── PS3_GAME/
│   │   │   ├── PARAM.SFO
│   │   │   ├── EBOOT.BIN
│   │   │   └── USRDIR/
│   │   └── PS3_UPDATE/              # Optional update
│   ├── God of War III.iso           # ISO format
│   └── The Last of Us.iso.gz        # Compressed ISO
└── PACKAGES/                         # PKG files (updates/DLC)
    ├── BLUS30455-update.pkg
    └── BLUS30455-dlc01.pkg
```

### Advantages by Format

| Format | Pros | Cons |
|--------|------|------|
| **ISO** | Fast loading, widely compatible | Large size, no updates |
| **Folder** | Can add updates, flexible | Takes disk space, many files |
| **ISO.gz** | Space-efficient (~50% savings) | Slightly slower decompression |

---

## Target Configuration Strategy

### Target 1: RPCS3 (Emulator)

**Best format:** Folder structure

```yaml
targets:
  - name: "rpcs3"
    output_path: /path/to/output/rpcs3/ps3
    format: "folder"           # Extract to PS3_GAME folder
    compression: false          # No compression for emulator
    organization:
      style: rich              # Per-letter directories
    metadata: true
    enabled: true
```

**Pipeline:**
```
ZIP → ISO → decrypt → extract → folder
```

### Target 2: ps3netsrv (Real PS3 Network)

**Best format:** ISO.gz (balanced size/performance)

```yaml
targets:
  - name: "ps3netsrv"
    output_path: /data/ps3netsrv/GAMES
    format: "iso"              # Decrypted ISO
    compression: "gzip"        # .iso.gz for space savings
    compression_level: 6       # Balanced (1=fast, 9=best)
    organization:
      style: minimal           # Flat directory
      create_subdirs: false    # All in /GAMES/
    metadata: false            # PS3 reads from PARAM.SFO
    enabled: true
```

**Pipeline:**
```
ZIP → ISO → decrypt → compress (gzip) → .iso.gz
```

**Alternative (folder format):**
```yaml
targets:
  - name: "ps3netsrv-folder"
    output_path: /data/ps3netsrv/GAMES
    format: "folder"           # JB folder format
    compression: false         # Folders aren't compressed
    organization:
      style: minimal
    enabled: false
```

### Target 3: Real PS3 Local (CFW)

**Best format:** Folder (for multiman/webman)

```yaml
targets:
  - name: "ps3-cfw"
    output_path: /path/to/output/ps3-cfw
    format: "folder"           # JB folder format
    compression: false
    organization:
      style: minimal
      create_subdirs: false
    metadata: false
    enabled: false
```

---

## Implementation: TransformPS3Stage

### Multi-Target Support

The stage needs to handle different output formats based on target config:

```python
class TransformPS3Stage(Stage):
    """Transform PS3 ISOs for various targets.
    
    Supports multiple output formats:
    - folder: Extracted PS3_GAME structure (RPCS3, CFW)
    - iso: Decrypted ISO (CFW, ps3netsrv)
    - iso.gz: Compressed decrypted ISO (ps3netsrv space-saving)
    """
    
    def _transform_ps3_game(
        self,
        zip_file: Path,
        target_format: str,
        target_compression: Optional[str],
        keys_dir: Path,
        temp_dir: Path,
        output_dir: Path,
    ) -> FileTransformation:
        """Transform PS3 game to target format."""
        
        transformation = FileTransformation(source_file=zip_file)
        
        # Step 1: Unzip encrypted ISO
        iso_path = self._unzip_iso(zip_file, temp_dir)
        transformation.add_step(...)
        
        # Step 2: Find disc key
        disc_key = self._find_disc_key(zip_file.stem, keys_dir)
        
        # Step 3: Decrypt ISO with PS3Dec
        dec_iso_path = self._decrypt_ps3_iso(iso_path, disc_key, temp_dir)
        transformation.add_step(...)
        
        # Step 4: Format-specific handling
        if target_format == "folder":
            # Extract for RPCS3 or CFW
            folder = self._extract_ps3_iso(dec_iso_path, output_dir)
            final_file = folder
            transformation.add_step(...)
            
        elif target_format == "iso":
            if target_compression == "gzip":
                # Compress for ps3netsrv
                gz_file = self._compress_gzip(dec_iso_path, output_dir)
                final_file = gz_file
                transformation.add_step(...)
            else:
                # Plain ISO
                final_file = output_dir / f"{zip_file.stem}.iso"
                shutil.move(dec_iso_path, final_file)
        
        # Step 5: Cleanup temps
        iso_path.unlink()
        if dec_iso_path.exists():
            dec_iso_path.unlink()
        
        transformation.final_file = final_file
        transformation.status = TransformStatus.SUCCESS
        return transformation
```

### Gzip Compression Method

```python
def _compress_gzip(self, iso_path: Path, output_dir: Path) -> Path:
    """Compress decrypted ISO to .iso.gz for ps3netsrv.
    
    Args:
        iso_path: Path to decrypted ISO
        output_dir: Output directory
        
    Returns:
        Path to .iso.gz file
    """
    import gzip
    import shutil
    
    gz_path = output_dir / f"{iso_path.stem}.iso.gz"
    
    with open(iso_path, 'rb') as f_in:
        with gzip.open(gz_path, 'wb', compresslevel=6) as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    return gz_path
```

### ISO Extraction Method (for folder format)

```python
def _extract_ps3_iso(self, iso_path: Path, output_dir: Path) -> Path:
    """Extract PS3 ISO to folder structure.
    
    Creates JB folder format:
    GAMEID/
        PS3_GAME/
            PARAM.SFO
            EBOOT.BIN
            USRDIR/
    
    Args:
        iso_path: Path to decrypted ISO
        output_dir: Output directory
        
    Returns:
        Path to game folder
    """
    import subprocess
    
    # Extract to temp location first
    temp_extract = output_dir / f"{iso_path.stem}_temp"
    temp_extract.mkdir(parents=True, exist_ok=True)
    
    # Use 7zip to extract ISO
    cmd = ["7z", "x", str(iso_path), f"-o{temp_extract}", "-y"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"7zip extraction failed: {result.stderr}")
    
    # Find PS3_GAME directory
    ps3_game_dirs = list(temp_extract.rglob("PS3_GAME"))
    if not ps3_game_dirs:
        raise RuntimeError("No PS3_GAME directory found in ISO")
    
    ps3_game_dir = ps3_game_dirs[0].parent
    
    # Read PARAM.SFO to get game ID
    param_sfo = ps3_game_dir / "PS3_GAME" / "PARAM.SFO"
    if param_sfo.exists():
        game_id = self._read_game_id_from_param_sfo(param_sfo)
    else:
        # Fallback to filename
        game_id = iso_path.stem
    
    # Move to final location with game ID as folder name
    final_dir = output_dir / game_id
    if final_dir.exists():
        shutil.rmtree(final_dir)
    
    shutil.move(ps3_game_dir, final_dir)
    
    # Cleanup temp
    shutil.rmtree(temp_extract)
    
    return final_dir
```

---

## PS3 Platform Config (Multi-Target)

```yaml
# Sony PlayStation 3 Platform Configuration

name: ps3
system_type: very_complex

# DAT Configuration
dat:
  source: retool_1g1r_usa
  expected_count: 1200

# Source ROMs (Myrient)
sources:
  - path: /path/to/... - PlayStation 3
    type: myrient
    recursive: false

# Decryption keys
decryption:
  enabled: true
  disc_keys_dir: /path/to/... - PlayStation 3 - Disc Keys TXT
  key_format: "dkey"    # 32-char hex in .dkey files

# List Files
lists:
  directory: /path/to/...
  patterns:
    delete: "ps3-delete"
    add_myrient: "ps3+*"
    add_extra: "ps3.*"

# Archive extraction
extract_archives: true

# Targets - Multiple formats!
targets:
  # Target 1: RPCS3 Emulator (folder format)
  - name: "rpcs3"
    output_path: /path/to/output/rpcs3/ps3
    format: "folder"
    compression: false
    organization:
      style: rich
      create_subdirs: true
      subdir_prefix: "_"
    metadata: true
    enabled: true

  # Target 2: ps3netsrv (compressed ISO)
  - name: "ps3netsrv"
    output_path: /data/ps3netsrv/GAMES
    format: "iso"
    compression: "gzip"
    compression_level: 6
    organization:
      style: minimal
      create_subdirs: false
    metadata: false
    enabled: true

  # Target 3: Real PS3 CFW (folder format)
  - name: "ps3-cfw"
    output_path: /path/to/output/ps3-cfw
    format: "folder"
    compression: false
    organization:
      style: minimal
      create_subdirs: false
    metadata: false
    enabled: false

enabled: true
```

---

## Storage Impact Comparison

**Example game: Uncharted 3 (40 GB)**

| Target | Format | Size | Notes |
|--------|--------|------|-------|
| Source | ZIP (encrypted ISO) | 38 GB | Original Myrient |
| RPCS3 | Folder (extracted) | 40 GB | Full extraction |
| ps3netsrv | ISO.gz | 20 GB | ~50% compression |
| ps3netsrv | ISO | 40 GB | No compression |
| ps3-cfw | Folder | 40 GB | Same as RPCS3 |

**For 100 game collection (avg 20 GB):**
- Source ZIPs: 1.9 TB
- RPCS3 folders: 2.0 TB
- ps3netsrv (.iso.gz): 1.0 TB ✅ (best space savings!)
- ps3netsrv (.iso): 2.0 TB

**ps3netsrv with .iso.gz is the most space-efficient for real PS3!**

---

## PKG File Support (Future)

Your PKG files can be integrated later:

**Use cases:**
1. **Game updates** - Apply patches to base games
2. **DLC content** - Add downloadable content
3. **Digital-only games** - Some games only available as PKG

**Integration points:**
- RPCS3: Install PKG files via CLI
- ps3netsrv: Copy PKG to PACKAGES/ directory
- PS3 CFW: Install via package manager

**Future enhancement:**
```python
class InstallPKGStage(Stage):
    """Install PKG files (updates/DLC) to base games."""
    
    def execute(self, context):
        # Find matching PKG files for installed games
        # Extract or install PKG content
        # Merge with base game
        pass
```

---

## Demo Script: demo_ps3.py

Will test all three targets:

```python
# Test 1: Single small game → RPCS3 folder
# Test 2: Same game → ps3netsrv .iso.gz
# Test 3: Compare sizes and verify formats
```

---

## Implementation Order

1. ✅ **Basic decryption** - Get PS3Dec working
2. ✅ **ISO extraction** - Extract to folder (7zip)
3. ✅ **RPCS3 target** - Folder format first
4. ⬜ **ps3netsrv target** - Add .iso.gz compression
5. ⬜ **Demo all targets** - Verify each format works
6. ⬜ **PKG support** - Add update/DLC handling (Phase 6)

---

## ps3netsrv Network Setup Notes

**For reference when setting up ps3netsrv:**

### Server Side
```bash
# Install ps3netsrv
sudo apt-get install ps3netsrv

# Or compile from source
git clone https://github.com/aldostools/webMAN-MOD.git
cd webMAN-MOD/_Projects_/ps3netsrv
make

# Run server
ps3netsrv /data/ps3netsrv/GAMES 38008
```

### PS3 Client Side
1. Install webMAN MOD or multiMAN on CFW PS3
2. Enable network client in settings
3. Add server IP and port (38008)
4. Games appear in XMB automatically

### File Naming
- ISO files: Can use any name (appears in XMB)
- Folder games: Use Game ID as folder name (BLUS30455, etc.)
- .iso.gz: Same as ISO, server decompresses automatically

---

## Summary

**Key Decisions:**
1. ✅ Support multiple targets with different formats
2. ✅ ps3netsrv best format: .iso.gz (50% space savings)
3. ✅ RPCS3 best format: folder (emulator preferred)
4. ✅ Use gzip compression for ps3netsrv ISOs
5. ✅ PKG files integrated in future phase

**Next Steps:**
1. Implement TransformPS3Stage with multi-format support
2. Add gzip compression method
3. Test with small PS3 game
4. Create demo showing all three targets
5. Validate on real PS3 with ps3netsrv

**This gives you maximum flexibility: emulation on PC AND real PS3 network streaming!** 🎮
