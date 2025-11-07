# Revision Duplicate Analysis

## Problem Statement

When building PSX 1G1R English collection, we end up with duplicate games that differ only by revision number. For example:
- `Alundra (USA).chd` (291M)
- `Alundra (USA) (Rev 1).chd` (291M)

This makes it difficult for users to know which version to use, as both appear in the collection.

## Scope Analysis

### Current State (PSX 1G1R English Build)

- **Total unique games**: 1,789
- **Games with multiple versions**: 11
- **Duplicates found**:
  1. Alundra (USA) - Base + Rev 1
  2. Dino Crisis (USA) - Base + Rev 1
  3. Gran Turismo (USA) - Base + Rev 1
  4. Gran Turismo 2 (USA) (Simulation Mode) - Base + Rev 1 + Rev 2 (3 versions!)
  5. Metal Gear Solid (USA) (Disc 1) - Base + Rev 1
  6. Oddworld - Abe's Oddysee (USA) - Base + Rev 2
  7. Soul Blade (USA) - Base + Rev 1
  8. Spyro - Year of the Dragon (USA) - Base + Rev 1
  9. Syphon Filter (USA) - Base + Rev 1
  10. Tomb Raider (USA) - Base + Rev 6 (!)
  11. Tomb Raider II - Starring Lara Croft (USA) - Rev 1 + Rev 3

**Impact**: ~0.6% of games affected (11 out of 1,789)

### Source Analysis (Myrient Redump PSX)

- **Total files**: 10,884
- **Unique base games**: 10,550
- **Games with multiple versions**: 306

This means ~2.9% of the full Redump set has multiple revisions.

### DAT File Analysis (redump.retool.1g1r.eng)

- **Total games**: 1,798
- **Games with (Rev X)**: 76
- **Games with BOTH base and Rev in DAT**: 0 ✅

**The DAT is correct!** Retool's 1G1R filtering properly selected only one version per game. The problem is in our matching logic.

## Root Cause

The issue occurs because:

1. **Source has both versions**: Myrient provides the complete Redump set including all revisions
   - Example: `Alundra (USA).zip` AND `Alundra (USA) (Rev 1).zip` both exist

2. **DAT only wants Rev 1**: The 1G1R DAT correctly contains only `Alundra (USA) (Rev 1)`

3. **Our matcher is too permissive**: The basename matching in `ROMMatcher._match_zip_file()` strips extensions but doesn't properly handle revision numbers:
   ```python
   # Current logic (lines 161-166):
   inner_base = Path(inner_name).stem  # "Alundra (USA)"
   if inner_base == rom_name_base:     # Matches both files!
       for dat_rom_name, (game, rom) in self.rom_name_index.items():
           if Path(dat_rom_name).stem == rom_name_base:
               return MatchResult(...)  # Accepts ANY version
   ```

4. **Fuzzy matching is the problem**: When the exact inner filename doesn't match (because DAT wants `.cue` but we're matching ZIP names), the fallback fuzzy matching strips the revision number and matches the base name.

## Why This Happens

The matching flow for `Alundra (USA) (Rev 1).zip`:
1. ✅ Exact match succeeds: inner file `Alundra (USA) (Rev 1).cue` matches DAT entry
2. ✅ File is correctly copied to work directory

The matching flow for `Alundra (USA).zip` (base version NOT in DAT):
1. ❌ Exact match fails: inner file `Alundra (USA).cue` not in DAT
2. ✅ Fuzzy match succeeds: strips "(Rev 1)" and matches base name "Alundra (USA)"
3. ❌ **Wrong file copied!** Base version matched to Rev 1 DAT entry

## Proposed Solutions

### Solution 1: Strict Filename Matching (Recommended)

**Change the matcher to require exact filename matches**, only allowing extension differences.

**Pros**:
- Simple and safe
- Prevents false positives
- Aligns with Retool's 1G1R intent
- No performance impact

**Cons**:
- May miss legitimately renamed files
- Requires clean source naming

**Implementation**:
```python
def _match_zip_file(self, zip_path: Path) -> MatchResult:
    """Match ZIP file against DAT with strict filename requirements."""
    
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            for inner_name in zf.namelist():
                if inner_name.endswith("/") or inner_name.startswith("."):
                    continue

                # STRICT: Only match if filename matches exactly (except extension)
                # This prevents "Game (USA).zip" from matching "Game (USA) (Rev 1)" in DAT
                
                # First try exact filename match
                if inner_name in self.rom_name_index:
                    game, rom = self.rom_name_index[inner_name]
                    return MatchResult(
                        file_path=zip_path,
                        match_type=MatchType.INNER_FILENAME,
                        dat_game=game,
                        dat_rom=rom,
                        confidence=1.0,
                    )
                
                # Allow extension differences (e.g., .cue vs .bin)
                # but NOT revision number differences
                inner_stem = Path(inner_name).stem
                for dat_rom_name in self.rom_name_index.keys():
                    dat_stem = Path(dat_rom_name).stem
                    if inner_stem == dat_stem:  # Exact stem match required
                        game, rom = self.rom_name_index[dat_rom_name]
                        return MatchResult(
                            file_path=zip_path,
                            match_type=MatchType.INNER_FILENAME,
                            dat_game=game,
                            dat_rom=rom,
                            confidence=0.95,
                        )
    
    except (zipfile.BadZipFile, OSError):
        pass

    return MatchResult(
        file_path=zip_path,
        match_type=MatchType.NO_MATCH,
        confidence=0.0,
    )
```

**Testing Required**:
- Verify Rev files still match correctly
- Verify base files are rejected
- Check for any legitimate files that stop matching

---

### Solution 2: Hash-Based Matching (Better Long-Term)

Use MD5/CRC hashes from DAT to match files, eliminating filename ambiguity entirely.

**Pros**:
- 100% accurate matching
- Handles renamed files correctly
- Industry standard approach
- Already partially implemented (filter_dat.py lines 254-264)

**Cons**:
- Requires MD5 calculation for all files (slow)
- Database needed for performance
- More complex to implement

**Implementation**:
```python
# In filter_dat.py, prioritize hash matching:
for file_path in context.source_files:
    result = None
    
    # 1. Try hash match first (most accurate)
    if file_path in context.file_md5s:
        md5 = context.file_md5s[file_path]
        result = matcher.match_by_hash(file_path, md5=md5)
        if result.is_matched():
            matched_files.append(file_path)
            continue
    
    # 2. Strict filename match (no fuzzy)
    result = matcher.match_file_strict(file_path)
    if result.is_matched():
        matched_files.append(file_path)
    else:
        unmatched_files.append(file_path)
```

**Status**: MD5 matching already works (we have it for ARRM metadata), but needs to be made the primary path.

---

### Solution 3: Revision Preference System

Add explicit logic to prefer higher revision numbers when multiple versions match.

**Pros**:
- Handles edge cases gracefully
- Can be combined with other solutions
- User can configure preference (newest vs oldest)

**Cons**:
- More complex logic
- Masks the underlying problem
- Still allows duplicates temporarily

**Implementation**:
```python
class RevisionMatcher:
    """Handle revision number preferences."""
    
    @staticmethod
    def extract_revision(filename: str) -> int:
        """Extract revision number from filename.
        
        Returns:
            Revision number (0 for base version, 1+ for revisions)
        """
        match = re.search(r'\(Rev (\d+)\)', filename)
        return int(match.group(1)) if match else 0
    
    @staticmethod
    def prefer_revision(files: list[Path], preference: str = "highest") -> Path:
        """Select preferred revision from multiple versions.
        
        Args:
            files: List of file paths for same game
            preference: "highest", "lowest", or "base"
        
        Returns:
            Preferred file path
        """
        if preference == "highest":
            return max(files, key=lambda f: RevisionMatcher.extract_revision(f.name))
        elif preference == "lowest":
            return min(files, key=lambda f: RevisionMatcher.extract_revision(f.name))
        else:  # base
            return min(files, key=lambda f: (RevisionMatcher.extract_revision(f.name), f.name))
```

**Usage**: Add deduplication step after filtering but before copying to work directory.

---

### Solution 4: Source Directory Pre-Filtering

Filter the source directory to remove unwanted revisions before processing.

**Pros**:
- Simple one-time operation
- Reduces processing time
- Keeps source clean

**Cons**:
- Loses data (can't go back)
- Requires manual decision on which versions to keep
- Doesn't solve the core matching problem

**Implementation**:
```bash
# Script to remove base versions when Rev X exists
cd /data/emu/source/myrient.erista.me/files/Redump/Sony\ -\ PlayStation/
find . -name "*.zip" | python3 << 'EOF'
import sys
import re
from pathlib import Path
from collections import defaultdict

files = [line.strip() for line in sys.stdin]
games = defaultdict(list)

# Group by base name
for f in files:
    base = re.sub(r' \(Rev \d+\)', '', f)
    games[base].append(f)

# For games with multiple versions, keep only highest rev
for base, versions in games.items():
    if len(versions) > 1:
        versions_with_rev = [(f, int(re.search(r'\(Rev (\d+)\)', f).group(1)) if '(Rev ' in f else 0) 
                              for f in versions]
        to_remove = [f for f, rev in versions_with_rev if rev != max(v[1] for v in versions_with_rev)]
        for f in to_remove:
            print(f"rm '{f}'")  # Print commands to review first
EOF
```

---

## Recommended Approach

Implement **Solution 1 (Strict Filename Matching)** immediately:

1. **Short-term** (Today):
   - Modify `ROMMatcher._match_zip_file()` to remove fuzzy matching
   - Require exact stem match (allow only extension differences)
   - Test with PSX build to verify duplicates are eliminated

2. **Medium-term** (This week):
   - Add **Solution 3 (Revision Preference)** as a fallback safety net
   - Configure preference to "highest" (prefer Rev 1 over base)
   - Add logging when multiple versions are found

3. **Long-term** (Next month):
   - Prioritize **Solution 2 (Hash-Based Matching)** as primary method
   - Make MD5 database population automatic
   - Use filename matching only as fallback

## Expected Results

After implementing Solution 1:
- **Before**: 1,789 games + 11 duplicates = 1,800 files
- **After**: 1,789 games (no duplicates)
- **Removed**: Base versions that weren't in 1G1R DAT

**Games affected** (will lose base version, keep Rev only):
1. Alundra (USA).chd ❌ → Keep only Rev 1 ✅
2. Dino Crisis (USA).chd ❌ → Keep only Rev 1 ✅
3. Gran Turismo (USA).chd ❌ → Keep only Rev 1 ✅
4. Gran Turismo 2 (USA) (Simulation Mode).chd ❌ → Keep only highest Rev ✅
5. Metal Gear Solid (USA) (Disc 1).chd ❌ → Keep only Rev 1 ✅
6. Oddworld - Abe's Oddysee (USA).chd ❌ → Keep only Rev 2 ✅
7. Soul Blade (USA).chd ❌ → Keep only Rev 1 ✅
8. Spyro - Year of the Dragon (USA).chd ❌ → Keep only Rev 1 ✅
9. Syphon Filter (USA).chd ❌ → Keep only Rev 1 ✅
10. Tomb Raider (USA).chd ❌ → Keep only Rev 6 ✅
11. Tomb Raider II (USA).chd - Will need to check which Rev DAT has ✅

## Testing Plan

1. **Unit Tests**:
   - Test matcher with exact stem matches (should succeed)
   - Test matcher with different stems (should fail)
   - Test matcher with same stem but different Rev (should fail)

2. **Integration Tests**:
   - Run PSX build with strict matching
   - Verify output has exactly 1,798 games (matching DAT count)
   - Verify no duplicates in output

3. **Validation**:
   - Check that all matched files have exact DAT entries
   - Verify Rev numbers in output match Rev numbers in DAT
   - Spot-check that correct versions are selected

## Code Locations

- **Matcher**: `src/romgroomer/dat_parser/matcher.py` lines 120-180
- **Filter Stage**: `src/romgroomer/stages/filter_dat.py` lines 250-270
- **Models**: `src/romgroomer/dat_parser/models.py` (DATFile, DATGame, DATRom)

## Additional Benefits

Fixing this will also:
- Reduce output size (eliminate duplicate ~3GB of CHD files)
- Improve user experience (no confusion about versions)
- Align with Retool's 1G1R intent
- Make collection more curated and professional
- Faster builds (fewer files to process)
