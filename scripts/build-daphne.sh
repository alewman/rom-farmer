#!/bin/bash
#===============================================================================
# ROM Farmer - DAPHNE/Laserdisc Build Script
#===============================================================================
# Converts Myrient's Hypseus Singe [Daphne] folder structure to Batocera format
#
# Myrient Structure:
#   Hypseus Singe [Daphne]/
#   ├── roms/           # Arcade ROM files (.zip)
#   ├── vldp/           # Video files for standard games
#   ├── vldp_dp/        # Video files for Don Bluth dual-play games
#   ├── sound/          # Sound samples
#   ├── fonts/          # Fonts
#   └── bezels/         # Bezels
#
# Batocera Structure:
#   /userdata/roms/daphne/
#   ├── roms/           # Arcade ROM files (.zip)
#   ├── gamename.daphne/
#   │   ├── gamename.dat
#   │   ├── gamename.m2v
#   │   └── gamename.ogg
#   ├── sound/
#   ├── fonts/
#   └── bezels/
#
# Usage: ./build-daphne.sh
#===============================================================================

set -e

# Configuration
SOURCE_DIR="/data/emu/source/myrient.erista.me/files/Laserdisc Collection/Hypseus Singe [Daphne]"
OUTPUT_DIR="/data/emu/rom-farmer/output/laserdisc-batocera/daphne"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=============================================="
echo "DAPHNE/Laserdisc Build Script"
echo "==============================================${NC}"

# Check source exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "${RED}ERROR: Source directory not found: $SOURCE_DIR${NC}"
    echo "Please run the Myrient sync first:"
    echo "  ./tools/rclone-myrient.sh arcade"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo -e "${YELLOW}Source: $SOURCE_DIR${NC}"
echo -e "${YELLOW}Output: $OUTPUT_DIR${NC}"
echo ""

#-------------------------------------------------------------------------------
# Copy supporting files
#-------------------------------------------------------------------------------
echo -e "${BLUE}--- Copying support files ---${NC}"

# ROMs (required arcade ROM files)
if [ -d "$SOURCE_DIR/roms" ]; then
    echo "Copying roms/..."
    mkdir -p "$OUTPUT_DIR/roms"
    rsync -av --progress "$SOURCE_DIR/roms/" "$OUTPUT_DIR/roms/"
fi

# Sound samples
if [ -d "$SOURCE_DIR/sound" ]; then
    echo "Copying sound/..."
    mkdir -p "$OUTPUT_DIR/sound"
    rsync -av --progress "$SOURCE_DIR/sound/" "$OUTPUT_DIR/sound/"
fi

# Fonts
if [ -d "$SOURCE_DIR/fonts" ]; then
    echo "Copying fonts/..."
    mkdir -p "$OUTPUT_DIR/fonts"
    rsync -av --progress "$SOURCE_DIR/fonts/" "$OUTPUT_DIR/fonts/"
fi

# Bezels
if [ -d "$SOURCE_DIR/bezels" ]; then
    echo "Copying bezels/..."
    mkdir -p "$OUTPUT_DIR/bezels"
    rsync -av --progress "$SOURCE_DIR/bezels/" "$OUTPUT_DIR/bezels/"
fi

#-------------------------------------------------------------------------------
# Build .daphne game folders from vldp/ (standard games)
#-------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}--- Building DAPHNE game folders from vldp/ ---${NC}"

if [ -d "$SOURCE_DIR/vldp" ]; then
    for gamedir in "$SOURCE_DIR/vldp"/*/; do
        if [ -d "$gamedir" ]; then
            gamename=$(basename "$gamedir")
            # Skip README files
            if [[ "$gamename" == *"README"* ]]; then
                continue
            fi
            
            target="$OUTPUT_DIR/${gamename}.daphne"
            echo -e "  ${GREEN}→ ${gamename}.daphne${NC}"
            mkdir -p "$target"
            rsync -av --quiet "$gamedir" "$target/"
        fi
    done
fi

#-------------------------------------------------------------------------------
# Build .daphne game folders from vldp_dp/ (Don Bluth dual-play games)
#-------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}--- Building DAPHNE game folders from vldp_dp/ ---${NC}"

if [ -d "$SOURCE_DIR/vldp_dp" ]; then
    for gamedir in "$SOURCE_DIR/vldp_dp"/*/; do
        if [ -d "$gamedir" ]; then
            gamename=$(basename "$gamedir")
            # Skip README files and CHD variants (we use regular versions)
            if [[ "$gamename" == *"README"* ]] || [[ "$gamename" == *"_chd"* ]]; then
                continue
            fi
            
            target="$OUTPUT_DIR/${gamename}.daphne"
            echo -e "  ${GREEN}→ ${gamename}.daphne${NC}"
            mkdir -p "$target"
            rsync -av --quiet "$gamedir" "$target/"
        fi
    done
fi

#-------------------------------------------------------------------------------
# Generate gamelist for reference
#-------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}--- Generating game list ---${NC}"

game_count=0
total_size=0

{
    echo "DAPHNE Laserdisc Game Collection"
    echo "================================="
    echo "Generated: $(date)"
    echo ""
    echo "Games:"
    echo "------"
    
    for daphne_dir in "$OUTPUT_DIR"/*.daphne; do
        if [ -d "$daphne_dir" ]; then
            gamename=$(basename "$daphne_dir" .daphne)
            size=$(du -sh "$daphne_dir" 2>/dev/null | cut -f1)
            echo "  $gamename - $size"
            ((game_count++))
        fi
    done
    
    echo ""
    echo "Total games: $game_count"
    echo "Total size: $(du -sh "$OUTPUT_DIR" 2>/dev/null | cut -f1)"
    
} > "$OUTPUT_DIR/gamelist.txt"

echo ""
echo -e "${GREEN}=============================================="
echo "Build Complete!"
echo "==============================================${NC}"
echo ""
echo "Games built: $game_count"
echo "Output directory: $OUTPUT_DIR"
echo "Total size: $(du -sh "$OUTPUT_DIR" 2>/dev/null | cut -f1)"
echo ""
echo "Game list saved to: $OUTPUT_DIR/gamelist.txt"
echo ""
echo -e "${YELLOW}To deploy to Batocera:${NC}"
echo "  Copy contents of $OUTPUT_DIR to /userdata/roms/daphne/"
echo ""
