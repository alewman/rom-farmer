#!/bin/bash
# PS2 AI-Excellent → AI-Great Upgrade
# Transfers 162 new PS2 CHD games + all media from build server to NUC
# Prerequisite: NVMe must have ~340G free (after PSP/Saturn moves)

set -euo pipefail

NUC="nuc"
SRC="/data/emu/rom-farmer/output/redump-1g1r-eng-chd-batocera-v2/ps2"
DST="/userdata/roms/ps2"
LIST="/data/emu/rom-farmer/lists/ps2+AI-Great"
EXISTING_LIST="/data/emu/rom-farmer/lists/ps2+AI-Excellent"
LOG="/tmp/ps2-upgrade.log"

echo "=== PS2 AI-Great Upgrade ===" | tee "$LOG"
echo "Started: $(date)" | tee -a "$LOG"

# Check NVMe free space on NUC
free_gb=$(sshpass -p linux ssh "$NUC" "df /userdata --output=avail | tail -1")
free_gb=$((free_gb / 1048576))
echo "NVMe free: ${free_gb}G" | tee -a "$LOG"
if [ "$free_gb" -lt 340 ]; then
    echo "ERROR: Need 340G free on NVMe, only have ${free_gb}G" | tee -a "$LOG"
    echo "Wait for PSP/Saturn moves to complete first." | tee -a "$LOG"
    exit 1
fi

# Build list of new games to transfer
echo "Building upgrade file list..." | tee -a "$LOG"
comm -13 <(grep -v '^#' "$EXISTING_LIST" | grep -v '^$' | sort) \
         <(grep -v '^#' "$LIST" | grep -v '^$' | sort) > /tmp/ps2-new-games.txt
count=$(wc -l < /tmp/ps2-new-games.txt)
echo "  $count new games to transfer" | tee -a "$LOG"

# Build rsync file list (CHDs + media + gamelist)
echo "Building rsync file list..." | tee -a "$LOG"
> /tmp/ps2-rsync-files.txt

# Add new game CHDs
while IFS= read -r game; do
    chd="${game}.chd"
    if [ -f "$SRC/$chd" ]; then
        echo "$chd" >> /tmp/ps2-rsync-files.txt
    else
        echo "  MISSING: $chd" | tee -a "$LOG"
    fi
done < /tmp/ps2-new-games.txt

# Add all media (for existing + new games)
echo "media/" >> /tmp/ps2-rsync-files.txt

# Add gamelist.xml
[ -f "$SRC/gamelist.xml" ] && echo "gamelist.xml" >> /tmp/ps2-rsync-files.txt

file_count=$(wc -l < /tmp/ps2-rsync-files.txt)
echo "  $file_count entries in rsync file list" | tee -a "$LOG"

# Single rsync batch transfer
echo "Transferring via rsync --files-from..." | tee -a "$LOG"
sshpass -p linux rsync -a -r --info=progress2 \
    --files-from=/tmp/ps2-rsync-files.txt \
    "$SRC/" "root@10.10.20.183:$DST/" 2>&1 | tee -a "$LOG"
echo "Transfer complete" | tee -a "$LOG"

# Verify
echo "Verifying..." | tee -a "$LOG"
remote_count=$(sshpass -p linux ssh "$NUC" "ls '$DST'/*.chd 2>/dev/null | wc -l")
echo "  Remote PS2 CHD count: $remote_count" | tee -a "$LOG"
echo "  Expected: ~330 (166 existing + 162 new + multi-disc)" | tee -a "$LOG"

# Final storage
sshpass -p linux ssh "$NUC" "df -h /userdata | tail -1" | tee -a "$LOG"

echo "Completed: $(date)" | tee -a "$LOG"
echo "DONE" | tee -a "$LOG"
