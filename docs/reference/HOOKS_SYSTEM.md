# Hooks System Documentation

## Overview

The hooks system provides a flexible, extensible way to inject custom behavior into the ROM processing pipeline without modifying core code. Hooks can capture hashes, record transformations, validate files, monitor progress, and more.

## Architecture

### Components

1. **HookPoint** - Enum defining 17 hook trigger points throughout pipeline execution
2. **HookContext** - Data passed to hooks containing paths, metadata, errors, etc.
3. **Hook** - Abstract base class defining hook methods (one per hook point)
4. **HookRegistry** - Central registry managing hooks and triggering them at appropriate points
5. **Built-in Hooks** - Ready-to-use implementations for common tasks

### Hook Points

The pipeline triggers hooks at these points (in order):

| Hook Point | When | Purpose |
|------------|------|---------|
| `BEFORE_PIPELINE` | Start of processing | Initialize resources, set up tracking |
| `VALIDATE_INPUT` | After pipeline starts | Check input file validity |
| `BEFORE_STAGE` | Before each stage | Capture pre-stage state, prepare stage |
| `STAGE_SKIP` | When stage skipped | Log skipped stages |
| `AFTER_STAGE` | After each stage | Capture post-stage state, verify output |
| `STAGE_ERROR` | Stage throws exception | Handle stage-specific errors |
| `VALIDATE_OUTPUT` | After all stages | Validate final output |
| `AFTER_PIPELINE` | Successful completion | Record results, cleanup |
| `ON_ERROR` | Pipeline exception | Handle pipeline errors |
| `ON_COMPLETE` | Always (finally block) | Guaranteed cleanup, final logging |

Additional file operation hooks:
- `BEFORE_READ`, `AFTER_READ` - File read operations
- `BEFORE_WRITE`, `AFTER_WRITE` - File write operations  
- `VERIFY_INTEGRITY` - File integrity checks

## Usage

### Basic Setup

```python
from romfarmer.processors.pipeline import PipelineProcessor
from romfarmer.processors.hooks import HookRegistry
from romfarmer.processors.builtin_hooks import (
    HashCaptureHook,
    TransformationTrackingHook,
    ProgressMonitorHook,
)
from romfarmer.metadata import MetadataDatabase

# Create database connection
db = MetadataDatabase(Path("metadata/database/romfarmer.db"))

# Create hook registry
registry = HookRegistry()

# Register hooks with priorities (lower = earlier)
registry.register('progress', ProgressMonitorHook(), priority=5)
registry.register('hash', HashCaptureHook(db), priority=10)
registry.register('track', TransformationTrackingHook(db), priority=20)

# Create processor with hooks
processor = PipelineProcessor(profile, stages, hooks=registry)

# Process with hooks active
result = await processor.process(
    input_path=Path("game.zip"),
    output_dir=Path("/output"),
)

# Access hook metadata
print(result.metadata)  # Contains data from all hooks
```

### Custom Hook

```python
from romfarmer.processors.hooks import Hook, HookContext, HookPoint

class CustomValidationHook(Hook):
    """Custom hook for platform-specific validation."""
    
    async def on_validate_input(self, context: HookContext):
        """Validate input file before processing."""
        path = context.input_path
        
        # Check file size
        if path.stat().st_size > 4 * 1024**3:  # 4GB limit
            raise ValueError(f"File too large: {path.name}")
        
        # Check extension
        if path.suffix not in ['.iso', '.zip', '.7z']:
            raise ValueError(f"Unsupported format: {path.suffix}")
        
        print(f"✓ Input validated: {path.name}")
    
    async def on_after_stage(self, context: HookContext):
        """Check output after each stage."""
        if context.output_path and context.output_path.exists():
            size_mb = context.output_path.stat().st_size / (1024**2)
            print(f"✓ Stage {context.stage_name}: {size_mb:.1f}MB")

# Register custom hook
registry.register('validate', CustomValidationHook(), priority=1)
```

### Conditional Hooks

```python
# Enable/disable hooks dynamically
registry.disable_hook('hash')  # Skip hash calculation
registry.enable_hook('hash')   # Re-enable

# Filter by hook points
registry.trigger(
    HookPoint.BEFORE_STAGE,
    context,
    filter_points=[HookPoint.BEFORE_STAGE, HookPoint.AFTER_STAGE]
)
```

## Built-in Hooks

### HashCaptureHook

Calculates and caches file hashes (CRC32, MD5, SHA1, SHA256).

**Features:**
- Checks `HashCache` table before recalculating (saves time!)
- Stores calculation time and file metadata
- Triggered before/after stages to capture input/output hashes
- Results stored in `context.metadata['source_hashes']` and `context.metadata['final_hashes']`

**Usage:**
```python
from romfarmer.processors.builtin_hooks import HashCaptureHook

hook = HashCaptureHook(database)
registry.register('hash', hook, priority=10)
```

**Metadata Output:**
```python
{
    'source_hashes': {
        'crc32': 'abc12345',
        'md5': '1234567890abcdef...',
        'sha1': 'abcd1234...',
        'sha256': '5678cafe...',
    },
    'final_hashes': {
        'crc32': 'def67890',
        'md5': 'fedcba0987654321...',
        ...
    }
}
```

### TransformationTrackingHook

Records transformations to `ROMTransformation` table, linking source and final hashes.

**Features:**
- Captures transformation chain (extract → compress → package)
- Records tool name, version, parameters
- Tracks duration
- Links to game metadata (if available)
- Enables reverse lookup: compressed file → original source hash

**Usage:**
```python
from romfarmer.processors.builtin_hooks import TransformationTrackingHook

hook = TransformationTrackingHook(database)
registry.register('track', hook, priority=20)
```

**Database Record:**
```sql
INSERT INTO rom_transformations (
    source_md5, source_sha1, ...,          -- Original file hashes
    transformation_tool,                    -- "extract → chdman"
    transformation_duration_seconds,        -- 45.2
    final_md5, final_sha1, ...             -- Compressed file hashes
) VALUES (...)
```

### ProgressMonitorHook

Logs progress and calls optional callbacks.

**Features:**
- Logs pipeline start/end
- Logs each stage execution
- Tracks timing per stage
- Aggregates metrics
- Optional custom callbacks

**Usage:**
```python
from romfarmer.processors.builtin_hooks import ProgressMonitorHook

def my_callback(event_type: str, data: dict):
    print(f"Event: {event_type}, Data: {data}")

hook = ProgressMonitorHook(callback=my_callback)
registry.register('progress', hook, priority=5)
```

**Output:**
```
Pipeline started: game.iso → /output
  Stage 1/3: extract_archive (2.3s)
  Stage 2/3: compress_chd (42.1s)  
  Stage 3/3: verify (1.2s)
Pipeline completed: game.chd (45.6s total)
```

### ValidationHook

Validates files at input and output stages.

**Features:**
- File existence check
- Size validation (min/max)
- Extension whitelist
- Custom validator functions

**Usage:**
```python
from romfarmer.processors.builtin_hooks import ValidationHook

def check_redump_format(path: Path) -> bool:
    """Custom validator for Redump disc images."""
    return path.suffix in ['.cue', '.iso', '.bin']

hook = ValidationHook(
    min_size=1024,                    # 1KB minimum
    max_size=50 * 1024**3,           # 50GB maximum
    allowed_extensions=['.iso', '.cue'],
    custom_validators=[check_redump_format],
)
registry.register('validate', hook, priority=1)
```

## Hook Context

The `HookContext` object passed to hooks contains:

```python
@dataclass
class HookContext:
    hook_point: HookPoint           # Which hook point triggered
    input_path: Path                # Current input file
    output_path: Path               # Current output file (if available)
    stage_name: str                 # Current stage name (if in stage)
    pipeline_context: dict          # Shared context between stages
    rom: Optional[Rom]              # ROM metadata (if parsed)
    error: Optional[Exception]      # Exception (if error occurred)
    metadata: dict                  # Shared between all hooks
    success: bool                   # Whether operation succeeded
    duration: float                 # Time taken (seconds)
```

**Key Features:**
- `metadata` dict is shared across all hooks (use for communication)
- `pipeline_context` is the stage context (transformations, temp_dir, etc.)
- `duration` is calculated automatically at appropriate points

## Integration Examples

### Example 1: Saturn ISO → CHD with Tracking

```python
from romfarmer.processors.profiles import PROFILE_SATURN
from romfarmer.processors.stages import (
    ExtractArchiveStage,
    CompressCHDStage,
)

# Setup stages
stages = {
    'extract_archive': ExtractArchiveStage(),
    'compress_chd': CompressCHDStage(),
}

# Setup hooks
db = MetadataDatabase(Path("metadata/database/romfarmer.db"))
registry = HookRegistry()
registry.register('hash', HashCaptureHook(db), priority=10)
registry.register('track', TransformationTrackingHook(db), priority=20)
registry.register('progress', ProgressMonitorHook(), priority=5)

# Create processor
processor = PipelineProcessor(PROFILE_SATURN, stages, hooks=registry)

# Process
result = await processor.process(
    input_path=Path("Panzer Dragoon (USA).zip"),
    output_dir=Path("/output/saturn"),
)

# Result contains:
# - Original path: Panzer Dragoon (USA).zip
# - Final path: Panzer Dragoon (USA).chd
# - Metadata with hashes, transformation tracking
# - Database records in HashCache + ROMTransformation
```

### Example 2: Batch Processing with Custom Hook

```python
class BatchStatsHook(Hook):
    """Track statistics across batch processing."""
    
    def __init__(self):
        self.total_files = 0
        self.total_size_before = 0
        self.total_size_after = 0
        self.total_duration = 0
    
    async def on_after_pipeline(self, context: HookContext):
        """Accumulate stats after each file."""
        self.total_files += 1
        self.total_size_before += context.input_path.stat().st_size
        self.total_size_after += context.output_path.stat().st_size
        self.total_duration += context.duration
    
    def print_summary(self):
        """Print batch statistics."""
        compression_ratio = (1 - self.total_size_after / self.total_size_before) * 100
        avg_time = self.total_duration / self.total_files
        
        print(f"\n=== Batch Processing Complete ===")
        print(f"Files processed: {self.total_files}")
        print(f"Size before: {self.total_size_before / 1024**3:.2f}GB")
        print(f"Size after: {self.total_size_after / 1024**3:.2f}GB")
        print(f"Compression: {compression_ratio:.1f}%")
        print(f"Avg time: {avg_time:.1f}s per file")

# Use in batch
stats_hook = BatchStatsHook()
registry.register('stats', stats_hook, priority=30)

for rom_file in rom_files:
    await processor.process(rom_file, output_dir)

stats_hook.print_summary()
```

## Performance Considerations

### Hash Caching

The `HashCaptureHook` checks the `HashCache` table before calculating hashes:

```python
# First time: Calculate and cache (slow)
await processor.process(path1, output_dir)  # 30 seconds

# Second time: Use cache (fast!)
await processor.process(path1, output_dir)  # 0.1 seconds
```

This is critical when:
- Processing same source files multiple times
- Pre-calculated hashes exist from hash pre-calculation job
- Switching between different compression profiles

### Hook Priority

Lower priority = earlier execution:

```python
registry.register('validate', ValidationHook(), priority=1)   # First
registry.register('progress', ProgressMonitorHook(), priority=5)
registry.register('hash', HashCaptureHook(), priority=10)
registry.register('track', TransformationTrackingHook(), priority=20)  # Last
```

**Why it matters:**
- Validation should fail fast (before expensive operations)
- Hashing should happen before transformation tracking needs them
- Progress monitoring should wrap everything

### Error Handling

Hooks can fail without stopping the pipeline:

```python
# In HookRegistry.trigger():
try:
    await method(context)
except Exception as e:
    logger.error(f"Hook {hook_name} failed: {e}")
    # Continue with other hooks
```

For critical hooks, implement error handling:

```python
class CriticalValidationHook(Hook):
    async def on_validate_input(self, context: HookContext):
        if not self.validate(context.input_path):
            raise ValueError("Critical validation failed!")  # Stops pipeline
```

## Testing Hooks

See `tests/test_hooks_integration.py` for examples.

Quick test:

```python
# Create test hook
class DebugHook(Hook):
    async def on_before_pipeline(self, context: HookContext):
        print(f"Starting: {context.input_path}")
    
    async def on_after_pipeline(self, context: HookContext):
        print(f"Done: {context.output_path}")

# Use in processing
registry = HookRegistry()
registry.register('debug', DebugHook())
processor = PipelineProcessor(profile, stages, hooks=registry)
```

## Future Enhancements

Planned improvements:

1. **Hook dependencies** - Declare "this hook requires hash hook"
2. **Conditional execution** - Skip hooks based on runtime conditions
3. **Async callbacks** - Non-blocking progress notifications
4. **Hook configuration** - Load hook settings from YAML/JSON
5. **Community hooks** - Share custom hooks via plugins
6. **ScreenScraper hook** - Auto-scrape metadata using cached hashes
7. **DAT validation hook** - Verify against No-Intro/Redump DATs

## Troubleshooting

### Hook not triggering

Check:
1. Hook registered? `print(registry.list_hooks())`
2. Hook enabled? `registry.enable_hook('name')`
3. Method implemented? Hook methods are optional (base class has empty defaults)
4. Stage reached? With no stages, only BEFORE/AFTER_PIPELINE and ON_COMPLETE trigger

### Missing metadata

The `metadata` dict is shared between hooks:

```python
# HashCaptureHook stores:
context.metadata['source_hashes'] = {...}

# TransformationTrackingHook reads:
hashes = context.metadata.get('source_hashes', {})
```

If metadata is missing:
1. Check hook priority (hash hook before track hook)
2. Check hook is actually running (add debug prints)
3. Verify metadata key names match

### Performance issues

If hooks slow down processing:
1. Use `HashCache` (check before calculating)
2. Batch database writes (don't commit per-file in batch)
3. Disable non-essential hooks during batch
4. Profile hooks with duration tracking

## Summary

The hooks system enables:

✅ **Hash tracking** - Cache and reuse expensive hash calculations  
✅ **Transformation provenance** - Link compressed files to original sources  
✅ **Custom validation** - Platform-specific rules  
✅ **Progress monitoring** - Real-time feedback and metrics  
✅ **Extensibility** - Add new behavior without modifying core code  
✅ **Batch processing** - Accumulate statistics across runs  
✅ **Error handling** - Graceful degradation when hooks fail  

The system is production-ready and actively used in ROM processing pipelines!
