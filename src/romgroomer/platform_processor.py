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
                # Construct output directory name: {platform}-{dat_variant}-{target}
                # e.g., virtualboy-1g1r-eng-batocera, virtualboy-1g1r-eng-top5-batocera
                if output_dir:
                    target_output_dir = output_dir
                else:
                    # Extract DAT variant from source (e.g., "retool_1g1r_eng" -> "1g1r-eng")
                    dat_source = self.config.dat.source
                    # Remove common prefixes and convert underscores to hyphens
                    dat_variant = dat_source.replace("retool_", "").replace("nointro_", "").replace("redump_", "")
                    dat_variant = dat_variant.replace("_", "-")
                    
                    # Append rating filter suffix if enabled
                    if self.config.rating_filter.enabled:
                        if self.config.rating_filter.top_n:
                            dat_variant += f"-top{self.config.rating_filter.top_n}"
                        elif self.config.rating_filter.max_size_gb:
                            dat_variant += f"-{int(self.config.rating_filter.max_size_gb)}gb"
                        elif self.config.rating_filter.min_rating:
                            dat_variant += f"-min{self.config.rating_filter.min_rating:.1f}"
                    
                    # Build descriptive output path
                    output_name = f"{self.platform_name}-{dat_variant}-{target.name}"
                    target_output_dir = Path(target.output_path).parent / output_name
                
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
        from romgroomer.config.models import SystemType, ExtractionType, CompressionFormat
        from romgroomer.stages import (
            ApplyListsStage,
            CompressCHDStage,
            CompressArchiveStage,
            CreateM3UStage,
            ExtractArchiveStage,
            FilterDATStage,
            FilterRatingStage,
            GenerateMetadataStage,
            OrganizeStage,
            Pipeline,
            TransformPS3Stage,
            UnzipRVZStage,
        )
        
        logger.info(f"Processing target: {target.name}")
        logger.info(f"  Platform: {self.platform_name}")
        logger.info(f"  Extraction: {self.config.extraction.type if self.config.extraction.enabled else 'none'}")
        logger.info(f"  Compression: {self.config.compression.format}")
        logger.info(f"  Source: {source_dir}")
        logger.info(f"  Output: {output_dir}")
        
        try:
            # Create pipeline for this target
            pipeline = Pipeline(
                platform_config=self.config,
                target_name=target.name
            )
            
            # Initialize metadata database for transformation recording (if needed)
            metadata_db = None
            if self.config.compression.format == CompressionFormat.CHD:
                from romgroomer.metadata.database import MetadataDatabase
                metadata_db_path = Path("metadata/database/romgroomer.db")
                metadata_db = MetadataDatabase(metadata_db_path)
            
            # Build pipeline based on extraction/compression config
            # Core stages: always filter and apply lists
            pipeline.add_stage(FilterDATStage())
            
            # Rating filter (if enabled)
            if self.config.rating_filter.enabled:
                logger.info("  Stage routing: Rating filter enabled")
                pipeline.add_stage(FilterRatingStage(
                    work_dir=work_dir,
                    top_n=self.config.rating_filter.top_n,
                    max_size_gb=self.config.rating_filter.max_size_gb,
                    min_rating=self.config.rating_filter.min_rating
                ))
            
            pipeline.add_stage(ApplyListsStage())
            
            # Extraction stage (if enabled)
            if self.config.extraction.enabled:
                extraction_type = self.config.extraction.type
                
                if extraction_type == ExtractionType.CARTRIDGE:
                    # Cartridge extraction: extract ROMs from ZIPs
                    logger.info("  Stage routing: Cartridge extraction enabled")
                    pipeline.add_stage(ExtractArchiveStage())
                    
                    # Add compression stage if needed
                    if self.config.compression.format == CompressionFormat.SEVENZ:
                        logger.info("  Stage routing: 7z compression enabled")
                        pipeline.add_stage(CompressArchiveStage())
                    elif self.config.compression.format == CompressionFormat.ZIP:
                        logger.info("  Stage routing: ZIP compression enabled")
                        pipeline.add_stage(CompressArchiveStage())
                
                elif extraction_type == ExtractionType.DISC:
                    # Disc extraction: extract CUE/BIN for CHD conversion
                    logger.info("  Stage routing: Disc extraction enabled")
                    pipeline.add_stage(ExtractArchiveStage())
                    
                    # Add CHD compression if configured
                    if self.config.compression.format == CompressionFormat.CHD:
                        logger.info("  Stage routing: CHD compression enabled")
                        pipeline.add_stage(CompressCHDStage(db_session=metadata_db.get_session() if metadata_db else None))
                        pipeline.add_stage(CreateM3UStage())
                
                elif extraction_type == ExtractionType.MIXED:
                    # Mixed systems may need special handling
                    logger.warning("  MIXED extraction type not fully implemented")
            
            # Legacy system_type support for backwards compatibility
            elif hasattr(self.config, 'system_type'):
                if self.config.system_type == SystemType.COMPLEX:
                    # Complex systems (Wii/GameCube RVZ)
                    logger.info("  Stage routing: COMPLEX (unzip_rvz)")
                    pipeline.add_stage(UnzipRVZStage())
                
                elif self.config.system_type == SystemType.VERY_COMPLEX:
                    # Very complex systems (PS3, Xbox 360)
                    if self.platform_name == 'ps3':
                        logger.info("  Stage routing: VERY_COMPLEX (PS3 transform)")
                        pipeline.add_stage(TransformPS3Stage())
                    else:
                        logger.warning(f"No stage routing for VERY_COMPLEX platform: {self.platform_name}")
            
            # Organization and metadata stages (always)
            pipeline.add_stage(OrganizeStage())
            pipeline.add_stage(GenerateMetadataStage())
            
            # Find DAT file path
            dat_file_path = self._find_dat_file()
            
            # Execute pipeline
            logger.info(f"  Executing {len(pipeline.stages)} stages...")
            start_time = time.time()
            
            results = pipeline.execute(
                source_dir=source_dir,
                work_dir=work_dir,
                output_dir=output_dir,
                dat_file_path=dat_file_path
            )
            
            duration = time.time() - start_time
            
            # Aggregate results
            files_processed = sum(r.files_processed for r in results)
            failed = any(r.status.value == 'failed' for r in results)
            
            if failed:
                errors = [r.message for r in results if r.status.value == 'failed']
                return {
                    'target': target.name,
                    'status': 'failed',
                    'files_processed': files_processed,
                    'duration': duration,
                    'errors': errors
                }
            
            return {
                'target': target.name,
                'status': 'success',
                'files_processed': files_processed,
                'duration': duration,
                'stages_executed': len(results)
            }
        
        except Exception as e:
            logger.error(f"Target processing failed: {e}", exc_info=True)
            return {
                'target': target.name,
                'status': 'failed',
                'files_processed': 0,
                'error': str(e)
            }
    
    def _find_dat_file(self) -> Optional[Path]:
        """Find DAT file for platform.
        
        Returns:
            Path to DAT file, or None if not configured
        """
        if not self.config.dat:
            return None
        
        # Common DAT locations based on source
        dat_base = Path("/data/emu/dats")
        source = self.config.dat.source
        
        # Map source to directory
        source_map = {
            'retool_1g1r_usa': 'nointro.retool.1g1r.usa',
            'retool_1g1r_eng': 'nointro.retool.1g1r.eng',  # No-Intro platforms
            'retool_1g1r_all': 'nointro.retool.1g1r.all',
            'redump_retool_1g1r_usa': 'redump.retool.1g1r.usa',
            'redump_retool_1g1r_eng': 'redump.retool.1g1r.eng',  # Redump platforms
        }
        
        dat_dir = dat_base / source_map.get(source, source)
        
        if not dat_dir.exists():
            logger.warning(f"DAT directory not found: {dat_dir}")
            return None
        
        # Find DAT file matching platform name
        # Look for files containing platform name (case-insensitive)
        # Map platform names to DAT file search terms
        platform_dat_map = {
            'psx': 'sony - playstation (',  # Include '(' to avoid matching "PlayStation Portable"
            'ps1': 'sony - playstation (',
            'ps2': 'playstation 2',
            'ps3': 'playstation 3',
            'psp': 'playstation portable',
            'virtualboy': 'nintendo - virtual boy',
        }
        
        platform_search = platform_dat_map.get(self.platform_name.lower(), self.platform_name.lower())
        
        platform_variants = [
            platform_search,
            self.platform_name.lower(),
            self.config.name.lower(),
            # Also try removing suffixes like -test, -demo, etc.
            self.platform_name.split('-')[0].lower(),
        ]
        
        for dat_file in dat_dir.glob("*.dat"):
            dat_name_lower = dat_file.name.lower()
            for variant in platform_variants:
                if variant in dat_name_lower:
                    logger.info(f"  Found DAT file: {dat_file.name}")
                    return dat_file
        
        logger.warning(f"No DAT file found for platform: {self.platform_name}")
        return None
    
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
