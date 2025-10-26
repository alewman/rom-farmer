#!/usr/bin/env python3
"""Compare DAT file MD5s with actual source file MD5s."""

import sys
import hashlib
import zipfile
from pathlib import Path
from collections import defaultdict
import xml.etree.ElementTree as ET

def calculate_cue_md5(zip_path: Path) -> str:
    """Extract and hash the CUE file from a ZIP."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Find the CUE file
            cue_files = [f for f in zf.namelist() if f.lower().endswith('.cue')]
            if not cue_files:
                return None
            
            # Hash the first CUE file
            cue_content = zf.read(cue_files[0])
            return hashlib.md5(cue_content).hexdigest()
    except Exception as e:
        print(f"  Error reading {zip_path.name}: {e}", file=sys.stderr)
        return None

def parse_dat_file(dat_path: Path) -> dict:
    """Parse DAT file and extract MD5 hashes."""
    tree = ET.parse(dat_path)
    root = tree.getroot()
    
    dat_md5s = {}
    for game in root.findall('.//game'):
        game_name = game.get('name')
        # Look for MD5 in rom elements
        for rom in game.findall('rom'):
            md5 = rom.get('md5')
            if md5:
                dat_md5s[game_name] = md5.lower()
                break
    
    return dat_md5s

def main():
    # Paths
    dat_dir = Path('/data/emu/dats/redump.retool.1g1r.eng')
    source_dir = Path('/data/emu/roms/saturn')
    
    # Find Saturn DAT file
    dat_files = list(dat_dir.glob('Sega - Saturn*.dat'))
    if not dat_files:
        print("❌ No Saturn DAT file found!")
        return 1
    
    dat_path = dat_files[0]
    print(f"📄 DAT file: {dat_path.name}")
    print()
    
    # Parse DAT
    print("Parsing DAT file...")
    dat_md5s = parse_dat_file(dat_path)
    print(f"  Found {len(dat_md5s)} games with MD5s in DAT")
    print()
    
    # Scan source directory
    print(f"Scanning source directory: {source_dir}")
    zip_files = list(source_dir.glob('*.zip'))
    print(f"  Found {len(zip_files)} ZIP files")
    print()
    
    # Compare MD5s
    print("Comparing MD5s...")
    matches = []
    mismatches = []
    not_in_dat = []
    
    for i, zip_path in enumerate(zip_files, 1):
        if i % 50 == 0:
            print(f"  Progress: {i}/{len(zip_files)}")
        
        # Calculate actual MD5
        actual_md5 = calculate_cue_md5(zip_path)
        if not actual_md5:
            continue
        
        # Get game name (remove .zip extension)
        game_name = zip_path.stem
        
        # Check if in DAT
        if game_name not in dat_md5s:
            not_in_dat.append((game_name, actual_md5))
            continue
        
        # Compare
        dat_md5 = dat_md5s[game_name]
        if actual_md5 == dat_md5:
            matches.append(game_name)
        else:
            mismatches.append((game_name, dat_md5, actual_md5))
    
    # Results
    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()
    print(f"✅ Matches: {len(matches)} games")
    print(f"❌ Mismatches: {len(mismatches)} games")
    print(f"⚠️  Not in DAT: {len(not_in_dat)} games")
    print()
    
    if mismatches:
        print("MISMATCHED MD5s (first 10):")
        print("-" * 80)
        for game_name, dat_md5, actual_md5 in mismatches[:10]:
            print(f"  {game_name}")
            print(f"    DAT:    {dat_md5}")
            print(f"    Actual: {actual_md5}")
        if len(mismatches) > 10:
            print(f"  ... and {len(mismatches) - 10} more")
        print()
    
    if not_in_dat:
        print("NOT IN DAT (first 10):")
        print("-" * 80)
        for game_name, actual_md5 in not_in_dat[:10]:
            print(f"  {game_name} ({actual_md5})")
        if len(not_in_dat) > 10:
            print(f"  ... and {len(not_in_dat) - 10} more")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
