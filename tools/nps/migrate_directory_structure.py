#!/usr/bin/env python3
"""
Migrate NoPayStation directory structure from old to new format.

Old format: TITLEID-GameName/base/files
New format: GameName [TITLEID]/files

This script:
1. Renames directories from "TITLEID-Name" to "Name [TITLEID]"
2. Moves contents from base/ folder up one level
3. Removes empty base/ directories
4. Preserves dlc/ and updates/ subdirectories
"""

import os
import sys
import shutil
import re
from pathlib import Path
from typing import List, Tuple, Optional


def parse_old_directory_name(dirname: str) -> Optional[Tuple[str, str]]:
    """
    Parse old directory format: TITLEID-GameName
    Returns (title_id, game_name) or None if doesn't match pattern.
    
    Examples:
        PCSE00880-World_of_Final_Fantasy -> (PCSE00880, World_of_Final_Fantasy)
        PCSA00001-ModNation_Racers -> (PCSA00001, ModNation_Racers)
    """
    # Match PS Vita title IDs: PCS[AEBUX]#####
    match = re.match(r'^(PCS[AEBUX]\d{5})-(.+)$', dirname)
    if match:
        return match.group(1), match.group(2)
    return None


def create_new_directory_name(title_id: str, game_name: str) -> str:
    """
    Create new directory format: GameName [TITLEID]
    
    Examples:
        (PCSE00880, World_of_Final_Fantasy) -> World_of_Final_Fantasy [PCSE00880]
        (PCSA00001, ModNation_Racers) -> ModNation_Racers [PCSA00001]
    """
    # Replace underscores with spaces for readability
    clean_name = game_name.replace('_', ' ')
    return f"{clean_name} [{title_id}]"


def migrate_game_directory(old_path: Path, dry_run: bool = False) -> dict:
    """
    Migrate a single game directory from old to new format.
    
    Returns dict with migration status:
        {
            'success': bool,
            'old_path': str,
            'new_path': str,
            'files_moved': int,
            'base_removed': bool,
            'error': str (if failed)
        }
    """
    result = {
        'success': False,
        'old_path': str(old_path),
        'new_path': None,
        'files_moved': 0,
        'base_removed': False,
        'error': None
    }
    
    try:
        # Parse old directory name
        old_dirname = old_path.name
        parsed = parse_old_directory_name(old_dirname)
        if not parsed:
            result['error'] = f"Doesn't match old format pattern"
            return result
        
        title_id, game_name = parsed
        
        # Create new directory name
        new_dirname = create_new_directory_name(title_id, game_name)
        new_path = old_path.parent / new_dirname
        result['new_path'] = str(new_path)
        
        # Check if target already exists
        if new_path.exists() and new_path != old_path:
            result['error'] = f"Target directory already exists: {new_path}"
            return result
        
        # Check for base/ subdirectory
        base_path = old_path / 'base'
        has_base = base_path.exists() and base_path.is_dir()
        
        if dry_run:
            print(f"  [DRY RUN] Would rename: {old_dirname}")
            print(f"            to: {new_dirname}")
            
            if has_base:
                base_files = list(base_path.iterdir())
                result['files_moved'] = len(base_files)
                print(f"            Move {len(base_files)} files from base/ to root")
                result['base_removed'] = True
            
            result['success'] = True
            return result
        
        # Step 1: If base/ exists, move its contents up
        if has_base:
            base_files = list(base_path.iterdir())
            for item in base_files:
                dest = old_path / item.name
                shutil.move(str(item), str(dest))
                result['files_moved'] += 1
            
            # Remove empty base/ directory
            base_path.rmdir()
            result['base_removed'] = True
        
        # Step 2: Rename directory to new format
        if old_path != new_path:
            old_path.rename(new_path)
        
        result['success'] = True
        
    except Exception as e:
        result['error'] = str(e)
    
    return result


def find_game_directories(root_path: Path) -> List[Path]:
    """
    Find all game directories that match old format pattern.
    Looks in: root_path/vita/games/usa/
    """
    game_dirs = []
    
    # Standard NoPayStation structure
    platforms = ['vita', 'ps3', 'psp', 'psx', 'psm']
    
    for platform in platforms:
        platform_path = root_path / platform / 'games'
        if not platform_path.exists():
            continue
        
        # Check all region directories
        for region_path in platform_path.iterdir():
            if not region_path.is_dir():
                continue
            
            # Find directories matching old format
            for game_path in region_path.iterdir():
                if not game_path.is_dir():
                    continue
                
                if parse_old_directory_name(game_path.name):
                    game_dirs.append(game_path)
    
    return game_dirs


def migrate_all(root_path: Path, dry_run: bool = False, limit: Optional[int] = None) -> dict:
    """
    Migrate all game directories in the NoPayStation packages structure.
    
    Args:
        root_path: Root packages directory (e.g., /data/emu/source/nopaystation/packages)
        dry_run: If True, only show what would be done
        limit: Optional limit on number of directories to process
    
    Returns:
        Summary statistics dictionary
    """
    print(f"{'='*70}")
    print(f"NoPayStation Directory Migration")
    print(f"{'='*70}")
    print(f"Root path: {root_path}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE MIGRATION'}")
    if limit:
        print(f"Limit: {limit} directories")
    print()
    
    # Find all directories to migrate
    print("Scanning for directories to migrate...")
    game_dirs = find_game_directories(root_path)
    
    if limit:
        game_dirs = game_dirs[:limit]
    
    print(f"Found {len(game_dirs)} directories to migrate\n")
    
    if not game_dirs:
        print("No directories found matching old format.")
        return {'total': 0, 'success': 0, 'failed': 0}
    
    # Process each directory
    stats = {
        'total': len(game_dirs),
        'success': 0,
        'failed': 0,
        'files_moved': 0,
        'base_removed': 0,
        'errors': []
    }
    
    for i, game_path in enumerate(game_dirs, 1):
        print(f"[{i}/{len(game_dirs)}] {game_path.name}")
        
        result = migrate_game_directory(game_path, dry_run=dry_run)
        
        if result['success']:
            stats['success'] += 1
            stats['files_moved'] += result['files_moved']
            if result['base_removed']:
                stats['base_removed'] += 1
            
            if not dry_run:
                print(f"  ✓ Migrated to: {Path(result['new_path']).name}")
                if result['files_moved'] > 0:
                    print(f"    Moved {result['files_moved']} files from base/")
        else:
            stats['failed'] += 1
            stats['errors'].append({
                'path': result['old_path'],
                'error': result['error']
            })
            print(f"  ✗ Failed: {result['error']}")
        
        print()
    
    # Summary
    print(f"{'='*70}")
    print(f"Migration Summary")
    print(f"{'='*70}")
    print(f"Total directories: {stats['total']}")
    print(f"Successfully migrated: {stats['success']}")
    print(f"Failed: {stats['failed']}")
    print(f"Files moved from base/: {stats['files_moved']}")
    print(f"base/ directories removed: {stats['base_removed']}")
    
    if stats['errors']:
        print(f"\nErrors ({len(stats['errors'])}):")
        for err in stats['errors'][:10]:  # Show first 10 errors
            print(f"  {err['path']}: {err['error']}")
        if len(stats['errors']) > 10:
            print(f"  ... and {len(stats['errors']) - 10} more")
    
    return stats


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Migrate NoPayStation directory structure',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to see what would be changed
  %(prog)s /data/emu/source/nopaystation/packages --dry-run
  
  # Migrate first 10 directories as test
  %(prog)s /data/emu/source/nopaystation/packages --limit 10
  
  # Full migration (no dry run)
  %(prog)s /data/emu/source/nopaystation/packages
        """
    )
    
    parser.add_argument(
        'root_path',
        help='Root packages directory (e.g., /data/emu/source/nopaystation/packages)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of directories to process (useful for testing)'
    )
    
    args = parser.parse_args()
    
    root_path = Path(args.root_path)
    
    if not root_path.exists():
        print(f"Error: Path does not exist: {root_path}", file=sys.stderr)
        sys.exit(1)
    
    if not root_path.is_dir():
        print(f"Error: Path is not a directory: {root_path}", file=sys.stderr)
        sys.exit(1)
    
    # Run migration
    stats = migrate_all(root_path, dry_run=args.dry_run, limit=args.limit)
    
    # Exit code based on results
    if stats['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
