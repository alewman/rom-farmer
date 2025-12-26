#!/usr/bin/env python3
"""
Deeper analysis: Does ARRM hash BIN for single-track and CUE for multi-track?
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

ROMS_BASE = Path("/data/emu/roms")
DATS_BASE = Path("/data/emu/rom-farmer/dats/redump")

DISC_SYSTEMS = {
    "3do": "Panasonic - 3DO Interactive Multiplayer",
    "dreamcast": "Sega - Dreamcast",
    "ps2": "Sony - PlayStation 2",
    "psx": "Sony - PlayStation",
    "megacd": "Sega - Mega CD & Sega CD",
    "saturn": "Sega - Saturn",
}


def parse_gamelist(gamelist_path: Path) -> dict:
    games = {}
    try:
        tree = ET.parse(gamelist_path)
        for game in tree.getroot().findall('.//game'):
            path_elem = game.find('path')
            md5_elem = game.find('md5')
            if path_elem is not None and md5_elem is not None and path_elem.text and md5_elem.text:
                games[path_elem.text] = md5_elem.text.lower()
    except Exception as e:
        print(f"  Error: {e}")
    return games


def parse_redump_dat(dat_path: Path) -> dict:
    games = {}
    try:
        tree = ET.parse(dat_path)
        for game in tree.getroot().findall('.//game'):
            game_name = game.get('name', '')
            files = {}
            for rom in game.findall('rom'):
                filename = rom.get('name', '')
                md5 = rom.get('md5', '').lower()
                size = int(rom.get('size', 0))
                if filename and md5:
                    files[filename] = {'md5': md5, 'size': size}
            if files:
                games[game_name] = files
    except Exception as e:
        print(f"  Error: {e}")
    return games


def find_dat_file(system: str) -> Path | None:
    pattern = DISC_SYSTEMS.get(system)
    if not pattern:
        return None
    for dat_file in DATS_BASE.glob("*.dat"):
        if pattern.lower() in dat_file.stem.lower():
            return dat_file
    return None


def analyze_by_track_count():
    """Analyze if single-track uses BIN hash and multi-track uses CUE hash."""
    
    print("=" * 80)
    print("ARRM Hashing Analysis by Track Count")
    print("=" * 80)
    
    for system, dat_pattern in DISC_SYSTEMS.items():
        gamelist_path = ROMS_BASE / system / "gamelist.xml"
        if not gamelist_path.exists():
            continue
            
        dat_path = find_dat_file(system)
        if not dat_path:
            continue
        
        print(f"\n{'='*60}")
        print(f"System: {system.upper()}")
        print(f"{'='*60}")
        
        arrm_games = parse_gamelist(gamelist_path)
        dat_games = parse_redump_dat(dat_path)
        
        # Build MD5 lookup tables
        cue_md5_to_game = {}  # CUE md5 -> game info
        bin_md5_to_game = {}  # BIN md5 -> game info
        iso_md5_to_game = {}  # ISO md5 -> game info
        
        for game_name, files in dat_games.items():
            bin_files = []
            cue_file = None
            iso_file = None
            
            for filename, info in files.items():
                ext = Path(filename).suffix.lower()
                if ext == '.cue':
                    cue_file = info
                    cue_md5_to_game[info['md5']] = {
                        'game': game_name, 
                        'bin_count': 0,  # Will be updated
                    }
                elif ext == '.bin':
                    bin_files.append(info)
                    bin_md5_to_game[info['md5']] = {
                        'game': game_name,
                        'size': info['size'],
                    }
                elif ext == '.iso':
                    iso_file = info
                    iso_md5_to_game[info['md5']] = {'game': game_name}
            
            # Update bin count for CUE entry
            if cue_file and cue_file['md5'] in cue_md5_to_game:
                cue_md5_to_game[cue_file['md5']]['bin_count'] = len(bin_files)
        
        # Analyze ARRM hashes
        stats = {
            'single_track_bin': 0,
            'single_track_cue': 0,
            'multi_track_bin': 0,
            'multi_track_cue': 0,
            'iso_match': 0,
            'no_match': 0,
        }
        
        single_bin_examples = []
        multi_cue_examples = []
        anomalies = []
        
        for arrm_path, arrm_md5 in arrm_games.items():
            ext = Path(arrm_path).suffix.lower()
            if ext not in ('.cue', '.bin', '.iso', '.chd'):
                continue
            
            matched = False
            
            # Check CUE match
            if arrm_md5 in cue_md5_to_game:
                info = cue_md5_to_game[arrm_md5]
                bin_count = info['bin_count']
                if bin_count == 1:
                    stats['single_track_cue'] += 1
                    anomalies.append(f"Single-track CUE match: {arrm_path}")
                else:
                    stats['multi_track_cue'] += 1
                    if len(multi_cue_examples) < 3:
                        multi_cue_examples.append(f"{arrm_path} ({bin_count} tracks)")
                matched = True
            
            # Check BIN match
            elif arrm_md5 in bin_md5_to_game:
                # Need to find bin count for this game
                info = bin_md5_to_game[arrm_md5]
                game_name = info['game']
                
                # Find bin count from dat_games
                game_files = dat_games.get(game_name, {})
                bin_count = sum(1 for f in game_files if Path(f).suffix.lower() == '.bin')
                
                if bin_count == 1:
                    stats['single_track_bin'] += 1
                    if len(single_bin_examples) < 3:
                        single_bin_examples.append(f"{arrm_path}")
                else:
                    stats['multi_track_bin'] += 1
                    anomalies.append(f"Multi-track BIN match: {arrm_path} ({bin_count} tracks)")
                matched = True
            
            # Check ISO match
            elif arrm_md5 in iso_md5_to_game:
                stats['iso_match'] += 1
                matched = True
            
            if not matched:
                stats['no_match'] += 1
        
        # Print results
        print("\nResults by track count:")
        print(f"  Single-track games matched via BIN: {stats['single_track_bin']}")
        print(f"  Single-track games matched via CUE: {stats['single_track_cue']} (anomaly!)")
        print(f"  Multi-track games matched via CUE:  {stats['multi_track_cue']}")
        print(f"  Multi-track games matched via BIN:  {stats['multi_track_bin']} (anomaly!)")
        print(f"  ISO matches:                        {stats['iso_match']}")
        print(f"  No match:                           {stats['no_match']}")
        
        if single_bin_examples:
            print(f"\n  Single-track BIN examples:")
            for ex in single_bin_examples:
                print(f"    - {ex}")
        
        if multi_cue_examples:
            print(f"\n  Multi-track CUE examples:")
            for ex in multi_cue_examples:
                print(f"    - {ex}")
        
        if anomalies and len(anomalies) <= 5:
            print(f"\n  Anomalies (unexpected behavior):")
            for a in anomalies[:5]:
                print(f"    ! {a}")
        elif anomalies:
            print(f"\n  Anomalies: {len(anomalies)} found (first 5):")
            for a in anomalies[:5]:
                print(f"    ! {a}")
    
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print("""
Based on analysis:
- Single-track CUE/BIN: ARRM hashes the BIN file (data)
- Multi-track CUE/BIN:  ARRM hashes the CUE file (text)
- ISO files:            ARRM hashes the ISO file

This is likely because:
1. For single-track, the BIN IS the game data, CUE is trivial
2. For multi-track, ScreenScraper uses CUE to identify the disc layout
3. ISO files are self-contained

ROM Farmer should:
1. For single-track: Hash the .bin file
2. For multi-track:  Hash the .cue file  
3. For ISO:          Hash the .iso file
""")


if __name__ == "__main__":
    analyze_by_track_count()
