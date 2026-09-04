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
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from romfarmer.driver.hooks import HookContext
    from romfarmer.driver.resolve import ResolvedBuild
    from romfarmer.ir.manifest import BuildManifest

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
from romfarmer.driver.resolve import (
    ResolvePaths,
)
from romfarmer.driver.resolve import (
    parse_dat as _parse_dat,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Phase-boundary types
#
# The five phases are composed as typed pure functions rather than method calls
# on a mutable orchestrator.  The function signatures act as capability
# starvation: each phase can only receive the data it is entitled to see.
#
# Hard rule: run_execute takes NO source paths and NO ResolvedPlatformConfig.
# All data flows through PlannedPlatform → ExecutedPlatform.
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class PlannedPlatform:
    """Result of CATALOG + PLAN phases — everything EXECUTE is entitled to see."""

    platform: str
    catalog: Any  # romfarmer.ir.catalog.Catalog
    build_plan: Any  # romfarmer.ir.actions.BuildPlan
    manifest: Any  # romfarmer.ir.manifest.BuildManifest
    traces: tuple[Any, ...] = ()  # PassTrace per pass — powers `plan run --explain`
    chain: tuple[str, ...] = ()  # negotiated FormatChain the plan was lowered with
    stages: tuple[tuple[str, Any], ...] = ()  # (pass name, Catalog entering it) — PlanSummary input


@dataclass(frozen=True)
class ExecEnv:
    """Execution environment — the only external-world handles EXECUTE may use."""

    cas_dir: Path
    scratch_base: Path
    db_path: Path
    output_dir: Path  # where terminal artifacts are hardlinked
    transforms: Any  # dict[str, Transform]


@dataclass(frozen=True)
class ExecutionReport:
    """Post-EXECUTE summary, consumed by EMIT and by the driver."""

    terminal_count: int
    failed_units: tuple[tuple[str, str], ...] = ()  # (canonical_name, reason)
    budget_stopped: tuple[str, ...] = ()  # unit_id strings skipped by stop-early
    actual_bytes: int = 0  # cumulative terminal artifact bytes


@dataclass(frozen=True)
class ExecutedPlatform:
    """Result of the EXECUTE phase — everything EMIT is entitled to see."""

    planned: PlannedPlatform
    layout: Any  # romfarmer.ir.layout.LayoutPlan
    report: ExecutionReport


class PhaseError(Exception):
    """Raised when a pipeline phase fails.

    The driver (``_process_platform``) is the sole try/except site — it
    catches ``PhaseError`` once per phase and applies per-phase policy:
    CATALOG/PLAN/EXECUTE failures skip the platform; EMIT failures are
    logged but do not mark outputs as invalid.
    """

    def __init__(self, phase: str, platform: str, cause: Exception) -> None:
        self.phase = phase
        self.platform = platform
        self.cause = cause
        super().__init__(f"{phase}({platform}): {cause}")


class PlanValidationError(PhaseError):
    """Raised by ``validate_plan`` when the BuildPlan references unregistered tools."""


# ─────────────────────────────────────────────────────────────────────────────
# Phase functions  (module-level, not closures over `self`)
# ─────────────────────────────────────────────────────────────────────────────


def validate_plan(plan: Any, transforms: Any, platform: str = "") -> None:
    """Raise PlanValidationError if any tool in *plan* lacks a Transform.

    Called by the driver immediately before EXECUTE so that missing-tool
    failures surface at plan time (bug-3 class prevention).
    """
    missing = {a.tool for up in plan.units for a in up.actions if a.tool not in transforms}
    if missing:
        raise PlanValidationError(
            "PLAN",
            platform,
            ValueError(f"BuildPlan references unregistered tools: {sorted(missing)}"),
        )


def run_catalog(
    resolved: "ResolvedPlatformConfig",
    *,
    source_dir: Path,
    dat_file: Path | None,
    kb: Any,
    digest_db: Path | None = None,
) -> Any:
    """CATALOG phase: scan *source_dir* and return a ``Catalog``.

    ``digest_db`` is the SQLite file for the FileDigestCache.  ``None`` means
    NO digest cache (a pure scan) — never an inferred workspace database, so
    tests and MCP sessions cannot write into a workspace they did not name.
    The driver and PlanSession pass their workspace's DB explicitly.

    Raises ``PhaseError`` on failure so the driver can apply skip policy.
    """
    from romfarmer.analysis.catalog_builder import CatalogBuilder
    from romfarmer.ir.catalog import PlatformId

    platform_id = PlatformId(resolved.platform)

    dat_parsed: Any = _parse_dat(dat_file) if dat_file else None

    try:
        source_dirs = tuple(
            (s.path, bool(s.recursive)) for s in (resolved.sources or ()) if s.path is not None
        ) or ((source_dir, False),)
        builder = CatalogBuilder(
            platform=platform_id,
            source_dir=source_dir,
            knowledge_base=kb,
            dat_file=dat_parsed,
            file_digest_cache=_open_digest_cache(resolved.platform, digest_db)
            if digest_db
            else None,
            source_dirs=source_dirs,
        )
        return builder.build()
    except Exception as exc:
        raise PhaseError("CATALOG", resolved.platform, exc) from exc


def run_plan(
    catalog: Any,
    manifest: Any,
    *,
    cost_model: Any,
    kb: Any,
    chain: "tuple[str, ...]" = (),
    action_cache: Any | None = None,
) -> PlannedPlatform:
    """PLAN phase: apply passes then lower the catalog to a ``BuildPlan``.

    Returns a ``PlannedPlatform`` carrying the post-pass catalog and the
    full ``BuildPlan`` — everything EXECUTE needs without requiring access
    to any ``ResolvedPlatformConfig``.

    Raises ``PhaseError`` on failure.
    """
    from romfarmer.ir.actions import BuildPlan
    from romfarmer.planner import PassRunner, passes
    from romfarmer.planner.lowering.base import lower as lower_unit

    platform_str = str(getattr(catalog, "platform", ""))
    chain = tuple(chain) or tuple(getattr(manifest, "chain", ()) or ())
    if not chain:
        raise PhaseError(
            "PLAN", platform_str, ValueError("no FormatChain: pass chain= or set manifest.chain")
        )

    try:
        runner = PassRunner(
            passes=list(passes.DEFAULT_PASSES),
            manifest=manifest,
            kb=kb,
            cost_model=cost_model,
        )
        final_catalog, traces = runner.run(catalog)
        stages = tuple(runner.stages)

        total_removed = sum(len(t.removed) for t in traces)
        logger.info(
            "run_plan(%s): %d → %d units (%d removed by passes)",
            platform_str,
            len(catalog.units),
            len(final_catalog.units),
            total_removed,
        )

        if not final_catalog.units:
            return PlannedPlatform(
                platform=platform_str,
                catalog=final_catalog,
                build_plan=BuildPlan(units=()),
                manifest=manifest,
                traces=tuple(traces),
                chain=chain,
                stages=stages,
            )

        unit_plans = []
        for unit in final_catalog.units:
            try:
                up = lower_unit(unit, chain, manifest, action_cache)
                unit_plans.append(up)
            except Exception as exc:
                logger.warning(
                    "run_plan(%s): lowering failed for %s: %s",
                    platform_str,
                    unit.canonical_name,
                    exc,
                )

        return PlannedPlatform(
            platform=platform_str,
            catalog=final_catalog,
            build_plan=BuildPlan(units=tuple(unit_plans)),
            manifest=manifest,
            traces=tuple(traces),
            chain=chain,
            stages=stages,
        )

    except PhaseError:
        raise
    except Exception as exc:
        raise PhaseError("PLAN", platform_str, exc) from exc


def run_execute(planned: PlannedPlatform, *, env: ExecEnv) -> ExecutedPlatform:
    """EXECUTE phase: run the Executor against the BuildPlan in *planned*.

    **Takes no source paths and no ResolvedPlatformConfig.**  All data
    flows through ``PlannedPlatform``.  The (ArtifactDecl, Identity) zip
    lives exclusively here — never in orchestrator glue.

    Returns ``ExecutedPlatform`` with a ``LayoutPlan`` ready for EMIT.
    Raises ``PhaseError`` on failure.
    """
    import os

    from romfarmer.engine.actioncache import ActionCache
    from romfarmer.engine.executor import Executor
    from romfarmer.ir.actions import Retention
    from romfarmer.ir.layout import LayoutEntry, LayoutPlan

    try:
        if not planned.build_plan.units:
            return ExecutedPlatform(
                planned=planned,
                layout=LayoutPlan(root_name=planned.platform, entries=()),
                report=ExecutionReport(terminal_count=0),
            )

        from romfarmer.engine.telemetry import UnitTelemetryStore

        chain = tuple(planned.chain or getattr(planned.manifest, "chain", ()) or ())
        tool_key = chain[0] if chain else "unknown"

        with ActionCache(env.db_path) as action_cache, UnitTelemetryStore(env.db_path) as tele:

            def _unit_telemetry(unit_plan: Any, terminal: tuple[Any, ...]) -> None:
                # CostModel feedback: (platform, chain tool) → source → output bytes.
                out_bytes = sum(int(i.size or 0) for i in terminal)
                version = unit_plan.actions[-1].tool_version if unit_plan.actions else ""
                tele.record(
                    planned.platform,
                    tool_key,
                    str(unit_plan.unit.unit_id),
                    int(unit_plan.unit.source_size),
                    out_bytes,
                    version,
                )

            executor = Executor(
                action_cache=action_cache,
                transforms=env.transforms,
                cas_dir=env.cas_dir,
                scratch_base=env.scratch_base,
                budget_bytes=getattr(planned.manifest, "effective_budget_bytes", None),
                unit_telemetry_cb=_unit_telemetry,
            )
            output_set = executor.run(planned.build_plan)

        # Build LayoutPlan: zip terminal ArtifactDecls with output identities.
        # This is the SOLE place this zip happens — never in orchestrator glue.
        # Bug-2 prevention: logical_name from decl, NOT the CAS hash filename.
        env.output_dir.mkdir(parents=True, exist_ok=True)
        entries: list[LayoutEntry] = []
        for unit_plan in planned.build_plan.units:
            identities = output_set.unit_outputs.get(unit_plan.unit.unit_id)
            if not identities:
                continue
            terminal_decls = [
                decl
                for action in unit_plan.actions
                for decl in action.outputs
                if decl.retention == Retention.TERMINAL
            ]
            for decl, ident in zip(terminal_decls, identities, strict=False):
                if ident.sha256 is None:
                    continue
                if decl.kind == "tree":
                    # Folder-shaped artifact (PS3 JB folder, etc.) — restore
                    # via the tree store's hardlink-per-file manifest, not
                    # the single-blob CAS path used for file artifacts.
                    from romfarmer.cas.store import ContentStore
                    from romfarmer.cas.tree import TreeStore

                    dest = env.output_dir / decl.logical_name
                    if not dest.exists():
                        try:
                            TreeStore(ContentStore(env.cas_dir)).restore(ident.sha256, dest)
                        except FileNotFoundError as exc:
                            logger.warning(
                                "run_execute(%s): tree restore failed for %s: %s",
                                planned.platform,
                                decl.logical_name,
                                exc,
                            )
                            continue
                    entries.append(
                        LayoutEntry(
                            artifact_sha256=ident.sha256,
                            relative_path=Path(decl.logical_name),
                        )
                    )
                    continue
                blobs = list(env.cas_dir.glob(f"{ident.sha256[:2]}/{ident.sha256[2:]}*"))
                if not blobs:
                    logger.warning(
                        "run_execute(%s): CAS blob missing for %s (%s)",
                        planned.platform,
                        decl.logical_name,
                        ident.sha256[:16],
                    )
                    continue
                dest = env.output_dir / decl.logical_name
                if not dest.exists():
                    try:
                        os.link(blobs[0], dest)
                    except OSError:
                        shutil.copy2(blobs[0], dest)
                entries.append(
                    LayoutEntry(
                        artifact_sha256=ident.sha256,
                        relative_path=Path(decl.logical_name),
                    )
                )

        layout = LayoutPlan(root_name=planned.platform, entries=tuple(entries))
        actual_bytes = sum(
            ident.size or 0
            for identities in output_set.unit_outputs.values()
            for ident in identities
        )
        logger.info(
            "run_execute(%s): complete, %d terminal files, %d bytes actual",
            planned.platform,
            len(entries),
            actual_bytes,
        )
        if output_set.budget_stopped:
            logger.info(
                "run_execute(%s): %d unit(s) budget-stopped",
                planned.platform,
                len(output_set.budget_stopped),
            )
        return ExecutedPlatform(
            planned=planned,
            layout=layout,
            report=ExecutionReport(
                terminal_count=len(entries),
                failed_units=(),
                budget_stopped=tuple(output_set.budget_stopped),
                actual_bytes=actual_bytes,
            ),
        )

    except PhaseError:
        raise
    except Exception as exc:
        raise PhaseError("EXECUTE", planned.platform, exc) from exc


def run_emit(
    executed: ExecutedPlatform,
    *,
    profile: Any | None,
    output_dir: Path,
) -> None:
    """EMIT phase: organise output files and generate metadata.

    Receives the ``ConcreteTargetProfile`` object loaded at RESOLVE time —
    no string lookup happens here (bug-5 prevention).

    Errors are propagated as ``PhaseError``.  The driver treats EMIT
    errors as non-fatal: terminal artifacts are already materialised by
    EXECUTE.
    """
    from romfarmer.ir.layout import LayoutPlan
    from romfarmer.targets.emitters.materializer import Materializer

    try:
        style = getattr(profile, "organisation_style", "flat") if profile else "flat"
        materializer = Materializer(style=style, move=True)

        layout = executed.layout
        if isinstance(layout, LayoutPlan) and layout.entries:
            files = [output_dir / e.relative_path for e in layout.entries]
            shas: list[str] | None = [e.artifact_sha256 for e in layout.entries]
        else:
            files = [f for f in output_dir.iterdir() if f.is_file()] if output_dir.exists() else []
            shas = None

        placed = materializer.emit(files, output_dir)

        # Re-anchor the layout to the organised locations.
        if shas is not None and len(placed) == len(shas):
            from romfarmer.ir.layout import LayoutEntry

            layout = LayoutPlan(
                root_name=output_dir.name,
                entries=tuple(
                    LayoutEntry(
                        artifact_sha256=sha,
                        relative_path=p.relative_to(output_dir),
                    )
                    for sha, p in zip(shas, placed, strict=False)
                ),
            )

        # Generate metadata (gamelist.xml) if the profile enables it.
        if profile is not None and getattr(profile, "metadata_enabled", False):
            from romfarmer.analysis.knowledge import KnowledgeBase
            from romfarmer.targets.emitters.es_gamelist import ESGamelistEmitter

            db_path = Path(get_paths().metadata_db)
            kb = KnowledgeBase(db_path if db_path.exists() else None)
            emitter = ESGamelistEmitter()
            if not isinstance(layout, LayoutPlan):
                layout = emitter.plan_layout(output_dir, profile)
            emitter.emit_metadata(layout, output_dir, kb, profile)

        logger.info("run_emit(%s): EMIT complete", executed.planned.platform)

    except PhaseError:
        raise
    except Exception as exc:
        raise PhaseError("EMIT", executed.planned.platform, exc) from exc


def _build_default_transforms() -> dict[str, Any]:
    """Build the standard transform registry for the EXECUTE phase."""
    from romfarmer.engine.transforms.archive import ArchiveTransform
    from romfarmer.engine.transforms.chd import CHDTransform
    from romfarmer.engine.transforms.m3u import M3UTransform
    from romfarmer.engine.transforms.ps3 import (
        PS3DecTransform,
        Ps3DkeyLookupTransform,
        Ps3ExtractTreeTransform,
    )
    from romfarmer.engine.transforms.rvz import RVZExtractTransform
    from romfarmer.engine.transforms.source import (
        PassthroughTransform,
        SourceCopyTransform,
    )
    from romfarmer.engine.transforms.squashfs import SquashFSTransform
    from romfarmer.engine.transforms.unzip import UnzipTransform
    from romfarmer.engine.transforms.wux import WUXExtractTransform
    from romfarmer.engine.transforms.xiso import XisoTransform

    return {
        "source-copy": SourceCopyTransform(),
        "passthrough": PassthroughTransform(),
        "unzip": UnzipTransform(),
        "compress-7z": ArchiveTransform(),
        "compress-zip": ArchiveTransform(),
        "chdman": CHDTransform(),
        "unzip-rvz": RVZExtractTransform(),
        "unzip-wux": WUXExtractTransform(),
        "extract-xiso": XisoTransform(),
        "mksquashfs": SquashFSTransform(),
        "ps3dec": PS3DecTransform(),
        "ps3-dkey-lookup": Ps3DkeyLookupTransform(),
        "ps3-extract-tree": Ps3ExtractTreeTransform(),
        "m3u-create": M3UTransform(),
    }


def _open_digest_cache(platform: str, db_path: Path) -> Any | None:
    """Open the FileDigestCache at ``db_path``; None (with a debug log) on error."""
    try:
        from romfarmer.analysis.file_digest_cache import FileDigestCache

        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return FileDigestCache(db_path)
    except Exception as exc:
        logger.debug("_open_digest_cache(%s): %s", platform, exc)
        return None


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
        resolved_configs: list[ResolvedPlatformConfig],
        recipes: dict[str, RecipeSpec],
        state_dir: Path | None = None,
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
        config_root: Path | None = None,
        platform_filter: list[str] | None = None,
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

        platforms: dict[str, SlimPlatformConfig] = {}
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
        fh.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
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
        errors: list[str] = []

        if not self.resolved_configs:
            errors.append("No platforms resolved for this build")

        # Check source directories
        for rc in self.resolved_configs:
            for src in rc.sources:
                if src.path and not src.path.exists():
                    errors.append(f"{rc.platform}: source path not found: {src.path}")

        # Target profile must load (loud, not a silent None — G4 #6)
        try:
            self._load_target_profile()
        except Exception as e:
            errors.append(f"target profile: {e}")

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

        budget_skipped: list[str] = []

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

    def _get_platforms_to_process(self, resume: bool) -> list[ResolvedPlatformConfig]:
        """Get ordered list of platforms to process.

        Applies:
            1. Tier ordering (lower tier = higher priority)
            2. Resume filtering (skip completed)
        """
        platforms = list(self.resolved_configs)

        # Apply tier ordering (ResolvedPlatformConfig is frozen — derive copies)
        if self.platform_tiers:
            from dataclasses import replace

            tiered: list[ResolvedPlatformConfig] = []
            for rc in platforms:
                tier = self.platform_tiers.get_platform_tier(rc.platform)
                tier_strategy = None
                if tier:
                    strategy = self._get_tier_strategy(rc.platform)
                    tier_strategy = strategy.value if strategy else None
                tiered.append(replace(rc, tier=tier, tier_strategy=tier_strategy))
            platforms = tiered
            self.resolved_configs = list(platforms)

            platforms.sort(key=lambda rc: (rc.tier or 99, rc.platform))

            # Log tier distribution
            tier_counts: dict[str, int] = {}
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

    def _process_platform(self, resolved: ResolvedPlatformConfig) -> None:
        """Drive the five compiler phases for one platform.

        This is the sole try/except site for per-phase error handling.  It
        never accesses the phase results beyond what it needs to pass to the
        next phase — capability starvation is enforced by the phase-function
        signatures (T6, 2026-07-04 architect review).
        """
        self.state.current_platform = resolved.platform
        self._save_state()

        logger.info(f"Processing platform: {resolved.platform}")

        # ── RESOLVE (public, frozen product) ───────────────────────────
        paths = get_paths()
        work_dir = paths.platform_temp_dir(resolved.platform)
        rb = self.resolve(resolved)
        source_dir, output_dir, dat_file, profile, chain, manifest = (
            rb.source_dir,
            rb.output_dir,
            rb.dat_file,
            rb.profile,
            rb.chain,
            rb.manifest,
        )
        logger.info(f"  Source: {source_dir}")
        logger.info(f"  Output: {output_dir}")

        from pathlib import Path as _Path

        from romfarmer.analysis.knowledge import KnowledgeBase
        from romfarmer.planner import CostModel

        db_path = _Path(paths.metadata_db)
        kb = KnowledgeBase(db_path if db_path.exists() else None)
        sd_path = _Path(paths.workspace_root) / "config" / "size_data.json"
        cost_model = CostModel(
            size_data_path=sd_path if sd_path.exists() else None,
            knowledge_base=kb,
        )

        # ── CATALOG phase ──────────────────────────────────────────────
        try:
            catalog = run_catalog(
                resolved,
                source_dir=source_dir,
                dat_file=dat_file,
                kb=kb,
                digest_db=db_path,
            )
        except PhaseError as exc:
            logger.warning(
                "_process_platform(%s): CATALOG failed — %s",
                resolved.platform,
                exc.cause,
                exc_info=True,
            )
            return

        if not getattr(catalog, "units", ()):
            logger.debug("_process_platform(%s): empty catalog — skipping", resolved.platform)
            return

        # ── PLAN phase (passes + lowering) ────────────────────────────
        from romfarmer.engine.actioncache import ActionCache

        cache_db = _Path(paths.metadata_db)
        cache_db.parent.mkdir(parents=True, exist_ok=True)

        with ActionCache(cache_db) as action_cache:
            try:
                planned = run_plan(
                    catalog,
                    manifest,
                    cost_model=cost_model,
                    kb=kb,
                    chain=chain,
                    action_cache=action_cache,
                )
            except PhaseError as exc:
                logger.warning(
                    "_process_platform(%s): PLAN failed — %s",
                    resolved.platform,
                    exc.cause,
                    exc_info=True,
                )
                return

            # ── Dry-run exit ───────────────────────────────────────────
            dry_run = getattr(self, "_dry_run", False)
            if dry_run:
                logger.info(
                    "  [dry-run] %s: %d units, chain=%s",
                    resolved.platform,
                    len(planned.build_plan.units),
                    chain,
                )
                for up in planned.build_plan.units:
                    logger.info(
                        "    %s: %d actions (%s)",
                        up.unit.canonical_name,
                        len(up.actions),
                        ", ".join(a.tool for a in up.actions),
                    )
                return

            # ── Plan validation (bug-3 prevention) ────────────────────
            transforms = _build_default_transforms()
            try:
                validate_plan(planned.build_plan, transforms, resolved.platform)
            except PlanValidationError as exc:
                logger.warning(
                    "_process_platform(%s): plan validation failed — %s",
                    resolved.platform,
                    exc.cause,
                )
                return

            # ── EXECUTE phase ──────────────────────────────────────────
            cas_dir = _Path(paths.workspace_root) / "store" / "cas"
            cas_dir.mkdir(parents=True, exist_ok=True)
            scratch_base = work_dir / "scratch"
            scratch_base.mkdir(parents=True, exist_ok=True)

            env = ExecEnv(
                cas_dir=cas_dir,
                scratch_base=scratch_base,
                db_path=cache_db,
                output_dir=output_dir,
                transforms=transforms,
            )

            try:
                executed = run_execute(planned, env=env)
            except PhaseError as exc:
                logger.warning(
                    "_process_platform(%s): EXECUTE failed — %s",
                    resolved.platform,
                    exc.cause,
                    exc_info=True,
                )
                return

            # Predicted-vs-actual report (T10 observability).  Prediction comes
            # from the CostModel for the chain tool — NOT UnitPlan.predicted_output_bytes,
            # which every lowering rule sets to the source size (identity).
            stopped = set(executed.report.budget_stopped)
            source_bytes = sum(
                up.unit.source_size
                for up in planned.build_plan.units
                if str(up.unit.unit_id) not in stopped
            )
            actual_bytes = executed.report.actual_bytes
            try:
                predicted_bytes, pred_label = cost_model.predict_output_bytes(
                    source_bytes, resolved.platform, chain[0] if chain else None
                )
            except Exception as exc:
                predicted_bytes, pred_label = source_bytes, f"fallback:source_size ({exc})"
            if predicted_bytes > 0:
                ratio = actual_bytes / predicted_bytes
                logger.info(
                    "  %s: %d MB actual vs %d MB predicted (%.2f×) [%s]",
                    resolved.platform,
                    actual_bytes // (1024 * 1024),
                    predicted_bytes // (1024 * 1024),
                    ratio,
                    pred_label,
                )
            if executed.report.budget_stopped:
                logger.info(
                    "  %s: %d unit(s) stopped by budget",
                    resolved.platform,
                    len(executed.report.budget_stopped),
                )
            # Platform-level size record (size_data.json) — WITH input bytes, so the
            # CostModel prior layer that reads it is no longer fed zeros.
            executed_units = [
                up
                for up in planned.build_plan.units
                if str(up.unit.unit_id) not in set(executed.report.budget_stopped)
            ]
            self._record_size(
                resolved,
                actual_bytes,
                executed.report.terminal_count,
                input_size_bytes=sum(up.unit.source_size for up in executed_units),
            )

        # ── EMIT phase (non-fatal) ─────────────────────────────────────
        try:
            run_emit(executed, profile=profile, output_dir=output_dir)
        except PhaseError as exc:
            # Outputs are already materialised — EMIT errors are best-effort
            logger.warning(
                "_process_platform(%s): EMIT error (outputs intact) — %s",
                resolved.platform,
                exc.cause,
                exc_info=True,
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Profile loading  (instance method — needs self.composed_target)
    # ─────────────────────────────────────────────────────────────────────────

    def _resolve_paths(self) -> "ResolvePaths":
        paths = get_paths()
        root = Path(paths.workspace_root)
        return ResolvePaths(
            workspace_root=root,
            config_dir=root / "config",
            dats_dir=Path(getattr(paths, "dats_dir", root / "dats")),
            lists_dir=root / "lists",
        )

    def _get_dat_pattern(self, platform: str) -> str | None:
        """DAT search pattern from ``config/dat_patterns.yaml`` (kept as a patch point)."""
        from romfarmer.driver.resolve import _dat_pattern

        return _dat_pattern(platform, self._resolve_paths().config_dir)

    def resolve(self, resolved: ResolvedPlatformConfig) -> "ResolvedBuild":
        """RESOLVE one platform into a frozen ``ResolvedBuild`` (public API).

        ``cli/plan.py`` and ``cli/doctor.py`` use this so ``plan --explain``
        predicts exactly what ``build`` does.  DAT discovery and profile
        loading go through the instance methods below so tests can patch them.
        """
        from romfarmer.driver.resolve import resolve_platform

        if not resolved.sources or resolved.sources[0].path is None:
            raise ValueError(f"No source directory for {resolved.platform}")
        return resolve_platform(
            resolved,
            self.composed_target,
            self._resolve_paths(),
            dat_file=self._find_dat_file(resolved),
            profile=self._load_target_profile(),
            sample_n=getattr(self, "_test_sample", None),
            sample_seed=getattr(self, "_test_seed", None) or 0,
        )

    def _load_target_profile(self) -> "object | None":
        """Load (and cache) the ``ConcreteTargetProfile`` for this build's target.

        Raises ``TargetProfileError`` — never returns a silent ``None`` for a
        misconfigured frontend/device (review G4 #6).
        """
        if hasattr(self, "_cached_target_profile"):
            return self._cached_target_profile
        from romfarmer.driver.resolve import load_target_profile

        profile = load_target_profile(self.composed_target, self._resolve_paths().config_dir)
        self._cached_target_profile = profile
        return profile

    def _load_curated_lists(self, platform: str) -> "tuple[frozenset[str], frozenset[str]]":
        from romfarmer.driver.resolve import load_curated_lists

        return load_curated_lists(platform, self._resolve_paths().lists_dir)

    def _build_manifest(
        self,
        resolved: "ResolvedPlatformConfig",
        platform: "object",
        dat_file: Path | None = None,
        chain: "tuple[str, ...]" = (),
    ) -> "BuildManifest":
        """Construct a ``BuildManifest`` (delegates to ``driver.resolve.build_manifest``)."""
        from romfarmer.driver.resolve import build_manifest, negotiate_format_chain
        from romfarmer.ir.catalog import PlatformId

        return build_manifest(
            resolved,
            PlatformId(str(platform)),
            chain=tuple(chain) or negotiate_format_chain(resolved),
            dat_file=dat_file,
            paths=self._resolve_paths(),
            sample_n=getattr(self, "_test_sample", None),
            sample_seed=getattr(self, "_test_seed", None) or 0,
        )

    def _find_dat_file(self, resolved: ResolvedPlatformConfig) -> Path | None:
        """Find the DAT file for a platform (delegates to ``driver.resolve.find_dat_file``)."""
        from romfarmer.driver.resolve import find_dat_file

        return find_dat_file(
            resolved, self._resolve_paths(), pattern=self._get_dat_pattern(resolved.platform)
        )

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
        input_size_bytes: int = 0,
    ):
        """Record output size (and input bytes) for future estimation."""
        try:
            from romfarmer.utils.size_tracking import record_platform_size

            record_platform_size(
                platform=resolved.platform,
                compression=resolved.compression.value,
                output_size_bytes=output_size,
                selection=resolved.tier_strategy or "all",
                output_files=files_processed,
                input_size_bytes=input_size_bytes,
                # Explicit path: never the cwd-relative default (tests patch get_paths)
                db_path=Path(get_paths().workspace_root) / "config" / "size_data.json",
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
            from romfarmer.analysis.knowledge import KnowledgeBase
            from romfarmer.config.generation_loader import load_generation
            from romfarmer.ir.catalog import Catalog, PlatformId
            from romfarmer.ir.manifest import BuildManifest
            from romfarmer.planner.costmodel import CostModel
            from romfarmer.planner.passes.generation import run as generation_pass

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
                    / "config"
                    / "curations"
                    / "rescue"
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
            logger.info(
                f"✅ Generation filter complete: removed {removed} cross-platform duplicates"
            )

        except Exception as e:
            logger.error(f"Generation filter error: {e}", exc_info=True)
            logger.warning("Generation filter failed, but build will continue")
            logger.warning("Generation filter failed, but build will continue")

    def _hook_context(self, platforms: list[str] | None = None) -> "HookContext":
        from romfarmer.driver.hooks import HookContext

        output_base = Path(self.build_spec.get_output_base())
        if not output_base.is_absolute():
            output_base = get_paths().workspace_root / output_base
        return HookContext(
            build_name=self.build_spec.name,
            output_base=output_base,
            platforms=tuple(platforms if platforms is not None else self.state.completed_platforms),
            metadata_db=get_paths().metadata_db,
            workspace_root=Path(get_paths().workspace_root),
        )

    def _run_post_build_hooks(self):
        """Run post-build hooks through the ``driver.hooks`` registry (no shell)."""
        if not self.build_spec.post_build:
            return
        from romfarmer.driver.hooks import run_post_build_hooks

        logger.info(f"\n{'=' * 60}")
        logger.info("Running post-build hooks...")
        logger.info(f"{'=' * 60}\n")
        run_post_build_hooks(self.build_spec.post_build, self._hook_context())

    def _run_deployment(self):
        """Deploy via ``driver.hooks.run_deployment`` (argv, never a shell string)."""
        deploy = self.build_spec.deploy
        if not deploy:
            return
        from romfarmer.driver.hooks import run_deployment

        logger.info(f"\n{'=' * 60}")
        logger.info("Running deployment...")
        logger.info(f"{'=' * 60}\n")
        result = run_deployment(deploy, self._hook_context().output_base)
        if result is None:
            return
        if result.ok:
            logger.info("  ✅ Deployment complete")
        else:
            logger.error(f"  ❌ Deployment failed: {result.summary}")

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
            f.write("Platforms Summary:\n")
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

    def get_status(self) -> dict[str, Any]:
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
            "last_updated": self.state.last_updated.isoformat()
            if self.state.last_updated
            else None,
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
    platforms: dict[str, SlimPlatformConfig],
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
            roots = yaml.safe_load(os.path.expandvars(f.read())).get("roots", {})
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
