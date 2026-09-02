# Xbox 360 Pipeline Architecture: Two Approaches

## The Challenge

Xbox 360 games require a **multi-step transformation chain**:
```
ZIP → Unzip → ISO (encrypted) → Decrypt → ISO (raw) → Extract → Folder → 
Rebuild → ISO (optimized) → Compress → XISO/ZSO (final)
```

**Question:** How do we track/manage this complexity?

## Approach 1: Per-File Processing (Sequential Transforms)

### Concept
**Process each file completely before moving to next file**

```python
class TransformStage(Stage):
    """Transform files through multiple steps."""
    
    def execute(self, context):
        for source_file in context.filtered_files:
            # Do ALL transforms for THIS file
            current = source_file
            
            # Step 1: Unzip
            current = self._unzip(current)
            
            # Step 2: Decrypt
            current = self._decrypt_xbox360(current)
            
            # Step 3: Extract
            current = self._extract_xiso(current)
            
            # Step 4: Rebuild
            current = self._rebuild_xiso(current)
            
            # Step 5: Compress
            final = self._compress_to_xiso(current)
            
            # Track transformation
            self._record_transformation(source_file, final)
            context.transformed_files.append(final)
        
        return result
```

### Flow Diagram
```
┌─────────────────────────────────────────────────────────┐
│ TransformStage: Process Each File Completely           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  File 1: Halo 3.zip                                     │
│    → unzip    → Halo 3.iso (encrypted)                 │
│    → decrypt  → Halo 3.iso (raw)                       │
│    → extract  → Halo 3/ (folder)                       │
│    → rebuild  → Halo 3.iso (optimized)                 │
│    → compress → Halo 3.xiso ✓                          │
│                                                         │
│  File 2: Gears of War.zip                               │
│    → unzip    → Gears of War.iso (encrypted)           │
│    → decrypt  → Gears of War.iso (raw)                 │
│    → extract  → Gears of War/ (folder)                 │
│    → rebuild  → Gears of War.iso (optimized)           │
│    → compress → Gears of War.xiso ✓                    │
│                                                         │
│  [Continue for all files...]                           │
└─────────────────────────────────────────────────────────┘
```

### Advantages ✅
- **Simple tracking**: One file → one result
- **Memory efficient**: Work on one file at a time
- **Easy cleanup**: Delete intermediates immediately
- **Clear progress**: "Processing file 45/200"
- **Failure isolation**: One bad file doesn't block others

### Disadvantages ❌
- **No parallelization**: Can't use multiple CPU cores per transform
- **Redundant disk I/O**: Write/read intermediates repeatedly
- **Can't optimize across files**: Each file processed independently

### Code Example
```python
class Xbox360TransformStage(Stage):
    """Transform Xbox 360 games through complete pipeline."""
    
    def __init__(self):
        super().__init__("Transform Xbox 360")
        self.tools = {
            'decrypt': Path('/path/to/xbox360_decrypt'),
            'extract': Path('/path/to/extract-xiso'),
            'rebuild': Path('/path/to/xdvdfs-tools/xdvdfs'),
            'compress': Path('/path/to/maxcso'),  # or custom XISO compressor
        }
    
    def execute(self, context: StageContext) -> StageResult:
        """Process each file through complete transformation chain."""
        
        transformed = []
        failed = []
        
        for i, zip_file in enumerate(context.filtered_files, 1):
            self._log_info(context, f"Processing {i}/{len(context.filtered_files)}: {zip_file.name}")
            
            try:
                # Create temp directory for this file
                temp_dir = context.work_dir / f"transform_{zip_file.stem}"
                temp_dir.mkdir()
                
                # Chain of transforms
                final_file = self._transform_xbox360_game(
                    source=zip_file,
                    temp_dir=temp_dir,
                    context=context,
                )
                
                if final_file:
                    transformed.append(final_file)
                    self._log_info(context, f"  ✓ {zip_file.name} → {final_file.name}")
                else:
                    failed.append(zip_file)
                    self._log_error(context, f"  ✗ Failed: {zip_file.name}")
                
                # Cleanup intermediates
                shutil.rmtree(temp_dir, ignore_errors=True)
                
            except Exception as e:
                self._log_error(context, f"  ✗ Error: {zip_file.name}: {e}")
                failed.append(zip_file)
        
        context.transformed_files = transformed
        return StageResult(
            status=StageStatus.SUCCESS,
            message=f"Transformed {len(transformed)} files",
            files_processed=len(context.filtered_files),
            files_matched=len(transformed),
            files_failed=len(failed),
        )
    
    def _transform_xbox360_game(
        self,
        source: Path,
        temp_dir: Path,
        context: StageContext,
    ) -> Optional[Path]:
        """Transform single Xbox 360 game through full pipeline.
        
        Args:
            source: Source ZIP file
            temp_dir: Temporary directory for intermediates
            context: Stage context
            
        Returns:
            Path to final XISO/ZSO file or None if failed
        """
        try:
            # Step 1: Unzip
            self._log_info(context, "    [1/5] Unzipping...")
            iso_encrypted = self._unzip_to_iso(source, temp_dir)
            if not iso_encrypted:
                return None
            
            # Step 2: Decrypt
            self._log_info(context, "    [2/5] Decrypting Xbox 360 ISO...")
            iso_decrypted = self._decrypt_xbox360_iso(iso_encrypted, temp_dir)
            if not iso_decrypted:
                return None
            iso_encrypted.unlink()  # Clean up encrypted version
            
            # Step 3: Extract to folder
            self._log_info(context, "    [3/5] Extracting ISO contents...")
            extracted_dir = self._extract_xiso_contents(iso_decrypted, temp_dir)
            if not extracted_dir:
                return None
            iso_decrypted.unlink()  # Clean up raw ISO
            
            # Step 4: Rebuild (optimize structure)
            self._log_info(context, "    [4/5] Rebuilding optimized ISO...")
            iso_rebuilt = self._rebuild_xiso(extracted_dir, temp_dir)
            if not iso_rebuilt:
                return None
            shutil.rmtree(extracted_dir)  # Clean up extracted folder
            
            # Step 5: Compress to final format
            self._log_info(context, "    [5/5] Compressing to XISO...")
            final_file = self._compress_to_xiso(iso_rebuilt, context.work_dir)
            if not final_file:
                return None
            iso_rebuilt.unlink()  # Clean up rebuilt ISO
            
            return final_file
            
        except Exception as e:
            self._log_error(context, f"    Transform failed: {e}")
            return None
    
    def _unzip_to_iso(self, zip_path: Path, temp_dir: Path) -> Optional[Path]:
        """Unzip to find ISO file."""
        with zipfile.ZipFile(zip_path, 'r') as zf:
            iso_files = [f for f in zf.namelist() if f.lower().endswith('.iso')]
            if not iso_files:
                return None
            zf.extract(iso_files[0], temp_dir)
            return temp_dir / iso_files[0]
    
    def _decrypt_xbox360_iso(self, iso_path: Path, temp_dir: Path) -> Optional[Path]:
        """Decrypt Xbox 360 ISO."""
        output = temp_dir / f"{iso_path.stem}_decrypted.iso"
        cmd = [str(self.tools['decrypt']), str(iso_path), str(output)]
        result = subprocess.run(cmd, capture_output=True)
        return output if result.returncode == 0 and output.exists() else None
    
    def _extract_xiso_contents(self, iso_path: Path, temp_dir: Path) -> Optional[Path]:
        """Extract ISO to folder using extract-xiso."""
        extract_dir = temp_dir / iso_path.stem
        cmd = [str(self.tools['extract']), '-d', str(extract_dir), str(iso_path)]
        result = subprocess.run(cmd, capture_output=True)
        return extract_dir if result.returncode == 0 and extract_dir.exists() else None
    
    def _rebuild_xiso(self, folder_path: Path, temp_dir: Path) -> Optional[Path]:
        """Rebuild optimized ISO from folder."""
        output = temp_dir / f"{folder_path.name}_rebuilt.iso"
        cmd = [str(self.tools['rebuild']), 'pack', str(folder_path), str(output)]
        result = subprocess.run(cmd, capture_output=True)
        return output if result.returncode == 0 and output.exists() else None
    
    def _compress_to_xiso(self, iso_path: Path, output_dir: Path) -> Optional[Path]:
        """Compress to XISO format."""
        output = output_dir / f"{iso_path.stem}.xiso"
        # Custom compression logic here
        # For now, just copy (implement real compression later)
        shutil.copy2(iso_path, output)
        return output
```

**Status Tracking:**
```python
# Track each transformation in context
context.transformations = [
    {
        'source': 'Halo 3.zip',
        'steps': [
            {'type': 'unzip', 'output': 'Halo 3.iso (encrypted)', 'status': 'success'},
            {'type': 'decrypt', 'output': 'Halo 3.iso (raw)', 'status': 'success'},
            {'type': 'extract', 'output': 'Halo 3/', 'status': 'success'},
            {'type': 'rebuild', 'output': 'Halo 3.iso (optimized)', 'status': 'success'},
            {'type': 'compress', 'output': 'Halo 3.xiso', 'status': 'success'},
        ],
        'final': 'Halo 3.xiso',
        'duration': 45.2,
    },
    # ... more files
]
```

---

## Approach 2: Batch Processing (Separate Stages per Transform)

### Concept
**Each transform is a separate stage, batch process all files**

```python
# Stage 1: Unzip all files
class UnzipStage(Stage):
    def execute(self, context):
        for zip_file in context.filtered_files:
            iso = self._unzip(zip_file)
            context.encrypted_isos.append(iso)

# Stage 2: Decrypt all files
class DecryptStage(Stage):
    def execute(self, context):
        for iso in context.encrypted_isos:
            decrypted = self._decrypt(iso)
            context.decrypted_isos.append(decrypted)

# Stage 3: Extract all files
class ExtractStage(Stage):
    def execute(self, context):
        for iso in context.decrypted_isos:
            folder = self._extract(iso)
            context.extracted_folders.append(folder)

# Stage 4: Rebuild all files
class RebuildStage(Stage):
    def execute(self, context):
        for folder in context.extracted_folders:
            rebuilt = self._rebuild(folder)
            context.rebuilt_isos.append(rebuilt)

# Stage 5: Compress all files
class CompressStage(Stage):
    def execute(self, context):
        for iso in context.rebuilt_isos:
            final = self._compress(iso)
            context.final_files.append(final)
```

### Flow Diagram
```
┌──────────────────────────────────────────────────────┐
│ Stage 1: UnzipStage (batch all files)               │
├──────────────────────────────────────────────────────┤
│  Halo 3.zip         → Halo 3.iso (encrypted)        │
│  Gears of War.zip   → Gears of War.iso (encrypted)  │
│  Forza 3.zip        → Forza 3.iso (encrypted)       │
│  [200 files...]                                      │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│ Stage 2: DecryptStage (batch all files)             │
├──────────────────────────────────────────────────────┤
│  Halo 3.iso         → Halo 3.iso (raw)              │
│  Gears of War.iso   → Gears of War.iso (raw)        │
│  Forza 3.iso        → Forza 3.iso (raw)             │
│  [200 files...]                                      │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│ Stage 3: ExtractStage (batch all files)             │
├──────────────────────────────────────────────────────┤
│  Halo 3.iso         → Halo 3/ (folder)              │
│  Gears of War.iso   → Gears of War/ (folder)        │
│  Forza 3.iso        → Forza 3/ (folder)             │
│  [200 files...]                                      │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│ Stage 4: RebuildStage (batch all files)             │
├──────────────────────────────────────────────────────┤
│  Halo 3/            → Halo 3.iso (rebuilt)          │
│  Gears of War/      → Gears of War.iso (rebuilt)    │
│  Forza 3/           → Forza 3.iso (rebuilt)         │
│  [200 files...]                                      │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│ Stage 5: CompressStage (batch all files)            │
├──────────────────────────────────────────────────────┤
│  Halo 3.iso         → Halo 3.xiso ✓                 │
│  Gears of War.iso   → Gears of War.xiso ✓           │
│  Forza 3.iso        → Forza 3.xiso ✓                │
│  [200 files...]                                      │
└──────────────────────────────────────────────────────┘
```

### Advantages ✅
- **Easy parallelization**: Batch process with ThreadPool
- **Checkpoint-able**: Can resume from any stage
- **Modular**: Easy to add/remove/swap transform steps
- **Testable**: Test each transform independently

### Disadvantages ❌
- **Disk space**: ALL intermediates exist at once
- **Complex tracking**: Need to match files across stages
- **Memory**: Holding 200+ file paths in context
- **Cleanup complexity**: What if stage 3 fails? Clean up stages 1-2?

---

## Approach 3: HYBRID (Recommended!) ⭐

### Concept
**Group related transforms into one stage, but keep stage boundaries clean**

```python
class TransformXbox360Stage(Stage):
    """Single stage that handles ALL Xbox 360-specific transforms.
    
    But processes files ONE AT A TIME for memory efficiency.
    """
    
    def execute(self, context):
        for file in context.filtered_files:
            # Complete pipeline for this ONE file
            final = self._transform_chain(file, context)
            context.transformed_files.append(final)
            # Intermediates cleaned up immediately
```

**Pipeline Structure:**
```
FilterDAT → ApplyLists → TransformXbox360 → Organize → Metadata
                              ↑
                              │
                    ┌─────────┴─────────┐
                    │ Per-file pipeline:│
                    │  1. Unzip         │
                    │  2. Decrypt       │
                    │  3. Extract       │
                    │  4. Rebuild       │
                    │  5. Compress      │
                    └───────────────────┘
```

### Why This is Best

1. **Clean stage boundaries**: Transform is ONE stage conceptually
2. **Memory efficient**: Process files one at a time
3. **Easy tracking**: Source file → final file mapping
4. **Cleanup simple**: Delete intermediates immediately
5. **Extensible**: Easy to add new transform steps
6. **Testable**: Can test full transform or individual steps

---

## Status Tracking: How Do We Do It?

### Option A: Context Lists (Current Design)
```python
@dataclass
class StageContext:
    # Track different stages of processing
    filtered_files: List[Path]      # After FilterDAT
    transformed_files: List[Path]   # After Transform
    organized_files: Dict[str, List[Path]]  # After Organize
```

**Problem:** Lost intermediate details!

### Option B: Transformation Records (Better!)
```python
@dataclass
class FileTransformation:
    """Track a file's complete transformation journey."""
    
    source_file: Path
    """Original file (e.g., Game.zip)"""
    
    final_file: Optional[Path]
    """Final output file (e.g., Game.xiso)"""
    
    steps: List[TransformStep]
    """Each transformation step"""
    
    status: str  # 'success', 'failed', 'in_progress'
    duration_seconds: float
    error: Optional[str] = None

@dataclass
class TransformStep:
    """Single transformation step."""
    
    step_type: str  # 'unzip', 'decrypt', 'extract', 'rebuild', 'compress'
    input_file: Path
    output_file: Optional[Path]
    tool: str  # 'zipfile', 'xbox360_decrypt', 'extract-xiso', etc.
    status: str
    duration_seconds: float
    error: Optional[str] = None

# In context:
@dataclass
class StageContext:
    transformations: List[FileTransformation] = field(default_factory=list)
```

**Usage:**
```python
def _transform_xbox360_game(self, source, temp_dir, context):
    transformation = FileTransformation(
        source_file=source,
        steps=[],
        status='in_progress',
    )
    
    # Step 1: Unzip
    step1_start = time.time()
    iso_encrypted = self._unzip(source, temp_dir)
    transformation.steps.append(TransformStep(
        step_type='unzip',
        input_file=source,
        output_file=iso_encrypted,
        tool='zipfile',
        status='success' if iso_encrypted else 'failed',
        duration_seconds=time.time() - step1_start,
    ))
    
    # Step 2: Decrypt
    step2_start = time.time()
    iso_decrypted = self._decrypt(iso_encrypted, temp_dir)
    transformation.steps.append(TransformStep(
        step_type='decrypt',
        input_file=iso_encrypted,
        output_file=iso_decrypted,
        tool='xbox360_decrypt',
        status='success' if iso_decrypted else 'failed',
        duration_seconds=time.time() - step2_start,
    ))
    
    # ... more steps
    
    transformation.final_file = final_output
    transformation.status = 'success'
    context.transformations.append(transformation)
    
    return final_output
```

**Benefits:**
- ✅ Complete audit trail
- ✅ Can resume from failures
- ✅ Easy to generate reports
- ✅ Debugging: See exactly which step failed

---

## Final Recommendation: HYBRID with Transformation Tracking

```python
# Pipeline stages (high level)
pipeline.add_stage(FilterDATStage())
pipeline.add_stage(ApplyListsStage())
pipeline.add_stage(TransformXbox360Stage())  # ← All transforms in ONE stage
pipeline.add_stage(OrganizeStage())
pipeline.add_stage(GenerateMetadataStage())

# Inside TransformXbox360Stage:
class TransformXbox360Stage(Stage):
    def execute(self, context):
        for source_file in context.filtered_files:
            # Process this ONE file completely
            transformation = self._transform_single_file(source_file, context)
            context.transformations.append(transformation)
            if transformation.status == 'success':
                context.transformed_files.append(transformation.final_file)
    
    def _transform_single_file(self, source, context):
        """Do all transforms for one file, track each step."""
        transformation = FileTransformation(source_file=source, steps=[])
        
        try:
            current = source
            for transform in self.transform_chain:
                step_result = transform(current, context)
                transformation.steps.append(step_result)
                if step_result.status != 'success':
                    transformation.status = 'failed'
                    return transformation
                current = step_result.output_file
            
            transformation.final_file = current
            transformation.status = 'success'
        except Exception as e:
            transformation.status = 'failed'
            transformation.error = str(e)
        
        return transformation
```

**This gives you:**
1. ✅ Clean high-level pipeline
2. ✅ Memory-efficient (one file at a time)
3. ✅ Complete tracking (all steps recorded)
4. ✅ Easy debugging (can inspect any transformation)
5. ✅ Extensible (add new transforms easily)

Does this clarify the vision?
