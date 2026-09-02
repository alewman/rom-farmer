#!/usr/bin/env python3
"""AI-curated PS2 game rankings.

Uses fuzzy matching (core title extraction) to match curated entries
against actual 1G1R filenames with version tags, language codes, etc.

Tier system:
  ESSENTIAL (Tier 1): Platform-defining. Everyone should play these.
  EXCELLENT (Tier 2): Outstanding games. Strong recommend.
  GREAT (Tier 3): Very good. Worth including in any serious collection.
  NOTABLE (Tier 4): Good games, worth including with space.
  COMPLETE (Tier 5): Everything else in the 1G1R set.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from romfarmer.ai.curator import AICurator, CuratedGame, GameTier, PlatformCuration


def extract_core_title(filename: str) -> str:
    """Extract the core game title from a Redump-style filename.

    Strips region codes, version info, language tags, disc info, etc.
    Handles Redump article-trailing format:
    "Mark of Kri, The (USA)" -> "the mark of kri"
    "Pucelle, La - Tactics (USA)" -> "la pucelle - tactics"
    """
    # Remove everything from the first parenthetical group onward
    core = re.sub(r"\s*\(.*", "", filename)
    # Handle trailing/mid-position articles: "X, The [rest]" -> "The X [rest]"
    # Matches both "Mark of Kri, The" (no rest) and "Pucelle, La - Tactics" (with rest)
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


# ---------------------------------------------------------------------------
# Tier definitions: "core title" -> note
# Core titles must match the output of extract_core_title()
# ---------------------------------------------------------------------------

ESSENTIAL_TITLES = {
    # Action/Adventure
    "god of war": "Definitive character action game. Redefined the genre.",
    "god of war ii": "Improved everything. Best PS2 action game.",
    "shadow of the colossus": "Art as a game. 16 bosses, nothing else. Revolutionary.",
    "ico": "Fumito Ueda's first masterpiece. Minimalist escort puzzle-adventure.",
    "ookami": "Clover Studio's cel-shaded Zelda. One of the most beautiful games ever made.",
    "kingdom hearts": "Disney x Final Fantasy. Cultural phenomenon.",
    "kingdom hearts ii": "Perfected the KH combat formula.",
    "devil may cry": "Invented the stylish action genre.",
    "devil may cry 3 - dante's awakening": "Best in the series. Peak character action.",
    # RPGs
    "final fantasy x": "Last great traditional FF. Emotional journey.",
    "final fantasy xii": "Gambit system was ahead of its time. Revisionist masterpiece.",
    "shin megami tensei - persona 3 fes": "Revolutionized the Persona formula. Social links originated here.",
    "shin megami tensei - persona 4": "The defining JRPG of the PS2 era. Murder mystery perfection.",
    "dragon quest viii - journey of the cursed king": "Best DQ in the West. Akira Toriyama's gorgeous world.",
    "shin megami tensei - nocturne": "The hardest, darkest JRPG ever. Press Turn system genius.",
    "dark cloud 2": "Procedural dungeons + city building + golf. Level-5's ambition.",
    # Stealth/Action
    "metal gear solid 3 - subsistence": "Greatest stealth game ever made. Naked Snake's origin.",
    "metal gear solid 2 - substance": "Postmodern masterpiece. Kojima's ultimate mind game.",
    # Survival Horror
    "silent hill 2": "Best horror game ever made. Psychologically devastating.",
    "silent hill 3": "Worthy sequel. Superb atmosphere.",
    "resident evil 4": "Reinvented third-person shooters. Redefined a franchise.",
    # Open World
    "grand theft auto - san andreas": "The open world standard. Massive scope.",
    "grand theft auto - vice city": "Perfect 80s atmosphere. Rockstar at peak style.",
    "grand theft auto iii": "Started the 3D open world revolution.",
    # Platformers
    "ratchet & clank - up your arsenal": "Best in the PS2 trilogy. Perfect action-platformer.",
    "ratchet & clank - going commando": "Refined the formula. Weapon upgrade system.",
    "jak and daxter - the precursor legacy": "Naughty Dog's 3D platformer masterwork.",
    "jak 3": "Open world + platforming. Peak PS2 platforming.",
    "sly 2 - band of thieves": "Best stealth-platformer ever. Heist structure genius.",
    # Racing
    "gran turismo 4": "700+ cars, 51 tracks. THE racing sim.",
    "burnout 3 - takedown": "Most fun arcade racer ever. Crash mode perfection.",
    # Fighting
    "tekken 5": "Best 3D fighter on PS2. Return to form.",
    # Strategy
    "disgaea - hour of darkness": "Infinite depth SRPG. Nippon Ichi's masterpiece.",
    # Sandbox
    "katamari damacy": "Pure creative genius. Roll everything into a ball.",
    "we love katamari": "More Katamari. More joy.",
}

EXCELLENT_TITLES = {
    # Action/Adventure
    "prince of persia - the sands of time": "Revived the franchise. Time rewind mechanic.",
    "prince of persia - warrior within": "Darker, more combat-focused. Divisive but excellent.",
    "prince of persia - the two thrones": "Satisfying trilogy conclusion.",
    "beyond good & evil": "Cult classic. Great world-building and investigation.",
    "psychonauts": "Tim Schafer's level design masterclass.",
    "bully": "Rockstar does school. Unique open-world gem.",
    "jak ii": "Dark open-world pivot. Bold direction.",
    "ratchet & clank": "The original. Started the franchise.",
    "sly cooper and the thievius raccoonus": "Charming stealth-platformer origin.",
    "sly 3 - honor among thieves": "More heist gameplay. Great cast.",
    "ratchet - deadlocked": "All combat, no fluff. Great co-op.",
    "castlevania - lament of innocence": "3D Castlevania done right.",
    "castlevania - curse of darkness": "Improved 3D Castlevania. Innocent Devils.",
    "kingdom hearts - re-chain of memories": "Card-based combat. Unique KH experience.",
    "odin sphere": "Vanillaware's 2D masterpiece. Gorgeous.",
    "grimgrimoire": "Vanillaware RTS. Underrated gem.",
    "maximo - ghosts to glory": "Neo-Ghosts'n Goblins. Brutal and fun.",
    "maximo vs army of zin": "Sequel with improved combat.",
    "god hand": "Clover's swan song. Deep combat system. Cult classic.",
    "viewtiful joe": "Stylish side-scroller. VFX powers.",
    "viewtiful joe 2": "More VFX mayhem.",
    "the mark of kri": "Disney art, brutal combat. Unique.",
    "rise of the kasai": "Mark of Kri sequel.",
    "the warriors": "Rockstar brawler. CAN YOU DIG IT?",
    # RPGs
    "xenosaga episode i - der wille zur macht": "Space opera JRPG. Ambitious storytelling.",
    "xenosaga episode iii - also sprach zarathustra": "Concluded the trilogy masterfully.",
    "star ocean - till the end of time": "Real-time combat JRPG. Plot twist for the ages.",
    "valkyrie profile 2 - silmeria": "Beautiful JRPG. Unique combat system.",
    "suikoden iii": "Trinity sight system. 108 stars.",
    "suikoden v": "Return to form. Best PS2 Suikoden.",
    "radiata stories": "170+ recruitable characters. Charming.",
    "rogue galaxy": "Level-5's space pirate action-RPG.",
    "wild arms 3": "Western-themed JRPG. Unique aesthetic.",
    "wild arms 5": "Best in the series. HEX battle system.",
    "wild arms - alter code - f": "Wild Arms 1 remake. Improved.",
    "grandia ii": "Excellent real-time combat system.",
    "grandia iii": "Best Grandia combat. Aerial combos.",
    "breath of fire - dragon quarter": "Roguelite JRPG. Existential drama.",
    "shin megami tensei - digital devil saga": "Hindu mythology JRPG. Press Turn combat.",
    "shin megami tensei - digital devil saga 2": "Concluded the DDS story perfectly.",
    "growlanser generations": "Tactical JRPG collection. Working Designs classic.",
    "atelier iris - eternal mana": "Charming alchemy RPG.",
    "shadow hearts - covenant": "Judgment Ring combat. WWI alternate history.",
    "shadow hearts - from the new world": "Americas setting. Fun cast.",
    "shadow hearts": "The original. Unique horror JRPG.",
    "tales of the abyss": "Free Run battle system. Great JRPG.",
    "tales of legendia": "Character-focused Tales. Beautiful music.",
    "magna carta - tears of blood": "Hyung-tae Kim art. Unique combat.",
    "dark cloud": "Level-5's first RPG. Georama world-building.",
    # Stealth/Action
    "hitman - blood money": "Best classic Hitman. Sandbox assassination.",
    "hitman - contracts": "Dark atmospheric Hitman.",
    "hitman 2 - silent assassin": "Stealth sandbox classic.",
    "tom clancy's splinter cell - chaos theory": "Peak Splinter Cell. Perfect stealth.",
    "tom clancy's splinter cell": "Started the series. Great stealth.",
    "timesplitters 2": "Best console FPS of its era.",
    "timesplitters - future perfect": "More TimeSplitters fun. Great humor.",
    "timesplitters": "The original. Goldeneye spiritual successor.",
    # Survival Horror
    "silent hill 4 - the room": "First-person apartment horror. Unique entry.",
    "fatal frame": "Camera-based horror. Terrifying.",
    "fatal frame ii - crimson butterfly": "Best in the series. Twin village horror.",
    "fatal frame iii - the tormented": "Conclusion of the PS2 trilogy.",
    "haunting ground": "Clock Tower spiritual successor. Underrated.",
    "clock tower 3": "Cinematic horror. Evade and fight.",
    "resident evil - code - veronica x": "Classic RE. Claire and Chris.",
    "resident evil - outbreak": "Co-op RE before its time.",
    "rule of rose": "Controversial horror. Rare. Atmospheric.",
    # Racing
    "gran turismo 3 - a-spec": "Launch-era masterpiece. Still gorgeous.",
    "burnout revenge": "Traffic checking perfection.",
    "need for speed - most wanted": "Police chases. Open world racing.",
    "need for speed - underground 2": "Tuner culture perfection.",
    "need for speed - underground": "Started the tuner craze.",
    "midnight club 3 - dub edition remix": "Best arcade racer on PS2.",
    "ssx 3": "Open mountain snowboarding. Peak SSX.",
    "ssx tricky": "Over-the-top snowboard fun.",
    # Fighting
    "guilty gear xx accent core plus": "Best 2D fighter on PS2.",
    "virtua fighter 4 - evolution": "Deep 3D fighting perfection.",
    "soulcalibur ii": "Weapon-based fighting at its best.",
    "soulcalibur iii": "PS2 exclusive entry. Character creation.",
    "tekken tag tournament": "Tag team Tekken. Launch classic.",
    "street fighter anniversary collection": "SF2 + SF3 Third Strike. Essential.",
    # Sports
    "nba street vol. 2": "Best arcade basketball ever.",
    "tony hawk's pro skater 3": "Peak THPS.",
    "tony hawk's underground": "Story mode THPS. Create-a-Park.",
    "espn nfl 2k5": "Best football game ever made. $20 price point legend.",
    "mvp baseball 2005": "Best baseball game ever made.",
    # Platformers/Compilations
    "mega man x8": "Return to form for X series.",
    "mega man anniversary collection": "MM1-8. Essential compilation.",
    "mega man x collection": "X1-X6. Great compilation.",
    "klonoa 2 - lunatea's veil": "Beautiful 2.5D platformer. Hidden gem.",
    # Strategy
    "disgaea 2 - cursed memories": "More SRPG insanity.",
    "la pucelle - tactics": "Nippon Ichi classic. Pre-Disgaea.",  # Redump: Pucelle, La - Tactics
    "phantom brave": "Unique SRPG. Confined mechanics.",
    "front mission 4": "Mech tactical RPG.",
    "stella deus - the gate of eternity": "Underrated Atlus SRPG.",
    # Sandbox/Sim
    "destroy all humans!": "Alien sandbox. Great humor.",
    "destroy all humans! 2": "More alien fun.",
    "mercenaries": "Open world destruction. Pandemic gem.",
    "twisted metal - black": "Dark vehicular combat. Best in series.",
    "war of the monsters": "Kaiju fighting game. Underrated.",
    # Unique
    "amplitude": "Rhythm game mastery. Harmonix precursor.",
    "frequency": "Started Harmonix's legacy.",
    "guitar hero": "Changed gaming culture forever.",
    "guitar hero ii": "Perfected the formula.",
    "dance dance revolution extreme 2": "Best home DDR release.",
    "rez": "Synesthesia shooter. Tetsuya Mizuguchi's vision.",
    "gradius v": "Treasure-developed. Best modern Gradius.",
    "r-type final": "100+ ships. Gorgeous shmup.",
    "under the skin": "Quirky Capcom gem.",
    "steambot chronicles": "Open-world mech life sim. Hidden gem.",
    "mister mosquito": "You're a mosquito. Bite people. Japan is wild.",
    "gitaroo man": "Rhythm game with heart.",
    "parappa the rapper 2": "Kick Punch sequel!",
    "darkwatch": "Vampire western FPS. Cult classic.",
    "psi-ops - the mindgate conspiracy": "Telekinesis physics playground.",
    "second sight": "Psychic powers stealth-action.",
}

GREAT_TITLES = {
    # Action
    "devil may cry 2": "Weakest DMC but still action-packed.",
    "baldur's gate - dark alliance": "Excellent hack-and-slash co-op.",
    "baldur's gate - dark alliance ii": "More of the same, still great.",
    "champions of norrath": "Diablo-style co-op. Snowblind engine.",
    "champions - return to arms": "Sequel. More co-op dungeon crawling.",
    "x-men legends": "Proto-Marvel Ultimate Alliance.",
    "x-men legends ii - rise of apocalypse": "Better sequel. Co-op.",
    "marvel - ultimate alliance": "Superhero dungeon crawler.",
    "spartan - total warrior": "Sega's hack-and-slash. Solid.",
    "onimusha - warlords": "Samurai Resident Evil. Great start.",
    "onimusha 3 - demon siege": "Jean Reno + samurai. Time travel.",
    "onimusha 2 - samurai's destiny": "More demon slaying.",
    "onimusha - dawn of dreams": "Last Onimusha. Biggest scope.",
    "way of the samurai": "Branching sword combat.",
    "way of the samurai 2": "More branching paths. Deeper.",
    "shinobi": "Hard 3D ninja action. Rewarding.",
    "nightshade": "Shinobi sequel. Female ninja.",
    "genji - dawn of the samurai": "Beautiful samurai action.",
    "blood will tell - tezuka osamu's dororo": "Dororo adaptation. Unique body-part recovery.",
    "nanobreaker": "Konami hack-and-slash. Gory.",
    "chaos legion": "Summon legions to fight. Unique.",
    "drakengard": "Yoko Taro's disturbing debut.",
    "drakengard 2": "More Yoko Taro weirdness.",
    "onimusha - blade warriors": "Onimusha fighting game.",
    "max payne": "Bullet time noir shooter.",
    "max payne 2 - the fall of max payne": "Improved Max Payne. Great story.",
    # RPGs
    "dot hack part 1 - infection": "MMO simulation RPG. Unique concept.",
    "dot hack part 2 - mutation": "Continuation of .hack.",
    "dot hack part 3 - outbreak": "Third chapter. Deeper into The World.",
    "dot hack part 4 - quarantine": "Concluded the original .hack.",
    "dot hack g.u. vol. 1 - rebirth": "Improved .hack. Better combat.",
    "dot hack g.u. vol. 2 - reminisce": "Continued the GU story.",
    "dot hack g.u. vol. 3 - redemption": "Concluded GU trilogy.",
    "xenosaga episode ii - jenseits von gut und boese": "Weakest Xenosaga but still good.",
    "suikoden iv": "Naval Suikoden. Divisive.",
    "suikoden tactics": "Suikoden tactical spin-off.",
    "arc the lad - twilight of the spirits": "Dual-perspective JRPG.",
    "romancing saga": "Free-form JRPG. SaGa at its best.",
    "ys - the ark of napishtim": "Fast-paced Ys action-RPG.",
    "mana khemia - alchemists of al-revis": "School alchemy RPG.",
    "mana khemia 2 - fall of alchemy": "Sequel. More alchemy.",
    "atelier iris 2 - the azoth of destiny": "Improved Atelier.",
    "atelier iris 3 - grand phantasm": "Quest-based Atelier.",
    "ar tonelico - melody of elemia": "Song magic RPG. Unique.",
    "ar tonelico ii - melody of metafalica": "Improved song magic.",
    "makai kingdom - chronicles of the sacred tome": "NIS vehicle combat SRPG.",
    "final fantasy x-2": "Job system. Divisive but deep combat.",
    "dirge of cerberus - final fantasy vii": "Vincent Valentine 3D shooter.",
    "wild arms 4": "Platforming JRPG hybrid.",
    "grandia xtreme": "Dungeon-focused Grandia.",
    "growlanser - heritage of war": "Later Growlanser entry.",
    # Shooters
    "black": "Gun porn FPS. Criterion. Explosions.",
    "killzone": "Sony's FPS franchise started here.",
    "medal of honor - frontline": "D-Day opening. Classic WW2 FPS.",
    "medal of honor - rising sun": "Pacific theater WW2.",
    "medal of honor - european assault": "European theater WW2.",
    "call of duty 2 - big red one": "Solid console WW2.",
    "call of duty - finest hour": "First console COD.",
    "call of duty 3": "Solid WW2 entry.",
    "brothers in arms - road to hill 30": "Tactical WW2 shooter.",
    "brothers in arms - earned in blood": "More tactical WW2.",
    "area 51": "Sci-fi FPS. David Duchovny.",
    "red faction": "Destructible environments. Revolutionary.",
    "red faction ii": "More destruction.",
    "tom clancy's splinter cell - pandora tomorrow": "Solid Splinter Cell sequel.",
    "tom clancy's splinter cell - double agent": "Moral choice Splinter Cell.",
    # Sports
    "fight night round 2": "Total Punch Control. Best boxing.",
    "fight night round 3": "Even prettier boxing.",
    "ssx on tour": "Skiing + snowboarding.",
    "hot shots golf 3": "Sony's fun golf sim.",
    "hot shots golf fore!": "Best Hot Shots.",
    "tony hawk's pro skater 4": "Open-world THPS.",
    "tony hawk's underground 2": "World Destruction Tour.",
    "tony hawk's american wasteland": "Open-world skating.",
    "nba street v3": "More arcade basketball.",
    "nba street": "Original arcade basketball.",
    "mvp baseball 2004": "Great baseball game.",
    "mvp baseball 2003": "Solid baseball.",
    # Platformers
    "pac-man world 2": "Solid 3D Pac-Man.",
    "pac-man world 3": "More 3D Pac-Man.",
    "sonic mega collection plus": "Classic Sonic compilation.",
    "sonic heroes": "Team-based 3D Sonic.",
    "rayman 2 - revolution": "Rayman 2 remake. Gorgeous.",
    "rayman 3 - hoodlum havoc": "Fun 3D Rayman.",
    "jak x - combat racing": "Jak + racing. Fun spin-off.",
    "jak and daxter - the lost frontier": "Last Jak game. Decent.",
    "crash bandicoot - the wrath of cortex": "Post-Naughty Dog Crash.",
    "crash twinsanity": "Open-world-ish Crash. Charming.",
    "crash nitro kart": "Crash racing.",
    "spyro - a hero's tail": "Decent post-Insomniac Spyro.",
    "mega man x - command mission": "RPG Mega Man X. Unique.",
    "mega man x7": "3D X. Rough but collectible.",
    "ape escape 2": "Monkey catching sequel.",
    "ape escape 3": "More monkey catching.",
    "ratchet & clank - size matters": "Portable port. Decent.",
    # Racing
    "wipeout fusion": "Anti-gravity racing.",
    "auto modellista": "Cel-shaded racing. Capcom unique.",
    "ridge racer v": "PS2 launch racer. Classic.",
    "enthusia - professional racing": "Konami's hidden GT competitor.",
    "need for speed - hot pursuit 2": "Classic NFS pursuit action.",
    "need for speed - carbon - collector's edition": "Canyon racing.",
    "midnight club ii": "Arcade street racing.",
    "burnout 2 - point of impact": "Pre-Takedown Burnout. Great.",
    "burnout": "Original Burnout. Started it all.",
    # Sim/Strategy
    "ace combat 04 - shattered skies": "Superb flight combat.",
    "ace combat 5 - the unsung war": "Cinematic flight combat.",
    "ace combat zero - the belkan war": "Great prequel.",
    "zone of the enders": "Kojima mech game. MGS2 demo.",
    "armored core 2": "FromSoftware mech building.",
    "armored core - last raven": "Most punishing AC.",
    "armored core 3": "Solid AC entry.",
    "armored core - nexus": "Double-disc AC.",
    "dynasty warriors 3": "Musou genre breakout.",
    "dynasty warriors 4": "Refined musou.",
    "dynasty warriors 5": "Peak PS2 musou.",
    "samurai warriors": "Japanese history musou.",
    "samurai warriors 2": "Improved samurai musou.",
    "romance of the three kingdoms vii": "Deep strategy sim.",
    "romance of the three kingdoms viii": "More ROTK strategy.",
    # Unique/Other
    "guitar hero iii - legends of rock": "Mainstream GH hit.",
    "guitar hero world tour": "Full band GH.",
    "guitar hero - aerosmith": "Band-specific GH.",
    "guitar hero - metallica": "Heavy metal GH.",
    "alien hominid": "Newgrounds to console. Hard side-scroller.",
    "karaoke revolution": "Harmonix singing game.",
    "taiko drum master": "Taiko drumming.",
    "lego star wars ii - the original trilogy": "Started the LEGO game phenomenon.",
    "lego star wars - the video game": "The original LEGO game.",
    # Gregory Horror Show not in US 1G1R set
    # MGS2 Sons of Liberty superseded by Substance in 1G1R
    # MGS3 Snake Eater not in 1G1R (superseded by Subsistence)
    "resident evil - outbreak - file 2": "More co-op RE.",
    "final fantasy xi - online - vana'diel collection 2008": "MMO on PS2. Historic.",
    "grand theft auto - liberty city stories": "GTA on PS2. Portable port.",
    "grand theft auto - vice city stories": "More Vice City.",
    "gradius iii and iv": "Classic Gradius compilation.",
    "twisted metal - head-on - extra twisted edition": "PSP port with extras.",
    # Co-op/Party
    "the lord of the rings - the two towers": "Movie tie-in done right.",
    "the lord of the rings - the return of the king": "Better movie game.",
    "the lord of the rings - the third age": "LOTR RPG.",
    "star wars - battlefront ii": "Classic Star Wars FPS.",
    "star wars - battlefront": "Original Battlefront.",
    "spider-man 2": "Best Spider-Man movement ever. Open world.",
    "spider-man": "Neversoft Spider-Man.",
    "mortal kombat - deception": "Best MK on PS2.",
    "mortal kombat - shaolin monks": "MK beat-em-up. Great co-op.",
    "mortal kombat - armageddon": "Every MK character.",
    "dragon ball z - budokai tenkaichi 3": "Best DBZ fighter.",
    "dragon ball z - budokai 2": "Solid DBZ fighter.",
    "naruto - ultimate ninja 3": "Best Naruto fighter on PS2.",
    "lara croft tomb raider - anniversary": "Classic TR1 remake.",
    "lara croft tomb raider - legend": "Lara Croft reborn.",
    "harry potter and the chamber of secrets": "Hogwarts open world.",
    "harry potter and the prisoner of azkaban": "Best HP on PS2.",
    "wwe smackdown vs. raw 2007": "Best WWE on PS2.",
    "wwe smackdown! vs. raw 2006": "Great WWE.",
    "the king of fighters 2002 - challenge to ultimate battle": "Best KOF compilation.",
    "the king of fighters xi": "Competitive KOF entry.",
    "metal slug anthology": "Classic run-n-gun compilation.",
    "contra - shattered soldier": "Hard classic Contra.",
    "neo contra": "Wild 3D Contra.",
}

# ---------------------------------------------------------------------------
# NOTABLE patterns: franchise keywords that catch remaining decent games
# Any game not in tiers 1-3 matching these goes to NOTABLE instead of COMPLETE
# ---------------------------------------------------------------------------
NOTABLE_KEYWORDS = [
    "Tomb Raider",
    "Max Payne",
    "Hitman",
    "Splinter Cell",
    "Medal of Honor",
    "Need for Speed",
    "Burnout",
    "Tony Hawk",
    "LEGO",
    "Star Wars",
    "Lord of the Rings",
    "Harry Potter",
    "Spider-Man",
    "Batman",
    "Dragon Ball",
    "Naruto",
    "WWE",
    "Mortal Kombat",
    "Mega Man",
    "Castlevania",
    "Contra",
    "Metal Slug",
    "Crash",
    "Spyro",
    "Rayman",
    "Tak and the",
    "Ratchet",
    "Jak ",
    "Sly ",
    "Final Fantasy",
    "Tales of",
    "Suikoden",
    "Atelier",
    "Mana Khemia",
    "Shin Megami",
    "Persona",
    "Shadow Hearts",
    "Ar Tonelico",
    "Tekken",
    "Virtua Fighter",
    "Soul Calibur",
    "Guilty Gear",
    "King of Fighters",
    "Gran Turismo",
    "Ridge Racer",
    "Wipeout",
    "Midnight Club",
    "Call of Duty",
    "Brothers in Arms",
    "Battlefield",
    "God of War",
    "Devil May Cry",
    "Onimusha",
    "Madden",
    "FIFA",
    "NBA ",
    "MLB ",
    "NHL ",
    "NCAA",
    "Sonic",
    "Pac-Man",
    "Bomberman",
    "Ace Combat",
    "Armored Core",
    "Zone of the Enders",
    "Romance of the Three Kingdoms",
    "Dynasty Warriors",
    "Samurai Warriors",
    "Disgaea",
    "La Pucelle",
    "Makai Kingdom",
    "Guitar Hero",
    "Rock Band",
    "Dance Dance",
    "DDRMAX",
    "Grand Theft Auto",
    "Mercenaries",
    "Destroy All",
    "Katamari",
    "Parappa",
    "Gitaroo",
    ".hack",
    "Xenosaga",
    "Wild Arms",
    "Ape Escape",
    "Dark Cloud",
    "Rogue Galaxy",
    "SSX",
    "Hot Shots",
    "Fight Night",
    "Resident Evil",
    "Silent Hill",
    "Fatal Frame",
    "Prince of Persia",
    "Beyond Good",
    "Psychonauts",
    "Odin Sphere",
    "Viewtiful Joe",
    "God Hand",
    "Gradius",
    "R-Type",
    "Twisted Metal",
    "Champions",
    "Baldur's Gate",
    "X-Men",
    "Marvel",
    "Justice League",
    "Persona",
    "Taiko",
    "Karaoke Revolution",
    "Phantom Brave",
    "Front Mission",
    "Naruto",
    "Dragon Ball Z",
    "One Piece",
    "Transformers",
    "Scooby-Doo",
    "SpongeBob",
    "Sims, The",
    "Simpsons",
    "Virtua Tennis",
    "Top Spin",
    "Buzz!",
    "EyeToy",
    "SingStar",
    "Contra",
    "Gradius",
    "Metal Slug",
    "Shin Megami Tensei",
    "Romancing SaGa",
    "Unlimited SaGa",
    "Shadow of",
    "Colossus",
    "Ico",
    "Ookami",
    "Xenosaga",
    "Arc the Lad",
    "Breath of Fire",
    "Valkyrie Profile",
    "Radiata Stories",
    "Kingdom Hearts",
    "Genji",
    "Blood Will Tell",
    "Way of the Samurai",
    "Shinobi",
    "Nightshade",
    "Klonoa",
    "Alien Hominid",
    "Rule of Rose",
    "Haunting Ground",
    "Clock Tower",
    "Frequency",
    "Amplitude",
    "Steambot",
    "Mister Mosquito",
    "Rez",
    "Lumines",
    "Psi-Ops",
    "Second Sight",
    "Darkwatch",
    "Under the Skin",
    "Gregory Horror",
    "Red Faction",
    "Area 51",
    "TimeSplitters",
    "Auto Modellista",
    "Enthusia",
    "Stella Deus",
]


def load_filenames(filepath: str) -> list[str]:
    """Load all PS2 filenames from dump file."""
    with open(filepath) as f:
        return [line.strip() for line in f if line.strip()]


def match_keyword(filename: str, keywords: list[str]) -> bool:
    """Check if filename contains any notable keyword."""
    fname_lower = filename.lower()
    for kw in keywords:
        if kw.lower() in fname_lower:
            return True
    return False


def build_lookup(titles: dict[str, str]) -> dict[str, str]:
    """Build a normalized lookup from a title->note dict."""
    return {k.lower().strip(): v for k, v in titles.items()}


def build_curation() -> PlatformCuration:
    """Build the complete PS2 curation using fuzzy matching."""
    filenames = load_filenames("/tmp/ps2_all.txt")

    # Build core->note lookups
    ess_lookup = build_lookup(ESSENTIAL_TITLES)
    exc_lookup = build_lookup(EXCELLENT_TITLES)
    great_lookup = build_lookup(GREAT_TITLES)

    games = []
    tier_counts = dict.fromkeys(GameTier, 0)
    unmatched_ess = set(ess_lookup.keys())
    unmatched_exc = set(exc_lookup.keys())
    unmatched_great = set(great_lookup.keys())

    # Track disc 2+ entries to skip counting
    disc2_pattern = re.compile(r"\(Disc [2-9]\)")

    for fname in filenames:
        core = extract_core_title(fname)
        is_extra_disc = bool(disc2_pattern.search(fname))

        # Check tiers in priority order
        if core in ess_lookup:
            tier = GameTier.ESSENTIAL
            note = ess_lookup[core]
            score = 95
            tags = ["essential"]
            unmatched_ess.discard(core)
        elif core in exc_lookup:
            tier = GameTier.EXCELLENT
            note = exc_lookup[core]
            score = 80
            tags = ["excellent"]
            unmatched_exc.discard(core)
        elif core in great_lookup:
            tier = GameTier.GREAT
            note = great_lookup[core]
            score = 65
            tags = ["great"]
            unmatched_great.discard(core)
        elif match_keyword(fname, NOTABLE_KEYWORDS):
            tier = GameTier.NOTABLE
            note = ""
            score = 50
            tags = ["notable"]
        else:
            tier = GameTier.COMPLETE
            note = ""
            score = 30
            tags = []

        # Extra discs inherit parent tier but flagged
        if is_extra_disc:
            tags.append("extra-disc")

        game = CuratedGame(
            name=fname,
            tier=tier,
            score=score,
            note=note,
            tags=tags,
        )
        games.append(game)
        tier_counts[tier] += 1

    curation = PlatformCuration(
        platform="ps2",
        version="1.0.0",
        curator="ai-frontier-claude-opus",
        games=games,
        generation="gen6",
        total_available=len(filenames),
        metadata={
            "source": "redump-1g1r-eng-chd-batocera-v2",
            "notes": "AI-curated by Claude Opus frontier model. Tiers based on critical consensus, historical significance, and genre diversity.",
        },
    )

    # Report
    print(f"\n{'=' * 60}")
    print("PS2 AI Curation Report")
    print(f"{'=' * 60}")
    print(f"Total games: {len(filenames)}")
    for tier in GameTier:
        count = tier_counts[tier]
        pct = count / len(filenames) * 100
        print(f"  {tier.label:12s}: {count:4d} ({pct:5.1f}%)")

    if unmatched_ess:
        print(f"\n  WARNING: {len(unmatched_ess)} Essential entries didn't match any file:")
        for n in sorted(unmatched_ess):
            print(f"    - {n}")
    if unmatched_exc:
        print(f"\n  WARNING: {len(unmatched_exc)} Excellent entries didn't match:")
        for n in sorted(unmatched_exc):
            print(f"    - {n}")
    if unmatched_great:
        print(f"\n  WARNING: {len(unmatched_great)} Great entries didn't match:")
        for n in sorted(unmatched_great):
            print(f"    - {n}")

    return curation


if __name__ == "__main__":
    curator = AICurator()
    curation = build_curation()

    # Save YAML curation
    path = curator.save_curation(curation)
    print(f"\nSaved curation to: {path}")

    # Generate list files for each useful tier cutoff
    for tier in [GameTier.ESSENTIAL, GameTier.EXCELLENT, GameTier.GREAT]:
        list_path = curator.generate_list_file("ps2", max_tier=tier)
        if list_path:
            count = len(curation.up_to_tier(tier))
            print(f"Generated list ({tier.value}): {list_path} ({count} games)")

    print("\nDone!")
