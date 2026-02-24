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
from datetime import datetime

from romfarmer.core.paths import get_paths
from romfarmer.config.target import ComposedTarget
from romfarmer.cache import CacheManager, CacheConfig
from romfarmer.build_models import BuildStatus, BuildConfig, BuildState


logger = logging.getLogger(__name__)


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
        
        # Load composed target for target builds
        self.composed_target: Optional[ComposedTarget] = None
        if hasattr(config, 'is_target_build') and config.is_target_build():
            self._load_composed_target()
        
        # Initialize ROM cache for build acceleration
        self.cache_manager = self._initialize_cache()
        
        # Initialize budget tracker for target builds with storage budgets
        self.budget_tracker = None
        self.platform_tiers = None
        self._initialize_budget_tracking()
        
        # Setup logging
        self._setup_logging()
        
        logger.info(f"Initialized build orchestrator: {config.name}")
    
    def _initialize_budget_tracking(self):
        """Initialize budget tracking for target builds with storage budgets."""
        from romfarmer.utils.storage_budget import compute_storage_budget, BudgetTracker
        from romfarmer.config.tiers_loader import load_platform_tiers
        
        # Only for target builds with storage budget
        if not (hasattr(self.config, 'is_target_build') and self.config.is_target_build()):
            return
        
        storage_budget = getattr(self.config, 'storage_budget', None)
        if not storage_budget or storage_budget == 'unlimited':
            logger.info("No storage budget constraint - unlimited build")
            return
        
        try:
            # Parse and compute budget
            budget = compute_storage_budget(storage_budget)
            self.budget_tracker = BudgetTracker(budget)
            logger.info(f"Storage budget: {budget}")
            
            # Load platform tiers
            self.platform_tiers = load_platform_tiers()
            logger.info(f"Loaded platform tiers config")
            
        except Exception as e:
            logger.error(f"Failed to initialize budget tracking: {e}")
            raise
    
    def _initialize_cache(self) -> Optional[CacheManager]:
        """Initialize ROM cache for build acceleration.
        
        Returns:
            CacheManager if enabled, None otherwise
        """
        try:
            config = CacheConfig.from_env(workspace_root=get_paths().workspace_root)
            
            if not config.enabled:
                logger.info("ROM cache disabled (set ROMGROOMER_CACHE_ENABLED=true to enable)")
                return None
            
            cache_manager = CacheManager(config)
            stats = cache_manager.get_stats()
            logger.info(f"ROM cache enabled: {stats['total_entries']} entries, {stats['total_size_human']}")
            return cache_manager
            
        except Exception as e:
            logger.warning(f"Failed to initialize ROM cache: {e}")
            return None
    
    def _resolve_path(self, path_str: str) -> Path:
        """
        Resolve a path string to an absolute Path.
        
        If the path is relative, resolve it against the workspace root.
        If absolute, use as-is.
        """
        path = Path(path_str)
        if path.is_absolute():
            return path
        # Resolve relative paths against workspace root
        return get_paths().workspace_root / path
    
    def _load_composed_target(self):
        """Load the composed target (frontend + device) for target builds."""
        from romfarmer.config import load_composed_target
        
        target_name = self.config.target
        if not target_name:
            logger.warning("Target build missing 'target' field, cannot load composed target")
            return
        
        try:
            self.composed_target = load_composed_target(target_name)
            logger.info(f"Loaded composed target: {target_name}")
            logger.info(f"  Frontend: {self.composed_target.frontend.name}")
            logger.info(f"  Device: {self.composed_target.device.name}")
        except FileNotFoundError as e:
            logger.error(f"Failed to load composed target '{target_name}': {e}")
            raise ValueError(f"Target '{target_name}' not found. Check config/targets/{target_name}.yaml exists.")
        except Exception as e:
            logger.error(f"Error loading composed target '{target_name}': {e}")
            raise
    
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
        from romfarmer.config import load_build_config
        
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
        build_logger = logging.getLogger(f'romfarmer.build.{self.config.name}')
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
        config_dir = self._resolve_path("config/platforms")
        for platform in self.config.platforms:
            config_file = config_dir / f"{platform}.yaml"
            if not config_file.exists():
                errors.append(f"Missing platform config: {config_file}")
        
        # Check output directory writable (if storage config exists)
        storage = getattr(self.config, 'storage', {})
        if isinstance(storage, dict) and 'output_base' in storage:
            output_base = self._resolve_path(storage['output_base'])
            if not output_base.exists():
                try:
                    output_base.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create output directory {output_base}: {e}")
        
            # Check temp directory writable
            if 'temp_path' in storage:
                temp_path = self._resolve_path(storage['temp_path'])
                if not temp_path.exists():
                    try:
                        temp_path.mkdir(parents=True, exist_ok=True)
                    except Exception as e:
                        errors.append(f"Cannot create temp directory {temp_path}: {e}")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # Target build validation
        # ═══════════════════════════════════════════════════════════════════════════
        if self.composed_target:
            # Count unsupported platforms (they'll be silently skipped during processing)
            unsupported_count = sum(
                1 for p in self.config.platforms 
                if not self.composed_target.supports_platform(p)
            )
            supported_count = len(self.config.platforms) - unsupported_count
            
            if unsupported_count > 0:
                logger.debug(
                    f"{unsupported_count} platforms will be skipped "
                    f"(unsupported by {self.composed_target.device.name})"
                )
            
            if supported_count == 0:
                errors.append(
                    f"No platforms are supported by {self.composed_target.device.name}. "
                    "Check device unsupported_platforms list."
                )
            
            # Log target configuration
            logger.info(f"Target build configuration:")
            logger.info(f"  Frontend: {self.composed_target.frontend.name}")
            logger.info(f"  Device: {self.composed_target.device.name}")
            logger.info(f"  Platforms: {supported_count} supported, {unsupported_count} will be skipped")
            if hasattr(self.config, 'storage_budget') and self.config.storage_budget:
                logger.info(f"  Storage budget: {self.config.storage_budget}")
            if hasattr(self.config, 'profile') and self.config.profile:
                logger.info(f"  Profile: {self.config.profile}")
        
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
        
        if self.budget_tracker:
            from romfarmer.utils.storage_budget import format_size
            logger.info(f"Storage budget: {format_size(self.budget_tracker.budget.available_bytes)}")
        
        # Track platforms skipped due to budget
        budget_skipped = []
        
        # Process each platform
        for i, platform in enumerate(platforms_to_process, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"[{i}/{len(platforms_to_process)}] Processing: {platform}")
            logger.info(f"{'='*60}\n")
            
            # ═══════════════════════════════════════════════════════════════════════════
            # BUDGET CHECK: Skip if we're over budget (for lower-tier platforms)
            # ═══════════════════════════════════════════════════════════════════════════
            if self.budget_tracker and self.platform_tiers:
                tier = self.platform_tiers.get_platform_tier(platform)
                # Tier 1-2 always proceed, Tier 3+ check budget
                if tier and tier >= 3:
                    estimated_size = self._estimate_platform_size(platform)
                    remaining = self.budget_tracker.remaining
                    
                    if estimated_size > remaining:
                        from romfarmer.utils.storage_budget import format_size
                        logger.warning(
                            f"⚠ Skipping {platform} (Tier {tier}): "
                            f"estimated {format_size(estimated_size)} > remaining {format_size(remaining)}"
                        )
                        budget_skipped.append(platform)
                        continue
            
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
        
        # Run generation-based cross-platform deduplication (if enabled)
        self._run_generation_filter()
        
        # Run post-build hooks
        self._run_post_build_hooks()
        
        # Build complete
        self.state.status = BuildStatus.COMPLETED
        self._save_state()
        
        logger.info(f"\n{'='*60}")
        logger.info("✅ Build complete!")
        logger.info(f"{'='*60}\n")
        
        self._generate_report()
        
        # Run deployment if configured
        self._run_deployment()
    
    def _get_platforms_to_process(self, resume: bool) -> List[str]:
        """
        Get list of platforms to process.
        
        For target builds:
        - Silently filters out platforms the device cannot run
        - Orders platforms by tier (Tier 1 first, then 2, etc.)
        For resumed builds, skips already-completed platforms.
        
        Args:
            resume: If True, skip already-completed platforms
        
        Returns:
            List of platform names to process, ordered by tier
        """
        platforms = list(self.config.platforms)
        
        # ═══════════════════════════════════════════════════════════════════════════
        # Filter out unsupported platforms for target builds (silently)
        # ═══════════════════════════════════════════════════════════════════════════
        if self.composed_target:
            supported = []
            skipped_unsupported = []
            
            for platform in platforms:
                if self.composed_target.supports_platform(platform):
                    supported.append(platform)
                else:
                    skipped_unsupported.append(platform)
            
            if skipped_unsupported:
                # Log at debug level only - user doesn't need to see this
                logger.debug(
                    f"Skipping unsupported platforms for {self.composed_target.device.name}: "
                    f"{', '.join(skipped_unsupported)}"
                )
            
            platforms = supported
        
        # ═══════════════════════════════════════════════════════════════════════════
        # Order platforms by tier (lower tier = higher priority)
        # ═══════════════════════════════════════════════════════════════════════════
        if self.platform_tiers:
            def get_sort_key(platform: str) -> tuple:
                tier = self.platform_tiers.get_platform_tier(platform)
                # Unknown platforms go to tier 99 (lowest priority)
                tier_num = tier if tier is not None else 99
                # Secondary sort by name for stability
                return (tier_num, platform)
            
            platforms = sorted(platforms, key=get_sort_key)
            
            # Log the ordering
            tier_counts = {}
            for p in platforms:
                tier = self.platform_tiers.get_platform_tier(p)
                tier_key = f"Tier {tier}" if tier else "Unknown"
                tier_counts[tier_key] = tier_counts.get(tier_key, 0) + 1
            
            logger.info(f"Platform ordering by tier: {tier_counts}")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # Skip completed platforms if resuming
        # ═══════════════════════════════════════════════════════════════════════════
        if resume:
            remaining = [
                p for p in platforms
                if p not in self.state.completed_platforms
            ]
            
            if remaining != platforms:
                skipped = set(platforms) - set(remaining)
                logger.info(f"Resuming build - skipping completed: {', '.join(skipped)}")
            
            platforms = remaining
        
        return platforms
    
    def _get_tier_strategy(self, platform: str):
        """Get the selection strategy for a platform based on its tier and build profile.
        
        Args:
            platform: Platform name
            
        Returns:
            TierStrategy enum value, or None if no tier system in use
        """
        from romfarmer.config.models import TierStrategy
        
        if not self.platform_tiers:
            return None
        
        tier_num = self.platform_tiers.get_platform_tier(platform)
        if tier_num is None:
            # Unknown platform - use default strategy (best_of for safety)
            return TierStrategy.BEST_OF
        
        # Get profile from build config
        profile_name = getattr(self.config, 'profile', None)
        profile = self.platform_tiers.get_profile(profile_name) if profile_name else None
        
        # Get strategy for this tier
        return self.platform_tiers.get_strategy_for_tier(tier_num, profile)
    
    def _estimate_platform_size(self, platform: str) -> int:
        """Estimate the output size for a platform.
        
        Uses historical data from size tracking database, or falls back to
        tier-based estimates from platform_tiers.yaml.
        
        Args:
            platform: Platform name
            
        Returns:
            Estimated size in bytes
        """
        from romfarmer.utils.size_tracking import estimate_platform_size
        
        # Determine compression and selection for this platform
        compression = "7z"  # Default
        if self.composed_target:
            comp_format = self.composed_target.get_preferred_compression(platform)
            if comp_format:
                compression = comp_format.value
        
        tier_strategy = self._get_tier_strategy(platform)
        selection = tier_strategy.value if tier_strategy else "all"
        
        # Try historical data first
        historical = estimate_platform_size(platform, compression, selection)
        if historical:
            return historical
        
        # Fall back to tier-based estimates
        if self.platform_tiers:
            tier_num = self.platform_tiers.get_platform_tier(platform)
            if tier_num:
                tier = self.platform_tiers.get_tier(tier_num)
                
                # Use tier's estimated size
                if tier.estimated_total_mb:
                    # Tier 1/2 have total estimates (all platforms combined)
                    # Divide by number of platforms in tier for rough per-platform
                    per_platform = tier.estimated_total_mb // max(len(tier.platforms), 1)
                    return per_platform * 1024 * 1024
                elif tier.estimated_per_platform_mb:
                    # Tier 3+ have per-platform estimates
                    estimate = tier.estimated_per_platform_mb * 1024 * 1024
                    # Scale down for best_of selection
                    if selection == "best_of":
                        estimate = estimate // 10  # Best-of is ~10% of full set
                    elif selection == "best_of_extended":
                        estimate = estimate // 5  # Extended is ~20%
                    return estimate
        
        # Ultimate fallback: 1GB
        return 1024 * 1024 * 1024
    
    def _process_platform(self, platform: str):
        """
        Process a single platform.
        
        Args:
            platform: Platform name
        
        Raises:
            Exception: If platform processing fails
        """
        from romfarmer.platform_processor import PlatformProcessor
        
        self.state.current_platform = platform
        self._save_state()
        
        # Get tier-based selection strategy if applicable
        tier_strategy = self._get_tier_strategy(platform)
        tier_num = self.platform_tiers.get_platform_tier(platform) if self.platform_tiers else None
        
        logger.info(f"Processing platform: {platform}")
        if tier_num:
            logger.info(f"  Tier: {tier_num}, Strategy: {tier_strategy.value if tier_strategy else 'default'}")
        
        # Get overrides for this platform from build config
        platform_overrides = getattr(self.config, 'platform_overrides', {})
        overrides = platform_overrides.get(platform, {}) if isinstance(platform_overrides, dict) else {}
        
        # Add tier strategy to overrides if applicable
        if tier_strategy:
            overrides['tier_strategy'] = tier_strategy.value
            overrides['tier'] = tier_num
        
        # Get directories from config
        storage = getattr(self.config, 'storage', {})
        if isinstance(storage, dict) and 'temp_path' in storage:
            work_dir = self._resolve_path(storage['temp_path']) / platform
        else:
            # Fallback to default temp directory from PathResolver
            work_dir = get_paths().platform_temp_dir(platform)
        # Don't pass output_dir - let platform processor construct descriptive name
        # based on platform-datvariant-target (e.g., virtualboy-1g1r-eng-batocera)
        
        # Create platform processor
        processor = PlatformProcessor(
            platform_name=platform,
            overrides=overrides,
            storage_config=storage,
            composed_target=self.composed_target,  # Pass composed target for target builds
            cache_manager=self.cache_manager,  # Pass cache for build acceleration
        )
        
        # Process platform (output_dir will be constructed by processor)
        result = processor.process(
            work_dir=work_dir
        )
        
        # ═══════════════════════════════════════════════════════════════════════════
        # SIZE TRACKING: Record output size for future estimation
        # ═══════════════════════════════════════════════════════════════════════════
        output_size = result.get('output_size', 0)
        if output_size == 0 and hasattr(processor, 'output_dir') and processor.output_dir and processor.output_dir.exists():
            # Calculate output size if not provided in result
            output_size = sum(f.stat().st_size for f in processor.output_dir.rglob('*') if f.is_file())
            result['output_size'] = output_size
        
        if output_size > 0:
            # Record to size tracking database for future estimation
            from romfarmer.utils.size_tracking import record_platform_size
            
            # Determine compression format used
            compression = "none"
            if self.composed_target:
                comp_format = self.composed_target.get_preferred_compression(platform)
                if comp_format:
                    compression = comp_format.value
            elif hasattr(self.config, 'compression') and self.config.compression:
                compression = self.config.compression.format.value if self.config.compression.format else "none"
            
            # Determine selection strategy used
            selection = tier_strategy.value if tier_strategy else "all"
            
            record_platform_size(
                platform=platform,
                compression=compression,
                output_size_bytes=output_size,
                selection=selection,
                output_files=result.get('files_processed', 0),
            )
        
        # Track budget usage if tracking
        if self.budget_tracker and output_size > 0:
            self.budget_tracker.record_actual(platform, output_size)
            from romfarmer.utils.storage_budget import format_size
            logger.info(f"  Output size: {format_size(output_size)}")
            logger.info(f"  Budget remaining: {format_size(self.budget_tracker.remaining)}")
        
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
        report_path = get_paths().build_report_file(self.config.name)
        
        duration = datetime.now() - self.state.started_at
        
        with open(report_path, 'w') as f:
            f.write(f"Build Report: {self.config.name}\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Description: {self.config.description}\n")
            f.write(f"Version: {self.config.version or 'N/A'}\n\n")
            
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
    
    def _run_generation_filter(self):
        """Run cross-platform generation deduplication if configured."""
        # Check if generation filter is enabled
        generation_filter = getattr(self.config, 'generation_filter', None)
        if not generation_filter or not generation_filter.enabled:
            logger.debug("Generation filter not enabled, skipping")
            return
        
        logger.info(f"\n{'='*60}")
        logger.info("Running generation-based cross-platform deduplication...")
        logger.info(f"{'='*60}\n")
        
        try:
            from romfarmer.config.generation_loader import load_generation
            from romfarmer.stages.filter_generation import FilterGenerationStage, GenerationConfig
            from romfarmer.stages.base import StageContext
            from pathlib import Path
            
            # Load generation definition
            generation_def = load_generation(generation_filter.generation)
            if not generation_def:
                logger.error(f"Generation not found: {generation_filter.generation}")
                return
            
            logger.info(f"Loaded generation: {generation_def.label}")
            logger.info(f"  Description: {generation_def.description}")
            logger.info(f"  Platform priority: {' > '.join(generation_def.get_platform_names())}")
            
            # Convert to stage config
            stage_config = GenerationConfig(
                name=generation_def.name,
                label=generation_def.label,
                platforms=generation_def.get_platform_names(),
                enabled=generation_def.enabled
            )
            
            # Prepare rescue lists (if configured)
            rescue_lists = None
            if generation_filter.rescue_lists:
                rescue_lists = {
                    platform: set(game.lower() for game in games)
                    for platform, games in generation_filter.rescue_lists.items()
                }
                logger.info(f"Rescue lists loaded for platforms: {', '.join(rescue_lists.keys())}")
            else:
                # Check for AI-generated cached rescue lists
                cache_file = Path("config/curations/rescue") / f"rescue-{generation_def.name}.yaml"
                if cache_file.exists():
                    from .ai.rescue_generator import RescueListResult
                    cached = RescueListResult.from_yaml(cache_file.read_text())
                    rescue_lists = {
                        platform: set(game.lower() for game in games)
                        for platform, games in cached.rescue_lists.items()
                    }
                    total = sum(len(g) for g in rescue_lists.values())
                    logger.info(f"Loaded AI-generated rescue lists: {total} games from {cache_file}")
            
            # Create filter stage
            filter_stage = FilterGenerationStage(stage_config, rescue_lists)
            
            # Determine output directory
            storage = getattr(self.config, 'storage', {})
            if isinstance(storage, dict):
                output_base = self._resolve_path(storage.get('output_base', 'output'))
                # Get the specific build output folder
                # For gen5-dedupe-batocera, this would be output/gen5-dedupe-batocera/
                output_template = storage.get('output_template', '{filter}-{region}-{format}-{target}')
                if '{' in output_template:
                    # Template uses placeholders - use build name directly
                    build_output = output_base / self.config.name
                else:
                    build_output = output_base / output_template
            else:
                build_output = self._resolve_path(f"output/{self.config.name}")
            
            logger.info(f"Processing output directory: {build_output}")
            
            # Create stage context
            context = StageContext(
                platform="generation_filter",
                work_dir=Path(f"temp/{self.config.name}_genfilter"),
                output_dir=build_output
            )
            # Add generation output dir for the stage to find platform subdirectories
            context.generation_output_dir = build_output
            
            # Run the filter
            result = filter_stage.execute(context)
            
            # Log results
            if result.status.value == "success":
                logger.info(f"\n✅ Generation filter complete!")
                logger.info(f"   {result.message}")
                logger.info(f"   Duration: {result.duration_seconds:.1f}s")
            elif result.status.value == "skipped":
                logger.info(f"⏭  Generation filter skipped: {result.message}")
            else:
                logger.warning(f"⚠  Generation filter issue: {result.message}")
                
        except Exception as e:
            logger.error(f"Error running generation filter: {e}", exc_info=True)
            # Don't fail the entire build for generation filter errors
            logger.warning("Generation filter failed, but build will continue")
    
    def _run_post_build_hooks(self):
        """Run post-build hooks (e.g., jdupes for deduplication)."""
        import subprocess
        
        post_build = getattr(self.config, 'post_build', [])
        if not post_build:
            return
        
        logger.info(f"\n{'='*60}")
        logger.info("Running post-build hooks...")
        logger.info(f"{'='*60}\n")
        
        # Get output base for variable substitution
        storage = getattr(self.config, 'storage', {})
        paths = get_paths()
        output_base = storage.get('output_base', str(paths.output_dir)) if isinstance(storage, dict) else str(paths.output_dir)
        
        for i, hook in enumerate(post_build, 1):
            name = hook.get('name', f'Hook {i}')
            command = hook.get('command', '')
            enabled = hook.get('enabled', True)
            
            if not enabled:
                logger.info(f"  ⊘ Skipping disabled hook: {name}")
                continue
            
            if not command:
                logger.warning(f"  ⚠ Hook '{name}' has no command, skipping")
                continue
            
            # Substitute variables in command
            command = command.replace('{output_base}', str(output_base))
            command = command.replace('{build_name}', self.config.name)
            
            logger.info(f"  Running: {name}")
            logger.info(f"    Command: {command}")
            
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    logger.info(f"    ✅ Success")
                    if result.stdout.strip():
                        # Log first few lines of output
                        lines = result.stdout.strip().split('\n')
                        for line in lines[:5]:
                            logger.info(f"      {line}")
                        if len(lines) > 5:
                            logger.info(f"      ... ({len(lines) - 5} more lines)")
                else:
                    logger.error(f"    ❌ Failed (exit code {result.returncode})")
                    if result.stderr:
                        logger.error(f"    {result.stderr}")
                        
            except Exception as e:
                logger.error(f"    ❌ Error: {e}")
    
    def _run_deployment(self):
        """Run deployment (rsync to target device)."""
        import subprocess
        
        deploy = getattr(self.config, 'deploy', None)
        if not deploy:
            return
        
        enabled = deploy.get('enabled', True)
        if not enabled:
            logger.info("Deployment disabled, skipping")
            return
        
        target = deploy.get('target', '')
        if not target:
            logger.warning("No deployment target specified, skipping")
            return
        
        logger.info(f"\n{'='*60}")
        logger.info("Running deployment...")
        logger.info(f"{'='*60}\n")
        
        # Get output base
        storage = getattr(self.config, 'storage', {})
        paths = get_paths()
        output_base = storage.get('output_base', str(paths.output_dir)) if isinstance(storage, dict) else str(paths.output_dir)
        
        # Build rsync command
        # -a: archive mode (preserves permissions, timestamps, etc.)
        # -v: verbose
        # -H: preserve hard links (CRITICAL for jdupes dedup)
        # --progress: show progress
        rsync_opts = deploy.get('rsync_options', '-avH --progress')
        delete_flag = '--delete' if deploy.get('delete_extra', False) else ''
        dry_run = '--dry-run' if deploy.get('dry_run', False) else ''
        
        command = f"rsync {rsync_opts} {delete_flag} {dry_run} {output_base}/ {target}"
        
        logger.info(f"  Target: {target}")
        logger.info(f"  Command: {command}")
        
        if deploy.get('confirm', True):
            logger.info("  (Deployment requires --deploy flag to execute)")
            return
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=False  # Show live output
            )
            
            if result.returncode == 0:
                logger.info("  ✅ Deployment complete")
            else:
                logger.error(f"  ❌ Deployment failed (exit code {result.returncode})")
                
        except Exception as e:
            logger.error(f"  ❌ Deployment error: {e}")
    
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
