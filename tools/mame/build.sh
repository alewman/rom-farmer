#!/bin/bash
set -e

# Build chdman from MAME source
# This builds ONLY the chdman tool, not full MAME emulator

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAME_DIR="$SCRIPT_DIR/src"
BUILD_DIR="$SCRIPT_DIR/build"
BIN_DIR="$SCRIPT_DIR/../bin"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    Build MAME chdman Tool                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if source exists
if [ ! -d "$MAME_DIR" ]; then
    echo "❌ MAME source not found!"
    echo "   Please run ./clone.sh first to download the source."
    exit 1
fi

cd "$MAME_DIR"

# Show version info
if [ -f "$SCRIPT_DIR/VERSION.txt" ]; then
    echo "📝 Building from:"
    grep -E "^(Short|Tag|Date):" "$SCRIPT_DIR/VERSION.txt" | sed 's/^/   /'
    echo ""
fi

# Check dependencies
echo "🔍 Checking build dependencies..."
echo ""

MISSING_DEPS=()

if ! command -v g++ &> /dev/null; then
    MISSING_DEPS+=("g++")
fi

if ! command -v make &> /dev/null; then
    MISSING_DEPS+=("make")
fi

if ! command -v python3 &> /dev/null; then
    MISSING_DEPS+=("python3")
fi

if ! pkg-config --exists sdl2 2>/dev/null; then
    MISSING_DEPS+=("libsdl2-dev")
fi

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo "⚠️  Missing dependencies: ${MISSING_DEPS[*]}"
    echo ""
    echo "Install with:"
    echo "  sudo apt-get install build-essential git python3 libsdl2-dev libsdl2-ttf-dev libfontconfig-dev"
    echo ""
    read -p "🤔 Try to continue anyway? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Detect CPU cores for parallel build
CORES=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
echo "🚀 Building with $CORES parallel jobs"
echo ""

# Build options
echo "🔧 Build configuration:"
echo "   Target: chdman only (TOOLS=1)"
echo "   Optimization: -O3 (maximum)"
echo "   Native CPU: yes (march=native)"
echo "   Debug symbols: no"
echo ""

# Ask about optimization
read -p "🤔 Use CPU-specific optimizations? (recommended, Y/n) " -n 1 -r
echo ""
USE_NATIVE="yes"
if [[ $REPLY =~ ^[Nn]$ ]]; then
    USE_NATIVE="no"
fi

# Clean old build (optional)
if [ -f "chdman" ] || [ -d "build" ]; then
    echo ""
    read -p "🧹 Clean previous build? (Y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        echo "🧹 Cleaning previous build..."
        make clean 2>/dev/null || true
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔨 Starting build..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⏱️  This will take 5-15 minutes depending on your CPU..."
echo ""

START_TIME=$(date +%s)

# Build command
BUILD_OPTS="TOOLS=1 OPTIMIZE=3 -j$CORES"
if [ "$USE_NATIVE" = "yes" ]; then
    BUILD_OPTS="$BUILD_OPTS ARCHOPTS=-march=native"
fi

echo "📝 Build command: make $BUILD_OPTS"
echo ""

# Run the build
if make $BUILD_OPTS; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ Build completed successfully in ${DURATION}s!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Find the built binary
    CHDMAN_BIN=""
    if [ -f "chdman" ]; then
        CHDMAN_BIN="$MAME_DIR/chdman"
    elif [ -f "build/chdman" ]; then
        CHDMAN_BIN="$MAME_DIR/build/chdman"
    elif [ -f "chdman64" ]; then
        CHDMAN_BIN="$MAME_DIR/chdman64"
    else
        echo "⚠️  Could not find built chdman binary!"
        echo "   Searching for it..."
        find . -name "chdman*" -type f 2>/dev/null
        exit 1
    fi
    
    # Create build directory and copy binary
    mkdir -p "$BUILD_DIR"
    cp "$CHDMAN_BIN" "$BUILD_DIR/chdman"
    chmod +x "$BUILD_DIR/chdman"
    
    echo "📦 Binary copied to: $BUILD_DIR/chdman"
    
    # Create symlink in bin directory
    mkdir -p "$BIN_DIR"
    ln -sf "../mame/build/chdman" "$BIN_DIR/chdman"
    
    echo "🔗 Symlink created: $BIN_DIR/chdman"
    echo ""
    
    # Test the binary
    echo "🧪 Testing built binary..."
    "$BUILD_DIR/chdman" --version || true
    echo ""
    
    # Record build info
    BUILD_INFO="$BUILD_DIR/BUILD_INFO.txt"
    cat > "$BUILD_INFO" << EOF
chdman Build Information
Built: $(date)
Build time: ${DURATION}s

Source:
$(grep -E "^(Commit|Short|Tag|Date):" "$SCRIPT_DIR/VERSION.txt" 2>/dev/null || echo "  No version info")

Build options:
  Command: make $BUILD_OPTS
  Cores: $CORES
  Native optimizations: $USE_NATIVE

Binary:
  Path: $BUILD_DIR/chdman
  Size: $(du -h "$BUILD_DIR/chdman" | cut -f1)
  
Test:
$("$BUILD_DIR/chdman" --version 2>&1 || echo "  Version test failed")
EOF
    
    cat "$BUILD_INFO"
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ All done!"
    echo ""
    echo "Usage:"
    echo "  $BIN_DIR/chdman --help"
    echo ""
    echo "Or add to PATH:"
    echo "  export PATH=\"$BIN_DIR:\$PATH\""
    echo "  chdman --help"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
else
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "❌ Build failed!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Common issues:"
    echo "  1. Missing dependencies - install build-essential, libsdl2-dev"
    echo "  2. Insufficient RAM - try reducing parallel jobs (-j$CORES)"
    echo "  3. Disk space - MAME builds need ~2GB free space"
    echo ""
    echo "Try:"
    echo "  sudo apt-get install build-essential git python3 libsdl2-dev"
    echo "  make clean"
    echo "  ./build.sh"
    exit 1
fi
