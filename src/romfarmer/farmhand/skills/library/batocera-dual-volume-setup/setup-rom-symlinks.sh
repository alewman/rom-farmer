#!/bin/bash
# setup-rom-symlinks.sh — Create symlinks for multi-volume Batocera ROM storage
#
# Usage: ./setup-rom-symlinks.sh <secondary_mount> <platform1> [platform2] ...
# Example: ./setup-rom-symlinks.sh /media/int2tbhd ps2 psx dreamcast saturn
#
# This script:
#   1. Creates /roms/<platform> on the secondary volume
#   2. Moves existing files from /userdata/roms/<platform> to secondary
#   3. Creates symlinks: /userdata/roms/<platform> → <secondary>/roms/<platform>
#
# Idempotent: safe to run multiple times.

set -euo pipefail

SECONDARY="${1:?Usage: $0 <secondary_mount> <platform1> [platform2] ...}"
shift
PLATFORMS=("$@")

if [ ${#PLATFORMS[@]} -eq 0 ]; then
    echo "Error: specify at least one platform"
    exit 1
fi

# Verify secondary is mounted
if ! mountpoint -q "$SECONDARY" 2>/dev/null; then
    echo "Error: $SECONDARY is not a mounted filesystem"
    exit 1
fi

echo "=== Batocera Dual-Volume ROM Symlink Setup ==="
echo "Secondary volume: $SECONDARY"
echo "Platforms: ${PLATFORMS[*]}"
echo ""

for PLATFORM in "${PLATFORMS[@]}"; do
    USERDATA_PATH="/userdata/roms/$PLATFORM"
    SECONDARY_PATH="$SECONDARY/roms/$PLATFORM"

    echo "--- $PLATFORM ---"

    # Already a symlink pointing to the right place?
    if [ -L "$USERDATA_PATH" ]; then
        TARGET=$(readlink -f "$USERDATA_PATH")
        if [ "$TARGET" = "$(realpath "$SECONDARY_PATH" 2>/dev/null)" ]; then
            echo "  ✓ Symlink already correct: $USERDATA_PATH → $SECONDARY_PATH"
            continue
        else
            echo "  ! Symlink exists but points to $TARGET — fixing"
            rm "$USERDATA_PATH"
        fi
    fi

    # Create target directory on secondary
    mkdir -p "$SECONDARY_PATH"

    # Move existing files if /userdata/roms/<platform> is a real directory
    if [ -d "$USERDATA_PATH" ] && [ ! -L "$USERDATA_PATH" ]; then
        FILE_COUNT=$(find "$USERDATA_PATH" -maxdepth 1 -type f | wc -l)
        if [ "$FILE_COUNT" -gt 0 ]; then
            echo "  Moving $FILE_COUNT files from $USERDATA_PATH to $SECONDARY_PATH"
            mv "$USERDATA_PATH"/* "$SECONDARY_PATH/" 2>/dev/null || true
        fi
        rmdir "$USERDATA_PATH" 2>/dev/null || rm -rf "$USERDATA_PATH"
    fi

    # Create the symlink
    ln -sfn "$SECONDARY_PATH" "$USERDATA_PATH"
    echo "  ✓ Created: $USERDATA_PATH → $SECONDARY_PATH"
done

echo ""
echo "=== Done. Verify with: ls -la /userdata/roms/ | grep '^l' ==="
