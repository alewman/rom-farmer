"""
Kind-based ROM organizer.

Organizes ROMs by kind (Games, Demos, Betas, etc.) extracted from filenames.
Supports No-Intro naming conventions for various ROM types.
"""

from pathlib import Path
from typing import Optional, List, Dict
import re
import logging

from .base import BaseOrganizer, OrganizeMode

logger = logging.getLogger(__name__)


# Standard kind markers from No-Intro
KIND_MARKERS: Dict[str, List[str]] = {
    "Demo": ["Demo", "Kiosk"],
    "Beta": ["Beta", "Proto", "Prototype"],
    "Sample": ["Sample"],
    "Program": ["Program"],
    "Application": ["Application"],
    "Unlicensed": ["Unlicensed"],
    "Pirate": ["Pirate"],
    "Aftermarket": ["Aftermarket"],
    "Homebrew": ["Homebrew"],
    "Hack": ["Hack"],
    "Translation": ["T+", "T-"],  # Translation markers
    "Enhancement": ["Enhancement"],
}


class KindOrganizer(BaseOrganizer):
    """
    Organize ROMs by kind (type).
    
    Extracts kind information from ROM filenames and organizes them into
    kind-specific directories. Useful for separating games from demos,
    betas, prototypes, etc.
    
    Examples:
        >>> organizer = KindOrganizer(
        ...     mode=OrganizeMode.MOVE,
        ...     keep_in_place=['Demo', 'Beta']
        ... )
        >>> stats = organizer.organize(Path('/roms/nes'))
        
        # Results in:
        # /roms/nes/Super Mario Demo (USA) (Demo).nes       <- kept in place
        # /roms/nes/By Kind/Proto/Game (USA) (Proto).nes    <- organized
        # /roms/nes/By Kind/Homebrew/Game (Homebrew).nes    <- organized
    
    Args:
        mode: How to organize files (move, copy, or symlink)
        dry_run: Preview changes without actually making them
        keep_in_place: Kinds to keep in root directory
        exclude_kinds: Kinds to exclude from organization
        custom_markers: Additional kind markers to recognize
    """
    
    def __init__(
        self,
        mode: OrganizeMode = OrganizeMode.MOVE,
        dry_run: bool = False,
        keep_in_place: Optional[List[str]] = None,
        exclude_kinds: Optional[List[str]] = None,
        custom_markers: Optional[Dict[str, List[str]]] = None,
    ):
        super().__init__(
            mode=mode,
            dry_run=dry_run,
            keep_in_place=keep_in_place,
            exclude_values=exclude_kinds,
        )
        
        # Merge custom markers with standard ones
        self.kind_markers = KIND_MARKERS.copy()
        if custom_markers:
            self.kind_markers.update(custom_markers)
    
    def get_organization_dir_name(self) -> str:
        """Get the directory name for kind organization."""
        return "By Kind"
    
    def get_organization_value(self, filename: str) -> Optional[str]:
        """
        Extract kind from filename.
        
        Searches for kind markers in parentheses, brackets, or as standalone words.
        Supports formats like:
        - (Demo)
        - (Proto)
        - [Beta]
        - (T+Eng)  # Translation
        
        Args:
            filename: ROM filename
            
        Returns:
            Kind name, or None if not detected
        """
        # Pattern to match content in parentheses or brackets
        pattern = r'[\(\[]([^\)\]]+)[\)\]]'
        
        matches = re.findall(pattern, filename)
        
        if not matches:
            return None
        
        # Check each match for kind markers
        for match in matches:
            # Split by comma for multi-value entries
            parts = [p.strip() for p in match.split(',')]
            
            for part in parts:
                # Check each kind and its markers
                for kind, markers in self.kind_markers.items():
                    for marker in markers:
                        # Case-insensitive check
                        if marker.lower() in part.lower():
                            logger.debug(f"Detected kind: {kind} (marker: {marker})")
                            return kind
        
        return None
