"""Processing stages for ROM Farmer."""

from .apply_lists import ApplyListsStage
from .apply_ps3_updates import ApplyPS3UpdatesStage
from .base import Stage, StageContext, StageResult, StageStatus
from .compress import CompressCHDStage
from .compress_archive import CompressArchiveStage
from .disc_models import CueSheet, DiscMetadata
from .domain import (
    PreFilters,
    FileSet,
    FileHashes,
    DiscGame,
    DiscProcessing,
    ProcessingStats,
    Transformation,
)
from .extract import ExtractArchiveStage
from .extract_ps3 import ExtractPS3Stage
from .filter_dat import FilterDATStage
from .filter_1g1r import Filter1G1RStage
from .filter_rating import FilterRatingStage
from .filter_selection import SelectionFilter
from .m3u import CreateM3UStage
from .metadata import GenerateMetadataStage
from .organize import OrganizeStage
from .pipeline import Pipeline
from .pre_filter import PreFilterStage
from .transform_models import (
    FileTransformation,
    TransformStatus,
    TransformStep,
    TransformType,
)
from .unzip_rvz import UnzipRVZStage
from .transform_ps3 import TransformPS3Stage

__all__ = [
    # Base classes
    "Stage",
    "StageResult",
    "StageContext",
    "StageStatus",
    # Domain objects
    "PreFilters",
    "FileSet",
    "FileHashes",
    "DiscGame",
    "DiscProcessing",
    "ProcessingStats",
    "Transformation",
    # Stages
    "PreFilterStage",
    "FilterDATStage",
    "Filter1G1RStage",
    "FilterRatingStage",
    "SelectionFilter",
    "ExtractArchiveStage",
    "ExtractPS3Stage",
    "ApplyListsStage",
    "ApplyPS3UpdatesStage",
    "CompressCHDStage",
    "CompressArchiveStage",
    "CreateM3UStage",
    "GenerateMetadataStage",
    "OrganizeStage",
    "UnzipRVZStage",
    "TransformPS3Stage",
    "Pipeline",
    # Legacy models
    "CueSheet",
    "DiscMetadata",
    "FileTransformation",
    "TransformStatus",
    "TransformStep",
    "TransformType",
]
