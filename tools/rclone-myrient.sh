#!/bin/bash
#===============================================================================
# ROM Farmer - Myrient Download Script
#===============================================================================
# Downloads ROM sets from Myrient using rclone
#
# Usage: ./rclone-myrient.sh [section]
#   section: all, nointro, redump, arcade, translations, chd, misc
#   (default: all)
#
# Requires: /usr/local/bin/rclone_sync.sh helper script
#
# Notes:
#   - Large systems (PS2, PS3, Xbox, Wii, etc.) use "*(*USA*)*" filter
#   - CD systems can be downloaded as pre-converted CHDs (see CHD section)
#   - For arcade, consider FBNeo for simpler setup, MAME for completeness
#===============================================================================

set -e

BASE_PATH="${MYRIENT_BASE_PATH:-/data/emu/source}"
SYNC_CMD="/usr/local/bin/rclone_sync.sh"
export RCLONE_VERBOSE=1

# Parse arguments
SECTION="${1:-all}"

# Helper function for syncing
sync() {
    local url="$1"
    local filter="${2:-}"
    
    if [ -n "$filter" ]; then
        echo "==> Syncing: $url (filter: $filter)"
        $SYNC_CMD "$url" "$BASE_PATH" "$filter"
    else
        echo "==> Syncing: $url"
        $SYNC_CMD "$url" "$BASE_PATH"
    fi
}

#===============================================================================
# NO-INTRO CARTRIDGE SETS
#===============================================================================
sync_nointro() {
    echo ""
    echo "=============================================="
    echo "NO-INTRO CARTRIDGE SETS"
    echo "=============================================="
    
    #---------------------------------------------------------------------------
    # ATARI
    #---------------------------------------------------------------------------
    echo "--- Atari Systems ---"
    sync "https://myrient.erista.me/files/No-Intro/Atari - Atari 2600"
    sync "https://myrient.erista.me/files/No-Intro/Atari - Atari 2600 (Aftermarket)"
    sync "https://myrient.erista.me/files/No-Intro/Atari - Atari 5200"
    sync "https://myrient.erista.me/files/No-Intro/Atari - Atari 7800 (BIN)"
    sync "https://myrient.erista.me/files/No-Intro/Atari - Atari 7800 (BIN) (Aftermarket)"
    sync "https://myrient.erista.me/files/No-Intro/Atari - Atari Jaguar (J64)"
    sync "https://myrient.erista.me/files/No-Intro/Atari - Atari Jaguar (J64) (Aftermarket)"
    sync "https://myrient.erista.me/files/No-Intro/Atari - Atari Lynx (LYX)"
    sync "https://myrient.erista.me/files/No-Intro/Atari - Atari Lynx (LYX) (Aftermarket)"
    
    #---------------------------------------------------------------------------
    # NINTENDO CARTRIDGE
    #---------------------------------------------------------------------------
    echo "--- Nintendo Cartridge Systems ---"
    # NES/Famicom
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Nintendo Entertainment System (Headered)"
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Nintendo Entertainment System (Headered) (Aftermarket)"
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Family Computer Disk System (FDS)"
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Family Computer Disk System (FDS) (Aftermarket)"
    
    # SNES
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Super Nintendo Entertainment System"
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Super Nintendo Entertainment System (Aftermarket)"
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Satellaview"
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Sufami Turbo"
    
    # N64
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Nintendo 64 (BigEndian)"
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Nintendo 64 (BigEndian) (Aftermarket)"
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Nintendo 64DD"
    
    # Game Boy
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Game Boy"
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Game Boy (Aftermarket)"
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Game Boy Color"
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Game Boy Color (Aftermarket)"
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Game Boy Advance"
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Game Boy Advance (Aftermarket)"
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Game Boy Advance (Multiboot)"
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Game Boy Advance (Video)"
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Game Boy Advance (e-Reader)"
    
    # DS/3DS (Decrypted for emulator compatibility)
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Nintendo DS (Decrypted)"
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Nintendo DS (Decrypted) (Aftermarket)"
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Nintendo DSi (Decrypted)"
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Nintendo DSi (Digital) (CDN) (Decrypted)"
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Nintendo 3DS (Decrypted)"
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - New Nintendo 3DS (Decrypted)"
    
    # Other Nintendo
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Virtual Boy"
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Virtual Boy (Aftermarket)"
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Pokemon Mini"
    sync "https://myrient.erista.me/files/No-Intro/Nintendo - Game & Watch"
    
    #---------------------------------------------------------------------------
    # SEGA CARTRIDGE
    #---------------------------------------------------------------------------
    echo "--- Sega Cartridge Systems ---"
    sync "https://myrient.erista.me/files/No-Intro/Sega - SG-1000 - SC-3000"
    sync "https://myrient.erista.me/files/No-Intro/Sega - SG-1000 - SC-3000 (Aftermarket)"
    sync "https://myrient.erista.me/files/No-Intro/Sega - Master System - Mark III"
    sync "https://myrient.erista.me/files/No-Intro/Sega - Master System - Mark III (Aftermarket)"
    sync "https://myrient.erista.me/files/No-Intro/Sega - Game Gear"
    sync "https://myrient.erista.me/files/No-Intro/Sega - Game Gear (Aftermarket)"
    sync "https://myrient.erista.me/files/No-Intro/Sega - Mega Drive - Genesis"
    sync "https://myrient.erista.me/files/No-Intro/Sega - Mega Drive - Genesis (Aftermarket)"
    sync "https://myrient.erista.me/files/No-Intro/Sega - 32X"
    sync "https://myrient.erista.me/files/No-Intro/Sega - PICO"
    
    #---------------------------------------------------------------------------
    # NEC
    #---------------------------------------------------------------------------
    echo "--- NEC Systems ---"
    sync "https://myrient.erista.me/files/No-Intro/NEC - PC Engine - TurboGrafx-16"
    sync "https://myrient.erista.me/files/No-Intro/NEC - PC Engine - TurboGrafx-16 (Aftermarket)"
    sync "https://myrient.erista.me/files/No-Intro/NEC - PC Engine SuperGrafx"
    sync "https://myrient.erista.me/files/No-Intro/NEC - PC Engine SuperGrafx (Aftermarket)"
    
    #---------------------------------------------------------------------------
    # SNK
    #---------------------------------------------------------------------------
    echo "--- SNK Systems ---"
    sync "https://myrient.erista.me/files/No-Intro/SNK - NeoGeo Pocket"
    # Note: No (Aftermarket) folder exists for NeoGeo Pocket on Myrient
    sync "https://myrient.erista.me/files/No-Intro/SNK - NeoGeo Pocket Color"
    # Note: No (Aftermarket) folder exists for NeoGeo Pocket Color on Myrient
    
    #---------------------------------------------------------------------------
    # BANDAI
    #---------------------------------------------------------------------------
    echo "--- Bandai Systems ---"
    sync "https://myrient.erista.me/files/No-Intro/Bandai - WonderSwan"
    # Note: WonderSwan (Aftermarket) does not exist on Myrient
    sync "https://myrient.erista.me/files/No-Intro/Bandai - WonderSwan Color"
    sync "https://myrient.erista.me/files/No-Intro/Bandai - WonderSwan Color (Aftermarket)"
    
    #---------------------------------------------------------------------------
    # OTHER CARTRIDGE SYSTEMS
    #---------------------------------------------------------------------------
    echo "--- Other Cartridge Systems ---"
    # Coleco
    sync "https://myrient.erista.me/files/No-Intro/Coleco - ColecoVision"
    # Note: ColecoVision (Aftermarket) does not exist on Myrient
    
    # Intellivision
    sync "https://myrient.erista.me/files/No-Intro/Mattel - Intellivision"
    sync "https://myrient.erista.me/files/No-Intro/Mattel - Intellivision (Aftermarket)"
    
    # Vectrex
    sync "https://myrient.erista.me/files/No-Intro/GCE - Vectrex"
    # Note: Vectrex (Aftermarket) does not exist on Myrient
    
    # Channel F
    sync "https://myrient.erista.me/files/No-Intro/Fairchild - Channel F"
    
    # Bally Astrocade
    sync "https://myrient.erista.me/files/No-Intro/Bally - Astrocade"
    
    # Odyssey 2
    sync "https://myrient.erista.me/files/No-Intro/Magnavox - Odyssey2"
    
    #---------------------------------------------------------------------------
    # HOME COMPUTERS (CARTRIDGE)
    #---------------------------------------------------------------------------
    echo "--- Home Computers (Cartridge) ---"
    # Commodore
    sync "https://myrient.erista.me/files/No-Intro/Commodore - Commodore 64"
    sync "https://myrient.erista.me/files/No-Intro/Commodore - Commodore 64 (Aftermarket)"
    sync "https://myrient.erista.me/files/No-Intro/Commodore - VIC-20"
    sync "https://myrient.erista.me/files/No-Intro/Commodore - Plus-4"
    
    # MSX
    sync "https://myrient.erista.me/files/No-Intro/Microsoft - MSX"
    sync "https://myrient.erista.me/files/No-Intro/Microsoft - MSX (Aftermarket)"
    sync "https://myrient.erista.me/files/No-Intro/Microsoft - MSX2"
    sync "https://myrient.erista.me/files/No-Intro/Microsoft - MSX2 (Aftermarket)"
    
    # ZX Spectrum
    sync "https://myrient.erista.me/files/No-Intro/Sinclair - ZX Spectrum +3"
    
    #---------------------------------------------------------------------------
    # PSP (Digital - No-Intro)
    #---------------------------------------------------------------------------
    echo "--- PSP Digital ---"
    sync "https://myrient.erista.me/files/No-Intro/Sony - PlayStation Portable (PSN) (Minis) (Decrypted)"
    sync "https://myrient.erista.me/files/No-Intro/Unofficial - Sony - PlayStation Portable (PSN) (Decrypted)"
}

#===============================================================================
# REDUMP DISC SETS
#===============================================================================
sync_redump() {
    echo ""
    echo "=============================================="
    echo "REDUMP DISC SETS"
    echo "=============================================="
    
    #---------------------------------------------------------------------------
    # SEGA DISC SYSTEMS
    #---------------------------------------------------------------------------
    echo "--- Sega Disc Systems ---"
    sync "https://myrient.erista.me/files/Redump/Sega - Mega CD & Sega CD"
    sync "https://myrient.erista.me/files/Redump/Sega - Saturn"
    sync "https://myrient.erista.me/files/Redump/Sega - Dreamcast"
    
    #---------------------------------------------------------------------------
    # NEC DISC SYSTEMS
    #---------------------------------------------------------------------------
    echo "--- NEC Disc Systems ---"
    sync "https://myrient.erista.me/files/Redump/NEC - PC Engine CD & TurboGrafx CD"
    sync "https://myrient.erista.me/files/Redump/NEC - PC-FX & PC-FXGA"
    
    #---------------------------------------------------------------------------
    # SNK DISC SYSTEMS
    #---------------------------------------------------------------------------
    echo "--- SNK Disc Systems ---"
    sync "https://myrient.erista.me/files/Redump/SNK - Neo Geo CD"
    
    #---------------------------------------------------------------------------
    # OTHER DISC SYSTEMS
    #---------------------------------------------------------------------------
    echo "--- Other Disc Systems ---"
    sync "https://myrient.erista.me/files/Redump/Panasonic - 3DO Interactive Multiplayer" "*(*USA*)*"
    sync "https://myrient.erista.me/files/Redump/Philips - CD-i"
    sync "https://myrient.erista.me/files/Redump/Commodore - Amiga CD32"
    sync "https://myrient.erista.me/files/Redump/Atari - Jaguar CD Interactive Multimedia System"
    
    #---------------------------------------------------------------------------
    # NINTENDO DISC SYSTEMS (USA Only - Large)
    #---------------------------------------------------------------------------
    echo "--- Nintendo Disc Systems (USA Only) ---"
    # GameCube - NKit RVZ format (smallest, Dolphin compatible)
    sync "https://myrient.erista.me/files/Redump/Nintendo - GameCube - NKit RVZ [zstd-19-128k]" "*(*USA*)*"
    # Wii - NKit RVZ format
    sync "https://myrient.erista.me/files/Redump/Nintendo - Wii - NKit RVZ [zstd-19-128k]" "*(*USA*)*"
    # Wii U
    sync "https://myrient.erista.me/files/Redump/Nintendo - Wii U - WUX" "*(*USA*)*"
    sync "https://myrient.erista.me/files/Redump/Nintendo - Wii U - Disc Keys"
    
    #---------------------------------------------------------------------------
    # MICROSOFT (USA Only - Large)
    #---------------------------------------------------------------------------
    echo "--- Microsoft Systems (USA Only) ---"
    sync "https://myrient.erista.me/files/Redump/Microsoft - Xbox" "*(*USA*)*"
    sync "https://myrient.erista.me/files/Redump/Microsoft - Xbox 360" "*(*USA*)*"
    
    #---------------------------------------------------------------------------
    # SONY DISC SYSTEMS
    #---------------------------------------------------------------------------
    echo "--- Sony Disc Systems ---"
    # PlayStation 1 (full set - not too large)
    sync "https://myrient.erista.me/files/Redump/Sony - PlayStation"
    sync "https://myrient.erista.me/files/Redump/Sony - PlayStation - SBI Subchannels"
    
    # PlayStation 2 (USA Only - Large)
    sync "https://myrient.erista.me/files/Redump/Sony - PlayStation 2" "*(*USA*)*"
    
    # PlayStation 3 (USA Only - Very Large)
    sync "https://myrient.erista.me/files/Redump/Sony - PlayStation 3" "*(*USA*)*"
    sync "https://myrient.erista.me/files/Redump/Sony - PlayStation 3 - Disc Keys TXT"
    
    # PSP (USA Only)
    sync "https://myrient.erista.me/files/Redump/Sony - PlayStation Portable" "*(*USA*)*"
}

#===============================================================================
# ARCADE SETS
#===============================================================================
sync_arcade() {
    echo ""
    echo "=============================================="
    echo "ARCADE SETS"
    echo "=============================================="
    
    #---------------------------------------------------------------------------
    # FINALBURN NEO (Recommended for most arcade)
    #---------------------------------------------------------------------------
    echo "--- FinalBurn Neo (Recommended) ---"
    # FBNeo arcade set - Neo Geo, CPS1/2/3, Cave, Toaplan, etc.
    sync "https://myrient.erista.me/files/FinalBurn Neo/arcade"
    sync "https://myrient.erista.me/files/FinalBurn Neo/samples"
    
    #---------------------------------------------------------------------------
    # MAME (For comprehensive arcade coverage)
    # Note: Choose ONE of merged/non-merged/split based on your needs:
    #   - merged: smallest, clones in parent zip
    #   - non-merged: largest, every game standalone (easiest)
    #   - split: medium, clones reference parent
    #---------------------------------------------------------------------------
    echo "--- MAME (Optional - Comprehensive) ---"
    # Uncomment ONE of these:
    # sync "https://myrient.erista.me/files/MAME/ROMs (merged)"
    # sync "https://myrient.erista.me/files/MAME/ROMs (non-merged)"
    # sync "https://myrient.erista.me/files/MAME/ROMs (split)"
    
    # MAME BIOS (needed for most MAME ROMs)
    sync "https://myrient.erista.me/files/MAME/ROMs (bios-devices)"
    
    # MAME CHDs for disc-based arcade (Naomi, Model 2/3, etc.)
    # WARNING: Very large!
    # sync "https://myrient.erista.me/files/MAME/CHDs (merged)"
    
    #---------------------------------------------------------------------------
    # REDUMP ARCADE DISCS
    #---------------------------------------------------------------------------
    echo "--- Redump Arcade Systems ---"
    # Sega arcade boards
    sync "https://myrient.erista.me/files/Redump/Arcade - Sega - Naomi"
    sync "https://myrient.erista.me/files/Redump/Arcade - Sega - Naomi - GDI Files"
    sync "https://myrient.erista.me/files/Redump/Arcade - Sega - Naomi 2"
    sync "https://myrient.erista.me/files/Redump/Arcade - Sega - Naomi 2 - GDI Files"
    sync "https://myrient.erista.me/files/Redump/Arcade - Sega - Chihiro"
    sync "https://myrient.erista.me/files/Redump/Arcade - Sega - Chihiro - GDI Files"
    sync "https://myrient.erista.me/files/Redump/Arcade - Sega - Lindbergh"
    sync "https://myrient.erista.me/files/Redump/Arcade - Sega - RingEdge"
    sync "https://myrient.erista.me/files/Redump/Arcade - Sega - RingEdge 2"
    
    # Triforce (Sega/Namco/Nintendo collaboration)
    sync "https://myrient.erista.me/files/Redump/Arcade - Namco - Sega - Nintendo - Triforce"
    sync "https://myrient.erista.me/files/Redump/Arcade - Namco - Sega - Nintendo - Triforce - GDI Files"
    
    # Namco
    sync "https://myrient.erista.me/files/Redump/Arcade - Namco - System 246"
}

#===============================================================================
# ENGLISH TRANSLATIONS (T-En Collection)
# Pre-patched ROMs with fan translations applied
#===============================================================================
sync_translations() {
    echo ""
    echo "=============================================="
    echo "ENGLISH TRANSLATIONS (T-En Collection)"
    echo "=============================================="
    
    #---------------------------------------------------------------------------
    # NINTENDO TRANSLATIONS
    #---------------------------------------------------------------------------
    echo "--- Nintendo Translations ---"
    sync "https://myrient.erista.me/files/T-En Collection/Nintendo - Famicom"
    sync "https://myrient.erista.me/files/T-En Collection/Nintendo - Famicom Disk System"
    sync "https://myrient.erista.me/files/T-En Collection/Nintendo - Super Famicom"
    sync "https://myrient.erista.me/files/T-En Collection/Nintendo - Super Famicom - MSU1"
    sync "https://myrient.erista.me/files/T-En Collection/Nintendo - Super Famicom - Enhanced Colors"
    sync "https://myrient.erista.me/files/T-En Collection/Nintendo - Super Famicom - Speed Hacks"
    sync "https://myrient.erista.me/files/T-En Collection/Nintendo - Game Boy"
    sync "https://myrient.erista.me/files/T-En Collection/Nintendo - Game Boy Color"
    sync "https://myrient.erista.me/files/T-En Collection/Nintendo - Game Boy Advance"
    sync "https://myrient.erista.me/files/T-En Collection/Nintendo - Virtual Boy"
    sync "https://myrient.erista.me/files/T-En Collection/Nintendo - Nintendo 64"
    sync "https://myrient.erista.me/files/T-En Collection/Nintendo - Nintendo DS"
    sync "https://myrient.erista.me/files/T-En Collection/Nintendo - Nintendo 3DS"
    sync "https://myrient.erista.me/files/T-En Collection/Nintendo - GameCube"
    sync "https://myrient.erista.me/files/T-En Collection/Nintendo - Wii"
    
    #---------------------------------------------------------------------------
    # SEGA TRANSLATIONS
    #---------------------------------------------------------------------------
    echo "--- Sega Translations ---"
    sync "https://myrient.erista.me/files/T-En Collection/Sega - Master System"
    sync "https://myrient.erista.me/files/T-En Collection/Sega - Game Gear"
    sync "https://myrient.erista.me/files/T-En Collection/Sega - Mega Drive"
    sync "https://myrient.erista.me/files/T-En Collection/Sega - Mega Drive - MSU-MD"
    sync "https://myrient.erista.me/files/T-En Collection/Sega - Mega Drive - Enhanced Colors"
    sync "https://myrient.erista.me/files/T-En Collection/Sega - Mega CD"
    sync "https://myrient.erista.me/files/T-En Collection/Sega - 32X"
    sync "https://myrient.erista.me/files/T-En Collection/Sega - 32X - MD+"
    sync "https://myrient.erista.me/files/T-En Collection/Sega - Saturn"
    sync "https://myrient.erista.me/files/T-En Collection/Sega - Dreamcast"
    
    #---------------------------------------------------------------------------
    # NEC TRANSLATIONS
    #---------------------------------------------------------------------------
    echo "--- NEC Translations ---"
    sync "https://myrient.erista.me/files/T-En Collection/NEC - PC Engine"
    sync "https://myrient.erista.me/files/T-En Collection/NEC - PC Engine CD"
    sync "https://myrient.erista.me/files/T-En Collection/NEC - SuperGrafx"
    sync "https://myrient.erista.me/files/T-En Collection/NEC - PC-FX"
    
    #---------------------------------------------------------------------------
    # SNK TRANSLATIONS
    #---------------------------------------------------------------------------
    echo "--- SNK Translations ---"
    sync "https://myrient.erista.me/files/T-En Collection/SNK - Neo Geo CD"
    sync "https://myrient.erista.me/files/T-En Collection/SNK - Neo Geo Pocket Color"
    
    #---------------------------------------------------------------------------
    # SONY TRANSLATIONS
    #---------------------------------------------------------------------------
    echo "--- Sony Translations ---"
    sync "https://myrient.erista.me/files/T-En Collection/Sony - PlayStation"
    sync "https://myrient.erista.me/files/T-En Collection/Sony - PlayStation 2"
    sync "https://myrient.erista.me/files/T-En Collection/Sony - PlayStation 3"
    sync "https://myrient.erista.me/files/T-En Collection/Sony - PlayStation Portable"
    
    #---------------------------------------------------------------------------
    # OTHER TRANSLATIONS
    #---------------------------------------------------------------------------
    echo "--- Other System Translations ---"
    sync "https://myrient.erista.me/files/T-En Collection/Bandai - WonderSwan"
    sync "https://myrient.erista.me/files/T-En Collection/Bandai - WonderSwan Color"
    sync "https://myrient.erista.me/files/T-En Collection/Microsoft - MSX"
    sync "https://myrient.erista.me/files/T-En Collection/Microsoft - MSX2"
    sync "https://myrient.erista.me/files/T-En Collection/Microsoft - MSX Turbo-R"
    sync "https://myrient.erista.me/files/T-En Collection/Panasonic - 3DO"
    
    #---------------------------------------------------------------------------
    # JAPANESE COMPUTER TRANSLATIONS
    #---------------------------------------------------------------------------
    echo "--- Japanese Computer Translations ---"
    sync "https://myrient.erista.me/files/T-En Collection/NEC - PC-8801"
    sync "https://myrient.erista.me/files/T-En Collection/NEC - PC-9801"
    sync "https://myrient.erista.me/files/T-En Collection/Sharp - X1"
    sync "https://myrient.erista.me/files/T-En Collection/Sharp - X68000"
}

#===============================================================================
# PRE-CONVERTED CHD SETS (Internet Archive - chadmaster)
# Saves time converting disc images to CHD format
#===============================================================================
sync_chd() {
    echo ""
    echo "=============================================="
    echo "PRE-CONVERTED CHD SETS (chadmaster)"
    echo "=============================================="
    
    echo "--- CD System CHDs ---"
    # PlayStation (choose one region or all)
    sync "https://myrient.erista.me/files/Internet Archive/chadmaster/chd_psx"
    # sync "https://myrient.erista.me/files/Internet Archive/chadmaster/chd_psx_eur"
    # sync "https://myrient.erista.me/files/Internet Archive/chadmaster/chd_psx_jap"
    
    # Other CD systems
    sync "https://myrient.erista.me/files/Internet Archive/chadmaster/chd_saturn"
    sync "https://myrient.erista.me/files/Internet Archive/chadmaster/chd_segacd"
    sync "https://myrient.erista.me/files/Internet Archive/chadmaster/dc-chd-zstd-redump"
    sync "https://myrient.erista.me/files/Internet Archive/chadmaster/pcecd-chd-zstd-redump"
    sync "https://myrient.erista.me/files/Internet Archive/chadmaster/ngcd-chd-zstd-redump"
    sync "https://myrient.erista.me/files/Internet Archive/chadmaster/3do-chd-zstd-redump"
    sync "https://myrient.erista.me/files/Internet Archive/chadmaster/jagcd-chd-zstd"
    
    echo "--- PSP CHDs ---"
    sync "https://myrient.erista.me/files/Internet Archive/chadmaster/psp-chd-zstd-redump-part1"
    sync "https://myrient.erista.me/files/Internet Archive/chadmaster/psp-chd-zstd-redump-part2"
    
    echo "--- Arcade CHDs ---"
    sync "https://myrient.erista.me/files/Internet Archive/chadmaster/fbnarcade-fullnonmerged"
    # sync "https://myrient.erista.me/files/Internet Archive/chadmaster/mame-merged"
    
    echo "--- Enhanced ROMs ---"
    sync "https://myrient.erista.me/files/Internet Archive/chadmaster/nintendo-super-famicom-msu1"
    sync "https://myrient.erista.me/files/Internet Archive/chadmaster/super-famicom-enhanced-colors"
    sync "https://myrient.erista.me/files/Internet Archive/chadmaster/sfc-speedhacks"
    sync "https://myrient.erista.me/files/Internet Archive/chadmaster/SegaMD-Enhanced-ROMs"
}

#===============================================================================
# RETROACHIEVEMENTS VERIFIED SETS
# Hash-matched ROMs for RetroAchievements compatibility
#===============================================================================
sync_retroachievements() {
    echo ""
    echo "=============================================="
    echo "RETROACHIEVEMENTS VERIFIED SETS"
    echo "=============================================="
    
    # Uncomment the systems you want - these are RA hash-verified
    echo "--- RetroAchievements Sets ---"
    # sync "https://myrient.erista.me/files/RetroAchievements/Arcade - FinalBurn Neo"
    # sync "https://myrient.erista.me/files/RetroAchievements/Nintendo - Nintendo Entertainment System"
    # sync "https://myrient.erista.me/files/RetroAchievements/Nintendo - Super Nintendo Entertainment System"
    # sync "https://myrient.erista.me/files/RetroAchievements/Nintendo - Game Boy"
    # sync "https://myrient.erista.me/files/RetroAchievements/Nintendo - Game Boy Color"
    # sync "https://myrient.erista.me/files/RetroAchievements/Nintendo - Game Boy Advance"
    # sync "https://myrient.erista.me/files/RetroAchievements/Sega - Mega Drive - Genesis"
    # sync "https://myrient.erista.me/files/RetroAchievements/Sony - PlayStation"
    echo "(Uncomment desired systems in script to enable)"
}

#===============================================================================
# MISCELLANEOUS / SPECIALTY SETS
#===============================================================================
sync_misc() {
    echo ""
    echo "=============================================="
    echo "MISCELLANEOUS SETS"
    echo "=============================================="
    
    #---------------------------------------------------------------------------
    # HOMEBREW MAME (Bootlegs, Hacks, Homebrew)
    #---------------------------------------------------------------------------
    echo "--- HBMAME (Homebrew/Hacks) ---"
    # sync "https://myrient.erista.me/files/HBMAME/ROMs"
    echo "(Uncomment in script to enable)"
    
    #---------------------------------------------------------------------------
    # eXo COLLECTIONS (Pre-configured DOS/Windows)
    #---------------------------------------------------------------------------
    echo "--- eXo Collections ---"
    # WARNING: These are HUGE (500GB+ for eXoDOS)
    # sync "https://myrient.erista.me/files/eXo/eXoDOS"
    # sync "https://myrient.erista.me/files/eXo/eXoWin3x"
    # sync "https://myrient.erista.me/files/eXo/eXoScummVM"
    echo "(Uncomment in script to enable - WARNING: Very large!)"
    
    #---------------------------------------------------------------------------
    # BIOS FILES
    #---------------------------------------------------------------------------
    echo "--- BIOS Collections ---"
    # sync "https://myrient.erista.me/files/Redump/Sony - PlayStation 2 - BIOS Images"
    echo "(Uncomment in script to enable)"
}

#===============================================================================
# MAIN EXECUTION
#===============================================================================
echo "=============================================="
echo "ROM Farmer - Myrient Download Script"
echo "=============================================="
echo "Base Path: $BASE_PATH"
echo "Section: $SECTION"
echo "=============================================="

case "$SECTION" in
    all)
        sync_nointro
        sync_redump
        sync_arcade
        sync_translations
        ;;
    nointro)
        sync_nointro
        ;;
    redump)
        sync_redump
        ;;
    arcade)
        sync_arcade
        ;;
    translations)
        sync_translations
        ;;
    chd)
        sync_chd
        ;;
    retroachievements|ra)
        sync_retroachievements
        ;;
    misc)
        sync_misc
        ;;
    *)
        echo "Unknown section: $SECTION"
        echo "Available sections: all, nointro, redump, arcade, translations, chd, retroachievements, misc"
        exit 1
        ;;
esac

echo ""
echo "=============================================="
echo "Download complete!"
echo "=============================================="
