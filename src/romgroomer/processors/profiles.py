"""Platform profiles for ROM processing.

A profile defines the complete processing pipeline for a specific platform
and emulator combination. Different emulators for the same system may need
different profiles (e.g., PS3 Batocera vs RPCS3).
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PlatformProfile:
    """Configuration for platform-specific processing.
    
    Attributes:
        name: Unique profile identifier (e.g., 'nes', 'ps3_batocera')
        description: Human-readable description
        parser_type: Parser to use ('nointro', 'redump', etc.)
        stages: List of stage names to execute in order
        output_format: Expected output format (e.g., '.nes', '.chd', '.sqfs')
        stage_config: Stage-specific configuration
        
    Example:
        >>> profile = PlatformProfile(
        ...     name="nes",
        ...     description="Nintendo Entertainment System",
        ...     parser_type="nointro",
        ...     stages=["extract_archive"],
        ...     output_format=".nes",
        ... )
    """
    
    name: str
    description: str
    parser_type: str
    stages: list[str]
    output_format: str
    stage_config: dict[str, dict] = field(default_factory=dict)


# ============================================================================
# CARTRIDGE PROFILES (Simple - just extraction)
# ============================================================================

PROFILE_NES = PlatformProfile(
    name="nes",
    description="Nintendo Entertainment System",
    parser_type="nointro",
    stages=["extract_archive"],
    output_format=".nes",
)

PROFILE_SNES = PlatformProfile(
    name="snes",
    description="Super Nintendo Entertainment System",
    parser_type="nointro",
    stages=["extract_archive"],
    output_format=".sfc",
)

PROFILE_GB = PlatformProfile(
    name="gb",
    description="Game Boy",
    parser_type="nointro",
    stages=["extract_archive"],
    output_format=".gb",
)

PROFILE_GBC = PlatformProfile(
    name="gbc",
    description="Game Boy Color",
    parser_type="nointro",
    stages=["extract_archive"],
    output_format=".gbc",
)

PROFILE_GBA = PlatformProfile(
    name="gba",
    description="Game Boy Advance",
    parser_type="nointro",
    stages=["extract_archive"],
    output_format=".gba",
)

PROFILE_NDS = PlatformProfile(
    name="nds",
    description="Nintendo DS",
    parser_type="nointro",
    stages=["extract_archive"],
    output_format=".nds",
)

PROFILE_GENESIS = PlatformProfile(
    name="genesis",
    description="Sega Genesis / Mega Drive",
    parser_type="nointro",
    stages=["extract_archive"],
    output_format=".md",
)

PROFILE_GG = PlatformProfile(
    name="gamegear",
    description="Sega Game Gear",
    parser_type="nointro",
    stages=["extract_archive"],
    output_format=".gg",
)

# ============================================================================
# DISC PROFILES (with CHD conversion and M3U playlists)
# ============================================================================

PROFILE_PSX = PlatformProfile(
    name="psx",
    description="PlayStation 1",
    parser_type="redump",
    stages=["extract_archive", "bin_cue_to_chd", "create_m3u_playlist"],
    output_format=".chd",  # or .m3u for multi-disc
)

PROFILE_SEGACD = PlatformProfile(
    name="segacd",
    description="Sega CD / Mega CD",
    parser_type="redump",
    stages=["extract_archive", "bin_cue_to_chd", "create_m3u_playlist"],
    output_format=".chd",
)

PROFILE_PCENGINECD = PlatformProfile(
    name="pcenginecd",
    description="PC Engine CD / TurboGrafx-CD",
    parser_type="redump",
    stages=["extract_archive", "bin_cue_to_chd", "create_m3u_playlist"],
    output_format=".chd",
)


# ============================================================================
# PROFILE REGISTRY
# ============================================================================

_PROFILES: dict[str, PlatformProfile] = {
    # Cartridge systems
    "nes": PROFILE_NES,
    "snes": PROFILE_SNES,
    "gb": PROFILE_GB,
    "gbc": PROFILE_GBC,
    "gba": PROFILE_GBA,
    "nds": PROFILE_NDS,
    "genesis": PROFILE_GENESIS,
    "gamegear": PROFILE_GG,
    
    # Disc systems (basic for now)
    "psx": PROFILE_PSX,
    "segacd": PROFILE_SEGACD,
    "pcenginecd": PROFILE_PCENGINECD,
}


def get_profile(name: str) -> PlatformProfile:
    """Get a platform profile by name.
    
    Args:
        name: Profile name (e.g., 'nes', 'psx', 'ps3_batocera')
        
    Returns:
        PlatformProfile instance
        
    Raises:
        ValueError: If profile not found
        
    Example:
        >>> profile = get_profile('nes')
        >>> print(profile.description)
        Nintendo Entertainment System
    """
    if name not in _PROFILES:
        available = ", ".join(sorted(_PROFILES.keys()))
        raise ValueError(
            f"Unknown profile: {name}\n"
            f"Available profiles: {available}"
        )
    return _PROFILES[name]


def list_profiles(system: Optional[str] = None) -> list[PlatformProfile]:
    """List available profiles.
    
    Args:
        system: Optional system filter (e.g., 'ps3' returns ps3_* profiles)
        
    Returns:
        List of PlatformProfile instances
        
    Example:
        >>> profiles = list_profiles()
        >>> for p in profiles:
        ...     print(f"{p.name}: {p.description}")
        nes: Nintendo Entertainment System
        snes: Super Nintendo Entertainment System
        ...
    """
    if system:
        return [p for name, p in _PROFILES.items() if name.startswith(system)]
    return list(_PROFILES.values())


def register_profile(profile: PlatformProfile) -> None:
    """Register a new platform profile.
    
    Args:
        profile: PlatformProfile to register
        
    Example:
        >>> custom_profile = PlatformProfile(
        ...     name="custom_system",
        ...     description="My Custom System",
        ...     parser_type="nointro",
        ...     stages=["extract_archive"],
        ...     output_format=".rom",
        ... )
        >>> register_profile(custom_profile)
    """
    _PROFILES[profile.name] = profile
