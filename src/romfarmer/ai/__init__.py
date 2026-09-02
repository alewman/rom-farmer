"""AI-powered curation and intelligence for ROM Farmer.

This package provides:
- AICurator: Tiered game ranking using metadata + curated knowledge
- RescueListGenerator: AI-powered rescue list generation for 1G1Gen dedup
- GenerationDefinition: Console generation definitions with platform priorities

The AI curator works in two modes:
1. **Static mode**: Agent generates ranked lists offline, stored as YAML.
   The build pipeline consumes them via ApplyListsStage or SelectionFilter.
2. **Live mode**: Copilot SDK queries Haiku in batch to generate rescue lists
   for 1G1Gen cross-platform dedup. Results are cached as YAML so subsequent
   builds are deterministic (no AI call unless you force-regenerate).
"""

from .curator import AICurator, CuratedGame, GameTier, PlatformCuration
from .generation import CONSOLE_GENERATIONS, GenerationDefinition
from .rescue_generator import RescueListGenerator, generate_rescue_lists

__all__ = [
    "AICurator",
    "GameTier",
    "CuratedGame",
    "PlatformCuration",
    "GenerationDefinition",
    "CONSOLE_GENERATIONS",
    "RescueListGenerator",
    "generate_rescue_lists",
]
