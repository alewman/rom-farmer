# 4TB Batocera NUC — Organizational Gap Analysis

**Date:** February 5, 2026  
**Project:** ROM Farmer + zelda-mcp  
**Target:** Batocera on NUC with 4TB SSD  
**Approach:** Hard-link deployment from built output library

---

## Executive Summary

ROM Farmer has a **production-grade build pipeline** with 71 platform configs, a 5-tier storage system, cross-generation deduplication, and 56 hand-curated Best-Games lists. The zelda-mcp metadata layer adds 120K+ ScreenScraper games with ratings, 8,008 FBNeo arcade games with parent-clone relationships, and 13,961 Wikipedia game articles with semantic search.

The built output totals **~16TB** across 50 platforms. The live Batocera share is a disconnected **710GB manual setup**. The critical missing piece is an automated **deploy layer** that projects a curated 4TB view of the library onto the Batocera share using hard links.

Six organizational gaps were identified, ranging from the missing master build config to collection quality scoring.

---

## Current State Inventory

### Build System

| Layer | Status | Details |
|-------|--------|---------|
| Build Pipeline | ✅ Production | 7 stages: match → delete → transform → compress → m3u → copy → metadata |
| Platform Configs | ✅ 71 configs | Every major system from Atari 2600 to Xbox 360 |
| Tier System | ✅ Well-designed | 5 tiers with budget allocation rules and 4 storage profiles |
| Generation Dedup | ✅ Defined | Gen 4CD through Gen 7 cross-platform deduplication |
| Best-Games Lists | ✅ 56 platforms | ~4,274 curated entries total across all platforms |
| Selection Strategies | ✅ 7 strategies | rating_budget, first, last, random, smallest, largest, alphabetical |
| Compression Prediction | ✅ Self-learning | Historical ratio tracking, gets smarter with each build |
| Interactive Wizard | ✅ Working | `./build-wizard` with auto-discovery |

### Metadata Layer (zelda-mcp)

| Database | Records | Capabilities |
|----------|---------|--------------|
| ScreenScraper | 120,241 games / 49 platforms | Ratings, genres, developers, release dates, descriptions |
| FBNeo DAT | 8,008 games / 617 hardware types | Parent-clone relationships, video specs, driver status |
| Wikipedia | 13,961 games / 7,737 articles | Semantic search, reception, gameplay, plot sections |

### Built Output (on disk)

| Output Build | Size | Platforms | Notes |
|---|---|---|---|
| `1g1r-eng-7z-batocera` | 390 GB | 30 cartridge platforms | Full 1G1R, 7z compressed |
| `1g1r-eng-chd-batocera` | 4.1 TB | 8 disc platforms | Full 1G1R, CHD compressed |
| `arcade-batocera` | 338 GB | 8 arcade platforms | FBNeo, MAME, Naomi, etc. |
| `xbox-full` | 6.5 TB | 1 (Xbox) | Full Xbox library |
| `1g1r-eng-raw-batocera` | 4.3 TB | Multiple | Uncompressed intermediate |
| `laserdisc-batocera` | 31 GB | 1 (Daphne) | Laserdisc games |
| `custom-all-7z-batocera` | 1.8 GB | Custom | Custom set |
| `1g1r-all-7z-batocera` | 1.6 GB | Few | All-region variant |
| **Total Built** | **~16 TB** | **50 platforms** | |

### Live Batocera Share

| Metric | Value |
|---|---|
| Total Size | 710 GB |
| Platform Dirs | 170+ (many empty Batocera defaults) |
| Platforms with ROMs | ~60 (many manually placed) |
| gamelist.xml files | 106 |
| Connection to rom-farmer | **None — fully manual** |

### Cartridge Platform Sizes (7z output)

| Platform | Size | Tier |
|---|---|---|
| 3DS | 288 GB | — |
| NDS | 50 GB | 3 |
| GBA | 13 GB | 2 |
| Mega Drive | 7.2 GB | 2 |
| SNES | 6.8 GB | 2 |
| N64 | 6.0 GB | 2 |
| NES | 4.0 GB | 2 |
| GB | 2.7 GB | 1 |
| GBC | 2.7 GB | 1 |
| Game Gear | 2.4 GB | 1 |
| GBC 2-Player | 1.8 GB | — |
| Atari 2600 | 1.7 GB | 1 |
| PC Engine | 921 MB | 1 |
| ColecoVision | 662 MB | 1 |
| SGB | 500 MB | — |
| GB 2-Player | 431 MB | — |
| Intellivision | 404 MB | 1 |
| Atari 7800 | 323 MB | 1 |
| NGPC | 311 MB | 1 |
| Sega 32X | 285 MB | 2 |
| Atari 5200 | 272 MB | 1 |
| Atari Jaguar | 260 MB | 4 |
| MSX1 | 108 MB | — |
| MSX2 | 82 MB | — |
| Vectrex | 69 MB | 1 |
| Virtual Boy | 64 MB | 1 |
| Master System | 50 MB | 1 |
| Pokémon Mini | 42 MB | 1 |
| WonderSwan Color | 37 MB | 1 |
| NGP | 27 MB | 1 |
| Atari Lynx | 23 MB | 1 |
| WonderSwan | 19 MB | 1 |
| SG-1000 | 839 KB | 1 |

### Disc Platform Sizes (CHD output)

| Platform | Size | Tier |
|---|---|---|
| PS2 | 2.8 TB | 5 |
| PSX | 492 GB | 3 |
| PSP | 374 GB | 4 |
| Dreamcast | 136 GB | 4 |
| PC Engine CD | 113 GB | 3 |
| Saturn | 91 GB | 3 |
| Mega CD | 71 GB | 3 |
| 3DO | 58 GB | 4 |

### Arcade Platform Sizes

| Platform | Size |
|---|---|
| MAME | 247 GB |
| Namco 246 | 26 GB |
| Naomi | 22 GB |
| FBNeo | 21 GB |
| Triforce | 11 GB |
| Naomi 2 | 6.9 GB |
| Atomiswave | 3.0 GB |
| Model 3 | 1.7 GB |
| Model 2 | 788 MB |

---

## Gap Analysis

### Gap 1: No "4TB NUC Build" Master Orchestration

**Problem:** The `1tb-batocera-complete.yaml` exists but there is **no 4TB NUC build config**. The 16TB of built output needs to be intelligently curated down to fit 4TB. The `platform_tiers.yaml` and `completionist` profile define the *strategy* but no build config actually *executes* it for this target.

**Impact:** Without this, there's no reproducible, deterministic definition of "what goes on the NUC."

**Proposed Budget Allocation:**

| Category | Est. Size | Strategy | Notes |
|---|---|---|---|
| Tier 1+2 (full 1G1R) | ~50 GB | `always_include` | All cartridge systems — the soul of retro gaming |
| Tier 3 disc (full 1G1R) | ~750 GB | `always_include` | PSX, Saturn, Sega CD, PCE-CD, NDS |
| Tier 4 best-of | ~200 GB | `best_of` | Dreamcast ~40GB, PSP ~60GB, 3DO ~15GB |
| Tier 5 best-of | ~500 GB | `best_of_extended` | PS2 top 200, GC top 80, Wii top 80 |
| Arcade (curated) | ~50 GB | `best_of` | FBNeo curated + Naomi/Atomiswave best |
| 3DS best-of | ~80 GB | `best_of` | Top 100 3DS games |
| Switch best-of | ~200 GB | `best_of` | Top 50 Switch games |
| PS3 best-of | ~300 GB | `best_of` | Top 30 PS3 games |
| Ports/Engines | ~20 GB | Manual | ScummVM, Doom, etc. |
| Metadata + Media | ~100 GB | Auto | Screenshots, videos, boxart |
| **Reserve** | **~200 GB** | — | Saves, BIOS, system files, slack |
| **Total** | **~2,450 GB** | | **~1.5 TB headroom for expansion** |

**Key Insight:** 4TB is more generous than expected. This means we can go deeper on Gen 6+ platforms (bigger PS2 selection, more GameCube/Wii games) or include fuller arcade sets.

**What's Needed:**
- `config/builds/4tb-nuc-batocera.yaml` — master orchestration
- References `platform_tiers.yaml` for tier-based inclusion rules
- References `generations.yaml` for cross-platform dedup
- Platform-specific selection overrides (PS2: rating_budget 200GB, etc.)

---

### Gap 2: No Hard Link Deployment Layer

**Problem:** Built output (`/data/emu/rom-farmer/output/`) and the live Batocera share (`/data/emu/share/roms-batocera/`) are **completely disconnected**. There is no automated way to project a build config's selections onto the Batocera directory structure.

**Impact:** This is the **single biggest operational gap**. Every deployment is manual, error-prone, and wastes disk space via copies instead of hard links.

**Current State:**
```
output/1g1r-eng-chd-batocera/saturn/  →  (manually copied to?)  →  share/roms-batocera/saturn/
                                          ❌ No automation
                                          ❌ No hard links  
                                          ❌ No state tracking
```

**Desired State:**
```
output/1g1r-eng-chd-batocera/saturn/Game.chd  ──hard link──→  share/roms-batocera/saturn/Game.chd
                                                                (0 bytes extra disk usage)
```

**What's Needed:** A `romfarmer deploy` command that:

1. **Reads** a build manifest (the 4TB NUC config)
2. **Creates** the Batocera folder structure (`share/roms-batocera/{platform}/`)
3. **Hard-links** from `output/` → `share/roms-batocera/` — zero extra disk space
4. **Copies** gamelist.xml + media into correct Batocera paths
5. **Tracks** deployment state in a manifest file
6. **Supports** incremental updates (add/remove games without full rebuild)
7. **Validates** hard link integrity (same filesystem check)
8. **Generates** a deployment report (platforms, game counts, total size)

**Space Savings:** Instead of 16TB output + 4TB copy = 20TB, you'd have 16TB output + 4TB of hard links ≈ **16TB total** (the 4TB share is essentially free).

---

### Gap 3: Best-Games Lists Not Connected to Metadata Quality

**Problem:** The 56 `+Best-Games` lists are hand-curated (good — human taste is the anchor), but they're **static** and don't leverage the 120K-game metadata database. They also vary wildly in depth:

| Platform | Best-Games Count | ScreenScraper Total | Coverage |
|---|---|---|---|
| PS2 | 66 | 3,102 | 2.1% |
| PSX | 60 | 10,850 | 0.6% |
| GBA | 106 | 7,182 | 1.5% |
| GameCube | 146 | 2,014 | 7.2% |
| Saturn | 42 | 2,408 | 1.7% |
| NDS | 104 | 7,672 | 1.4% |
| Wii | 151 | 2,729 | 5.5% |
| SNES | 65 | 4,287 | 1.5% |
| Neo Geo | 60 | — | DAT: 232 parents |

**Sub-gaps:**
- No "smart fill" — after best-of games are placed, remaining budget is wasted
- No genre diversity enforcement (could overweight RPGs, underweight sports)
- No cross-referencing with Wikipedia reception data for consensus picks
- PSP has 154 curated games but full 1G1R is 374GB — budget selection not connected

**What zelda-mcp Can Already Do:**
- `scraper_top_rated` → generate rating-ranked candidate lists for any platform
- `scraper_genres` → audit genre distribution in a selection
- `wiki_search` → find critically acclaimed games by description
- `dat_game_variants` → ensure arcade lists use parent ROMs not clones

**What's Needed:** A list-generation workflow:

1. Start with hand-curated Best-Games list (human taste = immutable anchor)
2. Query ScreenScraper for all games on platform, sorted by rating
3. Fill remaining budget with highest-rated games not already in Best-Games
4. Enforce genre diversity (configurable max N games per genre)
5. Respect multi-disc atomicity (never split disc sets)
6. Output a build-ready list file
7. Generate a "what was added and why" report

---

### Gap 4: 21 Platforms Missing from Output

Platforms with configs but **no built output**:

| Platform | Tier | Est. Best-Of Size | Priority | Notes |
|---|---|---|---|---|
| **GameCube** | 5 | ~50 GB (RVZ) | 🔴 High | Top 80 games, huge quality library |
| **Wii** | 5 | ~80 GB (RVZ) | 🔴 High | Top 80 games, unique motion library |
| **Wii U** | 5 | ~60 GB (WUA) | 🟡 Medium | Top 30, many remasters |
| **PS3** | 5 | ~300 GB (JB) | 🟡 Medium | Top 30, RPCS3 compatible |
| **Xbox 360** | 5 | ~200 GB | 🟠 Low | Xenia less mature |
| **Neo Geo** | 1 | ~5 GB (arcade) | 🔴 High | Essential arcade, 232 parent games |
| **Neo Geo CD** | 3 | ~32 GB (CHD) | 🟡 Medium | Already in live share |
| **FDS** | 1 | ~3 GB | 🔴 High | Trivial, already in live share |
| **SuperGrafx** | 1 | ~1 MB | 🔴 High | 6 games total, trivial |
| **Xbox** | 5 | ~100 GB (XISO) | 🟠 Low | 6.5TB raw exists, needs XISO compression |
| **Chihiro/Hikaru/Lindbergh** | — | ~5 GB | 🟠 Low | Exotic Sega arcade hardware |
| **HBMAME** | — | ~20 GB | 🟠 Low | Homebrew MAME variants |
| **PSP Minis** | — | ~29 GB | 🟡 Medium | Already staged |

**Biggest Bang for Buck:**
1. **GameCube + Wii** — adds ~130GB of the best games of that era
2. **Neo Geo + FDS + SuperGrafx** — tiny systems, huge cultural importance, trivial to build
3. **PS3 curated** — 30 games adds ~300GB of modern classics

---

### Gap 5: No Collection Quality Scoring

**Problem:** With all this metadata, there's no way to answer: *"How good is my 4TB collection?"*

**What's Needed:** A collection health dashboard that evaluates any build:

| Metric | Source | Question It Answers |
|---|---|---|
| **Coverage Score** | ScreenScraper top-rated | What % of the top 100 per platform are included? |
| **Genre Balance** | ScreenScraper genres | Is every genre represented? Overweight on RPGs? |
| **Era Spread** | ScreenScraper release dates | Are all decades of a platform's life covered? |
| **Multiplayer Ratio** | ScreenScraper players field | What % support 2+ players for couch co-op? |
| **Critical Consensus** | Wikipedia reception sections | Are the "must-play" consensus picks all present? |
| **Arcade Completeness** | FBNeo DAT hardware families | Are all major arcade manufacturers covered? |
| **Format Health** | Build output verification | Any broken CHDs? Missing M3U playlists? |

**Implementation:** An MCP tool `score_collection` that:
1. Takes a platform + list of included games
2. Cross-references against ScreenScraper ratings, genres, release dates
3. Returns a scorecard with letter grades per metric
4. Highlights notable missing games ("You're missing Chrono Trigger!")

---

### Gap 6: Live Batocera Share Needs Cleanup

**Problem:** The current `/data/emu/share/roms-batocera/` (710GB) is a legacy manual setup with:

| Issue | Examples |
|---|---|
| Duplicate directories | `megadrive` + `megadrive - Copy` |
| Old backup leftovers | `neogeo.previous2024`, `naomi.old`, `naomi.good.base` |
| Test directories | `jaguar.test`, `n64dd.tst`, `n64dd.tst.org` |
| Parallel versions | `n64` + `n64.unpacked` |
| Empty default dirs | 100+ empty Batocera placeholder directories |
| Inconsistent sources | Some from rom-farmer, some manual, some from legacy builds |

**Resolution:** Once Gap 2 (deploy layer) is implemented:

1. Archive the current share structure manifest (file listing + sizes)
2. Wipe and rebuild entirely from rom-farmer output via hard links
3. The new share becomes a **deterministic, reproducible projection** of a build config
4. Any "extra" content (ScummVM games, ports, homebrew) gets its own manual overlay mechanism

---

## Priority Roadmap

### Phase 1: Foundation (enables everything else)

| # | Task | Effort | Impact | Dependencies |
|---|---|---|---|---|
| 1a | Create `4tb-nuc-batocera.yaml` build config | Medium | 🔴 Critical | platform_tiers.yaml, generations.yaml |
| 1b | Build `romfarmer deploy` command (hard links) | Large | 🔴 Critical | Build config, filesystem same-device check |
| 1c | Build Neo Geo + FDS + SuperGrafx outputs | Small | 🟡 High | Trivial, fills Tier 1 gaps |

### Phase 2: Content Expansion

| # | Task | Effort | Impact | Dependencies |
|---|---|---|---|---|
| 2a | Build GameCube RVZ output (top 80) | Medium | 🔴 Critical | RVZ compression tooling (dolphin-tool) |
| 2b | Build Wii RVZ output (top 80) | Medium | 🔴 Critical | Same tooling as GameCube |
| 2c | Smart list generator (curated + rating fill) | Medium | 🟡 High | zelda-mcp scraper_top_rated |
| 2d | Build PS3 curated set (top 30) | Large | 🟡 High | RPCS3 compatibility list |

### Phase 3: Intelligence Layer

| # | Task | Effort | Impact | Dependencies |
|---|---|---|---|---|
| 3a | Collection health scorer | Small | 🟡 High | zelda-mcp metadata |
| 3b | Generation dedup execution (Gen 6) | Medium | 🟡 High | PS2/GC/Xbox cross-reference |
| 3c | Genre diversity enforcer for selections | Small | 🟢 Medium | ScreenScraper genre data |
| 3d | Deployment diff reports ("what changed") | Small | 🟢 Medium | Deploy state tracking |

### Phase 4: Polish

| # | Task | Effort | Impact | Dependencies |
|---|---|---|---|---|
| 4a | Media optimization profiles (device-sized) | Medium | 🟢 Medium | imagemagick, ffmpeg |
| 4b | Wii U + Xbox 360 builds | Large | 🟢 Medium | Format-specific tooling |
| 4c | Automated nightly deploy updates | Small | 🟢 Medium | Deploy command + cron |
| 4d | Web dashboard for collection browsing | Large | 🔵 Nice | Future enhancement |

---

## Technical Notes

### Hard Link Requirements
- Source (`output/`) and target (`share/roms-batocera/`) **must be on the same filesystem**
- Both currently under `/data/emu/` — ✅ same mount point
- Hard links don't work across filesystems — verify with `df -h /data/emu/rom-farmer/output /data/emu/share/roms-batocera`
- Hard link count visible via `stat` or `ls -l` (link count > 1)

### Compression Format Reference

| Platform Type | Source Format | Output Format | Tool | Typical Ratio |
|---|---|---|---|---|
| Cartridge (No-Intro) | .zip | .7z | 7z | 0.85-0.95 |
| Disc (Redump) | .bin/.cue in .zip | .chd | chdman | 0.62-0.75 |
| GameCube/Wii | .iso/.gcm | .rvz | dolphin-tool | 0.70-0.72 |
| PSP | .iso | .cso | maxcso | 0.85 |
| Xbox | .iso | .xiso | extract-xiso | 0.80 |
| PS3 | .iso | JB folder | ps3dec | 0.90 |

### Key zelda-mcp Tools for This Effort

| Tool | Use Case |
|---|---|
| `scraper_top_rated` | Generate rating-ranked game lists for any platform |
| `scraper_search` | Find specific games with metadata |
| `scraper_genres` | Audit genre distribution in a selection |
| `wiki_search` | Find critically acclaimed games by theme/description |
| `wiki_game_info` | Deep-dive on specific game's reception and history |
| `dat_hardware_list` | Understand arcade hardware landscape |
| `dat_hardware_games` | List all games for an arcade board (Neo Geo, CPS1, etc.) |
| `dat_game_variants` | See parent/clone relationships for arcade games |
| `dat_search` | Find arcade games by name |
| `get_platform_stats` | ROM collection statistics per platform |
| `calculate_budget` | Estimate how many ROMs fit in a storage budget |
| `get_compression_ratio` | Historical compression ratios per platform |

---

## Appendix: Platform Coverage Matrix

### Platforms with Both Config + Output ✅ (50)

Cartridge (30): atari2600, atari5200, atari7800, atarijaguar, atarilynx, colecovision, gamegear, gb, gb2players, gba, gbc, gbc2players, intellivision, mastersystem, megadrive, msx1, msx2, n64, nds, nes, ngp, ngpc, pcengine, pokemini, sega32x, sg1000, sgb, snes, vectrex, virtualboy, wswan, wswanc

Disc (8): 3do, dreamcast, megacd, pcenginecd, ps2, psp, psx, saturn

Arcade (8): atomiswave, fbneo, mame, model2, model3, namco246, naomi, naomi2, triforce

Special (1): 3ds

### Platforms with Config but No Output ❌ (21)

chihiro, fds, gamecube, hbmame, hikaru, lindbergh, neogeo, neogeocd, ps3, pspminis, supergrafx, wii, wiiu, xbox, xbox360 (+ 6 test/variant configs)

### Platforms in Live Batocera Share but Not in rom-farmer

amigacd32, amstradcpc, apple2, c64, c128, cdi, dos, scummvm, switch, and ~40 others (mostly Batocera-native platforms like ports, engines, homebrew)

---

*This analysis was generated by cross-referencing rom-farmer project configs, built output directories, live Batocera share contents, zelda-mcp metadata databases (ScreenScraper, FBNeo DAT, Wikipedia), and platform tier/generation definitions.*
