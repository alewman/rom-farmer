#!/usr/bin/env python3
"""
Test ScreenScraper with transformation tracking hashes.

This validates that our BIN (Track 1) hash approach works with ScreenScraper.

You need ScreenScraper credentials:
1. Register at https://www.screenscraper.fr/
2. Get dev credentials from forums
3. Set environment variables or edit this file
"""

import os
import sys
from pathlib import Path

try:
    from pyscreenscraper import ScreenScraperClient, exceptions
except ImportError:
    print("Error: pyscreenscraper not installed")
    print("Install with: pip install git+https://github.com/rhlobo/pyscreenscraper.git")
    sys.exit(1)


# ScreenScraper credentials
DEV_ID = os.environ.get("SS_DEV_ID", "")
DEV_PASSWORD = os.environ.get("SS_DEV_PASSWORD", "")
USER_ID = os.environ.get("SS_USER_ID", "")
USER_PASSWORD = os.environ.get("SS_USER_PASSWORD", "")

# Test hashes for "3D Baseball (USA)" - Sega Saturn
TEST_HASHES = {
    "chd": "497af1102b63d9d148e4ba4d119fb64e",  # Your CHD file
    "bin": "5f33157efd8a73de6612a852cf1ba147",  # BIN Track 1 from Redump
    "cue": "4d9347b77d53c8f366f787cc9ba5ef9a",  # CUE from Redump
}

SATURN_SYSTEM_ID = 22  # ScreenScraper system ID for Sega Saturn


def test_hash(client, hash_value, hash_type, game_name):
    """Test a single hash with ScreenScraper."""
    print(f"\n{'='*80}")
    print(f"Testing {hash_type.upper()} hash")
    print(f"MD5: {hash_value}")
    print(f"{'='*80}")
    
    try:
        # Search by MD5 hash
        game = client.search_game(
            system_id=SATURN_SYSTEM_ID,
            md5=hash_value,
            rom_name=game_name
        )
        
        print(f"✅ SUCCESS! Found game:")
        print(f"   Name: {game.nom}")
        print(f"   System: {game.system.text}")
        print(f"   Region: {game.region}")
        print(f"   Publisher: {game.editeur.text if game.editeur else 'N/A'}")
        print(f"   Release: {game.date}")
        
        # Show available media
        if game.medias:
            print(f"\n   Available media types:")
            media_types = set(m.type for m in game.medias)
            for media_type in sorted(media_types):
                count = len([m for m in game.medias if m.type == media_type])
                print(f"     - {media_type}: {count}")
        
        return True
        
    except exceptions.GameNotFoundError:
        print(f"❌ NOT FOUND: Game not in ScreenScraper database")
        return False
    except exceptions.AuthenticationError as e:
        print(f"❌ AUTH ERROR: {e}")
        print("   Check your credentials!")
        return False
    except exceptions.QuotaExceededError:
        print(f"❌ QUOTA EXCEEDED: API limit reached, wait 24h")
        return False
    except exceptions.ServerLoadError as e:
        print(f"⚠️  SERVER BUSY: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║          ScreenScraper Transformation Tracking Validation                  ║
╚════════════════════════════════════════════════════════════════════════════╝

Test Case: "3D Baseball (USA)" - Sega Saturn

We'll test three different hashes:
1. CHD hash  (497af110...) - Your converted file (probably unknown to SS)
2. BIN hash  (5f33157e...) - Redump Track 1 (should work!) ⭐
3. CUE hash  (4d9347b7...) - Redump CUE file (might work)

This validates our transformation tracking approach:
  Your CHD → Lookup transformation → Get BIN hash → Query ScreenScraper
""")
    
    # Check credentials
    if not all([DEV_ID, DEV_PASSWORD, USER_ID, USER_PASSWORD]):
        print("⚠️  ScreenScraper credentials not configured!")
        print("\nSet environment variables:")
        print("  export SS_DEV_ID='your_dev_id'")
        print("  export SS_DEV_PASSWORD='your_dev_password'")
        print("  export SS_USER_ID='your_username'")
        print("  export SS_USER_PASSWORD='your_password'")
        print("\nGet credentials from:")
        print("  - Register: https://www.screenscraper.fr/")
        print("  - Dev creds: https://www.screenscraper.fr/forumacces.php?zone=6")
        sys.exit(1)
    
    # Initialize client
    print(f"Initializing ScreenScraper client...")
    client = ScreenScraperClient(
        dev_id=DEV_ID,
        dev_password=DEV_PASSWORD,
        software_name="romgroomer-test",
        user_id=USER_ID,
        user_password=USER_PASSWORD
    )
    print(f"✓ Client initialized\n")
    
    # Test all three hashes
    results = {}
    
    print("\n" + "█"*80)
    print("TEST 1: Direct CHD Hash (Your converted file)")
    print("█"*80)
    print("Expected: ❌ NOT FOUND (ScreenScraper doesn't know your specific CHD)")
    results['chd'] = test_hash(client, TEST_HASHES['chd'], 'CHD', '3D Baseball (USA)')
    
    print("\n" + "█"*80)
    print("TEST 2: BIN (Track 1) Hash from Transformation Tracking")
    print("█"*80)
    print("Expected: ✅ FOUND (This is the Redump hash ScreenScraper knows)")
    results['bin'] = test_hash(client, TEST_HASHES['bin'], 'BIN Track 1', '3D Baseball (USA)')
    
    print("\n" + "█"*80)
    print("TEST 3: CUE File Hash from Redump DAT")
    print("█"*80)
    print("Expected: ❓ MAYBE (Depends on ScreenScraper's indexing)")
    results['cue'] = test_hash(client, TEST_HASHES['cue'], 'CUE', '3D Baseball (USA)')
    
    # Summary
    print("\n\n" + "╔" + "═"*78 + "╗")
    print("║" + " "*30 + "FINAL RESULTS" + " "*35 + "║")
    print("╚" + "═"*78 + "╝")
    print(f"\nDirect CHD Hash:          {'✅ FOUND' if results.get('chd') else '❌ NOT FOUND'}")
    print(f"BIN Track 1 Hash:         {'✅ FOUND' if results.get('bin') else '❌ NOT FOUND'} ← Transform approach")
    print(f"CUE Hash:                 {'✅ FOUND' if results.get('cue') else '❌ NOT FOUND'}")
    
    print("\n" + "="*80)
    if results.get('bin'):
        print("✅ SUCCESS! Transformation tracking approach VALIDATED!")
        print("\nThe strategy works:")
        print("  1. Your CHD → Look up transformation in database")
        print("  2. Get BIN (Track 1) hash: 5f33157efd8a73de6612a852cf1ba147")
        print("  3. Query ScreenScraper with BIN hash")
        print("  4. ✅ Game found and metadata retrieved!")
        print("\nThis proves we can scrape metadata for converted ROMs!")
    else:
        print("⚠️  BIN hash lookup failed. Possible reasons:")
        print("  - Authentication issues")
        print("  - Rate limiting / quota exceeded")
        print("  - Server load too high")
        print("  - Game not in ScreenScraper database (unlikely for popular game)")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
