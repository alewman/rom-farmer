#!/bin/bash
# Download NoPayStation database files
# These databases are updated periodically by the community

set -e

DEST_DIR="/data/emu/source/nopaystation"
BASE_URL="https://nopaystation.com/tsv"

mkdir -p "$DEST_DIR"
cd "$DEST_DIR"

echo "Downloading NoPayStation databases..."
echo "======================================"

# PS3 databases
echo -e "\n📦 PS3 Databases:"
wget -N "${BASE_URL}/PS3_GAMES.tsv" && echo "  ✓ PS3_GAMES.tsv"
wget -N "${BASE_URL}/PS3_DLCS.tsv" && echo "  ✓ PS3_DLCS.tsv"
wget -N "${BASE_URL}/PS3_THEMES.tsv" && echo "  ✓ PS3_THEMES.tsv"
wget -N "${BASE_URL}/PS3_AVATARS.tsv" && echo "  ✓ PS3_AVATARS.tsv"
wget -N "${BASE_URL}/PS3_UPDATES.tsv" && echo "  ✓ PS3_UPDATES.tsv"

# PS Vita databases
echo -e "\n📱 PS Vita Databases:"
wget -N "${BASE_URL}/PSV_GAMES.tsv" && echo "  ✓ PSV_GAMES.tsv"
wget -N "${BASE_URL}/PSV_DLCS.tsv" && echo "  ✓ PSV_DLCS.tsv"
wget -N "${BASE_URL}/PSV_THEMES.tsv" && echo "  ✓ PSV_THEMES.tsv"
wget -N "${BASE_URL}/PSV_UPDATES.tsv" && echo "  ✓ PSV_UPDATES.tsv"

# PSP databases
echo -e "\n🎮 PSP Databases:"
wget -N "${BASE_URL}/PSP_GAMES.tsv" && echo "  ✓ PSP_GAMES.tsv"
wget -N "${BASE_URL}/PSP_DLCS.tsv" && echo "  ✓ PSP_DLCS.tsv"
wget -N "${BASE_URL}/PSP_THEMES.tsv" && echo "  ✓ PSP_THEMES.tsv"
wget -N "${BASE_URL}/PSP_UPDATES.tsv" && echo "  ✓ PSP_UPDATES.tsv"

# PSX (PS1) database
echo -e "\n🕹️  PSX (PS1) Database:"
wget -N "${BASE_URL}/PSX_GAMES.tsv" && echo "  ✓ PSX_GAMES.tsv"

echo -e "\n✅ All databases downloaded to: $DEST_DIR"
echo ""
echo "Database sizes:"
ls -lh *.tsv | awk '{print "  " $9 ": " $5}'

echo -e "\nEntry counts:"
for f in *.tsv; do
    count=$(($(wc -l < "$f") - 1))  # Subtract header line
    printf "  %-20s %6d entries\n" "$f:" "$count"
done
