"""
Metadata management for ROM collections.

This module handles scraped game metadata and media files from sources like
ScreenScraper.fr (via ARRM) and provides deduplication and regeneration capabilities.
"""

from .arrm import ARRMImporter
from .dat_manager import DATEntry, DATManager
from .database import ExternalScore, GameMediaLink, MediaFile, MetadataDatabase, ScrapedGame
from .external_scores import MOBYGAMES_PLATFORM_IDS, MobyGamesFetcher, RawgFetcher, normalize_title
from .generator import GamelistGenerator
from .hash_capture import SmartHashCapture, SourceHashInfo
from .transformation import HashCache, ROMTransformation
from .transformation_recorder import TransformationContext, TransformationRecorder

__all__ = [
    "MetadataDatabase",
    "ScrapedGame",
    "MediaFile",
    "GameMediaLink",
    "ExternalScore",
    "ROMTransformation",
    "HashCache",
    "ARRMImporter",
    "GamelistGenerator",
    "DATManager",
    "DATEntry",
    "SmartHashCapture",
    "SourceHashInfo",
    "TransformationRecorder",
    "TransformationContext",
    "MobyGamesFetcher",
    "RawgFetcher",
    "normalize_title",
    "MOBYGAMES_PLATFORM_IDS",
]
