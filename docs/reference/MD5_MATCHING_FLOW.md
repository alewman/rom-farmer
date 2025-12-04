# MD5-Based DAT Matching - Flow Diagram

## High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DAT Filtering Pipeline                      │
└─────────────────────────────────────────────────────────────────────┘

┌───────────────┐
│ Source Files  │ (e.g., Dragon Age II (USA, Asia).zip)
└───────┬───────┘
        │
        ▼
┌────────────────────────────────────────────────────────────┐
│ Optional: Populate MD5s from ARRM                          │
│  • Query ScrapedGame table by game name                    │
│  • Store MD5 in context.file_md5s[file_path] = md5         │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────┐
│ FilterDATStage.execute()                                   │
│  For each file:                                            │
│    1. Check if MD5 available in context.file_md5s          │
│    2. If yes: Try matcher.match_by_hash(md5=...)           │
│    3. If no match: Try matcher.match_file() (name-based)   │
│    4. Track stats: hash_matched vs name_matched            │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────┐
│ Output Statistics                                          │
│  • Matched: 4,845 (99.9%)                                  │
│    - MD5 matched: 95 (renamed files)                       │
│    - Name matched: 4,750 (standard files)                  │
│  • Unmatched: 5 (needs investigation)                      │
└────────────────────────────────────────────────────────────┘
```

## Detailed Matching Logic

```
┌──────────────────────────────────────────────────────────────────────┐
│                     File Matching Decision Tree                      │
└──────────────────────────────────────────────────────────────────────┘

For file_path in source_files:
    │
    ├─► Is MD5 available in context.file_md5s?
    │   │
    │   ├─► YES ──┐
    │   │         │
    │   └─► NO ───┼─────────────────────┐
    │             │                     │
    │             ▼                     │
    │   ┌──────────────────────┐       │
    │   │ Try MD5 Matching     │       │
    │   │ matcher.match_by_hash│       │
    │   │ (file_path, md5=...) │       │
    │   └─────────┬────────────┘       │
    │             │                     │
    │             ├─► Match found?      │
    │             │   │                 │
    │             │   ├─► YES ──────────┼─► hash_matched += 1
    │             │   │                 │   DONE (matched)
    │             │   │                 │
    │             │   └─► NO ───────────┤
    │             │                     │
    │             └─────────────────────┤
    │                                   │
    │                                   ▼
    │   ┌───────────────────────────────────────┐
    │   │ Fallback: Name-Based Matching         │
    │   │ matcher.match_file(file_path)         │
    │   └────────────┬──────────────────────────┘
    │                │
    │                ├─► Match found?
    │                │   │
    │                │   ├─► YES ───► name_matched += 1
    │                │   │            DONE (matched)
    │                │   │
    │                │   └─► NO ────► unmatched += 1
    │                │                DONE (no match)
    └────────────────┴────────────────────────────────────┘
```

## Example: PS3 Redump Naming Update

```
┌────────────────────────────────────────────────────────────────────┐
│              Example: Dragon Age II Renamed File                   │
└────────────────────────────────────────────────────────────────────┘

DAT File (Created 2024-10-01):
┌─────────────────────────────────────────────────────────────────┐
│ Game: "Dragon Age II (USA)"                                     │
│ ROM:  "Dragon Age II (USA).iso"                                 │
│ MD5:  a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4                          │
└─────────────────────────────────────────────────────────────────┘
                            ▲
                            │
                            │ MD5 Match!
                            │
Source File (Redump updated 2025-10-20):
┌─────────────────────────────────────────────────────────────────┐
│ File: "Dragon Age II (USA, Asia).zip"  ◄─── NEW NAME            │
│ MD5:  a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4  ◄─── SAME HASH          │
└─────────────────────────────────────────────────────────────────┘

Without MD5 Matching:
  ✗ Name mismatch: "Dragon Age II (USA, Asia)" ≠ "Dragon Age II (USA)"
  ✗ File marked as UNMATCHED
  ✗ Appears as "missing" in reports

With MD5 Matching:
  ✓ MD5 match: a1b2...c3d4 = a1b2...c3d4
  ✓ File matched via hash
  ✓ Linked to game "Dragon Age II (USA)"
  ✓ Statistics show: "1 MD5 matched (renamed)"
```

## Data Structures

```
┌──────────────────────────────────────────────────────────────────┐
│                       StageContext                               │
├──────────────────────────────────────────────────────────────────┤
│ source_files: List[Path]                                         │
│   [                                                              │
│     Path("Dragon Age II (USA, Asia).zip"),                       │
│     Path("Fallout 3 (USA, Canada).zip"),                         │
│     ...                                                          │
│   ]                                                              │
│                                                                  │
│ file_md5s: Dict[Path, str]  ◄─── NEW FIELD                      │
│   {                                                              │
│     Path("Dragon Age II (USA, Asia).zip"):                       │
│       "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",                        │
│     Path("Fallout 3 (USA, Canada).zip"):                         │
│       "f1e2d3c4b5a6f1e2d3c4b5a6f1e2d3c4",                        │
│     ...                                                          │
│   }                                                              │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                     ROMMatcher Indices                           │
├──────────────────────────────────────────────────────────────────┤
│ md5_index: Dict[str, Tuple[DATGame, DATRom]]                     │
│   {                                                              │
│     "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4":                          │
│       (DATGame("Dragon Age II (USA)"), DATRom(...)),             │
│     "f1e2d3c4b5a6f1e2d3c4b5a6f1e2d3c4":                          │
│       (DATGame("Fallout 3 (USA)"), DATRom(...)),                 │
│     ...                                                          │
│   }                                                              │
│                                                                  │
│ rom_name_index: Dict[str, Tuple[DATGame, DATRom]]               │
│   {                                                              │
│     "Dragon Age II (USA).iso":                                   │
│       (DATGame("Dragon Age II (USA)"), DATRom(...)),             │
│     "Fallout 3 (USA).iso":                                       │
│       (DATGame("Fallout 3 (USA)"), DATRom(...)),                 │
│     ...                                                          │
│   }                                                              │
└──────────────────────────────────────────────────────────────────┘
```

## Statistics Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                    Statistics Tracking                           │
└──────────────────────────────────────────────────────────────────┘

Initialize counters:
  hash_matched = 0
  name_matched = 0
  unmatched = 0

For each file:
  │
  ├─► MD5 match?  ──► YES ─► hash_matched += 1
  │                          matched_files.append(file)
  │
  ├─► Name match? ──► YES ─► name_matched += 1
  │                          matched_files.append(file)
  │
  └─► No match?   ──► YES ─► unmatched += 1
                             unmatched_files.append(file)

Final output:
┌──────────────────────────────────────────────────────────────┐
│ Filter DAT                                                   │
│   Games in DAT: 4,893                                        │
│   Source files: 4,850                                        │
│   Matched: 4,845 (99.9%)                                     │
│     MD5 matched: 95      ◄─── Renamed files                 │
│     Name matched: 4,750  ◄─── Standard files                │
│   Unmatched: 5           ◄─── Unknown/problematic           │
└──────────────────────────────────────────────────────────────┘
```

## Performance Comparison

```
┌────────────────────────────────────────────────────────────────┐
│              Performance: Name vs MD5 Matching                 │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│ Name-Based Matching:                                           │
│   Time: O(1) dictionary lookup                                │
│   Cost: ~0.001ms per file                                     │
│   Data: Filename string comparison                            │
│                                                                │
│ MD5-Based Matching (ARRM pre-loaded):                          │
│   Time: O(1) dictionary lookup                                │
│   Cost: ~0.001ms per file                                     │
│   Data: MD5 string comparison (32 chars)                      │
│                                                                │
│ MD5-Based Matching (computed on-the-fly):                      │
│   Time: O(n) where n = file size                              │
│   Cost: ~10ms for 1GB file @ 100MB/s                          │
│   Data: Read entire file, compute hash                        │
│                                                                │
├────────────────────────────────────────────────────────────────┤
│ Recommendation: Use ARRM pre-loaded MD5s                       │
│   • Zero additional cost                                      │
│   • Already calculated during metadata import                 │
│   • Available for all Redump systems                          │
└────────────────────────────────────────────────────────────────┘
```

## Integration Timeline

```
┌────────────────────────────────────────────────────────────────┐
│                  RomGroomer Processing Stages                  │
└────────────────────────────────────────────────────────────────┘

Stage 1: Scan Source Directory
  │
  ▼
Stage 2: Load DAT File
  │
  ▼
Stage 3: Populate MD5s (NEW - optional pre-filter step)
  │     ┌──────────────────────────────────────┐
  │     │ Query ARRM database                  │
  │     │ For each source file:                │
  │     │   game = query_by_name(file.stem)    │
  │     │   if game.md5:                       │
  │     │     context.file_md5s[file] = md5    │
  │     └──────────────────────────────────────┘
  ▼
Stage 4: Filter DAT (ENHANCED)
  │     ┌──────────────────────────────────────┐
  │     │ Try MD5 matching first (if available)│
  │     │ Fallback to name matching            │
  │     │ Track statistics                     │
  │     └──────────────────────────────────────┘
  ▼
Stage 5: Copy Matched Files
  │
  ▼
... (rest of pipeline)
```
