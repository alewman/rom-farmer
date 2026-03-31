#!/bin/bash
# rclone-myrient-final-refresh.sh — Final sync of ALL local Myrient content
#
# Uses the DuckDB catalog to determine which (collection, system) pairs
# actually exist on Myrient, then syncs ONLY those. This prevents syncing
# against renamed/removed systems (which causes garbage downloads).
#
# Uses rclone sync per system. For large CD/DVD systems originally downloaded
# USA-only, the filter is preserved to avoid downloading all regions.
#
# Usage:
#   ./rclone-myrient-final-refresh.sh           # Refresh everything
#   ./rclone-myrient-final-refresh.sh status     # Show what would be synced
#   ./rclone-myrient-final-refresh.sh <collection>  # Just one collection
#
# Myrient shutdown: March 31, 2026 — THIS IS THE LAST CALL

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_PATH=/data/emu/source
MIRROR="${BASE_PATH}/myrient.erista.me/files"
MYRIENT="https://myrient.erista.me/files"
CATALOG_DB="${BASE_PATH}/myrient-catalog.duckdb"
export RCLONE_VERBOSE=1

# Track stats
TOTAL=0
SUCCESS=0
SKIPPED=0
FAILED=0
START_TIME=$(date +%s)

# ── USA-filtered Redump systems (originally downloaded with region filter) ──
# These are large (multi-TB) disc systems — downloading all regions would be too big
USA_FILTERED_REDUMP=(
    "Microsoft - Xbox"
    "Microsoft - Xbox 360"
    "Microsoft - Xbox One"
    "Nintendo - GameCube - NKit RVZ [zstd-19-128k]"
    "Nintendo - Wii - NKit RVZ [zstd-19-128k]"
    "Nintendo - Wii U - WUX"
    "Panasonic - 3DO Interactive Multiplayer"
    "Sony - PlayStation Portable"
    "Sony - PlayStation 2"
    "Sony - PlayStation 3"
)

# ── Systems to SKIP entirely ──
SKIP_SYSTEMS=(
    "IBM - PC compatible"   # Deleted intentionally — 13 TB
)

# ── Build list of valid (collection, system) pairs from catalog DB ──
VALID_SYSTEMS_FILE=$(mktemp)
trap "rm -f '$VALID_SYSTEMS_FILE'" EXIT

if [[ ! -f "$CATALOG_DB" ]]; then
    echo "ERROR: Catalog DB not found at $CATALOG_DB"
    echo "Run myrient-catalog.py first to build the catalog."
    exit 1
fi

echo "Loading valid systems from catalog DB..."
python3 -c "
import duckdb
db = duckdb.connect('$CATALOG_DB', read_only=True)
rows = db.execute('SELECT DISTINCT collection, system FROM files WHERE system IS NOT NULL ORDER BY collection, system').fetchall()
for coll, sys in rows:
    print(f'{coll}\t{sys}')
db.close()
" > "$VALID_SYSTEMS_FILE"

VALID_COUNT=$(wc -l < "$VALID_SYSTEMS_FILE")
echo "Catalog has ${VALID_COUNT} valid collection/system pairs"

is_valid_system() {
    local collection="$1"
    local system="$2"
    grep -qF "${collection}	${system}" "$VALID_SYSTEMS_FILE"
}

log() {
    echo ""
    echo "══════════════════════════════════════════════════════════════"
    echo "  $1"
    echo "  $(date '+%Y-%m-%d %H:%M:%S')"
    echo "══════════════════════════════════════════════════════════════"
    echo ""
}

check_space() {
    local free_gb
    free_gb=$(df -BG /data/emu | tail -1 | awk '{print $4}' | sed 's/G//')
    echo "  Disk space available: ${free_gb} GB"
    if (( free_gb < 500 )); then
        echo "  WARNING: LOW SPACE — less than 500 GB free. Stopping."
        return 1
    fi
    return 0
}

is_usa_filtered() {
    local sys="$1"
    for f in "${USA_FILTERED_REDUMP[@]}"; do
        if [[ "$f" == "$sys" ]]; then
            return 0
        fi
    done
    return 1
}

is_skipped() {
    local sys="$1"
    for s in "${SKIP_SYSTEMS[@]}"; do
        if [[ "$s" == "$sys" ]]; then
            return 0
        fi
    done
    return 1
}

sync_system() {
    local collection="$1"
    local system="$2"
    local filter="${3:-}"
    local local_dir="${MIRROR}/${collection}/${system}"

    TOTAL=$((TOTAL + 1))

    if is_skipped "$system"; then
        echo "  SKIP: ${collection}/${system} (blocklisted)"
        SKIPPED=$((SKIPPED + 1))
        return 0
    fi

    # Safety check: only sync systems confirmed to exist on Myrient
    if ! is_valid_system "$collection" "$system"; then
        echo "  SKIP: ${collection}/${system} (not in Myrient catalog — renamed/removed)"
        SKIPPED=$((SKIPPED + 1))
        return 0
    fi

    if ! check_space; then
        echo "  ABORT: low disk space"
        FAILED=$((FAILED + 1))
        return 1
    fi

    echo "  -> Syncing: ${collection}/${system}${filter:+ [filter: $filter]}"

    local remote_path="myrient:${collection}/${system}"

    if [[ -n "$filter" ]]; then
        /usr/bin/rclone sync "$remote_path" "$local_dir" --include "$filter" --size-only --retries 3 --low-level-retries 10 --retries-sleep 10s
    else
        /usr/bin/rclone sync "$remote_path" "$local_dir" --size-only --retries 3 --low-level-retries 10 --retries-sleep 10s
    fi

    local rc=$?
    if [[ $rc -eq 0 ]]; then
        SUCCESS=$((SUCCESS + 1))
    else
        echo "  FAILED (rc=$rc): ${collection}/${system}"
        FAILED=$((FAILED + 1))
    fi
    return $rc
}

sync_collection() {
    local collection="$1"
    local coll_dir="${MIRROR}/${collection}"

    if [[ ! -d "$coll_dir" ]]; then
        echo "  Collection not found locally: ${collection}"
        return 1
    fi

    log "Refreshing: ${collection}"

    # Some collections have files directly (not in subdirs) — handle both patterns
    local has_subdirs=0
    local has_files=0
    for item in "$coll_dir"/*/; do
        [[ -d "$item" ]] && has_subdirs=1 && break
    done
    for item in "$coll_dir"/*; do
        [[ -f "$item" ]] && has_files=1 && break
    done

    if [[ $has_subdirs -eq 1 ]]; then
        # Iterate system subdirectories
        for sys_dir in "$coll_dir"/*/; do
            [[ ! -d "$sys_dir" ]] && continue
            local system
            system=$(basename "$sys_dir")

            # Apply USA filter for known filtered Redump systems
            if [[ "$collection" == "Redump" ]] && is_usa_filtered "$system"; then
                sync_system "$collection" "$system" "*(*USA*)*"
            else
                sync_system "$collection" "$system"
            fi
        done
    fi

    # Also sync any loose files at the collection root (some have files + dirs)
    if [[ $has_files -eq 1 ]] && [[ $has_subdirs -eq 0 ]]; then
        # Pure file collection (no subdirs) — sync the collection itself
        TOTAL=$((TOTAL + 1))
        echo "  -> Syncing (flat): ${collection}"
        /usr/bin/rclone sync "myrient:${collection}" "$coll_dir" --size-only --retries 3 --low-level-retries 10 --retries-sleep 10s
        if [[ $? -eq 0 ]]; then
            SUCCESS=$((SUCCESS + 1))
        else
            FAILED=$((FAILED + 1))
        fi
    fi
}

show_status() {
    echo ""
    echo "== Local Myrient Mirror — Refresh Plan =="
    echo ""

    local total_valid=0
    local total_invalid=0

    for coll_dir in "$MIRROR"/*/; do
        [[ ! -d "$coll_dir" ]] && continue
        local coll
        coll=$(basename "$coll_dir")
        local valid=0
        local invalid=0
        local has_subdirs=0
        local file_count=0
        for sys_dir in "$coll_dir"/*/; do
            [[ ! -d "$sys_dir" ]] && continue
            has_subdirs=1
            local sys
            sys=$(basename "$sys_dir")
            if is_valid_system "$coll" "$sys"; then
                valid=$((valid + 1))
            else
                invalid=$((invalid + 1))
            fi
        done
        if [[ $has_subdirs -eq 0 ]]; then
            # Flat collection (files, no subdirs) — count files
            file_count=$(find "$coll_dir" -maxdepth 1 -type f | wc -l)
            total_valid=$((total_valid + 1))
            printf "  %-45s %4d files (flat sync)\n" "$coll" "$file_count"
        else
            total_valid=$((total_valid + valid))
            total_invalid=$((total_invalid + invalid))
            if [[ $invalid -gt 0 ]]; then
                printf "  %-45s %4d valid, %d SKIPPED\n" "$coll" "$valid" "$invalid"
            else
                printf "  %-45s %4d valid\n" "$coll" "$valid"
            fi
        fi
    done
    echo ""
    echo "Total: ${total_valid} systems to sync, ${total_invalid} to skip (not in catalog)"
    echo ""
    echo "USA-filtered Redump systems:"
    for f in "${USA_FILTERED_REDUMP[@]}"; do
        if [[ -d "${MIRROR}/Redump/${f}" ]]; then
            echo "  [filtered] $f"
        fi
    done
    echo ""
    echo "Blocklisted systems:"
    for s in "${SKIP_SYSTEMS[@]}"; do
        echo "  [skip] $s"
    done
}

# ── Main ──

MODE="${1:-all}"

case "$MODE" in
    status)
        show_status
        exit 0
        ;;
    all)
        log "FINAL MYRIENT REFRESH — ALL COLLECTIONS"
        echo "Syncing $(ls -1d "$MIRROR"/*/ 2>/dev/null | wc -l) collections"
        echo "Only systems confirmed in catalog DB will be synced"
        echo ""

        # Order: smaller/critical collections first, big ones last
        # This ensures we get the most important updates even if we hit space issues
        PRIORITY_ORDER=(
            "No-Intro"
            "Redump"
            "Hardware Target Game Database"
            "T-En Collection"
            "RetroAchievements"
            "FinalBurn Neo"
            "MAME"
            "HBMAME"
            "Lost Level"
            "TOSEC-PIX"
            "Touhou Project Collection"
            "Miscellaneous"
            "Laserdisc Collection"
            "Total DOS Collection"
            "eXo"
            "TeknoParrot"
        )

        for coll in "${PRIORITY_ORDER[@]}"; do
            if [[ -d "${MIRROR}/${coll}" ]]; then
                sync_collection "$coll"
            fi
        done

        # Catch any collections not in the priority list
        for coll_dir in "$MIRROR"/*/; do
            [[ ! -d "$coll_dir" ]] && continue
            coll=$(basename "$coll_dir")
            already_done=0
            for p in "${PRIORITY_ORDER[@]}"; do
                [[ "$p" == "$coll" ]] && already_done=1 && break
            done
            if [[ $already_done -eq 0 ]]; then
                sync_collection "$coll"
            fi
        done
        ;;
    *)
        # Single collection mode
        sync_collection "$MODE"
        ;;
esac

ELAPSED=$(( $(date +%s) - START_TIME ))
HOURS=$(( ELAPSED / 3600 ))
MINS=$(( (ELAPSED % 3600) / 60 ))

log "FINAL REFRESH COMPLETE"
echo "  Systems synced: ${SUCCESS}/${TOTAL}"
echo "  Skipped:        ${SKIPPED}"
echo "  Failed:         ${FAILED}"
echo "  Elapsed:        ${HOURS}h ${MINS}m"
echo "  Finished:       $(date)"
echo ""
