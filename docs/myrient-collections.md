# Myrient Collections Reference

This document catalogs the specialized ROM/game collections available on Myrient beyond the standard No-Intro and Redump sets.

## Quick Reference

| Collection | What It Is | Use Case |
|------------|------------|----------|
| **FinalBurn Neo** | Arcade romset optimized for FBNeo emulator | Neo Geo, CPS1/2/3, many arcade boards |
| **MAME** | Full MAME romsets (merged/split/non-merged) | Universal arcade emulation |
| **T-En Collection** | Pre-patched English translations | Japanese games with fan translations |
| **RetroAchievements** | RA-verified hashes | Achievement hunting |
| **TeknoParrot** | Modern PC-based arcade dumps | 2000s+ arcade games |
| **eXo** | Curated DOS/Win3x/ScummVM packs | Pre-configured classic PC games |
| **Internet Archive** | Mirrors of IA uploaders | Various specialized sets |

---

## Arcade Collections

### FinalBurn Neo (`/files/FinalBurn Neo/`)

FBNeo is a fork of FinalBurn Alpha optimized for accuracy. The romset includes:

| Folder | Contents |
|--------|----------|
| `arcade/` | Main arcade ROMs (Neo Geo, CPS1/2/3, Cave, Toaplan, etc.) |
| `samples/` | Audio samples for games that need them |
| `hdd/` | Hard disk images for newer arcade systems |
| `channelf/` | Fairchild Channel F (bonus) |
| `coleco/` | ColecoVision (bonus) |
| `fds/` | Famicom Disk System (bonus) |
| `megadrive/` | Genesis/Mega Drive (bonus) |
| `msx/` | MSX (bonus) |
| `nes/` | NES/Famicom (bonus) |
| `ngp/` | Neo Geo Pocket (bonus) |
| `pce/` | PC Engine (bonus) |
| `sg1000/` | Sega SG-1000 (bonus) |
| `sgx/` | PC Engine SuperGrafx (bonus) |
| `sms/` | Sega Master System (bonus) |
| `snes/` | Super Nintendo (bonus) |
| `spectrum/` | ZX Spectrum (bonus) |
| `tg16/` | TurboGrafx-16 (bonus) |

**Best for:** Neo Geo (AES/MVS), CPS1/CPS2/CPS3, Cave shmups, early 90s arcade

### MAME (`/files/MAME/`)

The Multiple Arcade Machine Emulator romset - the gold standard for arcade preservation.

| Folder | Description |
|--------|-------------|
| `ROMs (merged)/` | Parent + clones in one zip (smallest) |
| `ROMs (split)/` | Parents separate from clones |
| `ROMs (non-merged)/` | Every game fully standalone (largest, easiest to use) |
| `ROMs (bios-devices)/` | BIOS and device ROMs only |
| `CHDs (merged)/` | Hard disk/CD images for games that need them |
| `Software List ROMs/` | Home computer/console software MAME can run |
| `Software List CHDs/` | CD-based software list items |
| `Rollback ROMs/` | Older MAME versions (0.78, 0.139, etc.) |
| `Rollback CHDs/` | CHDs for older MAME versions |
| `EXTRAs/` | Artwork, manuals, samples, etc. |
| `Reference Sets/` | DAT files and documentation |

**Romset types explained:**
- **Merged**: Smallest size. Parent game contains all regional variants and clones
- **Split**: Medium size. Clones only contain unique files, reference parent
- **Non-merged**: Largest size. Every ROM is fully self-contained (easiest to manage)

**Best for:** Comprehensive arcade coverage, Model 2/3, Naomi, Atomiswave (via CHDs)

### TeknoParrot (`/files/TeknoParrot/`)

Modern PC-based arcade game dumps. These are NOT traditional ROM dumps - they're Windows/Linux arcade games that run on TeknoParrot loader.

**Highlights include:**
- Sega Lindbergh/RingEdge/RingWide/Nu/ALLS titles
- Namco System 246/256/357/ES3/ES4 titles  
- Taito Type X/X2/X3/X4/NESiCAxLive titles
- Raw Thrills games (Cruis'n, Big Buck Hunter, etc.)

**Notable games:**
- Initial D Arcade Stage 4-8 + Zero
- House of the Dead 4, Scarlet Dawn
- Tekken 4-7
- Virtua Fighter 5 series
- Mario Kart Arcade GP DX
- Pokken Tournament
- Gundam Extreme VS series
- BlazBlue/Guilty Gear arcade versions
- Street Fighter IV/V arcade

**Size warning:** Many games are 5-20+ GB each. Total collection is 1+ TB.

---

## English Translations (`/files/T-En Collection/`)

Pre-patched ROMs with fan translations applied. **This is gold for Japanese-exclusive games.**

### By Platform

| Platform | Notable Translations |
|----------|---------------------|
| **Super Famicom** | Tons of RPGs - Seiken Densetsu 3, Fire Emblem, Dragon Quest, etc. |
| **Famicom** | Sweet Home, Mother (EarthBound Zero), many RPGs |
| **FDS** | Famicom Disk System exclusives |
| **PC Engine CD** | Ys series, Tengai Makyou, etc. |
| **Saturn** | Many JRPGs, Radiant Silvergun (menus), etc. |
| **PlayStation** | Tons of RPGs and visual novels |
| **PlayStation 2** | Growing collection |
| **Neo Geo CD** | Fighting game stories, RPGs |
| **Mega Drive** | Phantasy Star translations, etc. |
| **Game Gear** | Japanese-only titles |
| **Game Boy/GBC/GBA** | Many Pokemon hacks, RPGs |
| **Nintendo DS** | Huge collection of Japanese DS games |
| **N64** | A few notable titles |
| **Dreamcast** | Some visual novels, niche titles |
| **PSP** | Growing collection |
| **PC-98** | Visual novels, strategy games |
| **MSX/MSX2** | Japanese computer exclusives |

### Special Collections

| Folder | Description |
|--------|-------------|
| `Nintendo - Super Famicom - MSU1/` | MSU-1 CD audio hacks (Link to the Past, etc.) |
| `Nintendo - Super Famicom - Enhanced Colors/` | SA-1 graphics enhanced hacks |
| `Nintendo - Super Famicom - Speed Hacks/` | FastROM patches for better performance |
| `Sega - Mega Drive - MSU-MD/` | CD audio hacks for Genesis |
| `Sega - Mega Drive - Enhanced Colors/` | Visual enhancement patches |
| `Sega - 32X - MD+/` | Enhanced 32X versions |

---

## RetroAchievements Sets (`/files/RetroAchievements/`)

ROMs verified to work with [RetroAchievements](https://retroachievements.org/) - these are hash-matched to ensure achievements unlock properly.

Covers nearly every supported RA platform:
- All Nintendo systems (NES through GameCube)
- All Sega systems
- PlayStation 1 & 2
- PSP
- Arcade
- Many obscure systems (Arduboy, Mega Duck, WASM-4, etc.)

**Use case:** If you want achievements, use THESE ROMs.

---

## eXo Collections (`/files/eXo/`)

Curated, pre-configured collections maintained by eXoDOS project. Everything is ready to run with DOSBox/ScummVM pre-configured.

| Collection | Contents |
|------------|----------|
| `eXoDOS/` | ~7000 DOS games, fully configured |
| `eXoWin3x/` | Windows 3.1 games |
| `eXoWin9x/` | Windows 95/98 games |
| `eXoScummVM/` | Point-and-click adventures |
| `eXoDREAMM/` | LucasArts games (DREAMM emulator) |
| `eXoAppleIIGS/` | Apple IIGS games |
| `eXoIF/` | Interactive Fiction (text adventures) |
| `eXoDemoScene/` | Demoscene productions |
| `Linux Patches/` | Patches for running on Linux |

**Size:** eXoDOS alone is ~500 GB. These are COMPLETE collections.

---

## Internet Archive Mirrors (`/files/Internet Archive/`)

Mirrors of various Internet Archive uploaders' collections. Notable ones:

| Uploader | Contents |
|----------|----------|
| `chadmaster/` | CHD conversions (PSX, Saturn, Dreamcast, PSP, Neo Geo CD, etc.) |
| `romhacking_net/` | Romhacking.net patches archive |
| `bluemaxima/` | Flashpoint (Flash games preservation) |
| `renascene/` | PSP scene releases |

### chadmaster highlights:
- `chd_psx/` - PlayStation CHDs (US)
- `chd_psx_eur/` - PlayStation CHDs (Europe)
- `chd_psx_jap/` - PlayStation CHDs (Japan)
- `chd_saturn/` - Saturn CHDs
- `chd_segacd/` - Sega CD CHDs
- `dc-chd-zstd-redump/` - Dreamcast CHDs
- `ngcd-chd-zstd-redump/` - Neo Geo CD CHDs
- `pcecd-chd-zstd-redump/` - PC Engine CD CHDs
- `psp-chd-zstd-redump-part1/2/` - PSP CHDs
- `jagcd-chd-zstd/` - Jaguar CD CHDs
- `fbnarcade-fullnonmerged/` - FBNeo non-merged set
- `mame-merged/` - MAME merged set
- `nintendo-super-famicom-msu1/` - MSU-1 audio hacks
- `super-famicom-enhanced-colors/` - SA-1 color hacks
- `SegaMD-Enhanced-ROMs/` - Enhanced Genesis ROMs

---

## Other Notable Collections

### Hardware Target Game Database (`/files/Hardware Target Game Database/`)
ROMs organized for specific hardware targets (flash carts, ODEs, etc.)

### HBMAME (`/files/HBMAME/`)
Homebrew MAME - includes bootlegs, hacks, and homebrew arcade games

### Lost Level (`/files/Lost Level/`)
Prototype, unreleased, and development ROM dumps

### Total DOS Collection (`/files/Total DOS Collection/`)
Alternative to eXoDOS - all DOS software ever released

### TOSEC (`/files/TOSEC/`, `/files/TOSEC-ISO/`)
The Old School Emulation Center - focuses on preservation of EVERYTHING including all revisions, bad dumps, etc. Much larger than No-Intro/Redump but less curated.

### Laserdisc Collection (`/files/Laserdisc Collection/`)
For Dragon's Lair, Space Ace, and other laserdisc games

### Touhou Project Collection (`/files/Touhou Project Collection/`)
Complete Touhou game collection

---

## Recommended Downloads by Use Case

### "I want arcade games that work"
1. **FinalBurn Neo `arcade/`** for Neo Geo, CPS, 90s arcade
2. **MAME `ROMs (non-merged)/`** for everything else
3. **MAME `CHDs (merged)/`** for Naomi, Model 2/3, etc.

### "I want English-translated Japanese games"
1. **T-En Collection** - pick your platforms

### "I want achievements"
1. **RetroAchievements** sets (hash-verified)

### "I want DOS/Windows retro games"
1. **eXoDOS** or **eXoWin3x/eXoWin9x**

### "I want modern arcade (2000s+)"
1. **TeknoParrot** collection (requires TeknoParrot loader)

### "I want pre-converted CHDs"
1. **Internet Archive/chadmaster/** collections

---

## Batocera Integration Notes

For Batocera/Batocera integration:

| Collection | Batocera System | Notes |
|------------|-----------------|-------|
| FBNeo arcade | `fbneo`, `neogeo` | Use FBNeo core |
| MAME | `mame` | Match MAME version to romset |
| T-En ROMs | Same as parent system | Drop-in replacement |
| TeknoParrot | `windows` (Wine) | Complex setup required |
| eXoDOS | `dos` | May need manual config |

---

Last updated: 2025-12-06
