#!/bin/bash
# Rebuild /data/emu/roms folders with symlinks to Myrient sources
# Preserves existing gamelist.xml and media folders
# Adds Aftermarket content for better scraping coverage

# Don't use set -e as ((count++)) returns 1 when count is 0

MYRIENT_NOINTRO="/data/emu/source/myrient.erista.me/files/No-Intro"
ROMS_BASE="/data/emu/roms"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Function to rebuild a system's roms folder with symlinks
rebuild_system() {
    local system="$1"
    shift
    local myrient_folders=("$@")
    
    local roms_dir="$ROMS_BASE/$system"
    
    echo ""
    echo "================================================================================"
    log_info "Processing: $system"
    echo "================================================================================"
    
    # Check if roms directory exists
    if [[ ! -d "$roms_dir" ]]; then
        log_warn "Creating new roms directory: $roms_dir"
        mkdir -p "$roms_dir"
    fi
    
    # Verify Myrient folders exist
    local valid_folders=()
    for folder in "${myrient_folders[@]}"; do
        local full_path="$MYRIENT_NOINTRO/$folder"
        if [[ -d "$full_path" ]]; then
            local count=$(ls "$full_path"/*.zip 2>/dev/null | wc -l)
            log_info "  Source: $folder ($count files)"
            valid_folders+=("$folder")
        else
            log_warn "  Missing: $folder"
        fi
    done
    
    if [[ ${#valid_folders[@]} -eq 0 ]]; then
        log_error "No valid source folders found for $system"
        return 1
    fi
    
    # Backup gamelist.xml if exists
    if [[ -f "$roms_dir/gamelist.xml" ]]; then
        log_info "  Preserving gamelist.xml"
    fi
    
    # Check for media folder
    if [[ -d "$roms_dir/media" ]]; then
        log_info "  Preserving media folder"
    fi
    
    # Count existing files
    local old_count=$(find "$roms_dir" -maxdepth 1 -name "*.zip" -type f -o -name "*.zip" -type l 2>/dev/null | wc -l)
    log_info "  Current files: $old_count"
    
    # Remove old zip files (but keep symlinks check)
    if [[ "$DRY_RUN" != "true" ]]; then
        # Remove regular files and hardlinks
        find "$roms_dir" -maxdepth 1 -name "*.zip" -type f -delete 2>/dev/null || true
        # Remove existing symlinks
        find "$roms_dir" -maxdepth 1 -name "*.zip" -type l -delete 2>/dev/null || true
        
        # Create symlinks to all source folders
        local new_count=0
        for folder in "${valid_folders[@]}"; do
            local full_path="$MYRIENT_NOINTRO/$folder"
            # Use find to handle filenames with spaces properly
            while IFS= read -r -d '' zip_file; do
                local filename=$(basename "$zip_file")
                # Only create if doesn't exist (avoid duplicates across folders)
                if [[ ! -L "$roms_dir/$filename" && ! -f "$roms_dir/$filename" ]]; then
                    ln -s "$zip_file" "$roms_dir/$filename"
                    new_count=$((new_count + 1))
                fi
            done < <(find "$full_path" -maxdepth 1 -name "*.zip" -type f -print0 2>/dev/null)
        done
        
        log_success "  Created $new_count symlinks"
    else
        # Dry run - just count what would be created
        local new_count=0
        for folder in "${valid_folders[@]}"; do
            local full_path="$MYRIENT_NOINTRO/$folder"
            new_count=$((new_count + $(ls "$full_path"/*.zip 2>/dev/null | wc -l)))
        done
        log_info "  [DRY RUN] Would create ~$new_count symlinks"
    fi
}

# Parse arguments
DRY_RUN="false"
SYSTEMS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN="true"
            shift
            ;;
        --all)
            SYSTEMS=("all")
            shift
            ;;
        *)
            SYSTEMS+=("$1")
            shift
            ;;
    esac
done

if [[ ${#SYSTEMS[@]} -eq 0 ]]; then
    echo "Usage: $0 [--dry-run] [--all | system1 system2 ...]"
    echo ""
    echo "Systems available:"
    echo "  Atari: atari2600, atari5200, atari7800, atarilynx, atarijaguar"
    echo "  Classic: colecovision, intellivision, vectrex"
    echo "  Nintendo: gb, gbc, gba, nes, fds, snes, n64, virtualboy"
    echo "  Sega: mastersystem, gamegear, megadrive, sega32x"
    echo "  Other: pcengine, supergrafx, ngp, ngpc, wswan, wswanc, msx1, msx2"
    echo ""
    echo "Examples:"
    echo "  $0 --dry-run atari2600          # Preview Atari 2600"
    echo "  $0 atari2600 atari7800           # Rebuild Atari 2600 and 7800"
    echo "  $0 --all                         # Rebuild all systems"
    exit 1
fi

echo "================================================================================"
echo "  REBUILD ROMS FOLDERS WITH SYMLINKS"
echo "================================================================================"
echo ""
if [[ "$DRY_RUN" == "true" ]]; then
    log_warn "DRY RUN MODE - No changes will be made"
fi

# Define system mappings: system -> Myrient folder names
# Format: rebuild_system "batocera_name" "Main Folder" "Aftermarket Folder" ...

process_system() {
    local sys="$1"
    case "$sys" in
        # Atari Systems
        atari2600)
            rebuild_system "atari2600" \
                "Atari - Atari 2600" \
                "Atari - Atari 2600 (Aftermarket)"
            ;;
        atari5200)
            rebuild_system "atari5200" \
                "Atari - Atari 5200"
            ;;
        atari7800)
            rebuild_system "atari7800" \
                "Atari - Atari 7800 (BIN)" \
                "Atari - Atari 7800 (BIN) (Aftermarket)" \
                "Atari - Atari 7800 (BIN) (Private)"
            ;;
        atarilynx)
            rebuild_system "lynx" \
                "Atari - Atari Lynx (LYX)" \
                "Atari - Atari Lynx (LYX) (Aftermarket)" \
                "Atari - Atari Lynx (LYX) (Private)"
            ;;
        atarijaguar)
            rebuild_system "jaguar" \
                "Atari - Atari Jaguar (J64)" \
                "Atari - Atari Jaguar (J64) (Aftermarket)"
            ;;
        
        # Classic Systems
        colecovision)
            rebuild_system "colecovision" \
                "Coleco - ColecoVision" \
                "Coleco - ColecoVision (Aftermarket)"
            ;;
        intellivision)
            rebuild_system "intellivision" \
                "Mattel - Intellivision" \
                "Mattel - Intellivision (Aftermarket)"
            ;;
        vectrex)
            rebuild_system "vectrex" \
                "GCE - Vectrex"
            ;;
        
        # Nintendo Handhelds
        gb)
            rebuild_system "gb" \
                "Nintendo - Game Boy" \
                "Nintendo - Game Boy (Aftermarket)" \
                "Nintendo - Game Boy (Private)"
            ;;
        gbc)
            rebuild_system "gbc" \
                "Nintendo - Game Boy Color" \
                "Nintendo - Game Boy Color (Aftermarket)" \
                "Nintendo - Game Boy Color (Private)"
            ;;
        gba)
            rebuild_system "gba" \
                "Nintendo - Game Boy Advance" \
                "Nintendo - Game Boy Advance (Aftermarket)" \
                "Nintendo - Game Boy Advance (e-Reader)" \
                "Nintendo - Game Boy Advance (Multiboot)" \
                "Nintendo - Game Boy Advance (Play-Yan)" \
                "Nintendo - Game Boy Advance (Private)" \
                "Nintendo - Game Boy Advance (Video)" \
                "Nintendo - Game Boy Advance (Video) (Aftermarket)" \
                "Nintendo - Game Boy Advance (Video) (Private)"
            ;;
        virtualboy)
            rebuild_system "virtualboy" \
                "Nintendo - Virtual Boy" \
                "Nintendo - Virtual Boy (Aftermarket)" \
                "Nintendo - Virtual Boy (Private)"
            ;;
        
        # Nintendo Consoles
        nes)
            rebuild_system "nes" \
                "Nintendo - Nintendo Entertainment System (Headered)" \
                "Nintendo - Nintendo Entertainment System (Headered) (Aftermarket)" \
                "Nintendo - Nintendo Entertainment System (Headered) (Private)"
            ;;
        fds)
            rebuild_system "fds" \
                "Nintendo - Family Computer Disk System (FDS)" \
                "Nintendo - Family Computer Disk System (FDS) (Aftermarket)"
            ;;
        snes)
            rebuild_system "snes" \
                "Nintendo - Super Nintendo Entertainment System" \
                "Nintendo - Super Nintendo Entertainment System (Aftermarket)" \
                "Nintendo - Super Nintendo Entertainment System (Private)"
            ;;
        n64)
            rebuild_system "n64" \
                "Nintendo - Nintendo 64 (BigEndian)" \
                "Nintendo - Nintendo 64 (BigEndian) (Aftermarket)" \
                "Nintendo - Nintendo 64 (BigEndian) (Private)"
            ;;
        
        # Sega Systems
        mastersystem)
            rebuild_system "mastersystem" \
                "Sega - Master System - Mark III" \
                "Sega - Master System - Mark III (Aftermarket)" \
                "Sega - Master System - Mark III (Private)"
            ;;
        gamegear)
            rebuild_system "gamegear" \
                "Sega - Game Gear" \
                "Sega - Game Gear (Aftermarket)"
            ;;
        megadrive)
            rebuild_system "megadrive" \
                "Sega - Mega Drive - Genesis" \
                "Sega - Mega Drive - Genesis (Aftermarket)" \
                "Sega - Mega Drive - Genesis (Private)"
            ;;
        sega32x)
            rebuild_system "sega32x" \
                "Sega - 32X"
            ;;
        
        # NEC Systems
        pcengine)
            rebuild_system "pcengine" \
                "NEC - PC Engine - TurboGrafx-16" \
                "NEC - PC Engine - TurboGrafx-16 (Aftermarket)" \
                "NEC - PC Engine - TurboGrafx-16 (Private)"
            ;;
        supergrafx)
            rebuild_system "supergrafx" \
                "NEC - PC Engine SuperGrafx" \
                "NEC - PC Engine SuperGrafx (Aftermarket)" \
                "NEC - PC Engine SuperGrafx (Private)"
            ;;
        
        # SNK Systems
        ngp)
            rebuild_system "ngp" \
                "SNK - NeoGeo Pocket" \
                "SNK - NeoGeo Pocket (Aftermarket)"
            ;;
        ngpc)
            rebuild_system "ngpc" \
                "SNK - NeoGeo Pocket Color"
            ;;
        
        # Bandai Systems
        wswan)
            rebuild_system "wswan" \
                "Bandai - WonderSwan" \
                "Bandai - WonderSwan (Aftermarket)"
            ;;
        wswanc)
            rebuild_system "wswanc" \
                "Bandai - WonderSwan Color" \
                "Bandai - WonderSwan Color (Aftermarket)"
            ;;
        
        # MSX
        msx1)
            rebuild_system "msx1" \
                "Microsoft - MSX" \
                "Microsoft - MSX (Aftermarket)"
            ;;
        msx2)
            rebuild_system "msx2" \
                "Microsoft - MSX2" \
                "Microsoft - MSX2 (Aftermarket)"
            ;;
        
        # Nintendo DS
        nds)
            rebuild_system "nds" \
                "Nintendo - Nintendo DS (Decrypted)" \
                "Nintendo - Nintendo DS (Decrypted) (Aftermarket)" \
                "Nintendo - Nintendo DS (Decrypted) (Private)" \
                "Nintendo - Nintendo DS (DSvision SD cards)"
            ;;
        ndsi)
            rebuild_system "ndsi" \
                "Nintendo - Nintendo DSi (Decrypted)" \
                "Nintendo - Nintendo DSi (Digital) (CDN) (Decrypted)"
            ;;
        
        # Pokemon Mini
        pokemini)
            rebuild_system "pokemini" \
                "Nintendo - Pokemon Mini"
            ;;
        
        *)
            log_error "Unknown system: $sys"
            return 1
            ;;
    esac
}

# Process systems
if [[ "${SYSTEMS[0]}" == "all" ]]; then
    # All No-Intro systems
    ALL_SYSTEMS=(
        atari2600 atari5200 atari7800 atarilynx atarijaguar
        colecovision intellivision vectrex
        gb gbc gba virtualboy
        nes fds snes n64
        nds ndsi pokemini
        mastersystem gamegear megadrive sega32x
        pcengine supergrafx
        ngp ngpc
        wswan wswanc
        msx1 msx2
    )
    for sys in "${ALL_SYSTEMS[@]}"; do
        process_system "$sys"
    done
else
    for sys in "${SYSTEMS[@]}"; do
        process_system "$sys"
    done
fi

echo ""
echo "================================================================================"
log_success "Done!"
echo "================================================================================"
