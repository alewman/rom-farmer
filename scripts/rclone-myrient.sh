#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SYNC_CMD="${SCRIPT_DIR}/rclone_sync.sh"

# Usage: $SYNC_CMD "https://myrient.erista.me/files/No-Intro/Nintendo - Nintendo Entertainment System (Headered)" ${BASE_PATH} "*(*USA*)*"

BASE_PATH=/data/emu/source
export RCLONE_VERBOSE=1


"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Nintendo - Wii U - WUX" ${BASE_PATH} "*(*USA*)*"
exit
# No-Intro Set
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Atari - Atari 2600" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Atari - Atari 5200" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Atari - Atari 7800 (BIN)" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Atari - Atari Jaguar (ROM)" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Atari - Atari Jaguar (J64)" ${BASE_PATH}
#lynx got split up into a bunch of groups. bll is a downloader version
#"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Atari - Lynx" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Atari - Atari Lynx (LYX)" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Atari - Atari Lynx (BLL)" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Atari - Atari Lynx (LNX)" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Atari - Atari Lynx (LYX) (Private)" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Bally - Astrocade" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Bally - Astrocade (Tapes)" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Bally - Astrocade (Tapes) (WAV)" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Bandai - WonderSwan" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Bandai - WonderSwan Color" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Coleco - ColecoVision" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Commodore - Commodore 64" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Commodore - Plus-4" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Commodore - VIC-20" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Fairchild - Channel F" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/GCE - Vectrex" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Microsoft - MSX" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Microsoft - MSX2" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/NEC - PC Engine - TurboGrafx-16" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/NEC - PC Engine SuperGrafx" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Game & Watch" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Game Boy" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Game Boy Advance" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Game Boy (Private)" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Game Boy Advance (Multiboot)" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Game Boy Advance (Play-Yan)" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Game Boy Advance (Private)" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Game Boy Advance (Video)" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Game Boy Advance (e-Reader)" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Game Boy Color" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Game Boy Color (Private)" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - New Nintendo 3DS (Decrypted)" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Nintendo 3DS (Decrypted)" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Nintendo 3DS (Digital) (CDN)" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Nintendo 64 (BigEndian)" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Nintendo 64 (BigEndian) (Private)" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Nintendo 64DD" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Nintendo DS (DSvision SD cards)" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Nintendo DS (Decrypted)" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Nintendo DS (Decrypted) (Private)" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Nintendo DSi (Decrypted)" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Nintendo DSi (Digital) (CDN) (Decrypted)" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Nintendo Entertainment System (Headered)" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Nintendo Entertainment System (Headered) (Private)/" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Pokemon Mini" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Satellaview" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Sufami Turbo" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Super Nintendo Entertainment System" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Super Nintendo Entertainment System (Private)" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Nintendo - Virtual Boy" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Non-Redump - Atari - Atari Jaguar CD" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/SNK - NeoGeo Pocket" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/SNK - NeoGeo Pocket Color" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Sega - 32X" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Sega - Game Gear" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Sega - Master System - Mark III" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Sega - Mega Drive - Genesis" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Sega - Mega Drive - Genesis (Private)" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Sega - PICO" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Sega - SG-1000" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Sinclair - ZX Spectrum +3" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Sony - PlayStation Portable (PSN) (Minis) (Decrypted)" ${BASE_PATH}

"$SYNC_CMD" "https://myrient.erista.me/files/No-Intro/Unofficial - Sony - PlayStation Portable (PSN) (Decrypted)/" ${BASE_PATH}


# Redump Set
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Arcade - Namco - System 246" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Arcade - Namco - Sega - Nintendo - Triforce" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Arcade - Namco - Sega - Nintendo - Triforce - GDI Files" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Arcade - Sega - Chihiro" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Arcade - Sega - Chihiro - GDI Files" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Arcade - Sega - Lindbergh" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Arcade - Sega - Naomi" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Arcade - Sega - Naomi - GDI Files" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Arcade - Sega - Naomi 2" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Arcade - Sega - Naomi 2 - GDI Files" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Arcade - Sega - RingEdge" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Arcade - Sega - RingEdge 2" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Atari - Jaguar CD Interactive Multimedia System" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Commodore - Amiga CD32" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/NEC - PC Engine CD & TurboGrafx CD" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/NEC - PC-FX & PC-FXGA" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Microsoft - Xbox" ${BASE_PATH} "*(*USA*)*"
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Microsoft - Xbox 360" ${BASE_PATH} "*(*USA*)*"
#Xbox One Removed
#"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Microsoft - Xbox One" ${BASE_PATH} "*(*USA*)*"
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Nintendo - GameCube - NKit RVZ [zstd-19-128k]" ${BASE_PATH} "*(*USA*)*"
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Nintendo - Wii - NKit RVZ [zstd-19-128k]" ${BASE_PATH} "*(*USA*)*"
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Nintendo - Wii U - Disc Keys" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Nintendo - Wii U - WUX" ${BASE_PATH} "*(*USA*)*"
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Philips - CD-i" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Panasonic - 3DO Interactive Multiplayer" ${BASE_PATH} "*(*USA*)*"
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Sega - Dreamcast" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Sega - Mega CD & Sega CD" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Sega - Saturn" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/SNK - Neo Geo CD" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Sony - PlayStation" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Sony - PlayStation Portable" ${BASE_PATH} "*(*USA*)*"
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Sony - PlayStation - SBI Subchannels" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Sony - PlayStation 2" ${BASE_PATH} "*(*USA*)*"
#"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Sony - PlayStation 2 - BIOS Images" ${BASE_PATH}
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Sony - PlayStation 3" ${BASE_PATH} "*(*USA*)*"
"$SYNC_CMD" "https://myrient.erista.me/files/Redump/Sony - PlayStation 3 - Disc Keys TXT" ${BASE_PATH}

exit

