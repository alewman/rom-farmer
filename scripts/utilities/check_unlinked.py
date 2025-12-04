#!/usr/bin/env python3
"""Find unlinked transformations and check if games exist in ARRM database."""

import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from romfarmer.metadata.database import ScrapedGame
from romfarmer.tracking.database import ROMTransformation

def main():
    # Connect to database
    db_path = Path.home() / '.local/share/romfarmer/scraped_games.db'
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Find unlinked transformations
    print("Finding unlinked transformations...")
    unlinked = session.query(ROMTransformation).filter(
        ROMTransformation.game_id == None,
        ROMTransformation.source_file_name.like('%.cue')
    ).limit(5).all()
    
    print(f"Found {len(unlinked)} unlinked transformations (showing first 5)")
    print("\nThese are games where transformation couldn't link to ARRM database:\n")
    print("=" * 80)
    
    for i, trans in enumerate(unlinked, 1):
        # Get the game name from filename
        game_name = trans.source_file_name.replace('.cue', '')
        
        print(f"\n{i}. {game_name}")
        print(f"   Source MD5: {trans.source_md5}")
        
        # Check if a game exists with this MD5
        game = session.query(ScrapedGame).filter(
            ScrapedGame.system == 'saturn',
            ScrapedGame.md5 == trans.source_md5
        ).first()
        
        if game:
            print(f"   ✅ Game DOES exist in DB: {game.name}")
            print(f"      (This means MD5s match but linking failed)")
        else:
            print(f"   ❌ Game NOT in ARRM database with this MD5")
            print(f"      (ARRM has different MD5 for this game)")
    
    session.close()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
