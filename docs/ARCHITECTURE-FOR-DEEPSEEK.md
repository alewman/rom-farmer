# ROM Farmer Architecture - Complete Technical Summary

**Date:** December 20, 2025  
**Purpose:** Provide Deepseek with accurate technical details for comparison research

---

## Executive Summary

ROM Farmer is a **27,584-line Python application** for automated ROM collection curation. It implements a sophisticated pipeline architecture with:

- **20 specialized stage classes** (8,664 LOC in stages alone)
- **Hash transformation database** tracking source→final hashes across format conversions
- **Live Sony PSN API integration** for PS3 game updates
- **3-tier smart hash caching** with 20-50x speedup
- **Multi-source merging** (Main + Aftermarket + Private folders)
- **Rating-based budget selection** with storage awareness
- **Resume capability** for interrupted builds

---

## 1. Core Technical Functionality

### 1.1 Pipeline Stages (20 Stage Classes)

| Stage File | Purpose | Platforms |
|------------|---------|-----------|
| `filter_dat.py` | Match against No-Intro/Redump DATs | All |
| `filter_1g1r.py` | Apply Retool 1G1R filtering | All |
| `filter_selection.py` | Rating-based budget selection | All |
| `filter_rating.py` | Filter by ScreenScraper ratings | All |
| `apply_lists.py` | Apply delete/keep curated lists | All |
| `pre_filter.py` | Pre-processing filter step | All |
| `extract.py` | Generic archive extraction | All |
| `extract_ps3.py` | PS3 decryption + JB extraction | PS3 |
| `transform_ps3.py` | PS3 multi-target transforms | PS3 |
| `apply_ps3_updates.py` | Sony PSN + NoPayStation updates | PS3 |
| `convert_xiso.py` | Redump → XISO + SquashFS | Xbox/360 |
| `unzip_rvz.py` | RVZ extraction | Wii/GC |
| `compress.py` | CHD compression | Disc systems |
| `compress_archive.py` | 7z/zip compression | Cartridge |
| `m3u.py` | Multi-disc playlist generation | Multi-disc |
| `organize.py` | Folder organization | All |
| `metadata.py` | gamelist.xml generation | All |

### 1.2 Transformation Tracking Database

Full SQLAlchemy schema in `src/romfarmer/metadata/transformation.py`:

```python
class ROMTransformation(Base):
    """Tracks source ROM → final processed file transformations."""
    __tablename__ = "rom_transformations"
    
    # Source (what ScreenScraper knows - from DAT files)
    source_md5 = Column(String(32), index=True, nullable=False)
    source_sha1 = Column(String(40))
    source_sha256 = Column(String(64))
    source_crc32 = Column(String(8))
    source_file_size = Column(BigInteger)
    source_format = Column(String(32))  # "redump-iso", "nointro-zip"
    source_dat = Column(String(128))    # "Redump - Microsoft Xbox 360"
    source_verified = Column(Boolean)   # From official DAT?
    
    # Transformation metadata
    transformation_tool = Column(String(64))     # "extract-xiso", "chdman", "PS3Dec"
    transformation_version = Column(String(32))  # "2.7.1", "0.251"
    transformation_params = Column(JSON)         # {"compression": "zstd", "level": 19}
    transformation_duration_seconds = Column(Float)
    
    # Final (what's on your disk after conversion)
    final_md5 = Column(String(32), index=True)
    final_sha1 = Column(String(40))
    final_file_size = Column(BigInteger)
    final_format = Column(String(32))  # "xiso", "chd", "rvz", "jb-folder"
    
    # Community verification
    verified = Column(Boolean, default=False)
    verification_count = Column(Integer, default=0)
    
    # Link to game metadata
    game_id = Column(Integer, ForeignKey("scraped_games.id"))
```

**Use case:** When you have a CHD file (converted from Redump ISO), ROM Farmer can:
1. Look up the CHD's `final_md5` in the transformation table
2. Find the original `source_md5` (Redump verified hash)
3. Query ScreenScraper with the source hash
4. Get correct metadata even though the file format changed

### 1.3 Smart Hash Capture (3-Tier Strategy)

In `src/romfarmer/metadata/hash_capture.py`:

```python
class SmartHashCapture:
    """
    Tier 1: DAT lookup     → 0.001s (95% of files)
    Tier 2: Hash cache     → 0.1s   (4% of files)  
    Tier 3: Calculate      → 120s   (1% of files)
    
    Result: 20-50x speedup for source hash capture
    """
```

### 1.4 ZipContentCache (69x Speedup for Large Collections)

```python
class ZipContentCache(Base):
    """Cache ZIP header CRC32 → contained file MD5.
    
    For torrentzipped archives (Myrient), we read CRC32 from ZIP header
    (instant) and cache the expensive MD5 calculation.
    
    Performance:
    - Without cache: ~40 min (calculate MD5 for 2000+ GB of ISOs)
    - With cache: ~35 sec (read ZIP headers + DB lookup)
    """
    content_crc32 = Column(String(8), nullable=False)  # Instant from header
    content_md5 = Column(String(32), nullable=False)   # Cached calculation
```

---

## 2. Platform-Specific Implementations

### 2.1 PS3: 5-Stage Transformation Pipeline (1,583 LOC)

```
Stage 1 - UNZIP:    Myrient ZIP → Encrypted Redump ISO
Stage 2 - DECRYPT:  PS3Dec + disc key (.dkey) → Decrypted ISO
Stage 3 - EXTRACT:  7z → JB folder structure (PS3_GAME/PARAM.SFO)
Stage 4 - UPDATE:   Sony PSN API + NoPayStation → Apply official patches
Stage 5 - DLC:      PKG files → Copy mode (RPCS3) or Extract mode (CFW)
```

**Unique PS3 capabilities:**

1. **Sony PSN API Integration** - Queries live update servers:
   ```python
   class SonyPSNClient:
       base_url = "https://a0.ww.np.dl.playstation.net/tpl/np"
       
       def get_updates_for_title(self, title_id: str) -> List[Dict]:
           url = f"{self.base_url}/{title_id}/{title_id}-ver.xml"
           # Returns live update PKG URLs from Sony servers
   ```

2. **NoPayStation Database** - Parses PS3_DLCS.tsv for DLC/updates

3. **PKG Decryption** - pkgrip integration with Python fallback

4. **PARAM.SFO Tracking** - Uses stable PARAM.SFO hash as folder identifier (survives updates)

5. **RAP License Handling** - Creates .rap files for DLC activation

6. **Intelligent DLC Filtering:**
   ```python
   def _is_story_dlc(self, name: str, entry: Dict) -> bool:
       # Size check: story DLC is typically >100MB
       # Keyword filtering: skip "costume", "skin", "avatar"
       # Include: "campaign", "mission", "expansion"
   ```

### 2.2 Xbox/Xbox 360: 3-Stage Transformation (432 LOC)

```
Stage 1 - UNZIP:     Myrient ZIP → Redump full disc ISO
Stage 2 - XISO:      extract-xiso -r → XISO format (game partition only)
Stage 3 - SQUASHFS:  mksquashfs zstd-19 → .iso.squashfs (optional)
```

**Transformation recording:**
```python
def _record_transformation(self, context, xiso_file, source_md5, source_size):
    transformation = ROMTransformation(
        source_md5=source_md5,
        source_format='redump-iso',
        source_dat='Redump - Microsoft Xbox 360',
        final_md5=self._calculate_md5(xiso_file),
        final_format='xiso',
        transformation_tool='extract-xiso',
        transformation_version='2.7.1',
        transformation_params={"format": "xiso", "mode": "rewrite"},
    )
```

### 2.3 Saturn/PS1/PS2: CHD Pipeline

```
Stage 1 - Match:    Verify against Redump DAT
Stage 2 - Extract:  Unzip BIN/CUE files
Stage 3 - Compress: chdman createcd → CHD (lzma level 9)
Stage 4 - M3U:      Generate playlists for multi-disc games
```

---

## 3. Architectural Features

### 3.1 Multi-Source Merging

Platform configs support multiple Myrient folders:

```yaml
# config/platforms/gba.yaml
sources:
  - path: "No-Intro/Nintendo - Game Boy Advance"
  - path: "No-Intro/Nintendo - Game Boy Advance (Aftermarket)"
  - path: "No-Intro/Nintendo - Game Boy Advance (e-Reader)"
  - path: "No-Intro/Nintendo - Game Boy Advance (Multiboot)"
  - path: "No-Intro/Nintendo - Game Boy Advance (Play-Yan)"
  - path: "No-Intro/Nintendo - Game Boy Advance (Video)"
  - path: "No-Intro/Nintendo - Game Boy Advance (Private)"
```

### 3.2 Rating-Based Budget Selection

```python
class SelectionConfig:
    strategy: str = "rating_budget"  # Use ScreenScraper ratings
    max_size_gb: float = 100.0       # Storage budget
    min_rating: float = 0.6          # Minimum quality threshold
    
# Fits highest-rated games into storage target
```

### 3.3 Storage Budget Awareness

```python
class StorageBudget:
    raw_capacity_bytes: int        # Advertised (512GB)
    formatted_capacity_bytes: int  # After formatting (93%)
    reserved_bytes: int            # For OS, saves (20GB default)
    available_bytes: int           # Actual ROM budget
```

### 3.4 Build State & Resume Capability

```python
class BuildState:
    build_name: str
    started_at: datetime
    completed_platforms: List[str]
    failed_platforms: List[str]
    current_platform: Optional[str]
    status: BuildStatus  # NOT_STARTED, RUNNING, PAUSED, COMPLETED, FAILED
```

Persisted to `.build_state_{name}.yaml` - interrupted builds resume where they left off.

### 3.5 Multi-Target Output

One source can produce multiple formats:

```yaml
# config/platforms/ps3.yaml
targets:
  - name: ps3netsrv
    output_path: /data/emu/ps3netsrv/GAMES
    # JB folder format, no .ps3 suffix
    
  - name: batocera
    output_path: /data/emu/roms/ps3
    # JB folder with .ps3 suffix
    
  - name: rpcs3
    output_path: ~/Games/RPCS3
    # Optimized for RPCS3 emulator
```

---

## 4. Code Statistics

| Component | Lines of Code |
|-----------|---------------|
| **Stages** (`src/romfarmer/stages/`) | 8,664 |
| **Metadata** (`src/romfarmer/metadata/`) | ~3,000 |
| **Build Orchestrator** | 952 |
| **Config/Core** | ~5,000 |
| **CLI/Commands** | ~2,000 |
| **Utils** | ~2,000 |
| **Other** | ~6,000 |
| **Total Python** | **27,584** |

Additional:
- 21+ platform YAML configs
- Multiple build configuration files
- Comprehensive test suite
- Documentation

---

## 5. Question for Deepseek

**ROM Farmer's claimed unique capabilities:**

1. ✅ **Hash transformation database** - Track source→final hash for metadata lookup after format conversion (Redump ISO → XISO → SquashFS, still find metadata)

2. ✅ **Live Sony PSN API integration** - Query update servers directly, not just static database downloads

3. ✅ **Multi-source merging** - Combine Main + Aftermarket + Private + specialty folders with DAT-based deduplication

4. ✅ **3-tier smart hash caching** - DAT lookup (instant) → cache (fast) → calculate (slow) with 20-50x speedup

5. ✅ **Rating/budget-based selection** - Fit highest-rated games into storage targets

6. ✅ **Pipeline resume capability** - Interrupt and continue large multi-platform builds

7. ✅ **Multi-target output** - One source → multiple destination formats simultaneously

**Research request:**

> Can you search for other open-source ROM curation/management tools and verify whether any have ALL of these capabilities combined?
> 
> We are particularly interested in:
> - Tools that track hash transformations for metadata lookup after format conversion
> - Tools that integrate with live update servers (not just static downloads)
> - Tools with pipeline architecture and resume capability
> - Tools with storage-aware budget-based selection
>
> Examples to compare against:
> - RomVault
> - CLRMamePro  
> - Romcenter
> - igir
> - Skyscraper
> - Retool
> - JDownloader ROM plugins
>
> We believe ROM Farmer may be the most comprehensive ROM curation pipeline in existence for the "middle processing" phase (between raw archives and final organized collection), but we'd like verification from someone with internet search capability.

---

## 6. What ROM Farmer Is NOT

To be clear about scope:

- **NOT a scraper** - Uses external tools (Skyscraper, RetroScraper, ARRM) for metadata
- **NOT a DAT creator** - Uses No-Intro/Redump DATs as authoritative sources
- **NOT an emulator frontend** - Outputs for EmulationStation/Batocera/etc.
- **NOT a download manager** - Assumes you have Myrient archives locally

ROM Farmer is specifically an **orchestration and transformation pipeline** that sits between "raw archives from Myrient" and "organized collection ready for emulation."

---

*Generated by ROM Farmer documentation system*
