#!/bin/bash
# Tool Installation Verification Script
# Tests all installed ROM compression tools

echo "ROM Groomer - Tool Verification"
echo "================================"
echo ""

TOOLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$TOOLS_DIR/bin"

PASSED=0
FAILED=0

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_tool() {
    local name=$1
    local path=$2
    local test_cmd=$3
    
    echo -n "Testing $name... "
    
    if [ ! -f "$path" ] && [ ! -L "$path" ]; then
        echo -e "${RED}✗ NOT FOUND${NC}"
        echo "  Location: $path"
        ((FAILED++))
        return 1
    fi
    
    if [ -n "$test_cmd" ]; then
        if eval "$test_cmd" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ OK${NC}"
            ((PASSED++))
            return 0
        else
            echo -e "${RED}✗ FAILED${NC}"
            echo "  Command: $test_cmd"
            ((FAILED++))
            return 1
        fi
    else
        echo -e "${GREEN}✓ EXISTS${NC}"
        ((PASSED++))
        return 0
    fi
}

echo "Checking Disc Compression Tools:"
echo "---------------------------------"

# 1. Saturn - chdman
check_tool "chdman (Saturn)" "$BIN_DIR/chdman" "$BIN_DIR/chdman 2>&1 | grep -q MAME"

# 2. PSP - maxcso
check_tool "maxcso (PSP)" "$BIN_DIR/maxcso" "$BIN_DIR/maxcso 2>&1 | grep -q maxcso"

# 3. Xbox - extract-xiso
check_tool "extract-xiso (Xbox)" "$BIN_DIR/extract-xiso" "$BIN_DIR/extract-xiso 2>&1 | grep -q 'extract-xiso'"

# 4. Xbox 360 - xdvdfs
check_tool "xdvdfs (Xbox 360)" "$BIN_DIR/xdvdfs" "$BIN_DIR/xdvdfs --help"

# 5. PS3 - ps3dec
check_tool "ps3dec (PS3)" "$BIN_DIR/ps3dec" "test -x $BIN_DIR/ps3dec"

# 6. Wii U - wud-compress
check_tool "wud-compress (Wii U)" "$BIN_DIR/wud-compress" "$BIN_DIR/wud-compress 2>&1 | grep -q Usage"

# 7. Wii/GC - wit
check_tool "wit (Wii/GC WBFS)" "$BIN_DIR/wit" "$BIN_DIR/wit --version"

# 8. Wii/GC - dolphin-tool
check_tool "dolphin-tool (Wii/GC RVZ)" "$BIN_DIR/dolphin-tool" "$BIN_DIR/dolphin-tool 2>&1 | grep -q convert"

# 9. Switch - nsz
check_tool "nsz (Switch)" "$BIN_DIR/nsz" "which nsz"

echo ""
echo "Checking Utility Tools:"
echo "-----------------------"

# Utilities
check_tool "rhash" "$(which rhash 2>/dev/null || echo '/usr/bin/rhash')" "rhash --version"
check_tool "7z" "$(which 7z 2>/dev/null || echo '/usr/bin/7z')" "7z --help"
check_tool "parallel" "$(which parallel 2>/dev/null || echo '/usr/bin/parallel')" "parallel --version"
check_tool "pv" "$(which pv 2>/dev/null || echo '/usr/bin/pv')" "pv --version"

echo ""
echo "Summary:"
echo "--------"
echo -e "${GREEN}Passed: $PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED${NC}"
else
    echo -e "${GREEN}Failed: 0${NC}"
fi
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tools verified successfully!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ Some tools need attention${NC}"
    exit 1
fi
