"""
Language-based ROM organizer.

Organizes ROMs by language extracted from filenames.
Supports No-Intro language codes.
"""

from pathlib import Path
from typing import Optional, List, Dict
import re
import logging

from .base import BaseOrganizer, OrganizeMode

logger = logging.getLogger(__name__)


# Standard language codes from No-Intro
LANGUAGE_CODES: Dict[str, str] = {
    "Ar": "Arabic",
    "Zh": "Chinese",
    "Cs": "Czech",
    "Da": "Danish",
    "Nl": "Dutch",
    "En": "English",
    "Fi": "Finnish",
    "Fr": "French",
    "De": "German",
    "El": "Greek",
    "He": "Hebrew",
    "Hu": "Hungarian",
    "It": "Italian",
    "Ja": "Japanese",
    "Ko": "Korean",
    "No": "Norwegian",
    "Pl": "Polish",
    "Pt": "Portuguese",
    "Ru": "Russian",
    "Es": "Spanish",
    "Sv": "Swedish",
    "Tr": "Turkish",
}


class LanguageOrganizer(BaseOrganizer):
    """
    Organize ROMs by language.
    
    Extracts language information from ROM filenames and creates language-specific
    directories. Typically used with symlinks to create virtual "By Language" folders
    without duplicating files.
    
    Examples:
        >>> organizer = LanguageOrganizer(
        ...     mode=OrganizeMode.SYMLINK,
        ...     exclude_languages=['En']  # English is default
        ... )
        >>> stats = organizer.organize(Path('/roms/nes'))
        
        # Results in:
        # /roms/nes/By Language/Japanese/
        # /roms/nes/By Language/French/
        # /roms/nes/By Language/German/
    
    Args:
        mode: How to organize files (typically SYMLINK)
        dry_run: Preview changes without actually making them
        language_priority: Preferred languages in order (for multi-language ROMs)
        keep_in_place: Languages to keep in root directory
        exclude_languages: Languages to exclude from organization
        use_full_names: Use full language names (e.g., "English") instead of codes ("En")
    """
    
    def __init__(
        self,
        mode: OrganizeMode = OrganizeMode.SYMLINK,
        dry_run: bool = False,
        language_priority: Optional[List[str]] = None,
        keep_in_place: Optional[List[str]] = None,
        exclude_languages: Optional[List[str]] = None,
        use_full_names: bool = True,
    ):
        # Store use_full_names first since we need it for exclude value conversion
        self.use_full_names = use_full_names
        self.language_priority = language_priority or ["En", "Es", "Fr", "De", "It", "Ja"]
        
        # Convert exclude_languages to full names if needed
        exclude_values = None
        if exclude_languages:
            if use_full_names:
                # Convert codes to full names for exclusion check
                exclude_values = []
                for lang in exclude_languages:
                    if lang in LANGUAGE_CODES:
                        exclude_values.append(LANGUAGE_CODES[lang])
                    else:
                        exclude_values.append(lang)  # Assume it's already a full name
            else:
                exclude_values = exclude_languages
        
        super().__init__(
            mode=mode,
            dry_run=dry_run,
            keep_in_place=keep_in_place,
            exclude_values=exclude_values,
        )
        
        # Validate language priority
        for lang in self.language_priority:
            if lang not in LANGUAGE_CODES:
                logger.warning(f"Unknown language code in priority list: {lang}")
    
    def get_organization_dir_name(self) -> str:
        """Get the directory name for language organization."""
        return "By Language"
    
    def get_organization_value(self, filename: str) -> Optional[str]:
        """
        Extract language from filename.
        
        Supports formats like:
        - (En)
        - (Ja)
        - (En,Fr)
        - (En,Fr,De)
        
        For multi-language ROMs, returns the highest priority language.
        
        Args:
            filename: ROM filename
            
        Returns:
            Language code or full name, or None if not detected
        """
        # Pattern to match content in parentheses
        pattern = r'\(([^)]+)\)'
        
        matches = re.findall(pattern, filename)
        
        if not matches:
            return None
        
        # Check each match for language codes
        detected_languages = []
        
        for match in matches:
            # Split by comma for multi-language entries
            parts = [p.strip() for p in match.split(',')]
            
            for part in parts:
                # Check if this part is a known language code
                if part in LANGUAGE_CODES:
                    detected_languages.append(part)
        
        if not detected_languages:
            return None
        
        # If multiple languages detected, use priority
        if len(detected_languages) > 1:
            logger.debug(f"Multi-language ROM detected: {detected_languages}")
            for priority_lang in self.language_priority:
                if priority_lang in detected_languages:
                    logger.debug(f"Selected language: {priority_lang} (priority)")
                    selected_lang = priority_lang
                    break
            else:
                # No priority match, use first detected
                selected_lang = detected_languages[0]
        else:
            selected_lang = detected_languages[0]
        
        # Return full name or code based on setting
        if self.use_full_names:
            return LANGUAGE_CODES[selected_lang]
        else:
            return selected_lang
