# Phase 5 Implementation Roadmap

**Date:** October 13, 2025  
**Status:** Ready to Begin

Based on actual format discoveries and Batocera/Retrobat support validation.

---

## Overview

Phase 5 implements complex system transformations for disc-based platforms that require multi-step processing (decryption, format conversion, compression).

**Key Insight:** Start with easy wins, build momentum, tackle complex systems with knowledge gained.

---

## System Priorities (Revised)

### Tier 1: Must Implement ✅

| System | Difficulty | Time Estimate | Why |
|--------|-----------|---------------|-----|
| **Wii** | 🟢 Easy | 1-2 days | Just unzip RVZ - no transform! |
| **GameCube** | 🟢 Easy | 1-2 days | Just unzip RVZ - no transform! |
| **PS3** | 🟡 Medium | 1 week | Decrypt + extract, have tools |

### Tier 2: Should Implement 🎯

| System | Difficulty | Time Estimate | Why |
|--------|-----------|---------------|-----|
| **Wii U** | 🟠 Hard | 1-2 weeks | WUA format! Batocera confirmed ✅ |

### Tier 3: Future/Optional 🔵

| System | Difficulty | Status | Notes |
|--------|-----------|--------|-------|
| Xbox 360 | Hard | Deferred | Xenia not in Batocera/Retrobat |
| Switch | Medium | Future | Yuzu/Ryujinx support exists |
| 3DS | Medium | Future | Citra support exists |

---

## Phase 5A: Wii & GameCube (QUICK WIN!)

**Timeline:** 1-2 days  
**Difficulty:** 🟢 Easy  
**Status:** 🎯 START HERE

### Why Start Here?

1. ✅ **Instant gratification** - Simplest possible transform
2. ✅ **Validates pipeline** - Tests Stage infrastructure with real files
3. ✅ **Builds confidence** - Success before tackling harder systems
4. ✅ **Large library** - Wii has 2000+ games, GameCube 1000+

### What We Need

**Input:** Myrient ZIPs containing RVZ files  
**Output:** Extracted RVZ files  
**Transform:** Just unzip! 🎉

### Implementation

```python
class UnzipRVZStage(Stage):
    """Extract RVZ files from Myrient archives.
    
    For Wii and GameCube, the RVZ format is Dolphin's native
    compressed format. No further transformation is needed!
    """
    
    def __init__(self):
        super().__init__("Unzip RVZ")
    
    def execute(self, context: StageContext) -> StageResult:
        import zipfile
        from pathlib import Path
        
        self._log_info(context, "Extracting RVZ files from archives...")
        
        extracted = []
        for zip_file in context.matched_files:
            try:
                # Extract to work directory
                extract_dir = context.work_dir / zip_file.stem
                extract_dir.mkdir(parents=True, exist_ok=True)
                
                with zipfile.ZipFile(zip_file, 'r') as zf:
                    # Extract only .rvz files
                    rvz_files = [f for f in zf.namelist() if f.endswith('.rvz')]
                    
                    for rvz_file in rvz_files:
                        zf.extract(rvz_file, extract_dir)
                        extracted_path = extract_dir / rvz_file
                        extracted.append(extracted_path)
                        
                        self._log_info(
                            context,
                            f"Extracted: {rvz_file} ({extracted_path.stat().st_size / 1e9:.1f} GB)"
                        )
            
            except Exception as e:
                self._log_error(context, f"Failed to extract {zip_file.name}: {e}")
                continue
        
        # Update context
        context.extracted_files = extracted
        
        return StageResult(
            status=StageStatus.SUCCESS,
            message=f"Extracted {len(extracted)} RVZ files",
            files_processed=len(context.matched_files),
        )
```

### Configuration

**Wii Config (`config/platforms/wii.yaml`):**
```yaml
platform:
  name: "wii"
  system_type: "large"
  
source:
  type: "myrient"
  path: "/data/emu/archive/archive.myrient.erista.me/files/Redump/Nintendo - Wii - NKit RVZ [zstd-19-128k]"
  pattern: "*.zip"
  
dat:
  type: "retool"
  path: "/data/emu/dats/redump.retool.1g1r.usa/Nintendo - Wii.dat"
  
processing:
  extract_archives: true
  format: "rvz"  # Keep RVZ format
  compress: false  # Already compressed!
  
targets:
  - name: "rocknix"
    style: "balanced"
  - name: "batocera"
    style: "rich"
```

**GameCube Config (`config/platforms/gamecube.yaml`):**
```yaml
platform:
  name: "gamecube"
  system_type: "large"
  
# Same structure as Wii
source:
  path: "/data/emu/archive/archive.myrient.erista.me/files/Redump/Nintendo - GameCube - NKit RVZ [zstd-19-128k]"
  
dat:
  path: "/data/emu/dats/redump.retool.1g1r.usa/Nintendo - GameCube.dat"
```

### Pipeline

```python
# Wii/GameCube pipeline
pipeline = Pipeline(platform_config=wii_config, target_name="batocera", console=console)

pipeline.add_stage(FilterDATStage())      # Match against Retool DAT
pipeline.add_stage(ApplyListsStage())     # Apply delete/keep lists
pipeline.add_stage(UnzipRVZStage())       # Extract RVZ files ✅
pipeline.add_stage(OrganizeStage())       # Organize by target style

pipeline.execute(context)
```

**That's it!** 4 stages, RVZ files ready for Dolphin! ✅

### Testing

1. Select 10 Wii games (mixed sizes)
2. Run pipeline with DRY_RUN
3. Verify:
   - ZIP extraction works
   - RVZ files are valid
   - Organization works
   - Total time < 5 minutes

### Success Criteria

- ✅ Extract 100% of RVZ files successfully
- ✅ Maintain filename structure (region, revision, etc.)
- ✅ Organize according to target style
- ✅ No errors in Dolphin when loading
- ✅ Pipeline completes in reasonable time

---

## Phase 5B: PlayStation 3

**Timeline:** 1 week  
**Difficulty:** 🟡 Medium  
**Status:** After 5A

### What We Need

**Input:** Myrient ZIPs with encrypted ISOs + disc keys  
**Output:** Decrypted folders (RPCS3 format) OR decrypted ISOs  
**Transform:** Unzip → Decrypt → Extract

### Implementation

```python
class TransformPS3Stage(Stage):
    """Transform PS3 ISOs for RPCS3.
    
    Supports multiple output formats:
    - folder: Extract to PS3_GAME folder structure (RPCS3 preferred)
    - iso: Decrypted ISO file (also works in RPCS3)
    """
    
    def __init__(self):
        super().__init__("Transform PS3")
        self.ps3dec_path = self._find_ps3dec()
        
    def _find_ps3dec(self) -> Path:
        """Find PS3Dec binary."""
        candidates = [
            Path("/data/emu/bin/PS3Dec"),
            Path("/usr/local/bin/PS3Dec"),
            Path("/usr/bin/PS3Dec"),
        ]
        
        for path in candidates:
            if path.exists() and path.is_file():
                return path
        
        raise FileNotFoundError("PS3Dec not found! Install from /data/emu/bin/")
    
    def execute(self, context: StageContext) -> StageResult:
        """Transform all PS3 games."""
        import tempfile
        
        keys_dir = Path(context.platform_config.decryption.disc_keys)
        target_format = context.platform_config.get_target_format(context.target_name)
        
        transformations = []
        
        for zip_file in context.matched_files:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                try:
                    # Transform this game
                    transformation = self._transform_ps3_game(
                        zip_file=zip_file,
                        keys_dir=keys_dir,
                        temp_dir=temp_path,
                        target_format=target_format,
                        output_dir=context.work_dir,
                    )
                    
                    transformations.append(transformation)
                    
                    self._log_info(context, transformation.get_summary())
                    
                except Exception as e:
                    self._log_error(context, f"Failed {zip_file.name}: {e}")
                    continue
                
                # temp_dir auto-cleaned here!
        
        # Update context
        context.transformations = transformations
        
        successful = sum(1 for t in transformations if t.status == TransformStatus.SUCCESS)
        
        return StageResult(
            status=StageStatus.SUCCESS,
            message=f"Transformed {successful}/{len(transformations)} PS3 games",
            files_processed=len(context.matched_files),
        )
    
    def _transform_ps3_game(
        self,
        zip_file: Path,
        keys_dir: Path,
        temp_dir: Path,
        target_format: str,
        output_dir: Path,
    ) -> FileTransformation:
        """Transform single PS3 game through all steps."""
        import time
        
        transformation = FileTransformation(source_file=zip_file)
        transformation.status = TransformStatus.IN_PROGRESS
        
        # Step 1: Unzip ISO
        start = time.time()
        iso_path = self._unzip_iso(zip_file, temp_dir)
        transformation.add_step(TransformStep(
            step_type=TransformType.UNZIP,
            input_file=zip_file,
            output_file=iso_path,
            tool="zipfile",
            status=TransformStatus.SUCCESS,
            duration_seconds=time.time() - start,
        ))
        
        # Step 2: Find disc key
        start = time.time()
        disc_key = self._find_disc_key(zip_file.stem, keys_dir)
        
        # Step 3: Decrypt with PS3Dec
        start = time.time()
        dec_iso_path = self._decrypt_ps3_iso(iso_path, disc_key, temp_dir)
        transformation.add_step(TransformStep(
            step_type=TransformType.DECRYPT_PS3,
            input_file=iso_path,
            output_file=dec_iso_path,
            tool="PS3Dec",
            status=TransformStatus.SUCCESS,
            duration_seconds=time.time() - start,
        ))
        
        # Step 4: Format-specific handling
        if target_format == "folder":
            # Extract to folder structure
            start = time.time()
            folder_path = self._extract_ps3_iso(dec_iso_path, output_dir)
            transformation.add_step(TransformStep(
                step_type=TransformType.EXTRACT_ISO,
                input_file=dec_iso_path,
                output_file=folder_path,
                tool="7zip",
                status=TransformStatus.SUCCESS,
                duration_seconds=time.time() - start,
            ))
            transformation.final_file = folder_path
            
        elif target_format == "iso":
            # Move decrypted ISO to output
            final_iso = output_dir / f"{zip_file.stem}_dec.iso"
            shutil.move(dec_iso_path, final_iso)
            transformation.final_file = final_iso
        
        transformation.status = TransformStatus.SUCCESS
        return transformation
    
    def _unzip_iso(self, zip_file: Path, temp_dir: Path) -> Path:
        """Extract ISO from ZIP."""
        import zipfile
        
        with zipfile.ZipFile(zip_file, 'r') as zf:
            iso_files = [f for f in zf.namelist() if f.endswith('.iso')]
            if not iso_files:
                raise ValueError(f"No ISO found in {zip_file}")
            
            iso_name = iso_files[0]
            zf.extract(iso_name, temp_dir)
            return temp_dir / iso_name
    
    def _find_disc_key(self, game_name: str, keys_dir: Path) -> str:
        """Find matching disc key file.
        
        Tries multiple filename variations to match game to key.
        """
        import zipfile
        
        # Try exact match first
        key_zip = keys_dir / f"{game_name}.zip"
        
        if not key_zip.exists():
            # Try variations (remove revision, region, etc.)
            # This is a simplified version - production needs more robust matching
            raise FileNotFoundError(f"No disc key found for {game_name}")
        
        # Extract and read .dkey file
        with zipfile.ZipFile(key_zip, 'r') as zf:
            dkey_files = [f for f in zf.namelist() if f.endswith('.dkey')]
            if not dkey_files:
                raise ValueError(f"No .dkey file in {key_zip}")
            
            dkey_content = zf.read(dkey_files[0]).decode('ascii').strip()
            return dkey_content
    
    def _decrypt_ps3_iso(self, iso_path: Path, disc_key: str, temp_dir: Path) -> Path:
        """Decrypt PS3 ISO using PS3Dec."""
        import subprocess
        
        dec_iso_path = temp_dir / f"{iso_path.stem}_dec.iso"
        
        cmd = [
            str(self.ps3dec_path),
            "d",          # decrypt mode
            "key",        # key type
            disc_key,     # 32-char hex key
            str(iso_path),
            str(dec_iso_path),
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"PS3Dec failed: {result.stderr}")
        
        if not dec_iso_path.exists():
            raise RuntimeError("Decrypted ISO not created")
        
        return dec_iso_path
    
    def _extract_ps3_iso(self, iso_path: Path, output_dir: Path) -> Path:
        """Extract PS3 ISO to folder structure using 7zip."""
        import subprocess
        
        # Get game ID from ISO (simplified - would parse PARAM.SFO properly)
        game_id = iso_path.stem.replace("_dec", "")
        folder_path = output_dir / game_id
        folder_path.mkdir(parents=True, exist_ok=True)
        
        cmd = ["7z", "x", str(iso_path), f"-o{folder_path}", "-y"]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"7zip extraction failed: {result.stderr}")
        
        return folder_path
```

### Configuration

```yaml
platform:
  name: "ps3"
  system_type: "large"
  
source:
  type: "myrient"
  path: "/data/emu/archive/archive.myrient.erista.me/files/Redump/Sony - PlayStation 3"
  
dat:
  type: "retool"
  path: "/data/emu/dats/redump.retool.1g1r.usa/Sony - PlayStation 3.dat"
  
decryption:
  enabled: true
  disc_keys: "/data/emu/archive/archive.myrient.erista.me/files/Redump/Sony - PlayStation 3 - Disc Keys TXT"
  key_format: "dkey"
  
processing:
  format: "folder"  # or "iso"
  
targets:
  - name: "batocera"
    format: "folder"  # RPCS3 preferred
  - name: "rocknix"
    format: "iso"     # Alternative if space constrained
```

### Testing

1. Select 5 small PS3 games
2. Verify disc keys exist
3. Test decryption
4. Test extraction
5. Verify in RPCS3

---

## Phase 5C: Wii U (WUA Format!)

**Timeline:** 1-2 weeks  
**Difficulty:** 🟠 Hard  
**Status:** After 5B

### Discovery: WUA Format ✅

**User confirmed:** Batocera DOES support Wii U via Cemu!  
**Target format:** WUA (Wii U Archive) - zstd compressed

**Example working file:**
```
The Legend of Zelda - Breath of the Wild (USA) (DLC) (v208).wua
```

This single 8GB file contains:
- Base game
- All updates (v208)
- All DLC

**Perfect target format!** 🎯

### Transformation Pipeline

```
Myrient ZIP (9 GB)
  ↓ [unzip]
WUX file (9 GB, encrypted)
  ↓ [wud-compress: WUX → WUD]
WUD file (23 GB, encrypted) ⚠️
  ↓ [decrypt with disc key + common key]
WUD file (23 GB, decrypted)
  ↓ [wud2wua or similar]
WUA file (8 GB, decrypted) ✅

Storage peak: ~41 GB per game!
```

### Research Needed

1. 🔍 **Find WUA creation tool**
   - Check Cemu documentation
   - Search for wud2wua converter
   - May need custom Python/zstd solution

2. 🔍 **Find Wii U decryption tool**
   - cdecrypt (most common)
   - JWUDTool (Java, has CLI)
   - Verify Linux compatibility

3. 🔑 **Key management**
   - Disc keys (per game)
   - Common key file
   - Otp.bin / Seeprom.bin?

### Implementation Priority

After PS3 is working:
1. Research tools (1-2 days)
2. Test with single small game (2-3 days)
3. Implement TransformWiiUStage (3-4 days)
4. Test with full collection sample (1-2 days)

---

## Timeline Summary

| Phase | Duration | Status | Start After |
|-------|----------|--------|-------------|
| **5A: Wii/GameCube** | 1-2 days | 🎯 Next | Phase 4 ✅ |
| **5B: PS3** | 1 week | Planned | 5A |
| **5C: Wii U** | 1-2 weeks | Planned | 5B |

**Total Phase 5:** 2-3 weeks

---

## Success Metrics

### Phase 5A (Wii/GameCube)
- ✅ 100% RVZ extraction success rate
- ✅ All files load in Dolphin
- ✅ Pipeline < 5 min for 10 games

### Phase 5B (PS3)
- ✅ 95%+ decryption success rate
- ✅ Key matching works for 90%+ games
- ✅ Extracted games work in RPCS3
- ✅ Storage peak < 15 GB per game

### Phase 5C (Wii U)
- ✅ WUA files created successfully
- ✅ Files load in Cemu/Batocera
- ✅ Storage managed with HYBRID approach
- ✅ DLC/updates properly included

---

## Let's Start! 🚀

**Next task:** Implement UnzipRVZStage for Wii/GameCube

This will:
1. Validate our Stage infrastructure with real files
2. Build confidence with quick success
3. Test DAT matching with Redump systems
4. Provide foundation for complex transforms

**Ready to create the Wii/GameCube configs and UnzipRVZStage?**
