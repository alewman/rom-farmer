"""Config resolver — the composition engine.

The resolver takes a BuildSpec and produces a ResolvedPlatformConfig for
each platform in the build. This is the heart of the new system.

Resolution algorithm:
    for each platform in (union of recipe platforms) - excludes:
        1. Load SlimPlatformConfig (intrinsic facts)
        2. Stack recipes in order (later wins for overlapping fields)
        3. Apply target constraints (frontend compression fallback, folder mapping)
        4. Apply device filter (skip unsupported platforms)
        5. Apply budget/tier constraints (if applicable)
        6. Derive output path
        → emit ResolvedPlatformConfig
"""

import logging
from dataclasses import MISSING, dataclass, field, fields, make_dataclass
from pathlib import Path
from typing import Any

from .build_spec import BuildSpec
from .models import (
    CompressionFormat,
    ExtractionType,
    MetadataFilterConfig,
    SelectionConfig,
    SourceConfig,
)
from .recipe import RecipeSpec
from .slim_platform import (
    ArcadeFilter,
    DATReference,
    ListPatterns,
    PS3Config,
    SlimPlatformConfig,
    XboxConfig,
)
from .target import ComposedTarget

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResolvedPlatformConfig:
    """Fully resolved configuration for one platform in one build.

    This is the output of the resolver — everything needed to build
    a pipeline for this platform. No further lookups needed.

    Frozen (2026-09-03): RESOLVE's output is a value.  The resolver composes
    it on a mutable ``_ResolvedDraft`` and emits it once; later stages use
    ``dataclasses.replace`` for derived copies (e.g. tier assignment).
    """

    # Identity
    platform: str
    display_name: str | None = None
    platform_type: str | None = None  # 'arcade' or None
    emulator: str | None = None
    metadata_system: str | None = None

    # Processing
    extraction_type: ExtractionType = ExtractionType.NONE
    compression: CompressionFormat = CompressionFormat.NONE
    multi_disc: bool = False

    # DAT
    dat: DATReference | None = None

    # Sources
    sources: list[SourceConfig] = field(default_factory=list)
    chd_sources: list[SourceConfig] | None = None

    # Filtering
    selection: SelectionConfig | None = None
    metadata_filter: MetadataFilterConfig | None = None
    apply_lists: bool = True
    list_patterns: ListPatterns | None = None
    arcade_filter: ArcadeFilter | None = None
    bios: list[str] | None = None
    samples_sources: list[SourceConfig] | None = None

    # Output
    output_dir: Path | None = None
    folder_name: str = ""  # From frontend folder mapping
    organization: str = "flat"  # From frontend/target default
    metadata: bool = True

    # Platform-specific
    ps3: PS3Config | None = None
    xbox: XboxConfig | None = None

    # Extras (DLC/updates)
    extras: Any | None = None  # ExtrasConfig from slim_platform

    # Build context
    tier: int | None = None
    tier_strategy: str | None = None

    # Source recipe name (for debugging/logging)
    recipe_name: str | None = None

    @property
    def is_arcade(self) -> bool:
        """Check if this is an arcade platform."""
        return self.platform_type == "arcade"

    def get_metadata_system(self) -> str:
        """Get the system name for metadata lookups."""
        return self.metadata_system or self.platform


def _make_draft_type() -> type:
    """Mutable twin of ``ResolvedPlatformConfig`` used only while composing."""
    spec = []
    for f in fields(ResolvedPlatformConfig):
        if f.default_factory is not MISSING:
            spec.append((f.name, f.type, field(default_factory=f.default_factory)))
        elif f.default is not MISSING:
            spec.append((f.name, f.type, field(default=f.default)))
        else:
            spec.append((f.name, f.type))
    return make_dataclass("_ResolvedDraft", spec)


_ResolvedDraft = _make_draft_type()


def _freeze(draft: Any) -> ResolvedPlatformConfig:
    return ResolvedPlatformConfig(
        **{f.name: getattr(draft, f.name) for f in fields(ResolvedPlatformConfig)}
    )


class ConfigResolver:
    """Resolves a BuildSpec into per-platform ResolvedPlatformConfigs.

    This is the composition engine that merges:
        platform intrinsics + recipe choices + target constraints = resolved config
    """

    def __init__(
        self,
        platforms: dict[str, SlimPlatformConfig],
        recipes: dict[str, RecipeSpec],
        composed_target: ComposedTarget | None = None,
    ):
        """Initialize the resolver.

        Args:
            platforms: Map of platform name → SlimPlatformConfig
            recipes: Map of recipe name → RecipeSpec
            composed_target: Loaded target (frontend + device)
        """
        self.platforms = platforms
        self.recipes = recipes
        self.composed_target = composed_target

    def resolve(
        self,
        build: BuildSpec,
    ) -> list[ResolvedPlatformConfig]:
        """Resolve a build spec into per-platform configs.

        Args:
            build: The build specification

        Returns:
            List of ResolvedPlatformConfig, one per platform
        """
        # Step 1: Determine which platforms to process
        platform_names = self._collect_platforms(build)
        logger.info(f"Resolved {len(platform_names)} platforms for build '{build.name}'")

        # Step 2: Load recipes referenced by this build
        build_recipes = self._load_build_recipes(build)

        # Step 3: Resolve each platform
        resolved = []
        for platform_name in sorted(platform_names):
            platform = self.platforms.get(platform_name)
            if platform is None:
                logger.warning(f"Platform '{platform_name}' not found, skipping")
                continue

            config = self._resolve_platform(
                platform=platform,
                recipes=build_recipes,
                build=build,
            )

            if config is not None:
                resolved.append(config)

        return resolved

    def _collect_platforms(self, build: BuildSpec) -> set[str]:
        """Determine which platforms to process for this build.

        Priority:
        1. If build.platforms is set, use exactly those
        2. Otherwise, union of all recipe platform lists
        3. Minus build.exclude
        4. Minus device unsupported platforms
        """
        if build.platforms is not None:
            # Explicit platform list
            platform_names = set(build.platforms)
        else:
            # Union of all recipe platform lists
            platform_names = set()
            for recipe_name in build.recipes:
                recipe = self.recipes.get(recipe_name)
                if recipe is None:
                    raise ValueError(f"Recipe '{recipe_name}' not found")
                if recipe.platforms:
                    platform_names.update(recipe.platforms)
                # Recipes with empty platforms don't contribute to the union
                # (they apply to whatever other recipes bring in)

        # Apply excludes
        platform_names -= set(build.exclude)

        # Apply device unsupported filter
        if self.composed_target:
            unsupported = set()
            for name in platform_names:
                if not self.composed_target.supports_platform(name):
                    unsupported.add(name)
                    logger.info(
                        f"Platform '{name}' not supported by device '{self.composed_target.device.name}', excluding"
                    )
            platform_names -= unsupported

        return platform_names

    def _load_build_recipes(self, build: BuildSpec) -> list[RecipeSpec]:
        """Load and validate recipes referenced by the build."""
        recipes = []
        for recipe_name in build.recipes:
            recipe = self.recipes.get(recipe_name)
            if recipe is None:
                raise ValueError(
                    f"Recipe '{recipe_name}' not found. "
                    f"Available recipes: {', '.join(sorted(self.recipes.keys()))}"
                )
            recipes.append(recipe)
        return recipes

    def _resolve_platform(
        self,
        platform: SlimPlatformConfig,
        recipes: list[RecipeSpec],
        build: BuildSpec,
    ) -> ResolvedPlatformConfig | None:
        """Resolve a single platform by stacking recipes on top of intrinsics.

        Returns None if the platform should be skipped.
        """
        # Start with intrinsics (mutable draft; frozen on return)
        config = _ResolvedDraft(
            platform=platform.name,
            display_name=platform.display_name,
            platform_type=platform.type,
            emulator=platform.emulator,
            metadata_system=platform.metadata_system,
            extraction_type=platform.extraction,
            multi_disc=platform.multi_disc,
            dat=platform.dat,
            sources=platform.sources,
            chd_sources=platform.chd_sources,
            list_patterns=platform.list_patterns,
            arcade_filter=platform.arcade_filter,
            bios=platform.bios,
            samples_sources=platform.samples_sources,
            ps3=platform.ps3,
            xbox=platform.xbox,
            extras=platform.extras,
        )

        # Stack recipes in order (later wins for overlapping fields)
        last_matching_recipe = None
        for recipe in recipes:
            if recipe.applies_to(platform.name):
                self._apply_recipe(config, recipe)
                last_matching_recipe = recipe.name

        config.recipe_name = last_matching_recipe

        # Apply optimizer generation thresholds (before global selection override
        # so that explicit build.selection can still win if set).
        if build.optimizer_thresholds:
            self._apply_optimizer_thresholds(config, build.optimizer_thresholds)

        # Apply build-level selection override (if any)
        if build.selection is not None:
            config.selection = build.selection

        # Apply target constraints
        if self.composed_target:
            self._apply_target_constraints(config, platform.name)

        # Derive output path
        config.output_dir = self._derive_output_path(config, build)

        return _freeze(config)

    def _apply_recipe(
        self,
        config: Any,  # _ResolvedDraft (mutable) — frozen by _resolve_platform
        recipe: RecipeSpec,
    ) -> None:
        """Apply a recipe's processing choices to a resolved config.

        Mutates config in place. Later recipes override earlier ones.
        """
        # Compression
        if recipe.compression is not None:
            effective = recipe.get_effective_compression()
            if effective is not None:
                config.compression = effective

        # Selection (stacks — later recipe replaces)
        if recipe.selection is not None:
            config.selection = recipe.selection

        # Metadata filter (stacks — later recipe replaces)
        if recipe.metadata_filter is not None:
            config.metadata_filter = recipe.metadata_filter

        # Apply lists
        if recipe.apply_lists is not None:
            config.apply_lists = recipe.apply_lists

        # Metadata
        if recipe.metadata is not None:
            config.metadata = recipe.metadata

        # Arcade filter overrides
        if recipe.arcade_filter_overrides is not None and config.arcade_filter is not None:
            # Merge overrides into existing arcade filter
            af_data = config.arcade_filter.model_dump()
            af_data.update(recipe.arcade_filter_overrides)
            config.arcade_filter = ArcadeFilter(**af_data)

        # PS3 overrides
        if recipe.ps3_updates_enabled is not None and config.ps3 is not None:
            ps3_data = config.ps3.model_dump()
            ps3_data["use_sony_psn"] = recipe.ps3_updates_enabled
            config.ps3 = PS3Config(**ps3_data)

        if recipe.ps3_dlc_enabled is not None and config.ps3 is not None:
            ps3_data = config.ps3.model_dump()
            ps3_data["dlc_enabled"] = recipe.ps3_dlc_enabled
            config.ps3 = PS3Config(**ps3_data)

    def _apply_target_constraints(
        self,
        config: Any,  # _ResolvedDraft (mutable) — frozen by _resolve_platform
        platform_name: str,
    ) -> None:
        """Apply target (frontend + device) constraints.

        - Folder name mapping from frontend
        - Compression fallback (e.g., 7z → zip for RocknIX)
        - Default organization style from frontend
        - Metadata default from frontend
        """
        target = self.composed_target
        if target is None:
            return

        # Folder name from frontend mapping
        config.folder_name = target.get_folder_name(platform_name)

        # Organization from frontend defaults
        if hasattr(target.frontend, "defaults") and target.frontend.defaults:
            config.organization = target.frontend.defaults.organization
            config.metadata = target.frontend.defaults.metadata

        # Compression fallback
        # If the recipe set 7z but the frontend doesn't support it, fall back
        if config.compression != CompressionFormat.NONE:
            fallback = getattr(target.frontend, "compression_fallback", {})
            if fallback:
                comp_str = config.compression.value
                if comp_str in fallback:
                    fallback_str = fallback[comp_str]
                    try:
                        config.compression = CompressionFormat(fallback_str)
                        logger.info(
                            f"  {platform_name}: compression fallback "
                            f"{comp_str} → {fallback_str} (frontend: {target.frontend.name})"
                        )
                    except ValueError:
                        logger.warning(f"  Invalid fallback format: {fallback_str}")

        # Override with target's preferred compression if set
        target_pref = target.get_preferred_compression(platform_name, default=None)
        if target_pref and target_pref != "none":
            try:
                pref_format = CompressionFormat(target_pref)
                # Only override if recipe didn't explicitly set something
                # (target preferred is a hint, recipe is explicit)
                if config.compression == CompressionFormat.NONE:
                    config.compression = pref_format
            except ValueError:
                pass

    def _apply_optimizer_thresholds(
        self,
        config: Any,  # _ResolvedDraft (mutable) — frozen by _resolve_platform
        thresholds: dict[str, float],
    ) -> None:
        """Apply per-generation optimizer thresholds as a per-platform min_rating.

        Looks up the platform's generation (via CONSOLE_GENERATIONS) and, if
        the generation has a non-zero threshold, installs a SelectionConfig
        with ``min_rating`` set accordingly.

        The existing ``config.selection`` is preserved and only
        ``min_rating`` is overridden, so other selection constraints
        (e.g., ``top_n``, ``max_size_gb``) remain intact.
        """
        from romfarmer.config.generation_loader import platform_generation

        gen = platform_generation(config.platform)
        threshold = thresholds.get(gen, 0.0)

        if threshold <= 0.0:
            # Floor gens (gen3/gen4/arcade) — include everything, no filter needed
            return

        if config.selection is not None:
            # Patch the existing SelectionConfig in place (copy with new min_rating)
            existing = config.selection.model_dump()
            existing["min_rating"] = threshold
            config.selection = SelectionConfig(**existing)
        else:
            config.selection = SelectionConfig(min_rating=threshold)

        logger.debug(
            f"  {config.platform}: optimizer threshold {gen}={threshold:.2f} "
            f"→ selection.min_rating={threshold:.2f}"
        )

    def _derive_output_path(
        self,
        config: Any,  # _ResolvedDraft or ResolvedPlatformConfig
        build: BuildSpec,
    ) -> Path:
        """Derive the output path for a platform.

        Pattern: {output_base} / {folder_name}

        The folder_name comes from the frontend's folder mapping.
        The output_base comes from the build spec.
        """
        output_base = build.get_output_base()
        folder = config.folder_name or config.platform
        return output_base / folder


def resolve_build(
    build: BuildSpec,
    platforms: dict[str, SlimPlatformConfig],
    recipes: dict[str, RecipeSpec],
    composed_target: ComposedTarget | None = None,
) -> list[ResolvedPlatformConfig]:
    """Convenience function to resolve a build in one call.

    Args:
        build: Build specification
        platforms: Map of platform name → SlimPlatformConfig
        recipes: Map of recipe name → RecipeSpec
        composed_target: Optional composed target (frontend + device)

    Returns:
        List of ResolvedPlatformConfig
    """
    resolver = ConfigResolver(
        platforms=platforms,
        recipes=recipes,
        composed_target=composed_target,
    )
    return resolver.resolve(build)
