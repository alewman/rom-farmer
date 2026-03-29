#!/bin/bash
# myrient-hardlink-backup.sh — Create a hard-link snapshot of the Myrient source directory
#
# Hard links cost ZERO extra disk space. Both the backup and source point to
# the same on-disk data. If rclone sync later deletes a file from the source
# (because Myrient removed it), the backup's hard link still holds the data.
# Space is only reclaimed when ALL links to a file are removed.
#
# Each snapshot is timestamped so you can keep multiple generations.
# Use 'prune' to clean old snapshots (keeping the most recent N).
#
# Usage:
#   ./myrient-hardlink-backup.sh                 # Create a new snapshot
#   ./myrient-hardlink-backup.sh status          # Show existing snapshots
#   ./myrient-hardlink-backup.sh prune [N]       # Keep only the N most recent (default: 3)
#   ./myrient-hardlink-backup.sh verify          # Verify hard links are intact
#   ./myrient-hardlink-backup.sh diff [SNAP]     # Show files in snapshot but not in source

set -euo pipefail

# ─── Configuration ───────────────────────────────────────────────────
SOURCE_DIR="/data/emu/source/myrient.erista.me"
BACKUP_BASE="/data/emu/source/myrient-snapshots"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
SNAPSHOT_DIR="${BACKUP_BASE}/snapshot_${TIMESTAMP}"

# ─── Functions ───────────────────────────────────────────────────────

log() {
    echo "[$(date '+%H:%M:%S')] $1"
}

create_snapshot() {
    if [ ! -d "$SOURCE_DIR" ]; then
        echo "ERROR: Source directory not found: $SOURCE_DIR"
        exit 1
    fi

    mkdir -p "$BACKUP_BASE"

    log "Creating hard-link snapshot..."
    log "  Source: $SOURCE_DIR"
    log "  Target: $SNAPSHOT_DIR"

    # Count files first
    local file_count
    file_count=$(find "$SOURCE_DIR" -type f | wc -l)
    log "  Files to link: ${file_count}"

    # cp -al creates a recursive hard-link copy:
    #   -a  = archive mode (preserves permissions, timestamps, symlinks, etc.)
    #   -l  = hard link files instead of copying
    cp -al "$SOURCE_DIR" "$SNAPSHOT_DIR"

    # Verify the snapshot
    local snap_count
    snap_count=$(find "$SNAPSHOT_DIR" -type f | wc -l)

    # Calculate apparent size vs actual disk usage
    local apparent
    apparent=$(du -sh --apparent-size "$SNAPSHOT_DIR" 2>/dev/null | cut -f1)
    local actual
    actual=$(du -sh "$SNAPSHOT_DIR" 2>/dev/null | cut -f1)

    log "Snapshot complete!"
    log "  Files linked: ${snap_count}"
    log "  Apparent size: ${apparent} (data preserved if source files are deleted)"
    log "  Actual extra space: ~0 bytes (hard links share on-disk data)"
    log ""
    log "  Path: $SNAPSHOT_DIR"

    # Write a metadata file
    cat > "${SNAPSHOT_DIR}/.snapshot_meta" << EOF
snapshot_created: ${TIMESTAMP}
source_dir: ${SOURCE_DIR}
file_count: ${snap_count}
apparent_size: ${apparent}
created_by: myrient-hardlink-backup.sh
purpose: Preserve files that rclone sync may delete when Myrient removes content
EOF

    log ""
    log "To see what rclone sync would delete (files in snapshot but not source):"
    log "  $0 diff snapshot_${TIMESTAMP}"
}

show_status() {
    echo ""
    echo "═══════════════════════════════════════════════════"
    echo "  Myrient Hard-Link Snapshots"
    echo "═══════════════════════════════════════════════════"
    echo ""
    echo "  Source: $SOURCE_DIR"
    echo "  Backup: $BACKUP_BASE"
    echo ""

    if [ ! -d "$BACKUP_BASE" ]; then
        echo "  No snapshots exist yet."
        echo "  Run: $0  (to create first snapshot)"
        return
    fi

    # List snapshots
    local count=0
    for snap in "$BACKUP_BASE"/snapshot_*; do
        [ -d "$snap" ] || continue
        count=$((count + 1))
        local name
        name=$(basename "$snap")
        local files
        files=$(find "$snap" -type f -not -name '.snapshot_meta' | wc -l)
        local apparent
        apparent=$(du -sh --apparent-size "$snap" 2>/dev/null | cut -f1)
        local created=""
        if [ -f "$snap/.snapshot_meta" ]; then
            created=$(grep 'snapshot_created:' "$snap/.snapshot_meta" | cut -d' ' -f2)
        fi
        echo "  ${name}: ${files} files, ${apparent} apparent (created: ${created:-unknown})"
    done

    if [ "$count" -eq 0 ]; then
        echo "  No snapshots exist yet."
    else
        echo ""
        echo "  Total snapshots: $count"

        # Show source stats for comparison
        local src_files
        src_files=$(find "$SOURCE_DIR" -type f | wc -l)
        local src_size
        src_size=$(du -sh --apparent-size "$SOURCE_DIR" 2>/dev/null | cut -f1)
        echo ""
        echo "  Current source: ${src_files} files, ${src_size}"
    fi

    # Show actual disk usage
    echo ""
    echo "  Disk: $(df -h /data/emu | tail -1 | awk '{print $4 " free / " $2 " total"}')"
    echo ""
}

prune_snapshots() {
    local keep="${1:-3}"

    if [ ! -d "$BACKUP_BASE" ]; then
        echo "No snapshots directory found."
        return
    fi

    # Get sorted list of snapshots (oldest first)
    local snapshots=()
    while IFS= read -r snap; do
        snapshots+=("$snap")
    done < <(find "$BACKUP_BASE" -maxdepth 1 -name 'snapshot_*' -type d | sort)

    local total=${#snapshots[@]}

    if [ "$total" -le "$keep" ]; then
        echo "Only ${total} snapshot(s) exist — keeping all (threshold: ${keep})."
        return
    fi

    local to_remove=$((total - keep))
    echo "Pruning ${to_remove} old snapshot(s), keeping ${keep} most recent..."
    echo ""

    for ((i=0; i<to_remove; i++)); do
        local snap="${snapshots[$i]}"
        local name
        name=$(basename "$snap")
        local files
        files=$(find "$snap" -type f | wc -l)
        echo "  Removing: ${name} (${files} files)"
        rm -rf "$snap"
    done

    echo ""
    echo "Done. Remaining snapshots:"
    show_status
}

verify_snapshot() {
    if [ ! -d "$BACKUP_BASE" ]; then
        echo "No snapshots directory found."
        return
    fi

    # Use the most recent snapshot
    local latest
    latest=$(find "$BACKUP_BASE" -maxdepth 1 -name 'snapshot_*' -type d | sort | tail -1)

    if [ -z "$latest" ]; then
        echo "No snapshots found."
        return
    fi

    local name
    name=$(basename "$latest")
    echo ""
    echo "Verifying latest snapshot: ${name}"
    echo ""

    # Check that files have link count > 1 (shared with source)
    local total=0
    local shared=0
    local orphaned=0

    while IFS= read -r file; do
        total=$((total + 1))
        local links
        links=$(stat -c '%h' "$file" 2>/dev/null || echo "1")
        if [ "$links" -gt 1 ]; then
            shared=$((shared + 1))
        else
            orphaned=$((orphaned + 1))
        fi
        # Progress every 10000 files
        if [ $((total % 10000)) -eq 0 ]; then
            echo "  Checked ${total} files..."
        fi
    done < <(find "$latest" -type f -not -name '.snapshot_meta')

    echo ""
    echo "  Total files: ${total}"
    echo "  Shared with source (link count > 1): ${shared}"
    echo "  Orphaned (source file deleted, snapshot preserves it): ${orphaned}"
    echo ""

    if [ "$orphaned" -gt 0 ]; then
        echo "  ${orphaned} file(s) exist ONLY in the snapshot — these were"
        echo "  deleted from the source (probably by rclone sync)."
        echo "  The snapshot is protecting them. Run '$0 diff' to see which ones."
    else
        echo "  All files are shared — no deletions detected from source."
    fi
    echo ""
}

diff_snapshot() {
    local snap_name="${1:-}"

    if [ -z "$snap_name" ]; then
        # Use latest
        local latest
        latest=$(find "$BACKUP_BASE" -maxdepth 1 -name 'snapshot_*' -type d | sort | tail -1)
        if [ -z "$latest" ]; then
            echo "No snapshots found."
            return
        fi
        snap_name=$(basename "$latest")
    fi

    local snap_dir="${BACKUP_BASE}/${snap_name}"

    if [ ! -d "$snap_dir" ]; then
        echo "Snapshot not found: $snap_dir"
        return
    fi

    echo ""
    echo "Files in ${snap_name} but NOT in source (protected from deletion):"
    echo "══════════════════════════════════════════════════════════════════"
    echo ""

    local count=0
    # Compare by relative path
    while IFS= read -r file; do
        local rel="${file#${snap_dir}/}"
        local src_file="${SOURCE_DIR}/${rel}"
        if [ ! -f "$src_file" ]; then
            local size
            size=$(stat -c '%s' "$file" 2>/dev/null || echo "0")
            local human
            human=$(numfmt --to=iec "$size" 2>/dev/null || echo "${size}B")
            echo "  [${human}] ${rel}"
            count=$((count + 1))
        fi
    done < <(find "$snap_dir" -type f -not -name '.snapshot_meta')

    echo ""
    if [ "$count" -eq 0 ]; then
        echo "  No differences — source and snapshot are identical."
    else
        echo "  ${count} file(s) preserved by snapshot (deleted from source)."
    fi
    echo ""
}

# ─── Dispatcher ──────────────────────────────────────────────────────
case "${1:-create}" in
    create|"")
        create_snapshot
        ;;
    status)
        show_status
        ;;
    prune)
        prune_snapshots "${2:-3}"
        ;;
    verify)
        verify_snapshot
        ;;
    diff)
        diff_snapshot "${2:-}"
        ;;
    *)
        echo "Myrient Hard-Link Backup"
        echo ""
        echo "Creates zero-cost snapshots using hard links to protect files"
        echo "that rclone sync might delete when Myrient removes content."
        echo ""
        echo "Usage: $0 [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  create         Create a new hard-link snapshot (default)"
        echo "  status         Show existing snapshots"
        echo "  prune [N]      Remove old snapshots, keep N most recent (default: 3)"
        echo "  verify         Check if source files have been deleted"
        echo "  diff [SNAP]    Show files preserved by snapshot but missing from source"
        echo ""
        echo "How it works:"
        echo "  Hard links point two paths to the same on-disk data."
        echo "  If rclone sync deletes file A from source/, the snapshot's"
        echo "  hard link still references the data — zero extra space until"
        echo "  a deletion occurs, then only the deleted files use space."
        echo ""
        exit 0
        ;;
esac
