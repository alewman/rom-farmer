"""Utilities for generating descriptive output directory names.

Output directories are named based on the build configuration:
- Target platform (batocera, rpcs3, ps3netsrv)
- Region filter (usa, eur, jpn, world, all)
- DAT type (1g1r, all, etc.)
- Letter filter (A, B, C, ..., all)

Examples:
    batocera-usa-1g1r-A     → Batocera, USA only, 1G1R, A games
    rpcs3-eng-1g1r-all      → RPCS3, English, 1G1R, all letters
    ps3netsrv-usa-all-M     → PS3NetSrv, USA, all versions, M games
"""

from pathlib import Path
from typing import List, Optional


def generate_output_dirname(
    target_name: str,
    dat_name: Optional[str] = None,
    letter_filter: Optional[str] = None,
    region_filter: Optional[List[str]] = None,
    language_filter: Optional[List[str]] = None,
) -> str:
    """Generate descriptive output directory name.
    
    Args:
        target_name: Target platform (batocera, rpcs3, ps3netsrv)
        dat_name: DAT configuration name (retool_1g1r_usa, etc.)
        letter_filter: Letter filter (A, B, C, etc.)
        region_filter: Region tags (USA, EUR, JPN, World)
        language_filter: Language tags (En, Fr, De, etc.)
        
    Returns:
        Directory name string (e.g., "batocera-usa-1g1r-A")
    """
    parts = [target_name.lower()]
    
    # Extract region from filters or DAT name
    region_part = _extract_region(region_filter, dat_name)
    if region_part:
        parts.append(region_part)
    
    # Extract language if specified
    if language_filter:
        lang_part = _format_languages(language_filter)
        if lang_part:
            parts.append(lang_part)
    
    # Extract DAT type (1g1r, all, etc.)
    dat_part = _extract_dat_type(dat_name)
    if dat_part:
        parts.append(dat_part)
    
    # Add letter filter
    letter_part = letter_filter.upper() if letter_filter else "all"
    parts.append(letter_part)
    
    return "-".join(parts)


def _extract_region(
    region_filter: Optional[List[str]],
    dat_name: Optional[str]
) -> str:
    """Extract region identifier from filters or DAT name.
    
    Args:
        region_filter: Region filter list
        dat_name: DAT configuration name
        
    Returns:
        Region string (usa, eur, jpn, world, eng, all)
    """
    # Priority 1: Explicit region filter
    if region_filter:
        if len(region_filter) == 1:
            return region_filter[0].lower()
        else:
            # Multiple regions - use abbreviated form
            return "+".join(r[:3].lower() for r in region_filter)
    
    # Priority 2: Extract from DAT name
    if dat_name:
        dat_lower = dat_name.lower()
        if "usa" in dat_lower:
            return "usa"
        elif "eur" in dat_lower or "europe" in dat_lower:
            return "eur"
        elif "jpn" in dat_lower or "japan" in dat_lower:
            return "jpn"
        elif "eng" in dat_lower or "english" in dat_lower:
            return "eng"
        elif "world" in dat_lower:
            return "world"
        elif "all" in dat_lower:
            return "all"
    
    return "all"


def _format_languages(languages: List[str]) -> Optional[str]:
    """Format language filter into compact string.
    
    Args:
        languages: List of language codes
        
    Returns:
        Formatted language string or None
    """
    if not languages:
        return None
    
    if len(languages) == 1:
        return languages[0].lower()
    
    # Multiple languages - join with +
    return "+".join(lang.lower() for lang in languages)


def _extract_dat_type(dat_name: Optional[str]) -> str:
    """Extract DAT type from DAT name.
    
    Args:
        dat_name: DAT configuration name
        
    Returns:
        DAT type (1g1r, all, etc.)
    """
    if not dat_name:
        return "all"
    
    dat_lower = dat_name.lower()
    
    if "1g1r" in dat_lower:
        return "1g1r"
    elif "retool" in dat_lower:
        return "retool"
    elif "all" in dat_lower:
        return "all"
    
    return "custom"


def apply_output_naming(
    base_output_dir: Path,
    target_name: str,
    dat_name: Optional[str] = None,
    letter_filter: Optional[str] = None,
    region_filter: Optional[List[str]] = None,
    language_filter: Optional[List[str]] = None,
) -> Path:
    """Apply descriptive naming to output directory.
    
    Args:
        base_output_dir: Base output directory (e.g., /path/to/output/ps3)
        target_name: Target platform name
        dat_name: DAT configuration name
        letter_filter: Letter filter
        region_filter: Region filter
        language_filter: Language filter
        
    Returns:
        Full output directory path with descriptive name
        
    Example:
        >>> apply_output_naming(
        ...     Path("/path/to/output/ps3"),
        ...     "batocera",
        ...     "retool_1g1r_usa",
        ...     "A",
        ...     ["USA"],
        ...     None
        ... )
        PosixPath('/path/to/output/ps3/batocera-usa-1g1r-A')
    """
    dirname = generate_output_dirname(
        target_name=target_name,
        dat_name=dat_name,
        letter_filter=letter_filter,
        region_filter=region_filter,
        language_filter=language_filter,
    )
    
    return base_output_dir / dirname
