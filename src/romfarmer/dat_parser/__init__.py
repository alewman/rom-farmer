"""DAT file parsing system for ROM Farmer.

This module provides parsers for:
- Logiqx XML DAT format (standard No-Intro/Redump format)
- Retool-enhanced DATs (with <category> tags and pre-filtering)
- ROM filename matching and validation
- Hash-based ROM identification
"""

from .clonelist import (
    DATDiffResult,
    DATRename,
    MetadataEntry,
    PatchAction,
    PatchResult,
    ValidationIssue,
    ValidationResult,
    clonelist_patch,
    clonelist_validate,
    dat_diff,
    metadata_generate,
    metadata_to_retool_json,
)
from .matcher import MatchResult, MatchType, ROMMatcher
from .models import DATDisk, DATFile, DATGame, DATRom, DATType, ROMStatus
from .parser import DATParser, RetoolDATParser

__all__ = [
    "DATDisk",
    "DATFile",
    "DATGame",
    "DATRom",
    "DATType",
    "ROMStatus",
    "DATParser",
    "RetoolDATParser",
    "ROMMatcher",
    "MatchResult",
    "MatchType",
    "dat_diff",
    "clonelist_validate",
    "clonelist_patch",
    "metadata_generate",
    "metadata_to_retool_json",
    "DATDiffResult",
    "DATRename",
    "ValidationResult",
    "ValidationIssue",
    "PatchResult",
    "PatchAction",
    "MetadataEntry",
]
