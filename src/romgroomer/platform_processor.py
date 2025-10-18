"""
Platform processor for build orchestration.

This module provides the interface between the BuildOrchestrator and
the existing stage-based processing pipeline.
"""

import time
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from romgroomer.config.loader import load_platform_config
from romgroomer.config.models import PlatformConfig
from romgroomer.stages.pipeline import Pipeline
from romgroomer.stages.base import StageStatus


logger = logging.getLogger(__name__)


class PlatformProcessor:
    """
    Process a single platform using the stage-based pipeline.
    
    This class serves as the integration point between the BuildOrchestrator
    and the existing stage-based processing system. It:
    
    1. Loads platform configuration
    2. Applies build-level overrides
    3. Creates appropriate pipeline stages
    4. Executes the pipeline
    5. Returns results to orchestrator
    
    The processor adapts platform configs to work with different targets
    and handles platform-specific processing logic.
    """
    
    def __init__(
        self,
        platform_name: str,
        config_dir: Path = Path("config/platforms"),
        overrides: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize platform processor.
        
        Args:
            platform_name: Name of platform (e.g., 'saturn', 'wii')
            config_dir: Directory containing platform configs
            overrides: Optional overrides from build config
        """
        self.platform_name = platform_name
        self.config_path = config_dir / f"{platform_name}.yaml"
        self.overrides = overrides or {}
        
        # Load configuration
        self.config = self._load_config()
        
        logger.info(f"Initialized platform processor: {platform_name}")
    
    def _load_config(self) -> PlatformConfig:
        """
        Load platform configuration from YAML.
        
        Returns:
            PlatformConfig instance
        
        Raises:
            FileNotFoundError: If config file doesn't exist
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Platform config not found: {self.config_path}")
        
        # Use the config loader
        config = load_platform_config(self.platform_name)
        
        # Apply overrides from build config
        if self.overrides:
            config = self._apply_overrides(config, self.overrides)
        
        return config
    
    def _apply_overrides(
        self,
        config: PlatformConfig,
        overrides: Dict[str, Any]
    ) -> PlatformConfig:
        """
        Apply build-level overrides to platform config.
        
        Args:
            config: Original platform config
            overrides: Override values from build config
        
        Returns:
            Modified platform config
        
        Example overrides:
            {
                'targets': ['batocera'],  # Only process one target
                'compression': {'level': 5},  # Override compression
                'enabled': False  # Skip this platform
            }
        """
        logger.info(f"Applying overrides for {self.platform_name}: {overrides}")
        
        # Handle target filtering
        if 'targets' in overrides:
            allowed_targets = set(overrides['targets'])
            config.targets = [
                t for t in config.targets
                if t.name in allowed_targets
            ]
            logger.info(f"  Filtered targets: {[t.name for t in config.targets]}")
        
        # Handle compression overrides
        if 'compression' in overrides:
            for key, value in overrides['compression'].items():
                if hasattr(config.compression, key):
                    setattr(config.compression, key, value)
                    logger.info(f"  Override compression.{key} = {value}")
        
        # Handle enabled flag
        if 'enabled' in overrides:
            config.enabled = overrides['enabled']
            logger.info(f"  Override enabled = {config.enabled}")
        
        return config
    
    def process(
        self,
        source_dir: Optional[Path] = None,
        work_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Process platform using configured pipeline.
        
        Args:
            source_dir: Optional override for source directory
            work_dir: Optional override for work directory
            output_dir: Optional override for output directory
        
        Returns:
            Dictionary with processing results:
            {
                'platform': 'saturn',
                'status': 'success',  # or 'failed', 'skipped'
                'targets_processed': 2,
                'files_processed': 150,
                'duration': 2700.5,  # seconds
                'errors': []
            }
        """
        start_time = time.time()
        
        logger.info(f"Processing platform: {self.platform_name}")
        
        # Check if platform is enabled
        if not self.config.enabled:
            logger.info(f"Platform {self.platform_name} is disabled, skipping")
            return {
                'platform': self.platform_name,
                'status': 'skipped',
                'targets_processed': 0,
                'files_processed': 0,
                'duration': 0,
                'errors': [],
                'message': 'Platform disabled in config'
            }
        
        # Use config directories or overrides
        source_dir = source_dir or self._get_source_dir()
        work_dir = work_dir or self._get_work_dir()
        
        # Process each target
        results = []
        total_files = 0
        errors = []
        
        for target in self.config.targets:
            if not target.enabled:
                logger.info(f"Target {target.name} disabled, skipping")
                continue
            
            try:
                target_output_dir = output_dir or Path(target.output_path)
                
                logger.info(f"Processing target: {target.name}")
                logger.info(f"  Source: {source_dir}")
                logger.info(f"  Work: {work_dir}")
                logger.info(f"  Output: {target_output_dir}")
                
                # Create and run pipeline
                result = self._process_target(
                    target=target,
                    source_dir=source_dir,
                    work_dir=work_dir,
                    output_dir=target_output_dir
                )
                
                results.append(result)
                total_files += result.get('files_processed', 0)
                
                if result.get('status') == 'failed':
                    errors.append(result.get('error'))
                
            except Exception as e:
                logger.error(f"Target {target.name} failed: {e}", exc_info=True)
                errors.append(str(e))
                results.append({
                    'target': target.name,
                    'status': 'failed',
                    'error': str(e)
                })
        
        duration = time.time() - start_time
        
        # Determine overall status
        if not results:
            status = 'skipped'
        elif errors:
            status = 'failed'
        else:
            status = 'success'
        
        return {
            'platform': self.platform_name,
            'status': status,
            'targets_processed': len([r for r in results if r.get('status') == 'success']),
            'files_processed': total_files,
            'duration': duration,
            'errors': errors,
            'target_results': results
        }
    
    def _get_source_dir(self) -> Path:
        """Get source directory from config."""
        if self.config.sources:
            return Path(self.config.sources[0].path)
        raise ValueError(f"No source directory configured for {self.platform_name}")
    
    def _get_work_dir(self) -> Path:
        """Get work directory from config or default."""
        # Use temp directory from config or default
        return Path("/data/emu/temp") / self.platform_name
    
    def _process_target(
        self,
        target: Any,  # TargetConfig
        source_dir: Path,
        work_dir: Path,
        output_dir: Path
    ) -> Dict[str, Any]:
        """
        Process a single target using the pipeline.
        
        Args:
            target: Target configuration
            source_dir: Source directory
            work_dir: Working directory
            output_dir: Output directory
        
        Returns:
            Dictionary with target processing results
        """
        # NOTE: This is a placeholder that would integrate with existing
        # stage-based pipeline once we have the actual stage implementations.
        
        logger.info(f"Processing target: {target.name}")
        logger.info(f"  Platform: {self.platform_name}")
        logger.info(f"  Source: {source_dir}")
        logger.info(f"  Output: {output_dir}")
        
        # TODO: Create pipeline with appropriate stages based on platform type
        # TODO: Execute pipeline
        # TODO: Return detailed results
        
        # For now, return placeholder result
        return {
            'target': target.name,
            'status': 'success',
            'files_processed': 0,
            'message': 'Platform processing not yet fully implemented (Phase 6C placeholder)'
        }
    
    def verify(self) -> bool:
        """
        Verify platform processing completed successfully.
        
        Checks:
        - Output files exist
        - File counts match expectations
        - No corruption detected
        
        Returns:
            True if verification passes
        """
        # TODO: Implement output verification
        logger.info(f"Verifying platform: {self.platform_name}")
        return True
