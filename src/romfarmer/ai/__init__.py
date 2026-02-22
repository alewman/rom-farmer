"""AI-powered curation and intelligence for ROM Farmer.

This package provides:
- GameRanker: Tiered game ranking using metadata + curated knowledge
- ListGenerator: Produces ranked game lists for build pipeline consumption
- CrossPlatformResolver: 1R1G (One ROM, One Generation) intelligence

The AI curator works in two modes:
1. **Static mode** (current): Agent generates ranked lists offline, stored as YAML.
   The build pipeline consumes them via ApplyListsStage or SelectionFilter.
2. **Live mode** (future): LLM is queried during build via Copilot SDK / API.
   Decisions are cached so subsequent builds are deterministic.
"""

from .curator import AICurator, GameTier, CuratedGame, PlatformCuration
from .generation import GenerationDefinition, CONSOLE_GENERATIONS

__all__ = [
    "AICurator",
    "GameTier",
    "CuratedGame",
    "PlatformCuration",
    "GenerationDefinition",
    "CONSOLE_GENERATIONS",
]
