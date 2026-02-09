#!/usr/bin/env python3
"""
Verify ARRM Hashing Behavior for CUE/BIN Disc Systems

This script cross-references ARRM's gamelist.xml MD5 hashes against Redump DAT
entries to determine which file type (CUE vs BIN) ARRM actually hashes.

For each game found in gamelist.xml:
1. Extract the stored MD5 hash
2. Look up the game in the Redump DAT
3. Compare ARRM's MD5 against the CUE file MD5 and BIN file MD5(s)
4. Report which one matches

This will help us understand ARRM's hashing strategy for disc-based systems.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
import re
import sys

# Configuration
ROMS_BASE = Path("/data/emu/roms")
DATS_BASE = Path("/data/emu/rom-farmer/dats/redump")

# Systems with CUE/BIN format and their DAT patterns
DISC_SYSTEMS = {
    "3do": "Panasonic - 3DO Interactive Multiplayer",
    "dreamcast": "Sega - Dreamcast",
    "megacd": "Sega - Mega CD & Sega CD",
    "pcenginecd": "NEC - PC Engine CD & TurboGrafx-CD",
    "psx": "Sony - PlayStation",
    "ps2": "Sony - PlayStation 2",
    "saturn": "Sega - Saturn",
    "segacd": "Sega - Mega CD & Sega CD",  # Alias
}


def parse_gamelist(gamelist_path: Path) -> dict:
    """Parse gamelist.xml and extract path -> md5 mappings."""
    games = {}
    try:
        tree = ET.parse(gamelist_path)
        root = tree.getroot()
        for game in root.findall('.//game'):
            path_elem = game.find('path')
            md5_elem = game.find('md5')
            name_elem = game.find('name')
            
            if path_elem is not None and md5_elem is not None:
                path = path_elem.text
                md5 = md5_elem.text.lower() if md5_elem.text else None
                name = name_elem.text if name_elem is not None else Path(path).stem
                
                if path and md5:
                    games[path] = {
                        'md5': md5,
                        'name': name,
                        'extension': Path(path).suffix.lower()
                    }
    except Exception as e:
        print(f"  Error parsing {gamelist_path}: {e}")
    
    return games


def parse_redump_dat(dat_path: Path) -> dict:
    """Parse Redump DAT and extract game -> file hashes mappings."""
    games = {}
    try:
        tree = ET.parse(dat_path)
        root = tree.getroot()
        
        for game in root.findall('.//game'):
            game_name = game.get('name', '')
            files = {}
            
            for rom in game.findall('rom'):
                filename = rom.get('name', '')
                md5 = rom.get('md5', '').lower()
                size = int(rom.get('size', 0))
                
                if filename and md5:
                    ext = Path(filename).suffix.lower()
                    files[filename] = {
                        'md5': md5,
                        'size': size,
                        'extension': ext
                    }
            
            if files:
                games[game_name] = files
                
    except Exception as e:
        print(f"  Error parsing {dat_path}: {e}")
    
    return games


def find_dat_file(system: str) -> Path | None:
    """Find the Redump DAT file for a system."""
    pattern = DISC_SYSTEMS.get(system)
    if not pattern:
        return None
    
    # Try exact match first
    for dat_file in DATS_BASE.glob("*.dat"):
        if pattern.lower() in dat_file.stem.lower():
            return dat_file
    
    return None


def normalize_game_name(name: str) -> str:
    """Normalize game name for matching."""
    # Remove extension
    name = re.sub(r'\.(cue|bin|iso|chd)$', '', name, flags=re.IGNORECASE)
    # Remove path prefix
    name = name.lstrip('./')
    # Normalize whitespace
    name = ' '.join(name.split())
    return name.lower()


def find_dat_match(arrm_path: str, arrm_name: str, dat_games: dict) -> tuple:
    """Find matching game in DAT for an ARRM entry."""
    # Get the filename without path
    filename = Path(arrm_path).stem
    norm_filename = normalize_game_name(filename)
    
    best_match = None
    best_score = 0
    
    for dat_game_name, files in dat_games.items():
        norm_dat_name = normalize_game_name(dat_game_name)
        
        # Exact match
        if norm_filename == norm_dat_name:
            return dat_game_name, files
        
        # Partial match - filename contained in DAT name or vice versa
        if norm_filename in norm_dat_name or norm_dat_name in norm_filename:
            score = len(set(norm_filename.split()) & set(norm_dat_name.split()))
            if score > best_score:
                best_score = score
                best_match = (dat_game_name, files)
    
    return best_match if best_match else (None, None)


def analyze_hash_match(arrm_md5: str, dat_files: dict) -> dict:
    """Analyze which file in the DAT matches ARRM's MD5."""
    result = {
        'matched_file': None,
        'matched_type': None,
        'cue_md5': None,
        'bin_md5s': [],
        'iso_md5': None,
    }
    
    for filename, info in dat_files.items():
        ext = info['extension']
        md5 = info['md5']
        size = info['size']
        
        if ext == '.cue':
            result['cue_md5'] = md5
        elif ext == '.bin':
            result['bin_md5s'].append({'filename': filename, 'md5': md5, 'size': size})
        elif ext == '.iso':
            result['iso_md5'] = md5
        
        if md5 == arrm_md5:
            result['matched_file'] = filename
            result['matched_type'] = ext
    
    return result


def main():
    print("=" * 80)
    print("ARRM Hashing Behavior Verification for CUE/BIN Disc Systems")
    print("=" * 80)
    print()
    
    # Overall statistics
    overall_stats = defaultdict(lambda: defaultdict(int))
    detailed_results = []
    
    for system, dat_pattern in DISC_SYSTEMS.items():
        gamelist_path = ROMS_BASE / system / "gamelist.xml"
        
        if not gamelist_path.exists():
            continue
        
        print(f"\n{'='*60}")
        print(f"System: {system.upper()}")
        print(f"{'='*60}")
        
        # Find DAT file
        dat_path = find_dat_file(system)
        if not dat_path:
            print(f"  WARNING: No DAT file found for pattern '{dat_pattern}'")
            continue
        
        print(f"  DAT: {dat_path.name}")
        
        # Parse files
        arrm_games = parse_gamelist(gamelist_path)
        dat_games = parse_redump_dat(dat_path)
        
        print(f"  ARRM games: {len(arrm_games)}")
        print(f"  DAT games: {len(dat_games)}")
        
        # Filter to only CUE/BIN/ISO games
        cue_games = {p: g for p, g in arrm_games.items() 
                     if g['extension'] in ('.cue', '.bin', '.iso', '.chd')}
        
        print(f"  Disc games in ARRM: {len(cue_games)}")
        print()
        
        # Statistics for this system
        stats = defaultdict(int)
        
        # Analyze each game
        sample_count = 0
        for arrm_path, arrm_info in cue_games.items():
            arrm_md5 = arrm_info['md5']
            arrm_name = arrm_info['name']
            arrm_ext = arrm_info['extension']
            
            # Find matching DAT entry
            dat_game_name, dat_files = find_dat_match(arrm_path, arrm_name, dat_games)
            
            if not dat_files:
                stats['no_dat_match'] += 1
                continue
            
            # Analyze which file matches
            match_result = analyze_hash_match(arrm_md5, dat_files)
            
            if match_result['matched_type']:
                stats[f"matched_{match_result['matched_type']}"] += 1
                overall_stats[system][match_result['matched_type']] += 1
                
                # Store detailed result for interesting cases
                if sample_count < 3 or match_result['matched_type'] == '.cue':
                    detailed_results.append({
                        'system': system,
                        'game': arrm_name[:50],
                        'arrm_ext': arrm_ext,
                        'arrm_md5': arrm_md5,
                        'matched_type': match_result['matched_type'],
                        'matched_file': match_result['matched_file'],
                        'cue_md5': match_result['cue_md5'],
                        'bin_count': len(match_result['bin_md5s']),
                    })
                    sample_count += 1
            else:
                stats['no_hash_match'] += 1
                overall_stats[system]['no_match'] += 1
                
                # Log unmatched for debugging
                if stats['no_hash_match'] <= 2:
                    print(f"  NO MATCH: {arrm_name[:40]}")
                    print(f"    ARRM MD5: {arrm_md5}")
                    print(f"    CUE MD5:  {match_result['cue_md5']}")
                    for bin_info in match_result['bin_md5s'][:3]:
                        print(f"    BIN MD5:  {bin_info['md5']} ({bin_info['size']:,} bytes)")
        
        # Print system summary
        print(f"  Results for {system}:")
        for match_type, count in sorted(stats.items()):
            print(f"    {match_type}: {count}")
    
    # Print overall summary
    print("\n" + "=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)
    
    totals = defaultdict(int)
    
    print("\nMatches by System and File Type:")
    print("-" * 60)
    print(f"{'System':<15} {'CUE':<8} {'BIN':<8} {'ISO':<8} {'None':<8}")
    print("-" * 60)
    
    for system in DISC_SYSTEMS:
        if system in overall_stats:
            cue = overall_stats[system].get('.cue', 0)
            bin_ = overall_stats[system].get('.bin', 0)
            iso = overall_stats[system].get('.iso', 0)
            none = overall_stats[system].get('no_match', 0)
            
            totals['.cue'] += cue
            totals['.bin'] += bin_
            totals['.iso'] += iso
            totals['no_match'] += none
            
            if cue or bin_ or iso or none:
                print(f"{system:<15} {cue:<8} {bin_:<8} {iso:<8} {none:<8}")
    
    print("-" * 60)
    print(f"{'TOTAL':<15} {totals['.cue']:<8} {totals['.bin']:<8} {totals['.iso']:<8} {totals['no_match']:<8}")
    
    # Print detailed samples
    if detailed_results:
        print("\n" + "=" * 80)
        print("SAMPLE MATCHES (showing what ARRM MD5 matched in DAT)")
        print("=" * 80)
        
        for r in detailed_results[:15]:
            print(f"\n  [{r['system'].upper()}] {r['game']}")
            print(f"    ARRM path ext: {r['arrm_ext']}")
            print(f"    ARRM MD5:      {r['arrm_md5']}")
            print(f"    Matched:       {r['matched_type']} file")
            print(f"    Matched file:  {r['matched_file']}")
            if r['cue_md5']:
                print(f"    CUE MD5:       {r['cue_md5']}")
            print(f"    BIN files:     {r['bin_count']}")
    
    # Conclusion
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    
    total_matches = totals['.cue'] + totals['.bin'] + totals['.iso']
    if total_matches > 0:
        cue_pct = (totals['.cue'] / total_matches) * 100
        bin_pct = (totals['.bin'] / total_matches) * 100
        iso_pct = (totals['.iso'] / total_matches) * 100
        
        print(f"\nOf {total_matches} matched games:")
        print(f"  - CUE file MD5 matched: {totals['.cue']:4} ({cue_pct:5.1f}%)")
        print(f"  - BIN file MD5 matched: {totals['.bin']:4} ({bin_pct:5.1f}%)")
        print(f"  - ISO file MD5 matched: {totals['.iso']:4} ({iso_pct:5.1f}%)")
        
        if bin_pct > 90:
            print("\n*** ARRM predominantly hashes BIN files, NOT CUE files! ***")
        elif cue_pct > 90:
            print("\n*** ARRM predominantly hashes CUE files ***")
        else:
            print("\n*** Mixed behavior detected - needs investigation ***")


if __name__ == "__main__":
    main()
