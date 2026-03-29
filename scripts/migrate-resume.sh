#!/usr/bin/env bash
set -euo pipefail
# ============================================================================
# Migration resume — Steps 9-14
# Steps 0-8 already completed. This picks up from PS2/Xbox deployment.
# ============================================================================

TARGET_HOST="root@10.10.20.183"
TARGET_PASS="linux"
NVME_ROMS="/userdata/roms"
HDD_ROMS="/media/int2tbhd/roms"

RF_ROOT="/data/emu/rom-farmer"
REDUMP="$RF_ROOT/output/redump-1g1r-eng-chd-batocera-v2"
NOINTRO="$RF_ROOT/output/nointro-1g1r-eng-7z-batocera-v2"
ARCADE="$RF_ROOT/output/arcade-batocera"
LASERDISC="$RF_ROOT/output/laserdisc-batocera"
LISTS="$RF_ROOT/lists"

RSYNC_BASE="-avh --progress --stats --delete"
RSYNC_SSH="sshpass -p '$TARGET_PASS' ssh"
MAX_RETRIES=10
RETRY_DELAY=30

ARCADE_PLATFORMS=(mame fbneo naomi naomi2 atomiswave model2 model3 namco246 triforce)

CART_PLATFORMS=(nes snes megadrive n64 gba gb gbc gamegear \
    mastersystem pcengine atari2600 atari7800 atari5200 \
    sg1000 sega32x ngpc ngp wswan wswanc \
    lynx jaguar colecovision intellivision virtualboy vectrex \
    fds supergrafx msx1 msx2 pokemini sgb \
    gb2players gbc2players)

log() { echo "$(date '+%H:%M:%S') $*"; }
step() { echo ""; echo "========== STEP $1: $2 =========="; }

rcmd() {
    local attempt rc
    for attempt in $(seq 1 $MAX_RETRIES); do
        set +e
        sshpass -p "$TARGET_PASS" ssh "$TARGET_HOST" "$@"
        rc=$?
        set -e
        if (( rc != 255 )); then
            return $rc
        fi
        if (( attempt < MAX_RETRIES )); then
            log "  SSH connection failed (attempt $attempt/$MAX_RETRIES), retrying in ${RETRY_DELAY}s..."
            sleep "$RETRY_DELAY"
        fi
    done
    log "ERROR: SSH connection failed after $MAX_RETRIES attempts: $*"
    return 255
}

rsync_to() {
    local src="$1" dst="$2"
    shift 2
    local attempt rc
    for attempt in $(seq 1 $MAX_RETRIES); do
        set +e
        rsync $RSYNC_BASE "$@" -e "$RSYNC_SSH" "$src" "$TARGET_HOST:$dst"
        rc=$?
        set -e
        if (( rc == 0 )); then
            return 0
        elif (( rc == 255 )); then
            if (( attempt < MAX_RETRIES )); then
                log "  rsync SSH failure (attempt $attempt/$MAX_RETRIES), retrying in ${RETRY_DELAY}s..."
                sleep "$RETRY_DELAY"
            fi
        else
            log "ERROR: rsync failed with code $rc: $src → $dst"
            return $rc
        fi
    done
    log "ERROR: rsync SSH failed after $MAX_RETRIES attempts: $src → $dst"
    return 255
}

check_free() {
    local device="$1" label="$2"
    local free_gb
    free_gb=$(rcmd "df -BG '$device' | tail -1 | awk '{print \$4}' | tr -d 'G'")
    log "$label free space: ${free_gb} GB"
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

# ============================================================================

log "Resuming migration from Step 9"
check_free "/userdata" "NVMe"
check_free "/media/int2tbhd" "HDD"

# --- Step 9: Deploy PS2 curated and Xbox curated to NVMe ---
step 9 "Deploy AI-curated PS2 (354 GB) and Xbox (149 GB) to NVMe"

log "Syncing PS2 (AI-Excellent, 158 games)..."
rcmd "mkdir -p '$NVME_ROMS/ps2'"
ps2_list=$(make_list_file "$LISTS/ps2+AI-Excellent" ".chd")
rsync $RSYNC_BASE -e "$RSYNC_SSH" \
    --files-from="$ps2_list" \
    "$REDUMP/ps2/" "$TARGET_HOST:$NVME_ROMS/ps2/"
rm -f "$ps2_list"
check_free "/userdata" "NVMe"

log "Syncing Xbox (AI-Great, 48 games)..."
rcmd "mkdir -p '$NVME_ROMS/xbox'"
xbox_list=$(make_list_file "$LISTS/xbox+AI-Great" ".iso")
rsync $RSYNC_BASE -e "$RSYNC_SSH" \
    --files-from="$xbox_list" \
    "$REDUMP/xbox/" "$TARGET_HOST:$NVME_ROMS/xbox/"
rm -f "$xbox_list"
check_free "/userdata" "NVMe"

# --- Step 10: Deploy megacd and neogeocd to HDD ---
step 10 "Deploy MegaCD and NeoGeoCD to HDD"

# MegaCD: remove old symlink, update HDD copy
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

# NeoGeoCD
rcmd "mkdir -p '$HDD_ROMS/neogeocd'"
log "Syncing NeoGeoCD to HDD..."
rsync_to "$REDUMP/neogeocd/" "$HDD_ROMS/neogeocd/"
rcmd "ln -sfn '$HDD_ROMS/neogeocd' '$NVME_ROMS/neogeocd'"

# --- Step 11: rsync HDD platforms from build ---
step 11 "Update HDD platforms from build output (rsync --delete)"

# 3DO
log "Syncing 3DO..."
if rcmd "test -L '$NVME_ROMS/3do'"; then
    rcmd "rm -f '$NVME_ROMS/3do'"
fi
rcmd "mkdir -p '$HDD_ROMS/3do'"
rsync_to "$REDUMP/3do/" "$HDD_ROMS/3do/"
rcmd "ln -sfn '$HDD_ROMS/3do' '$NVME_ROMS/3do'"

# 3DS
log "Updating 3DS on HDD from build..."
rsync_to "$NOINTRO/3ds/" "$HDD_ROMS/3ds/"
rcmd "ln -sfn '$HDD_ROMS/3ds' '$NVME_ROMS/3ds'" || true

# NDS
log "Updating NDS on HDD from build..."
rcmd "mkdir -p '$HDD_ROMS/nds'"
rsync_to "$NOINTRO/nds/" "$HDD_ROMS/nds/"
rcmd "ln -sfn '$HDD_ROMS/nds' '$NVME_ROMS/nds'" || true

# Daphne
log "Updating Daphne on HDD from build..."
rsync_to "$LASERDISC/daphne/" "$HDD_ROMS/daphne/"
rcmd "ln -sfn '$HDD_ROMS/daphne' '$NVME_ROMS/daphne'" || true

# Arcade platforms
log "Syncing arcade platforms to HDD..."
for arcade_sys in "${ARCADE_PLATFORMS[@]}"; do
    if [[ -d "$ARCADE/$arcade_sys" ]]; then
        log "  $arcade_sys..."
        rcmd "mkdir -p '$HDD_ROMS/$arcade_sys'"
        rsync_to "$ARCADE/$arcade_sys/" "$HDD_ROMS/$arcade_sys/"
        rcmd "ln -sfn '$HDD_ROMS/$arcade_sys' '$NVME_ROMS/$arcade_sys'" || true
    fi
done

# --- Step 12: rsync all cart platforms to NVMe ---
step 12 "Update cart platforms on NVMe (rsync --delete)"
for cart in "${CART_PLATFORMS[@]}"; do
    if [[ -d "$NOINTRO/$cart" ]]; then
        log "  $cart..."
        rcmd "mkdir -p '$NVME_ROMS/$cart'"
        rsync_to "$NOINTRO/$cart/" "$NVME_ROMS/$cart/"
    else
        log "  $cart: no build output, skipping"
    fi
done
check_free "/userdata" "NVMe"

# --- Step 13: Verify all symlinks ---
step 13 "Verify symlinks"
rcmd '
echo "--- Symlinks ---"
for d in /userdata/roms/*/; do
    name=$(basename "$d")
    if [ -L "${d%/}" ]; then
        target=$(readlink "${d%/}")
        count=$(find "$target" -maxdepth 1 -type f 2>/dev/null | wc -l)
        printf "  %-20s → %s (%s files) [symlink]\n" "$name" "$target" "$count"
    fi
done
'

# --- Step 14: Final verification ---
step 14 "Final verification"
echo ""
echo "=== NVMe Storage ==="
rcmd "df -h /userdata"
echo ""
echo "=== HDD Storage ==="
rcmd "df -h /media/int2tbhd"
echo ""
echo "=== ROM Directory Summary ==="
rcmd '
for d in /userdata/roms/*/; do
    name=$(basename "$d")
    if [ -L "${d%/}" ]; then
        target=$(readlink "${d%/}")
        count=$(find "$target" -maxdepth 1 -type f 2>/dev/null | wc -l)
        size=$(du -sh "$target" 2>/dev/null | cut -f1)
        printf "  %-20s %8s  %5s files  [HDD]\n" "$name" "$size" "$count"
    else
        count=$(find "$d" -maxdepth 1 -type f 2>/dev/null | wc -l)
        size=$(du -sh "$d" 2>/dev/null | cut -f1)
        printf "  %-20s %8s  %5s files  [NVMe]\n" "$name" "$size" "$count"
    fi
done
'

echo ""
echo "============================================================"
echo "Migration complete!"
echo "============================================================"
