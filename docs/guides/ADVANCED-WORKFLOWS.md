# Advanced ROM Processing Workflows

## The Challenge

Different systems need different transformations, and **different emulators need different output formats** for the same system!

### Real-World Examples

#### PS3 Games
- **Source**: Encrypted `.pkg` or disc dumps
- **Batocera**: Wants `.sqfs` (SquashFS compressed)
- **RPCS3**: Wants `.jb` folder format (decrypted game files)
- **Both need**: Decryption step first!

#### Xbox 360
- **Source**: ISO images (encrypted)
- **Needs**: Decryption with `xbox360_decrypt`
- **Output**: Extracted game folder or `.xex` executable

#### Wii U
- **Source**: Various formats (`.wud`, `.wux`, loadiine)
- **Cemu**: Wants decrypted loadiine format
- **Needs**: Title key extraction + decryption

#### PSP
- **Source**: `.iso` files
- **Option 1**: Keep as `.iso` (compatible, large)
- **Option 2**: Convert to `.cso` (compressed, smaller)
- **Choice**: User preference!

## Solution: Multi-Stage Pipelines with Platform Profiles

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Configurable Processing Pipeline                 │
└─────────────────────────────────────────────────────────────────────┘

Input File → [Stage 1] → [Stage 2] → [Stage 3] → Output
             ↓          ↓           ↓            ↓
          Extract    Decrypt     Convert      Final Format
                                             (platform-specific)
```

## Architecture

### 1. Processing Stages (Building Blocks)

```python
# processors/stages.py

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

class ProcessingStage(ABC):
    """Base class for a single processing stage."""
    
    @abstractmethod
    async def process(self, input_path: Path, context: dict) -> Path:
        """
        Process input and return output path.
        
        Args:
            input_path: File or directory to process
            context: Shared context between stages
            
        Returns:
            Path to processed output
        """
        pass
    
    @abstractmethod
    def can_process(self, input_path: Path) -> bool:
        """Check if this stage can process the input."""
        pass


# ============================================================================
# EXTRACTION STAGES
# ============================================================================

class ExtractArchiveStage(ProcessingStage):
    """Extract .zip, .7z, .rar archives."""
    
    async def process(self, input_path: Path, context: dict) -> Path:
        if input_path.suffix in ['.zip', '.7z', '.rar']:
            extract_dir = context['temp_dir'] / input_path.stem
            await self._extract(input_path, extract_dir)
            return extract_dir
        return input_path
    
    def can_process(self, input_path: Path) -> bool:
        return input_path.suffix in ['.zip', '.7z', '.rar']


# ============================================================================
# DECRYPTION STAGES
# ============================================================================

class PS3DecryptStage(ProcessingStage):
    """Decrypt PS3 games using PS3Dec."""
    
    def __init__(self, ps3dec_path: Path):
        self.ps3dec_path = ps3dec_path
    
    async def process(self, input_path: Path, context: dict) -> Path:
        """
        Decrypt PS3 game files.
        
        Input: Encrypted game folder or .pkg
        Output: Decrypted game folder
        """
        output_dir = context['temp_dir'] / f"{input_path.stem}_decrypted"
        
        # Run PS3Dec
        await self._run_command([
            str(self.ps3dec_path),
            "d",  # decrypt mode
            "key", context.get('rap_file'),  # RAP/RIF file for license
            str(input_path),
            str(output_dir)
        ])
        
        return output_dir
    
    def can_process(self, input_path: Path) -> bool:
        # Check for PS3 game structure
        return (input_path / "PS3_GAME").exists() or input_path.suffix == '.pkg'


class Xbox360DecryptStage(ProcessingStage):
    """Decrypt Xbox 360 ISOs."""
    
    async def process(self, input_path: Path, context: dict) -> Path:
        """
        Decrypt Xbox 360 ISO.
        
        Input: Encrypted .iso
        Output: Decrypted .iso
        """
        output_file = context['temp_dir'] / f"{input_path.stem}_decrypted.iso"
        
        # Use xbox360_decrypt or similar tool
        await self._run_command([
            "xbox360_decrypt",
            str(input_path),
            str(output_file)
        ])
        
        return output_file
    
    def can_process(self, input_path: Path) -> bool:
        return input_path.suffix == '.iso' and self._is_xbox360_iso(input_path)


class WiiUDecryptStage(ProcessingStage):
    """Decrypt Wii U games."""
    
    def __init__(self, keys_path: Path):
        self.keys_path = keys_path
    
    async def process(self, input_path: Path, context: dict) -> Path:
        """
        Decrypt Wii U game.
        
        Input: .wud, .wux, or encrypted loadiine
        Output: Decrypted loadiine format
        """
        output_dir = context['temp_dir'] / f"{input_path.stem}_decrypted"
        
        # Use CDecrypt or similar
        await self._run_command([
            "cdecrypt",
            "--keys", str(self.keys_path),
            str(input_path),
            str(output_dir)
        ])
        
        return output_dir
    
    def can_process(self, input_path: Path) -> bool:
        return input_path.suffix in ['.wud', '.wux'] or \
               (input_path.is_dir() and (input_path / "code").exists())


# ============================================================================
# CONVERSION STAGES
# ============================================================================

class BinCueToChd(ProcessingStage):
    """Convert .bin/.cue to .chd format."""
    
    async def process(self, input_path: Path, context: dict) -> Path:
        """
        Convert disc image to CHD.
        
        Input: .cue file (with associated .bin)
        Output: .chd file
        """
        output_file = context['output_dir'] / f"{input_path.stem}.chd"
        
        await self._run_command([
            "chdman",
            "createcd",
            "-i", str(input_path),
            "-o", str(output_file)
        ])
        
        return output_file
    
    def can_process(self, input_path: Path) -> bool:
        return input_path.suffix == '.cue'


class IsoToCso(ProcessingStage):
    """Compress ISO to CSO (PSP)."""
    
    def __init__(self, compression_level: int = 9):
        self.compression_level = compression_level
    
    async def process(self, input_path: Path, context: dict) -> Path:
        """
        Compress ISO to CSO.
        
        Input: .iso file
        Output: .cso file (compressed)
        """
        output_file = context['output_dir'] / f"{input_path.stem}.cso"
        
        await self._run_command([
            "ciso",
            str(self.compression_level),
            str(input_path),
            str(output_file)
        ])
        
        return output_file
    
    def can_process(self, input_path: Path) -> bool:
        return input_path.suffix == '.iso'


class PS3ToSquashFS(ProcessingStage):
    """Convert PS3 game folder to SquashFS (Batocera format)."""
    
    async def process(self, input_path: Path, context: dict) -> Path:
        """
        Create SquashFS archive from PS3 game.
        
        Input: Decrypted PS3 game folder
        Output: .sqfs file
        """
        output_file = context['output_dir'] / f"{input_path.stem}.sqfs"
        
        await self._run_command([
            "mksquashfs",
            str(input_path),
            str(output_file),
            "-comp", "zstd",  # Use zstd compression
            "-Xcompression-level", "19"
        ])
        
        return output_file
    
    def can_process(self, input_path: Path) -> bool:
        # Check for PS3 game structure
        return input_path.is_dir() and (input_path / "PS3_GAME").exists()


# ============================================================================
# FINALIZATION STAGES
# ============================================================================

class CreateM3uPlaylist(ProcessingStage):
    """Create .m3u playlist for multi-disc games."""
    
    async def process(self, input_path: Path, context: dict) -> Path:
        """
        Create M3U playlist.
        
        Input: First disc file
        Output: .m3u playlist file
        """
        rom = context['rom']
        if not rom.disc_total or rom.disc_total <= 1:
            return input_path
        
        # Find all discs for this game
        disc_files = self._find_disc_files(rom, context['output_dir'])
        
        # Create .m3u file
        m3u_file = context['output_dir'] / f"{rom.title}.m3u"
        with m3u_file.open('w') as f:
            for disc_file in sorted(disc_files):
                f.write(f"{disc_file.name}\n")
        
        context['disc_files'] = disc_files
        return m3u_file
    
    def can_process(self, input_path: Path) -> bool:
        rom = context.get('rom')
        return rom and rom.disc_total and rom.disc_total > 1
```

### 2. Platform Profiles (Configuration)

```python
# processors/profiles.py

from dataclasses import dataclass, field
from typing import List, Literal, Optional

@dataclass
class PlatformProfile:
    """Configuration for platform-specific processing."""
    
    name: str
    description: str
    
    # Pipeline stages (in order)
    stages: List[str]
    
    # Output format
    output_format: str
    
    # Stage-specific configuration
    stage_config: dict = field(default_factory=dict)


# ============================================================================
# CARTRIDGE PROFILES
# ============================================================================

PROFILE_NES = PlatformProfile(
    name="nes",
    description="Nintendo Entertainment System",
    stages=["extract_archive"],
    output_format=".nes",
)

PROFILE_GBA = PlatformProfile(
    name="gba",
    description="Game Boy Advance",
    stages=["extract_archive"],
    output_format=".gba",
)

# ============================================================================
# DISC PROFILES (SIMPLE)
# ============================================================================

PROFILE_PSX_CHD = PlatformProfile(
    name="psx_chd",
    description="PlayStation 1 (CHD format)",
    stages=[
        "extract_archive",
        "bin_cue_to_chd",
        "create_m3u_playlist",
    ],
    output_format=".m3u",  # or .chd for single disc
)

PROFILE_DREAMCAST_CHD = PlatformProfile(
    name="dreamcast_chd",
    description="Dreamcast (CHD format)",
    stages=[
        "extract_archive",
        "gdi_to_chd",  # Dreamcast uses .gdi
        "create_m3u_playlist",
    ],
    output_format=".chd",
)

# ============================================================================
# ADVANCED PROFILES (WITH DECRYPTION)
# ============================================================================

PROFILE_PS3_BATOCERA = PlatformProfile(
    name="ps3_batocera",
    description="PlayStation 3 (Batocera - SquashFS format)",
    stages=[
        "extract_archive",
        "ps3_decrypt",
        "ps3_to_squashfs",
    ],
    output_format=".sqfs",
    stage_config={
        "ps3_decrypt": {
            "ps3dec_path": "/data/emu/bin/PS3Dec",
            "rap_files_dir": "/data/emu/keys/ps3",
        },
        "ps3_to_squashfs": {
            "compression": "zstd",
            "compression_level": 19,
        },
    },
)

PROFILE_PS3_RPCS3 = PlatformProfile(
    name="ps3_rpcs3",
    description="PlayStation 3 (RPCS3 - folder format)",
    stages=[
        "extract_archive",
        "ps3_decrypt",
        # No conversion - keep as folder
    ],
    output_format=".jb",  # Actually a folder, but marked as .jb format
    stage_config={
        "ps3_decrypt": {
            "ps3dec_path": "/data/emu/bin/PS3Dec",
            "rap_files_dir": "/data/emu/keys/ps3",
        },
    },
)

PROFILE_XBOX360 = PlatformProfile(
    name="xbox360",
    description="Xbox 360 (decrypted)",
    stages=[
        "extract_archive",
        "xbox360_decrypt",
        "extract_xbox360_iso",  # Extract to folder
    ],
    output_format=".xex",  # Folder with default.xex
    stage_config={
        "xbox360_decrypt": {
            "verify_signature": True,
        },
    },
)

PROFILE_WIIU_CEMU = PlatformProfile(
    name="wiiu_cemu",
    description="Wii U (Cemu - loadiine format)",
    stages=[
        "extract_archive",
        "wiiu_decrypt",
        # Output is loadiine format folder
    ],
    output_format=".loadiine",  # Folder structure
    stage_config={
        "wiiu_decrypt": {
            "keys_path": "/data/emu/keys/wiiu/keys.txt",
            "output_format": "loadiine",
        },
    },
)

# ============================================================================
# PSP PROFILES (USER CHOICE)
# ============================================================================

PROFILE_PSP_ISO = PlatformProfile(
    name="psp_iso",
    description="PSP (ISO - uncompressed)",
    stages=["extract_archive"],
    output_format=".iso",
)

PROFILE_PSP_CSO = PlatformProfile(
    name="psp_cso",
    description="PSP (CSO - compressed)",
    stages=[
        "extract_archive",
        "iso_to_cso",
    ],
    output_format=".cso",
    stage_config={
        "iso_to_cso": {
            "compression_level": 9,
        },
    },
)

# ============================================================================
# PROFILE REGISTRY
# ============================================================================

PROFILES = {
    # Cartridge systems
    "nes": PROFILE_NES,
    "gba": PROFILE_GBA,
    
    # Disc systems (simple)
    "psx": PROFILE_PSX_CHD,
    "dreamcast": PROFILE_DREAMCAST_CHD,
    
    # Advanced systems (multiple profiles)
    "ps3_batocera": PROFILE_PS3_BATOCERA,
    "ps3_rpcs3": PROFILE_PS3_RPCS3,
    "xbox360": PROFILE_XBOX360,
    "wiiu": PROFILE_WIIU_CEMU,
    
    # User choice systems
    "psp_iso": PROFILE_PSP_ISO,
    "psp_cso": PROFILE_PSP_CSO,
}


def get_profile(name: str) -> PlatformProfile:
    """Get a platform profile by name."""
    if name not in PROFILES:
        raise ValueError(f"Unknown profile: {name}")
    return PROFILES[name]


def list_profiles(system: Optional[str] = None) -> List[PlatformProfile]:
    """
    List available profiles.
    
    Args:
        system: Optional system filter (e.g., "ps3" returns ps3_batocera and ps3_rpcs3)
    """
    if system:
        return [p for name, p in PROFILES.items() if name.startswith(system)]
    return list(PROFILES.values())
```

### 3. Pipeline Processor

```python
# processors/pipeline.py

from pathlib import Path
from typing import List, Optional
from rich.progress import Progress, TaskID

from .stages import ProcessingStage
from .profiles import PlatformProfile, get_profile


class PipelineProcessor:
    """
    Execute a multi-stage processing pipeline.
    
    This is the main processor that orchestrates stages based on a profile.
    """
    
    def __init__(self, profile: PlatformProfile, stages: dict[str, ProcessingStage]):
        """
        Initialize pipeline processor.
        
        Args:
            profile: Platform profile defining the pipeline
            stages: Registered processing stages
        """
        self.profile = profile
        self.stages = stages
    
    async def process(
        self,
        input_path: Path,
        output_dir: Path,
        rom: Optional[object] = None,
        progress: Optional[Progress] = None,
        task: Optional[TaskID] = None,
    ) -> ProcessedRom:
        """
        Execute the processing pipeline.
        
        Args:
            input_path: Input file or directory
            output_dir: Output directory
            rom: ROM metadata (from parser)
            progress: Optional Rich progress bar
            task: Optional progress task ID
            
        Returns:
            ProcessedRom with final output path and metadata
        """
        # Setup context shared between stages
        context = {
            'rom': rom,
            'temp_dir': output_dir / ".temp",
            'output_dir': output_dir,
            'profile': self.profile,
            'transformations': [],
        }
        context['temp_dir'].mkdir(exist_ok=True)
        
        current_path = input_path
        
        # Execute each stage in order
        for i, stage_name in enumerate(self.profile.stages):
            stage = self.stages.get(stage_name)
            if not stage:
                raise ValueError(f"Unknown stage: {stage_name}")
            
            # Update progress
            if progress and task:
                progress.update(
                    task,
                    description=f"[cyan]{stage_name}[/cyan]",
                    completed=i,
                    total=len(self.profile.stages),
                )
            
            # Check if stage can process current path
            if not stage.can_process(current_path):
                continue
            
            # Apply stage-specific config
            if stage_name in self.profile.stage_config:
                stage.configure(self.profile.stage_config[stage_name])
            
            # Execute stage
            current_path = await stage.process(current_path, context)
            context['transformations'].append(stage_name)
        
        # Cleanup temp directory
        if not context.get('keep_intermediates', False):
            shutil.rmtree(context['temp_dir'], ignore_errors=True)
        
        return ProcessedRom(
            original=rom,
            original_path=input_path,
            processed_path=current_path,
            format=self.profile.output_format,
            transformations=context['transformations'],
            disc_files=context.get('disc_files', []),
            metadata=context.get('metadata', {}),
        )
```

### 4. User Configuration

```yaml
# config.yaml

processors:
  # Default profile per system
  profiles:
    psx: psx_chd
    ps3: ps3_batocera      # or ps3_rpcs3 for RPCS3 users
    xbox360: xbox360
    wiiu: wiiu_cemu
    psp: psp_cso           # or psp_iso for uncompressed
    dreamcast: dreamcast_chd
  
  # Tool paths
  tools:
    ps3dec: /data/emu/bin/PS3Dec
    chdman: /usr/bin/chdman
    ciso: /usr/bin/ciso
    mksquashfs: /usr/bin/mksquashfs
  
  # Key/license files
  keys:
    ps3_rap: /data/emu/keys/ps3
    wiiu_keys: /data/emu/keys/wiiu/keys.txt
  
  # Processing options
  options:
    keep_intermediates: false  # Keep temp files for debugging
    verify_hashes: true         # Verify after processing
    parallel_processing: 4      # Process 4 ROMs at once
```

### 5. CLI Usage

```bash
# Use default profile for system
romfarmer process --system ps3 "Gran Turismo 5.pkg"

# Specify custom profile
romfarmer process --profile ps3_rpcs3 "Gran Turismo 5.pkg"

# List available profiles for a system
romfarmer profiles --system ps3
# Output:
#   ps3_batocera - PlayStation 3 (Batocera - SquashFS format)
#   ps3_rpcs3    - PlayStation 3 (RPCS3 - folder format)

# Batch processing with profile
romfarmer batch --profile ps3_batocera /path/to/ps3/roms/

# Show what a profile will do (dry-run)
romfarmer process --profile ps3_batocera --dry-run "game.pkg"
# Output:
#   Pipeline for profile 'ps3_batocera':
#   1. extract_archive    - Extract .pkg archive
#   2. ps3_decrypt        - Decrypt PS3 game files
#   3. ps3_to_squashfs    - Create SquashFS archive
#   
#   Output: game.sqfs (SquashFS format)
```

### 6. Example Workflow

```python
from romfarmer.processors.pipeline import PipelineProcessor
from romfarmer.processors.profiles import get_profile
from romfarmer.processors.stages import *

# Setup stages
stages = {
    'extract_archive': ExtractArchiveStage(),
    'ps3_decrypt': PS3DecryptStage(Path("/data/emu/bin/PS3Dec")),
    'ps3_to_squashfs': PS3ToSquashFS(),
}

# Get profile
profile = get_profile('ps3_batocera')

# Create processor
processor = PipelineProcessor(profile, stages)

# Process a game
result = await processor.process(
    input_path=Path("Gran Turismo 5.pkg"),
    output_dir=Path("/roms/ps3/"),
)

print(f"✓ {result.original.title}")
print(f"  Format: {result.format}")
print(f"  Steps: {' → '.join(result.transformations)}")
print(f"  Output: {result.processed_path}")

# Output:
#   ✓ Gran Turismo 5
#     Format: .sqfs
#     Steps: extract_archive → ps3_decrypt → ps3_to_squashfs
#     Output: /roms/ps3/Gran Turismo 5.sqfs
```

## Benefits

### 1. **Flexible for Different Emulators**
```yaml
# Batocera user
profiles:
  ps3: ps3_batocera  # SquashFS format

# RPCS3 user
profiles:
  ps3: ps3_rpcs3     # Folder format
```

### 2. **Composable Stages**
- Each stage is independent and testable
- Add new stages without changing existing ones
- Reuse stages across profiles

### 3. **Clear Pipeline**
```
PS3 Batocera:  extract → decrypt → squashfs
PS3 RPCS3:     extract → decrypt
Xbox 360:      extract → decrypt → extract_iso
PSP CSO:       extract → iso_to_cso
PSP ISO:       extract
```

### 4. **User Control**
- Choose profile per system
- Override default profile
- See what will happen before processing

### 5. **Extensible**
Need a new system? Just add:
1. New stages (if needed)
2. New profile
3. Update config

## Summary

> **The key insight**: Different emulators need different outputs for the **same system**.

**Solution**:
- ✅ **Stages**: Modular, composable transformation steps
- ✅ **Profiles**: System + emulator-specific pipelines
- ✅ **Configuration**: User chooses what they need
- ✅ **Pipeline Processor**: Orchestrates everything

This handles all your tricky cases:
- PS3 → Batocera (.sqfs) vs RPCS3 (.jb folder)
- Xbox 360 decryption
- Wii U decryption + format conversion
- PSP compression choice
- Multi-disc playlists
- And anything else we need!

🚀 Ready to implement this?
