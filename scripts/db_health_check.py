#!/usr/bin/env python3
"""
Database Health Check and Safety Warning Tool

Run this before any database operations to see what data exists
and prevent accidental data loss.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.romfarmer.metadata.database import MetadataDatabase, ScrapedGame
from src.romfarmer.metadata.transformation import ROMTransformation


def check_database_health():
    """Check database contents and warn about destructive operations."""
    
    # Use project database (workspace-relative)
    db_path = Path(__file__).parent.parent / 'metadata/database/romfarmer.db'
    
    if not db_path.exists():
        print(f"⚠️  Database does not exist: {db_path}")
        print(f"   It will be created on first use.")
        return
    
    print(f"📊 Database Health Check")
    print(f"   Location: {db_path}")
    print(f"   Size: {db_path.stat().st_size / 1024:.1f} KB")
    print()
    
    db = MetadataDatabase(db_path)
    session = db.get_session()
    
    try:
        # Check scraped games
        total_games = session.query(ScrapedGame).count()
        print(f"🎮 Scraped Games: {total_games:,}")
        
        if total_games > 0:
            systems = session.query(ScrapedGame.system).distinct().all()
            print(f"   Systems:")
            for system in sorted(systems):
                count = session.query(ScrapedGame).filter_by(system=system[0]).count()
                
                # Check how many have MD5s
                with_md5 = session.query(ScrapedGame).filter(
                    ScrapedGame.system == system[0],
                    ScrapedGame.md5.isnot(None),
                    ScrapedGame.md5 != ''
                ).count()
                
                md5_percent = (with_md5 / count * 100) if count > 0 else 0
                print(f"     • {system[0]}: {count:,} games ({with_md5:,} with MD5 - {md5_percent:.1f}%)")
        
        print()
        
        # Check transformations
        total_trans = session.query(ROMTransformation).count()
        print(f"🔄 ROM Transformations: {total_trans:,}")
        
        if total_trans > 0:
            # Check linked vs unlinked
            linked = session.query(ROMTransformation).filter(
                ROMTransformation.game_id.isnot(None)
            ).count()
            unlinked = total_trans - linked
            linked_percent = (linked / total_trans * 100) if total_trans > 0 else 0
            
            print(f"   • Linked to games: {linked:,} ({linked_percent:.1f}%)")
            print(f"   • Unlinked: {unlinked:,} ({100-linked_percent:.1f}%)")
            
            # Show formats
            print(f"   • Formats:")
            formats = session.query(
                ROMTransformation.source_format,
                ROMTransformation.final_format
            ).distinct().all()
            
            for src, dst in formats:
                count = session.query(ROMTransformation).filter(
                    ROMTransformation.source_format == src,
                    ROMTransformation.final_format == dst
                ).count()
                print(f"     • {src or '?'} → {dst or '?'}: {count:,}")
        
        print()
        print("=" * 60)
        print()
        print("⚠️  WARNING: Database operations can be destructive!")
        print()
        print("   SAFE operations:")
        print("     • Adding new games (import/scrape)")
        print("     • Adding new transformations (builds)")
        print("     • Querying data")
        print()
        print("   DESTRUCTIVE operations:")
        print("     • DELETE queries")
        print("     • DROP TABLE")
        print("     • Deleting database file")
        print("     • Overwriting with fresh schema")
        print()
        print(f"   💾 Always backup before destructive operations:")
        print(f"      cp {db_path} {db_path}.backup")
        print()
        
    finally:
        session.close()


if __name__ == "__main__":
    check_database_health()
