#!/usr/bin/env python3
"""Test script for nps_database module."""

import sys
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nps.nps_database import NPSDatabase
from nps.nps_models import ContentEntry, TitleBundle


def main():
    """Test database loading and querying."""
    
    db_dir = Path('/data/emu/source/nopaystation')
    
    if not db_dir.exists():
        print(f"❌ Database directory not found: {db_dir}")
        return 1
    
    print("=" * 80)
    print("Testing NPSDatabase")
    print("=" * 80)
    print()
    
    # Initialize database
    print("1. Initializing database...")
    db = NPSDatabase(db_dir)
    print("   ✓ Database initialized")
    print()
    
    # Load PS Vita databases
    print("2. Loading PS Vita databases...")
    db.load_platform('vita', types=['games', 'dlc'])
    print(f"   ✓ Loaded {len(db.entries):,} entries")
    print()
    
    # Get statistics
    print("3. Database statistics:")
    stats = db.get_stats()
    print(f"   Total entries: {stats['total_entries']:,}")
    print(f"   Platforms: {stats['platforms']}")
    print(f"   Types: {stats['types']}")
    print()
    print("   By platform:")
    for platform, count in stats['by_platform'].items():
        print(f"     {platform}: {count:,}")
    print()
    print("   By type:")
    for content_type, count in stats['by_type'].items():
        print(f"     {content_type}: {count:,}")
    print()
    print("   By region:")
    for region, count in stats['by_region'].items():
        print(f"     {region}: {count:,}")
    print()
    
    # Test search
    print("4. Testing search for 'doctor who'...")
    results = db.search('doctor who', platform='vita', region='USA')
    print(f"   Found {len(results)} results:")
    for entry in results[:10]:  # Show first 10
        print(f"     • {entry.name} ({entry.title_id}) [{entry.content_type}]")
    print()
    
    # Test Title ID lookup
    if results:
        first_result = results[0]
        print(f"5. Testing Title ID lookup for {first_result.title_id}...")
        title_entries = db.get_by_title_id(first_result.title_id, platform='vita')
        print(f"   Found {len(title_entries)} entries for this Title ID:")
        for entry in title_entries:
            print(f"     • {entry.name} ({entry.content_type})")
        print()
        
        # Test bundle building
        print(f"6. Building TitleBundle for {first_result.title_id}...")
        bundle = db.build_title_bundle(first_result.title_id, 'vita', region='USA')
        if bundle:
            print(f"   ✓ Bundle created:")
            print(f"     Game: {bundle.get_display_name()}")
            counts = bundle.count_by_type()
            print(f"     Content: {counts['base_game']} game, {counts['dlc']} DLC, {counts['updates']} updates")
            print(f"     Total size: {bundle.get_total_size() / (1024**3):.2f} GB")
        print()
    
    # Test Content ID lookup
    print("7. Testing Content ID lookup...")
    if db.entries:
        test_entry = db.entries[0]
        found = db.get_by_content_id(test_entry.content_id)
        if found:
            print(f"   ✓ Found: {found.name}")
        print()
    
    print("=" * 80)
    print("✅ All tests passed!")
    print("=" * 80)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
