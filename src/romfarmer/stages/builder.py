"""Declarative pipeline builder.

Replaces the 200-line if/elif chain in PlatformProcessor._process_target()
with a declarative lookup table that maps extraction types to stage sequences.

Usage:
    from romfarmer.stages.builder import build_pipeline
    
    pipeline = build_pipeline(resolved_config, cache_manager=cache)
    results = pipeline.execute(source_dir, work_dir, output_dir, dat_file_path)
"""

import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from romfarmer.config.resolver import ResolvedPlatformConfig
from romfarmer.config.models import (
    CompressionFormat,
    ExtractionType,
    SelectionConfig,
    SelectionStrategy,
)
from .base import Stage
from .pipeline import Pipeline

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Stage factory functions for each extraction type
# ═══════════════════════════════════════════════════════════════════════════════

def _cartridge_stages(
    resolved: ResolvedPlatformConfig,
    cache_manager: Optional[Any] = None,
    **kwargs,
) -> List[Stage]:
    """Build stages for cartridge extraction (No-Intro ROMs).
    
    Extract → optionally compress to 7z/zip.
    When no compression is needed, CAS passthrough keeps the store
    self-contained.
    """
    from romfarmer.stages import (
        CachePreCheckStage,
        CompressArchiveStage,
        ExtractArchiveStage,
    )
    from romfarmer.stages.cache_store import CacheStoreStage
    
    stages: List[Stage] = []
    
    if cache_manager and resolved.compression in (CompressionFormat.SEVENZ, CompressionFormat.ZIP):
        # Transformation pipeline: pre-check → extract → compress (compress stores to CAS)
        stages.append(CachePreCheckStage(
            cache_manager=cache_manager,
            output_format=resolved.compression.value,
        ))
        stages.append(ExtractArchiveStage())
        stages.append(CompressArchiveStage(cache_manager=cache_manager))
    elif cache_manager:
        # Passthrough pipeline: pre-check → extract → store (CAS keeps raw ROMs)
        stages.append(CachePreCheckStage(
            cache_manager=cache_manager,
            output_format=None,  # auto-detect from ZIP contents
        ))
        stages.append(ExtractArchiveStage())
        stages.append(CacheStoreStage(
            cache_manager=cache_manager,
            output_format=None,  # auto-detect from file extension
            tool_name="passthrough",
        ))
    else:
        # No cache — just extract
        stages.append(ExtractArchiveStage())
        if resolved.compression in (CompressionFormat.SEVENZ, CompressionFormat.ZIP):
            stages.append(CompressArchiveStage())
    
    return stages


def _disc_stages(
    resolved: ResolvedPlatformConfig,
    cache_manager: Optional[Any] = None,
    metadata_db: Optional[Any] = None,
    **kwargs,
) -> List[Stage]:
    """Build stages for disc extraction (Redump).
    
    Extract CUE/BIN → optionally convert to CHD → create M3U playlists.
    When no conversion is needed, CAS passthrough keeps the store
    self-contained.
    """
    from romfarmer.stages import (
        CachePreCheckStage,
        CompressCHDStage,
        CreateM3UStage,
        ExtractArchiveStage,
    )
    from romfarmer.stages.cache_store import CacheStoreStage
    
    stages: List[Stage] = []
    
    if resolved.compression == CompressionFormat.CHD:
        # Transformation pipeline: pre-check → extract → CHD (CHD stores to CAS)
        if cache_manager:
            stages.append(CachePreCheckStage(
                cache_manager=cache_manager,
                output_format="chd",
            ))
        stages.append(ExtractArchiveStage())
        db_session = metadata_db.get_session() if metadata_db else None
        stages.append(CompressCHDStage(
            db_session=db_session,
            cache_manager=cache_manager,
        ))
        stages.append(CreateM3UStage())
    elif cache_manager:
        # Passthrough pipeline: pre-check → extract → store
        stages.append(CachePreCheckStage(
            cache_manager=cache_manager,
            output_format=None,
        ))
        stages.append(ExtractArchiveStage())
        stages.append(CacheStoreStage(
            cache_manager=cache_manager,
            output_format=None,
            tool_name="passthrough",
        ))
    else:
        # No cache — just extract
        stages.append(ExtractArchiveStage())
    
    return stages


def _rvz_stages(
    resolved: ResolvedPlatformConfig,
    cache_manager: Optional[Any] = None,
    **kwargs,
) -> List[Stage]:
    """Build stages for RVZ extraction (Wii/GameCube).
    
    Unzip RVZ from source archives. No transformation needed — RVZ is
    Dolphin's native format. CAS passthrough stores extracted RVZ files
    so multi-frontend builds are instant.
    """
    from romfarmer.stages import CachePreCheckStage, UnzipRVZStage
    from romfarmer.stages.cache_store import CacheStoreStage
    
    stages: List[Stage] = []
    
    if cache_manager:
        # Pre-check: skip extraction entirely if RVZ is already in CAS
        stages.append(CachePreCheckStage(
            cache_manager=cache_manager,
            output_format="rvz",
        ))
    
    # Extract RVZ from ZIP archives
    stages.append(UnzipRVZStage())
    
    if cache_manager:
        # Store extracted RVZ in CAS for future builds
        stages.append(CacheStoreStage(
            cache_manager=cache_manager,
            output_format="rvz",
            tool_name="passthrough",
        ))
    
    return stages


def _ps3_stages(
    resolved: ResolvedPlatformConfig,
    cache_manager: Optional[Any] = None,
    **kwargs,
) -> List[Stage]:
    """Build stages for PS3 decryption + extraction (tree-cache accelerated).

    Uses TransformPS3Stage which checks the CAS tree cache first.
    If every game is already cached (e.g. from a prior ingest), the build
    is instant — just hardlinks from CAS to the work directory.
    """
    from romfarmer.stages.transform_ps3 import TransformPS3Stage

    # Create tree store for CAS-backed folder dedup
    tree_store = None
    try:
        from romfarmer.cas import ContentStore, TreeStore
        store = ContentStore("store")
        tree_store = TreeStore(store)
    except Exception:
        pass

    stages: List[Stage] = []
    stages.append(TransformPS3Stage(
        tree_store=tree_store,
        cache_manager=cache_manager,
    ))

    return stages


def _xiso_stages(
    resolved: ResolvedPlatformConfig,
    metadata_db: Optional[Any] = None,
    cache_manager: Optional[Any] = None,
    **kwargs,
) -> List[Stage]:
    """Build stages for Xbox XISO conversion."""
    from romfarmer.stages import (
        CompressSquashfsStage,
        ConvertXISOStage,
        ExtractArchiveStage,
    )
    
    stages: List[Stage] = []
    
    # Extract from ZIP first
    stages.append(ExtractArchiveStage())
    
    # Convert to XISO
    extract_xiso_path = None
    if resolved.xbox:
        extract_xiso_path = resolved.xbox.extract_xiso_path
    
    db_session = metadata_db.get_session() if metadata_db else None
    stages.append(ConvertXISOStage(
        extract_xiso_path=extract_xiso_path,
        db_session=db_session,
    ))
    
    # Optional squashfs compression
    if resolved.compression == CompressionFormat.SQUASHFS:
        stages.append(CompressSquashfsStage())
    
    return stages


def _none_stages(
    resolved: ResolvedPlatformConfig,
    **kwargs,
) -> List[Stage]:
    """No extraction needed."""
    return []


# ═══════════════════════════════════════════════════════════════════════════════
# The lookup table
# ═══════════════════════════════════════════════════════════════════════════════

EXTRACTION_STAGE_BUILDERS = {
    ExtractionType.NONE: _none_stages,
    ExtractionType.CARTRIDGE: _cartridge_stages,
    ExtractionType.DISC: _disc_stages,
    ExtractionType.RVZ: _rvz_stages,
    ExtractionType.PS3: _ps3_stages,
    ExtractionType.XISO: _xiso_stages,
}


# ═══════════════════════════════════════════════════════════════════════════════
# Main builder function
# ═══════════════════════════════════════════════════════════════════════════════

def build_pipeline(
    resolved: ResolvedPlatformConfig,
    cache_manager: Optional[Any] = None,
    composed_target: Optional[Any] = None,
    work_dir: Optional[Path] = None,
) -> Pipeline:
    """Build a processing pipeline from a resolved config.
    
    This replaces the 200-line if/elif chain in PlatformProcessor._process_target().
    
    The pipeline is assembled declaratively:
    1. Filtering stages (DAT filter or arcade filter)
    2. Selection stages (if configured)
    3. List stages (keep/delete lists)
    4. Extraction + compression stages (from lookup table)
    5. PS3 updates (if applicable)
    6. Output stages (organize + metadata)
    
    Args:
        resolved: Fully resolved platform config from the resolver
        cache_manager: Optional ROM cache for build acceleration
        composed_target: Optional composed target for pipeline context
        work_dir: Working directory for selection filter temp files
        
    Returns:
        Assembled Pipeline ready for execution
    """
    from romfarmer.stages import (
        ApplyListsStage,
        ApplyPS3UpdatesStage,
        CopyArcadeStage,
        FilterArcadeStage,
        FilterDATStage,
        Filter1G1RStage,
        GenerateMetadataStage,
        OrganizeStage,
        SelectionFilter,
    )
    
    # We need a PlatformConfig-like object for the Pipeline constructor.
    # For now, create the pipeline with minimal config — the stages use
    # StageContext which we can populate from the resolved config.
    # This is a transitional step; eventually Pipeline will take ResolvedPlatformConfig directly.
    platform_config = _build_compat_platform_config(resolved)
    
    pipeline = Pipeline(
        platform_config=platform_config,
        target_name=resolved.folder_name or resolved.platform,
        composed_target=composed_target,
        tier=resolved.tier,
        tier_strategy=resolved.tier_strategy,
    )
    
    # Initialize metadata database for transformation recording (if needed)
    metadata_db = None
    if resolved.compression == CompressionFormat.CHD or resolved.extraction_type == ExtractionType.XISO:
        try:
            from romfarmer.metadata.database import MetadataDatabase
            metadata_db_path = Path("metadata/database/romfarmer.db")
            metadata_db = MetadataDatabase(metadata_db_path)
        except Exception as e:
            logger.warning(f"Could not initialize metadata DB: {e}")
    
    # ── 1. Filtering ──────────────────────────────────────────────────────
    if resolved.is_arcade:
        pipeline.add_stage(FilterArcadeStage())
    else:
        pipeline.add_stage(FilterDATStage())
        pipeline.add_stage(Filter1G1RStage())
    
    # ── 2. Selection (if configured) ──────────────────────────────────────
    if resolved.selection:
        output_format = resolved.compression.value.lower() if resolved.compression != CompressionFormat.NONE else None
        pipeline.add_stage(SelectionFilter(
            work_dir=work_dir or Path("temp"),
            selection=resolved.selection,
            platform=resolved.platform,
            output_format=output_format,
        ))
    
    # ── 3. Apply lists ────────────────────────────────────────────────────
    if resolved.apply_lists:
        pipeline.add_stage(ApplyListsStage())
    
    # ── 4. Extraction + Compression (lookup table) ────────────────────────
    if resolved.is_arcade:
        # Arcade recompression: ZIP → 7z when frontend prefers 7z
        if resolved.compression in (CompressionFormat.SEVENZ,) and cache_manager:
            from romfarmer.stages.recompress_arcade import RecompressArcadeStage
            pipeline.add_stage(RecompressArcadeStage(
                cache_manager=cache_manager,
            ))
        # Arcade: copy/link ROMs + CHDs to output
        # CAS-aware: populates store for instant multi-frontend builds
        pipeline.add_stage(CopyArcadeStage(cache_manager=cache_manager))
    else:
        stage_builder = EXTRACTION_STAGE_BUILDERS.get(resolved.extraction_type, _none_stages)
        # Pass all possible kwargs — each builder uses **kwargs to ignore irrelevant ones
        extraction_stages = stage_builder(
            resolved=resolved,
            cache_manager=cache_manager,
            metadata_db=metadata_db,
        )

        for stage in extraction_stages:
            pipeline.add_stage(stage)
    
    # ── 5. PS3 Updates (if applicable) ────────────────────────────────────
    if (
        resolved.extraction_type == ExtractionType.PS3
        and resolved.ps3
        and resolved.ps3.nps_database
        and resolved.ps3.pkg_archive
    ):
        pipeline.add_stage(ApplyPS3UpdatesStage(
            nps_database=str(resolved.ps3.nps_database),
            pkg_archive=str(resolved.ps3.pkg_archive),
            apply_updates=resolved.ps3.use_sony_psn,
            apply_dlc=resolved.ps3.dlc_enabled,
            dlc_mode=resolved.ps3.dlc_mode,
            use_sony_psn=resolved.ps3.use_sony_psn,
        ))
    
    # ── 6. Output (organize + metadata) ───────────────────────────────────
    if not resolved.is_arcade:
        pipeline.add_stage(OrganizeStage())
    
    if resolved.metadata:
        pipeline.add_stage(GenerateMetadataStage())
    
    logger.info(
        f"Built pipeline for {resolved.platform}: "
        f"{len(pipeline.stages)} stages "
        f"(extraction={resolved.extraction_type.value}, "
        f"compression={resolved.compression.value})"
    )
    
    return pipeline


def _build_compat_platform_config(resolved: ResolvedPlatformConfig):
    """Build a backward-compatible PlatformConfig from a ResolvedPlatformConfig.
    
    This is a transitional shim. The Pipeline and Stage classes currently
    expect PlatformConfig. This creates a minimal one from the resolved config.
    
    TODO: Migrate Pipeline/Stage to use ResolvedPlatformConfig directly.
    """
    from romfarmer.config.models import (
        CompressionConfig,
        DATConfig,
        ExtractionConfig,
        ListFileConfig,
        PlatformConfig,
        TargetProfile,
        OrganizationConfig,
        OrganizationStyle,
    )
    
    # Build DAT config
    dat = None
    if resolved.dat:
        dat = DATConfig(
            source=resolved.dat.source,
            file=resolved.dat.file,
            expected_count=resolved.dat.expected_count,
            match_method=resolved.dat.match_method,
            filter_driver=resolved.dat.filter_driver,
            filter_romof=resolved.dat.filter_romof,
            exclude_romof=resolved.dat.exclude_romof,
            name_pattern=resolved.dat.name_pattern,
            exclude_name_pattern=resolved.dat.exclude_name_pattern,
        )
    
    # Build extraction config
    extraction = ExtractionConfig(
        enabled=resolved.extraction_type != ExtractionType.NONE,
        type=resolved.extraction_type,
    )
    if resolved.ps3:
        extraction.keys_directory = resolved.ps3.keys_directory
        extraction.ps3dec_path = resolved.ps3.ps3dec_path
    if resolved.xbox:
        extraction.extract_xiso_path = resolved.xbox.extract_xiso_path
    
    # Build compression config
    compression = None
    if resolved.compression != CompressionFormat.NONE:
        compression = CompressionConfig(format=resolved.compression)
    
    # Build lists config
    lists = None
    if resolved.list_patterns:
        patterns = {}
        lp = resolved.list_patterns
        if lp.delete:
            patterns["delete"] = lp.delete
        if lp.add_myrient:
            patterns["add_myrient"] = lp.add_myrient
        if lp.add_extra:
            patterns["add_extra"] = lp.add_extra
        if lp.add:
            patterns["add"] = lp.add
        
        try:
            lists = ListFileConfig(directory=Path("lists"), patterns=patterns)
        except Exception:
            lists = None
    
    # Build minimal target
    org_style = OrganizationStyle.FLAT
    try:
        org_style = OrganizationStyle(resolved.organization)
    except ValueError:
        pass
    
    targets = [
        TargetProfile(
            name=resolved.folder_name or resolved.platform,
            output_path=resolved.output_dir or Path(f"output/{resolved.platform}"),
            organization=OrganizationConfig(style=org_style),
            metadata=resolved.metadata,
            enabled=True,
        )
    ]
    
    return PlatformConfig(
        name=resolved.platform,
        type=resolved.platform_type,
        emulator=resolved.emulator,
        metadata_system=resolved.metadata_system,
        dat=dat,
        sources=resolved.sources,
        chd_sources=resolved.chd_sources,
        arcade_filter=resolved.arcade_filter.model_dump() if resolved.arcade_filter else None,
        extraction=extraction,
        compression=compression,
        lists=lists,
        selection=resolved.selection,
        multi_disc_handling=resolved.multi_disc,
        targets=targets,
        enabled=True,
    )
