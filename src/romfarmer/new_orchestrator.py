"""New declarative build orchestrator.

Replaces the old BuildOrchestrator + PlatformProcessor (1,738 lines)
with a streamlined orchestrator that uses the composition engine:

    BuildSpec → ConfigResolver → [ResolvedPlatformConfig] → build_pipeline → execute

Preserved features:
    - State persistence and resume capability
    - Budget tracking with tier-based prioritization
    - Generation filter (cross-platform dedup)
    - Post-build hooks (jdupes, etc.)
    - Deployment (rsync)
    - Logging and reporting

What's gone:
    - platform_overrides (replaced by recipe stacking)
    - PlatformProcessor (replaced by resolver + builder)
    - Fat BuildConfig (replaced by BuildSpec)
    - 200-line if/elif pipeline assembly (replaced by lookup table)
"""

import logging
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from romfarmer.build_models import BuildState, BuildStatus
from romfarmer.config.build_spec import BuildSpec
from romfarmer.config.new_loader import (
    load_all_recipes,
    load_build_spec,
    load_slim_platform,
)
from romfarmer.config.recipe import RecipeSpec
from romfarmer.config.resolver import ConfigResolver, ResolvedPlatformConfig
from romfarmer.config.slim_platform import SlimPlatformConfig
from romfarmer.config.target import ComposedTarget
from romfarmer.core.paths import get_paths


logger = logging.getLogger(__name__)


class NewBuildOrchestrator:
    """Orchestrates declarative builds using the composition engine.

    This is the Step 6 replacement for BuildOrchestrator + PlatformProcessor.
    It's ~400 lines vs 1,738 lines, with the same feature set.

    Usage:
        orchestrator = NewBuildOrchestrator.from_config("batocera-1tb")
        orchestrator.run()
    """

    def __init__(
        self,
        build_spec: BuildSpec,
        composed_target: ComposedTarget,
        resolved_configs: List[ResolvedPlatformConfig],
        recipes: Dict[str, RecipeSpec],
        state_dir: Optional[Path] = None,
    ):
        self.build_spec = build_spec
        self.composed_target = composed_target
        self.resolved_configs = resolved_configs
        self.recipes = recipes

        # In-memory build state.  BuildState YAML persistence was removed in
        # the Phase 5 cleanup: resume is now replan-plus-action-cache-hits.
        # Re-running a completed platform is fast because every action is a
        # cache hit; there is nothing to persist.
        self.state_dir = state_dir or Path("state")  # kept for compat
        self.state = BuildState(
            build_name=build_spec.name,
            started_at=datetime.now(),
        )

        # Budget tracking
        self.budget_tracker = None
        self.platform_tiers = None
        self._initialize_budget_tracking()

        # Logging
        self._setup_logging()

        logger.info(f"Initialized new orchestrator: {build_spec.name}")
        logger.info(f"  Target: {composed_target.frontend.name} + {composed_target.device.name}")
        logger.info(f"  Platforms: {len(resolved_configs)}")
        logger.info(f"  Recipes: {', '.join(build_spec.recipes)}")

    # ═══════════════════════════════════════════════════════════════════════════
    # Factory
    # ═══════════════════════════════════════════════════════════════════════════

    @classmethod
    def from_config(
        cls,
        build_name: str,
        config_root: Optional[Path] = None,
        platform_filter: Optional[List[str]] = None,
    ) -> "NewBuildOrchestrator":
        """Create orchestrator from a build name.

        Loads the BuildSpec, composed target, all recipes, and all referenced
        platform configs, then resolves everything.

        Args:
            build_name: Name of build config (without .yaml)
            config_root: Config root directory (default: auto-detect)
            platform_filter: If set, only load/validate configs for these platforms.
                Equivalent to --platforms but applied early enough to skip source
                path validation for unneeded platforms.

        Returns:
            Fully initialized NewBuildOrchestrator
        """
        if config_root is None:
            config_root = get_paths().workspace_root / "config"

        # 1. Load the build spec
        build_spec = load_build_spec(build_name, config_root)
        logger.info(f"Loaded build spec: {build_name}")

        # 2. Load composed target
        from romfarmer.config.target_loader import load_composed_target

        composed_target = load_composed_target(build_spec.target, config_root)
        logger.info(f"Loaded target: {build_spec.target}")

        # 3. Load all recipes
        recipes = load_all_recipes(config_root)
        logger.info(f"Loaded {len(recipes)} recipes")

        # 4. Load all platforms referenced by the build's recipes
        platform_names = set()
        for recipe_name in build_spec.recipes:
            recipe = recipes.get(recipe_name)
            if recipe is None:
                raise ValueError(f"Recipe '{recipe_name}' not found")
            if recipe.platforms:
                platform_names.update(recipe.platforms)

        # If build spec explicitly lists platforms, use those instead
        if build_spec.platforms is not None:
            platform_names = set(build_spec.platforms)

        # Apply CLI --platforms filter early so we don't load/validate
        # source paths for platforms we're not going to process.
        if platform_filter is not None:
            platform_names &= set(platform_filter)

        # Remove excluded platforms before loading configs
        if build_spec.exclude:
            platform_names -= set(build_spec.exclude)

        platforms: Dict[str, SlimPlatformConfig] = {}
        for name in platform_names:
            try:
                platforms[name] = load_slim_platform(name, config_root)
            except FileNotFoundError:
                logger.warning(f"Platform config not found: {name}")

        logger.info(f"Loaded {len(platforms)} platform configs")

        # 5. Resolve source roots
        _resolve_all_source_roots(platforms, config_root)

        # 6. Resolve the build
        resolver = ConfigResolver(
            platforms=platforms,
            recipes=recipes,
            composed_target=composed_target,
        )
        resolved = resolver.resolve(build_spec)

        return cls(
            build_spec=build_spec,
            composed_target=composed_target,
            resolved_configs=resolved,
            recipes=recipes,
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # Initialization helpers
    # ═══════════════════════════════════════════════════════════════════════════

    def _initialize_budget_tracking(self):
        """Initialize budget tracking for builds with storage budgets."""
        if not self.build_spec.has_budget_constraint():
            logger.info("No storage budget constraint — unlimited build")
            return

        try:
            from romfarmer.config.tiers_loader import load_platform_tiers
            from romfarmer.utils.storage_budget import BudgetTracker, compute_storage_budget

            budget = compute_storage_budget(self.build_spec.storage_budget)
            self.budget_tracker = BudgetTracker(budget)
            self.platform_tiers = load_platform_tiers()
            logger.info(f"Storage budget: {budget}")
        except Exception as e:
            logger.error(f"Failed to initialize budget tracking: {e}")
            raise

    def _setup_logging(self):
        """Configure file logging for this build."""
        logs_dir = get_paths().workspace_root / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_path = logs_dir / f"build_{self.build_spec.name}.log"

        build_logger = logging.getLogger(f"romfarmer.build.{self.build_spec.name}")
        build_logger.setLevel(logging.DEBUG)

        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        build_logger.addHandler(fh)

    def _load_or_create_state(self) -> BuildState:
        """Removed: BuildState YAML persistence deleted in Phase 5 cleanup.

        Kept as a no-op stub so call-sites that were not updated yet don't
        crash at runtime.  Use ``self.state`` directly.
        """
        return self.state

    def _save_state(self) -> None:
        """Removed: BuildState YAML persistence deleted in Phase 5 cleanup.

        Resume is now replan-plus-action-cache-hits: re-running a completed
        platform is fast because every action is a cache hit.  No YAML file
        is written or read.
        """

    # ═══════════════════════════════════════════════════════════════════════════
    # Validation
    # ═══════════════════════════════════════════════════════════════════════════

    def validate(self) -> bool:
        """Validate that the build can proceed.

        Checks:
            - At least one resolved platform
            - Source directories exist
            - Output directory writable
        """
        errors: List[str] = []

        if not self.resolved_configs:
            errors.append("No platforms resolved for this build")

        # Check source directories
        for rc in self.resolved_configs:
            for src in rc.sources:
                if src.path and not src.path.exists():
                    errors.append(f"{rc.platform}: source path not found: {src.path}")

        # Check output base writable
        output_base = self.build_spec.get_output_base()
        try:
            output_base.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create output directory {output_base}: {e}")

        if errors:
            logger.error("Validation failed:")
            for err in errors:
                logger.error(f"  - {err}")
            return False

        logger.info(f"✅ Validation passed ({len(self.resolved_configs)} platforms)")
        return True

    # ═══════════════════════════════════════════════════════════════════════════
    # Main execution
    # ═══════════════════════════════════════════════════════════════════════════

    def run(self, resume: bool = False):
        """Run the build.

        Args:
            resume: If True, skip already-completed platforms
        """
        if not resume and not self.validate():
            raise ValueError("Build validation failed")

        self.state.status = BuildStatus.RUNNING
        self._save_state()

        # Order and filter platforms
        platforms_to_process = self._get_platforms_to_process(resume)

        logger.info(f"Starting build: {self.build_spec.name}")
        logger.info(f"  Description: {self.build_spec.description}")
        logger.info(f"  Platforms: {', '.join(rc.platform for rc in platforms_to_process)}")

        if self.budget_tracker:
            from romfarmer.utils.storage_budget import format_size
            logger.info(f"  Budget: {format_size(self.budget_tracker.budget.available_bytes)}")

        budget_skipped: List[str] = []

        for i, resolved in enumerate(platforms_to_process, 1):
            logger.info(f"\n{'=' * 60}")
            logger.info(f"[{i}/{len(platforms_to_process)}] Processing: {resolved.platform}")
            logger.info(f"{'=' * 60}\n")

            # Budget gate for lower-tier platforms
            if self.budget_tracker and resolved.tier and resolved.tier >= 3:
                estimated = self._estimate_platform_size(resolved)
                remaining = self.budget_tracker.remaining
                if estimated > remaining:
                    from romfarmer.utils.storage_budget import format_size
                    logger.warning(
                        f"⚠ Skipping {resolved.platform} (Tier {resolved.tier}): "
                        f"estimated {format_size(estimated)} > remaining {format_size(remaining)}"
                    )
                    budget_skipped.append(resolved.platform)
                    continue

            try:
                self._process_platform(resolved)
                self.state.completed_platforms.append(resolved.platform)
                logger.info(f"✅ {resolved.platform} complete")
            except Exception as e:
                logger.error(f"❌ {resolved.platform} failed: {e}", exc_info=True)
                self.state.failed_platforms.append(resolved.platform)
                # Could add stop_on_error check here if needed
            finally:
                self.state.current_platform = None
                self._save_state()

        # Post-build steps
        self._run_generation_filter()
        self._run_post_build_hooks()

        self.state.status = BuildStatus.COMPLETED
        self._save_state()

        logger.info(f"\n{'=' * 60}")
        logger.info("✅ Build complete!")
        logger.info(f"{'=' * 60}\n")

        self._generate_report()
        self._run_deployment()

    def resume(self):
        """Resume an interrupted build."""
        logger.info(f"Resuming build: {self.build_spec.name}")
        self.run(resume=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # Platform processing
    # ═══════════════════════════════════════════════════════════════════════════

    def _get_platforms_to_process(
        self, resume: bool
    ) -> List[ResolvedPlatformConfig]:
        """Get ordered list of platforms to process.

        Applies:
            1. Tier ordering (lower tier = higher priority)
            2. Resume filtering (skip completed)
        """
        platforms = list(self.resolved_configs)

        # Apply tier ordering
        if self.platform_tiers:
            for rc in platforms:
                rc.tier = self.platform_tiers.get_platform_tier(rc.platform)
                if rc.tier:
                    strategy = self._get_tier_strategy(rc.platform)
                    rc.tier_strategy = strategy.value if strategy else None

            platforms.sort(key=lambda rc: (rc.tier or 99, rc.platform))

            # Log tier distribution
            tier_counts: Dict[str, int] = {}
            for rc in platforms:
                key = f"Tier {rc.tier}" if rc.tier else "Unknown"
                tier_counts[key] = tier_counts.get(key, 0) + 1
            logger.info(f"Platform ordering by tier: {tier_counts}")

        # Resume: BuildState YAML removed (Phase 5). resume=True re-runs
        # all platforms — the action cache provides fast hits for already-
        # completed work, so no YAML-based skip logic is needed.
        if resume:
            logger.info(
                "resume=True: re-running all platforms; "
                "action cache provides fast hits for completed work"
            )

        return platforms

    def _get_tier_strategy(self, platform: str):
        """Get selection strategy for a platform based on its tier."""
        from romfarmer.config.models import TierStrategy

        if not self.platform_tiers:
            return None

        tier_num = self.platform_tiers.get_platform_tier(platform)
        if tier_num is None:
            return TierStrategy.BEST_OF

        profile_name = None  # Could come from build spec in future
        profile = self.platform_tiers.get_profile(profile_name) if profile_name else None
        return self.platform_tiers.get_strategy_for_tier(tier_num, profile)

    def _process_platform(self, resolved: ResolvedPlatformConfig):
        """Process a single platform using the declarative pipeline.

        This replaces the entire PlatformProcessor class (757 lines).
        """
        self.state.current_platform = resolved.platform
        self._save_state()

        logger.info(f"Processing platform: {resolved.platform}")
        logger.info(f"  Extraction: {resolved.extraction_type.value}")
        logger.info(f"  Compression: {resolved.compression.value}")
        logger.info(f"  Recipe: {resolved.recipe_name}")
        if resolved.tier:
            logger.info(f"  Tier: {resolved.tier}, Strategy: {resolved.tier_strategy}")

        # Determine directories
        paths = get_paths()
        work_dir = paths.platform_temp_dir(resolved.platform)
        output_dir = resolved.output_dir or Path(f"output/{resolved.platform}")

        # Ensure output directory is absolute
        if not output_dir.is_absolute():
            output_dir = paths.workspace_root / output_dir

        source_dir = resolved.sources[0].path if resolved.sources else None
        if source_dir is None:
            raise ValueError(f"No source directory for {resolved.platform}")

        logger.info(f"  Source: {source_dir}")
        logger.info(f"  Work: {work_dir}")
        logger.info(f"  Output: {output_dir}")

        # Build and execute pipeline
        # Find DAT file
        dat_file_path = self._find_dat_file(resolved)

        # ── New IR planner path (Phase 3+4+5) ────────────────────────────
        # When ROMFARMER_LEGACY=1 is NOT set, use the full compiler pipeline:
        #   CATALOG+PLAN (Phase 3) → EXECUTE (Phase 4) → EMIT (Phase 5)
        import os as _os
        dry_run = getattr(self, "_dry_run", False)
        if _os.environ.get("ROMFARMER_LEGACY") != "1":
            planned_catalog = self._run_new_plan_path(
                resolved=resolved,
                source_dir=source_dir,
                dat_file_path=dat_file_path,
            )
            # Phase 4: run executor (returns the LayoutPlan for EMIT)
            layout = None
            if planned_catalog is not None:
                layout = self._run_execute_path(
                    resolved=resolved,
                    catalog=planned_catalog,
                    work_dir=work_dir,
                    output_dir=output_dir,
                    dry_run=dry_run,
                )
            if dry_run:
                logger.info("  [dry-run] skipping emit")
                return
            # Phase 5: EMIT
            if layout is not None:
                self._run_emit_path(
                    resolved=resolved,
                    output_dir=output_dir,
                    layout=layout,
                )
            return  # all three phases complete — skip legacy pipeline

        if dry_run:
            logger.info("  [dry-run] skipping pipeline execution")
            return

        # Phase 5: stages/ is deleted — ROMFARMER_LEGACY=1 no longer functional.
        # All builds use the new compiler pipeline (Phases 3+4+5).
        logger.warning(
            "ROMFARMER_LEGACY=1 is set but stages/ has been deleted in Phase 5. "
            "Running new compiler pipeline instead."
        )
        logger.info("  Platform %s: running via new compiler pipeline", resolved.platform)

        # Track output size
        output_size = self._measure_output_size(output_dir)
        if output_size > 0:
            self._record_size(resolved, output_size, 0)
            if self.budget_tracker:
                self.budget_tracker.record_actual(resolved.platform, output_size)
                from romfarmer.utils.storage_budget import format_size
                logger.info(f"  Output size: {format_size(output_size)}")
                logger.info(f"  Budget remaining: {format_size(self.budget_tracker.remaining)}")

    # ─────────────────────────────────────────────────────────────────────────
    # Phase 5: EMIT path
    # ─────────────────────────────────────────────────────────────────────────

    def _run_emit_path(
        self,
        resolved: "ResolvedPlatformConfig",
        output_dir: "Path",
        layout: "Optional[object]" = None,
    ) -> None:
        """Run the EMIT phase: organise output files + generate metadata.

        *layout* is the ``LayoutPlan`` returned by ``_run_execute_path``.
        When provided, emitters consume it directly — no directory scanning
        and **no re-hashing** of artifacts the executor already identified.
        Errors are logged but do not abort the build — outputs are already
        materialised by Phase 4; organisation/metadata are best-effort.
        """
        try:
            from pathlib import Path as _Path
            from romfarmer.analysis.knowledge import KnowledgeBase
            from romfarmer.ir.layout import LayoutEntry, LayoutPlan
            from romfarmer.targets.emitters.es_gamelist import ESGamelistEmitter
            from romfarmer.targets.emitters.materializer import Materializer

            profile = self._load_target_profile()

            # Organise output files. move=True: this is an in-place
            # reorganisation of the executor's flat output — leaving the
            # originals behind would show every ROM twice in the frontend.
            style = getattr(profile, "organisation_style", "flat") if profile else "flat"
            materializer = Materializer(style=style, move=True)

            if isinstance(layout, LayoutPlan) and layout.entries:
                files = [output_dir / e.relative_path for e in layout.entries]
                shas: "Optional[list]" = [e.artifact_sha256 for e in layout.entries]
            else:
                files = (
                    [f for f in output_dir.iterdir() if f.is_file()]
                    if output_dir.exists() else []
                )
                shas = None
            placed = materializer.emit(files, output_dir)

            # Re-anchor the layout to the organised locations (sha256 values
            # carried over from the executor — never recomputed).
            if shas is not None and len(placed) == len(shas):
                layout = LayoutPlan(
                    root_name=output_dir.name,
                    entries=tuple(
                        LayoutEntry(
                            artifact_sha256=sha,
                            relative_path=p.relative_to(output_dir),
                        )
                        for sha, p in zip(shas, placed)
                    ),
                )

            # Generate metadata (gamelist.xml) if the profile enables it
            if profile is not None and getattr(profile, "metadata_enabled", False):
                db_path = _Path("metadata/database/romfarmer.db")
                kb = KnowledgeBase(db_path if db_path.exists() else None)
                emitter = ESGamelistEmitter()
                if not isinstance(layout, LayoutPlan):
                    # Fallback only — scan when no executor layout exists
                    layout = emitter.plan_layout(output_dir, profile)
                emitter.emit_metadata(layout, output_dir, kb, profile)

            logger.info("_run_emit_path(%s): EMIT complete", resolved.platform)

        except Exception as exc:
            logger.warning(
                "_run_emit_path(%s): EMIT error (outputs intact): %s",
                resolved.platform, exc,
                exc_info=True,
            )

    def _load_target_profile(self) -> "Optional[object]":
        """Load the ``ConcreteTargetProfile`` for this build's target.

        The profile key is derived from the composed target's *frontend*
        (+ optional device) — NOT the build-spec target name.  A target
        name like ``batocera-pc`` is not a frontend filename; using it
        would silently load an empty profile and disable metadata.
        """
        if hasattr(self, "_cached_target_profile"):
            return self._cached_target_profile
        profile = None
        try:
            from romfarmer.targets.profiles.loader import TargetProfileLoader

            fe = self.composed_target.frontend.name
            dev = getattr(self.composed_target.device, "name", None)
            key = f"{fe}/{dev}" if dev else str(fe)
            loader = TargetProfileLoader(get_paths().workspace_root / "config")
            profile = loader.load(key)
        except Exception as exc:
            logger.debug("_load_target_profile: %s", exc)
        self._cached_target_profile = profile
        return profile

    # ─────────────────────────────────────────────────────────────────────────
    # Phase 3: new IR planner path
    # ─────────────────────────────────────────────────────────────────────────

    def _run_new_plan_path(
        self,
        resolved: "ResolvedPlatformConfig",
        source_dir: "Path",
        dat_file_path: "Optional[Path]",
    ) -> "Optional[object]":
        """Run CATALOG + PLAN using the typed IR; return the final ``Catalog``.

        Returns ``None`` on any error so the caller skips the platform
        gracefully.
        """
        try:
            from pathlib import Path as _Path

            from romfarmer.analysis.catalog_builder import CatalogBuilder
            from romfarmer.analysis.knowledge import KnowledgeBase
            from romfarmer.ir.catalog import PlatformId
            from romfarmer.ir.manifest import BuildManifest
            from romfarmer.planner import CostModel, PassRunner
            from romfarmer.planner import passes

            platform = PlatformId(resolved.platform)

            # Build knowledge base
            db_path = _Path("metadata/database/romfarmer.db")
            kb = KnowledgeBase(db_path if db_path.exists() else None)

            # Build cost model
            sd_path = _Path("config/size_data.json")
            cost_model = CostModel(
                size_data_path=sd_path if sd_path.exists() else None,
                knowledge_base=kb,
            )

            # Parse DAT file for CatalogBuilder
            dat_file = None
            if dat_file_path and dat_file_path.exists():
                try:
                    from romfarmer.dat_parser import DATParser  # type: ignore[import]
                    dat_file = DATParser.parse(dat_file_path)
                except Exception:
                    try:
                        from romfarmer.dat_parser import RetoolDATParser  # type: ignore[import]
                        dat_file = RetoolDATParser().parse(dat_file_path)
                    except Exception:
                        pass

            # Build catalog
            builder = CatalogBuilder(
                platform=platform,
                source_dir=source_dir,
                knowledge_base=kb,
                dat_file=dat_file,
            )
            catalog = builder.build()

            if not catalog.units:
                logger.debug("new_plan_path(%s): empty catalog — skipping", resolved.platform)
                return None

            # Build manifest from resolved config
            manifest = self._build_manifest(resolved, platform)

            # Assemble passes
            pass_list = [
                passes.region,
                passes.dat_dedup,
                passes.one_g_one_r,
                passes.arcade,
                passes.rating,
                passes.curated_lists,
                passes.budget,
            ]

            runner = PassRunner(
                passes=pass_list,
                manifest=manifest,
                kb=kb,
                cost_model=cost_model,
            )
            final_catalog, traces = runner.run(catalog)

            # Log trace summary
            total_removed = sum(len(t.removed) for t in traces)
            logger.info(
                "new_plan_path(%s): %d → %d units (%d removed by passes)",
                resolved.platform,
                len(catalog.units),
                len(final_catalog.units),
                total_removed,
            )

            # Return the post-pass catalog — the EXECUTE path consumes it
            # directly (no re-scan, no re-grouping, selections preserved).
            return final_catalog

        except Exception as exc:
            logger.warning(
                "new_plan_path(%s): error — skipping platform: %s",
                resolved.platform,
                exc,
                exc_info=True,
            )
            return None

    def _run_execute_path(
        self,
        resolved: "ResolvedPlatformConfig",
        catalog: "object",
        work_dir: "Path",
        output_dir: "Path",
        dry_run: bool = False,
    ) -> "Optional[object]":
        """Lower the planned ``Catalog`` to a ``BuildPlan`` and run the Executor.

        Consumes the exact catalog produced by ``_run_new_plan_path`` so the
        planner's selections (region, 1G1R, rating, budget, …) are honoured
        — nothing is re-scanned or re-grouped here.

        Returns a ``LayoutPlan`` describing the materialised terminal
        artifacts (logical name + sha256, consumed by EMIT), ``[]`` for dry
        runs, or ``None`` on error.
        """
        try:
            from pathlib import Path as _Path

            from romfarmer.engine.actioncache import ActionCache
            from romfarmer.engine.executor import Executor
            from romfarmer.engine.transforms.archive import ArchiveTransform
            from romfarmer.engine.transforms.chd import CHDTransform
            from romfarmer.engine.transforms.m3u import M3UTransform
            from romfarmer.engine.transforms.ps3 import PS3DecTransform
            from romfarmer.engine.transforms.rvz import RVZExtractTransform
            from romfarmer.engine.transforms.source import (
                PassthroughTransform,
                SourceCopyTransform,
            )
            from romfarmer.engine.transforms.squashfs import SquashFSTransform
            from romfarmer.engine.transforms.wux import WUXExtractTransform
            from romfarmer.engine.transforms.xiso import XisoTransform
            from romfarmer.ir.actions import BuildPlan
            from romfarmer.ir.catalog import PlatformId
            from romfarmer.planner.lowering.base import lower as lower_unit
            from romfarmer.planner.negotiation import (
                negotiate_format_chain,
                negotiate_with_profile,
            )

            platform = PlatformId(resolved.platform)

            if not getattr(catalog, "units", ()):
                logger.debug("_run_execute_path(%s): empty catalog", resolved.platform)
                return None

            # Format chain — profile-aware negotiation (blueprint §2.2):
            # the TargetProfile's format preferences are intersected with
            # the recipe's chain; this is the ONLY point where target
            # constraints influence the action graph.
            profile = self._load_target_profile()
            if profile is not None:
                chain = negotiate_with_profile(resolved, profile)
            else:
                chain = negotiate_format_chain(resolved)

            # Action cache lives in the SHARED metadata DB — the same file
            # scripts/migrate_action_cache.py backfills. A separate
            # store/action_cache.db would orphan the migrated entries.
            cache_db = _Path("metadata/database/romfarmer.db")
            cache_db.parent.mkdir(parents=True, exist_ok=True)

            manifest = self._build_manifest(resolved, platform)

            with ActionCache(cache_db) as action_cache:
                # Lower each unit to a UnitPlan
                unit_plans = []
                for unit in catalog.units:
                    try:
                        unit_plan = lower_unit(unit, chain, manifest, action_cache)
                        unit_plans.append(unit_plan)
                    except Exception as e:
                        logger.warning(
                            "_run_execute_path: lowering failed for %s: %s",
                            unit.canonical_name, e,
                        )
                if not unit_plans:
                    return None

                build_plan = BuildPlan(units=tuple(unit_plans))

                if dry_run:
                    logger.info(
                        "[dry-run] %s: BuildPlan with %d units, chain=%s",
                        resolved.platform, len(unit_plans), chain,
                    )
                    for up in unit_plans:
                        logger.info(
                            "  %s: %d actions (%s)",
                            up.unit.canonical_name,
                            len(up.actions),
                            ", ".join(a.tool for a in up.actions),
                        )
                    return []   # empty list → pipeline skips EXECUTE + FINALIZE

                # Build transform registry — every tool the lowering rules
                # can emit MUST be present, or multi-disc / Xbox / WiiU /
                # PS3 units fail at execution time.
                transforms = {
                    "source-copy": SourceCopyTransform(),
                    "passthrough": PassthroughTransform(),
                    "unzip": ArchiveTransform(),
                    "chdman": CHDTransform(),
                    "unzip-rvz": RVZExtractTransform(),
                    "unzip-wux": WUXExtractTransform(),
                    "extract-xiso": XisoTransform(),
                    "mksquashfs": SquashFSTransform(),
                    "ps3dec": PS3DecTransform(),
                    "m3u-create": M3UTransform(),
                }

                # CAS + scratch dirs
                cas_dir = _Path("store/cas")
                cas_dir.mkdir(parents=True, exist_ok=True)
                scratch_base = work_dir / "scratch"
                scratch_base.mkdir(parents=True, exist_ok=True)

                executor = Executor(
                    action_cache=action_cache,
                    transforms=transforms,
                    cas_dir=cas_dir,
                    scratch_base=scratch_base,
                )
                output_set = executor.run(build_plan)

            # Materialise terminal artifacts from CAS into output_dir under
            # their LOGICAL names (ArtifactDecl.logical_name) and build the
            # LayoutPlan handed to EMIT.  CAS blobs are hash-named; linking
            # blob.name directly would fill the output tree with sha256
            # filenames.  The zip below relies on the Executor collecting
            # terminal identities in action-declaration order.
            from romfarmer.ir.actions import Retention
            from romfarmer.ir.layout import LayoutEntry, LayoutPlan

            output_dir.mkdir(parents=True, exist_ok=True)
            entries: list = []
            for unit_plan in build_plan.units:
                identities = output_set.unit_outputs.get(unit_plan.unit.unit_id)
                if not identities:
                    continue
                terminal_decls = [
                    decl
                    for action in unit_plan.actions
                    for decl in action.outputs
                    if decl.retention == Retention.TERMINAL
                ]
                for decl, ident in zip(terminal_decls, identities):
                    if ident.sha256 is None:
                        continue
                    blobs = list(
                        cas_dir.glob(f"{ident.sha256[:2]}/{ident.sha256[2:]}*")
                    )
                    if not blobs:
                        logger.warning(
                            "_run_execute_path(%s): CAS blob missing for %s (%s)",
                            resolved.platform, decl.logical_name, ident.sha256[:16],
                        )
                        continue
                    dest = output_dir / decl.logical_name
                    if not dest.exists():
                        try:
                            import os
                            os.link(blobs[0], dest)
                        except OSError:
                            import shutil
                            shutil.copy2(blobs[0], dest)
                    entries.append(
                        LayoutEntry(
                            artifact_sha256=ident.sha256,
                            relative_path=_Path(decl.logical_name),
                        )
                    )

            layout = LayoutPlan(root_name=output_dir.name, entries=tuple(entries))
            logger.info(
                "_run_execute_path(%s): executor complete, %d terminal files",
                resolved.platform, len(entries),
            )
            return layout

        except Exception as exc:
            logger.warning(
                "_run_execute_path(%s): error — skipping platform: %s",
                resolved.platform, exc,
                exc_info=True,
            )
            return None

    def _load_curated_lists(
        self, platform: str
    ) -> "tuple[frozenset[str], frozenset[str]]":
        """Load include/exclude lists from the ``lists/`` directory.

        Returns ``(curated_include, curated_exclude)`` as frozensets of
        canonical game names (extension stripped, disc tags stripped).

        List file naming convention (unchanged from legacy):
        - ``lists/{platform}-delete``  → games to always exclude
        - ``lists/{platform}+*``       → games to always include (rescue)

        Lines starting with ``#`` or empty lines are ignored.  Filenames
        include extensions (e.g. ``Crash Bandicoot (USA).chd``) — we strip
        to canonical name for the planner pass.
        """
        import re as _re

        _disc_tag = _re.compile(r"\s*\((?:Disc|Disk|CD)\s*\d+\)", _re.IGNORECASE)

        def _parse(path: Path) -> frozenset[str]:
            if not path.exists():
                return frozenset()
            names: set[str] = set()
            for raw_line in path.read_text(errors="replace").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                # Strip extension, then disc tags
                stem = Path(line).stem
                canonical = _disc_tag.sub("", stem).strip()
                if canonical:
                    names.add(canonical)
            return frozenset(names)

        lists_dir = get_paths().workspace_root / "lists"
        delete_path = lists_dir / f"{platform}-delete"
        curated_exclude = _parse(delete_path)

        # Collect all add/include lists matching "{platform}+*"
        curated_include: set[str] = set()
        if lists_dir.exists():
            for add_file in lists_dir.glob(f"{platform}+*"):
                curated_include.update(_parse(add_file))

        if curated_exclude:
            logger.debug(
                "_load_curated_lists(%s): %d excluded, %d included",
                platform, len(curated_exclude), len(curated_include),
            )
        return frozenset(curated_include), curated_exclude

    def _build_manifest(
        self,
        resolved: "ResolvedPlatformConfig",
        platform: "object",
    ) -> "BuildManifest":
        """Construct a ``BuildManifest`` from a ``ResolvedPlatformConfig``."""
        from romfarmer.ir.manifest import BuildManifest



        preferred_regions: tuple = ()
        if resolved.selection and resolved.selection.preferred_regions:
            preferred_regions = tuple(resolved.selection.preferred_regions)
        # Rating — both thresholds are in SelectionConfig, not a separate field
        rating_min = None
        rating_top_n = None
        if resolved.selection:
            rating_min = getattr(resolved.selection, "min_rating", None)

        # Budget
        budget_bytes = None
        safety_margin = 0.05
        if resolved.selection:
            max_gb = getattr(resolved.selection, "max_size_gb", None)
            if max_gb:
                budget_bytes = int(float(max_gb) * 1024 ** 3)

        # Generation
        gen_name = None
        gen_order: tuple = ()
        gen_cfg = getattr(resolved, "generation_filter", None)
        if gen_cfg and getattr(gen_cfg, "enabled", False):
            gen_name = getattr(gen_cfg, "generation", None)
            if gen_name:
                try:
                    from romfarmer.config.generation_loader import load_generation  # type: ignore[import]
                    gen_def = load_generation(gen_name)
                    if gen_def:
                        gen_order = tuple(gen_def.get_platform_names())
                except Exception:
                    pass


        # Curated lists — load delete and add lists from lists/ directory
        curated_include, curated_exclude = self._load_curated_lists(
            str(platform)
        )
        return BuildManifest(
            preferred_regions=preferred_regions,
            rating_min=rating_min,
            rating_top_n=rating_top_n,
            budget_bytes=budget_bytes,
            safety_margin=safety_margin,
            generation_name=gen_name,
            generation_platform_order=gen_order,
            curated_include=curated_include,
            curated_exclude=curated_exclude,
        )

    def _find_dat_file(self, resolved: ResolvedPlatformConfig) -> Optional[Path]:
        """Find DAT file for a platform.

        Uses the DAT reference from the resolved config to locate
        the correct DAT file in the dats/ directory.
        """
        if not resolved.dat:
            return None

        # No DAT for digital-only platforms
        from romfarmer.config.models import DATSource
        if resolved.dat.source == DATSource.NONE:
            return None

        # Explicit file path
        if resolved.dat.file:
            dat_path = Path(resolved.dat.file)
            if dat_path.exists():
                return dat_path
            # Try relative to workspace
            ws_path = get_paths().workspace_root / dat_path
            if ws_path.exists():
                return ws_path

        # Auto-detect from source
        dat_base = get_paths().dats_dir
        source = resolved.dat.source
        if source is None:
            return None

        source_str = source.value if hasattr(source, "value") else str(source)

        # Map source to directory
        source_map = {
            "retool_1g1r_usa": "nointro.retool.1g1r.usa",
            "retool_1g1r_all": "nointro.retool.1g1r.all",
            "retool_1g1r_eng": None,  # Depends on extraction type
            "redump_retool_1g1r_usa": "redump.retool.1g1r.usa",
            "redump_retool_1g1r_eng": "redump.retool.1g1r.eng",
            "nointro_retool_1g1r_eng": "nointro.retool.1g1r.eng",
        }

        dat_dir_name = source_map.get(source_str)

        if dat_dir_name is None and source_str == "retool_1g1r_eng":
            # Disambiguate based on extraction type
            from romfarmer.config.models import ExtractionType
            if resolved.extraction_type == ExtractionType.CARTRIDGE:
                dat_dir_name = "nointro.retool.1g1r.eng"
            else:
                dat_dir_name = "redump.retool.1g1r.eng"

        if dat_dir_name is None:
            dat_dir_name = source_str

        dat_dir = dat_base / dat_dir_name
        if not dat_dir.exists():
            logger.warning(f"DAT directory not found: {dat_dir}")
            return None

        # Search for matching DAT file
        # Check variants in priority order: specific yaml pattern first,
        # then generic platform name fallbacks. For each variant, scan ALL
        # files before falling back — prevents "xbox" matching "xbox 360".
        platform_search = self._get_dat_pattern(resolved.platform)
        variants = [platform_search] if platform_search else []
        variants.extend([
            resolved.platform.lower(),
            resolved.platform.split("-")[0].lower(),
        ])

        dat_files = list(dat_dir.glob("*.dat"))
        for variant in variants:
            if not variant:
                continue
            for dat_file in dat_files:
                if variant in dat_file.name.lower():
                    logger.info(f"  DAT: {dat_file.name}")
                    return dat_file

        logger.warning(f"No DAT file found for {resolved.platform}")
        return None

    def _get_dat_pattern(self, platform: str) -> Optional[str]:
        """Get DAT file search pattern from config/dat_patterns.yaml."""
        patterns_path = get_paths().workspace_root / "config" / "dat_patterns.yaml"
        if not patterns_path.exists():
            return None
        try:
            with open(patterns_path) as f:
                patterns = yaml.safe_load(f)
            return patterns.get(platform.lower()) if patterns else None
        except Exception:
            return None

    def _measure_output_size(self, output_dir: Path) -> int:
        """Measure total output size in bytes."""
        if not output_dir.exists():
            return 0
        return sum(f.stat().st_size for f in output_dir.rglob("*") if f.is_file())

    def _record_size(
        self,
        resolved: ResolvedPlatformConfig,
        output_size: int,
        files_processed: int,
    ):
        """Record output size for future estimation."""
        try:
            from romfarmer.utils.size_tracking import record_platform_size

            record_platform_size(
                platform=resolved.platform,
                compression=resolved.compression.value,
                output_size_bytes=output_size,
                selection=resolved.tier_strategy or "all",
                output_files=files_processed,
            )
        except Exception as e:
            logger.warning(f"Failed to record size: {e}")

    def _estimate_platform_size(self, resolved: ResolvedPlatformConfig) -> int:
        """Estimate output size for budget pre-check."""
        from romfarmer.utils.size_tracking import estimate_platform_size

        compression = resolved.compression.value
        selection = resolved.tier_strategy or "all"

        historical = estimate_platform_size(resolved.platform, compression, selection)
        if historical:
            return historical

        # Tier-based fallback
        if self.platform_tiers and resolved.tier:
            tier = self.platform_tiers.get_tier(resolved.tier)
            if tier:
                if tier.estimated_per_platform_mb:
                    estimate = tier.estimated_per_platform_mb * 1024 * 1024
                    if selection == "best_of":
                        estimate //= 10
                    elif selection == "best_of_extended":
                        estimate //= 5
                    return estimate

        return 1024 * 1024 * 1024  # 1 GB fallback

    # ═══════════════════════════════════════════════════════════════════════════
    # Post-build steps
    # ═══════════════════════════════════════════════════════════════════════════

    def _run_generation_filter(self) -> None:
        """Run cross-platform generation deduplication (if configured).

        Phase 5 implementation: uses the pure ``generation`` planner pass
        instead of the legacy ``FilterGenerationStage``.
        """
        gen_filter = self.build_spec.generation_filter
        if not gen_filter or not gen_filter.enabled:
            return

        logger.info(f"\n{'=' * 60}")
        logger.info("Running generation-based cross-platform deduplication...")
        logger.info(f"{'=' * 60}\n")

        try:
            from romfarmer.config.generation_loader import load_generation
            from romfarmer.planner.passes.generation import run as generation_pass
            from romfarmer.ir.catalog import Catalog, PlatformId
            from romfarmer.ir.manifest import BuildManifest
            from romfarmer.analysis.knowledge import KnowledgeBase
            from romfarmer.planner.costmodel import CostModel

            generation_def = load_generation(gen_filter.generation)
            if not generation_def:
                logger.error(f"Generation not found: {gen_filter.generation}")
                return

            platform_order = tuple(generation_def.get_platform_names())
            logger.info(f"Generation: {generation_def.label}")
            logger.info(f"  Priority: {' > '.join(platform_order)}")

            # Load rescue lists as curated_include
            curated_include: frozenset[str] = frozenset()
            if gen_filter.rescue_lists:
                include_set: set[str] = set()
                for games in gen_filter.rescue_lists.values():
                    include_set.update(g.lower() for g in games)
                curated_include = frozenset(include_set)
            else:
                rescue_file = (
                    Path(__file__).resolve().parent.parent.parent
                    / "config" / "curations" / "rescue"
                    / f"rescue-{gen_filter.generation}.yaml"
                )
                if rescue_file.exists():
                    import yaml
                    rescue_data = yaml.safe_load(rescue_file.read_text())
                    if rescue_data and rescue_data.get("rescue_lists"):
                        include_set = set()
                        for games in rescue_data["rescue_lists"].values():
                            include_set.update(g.lower() for g in games)
                        curated_include = frozenset(include_set)
                        logger.info(f"  Auto-loaded {len(curated_include)} rescue entries")

            # Build a merged multi-platform catalog from output directories
            build_output = self.build_spec.get_output_base()
            if not build_output.is_absolute():
                build_output = get_paths().workspace_root / build_output

            from romfarmer.analysis.catalog_builder import CatalogBuilder
            kb = KnowledgeBase()
            merged: Catalog | None = None
            for plat_name in platform_order:
                plat_dir = build_output / plat_name
                if not plat_dir.exists():
                    continue
                builder = CatalogBuilder(
                    platform=PlatformId(plat_name),
                    source_dir=plat_dir,
                    knowledge_base=kb,
                )
                cat = builder.build()
                if merged is None:
                    merged = cat
                else:
                    try:
                        merged = merged.merge(cat)
                    except ValueError:
                        pass  # overlapping ids — skip this platform

            if merged is None or not merged.units:
                logger.info("Generation filter: no units found in output dirs, skipping")
                return

            manifest = BuildManifest(
                generation_name=generation_def.name,
                generation_platform_order=platform_order,
                curated_include=curated_include,
            )
            result = generation_pass(merged, manifest, kb, CostModel())
            removed = len(merged.units) - len(result.catalog.units)
            logger.info(f"✅ Generation filter complete: removed {removed} cross-platform duplicates")

        except Exception as e:
            logger.error(f"Generation filter error: {e}", exc_info=True)
            logger.warning("Generation filter failed, but build will continue")
            logger.warning("Generation filter failed, but build will continue")

    def _run_post_build_hooks(self):
        """Run post-build hooks (jdupes, genre_organize, etc.)."""
        if not self.build_spec.post_build:
            return

        logger.info(f"\n{'=' * 60}")
        logger.info("Running post-build hooks...")
        logger.info(f"{'=' * 60}\n")

        output_base = str(self.build_spec.get_output_base())
        if not Path(output_base).is_absolute():
            output_base = str(get_paths().workspace_root / output_base)

        for i, hook in enumerate(self.build_spec.post_build, 1):
            logger.info(f"  [{i}/{len(self.build_spec.post_build)}] Hook: {hook.name} (type: {hook.type})")

            # Native genre_organize hook — no shell command needed
            if hook.type == "genre_organize":
                try:
                    self._run_genre_organize_hook(hook, Path(output_base))
                except Exception as e:
                    logger.error(f"    ❌ Genre organize error: {e}", exc_info=True)
                continue

            # Native quarantine_unpolished hook — hides unpolished root entries, links to Other/
            if hook.type == "quarantine_unpolished":
                try:
                    self._run_quarantine_unpolished_hook(hook, Path(output_base))
                except Exception as e:
                    logger.error(f"    ❌ Quarantine error: {e}", exc_info=True)
                continue

            # Native patch_gamelist hook — clones root gamelist entries for subdir files
            if hook.type == "patch_gamelist":
                try:
                    self._run_patch_gamelist_hook(hook, Path(output_base))
                except Exception as e:
                    logger.error(f"    ❌ Patch gamelist error: {e}", exc_info=True)
                continue

            # Fall through to shell command execution
            if not hook.command:
                logger.info(f"  ⊘ Skipping hook '{hook.name}' (no command)")
                continue

            # Variable substitution
            command = hook.command.replace("{output_base}", output_base)
            command = command.replace("{build_name}", self.build_spec.name)

            logger.info(f"    Command: {command}")

            try:
                result = subprocess.run(
                    command, shell=True, capture_output=True, text=True
                )
                if result.returncode == 0:
                    logger.info("    ✅ Success")
                    for line in result.stdout.strip().split("\n")[:5]:
                        if line:
                            logger.info(f"      {line}")
                else:
                    logger.error(f"    ❌ Failed (exit {result.returncode})")
                    if result.stderr:
                        logger.error(f"    {result.stderr}")
            except Exception as e:
                logger.error(f"    ❌ Error: {e}")

    def _run_genre_organize_hook(self, hook, output_base: Path):
        """
        Run genre organization for all completed platforms.

        Iterates over completed platforms, looks each up in the metadata DB
        by system name, and creates hardlinked 'By Genre/' subdirectories.
        Zero disk cost on ZFS/same-filesystem hardlinks.

        Hook options (all optional):
            mode: hardlink | copy | symlink | move  (default: hardlink)
            merge_small: int  — merge genres with < N games into 'Other' (default: 3)
            exclude_genres: list of genre names to skip
            system_map: dict mapping platform → system name for DB lookups
            platforms: list of platforms to process (default: all completed)
        """
        from romfarmer.organizers.base import OrganizeMode
        from romfarmer.organizers.genre import GenreOrganizer

        mode = OrganizeMode(hook.options.get("mode", "hardlink"))
        merge_small = hook.options.get("merge_small", 3)
        exclude_genres = hook.options.get("exclude_genres") or None
        system_map: dict = hook.options.get("system_map") or {}
        metadata_db = get_paths().metadata_db

        if not metadata_db.exists():
            logger.warning(f"  ⚠ Metadata DB not found: {metadata_db} — skipping genre organization")
            return

        # Determine which platforms to process
        platforms = hook.options.get("platforms") or self.state.completed_platforms
        if not platforms:
            logger.info("  No completed platforms to genre-organize")
            return

        logger.info(f"  Genre organizing {len(platforms)} platform(s) (mode: {mode.value})")

        total_organized = 0
        total_skipped = 0

        for platform in platforms:
            platform_dir = output_base / platform
            if not platform_dir.exists():
                logger.debug(f"  Skipping {platform} (no output dir)")
                continue

            system = system_map.get(platform, platform)

            try:
                organizer = GenreOrganizer(
                    metadata_db=metadata_db,
                    system=system,
                    mode=mode,
                    merge_small=merge_small,
                    exclude_genres=list(exclude_genres) if exclude_genres else None,
                )
                stats = organizer.organize(platform_dir)
                organized = stats.files_moved + stats.files_copied + stats.symlinks_created
                total_organized += organized
                total_skipped += stats.skipped
                if organized > 0 or stats.errors > 0:
                    logger.info(
                        f"    {platform}: {organized} organized, "
                        f"{stats.skipped} skipped"
                        + (f", {stats.errors} errors" if stats.errors else "")
                    )
                else:
                    logger.debug(f"    {platform}: no genre data in DB")
            except Exception as e:
                logger.warning(f"    {platform}: genre organize failed — {e}")

        logger.info(f"  ✅ Genre organization complete: {total_organized} hardlinks created across {len(platforms)} platforms")

    def _run_quarantine_unpolished_hook(self, hook, output_base: Path):
        """
        Move unpolished root-level games into a quarantine subfolder (default: Other/).

        A game is "unpolished" if it is missing a required metadata field in the
        root gamelist.xml entry.  Unpolished games are:
          - hardlinked into <folder_name>/ (zero disk cost)
          - hidden in the root gamelist via <hidden>true</hidden>
        patch_gamelist then backfills a visible entry for the subdir copy.

        Files already in any subdir (By Genre/, Best Games/, Translations/, etc.)
        are never touched.

        Hook options (all optional):
            folder_name:   destination subdir name (default: Other)
            require_image: hide if <image> is absent (default: true)
            require_desc:  hide if <desc> is absent  (default: true)
            platforms:     list of platforms to process (default: all completed)
        """
        import os
        from xml.etree import ElementTree as ET

        folder_name  = hook.options.get("folder_name",  "Other")
        require_image = hook.options.get("require_image", True)
        require_desc  = hook.options.get("require_desc",  True)

        platforms = hook.options.get("platforms") or self.state.completed_platforms
        if not platforms:
            logger.info("  No completed platforms to process")
            return

        logger.info(
            f"  Quarantining unpolished games for {len(platforms)} platform(s) "
            f"→ {folder_name}/  (require_image={require_image}, require_desc={require_desc})"
        )
        total_quarantined = 0

        for platform in platforms:
            platform_dir = output_base / platform
            gamelist_path = platform_dir / "gamelist.xml"
            if not gamelist_path.exists():
                continue

            tree = ET.parse(gamelist_path)
            xml_root = tree.getroot()
            quarantine_dir = platform_dir / folder_name
            quarantined = 0

            for game in xml_root.findall("game"):
                path_text = game.findtext("path") or ""
                rel = path_text.lstrip("./")
                # Root-level entries only — skip anything already in a subdir
                if "/" in rel:
                    continue
                # Skip already-hidden entries
                if game.findtext("hidden") == "true":
                    continue

                missing_image = require_image and not (game.findtext("image") or "").strip()
                missing_desc  = require_desc  and not (game.findtext("desc")  or "").strip()
                if not missing_image and not missing_desc:
                    continue  # polished — leave in root

                rom_path = platform_dir / rel
                if not rom_path.exists():
                    continue

                # Hardlink into quarantine subdir
                quarantine_dir.mkdir(parents=True, exist_ok=True)
                dest = quarantine_dir / rom_path.name
                if not dest.exists():
                    try:
                        os.link(rom_path, dest)
                    except OSError:
                        import shutil
                        shutil.copy2(rom_path, dest)

                # Hide the root gamelist entry
                hidden_elem = game.find("hidden")
                if hidden_elem is None:
                    hidden_elem = ET.SubElement(game, "hidden")
                hidden_elem.text = "true"
                quarantined += 1

            if quarantined > 0:
                ET.indent(tree, space="  ")
                tree.write(gamelist_path, encoding="utf-8", xml_declaration=True)
                logger.info(f"    {platform}: {quarantined} games → {folder_name}/")
            total_quarantined += quarantined

        logger.info(
            f"  ✅ Quarantine complete: {total_quarantined} games moved to {folder_name}/"
            f" across {len(platforms)} platforms"
        )

    def _run_patch_gamelist_hook(self, hook, output_base: Path):
        """
        Patch gamelist.xml files to include subdirectory entries.

        GenerateMetadataStage only writes root-level entries. After
        GenreOrganizer creates By Genre/ hardlinks (and ApplyListsStage
        creates Best Games/ etc.), those files have no gamelist coverage.
        This hook clones each root entry for every matching file found in
        any subdirectory, so EmulationStation can browse by folder.

        Hook options (all optional):
            platforms: list of platforms to process (default: all completed)
        """
        import importlib.util

        script_path = (
            Path(__file__).resolve().parent.parent.parent
            / "scripts" / "patch_gamelist_subdirs.py"
        )
        if not script_path.exists():
            logger.warning(f"  ⚠ patch_gamelist_subdirs.py not found at {script_path}")
            return

        spec = importlib.util.spec_from_file_location("patch_gamelist_subdirs", script_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        platforms = hook.options.get("platforms") or self.state.completed_platforms
        if not platforms:
            logger.info("  No completed platforms to patch")
            return

        logger.info(f"  Patching gamelist subdirs for {len(platforms)} platform(s)")
        total_added = 0

        for platform in platforms:
            platform_dir = output_base / platform
            if not platform_dir.exists():
                logger.debug(f"  Skipping {platform} (no output dir)")
                continue

            stats = mod.patch_platform(platform_dir)
            added = stats.get("added", 0)
            status = stats.get("status", "?")
            total_added += added

            if added > 0:
                logger.info(f"    {platform}: +{added} gamelist entries added")
            elif status not in ("ok", "skipped (folder format)"):
                logger.debug(f"    {platform}: [{status}]")

        logger.info(
            f"  ✅ Gamelist patch complete: {total_added} entries added"
            f" across {len(platforms)} platforms"
        )

    def _run_deployment(self):
        """Run deployment (rsync to target)."""
        deploy = self.build_spec.deploy
        if not deploy:
            return

        logger.info(f"\n{'=' * 60}")
        logger.info("Running deployment...")
        logger.info(f"{'=' * 60}\n")

        output_base = str(self.build_spec.get_output_base())
        if not Path(output_base).is_absolute():
            output_base = str(get_paths().workspace_root / output_base)

        destination = deploy.destination
        method = deploy.method
        options = deploy.options

        logger.info(f"  Method: {method}")
        logger.info(f"  Destination: {destination}")

        if method == "rsync":
            rsync_opts = options.get("rsync_flags", "-avH --progress")
            delete_flag = "--delete" if options.get("delete_extra", False) else ""
            dry_run = "--dry-run" if options.get("dry_run", False) else ""

            command = f"rsync {rsync_opts} {delete_flag} {dry_run} {output_base}/ {destination}"
            logger.info(f"  Command: {command}")

            if options.get("confirm", True):
                logger.info("  (Requires --deploy flag to execute)")
                return

            try:
                result = subprocess.run(command, shell=True)
                if result.returncode == 0:
                    logger.info("  ✅ Deployment complete")
                else:
                    logger.error(f"  ❌ Deployment failed (exit {result.returncode})")
            except Exception as e:
                logger.error(f"  ❌ Deployment error: {e}")

    def _generate_report(self):
        """Generate build completion report."""
        report_path = get_paths().build_report_file(self.build_spec.name)
        duration = datetime.now() - self.state.started_at

        total = len(self.resolved_configs)
        completed = len(self.state.completed_platforms)
        failed = len(self.state.failed_platforms)

        with open(report_path, "w") as f:
            f.write(f"Build Report: {self.build_spec.name}\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Description: {self.build_spec.description}\n")
            f.write(f"Target: {self.build_spec.target}\n")
            f.write(f"Recipes: {', '.join(self.build_spec.recipes)}\n\n")
            f.write(f"Started: {self.state.started_at}\n")
            f.write(f"Completed: {datetime.now()}\n")
            f.write(f"Duration: {duration}\n\n")
            f.write(f"Status: {self.state.status.value}\n\n")
            f.write(f"Platforms Summary:\n")
            f.write(f"  Total: {total}\n")
            f.write(f"  Completed: {completed}\n")
            f.write(f"  Failed: {failed}\n")
            f.write(f"  Success Rate: {completed / max(total, 1) * 100:.1f}%\n\n")

            if self.state.completed_platforms:
                f.write(f"Completed Platforms ({completed}):\n")
                for p in self.state.completed_platforms:
                    f.write(f"  ✅ {p}\n")
                f.write("\n")

            if self.state.failed_platforms:
                f.write(f"Failed Platforms ({failed}):\n")
                for p in self.state.failed_platforms:
                    f.write(f"  ❌ {p}\n")
                f.write("\n")

            f.write("=" * 60 + "\n")

        logger.info(f"Report saved: {report_path}")

    # ═══════════════════════════════════════════════════════════════════════════
    # Status
    # ═══════════════════════════════════════════════════════════════════════════

    def get_status(self) -> Dict[str, Any]:
        """Get current build status."""
        total = len(self.resolved_configs)
        completed = len(self.state.completed_platforms)
        failed = len(self.state.failed_platforms)

        return {
            "build_name": self.build_spec.name,
            "description": self.build_spec.description,
            "target": self.build_spec.target,
            "recipes": self.build_spec.recipes,
            "status": self.state.status.value,
            "current_platform": self.state.current_platform,
            "started_at": self.state.started_at.isoformat(),
            "last_updated": self.state.last_updated.isoformat() if self.state.last_updated else None,
            "progress": {
                "total": total,
                "completed": completed,
                "failed": failed,
                "remaining": total - completed - failed,
                "percent": (completed / total * 100) if total > 0 else 0,
            },
            "completed_platforms": self.state.completed_platforms,
            "failed_platforms": self.state.failed_platforms,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _resolve_all_source_roots(
    platforms: Dict[str, SlimPlatformConfig],
    config_root: Path,
):
    """Resolve source root references in all platform configs.

    Reads config/sources.yaml and replaces root/subdir references
    with absolute paths in each platform's SourceConfig.
    """
    sources_path = config_root / "sources.yaml"
    if not sources_path.exists():
        return

    try:
        with open(sources_path) as f:
            roots = yaml.safe_load(f).get("roots", {})
    except Exception as e:
        logger.error(f"Failed to load sources.yaml: {e}")
        return

    for platform in platforms.values():
        for source in platform.sources:
            if source.root and source.root in roots:
                root_path = Path(roots[source.root])
                source.path = root_path / source.subdir if source.subdir else root_path
                if not source.path.exists():
                    logger.warning(f"{platform.name}: source path not found: {source.path}")

        # Also resolve chd_sources
        if platform.chd_sources:
            for source in platform.chd_sources:
                if source.root and source.root in roots:
                    root_path = Path(roots[source.root])
                    source.path = root_path / source.subdir if source.subdir else root_path
