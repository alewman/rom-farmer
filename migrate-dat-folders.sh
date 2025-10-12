#!/bin/bash
#
# migrate-dat-folders.sh
# 
# Migrate DAT folder structure to consistent naming convention
# Pattern: {source}.{tool}.{filter}.{region}/
#
# Where:
#   source = nointro | redump
#   tool   = retool | (other tools)
#   filter = 1g1r | (other filters)
#   region = all | eng | usa | jpn | etc.

set -euo pipefail

DATS_DIR="/data/emu/dats"
DRY_RUN=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  ROM Groomer - DAT Folder Migration${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

do_rename() {
    local old_path="$1"
    local new_path="$2"
    
    if [ "$DRY_RUN" = true ]; then
        print_info "Would rename: $old_path → $new_path"
    else
        if [ -d "$old_path" ]; then
            mv "$old_path" "$new_path"
            print_success "Renamed: $(basename "$old_path") → $(basename "$new_path")"
        else
            print_warning "Skipped (not found): $old_path"
        fi
    fi
}

print_header

# Check if dats directory exists
if [ ! -d "$DATS_DIR" ]; then
    print_error "DAT directory not found: $DATS_DIR"
    exit 1
fi

cd "$DATS_DIR"

print_info "Current directory: $DATS_DIR"
echo

# Parse command line arguments
if [ "${1:-}" = "--dry-run" ] || [ "${1:-}" = "-n" ]; then
    DRY_RUN=true
    print_warning "DRY RUN MODE - No changes will be made"
    echo
fi

print_info "Analyzing folder structure..."
echo

# List current folders
print_info "Current folders:"
ls -1d */ 2>/dev/null | sed 's/\///' | sed 's/^/  - /'
echo

# Migrations to perform
declare -a migrations=(
    # Old Name                      New Name
    "retool:nointro.retool"
    "retool.all:nointro.retool.all"
    "retool.redump.1g1r.eng:redump.retool.1g1r.eng"
)

print_info "Planned migrations:"
echo

migration_count=0
for migration in "${migrations[@]}"; do
    old_name="${migration%%:*}"
    new_name="${migration#*:}"
    
    old_path="$DATS_DIR/$old_name"
    new_path="$DATS_DIR/$new_name"
    
    # Check if old path exists
    if [ -d "$old_path" ]; then
        echo "  $old_name → $new_name"
        migration_count=$((migration_count + 1))
    fi
done

echo

if [ $migration_count -eq 0 ]; then
    print_success "No migrations needed - all folders already follow naming convention!"
    exit 0
fi

print_info "Found $migration_count folder(s) to migrate"
echo

# Confirm if not dry run
if [ "$DRY_RUN" = false ]; then
    read -p "Proceed with migration? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Migration cancelled"
        exit 0
    fi
    echo
fi

# Perform migrations
print_info "Performing migrations..."
echo

for migration in "${migrations[@]}"; do
    old_name="${migration%%:*}"
    new_name="${migration#*:}"
    
    old_path="$DATS_DIR/$old_name"
    new_path="$DATS_DIR/$new_name"
    
    do_rename "$old_path" "$new_path"
done

echo

if [ "$DRY_RUN" = true ]; then
    print_warning "DRY RUN COMPLETE - Run without --dry-run to apply changes"
else
    print_success "Migration complete!"
    echo
    print_info "Updated folder structure:"
    ls -1d */ 2>/dev/null | sed 's/\///' | sed 's/^/  - /'
fi

echo

# Show recommended structure
print_info "Recommended naming convention:"
cat << 'PATTERN'

  Pattern: {source}.{tool}.{filter}.{region}/
  
  Where:
    source = nointro | redump
    tool   = retool | (other tools)
    filter = 1g1r | (other filters)
    region = all | eng | usa | jpn | etc.
  
  Examples:
    ✓ nointro/                      - Raw No-Intro DATs
    ✓ redump/                       - Raw Redump DATs
    ✓ nointro.retool/               - No-Intro processed by Retool
    ✓ nointro.retool.1g1r.all/      - No-Intro + Retool + 1G1R (all regions)
    ✓ nointro.retool.1g1r.eng/      - No-Intro + Retool + 1G1R (English)
    ✓ nointro.retool.1g1r.usa/      - No-Intro + Retool + 1G1R (USA)
    ✓ redump.retool.1g1r.eng/       - Redump + Retool + 1G1R (English)
    ✓ redump.retool.1g1r.usa/       - Redump + Retool + 1G1R (USA)
    
PATTERN

echo
