# ScreenScraper Actual Database Contents

## Game: 3D Baseball (USA) - Sega Saturn

Data scraped from ScreenScraper.fr on 2025-10-12

### What ScreenScraper Has Indexed:

| Filename | Type | MD5 | CRC32 | SHA1 | Size | Scrapes | Filenames |
|----------|------|-----|-------|------|------|---------|-----------|
| **3D Baseball (USA).chd** | iso (cd) | **CC5F238DADB317016D76C378565CA099** | 1B39F1C1 | 1A471015... | 95.62 MB | 4,289 | 1,986 |
| **3D Baseball (USA).cue** | rom (cd) | **4D9347B77D53C8F366F787CC9BA5EF9A** | b72d70f5 | 3450eef6... | 204 B | 1,558 | 577 |
| **3D Baseball (USA).bin** | rom (cd) | **3BB15F208C412E96DB79F96C0AFCBF1E** | 58e4d9f3 | 623ea38c... | 336.08 MB | 261 | 11 |
| 3D Baseball (USA).zip | rom (cd) | 27888823362E9BEFB69C8C1F55B6C0FD | 3C35EF83 | EA331F12... | 144.61 MB | 1,531 | 711 |
| 3D Baseball - The Majors (Japan).chd | rom (cd) | 7b0660b188b2281a95d36fe70ed8b570 | bb6fd83b | a7543bca... | 257 B | 919 | 404 |
| 3D Baseball (United States).cue | rom (cd) | 76dc1039d24e930daaf9f2ddc3ca15d6 | 1da32e7a | 66687148... | 144 B | 0 | 0 |

### Critical Discovery: THREE Different Hashes!

**Our Redump DAT had:**
- BIN Track 1 MD5: `5f33157efd8a73de6612a852cf1ba147` ❌ NOT IN SCREENSCRAPER!
- CUE MD5: `4d9347b77d53c8f366f787cc9ba5ef9a` ✅ IN SCREENSCRAPER! (1,558 scrapes)

**ScreenScraper has DIFFERENT BIN hash:**
- BIN MD5: `3bb15f208c412e96db79f96c0afcbf1e` (336.08 MB = full disc?)
- This is NOT Track 1 only - this appears to be the complete BIN!

**Your CHD:**
- Your CHD MD5: `497af1102b63d9d148e4ba4d119fb64e` ❌ NOT IN SCREENSCRAPER
- SS has CHD MD5: `CC5F238DADB317016D76C378565CA099` ✅ (4,289 scrapes!)

## Analysis

### What This Means:

1. **ScreenScraper indexes MULTIPLE file types:**
   - CUE files (204 bytes) - 1,558 scrapes ⭐ MOST POPULAR FOR QUERIES!
   - Full BIN files (336 MB) - 261 scrapes
   - CHD files (95.62 MB) - 4,289 scrapes 🎯 MOST SCRAPED OVERALL!
   - ZIP files (144 MB) - 1,531 scrapes

2. **The Redump BIN Track 1 hash we have is NOT what ScreenScraper uses!**
   - Redump Track 1: `5f33157e...` (data track only)
   - ScreenScraper: `3bb15f20...` (full BIN with all tracks?)

3. **Best query strategy:**
   - **Primary:** CUE hash (4d9347b7...) - 1,558 successful queries
   - **Secondary:** CHD hash if you have matching conversion
   - **Tertiary:** Full BIN hash (not Track 1!)

### Why ARRM Had Better Match Rate:

ARRM scraped using the **CHD hash** that ScreenScraper knows:
- ARRM imported: `cc5f238d...` ✅ 4,289 scrapes in SS database
- Your CHD: `497af110...` ❌ Different conversion, unknown to SS

## Revised Strategy

### Option 1: Use CUE Hash (SIMPLEST!)
```python
# We already track this in our transformation database!
# CUE → CHD transformation
transformation = recorder.find_source_hash(chd_file)
cue_md5 = transformation.source_md5
# Query ScreenScraper with CUE hash
game = screenscraper.search_game(md5=cue_md5)  # ✅ Will work!
```

### Option 2: Get Full BIN Hash (More Complex)
```python
# Need to hash the ENTIRE BIN file, not just Track 1
# This is what ScreenScraper has indexed
full_bin_md5 = hash_full_file(bin_file)  # 336 MB
game = screenscraper.search_game(md5=full_bin_md5)  # ✅ Will work!
```

### Option 3: Use Known CHD Hash (Requires Community DB)
```python
# Only works if your CHD matches a known conversion
# Your CHD is different from the one SS knows
chd_md5 = hash_file(chd_file)
game = screenscraper.search_game(md5=chd_md5)  # ❌ Won't work for your files
```

## Updated Test Plan

We should test with **CUE hash** instead of BIN Track 1:

```python
TEST_HASHES = {
    "chd": "497af1102b63d9d148e4ba4d119fb64e",  # Your CHD ❌ Unknown to SS
    "cue": "4d9347b77d53c8f366f787cc9ba5ef9a",  # Redump CUE ✅ 1,558 scrapes!
    "bin": "3bb15f208c412e96db79f96c0afcbf1e",  # Full BIN (if we have it)
    "ss_chd": "CC5F238DADB317016D76C378565CA099", # SS's known CHD ✅ 4,289 scrapes!
}
```

## Conclusion

**The CUE file hash is our best bet!**

- ✅ Small file (204 bytes) - fast to hash
- ✅ 1,558 successful scrapes in SS database
- ✅ We already track CUE → CHD transformations
- ✅ Redump DATs have CUE hashes
- ✅ Most reliable for disc-based games

**Next Steps:**
1. Update our test to focus on CUE hash
2. Verify CUE hash lookup works with dev credentials
3. Update transformation strategy to prioritize CUE hashes
4. Keep BIN Track 1 hashes in DAT database for reference
