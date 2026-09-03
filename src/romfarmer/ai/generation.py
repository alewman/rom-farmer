"""Compatibility re-export — the generation table now lives in ``romfarmer.config.console_generations``."""

from __future__ import annotations

from romfarmer.config.console_generations import (
    CONSOLE_GENERATIONS,
    GenerationDefinition,
    find_platform_generation,
    get_all_platforms_with_generation,
    get_generation,
)

__all__ = [
    "CONSOLE_GENERATIONS",
    "GenerationDefinition",
    "find_platform_generation",
    "get_all_platforms_with_generation",
    "get_generation",
]
