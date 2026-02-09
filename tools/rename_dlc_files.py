#!/usr/bin/env python3
"""Rename existing DLC files to match new normalization scheme.

This renames files from old format (with - dashes) to new format (spaces only).
"""

from pathlib import Path


def normalize_filename(name: str) -> str:
    """New normalization - same as sync_nps_dlc.py."""
    # Remove trademark/copyright symbols
    safe_name = name.replace('®', '').replace('™', '').replace('©', '')
    
    # Normalize separators: convert - and : to single space
    safe_name = safe_name.replace(':', ' ').replace(' - ', ' ')
    
    # Remove filesystem-unsafe characters
    safe_name = safe_name.replace('/', ' ').replace('\\', ' ')
    
    # Collapse multiple spaces to single space
    safe_name = ' '.join(safe_name.split())
    
    return safe_name


def main():
    pkg_dir = Path('/data/emu/source/nopaystation/downloads-ps3-dlc/packages')
    
    renamed = 0
    skipped = 0
    
    print(f"Scanning: {pkg_dir}")
    print()
    
    for pkg_file in sorted(pkg_dir.glob('*.pkg')):
        old_name = pkg_file.stem  # Without .pkg
        new_name = normalize_filename(old_name)
        
        if old_name == new_name:
            skipped += 1
            continue
        
        new_path = pkg_file.parent / f"{new_name}.pkg"
        
        # Check if target already exists
        if new_path.exists():
            print(f"⚠ SKIP (target exists): {old_name}")
            print(f"                    → {new_name}")
            skipped += 1
            continue
        
        # Rename
        print(f"✓ RENAME: {old_name}")
        print(f"       → {new_name}")
        pkg_file.rename(new_path)
        renamed += 1
    
    print()
    print("=" * 80)
    print(f"Renamed: {renamed}")
    print(f"Skipped: {skipped}")
    print(f"Total:   {renamed + skipped}")


if __name__ == '__main__':
    main()
