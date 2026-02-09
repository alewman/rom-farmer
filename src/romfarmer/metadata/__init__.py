"""
Metadata management for ROM collections.

This module handles scraped game metadata and media files from sources like
ScreenScraper.fr (via ARRM) and provides deduplication and regeneration capabilities.
"""

from .database import MetadataDatabase, ScrapedGame, MediaFile, GameMediaLink
from .transformation import ROMTransformation, HashCache
from .arrm import ARRMImporter
from .generator import GamelistGenerator
from .dat_manager import DATManager, DATEntry
from .hash_capture import SmartHashCapture, SourceHashInfo
from .transformation_recorder import TransformationRecorder, TransformationContext

__all__ = [
    "MetadataDatabase",
    "ScrapedGame",
    "MediaFile",
    "GameMediaLink",
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
]
