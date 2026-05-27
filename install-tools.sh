#!/usr/bin/env bash
# =============================================================================
# ROM Farmer — Tool Installer
# =============================================================================
#
# Downloads and builds the external tools used by ROM Farmer for disc
# compression, format conversion, and PKG handling.
#
# Usage:
#   ./install-tools.sh           # Install all tools
#   ./install-tools.sh --check   # Check what's already installed
#   ./install-tools.sh chdman dolphin-tool xdvdfs   # Install specific tools
#
# Requirements (Debian/Ubuntu):
#   sudo apt install build-essential cmake git python3 python3-pip cargo \
#                    libevdev-dev libpugixml-dev libminizip-dev nasm
#
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS_DIR="$SCRIPT_DIR/tools"
BIN_DIR="$TOOLS_DIR/bin"

# Colour helpers
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()   { echo -e "${GREEN}  ✓ $*${NC}"; }
warn() { echo -e "${YELLOW}  ⚠ $*${NC}"; }
fail() { echo -e "${RED}  ✗ $*${NC}"; }
hdr()  { echo ""; echo "── $* ──"; }

# =============================================================================
# Tool definitions
# =============================================================================

ALL_TOOLS=(chdman dolphin-tool extract-xiso maxcso nsz xdvdfs wit pkg2zip ps3dec wud-compress)

check_tool() {
    local name=$1
    local bin="$BIN_DIR/$name"
    if [ -f "$bin" ] && [ -x "$bin" ]; then
        echo -e "  ${GREEN}✓${NC} $name"
        return 0
    elif [ -L "$bin" ] && [ -e "$bin" ]; then
        echo -e "  ${GREEN}✓${NC} $name (symlink)"
        return 0
    else
        echo -e "  ${RED}✗${NC} $name (not found)"
        return 1
    fi
}

cmd_check() {
    hdr "Tool Status"
    local missing=0
    for tool in "${ALL_TOOLS[@]}"; do
        check_tool "$tool" || ((missing++))
    done
    echo ""
    if [ "$missing" -eq 0 ]; then
        ok "All tools installed"
    else
        warn "$missing tool(s) not installed. Run ./install-tools.sh to install."
    fi
}

# =============================================================================
# Individual tool installers
# =============================================================================

install_chdman() {
    hdr "chdman (CHD compression — part of MAME)"
    if [ -L "$BIN_DIR/chdman" ] && [ -e "$BIN_DIR/chdman" ]; then
        ok "already installed"; return 0
    fi
    echo "  Building from source (this takes 10-30 min)..."
    cd "$TOOLS_DIR/mame"
    [ ! -d src ] && ./clone.sh
    ./build.sh
    ok "chdman installed"
}

install_dolphin_tool() {
    hdr "dolphin-tool (RVZ/WBFS compression — part of Dolphin)"
    if [ -L "$BIN_DIR/dolphin-tool" ] && [ -e "$BIN_DIR/dolphin-tool" ]; then
        ok "already installed"; return 0
    fi
    echo "  Building from source (requires cmake, ~5 min)..."
    cd "$TOOLS_DIR/dolphin-tool"
    [ ! -d src ] && ./clone.sh
    ./build.sh
    ok "dolphin-tool installed"
}

install_extract_xiso() {
    hdr "extract-xiso (Xbox ISO extraction)"
    if [ -L "$BIN_DIR/extract-xiso" ] && [ -e "$BIN_DIR/extract-xiso" ]; then
        ok "already installed"; return 0
    fi
    cd "$TOOLS_DIR/extract-xiso"
    [ ! -d src ] && ./clone.sh
    ./build.sh
    ok "extract-xiso installed"
}

install_maxcso() {
    hdr "maxcso (PSP CSO compression)"
    if [ -L "$BIN_DIR/maxcso" ] && [ -e "$BIN_DIR/maxcso" ]; then
        ok "already installed"; return 0
    fi
    cd "$TOOLS_DIR/maxcso"
    [ ! -d src ] && ./clone.sh
    ./build.sh
    ok "maxcso installed"
}

install_nsz() {
    hdr "nsz (Nintendo Switch NSZ compression)"
    if command -v nsz &>/dev/null; then
        # Create symlink in our bin dir
        ln -sf "$(command -v nsz)" "$BIN_DIR/nsz" 2>/dev/null || true
        ok "already installed (system nsz)"; return 0
    fi
    echo "  Installing via pip..."
    pip install nsz --quiet
    # Create symlink
    NSZ_BIN=$(command -v nsz 2>/dev/null || python3 -c "import sysconfig; print(sysconfig.get_path('scripts'))")/nsz
    ln -sf "$NSZ_BIN" "$BIN_DIR/nsz"
    ok "nsz installed"
}

install_xdvdfs() {
    hdr "xdvdfs / xdvdfsd (Xbox 360 XDVDFS tools)"
    if [ -L "$BIN_DIR/xdvdfs" ] && [ -e "$BIN_DIR/xdvdfs" ]; then
        ok "already installed"; return 0
    fi
    cd "$TOOLS_DIR/xdvdfs-tools"
    [ ! -d src ] && ./clone.sh
    ./build.sh
    ok "xdvdfs installed"
}

install_wit() {
    hdr "wit / wwt / wdf (Wiimms ISO Tools — Wii/GC)"
    if [ -L "$BIN_DIR/wit" ] && [ -e "$BIN_DIR/wit" ]; then
        ok "already installed"; return 0
    fi
    cd "$TOOLS_DIR/wit"
    [ ! -d src ] && ./clone.sh
    ./build.sh
    ok "wit installed"
}

install_pkg2zip() {
    hdr "pkg2zip (PS3/PSP PKG extraction)"
    if [ -L "$BIN_DIR/pkg2zip" ] && [ -e "$BIN_DIR/pkg2zip" ]; then
        ok "already installed"; return 0
    fi
    cd "$TOOLS_DIR/pkg2zip"
    [ ! -d src ] && ./clone.sh
    ./build.sh
    ok "pkg2zip installed"
}

install_ps3dec() {
    hdr "PS3Dec (PS3 disc decryption)"
    if [ -L "$BIN_DIR/ps3dec" ] && [ -e "$BIN_DIR/ps3dec" ]; then
        ok "already installed"; return 0
    fi
    # ps3dec must be built from source; no public release binaries.
    # Source: https://github.com/Redrrx/PS3Dec  (C++ reimplementation)
    local src="$TOOLS_DIR/ps3dec/src"
    local bin_out="$TOOLS_DIR/ps3dec/build/PS3Dec"
    mkdir -p "$(dirname "$src")"
    if [ ! -d "$src" ]; then
        echo "  Cloning PS3Dec..."
        git clone --depth 1 https://github.com/Redrrx/PS3Dec.git "$src"
    fi
    echo "  Building PS3Dec..."
    mkdir -p "$TOOLS_DIR/ps3dec/build"
    cmake -S "$src" -B "$TOOLS_DIR/ps3dec/build" -DCMAKE_BUILD_TYPE=Release -Wno-dev
    cmake --build "$TOOLS_DIR/ps3dec/build" --config Release -j"$(nproc)"
    if [ -f "$bin_out" ]; then
        ln -sf "$bin_out" "$BIN_DIR/ps3dec"
        ok "ps3dec installed"
    else
        fail "ps3dec build failed — check output above"
    fi
}

install_wud_compress() {
    hdr "wud-compress (Wii U WUD compression)"
    if [ -L "$BIN_DIR/wud-compress" ] && [ -e "$BIN_DIR/wud-compress" ]; then
        ok "already installed"; return 0
    fi
    cd "$TOOLS_DIR/wud-compress"
    [ ! -d src ] && ./clone.sh
    ./build.sh
    ok "wud-compress installed"
}

dispatch() {
    case "$1" in
        chdman)          install_chdman ;;
        dolphin-tool)    install_dolphin_tool ;;
        extract-xiso)    install_extract_xiso ;;
        maxcso)          install_maxcso ;;
        nsz)             install_nsz ;;
        xdvdfs)          install_xdvdfs ;;
        wit)             install_wit ;;
        pkg2zip)         install_pkg2zip ;;
        ps3dec)          install_ps3dec ;;
        wud-compress)    install_wud_compress ;;
        *)               fail "Unknown tool: $1"; exit 1 ;;
    esac
}

# =============================================================================
# Main
# =============================================================================

mkdir -p "$BIN_DIR"

if [ "${1:-}" = "--check" ]; then
    cmd_check
    exit 0
fi

if [ $# -gt 0 ]; then
    # Install only requested tools
    for t in "$@"; do dispatch "$t"; done
else
    # Install all
    echo "Installing all ROM Farmer tools..."
    echo "(You can also run: ./install-tools.sh <tool> to install individually)"
    for t in "${ALL_TOOLS[@]}"; do dispatch "$t"; done
fi

echo ""
ok "Done. Run './tools/verify-tools.sh' to verify all tools."
