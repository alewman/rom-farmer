# Processor Architecture

## Overview

While **parsers** understand naming conventions, **processors** handle the file transformations and workflows specific to each ROM type.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          ROM Processing Pipeline                     │
└─────────────────────────────────────────────────────────────────────┘

Input File → Parser → Processor → Validator → Output
             ↓        ↓           ↓            ↓
          (metadata) (transform)  (verify)   (organized)
```

## Parser vs Processor

| Component | Responsibility | Examples |
|-----------|----------------|----------|
| **Parser** | Extract metadata from filename | regions, languages, disc numbers |
| **Processor** | Transform files for system | extract, convert, create playlists |

## Processor Types

### 1. CartridgeProcessor (No-Intro)
**Used for**: Cartridge-based systems (GB, GBA, NES, SNES, etc.)

**Workflow**:
```python
class CartridgeProcessor(BaseProcessor):
    """
    Simple processor for cartridge ROMs.
    Usually just extraction - no format conversion needed.
    """
    
    async def process(self, rom: Rom) -> ProcessedRom:
        # 1. Extract if needed (.zip → .gb, .gba, .nes, etc.)
        if rom.path.suffix == '.zip':
            extracted = await self.extract_archive(rom.path)
            rom.path = extracted
        
        # 2. Verify integrity
        await self.verify_hash(rom)
        
        # 3. Done! Cartridge ROMs are ready as-is
        return ProcessedRom(
            original=rom,
            processed_path=rom.path,
            format=rom.path.suffix,
            transformations=["extracted"]
        )
```

**No conversion needed because**:
- `.gb`, `.gba`, `.nes`, `.smd` are already optimal formats
- Emulators read them directly
- No multi-file complications

### 2. DiscProcessor (Redump)
**Used for**: Disc-based systems (PS1, PS2, Dreamcast, Sega CD, etc.)

**Workflow**:
```python
class DiscProcessor(BaseProcessor):
    """
    Complex processor for disc-based ROMs.
    Handles format conversion and multi-disc playlists.
    """
    
    async def process(self, rom: Rom) -> ProcessedRom:
        # 1. Extract archive
        if rom.path.suffix in ['.zip', '.7z']:
            extracted_dir = await self.extract_archive(rom.path)
        
        # 2. Convert format (.bin/.cue → .chd)
        if self.config.disc_format == 'chd':
            chd_file = await self.convert_to_chd(
                cue_file=find_cue_file(extracted_dir)
            )
        
        # 3. Handle multi-disc games
        if rom.disc_total and rom.disc_total > 1:
            # Create .m3u playlist
            m3u_file = await self.create_m3u_playlist(
                game_title=rom.title,
                disc_number=rom.disc_number,
                disc_total=rom.disc_total
            )
            return ProcessedRom(
                original=rom,
                processed_path=m3u_file,  # Point to playlist
                format='.m3u',
                disc_files=[chd_file],
                transformations=["extracted", "converted_chd", "created_m3u"]
            )
        
        # 4. Single disc
        return ProcessedRom(
            original=rom,
            processed_path=chd_file,
            format='.chd',
            transformations=["extracted", "converted_chd"]
        )
```

**Complex because**:
- Need format conversion (`.bin/.cue` → `.chd` for space)
- Multi-disc games need `.m3u` playlists
- May need to merge tracks for some systems

### 3. ISOProcessor (Optional)
**Used for**: Systems that use ISO format (PSP, some Dreamcast)

**Workflow**:
```python
class ISOProcessor(BaseProcessor):
    """
    Processor for ISO-based systems.
    May need CSO compression for PSP.
    """
    
    async def process(self, rom: Rom) -> ProcessedRom:
        # 1. Extract
        if rom.path.suffix in ['.zip', '.7z']:
            iso_file = await self.extract_archive(rom.path)
        
        # 2. Optional: Compress to CSO (PSP)
        if self.config.compress_psp:
            cso_file = await self.compress_to_cso(iso_file)
            return ProcessedRom(
                original=rom,
                processed_path=cso_file,
                format='.cso',
                transformations=["extracted", "compressed_cso"]
            )
        
        return ProcessedRom(
            original=rom,
            processed_path=iso_file,
            format='.iso',
            transformations=["extracted"]
        )
```

## Factory Pattern

```python
# processors/__init__.py

from .base import BaseProcessor
from .cartridge import CartridgeProcessor
from .disc import DiscProcessor
from .iso import ISOProcessor

_PROCESSORS: dict[str, type[BaseProcessor]] = {
    'cartridge': CartridgeProcessor,
    'disc': DiscProcessor,
    'iso': ISOProcessor,
}

def get_processor(parser_type: str, config: ProcessorConfig) -> BaseProcessor:
    """Get processor based on parser type."""
    # Map parser types to processor types
    processor_map = {
        'nointro': 'cartridge',  # No-Intro → Cartridge
        'redump': 'disc',        # Redump → Disc
        'iso': 'iso',            # ISO systems
    }
    
    processor_type = processor_map.get(parser_type, 'cartridge')
    processor_class = _PROCESSORS[processor_type]
    return processor_class(config)
```

## Configuration

```python
# config.py

class ProcessorConfig:
    """Configuration for ROM processors."""
    
    # Disc format conversion
    disc_format: Literal['chd', 'bin/cue', 'keep'] = 'chd'
    
    # M3U playlist creation
    create_m3u: bool = True
    m3u_template: str = "{title}.m3u"
    
    # PSP compression
    compress_psp: bool = True
    
    # Archive extraction
    extract_archives: bool = True
    archive_formats: list[str] = ['.zip', '.7z', '.rar']
    
    # Temporary directory
    temp_dir: Path = Path("/tmp/romgroomer")
    
    # Keep intermediate files (for debugging)
    keep_intermediates: bool = False
```

## Usage Example

```python
from romgroomer.parsers import get_parser, get_parser_for_file
from romgroomer.processors import get_processor
from romgroomer.config import ProcessorConfig

async def process_rom(rom_path: Path):
    # 1. Parse filename
    parser = get_parser_for_file(rom_path)
    rom = parser.parse(rom_path.name)
    
    # 2. Get appropriate processor
    config = ProcessorConfig(disc_format='chd', create_m3u=True)
    processor = get_processor(parser.name, config)
    
    # 3. Process the ROM
    processed = await processor.process(rom)
    
    print(f"✓ Processed: {rom.title}")
    print(f"  Format: {processed.format}")
    print(f"  Steps: {', '.join(processed.transformations)}")
    print(f"  Output: {processed.processed_path}")
```

**Example outputs**:

```
# Cartridge ROM (No-Intro)
✓ Processed: Super Mario Bros.
  Format: .nes
  Steps: extracted
  Output: /roms/nes/Super Mario Bros (USA).nes

# Single disc (Redump)
✓ Processed: Metal Gear Solid
  Format: .chd
  Steps: extracted, converted_chd
  Output: /roms/psx/Metal Gear Solid (USA).chd

# Multi-disc (Redump)
✓ Processed: Final Fantasy VII
  Format: .m3u
  Steps: extracted, converted_chd, created_m3u
  Output: /roms/psx/Final Fantasy VII (USA).m3u
  Discs:
    - Final Fantasy VII (USA) (Disc 1).chd
    - Final Fantasy VII (USA) (Disc 2).chd
    - Final Fantasy VII (USA) (Disc 3).chd
```

## Benefits

### 1. **Separation of Concerns**
- Parsers: Understand naming
- Processors: Transform files
- Each does one thing well

### 2. **Type-Specific Workflows**
- Cartridge ROMs: Simple extraction
- Disc ROMs: Conversion + playlists
- ISO ROMs: Optional compression
- Each type gets appropriate treatment

### 3. **Extensibility**
- Add new processor types easily
- Configure behavior per system
- Test each processor independently

### 4. **Configuration Control**
```yaml
# config.yaml
processors:
  disc:
    format: chd           # or 'bin/cue', 'keep'
    create_m3u: true
  
  iso:
    compress_psp: true    # CSO for PSP
  
  cartridge:
    extract: true         # Just extract, no conversion
```

## Implementation Priority

### Phase 2a (Current)
- [ ] BaseProcessor abstract class
- [ ] CartridgeProcessor (simple)
- [ ] Basic processor factory

### Phase 2b (Next)
- [ ] DiscProcessor with CHD conversion
- [ ] M3U playlist creation
- [ ] Multi-disc detection

### Phase 2c (Future)
- [ ] ISOProcessor with CSO compression
- [ ] Advanced track merging
- [ ] System-specific optimizations

## Real-World Example

**Input**: `Final Fantasy VII (USA) (Disc 1).zip`

**Cartridge Parser** would say: "Not my job!" ❌

**Disc Parser** would say:
```python
Rom(
    title="Final Fantasy VII",
    regions=['usa'],
    disc_number=1,
    disc_total=3,  # Detected from other files
    languages=None
)
```

**Disc Processor** would:
1. Extract `.zip` → get `.bin` + `.cue`
2. Convert `.bin/.cue` → `.chd`
3. See `disc_number=1` and `disc_total=3`
4. Create `Final Fantasy VII (USA).m3u`:
   ```
   Final Fantasy VII (USA) (Disc 1).chd
   Final Fantasy VII (USA) (Disc 2).chd
   Final Fantasy VII (USA) (Disc 3).chd
   ```
5. Return the `.m3u` as final output

**EmulationStation** sees one game: `Final Fantasy VII.m3u` ✓

## Summary

> **Yes, different parsers can trigger different processors with completely different workflows!**

- **No-Intro** → CartridgeProcessor → Simple extraction
- **Redump** → DiscProcessor → CHD conversion + M3U playlists
- **ISO systems** → ISOProcessor → CSO compression (optional)

This is the **power of the architecture** you requested - enterprise-grade and extensible! 🚀
