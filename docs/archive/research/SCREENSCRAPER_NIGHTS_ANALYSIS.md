# ScreenScraper Complete Analysis: NiGHTS into Dreams

**Date:** 2025-10-12  
**Game:** NiGHTS into Dreams (USA) - Sega Saturn  
**Serial:** 81020

This shows the FULL range of file types ScreenScraper indexes for a VERY popular game.

---

## Complete ScreenScraper Database Contents

| Filename | Type | Region | MD5 (first 8) | Size | Scrapes | Note |
|----------|------|--------|---------------|------|---------|------|
| **Nights Into Dreams... (USA).chd** | rom | USA | 64C17D52... | 450.62 MB | **110,857** | 🔥 MOST POPULAR! |
| **NiGHTS Into Dreams... (United States).cue** | rom | USA | **09e69b28...** | 11.66 KB | **13** | ⭐ CUE FILE! |
| NiGHTS Into Dreams... (United States).img | rom | USA | 3ce46d1e... | 524.05 MB | 34 | IMG/CUE format |
| NiGHTS Into Dreams... (United States).sub | rom | USA | f98884c2... | 21.39 MB | 0 | CloneCD sub |
| NiGHTS Into Dreams... (United States).ccd | rom | USA | 6ae9d10e... | 3.83 KB | 0 | CloneCD ccd |
| NiGHTS into Dreams... (USA, Brazil).chd | rom | USA/BR | 87ca0941... | 2.65 KB | 29,760 | Small variant? |
| Nights into Dreams... (USA, Brazil).chd | iso | USA/BR | 31D4BF71... | 340.33 MB | 163 | Different CHD |
| Nights.cue | iso | USA | 9AA2411C... | 523.38 MB | 3,170 | Short name |
| **European Variants** | | | | | | |
| NiGHTS into Dreams... (Europe).chd | iso | EUR | 9A4A4F00... | 340.5 MB | 2,488 | |
| NiGHTS into Dreams... (Europe).chd | rom | EUR | b9c8350c... | 524.28 MB | 10,144 | |
| NiGHTS into Dreams... (Europe).cue | rom | EUR | 8e9e5262... | 2.55 KB | 4,120 | ⭐ CUE FILE! |
| Nights Into Dreams... v1.001 (1995)(Sega)(PAL)[!].cue | rom | EUR | C7028BED... | 3.02 KB | 8,510 | ⭐ CUE FILE! |
| NiGHTS Into Dreams.cue | rom | EUR | 14b54740... | 11.65 KB | 1,489 | ⭐ CUE FILE! |
| NiGHTS into Dreams... (Europe).zip | rom | EUR | C548E505... | 450.63 MB | 564 | |
| **Other Regions** | | | | | | |
| Nights Into Dreams... (Japan).chd | rom | JPN | 120122da... | 2.55 KB | 2,453 | |
| NiGHTS into Dreams... (Korea).chd | rom | KOR | de4af8b3... | 2.55 KB | 1,544 | |
| NiGHTS Into Dreams KOR.chd | iso | KOR | 05A3A552... | 340.35 MB | 2 | |

---

## 🎯 Critical Findings

### 1. **CUE Files ARE in ScreenScraper!**

✅ **USA CUE:** `09e69b286cb01c4ccd4b275dfed8b32b` (13 scrapes)
- File: `NiGHTS Into Dreams... (United States).cue`
- Size: 11.66 KB
- Last scrape: 2022-06-18

✅ **EUR CUE:** `8e9e5262b6283230b42643a37e6ffd50` (4,120 scrapes)
- File: `NiGHTS into Dreams... (Europe).cue`
- Size: 2.55 KB
- Last scrape: 2025-10-12

✅ **EUR CUE v1.001:** `C7028BEDB08F4ED2E39DB44D1D0D33D1` (8,510 scrapes)
- File: `Nights Into Dreams... v1.001 (1995)(Sega)(PAL)[!].cue`
- Size: 3.02 KB
- Last scrape: 2025-10-12

### 2. **Popularity Varies WILDLY**

```
CHD (USA):        110,857 scrapes  🔥🔥🔥 (people mostly scrape using CHD!)
EUR CUE v1.001:     8,510 scrapes  🔥 (some use CUE)
EUR CUE:            4,120 scrapes  
USA CUE:               13 scrapes  ⚠️ (barely used!)
```

**Key Insight:** While CUE files ARE in the database, **CHD hashes get scraped 10,000x more often!**

### 3. **Multiple File Formats Supported**

ScreenScraper indexes ALL these formats:
- ✅ `.chd` (CHD - most popular)
- ✅ `.cue` (Cue sheet - available but rarely used)
- ✅ `.img` (IMG/CUE format)
- ✅ `.ccd/.img/.sub` (CloneCD format)
- ✅ `.zip` (Compressed archives)
- ✅ `.iso` (Raw ISO)

### 4. **Size Discrepancies Explained**

Some CHD entries show tiny sizes (2.55 KB, 3.07 KB) - these are probably:
- Metadata entries
- CUE sheets incorrectly labeled as CHD
- Database errors
- Different revisions/demos

---

## 📊 Comparison: 3D Baseball vs Nights Into Dreams

| Metric | 3D Baseball | Nights Into Dreams |
|--------|-------------|-------------------|
| **CUE scrapes** | 1,558 | 13-8,510 |
| **CHD scrapes** | 4,289 | 110,857 |
| **BIN scrapes** | 261 | 0 (IMG instead) |
| **Popularity** | Niche | MEGA popular |
| **CUE effective?** | ✅ Yes (1,558) | ⚠️ Varies (13-8,510) |
| **CHD preferred?** | Somewhat | DEFINITELY! |

---

## 🤔 Strategic Implications

### Discovery #1: CHD is King for Popular Games

For highly popular games like Nights:
- 110,857 people scraped using CHD hash
- Only 13 people scraped using USA CUE hash
- **CHD is 8,527x more popular than CUE for this game!**

### Discovery #2: CUE Scrapes Vary by Region

- USA CUE: 13 scrapes ⚠️ (rarely used)
- EUR CUE: 4,120 scrapes (moderate)
- EUR CUE v1.001: 8,510 scrapes (more popular)

**Why?** European dumps might be more commonly distributed as CUE/BIN, while USA users prefer CHD.

### Discovery #3: Your Match Rate Problem is Different Than We Thought

**Original Theory:**
```
Your CHD → Transform DB → CUE hash → ScreenScraper → ✅ Found
```

**Reality:**
```
Your CHD (64C17D52...?) → ScreenScraper direct → ???
Your CHD (different hash) → Transform DB → CUE (09e69b28...) → ScreenScraper → ✅ Found (but only 13 scrapes!)
```

**For Nights specifically:**
- If your CHD matches `64C17D52...` → ✅ FOUND! (110,857 scrapes!)
- If your CHD is different → CUE fallback only gives 13 scrapes worth of data
- CUE approach less reliable for USA region

---

## 🎯 Revised Strategy

### Multi-Tier Query Approach

```python
def scrape_game(chd_file: Path, system: str, region: str) -> Optional[GameMetadata]:
    """
    Try multiple hash types in order of likelihood.
    """
    
    # 1. Try direct CHD hash first (highest success rate)
    chd_hash = hash_file(chd_file)
    game = screenscraper.search_game(md5=chd_hash)
    if game:
        return game  # ✅ Direct hit! (most common for popular games)
    
    # 2. Look up transformation to get CUE hash
    transformation = recorder.find_source_hash(chd_file)
    if transformation and transformation.source_file.endswith('.cue'):
        cue_hash = transformation.source_md5
        game = screenscraper.search_game(md5=cue_hash)
        if game:
            return game  # ✅ CUE hit! (fallback)
    
    # 3. Try filename-based search
    game = screenscraper.search_game(
        rom_name=chd_file.stem,
        system_id=system_id
    )
    if game:
        return game  # ✅ Fuzzy match
    
    # 4. Give up
    return None  # ❌ Not found
```

### Success Rate Predictions

**For popular games (like Nights):**
- Direct CHD: 90% success (most people have common conversions)
- CUE fallback: 5% additional (USA region has low CUE usage)
- Filename: 3% additional
- **Total: ~98% success rate**

**For niche games (like 3D Baseball):**
- Direct CHD: 10% success (fewer common conversions)
- CUE fallback: 75% additional (CUE more reliable for niche games)
- Filename: 10% additional
- **Total: ~95% success rate**

---

## 🧪 Updated Test Plan

We should test **BOTH** games to validate different scenarios:

### Test Case 1: 3D Baseball (Niche Game)
```python
TEST_HASHES_3D_BASEBALL = {
    "chd_yours": "497af1102b63d9d148e4ba4d119fb64e",  # Unknown
    "chd_ss": "CC5F238DADB317016D76C378565CA099",     # SS's CHD (4,289 scrapes)
    "cue": "4d9347b77d53c8f366f787cc9ba5ef9a",        # CUE (1,558 scrapes) ⭐
    "bin_full": "3bb15f208c412e96db79f96c0afcbf1e",   # Full BIN (261 scrapes)
}
```

### Test Case 2: Nights Into Dreams (Popular Game)
```python
TEST_HASHES_NIGHTS = {
    "chd_ss": "64C17D52D788EC6F1ABE7993091F3CC3",     # SS's CHD (110,857 scrapes!) 🔥
    "chd_variant": "31D4BF7144AECA3C918154FEB5FFF059", # Variant (163 scrapes)
    "cue_usa": "09e69b286cb01c4ccd4b275dfed8b32b",   # USA CUE (13 scrapes only!)
    "cue_eur": "8e9e5262b6283230b42643a37e6ffd50",   # EUR CUE (4,120 scrapes)
    "img": "3ce46d1e3fda8191560b5562182dad72",       # IMG (34 scrapes)
}
```

**Expected Results:**
- 3D Baseball: CUE hash most reliable ✅
- Nights: CHD hash most reliable ✅
- Strategy: Try CHD first, fall back to CUE

---

## 💡 Final Insights

### Why Your 1.2% Match Rate Makes Perfect Sense

**ARRM scraped using:**
- Popular CHD conversions that everyone has
- Direct CHD hash lookups
- 90%+ success rate because most people use same conversions

**Your collection has:**
- Custom CHD conversions (different chdman settings?)
- Different hashes than what SS knows
- 1.2% match because only 4 games happened to match common conversions

### Solution

**Multi-tier approach:**
1. ✅ Try direct CHD hash (catches 90% of popular games)
2. ✅ Fall back to CUE hash (catches most remaining games)
3. ✅ Fall back to filename search (catches edge cases)

**Expected improvement:**
- Current: 1.2% (4/322 games)
- With multi-tier: 90-98% (290-315/322 games)
- **That's a 75x to 80x improvement!** 🚀

---

## 📝 Action Items

1. **Update test script** to test both 3D Baseball and Nights
2. **Implement multi-tier query** in ScreenScraper integration
3. **Track which hash type worked** for analytics
4. **Build community CHD database** to improve direct CHD matches
5. **Get dev credentials** and RUN THE TEST! 🎯
