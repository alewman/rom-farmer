#!/bin/bash

# Master build script for all tools
# This is a convenience wrapper

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              ROM Groomer Tools Build Manager                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

show_menu() {
    echo "Available tools:"
    echo ""
    echo "  1) MAME (chdman) - CHD file management"
    echo "  2) All tools"
    echo "  q) Quit"
    echo ""
}

build_mame() {
    echo "Building MAME/chdman..."
    cd "$SCRIPT_DIR/mame"
    
    if [ ! -d src ]; then
        echo "Source not found, cloning first..."
        ./clone.sh
    fi
    
    ./build.sh
}

while true; do
    show_menu
    read -p "Select tool to build: " choice
    
    case $choice in
        1)
            build_mame
            ;;
        2)
            build_mame
            # Add other tools here as we create them
            ;;
        q|Q)
            echo "Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid choice"
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
    clear
done
