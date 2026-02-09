"""Arcade system support for ROM Farmer.

This module provides arcade-specific functionality:
- Clone classification (bootleg, hack, prototype, regional, etc.)
- 1G1R filtering for arcade systems
- Working game filtering based on driver status
"""

from .classifier import ArcadeClassifier, classify_arcade_game
from .filter import ArcadeFilter

__all__ = ["ArcadeClassifier", "ArcadeFilter", "classify_arcade_game"]
