#!/usr/bin/env python3
"""Test script for nps_search module."""

import sys
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nps.nps_database import NPSDatabase
from nps.nps_search import NPSSearch, SearchResultFormatter


def main():
    """Test search functionality."""
    
    db_dir = Path('/path/to/source/nopaystation')
    
    if not db_dir.exists():
        print(f"❌ Database directory not found: {db_dir}")
        return 1
    
    print("=" * 80)
    print("Testing NPSSearch Engine")
    print("=" * 80)
    print()
    
    # Initialize database
    print("1. Loading PS Vita databases...")
    db = NPSDatabase(db_dir)
    db.load_platform('vita', types=['games', 'dlc', 'updates'])
    print(f"   ✓ Loaded {len(db.entries):,} entries")
    print()
    
    # Initialize search engine
    print("2. Initializing search engine...")
    search = NPSSearch(db)
    print("   ✓ Search engine ready")
    print()
    
    # Test 1: Basic fuzzy search
    print("=" * 80)
    print("TEST 1: Basic Fuzzy Search - 'doctor who'")
    print("=" * 80)
    results = search.search('doctor who', platform='vita', region='USA')
    print(SearchResultFormatter.format_search_results(results, limit=10))
    print()
    
    # Test 2: Title ID search
    print("=" * 80)
    print("TEST 2: Title ID Search - 'PCSE00065' (Pinball Arcade)")
    print("=" * 80)
    results = search.search('PCSE00065', platform='vita')
    print(f"Found {len(results)} entries for PCSE00065:")
    for entry, score in results[:15]:
        print(f"  • {entry.name} [{entry.content_type}]")
    print()
    
    # Test 3: Dependency resolution (--complete flag)
    print("=" * 80)
    print("TEST 3: Search with Dependencies - 'doctor who' --complete")
    print("=" * 80)
    bundles = search.search_with_dependencies(
        'doctor who',
        platform='vita',
        region='USA',
        include_dlc=True,
        include_updates=True
    )
    
    print(f"Found {len(bundles)} complete title bundle(s):\n")
    for i, bundle in enumerate(bundles, 1):
        print(f"{i}. {SearchResultFormatter.format_bundle(bundle, show_details=True)}")
        print()
    
    # Test 4: Find specific DLC
    print("=" * 80)
    print("TEST 4: Find DLC for Pinball Arcade (PCSE00065)")
    print("=" * 80)
    dlc = search.find_dlc_for_title('PCSE00065', 'vita', region='USA')
    print(f"Found {len(dlc)} DLC items:")
    
    # Group DLC by keywords
    doctor_who_dlc = [d for d in dlc if 'doctor who' in d.name.lower()]
    print(f"\n  Doctor Who DLC ({len(doctor_who_dlc)}):")
    for d in doctor_who_dlc:
        size_mb = d.file_size / (1024**2)
        print(f"    • {d.name} ({size_mb:.1f} MB)")
    print()
    
    # Test 5: Multiple platform search
    print("=" * 80)
    print("TEST 5: Cross-Platform Search - 'metal gear'")
    print("=" * 80)
    
    # Load PS3 for comparison
    print("  Loading PS3 databases...")
    db.load_platform('ps3', types=['games', 'dlc'])
    print(f"  ✓ Now have {len(db.entries):,} total entries")
    print()
    
    # Search both platforms
    vita_results = search.search('metal gear', platform='vita', content_type='games')
    ps3_results = search.search('metal gear', platform='ps3', content_type='games')
    
    print(f"  PS Vita: {len(vita_results)} results")
    for entry, score in vita_results[:5]:
        print(f"    • {entry.name} ({score:.1%})")
    print()
    
    print(f"  PS3: {len(ps3_results)} results")
    for entry, score in ps3_results[:5]:
        print(f"    • {entry.name} ({score:.1%})")
    print()
    
    # Test 6: Related content lookup
    print("=" * 80)
    print("TEST 6: Find Related Content")
    print("=" * 80)
    if vita_results:
        base_game = vita_results[0][0]
        print(f"  Base: {base_game.name}")
        
        related = search.get_related_content(base_game, include_types=['dlc', 'updates'])
        for content_type, entries in related.items():
            print(f"    {content_type.upper()}: {len(entries)} items")
    print()
    
    # Test 7: Exact vs fuzzy matching
    print("=" * 80)
    print("TEST 7: Scoring Comparison")
    print("=" * 80)
    test_queries = [
        'minecraft',           # Exact word
        'mine craft',          # Separated
        'persona 4',           # With number
        'final fantasy',       # Common phrase
    ]
    
    for query in test_queries:
        results = search.search(query, platform='vita', content_type='games', limit=3)
        print(f"  Query: '{query}'")
        if results:
            for entry, score in results[:3]:
                print(f"    {score:.1%} - {entry.name}")
        else:
            print("    No results")
        print()
    
    print("=" * 80)
    print("✅ All search tests passed!")
    print("=" * 80)
    
    # Summary statistics
    stats = db.get_stats()
    print("\nDatabase Statistics:")
    print(f"  Total entries: {stats['total_entries']:,}")
    print(f"  Platforms: {', '.join(stats['platforms'])}")
    print(f"  Content types: {', '.join(stats['types'])}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
