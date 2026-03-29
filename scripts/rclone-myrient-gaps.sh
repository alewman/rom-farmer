#!/bin/bash
# rclone-myrient-gaps.sh — Download priority gaps before Myrient shutdown (March 2026)
#
# This script downloads collections we DON'T already have locally.
# The original rclone-myrient.sh covers No-Intro/Redump systems we already sync.
# This one fills the gaps identified in our analysis.
#
# Estimated total: ~3.7 TB (fits easily within our 24 TB free)
#
# Usage:
#   ./rclone-myrient-gaps.sh          # Run everything
#   ./rclone-myrient-gaps.sh dos      # Just DOS/PC collections
#   ./rclone-myrient-gaps.sh redump   # Just missing Redump systems
#   ./rclone-myrient-gaps.sh nointro  # Just missing No-Intro systems
#   ./rclone-myrient-gaps.sh exo      # Just eXo collections
#   ./rclone-myrient-gaps.sh extras   # Nice-to-have extras

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SYNC_CMD="${SCRIPT_DIR}/rclone_sync.sh"
BASE_PATH=/data/emu/source
export RCLONE_VERBOSE=1

SECTION="${1:-all}"

log() { echo ""; echo "========== $1 =========="; echo ""; }

# ─────────────────────────────────────────────────────────────────────
# PRIORITY 1: DOS / PC Gaming (~3.1 TB)
# ─────────────────────────────────────────────────────────────────────
sync_dos() {
    log "PRIORITY 1: DOS / PC Gaming"

    # eXoDOS — curated, pre-configured DOSBox packages (~1.2 TB)
    log "eXo / eXoDOS (~1.2 TB)"
    "$SYNC_CMD" "https://myrient.erista.me/files/eXo/eXoDOS" ${BASE_PATH}

    # eXoScummVM — pre-configured ScummVM adventure games (~253 GB)
    log "eXo / eXoScummVM (~253 GB)"
    "$SYNC_CMD" "https://myrient.erista.me/files/eXo/eXoScummVM" ${BASE_PATH}

    # eXoDREAMM — LucasArts games via DREAMM engine (~80 GB)
    log "eXo / eXoDREAMM (~80 GB)"
    "$SYNC_CMD" "https://myrient.erista.me/files/eXo/eXoDREAMM" ${BASE_PATH}

    # eXoWin3x — Windows 3.x games (~346 GB)
    log "eXo / eXoWin3x (~346 GB)"
    "$SYNC_CMD" "https://myrient.erista.me/files/eXo/eXoWin3x" ${BASE_PATH}

    # eXoWin9x — Windows 9x games (~263 GB)
    log "eXo / eXoWin9x (~263 GB)"
    "$SYNC_CMD" "https://myrient.erista.me/files/eXo/eXoWin9x" ${BASE_PATH}

    # Total DOS Collection - Games (~1.0 TB, raw archive with everything)
    log "Total DOS Collection / Games (~1.0 TB)"
    "$SYNC_CMD" "https://myrient.erista.me/files/Total DOS Collection/Games" ${BASE_PATH}

    # Total DOS Collection - Applications (~1.8 GB)
    log "Total DOS Collection / Applications (~1.8 GB)"
    "$SYNC_CMD" "https://myrient.erista.me/files/Total DOS Collection/Applications" ${BASE_PATH}

    # Total DOS Collection - Drivers (~7 MB)
    "$SYNC_CMD" "https://myrient.erista.me/files/Total DOS Collection/Drivers" ${BASE_PATH}
}

# ─────────────────────────────────────────────────────────────────────
# PRIORITY 2: Missing Redump disc systems (~541 GB)
# ─────────────────────────────────────────────────────────────────────
sync_redump() {
    log "PRIORITY 2: Missing Redump disc systems"

    # Commodore - Amiga CD (~251 GB) — Batocera: PUAE
    "$SYNC_CMD" "https://myrient.erista.me/files/Redump/Commodore - Amiga CD" ${BASE_PATH}

    # Fujitsu - FM-Towns (~217 GB) — Batocera: Tsugaru
    "$SYNC_CMD" "https://myrient.erista.me/files/Redump/Fujitsu - FM-Towns" ${BASE_PATH}

    # Bandai - Playdia (~20 GB)
    "$SYNC_CMD" "https://myrient.erista.me/files/Redump/Bandai - Playdia Quick Interactive System" ${BASE_PATH}

    # NEC - PC-98 series (~22 GB) — Batocera: np2kai
    "$SYNC_CMD" "https://myrient.erista.me/files/Redump/NEC - PC-98 series" ${BASE_PATH}

    # Commodore - Amiga CDTV (~11 GB) — Batocera: PUAE
    "$SYNC_CMD" "https://myrient.erista.me/files/Redump/Commodore - Amiga CDTV" ${BASE_PATH}

    # Sharp - X68000 (~9 GB) — Batocera: px68k
    "$SYNC_CMD" "https://myrient.erista.me/files/Redump/Sharp - X68000" ${BASE_PATH}

    # VM Labs - NUON (~8 GB) — experimental
    "$SYNC_CMD" "https://myrient.erista.me/files/Redump/VM Labs - NUON" ${BASE_PATH}

    # NEC - PC-88 series (~1.4 GB) — Batocera: quasi88
    "$SYNC_CMD" "https://myrient.erista.me/files/Redump/NEC - PC-88 series" ${BASE_PATH}

    # Mattel - HyperScan (~650 MB)
    "$SYNC_CMD" "https://myrient.erista.me/files/Redump/Mattel - HyperScan" ${BASE_PATH}

    # IBM - PC compatible (disc images — size TBD, has 28 subdirs)
    "$SYNC_CMD" "https://myrient.erista.me/files/Redump/IBM - PC compatible" ${BASE_PATH}

    # Apple - Macintosh (disc images)
    "$SYNC_CMD" "https://myrient.erista.me/files/Redump/Apple - Macintosh" ${BASE_PATH}
}

# ─────────────────────────────────────────────────────────────────────
# PRIORITY 3: Missing No-Intro cartridge/ROM systems (< 1 GB total)
# ─────────────────────────────────────────────────────────────────────
sync_nointro() {
    log "PRIORITY 3: Missing No-Intro systems (tiny)"

    # Atari ST (~109 MB) — Batocera: Hatari
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Atari - Atari ST" ${BASE_PATH}

    # Atari 8-bit Family (~3 MB) — Batocera: Atari800
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Atari - 8-bit Family" ${BASE_PATH}

    # Commodore Amiga (floppy ROMs)
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Commodore - Amiga" ${BASE_PATH}

    # Emerson Arcadia 2001 (~180 KB)
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Emerson - Arcadia 2001" ${BASE_PATH}

    # Epoch Super Cassette Vision (~679 KB)
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Epoch - Super Cassette Vision" ${BASE_PATH}

    # Funtech Super Acan (~12 MB)
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Funtech - Super Acan" ${BASE_PATH}

    # Hartung Game Master (~161 KB)
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Hartung - Game Master" ${BASE_PATH}

    # Interton VC 4000 (~118 KB)
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Interton - VC 4000" ${BASE_PATH}

    # Tiger Game.com (~10 MB)
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Tiger - Game.com" ${BASE_PATH}

    # Casio Loopy (~15 MB)
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Casio - Loopy (BigEndian)" ${BASE_PATH}

    # RCA Studio II (~18 KB)
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/RCA - Studio II" ${BASE_PATH}

    # Philips Videopac+ (~163 KB)
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Philips - Videopac+" ${BASE_PATH}

    # NEC PC-98 No-Intro set (~13 MB)
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/NEC - PC-98" ${BASE_PATH}

    # Nokia N-Gage (~20 MB)
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nokia - N-Gage (WIP)" ${BASE_PATH}

    # Watara Supervision
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Watara - Supervision" ${BASE_PATH}

    # VTech V.Smile
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/VTech - V.Smile" ${BASE_PATH}

    # Bit Corporation Gamate
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Bit Corporation - Gamate" ${BASE_PATH}

    # Entex Adventure Vision
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Entex - Adventure Vision" ${BASE_PATH}

    # Nichibutsu My Vision
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nichibutsu - My Vision" ${BASE_PATH}

    # Epoch Game Pocket Computer
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Epoch - Game Pocket Computer" ${BASE_PATH}

    # Welback Mega Duck
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Welback - Mega Duck" ${BASE_PATH}

    # Casio PV-1000
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Casio - PV-1000" ${BASE_PATH}

    # Bandai Design Master
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Bandai - Design Master Denshi Mangajuku" ${BASE_PATH}

    # Sega Beena
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Sega - Beena" ${BASE_PATH}

    # Nintendo Family Computer Disk System (QD format)
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Family Computer Disk System (QD)" ${BASE_PATH}

    # VTech CreatiVision
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/VTech - CreatiVision" ${BASE_PATH}

    # Sharp X68000 (Flux)
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Sharp - X68000 (Flux)" ${BASE_PATH}

    # GamePark GP32 / GP2X
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/GamePark - GP32" ${BASE_PATH}
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/GamePark - GP2X" ${BASE_PATH}

    # Benesse Pocket Challenge
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Benesse - Pocket Challenge V2" ${BASE_PATH}
    "$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Benesse - Pocket Challenge W" ${BASE_PATH}
}

# ─────────────────────────────────────────────────────────────────────
# PRIORITY 3.5: eXo extras (~34 GB)
# ─────────────────────────────────────────────────────────────────────
sync_exo_extras() {
    log "eXo extras"

    # eXoIF — Interactive Fiction (~16 GB)
    "$SYNC_CMD" "https://myrient.erista.me/files/eXo/eXoIF" ${BASE_PATH}

    # eXoDemoScene (~9 GB)
    "$SYNC_CMD" "https://myrient.erista.me/files/eXo/eXoDemoScene" ${BASE_PATH}

    # eXoAppleIIGS (~9 GB)
    "$SYNC_CMD" "https://myrient.erista.me/files/eXo/eXoAppleIIGS" ${BASE_PATH}

    # Linux Patches for eXo (~6 GB)
    "$SYNC_CMD" "https://myrient.erista.me/files/eXo/Linux Patches" ${BASE_PATH}
}

# ─────────────────────────────────────────────────────────────────────
# PRIORITY 4: T-En fan translations & other extras
# ─────────────────────────────────────────────────────────────────────
sync_extras() {
    log "PRIORITY 4: T-En translations & extras"

    # T-En Collection — English fan translations (61 systems, size unknown but likely small)
    # These are patches/translated ROMs, very useful for Batocera
    "$SYNC_CMD" "https://myrient.erista.me/files/T-En Collection" ${BASE_PATH}

    # RetroAchievements hash sets (53 systems)
    "$SYNC_CMD" "https://myrient.erista.me/files/RetroAchievements" ${BASE_PATH}
}

# ─────────────────────────────────────────────────────────────────────
# DISPATCHER
# ─────────────────────────────────────────────────────────────────────
case "$SECTION" in
    dos)     sync_dos ;;
    redump)  sync_redump ;;
    nointro) sync_nointro ;;
    exo)     sync_exo_extras ;;
    extras)  sync_extras ;;
    all)
        sync_nointro    # tiny, do first
        sync_redump     # medium
        sync_exo_extras # medium
        sync_extras     # unknown but likely small
        sync_dos        # biggest, do last
        ;;
    *)
        echo "Usage: $0 [all|dos|redump|nointro|exo|extras]"
        exit 1
        ;;
esac

log "DONE — $SECTION sync complete"
