#!/usr/bin/env python3
"""
Extract PKG files and copy work.bin licenses
Uses pkg2zip to extract PKGs and copies the generated work.bin to base directory
"""

import subprocess
import shutil
from pathlib import Path
from typing import Optional


def extract_pkg_and_get_workbin(pkg_file: Path, zrif_file: Path, output_dir: Path) -> Optional[Path]:
    """
    Extract a PKG file using pkg2zip and return the path to work.bin
    
    Args:
        pkg_file: Path to .pkg file
        zrif_file: Path to .zrif file
        output_dir: Directory to extract to
        
    Returns:
        Path to extracted work.bin or None if extraction failed
    """
    # Read zRIF content
    with open(zrif_file, 'r') as f:
        zrif_string = f.read().strip()
    
    # Run pkg2zip
    try:
        result = subprocess.run(
            ['pkg2zip', '-x', str(pkg_file), zrif_string],
            cwd=output_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per file
        )
        
        if result.returncode != 0:
            return None
        
        # Find the extracted app directory
        app_dirs = list(output_dir.glob('app/*/'))
        if not app_dirs:
            return None
        
        # Get work.bin from sce_sys/package/
        work_bin = app_dirs[0] / 'sce_sys' / 'package' / 'work.bin'
        if work_bin.exists():
            return work_bin
        
        return None
        
    except subprocess.TimeoutExpired:
        print(f"    Timeout extracting {pkg_file.name}")
        return None
    except Exception as e:
        print(f"    Error: {e}")
        return None


def process_game_directory(game_dir: Path, keep_extracted: bool = False, verbose: bool = False) -> dict:
    """
    Process a single game directory
    
    Args:
        game_dir: Path to game directory
        keep_extracted: Keep the extracted app/ directory
        verbose: Print detailed progress
        
    Returns:
        Result dict with status
    """
    result = {
        'status': 'skipped',
        'message': '',
        'work_bin_created': False
    }
    
    base_dir = game_dir / 'base'
    if not base_dir.exists():
        result['message'] = 'No base/ directory'
        return result
    
    # Find PKG and zRIF files
    pkg_files = list(base_dir.glob('*.pkg'))
    zrif_files = list(base_dir.glob('*.zrif'))
    
    if not pkg_files or not zrif_files:
        result['message'] = 'Missing PKG or zRIF'
        return result
    
    pkg_file = pkg_files[0]
    zrif_file = zrif_files[0]
    
    # Check if work.bin already exists and is 512 bytes (proper format)
    existing_work_bin = base_dir / 'work.bin'
    if existing_work_bin.exists():
        size = existing_work_bin.stat().st_size
        if size == 512:
            result['status'] = 'already_done'
            result['message'] = 'work.bin already exists (512 bytes)'
            return result
        else:
            # Remove old work.bin (text format)
            if verbose:
                print(f"    Removing old work.bin ({size} bytes)")
            existing_work_bin.unlink()
    
    if verbose:
        print(f"    Extracting {pkg_file.name}...")
    
    # Extract PKG
    extracted_work_bin = extract_pkg_and_get_workbin(pkg_file, zrif_file, base_dir)
    
    if extracted_work_bin is None:
        result['status'] = 'failed'
        result['message'] = 'Extraction failed'
        return result
    
    # Copy work.bin to base directory
    target_work_bin = base_dir / 'work.bin'
    shutil.copy2(extracted_work_bin, target_work_bin)
    result['work_bin_created'] = True
    
    if verbose:
        print(f"    Created work.bin ({target_work_bin.stat().st_size} bytes)")
    
    # Clean up extracted app directory unless keeping it
    if not keep_extracted:
        app_dir = base_dir / 'app'
        if app_dir.exists():
            shutil.rmtree(app_dir)
            if verbose:
                print(f"    Cleaned up app/ directory")
    
    result['status'] = 'success'
    result['message'] = 'work.bin created'
    return result


def batch_process(root_dir: Path, keep_extracted: bool = False, verbose: bool = False, 
                  limit: Optional[int] = None) -> dict:
    """
    Process all game directories
    
    Args:
        root_dir: Root directory containing game folders
        keep_extracted: Keep extracted app/ directories
        verbose: Print detailed progress
        limit: Optional limit on number of games to process
        
    Returns:
        Statistics dict
    """
    stats = {
        'total_games': 0,
        'success': 0,
        'already_done': 0,
        'failed': 0,
        'skipped': 0,
        'errors': []
    }
    
    game_dirs = sorted([d for d in root_dir.glob('*-*') if d.is_dir()])
    
    if limit:
        game_dirs = game_dirs[:limit]
    
    for i, game_dir in enumerate(game_dirs, 1):
        stats['total_games'] += 1
        
        print(f"[{i}/{len(game_dirs)}] {game_dir.name}")
        
        result = process_game_directory(game_dir, keep_extracted, verbose)
        
        stats[result['status']] += 1
        
        if result['status'] == 'failed':
            stats['errors'].append(f"{game_dir.name}: {result['message']}")
        
        if not verbose:
            print(f"  → {result['message']}")
    
    return stats


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Extract PKGs and create proper work.bin license files'
    )
    parser.add_argument(
        'input',
        type=Path,
        help='Root directory containing game folders'
    )
    parser.add_argument(
        '-k', '--keep-extracted',
        action='store_true',
        help='Keep extracted app/ directories'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '-l', '--limit',
        type=int,
        help='Limit number of games to process (for testing)'
    )
    
    args = parser.parse_args()
    
    print(f"Processing: {args.input}")
    print("=" * 60)
    
    if args.limit:
        print(f"Limit: {args.limit} games (testing mode)")
        print("=" * 60)
    
    stats = batch_process(
        args.input,
        keep_extracted=args.keep_extracted,
        verbose=args.verbose,
        limit=args.limit
    )
    
    print("\n" + "=" * 60)
    print("BATCH PROCESSING COMPLETE")
    print("=" * 60)
    print(f"Total games: {stats['total_games']}")
    print(f"Successfully created work.bin: {stats['success']}")
    print(f"Already had work.bin: {stats['already_done']}")
    print(f"Failed: {stats['failed']}")
    print(f"Skipped (no PKG/zRIF): {stats['skipped']}")
    
    if stats['errors']:
        print("\nErrors:")
        for error in stats['errors'][:20]:  # Show first 20 errors
            print(f"  - {error}")
        if len(stats['errors']) > 20:
            print(f"  ... and {len(stats['errors']) - 20} more")


if __name__ == '__main__':
    main()
