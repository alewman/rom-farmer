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


# Load credentials from .env file if it exists
def load_env():
    """Load credentials from .env file."""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip().replace('.', '_').upper()
                    if key.startswith('SS_'):
                        os.environ[key] = value.strip()

load_env()

# ScreenScraper credentials
DEV_ID = os.environ.get("SS_DEV_ID", "")
DEV_PASSWORD = os.environ.get("SS_DEV_PASSWORD", "")
USER_ID = os.environ.get("SS_USERNAME", "")
USER_PASSWORD = os.environ.get("SS_PASSWORD", "")

# Test Case 1: "3D Baseball (USA)" - Niche game, CUE should work best
# Based on actual ScreenScraper database contents (verified 2025-10-12)
TEST_HASHES_3D_BASEBALL = {
    "chd_yours": "497af1102b63d9d148e4ba4d119fb64e",  # Your CHD (unknown to SS)
    "chd_ss": "CC5F238DADB317016D76C378565CA099",     # SS's CHD (4,289 scrapes!)
    "cue": "4d9347b77d53c8f366f787cc9ba5ef9a",        # CUE from Redump (1,558 scrapes!)
    "bin_full": "3bb15f208c412e96db79f96c0afcbf1e",   # Full BIN in SS (261 scrapes)
    "bin_track1": "5f33157efd8a73de6612a852cf1ba147", # Redump Track 1 (probably not in SS)
}

# Test Case 2: "NiGHTS into Dreams (USA)" - Popular game, CHD should work best
TEST_HASHES_NIGHTS = {
    "chd_ss": "64C17D52D788EC6F1ABE7993091F3CC3",     # SS's CHD (110,857 scrapes!) 🔥
    "chd_variant": "31D4BF7144AECA3C918154FEB5FFF059", # Variant (163 scrapes)
    "cue_usa": "09e69b286cb01c4ccd4b275dfed8b32b",   # USA CUE (13 scrapes only!)
    "cue_eur": "8e9e5262b6283230b42643a37e6ffd50",   # EUR CUE (4,120 scrapes)
    "img": "3ce46d1e3fda8191560b5562182dad72",       # IMG (34 scrapes)
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

Based on ACTUAL ScreenScraper database contents (verified 2025-10-12):

We'll test FIVE different hashes:
1. Your CHD       (497af110...) - Unknown to SS (expected: ❌)
2. SS's known CHD (CC5F238D...) - 4,289 scrapes (expected: ✅)  
3. CUE hash       (4d9347b7...) - 1,558 scrapes (expected: ✅) ⭐ BEST!
4. Full BIN hash  (3bb15f20...) - 261 scrapes (expected: ✅)
5. BIN Track 1    (5f33157e...) - Redump only (expected: ❌)

This validates our transformation tracking approach:
  Your CHD → Lookup transformation → Get CUE hash → Query ScreenScraper ✅
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
        software_name="romfarmer-test",
        user_id=USER_ID,
        user_password=USER_PASSWORD
    )
    print(f"✓ Client initialized\n")
    
    # Test all five hashes
    results = {}
    
    print("\n" + "█"*80)
    print("TEST 1: Your CHD Hash")
    print("█"*80)
    print("Expected: ❌ NOT FOUND (Different conversion than what SS has)")
    results['chd_yours'] = test_hash(client, TEST_HASHES['chd_yours'], 'Your CHD', '3D Baseball (USA)')
    
    print("\n" + "█"*80)
    print("TEST 2: ScreenScraper's Known CHD Hash")
    print("█"*80)
    print("Expected: ✅ FOUND (SS has this exact CHD - 4,289 scrapes!)")
    results['chd_ss'] = test_hash(client, TEST_HASHES['chd_ss'], 'SS CHD', '3D Baseball (USA)')
    
    print("\n" + "█"*80)
    print("TEST 3: CUE File Hash from Transformation Tracking")
    print("█"*80)
    print("Expected: ✅ FOUND (1,558 scrapes - BEST approach!) ⭐")
    results['cue'] = test_hash(client, TEST_HASHES['cue'], 'CUE', '3D Baseball (USA)')
    
    print("\n" + "█"*80)
    print("TEST 4: Full BIN Hash (All Tracks)")
    print("█"*80)
    print("Expected: ✅ FOUND (SS has full BIN - 261 scrapes)")
    results['bin_full'] = test_hash(client, TEST_HASHES['bin_full'], 'Full BIN', '3D Baseball (USA)')
    
    print("\n" + "█"*80)
    print("TEST 5: BIN Track 1 Only (Redump)")
    print("█"*80)
    print("Expected: ❌ NOT FOUND (Redump Track 1 not in SS database)")
    results['bin_track1'] = test_hash(client, TEST_HASHES['bin_track1'], 'BIN Track 1', '3D Baseball (USA)')
    
    # Summary
    print("\n\n" + "╔" + "═"*78 + "╗")
    print("║" + " "*30 + "FINAL RESULTS" + " "*35 + "║")
    print("╚" + "═"*78 + "╝")
    print(f"\nYour CHD Hash:            {'✅ FOUND' if results.get('chd_yours') else '❌ NOT FOUND'}")
    print(f"ScreenScraper's CHD:      {'✅ FOUND' if results.get('chd_ss') else '❌ NOT FOUND'}")
    print(f"CUE Hash:                 {'✅ FOUND' if results.get('cue') else '❌ NOT FOUND'} ← Transform approach ⭐")
    print(f"Full BIN Hash:            {'✅ FOUND' if results.get('bin_full') else '❌ NOT FOUND'}")
    print(f"BIN Track 1 Hash:         {'✅ FOUND' if results.get('bin_track1') else '❌ NOT FOUND'}")
    
    print("\n" + "="*80)
    if results.get('cue'):
        print("✅ SUCCESS! CUE-based transformation tracking VALIDATED!")
        print("\nThe strategy works:")
        print("  1. Your CHD → Look up transformation in database")
        print("  2. Get CUE hash: 4d9347b77d53c8f366f787cc9ba5ef9a")
        print("  3. Query ScreenScraper with CUE hash")
        print("  4. ✅ Game found and metadata retrieved!")
        print("\nThis proves we can scrape metadata for converted ROMs!")
        print("\n💡 Key Discovery:")
        print("   - CUE hashes work best (1,558 scrapes in SS)")
        print("   - BIN Track 1 from Redump NOT what SS uses")
        print("   - SS uses full BIN or CUE for disc-based games")
    else:
        print("⚠️  CUE hash lookup failed. Possible reasons:")
        print("  - Authentication issues")
        print("  - Rate limiting / quota exceeded")
        print("  - Server load too high")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
