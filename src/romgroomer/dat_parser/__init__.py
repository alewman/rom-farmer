"""DAT file parsing system for ROM Groomer.

This module provides parsers for:
- Logiqx XML DAT format (standard No-Intro/Redump format)
- Retool-enhanced DATs (with <category> tags and pre-filtering)
- ROM filename matching and validation
- Hash-based ROM identification
"""

from .models import DATFile, DATGame, DATRom, DATType, ROMStatus
from .parser import DATParser, RetoolDATParser
from .matcher import ROMMatcher, MatchResult, MatchType

__all__ = [
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
