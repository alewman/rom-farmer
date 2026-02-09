#!/bin/bash
#
# Pre-calculate and cache hashes for source ROM files
# Designed for long-running parallel processing with comprehensive logging
#
# Usage: ./tools/precalculate-hashes.sh [--resume] [--dry-run] [--jobs N]
#

set -euo pipefail

# Configuration
SOURCE_DIR="/data/emu/source/myrient.erista.me/files"
DB_PATH="/data/emu/rom-groomer-python/metadata/database/romgroomer.db"
LOG_DIR="/data/emu/rom-groomer-python/logs/hash-precalc"
TEMP_DIR="/data/emu/rom-groomer-python/temp/hash-extraction"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${LOG_DIR}/precalc_${TIMESTAMP}.log"
ERROR_LOG="${LOG_DIR}/precalc_${TIMESTAMP}_errors.log"
PROGRESS_FILE="${LOG_DIR}/precalc_${TIMESTAMP}_progress.txt"
STATS_FILE="${LOG_DIR}/precalc_${TIMESTAMP}_stats.json"

# Parallel job control
JOBS=${JOBS:-8}  # Default 8 parallel jobs
DRY_RUN=0
RESUME=0

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --resume)
            RESUME=1
            shift
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --jobs)
            JOBS="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--resume] [--dry-run] [--jobs N]"
            exit 1
            ;;
    esac
done

# Create log directory
mkdir -p "${LOG_DIR}"

# Logging functions
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "${LOG_FILE}"
}

log_error() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $*" | tee -a "${LOG_FILE}" "${ERROR_LOG}"
}

log_progress() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" >> "${PROGRESS_FILE}"
}

# Check dependencies
check_dependencies() {
    local missing=()
    
    for cmd in rhash parallel sqlite3 python3 unzip 7z; do
        if ! command -v "$cmd" &>/dev/null; then
            missing+=("$cmd")
        fi
    done
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing required commands: ${missing[*]}"
        exit 1
    fi
    
    if [[ ! -d "$SOURCE_DIR" ]]; then
        log_error "Source directory not found: $SOURCE_DIR"
        exit 1
    fi
    
    if [[ ! -f "$DB_PATH" ]]; then
        log_error "Database not found: $DB_PATH"
        log_error "Please run: romgroomer db init"
        exit 1
    fi
    
    # Create temp directory for extraction
    mkdir -p "$TEMP_DIR"
}

# Get file extensions to process
get_file_extensions() {
    cat <<'EOF'
# Archive files from Myrient (No-Intro and Redump)
-name "*.zip" -o -name "*.7z"
EOF
}

# Find all ZIP/7z files to process
find_files() {
    log "Scanning for archive files in: $SOURCE_DIR"
    
    find "$SOURCE_DIR" -type f \( -name "*.zip" -o -name "*.7z" \) -printf '%p\t%s\t%T@\n' | sort
}

# Check if file is already cached and up-to-date
is_file_cached() {
    local archive_path="$1"
    local inner_filename="$2"
    local filesize="$3"
    local mtime="$4"
    
    # Create unique path identifier: archive_path::inner_filename
    local cache_key="${archive_path}::${inner_filename}"
    
    # Query database for existing cache entry
    local cached=$(sqlite3 "$DB_PATH" <<SQL
SELECT COUNT(*) FROM hash_cache
WHERE file_path = '${cache_key//\'/\'\'}'
  AND file_size = $filesize
  AND mtime = $mtime
  AND md5 IS NOT NULL
  AND sha1 IS NOT NULL
  AND crc32 IS NOT NULL;
SQL
)
    
    [[ "$cached" -eq 1 ]]
}

# Extract and calculate hashes for files inside ZIP/7z archive
calculate_archive_hashes() {
    local archive_path="$1"
    local archive_size="$2"
    local archive_mtime="$3"
    
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ARCHIVE: $archive_path" >> "$PROGRESS_FILE"
    
    # Create unique temp directory for this archive
    local temp_extract="$TEMP_DIR/$$_$(basename "$archive_path" .zip)_$(date +%s%N)"
    mkdir -p "$temp_extract"
    
    # List archive contents first
    local file_list=""
    if [[ "$archive_path" == *.zip ]]; then
        file_list=$(unzip -l "$archive_path" 2>/dev/null | awk '/^---------/{p=1; next} p && NF>=4 {$1=""; $2=""; $3=""; print substr($0,4)}' | grep -v "^$")
    elif [[ "$archive_path" == *.7z ]]; then
        file_list=$(7z l -slt "$archive_path" 2>/dev/null | grep "^Path = " | cut -d' ' -f3- | tail -n +2)
    else
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: Unsupported archive format: $archive_path" >> "$ERROR_LOG"
        echo "ERROR"
        rm -rf "$temp_extract"
        return 1
    fi
    
    if [[ -z "$file_list" ]]; then
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: Failed to list archive contents: $archive_path" >> "$ERROR_LOG"
        echo "ERROR"
        rm -rf "$temp_extract"
        return 1
    fi
    
    local success_count=0
    local skip_count=0
    local error_count=0
    
    # Process each file in the archive
    while IFS= read -r inner_file; do
        # Skip directories and TORRENTZIPPED marker
        [[ -z "$inner_file" || "$inner_file" == */ || "$inner_file" == "TORRENTZIPPED-"* ]] && continue
        
        # Extract single file
        local extract_success=false
        if [[ "$archive_path" == *.zip ]]; then
            if unzip -j -o "$archive_path" "$inner_file" -d "$temp_extract" &>/dev/null; then
                extract_success=true
            fi
        elif [[ "$archive_path" == *.7z ]]; then
            if 7z e -o"$temp_extract" "$archive_path" "$inner_file" -y &>/dev/null; then
                extract_success=true
            fi
        fi
        
        if ! $extract_success; then
            echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: Failed to extract: $inner_file from $archive_path" >> "$ERROR_LOG"
            ((error_count++))
            continue
        fi
        
        # Get extracted file path
        local extracted_file="$temp_extract/$(basename "$inner_file")"
        
        if [[ ! -f "$extracted_file" ]]; then
            echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: Extracted file not found: $extracted_file" >> "$ERROR_LOG"
            ((error_count++))
            continue
        fi
        
        # Get file size and mtime
        local inner_size=$(stat -c%s "$extracted_file" 2>/dev/null)
        local inner_mtime="$archive_mtime"  # Use archive mtime as proxy
        
        # Create cache key: archive_path::inner_filename
        local cache_key="${archive_path}::${inner_file}"
        
        # Check if already cached (if RESUME mode)
        if [[ $RESUME -eq 1 ]]; then
            local cached=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM hash_cache WHERE file_path = '${cache_key//\'/\'\'}' AND file_size = $inner_size AND mtime = $inner_mtime AND md5 IS NOT NULL;" 2>/dev/null || echo "0")
            if [[ "$cached" -eq 1 ]]; then
                echo "[$(date +'%Y-%m-%d %H:%M:%S')]   SKIP: $inner_file (already cached)" >> "$PROGRESS_FILE"
                ((skip_count++))
                rm -f "$extracted_file"
                continue
            fi
        fi
        
        # Calculate hashes
        local start_time=$(date +%s)
        local hash_output
        
        if ! hash_output=$(rhash --crc32 --md5 --sha1 --printf='%c %m %h\n' "$extracted_file" 2>&1); then
            echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: Failed to hash: $inner_file from $archive_path - $hash_output" >> "$ERROR_LOG"
            ((error_count++))
            rm -f "$extracted_file"
            continue
        fi
        
        local end_time=$(date +%s)
        local calc_time=$((end_time - start_time))
        
        # Parse rhash output with custom printf format: <crc32> <md5> <sha1>
        local crc32=$(echo "$hash_output" | awk '{print $1}')
        local md5=$(echo "$hash_output" | awk '{print $2}')
        local sha1=$(echo "$hash_output" | awk '{print $3}')
        
        # Validate hashes
        if [[ -z "$crc32" || -z "$md5" || -z "$sha1" ]]; then
            echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: Invalid hash output for: $inner_file from $archive_path - Output: $hash_output" >> "$ERROR_LOG"
            ((error_count++))
            rm -f "$extracted_file"
            continue
        fi
        
        # Store in database
        if [[ $DRY_RUN -eq 0 ]]; then
            local sql_cache_key="${cache_key//\'/\'\'}"
            sqlite3 "$DB_PATH" "INSERT OR REPLACE INTO hash_cache (file_path, file_size, mtime, crc32, md5, sha1, calculation_time, created_at) VALUES ('$sql_cache_key', $inner_size, $inner_mtime, '$crc32', '$md5', '$sha1', $calc_time, datetime('now'));" 2>/dev/null || {
                echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: Database insert failed for: $inner_file" >> "$ERROR_LOG"
                ((error_count++))
            }
        fi
        
        echo "[$(date +'%Y-%m-%d %H:%M:%S')]   DONE: $inner_file (${calc_time}s) - CRC32: $crc32, MD5: $md5" >> "$PROGRESS_FILE"
        ((success_count++))
        
        # Clean up extracted file
        rm -f "$extracted_file"
        
    done <<< "$file_list"
    
    # Clean up temp directory
    rm -rf "$temp_extract"
    
    # Report archive results
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] COMPLETE: $archive_path - Success: $success_count, Skip: $skip_count, Error: $error_count" >> "$PROGRESS_FILE"
    
    if [[ $error_count -gt 0 ]]; then
        echo "ERROR"
    elif [[ $success_count -eq 0 && $skip_count -eq 0 ]]; then
        echo "SKIP"
    else
        echo "SUCCESS"
    fi
}

export -f calculate_archive_hashes
export DB_PATH PROGRESS_FILE ERROR_LOG DRY_RUN RESUME TEMP_DIR

# Process files in parallel
process_files() {
    local file_list="$1"
    local total_files=$(wc -l < "$file_list")
    
    log "Found $total_files archive files to process"
    log "Using $JOBS parallel jobs"
    
    if [[ $DRY_RUN -eq 1 ]]; then
        log "DRY RUN MODE - No database changes will be made"
    fi
    
    if [[ $RESUME -eq 1 ]]; then
        log "RESUME MODE - Skipping already cached files"
    fi
    
    log "Processing archives..."
    
    # Use GNU parallel with progress monitoring
    local success_count=0
    local skip_count=0
    local error_count=0
    
    # Process with parallel
    cat "$file_list" | parallel --colsep '\t' -j "$JOBS" --bar \
        calculate_archive_hashes {1} {2} {3} > "${LOG_DIR}/parallel_results_${TIMESTAMP}.txt"
    
    # Count results
    if [[ -f "${LOG_DIR}/parallel_results_${TIMESTAMP}.txt" ]]; then
        success_count=$(grep -c "^SUCCESS$" "${LOG_DIR}/parallel_results_${TIMESTAMP}.txt" || true)
        skip_count=$(grep -c "^SKIP$" "${LOG_DIR}/parallel_results_${TIMESTAMP}.txt" || true)
        error_count=$(grep -c "^ERROR$" "${LOG_DIR}/parallel_results_${TIMESTAMP}.txt" || true)
    fi
    
    log "Processing complete!"
    log "  Success: $success_count"
    log "  Skipped: $skip_count"
    log "  Errors:  $error_count"
    log "  Total:   $total_files"
    
    # Write stats JSON
    cat > "$STATS_FILE" <<JSON
{
  "timestamp": "$(date -Iseconds)",
  "source_dir": "$SOURCE_DIR",
  "total_archives": $total_files,
  "success_count": $success_count,
  "skip_count": $skip_count,
  "error_count": $error_count,
  "parallel_jobs": $JOBS,
  "dry_run": $DRY_RUN,
  "resume_mode": $RESUME
}
JSON
}

# Generate summary report
generate_report() {
    log ""
    log "=== Hash Pre-calculation Summary ==="
    log ""
    log "Logs:"
    log "  Main log:     $LOG_FILE"
    log "  Error log:    $ERROR_LOG"
    log "  Progress log: $PROGRESS_FILE"
    log "  Stats JSON:   $STATS_FILE"
    log ""
    
    # Database statistics
    local total_cached=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM hash_cache;")
    local total_size=$(sqlite3 "$DB_PATH" "SELECT SUM(file_size) FROM hash_cache;")
    local size_gb=$(echo "scale=2; $total_size / 1024 / 1024 / 1024" | bc)
    
    log "Database Statistics:"
    log "  Total cached files: $total_cached"
    log "  Total size: ${size_gb} GB"
    log ""
    
    # Show recent errors if any
    if [[ -s "$ERROR_LOG" ]]; then
        log "⚠️  Errors occurred during processing!"
        log "   See: $ERROR_LOG"
        log ""
        log "Recent errors:"
        tail -10 "$ERROR_LOG" | while read line; do
            log "   $line"
        done
    else
        log "✓ No errors encountered"
    fi
    
    log ""
    log "Next steps:"
    log "  1. Review logs for any issues"
    log "  2. Run transformation scripts using cached hashes"
    log "  3. Query ScreenScraper with pre-calculated hashes"
    log ""
}

# Main execution
main() {
    log "========================================"
    log "ROM Hash Pre-calculation (Parallel)"
    log "========================================"
    log "Source: $SOURCE_DIR"
    log "Database: $DB_PATH"
    log "Jobs: $JOBS"
    log "Timestamp: $TIMESTAMP"
    log ""
    
    # Check dependencies
    check_dependencies
    
    # Find files
    local file_list="${LOG_DIR}/file_list_${TIMESTAMP}.txt"
    find_files > "$file_list"
    
    # Process files
    process_files "$file_list"
    
    # Generate report
    generate_report
    
    log "Complete! You can monitor progress with:"
    log "  tail -f $PROGRESS_FILE"
}

# Run main
main
