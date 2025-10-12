"""ROM processing system.

This module provides a flexible, multi-stage processing pipeline for ROM files.
Different ROM types (cartridges vs discs) and platforms (PS3 Batocera vs RPCS3)
can have completely different processing workflows.

Architecture:
    - ProcessingStage: Individual transformation step (extract, decrypt, convert)
    - PipelineProcessor: Orchestrates stages based on platform profile
    - PlatformProfile: Configuration defining which stages to run
    - ProcessedRom: Result of processing with metadata

Example:
    >>> from romgroomer.processors import get_processor, get_profile
    >>> from romgroomer.parsers import get_parser
    >>> 
    >>> # Parse ROM filename
    >>> parser = get_parser("nointro")
    >>> rom = parser.parse("Super Mario Bros (USA).zip")
    >>> 
    >>> # Get processor for this parser type
    >>> profile = get_profile("nes")
    >>> processor = get_processor(profile)
    >>> 
    >>> # Process the ROM
    >>> result = await processor.process(
    ...     input_path=Path("Super Mario Bros (USA).zip"),
    ...     output_dir=Path("/roms/nes/"),
    ...     rom=rom
    ... )
    >>> 
    >>> print(f"Output: {result.processed_path}")
    Output: /roms/nes/Super Mario Bros (USA).nes
"""

from .base import ProcessingStage, BaseProcessor, ProcessedRom
from .pipeline import PipelineProcessor
from .profiles import PlatformProfile, get_profile, list_profiles

__all__ = [
    "ProcessingStage",
    "BaseProcessor",
    "ProcessedRom",
    "PipelineProcessor",
    "PlatformProfile",
    "get_profile",
    "list_profiles",
]
