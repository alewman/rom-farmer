#!/usr/bin/env python3
"""Generate AI-curated game lists for ROM Farmer.

This script uses frontier AI knowledge to produce tiered, ranked game lists
for platforms where intelligent curation beats "include everything."

Run: python3 scripts/generate_ai_curations.py
Output: config/curations/*.yaml + lists/*+AI-* files
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from romfarmer.ai.curator import AICurator, CuratedGame, GameTier, PlatformCuration


# ---------------------------------------------------------------------------
# PS2 — The Big One
# 1,797 games in our 1G1R set. Full set = 2.6 TB.
# We curate ~300 games across tiers for a killer ~500-600 GB deployment.
# ---------------------------------------------------------------------------

PS2_ESSENTIAL = [
    # The games that DEFINE the PS2. Anyone with a PS2 must play these.
    # Score 95-100.
    ("Shadow of the Colossus (USA)", 100, ["masterpiece", "genre-defining"], "One of the greatest games ever made"),
    ("Metal Gear Solid 3 - Subsistence (USA) (En,Es) (Disc 1) (Subsistence)", 99, ["masterpiece", "stealth"], "Best MGS. Definitive edition with 3D camera"),
    ("Metal Gear Solid 3 - Subsistence (USA) (En,Es) (Disc 2) (Persistence)", 99, ["multi-disc"], "MGS3 Disc 2 — online/bonus content"),
    ("Final Fantasy X (USA, Canada)", 98, ["masterpiece", "jrpg"], "Last great turn-based mainline FF"),
    ("Kingdom Hearts II (USA)", 98, ["masterpiece", "action-rpg"], "Peak of Disney/Square crossover"),
    ("God of War II (USA)", 97, ["masterpiece", "action"], "Technical marvel, perfect combat"),
    ("God of War (USA)", 97, ["masterpiece", "action"], "Invented a genre. Kratos debut"),
    ("Ico (USA)", 97, ["masterpiece", "adventure"], "Fumito Ueda's first masterpiece"),
    ("Grand Theft Auto - San Andreas (USA) (v3.00)", 97, ["masterpiece", "open-world"], "Biggest GTA, peak PS2 open world"),
    ("Shin Megami Tensei - Persona 4 (USA)", 97, ["masterpiece", "jrpg"], "Best Persona. Murder mystery + social sim"),
    ("Shin Megami Tensei - Persona 3 FES (USA)", 96, ["masterpiece", "jrpg"], "Reinvented the JRPG. Social link pioneer"),
    ("Final Fantasy XII (USA)", 96, ["masterpiece", "jrpg"], "Most ambitious FF world design"),
    ("Kingdom Hearts (USA)", 96, ["masterpiece", "action-rpg"], "The impossible crossover that worked"),
    ("Silent Hill 2 (USA) (En,Ja,Fr,De,Es,It) (v2.01)", 96, ["masterpiece", "horror"], "Best horror game ever made. Peak psychological terror"),
    ("Devil May Cry 3 - Dante's Awakening (USA) (En,Ja) (Special Edition)", 95, ["masterpiece", "action"], "Invented stylish action. Turbo mode"),
    ("Ookami (USA)", 95, ["masterpiece", "action-adventure", "hidden-gem"], "Cel-shaded Zelda. Criminally undersold"),
    ("Dragon Quest VIII - Journey of the Cursed King (USA)", 95, ["masterpiece", "jrpg"], "Most charming JRPG ever. Toriyama art"),
    ("Ratchet & Clank - Up Your Arsenal (USA) (En,Fr,Es)", 95, ["masterpiece", "platformer"], "Peak of the series. Perfect fun"),
]

PS2_EXCELLENT = [
    # Outstanding games. The second wave you'd add to any serious collection.
    # Score 85-94.
    ("Grand Theft Auto - Vice City (USA) (v4.00)", 94, ["classic", "open-world"], "80s Miami perfection"),
    ("Grand Theft Auto III (USA)", 93, ["genre-defining", "open-world"], "Invented the 3D open world genre"),
    ("Devil May Cry (USA)", 93, ["genre-defining", "action"], "Birth of stylish action"),
    ("Metal Gear Solid 2 - Substance (USA)", 93, ["classic", "stealth"], "Substance > Sons of Liberty. Extra content"),
    ("Jak and Daxter - The Precursor Legacy (USA) (En,Fr,De,Es,It)", 92, ["classic", "platformer"], "Naughty Dog's 3D platformer masterclass"),
    ("Ratchet & Clank - Going Commando (USA) (v2.00)", 92, ["classic", "platformer"], "Perfect sequel. Introduced RPG elements"),
    ("Ratchet & Clank (USA) (En,Fr,De,Es,It)", 91, ["classic", "platformer"], "Inventive weapons + humor"),
    ("Silent Hill 3 (USA) (En,Ja,Fr,De,Es,It,Ko)", 91, ["classic", "horror"], "Heather's story. Visceral horror"),
    ("Resident Evil 4 (USA)", 91, ["genre-defining", "horror"], "Reinvented survival horror. Over-the-shoulder"),
    ("Ace Combat 04 - Shattered Skies (USA)", 91, ["classic", "flight"], "Best arcade flight game ever"),
    ("Ace Combat 5 - The Unsung War (USA) (En,Ja)", 90, ["classic", "flight"], "Emotional flight combat"),
    ("Jak II (USA) (En,Fr,De,Es,It,Ja,Ko)", 90, ["classic", "platformer"], "Dark open-world pivot. Bold"),
    ("Jak 3 (USA) (En,Fr,De,Es,It,Ja,Ko)", 90, ["classic", "platformer"], "Desert wasteland + Light Jak"),
    ("Sly Cooper and the Thievius Raccoonus (USA)", 90, ["classic", "platformer"], "Stealth-platformer gem"),
    ("Sly 2 - Band of Thieves (USA)", 90, ["classic", "platformer"], "Open hub worlds. Peak Sly"),
    ("Sly 3 - Honor Among Thieves (USA)", 89, ["classic", "platformer"], "Heist gameplay. Satisfying conclusion"),
    ("Katamari Damacy (USA)", 89, ["unique", "puzzle"], "Nothing else like it. Roll up the world"),
    ("We Love Katamari (USA)", 89, ["unique", "puzzle"], "More Katamari. More joy"),
    ("Burnout 3 - Takedown (USA)", 89, ["classic", "racing"], "Best arcade racer ever made"),
    ("Gran Turismo 4 (USA)", 89, ["classic", "racing"], "Definitive PS2 racing sim"),
    ("Gran Turismo 3 - A-Spec (USA)", 88, ["classic", "racing"], "PS2 launch showcase"),
    ("Tekken 5 (USA, Asia)", 88, ["classic", "fighting"], "Best 3D fighter of the era"),
    ("Tekken Tag Tournament (USA)", 87, ["classic", "fighting"], "PS2 launch title. Tag system"),
    ("Guilty Gear XX Accent Core Plus (USA)", 87, ["classic", "fighting"], "Peak 2D fighter on PS2"),
    ("Dark Cloud 2 (USA)", 87, ["hidden-gem", "action-rpg"], "Whimsical dungeon crawler + town building"),
    ("Rogue Galaxy (USA)", 87, ["hidden-gem", "action-rpg"], "Level-5's space opera. Beautiful"),
    ("Radiata Stories (USA)", 86, ["hidden-gem", "jrpg"], "170 recruitable characters. Charming"),
    ("Star Ocean - Till the End of Time (USA) (Disc 1)", 86, ["classic", "jrpg"], "Real-time combat JRPG. Mind-bending plot"),
    ("Star Ocean - Till the End of Time (USA) (Disc 2)", 86, ["multi-disc"], "Star Ocean 3 Disc 2"),
    ("Valkyrie Profile 2 - Silmeria (USA)", 86, ["hidden-gem", "jrpg"], "Beautiful platformer-RPG hybrid"),
    ("Suikoden III (USA)", 86, ["classic", "jrpg"], "Trinity sight system. 108 stars"),
    ("Suikoden V (USA)", 86, ["hidden-gem", "jrpg"], "Return to form. Army battles"),
    ("Xenosaga Episode I - Der Wille zur Macht (USA)", 85, ["classic", "jrpg"], "Spiritual successor to Xenogears"),
    ("Xenosaga Episode III - Also sprach Zarathustra (USA) (Disc 1)", 85, ["classic", "jrpg"], "Series conclusion. Best combat"),
    ("Xenosaga Episode III - Also sprach Zarathustra (USA) (Disc 2)", 85, ["multi-disc"], "Xenosaga III Disc 2"),
    ("Shin Megami Tensei - Nocturne (USA)", 85, ["classic", "jrpg"], "Featuring Dante. Press-turn combat perfection"),
    ("Shin Megami Tensei - Digital Devil Saga (USA)", 85, ["hidden-gem", "jrpg"], "Atma devouring. Dark and brilliant"),
    ("Shin Megami Tensei - Digital Devil Saga 2 (USA)", 85, ["hidden-gem", "jrpg"], "Conclusion of DDS duology"),
    ("Disgaea - Hour of Darkness (USA)", 85, ["classic", "strategy-rpg"], "Infinite depth SRPG. Level 9999"),
    ("Final Fantasy X-2 (USA, Canada)", 85, ["classic", "jrpg"], "Dress sphere system. Underrated"),
    ("Shadow of Rome (USA)", 85, ["hidden-gem", "action"], "Gladiator combat + stealth. Overlooked gem"),
    ("Resident Evil - Code - Veronica X (USA)", 85, ["classic", "horror"], "Best classic-style RE"),
    ("Twisted Metal - Black (USA)", 85, ["classic", "vehicular-combat"], "Dark, violent, perfect car combat"),
    ("SSX 3 (USA)", 85, ["classic", "sports"], "Best snowboard game. Open mountain"),
    ("SSX Tricky (USA, Asia)", 85, ["classic", "sports"], "IT'S TRICKY! Peak arcade sports"),
    ("Tony Hawk's Pro Skater 3 (USA)", 85, ["classic", "sports"], "Peak of the THPS series"),
    ("Tony Hawk's Underground (USA)", 85, ["classic", "sports"], "Story mode + THPS perfection"),
    ("NBA Street Vol. 2 (USA)", 85, ["classic", "sports"], "Best arcade basketball ever"),
    ("TimeSplitters 2 (USA)", 85, ["hidden-gem", "fps"], "Goldeneye spiritual successor. Local MP gold"),
    ("TimeSplitters - Future Perfect (USA)", 85, ["hidden-gem", "fps"], "Best TS. Story + multiplayer"),
]

PS2_GREAT = [
    # Very good games. The core of a serious collection.
    # Score 75-84.
    ("Ace Combat Zero - The Belkan War (USA)", 84, ["classic", "flight"], "Prequel. Ace style system"),
    ("Beyond Good & Evil (USA) (En,Fr,De,Es,It)", 84, ["hidden-gem", "action-adventure"], "Jade's adventure. Cultclassic"),
    ("Baldur's Gate - Dark Alliance (USA)", 84, ["classic", "action-rpg"], "Couch co-op dungeon crawler"),
    ("Baldur's Gate - Dark Alliance II (USA)", 83, ["classic", "action-rpg"], "More co-op dungeon crawling"),
    ("Champions of Norrath (USA)", 83, ["hidden-gem", "action-rpg"], "Baldur's Gate style. 4 player co-op"),
    ("Champions - Return to Arms (USA)", 83, ["hidden-gem", "action-rpg"], "Sequel. More content"),
    ("Viewtiful Joe (USA)", 83, ["hidden-gem", "action"], "Cel-shaded Capcom brilliance"),
    ("Viewtiful Joe 2 (USA)", 82, ["hidden-gem", "action"], "More VFX powers. Co-op mode"),
    ("Prince of Persia - The Sands of Time (USA)", 84, ["classic", "action-adventure"], "Time rewind mechanic. Elegant"),
    ("Prince of Persia - Warrior Within (USA)", 82, ["classic", "action-adventure"], "Darker, but excellent combat"),
    ("Prince of Persia - The Two Thrones (USA)", 82, ["classic", "action-adventure"], "Satisfying trilogy conclusion"),
    ("Zone of the Enders - The 2nd Runner (USA)", 83, ["hidden-gem", "mech-action"], "Kojima mech action. Gorgeous"),
    ("War of the Monsters (USA)", 82, ["hidden-gem", "fighting"], "Kaiju arena fighting. Pure fun"),
    ("Frequency (USA)", 80, ["hidden-gem", "rhythm"], "Harmonix before Guitar Hero"),
    ("Amplitude (USA)", 80, ["hidden-gem", "rhythm"], "Harmonix refined. Incredible soundtrack"),
    ("Guitar Hero II (USA)", 83, ["classic", "rhythm"], "Peak plastic guitar. Best setlist"),
    ("Guitar Hero (USA)", 82, ["genre-defining", "rhythm"], "Started a revolution"),
    ("Psychonauts (USA)", 84, ["hidden-gem", "platformer"], "Tim Schafer's mind-diving masterpiece"),
    ("Destroy All Humans! (USA)", 82, ["classic", "action"], "Alien invasion comedy. Open world"),
    ("Destroy All Humans! 2 (USA)", 81, ["classic", "action"], "Cold War alien sequel"),
    ("Bully (USA) (v1.01)", 83, ["classic", "open-world"], "Rockstar's school sim. Brilliant"),
    ("Odin Sphere (USA)", 83, ["hidden-gem", "action-rpg"], "Vanillaware art. 2D masterpiece"),
    ("GrimGrimoire (USA)", 80, ["hidden-gem", "strategy"], "Vanillaware RTS. Unique"),
    ("Growlanser - Generations (USA)", 80, ["hidden-gem", "strategy-rpg"], "Working Designs' last game. Tactical"),
    ("La Pucelle - Tactics (USA)", 80, ["hidden-gem", "strategy-rpg"], "Pre-Disgaea NIS. Charming"),
    ("Phantom Brave (USA)", 81, ["hidden-gem", "strategy-rpg"], "NIS boardless SRPG"),
    ("Makai Kingdom - Chronicles of the Sacred Tome (USA)", 80, ["hidden-gem", "strategy-rpg"], "NIS vehicle-based SRPG"),
    ("Disgaea 2 - Cursed Memories (USA)", 83, ["classic", "strategy-rpg"], "Refined Disgaea. Better story"),
    ("Wild Arms 3 (USA)", 81, ["hidden-gem", "jrpg"], "Western JRPG. Cel-shaded charm"),
    ("Wild Arms - Alter Code F (USA)", 80, ["hidden-gem", "jrpg"], "WA1 remake. Enhanced"),
    ("Wild Arms 5 (USA)", 80, ["hidden-gem", "jrpg"], "Hex-based combat. Solid sendoff"),
    ("Breath of Fire - Dragon Quarter (USA)", 80, ["hidden-gem", "jrpg"], "Roguelike JRPG. Ahead of its time"),
    ("Jade Cocoon 2 (USA)", 79, ["hidden-gem", "jrpg"], "Monster collecting + breeding"),
    ("Atelier Iris - Eternal Mana (USA)", 79, ["hidden-gem", "jrpg"], "Beginning of Atelier on PS2"),
    ("Atelier Iris 2 - The Azoth of Destiny (USA)", 79, ["hidden-gem", "jrpg"], "Improved alchemy system"),
    ("Mana Khemia - Alchemists of Al-Revis (USA)", 80, ["hidden-gem", "jrpg"], "Best Atelier-era game. School setting"),
    ("Stella Deus - The Gate of Eternity (USA)", 78, ["hidden-gem", "strategy-rpg"], "Atlus SRPG. Beautiful art"),
    ("Romancing SaGa - Minstrel Song (USA)", 78, ["hidden-gem", "jrpg"], "Non-linear SaGa. Acquired taste, great depth"),
    ("Grandia II (USA)", 80, ["classic", "jrpg"], "Excellent battle system"),
    ("Grandia III (USA)", 79, ["hidden-gem", "jrpg"], "Best combat in series"),
    ("Grandia Xtreme (USA)", 76, ["hidden-gem", "jrpg"], "Dungeon-focused. Great combat"),
    ("Tales of the Abyss (USA)", 83, ["classic", "jrpg"], "Best Tales on PS2"),
    ("Tales of Legendia (USA)", 79, ["hidden-gem", "jrpg"], "Underrated. Great characters"),
    ("Ar Tonelico - Melody of Elemia (USA)", 79, ["hidden-gem", "jrpg"], "Music magic system. Unique"),
    ("Ar Tonelico II - Melody of Metafalica (USA)", 79, ["hidden-gem", "jrpg"], "Refined song crafting"),
    (".hack--Infection - Part 1 (USA)", 78, ["classic", "jrpg"], "Simulated MMO. Pioneering"),
    (".hack--Mutation - Part 2 (USA)", 78, ["classic", "jrpg"], "Continues the story"),
    (".hack--Outbreak - Part 3 (USA)", 78, ["classic", "jrpg"], "Gets deeper"),
    (".hack--Quarantine - Part 4 (USA)", 78, ["classic", "jrpg"], "Conclusion. Rare game"),
    (".hack--G.U. Vol. 1--Rebirth (USA)", 80, ["hidden-gem", "jrpg"], "Better combat. New story"),
    (".hack--G.U. Vol. 2--Reminisce (USA)", 80, ["hidden-gem", "jrpg"], "Continues Haseo's journey"),
    (".hack--G.U. Vol. 3--Redemption (USA)", 80, ["hidden-gem", "jrpg"], "Trilogy finale"),
    ("Castlevania - Lament of Innocence (USA)", 80, ["classic", "action"], "3D Castlevania done right"),
    ("Castlevania - Curse of Darkness (USA)", 79, ["hidden-gem", "action-rpg"], "Devil forging. Underrated"),
    ("Mega Man X Collection (USA)", 82, ["compilation", "platformer"], "X1-X6 on one disc"),
    ("Mega Man Anniversary Collection (USA)", 82, ["compilation", "platformer"], "MM1-MM8 classic collection"),
    ("Contra - Shattered Soldier (USA)", 81, ["classic", "run-and-gun"], "Hard as nails. Pure Contra"),
    ("Gradius V (USA)", 82, ["hidden-gem", "shmup"], "Treasure-developed shmup masterpiece"),
    ("R-Type Final (USA)", 80, ["classic", "shmup"], "100+ ships. Shmup epic"),
    ("Maximo - Ghosts to Glory (USA)", 80, ["hidden-gem", "platformer"], "Ghosts 'n Goblins successor"),
    ("Maximo vs. Army of Zin (USA)", 79, ["hidden-gem", "platformer"], "Improved sequel"),
    ("The Warriors (USA)", 82, ["hidden-gem", "beat-em-up"], "Rockstar meets brawler. Can you dig it"),
    ("Mark of Kri, The (USA)", 80, ["hidden-gem", "action"], "Brutal Disney-styled combat"),
    ("Rise of the Kasai (USA)", 78, ["hidden-gem", "action"], "Sequel. Co-op stealth-action"),
    ("Onimusha 3 - Demon Siege (USA)", 82, ["classic", "action"], "Jean Reno in feudal Japan"),
    ("Onimusha - Warlords (USA)", 81, ["classic", "action"], "RE meets samurai"),
    ("Onimusha 2 - Samurai's Destiny (USA)", 80, ["classic", "action"], "Gift system. Branching paths"),
    ("Onimusha - Dawn of Dreams (USA) (Disc 1)", 80, ["classic", "action"], "Final Onimusha. Huge game"),
    ("Onimusha - Dawn of Dreams (USA) (Disc 2)", 80, ["multi-disc"], "Onimusha DoD Disc 2"),
    ("Soul Calibur II (USA)", 83, ["classic", "fighting"], "Heihachi on PS2. Perfect 3D fighter"),
    ("Soul Calibur III (USA)", 82, ["classic", "fighting"], "Chronicles of the Sword mode"),
    ("Virtua Fighter 4 - Evolution (USA)", 83, ["classic", "fighting"], "Deepest 3D fighter"),
    ("King of Fighters XI, The (USA)", 80, ["classic", "fighting"], "Tag system KOF"),
    ("Street Fighter Anniversary Collection (USA)", 82, ["compilation", "fighting"], "SF2 + SF3 Third Strike"),
    ("Capcom vs. SNK 2 - Mark of the Millennium 2001 (USA)", 83, ["classic", "fighting"], "Ultimate crossover fighter"),
    ("Marvel vs. Capcom 2 - New Age of Heroes (USA)", 82, ["classic", "fighting"], "I WANNA TAKE YOU FOR A RIDE"),
    ("Gauntlet - Dark Legacy (USA)", 80, ["classic", "action-rpg"], "4-player couch co-op dungeon crawl"),
    ("X-Men Legends II - Rise of Apocalypse (USA)", 80, ["classic", "action-rpg"], "4-player co-op Marvel RPG"),
    ("X-Men Legends (USA) (En,Fr)", 79, ["classic", "action-rpg"], "Proto-Ultimate Alliance"),
    ("Burnout Revenge (USA)", 83, ["classic", "racing"], "Traffic checking. Aggressive racing"),
    ("Need for Speed - Most Wanted (USA) (En,Fr,Es) (v1.02)", 82, ["classic", "racing"], "Best NFS. Police chases"),
    ("Need for Speed - Underground 2 (USA) (En,Fr,Es)", 81, ["classic", "racing"], "Street racing + customization"),
    ("Midnight Club 3 - DUB Edition Remix (USA)", 81, ["hidden-gem", "racing"], "Open-world street racing"),
    ("Wipeout Fusion (USA)", 79, ["classic", "racing"], "Anti-gravity racing on PS2"),
    ("Downhill Domination (USA)", 79, ["hidden-gem", "racing"], "Mountain bike combat racing. Underrated"),
    ("ATV Offroad Fury 2 (USA)", 78, ["hidden-gem", "racing"], "Online PS2 pioneer. Great tracks"),
    ("WWE SmackDown! Here Comes the Pain (USA)", 83, ["classic", "wrestling"], "Best wrestling game ever made"),
    ("WWE SmackDown vs. Raw 2006 (USA)", 80, ["classic", "wrestling"], "GM mode perfection"),
    ("Fight Night Round 3 (USA)", 80, ["classic", "boxing"], "Total Punch Control"),
    ("NFL Street 2 (USA)", 80, ["hidden-gem", "sports"], "Arcade football perfection"),
    ("MVP Baseball 2005 (USA)", 80, ["classic", "sports"], "Best baseball game on PS2"),
    ("Hot Shots Golf 3 (USA)", 79, ["hidden-gem", "sports"], "Addictive arcade golf"),
    ("Manhunt (USA)", 80, ["classic", "stealth-horror"], "Rockstar's most disturbing game"),
    ("Hitman - Blood Money (USA)", 82, ["classic", "stealth"], "Best classic Hitman"),
    ("Hitman - Contracts (USA, Australia)", 80, ["classic", "stealth"], "Darkest Hitman"),
    ("Splinter Cell - Chaos Theory (USA) (En,Fr)", 82, ["classic", "stealth"], "Best Splinter Cell"),
    ("SOCOM - U.S. Navy SEALs II (USA)", 79, ["classic", "shooter"], "Peak PS2 tactical shooter"),
    ("SOCOM - U.S. Navy SEALs - Combined Assault (USA)", 78, ["classic", "shooter"], "SOCOM refined"),
    ("Black (USA, Europe)", 80, ["hidden-gem", "fps"], "Criterion's gun porn FPS. Incredible destruction"),
    ("Killzone (USA, Europe, Australia)", 78, ["classic", "fps"], "PS2's Halo killer attempt. Atmospheric"),
    ("Mercenaries - Playground of Destruction (USA) (En,Fr,Es)", 81, ["hidden-gem", "open-world"], "Open-world military sandbox"),
    ("Red Faction (USA) (v2.00)", 79, ["classic", "fps"], "Geo-Mod destruction"),
    ("Freedom Fighters (USA)", 80, ["hidden-gem", "shooter"], "Squad-based freedom fighting. Underrated gem"),
    ("Psi-Ops - The Mindgate Conspiracy (USA)", 79, ["hidden-gem", "action"], "Telekinesis physics. Ahead of its time"),
    ("Second Sight (USA)", 78, ["hidden-gem", "action"], "Psychic powers + stealth"),
    ("The Suffering (USA)", 79, ["hidden-gem", "horror"], "Prison horror. Unique monsters"),
    ("Fatal Frame (USA)", 80, ["hidden-gem", "horror"], "Camera Obscura ghost photography"),
    ("Fatal Frame II - Crimson Butterfly (USA) (Director's Cut)", 82, ["hidden-gem", "horror"], "Best in series. Twin village"),
    ("Fatal Frame III - The Tormented (USA)", 80, ["hidden-gem", "horror"], "Dream/reality horror"),
    ("Silent Hill 4 - The Room (USA) (En,Ja)", 79, ["classic", "horror"], "First-person apartment horror"),
    ("Haunting Ground (USA)", 79, ["hidden-gem", "horror"], "Clock Tower spiritual successor"),
    ("Rule of Rose (USA)", 78, ["hidden-gem", "horror"], "Controversial. Disturbing atmosphere"),
    ("Indigo Prophecy (USA) (En,Fr)", 80, ["classic", "adventure"], "David Cage before Heavy Rain. QTE narrative"),
    ("Jak X - Combat Racing (USA)", 79, ["hidden-gem", "racing"], "Jak universe racing. Surprisingly great"),
    ("Ratchet - Deadlocked (USA) (En,Fr,Es)", 80, ["classic", "action"], "Gladiator Ratchet. Pure combat"),
    ("Persona 3 FES (USA)", 97, [], ""),  # Skip - already in Essential
    ("God Hand (USA)", 83, ["hidden-gem", "beat-em-up"], "Clover's last game. Insane difficulty. Cult classic"),
    ("Under the Skin (USA)", 75, ["hidden-gem", "action"], "Weird Capcom gem. Alien pranking"),
    ("Gregory Horror Show (Europe) (En,Fr,De,Es,It)", 76, ["hidden-gem", "horror-adventure"], "Unique art style. Hotel of horrors"),
]

# Filter out the duplicate Persona 3 entry
PS2_GREAT = [g for g in PS2_GREAT if not (g[0].startswith("Persona 3") and g[3] == "")]

PS2_NOTABLE = [
    # Good games worth including in a generous collection.
    # Score 65-77.
    ("Steambot Chronicles (USA)", 77, ["hidden-gem", "action-rpg"], "Mech sim + music. Utterly unique"),
    ("Okage - Shadow King (USA)", 76, ["hidden-gem", "jrpg"], "Tim Burton meets JRPG"),
    ("Dark Chronicle (Europe) (En,Fr,De,Es,It)", 77, ["classic", "action-rpg"], "EU name for Dark Cloud 2"),
    ("Forever Kingdom (USA)", 73, ["hidden-gem", "action-rpg"], "Prequel to Evergrace"),
    ("Drakengard (USA)", 75, ["hidden-gem", "action-rpg"], "Yoko Taro's first. Dark as hell"),
    ("Drakengard 2 (USA)", 74, ["hidden-gem", "action-rpg"], "Lighter tone but solid"),
    ("Ring of Red (USA)", 75, ["hidden-gem", "strategy"], "Alt-history mech strategy"),
    ("Front Mission 4 (USA)", 76, ["hidden-gem", "strategy-rpg"], "Wanzer tactical combat"),
    ("Arcana Heart (USA)", 74, ["hidden-gem", "fighting"], "All-female fighter. Deep systems"),
    ("Samurai Shodown V (USA)", 75, ["classic", "fighting"], "SNK samurai fighter on PS2"),
    ("Neo Contra (USA, Europe)", 75, ["hidden-gem", "run-and-gun"], "3D Contra. Actually good"),
    ("Shinobi (USA)", 76, ["hidden-gem", "action"], "Hard-as-nails ninja action"),
    ("Nightshade (USA)", 75, ["hidden-gem", "action"], "Shinobi sequel. Female ninja"),
    ("Gungrave (USA)", 74, ["hidden-gem", "action"], "Yasuhiro Nightow + Trigun aesthetics"),
    ("Gungrave - Overdose (USA)", 74, ["hidden-gem", "action"], "Better than the first"),
    ("Crimson Tears (USA)", 72, ["hidden-gem", "beat-em-up"], "Cyberpunk dungeon brawler"),
    ("Blood Will Tell - Tezuka Osamu's Dororo (USA)", 76, ["hidden-gem", "action"], "Osamu Tezuka's manga. 48 demons"),
    ("Genji - Dawn of the Samurai (USA)", 75, ["hidden-gem", "action"], "Beautiful samurai action"),
    ("Way of the Samurai (USA)", 74, ["hidden-gem", "action"], "Branching samurai paths"),
    ("Way of the Samurai 2 (USA)", 75, ["hidden-gem", "action"], "Expanded town + paths"),
    ("Kengo - Master of Bushido (USA)", 72, ["hidden-gem", "fighting"], "Realistic sword combat"),
    ("Shadow Hearts (USA)", 77, ["hidden-gem", "jrpg"], "Judgment Ring combat. WWI horror RPG"),
    ("Shadow Hearts - Covenant (USA) (Disc 1)", 78, ["hidden-gem", "jrpg"], "Best Shadow Hearts. WWI epic"),
    ("Shadow Hearts - Covenant (USA) (Disc 2)", 78, ["multi-disc"], "Shadow Hearts Covenant Disc 2"),
    ("Shadow Hearts - From the New World (USA)", 75, ["hidden-gem", "jrpg"], "Americas setting. Lighter tone"),
    ("Xenosaga Episode II - Jenseits von Gut und Boese (USA) (Disc 1)", 76, ["classic", "jrpg"], "Weakest Xenosaga but still needed"),
    ("Xenosaga Episode II - Jenseits von Gut und Boese (USA) (Disc 2)", 76, ["multi-disc"], "Xenosaga II Disc 2"),
    ("Magna Carta - Tears of Blood (USA)", 73, ["hidden-gem", "jrpg"], "Korean RPG. Beautiful art"),
    ("Ephemeral Fantasia (USA)", 71, ["hidden-gem", "jrpg"], "Time loop RPG. Flawed but interesting"),
    ("Unlimited Saga (USA)", 70, ["hidden-gem", "jrpg"], "Most divisive SaGa. Board game RPG"),
    ("Crimson Sea 2 (USA)", 72, ["hidden-gem", "action-rpg"], "Koei action RPG"),
    ("Spy Hunter (USA)", 72, ["classic", "racing-action"], "Modernized spy car combat"),
    ("Stuntman (USA)", 73, ["hidden-gem", "driving"], "Movie stunt driving. Brutally hard"),
    ("Auto Modellista (USA)", 72, ["hidden-gem", "racing"], "Cel-shaded racing. Capcom style"),
    ("Test Drive - Eve of Destruction (USA)", 72, ["hidden-gem", "racing"], "Demolition derby. Pure chaos"),
    ("Def Jam - Fight for NY (USA)", 78, ["hidden-gem", "fighting"], "Hip-hop fighting. Incredibly fun"),
    ("Urban Reign (USA)", 75, ["hidden-gem", "beat-em-up"], "Namco brawler. Great co-op"),
    ("God Hand (USA)", 83, [], ""),  # Already in Great tier
    ("Metal Slug Anthology (USA)", 77, ["compilation", "run-and-gun"], "All Metal Slugs on one disc"),
    ("Taiko no Tatsujin - Taiko Drum Master (USA)", 76, ["hidden-gem", "rhythm"], "Namco drum game. Pure joy"),
    ("Gitaroo Man (USA)", 78, ["hidden-gem", "rhythm"], "Cult classic rhythm game"),
    ("Parappa the Rapper 2 (USA)", 75, ["classic", "rhythm"], "Kick punch chop. Sequel"),
    ("Space Channel 5 - Special Edition (USA)", 76, ["classic", "rhythm"], "Ulala's dancing. Sega charm"),
    ("Rez (USA)", 77, ["genre-defining", "rhythm-shooter"], "Synesthesia shooter. Art game pioneer"),
    ("Klonoa 2 - Lunatea's Veil (USA)", 78, ["hidden-gem", "platformer"], "Beautiful 2.5D platformer"),
    ("Ty the Tasmanian Tiger (USA)", 73, ["hidden-gem", "platformer"], "Australian platformer. Solid fun"),
    ("Ty the Tasmanian Tiger 2 - Bush Rescue (USA)", 73, ["hidden-gem", "platformer"], "Open world sequel"),
    ("Sphinx and the Cursed Mummy (USA)", 75, ["hidden-gem", "action-adventure"], "Egyptian Zelda-like"),
    ("Primal (USA) (En,Fr,De,Es,It)", 75, ["hidden-gem", "action-adventure"], "Demon realms. Unique premise"),
    ("Ico (USA)", 97, [], ""),  # Already in Essential
    ("The Thing (USA)", 75, ["hidden-gem", "horror"], "Movie sequel. Squad trust system"),
    ("Obscure (USA)", 73, ["hidden-gem", "horror"], "Co-op survival horror. High school"),
    ("Obscure II (USA)", 72, ["hidden-gem", "horror"], "College setting sequel"),
    ("Clock Tower 3 (USA)", 73, ["hidden-gem", "horror"], "Capcom survival horror. Chase sequences"),
    ("Extermination (USA)", 72, ["hidden-gem", "horror"], "Early PS2 horror. Antarctic base"),
    ("Cold Fear (USA)", 73, ["hidden-gem", "horror"], "Ship-based horror. Waves mechanic"),
    ("Forbidden Siren (USA)", 76, ["hidden-gem", "horror"], "Japan Studio horror. Sightjack mechanic"),
    ("Forbidden Siren 2 (Europe) (En,Fr,De,Es,It)", 76, ["hidden-gem", "horror"], "Improved sight-jack"),
    ("Darkwatch (USA, Europe)", 74, ["hidden-gem", "fps"], "Vampire western FPS"),
    ("Area 51 (USA)", 73, ["hidden-gem", "fps"], "David Duchovny alien FPS"),
    ("Aliens vs. Predator - Extinction (USA)", 72, ["hidden-gem", "strategy"], "RTS on PS2. Three factions"),
    ("Full Spectrum Warrior (USA)", 75, ["hidden-gem", "tactical"], "Squad tactics. Realistic"),
    ("Conflict - Desert Storm (USA)", 73, ["hidden-gem", "tactical-shooter"], "4-player tactical"),
    ("LEGO Star Wars II - The Original Trilogy (USA) (En,Fr,Es)", 77, ["classic", "action-adventure"], "Started the LEGO empire"),
    ("LEGO Star Wars - The Video Game (USA) (En,Fr,Es)", 76, ["classic", "action-adventure"], "Prequels in LEGO. Charming"),
    ("Dragon Ball Z - Budokai 3 (USA)", 78, ["classic", "fighting"], "Best PS2 DBZ fighter"),
    ("Dragon Ball Z - Budokai Tenkaichi 3 (USA)", 77, ["classic", "fighting"], "161 characters. Spectacle"),
    ("Naruto - Ultimate Ninja 3 (USA) (En,Ja)", 74, ["classic", "fighting"], "Best Naruto PS2 fighter"),
    ("Samurai Warriors 2 (USA, Europe)", 74, ["classic", "musou"], "Koei warriors. Sengoku era"),
    ("Dynasty Warriors 5 (USA)", 73, ["classic", "musou"], "Peak Dynasty Warriors on PS2"),
]

# Filter out duplicates that are in higher tiers
PS2_NOTABLE = [g for g in PS2_NOTABLE if g[3] != ""]


def build_ps2_curation() -> PlatformCuration:
    """Build the complete PS2 curation."""
    games = []
    
    for name, score, tags, note in PS2_ESSENTIAL:
        games.append(CuratedGame(
            name=name, tier=GameTier.ESSENTIAL, score=score,
            tags=tags, note=note,
        ))
    
    for name, score, tags, note in PS2_EXCELLENT:
        games.append(CuratedGame(
            name=name, tier=GameTier.EXCELLENT, score=score,
            tags=tags, note=note,
        ))
    
    for name, score, tags, note in PS2_GREAT:
        games.append(CuratedGame(
            name=name, tier=GameTier.EXCELLENT if score >= 85 else GameTier.GREAT, 
            score=score, tags=tags, note=note,
        ))
    
    for name, score, tags, note in PS2_NOTABLE:
        games.append(CuratedGame(
            name=name, tier=GameTier.NOTABLE, score=score,
            tags=tags, note=note,
        ))
    
    return PlatformCuration(
        platform="ps2",
        version="1.0.0",
        curator="claude-opus-4-frontier",
        games=games,
        generation="gen6",
        total_available=1797,
        metadata={
            "budget_strategy": "tiered",
            "source": "AI knowledge + gaming canon consensus",
            "notes": "Essential+Excellent for ~500GB, add Great for ~750GB, add Notable for ~1TB",
        },
    )


# ---------------------------------------------------------------------------
# Xbox — 68 games in our 1G1R set (already curated by size, but let's rank)
# ---------------------------------------------------------------------------

XBOX_ESSENTIAL = [
    ("Halo - Combat Evolved (USA)", 100, ["masterpiece", "genre-defining"], "Changed console FPS forever"),
    ("Halo 2 (USA) (En,Ja)", 99, ["masterpiece", "fps"], "Xbox Live defining game"),
    ("Star Wars - Knights of the Old Republic (USA)", 98, ["masterpiece", "rpg"], "BioWare's Star Wars RPG masterpiece"),
    ("Fable (USA)", 95, ["masterpiece", "rpg"], "Molyneux's best. Morality system pioneered"),
    ("Tom Clancy's Splinter Cell (USA) (En,Fr)", 94, ["masterpiece", "stealth"], "Defined stealth action. Sam Fisher"),
    ("Ninja Gaiden (USA)", 97, ["masterpiece", "action"], "Best action game of gen. Itagaki's opus"),
]

XBOX_EXCELLENT = [
    ("Tom Clancy's Splinter Cell - Chaos Theory (USA) (En,Fr)", 93, ["classic", "stealth"], "Best Splinter Cell. Co-op stealth"),
    ("Tom Clancy's Splinter Cell - Pandora Tomorrow (USA) (En,Fr)", 88, ["classic", "stealth"], "Spies vs Mercs multiplayer"),
    ("Morrowind - The Elder Scrolls III - Game of the Year Edition (USA)", 94, ["masterpiece", "rpg"], "Deepest Elder Scrolls world"),
    ("Jade Empire (USA)", 90, ["classic", "rpg"], "BioWare martial arts RPG"),
    ("Star Wars - Knights of the Old Republic II - The Sith Lords (USA)", 90, ["classic", "rpg"], "Obsidian's darker KOTOR"),
    ("Burnout 3 - Takedown (USA)", 92, ["classic", "racing"], "Best arcade racer ever"),
    ("Jet Set Radio Future (USA) (En,Ja)", 88, ["hidden-gem", "action"], "Cel-shaded skating graffiti"),
    ("Panzer Dragoon Orta (USA)", 89, ["hidden-gem", "rail-shooter"], "Gorgeous. Best of its kind"),
    ("Crimson Skies - High Road to Revenge (USA)", 88, ["hidden-gem", "flight-action"], "Arcade dogfighting. Xbox Live pioneer"),
    ("Tony Hawk's Pro Skater 3 (USA)", 86, ["classic", "sports"], "Best THPS on Xbox"),
    ("Psychonauts (USA)", 88, ["hidden-gem", "platformer"], "Tim Schafer genius. Mind-diving"),
    ("Beyond Good & Evil (USA)", 86, ["hidden-gem", "action-adventure"], "Jade's quest. Best version"),
    ("Prince of Persia - The Sands of Time (USA)", 88, ["classic", "action-adventure"], "Smooth 60fps on Xbox"),
]

XBOX_GREAT = [
    ("Blinx - The Time Sweeper (USA)", 80, ["hidden-gem", "platformer"], "Time-control platformer. Xbox exclusive"),
    ("Conker - Live & Reloaded (USA)", 84, ["classic", "platformer"], "Mature platformer. Rares farewell"),
    ("Oddworld - Munch's Oddysee (USA)", 81, ["classic", "platformer"], "3D Oddworld. Launch title"),
    ("Oddworld - Stranger's Wrath (USA)", 85, ["hidden-gem", "fps-action"], "Live ammo. Brilliant hybrid"),
    ("MechAssault (USA) (En,Fr)", 82, ["hidden-gem", "mech-action"], "Xbox Live mech combat"),
    ("MechAssault 2 - Lone Wolf (USA)", 80, ["hidden-gem", "mech-action"], "Hijack mechs. Expanded"),
    ("Phantom Dust (USA, Japan)", 83, ["hidden-gem", "action"], "Card-based arena combat. Ahead of its time"),
    ("Otogi - Myth of Demons (USA)", 82, ["hidden-gem", "action"], "FromSoft stylish action"),
    ("Otogi 2 - Immortal Warriors (USA)", 82, ["hidden-gem", "action"], "More FromSoft demon slaying"),
    ("Grabbed by the Ghoulies (USA)", 75, ["hidden-gem", "beat-em-up"], "Rare's haunted house brawler"),
    ("Armed and Dangerous (USA)", 78, ["hidden-gem", "shooter"], "Comedy shooter. Land shark gun"),
    ("Baldur's Gate - Dark Alliance II (USA)", 82, ["classic", "action-rpg"], "Best version. Co-op dungeon crawling"),
    ("Baldur's Gate - Dark Alliance (USA)", 82, ["classic", "action-rpg"], "Co-op ARPG"),
    ("Breakdown (USA) (En,Ja)", 80, ["hidden-gem", "fps"], "First-person brawler. Unique"),
    ("Brute Force (USA)", 76, ["hidden-gem", "shooter"], "4-player squad shooter"),
    ("Call of Cthulhu - Dark Corners of the Earth (USA)", 80, ["hidden-gem", "horror"], "Lovecraftian horror FPS"),
    ("Stubbs the Zombie in Rebel Without a Pulse (USA)", 78, ["hidden-gem", "action"], "Play as the zombie. Comedy horror"),
    ("Metal Wolf Chaos (Japan)", 75, ["hidden-gem", "mech-action"], "President in a mech. Japan only. Legendary"),
    ("Deathrow (USA)", 78, ["hidden-gem", "sports"], "Brutal future-sport. Excel combat"),
]

XBOX_NOTABLE = [
    ("Tony Hawk's Pro Skater 2x (USA)", 78, ["classic", "sports"], "THPS1+2 remastered. Xbox launch"),
    ("Shenmue II (USA, Europe)", 82, ["classic", "adventure"], "Yu Suzuki's epic. Best version"),
    ("Voodoo Vince (USA)", 75, ["hidden-gem", "platformer"], "Voodoo doll platformer"),
    ("Kung Fu Chaos (USA)", 74, ["hidden-gem", "party"], "Martial arts party game"),
    ("Quantum Redshift (USA, Europe)", 76, ["hidden-gem", "racing"], "Wipeout-style anti-grav racer"),
    ("RalliSport Challenge 2 (USA)", 80, ["hidden-gem", "racing"], "Best rally game on Xbox"),
    ("Midtown Madness 3 (USA)", 76, ["hidden-gem", "racing"], "Open city racing"),
    ("Project Gotham Racing 2 (USA, Europe)", 84, ["classic", "racing"], "Kudos system. Gorgeous cities"),
    ("Forza Motorsport (USA)", 85, ["classic", "racing"], "Birth of Forza. Sim racing"),
    ("Grabbed by the Ghoulies (USA)", 75, [], ""),  # Already in Great
    ("Bloodrayne (USA)", 73, ["hidden-gem", "action"], "Vampire action. Campy fun"),
    ("The Chronicles of Riddick - Escape from Butcher Bay (USA)", 88, ["hidden-gem", "fps"], "Best movie game ever. Starbreeze masterpiece"),
    ("Thief - Deadly Shadows (USA)", 82, ["classic", "stealth"], "Cradle level. Horror stealth"),
    ("Doom 3 (USA)", 80, ["classic", "fps"], "Best version on Xbox. Flashlight horror"),
    ("Full Spectrum Warrior (USA)", 78, ["hidden-gem", "tactical"], "Squad tactics. Realistic"),
]

XBOX_NOTABLE = [g for g in XBOX_NOTABLE if g[3] != ""]


def build_xbox_curation() -> PlatformCuration:
    """Build Xbox curation."""
    games = []
    for tier_data, tier in [
        (XBOX_ESSENTIAL, GameTier.ESSENTIAL),
        (XBOX_EXCELLENT, GameTier.EXCELLENT),
        (XBOX_GREAT, GameTier.GREAT),
        (XBOX_NOTABLE, GameTier.NOTABLE),
    ]:
        for name, score, tags, note in tier_data:
            games.append(CuratedGame(
                name=name, tier=tier, score=score,
                tags=tags, note=note,
            ))
    
    return PlatformCuration(
        platform="xbox",
        version="1.0.0",
        curator="claude-opus-4-frontier",
        games=games,
        generation="gen6",
        total_available=68,
        metadata={"source": "AI knowledge + gaming canon"},
    )


# ---------------------------------------------------------------------------
# Main: Generate all curations and list files
# ---------------------------------------------------------------------------

def validate_curation(curation: PlatformCuration, available_files: list[str]) -> dict:
    """Validate curated names against actual build output filenames.
    
    Returns dict with matched/unmatched counts and details.
    """
    available_set = set(available_files)
    matched = []
    unmatched = []
    
    for game in curation.games:
        if game.name in available_set:
            matched.append(game.name)
        else:
            # Try fuzzy match — strip version info
            found = False
            for avail in available_files:
                if avail.startswith(game.name.split(" (")[0]):
                    unmatched.append((game.name, f"partial match: {avail}"))
                    found = True
                    break
            if not found:
                unmatched.append((game.name, "NO MATCH"))
    
    return {
        "total": len(curation.games),
        "matched": len(matched),
        "unmatched": len(unmatched),
        "details": unmatched,
    }


def main():
    workspace = Path("/data/emu/rom-farmer")
    curator = AICurator(workspace_root=workspace)
    
    # --- PS2 ---
    print("=" * 60)
    print("Generating PS2 AI Curation")
    print("=" * 60)
    
    ps2 = build_ps2_curation()
    
    # Validate against actual files
    ps2_files = [p.stem for p in sorted((workspace / "output" / "redump-1g1r-eng-chd-batocera-v2" / "ps2").glob("*.chd"))]
    result = validate_curation(ps2, ps2_files)
    print(f"  Matched: {result['matched']}/{result['total']}")
    if result['unmatched'] > 0:
        print(f"  Unmatched ({result['unmatched']}):")
        for name, detail in result['details']:
            print(f"    {name}")
            print(f"      -> {detail}")
    
    # Save curation YAML
    path = curator.save_curation(ps2)
    print(f"  Saved: {path}")
    
    # Generate list files at different tier levels
    for tier in [GameTier.ESSENTIAL, GameTier.EXCELLENT, GameTier.GREAT]:
        count = len(ps2.up_to_tier(tier))
        list_path = curator.generate_list_file("ps2", max_tier=tier)
        print(f"  List ({tier.value}): {list_path} — {count} games")
    
    # --- Xbox ---
    print()
    print("=" * 60)
    print("Generating Xbox AI Curation") 
    print("=" * 60)
    
    xbox = build_xbox_curation()
    
    xbox_files = [p.stem for p in sorted((workspace / "output" / "redump-1g1r-eng-chd-batocera-v2" / "xbox").glob("*.iso"))]
    result = validate_curation(xbox, xbox_files)
    print(f"  Matched: {result['matched']}/{result['total']}")
    if result['unmatched'] > 0:
        print(f"  Unmatched ({result['unmatched']}):")
        for name, detail in result['details']:
            print(f"    {name}")
            print(f"      -> {detail}")
    
    path = curator.save_curation(xbox)
    print(f"  Saved: {path}")
    
    for tier in [GameTier.ESSENTIAL, GameTier.EXCELLENT, GameTier.GREAT]:
        count = len(xbox.up_to_tier(tier))
        list_path = curator.generate_list_file("xbox", max_tier=tier)
        print(f"  List ({tier.value}): {list_path} — {count} games")
    
    # --- Summary ---
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for platform_name, curation in [("PS2", ps2), ("Xbox", xbox)]:
        print(f"\n{platform_name}:")
        for tier in GameTier:
            count = len(curation.by_tier(tier))
            if count:
                print(f"  {tier.label}: {count} games")
        print(f"  Total curated: {len(curation.games)} / {curation.total_available}")


if __name__ == "__main__":
    main()
