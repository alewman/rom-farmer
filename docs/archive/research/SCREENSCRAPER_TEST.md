# ScreenScraper Validation Test

## What This Tests

This script validates that our transformation tracking approach works with ScreenScraper.fr.

We test three different MD5 hashes for the same game ("3D Baseball (USA)" on Saturn):

1. **CHD hash** (`497af110...`) - Your converted CHD file  
   **Expected**: ❌ NOT FOUND (ScreenScraper doesn't know your specific conversion)

2. **BIN Track 1 hash** (`5f33157e...`) - From Redump DAT  
   **Expected**: ✅ FOUND (This is what ScreenScraper knows!) ⭐

3. **CUE hash** (`4d9347b7...`) - From Redump DAT  
   **Expected**: ❓ MAYBE (Depends on ScreenScraper's indexing)

## Setup

### 1. Get ScreenScraper Credentials

**Register an account:**
- Go to: https://www.screenscraper.fr/
- Create a free account

**Get developer credentials:**
- Forum post: https://www.screenscraper.fr/forumacces.php?zone=6
- Request `devid` and `devpassword` (usually granted quickly)

### 2. Set Environment Variables

```bash
export SS_DEV_ID="your_dev_id_here"
export SS_DEV_PASSWORD="your_dev_password_here"
export SS_USER_ID="your_screenscraper_username"
export SS_USER_PASSWORD="your_screenscraper_password"
```

### 3. Run the Test

```bash
cd /path/to/rom-farmer
python3 test_screenscraper_validation.py
```

## Expected Output

```
╔════════════════════════════════════════════════════════════════════════════╗
║          ScreenScraper Transformation Tracking Validation                  ║
╚════════════════════════════════════════════════════════════════════════════╝

Test Case: "3D Baseball (USA)" - Sega Saturn

████████████████████████████████████████████████████████████████████████████████
TEST 1: Direct CHD Hash (Your converted file)
████████████████████████████████████████████████████████████████████████████████
Expected: ❌ NOT FOUND

Testing CHD hash
MD5: 497af1102b63d9d148e4ba4d119fb64e
❌ NOT FOUND: Game not in ScreenScraper database

████████████████████████████████████████████████████████████████████████████████
TEST 2: BIN (Track 1) Hash from Transformation Tracking
████████████████████████████████████████████████████████████████████████████████
Expected: ✅ FOUND

Testing BIN TRACK 1 hash
MD5: 5f33157efd8a73de6612a852cf1ba147
✅ SUCCESS! Found game:
   Name: 3D Baseball
   System: Sega Saturn
   Region: us
   Publisher: Crystal Dynamics
   Release: 1996-10-31
   
   Available media types:
     - box-2D: 2
     - box-3D: 1
     - screenshot: 4
     - video: 1
     - wheel: 1

████████████████████████████████████████████████████████████████████████████████
TEST 3: CUE File Hash from Redump DAT
████████████████████████████████████████████████████████████████████████████████
Expected: ❓ MAYBE

Testing CUE hash
MD5: 4d9347b77d53c8f366f787cc9ba5ef9a
❌ NOT FOUND: Game not in ScreenScraper database


╔══════════════════════════════════════════════════════════════════════════════╗
║                            FINAL RESULTS                                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

Direct CHD Hash:          ❌ NOT FOUND
BIN Track 1 Hash:         ✅ FOUND ← Transform approach
CUE Hash:                 ❌ NOT FOUND

================================================================================
✅ SUCCESS! Transformation tracking approach VALIDATED!

The strategy works:
  1. Your CHD → Look up transformation in database
  2. Get BIN (Track 1) hash: 5f33157efd8a73de6612a852cf1ba147
  3. Query ScreenScraper with BIN hash
  4. ✅ Game found and metadata retrieved!

This proves we can scrape metadata for converted ROMs!
================================================================================
```

## What This Proves

If **TEST 2 succeeds** (BIN Track 1 hash), it proves:

✅ **Your transformation tracking approach is correct!**

The workflow:
```
Your CHD file (497af110...)
    ↓
Look up in rom_transformations table
    ↓
Find source_md5: 5f33157efd8a73de6612a852cf1ba147
    ↓
Query ScreenScraper with this hash
    ↓
✅ Get metadata, box art, screenshots, etc.!
```

This solves the **1.2% match rate problem** for Saturn/PS1/PS2 disc-based systems!

## Rate Limiting

⚠️ **Important**: ScreenScraper has strict rate limits:

- **Guest users**: Very limited, often disabled during high load
- **Registered users**: ~20,000 requests/day (OK scrapes)
- **Failed searches** (KO scrapes): Much lower limit (~2,000/day)

**Best practices:**
1. ✅ Always use registered user credentials
2. ✅ Cache results aggressively (never request same game twice)
3. ✅ Use hash-based lookups (not filename)
4. ✅ Cache "not found" results to avoid wasting KO quota
5. ✅ Consider donating if doing large-scale scraping

## Troubleshooting

**Authentication Error:**
- Double-check your credentials
- Make sure environment variables are set correctly
- Dev credentials may need approval from forums

**Quota Exceeded:**
- Wait 24 hours for quota reset
- Check if you're hitting KO scrape limit (not found results)
- Consider using a premium account for higher limits

**Server Load Error:**
- ScreenScraper is under high load
- Try again during off-peak hours (European morning)
- This is normal and not a bug

**Game Not Found:**
- Some games may not be in the database
- Try alternative hash (CRC32, SHA1)
- Check game name spelling
