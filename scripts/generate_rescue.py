#!/usr/bin/env python3
"""Generate rescue lists for a generation via Copilot Router API."""
import asyncio
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Force unbuffered stdout
import functools
print = functools.partial(print, flush=True)



from romfarmer.ai.rescue_generator import RescueListGenerator
from romfarmer.cli.generation import (
    _find_duplicates, _enrich_with_metadata, _load_generations, RESCUE_DIR,
)

GEN = sys.argv[1] if len(sys.argv) > 1 else "gen6"

gens = _load_generations()
gen = gens[GEN]
platforms = [p["name"] for p in gen["platforms"]]
output_path = Path("roms-retrobat")

duplicates, platform_games = _find_duplicates(output_path, platforms)
print(f"Found {len(duplicates)} duplicates for {GEN}")

games = []
for mk, plats in duplicates.items():
    any_game = next(iter(plats.values()))
    games.append({"name": any_game.original_name, "platforms": sorted(plats.keys())})

games = _enrich_with_metadata(games)
enriched = sum(1 for g in games if g.get("metadata"))
print(f"Enriched {enriched}/{len(games)} games with metadata")

generator = RescueListGenerator(model="claude-haiku-4.5", batch_size=50)
result = asyncio.run(generator.generate_via_api(GEN, platforms, games))

RESCUE_DIR.mkdir(parents=True, exist_ok=True)
generator.save(result, RESCUE_DIR)

print(f"\nResults for {GEN}:")
print(f"  Total evaluated: {result.stats['total_evaluated']}")
print(f"  Total rescued: {result.stats['total_rescued']}")
print(f"  Rescue rate: {result.stats['rescue_rate']}")
for p, g in sorted(result.rescue_lists.items()):
    print(f"  {p}: {len(g)} games")
    for name in sorted(g):
        print(f"    - {name}")
