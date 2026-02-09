# Transformation Tracking Integration Guide

## Overview

This guide shows how to integrate transformation tracking into your ROM processing workflow. The transformation recorder automatically captures source→final hash mappings, enabling ScreenScraper lookups even for converted files (CHD, XISO, CSO, etc.).

## Quick Start

### Basic Integration

```python
from pathlib import Path
from romfarmer.metadata import MetadataDatabase, DATManager, TransformationRecorder

# Setup
db = MetadataDatabase("metadata/database/romfarmer.db")
dat_manager = DATManager([Path("/data/emu/dats/redump")])

with db.get_session() as session:
    recorder = TransformationRecorder(session, dat_manager)
    
    # Process ROMs with automatic transformation tracking
    source_file = Path("/source/saturn/game.cue")
    
    with recorder.record_transformation(
        source_file=source_file,
        system="saturn",
        tool="chdman",
        version="0.251",
        params={"compression": "zstd"}
    ) as transform:
        # Your actual ROM processing here
        final_file = convert_to_chd(source_file)
        
        # Record the final file
        transform.set_final_file(final_file)
    
    # Transformation automatically saved with:
    # - Source hash (from Redump DAT - instant!)
    # - Final hash (calculated or cached)
    # - Tool metadata
    # - Timing information
```

## Real-World Example: Saturn CHD Pipeline

### Scenario
You have Redump Saturn ISOs (CUE+BIN) and want to convert them to CHD format while maintaining scraping capability.

### Before Transformation Tracking
```bash
# Convert to CHD
chdman createcd -i "3D Baseball (USA).cue" -o "output/3D Baseball (USA).chd"

# Problem: ScreenScraper doesn't know this CHD hash!
# MD5 of CUE: 4d9347b77d53c8f366f787cc9ba5ef9a (Redump knows this)
# MD5 of CHD: 497af1102b63d9d148e4ba4d119fb64e (ScreenScraper doesn't know this)
# Result: No metadata found! 😢
```

### After Transformation Tracking
```python
from pathlib import Path
from romfarmer.metadata import MetadataDatabase, DATManager, TransformationRecorder
import subprocess

# Setup
db = MetadataDatabase("metadata/database/romfarmer.db")
dat_manager = DATManager([Path("/data/emu/dats/redump")])

def process_saturn_collection():
    source_dir = Path("/data/emu/source/myrient.erista.me/files/Redump/Sega - Saturn")
    output_dir = Path("/data/emu/stage/eng.1g1r/saturn")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with db.get_session() as session:
        recorder = TransformationRecorder(session, dat_manager)
        
        # Process each CUE file
        for cue_file in source_dir.glob("**/*.cue"):
            output_chd = output_dir / cue_file.with_suffix(".chd").name
            
            if output_chd.exists():
                print(f"Skipping (already exists): {output_chd.name}")
                continue
            
            print(f"\nProcessing: {cue_file.name}")
            
            # Record transformation
            with recorder.record_transformation(
                source_file=cue_file,
                system="saturn",
                tool="chdman",
                version="0.251",
                params={"compression": "zstd", "hunksize": "auto"}
            ) as transform:
                # Run chdman
                result = subprocess.run([
                    "chdman", "createcd",
                    "-i", str(cue_file),
                    "-o", str(output_chd),
                    "-c", "zstd"
                ], capture_output=True)
                
                if result.returncode == 0:
                    # Record final file
                    transform.set_final_file(output_chd)
                    print(f"✓ Converted and recorded: {output_chd.name}")
                else:
                    print(f"✗ Conversion failed: {result.stderr.decode()}")
        
        # Show statistics
        recorder.print_stats()

if __name__ == "__main__":
    process_saturn_collection()
```

### What Gets Recorded

For "3D Baseball (USA)":
```
Source File:
  Name: 3D Baseball (USA).cue
  MD5:  4d9347b77d53c8f366f787cc9ba5ef9a (from Redump DAT)
  Size: 337 MB
  Format: cue

Transformation:
  Tool: chdman v0.251
  Params: {"compression": "zstd", "hunksize": "auto"}
  Duration: 45.2 seconds
  Date: 2025-10-12 01:45:40

Final File:
  Name: 3D Baseball (USA).chd
  MD5:  497af1102b63d9d148e4ba4d119fb64e
  Size: 95.6 MB
  Format: chd
```

### Using Transformations for Scraping

```python
from romfarmer.metadata import MetadataDatabase, TransformationRecorder

def scrape_with_transformation(chd_file: Path):
    db = MetadataDatabase("metadata/database/romfarmer.db")
    
    with db.get_session() as session:
        recorder = TransformationRecorder(session)
        
        # Look up original hash
        transformation = recorder.find_source_hash(chd_file)
        
        if transformation:
            # Use source hash for ScreenScraper query!
            source_md5 = transformation.source_md5
            print(f"CHD hash: {transformation.final_md5}")
            print(f"Source hash: {source_md5}")
            print(f"Use {source_md5} for ScreenScraper lookup!")
            
            # Now ScreenScraper will find it!
            metadata = screenscraper_query(source_md5, system="saturn")
            return metadata
        else:
            print("No transformation found, using direct hash")
            # Fall back to direct hash
            return screenscraper_query_direct(chd_file)
```

## Performance Optimization

### DAT Integration Benefits

Without DAT files:
```
Process 322 Saturn games:
- Calculate 322 source hashes: 322 × 120s = 10.7 hours 😱
- Calculate 322 final hashes: 322 × 0.3s = 1.6 minutes
Total: ~10.7 hours
```

With DAT files:
```
Process 322 Saturn games:
- Look up 322 source hashes in Redump DAT: 322 × 0.001s = 0.3s ⚡
- Calculate 322 final hashes: 322 × 0.3s = 1.6 minutes
Total: ~2 minutes (320x faster!)
```

### Hash Cache Benefits

Second run (after conversion):
```
Process 322 Saturn games again:
- Source hashes: 0.3s (from DAT)
- Final hashes: 322 × 0.001s = 0.3s (from cache) ⚡
Total: ~1 second!
```

## Integration with Existing Tools

### With igir

```python
# After igir processes ROMs
with recorder.record_transformation(
    source_file=original_rom,
    system=system,
    tool="igir",
    version="2.x.x",
    params={"filter": "1g1r", "region": "USA"}
) as transform:
    # igir processes the ROM
    result = run_igir(original_rom, output_dir)
    transform.set_final_file(result.output_file)
```

### With Custom Scripts

```python
# Your existing ROM processing
def my_rom_processor(source: Path, output: Path):
    # ... your processing logic ...
    return output

# Wrap it with transformation tracking
with recorder.record_transformation(
    source_file=source,
    system="xbox360",
    tool="extract-xiso",
    version="custom"
) as transform:
    final = my_rom_processor(source, output)
    transform.set_final_file(final)
```

## Testing Your Integration

### 1. Test with Sample Files

```bash
# Test transformation recording
romfarmer metadata test-transform \
  -d /data/emu/dats/redump \
  -s "/source/saturn/game.cue" \
  -f "/output/saturn/game.chd" \
  --system saturn \
  --tool chdman \
  --version 0.251
```

### 2. Verify Database Records

```bash
# Check transformations
sqlite3 metadata/database/romfarmer.db \
  "SELECT source_file_name, final_file_name, transformation_tool 
   FROM rom_transformations;"
```

### 3. Test Reverse Lookup

```python
# Can you find the source hash?
transformation = recorder.find_source_hash(Path("/output/saturn/game.chd"))
assert transformation is not None
assert transformation.source_md5 == "4d9347b77d53c8f366f787cc9ba5ef9a"
```

## System-Specific Examples

### Xbox 360 (XISO)

```python
with recorder.record_transformation(
    source_file=Path("/source/xbox360/game.iso"),
    system="xbox360",
    tool="extract-xiso",
    version="2.7.1",
    params={"extract": True}
) as transform:
    # Extract XISO
    result = subprocess.run(["extract-xiso", str(source_file)])
    transform.set_final_file(Path("/output/xbox360/game.xiso"))
```

### PS3 (Decrypted)

```python
with recorder.record_transformation(
    source_file=Path("/source/ps3/game_encrypted.iso"),
    system="ps3",
    tool="PS3Dec",
    version="1.0",
    params={"decrypt": True}
) as transform:
    # Decrypt ISO
    decrypted = decrypt_ps3_iso(source_file)
    transform.set_final_file(decrypted)
```

### PSP (CSO)

```python
with recorder.record_transformation(
    source_file=Path("/source/psp/game.iso"),
    system="psp",
    tool="ciso",
    version="1.0",
    params={"compression": 9}
) as transform:
    # Compress to CSO
    result = subprocess.run([
        "ciso", "9", str(source_file), str(output_cso)
    ])
    transform.set_final_file(output_cso)
```

## Next Steps

1. **Integrate with your ROM processing pipeline** - Add transformation recording to your existing scripts
2. **Process your collections** - Run transformations on your Saturn, Xbox 360, PS3 collections
3. **Implement ScreenScraper integration** - Use transformation lookup for metadata queries
4. **Share transformations** - Export your transformation database for the community

## Benefits Summary

✅ **Automatic tracking** - No manual hash management  
✅ **Instant lookups** - DAT integration = 320x speedup  
✅ **Perfect accuracy** - Hash-based matching, not filename  
✅ **Bidirectional** - Source→Final and Final→Source  
✅ **Tool agnostic** - Works with chdman, extract-xiso, etc.  
✅ **Community ready** - Export/import transformation databases  

## Troubleshooting

### "Source hash not found in DAT"
- Normal for non-standard files
- Hash will be calculated (slower but still works)
- Consider adding to community database

### "Transformation already exists"
- System updates existing record
- Check if you're reprocessing the same files

### "Final file not set"
- Make sure to call `transform.set_final_file(final_file)`
- File must exist before calling

## See Also

- [ROM_TRANSFORMATION_TRACKING.md](ROM_TRANSFORMATION_TRACKING.md) - Complete design document
- [INSTALLATION.md](INSTALLATION.md) - Setup instructions
- [API Documentation](API.md) - Detailed API reference
