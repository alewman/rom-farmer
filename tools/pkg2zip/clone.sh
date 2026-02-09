#!/bin/bash
# Clone pkg2zip source repository

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="${SCRIPT_DIR}/src"

echo "=== Cloning pkg2zip ==="

if [ -d "$SRC_DIR" ]; then
    echo "Source directory already exists: $SRC_DIR"
    echo "To update, run: cd $SRC_DIR && git pull"
    exit 0
fi

echo "Cloning from: https://github.com/lusid1/pkg2zip.git"
git clone https://github.com/lusid1/pkg2zip.git "$SRC_DIR"

echo ""
echo "✓ Clone complete!"
echo ""
echo "Next steps:"
echo "  ./build.sh    # Build pkg2zip"
