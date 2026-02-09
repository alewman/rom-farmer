#!/bin/bash
# Build pkg2zip from source

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="${SCRIPT_DIR}/src"
BIN_DIR="${SCRIPT_DIR}/../bin"

echo "=== Building pkg2zip ==="

if [ ! -d "$SRC_DIR" ]; then
    echo "Error: Source directory not found: $SRC_DIR"
    echo "Run ./clone.sh first"
    exit 1
fi

cd "$SRC_DIR"

echo "Building pkg2zip..."
make clean 2>/dev/null || true
make -j$(nproc)

# Create bin directory if needed
mkdir -p "$BIN_DIR"

# Create symlink in tools/bin
echo "Installing to: $BIN_DIR/pkg2zip"
ln -sf "$SRC_DIR/pkg2zip" "$BIN_DIR/pkg2zip"

echo ""
echo "✓ Build complete!"
echo ""
echo "Binary: $BIN_DIR/pkg2zip"
echo ""
echo "Test it:"
echo "  $BIN_DIR/pkg2zip --help"
