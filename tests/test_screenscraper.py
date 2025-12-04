#!/usr/bin/env python3
"""
Quick ScreenScraper API test to validate transformation tracking.

This script tests if we can find games using:
1. Direct CHD hash (probably won't work)
2. BIN Track 1 hash from transformation (should work!)
3. CUE hash from Redump DAT (might work)

NOTE: ScreenScraper API requires:
- devid (developer ID)
- devpassword (developer password)  
- softname (your software name)
- ssid/sspassword (user credentials) - optional but increases rate limits

Get credentials from: https://www.screenscraper.fr/
"""

import hashlib
import requests
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# ScreenScraper API endpoint
API_BASE = "https://www.screenscraper.fr/api2"

# You'll need to set these (free registration at screenscraper.fr)
DEVID = ""  # Get from ScreenScraper forums
DEVPASSWORD = ""  # Get from ScreenScraper forums
SOFTNAME = "romfarmer"
SSID = ""  # Your ScreenScraper username (optional)
SSPASSWORD = ""  # Your ScreenScraper password (optional)


def screenscraper_query(
    md5: str,
    system_id: str = "22",  # 22 = Sega Saturn
    rom_name: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Query ScreenScraper API by ROM hash.
    
    Args:
        md5: MD5 hash of the ROM
        system_id: ScreenScraper system ID (22 = Saturn)
        rom_name: Optional ROM filename
    
    Returns:
        Game metadata if found, None otherwise
    """
    if not DEVID or not DEVPASSWORD:
        print("⚠️  ScreenScraper credentials not configured!")
        print("   Get devid/devpassword from: https://www.screenscraper.fr/forumacces.php?zone=6")
        return None
    
    # Build API URL
    url = f"{API_BASE}/jeuInfos.php"
    
    params = {
        "devid": DEVID,
        "devpassword": DEVPASSWORD,
        "softname": SOFTNAME,
        "output": "json",
        "romtype": "rom",
        "rommd5": md5,
        "systemeid": system_id,
    }
    
    if SSID and SSPASSWORD:
        params["ssid"] = SSID
        params["sspassword"] = SSPASSWORD
    
    if rom_name:
        params["romnom"] = rom_name
    
    try:
        print(f"🔍 Querying ScreenScraper for MD5: {md5}")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if "response" in data and "jeu" in data["response"]:
                game = data["response"]["jeu"]
                print(f"✅ FOUND: {game.get('nom', 'Unknown')}")
                return game
            elif "response" in data:
                error = data["response"].get("erreur", "Unknown error")
                print(f"❌ Not found: {error}")
                return None
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None


def test_saturn_game(
    chd_file: Path,
    chd_md5: str,
    bin_md5: str,
    cue_md5: str,
):
    """Test all three hashes for a Saturn game."""
    print(f"\n{'='*80}")
    print(f"Testing: {chd_file.name}")
    print(f"{'='*80}\n")
    
    print("Test 1: Direct CHD hash (probably won't work)")
    print(f"  MD5: {chd_md5}")
    result1 = screenscraper_query(chd_md5, system_id="22", rom_name=chd_file.name)
    
    print("\nTest 2: BIN (Track 1) hash from transformation (should work!)")
    print(f"  MD5: {bin_md5}")
    result2 = screenscraper_query(bin_md5, system_id="22", rom_name=chd_file.stem)
    
    print("\nTest 3: CUE hash from Redump DAT (might work)")
    print(f"  MD5: {cue_md5}")
    result3 = screenscraper_query(cue_md5, system_id="22", rom_name=chd_file.stem)
    
    print("\n" + "="*80)
    print("RESULTS:")
    print("="*80)
    print(f"Direct CHD:      {'✅ FOUND' if result1 else '❌ NOT FOUND'}")
    print(f"BIN (Track 1):   {'✅ FOUND' if result2 else '❌ NOT FOUND'} ← Expected to work")
    print(f"CUE:             {'✅ FOUND' if result3 else '❌ NOT FOUND'}")
    print("="*80 + "\n")
    
    if result2:
        print("✅ SUCCESS! BIN hash works for ScreenScraper queries!")
        print("   This validates our transformation tracking approach.")
    else:
        print("⚠️  BIN hash didn't work. Possible reasons:")
        print("   - ScreenScraper credentials not configured")
        print("   - Rate limiting")
        print("   - Game not in ScreenScraper database")


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                 ScreenScraper Transformation Validator                      ║
╚════════════════════════════════════════════════════════════════════════════╝

This script validates that our transformation tracking approach works with
ScreenScraper's API.

Test Case: 3D Baseball (USA) - Sega Saturn

We have three hashes:
1. CHD hash:  497af1102b63d9d148e4ba4d119fb64e (Your conversion - probably unknown)
2. BIN hash:  5f33157efd8a73de6612a852cf1ba147 (Redump Track 1 - should work!)
3. CUE hash:  4d9347b77d53c8f366f787cc9ba5ef9a (Redump CUE - might work)

The transformation tracking strategy is:
  CHD file → Look up transformation → Get BIN hash → Query ScreenScraper

Let's test if this works!
""")
    
    # Test with 3D Baseball
    test_saturn_game(
        chd_file=Path("/data/emu/stage/eng.1g1r/saturn/3D Baseball (USA).chd"),
        chd_md5="497af1102b63d9d148e4ba4d119fb64e",  # Your CHD
        bin_md5="5f33157efd8a73de6612a852cf1ba147",  # Track 1 from Redump
        cue_md5="4d9347b77d53c8f366f787cc9ba5ef9a",  # CUE from Redump
    )
    
    print("""
📝 NOTE: To actually test this, you need ScreenScraper API credentials:

1. Register at: https://www.screenscraper.fr/
2. Get developer credentials from: https://www.screenscraper.fr/forumacces.php?zone=6
3. Edit this file and set:
   DEVID = "your_dev_id"
   DEVPASSWORD = "your_dev_password"
   SSID = "your_username"  (optional - for better rate limits)
   SSPASSWORD = "your_password"  (optional)

Then run again to validate the approach!
""")
