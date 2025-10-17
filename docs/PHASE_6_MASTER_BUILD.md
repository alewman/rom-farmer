# Phase 6: Master Build Orchestrator

**Date:** October 17, 2025  
**Goal:** Create unified build system to process multiple platforms automatically  
**Target:** ROM Groomer 1.0 release

---

## Overview

**Purpose:** Transform `romgroomer` from single-platform tool to multi-platform build orchestrator.

**Current State:**
- ✅ 4 platforms working (Saturn, Wii, GameCube, PS3)
- ✅ Individual platform configs exist
- ✅ Stages are modular and reusable
- ❌ No orchestration layer (must run platforms manually)

**Target State:**
```bash
# Single command to build entire collection
romgroomer build batocera-complete

# Or specific platforms
romgroomer build batocera-complete --platforms saturn,wii,ps3

# Resume after failure
romgroomer resume batocera-complete

# Check status
romgroomer status batocera-complete
```

---

## Architecture

### Component Hierarchy

```
Master Build Config (YAML)
    ├── Build Profile (batocera-complete, rocknix-2tb, etc.)
    │   ├── Enabled platforms
    │   ├── Global settings
    │   └── Storage constraints
    │
    ├── Build Orchestrator
    │   ├── Load profile + platform configs
    │   ├── Validate sources/storage
    │   ├── Process platforms sequentially
    │   ├── Track progress
    │   └── Handle errors
    │
    └── Platform Processors (existing)
        ├── Saturn (existing)
        ├── Wii (existing)
        ├── GameCube (existing)
        └── PS3 (existing)
```

### Data Flow

```
User runs: romgroomer build batocera-complete
    ↓
Load: config/builds/batocera-complete.yaml
    ↓
Validate: Check sources, storage, tools
    ↓
For each platform:
    ├── Load: config/platforms/{platform}.yaml
    ├── Process: Run platform-specific stages
    ├── Track: Record progress/errors
    └── Continue or stop on error
    ↓
Complete: Generate report, cleanup
```

---

## Implementation Plan

### Phase 6A: Build Configuration System (2 days)

**Goal:** Create master build configs and validation

**Files to create:**
```
config/builds/
├── batocera-complete.yaml    # All platforms for Batocera
├── rocknix-2tb.yaml          # Subset for RocknIX 2TB drive
└── template.yaml             # Template for new builds
```

**Schema:**
```yaml
# config/builds/batocera-complete.yaml
name: batocera-complete
description: "Complete ROM collection for Batocera (PS2 and below)"
version: "1.0"

# Global settings
settings:
  parallel: false              # Process sequentially for now
  stop_on_error: false         # Continue even if one platform fails
  cleanup_temp: true           # Delete temp files after each platform
  verify_outputs: true         # Verify files after creation

# Storage management
storage:
  temp_path: /data/emu/temp
  max_temp_size: 100GB         # Fail if temp exceeds this
  output_base: /data/emu/output/batocera
  max_output_size: 2TB         # Warn if approaching limit
  reserve_space: 50GB          # Keep this much free

# Platforms to process (in order)
platforms:
  # Already implemented
  - saturn
  - wii
  - gamecube
  - ps3
  
  # Phase 6B: Simple cartridge systems
  - nes
  - snes
  - genesis
  - n64
  - gba
  
  # Phase 6C: Additional CD/DVD
  - ps1
  - ps2
  - psp

# Platform-specific overrides (optional)
platform_overrides:
  ps3:
    targets: [batocera]        # Only Batocera target, not all 4
  saturn:
    compression_level: 5       # Faster compression for testing
```

**Validation checks:**
1. All platforms have configs in `config/platforms/`
2. All source directories exist
3. Required tools are installed
4. Sufficient storage available
5. No output conflicts

---

### Phase 6B: Build Orchestrator (3 days)

**Goal:** Core orchestration logic

**File:** `src/romgroomer/build_orchestrator.py`

```python
"""
Master build orchestrator for multi-platform ROM processing.
"""

from pathlib import Path
from typing import List, Dict, Optional
import yaml
import logging
from dataclasses import dataclass
from datetime import datetime

from romgroomer.platform_processor import PlatformProcessor
from romgroomer.storage import StorageManager
from romgroomer.progress import ProgressTracker


@dataclass
class BuildConfig:
    """Master build configuration."""
    name: str
    description: str
    version: str
    settings: Dict
    storage: Dict
    platforms: List[str]
    platform_overrides: Dict = None


@dataclass
class BuildState:
    """Current build state for resume capability."""
    build_name: str
    started_at: datetime
    completed_platforms: List[str]
    failed_platforms: List[str]
    current_platform: Optional[str]
    status: str  # running, paused, completed, failed


class BuildOrchestrator:
    """
    Orchestrates multi-platform ROM builds.
    
    Features:
    - Sequential platform processing
    - Progress tracking
    - Error handling and recovery
    - Storage management
    - Resume capability
    """
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config: BuildConfig = self._load_config()
        self.state: BuildState = self._load_or_create_state()
        
        self.storage = StorageManager(self.config.storage)
        self.progress = ProgressTracker(self.config.name)
        self.logger = logging.getLogger(__name__)
    
    def _load_config(self) -> BuildConfig:
        """Load and validate build configuration."""
        with open(self.config_path) as f:
            data = yaml.safe_load(f)
        
        # Validate schema
        required = ['name', 'description', 'platforms', 'storage']
        for field in required:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        return BuildConfig(**data)
    
    def _load_or_create_state(self) -> BuildState:
        """Load existing build state or create new."""
        state_file = Path(f".build_state_{self.config.name}.yaml")
        
        if state_file.exists():
            with open(state_file) as f:
                data = yaml.safe_load(f)
            return BuildState(**data)
        
        return BuildState(
            build_name=self.config.name,
            started_at=datetime.now(),
            completed_platforms=[],
            failed_platforms=[],
            current_platform=None,
            status='not_started'
        )
    
    def _save_state(self):
        """Persist build state for resume."""
        state_file = Path(f".build_state_{self.config.name}.yaml")
        
        with open(state_file, 'w') as f:
            yaml.dump({
                'build_name': self.state.build_name,
                'started_at': self.state.started_at.isoformat(),
                'completed_platforms': self.state.completed_platforms,
                'failed_platforms': self.state.failed_platforms,
                'current_platform': self.state.current_platform,
                'status': self.state.status
            }, f)
    
    def validate(self) -> bool:
        """
        Validate build can proceed.
        
        Checks:
        - Platform configs exist
        - Source directories exist
        - Tools are installed
        - Storage available
        """
        self.logger.info(f"Validating build: {self.config.name}")
        
        errors = []
        
        # Check platform configs
        for platform in self.config.platforms:
            config_file = Path(f"config/platforms/{platform}.yaml")
            if not config_file.exists():
                errors.append(f"Missing config: {config_file}")
        
        # Check storage
        if not self.storage.validate():
            errors.append("Storage validation failed")
        
        if errors:
            for error in errors:
                self.logger.error(error)
            return False
        
        self.logger.info("✅ Validation passed")
        return True
    
    def run(self, resume: bool = False):
        """
        Run the build.
        
        Args:
            resume: If True, skip already-completed platforms
        """
        if not resume and not self.validate():
            raise ValueError("Build validation failed")
        
        self.state.status = 'running'
        self._save_state()
        
        platforms_to_process = self._get_platforms_to_process(resume)
        
        self.logger.info(f"Starting build: {self.config.name}")
        self.logger.info(f"Platforms: {', '.join(platforms_to_process)}")
        
        for platform in platforms_to_process:
            try:
                self._process_platform(platform)
                self.state.completed_platforms.append(platform)
                self.logger.info(f"✅ {platform} complete")
                
            except Exception as e:
                self.logger.error(f"❌ {platform} failed: {e}")
                self.state.failed_platforms.append(platform)
                
                if self.config.settings.get('stop_on_error', False):
                    self.state.status = 'failed'
                    self._save_state()
                    raise
            
            finally:
                self.state.current_platform = None
                self._save_state()
                
                # Cleanup temp files if configured
                if self.config.settings.get('cleanup_temp', True):
                    self.storage.cleanup_temp()
        
        self.state.status = 'completed'
        self._save_state()
        
        self._generate_report()
    
    def _get_platforms_to_process(self, resume: bool) -> List[str]:
        """Get list of platforms to process."""
        if not resume:
            return self.config.platforms
        
        # Skip already completed
        return [
            p for p in self.config.platforms
            if p not in self.state.completed_platforms
        ]
    
    def _process_platform(self, platform: str):
        """Process a single platform."""
        self.state.current_platform = platform
        self._save_state()
        
        self.logger.info(f"Processing: {platform}")
        
        # Load platform config
        config_path = Path(f"config/platforms/{platform}.yaml")
        
        # Apply overrides if any
        overrides = self.config.platform_overrides.get(platform, {})
        
        # Create processor
        processor = PlatformProcessor(
            config_path=config_path,
            overrides=overrides,
            progress_tracker=self.progress
        )
        
        # Run platform processing
        processor.run()
        
        # Verify outputs if configured
        if self.config.settings.get('verify_outputs', True):
            processor.verify()
    
    def _generate_report(self):
        """Generate build completion report."""
        report_path = Path(f"build_report_{self.config.name}.txt")
        
        with open(report_path, 'w') as f:
            f.write(f"Build Report: {self.config.name}\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Started: {self.state.started_at}\n")
            f.write(f"Completed: {datetime.now()}\n")
            f.write(f"Duration: {datetime.now() - self.state.started_at}\n\n")
            
            f.write(f"Status: {self.state.status}\n\n")
            
            f.write(f"Completed Platforms ({len(self.state.completed_platforms)}):\n")
            for platform in self.state.completed_platforms:
                f.write(f"  ✅ {platform}\n")
            
            if self.state.failed_platforms:
                f.write(f"\nFailed Platforms ({len(self.state.failed_platforms)}):\n")
                for platform in self.state.failed_platforms:
                    f.write(f"  ❌ {platform}\n")
            
            f.write("\n" + "=" * 60 + "\n")
        
        self.logger.info(f"Report saved: {report_path}")
    
    def status(self) -> Dict:
        """Get current build status."""
        total = len(self.config.platforms)
        completed = len(self.state.completed_platforms)
        failed = len(self.state.failed_platforms)
        
        return {
            'build_name': self.config.name,
            'status': self.state.status,
            'current_platform': self.state.current_platform,
            'progress': {
                'total': total,
                'completed': completed,
                'failed': failed,
                'remaining': total - completed - failed,
                'percent': (completed / total * 100) if total > 0 else 0
            },
            'completed_platforms': self.state.completed_platforms,
            'failed_platforms': self.state.failed_platforms
        }
```

**Supporting modules:**

**`src/romgroomer/storage.py`** - Storage management
```python
class StorageManager:
    """Manage storage constraints during build."""
    
    def __init__(self, config: Dict):
        self.temp_path = Path(config['temp_path'])
        self.max_temp_size = self._parse_size(config['max_temp_size'])
        self.output_base = Path(config['output_base'])
        self.max_output_size = self._parse_size(config.get('max_output_size', '10TB'))
        self.reserve_space = self._parse_size(config.get('reserve_space', '50GB'))
    
    def validate(self) -> bool:
        """Check storage requirements."""
        # Check temp directory exists/writable
        # Check available space
        # Return True if OK
        pass
    
    def cleanup_temp(self):
        """Remove temporary files."""
        pass
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string like '100GB' to bytes."""
        pass
```

**`src/romgroomer/progress.py`** - Progress tracking
```python
class ProgressTracker:
    """Track progress across platforms."""
    
    def __init__(self, build_name: str):
        self.build_name = build_name
        self.events = []
    
    def log_event(self, platform: str, stage: str, status: str, details: Dict = None):
        """Log a build event."""
        pass
    
    def get_summary(self) -> Dict:
        """Get progress summary."""
        pass
```

---

### Phase 6C: CLI Integration (2 days)

**Goal:** User-friendly command-line interface

**File:** `src/romgroomer/cli.py`

```python
"""
Command-line interface for ROM Groomer.
"""

import click
from pathlib import Path
import yaml
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

from romgroomer.build_orchestrator import BuildOrchestrator


console = Console()


@click.group()
def cli():
    """ROM Groomer - Multi-platform ROM collection manager."""
    pass


@cli.command()
@click.argument('build_name')
@click.option('--platforms', help='Comma-separated platform list (overrides config)')
@click.option('--resume', is_flag=True, help='Resume interrupted build')
def build(build_name: str, platforms: str = None, resume: bool = False):
    """
    Run a build profile.
    
    Examples:
        romgroomer build batocera-complete
        romgroomer build batocera-complete --platforms saturn,wii
        romgroomer build batocera-complete --resume
    """
    config_path = Path(f"config/builds/{build_name}.yaml")
    
    if not config_path.exists():
        console.print(f"[red]Error: Build config not found: {config_path}[/red]")
        return 1
    
    orchestrator = BuildOrchestrator(config_path)
    
    # Override platforms if specified
    if platforms:
        orchestrator.config.platforms = platforms.split(',')
    
    try:
        orchestrator.run(resume=resume)
        console.print(f"[green]✅ Build complete: {build_name}[/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Build failed: {e}[/red]")
        return 1


@cli.command()
@click.argument('build_name')
def status(build_name: str):
    """
    Show build status.
    
    Examples:
        romgroomer status batocera-complete
    """
    config_path = Path(f"config/builds/{build_name}.yaml")
    
    if not config_path.exists():
        console.print(f"[red]Error: Build config not found: {config_path}[/red]")
        return 1
    
    orchestrator = BuildOrchestrator(config_path)
    status_data = orchestrator.status()
    
    # Display status table
    table = Table(title=f"Build Status: {build_name}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Status", status_data['status'])
    table.add_row("Current Platform", status_data['current_platform'] or 'None')
    table.add_row("Progress", f"{status_data['progress']['percent']:.1f}%")
    table.add_row("Completed", str(status_data['progress']['completed']))
    table.add_row("Failed", str(status_data['progress']['failed']))
    table.add_row("Remaining", str(status_data['progress']['remaining']))
    
    console.print(table)
    
    # List platforms
    if status_data['completed_platforms']:
        console.print("\n[green]Completed:[/green]")
        for platform in status_data['completed_platforms']:
            console.print(f"  ✅ {platform}")
    
    if status_data['failed_platforms']:
        console.print("\n[red]Failed:[/red]")
        for platform in status_data['failed_platforms']:
            console.print(f"  ❌ {platform}")


@cli.command()
@click.argument('build_name')
def resume(build_name: str):
    """
    Resume interrupted build.
    
    Examples:
        romgroomer resume batocera-complete
    """
    # Calls build with resume flag
    ctx = click.get_current_context()
    ctx.invoke(build, build_name=build_name, resume=True)


@cli.command()
def list_builds():
    """List available build profiles."""
    builds_dir = Path("config/builds")
    
    if not builds_dir.exists():
        console.print("[yellow]No build configs found[/yellow]")
        return
    
    table = Table(title="Available Builds")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Platforms", style="green")
    
    for config_file in builds_dir.glob("*.yaml"):
        with open(config_file) as f:
            config = yaml.safe_load(f)
        
        table.add_row(
            config['name'],
            config.get('description', 'No description'),
            ', '.join(config.get('platforms', []))
        )
    
    console.print(table)


if __name__ == '__main__':
    cli()
```

---

### Phase 6D: Testing & Integration (2 days)

**Goal:** Test master build with existing platforms

**Test Plan:**

1. **Unit Tests:**
   - BuildOrchestrator initialization
   - Config validation
   - State persistence
   - Storage checks

2. **Integration Tests:**
   - Single platform build
   - Multi-platform build
   - Resume capability
   - Error handling

3. **End-to-End Test:**
   ```bash
   # Create test build
   romgroomer build test-small --platforms saturn,wii
   
   # Check status
   romgroomer status test-small
   
   # Simulate failure, resume
   # (kill process mid-build)
   romgroomer resume test-small
   ```

4. **Full Build Test:**
   ```bash
   # Run complete build with 4 existing platforms
   romgroomer build batocera-phase5 --platforms saturn,wii,gamecube,ps3
   ```

---

## Timeline

### Week 1: Core Infrastructure (Days 1-5)

**Day 1: Build Configuration**
- Create config schema
- Create batocera-complete.yaml
- Create template.yaml
- Validation logic

**Day 2-3: Build Orchestrator**
- BuildOrchestrator class
- Config loading
- State management
- Platform processing loop

**Day 4: Storage & Progress**
- StorageManager implementation
- ProgressTracker implementation
- Integration with orchestrator

**Day 5: CLI Interface**
- Click CLI setup
- build/status/resume commands
- Rich console output

### Week 2: Testing & Polish (Days 6-10)

**Day 6-7: Testing**
- Unit tests
- Integration tests
- Fix bugs

**Day 8: End-to-End Testing**
- Run complete build with 4 platforms
- Verify outputs
- Test resume capability

**Day 9: Documentation**
- User guide
- API documentation
- Example configs

**Day 10: Polish & Release**
- Error messages
- Help text
- README updates
- Tag v1.0-alpha

---

## Success Criteria

### Functional Requirements

✅ **Build Execution:**
- Single command builds multiple platforms
- Platforms process sequentially
- Progress tracked and displayed
- Errors logged with details

✅ **State Management:**
- Build state persisted to disk
- Resume skips completed platforms
- Failed platforms tracked
- Clean state on fresh build

✅ **Storage Management:**
- Temp space monitored
- Output space checked
- Cleanup automatic
- Warnings on low space

✅ **User Experience:**
- Clear progress indicators
- Helpful error messages
- Status command shows progress
- Report generated on completion

### Performance Requirements

✅ **Efficiency:**
- Minimal overhead (<5% of total time)
- No redundant work on resume
- Temp cleanup releases space promptly

✅ **Reliability:**
- Handles platform failures gracefully
- State always consistent
- No data loss on crash

---

## Example Usage

### Build Complete Collection

```bash
# First time - full build
romgroomer build batocera-complete
```

**Output:**
```
ROM Groomer v1.0
================

Build: batocera-complete
Platforms: saturn, wii, gamecube, ps3

✅ Validation passed
📦 Starting build...

[1/4] Processing saturn...
  ✓ Found 150 games
  ✓ Extracted archives
  ✓ Created CHD files
  ✓ Generated M3U files
  ✓ Organized output
  ⏱️  Duration: 45m
  ✅ Saturn complete

[2/4] Processing wii...
  ✓ Found 312 games
  ✓ Extracted RVZ files
  ✓ Organized output
  ⏱️  Duration: 1h 15m
  ✅ Wii complete

[3/4] Processing gamecube...
  ✓ Found 198 games
  ✓ Extracted RVZ files
  ✓ Organized output
  ⏱️  Duration: 35m
  ✅ GameCube complete

[4/4] Processing ps3...
  ✓ Found 87 games
  ✓ Decrypted ISOs
  ✓ Created JB folders
  ✓ Created .ps3 folders (Batocera)
  ⏱️  Duration: 2h 30m
  ✅ PS3 complete

================
✅ Build complete!
Duration: 5h 5m
Report: build_report_batocera-complete.txt
```

### Check Status

```bash
romgroomer status batocera-complete
```

**Output:**
```
Build Status: batocera-complete
╭──────────────────┬─────────────╮
│ Metric           │ Value       │
├──────────────────┼─────────────┤
│ Status           │ running     │
│ Current Platform │ ps3         │
│ Progress         │ 75.0%       │
│ Completed        │ 3           │
│ Failed           │ 0           │
│ Remaining        │ 1           │
╰──────────────────┴─────────────╯

Completed:
  ✅ saturn
  ✅ wii
  ✅ gamecube
```

### Resume After Interruption

```bash
# Process killed mid-build
^C

# Resume later
romgroomer resume batocera-complete
```

**Output:**
```
ROM Groomer v1.0
================

Resuming build: batocera-complete
Skipping completed: saturn, wii, gamecube
Remaining: ps3

[1/1] Processing ps3...
  ...
```

---

## Next Phase Preview: Phase 7

**After Phase 6 complete, we can add platforms rapidly:**

**Week 1: Cartridge Systems (7 systems)**
- NES, SNES, Genesis (No-Intro, unzip)
- GB, GBC, GBA (No-Intro, unzip)
- N64 (No-Intro, unzip)

**Week 2: CD Systems (3 systems)**
- PS1 (Redump, BIN/CUE → CHD, like Saturn)
- Dreamcast (Redump, GDI → CHD, like Saturn)
- Sega CD (Redump, BIN/CUE → CHD, like Saturn)

**Week 3: DVD/Handheld (2 systems)**
- PS2 (Redump, ISO extraction)
- PSP (Redump, ISO → CSO)

**Result:** ROM Groomer 1.0 with 16 systems! 🎉

---

## Let's Build Phase 6! 🚀

**Ready to start with Phase 6A: Build Configuration?**
