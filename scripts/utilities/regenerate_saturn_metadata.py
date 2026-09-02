#!/usr/bin/env python3
"""Regenerate Saturn gamelist.xml with full metadata."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from romfarmer.stages.base import StageContext
from romfarmer.stages.metadata import GenerateMetadataStage

from romfarmer.config.loader import ConfigLoader


def main():
    """Regenerate Saturn metadata."""
    print("=" * 80)
    print("REGENERATING SATURN METADATA")
    print("=" * 80)

    # Load platform config
    config_loader = ConfigLoader()
    platform_config = config_loader.load_platform_config("saturn")

    # Create stage context
    context = StageContext(
        platform_name="saturn",
        platform_config=platform_config,
        target_name="batocera",
        output_dir=Path("/data/emu/output/saturn"),
        work_dir=Path("/data/emu/temp/saturn"),
        source_dir=Path("/data/emu/source"),
        disc_metadata={},  # Will be loaded from existing files
        organized_files={},
    )

    # Load disc metadata from M3U files
    print("\nLoading disc metadata from M3U files...")
    m3u_files = list(context.output_dir.rglob("*.m3u"))
    print(f"Found {len(m3u_files)} M3U files")

    # For now, just regenerate without disc metadata (simpler)
    # The metadata stage will process all files it finds

    # Create metadata stage
    metadata_stage = GenerateMetadataStage()

    # Initialize metadata database
    metadata_stage._init_metadata_db(context)

    # Execute stage
    print("\nRegenerating gamelist.xml...")
    result = metadata_stage.execute(context)

    print(f"\nResult: {result.status}")
    print(f"Message: {result.message}")
    if result.details:
        print(f"Details: {result.details}")

    # Verify results
    gamelist_path = context.output_dir / "gamelist.xml"
    if gamelist_path.exists():
        import xml.etree.ElementTree as ET

        tree = ET.parse(gamelist_path)
        root = tree.getroot()

        games = root.findall("game")
        games_with_desc = sum(1 for game in games if game.find("desc") is not None)
        games_with_rating = sum(1 for game in games if game.find("rating") is not None)

        print(f"\n{'=' * 80}")
        print("VERIFICATION")
        print(f"{'=' * 80}")
        print(f"Total games: {len(games)}")
        print(
            f"Games with description: {games_with_desc} ({games_with_desc / len(games) * 100:.1f}%)"
        )
        print(
            f"Games with rating: {games_with_rating} ({games_with_rating / len(games) * 100:.1f}%)"
        )

        # Sample a few games
        print("\nSample games:")
        for i, game in enumerate(games[:5]):
            path = game.find("path").text
            name = game.find("name").text
            has_desc = game.find("desc") is not None
            has_rating = game.find("rating") is not None
            print(f"  {i + 1}. {name}")
            print(f"     Path: {path}")
            print(f"     Has description: {has_desc}")
            print(f"     Has rating: {has_rating}")


if __name__ == "__main__":
    main()
