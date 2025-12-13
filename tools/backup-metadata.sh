#!/bin/bash
# =============================================================================
# Backup ROM Metadata (gamelist.xml and media folders)
# =============================================================================
# This script backs up gamelist.xml files and media folders from ROM directories.
# These contain scraped metadata and artwork that takes a long time to regenerate.
#
# Usage:
#   ./backup-metadata.sh                    # Backup to default location
#   ./backup-metadata.sh /path/to/backup    # Backup to custom location
#   ./backup-metadata.sh --restore          # Restore from latest backup
#   ./backup-metadata.sh --list             # List available backups
# =============================================================================

set -e

# Configuration
ROMS_DIR="${ROMS_DIR:-/data/emu/roms}"
BACKUP_BASE="${1:-/data/emu/archive}"
BACKUP_NAME="metadata-backup"
DATE_STAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_BASE}/${BACKUP_NAME}_${DATE_STAMP}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# List available backups
list_backups() {
    echo -e "\n${BLUE}Available metadata backups:${NC}"
    echo "================================================"
    
    if [ ! -d "$BACKUP_BASE" ]; then
        log_warning "Backup directory does not exist: $BACKUP_BASE"
        return 1
    fi
    
    # Find all metadata backups
    backups=$(find "$BACKUP_BASE" -maxdepth 1 -type d -name "${BACKUP_NAME}_*" | sort -r)
    
    if [ -z "$backups" ]; then
        log_warning "No backups found in $BACKUP_BASE"
        return 1
    fi
    
    for backup in $backups; do
        backup_name=$(basename "$backup")
        backup_size=$(du -sh "$backup" 2>/dev/null | cut -f1)
        system_count=$(ls -d "$backup"/*/ 2>/dev/null | wc -l)
        echo "  $backup_name  ($backup_size, $system_count systems)"
    done
    echo ""
}

# Restore from backup
restore_backup() {
    local restore_from="$1"
    
    # If no specific backup provided, use the latest
    if [ -z "$restore_from" ]; then
        restore_from=$(find "$BACKUP_BASE" -maxdepth 1 -type d -name "${BACKUP_NAME}_*" | sort -r | head -1)
    fi
    
    if [ ! -d "$restore_from" ]; then
        log_error "Backup not found: $restore_from"
        list_backups
        return 1
    fi
    
    log_info "Restoring from: $restore_from"
    log_info "Target: $ROMS_DIR"
    echo ""
    
    # Confirm
    read -p "This will overwrite existing metadata. Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warning "Restore cancelled"
        return 1
    fi
    
    # Count systems to restore
    systems=$(ls -d "$restore_from"/*/ 2>/dev/null | wc -l)
    current=0
    
    for system_dir in "$restore_from"/*/; do
        system=$(basename "$system_dir")
        current=$((current + 1))
        
        target_dir="$ROMS_DIR/$system"
        
        if [ ! -d "$target_dir" ]; then
            log_warning "[$current/$systems] Skipping $system (target doesn't exist)"
            continue
        fi
        
        echo -ne "\r[$current/$systems] Restoring $system...                    "
        
        # Restore gamelist.xml
        if [ -f "$system_dir/gamelist.xml" ]; then
            cp "$system_dir/gamelist.xml" "$target_dir/"
        fi
        
        # Restore media folder
        if [ -d "$system_dir/media" ]; then
            rsync -a "$system_dir/media/" "$target_dir/media/"
        fi
    done
    
    echo ""
    log_success "Restore complete!"
}

# Main backup function
do_backup() {
    echo ""
    echo "================================================"
    echo "  ROM Metadata Backup"
    echo "================================================"
    echo ""
    log_info "Source: $ROMS_DIR"
    log_info "Backup: $BACKUP_DIR"
    echo ""
    
    # Check source exists
    if [ ! -d "$ROMS_DIR" ]; then
        log_error "ROMs directory not found: $ROMS_DIR"
        exit 1
    fi
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Count systems
    total_systems=0
    systems_with_metadata=0
    
    for system_dir in "$ROMS_DIR"/*/; do
        [ -d "$system_dir" ] || continue
        total_systems=$((total_systems + 1))
        
        system=$(basename "$system_dir")
        has_metadata=false
        
        # Check for gamelist.xml or media folder
        if [ -f "$system_dir/gamelist.xml" ] || [ -d "$system_dir/media" ]; then
            has_metadata=true
            systems_with_metadata=$((systems_with_metadata + 1))
        fi
    done
    
    log_info "Found $total_systems systems, $systems_with_metadata with metadata"
    echo ""
    
    # Backup each system
    current=0
    backed_up=0
    total_size=0
    
    for system_dir in "$ROMS_DIR"/*/; do
        [ -d "$system_dir" ] || continue
        
        system=$(basename "$system_dir")
        current=$((current + 1))
        
        # Skip if no metadata
        if [ ! -f "$system_dir/gamelist.xml" ] && [ ! -d "$system_dir/media" ]; then
            continue
        fi
        
        echo -ne "\r[$current/$total_systems] Backing up $system...                    "
        
        # Create system backup directory
        system_backup="$BACKUP_DIR/$system"
        mkdir -p "$system_backup"
        
        # Backup gamelist.xml
        if [ -f "$system_dir/gamelist.xml" ]; then
            cp "$system_dir/gamelist.xml" "$system_backup/"
        fi
        
        # Backup media folder (using rsync for efficiency)
        if [ -d "$system_dir/media" ]; then
            rsync -a "$system_dir/media" "$system_backup/"
        fi
        
        backed_up=$((backed_up + 1))
    done
    
    echo ""
    echo ""
    
    # Calculate backup size
    backup_size=$(du -sh "$BACKUP_DIR" | cut -f1)
    
    # Create a manifest
    cat > "$BACKUP_DIR/MANIFEST.txt" << EOF
ROM Metadata Backup
===================
Date: $(date)
Source: $ROMS_DIR
Systems backed up: $backed_up
Total size: $backup_size

Systems:
EOF
    
    for system_dir in "$BACKUP_DIR"/*/; do
        [ -d "$system_dir" ] || continue
        system=$(basename "$system_dir")
        has_gamelist=""
        has_media=""
        [ -f "$system_dir/gamelist.xml" ] && has_gamelist="gamelist.xml"
        [ -d "$system_dir/media" ] && has_media="media/"
        echo "  $system: $has_gamelist $has_media" >> "$BACKUP_DIR/MANIFEST.txt"
    done
    
    # Summary
    echo "================================================"
    echo "  Backup Complete!"
    echo "================================================"
    echo ""
    log_success "Systems backed up: $backed_up"
    log_success "Backup size: $backup_size"
    log_success "Location: $BACKUP_DIR"
    echo ""
    
    # Cleanup old backups (keep last 5)
    backup_count=$(find "$BACKUP_BASE" -maxdepth 1 -type d -name "${BACKUP_NAME}_*" | wc -l)
    if [ "$backup_count" -gt 5 ]; then
        log_info "Cleaning up old backups (keeping 5 most recent)..."
        find "$BACKUP_BASE" -maxdepth 1 -type d -name "${BACKUP_NAME}_*" | sort | head -n -5 | xargs rm -rf
        log_success "Cleanup complete"
    fi
}

# Parse arguments
case "${1:-}" in
    --restore)
        restore_backup "$2"
        ;;
    --list)
        list_backups
        ;;
    --help|-h)
        echo "Usage: $0 [OPTIONS] [BACKUP_DIR]"
        echo ""
        echo "Options:"
        echo "  --restore [BACKUP]  Restore from backup (latest if not specified)"
        echo "  --list              List available backups"
        echo "  --help, -h          Show this help"
        echo ""
        echo "Environment variables:"
        echo "  ROMS_DIR            Source ROMs directory (default: /data/emu/roms)"
        echo ""
        echo "Examples:"
        echo "  $0                           # Backup to /data/emu/archive"
        echo "  $0 /mnt/backup              # Backup to custom location"
        echo "  $0 --restore                # Restore from latest backup"
        echo "  $0 --list                   # List available backups"
        ;;
    *)
        do_backup
        ;;
esac
