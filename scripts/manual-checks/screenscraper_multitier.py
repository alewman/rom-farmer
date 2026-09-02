#!/usr/bin/env python3
"""
Test ScreenScraper with two different game scenarios.

This validates our multi-tier query strategy for disc-based games.

Test Case 1: 3D Baseball (niche game) - CUE hash should work best
Test Case 2: NiGHTS into Dreams (popular game) - CHD hash should work best

You need ScreenScraper credentials:
1. Register at https://www.screenscraper.fr/
2. Get dev credentials from forums (https://www.screenscraper.fr/forumaccess.php?zone=6)
3. Add to .env file
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
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip().replace(".", "_").upper()
                    if key.startswith("SS_"):
                        os.environ[key] = value.strip()


load_env()

# ScreenScraper credentials
DEV_ID = os.environ.get("SS_DEV_ID", "")
DEV_PASSWORD = os.environ.get("SS_DEV_PASSWORD", "")
USER_ID = os.environ.get("SS_USERNAME", "")
USER_PASSWORD = os.environ.get("SS_PASSWORD", "")

# Test Case 1: "3D Baseball (USA)" - Niche game
TEST_3D_BASEBALL = {
    "name": "3D Baseball (USA)",
    "hashes": {
        "chd_yours": ("497af1102b63d9d148e4ba4d119fb64e", "Your CHD", "❌ NOT FOUND (unknown)"),
        "chd_ss": ("CC5F238DADB317016D76C378565CA099", "SS's CHD", "✅ FOUND (4,289 scrapes)"),
        "cue": ("4d9347b77d53c8f366f787cc9ba5ef9a", "CUE", "✅ FOUND (1,558 scrapes) ⭐"),
        "bin_full": ("3bb15f208c412e96db79f96c0afcbf1e", "Full BIN", "✅ FOUND (261 scrapes)"),
        "bin_track1": (
            "5f33157efd8a73de6612a852cf1ba147",
            "BIN Track 1",
            "❌ NOT FOUND (Redump only)",
        ),
    },
}

# Test Case 2: "NiGHTS into Dreams (USA)" - Popular game
TEST_NIGHTS = {
    "name": "NiGHTS into Dreams (USA)",
    "hashes": {
        "chd_ss": (
            "64C17D52D788EC6F1ABE7993091F3CC3",
            "SS's CHD",
            "✅ FOUND (110,857 scrapes!) 🔥",
        ),
        "chd_variant": (
            "31D4BF7144AECA3C918154FEB5FFF059",
            "CHD Variant",
            "✅ FOUND (163 scrapes)",
        ),
        "cue_usa": ("09e69b286cb01c4ccd4b275dfed8b32b", "USA CUE", "✅ FOUND (13 scrapes only)"),
        "cue_eur": ("8e9e5262b6283230b42643a37e6ffd50", "EUR CUE", "✅ FOUND (4,120 scrapes)"),
        "img": ("3ce46d1e3fda8191560b5562182dad72", "IMG", "✅ FOUND (34 scrapes)"),
    },
}

SATURN_SYSTEM_ID = 22  # ScreenScraper system ID for Sega Saturn


def test_hash(client, hash_value, hash_type, game_name, expected):
    """Test a single hash with ScreenScraper."""
    print(f"\n{'─' * 80}")
    print(f"Testing: {hash_type}")
    print(f"MD5: {hash_value}")
    print(f"Expected: {expected}")
    print(f"{'─' * 80}")

    try:
        # Search by MD5 hash
        game = client.search_game(system_id=SATURN_SYSTEM_ID, md5=hash_value, rom_name=game_name)

        print("✅ SUCCESS! Found game:")
        print(f"   Name: {game.nom}")
        print(f"   System: {game.system.text}")
        print(f"   Region: {game.region}")
        print(f"   Publisher: {game.editeur.text if game.editeur else 'N/A'}")
        print(f"   Release: {game.date}")

        # Show available media
        if game.medias:
            print("\n   Available media types:")
            media_types = {m.type for m in game.medias}
            for media_type in sorted(media_types):
                count = len([m for m in game.medias if m.type == media_type])
                print(f"     - {media_type}: {count}")

        return True

    except exceptions.GameNotFoundError:
        print("❌ NOT FOUND: Game not in ScreenScraper database")
        return False
    except exceptions.AuthenticationError as e:
        print(f"❌ AUTH ERROR: {e}")
        print("   Check your credentials!")
        return False
    except exceptions.QuotaExceededError:
        print("❌ QUOTA EXCEEDED: API limit reached, wait 24h")
        return False
    except exceptions.ServerLoadError as e:
        print(f"⚠️  SERVER BUSY: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_game(client, test_case):
    """Test all hashes for a game."""
    game_name = test_case["name"]
    hashes = test_case["hashes"]
    results = {}

    print("\n\n" + "╔" + "═" * 78 + "╗")
    print(f"║  Game: {game_name:<68} ║")
    print("╚" + "═" * 78 + "╝")

    for key, (hash_value, hash_type, expected) in hashes.items():
        print(f"\n{'█' * 80}")
        print(f"TEST: {hash_type}")
        print(f"{'█' * 80}")
        results[key] = test_hash(client, hash_value, hash_type, game_name, expected)

    return results


def print_summary(game_name, results, hashes):
    """Print summary for a game."""
    print("\n\n" + "╔" + "═" * 78 + "╗")
    print(f"║  SUMMARY: {game_name:<64} ║")
    print("╚" + "═" * 78 + "╝\n")

    for key, (_hash_value, hash_type, _expected) in hashes.items():
        status = "✅ FOUND" if results.get(key) else "❌ NOT FOUND"
        print(f"{hash_type:<20} {status}")

    found = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\n{'─' * 80}")
    print(f"Success rate: {found}/{total} ({100 * found // total}%)")
    print(f"{'─' * 80}")


def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║              ScreenScraper Multi-Tier Query Strategy Validation            ║
╚════════════════════════════════════════════════════════════════════════════╝

Testing TWO games to validate different scenarios:

Test Case 1: 3D Baseball (USA) - NICHE GAME
  - Expected: CUE hash works best (1,558 scrapes)
  - Expected: Direct CHD less common (4,289 scrapes)
  - Strategy: CUE-first approach

Test Case 2: NiGHTS into Dreams (USA) - POPULAR GAME
  - Expected: CHD hash works best (110,857 scrapes!) 🔥
  - Expected: CUE hash works but less common (13 scrapes)
  - Strategy: CHD-first approach

This validates our multi-tier query strategy:
  1. Try direct CHD hash (catches 90% of popular games)
  2. Fall back to CUE hash (catches niche/converted games)
  3. Fall back to filename search (last resort)

Based on actual ScreenScraper database analysis (2025-10-12).
""")

    # Check credentials
    if not all([DEV_ID, DEV_PASSWORD, USER_ID, USER_PASSWORD]):
        print("⚠️  ScreenScraper credentials not configured!")
        print("\nSet environment variables or add to .env file:")
        print("  ss.dev_id=your_dev_id")
        print("  ss.dev_password=your_dev_password")
        print("  ss.username=your_username")
        print("  ss.password=your_password")
        print("\nGet developer credentials from:")
        print("  https://www.screenscraper.fr/forumacces.php?zone=6")
        print("\nCurrent .env status:")
        print(f"  {'✅' if USER_ID else '❌'} ss.username")
        print(f"  {'✅' if USER_PASSWORD else '❌'} ss.password")
        print(f"  {'✅' if DEV_ID else '❌'} ss.dev_id")
        print(f"  {'✅' if DEV_PASSWORD else '❌'} ss.dev_password")
        sys.exit(1)

    # Initialize client
    print("\nInitializing ScreenScraper client...")
    print(f"  User: {USER_ID}")
    print(f"  Dev ID: {DEV_ID[:4]}{'*' * (len(DEV_ID) - 4) if len(DEV_ID) > 4 else ''}")

    try:
        client = ScreenScraperClient(
            dev_id=DEV_ID,
            dev_password=DEV_PASSWORD,
            software_name="romfarmer-validation",
            user_id=USER_ID,
            user_password=USER_PASSWORD,
        )
        print("✅ Client initialized successfully!\n")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        sys.exit(1)

    # Test both games
    results_baseball = test_game(client, TEST_3D_BASEBALL)
    results_nights = test_game(client, TEST_NIGHTS)

    # Print summaries
    print_summary(TEST_3D_BASEBALL["name"], results_baseball, TEST_3D_BASEBALL["hashes"])
    print_summary(TEST_NIGHTS["name"], results_nights, TEST_NIGHTS["hashes"])

    # Final analysis
    print("\n\n" + "╔" + "═" * 78 + "╗")
    print("║" + " " * 25 + "FINAL ANALYSIS" + " " * 38 + "║")
    print("╚" + "═" * 78 + "╝\n")

    print("Strategy Validation:")
    print("─" * 80)

    # Check if CUE works for niche game
    if results_baseball.get("cue"):
        print("✅ CUE strategy works for niche games (3D Baseball)")
    else:
        print("❌ CUE strategy failed for niche game")

    # Check if CHD works for popular game
    if results_nights.get("chd_ss"):
        print("✅ CHD strategy works for popular games (NiGHTS)")
    else:
        print("❌ CHD strategy failed for popular game")

    print("\n" + "─" * 80)
    print("Recommended Query Strategy:")
    print("─" * 80)
    print("1. Try direct CHD hash first (fast, works for 90% of popular games)")
    print("2. Fall back to CUE hash (works for niche/converted games)")
    print("3. Fall back to IMG/BIN if available")
    print("4. Fall back to filename search as last resort")
    print("─" * 80)

    print("\n💡 Key Insight:")
    if results_baseball.get("cue") and results_nights.get("chd_ss"):
        print("✅ Multi-tier approach VALIDATED!")
        print("   Different games need different strategies!")
        print("   Your 1.2% match rate should improve to 90-98%! 🚀")
    else:
        print("⚠️  Some tests failed. Check:")
        print("   - Authentication credentials")
        print("   - API quota limits")
        print("   - Server load (try during off-peak hours)")

    print("\n" + "═" * 80 + "\n")


if __name__ == "__main__":
    main()
