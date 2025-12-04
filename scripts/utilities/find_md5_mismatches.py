#!/usr/bin/env python3
"""Find games where DAT MD5 doesn't match ARRM's scraped database MD5."""

import sys
from pathlib import Path
import xml.etree.ElementTree as ET
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from romfarmer.db.metadata import ScrapedGame

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
    db_path = Path.home() / '.local/share/romfarmer/scraped_games.db'
    
    # Find Saturn DAT file
    dat_files = list(dat_dir.glob('Sega - Saturn*.dat'))
    if not dat_files:
        print("❌ No Saturn DAT file found!")
        return 1
    
    dat_path = dat_files[0]
    print(f"📄 DAT file: {dat_path.name}")
    print(f"💾 Database: {db_path}")
    print()
    
    # Parse DAT
    print("Parsing DAT file...")
    dat_md5s = parse_dat_file(dat_path)
    print(f"  Found {len(dat_md5s)} games with MD5s in DAT")
    print()
    
    # Connect to database
    print("Connecting to database...")
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Get Saturn games from database
    print("Querying Saturn games from ARRM database...")
    db_games = session.query(ScrapedGame).filter_by(system='saturn').all()
    print(f"  Found {len(db_games)} Saturn games in database")
    print()
    
    # Compare MD5s
    print("Comparing MD5s...")
    mismatches = []
    
    for db_game in db_games:
        # Try to match by name (remove file extensions, normalize)
        db_name = db_game.name
        
        # Check if this game is in our DAT (by exact name match)
        for dat_name, dat_md5 in dat_md5s.items():
            # Simple name matching - could be more sophisticated
            if dat_name in db_name or db_name in dat_name:
                if db_game.md5 and db_game.md5.lower() != dat_md5:
                    mismatches.append({
                        'dat_name': dat_name,
                        'db_name': db_name,
                        'dat_md5': dat_md5,
                        'db_md5': db_game.md5.lower(),
                        'db_id': db_game.id
                    })
                break
    
    session.close()
    
    # Results
    print()
    print("=" * 80)
    print("MD5 MISMATCHES")
    print("=" * 80)
    print()
    print(f"Found {len(mismatches)} games where ARRM's MD5 doesn't match DAT")
    print()
    
    if mismatches:
        print("First 5 mismatched games for testing:")
        print("-" * 80)
        for i, mismatch in enumerate(mismatches[:5], 1):
            print(f"\n{i}. {mismatch['dat_name']}")
            print(f"   Database name: {mismatch['db_name']}")
            print(f"   DAT MD5:  {mismatch['dat_md5']}")
            print(f"   ARRM MD5: {mismatch['db_md5']}")
            print(f"   Game ID:  {mismatch['db_id']}")
    else:
        print("✅ No mismatches found! All MD5s match between DAT and ARRM database.")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
