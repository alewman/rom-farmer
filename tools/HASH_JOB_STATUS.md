# Hash Pre-calculation Job - Overnight Run

## Status: ✅ RUNNING (Started Oct 12, 2025 05:19 AM)

**PID:** Check with `ps aux | grep precalculate-hashes.sh`

## Job Details

- **Source:** `/data/emu/source/myrient.erista.me/files`
- **Archives:** 102,159 ZIP files (No-Intro + Redump)
- **Parallel Jobs:** 12 workers
- **Database:** `/data/emu/rom-farmer/metadata/database/romfarmer.db`
- **Estimated Time:** 15-30 hours

## What It's Doing

For each ZIP archive:
1. Extract inner ROM file to temp directory
2. Calculate hashes: CRC32, MD5, SHA1 (using rhash)
3. Store in database with key: `archive.zip::inner_file.rom`
4. Clean up temp file
5. Move to next archive

## Monitor Progress

```bash
# Watch progress log (real-time)
tail -f logs/hash-precalc/precalc_*_progress.txt

# Check database growth
watch -n 10 'sqlite3 metadata/database/romfarmer.db "SELECT COUNT(*) FROM hash_cache;"'

# Check for errors
tail -f logs/hash-precalc/precalc_*_errors.log

# Job status
ps aux | grep precalculate-hashes

# Recent progress (last 30 lines)
tail -30 logs/hash-precalc/precalc_*_progress.txt
```

## Log Files

All logs in: `/data/emu/rom-farmer/logs/hash-precalc/`

- `precalc_*_progress.txt` - Per-file progress (ARCHIVE/DONE/COMPLETE)
- `precalc_*_errors.log` - Errors only
- `precalc_*.log` - Main job log (start/end/summary)
- `nohup_FINAL_*.log` - Full output (includes all stderr/stdout)
- `parallel_results_*.txt` - Per-archive SUCCESS/SKIP/ERROR status

## Known Issues

### Database Insert Failures

Some entries are failing to insert into the database. Errors like:
```
ERROR: Database insert failed for: Pokemon Battle Card-e+ - Series 2 - 08-B006 (Japan).raw
```

**Cause:** Likely SQL escaping issue with special characters in filenames (apostrophes, dashes, etc.)

**Impact:** Job continues processing, but some hashes aren't being stored

**Fix Needed:** Update SQL escaping in `calculate_archive_hashes()` function
- Current: `${cache_key//\'/\'\'}`  (bash escape)
- May need: SQLite parameter binding or better escaping

### Hash Parsing (FIXED)

Earlier runs had issues parsing rhash output due to spaces in filenames.

**Solution Applied:**
- Changed from `--simple` to `--printf='%c %m %h\n'`
- Clean output: `<crc32> <md5> <sha1>` (space-separated, no filename)
- Parsing: `awk '{print $1}'`, `awk '{print $2}'`, `awk '{print $3}'`

**Status:** ✅ Working correctly in final run

## Success Metrics

Check database to see how many entries were successfully cached:

```bash
sqlite3 metadata/database/romfarmer.db <<SQL
SELECT 
    COUNT(*) as total_cached,
    SUM(file_size) / 1024.0 / 1024.0 / 1024.0 as total_gb,
    AVG(calculation_time) as avg_hash_time_sec,
    MIN(created_at) as first_entry,
    MAX(created_at) as last_entry
FROM hash_cache;
SQL
```

Sample output after completion:
```
total_cached   | 102000
total_gb       | 45.6
avg_hash_time  | 0.15
first_entry    | 2025-10-12 05:19:00
last_entry     | 2025-10-12 21:45:00
```

## Resume After Completion

When the job finishes (or if interrupted), you can resume with:

```bash
./tools/precalculate-hashes.sh --resume --jobs 12
```

This will:
- Skip files already in database (checks file_path + size + mtime)
- Only process new/changed files
- Much faster for incremental updates

## Next Steps (When Complete)

1. **Check Statistics**
   ```bash
   sqlite3 metadata/database/romfarmer.db "SELECT COUNT(*) FROM hash_cache;"
   ```

2. **Review Errors**
   ```bash
   grep "ERROR" logs/hash-precalc/precalc_*_errors.log | wc -l
   cat logs/hash-precalc/precalc_*_stats.json
   ```

3. **Fix Database Insert Issues**
   - Update SQL escaping in script
   - Re-run with `--resume` to catch failed entries

4. **Test Hash Lookup**
   ```bash
   sqlite3 metadata/database/romfarmer.db <<SQL
   SELECT file_path, crc32, md5, sha1 
   FROM hash_cache 
   WHERE file_path LIKE '%Zelda%' 
   LIMIT 5;
   SQL
   ```

5. **Integration**
   - Update compression scripts to query hash_cache before hashing
   - Add ScreenScraper lookup using cached hashes
   - Link to ROMTransformation table for tracking

## File Path Format

Hashes are stored with special path format:

```
Format: <archive_path>::<inner_filename>

Example:
/data/emu/source/myrient.erista.me/files/No-Intro/Nintendo - Game Boy/Zelda (USA).zip::Zelda (USA).gb

Components:
- Archive: /data/emu/source/.../Zelda (USA).zip
- Separator: ::
- Inner file: Zelda (USA).gb
```

This allows:
- Fast lookup without re-extraction
- Unique identification of ROM within archive
- Tracking of source archive location

## Estimated Completion

**Best case:** ~15 hours (fast disk, small ROMs)
**Worst case:** ~30 hours (slower disk, large disc images)
**Most likely:** ~20-24 hours

Check progress percentage:
```bash
# Count processed archives
grep "COMPLETE:" logs/hash-precalc/precalc_*_progress.txt | wc -l

# Total archives
echo "102159"

# Calculate percentage
python3 -c "print(f'{(PROCESSED/102159*100):.1f}%')"
```

## Troubleshooting

### Job Stopped Running

```bash
# Check if process exists
ps aux | grep precalculate-hashes

# Check exit status in nohup log
tail -50 logs/hash-precalc/nohup_FINAL_*.log

# Resume if needed
./tools/precalculate-hashes.sh --resume --jobs 12 > logs/hash-precalc/nohup_RESUME_$(date +%Y%m%d_%H%M%S).log 2>&1 &
```

### Disk Space Issues

```bash
# Check available space
df -h /data/emu

# Check log directory size
du -sh logs/hash-precalc/

# Clean up old test runs if needed
rm logs/hash-precalc/precalc_20251012_051* # (keep FINAL run)
```

### Database Locked

```bash
# Check for other processes
lsof metadata/database/romfarmer.db

# If locked, wait and retry
# SQLite allows one writer at a time
```

## Performance Tuning

If you want to adjust performance:

```bash
# Stop current job
pkill -f precalculate-hashes.sh

# Adjust parallel jobs (more = faster, but more disk I/O)
./tools/precalculate-hashes.sh --resume --jobs 16  # For 16-core system

# Or reduce if system is struggling
./tools/precalculate-hashes.sh --resume --jobs 6
```

## Success Criteria

Job is successful if:
- ✅ 100,000+ entries in hash_cache table
- ✅ Most archives processed (check COMPLETE count)
- ✅ No critical errors in error log
- ✅ Database file size ~500MB-2GB (depends on entry count)

---

## Sleep Well! 😴

The job will run overnight. In the morning:

1. Check if it's still running: `ps aux | grep precalculate`
2. Review progress: `tail -50 logs/hash-precalc/precalc_*_progress.txt`
3. Check database: `sqlite3 metadata/database/romfarmer.db "SELECT COUNT(*) FROM hash_cache;"`
4. Review this document for next steps

The hash cache will enable:
- ⚡ Instant hash lookups (no re-calculation)
- 🔍 ScreenScraper queries without decompression  
- 📊 DAT verification against No-Intro/Redump
- 🔗 ROM transformation tracking (source → final)

**Phase 2 integration coming next!**
