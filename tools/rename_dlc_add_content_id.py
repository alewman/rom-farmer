#!/usr/bin/env python3
"""Rename existing DLC files to include Content ID for regional differentiation.

This adds Content ID to filenames to prevent collisions between US/EU/JP versions.
Format: "Name [CONTENT_ID].pkg"
"""

import csv
from pathlib import Path


def normalize_filename(name: str) -> str:
    """Normalize filename - same as sync_nps_dlc.py."""
    safe_name = name.replace('®', '').replace('™', '').replace('©', '')
    safe_name = safe_name.replace(':', ' ').replace(' - ', ' ')
    safe_name = safe_name.replace('/', ' ').replace('\\', ' ')
    safe_name = ' '.join(safe_name.split())
    return safe_name


def main():
    database_path = Path('/path/to/source/nopaystation/PS3_DLCS.tsv')
    pkg_dir = Path('/path/to/source/nopaystation/downloads-ps3-dlc/packages')
    
    print(f"Loading database: {database_path}")
    
    # Build mapping: normalized_name -> list of (original_name, content_id)
    name_map = {}
    
    with open(database_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            name = row.get('Name', '')
            content_id = row.get('Content ID', '')
            
            if not name or not content_id:
                continue
            
            normalized = normalize_filename(name)
            
            if normalized not in name_map:
                name_map[normalized] = []
            
            name_map[normalized].append((name, content_id))
    
    print(f"  Loaded {len(name_map)} unique normalized names")
    print()
    
    renamed = 0
    skipped = 0
    errors = 0
    
    print("Processing files...")
    print()
    
    for pkg_file in sorted(pkg_dir.glob('*.pkg')):
        # Skip files that already have Content ID in brackets
        if '[' in pkg_file.name and ']' in pkg_file.name:
            skipped += 1
            continue
        
        old_name_with_ext = pkg_file.name  # e.g., "Siren Blood Curse Episode 4.pkg"
        old_name = pkg_file.stem  # Without .pkg
        
        # Look up in database
        if old_name not in name_map:
            print(f"⚠ NOT IN DB: {old_name}")
            errors += 1
            continue
        
        entries = name_map[old_name]
        
        # If only one entry, simple rename
        if len(entries) == 1:
            original_name, content_id = entries[0]
            new_path = pkg_file.parent / f"{old_name} [{content_id}].pkg"
            
            if new_path.exists():
                print(f"⚠ SKIP (target exists): {old_name}")
                skipped += 1
                continue
            
            pkg_file.rename(new_path)
            renamed += 1
            
            if renamed % 100 == 0:
                print(f"  Progress: {renamed} renamed...")
        
        # Multiple entries - ambiguous! Keep first one found
        else:
            print(f"⚠ MULTIPLE MATCHES ({len(entries)}): {old_name}")
            print(f"  Entries:")
            for orig, cid in entries:
                print(f"    - {cid}: {orig}")
            
            # Use first match
            original_name, content_id = entries[0]
            new_path = pkg_file.parent / f"{old_name} [{content_id}].pkg"
            
            if new_path.exists():
                print(f"  SKIP (target exists)")
                skipped += 1
                continue
            
            print(f"  Using first: [{content_id}]")
            pkg_file.rename(new_path)
            renamed += 1
    
    print()
    print("=" * 80)
    print(f"Renamed: {renamed}")
    print(f"Skipped: {skipped}")
    print(f"Errors:  {errors}")
    print(f"Total:   {renamed + skipped + errors}")


if __name__ == '__main__':
    main()
