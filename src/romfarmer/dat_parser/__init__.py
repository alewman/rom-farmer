"""DAT file parsing system for ROM Farmer.

This module provides parsers for:
- Logiqx XML DAT format (standard No-Intro/Redump format)
- Retool-enhanced DATs (with <category> tags and pre-filtering)
- ROM filename matching and validation
- Hash-based ROM identification
"""

from .models import DATDisk, DATFile, DATGame, DATRom, DATType, ROMStatus
from .parser import DATParser, RetoolDATParser
from .matcher import ROMMatcher, MatchResult, MatchType

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
]
