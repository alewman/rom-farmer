# Hash Pre-calculation Script

## Overview

Pre-calculates and caches hashes (CRC32, MD5, SHA1) for all source ROM files in `/data/emu/source`. This creates a fast lookup cache that eliminates re-hashing during compression operations.

## Features

- ✅ **Parallel Processing**: Uses GNU parallel with configurable job count (default: 8)
- ✅ **Comprehensive Logging**: Main log, error log, progress log, stats JSON
- ✅ **Resume Capability**: Skip already-cached files with `--resume`
- ✅ **Smart Caching**: Checks file size + mtime to detect changes
- ✅ **Multi-hash**: Calculates CRC32, MD5, SHA1 in one pass (rhash)
- ✅ **Progress Monitoring**: Real-time progress bar with GNU parallel
- ✅ **Error Handling**: Continues on errors, logs everything
- ✅ **Dry Run Mode**: Test without database changes

## Usage

```bash
# Full run (first time - will take hours)
./tools/precalculate-hashes.sh

# Resume interrupted run (skips cached files)
./tools/precalculate-hashes.sh --resume

# Dry run (no database changes)
./tools/precalculate-hashes.sh --dry-run

# Custom parallel jobs (adjust for CPU cores)
./tools/precalculate-hashes.sh --jobs 16

# Combined options
./tools/precalculate-hashes.sh --resume --jobs 12
```

## Supported File Types

### Cartridge ROMs (No-Intro)
- Nintendo: `.nes`, `.fds`, `.sfc`, `.n64`, `.gb`, `.gbc`, `.gba`, `.nds`, `.3ds`, `.cia`
- Sega: `.gen`, `.md`, `.smd`, `.gg`, `.sms`
- Other: `.pce`, `.sgx`, `.ws`, `.wsc`, `.ngp`, `.ngc`, `.a26`, `.a52`, `.a78`, `.lnx`, `.col`, `.vec`, `.jag`, `.j64`

### Disc Images (Redump)
- Raw: `.iso`, `.bin`, `.img`
- Cue sheets: `.cue`, `.gdi`, `.ccd`, `.mds`, `.nrg`

### Compressed Archives
- `.7z`, `.zip`, `.rar`

### Processed Formats (for verification)
- `.chd`, `.cso`, `.rvz`, `.wbfs`, `.wux`, `.xiso`, `.nsz`, `.xcz`

## Performance

**Estimated Time** (for large collection):
- 10,000 files @ ~50 MB average: ~3-4 hours (8 parallel jobs)
- 50,000 files @ ~50 MB average: ~15-20 hours (8 parallel jobs)
- 100,000 files @ ~10 MB average: ~10-15 hours (8 parallel jobs)

**Speed Factors**:
- Disk I/O (SSD vs HDD)
- CPU cores (more jobs = faster)
- File sizes (larger = slower per file)
- Archive contents (7z/zip slower due to extraction)

**Optimization Tips**:
- Use `--jobs` matching your CPU core count
- Run on SSD for best performance
- Use `--resume` for incremental updates
- Monitor with: `tail -f logs/hash-precalc/precalc_*_progress.txt`

## Logs

All logs stored in: `/data/emu/rom-farmer/logs/hash-precalc/`

### Log Files

**Main Log** (`precalc_YYYYMMDD_HHMMSS.log`)
- Overall progress
- Summary statistics
- Start/end times

**Error Log** (`precalc_YYYYMMDD_HHMMSS_errors.log`)
- Failed file paths
- Hash calculation errors
- Database errors

**Progress Log** (`precalc_YYYYMMDD_HHMMSS_progress.txt`)
- Per-file status (SKIP/HASH/DONE/ERROR)
- Real-time monitoring file
- Use with: `tail -f`

**Stats JSON** (`precalc_YYYYMMDD_HHMMSS_stats.json`)
- Machine-readable statistics
- Success/skip/error counts
- Configuration used

**File List** (`file_list_YYYYMMDD_HHMMSS.txt`)
- All discovered files (path, size, mtime)
- Can be reused for debugging

**Parallel Results** (`parallel_results_YYYYMMDD_HHMMSS.txt`)
- Per-file SUCCESS/SKIP/ERROR status
- Used for final statistics

## Monitoring

### Real-time Progress
```bash
# Watch progress log
tail -f logs/hash-precalc/precalc_*_progress.txt

# Watch main log
tail -f logs/hash-precalc/precalc_*.log

# Check database growth
watch -n 10 'sqlite3 metadata/romfarmer.db "SELECT COUNT(*) FROM hash_cache;"'

# Monitor errors
tail -f logs/hash-precalc/precalc_*_errors.log
```

### Check Status
```bash
# Database statistics
sqlite3 metadata/romfarmer.db <<SQL
SELECT 
    COUNT(*) as total_files,
    SUM(file_size) / 1024.0 / 1024.0 / 1024.0 as total_gb,
    AVG(calculation_time) as avg_time_sec
FROM hash_cache;
SQL

# Recent hashes
sqlite3 metadata/romfarmer.db <<SQL
SELECT file_path, crc32, calculation_time
FROM hash_cache
ORDER BY created_at DESC
LIMIT 10;
SQL
```

## Resume After Interruption

If the script is interrupted (Ctrl+C, power loss, etc.):

```bash
# Resume - skips already cached files
./tools/precalculate-hashes.sh --resume
```

The script checks file size + mtime, so only new/changed files are re-hashed.

## Integration

### Compression Scripts
```python
# In Python transformation scripts
from romfarmer.models import HashCache

# Check cache first
cached = db.query(HashCache).filter_by(
    file_path=source_file,
    file_size=os.path.getsize(source_file),
    mtime=int(os.path.getmtime(source_file))
).first()

if cached:
    # Use cached hashes - instant!
    source_md5 = cached.md5
    source_sha1 = cached.sha1
    source_crc32 = cached.crc32
else:
    # Calculate on-the-fly (fallback)
    # ...
```

### ScreenScraper Queries
```python
# Query by hash without decompression
def lookup_screenscraper(file_path):
    cached = get_cached_hash(file_path)
    if cached:
        # Query ScreenScraper API with cached hash
        return screenscraper_api.get_game_info(
            crc32=cached.crc32,
            md5=cached.md5
        )
```

## Database Schema

```sql
CREATE TABLE hash_cache (
    id INTEGER PRIMARY KEY,
    file_path TEXT NOT NULL UNIQUE,
    file_size INTEGER NOT NULL,
    mtime REAL NOT NULL,
    crc32 TEXT,
    md5 TEXT,
    sha1 TEXT,
    sha256 TEXT,
    calculation_time INTEGER,  -- seconds
    created_at DATETIME,
    updated_at DATETIME
);

CREATE INDEX idx_hash_cache_md5 ON hash_cache(md5);
CREATE INDEX idx_hash_cache_sha1 ON hash_cache(sha1);
CREATE INDEX idx_hash_cache_crc32 ON hash_cache(crc32);
CREATE INDEX idx_hash_cache_path ON hash_cache(file_path);
```

## Troubleshooting

### Script Fails to Start
```bash
# Check dependencies
rhash --version
parallel --version
sqlite3 --version

# Check database exists
ls -lh metadata/romfarmer.db

# Check source directory
ls -lh /data/emu/source/
```

### Too Slow
```bash
# Increase parallel jobs
./tools/precalculate-hashes.sh --jobs 16

# Check disk I/O (should be mostly read)
iostat -x 5

# Check CPU usage
htop
```

### Database Locked
```bash
# Check for other processes
lsof metadata/romfarmer.db

# Wait and retry
```

### Out of Disk Space
```bash
# Check log directory size
du -sh logs/hash-precalc/

# Clean old logs
find logs/hash-precalc/ -name "*.log" -mtime +30 -delete
```

## Benefits

### Before (without cache)
- Hash calculation: 30-60s per large disc image
- Total time: Recalculate every compression run
- ScreenScraper: Must decompress to identify

### After (with cache)
- Hash lookup: <1ms (database query)
- Total time: One-time 10-20 hour investment
- ScreenScraper: Instant lookup, no decompression

### Example Time Savings
**50 Wii games (235 GB):**
- Without cache: 25-50 minutes per batch (recalculate each time)
- With cache: <1 second (database lookup)
- **Savings: ~25-50 minutes per run!**

## Next Steps

After pre-calculation completes:

1. ✅ **Verify**: Check stats JSON and logs
2. ✅ **Integrate**: Update compression scripts to use cache
3. ✅ **Transform**: Run compression with cached hashes
4. ✅ **Scrape**: Query ScreenScraper with pre-calculated hashes
5. ✅ **Maintain**: Run `--resume` after rclone sync updates

## Incremental Updates

After running rclone sync:

```bash
# Hash only new/changed files
./tools/precalculate-hashes.sh --resume --jobs 12

# Takes minutes instead of hours!
```

The script detects changes via mtime (modification time), so only new or modified files are re-hashed.
