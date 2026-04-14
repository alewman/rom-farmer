"""
ROM organization system.

This module provides organizers for structuring ROM collections by various criteria:
- RegionOrganizer: Organize by region (USA, Europe, Japan, etc.)
- KindOrganizer: Organize by kind (Games, Demos, Betas, etc.)
- LanguageOrganizer: Organize by language (English, Japanese, etc.)
- AlphabeticalOrganizer: Split into letter groups (Everdrive/flashcart)
"""

from .base import BaseOrganizer, OrganizeMode
from .region import RegionOrganizer
from .kind import KindOrganizer
from .language import LanguageOrganizer
from .alphabetical import AlphabeticalOrganizer

__all__ = [
    "BaseOrganizer",
    "OrganizeMode",
    "RegionOrganizer",
    "KindOrganizer",
    "LanguageOrganizer",
    "AlphabeticalOrganizer",
]
