#!/usr/bin/env python3
"""Test Sony PSN update integration with Borderlands 2."""

from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from romgroomer.stages.apply_ps3_updates import SonyPSNClient

def main():
    """Test Sony PSN client."""
    print("=" * 70)
    print("Testing Sony PSN Update Integration")
    print("=" * 70)
    
    client = SonyPSNClient()
    
    # Test with Borderlands 2
    title_id = "BLUS30982"
    print(f"\nQuerying updates for: {title_id} (Borderlands 2)")
    print("-" * 70)
    
    updates = client.get_updates_for_title(title_id)
    
    if not updates:
        print("❌ No updates found!")
        return 1
    
    print(f"\n✓ Found {len(updates)} update(s):\n")
    
    for i, update in enumerate(updates, 1):
        print(f"Update {i}:")
        print(f"  Name: {update.get('Name', 'Unknown')}")
        print(f"  Title ID: {update.get('Title ID', 'Unknown')}")
        print(f"  Version: {update.get('Version', 'Unknown')}")
        print(f"  Size: {update.get('File Size', 'Unknown')}")
        print(f"  SHA1: {update.get('SHA1', 'Unknown')}")
        print(f"  PKG URL: {update.get('PKG direct link', 'Unknown')}")
        print(f"  RAP: {update.get('RAP', 'Unknown')}")
        print(f"  Source: {update.get('Source', 'Unknown')}")
        print()
    
    print("=" * 70)
    print("✓ Sony PSN integration test PASSED!")
    print("=" * 70)
    return 0

if __name__ == '__main__':
    sys.exit(main())
