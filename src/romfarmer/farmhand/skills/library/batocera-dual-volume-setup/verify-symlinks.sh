#!/bin/bash
# verify-symlinks.sh — Check that all ROM symlinks are valid
#
# Usage: ./verify-symlinks.sh
# Checks /userdata/roms/ for symlinks and verifies their targets exist.

set -euo pipefail

echo "=== ROM Symlink Verification ==="
ERRORS=0
CHECKED=0

for LINK in /userdata/roms/*/; do
    LINK="${LINK%/}"  # Remove trailing slash
    BASENAME=$(basename "$LINK")

    if [ -L "$LINK" ]; then
        CHECKED=$((CHECKED + 1))
        TARGET=$(readlink -f "$LINK")
        if [ -d "$TARGET" ]; then
            COUNT=$(find "$TARGET" -maxdepth 1 -type f | wc -l)
            echo "  ✓ $BASENAME → $TARGET ($COUNT files)"
        else
            echo "  ✗ $BASENAME → $TARGET (BROKEN — target missing!)"
            ERRORS=$((ERRORS + 1))
        fi
    fi
done

echo ""
echo "Checked $CHECKED symlinks, $ERRORS broken"
[ "$ERRORS" -eq 0 ] && echo "All symlinks OK" || echo "WARNING: Fix broken symlinks!"
exit $ERRORS
