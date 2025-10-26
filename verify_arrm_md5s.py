#!/usr/bin/env python3
"""
Verify ARRM MD5 hashes in gamelist.xml against source CUE files.

ARRM stores the MD5 of the .cue file (not the .zip or .bin files).
This script validates that discovery by:
1. Parsing gamelist.xml to extract MD5s and game paths
2. Finding corresponding source .zip files
3. Extracting .cue files and computing their MD5s
4. Comparing against gamelist.xml values
"""

import xml.etree.ElementTree as ET
import hashlib
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import sys

def compute_md5(file_path: Path) -> str:
    """Compute MD5 hash of a file."""
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5.update(chunk)
    return md5.hexdigest()

def extract_cue_from_zip(zip_path: Path, temp_dir: Path) -> Optional[Path]:
    """Extract the .cue file from a zip archive."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Find the .cue file
            cue_files = [f for f in zf.namelist() if f.lower().endswith('.cue')]
            if not cue_files:
                return None
            
            # Extract just the .cue file
            cue_name = cue_files[0]
            zf.extract(cue_name, temp_dir)
            return temp_dir / cue_name
    except Exception as e:
        print(f"Error extracting {zip_path}: {e}", file=sys.stderr)
        return None

def parse_gamelist(gamelist_path: Path) -> List[Dict[str, str]]:
    """Parse gamelist.xml and extract game entries with MD5 and path."""
    tree = ET.parse(gamelist_path)
    root = tree.getroot()
    
    games = []
    for game_elem in root.findall('game'):
        path_elem = game_elem.find('path')
        md5_elem = game_elem.find('md5')
        name_elem = game_elem.find('name')
        
        if path_elem is not None and md5_elem is not None:
            games.append({
                'name': name_elem.text if name_elem is not None else 'Unknown',
                'path': path_elem.text.replace('./', ''),
                'md5': md5_elem.text
            })
    
    return games

def verify_saturn_md5s(
    gamelist_path: Path,
    source_dir: Path,
    temp_dir: Path,
    verbose: bool = False
) -> Tuple[int, int, int]:
    """
    Verify MD5 hashes in gamelist.xml against source .cue files.
    
    Returns:
        (matches, mismatches, missing) - counts of verification results
    """
    # Create temp directory for extraction
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Parse gamelist
    print(f"📋 Parsing {gamelist_path}...")
    games = parse_gamelist(gamelist_path)
    print(f"   Found {len(games)} games with MD5 hashes\n")
    
    matches = 0
    mismatches = 0
    missing = 0
    
    for i, game in enumerate(games, 1):
        game_name = game['name']
        expected_md5 = game['md5']
        zip_filename = game['path']
        
        # Find source zip file
        source_zip = source_dir / zip_filename
        
        if not source_zip.exists():
            missing += 1
            if verbose:
                print(f"❌ [{i}/{len(games)}] MISSING: {game_name}")
                print(f"   Expected: {source_zip}")
            continue
        
        # Extract .cue file
        cue_path = extract_cue_from_zip(source_zip, temp_dir)
        if not cue_path:
            print(f"⚠️  [{i}/{len(games)}] NO CUE: {game_name}")
            missing += 1
            continue
        
        # Compute MD5 of .cue file
        actual_md5 = compute_md5(cue_path)
        
        # Compare
        if actual_md5 == expected_md5:
            matches += 1
            if verbose:
                print(f"✅ [{i}/{len(games)}] MATCH: {game_name}")
                print(f"   MD5: {actual_md5}")
        else:
            mismatches += 1
            print(f"❌ [{i}/{len(games)}] MISMATCH: {game_name}")
            print(f"   Expected: {expected_md5}")
            print(f"   Actual:   {actual_md5}")
            print(f"   Source:   {source_zip}")
        
        # Clean up extracted .cue file
        if cue_path.exists():
            cue_path.unlink()
        
        # Progress indicator for non-verbose mode
        if not verbose and i % 10 == 0:
            print(f"Progress: {i}/{len(games)} games verified...", end='\r')
    
    if not verbose:
        print()  # Clear progress line
    
    return matches, mismatches, missing

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Verify ARRM MD5 hashes against source CUE files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Verify all Saturn games
  python3 verify_arrm_md5s.py
  
  # Verbose mode (show all matches)
  python3 verify_arrm_md5s.py -v
  
  # Custom paths
  python3 verify_arrm_md5s.py --gamelist /path/to/gamelist.xml --source /path/to/roms
        """
    )
    
    parser.add_argument(
        '--gamelist',
        type=Path,
        default=Path('/data/emu/roms/saturn/gamelist.xml'),
        help='Path to gamelist.xml (default: /data/emu/roms/saturn/gamelist.xml)'
    )
    
    parser.add_argument(
        '--source',
        type=Path,
        default=Path('/data/emu/source/myrient.erista.me/files/Redump/Sega - Saturn'),
        help='Path to source ROM directory (default: Redump Saturn directory)'
    )
    
    parser.add_argument(
        '--temp',
        type=Path,
        default=Path('/tmp/saturn_verify'),
        help='Temporary directory for extraction (default: /tmp/saturn_verify)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show all verification results (not just errors)'
    )
    
    args = parser.parse_args()
    
    # Validate paths
    if not args.gamelist.exists():
        print(f"❌ Error: gamelist.xml not found: {args.gamelist}", file=sys.stderr)
        return 1
    
    if not args.source.exists():
        print(f"❌ Error: Source directory not found: {args.source}", file=sys.stderr)
        return 1
    
    print("=" * 70)
    print("ARRM MD5 Verification")
    print("=" * 70)
    print(f"Gamelist: {args.gamelist}")
    print(f"Source:   {args.source}")
    print(f"Temp:     {args.temp}")
    print("=" * 70)
    print()
    
    # Run verification
    matches, mismatches, missing = verify_saturn_md5s(
        args.gamelist,
        args.source,
        args.temp,
        verbose=args.verbose
    )
    
    # Print summary
    total = matches + mismatches + missing
    print()
    print("=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    print(f"Total games:     {total}")
    print(f"✅ Matches:      {matches} ({matches/total*100:.1f}%)")
    print(f"❌ Mismatches:   {mismatches} ({mismatches/total*100:.1f}%)")
    print(f"⚠️  Missing:      {missing} ({missing/total*100:.1f}%)")
    print("=" * 70)
    
    if mismatches == 0 and missing == 0:
        print("\n🎉 SUCCESS! All MD5 hashes verified correctly!")
        print("   ARRM indeed stores CUE file MD5s, not ZIP or BIN MD5s.")
        return 0
    elif mismatches > 0:
        print(f"\n⚠️  WARNING: {mismatches} MD5 mismatches found!")
        return 1
    else:
        print(f"\n⚠️  WARNING: {missing} games missing from source directory")
        return 1

if __name__ == '__main__':
    sys.exit(main())
