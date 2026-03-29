#!/bin/bash
# rclone-myrient-treasures.sh — Download high-value curated collections from Myrient
#
# Built from catalog analysis of 357 TB / 2.26M files across 21 collections.
# Prioritized by: uniqueness, curation quality, playability, and replaceability.
#
# Estimated totals by section:
#   translations   ~750 GB    T-En English fan translations (61 systems)
#   teknoparrot    ~1.7 TB    Modern arcade (TeknoParrot/RetroBat)
#   exo            ~2.2 TB    eXo curated DOS/Win/ScummVM collections
#   retroach       ~2.6 TB    RetroAchievements curated 1G1R sets
#   magazines      ~300 GB    Nintendo Power + cherry-picked TOSEC-PIX
#   curated        ~800 GB    Tiny Best Set, HTGDB, Lost Level, TDC
#   laserdisc      ~430 GB    Hypseus Singe laserdisc games (Batocera)
#   arcade         ~130 GB    FinalBurn Neo + MAME ROMs + HBMAME
#
# Usage:
#   ./rclone-myrient-treasures.sh                    # Run all sections in priority order
#   ./rclone-myrient-treasures.sh translations       # Just T-En translations
#   ./rclone-myrient-treasures.sh teknoparrot         # Just TeknoParrot
#   ./rclone-myrient-treasures.sh exo                 # Just eXo collections
#   ./rclone-myrient-treasures.sh retroach            # Just RetroAchievements
#   ./rclone-myrient-treasures.sh magazines           # Just magazines
#   ./rclone-myrient-treasures.sh curated             # Just curated sets
#   ./rclone-myrient-treasures.sh laserdisc           # Just laserdisc games
#   ./rclone-myrient-treasures.sh arcade              # Just arcade ROMs
#   ./rclone-myrient-treasures.sh status              # Show download progress
#
# Run in background:
#   nohup ./rclone-myrient-treasures.sh > /tmp/myrient-treasures.log 2>&1 &

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SYNC_CMD="${SCRIPT_DIR}/rclone_sync.sh"
BASE_PATH=/data/emu/source
MYRIENT="https://myrient.erista.me/files"
export RCLONE_VERBOSE=1

SECTION="${1:-all}"
STARTED_AT=$(date '+%Y-%m-%d %H:%M:%S')

log() { 
    echo ""
    echo "══════════════════════════════════════════════════════════════"
    echo "  $1"
    echo "  $(date '+%Y-%m-%d %H:%M:%S')"
    echo "══════════════════════════════════════════════════════════════"
    echo ""
}

check_space() {
    local avail_gb
    avail_gb=$(df --output=avail /data/emu | tail -1 | awk '{print int($1/1048576)}')
    if [ "$avail_gb" -lt 500 ]; then
        echo "WARNING: Only ${avail_gb} GB free on /data/emu — stopping to preserve space!"
        echo "Run 'jdupes -r -d /data/emu/source' to reclaim space, then re-run."
        exit 1
    fi
    echo "  Disk space available: ${avail_gb} GB"
}

# ═══════════════════════════════════════════════════════════════════════
# PRIORITY 1: T-En Collection — English Fan Translations (~750 GB)
# ═══════════════════════════════════════════════════════════════════════
# 61 systems of hand-translated Japanese games into English.
# Irreplaceable if community splinters. Every file is a playable game
# you literally couldn't play in English before.
# Includes: SNES (569 games), PS2, PSP, PS1, PS3, Dreamcast, Saturn,
#           NDS, GBA, Genesis/MD, N64, PC Engine, FM-Towns, and more.
sync_translations() {
    log "PRIORITY 1: T-En English Fan Translations (~750 GB)"
    check_space
    "$SYNC_CMD" "${MYRIENT}/T-En Collection" ${BASE_PATH}
}

# ═══════════════════════════════════════════════════════════════════════
# PRIORITY 2: TeknoParrot — Modern Arcade Games (~1.7 TB)
# ═══════════════════════════════════════════════════════════════════════
# 527 modern arcade game dumps that run via TeknoParrot on Windows/RetroBat.
# Sega, Namco, Taito, Raw Thrills, etc. — stuff you played in arcades
# in the 2000s-2020s. Can't get this organized anywhere else.
sync_teknoparrot() {
    log "PRIORITY 2: TeknoParrot — Modern Arcade Games (~1.7 TB)"
    check_space
    "$SYNC_CMD" "${MYRIENT}/TeknoParrot" ${BASE_PATH}
}

# ═══════════════════════════════════════════════════════════════════════
# PRIORITY 3: eXo Collections — Curated DOS/Windows Gaming (~2.2 TB)
# ═══════════════════════════════════════════════════════════════════════
# Pre-configured, ready-to-play collections. Gold standard for
# DOS/Windows gaming. Each game has DOSBox/ScummVM configs already set up.
#   eXoDOS:     15,626 files, 1.26 TB — definitive DOS gaming collection
#   eXoWin3x:    1,150 files, 346 GB  — Windows 3.x games
#   eXoWin9x:      680 files, 263 GB  — Windows 95/98 games
#   eXoScummVM:    683 files, 253 GB  — Point-and-click adventures
#   eXoDREAMM:      57 files,  80 GB  — LucasArts via DREAMM engine
#   eXoIF:         891 files,  16 GB  — Interactive fiction (Zork etc.)
#   eXoDemoScene: 2,486 files,   9 GB — Demoscene demos
#   eXoAppleIIGS:   475 files,   9 GB — Apple IIGS games
#   Linux Patches:   38 files,   6 GB — Linux compatibility patches
sync_exo() {
    log "PRIORITY 3: eXo Collections (~2.2 TB)"
    check_space

    log "eXoDOS (15,626 games, ~1.26 TB)"
    "$SYNC_CMD" "${MYRIENT}/eXo/eXoDOS" ${BASE_PATH}

    log "eXoScummVM (683 games, ~253 GB)"
    "$SYNC_CMD" "${MYRIENT}/eXo/eXoScummVM" ${BASE_PATH}

    log "eXoWin3x (1,150 games, ~346 GB)"
    "$SYNC_CMD" "${MYRIENT}/eXo/eXoWin3x" ${BASE_PATH}

    log "eXoWin9x (680 games, ~263 GB)"
    "$SYNC_CMD" "${MYRIENT}/eXo/eXoWin9x" ${BASE_PATH}

    log "eXoDREAMM (57 games, ~80 GB)"
    "$SYNC_CMD" "${MYRIENT}/eXo/eXoDREAMM" ${BASE_PATH}

    log "eXoIF — Interactive Fiction (~16 GB)"
    "$SYNC_CMD" "${MYRIENT}/eXo/eXoIF" ${BASE_PATH}

    log "eXoDemoScene (~9 GB)"
    "$SYNC_CMD" "${MYRIENT}/eXo/eXoDemoScene" ${BASE_PATH}

    log "eXoAppleIIGS (~9 GB)"
    "$SYNC_CMD" "${MYRIENT}/eXo/eXoAppleIIGS" ${BASE_PATH}

    log "eXo Linux Patches (~6 GB)"
    "$SYNC_CMD" "${MYRIENT}/eXo/Linux Patches" ${BASE_PATH}
}

# ═══════════════════════════════════════════════════════════════════════
# PRIORITY 4: RetroAchievements — Curated 1G1R Sets (~2.6 TB)
# ═══════════════════════════════════════════════════════════════════════
# Pre-curated "best version" ROM sets that work with RetroAchievements.
# These are THE definitive 1G1R picks for 53 systems. Includes:
#   PS2 (1.7 TB), PS1 (307 GB), PSP (219 GB), GameCube (194 GB),
#   Dreamcast (89 GB), Saturn (49 GB), NDS (33 GB), Sega CD (23 GB),
#   TurboGrafx-CD (19 GB), N64 (12 GB), plus 43 smaller systems.
sync_retroach() {
    log "PRIORITY 4: RetroAchievements — Curated 1G1R Sets (~2.6 TB)"
    check_space
    "$SYNC_CMD" "${MYRIENT}/RetroAchievements" ${BASE_PATH}
}

# ═══════════════════════════════════════════════════════════════════════
# PRIORITY 5: Magazines & Publications (~300 GB)
# ═══════════════════════════════════════════════════════════════════════
# Gaming history in print form. Mix of complete runs and partial collections.
#
# Nintendo Power Issues 1-285 (complete run): 285 files, 37 GB
# No-Intro Magazine Scans (PDF):             595 files, 89 GB  (Famitsu, RePlay, etc.)
# No-Intro Magazine Scans (CBZ):             195 files, 204 GB (archival quality)
#
# TOSEC-PIX cherry picks (English gaming magazines):
#   Electronic Gaming Monthly:   203 issues, ~43 GB
#   Retro Gamer:                 142 issues, ~30 GB
#   Computer Gaming World:       454 issues, ~129 GB  (skip — big, niche)
#   Edge:                        374 issues, ~23 GB
#   Game Informer:                90 issues, ~16 GB  (AU edition mostly)
#   N64 Magazine:                 64 issues, ~15 GB
#   Nintendo:                  1,952 files, ~157 GB  (TOSEC-PIX/Nintendo — guides, manuals, etc.)
#
# NOTE: Full TOSEC-PIX is 2.3 TB. We cherry-pick the most interesting.
sync_magazines() {
    log "PRIORITY 5: Magazines & Publications"
    check_space

    # Nintendo Power — complete run, Issues 1-285 (37 GB)
    log "Nintendo Power Issues 1-285 (37 GB)"
    "$SYNC_CMD" "${MYRIENT}/Miscellaneous/Nintendo Power Issues 1-285" ${BASE_PATH}

    # No-Intro magazine scans — PDF format (89 GB, most usable)
    log "No-Intro Magazine Scans PDF (89 GB)"
    "$SYNC_CMD" "${MYRIENT}/No-Intro/Unofficial - Video Game Magazine Scans (PDF)" ${BASE_PATH}

    # No-Intro magazine scans — CBZ format (204 GB, archival)
    log "No-Intro Magazine Scans CBZ (204 GB)"
    "$SYNC_CMD" "${MYRIENT}/No-Intro/Unofficial - Video Game Magazine Scans (CBZ)" ${BASE_PATH}

    # Super Mario 64 Complete Guide Book (2 GB — nostalgia)
    log "Super Mario 64 Guide Book (2 GB)"
    "$SYNC_CMD" "${MYRIENT}/Miscellaneous/Super Mario 64 Complete Guide Book" ${BASE_PATH}

    # TOSEC-PIX: Multi-format magazine scans (668 GB — EGM, Edge, Retro Gamer, etc.)
    # This is the big one with 9,243 files of cross-platform gaming magazines
    log "TOSEC-PIX Multi-format Magazines (668 GB — EGM, Edge, CGW, Retro Gamer, etc.)"
    "$SYNC_CMD" "${MYRIENT}/TOSEC-PIX/Multi-format" ${BASE_PATH}

    # TOSEC-PIX: Nintendo-specific publications (157 GB)
    log "TOSEC-PIX Nintendo Publications (157 GB)"
    "$SYNC_CMD" "${MYRIENT}/TOSEC-PIX/Nintendo" ${BASE_PATH}

    # TOSEC-PIX: Sony publications (135 GB)
    log "TOSEC-PIX Sony Publications (135 GB)"
    "$SYNC_CMD" "${MYRIENT}/TOSEC-PIX/Sony" ${BASE_PATH}

    # TOSEC-PIX: Sega publications (98 GB)
    log "TOSEC-PIX Sega Publications (98 GB)"
    "$SYNC_CMD" "${MYRIENT}/TOSEC-PIX/Sega" ${BASE_PATH}

    # TOSEC-PIX: Microsoft/Xbox publications (77 GB)
    log "TOSEC-PIX Microsoft Publications (77 GB)"
    "$SYNC_CMD" "${MYRIENT}/TOSEC-PIX/Microsoft" ${BASE_PATH}
}

# ═══════════════════════════════════════════════════════════════════════
# PRIORITY 6: Other Curated Collections (~800 GB)
# ═══════════════════════════════════════════════════════════════════════
sync_curated() {
    log "PRIORITY 6: Other Curated Collections"
    check_space

    # Tiny Best Set: GO! — curated "best of" across all systems (97 GB)
    # Perfect starter/demo collection, already filtered to essentials
    log "Tiny Best Set: GO! (97 GB)"
    "$SYNC_CMD" "${MYRIENT}/Miscellaneous/Tiny Best Set: GO!" ${BASE_PATH}

    # Hardware Target Game Database — curated for flashcarts & FPGA (400 GB)
    # EverDrive, MiSTer, Darksoft, MegaSD sets — already filtered
    log "Hardware Target Game Database (400 GB)"
    "$SYNC_CMD" "${MYRIENT}/Hardware Target Game Database" ${BASE_PATH}

    # Lost Level — prototypes, unreleased games, betas (296 GB)
    # Unique content that literally doesn't exist elsewhere
    log "Lost Level Archive (296 GB)"
    "$SYNC_CMD" "${MYRIENT}/Lost Level" ${BASE_PATH}

    # Total DOS Collection (1 TB — overlaps eXoDOS but different curation)
    # 41,719 DOS games in the Games section alone
    log "Total DOS Collection (~1 TB)"
    "$SYNC_CMD" "${MYRIENT}/Total DOS Collection/Games" ${BASE_PATH}
    "$SYNC_CMD" "${MYRIENT}/Total DOS Collection/Applications" ${BASE_PATH}
    "$SYNC_CMD" "${MYRIENT}/Total DOS Collection/Drivers" ${BASE_PATH}
}

# ═══════════════════════════════════════════════════════════════════════
# PRIORITY 7: Laserdisc Games (~430 GB)
# ═══════════════════════════════════════════════════════════════════════
# Dragon's Lair, Space Ace, etc. — Batocera supports Hypseus Singe natively.
# Also grab the HD AI-enhanced versions and Daphne format.
sync_laserdisc() {
    log "PRIORITY 7: Laserdisc Games"
    check_space

    # Hypseus Singe — main laserdisc game collection (244 GB)
    log "Hypseus Singe (244 GB)"
    "$SYNC_CMD" "${MYRIENT}/Laserdisc Collection/Hypseus Singe" ${BASE_PATH}

    # Hypseus Singe HD [AI enhanced] — upscaled versions (185 GB)
    log "Hypseus Singe HD AI Enhanced (185 GB)"
    "$SYNC_CMD" "${MYRIENT}/Laserdisc Collection/Hypseus Singe HD [AI enhanced]" ${BASE_PATH}

    # Hypseus Singe [Daphne] — legacy Daphne-compatible format (37 GB)
    log "Hypseus Singe Daphne format (37 GB)"
    "$SYNC_CMD" "${MYRIENT}/Laserdisc Collection/Hypseus Singe [Daphne]" ${BASE_PATH}

    # Hypseus Singe 4K [standalone] (12 GB)
    log "Hypseus Singe 4K Standalone (12 GB)"
    "$SYNC_CMD" "${MYRIENT}/Laserdisc Collection/Hypseus Singe 4K [standalone]" ${BASE_PATH}

    # LD Ports — laserdisc game ports to other platforms (430 GB)
    log "LD Ports (430 GB)"
    "$SYNC_CMD" "${MYRIENT}/Laserdisc Collection/Various - LD Ports" ${BASE_PATH}

    # Standalone players (2 GB)
    log "Standalone Players (2 GB)"
    "$SYNC_CMD" "${MYRIENT}/Laserdisc Collection/Standalone" ${BASE_PATH}

    # LD ROMs (0.3 GB)
    "$SYNC_CMD" "${MYRIENT}/Laserdisc Collection/Various - LD ROMs" ${BASE_PATH}
}

# ═══════════════════════════════════════════════════════════════════════
# PRIORITY 8: Arcade ROM Sets (~130 GB)
# ═══════════════════════════════════════════════════════════════════════
# FinalBurn Neo is a lighter/faster alternative to MAME.
# MAME merged ROMs are the canonical arcade set.
# HBMAME is homebrew/hack MAME games.
sync_arcade() {
    log "PRIORITY 8: Arcade ROM Sets"
    check_space

    # FinalBurn Neo — all systems (28 GB total)
    log "FinalBurn Neo (28 GB)"
    "$SYNC_CMD" "${MYRIENT}/FinalBurn Neo" ${BASE_PATH}

    # MAME ROMs merged (84 GB — canonical arcade set)
    log "MAME ROMs merged (84 GB)"
    "$SYNC_CMD" "${MYRIENT}/MAME/ROMs (merged)" ${BASE_PATH}

    # MAME BIOS/devices (0.6 GB — needed for MAME to work)
    log "MAME BIOS-devices (0.6 GB)"
    "$SYNC_CMD" "${MYRIENT}/MAME/ROMs (bios-devices)" ${BASE_PATH}

    # HBMAME — homebrew/hacked arcade games (36 GB total)
    log "HBMAME (36 GB)"
    "$SYNC_CMD" "${MYRIENT}/HBMAME" ${BASE_PATH}
}

# ═══════════════════════════════════════════════════════════════════════
# PRIORITY 9: Miscellaneous Interesting Items
# ═══════════════════════════════════════════════════════════════════════
sync_misc() {
    log "PRIORITY 9: Miscellaneous Interesting Items"
    check_space

    # Touhou Project Collection — fan content + official (426 GB)
    log "Touhou Project Collection (426 GB)"
    "$SYNC_CMD" "${MYRIENT}/Touhou Project Collection" ${BASE_PATH}

    # Atari Mania (tiny — 5,178 files of Atari history)
    log "Atari Mania"
    "$SYNC_CMD" "${MYRIENT}/Miscellaneous/Atari Mania" ${BASE_PATH}

    # No-Intro Manual Scans (tiny)
    log "No-Intro Video Game Manual Scans"
    "$SYNC_CMD" "${MYRIENT}/No-Intro/Unofficial - Video Game Manual Scans (JPEG)" ${BASE_PATH}

    # Valve Developer Repository (31 GB — Source engine history)
    log "Valve Developer Repository (31 GB)"
    "$SYNC_CMD" "${MYRIENT}/Miscellaneous/Valve Developer Repository" ${BASE_PATH}
}

# ═══════════════════════════════════════════════════════════════════════
# STATUS — show what's been downloaded and what's left
# ═══════════════════════════════════════════════════════════════════════
show_status() {
    echo ""
    echo "═══════════════════════════════════════════════"
    echo "  Myrient Treasures — Download Status"
    echo "═══════════════════════════════════════════════"
    echo ""

    local base="/data/emu/source/myrient.erista.me/files"

    declare -A targets
    targets["T-En Collection"]="750 GB"
    targets["TeknoParrot"]="1.7 TB"
    targets["eXo"]="2.2 TB"
    targets["RetroAchievements"]="2.6 TB"
    targets["Miscellaneous/Nintendo Power Issues 1-285"]="37 GB"
    targets["No-Intro/Unofficial - Video Game Magazine Scans (PDF)"]="89 GB"
    targets["No-Intro/Unofficial - Video Game Magazine Scans (CBZ)"]="204 GB"
    targets["TOSEC-PIX/Multi-format"]="668 GB"
    targets["Miscellaneous/Tiny Best Set: GO!"]="97 GB"
    targets["Hardware Target Game Database"]="400 GB"
    targets["Lost Level"]="296 GB"
    targets["Total DOS Collection"]="1 TB"
    targets["Laserdisc Collection/Hypseus Singe"]="244 GB"
    targets["FinalBurn Neo"]="28 GB"
    targets["MAME/ROMs (merged)"]="84 GB"
    targets["HBMAME"]="36 GB"
    targets["Touhou Project Collection"]="426 GB"

    for target in "${!targets[@]}"; do
        local dir="${base}/${target}"
        if [ -d "$dir" ]; then
            local size
            size=$(du -sh "$dir" 2>/dev/null | cut -f1)
            echo "  ✓ ${target}: ${size} / ${targets[$target]}"
        else
            echo "  ○ ${target}: not started (target: ${targets[$target]})"
        fi
    done

    echo ""
    echo "  Disk: $(df -h /data/emu | tail -1 | awk '{print $4 " free / " $2 " total (" $5 " used)"}')"
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════
# DISPATCHER
# ═══════════════════════════════════════════════════════════════════════
case "$SECTION" in
    translations) sync_translations ;;
    teknoparrot)  sync_teknoparrot ;;
    exo)          sync_exo ;;
    retroach)     sync_retroach ;;
    magazines)    sync_magazines ;;
    curated)      sync_curated ;;
    laserdisc)    sync_laserdisc ;;
    arcade)       sync_arcade ;;
    misc)         sync_misc ;;
    status)       show_status ;;
    all)
        log "Starting full treasure hunt — $(date)"
        echo "Estimated total: ~9+ TB across 9 sections"
        echo ""

        # Order: smallest/most-valuable first, biggest last
        sync_translations   # ~750 GB   — irreplaceable fan translations
        sync_arcade         # ~130 GB   — FBNeo + MAME merged + HBMAME
        sync_magazines      # ~300 GB   — Nintendo Power + TOSEC-PIX picks
        sync_curated        # ~800 GB   — Tiny Best Set, HTGDB, Lost Level, TDC
        sync_laserdisc      # ~430 GB   — Hypseus Singe for Batocera
        sync_teknoparrot    # ~1.7 TB   — modern arcade
        sync_exo            # ~2.2 TB   — curated DOS/Windows
        sync_retroach       # ~2.6 TB   — curated 1G1R sets
        sync_misc           # ~500 GB   — Touhou, Valve, Atari Mania

        log "ALL SECTIONS COMPLETE — started ${STARTED_AT}, finished $(date)"
        ;;
    *)
        echo "Myrient Treasures — High-Value Collection Downloader"
        echo ""
        echo "Usage: $0 [SECTION]"
        echo ""
        echo "Sections (in priority order):"
        echo "  translations   T-En English fan translations (61 systems, ~750 GB)"
        echo "  teknoparrot    TeknoParrot modern arcade games (~1.7 TB)"
        echo "  exo            eXo curated DOS/Win/ScummVM (~2.2 TB)"
        echo "  retroach       RetroAchievements curated 1G1R (~2.6 TB)"
        echo "  magazines      Nintendo Power + TOSEC-PIX picks (~300 GB)"
        echo "  curated        Tiny Best Set, HTGDB, Lost Level, TDC (~800 GB)"
        echo "  laserdisc      Hypseus Singe laserdisc games (~430 GB)"
        echo "  arcade         FinalBurn Neo + MAME merged + HBMAME (~130 GB)"
        echo "  misc           Touhou, Valve repo, Atari Mania (~500 GB)"
        echo "  status         Show download progress"
        echo "  all            Run everything in priority order"
        echo ""
        echo "Examples:"
        echo "  $0 translations                    # Just the fan translations"
        echo "  $0 all                             # Everything"
        echo "  nohup $0 all > /tmp/myrient-treasures.log 2>&1 &"
        exit 0
        ;;
esac
