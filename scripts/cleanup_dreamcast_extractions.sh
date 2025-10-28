#!/bin/bash
################################################################################
# Script: cleanup_dreamcast_extractions.sh
# Description: Clean up extracted BIN/CUE files from Dreamcast directory,
#              keeping only the original ZIPs and ARRM metadata.
#
# This script removes the extracted disc files that were needed for ARRM
# scraping but are no longer required. The romgroomer pipeline will extract
# from the ZIPs as needed during the build process.
#
# Usage: ./cleanup_dreamcast_extractions.sh [--dry-run]
#
# Example:
#   # Preview what would be deleted
#   ./cleanup_dreamcast_extractions.sh --dry-run
#
#   # Actually delete files
#   ./cleanup_dreamcast_extractions.sh
################################################################################

set -euo pipefail

# Configuration
DREAMCAST_DIR="/data/emu/roms/dreamcast"
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run|-n)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Clean up extracted Dreamcast disc files, keeping ZIPs and metadata.

OPTIONS:
    --dry-run, -n    Show what would be deleted without actually deleting
    --help, -h       Show this help message

FILES DELETED:
    - *.cue (CUE sheet files)
    - *.bin (Binary disc images)
    - *.gdi (GD-ROM disc descriptors)

FILES KEPT:
    - *.zip (Original Redump archives)
    - gamelist*.xml (ARRM metadata)
    - media/ (Artwork and metadata)
EOF
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate directory exists
if [[ ! -d "$DREAMCAST_DIR" ]]; then
    echo "ERROR: Dreamcast directory not found: $DREAMCAST_DIR"
    exit 1
fi

# Count files
echo "Analyzing $DREAMCAST_DIR..."
cue_count=$(find "$DREAMCAST_DIR" -maxdepth 1 -type f -name "*.cue" | wc -l)
bin_count=$(find "$DREAMCAST_DIR" -maxdepth 1 -type f -name "*.bin" | wc -l)
gdi_count=$(find "$DREAMCAST_DIR" -maxdepth 1 -type f -name "*.gdi" | wc -l)
zip_count=$(find "$DREAMCAST_DIR" -maxdepth 1 -type f -name "*.zip" | wc -l)

total_to_delete=$((cue_count + bin_count + gdi_count))

echo ""
echo "Current state:"
echo "  CUE files: $cue_count"
echo "  BIN files: $bin_count"
echo "  GDI files: $gdi_count"
echo "  ZIP files: $zip_count (will be kept)"
echo ""

if [[ $total_to_delete -eq 0 ]]; then
    echo "No extracted disc files found. Directory is already clean!"
    exit 0
fi

# Calculate disk space
echo "Calculating disk space..."
if command -v du >/dev/null 2>&1; then
    cue_size=$(find "$DREAMCAST_DIR" -maxdepth 1 -type f -name "*.cue" -exec du -ch {} + 2>/dev/null | grep total$ | cut -f1 || echo "0")
    bin_size=$(find "$DREAMCAST_DIR" -maxdepth 1 -type f -name "*.bin" -exec du -ch {} + 2>/dev/null | grep total$ | cut -f1 || echo "0")
    gdi_size=$(find "$DREAMCAST_DIR" -maxdepth 1 -type f -name "*.gdi" -exec du -ch {} + 2>/dev/null | grep total$ | cut -f1 || echo "0")
    
    echo "  Disk space to reclaim:"
    [[ "$cue_size" != "0" ]] && echo "    CUE files: $cue_size"
    [[ "$bin_size" != "0" ]] && echo "    BIN files: $bin_size"
    [[ "$gdi_size" != "0" ]] && echo "    GDI files: $gdi_size"
    echo ""
fi

if [[ "$DRY_RUN" == true ]]; then
    echo "DRY RUN MODE - No files will be deleted"
    echo ""
    echo "Files that would be deleted:"
    find "$DREAMCAST_DIR" -maxdepth 1 -type f \( -name "*.cue" -o -name "*.bin" -o -name "*.gdi" \) | head -20
    
    if [[ $total_to_delete -gt 20 ]]; then
        echo "  ... and $((total_to_delete - 20)) more files"
    fi
    
    echo ""
    echo "To actually delete these files, run without --dry-run"
    exit 0
fi

# Confirm deletion
echo "WARNING: This will delete $total_to_delete extracted disc files."
echo "Original ZIP files and ARRM metadata will be preserved."
echo ""
read -p "Continue? (yes/no): " confirm

if [[ "$confirm" != "yes" ]]; then
    echo "Aborted."
    exit 0
fi

# Delete files
echo ""
echo "Deleting extracted disc files..."

deleted=0

# Delete CUE files
if [[ $cue_count -gt 0 ]]; then
    echo "  Deleting CUE files..."
    find "$DREAMCAST_DIR" -maxdepth 1 -type f -name "*.cue" -delete
    deleted=$((deleted + cue_count))
fi

# Delete BIN files
if [[ $bin_count -gt 0 ]]; then
    echo "  Deleting BIN files..."
    find "$DREAMCAST_DIR" -maxdepth 1 -type f -name "*.bin" -delete
    deleted=$((deleted + bin_count))
fi

# Delete GDI files
if [[ $gdi_count -gt 0 ]]; then
    echo "  Deleting GDI files..."
    find "$DREAMCAST_DIR" -maxdepth 1 -type f -name "*.gdi" -delete
    deleted=$((deleted + gdi_count))
fi

echo ""
echo "✓ Cleanup complete!"
echo "  Deleted: $deleted files"
echo "  Kept: $zip_count ZIP files + metadata"
echo ""
echo "The romgroomer pipeline will extract ZIPs as needed during builds."
