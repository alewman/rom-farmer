"""Console generation definitions for 1R1G cross-platform deduplication.

Each generation defines:
- The platforms in that generation
- Priority order (first = keep, rest = exclusives only)
- Platform capability mappings for the target system

Priority is based on: library quality, emulation accuracy, and community
consensus for "definitive version" of cross-platform games.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GenerationDefinition:
    """A console generation for cross-platform deduplication.
    
    Attributes:
        name: Generation identifier (gen3, gen4, gen5, etc.)
        label: Human-readable label
        era: Approximate year range
        platforms: Platform names in priority order (first = highest priority).
                   These must match ROM Farmer platform directory names.
        notes: Per-platform notes explaining priority decisions
    """
    name: str
    label: str
    era: str
    platforms: list[str]
    notes: dict[str, str] = field(default_factory=dict)
    
    @property
    def primary(self) -> str:
        """The highest priority platform (keeper for duplicates)."""
        return self.platforms[0]
    
    @property
    def secondary(self) -> list[str]:
        """Lower priority platforms (become exclusives-only)."""
        return self.platforms[1:]
    
    def platform_rank(self, platform: str) -> Optional[int]:
        """Get priority rank (0=highest). None if not in this generation."""
        try:
            return self.platforms.index(platform)
        except ValueError:
            return None


# ---------------------------------------------------------------------------
# Console generation definitions
# ---------------------------------------------------------------------------
# Priority rationale for each generation:
# - "Definitive version" community consensus
# - Emulation maturity and accuracy on x86_64 Batocera
# - Library size (larger library = more exclusives to preserve)
#
# For 1R1G: the PRIMARY platform keeps ALL its games.
# Secondary platforms keep only exclusives (games not on primary).
# This saves enormous space on cross-platform generations.
# ---------------------------------------------------------------------------

CONSOLE_GENERATIONS: list[GenerationDefinition] = [
    GenerationDefinition(
        name="gen3",
        label="8-bit Era",
        era="1983-1992",
        platforms=["nes", "mastersystem", "atari7800", "sg1000"],
        notes={
            "nes": "Largest library, best emulation, definitive 8-bit platform",
            "mastersystem": "Strong European library, good exclusives",
            "atari7800": "Small library, unique backward compat titles",
            "sg1000": "Niche, mostly Japan-only",
        },
    ),
    GenerationDefinition(
        name="gen4",
        label="16-bit Era",
        era="1988-1996",
        platforms=["snes", "megadrive", "pcengine", "supergrafx"],
        notes={
            "snes": "Strongest RPG/platformer library, definitive 16-bit",
            "megadrive": "Strong action/sports library, excellent exclusives",
            "pcengine": "Best shmup library, strong Japan exclusives",
            "supergrafx": "Tiny library (7 games), all exclusive to platform",
        },
    ),
    GenerationDefinition(
        name="gen5",
        label="32/64-bit Era", 
        era="1993-2000",
        platforms=["psx", "saturn"],
        notes={
            "psx": "Largest library in history, definitive gen5 platform",
            "saturn": "Best 2D library, strong Japan exclusives, arcade ports",
            # N64 deliberately excluded: tiny cart-based library, no meaningful
            # cross-platform overlap worth deduplicating.
            # 3DO excluded: tiny library, minimal overlap.
        },
    ),
    GenerationDefinition(
        name="gen5_handheld",
        label="Gen 5 Handhelds",
        era="1989-2003",
        platforms=["gbc", "gba", "gamegear", "ngpc", "wswan", "wswanc"],
        notes={
            "gbc": "Largest handheld library of era, backward compat with GB",
            "gba": "32-bit handheld, many SNES-quality exclusives",
            "gamegear": "Sega's handheld, strong Sonic/Sega exclusives",
            "ngpc": "Tiny gem library — fighting games masterclass",
            "wswan": "Japan-only, some unique RPGs",
            "wswanc": "WonderSwan Color — enhanced Japan-only titles",
        },
    ),
    GenerationDefinition(
        name="gen6",
        label="128-bit Era",
        era="2000-2005",
        platforms=["ps2", "dreamcast", "xbox"],
        notes={
            "ps2": "Largest console library ever. Best RPG/action catalog",
            "dreamcast": "Died young but legendary library. Best arcade ports (Naomi)",
            "xbox": "Strongest Western exclusives (Halo, Knights of the Old Republic)",
        },
    ),
    GenerationDefinition(
        name="gen6_handheld",
        label="Gen 6 Handhelds",
        era="2001-2010",
        platforms=["nds", "psp"],
        notes={
            "nds": "Massive library, touch-screen exclusives, backward compat GBA",
            "psp": "Console-quality handheld, strong RPG/action library",
        },
    ),
    GenerationDefinition(
        name="portable",
        label="Dedicated Portables",
        era="1989-2017",
        platforms=["gb", "gbc", "gba", "nds", "3ds"],
        notes={
            "gb": "The original Game Boy — foundational handheld titles",
            "gbc": "Enhanced GB with color",
            "gba": "32-bit handheld golden age",
            "nds": "Dual-screen innovation, huge library",
            "3ds": "Most recent dedicated Nintendo handheld",
        },
    ),
    # Arcade generations aren't cross-platform in the same way —
    # arcade ports to consoles are different enough to both merit inclusion.
    # But MAME vs FBNeo IS a dedup target.
    GenerationDefinition(
        name="arcade",
        label="Arcade",
        era="1970-2010",
        platforms=["mame", "fbneo", "naomi", "naomi2", "atomiswave", 
                   "model2", "model3", "namco246", "triforce"],
        notes={
            "mame": "Most comprehensive, definitive arcade platform",
            "fbneo": "Alternative emulator, some games better here",
            "naomi": "Sega arcade board — Dreamcast sibling",
            "naomi2": "Enhanced Naomi — Virtua Fighter 4, etc.",
            "atomiswave": "Later Sega arcade board",
            "model2": "Sega Model 2 — Daytona USA, Virtua Fighter 2",
            "model3": "Sega Model 3 — Virtua Fighter 3, Daytona 2",
            "namco246": "Namco System 246 — PS2-based arcade",
            "triforce": "Nintendo/Sega/Namco GameCube-based arcade",
        },
    ),
]


def get_generation(name: str) -> Optional[GenerationDefinition]:
    """Look up a generation by name."""
    for gen in CONSOLE_GENERATIONS:
        if gen.name == name:
            return gen
    return None


def find_platform_generation(platform: str) -> Optional[GenerationDefinition]:
    """Find which generation a platform belongs to (first match)."""
    for gen in CONSOLE_GENERATIONS:
        if platform in gen.platforms:
            return gen
    return None


def get_all_platforms_with_generation() -> dict[str, GenerationDefinition]:
    """Map every platform to its generation."""
    result = {}
    for gen in CONSOLE_GENERATIONS:
        for platform in gen.platforms:
            if platform not in result:  # First match wins
                result[platform] = gen
    return result
