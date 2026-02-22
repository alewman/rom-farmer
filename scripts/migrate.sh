#!/usr/bin/env bash
set -euo pipefail
# ============================================================================
# Batocera NUC Migration Script
# ============================================================================
#
# One-time migration from existing ROM layout to AI-curated deployment.
# Handles the careful sequencing required to avoid running out of NVMe space.
#
# Current state:
#   NVMe: 3ds, nds, arcade, daphne on NVMe (need to move to HDD)
#   HDD:  dreamcast, megacd, psp, saturn, 3do symlinked from NVMe
#   Missing: PS2, Xbox not yet deployed
#   Stale: lindbergh (96GB), namco2x6 (18GB), atarijaguar, atarilynx
#
# Target state:
#   NVMe: psx, psp, ps2-curated, xbox-curated, dreamcast, saturn, pcenginecd, all carts
#   HDD:  3ds, nds, 3do, megacd, neogeocd, daphne, all arcade (symlinked)
#
# Sequence (space-aware):
#   0. Reduce ext4 reserved blocks 5%→1% (gain 73 GB)
#   1. Clean stale dirs from NVMe (free ~115 GB)
#   2. rsync --delete psx, pcenginecd (free ~52 GB from cleanup)
#   3. Local move 3ds NVMe→HDD (free 424 GB)
#   4. rsync dreamcast, saturn from build to NVMe (use 204 GB)
#   5. Local move nds NVMe→HDD (free 55 GB)
#   6. rsync psp from build to NVMe (use 374 GB)
#   7. Local move daphne NVMe→HDD (free 32 GB)
#   8. Local move all arcade NVMe→HDD (free ~398 GB)
#   9. rsync PS2 curated, Xbox curated to NVMe (use 503 GB)
#  10. rsync megacd, neogeocd from build to HDD
#  11. rsync 3do, 3ds, nds, daphne, arcade from build to HDD (--delete update)
#  12. rsync all cart platforms to NVMe (--delete update)
#  13. Clean old HDD copies of dreamcast, psp, saturn
#  14. Verify and create all symlinks
#
# Usage:
#   ./scripts/migrate.sh           # Run the migration
#   ./scripts/migrate.sh --dry-run # Show what would happen
# ============================================================================

TARGET_HOST="root@10.10.20.183"
TARGET_PASS="linux"
NVME_ROMS="/userdata/roms"
HDD_ROMS="/media/int2tbhd/roms"

# Build outputs
RF_ROOT="/data/emu/rom-farmer"
REDUMP="$RF_ROOT/output/redump-1g1r-eng-chd-batocera-v2"
NOINTRO="$RF_ROOT/output/nointro-1g1r-eng-7z-batocera-v2"
ARCADE="$RF_ROOT/output/arcade-batocera"
LASERDISC="$RF_ROOT/output/laserdisc-batocera"
LISTS="$RF_ROOT/lists"

RSYNC_BASE="-avh --progress --stats --delete"
RSYNC_SSH="sshpass -p '$TARGET_PASS' ssh -o StrictHostKeyChecking=no"

DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

# Arcade systems
ARCADE_PLATFORMS=(mame fbneo naomi naomi2 atomiswave model2 model3 namco246 triforce)

# Cart platforms
CART_PLATFORMS=(nes snes megadrive n64 gba gb gbc gamegear \
    mastersystem pcengine atari2600 atari7800 atari5200 \
    sg1000 sega32x ngpc ngp wswan wswanc \
    lynx jaguar colecovision intellivision virtualboy vectrex \
    fds supergrafx msx1 msx2 pokemini sgb \
    gb2players gbc2players)

# ============================================================================
# Helpers
# ============================================================================

log() { echo "$(date '+%H:%M:%S') $*"; }
step() { echo ""; echo "========== STEP $1: $2 =========="; }

rcmd() {
    if $DRY_RUN; then
        echo "  [DRY-RUN] remote: $*"
    else
        sshpass -p "$TARGET_PASS" ssh -o StrictHostKeyChecking=no "$TARGET_HOST" "$@"
    fi
}

rsync_to() {
    local src="$1" dst="$2"
    shift 2
    if $DRY_RUN; then
        echo "  [DRY-RUN] rsync $RSYNC_BASE $* $src → $TARGET_HOST:$dst"
    else
        rsync $RSYNC_BASE "$@" -e "$RSYNC_SSH" "$src" "$TARGET_HOST:$dst"
    fi
}

check_free() {
    local device="$1" label="$2"
    local free_gb
    free_gb=$(rcmd "df -BG '$device' | tail -1 | awk '{print \$4}' | tr -d 'G'")
    log "$label free space: ${free_gb} GB"
    echo "$free_gb"
}

make_list_file() {
    local list_file="$1" ext="$2"
    local tmpfile
    tmpfile=$(mktemp)
    grep -v '^#' "$list_file" | grep -v '^$' | while IFS= read -r line; do
        echo "${line}${ext}"
    done > "$tmpfile"
    echo "$tmpfile"
}

local_move_to_hdd() {
    # Move a platform from NVMe to HDD locally on the NUC
    local platform="$1"
    local nvme_dir="$NVME_ROMS/$platform"
    local hdd_dir="$HDD_ROMS/$platform"
    
    log "Local move: $platform NVMe → HDD"
    
    if $DRY_RUN; then
        echo "  [DRY-RUN] cp -a $nvme_dir $hdd_dir && rm -rf $nvme_dir && ln -sfn $hdd_dir $nvme_dir"
        return
    fi
    
    # Check if it's already a symlink (already moved)
    if rcmd "test -L '$nvme_dir'"; then
        log "  $platform already symlinked, skipping move"
        return
    fi
    
    # Check if dir exists on NVMe
    if ! rcmd "test -d '$nvme_dir'"; then
        log "  $platform not found on NVMe, skipping"
        return
    fi
    
    # Make HDD target dir parent
    rcmd "mkdir -p '$HDD_ROMS'"
    
    # Copy if HDD copy doesn't exist yet
    if rcmd "test -d '$hdd_dir'"; then
        log "  $platform already exists on HDD, removing NVMe copy"
    else
        log "  Copying $platform to HDD (this may take a while)..."
        rcmd "cp -a '$nvme_dir' '$hdd_dir'"
    fi
    
    # Remove NVMe copy and create symlink
    rcmd "rm -rf '$nvme_dir'"
    rcmd "ln -sfn '$hdd_dir' '$nvme_dir'"
    log "  ✓ $platform moved to HDD and symlinked"
}

# ============================================================================
# Migration Steps
# ============================================================================

log "Starting AI-Curated Batocera NUC Migration"
log "Target: $TARGET_HOST"
log "Dry run: $DRY_RUN"
echo ""

# Verify connectivity
if ! $DRY_RUN; then
    if ! rcmd "echo ok" >/dev/null 2>&1; then
        log "ERROR: Cannot reach $TARGET_HOST"
        exit 1
    fi
fi

# --- Step 0: Reduce ext4 reserved blocks ---
step 0 "Reduce ext4 reserved blocks from 5% to 1%"
if $DRY_RUN; then
    echo "  [DRY-RUN] tune2fs -m 1 /dev/nvme0n1p2"
else
    # Check current reserved percentage
    current_reserved=$(rcmd "tune2fs -l /dev/nvme0n1p2 2>/dev/null | grep 'Reserved block count' | awk '{print \$NF}'")
    total_blocks=$(rcmd "tune2fs -l /dev/nvme0n1p2 2>/dev/null | grep 'Block count' | awk '{print \$NF}'")
    if [[ -n "$current_reserved" && -n "$total_blocks" ]]; then
        reserved_pct=$((current_reserved * 100 / total_blocks))
        if (( reserved_pct > 1 )); then
            log "Current reserved: ${reserved_pct}% ($current_reserved blocks). Reducing to 1%..."
            rcmd "tune2fs -m 1 /dev/nvme0n1p2"
            log "✓ Reserved blocks reduced to 1%"
        else
            log "Already at ${reserved_pct}% reserved, skipping"
        fi
    else
        log "WARNING: Could not read filesystem info, skipping tune2fs"
    fi
fi
$DRY_RUN || check_free "/userdata" "NVMe"

# --- Step 1: Clean stale directories ---
step 1 "Clean stale directories from NVMe"
STALE_DIRS=(lindbergh namco2x6 atarijaguar atarilynx neogeo)
for d in "${STALE_DIRS[@]}"; do
    if $DRY_RUN; then
        echo "  [DRY-RUN] rm -rf $NVME_ROMS/$d"
    else
        if rcmd "test -d '$NVME_ROMS/$d' && ! test -L '$NVME_ROMS/$d'"; then
            local_size=$(rcmd "du -sh '$NVME_ROMS/$d' | awk '{print \$1}'")
            log "  Removing $d ($local_size)..."
            rcmd "rm -rf '$NVME_ROMS/$d'"
        else
            log "  $d not found or is symlink, skipping"
        fi
    fi
done
$DRY_RUN || check_free "/userdata" "NVMe"

# --- Step 2: rsync --delete PSX and PCEngineCD (clean existing) ---
step 2 "Update PSX and PCEngineCD (rsync --delete cleans extra files)"

log "Syncing PSX..."
rcmd "rm -f '$NVME_ROMS/psx/.gitkeep' 2>/dev/null; mkdir -p '$NVME_ROMS/psx'"
rsync_to "$REDUMP/psx/" "$NVME_ROMS/psx/"

$DRY_RUN || check_free "/userdata" "NVMe"

log "Syncing PCEngineCD..."
rcmd "mkdir -p '$NVME_ROMS/pcenginecd'"
rsync_to "$REDUMP/pcenginecd/" "$NVME_ROMS/pcenginecd/"

$DRY_RUN || check_free "/userdata" "NVMe"

# --- Step 3: Local move 3DS to HDD ---
step 3 "Move 3DS from NVMe to HDD (frees ~424 GB)"
local_move_to_hdd "3ds"
$DRY_RUN || check_free "/userdata" "NVMe"

# --- Step 4: Deploy dreamcast and saturn from build to NVMe ---
step 4 "Deploy Dreamcast and Saturn to NVMe (from build output)"

# Remove old symlinks first
for p in dreamcast saturn; do
    if $DRY_RUN; then
        echo "  [DRY-RUN] remove symlink $NVME_ROMS/$p, mkdir, rsync from build"
    else
        if rcmd "test -L '$NVME_ROMS/$p'"; then
            log "  Removing $p symlink..."
            rcmd "rm -f '$NVME_ROMS/$p'"
        fi
        rcmd "mkdir -p '$NVME_ROMS/$p'"
    fi
done

log "Syncing Dreamcast (124 GB)..."
rsync_to "$REDUMP/dreamcast/" "$NVME_ROMS/dreamcast/"
$DRY_RUN || check_free "/userdata" "NVMe"

log "Syncing Saturn (80 GB)..."
rsync_to "$REDUMP/saturn/" "$NVME_ROMS/saturn/"
$DRY_RUN || check_free "/userdata" "NVMe"

# --- Step 5: Local move NDS to HDD ---
step 5 "Move NDS from NVMe to HDD (frees ~55 GB)"
local_move_to_hdd "nds"
$DRY_RUN || check_free "/userdata" "NVMe"

# --- Step 6: Deploy PSP from build to NVMe ---
step 6 "Deploy PSP to NVMe (374 GB)"

if $DRY_RUN; then
    echo "  [DRY-RUN] remove psp symlink, rsync from build"
else
    if rcmd "test -L '$NVME_ROMS/psp'"; then
        log "  Removing PSP symlink..."
        rcmd "rm -f '$NVME_ROMS/psp'"
    fi
    rcmd "mkdir -p '$NVME_ROMS/psp'"
fi

log "Syncing PSP..."
rsync_to "$REDUMP/psp/" "$NVME_ROMS/psp/"
$DRY_RUN || check_free "/userdata" "NVMe"

# --- Step 7: Local move daphne to HDD ---
step 7 "Move Daphne from NVMe to HDD (frees ~32 GB)"
local_move_to_hdd "daphne"
$DRY_RUN || check_free "/userdata" "NVMe"

# --- Step 8: Local move arcade platforms to HDD ---
step 8 "Move arcade platforms from NVMe to HDD (frees ~398 GB)"
for arcade_sys in "${ARCADE_PLATFORMS[@]}"; do
    local_move_to_hdd "$arcade_sys"
done
$DRY_RUN || check_free "/userdata" "NVMe"

# --- Step 9: Deploy PS2 curated and Xbox curated to NVMe ---
step 9 "Deploy AI-curated PS2 (354 GB) and Xbox (149 GB) to NVMe"

# PS2: Create files-from list
log "Syncing PS2 (AI-Excellent, 158 games)..."
if $DRY_RUN; then
    echo "  [DRY-RUN] rsync ps2 with --files-from from ps2+AI-Excellent list"
else
    rcmd "mkdir -p '$NVME_ROMS/ps2'"
    ps2_list=$(make_list_file "$LISTS/ps2+AI-Excellent" ".chd")
    rsync $RSYNC_BASE -e "$RSYNC_SSH" \
        --files-from="$ps2_list" \
        "$REDUMP/ps2/" "$TARGET_HOST:$NVME_ROMS/ps2/"
    rm -f "$ps2_list"
fi
$DRY_RUN || check_free "/userdata" "NVMe"

# Xbox: Create files-from list
log "Syncing Xbox (AI-Great, 48 games)..."
if $DRY_RUN; then
    echo "  [DRY-RUN] rsync xbox with --files-from from xbox+AI-Great list"
else
    rcmd "mkdir -p '$NVME_ROMS/xbox'"
    xbox_list=$(make_list_file "$LISTS/xbox+AI-Great" ".iso")
    rsync $RSYNC_BASE -e "$RSYNC_SSH" \
        --files-from="$xbox_list" \
        "$REDUMP/xbox/" "$TARGET_HOST:$NVME_ROMS/xbox/"
    rm -f "$xbox_list"
fi
$DRY_RUN || check_free "/userdata" "NVMe"

# --- Step 10: Deploy megacd and neogeocd to HDD ---
step 10 "Deploy MegaCD and NeoGeoCD to HDD"

# Remove old megacd symlink if it exists, remove old HDD copy
if $DRY_RUN; then
    echo "  [DRY-RUN] rsync megacd, neogeocd to HDD and create symlinks"
else
    # MegaCD: was previously on HDD (symlinked), update in place
    if rcmd "test -L '$NVME_ROMS/megacd'"; then
        log "  MegaCD already symlinked to HDD, updating..."
        rcmd "rm -f '$NVME_ROMS/megacd'"
    elif rcmd "test -d '$NVME_ROMS/megacd'"; then
        log "  Removing MegaCD from NVMe..."
        rcmd "rm -rf '$NVME_ROMS/megacd'"
    fi
    rcmd "mkdir -p '$HDD_ROMS/megacd'"
    log "Syncing MegaCD to HDD..."
    rsync_to "$REDUMP/megacd/" "$HDD_ROMS/megacd/"
    rcmd "ln -sfn '$HDD_ROMS/megacd' '$NVME_ROMS/megacd'"
    
    # NeoGeoCD: new deployment to HDD
    rcmd "mkdir -p '$HDD_ROMS/neogeocd'"
    log "Syncing NeoGeoCD to HDD..."
    rsync_to "$REDUMP/neogeocd/" "$HDD_ROMS/neogeocd/"
    rcmd "ln -sfn '$HDD_ROMS/neogeocd' '$NVME_ROMS/neogeocd'"
fi

# --- Step 11: rsync HDD platforms from build ---
step 11 "Update HDD platforms from build output (rsync --delete)"

# 3DO: already on HDD, just update
log "Syncing 3DO..."
if $DRY_RUN; then
    echo "  [DRY-RUN] rsync 3do to HDD"
else
    # Remove old symlink pointing to wrong path if needed
    if rcmd "test -L '$NVME_ROMS/3do'"; then
        rcmd "rm -f '$NVME_ROMS/3do'"
    fi
    rcmd "mkdir -p '$HDD_ROMS/3do'"
    rsync_to "$REDUMP/3do/" "$HDD_ROMS/3do/"
    rcmd "ln -sfn '$HDD_ROMS/3do' '$NVME_ROMS/3do'"
fi

# 3DS
log "Updating 3DS on HDD from build..."
rsync_to "$NOINTRO/3ds/" "$HDD_ROMS/3ds/"
rcmd "ln -sfn '$HDD_ROMS/3ds' '$NVME_ROMS/3ds'" 2>/dev/null || true

# NDS
log "Updating NDS on HDD from build..."
rsync_to "$NOINTRO/nds/" "$HDD_ROMS/nds/"
rcmd "ln -sfn '$HDD_ROMS/nds' '$NVME_ROMS/nds'" 2>/dev/null || true

# Daphne
log "Updating Daphne on HDD from build..."
rsync_to "$LASERDISC/daphne/" "$HDD_ROMS/daphne/"
rcmd "ln -sfn '$HDD_ROMS/daphne' '$NVME_ROMS/daphne'" 2>/dev/null || true

# Arcade platforms
log "Syncing arcade platforms to HDD..."
for arcade_sys in "${ARCADE_PLATFORMS[@]}"; do
    if [[ -d "$ARCADE/$arcade_sys" ]]; then
        log "  $arcade_sys..."
        if ! $DRY_RUN; then
            rcmd "mkdir -p '$HDD_ROMS/$arcade_sys'"
            rsync_to "$ARCADE/$arcade_sys/" "$HDD_ROMS/$arcade_sys/"
            rcmd "ln -sfn '$HDD_ROMS/$arcade_sys' '$NVME_ROMS/$arcade_sys'"
        fi
    fi
done

# --- Step 12: rsync all cart platforms to NVMe ---
step 12 "Update cart platforms on NVMe (rsync --delete)"
for cart in "${CART_PLATFORMS[@]}"; do
    if [[ -d "$NOINTRO/$cart" ]]; then
        log "  $cart..."
        if ! $DRY_RUN; then
            rcmd "mkdir -p '$NVME_ROMS/$cart'"
            rsync_to "$NOINTRO/$cart/" "$NVME_ROMS/$cart/"
        fi
    else
        log "  $cart: no build output, skipping"
    fi
done
$DRY_RUN || check_free "/userdata" "NVMe"

# --- Step 13: Clean old HDD copies ---
step 13 "Clean old HDD copies of platforms now on NVMe"
for old_hdd in dreamcast psp saturn; do
    if $DRY_RUN; then
        echo "  [DRY-RUN] rm -rf $HDD_ROMS/$old_hdd"
    else
        if rcmd "test -d '$HDD_ROMS/$old_hdd'"; then
            local_size=$(rcmd "du -sh '$HDD_ROMS/$old_hdd' | awk '{print \$1}'")
            log "  Removing old $old_hdd from HDD ($local_size)..."
            rcmd "rm -rf '$HDD_ROMS/$old_hdd'"
        fi
    fi
done
$DRY_RUN || check_free "/media/int2tbhd" "HDD"

# --- Step 14: Final verification ---
step 14 "Final verification"
if ! $DRY_RUN; then
    echo ""
    echo "=== NVMe Storage ==="
    rcmd "df -h /userdata"
    echo ""
    echo "=== HDD Storage ==="
    rcmd "df -h /media/int2tbhd"
    echo ""
    echo "=== ROM Directory Summary ==="
    rcmd '
    echo "--- NVMe (direct) ---"
    for d in /userdata/roms/*/; do
        name=$(basename "$d")
        if [ -L "${d%/}" ]; then
            target=$(readlink "${d%/}")
            count=$(find "$target" -maxdepth 1 -type f 2>/dev/null | wc -l)
            echo "  $name → $target ($count files) [symlink]"
        else
            count=$(find "$d" -maxdepth 1 -type f 2>/dev/null | wc -l)
            size=$(du -sh "$d" 2>/dev/null | cut -f1)
            echo "  $name: $size ($count files)"
        fi
    done
    '
fi

echo ""
echo "============================================================"
echo "Migration complete!"
echo "============================================================"
echo ""
echo "NVMe platforms: psx, psp, ps2 (curated), xbox (curated),"
echo "  dreamcast, saturn, pcenginecd, + 33 cart platforms"
echo ""
echo "HDD platforms (symlinked): 3ds, nds, 3do, megacd, neogeocd,"
echo "  daphne, + 9 arcade platforms"
echo "============================================================"
