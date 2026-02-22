#!/usr/bin/env bash
set -euo pipefail
# ============================================================================
# AI-Curated Batocera NUC Deployment Script
# ============================================================================
#
# Deploys AI-curated ROM collection to Batocera NUC (10.10.20.183)
# using rsync over SSH. Requires sshpass for password auth.
#
# Storage plan:
#   NVMe /userdata/roms/ (~1,795 GB):
#     - All disc platforms (PSX, PSP, PS2-curated, Xbox-curated, DC, Saturn, etc.)
#     - All cart platforms (NES, SNES, N64, GBA, etc.)
#   HDD /media/int2tbhd/ (~1,813 GB):
#     - 3DS (422 GB), NDS (49 GB), arcade (339 GB), daphne (31 GB)
#     - Symlinked from /userdata/roms/<platform>
#
# PS2: AI-Excellent tier (158 games, ~354 GB) — curated from 1,797
# Xbox: AI-Great tier (48 games, ~149 GB) — curated from 68
# Everything else: Full 1G1R set
#
# Usage:
#   ./scripts/deploy.sh plan        # Show what would be deployed
#   ./scripts/deploy.sh deploy      # Execute the deployment
#   ./scripts/deploy.sh deploy-platform <name>  # Deploy one platform
# ============================================================================

TARGET_HOST="root@10.10.20.183"
TARGET_PASS="linux"
NVME_ROMS="/userdata/roms"
HDD_BASE="/media/int2tbhd"

# Build output directories
RF_ROOT="/data/emu/rom-farmer"
REDUMP_V2="$RF_ROOT/output/redump-1g1r-eng-chd-batocera-v2"
NOINTRO_V2="$RF_ROOT/output/nointro-1g1r-eng-7z-batocera-v2"
ARCADE="$RF_ROOT/output/arcade-batocera"
LASERDISC="$RF_ROOT/output/laserdisc-batocera"
LISTS="$RF_ROOT/lists"

# Rsync base options
RSYNC_OPTS="-avh --progress --stats"
RSYNC_SSH="sshpass -p '$TARGET_PASS' ssh -o StrictHostKeyChecking=no"

# ============================================================================
# Platform definitions: (source_dir, target_location, filter_type)
# ============================================================================
# filter_type: "full" = deploy everything, "list:filename" = use curated list

declare -A PLATFORM_SOURCE
declare -A PLATFORM_TARGET  # nvme or hdd
declare -A PLATFORM_FILTER
declare -A PLATFORM_EXT     # file extension for list-filtered platforms

# --- Disc platforms (Redump v2 CHD) → NVMe ---
PLATFORM_SOURCE[psx]="$REDUMP_V2/psx"
PLATFORM_TARGET[psx]="nvme"
PLATFORM_FILTER[psx]="full"

PLATFORM_SOURCE[psp]="$REDUMP_V2/psp"
PLATFORM_TARGET[psp]="nvme"
PLATFORM_FILTER[psp]="full"

PLATFORM_SOURCE[ps2]="$REDUMP_V2/ps2"
PLATFORM_TARGET[ps2]="nvme"
PLATFORM_FILTER[ps2]="list:ps2+AI-Excellent"
PLATFORM_EXT[ps2]=".chd"

PLATFORM_SOURCE[xbox]="$REDUMP_V2/xbox"
PLATFORM_TARGET[xbox]="nvme"
PLATFORM_FILTER[xbox]="list:xbox+AI-Great"
PLATFORM_EXT[xbox]=".iso"

PLATFORM_SOURCE[dreamcast]="$REDUMP_V2/dreamcast"
PLATFORM_TARGET[dreamcast]="nvme"
PLATFORM_FILTER[dreamcast]="full"

PLATFORM_SOURCE[saturn]="$REDUMP_V2/saturn"
PLATFORM_TARGET[saturn]="nvme"
PLATFORM_FILTER[saturn]="full"

PLATFORM_SOURCE[pcenginecd]="$REDUMP_V2/pcenginecd"
PLATFORM_TARGET[pcenginecd]="nvme"
PLATFORM_FILTER[pcenginecd]="full"

PLATFORM_SOURCE[megacd]="$REDUMP_V2/megacd"
PLATFORM_TARGET[megacd]="nvme"
PLATFORM_FILTER[megacd]="full"

PLATFORM_SOURCE[neogeocd]="$REDUMP_V2/neogeocd"
PLATFORM_TARGET[neogeocd]="nvme"
PLATFORM_FILTER[neogeocd]="full"

PLATFORM_SOURCE[3do]="$REDUMP_V2/3do"
PLATFORM_TARGET[3do]="hdd"
PLATFORM_FILTER[3do]="full"

# --- Cart platforms (No-Intro v2 7z/zip) → NVMe ---
for cart_platform in snes megadrive n64 gba gb gbc gamegear \
    mastersystem pcengine atari2600 atari7800 atari5200 \
    sg1000 sega32x ngpc ngp wswan wswanc \
    lynx jaguar colecovision intellivision virtualboy vectrex \
    fds supergrafx msx1 msx2 pokemini sgb \
    gb2players gbc2players; do
    if [[ -d "$NOINTRO_V2/$cart_platform" ]]; then
        PLATFORM_SOURCE[$cart_platform]="$NOINTRO_V2/$cart_platform"
        PLATFORM_TARGET[$cart_platform]="nvme"
        PLATFORM_FILTER[$cart_platform]="full"
    fi
done

# NES: use v2 zip (works fine with RetroArch)
PLATFORM_SOURCE[nes]="$NOINTRO_V2/nes"
PLATFORM_TARGET[nes]="nvme"
PLATFORM_FILTER[nes]="full"

# --- Large platforms → HDD (symlinked) ---
PLATFORM_SOURCE[3ds]="$NOINTRO_V2/3ds"
PLATFORM_TARGET[3ds]="hdd"
PLATFORM_FILTER[3ds]="full"

PLATFORM_SOURCE[nds]="$NOINTRO_V2/nds"
PLATFORM_TARGET[nds]="hdd"
PLATFORM_FILTER[nds]="full"

# --- Arcade → HDD ---
# Arcade has sub-directories for each arcade system
ARCADE_PLATFORMS=(mame fbneo naomi naomi2 atomiswave model2 model3 namco246 triforce)

# --- Laserdisc → HDD ---
PLATFORM_SOURCE[daphne]="$LASERDISC/daphne"
PLATFORM_TARGET[daphne]="hdd"
PLATFORM_FILTER[daphne]="full"


# ============================================================================
# Functions
# ============================================================================

remote_cmd() {
    sshpass -p "$TARGET_PASS" ssh -o StrictHostKeyChecking=no "$TARGET_HOST" "$@"
}

make_list_file() {
    # Convert a ROM Farmer list to a file-list for rsync --files-from
    local list_file="$1"
    local ext="$2"
    local tmpfile
    tmpfile=$(mktemp)
    
    # Strip comments and empty lines, add extension
    grep -v '^#' "$list_file" | grep -v '^$' | while IFS= read -r line; do
        echo "${line}${ext}"
    done > "$tmpfile"
    
    echo "$tmpfile"
}

plan_platform() {
    local platform="$1"
    local source="${PLATFORM_SOURCE[$platform]}"
    local target="${PLATFORM_TARGET[$platform]}"
    local filter="${PLATFORM_FILTER[$platform]}"
    
    local target_dir
    if [[ "$target" == "nvme" ]]; then
        target_dir="$NVME_ROMS/$platform"
    else
        target_dir="$HDD_BASE/$platform"
    fi
    
    local file_count size_gb
    if [[ "$filter" == "full" ]]; then
        file_count=$(find "$source" -maxdepth 1 -type f 2>/dev/null | wc -l)
        size_gb=$(du -sb "$source" 2>/dev/null | awk '{printf "%.1f", $1/1073741824}')
        printf "  %-20s → %-4s  %6s files  %8s GB  [full]\n" "$platform" "$target" "$file_count" "$size_gb"
    elif [[ "$filter" == list:* ]]; then
        local list_name="${filter#list:}"
        local list_path="$LISTS/$list_name"
        file_count=$(grep -cv '^#\|^$' "$list_path" 2>/dev/null || echo 0)
        local ext="${PLATFORM_EXT[$platform]:-.chd}"
        local total_size=0
        while IFS= read -r line; do
            [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
            local f="$source/${line}${ext}"
            if [[ -f "$f" ]]; then
                total_size=$((total_size + $(stat --printf="%s" "$f")))
            fi
        done < "$list_path"
        size_gb=$(echo "scale=1; $total_size / 1073741824" | bc)
        printf "  %-20s → %-4s  %6s files  %8s GB  [AI: %s]\n" "$platform" "$target" "$file_count" "$size_gb" "$list_name"
    fi
}

deploy_platform() {
    local platform="$1"
    local source="${PLATFORM_SOURCE[$platform]}"
    local target="${PLATFORM_TARGET[$platform]}"
    local filter="${PLATFORM_FILTER[$platform]}"
    
    local target_dir
    if [[ "$target" == "nvme" ]]; then
        target_dir="$NVME_ROMS/$platform/"
    else
        target_dir="$HDD_BASE/$platform/"
    fi
    
    echo ">>> Deploying $platform → $TARGET_HOST:$target_dir"
    
    # Create target directory
    remote_cmd "mkdir -p '$target_dir'"
    
    if [[ "$filter" == "full" ]]; then
        rsync $RSYNC_OPTS -e "$RSYNC_SSH" \
            "$source/" "$TARGET_HOST:$target_dir"
    elif [[ "$filter" == list:* ]]; then
        local list_name="${filter#list:}"
        local list_path="$LISTS/$list_name"
        local ext="${PLATFORM_EXT[$platform]:-.chd}"
        local tmpfile
        tmpfile=$(make_list_file "$list_path" "$ext")
        
        rsync $RSYNC_OPTS -e "$RSYNC_SSH" \
            --files-from="$tmpfile" \
            "$source/" "$TARGET_HOST:$target_dir"
        
        rm -f "$tmpfile"
    fi
    
    # Create symlink if HDD platform
    if [[ "$target" == "hdd" ]]; then
        echo "  Creating symlink: $NVME_ROMS/$platform → $target_dir"
        remote_cmd "ln -sfn '$target_dir' '$NVME_ROMS/$platform'"
    fi
    
    echo "  ✓ $platform deployed"
}

deploy_arcade() {
    echo ">>> Deploying arcade platforms"
    
    for arcade_sys in "${ARCADE_PLATFORMS[@]}"; do
        local source_dir="$ARCADE/$arcade_sys"
        if [[ -d "$source_dir" ]]; then
            local target_dir="$HDD_BASE/$arcade_sys/"
            local nvme_link="$NVME_ROMS/$arcade_sys"
            
            echo "  $arcade_sys..."
            remote_cmd "mkdir -p '$target_dir'"
            rsync $RSYNC_OPTS -e "$RSYNC_SSH" \
                "$source_dir/" "$TARGET_HOST:$target_dir"
            remote_cmd "ln -sfn '$target_dir' '$nvme_link'"
        fi
    done
    
    echo "  ✓ Arcade platforms deployed"
}


# ============================================================================
# Main
# ============================================================================

case "${1:-plan}" in
    plan)
        echo "============================================================"
        echo "AI-Curated Batocera NUC Deployment Plan"
        echo "============================================================"
        echo ""
        echo "Target: $TARGET_HOST"
        echo "NVMe: $NVME_ROMS (~1,795 GB)"
        echo "HDD:  $HDD_BASE (~1,813 GB)"
        echo ""
        
        total_nvme=0
        total_hdd=0
        
        echo "--- Disc Platforms ---"
        for p in psx psp ps2 xbox dreamcast saturn pcenginecd megacd neogeocd; do
            [[ -v PLATFORM_SOURCE[$p] ]] && plan_platform "$p"
        done
        
        echo ""
        echo "--- Cart Platforms (NVMe) ---"
        for p in nes snes megadrive n64 gba gb gbc gamegear \
            mastersystem pcengine atari2600 atari7800 atari5200 \
            sg1000 sega32x ngpc ngp wswan wswanc \
            lynx jaguar colecovision intellivision virtualboy vectrex \
            fds supergrafx msx1 msx2 pokemini sgb \
            gb2players gbc2players; do
            [[ -v PLATFORM_SOURCE[$p] ]] && plan_platform "$p"
        done
        
        echo ""
        echo "--- Large Platforms (HDD, symlinked) ---"
        for p in 3ds nds 3do daphne; do
            [[ -v PLATFORM_SOURCE[$p] ]] && plan_platform "$p"
        done
        
        echo ""
        echo "--- Arcade (HDD, symlinked) ---"
        for arcade_sys in "${ARCADE_PLATFORMS[@]}"; do
            if [[ -d "$ARCADE/$arcade_sys" ]]; then
                local_count=$(find "$ARCADE/$arcade_sys" -maxdepth 1 -type f 2>/dev/null | wc -l)
                local_size=$(du -sb "$ARCADE/$arcade_sys" 2>/dev/null | awk '{printf "%.1f", $1/1073741824}')
                printf "  %-20s → hdd   %6s files  %8s GB  [full]\n" "$arcade_sys" "$local_count" "$local_size"
            fi
        done
        
        echo ""
        echo "============================================================"
        echo "PS2 Curation: 158 games from 1,797 (AI-Excellent tier)"
        echo "Xbox Curation: 48 games from 68 (AI-Great tier)"
        echo "============================================================"
        ;;
    
    deploy)
        echo "Starting full deployment..."
        echo "Target: $TARGET_HOST"
        echo ""
        
        # Disc platforms (NVMe)
        for p in psx psp ps2 xbox dreamcast saturn pcenginecd megacd neogeocd; do
            [[ -v PLATFORM_SOURCE[$p] ]] && deploy_platform "$p"
        done
        
        # Cart platforms
        for p in nes snes megadrive n64 gba gb gbc gamegear \
            mastersystem pcengine atari2600 atari7800 atari5200 \
            sg1000 sega32x ngpc ngp wswan wswanc \
            lynx jaguar colecovision intellivision virtualboy vectrex \
            fds supergrafx msx1 msx2 pokemini sgb \
            gb2players gbc2players; do
            [[ -v PLATFORM_SOURCE[$p] ]] && deploy_platform "$p"
        done
        
        # HDD platforms (symlinked)
        for p in 3ds nds 3do daphne; do
            [[ -v PLATFORM_SOURCE[$p] ]] && deploy_platform "$p"
        done
        
        # Arcade
        deploy_arcade
        
        echo ""
        echo "============================================================"
        echo "Deployment complete!"
        echo "============================================================"
        ;;
    
    deploy-platform)
        platform="${2:?Usage: deploy.sh deploy-platform <name>}"
        if [[ -v PLATFORM_SOURCE[$platform] ]]; then
            deploy_platform "$platform"
        elif [[ " ${ARCADE_PLATFORMS[*]} " =~ " $platform " ]]; then
            echo "Deploying arcade platform: $platform"
            source_dir="$ARCADE/$platform"
            target_dir="$HDD_BASE/$platform/"
            remote_cmd "mkdir -p '$target_dir'"
            rsync $RSYNC_OPTS -e "$RSYNC_SSH" \
                "$source_dir/" "$TARGET_HOST:$target_dir"
            remote_cmd "ln -sfn '$target_dir' '$NVME_ROMS/$platform'"
        else
            echo "Unknown platform: $platform"
            exit 1
        fi
        ;;
    
    *)
        echo "Usage: $0 {plan|deploy|deploy-platform <name>}"
        exit 1
        ;;
esac
