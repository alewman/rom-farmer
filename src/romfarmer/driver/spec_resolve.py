"""RESOLVE from a ``Spec`` — ``resolve_build(spec, …) -> tuple[ResolvedBuild, …]``.

The Spec carries the *choices* (sources, extraction, compression, DAT lever,
pass policy, budget).  Platform *intrinsics* that are facts rather than
choices (arcade filter, PS3 keys config, DAT platform name, emulator, …)
still come from ``config/platforms/<id>.yaml``; the frontend/device pair
comes from ``config/frontends`` + ``config/devices``.  The Spec wins wherever
both say something.

``spec_from_build`` is the shim that lowers a legacy ``config/builds`` YAML
(recipes + target) into a Spec, so every existing build is one caller of the
new seam.  Its docstring records whether the legacy name is reclaimed later.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from romfarmer.ir.spec import (
    Spec,
    SpecBudget,
    SpecCuratedLists,
    SpecDat,
    SpecError,
    SpecIntent,
    SpecPasses,
    SpecPlatform,
    SpecRating,
    SpecRegion,
    SpecSample,
    SpecTarget,
)

from .resolve import ResolvedBuild, ResolvePaths, dat_is_retool_1g1r, resolve_platform
from .sources import alias_path, load_source_roots, resolve_source

if TYPE_CHECKING:
    from romfarmer.config.resolver import ResolvedPlatformConfig
    from romfarmer.config.target import ComposedTarget

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Target composition (frontend + device, no config/targets/*.yaml needed)
# ---------------------------------------------------------------------------


def compose_target(frontend: str, device: str | None, config_root: Path) -> ComposedTarget:
    from romfarmer.config.target import ComposedTarget, TargetConfig
    from romfarmer.config.target_loader import load_device, load_frontend

    dev = device or "pc"
    try:
        fe_cfg = load_frontend(frontend, config_root)
        dev_cfg = load_device(dev, config_root)
    except Exception as exc:
        raise SpecError(f"target {frontend}/{dev}: {exc}") from exc
    tc = TargetConfig(name=f"{frontend}-{dev}", frontend=frontend, device=dev)
    return ComposedTarget(name=tc.name, frontend=fe_cfg, device=dev_cfg, target_config=tc)


# ---------------------------------------------------------------------------
# Spec platform → ResolvedPlatformConfig
# ---------------------------------------------------------------------------


def _resolved_from_spec_platform(
    sp: SpecPlatform,
    composed: ComposedTarget,
    config_root: Path,
    output_base: Path,
    roots: dict[str, Path],
) -> ResolvedPlatformConfig:
    from romfarmer.config.models import (
        CompressionFormat,
        DATSource,
        ExtractionType,
        SelectionConfig,
        SourceConfig,
    )
    from romfarmer.config.new_loader import load_slim_platform
    from romfarmer.config.resolver import ResolvedPlatformConfig
    from romfarmer.config.slim_platform import DATReference

    try:
        slim = load_slim_platform(sp.platform, config_root)
    except FileNotFoundError as exc:
        raise SpecError(
            f"platforms[{sp.platform!r}]: no config/platforms/{sp.platform}.yaml"
        ) from exc
    try:
        extraction = ExtractionType(sp.extraction)
        compression = CompressionFormat(sp.compression)
    except ValueError as exc:
        raise SpecError(f"platforms[{sp.platform!r}]: {exc}") from exc

    sources = []
    for i, src in enumerate(sp.sources):
        p = resolve_source(src, roots, f"platforms[{sp.platform!r}].sources[{i}]")
        if not p.exists():
            raise SpecError(
                f"platforms[{sp.platform!r}].sources[{i}]: directory not found: {p} "
                f"(root {src.root!r} → {roots[src.root]})"
            )
        sources.append(SourceConfig.model_validate({"path": p, "recursive": src.recursive}))

    dat: DATReference | None = slim.dat
    if sp.dat.source is not None or sp.dat.file is not None:
        update: dict[str, Any] = {}
        if sp.dat.source is not None:
            try:
                update["source"] = DATSource(sp.dat.source)
            except ValueError as exc:
                raise SpecError(f"platforms[{sp.platform!r}].dat.source: {exc}") from exc
        if sp.dat.file is not None:
            update["file"] = Path(sp.dat.file)
        dat = (
            slim.dat.model_copy(update=update)
            if slim.dat is not None
            else DATReference.model_validate(update)
        )

    ps = sp.passes
    selection = SelectionConfig.model_validate(
        {
            "preferred_regions": list(ps.region.preferred),
            "min_rating": ps.rating.min,
            "top_n": ps.rating.top_n,
            "unrated": ps.rating.unrated or "keep",
            "max_size_gb": (ps.budget.max_bytes / 1024**3) if ps.budget.max_bytes else None,
            "unrated_as": ps.budget.unrated_as,
            "safety_margin": 0.0,  # retired: p90 headroom is the constraint
        }
    )

    folder_name = composed.get_folder_name(sp.platform)
    defaults = getattr(composed.frontend, "defaults", None)
    organization = getattr(defaults, "organization", "flat") if defaults else "flat"
    metadata = getattr(defaults, "metadata", True) if defaults else True

    rc = ResolvedPlatformConfig(
        platform=sp.platform,
        display_name=slim.display_name,
        platform_type=slim.type,
        emulator=slim.emulator,
        metadata_system=slim.metadata_system,
        extraction_type=extraction,
        compression=compression,
        multi_disc=slim.multi_disc,
        dat=dat,
        sources=sources,
        chd_sources=slim.chd_sources,
        selection=selection,
        arcade_filter=slim.arcade_filter,
        bios=slim.bios,
        samples_sources=slim.samples_sources,
        output_dir=output_base / (folder_name or sp.platform),
        folder_name=folder_name or "",
        organization=organization,
        metadata=metadata,
        ps3=slim.ps3,
        xbox=slim.xbox,
        extras=slim.extras,
        recipe_name=None,
    )
    if sp.dat.retool_1g1r != dat_is_retool_1g1r(rc):
        raise SpecError(
            f"platforms[{sp.platform!r}].dat.retool_1g1r={sp.dat.retool_1g1r} disagrees with the DAT "
            f"source {getattr(rc.dat, 'source', None)!r} — the flag must state what the DAT is"
        )
    return rc


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def resolve_build(
    spec: Spec,
    config_root: Path,
    *,
    workspace_root: Path | None = None,
    output_base: Path | None = None,
    artifacts_dir: Path | None = None,
) -> tuple[ResolvedBuild, ...]:
    """RESOLVE every platform of *spec*; platforms ordered by priority desc, then id.

    Pure apart from reading config/DAT/artifact files.  Raises ``SpecError``
    for anything the spec gets wrong (unknown platform, missing source dir,
    mismatched DAT lever, unresolvable curated ref) and the usual
    ``FormatNegotiationError`` / ``TargetProfileError`` from RESOLVE.
    """
    from romfarmer.driver.curated import load_curated

    ws = workspace_root or config_root.parent
    paths = ResolvePaths(
        workspace_root=ws, config_dir=config_root, dats_dir=ws / "dats", lists_dir=ws / "lists"
    )
    art_dir = artifacts_dir or ws / "artifacts"
    out_base = output_base or ws / "output" / f"spec-{spec.spec_hash()[:12]}"
    composed = compose_target(spec.target.frontend, spec.target.device, config_root)
    roots = load_source_roots(config_root)

    builds: list[ResolvedBuild] = []
    for sp in sorted(spec.platforms, key=lambda p: (-p.priority, p.platform)):
        rc = _resolved_from_spec_platform(sp, composed, config_root, out_base, roots)
        curated: tuple[frozenset[str], frozenset[str]] | None = (frozenset(), frozenset())
        if sp.passes.curated_lists.ref is not None:
            art = load_curated(sp.passes.curated_lists.ref, art_dir)
            curated = (art.include, art.exclude)
        rb = resolve_platform(
            rc,
            composed,
            paths,
            sample_n=sp.passes.sample.n,
            sample_seed=sp.passes.sample.seed,
            curated=curated,
            dat_filter=sp.passes.dat_filter,
        )
        builds.append(rb)
    return tuple(builds)


# ---------------------------------------------------------------------------
# Legacy shim: config/builds/<name>.yaml → Spec
# ---------------------------------------------------------------------------


def spec_from_build(
    build_name: str,
    config_root: Path | None = None,
    *,
    freeze_lists: bool = True,
    artifacts_dir: Path | None = None,
) -> Spec:
    """Lower a legacy build (recipes × target) into a ``Spec``.

    Every choice the resolver made — compression fallbacks, optimizer
    thresholds (already expanded to per-platform ``min_rating``), selection —
    is read back from the ``ResolvedPlatformConfig`` and written down
    explicitly, so the Spec has no recipe or generation indirection.

    Legacy ``lists/`` curation is frozen into hash-addressed artifacts when
    ``freeze_lists`` is true (default), so the lowered Spec reproduces the
    legacy plan exactly.

    Naming: the legacy pydantic ``config.build_spec.BuildSpec`` keeps its name
    until this shim is the only reader of ``config/builds``; at that point
    ``BuildSpec`` is retired and the name is NOT reclaimed — ``Spec`` stays
    ``Spec`` (recorded per brief v2 changelog item 2).
    """
    from romfarmer.core.paths import get_paths
    from romfarmer.driver.curated import freeze_lists as _freeze
    from romfarmer.new_orchestrator import NewBuildOrchestrator
    from romfarmer.utils.storage_budget import parse_size_spec

    ws = Path(get_paths().workspace_root)
    cfg = config_root or ws / "config"
    orch = NewBuildOrchestrator.from_config(build_name, config_root=cfg)
    bs = orch.build_spec
    composed = orch.composed_target
    art_dir = artifacts_dir or ws / "artifacts"

    roots = load_source_roots(cfg)

    storage = None
    if bs.has_budget_constraint():
        try:
            storage = parse_size_spec(str(bs.storage_budget))
        except Exception:
            storage = None

    platforms: list[SpecPlatform] = []
    for rc in sorted(orch.resolved_configs, key=lambda r: r.platform):
        sel = rc.selection
        dat_src = getattr(getattr(rc, "dat", None), "source", None)
        dat_src_value = getattr(dat_src, "value", dat_src)
        dat_filter = dat_src_value is not None and str(dat_src_value) != "none"
        ref = None
        if freeze_lists:
            art = _freeze(rc.platform, ws / "lists", art_dir)
            ref = art.ref if art is not None else None
        max_bytes = None
        if sel is not None and getattr(sel, "max_size_gb", None):
            max_bytes = int(float(sel.max_size_gb or 0) * 1024**3)
        platforms.append(
            SpecPlatform(
                platform=rc.platform,
                sources=_alias_sources(rc, roots),
                extraction=rc.extraction_type.value,
                compression=rc.compression.value,
                priority=0,
                dat=SpecDat(
                    retool_1g1r=dat_is_retool_1g1r(rc),
                    source=str(dat_src_value) if dat_src_value is not None else None,
                    file=str(rc.dat.file) if (rc.dat is not None and rc.dat.file) else None,
                ),
                passes=SpecPasses(
                    dat_filter=dat_filter,
                    region=SpecRegion(preferred=tuple(sel.preferred_regions) if sel else ()),
                    rating=SpecRating(
                        min=getattr(sel, "min_rating", None) if sel else None,
                        top_n=getattr(sel, "top_n", None) if sel else None,
                        unrated=(
                            getattr(sel, "unrated", "keep")
                            if sel and getattr(sel, "min_rating", None) is not None
                            else None
                        ),
                    ),
                    curated_lists=SpecCuratedLists(ref=ref),
                    budget=SpecBudget(
                        max_bytes=max_bytes,
                        unrated_as=str(getattr(sel, "unrated_as", "median")) if sel else "median",
                    ),
                    sample=SpecSample(),
                ),
            )
        )

    spec = Spec(
        target=SpecTarget(
            frontend=composed.frontend.name,
            device=getattr(composed.device, "name", None),
            storage_bytes=storage,
            reserve_bytes=None,
        ),
        platforms=tuple(platforms),
        intent=SpecIntent(
            text=f"lowered from config/builds/{build_name}.yaml (recipes: {', '.join(bs.recipes)})",
            authored_by="shim:spec_from_build",
        ),
    )
    from romfarmer.ir.spec import validate_spec

    validate_spec(spec)
    return spec


def _alias_sources(rc: ResolvedPlatformConfig, roots: dict[str, Path]) -> tuple[Any, ...]:
    out = []
    for s in rc.sources:
        if s.path is None:
            continue
        aliased = alias_path(Path(s.path), roots, recursive=bool(s.recursive))
        if aliased is None:
            raise SpecError(
                f"{rc.platform}: source {s.path} is under no named root in config/sources.yaml — "
                "add a root alias so the Spec stays portable (no absolute paths in specs)"
            )
        out.append(aliased)
    return tuple(out)
