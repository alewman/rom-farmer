"""
Build orchestrator for multi-platform ROM processing.

This module provides the core orchestration logic for running builds across
multiple platforms. It loads build configurations, manages platform processing,
tracks progress, and handles errors.
"""

from pathlib import Path
from typing import List, Dict, Optional, Any
import yaml
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


logger = logging.getLogger(__name__)


class BuildStatus(Enum):
    """Build status states."""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BuildConfig:
    """
    Master build configuration.
    
    Loaded from YAML files in config/builds/
    """
    name: str
    description: str
    version: str
    settings: Dict[str, Any]
    storage: Dict[str, Any]
    platforms: List[str]
    platform_overrides: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    
    @classmethod
    def from_yaml(cls, config_path: Path) -> 'BuildConfig':
        """Load build config from YAML file."""
        with open(config_path) as f:
            data = yaml.safe_load(f)
        
        # Validate required fields
        required = ['name', 'description', 'platforms', 'storage']
        for field in required:
            if field not in data:
                raise ValueError(f"Missing required field in {config_path}: {field}")
        
        return cls(
            name=data['name'],
            description=data['description'],
            version=data.get('version', '1.0'),
            settings=data.get('settings', {}),
            storage=data['storage'],
            platforms=data['platforms'],
            platform_overrides=data.get('platform_overrides', {}),
            metadata=data.get('metadata', {}),
            notes=data.get('notes', '')
        )


@dataclass
class BuildState:
    """
    Current build state for resume capability.
    
    Persisted to .build_state_{name}.yaml for resume support.
    """
    build_name: str
    started_at: datetime
    completed_platforms: List[str] = field(default_factory=list)
    failed_platforms: List[str] = field(default_factory=list)
    current_platform: Optional[str] = None
    status: BuildStatus = BuildStatus.NOT_STARTED
    last_updated: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for YAML serialization."""
        return {
            'build_name': self.build_name,
            'started_at': self.started_at.isoformat(),
            'completed_platforms': self.completed_platforms,
            'failed_platforms': self.failed_platforms,
            'current_platform': self.current_platform,
            'status': self.status.value,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BuildState':
        """Load from dictionary (YAML deserialization)."""
        return cls(
            build_name=data['build_name'],
            started_at=datetime.fromisoformat(data['started_at']),
            completed_platforms=data.get('completed_platforms', []),
            failed_platforms=data.get('failed_platforms', []),
            current_platform=data.get('current_platform'),
            status=BuildStatus(data.get('status', 'not_started')),
            last_updated=datetime.fromisoformat(data['last_updated']) if data.get('last_updated') else None
        )


class BuildOrchestrator:
    """
    Orchestrates multi-platform ROM builds.
    
    Features:
    - Load and validate build configurations
    - Sequential platform processing
    - Progress tracking and state persistence
    - Error handling and recovery
    - Storage management
    - Resume capability
    
    Usage:
        orchestrator = BuildOrchestrator.from_config("batocera-phase5")
        orchestrator.run()
    """
    
    def __init__(self, config: BuildConfig, state_dir: Path = Path(".")):
        self.config = config
        self.state_dir = state_dir
        self.state_file = state_dir / f".build_state_{config.name}.yaml"
        self.state = self._load_or_create_state()
        
        # Setup logging
        self._setup_logging()
        
        logger.info(f"Initialized build orchestrator: {config.name}")
    
    @classmethod
    def from_config(cls, build_name: str, config_dir: Path = Path("config/builds")) -> 'BuildOrchestrator':
        """
        Create orchestrator from build name.
        
        Args:
            build_name: Name of build config (without .yaml extension)
            config_dir: Directory containing build configs
        
        Returns:
            BuildOrchestrator instance
        
        Raises:
            FileNotFoundError: If config file doesn't exist
        """
        from romgroomer.config import load_build_config
        
        config_path = config_dir / f"{build_name}.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"Build config not found: {config_path}")
        
        config = load_build_config(build_name, config_root=config_dir.parent)
        return cls(config)
    
    def _setup_logging(self):
        """Configure logging for this build."""
        settings = getattr(self.config, 'settings', {})
        log_level = settings.get('log_level', 'INFO') if isinstance(settings, dict) else 'INFO'
        log_file = settings.get('log_file', f'build_{self.config.name}.log') if isinstance(settings, dict) else f'build_{self.config.name}.log'
        
        # Create logger for this build
        build_logger = logging.getLogger(f'romgroomer.build.{self.config.name}')
        build_logger.setLevel(getattr(logging, log_level))
        
        # File handler
        fh = logging.FileHandler(log_file)
        fh.setLevel(getattr(logging, log_level))
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(getattr(logging, log_level))
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        build_logger.addHandler(fh)
        build_logger.addHandler(ch)
    
    def _load_or_create_state(self) -> BuildState:
        """Load existing build state or create new."""
        if self.state_file.exists():
            logger.info(f"Loading existing build state: {self.state_file}")
            with open(self.state_file) as f:
                data = yaml.safe_load(f)
            return BuildState.from_dict(data)
        
        logger.info("Creating new build state")
        return BuildState(
            build_name=self.config.name,
            started_at=datetime.now()
        )
    
    def _save_state(self):
        """Persist build state for resume capability."""
        self.state.last_updated = datetime.now()
        
        with open(self.state_file, 'w') as f:
            yaml.dump(self.state.to_dict(), f, default_flow_style=False)
        
        logger.debug(f"Saved build state: {self.state_file}")
    
    def validate(self) -> bool:
        """
        Validate build can proceed.
        
        Checks:
        - Platform configs exist
        - Source directories exist (if specified in platform configs)
        - Required tools installed (future)
        - Storage available
        
        Returns:
            True if validation passes, False otherwise
        """
        logger.info(f"Validating build: {self.config.name}")
        errors = []
        
        # Check platform configs exist
        config_dir = Path("config/platforms")
        for platform in self.config.platforms:
            config_file = config_dir / f"{platform}.yaml"
            if not config_file.exists():
                errors.append(f"Missing platform config: {config_file}")
        
        # Check output directory writable (if storage config exists)
        storage = getattr(self.config, 'storage', {})
        if isinstance(storage, dict) and 'output_base' in storage:
            output_base = Path(storage['output_base'])
            if not output_base.exists():
                try:
                    output_base.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create output directory {output_base}: {e}")
        
            # Check temp directory writable
            if 'temp_path' in storage:
                temp_path = Path(storage['temp_path'])
                if not temp_path.exists():
                    try:
                        temp_path.mkdir(parents=True, exist_ok=True)
                    except Exception as e:
                        errors.append(f"Cannot create temp directory {temp_path}: {e}")
        
        # Report errors
        if errors:
            logger.error("Validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            return False
        
        logger.info("✅ Validation passed")
        return True
    
    def run(self, resume: bool = False):
        """
        Run the build.
        
        Args:
            resume: If True, skip already-completed platforms
        
        Raises:
            ValueError: If validation fails
            Exception: If platform processing fails and stop_on_error is True
        """
        # Validate unless resuming
        if not resume and not self.validate():
            raise ValueError("Build validation failed")
        
        # Update state
        self.state.status = BuildStatus.RUNNING
        self._save_state()
        
        # Get platforms to process
        platforms_to_process = self._get_platforms_to_process(resume)
        
        logger.info(f"Starting build: {self.config.name}")
        logger.info(f"Description: {self.config.description}")
        logger.info(f"Platforms to process: {', '.join(platforms_to_process)}")
        
        # Process each platform
        for i, platform in enumerate(platforms_to_process, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"[{i}/{len(platforms_to_process)}] Processing: {platform}")
            logger.info(f"{'='*60}\n")
            
            try:
                self._process_platform(platform)
                self.state.completed_platforms.append(platform)
                logger.info(f"✅ {platform} complete")
                
            except Exception as e:
                logger.error(f"❌ {platform} failed: {e}", exc_info=True)
                self.state.failed_platforms.append(platform)
                
                # Check if we should stop
                settings = getattr(self.config, 'settings', {})
                if isinstance(settings, dict) and settings.get('stop_on_error', False):
                    self.state.status = BuildStatus.FAILED
                    self._save_state()
                    raise
            
            finally:
                self.state.current_platform = None
                self._save_state()
        
        # Build complete
        self.state.status = BuildStatus.COMPLETED
        self._save_state()
        
        logger.info(f"\n{'='*60}")
        logger.info("✅ Build complete!")
        logger.info(f"{'='*60}\n")
        
        self._generate_report()
    
    def _get_platforms_to_process(self, resume: bool) -> List[str]:
        """
        Get list of platforms to process.
        
        Args:
            resume: If True, skip already-completed platforms
        
        Returns:
            List of platform names to process
        """
        if not resume:
            return self.config.platforms
        
        # Skip completed platforms
        remaining = [
            p for p in self.config.platforms
            if p not in self.state.completed_platforms
        ]
        
        if remaining != self.config.platforms:
            skipped = set(self.config.platforms) - set(remaining)
            logger.info(f"Resuming build - skipping completed: {', '.join(skipped)}")
        
        return remaining
    
    def _process_platform(self, platform: str):
        """
        Process a single platform.
        
        Args:
            platform: Platform name
        
        Raises:
            Exception: If platform processing fails
        """
        from romgroomer.platform_processor import PlatformProcessor
        
        self.state.current_platform = platform
        self._save_state()
        
        logger.info(f"Processing platform: {platform}")
        
        # Get overrides for this platform from build config
        platform_overrides = getattr(self.config, 'platform_overrides', {})
        overrides = platform_overrides.get(platform, {}) if isinstance(platform_overrides, dict) else {}
        
        # Get directories from config
        storage = getattr(self.config, 'storage', {})
        if isinstance(storage, dict) and 'temp_path' in storage:
            work_dir = Path(storage['temp_path']) / platform
        else:
            # Fallback to default temp directory
            work_dir = Path('/data/emu/temp') / platform
        # Don't pass output_dir - let platform processor construct descriptive name
        # based on platform-datvariant-target (e.g., virtualboy-1g1r-eng-batocera)
        
        # Create platform processor
        processor = PlatformProcessor(
            platform_name=platform,
            overrides=overrides
        )
        
        # Process platform (output_dir will be constructed by processor)
        result = processor.process(
            work_dir=work_dir
        )
        
        # Log results
        logger.info(f"Platform processing complete: {platform}")
        logger.info(f"  Status: {result['status']}")
        logger.info(f"  Targets processed: {result['targets_processed']}")
        logger.info(f"  Files processed: {result['files_processed']}")
        logger.info(f"  Duration: {result['duration']:.1f}s")
        
        # Check for errors
        if result['status'] == 'failed':
            error_msg = '; '.join(result['errors'])
            raise Exception(f"Platform processing failed: {error_msg}")
        
        # Verify if configured
        settings = getattr(self.config, 'settings', {})
        if isinstance(settings, dict) and settings.get('verify_outputs', True):
            if not processor.verify():
                raise Exception("Output verification failed")
        
        # Cleanup temp files if configured
        cleanup_temp = settings.get('cleanup_temp', True) if isinstance(settings, dict) else True
        if cleanup_temp and work_dir.exists():
            logger.info(f"Cleaning up temp directory: {work_dir}")
            import shutil
            shutil.rmtree(work_dir)
    
    def _generate_report(self):
        """Generate build completion report."""
        report_path = Path(f"build_report_{self.config.name}.txt")
        
        duration = datetime.now() - self.state.started_at
        
        with open(report_path, 'w') as f:
            f.write(f"Build Report: {self.config.name}\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Description: {self.config.description}\n")
            f.write(f"Version: {self.config.version}\n\n")
            
            f.write(f"Started: {self.state.started_at}\n")
            f.write(f"Completed: {datetime.now()}\n")
            f.write(f"Duration: {duration}\n\n")
            
            f.write(f"Status: {self.state.status.value}\n\n")
            
            # Platforms summary
            total = len(self.config.platforms)
            completed = len(self.state.completed_platforms)
            failed = len(self.state.failed_platforms)
            
            f.write(f"Platforms Summary:\n")
            f.write(f"  Total: {total}\n")
            f.write(f"  Completed: {completed}\n")
            f.write(f"  Failed: {failed}\n")
            f.write(f"  Success Rate: {completed/total*100:.1f}%\n\n")
            
            # Completed platforms
            if self.state.completed_platforms:
                f.write(f"Completed Platforms ({completed}):\n")
                for platform in self.state.completed_platforms:
                    f.write(f"  ✅ {platform}\n")
                f.write("\n")
            
            # Failed platforms
            if self.state.failed_platforms:
                f.write(f"Failed Platforms ({failed}):\n")
                for platform in self.state.failed_platforms:
                    f.write(f"  ❌ {platform}\n")
                f.write("\n")
            
            f.write("=" * 60 + "\n")
        
        logger.info(f"Report saved: {report_path}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current build status.
        
        Returns:
            Dictionary with build status information
        """
        total = len(self.config.platforms)
        completed = len(self.state.completed_platforms)
        failed = len(self.state.failed_platforms)
        remaining = total - completed - failed
        
        return {
            'build_name': self.config.name,
            'description': self.config.description,
            'status': self.state.status.value,
            'current_platform': self.state.current_platform,
            'started_at': self.state.started_at.isoformat(),
            'last_updated': self.state.last_updated.isoformat() if self.state.last_updated else None,
            'progress': {
                'total': total,
                'completed': completed,
                'failed': failed,
                'remaining': remaining,
                'percent': (completed / total * 100) if total > 0 else 0
            },
            'completed_platforms': self.state.completed_platforms,
            'failed_platforms': self.state.failed_platforms
        }
    
    def resume(self):
        """Resume interrupted build."""
        logger.info(f"Resuming build: {self.config.name}")
        self.run(resume=True)
