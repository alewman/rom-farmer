#!/bin/bash
# Test hash calculation for a single ZIP archive

set -euo pipefail

SOURCE_DIR="/path/to/source/myrient/files"
DB_PATH="/path/to/..."
TEMP_DIR="/path/to/..."

# Pick a test archive
TEST_ARCHIVE="/path/to/source/No-Intro/Nintendo - Game Boy/SolarStriker (World).zip"

echo "Testing hash calculation for:"
echo "  $TEST_ARCHIVE"
echo ""

# Create temp directory
mkdir -p "$TEMP_DIR/test"

# List contents
echo "Archive contents:"
unzip -l "$TEST_ARCHIVE"
echo ""

# Extract
echo "Extracting..."
unzip -j -o "$TEST_ARCHIVE" -d "$TEMP_DIR/test"
echo ""

# Calculate hash
echo "Calculating hashes..."
for file in "$TEMP_DIR/test"/*; do
    [[ -f "$file" ]] || continue
    echo "File: $file"
    rhash --simple --crc32 --md5 --sha1 "$file"
    echo ""
done

# Clean up
rm -rf "$TEMP_DIR/test"

echo "Test complete!"
