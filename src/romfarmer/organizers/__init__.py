"""
ROM organization system.

This module provides organizers for structuring ROM collections by various criteria:
- RegionOrganizer: Organize by region (USA, Europe, Japan, etc.)
- KindOrganizer: Organize by kind (Games, Demos, Betas, etc.)
- LanguageOrganizer: Organize by language (English, Japanese, etc.)
- AlphabeticalOrganizer: Split into letter groups (Everdrive/flashcart)
- GenreOrganizer: Organize by genre (Action, RPG, Sports, etc.) via metadata DB
"""

from .alphabetical import AlphabeticalOrganizer
from .base import BaseOrganizer, OrganizeMode
from .genre import GenreOrganizer
from .kind import KindOrganizer
from .language import LanguageOrganizer
from .region import RegionOrganizer

__all__ = [
    "BaseOrganizer",
    "OrganizeMode",
    "RegionOrganizer",
    "KindOrganizer",
    "LanguageOrganizer",
    "AlphabeticalOrganizer",
    "GenreOrganizer",
]
