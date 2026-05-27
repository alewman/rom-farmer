#!/usr/bin/env python3
"""Generate AI-powered rescue lists for 1G1Gen cross-platform deduplication.

This tool queries the Copilot SDK (Claude Haiku) to identify games where a
non-primary platform has the definitively superior version, overriding
the deterministic priority system.

Usage:
    # Generate rescue lists for gen6 (PS2 > GC > Xbox > DC)
    python -m romfarmer.ai.rescue_generator_cli gen6

    # Generate for gen5 (PSX > Saturn)
    python -m romfarmer.ai.rescue_generator_cli gen5

    # Force regenerate (ignore cache)
    python -m romfarmer.ai.rescue_generator_cli gen6 --force

    # Dry run — show duplicates without calling AI
    python -m romfarmer.ai.rescue_generator_cli gen6 --dry-run

    # Use specific build output to find real duplicates
    python -m romfarmer.ai.rescue_generator_cli gen6 --output-dir output/redump-1g1r-eng-chd-batocera-v2
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Ensure rom-farmer src is importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from romfarmer.ai.generation import CONSOLE_GENERATIONS, get_generation
from romfarmer.ai.rescue_generator import (
    RescueListGenerator,
    RescueListResult,
    generate_rescue_lists,
)
from romfarmer.cross_platform.game_normalizer import GameNameNormalizer

logger = logging.getLogger(__name__)

def _get_workspace_root() -> Path:
    from romfarmer.core.paths import paths
    return paths.workspace_root

WORKSPACE_ROOT: Path  # resolved lazily via _get_workspace_root()


def find_cross_platform_duplicates(
    generation_name: str,
    output_dir: Path | None = None,
) -> tuple[list[str], list[dict[str, list[str]]]]:
    """Scan build output to find actual cross-platform duplicate games.

    Args:
        generation_name: e.g. "gen6"
        output_dir: Build output directory containing platform subdirs.
                    If None, scans all output/ dirs for matching platforms.

    Returns:
        Tuple of (platform_priority, duplicate_games).
        duplicate_games is list of {"name": str, "platforms": [str, ...]}.
    """
    gen = get_generation(generation_name)
    if not gen:
        print(f"ERROR: Unknown generation: {generation_name}")
        print(f"Available: {', '.join(g.name for g in CONSOLE_GENERATIONS)}")
        sys.exit(1)

    platforms = gen.platforms
    normalizer = GameNameNormalizer()

    # Find platform directories in build output
    if output_dir:
        search_dirs = [output_dir]
    else:
        # Scan all output directories
        output_base = _get_workspace_root() / "output"
        search_dirs = [d for d in output_base.iterdir() if d.is_dir()] if output_base.exists() else []

    # Collect normalized game names per platform
    from collections import defaultdict
    platform_games: dict[str, dict[str, str]] = {}  # platform -> {match_key: original_name}

    for search_dir in search_dirs:
        for platform in platforms:
            platform_dir = search_dir / platform
            if not platform_dir.exists():
                continue

            if platform not in platform_games:
                platform_games[platform] = {}

            # Find game files
            for pattern in ['*.chd', '*.rvz', '*.iso', '*.xiso', '*.cue', '*.7z',
                            '*.zip', '*.m3u', '*.cso', '*.pbp']:
                for f in platform_dir.glob(pattern):
                    norm = normalizer.normalize(f.stem, platform, str(f))
                    key = norm.match_key()
                    if key not in platform_games[platform]:
                        platform_games[platform][key] = f.stem

    if not platform_games:
        print(f"No platform directories found for {generation_name} in output/")
        print(f"Looking for: {', '.join(platforms)}")
        return platforms, []

    print(f"\nPlatforms found:")
    for p in platforms:
        count = len(platform_games.get(p, {}))
        marker = " (primary)" if p == platforms[0] else ""
        print(f"  {p:15s}: {count:5d} games{marker}")

    # Find games on 2+ platforms
    all_keys: dict[str, dict[str, str]] = defaultdict(dict)  # match_key -> {platform: name}
    for platform, games in platform_games.items():
        for key, name in games.items():
            all_keys[key][platform] = name

    duplicates = []
    for key, plats in sorted(all_keys.items()):
        if len(plats) >= 2:
            # Use the name from the primary platform if available
            primary_name = None
            for p in platforms:
                if p in plats:
                    primary_name = plats[p]
                    break
            duplicates.append({
                "name": primary_name or list(plats.values())[0],
                "platforms": list(plats.keys()),
            })

    print(f"\nCross-platform duplicates: {len(duplicates)}")

    return platforms, duplicates


async def run_generate(args: argparse.Namespace) -> None:
    """Run the rescue list generation."""
    platforms, duplicates = find_cross_platform_duplicates(
        args.generation,
        Path(args.output_dir) if args.output_dir else None,
    )

    if not duplicates:
        print("No duplicates found. Nothing to do.")
        return

    if args.dry_run:
        print(f"\n[DRY RUN] Would evaluate {len(duplicates)} games")
        print(f"Primary platform: {platforms[0]}")
        print(f"\nSample duplicates:")
        for d in duplicates[:20]:
            print(f"  {d['name']:50s} — {', '.join(d['platforms'])}")
        if len(duplicates) > 20:
            print(f"  ... and {len(duplicates) - 20} more")
        return

    cache_dir = WORKSPACE_ROOT / "config" / "curations" / "rescue"

    rescue_lists = await generate_rescue_lists(
        generation_name=args.generation,
        platform_priority=platforms,
        duplicate_games=duplicates,
        model=args.model,
        cache_dir=cache_dir,
        force_regenerate=args.force,
    )

    # Summary
    total_rescued = sum(len(v) for v in rescue_lists.values())
    print(f"\n{'=' * 60}")
    print(f"RESCUE LIST SUMMARY: {args.generation}")
    print(f"{'=' * 60}")
    print(f"Total cross-platform duplicates: {len(duplicates)}")
    print(f"Total rescued (kept on non-primary): {total_rescued}")
    print(f"Rescue rate: {total_rescued / max(len(duplicates), 1) * 100:.1f}%")
    print()
    for platform, games in sorted(rescue_lists.items()):
        print(f"  {platform} ({len(games)} rescued):")
        for g in sorted(games)[:10]:
            print(f"    - {g}")
        if len(games) > 10:
            print(f"    ... and {len(games) - 10} more")
    print(f"\nSaved to: {cache_dir / f'rescue-{args.generation}.yaml'}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate AI-powered rescue lists for 1G1Gen deduplication"
    )
    parser.add_argument(
        "generation",
        help="Generation name (gen4cd, gen5, gen6, gen7)",
    )
    parser.add_argument(
        "--output-dir",
        help="Build output directory with platform subdirs (default: scan all output/)",
    )
    parser.add_argument(
        "--model",
        default="claude-haiku-4.5",
        help="Copilot model to use (default: claude-haiku-4.5)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force regeneration (ignore cache)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show duplicates without calling AI",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose logging",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    asyncio.run(run_generate(args))


if __name__ == "__main__":
    main()
