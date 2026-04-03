#!/bin/bash
# Install Wii DLC WADs to Dolphin NAND (Batocera)
#
# This script installs WAD files from the nand/ subfolder into the
# Dolphin emulator's NAND storage, making DLC available in-game.
#
# Usage: Run from the wii-extras output directory
#   cd /userdata/roms/wii/wii-extras
#   ./install.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WAD_DIR="${SCRIPT_DIR}/nand"

# Batocera Dolphin NAND path
NAND_DIR="/userdata/saves/dolphin-emu/Wii"

if [[ ! -d "$WAD_DIR" ]]; then
    echo "ERROR: nand/ directory not found at ${WAD_DIR}"
    exit 1
fi

WAD_COUNT=$(find "$WAD_DIR" -maxdepth 1 -name '*.wad' | wc -l)

if [[ "$WAD_COUNT" -eq 0 ]]; then
    echo "No WAD files found in ${WAD_DIR}"
    exit 0
fi

echo "Installing ${WAD_COUNT} WAD files to Dolphin NAND..."
echo "NAND directory: ${NAND_DIR}"
echo

INSTALLED=0
FAILED=0

for wad in "${WAD_DIR}"/*.wad; do
    name="$(basename "$wad")"
    echo "  Installing: ${name} ..."

    # Try dolphin-tool first
    if command -v dolphin-tool &>/dev/null; then
        if dolphin-tool install --nand="$NAND_DIR" "$wad" &>/dev/null; then
            echo "    OK"
            ((INSTALLED++))
            continue
        fi
    fi

    # Fallback: direct copy
    mkdir -p "$NAND_DIR"
    if cp "$wad" "${NAND_DIR}/${name}"; then
        echo "    OK (copied)"
        ((INSTALLED++))
    else
        echo "    FAILED"
        ((FAILED++))
    fi
done

echo
echo "Done: ${INSTALLED} installed, ${FAILED} failed (out of ${WAD_COUNT})"
