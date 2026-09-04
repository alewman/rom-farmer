"""RESOLVE phase — ``ResolvedPlatformConfig`` → frozen ``ResolvedBuild``.

Everything the later phases need is decided here, once, and returned as a
value:

* the ``BuildManifest`` (selection policy, curated lists, arcade selection,
  PS3 keys, format chain, budget),
* the negotiated ``FormatChain`` (recipe ∩ target-profile preferences),
* the DAT file, the ``ConcreteTargetProfile``, and the source/output dirs.

``resolve_platform`` is pure apart from reading config/DAT/list files under
the directories named in ``ResolvePaths``.  It never touches source ROMs.

History: these functions were private methods on ``NewBuildOrchestrator``
(``_find_dat_file`` / ``_build_manifest`` / ``_load_target_profile`` /
``_load_curated_lists``) plus ``planner/negotiation.py``; ``cli/plan.py`` and
``cli/doctor.py`` reached into them.  Moved here 2026-09-03 (review item 2.2).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from romfarmer.ir.catalog import PlatformId
from romfarmer.ir.chain import FormatChain
from romfarmer.ir.manifest import BuildManifest
from romfarmer.targets.profiles.loader import TargetProfileError

if TYPE_CHECKING:
    from romfarmer.config.resolver import ResolvedPlatformConfig
    from romfarmer.config.target import ComposedTarget
    from romfarmer.targets.profiles.loader import ConcreteTargetProfile

logger = logging.getLogger(__name__)

_UNSET: Any = object()


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ResolvePaths:
    """Directories RESOLVE may read.  Built from ``core.paths`` by the driver."""

    workspace_root: Path
    config_dir: Path
    dats_dir: Path
    lists_dir: Path

    @classmethod
    def from_workspace(cls, workspace_root: Path) -> ResolvePaths:
        return cls(
            workspace_root=workspace_root,
            config_dir=workspace_root / "config",
            dats_dir=workspace_root / "dats",
            lists_dir=workspace_root / "lists",
        )


@dataclass(frozen=True)
class ResolvedBuild:
    """The RESOLVE product for one platform — everything CATALOG/PLAN/EMIT need."""

    platform: str
    resolved: ResolvedPlatformConfig
    manifest: BuildManifest
    chain: FormatChain
    dat_file: Path | None
    profile: ConcreteTargetProfile | None
    source_dir: Path
    source_dirs: tuple[tuple[Path, bool], ...]  # (dir, recursive)
    output_dir: Path
    notes: tuple[str, ...] = ()  # human-readable RESOLVE facts an agent should see


# ---------------------------------------------------------------------------
# Format negotiation (moved from planner/negotiation.py)
# ---------------------------------------------------------------------------


class FormatNegotiationError(ValueError):
    """Recipe and profile format preferences have no intersection.

    Silent fallback was the pre-T11 behaviour and is exactly the bug-5 class:
    a wrong profile key or a misconfigured recipe would produce unexpected
    output with no warning.  Hard failure forces the misconfiguration to
    surface at RESOLVE time rather than silently producing the wrong format.
    """


def negotiate_format_chain(resolved: ResolvedPlatformConfig) -> FormatChain:
    """Map ``(extraction_type, compression)`` to the lowering ``FormatChain``.

    Raises:
        ValueError: if the combination is unrecognised.
    """
    from romfarmer.config.models import CompressionFormat, ExtractionType

    et = resolved.extraction_type
    cf = resolved.compression

    if et == ExtractionType.DISC:
        if cf == CompressionFormat.CHD:
            return ("chd",)
        return ("cue_bin",)  # passthrough — keep CUE/BIN
    if et == ExtractionType.CARTRIDGE:
        if cf == CompressionFormat.SEVENZ:
            return ("7z",)
        if cf == CompressionFormat.ZIP:
            return ("zip",)
        return ("passthrough",)
    if et == ExtractionType.RVZ:
        return ("rvz",)
    if et == ExtractionType.WUX:
        return ("wux",)
    if et == ExtractionType.PS3:
        return ("ps3",)
    if et == ExtractionType.XISO:
        if cf == CompressionFormat.SQUASHFS:
            return ("xiso", "squashfs")
        return ("xiso",)
    if et == ExtractionType.NONE:
        return ("passthrough",)

    raise ValueError(
        f"Unrecognised extraction_type={et!r} / compression={cf!r}. "
        "Add a mapping in driver/resolve.py:negotiate_format_chain."
    )


def negotiate_with_profile(
    resolved: ResolvedPlatformConfig,
    profile: ConcreteTargetProfile,
) -> FormatChain:
    """Recipe chain ∩ profile preferences (blueprint §2.2 — intersection, not override).

    1. Config default from ``negotiate_format_chain``.
    2. If the profile lists no preferences for the platform, the default stands.
    3. If the default is among the profile's supported chains, keep it.
    4. Otherwise raise ``FormatNegotiationError`` — never silently substitute.
    """
    default_chain = negotiate_format_chain(resolved)
    platform_prefs = profile.format_preferences(PlatformId(resolved.platform))
    if not platform_prefs:
        return default_chain
    if default_chain in platform_prefs:
        return default_chain
    raise FormatNegotiationError(
        f"Format negotiation failed for platform '{resolved.platform}': "
        f"recipe chain {default_chain!r} is not in profile preferences "
        f"{platform_prefs!r}.  Check the target profile's format_preferences "
        f"for this platform or update the recipe."
    )


# ---------------------------------------------------------------------------
# Target profile
# ---------------------------------------------------------------------------


def load_target_profile(composed_target: ComposedTarget, config_dir: Path) -> ConcreteTargetProfile:
    """Load the ``ConcreteTargetProfile`` for ``frontend[/device]``.

    Fails loudly (``TargetProfileError``) when the frontend YAML is missing or
    unparseable — a silent ``None`` here disables metadata and format
    negotiation for the whole build with nothing above DEBUG level (review
    G4 #6).  The profile key is the frontend name (+ device), NOT the
    build-spec target name (bug-5).
    """
    from romfarmer.targets.profiles.loader import TargetProfileLoader

    fe = composed_target.frontend.name
    dev = getattr(composed_target.device, "name", None)
    key = f"{fe}/{dev}" if dev else str(fe)
    try:
        return TargetProfileLoader(config_dir).load(key)
    except TargetProfileError:
        raise
    except Exception as exc:
        raise TargetProfileError(f"cannot load target profile {key!r}: {exc}") from exc


# ---------------------------------------------------------------------------
# DAT discovery
# ---------------------------------------------------------------------------

_DAT_CACHE: dict[Path, Any] = {}

_DAT_SOURCE_DIRS = {
    "retool_1g1r_usa": "nointro.retool.1g1r.usa",
    "retool_1g1r_all": "nointro.retool.1g1r.all",
    "retool_1g1r_eng": None,  # depends on extraction type
    "redump_retool_1g1r_usa": "redump.retool.1g1r.usa",
    "redump_retool_1g1r_eng": "redump.retool.1g1r.eng",
    "nointro_retool_1g1r_eng": "nointro.retool.1g1r.eng",
}


def parse_dat(dat_file: Path) -> Any | None:
    """Parse a DAT once per process (CATALOG and the manifest both need it)."""
    if dat_file in _DAT_CACHE:
        return _DAT_CACHE[dat_file]
    parsed: Any = None
    if dat_file.exists():
        try:
            from romfarmer.dat_parser import DATParser

            parsed = DATParser().parse(dat_file)  # type: ignore[no-untyped-call]
        except Exception:
            try:
                from romfarmer.dat_parser import RetoolDATParser

                parsed = RetoolDATParser().parse(dat_file)  # type: ignore[no-untyped-call]
            except Exception:
                logger.warning("could not parse DAT %s", dat_file)
    _DAT_CACHE[dat_file] = parsed
    return parsed


def dat_is_retool_1g1r(resolved: ResolvedPlatformConfig) -> bool:
    """True when the platform's DAT is a Retool 1G1R export (already deduplicated)."""
    dat = getattr(resolved, "dat", None)
    source = getattr(dat, "source", None)
    value = getattr(source, "value", source)
    return isinstance(value, str) and "1g1r" in value.lower()


def _dat_pattern(platform: str, config_dir: Path) -> str | None:
    patterns_path = config_dir / "dat_patterns.yaml"
    if not patterns_path.exists():
        return None
    try:
        with open(patterns_path) as f:
            patterns = yaml.safe_load(f)
        return patterns.get(platform.lower()) if patterns else None
    except Exception:
        return None


def find_dat_file(
    resolved: ResolvedPlatformConfig,
    paths: ResolvePaths,
    *,
    pattern: str | None = _UNSET,
) -> Path | None:
    """Locate the DAT for a platform from its ``dat`` reference; ``None`` if none applies.

    ``pattern`` overrides the ``config/dat_patterns.yaml`` lookup (tests).
    """
    if not resolved.dat:
        return None
    from romfarmer.config.models import DATSource, ExtractionType

    if resolved.dat.source == DATSource.NONE:
        return None

    if resolved.dat.file:
        dat_path = Path(resolved.dat.file)
        if dat_path.exists():
            return dat_path
        ws_path = paths.workspace_root / dat_path
        if ws_path.exists():
            return ws_path

    source = resolved.dat.source
    if source is None:
        return None
    source_str = source.value if hasattr(source, "value") else str(source)
    dat_dir_name = _DAT_SOURCE_DIRS.get(source_str)
    if dat_dir_name is None and source_str == "retool_1g1r_eng":
        dat_dir_name = (
            "nointro.retool.1g1r.eng"
            if resolved.extraction_type == ExtractionType.CARTRIDGE
            else "redump.retool.1g1r.eng"
        )
    if dat_dir_name is None:
        dat_dir_name = source_str

    dat_dir = paths.dats_dir / dat_dir_name
    if not dat_dir.exists():
        logger.warning("DAT directory not found: %s", dat_dir)
        return None

    # Variants in priority order; scan ALL files per variant before falling
    # back so "xbox" cannot match "xbox 360".
    platform_search = (
        _dat_pattern(resolved.platform, paths.config_dir) if pattern is _UNSET else pattern
    )
    variants: list[str] = [platform_search] if platform_search else []
    dat_platform_name = getattr(resolved.dat, "platform_name", None)
    if dat_platform_name:
        variants.append(f"{dat_platform_name} (".lower())
        variants.append(str(dat_platform_name).lower())
    variants.extend([resolved.platform.lower(), resolved.platform.split("-")[0].lower()])

    dat_files = list(dat_dir.glob("*.dat"))
    for variant in variants:
        if not variant:
            continue
        for dat_file in dat_files:
            if variant in dat_file.name.lower():
                logger.info("  DAT: %s", dat_file.name)
                return dat_file

    logger.warning("No DAT file found for %s", resolved.platform)
    return None


# ---------------------------------------------------------------------------
# Curated lists
# ---------------------------------------------------------------------------

_DISC_TAG = re.compile(r"\s*\((?:Disc|Disk|CD)\s*\d+\)", re.IGNORECASE)


def _parse_list(path: Path) -> frozenset[str]:
    if not path.exists():
        return frozenset()
    names: set[str] = set()
    for raw_line in path.read_text(errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        canonical = _DISC_TAG.sub("", Path(line).stem).strip()
        if canonical:
            names.add(canonical)
    return frozenset(names)


def load_curated_lists(platform: str, lists_dir: Path) -> tuple[frozenset[str], frozenset[str]]:
    """``(curated_include, curated_exclude)`` from ``lists/{platform}+*`` and ``lists/{platform}-delete``.

    Names are canonical (extension and disc tags stripped).  Lines starting
    with ``#`` are ignored.
    """
    curated_exclude = _parse_list(lists_dir / f"{platform}-delete")
    curated_include: set[str] = set()
    if lists_dir.exists():
        for add_file in lists_dir.glob(f"{platform}+*"):
            curated_include.update(_parse_list(add_file))
    return frozenset(curated_include), curated_exclude


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


def build_manifest(
    resolved: ResolvedPlatformConfig,
    platform: PlatformId,
    *,
    chain: FormatChain,
    dat_file: Path | None,
    paths: ResolvePaths,
    sample_n: int | None = None,
    sample_seed: int = 0,
    curated: tuple[frozenset[str], frozenset[str]] | None = None,
    dat_filter: bool | None = None,
) -> BuildManifest:
    """Construct the frozen ``BuildManifest`` for one platform.

    ``curated`` overrides the legacy ``lists/`` discovery (the Spec path
    supplies hash-addressed artifacts); ``dat_filter`` overrides the
    "gate iff a DAT was found" default.
    """
    sel = resolved.selection
    preferred_regions: tuple[str, ...] = (
        tuple(sel.preferred_regions) if sel and sel.preferred_regions else ()
    )
    rating_min = getattr(sel, "min_rating", None) if sel else None
    rating_top_n = getattr(sel, "top_n", None) if sel else None
    rating_unrated = getattr(sel, "unrated", "keep") if sel else "keep"
    budget_unrated_as = getattr(sel, "unrated_as", "median") if sel else "median"
    safety_margin = float(getattr(sel, "safety_margin", 0.0)) if sel else 0.0

    budget_bytes = None
    if sel:
        max_gb = getattr(sel, "max_size_gb", None)
        if max_gb:
            budget_bytes = int(float(max_gb) * 1024**3)

    gen_name = None
    gen_order: tuple[str, ...] = ()
    gen_cfg = getattr(resolved, "generation_filter", None)
    if gen_cfg and getattr(gen_cfg, "enabled", False):
        gen_name = getattr(gen_cfg, "generation", None)
        if gen_name:
            try:
                from romfarmer.config.generation_loader import load_generation

                gen_def = load_generation(gen_name)
                if gen_def:
                    gen_order = tuple(gen_def.get_platform_names())
            except Exception:
                pass

    if curated is None:
        curated_include, curated_exclude = load_curated_lists(str(platform), paths.lists_dir)
    else:
        curated_include, curated_exclude = curated

    ps3_keys_directory = None
    keys_dir = getattr(getattr(resolved, "extraction", None), "keys_directory", None)
    if keys_dir:
        ps3_keys_directory = str(keys_dir)

    # Arcade: decide the selection here from DAT facts the catalog never sees
    arcade_selected: frozenset[str] | None = None
    arcade_rejections: tuple[tuple[str, str], ...] = ()
    if resolved.arcade_filter is not None and dat_file is not None:
        dat_parsed = parse_dat(dat_file)
        if dat_parsed is not None:
            from romfarmer.arcade.selection import select_arcade_games

            arcade_selected, arcade_rejections = select_arcade_games(
                dat_parsed, resolved.arcade_filter, resolved.dat
            )
            logger.info(
                "  arcade filter: %d of %d DAT entries selected",
                len(arcade_selected),
                len(dat_parsed.games),
            )

    return BuildManifest(
        platform=platform,
        chain=tuple(chain),
        preferred_regions=preferred_regions,
        rating_min=rating_min,
        rating_top_n=rating_top_n,
        rating_unrated=str(rating_unrated),
        budget_bytes=budget_bytes,
        budget_unrated_as=str(budget_unrated_as),
        safety_margin=safety_margin,
        generation_name=gen_name,
        generation_platform_order=gen_order,
        curated_include=curated_include,
        curated_exclude=curated_exclude,
        dat_filter=(dat_file is not None)
        if dat_filter is None
        else (dat_filter and dat_file is not None),
        one_g_one_r=not dat_is_retool_1g1r(resolved) and arcade_selected is None,
        arcade_selected=arcade_selected,
        arcade_rejections=arcade_rejections,
        sample_n=sample_n,
        sample_seed=sample_seed,
        ps3_keys_directory=ps3_keys_directory,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def resolve_platform(
    resolved: ResolvedPlatformConfig,
    composed_target: ComposedTarget | None,
    paths: ResolvePaths,
    *,
    dat_file: Path | None = _UNSET,
    profile: ConcreteTargetProfile | None = _UNSET,
    sample_n: int | None = None,
    sample_seed: int = 0,
    curated: tuple[frozenset[str], frozenset[str]] | None = None,
    dat_filter: bool | None = None,
) -> ResolvedBuild:
    """RESOLVE one platform into a frozen ``ResolvedBuild``.

    ``dat_file`` / ``profile`` may be supplied to skip discovery (tests,
    ``doctor``).  Raises ``ValueError`` when the platform has no source
    directory, ``TargetProfileError`` when the profile cannot be loaded, and
    ``FormatNegotiationError`` when recipe and profile disagree.
    """
    source_dir = resolved.sources[0].path if resolved.sources else None
    if source_dir is None:
        raise ValueError(f"No source directory for {resolved.platform}")
    source_dirs = tuple(
        (s.path, bool(s.recursive)) for s in (resolved.sources or ()) if s.path is not None
    ) or ((source_dir, False),)

    output_dir = resolved.output_dir or Path(f"output/{resolved.platform}")
    if not output_dir.is_absolute():
        output_dir = paths.workspace_root / output_dir

    if profile is _UNSET:
        profile = (
            load_target_profile(composed_target, paths.config_dir) if composed_target else None
        )
    if dat_file is _UNSET:
        dat_file = find_dat_file(resolved, paths)

    chain = (
        negotiate_with_profile(resolved, profile)
        if profile is not None
        else negotiate_format_chain(resolved)
    )
    platform_id = PlatformId(resolved.platform)
    notes: list[str] = []
    dat_src = getattr(getattr(resolved, "dat", None), "source", None)
    dat_src_value = getattr(dat_src, "value", dat_src)
    if dat_src_value is not None and str(dat_src_value) != "none" and dat_file is None:
        notes.append(
            f"DAT expected (source={dat_src_value}) but no file found under {paths.dats_dir} — "
            "dat_filter cannot gate; 1g1r falls back to the name heuristic"
        )
    if chain == ("passthrough",):
        notes.append("chain=passthrough: source files are copied as-is (no compression)")
    manifest = build_manifest(
        resolved,
        platform_id,
        chain=chain,
        dat_file=dat_file,
        paths=paths,
        sample_n=sample_n,
        sample_seed=sample_seed,
        curated=curated,
        dat_filter=dat_filter,
    )
    return ResolvedBuild(
        platform=resolved.platform,
        resolved=resolved,
        manifest=manifest,
        chain=chain,
        dat_file=dat_file,
        profile=profile,
        source_dir=source_dir,
        source_dirs=source_dirs,
        output_dir=output_dir,
        notes=tuple(notes),
    )
