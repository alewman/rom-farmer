"""
Platform processor for build orchestration.

This module provides the interface between the BuildOrchestrator and
the existing stage-based processing pipeline.
"""

import time
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from romfarmer.config.loader import load_platform_config
from romfarmer.config.overrides import apply_overrides
from romfarmer.core.paths import get_paths
from romfarmer.config.models import PlatformConfig
from romfarmer.stages.pipeline import Pipeline
from romfarmer.stages.base import StageStatus
from romfarmer.cache import CacheManager, CacheConfig


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
        overrides: Optional[Dict[str, Any]] = None,
        storage_config: Optional[Dict[str, Any]] = None,
        composed_target: Optional[Any] = None,  # ComposedTarget for target builds
        cache_manager: Optional[CacheManager] = None,  # ROM cache for build acceleration
    ):
        """
        Initialize platform processor.
        
        Args:
            platform_name: Name of platform (e.g., 'saturn', 'wii')
            config_dir: Directory containing platform configs
            overrides: Optional overrides from build config
            storage_config: Optional storage configuration from build config
            composed_target: Optional ComposedTarget for target builds (provides frontend + device info)
            cache_manager: Optional CacheManager for caching compressed ROMs
        """
        self.platform_name = platform_name
        self.config_path = self._resolve_path(config_dir / f"{platform_name}.yaml")
        self.overrides = overrides or {}
        self.storage_config = storage_config or {}
        self.composed_target = composed_target  # Store for pipeline
        self.cache_manager = cache_manager  # Store for stages
        
        # Load configuration
        self.config = self._load_config()
        
        # Resolve source roots
        self._resolve_source_roots()
        
        logger.info(f"Initialized platform processor: {platform_name}")
    
    def _resolve_path(self, path: Path) -> Path:
        """
        Resolve a path to an absolute Path.
        
        If the path is relative, resolve it against the workspace root.
        If absolute, use as-is.
        """
        if path.is_absolute():
            return path
        # Resolve relative paths against workspace root
        return get_paths().workspace_root / path
    
    def _resolve_source_roots(self):
        """Resolve source roots from config/sources.yaml."""
        import yaml
        sources_config_path = self._resolve_path(Path("config/sources.yaml"))
        if not sources_config_path.exists():
            return

        try:
            with open(sources_config_path) as f:
                roots = yaml.safe_load(f).get('roots', {})
            
            for source in self.config.sources:
                if source.root:
                    if source.root not in roots:
                        logger.warning(f"Source root '{source.root}' not found in sources.yaml")
                        continue
                    
                    root_path = Path(roots[source.root])
                    if source.subdir:
                        source.path = root_path / source.subdir
                    else:
                        source.path = root_path
                        
                    if not source.path.exists():
                        logger.warning(f"Resolved source path does not exist: {source.path}")
                        
                    logger.info(f"Resolved source root '{source.root}' to: {source.path}")
        except Exception as e:
            logger.error(f"Failed to resolve source roots: {e}")

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
        
        # Apply overrides from build config using the new override system
        if self.overrides:
            config = apply_overrides(config, self.overrides, self.storage_config)
        
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
        
        # Log source directories
        all_source_dirs = self._get_all_source_dirs()
        if len(all_source_dirs) > 1:
            logger.info(f"Using {len(all_source_dirs)} source directories:")
            for idx, src_dir in enumerate(all_source_dirs, 1):
                logger.info(f"  {idx}. {src_dir}")
        else:
            logger.info(f"Using source directory: {source_dir}")
        
        # Process each target
        results = []
        total_files = 0
        errors = []
        
        for target in self.config.targets:
            if not target.enabled:
                logger.info(f"Target {target.name} disabled, skipping")
                continue
            
            try:
                # Construct output directory
                # For target builds: Use composed_target's folder mapping
                # For legacy builds: Use configured output_path or template
                if output_dir:
                    target_output_dir = output_dir
                elif self.composed_target:
                    # Target build: Use frontend's folder mapping for this platform
                    # e.g., batocera-pc might map 'nes' -> 'nes' or 'saturn' -> 'saturn'
                    folder_name = self.composed_target.get_folder_name(self.platform_name)
                    output_base = self.storage_config.get('output_base', str(get_paths().output_dir))
                    target_output_dir = self._resolve_path(Path(output_base)) / folder_name
                    logger.info(f"  Target build folder mapping: {self.platform_name} -> {folder_name}")
                elif (
                    self.overrides 
                    and 'targets' in self.overrides 
                    and self.overrides['targets'] 
                    and isinstance(self.overrides['targets'][0], dict)
                ):
                    # If targets are explicitly defined in overrides, use the provided path directly
                    target_output_dir = self._resolve_path(Path(target.output_path))
                elif self.storage_config.get('output_template'):
                    # Use template if available
                    # Convert target object to dict for _generate_output_path
                    target_dict = {'name': target.name}
                    target_output_dir = self._resolve_path(Path(self._generate_output_path(target_dict, self.config)))
                else:
                    # Use the configured output path directly
                    # This respects the explicit path set in the platform YAML
                    target_output_dir = self._resolve_path(Path(target.output_path))
                
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
                    # Get errors from result (can be 'error' singular or 'errors' plural)
                    result_errors = result.get('errors', [result.get('error')]) if result.get('errors') else [result.get('error')]
                    for error in result_errors:
                        if error:
                            errors.append(error)
                
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
        """Get primary source directory from config."""
        if self.config.sources:
            return Path(self.config.sources[0].path)
        raise ValueError(f"No source directory configured for {self.platform_name}")
    
    def _get_all_source_dirs(self) -> list[Path]:
        """Get all source directories from config."""
        if not self.config.sources:
            raise ValueError(f"No source directories configured for {self.platform_name}")
        return [Path(src.path) for src in self.config.sources]
    
    def _get_work_dir(self) -> Path:
        """Get work directory from config or default."""
        # Use temp directory from PathResolver
        return get_paths().platform_temp_dir(self.platform_name)
    
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
        from romfarmer.config.models import SystemType, ExtractionType, CompressionFormat, SelectionStrategy
        from romfarmer.stages import (
            ApplyListsStage,
            ApplyPS3UpdatesStage,
            CompressCHDStage,
            CompressArchiveStage,
            CompressSquashfsStage,
            ConvertXISOStage,
            CreateM3UStage,
            ExtractArchiveStage,
            ExtractPS3Stage,
            FilterDATStage,
            Filter1G1RStage,
            FilterRatingStage,
            SelectionFilter,
            GenerateMetadataStage,
            OrganizeStage,
            Pipeline,
            TransformPS3Stage,
            UnzipRVZStage,
        )
        
        logger.info(f"Processing target: {target.name}")
        logger.info(f"  Platform: {self.platform_name}")
        logger.info(f"  Extraction: {self.config.extraction.type if self.config.extraction.enabled else 'none'}")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # Determine effective compression format
        # Priority: composed_target > platform_config
        # ═══════════════════════════════════════════════════════════════════════════
        effective_compression = None
        compression_source = "none"
        
        if self.composed_target:
            # Get target's preferred compression for this platform
            target_pref = self.composed_target.get_preferred_compression(self.platform_name, default="none")
            if target_pref and target_pref != "none":
                # Map string to CompressionFormat enum
                try:
                    effective_compression = CompressionFormat(target_pref)
                    compression_source = f"target ({self.composed_target.frontend.name})"
                except ValueError:
                    logger.warning(f"  Unknown compression format from target: {target_pref}")
        
        # Fall back to platform config if target didn't specify
        if effective_compression is None and self.config.compression and self.config.compression.format:
            effective_compression = self.config.compression.format
            compression_source = "platform config"
        
        logger.info(f"  Compression: {effective_compression.value if effective_compression else 'none'} (from {compression_source})")
        logger.info(f"  Source: {source_dir}")
        logger.info(f"  Output: {output_dir}")
        if self.composed_target:
            logger.info(f"  Target: {self.composed_target.frontend.name} + {self.composed_target.device.name}")
        
        # Extract tier info from overrides (set by orchestrator)
        tier = self.overrides.get('tier')
        tier_strategy = self.overrides.get('tier_strategy')
        if tier:
            logger.info(f"  Tier: {tier}, Strategy: {tier_strategy}")
        
        try:
            # Create pipeline for this target
            pipeline = Pipeline(
                platform_config=self.config,
                target_name=target.name,
                composed_target=self.composed_target,  # Pass composed target to pipeline
                tier=tier,
                tier_strategy=tier_strategy,
            )
            
            # Initialize metadata database for transformation recording (if needed)
            metadata_db = None
            # Initialize metadata database for CHD or XISO transformations
            if effective_compression == CompressionFormat.CHD or \
               (self.config.extraction.enabled and self.config.extraction.type == ExtractionType.XISO):
                from romfarmer.metadata.database import MetadataDatabase
                metadata_db_path = Path("metadata/database/romfarmer.db")
                metadata_db = MetadataDatabase(metadata_db_path)
            
            # Build pipeline based on extraction/compression config
            # Core stages: always filter and apply lists
            pipeline.add_stage(FilterDATStage())
            pipeline.add_stage(Filter1G1RStage())
            
            # Determine output format for compression ratio prediction
            output_format = effective_compression.value.lower() if effective_compression else None
            
            # Selection filter (if configured) - replaces rating_filter
            if self.config.selection:
                logger.info(f"  Stage routing: Selection filter enabled ({self.config.selection.strategy.value})")
                pipeline.add_stage(SelectionFilter(
                    work_dir=work_dir,
                    selection=self.config.selection,
                    platform=self.config.name,
                    output_format=output_format
                ))
            elif self.config.rating_filter.enabled:
                # Backward compatibility: convert rating_filter to selection
                logger.warning("  rating_filter is deprecated, use selection instead")
                from romfarmer.config.models import SelectionConfig
                selection = SelectionConfig(
                    strategy=SelectionStrategy.RATING_BUDGET,
                    limit=self.config.rating_filter.top_n,
                    max_size_gb=self.config.rating_filter.max_size_gb,
                    min_rating=self.config.rating_filter.min_rating
                )
                pipeline.add_stage(SelectionFilter(
                    work_dir=work_dir,
                    selection=selection,
                    platform=self.config.name,
                    output_format=output_format
                ))
            
            pipeline.add_stage(ApplyListsStage())
            
            # Extraction stage (if enabled)
            if self.config.extraction.enabled:
                extraction_type = self.config.extraction.type
                
                if extraction_type == ExtractionType.CARTRIDGE:
                    # Cartridge extraction: extract ROMs from ZIPs
                    logger.info("  Stage routing: Cartridge extraction enabled")
                    pipeline.add_stage(ExtractArchiveStage())
                    
                    # Add compression stage based on effective_compression
                    if effective_compression == CompressionFormat.SEVENZ:
                        logger.info("  Stage routing: 7z compression enabled")
                        pipeline.add_stage(CompressArchiveStage())
                    elif effective_compression == CompressionFormat.ZIP:
                        logger.info("  Stage routing: ZIP compression enabled")
                        pipeline.add_stage(CompressArchiveStage())
                
                elif extraction_type == ExtractionType.DISC:
                    # Disc extraction: extract CUE/BIN for CHD conversion
                    logger.info("  Stage routing: Disc extraction enabled")
                    pipeline.add_stage(ExtractArchiveStage())
                    
                    # Add CHD compression if configured
                    if effective_compression == CompressionFormat.CHD:
                        logger.info("  Stage routing: CHD compression enabled")
                        pipeline.add_stage(CompressCHDStage(
                            db_session=metadata_db.get_session() if metadata_db else None,
                            cache_manager=self.cache_manager,
                        ))
                        pipeline.add_stage(CreateM3UStage())
                
                elif extraction_type == ExtractionType.RVZ:
                    # RVZ extraction: unzip Wii/GameCube RVZ archives
                    logger.info("  Stage routing: RVZ extraction enabled")
                    pipeline.add_stage(UnzipRVZStage())
                
                elif extraction_type == ExtractionType.PS3:
                    # PS3 extraction: decrypt ISO and extract to JB folder format
                    logger.info("  Stage routing: PS3 extraction enabled")
                    pipeline.add_stage(ExtractPS3Stage(
                        keys_directory=self.config.extraction.keys_directory,
                        ps3dec_path=self.config.extraction.ps3dec_path
                    ))
                
                elif extraction_type == ExtractionType.XISO:
                    # XISO extraction: extract ZIP, convert Redump ISO to XISO format
                    logger.info("  Stage routing: XISO extraction enabled (Xbox)")
                    pipeline.add_stage(ExtractArchiveStage())  # Extract from ZIP first
                    pipeline.add_stage(ConvertXISOStage(
                        extract_xiso_path=self.config.extraction.extract_xiso_path,
                        db_session=metadata_db.get_session() if metadata_db else None
                    ))
                    # Add squashfs compression if configured
                    if effective_compression == CompressionFormat.SQUASHFS:
                        logger.info("  Stage routing: Squashfs compression enabled")
                        pipeline.add_stage(CompressSquashfsStage())
                
                elif extraction_type == ExtractionType.MIXED:
                    # Mixed systems may need special handling
                    logger.warning("  MIXED extraction type not fully implemented")
            
            # Legacy system_type support for backwards compatibility (deprecated)
            elif hasattr(self.config, 'system_type') and self.config.system_type is not None:
                import warnings
                warnings.warn(
                    f"Platform uses deprecated 'system_type'. Migrate to 'extraction' config.",
                    DeprecationWarning,
                    stacklevel=2
                )
                if self.config.system_type == SystemType.COMPLEX:
                    # Complex systems (Wii/GameCube RVZ)
                    logger.info("  Stage routing: COMPLEX (unzip_rvz) - DEPRECATED")
                    pipeline.add_stage(UnzipRVZStage())
                
                elif self.config.system_type == SystemType.VERY_COMPLEX:
                    # Very complex systems (PS3, Xbox 360)
                    if self.platform_name == 'ps3':
                        logger.info("  Stage routing: VERY_COMPLEX (PS3 transform) - DEPRECATED")
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
        
        # If explicit file path is specified, use it
        if hasattr(self.config.dat, 'file') and self.config.dat.file:
            explicit_path = Path(self.config.dat.file)
            if explicit_path.exists():
                logger.info(f"  Using explicit DAT file: {explicit_path.name}")
                return explicit_path
            else:
                logger.warning(f"  Explicit DAT file not found: {explicit_path}")
                # Fall through to auto-detection
        
        # Common DAT locations based on source - use PathResolver
        from romfarmer.core.paths import get_paths
        dat_base = get_paths().dats_dir
        source = self.config.dat.source
        
        # Map source to directory
        source_map = {
            'retool_1g1r_usa': 'nointro.retool.1g1r.usa',
            'retool_1g1r_all': 'nointro.retool.1g1r.all',
            'redump_retool_1g1r_usa': 'redump.retool.1g1r.usa',
            'redump_retool_1g1r_eng': 'redump.retool.1g1r.eng',  # Explicit Redump
            'nointro_retool_1g1r_eng': 'nointro.retool.1g1r.eng',  # Explicit No-Intro
        }
        
        # Dynamic mapping for ambiguous sources
        dat_dir_name = source_map.get(source)
        
        if not dat_dir_name:
            if source == 'retool_1g1r_eng':
                # Check extraction type to decide between No-Intro and Redump
                # Default to Redump for safety if extraction type is unknown/disc
                is_cartridge = False
                if self.config.extraction and hasattr(self.config.extraction, 'type'):
                    # Check against string or Enum value
                    ext_type = str(self.config.extraction.type)
                    if 'cartridge' in ext_type.lower():
                        is_cartridge = True
                
                if is_cartridge:
                    dat_dir_name = 'nointro.retool.1g1r.eng'
                else:
                    dat_dir_name = 'redump.retool.1g1r.eng'
            else:
                # Fallback to using source as directory name
                dat_dir_name = source
            
        dat_dir = dat_base / dat_dir_name
        
        logger.info(f"  Looking for DAT in: {dat_dir}")
        logger.info(f"  DAT source: {source}")
        
        if not dat_dir.exists():
            logger.warning(f"DAT directory not found: {dat_dir}")
            return None
        
        # Load platform-to-DAT patterns from config
        platform_search = self._get_dat_pattern_for_platform()
        logger.info(f"  Platform search term: {platform_search}")
        
        # If we have a specific mapping, try that first (more specific match)
        if platform_search:
            logger.info(f"  Searching DAT files in {dat_dir}...")
            for dat_file in dat_dir.glob("*.dat"):
                logger.debug(f"  Checking: {dat_file.name}")
                if platform_search in dat_file.name.lower():
                    logger.info(f"  Found DAT file: {dat_file.name}")
                    return dat_file
        
        # Fallback to generic variants
        platform_variants = [
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
    
    def _get_dat_pattern_for_platform(self) -> Optional[str]:
        """
        Get the DAT file search pattern for the current platform.
        
        Loads patterns from config/dat_patterns.yaml. This allows adding
        new platforms without code changes.
        
        Returns:
            Search pattern string, or None if not found
        """
        import yaml
        
        patterns_path = Path("config/dat_patterns.yaml")
        if not patterns_path.exists():
            logger.warning(f"DAT patterns config not found: {patterns_path}")
            return None
        
        try:
            with open(patterns_path) as f:
                patterns = yaml.safe_load(f)
            
            if patterns and self.platform_name.lower() in patterns:
                return patterns[self.platform_name.lower()]
            
            return None
        except Exception as e:
            logger.error(f"Failed to load DAT patterns: {e}")
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
