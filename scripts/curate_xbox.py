#!/usr/bin/env python3
"""AI-curated Xbox game rankings.

Only 68 games in the 1G1R set — this is already a tight collection.
Most of these are genuinely good games, so the tier distribution is top-heavy.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from romfarmer.ai.curator import AICurator, CuratedGame, GameTier, PlatformCuration


def extract_core_title(filename: str) -> str:
    """Extract core title, handling Redump article format."""
    core = re.sub(r"\s*\(.*", "", filename)
    article_match = re.match(
        r"^(.*?),\s+(The|A|An|La|Le|Les|El|Los|Las|Der|Die|Das)(?:\s+(.*))?$", core, re.IGNORECASE
    )
    if article_match:
        rest = article_match.group(3) or ""
        if rest:
            core = f"{article_match.group(2)} {article_match.group(1)} {rest}"
        else:
            core = f"{article_match.group(2)} {article_match.group(1)}"
    return core.strip().lower()


# Xbox has only 68 games — curate them all manually
ESSENTIAL_TITLES = {
    "halo - combat evolved": "Defined the Xbox. Defined console FPS. Iconic.",
    "halo 2": "Revolutionized online console gaming. Legendary multiplayer.",
    "the elder scrolls iii - morrowind": "Open-world RPG masterpiece. Best on Xbox.",
    "fable - the lost chapters": "Molyneux's charming RPG. Definitive version.",
    "star wars - knights of the old republic": "Best Star Wars RPG ever made. BioWare classic.",
    "ninja gaiden black": "Hardest, best action game of its gen. Itagaki's opus.",
    "half-life 2": "One of the greatest FPS ever. Console port was excellent.",
    "jade empire": "BioWare martial arts RPG. Unique setting.",
    "the chronicles of riddick - escape from butcher bay": "Best movie tie-in ever. Stealth-FPS perfection.",
    "panzer dragoon orta": "Gorgeous rail shooter. Sega's swan song on non-Sega hardware.",
    "psychonauts": "Tim Schafer's masterpiece. Better than PS2 version.",
}

EXCELLENT_TITLES = {
    "star wars - knights of the old republic ii - the sith lords": "Obsidian's darker, deeper sequel.",
    "conker - live & reloaded": "Rare's adult platformer remake. Gorgeous.",
    "jsrf - jet set radio future": "Cel-shaded inline skating. Hideki Naganuma soundtrack.",
    "oddworld - stranger's wrath": "Unique FPS-platformer hybrid. Underrated gem.",
    "crimson skies - high road to revenge": "Arcade dogfighting perfection.",
    "prince of persia - the sands of time": "Time rewind platforming. Multi-platform classic.",
    "beyond good & evil": "Cult classic investigation-adventure.",
    "ninja gaiden": "Original before Black. Still incredible.",
    "forza motorsport & xbox live arcade": "Started the Forza dynasty.",
    "project gotham racing 2": "Best Xbox racer. Photo mode pioneer.",
    "tom clancy's splinter cell - chaos theory": "Peak stealth gaming.",
    "doom 3": "id Software horror FPS. Xbox port was impressive.",
    "burnout 3 - takedown": "Best arcade racer. Crash mode.",
    "timesplitters 2": "Goldeneye spiritual successor.",
    "timesplitters - future perfect": "More TS fun. Great campaign.",
    "mechassault": "Mech combat. Xbox Live launch title.",
    "soulcalibur ii": "Great fighting game. Spawn as guest character!",
    "baldur's gate - dark alliance": "Hack-and-slash co-op classic.",
    "baldur's gate - dark alliance ii": "More co-op dungeon crawling.",
    "max payne": "Bullet time noir. Iconic.",
    "need for speed - most wanted": "Police chases. Open world racing.",
    "burnout revenge": "Traffic checking. Great arcade racing.",
    "dead or alive 3": "Team Ninja fighting. Xbox showcase.",
    "tom clancy's splinter cell": "Started the stealth franchise.",
}

GREAT_TITLES = {
    "project gotham racing": "Xbox launch racer. Kudos system.",
    "tom clancy's splinter cell - double agent": "Moral choice Splinter Cell.",
    "tom clancy's ghost recon - advanced warfighter": "Tactical shooter. Next-gen feel.",
    "tom clancy's ghost recon": "Original tactical shooter.",
    "call of duty 3": "Decent WW2 FPS.",
    "battlefield 2 - modern combat": "Multiplayer focused FPS.",
    "nba street vol. 2": "Arcade basketball perfection.",
    "tony hawk's pro skater 3": "Peak THPS.",
    "tony hawk's pro skater 2x": "THPS1+2 compilation. Great value.",
    "ssx tricky": "Snowboarding fun.",
    "fight night round 3": "Boxing game. Total Punch Control.",
    "lara croft tomb raider - legend": "Tomb Raider reborn.",
    "blitz - the league": "Arcade football. Midway style.",
}

# Everything else is Notable (sports franchises, demos, etc.)


def load_filenames(filepath: str) -> list[str]:
    with open(filepath) as f:
        return [line.strip() for line in f if line.strip()]


def build_curation() -> PlatformCuration:
    filenames = load_filenames("/tmp/xbox_all.txt")

    ess = {k.lower(): v for k, v in ESSENTIAL_TITLES.items()}
    exc = {k.lower(): v for k, v in EXCELLENT_TITLES.items()}
    grt = {k.lower(): v for k, v in GREAT_TITLES.items()}

    games = []
    unmatched_ess = set(ess.keys())
    unmatched_exc = set(exc.keys())
    unmatched_grt = set(grt.keys())

    for fname in filenames:
        core = extract_core_title(fname)

        if core in ess:
            tier, score, note, tags = GameTier.ESSENTIAL, 95, ess[core], ["essential"]
            unmatched_ess.discard(core)
        elif core in exc:
            tier, score, note, tags = GameTier.EXCELLENT, 80, exc[core], ["excellent"]
            unmatched_exc.discard(core)
        elif core in grt:
            tier, score, note, tags = GameTier.GREAT, 65, grt[core], ["great"]
            unmatched_grt.discard(core)
        else:
            tier, score, note, tags = GameTier.NOTABLE, 50, "", ["notable"]

        games.append(CuratedGame(name=fname, tier=tier, score=score, note=note, tags=tags))

    curation = PlatformCuration(
        platform="xbox",
        version="1.0.0",
        curator="ai-frontier-claude-opus",
        games=games,
        generation="gen6",
        total_available=len(filenames),
        metadata={
            "source": "redump-1g1r-eng-chd-batocera-v2",
            "notes": "AI-curated by Claude Opus. Small collection (68 games) so most are Notable+.",
        },
    )

    print(f"\n{'=' * 60}")
    print("Xbox AI Curation Report")
    print(f"{'=' * 60}")
    print(f"Total games: {len(filenames)}")
    for tier in GameTier:
        count = len(curation.by_tier(tier))
        if count > 0:
            print(f"  {tier.label:12s}: {count:3d} ({count / len(filenames) * 100:5.1f}%)")

    if unmatched_ess:
        print(f"\n  WARN: {len(unmatched_ess)} Essential unmatched: {sorted(unmatched_ess)}")
    if unmatched_exc:
        print(f"\n  WARN: {len(unmatched_exc)} Excellent unmatched: {sorted(unmatched_exc)}")
    if unmatched_grt:
        print(f"\n  WARN: {len(unmatched_grt)} Great unmatched: {sorted(unmatched_grt)}")

    return curation


if __name__ == "__main__":
    curator = AICurator()
    curation = build_curation()

    path = curator.save_curation(curation)
    print(f"\nSaved curation to: {path}")

    for tier in [GameTier.ESSENTIAL, GameTier.EXCELLENT, GameTier.GREAT]:
        list_path = curator.generate_list_file("xbox", max_tier=tier)
        if list_path:
            count = len(curation.up_to_tier(tier))
            print(f"Generated list ({tier.value}): {list_path} ({count} games)")

    print("\nDone!")
