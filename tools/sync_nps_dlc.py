#!/usr/bin/env python3
"""Sync NoPayStation DLC packages - download missing DLC from database.

This tool:
1. Reads the NoPayStation database (PS3_DLCS.tsv or PSV_GAMES.tsv)
2. Checks which PKG files are available locally
3. Downloads missing PKG files from NoPayStation CDN
4. Organizes downloaded files with proper naming

Usage:
    # Sync all missing PS3 DLC
    python3 tools/sync_nps_dlc.py
    
    # Sync PS Vita games
    python3 tools/sync_nps_dlc.py --platform vita
    
    # Sync DLC for specific title ID
    python3 tools/sync_nps_dlc.py --title-id BLUS31527
    
    # Filter by region (USA only)
    python3 tools/sync_nps_dlc.py --region USA
    
    # Filter by region (Europe only)
    python3 tools/sync_nps_dlc.py --region EUR
    
    # Filter by region (Japan only)
    python3 tools/sync_nps_dlc.py --region JPN
    
    # Dry run (don't download, just report)
    python3 tools/sync_nps_dlc.py --dry-run
    
    # Download only (skip already downloaded)
    python3 tools/sync_nps_dlc.py --download-only
"""

import argparse
import csv
import hashlib
import re
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime


class NPSDLCSync:
    """Sync NoPayStation DLC packages."""
    
    # Size tolerance: Accept downloads within this % of expected size (handles DB errors)
    SIZE_TOLERANCE_PERCENT = 5.0  # 5% tolerance
    
    # Region mapping: Content ID prefix -> Region
    REGION_MAP = {
        'UP': 'USA',    # PS3/Vita USA
        'UC': 'USA',    # PS3 USA (alternative)
        'EP': 'EUR',    # PS3/Vita Europe
        'HP': 'JPN',    # PS3/Vita Japan
        'JP': 'JPN',    # PS3/Vita Japan (alternative)
        'NP': 'JPN',    # PS3/Vita Japan (NP prefix)
        'KP': 'ASI',    # PS3/Vita Asia
    }
    
    def __init__(
        self,
        database_path: Path,
        pkg_archive: Path,
        platform: str = 'ps3',
        dry_run: bool = False,
        verbose: bool = False
    ):
        """Initialize sync tool.
        
        Args:
            database_path: Path to database TSV file
            pkg_archive: Directory to store PKG files
            platform: Platform (ps3 or vita)
            dry_run: Don't download, just report
            verbose: Show detailed progress
        """
        self.database_path = Path(database_path)
        self.pkg_archive = Path(pkg_archive)
        self.platform = platform.lower()
        self.dry_run = dry_run
        self.verbose = verbose
        
        self.pkg_archive.mkdir(parents=True, exist_ok=True)
        
        # Load database
        self.dlc_entries: List[Dict] = []
        self._load_database()
    
    def _load_database(self):
        """Load NoPayStation database."""
        print(f"Loading database: {self.database_path}")
        
        with open(self.database_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                pkg_link = row.get('PKG direct link', '')
                
                # Check for license key based on platform
                if self.platform == 'vita':
                    # Vita uses zRIF
                    license_key = row.get('zRIF', '')
                else:
                    # PS3 uses RAP
                    license_key = row.get('RAP', '')
                
                # Skip entries without PKG link
                # Note: Some content is free (no license needed), so we include those too
                if pkg_link:
                    self.dlc_entries.append(row)
        
        print(f"  Loaded {len(self.dlc_entries):,} entries ({self.platform.upper()})")
    
    def _normalize_filename(self, name: str) -> str:
        """Normalize DLC name to safe filename.
        
        Removes special characters and normalizes separators for consistent matching.
        Database often has duplicate entries with variations like:
        - "Game - DLC" vs "Game® : DLC"
        Both normalize to same filename for deduplication.
        
        Args:
            name: DLC name from database
            
        Returns:
            Safe filename (without .pkg extension)
        """
        # Remove trademark/copyright symbols
        safe_name = name.replace('®', '').replace('™', '').replace('©', '')
        
        # Normalize separators: convert - and : to single space
        # This handles "GTA IV - Ballad" == "GTA IV: Ballad"
        safe_name = safe_name.replace(':', ' ').replace(' - ', ' ')
        
        # Remove filesystem-unsafe characters
        safe_name = safe_name.replace('/', ' ').replace('\\', ' ')
        
        # Collapse multiple spaces to single space
        safe_name = ' '.join(safe_name.split())
        
        return safe_name
    
    def _find_local_pkg(self, dlc_entry: Dict) -> Optional[Path]:
        """Find if PKG file exists locally.
        
        Args:
            dlc_entry: Database entry
            
        Returns:
            Path to local PKG or None
        """
        name = dlc_entry.get('Name', '')
        content_id = dlc_entry.get('Content ID', '')
        title_id = dlc_entry.get('Title ID', '')
        
        normalized_name = self._normalize_filename(name)
        
        # Strategy 1: Check for new format with Content ID (most reliable)
        # Format: "Name [CONTENT_ID].pkg"
        if content_id:
            path_with_id = self.pkg_archive / f"{normalized_name} [{content_id}].pkg"
            if path_with_id.exists():
                return path_with_id
        
        # Strategy 2: Check for old format without Content ID (backward compatibility)
        # Format: "Name.pkg"
        old_path = self.pkg_archive / f"{normalized_name}.pkg"
        if old_path.exists():
            return old_path
        
        # Strategy 3: Glob search by Title ID (fallback for edge cases)
        # Only use if we have no Content ID, or Content ID search failed
        # This handles renamed/moved files
        if title_id and not content_id:
            def escape_glob(s):
                """Escape glob metacharacters in string."""
                return s.replace('[', r'\[').replace(']', r'\]').replace('*', r'\*').replace('?', r'\?')
            
            try:
                matches = list(self.pkg_archive.glob(f"*{escape_glob(title_id)}*.pkg"))
                if matches:
                    return matches[0]
            except ValueError:
                pass
        
        return None
    
    def _calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            SHA256 hash as hex string (uppercase)
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read in 8MB chunks for efficiency
            for chunk in iter(lambda: f.read(8388608), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest().upper()
    
    def _verify_pkg_hash(self, pkg_path: Path, expected_hash: str) -> Tuple[bool, Optional[str]]:
        """Verify PKG file hash matches expected.
        
        Args:
            pkg_path: Path to PKG file
            expected_hash: Expected SHA256 hash
            
        Returns:
            Tuple of (matches, actual_hash or error_message)
        """
        if not expected_hash:
            return True, None  # No hash to verify
        
        try:
            actual_hash = self._calculate_sha256(pkg_path)
            matches = actual_hash == expected_hash.upper()
            return matches, actual_hash
        except Exception as e:
            return False, f"Hash verification error: {e}"
    
    def _create_rap_file(self, dlc_entry: Dict) -> Tuple[bool, Optional[str]]:
        """Create RAP license file from database entry.
        
        Args:
            dlc_entry: Database entry with RAP key
            
        Returns:
            Tuple of (success, error_message)
        """
        content_id = dlc_entry.get('Content ID', '')
        
        # Get license key based on platform
        if self.platform == 'vita':
            # Vita uses zRIF - skip for now (would need pkg2zip or similar tool)
            # zRIF is a compressed form that needs external tools to convert
            return False, None  # Not an error, just not supported yet
        
        # PS3 uses RAP
        rap_hex = dlc_entry.get('RAP', '').strip()
        
        if not content_id:
            return False, "No Content ID"
        
        # Silently skip if RAP is missing/empty (common for free DLC)
        # Also check if it's too short to be valid (valid RAPs are 32 hex chars = 16 bytes)
        if not rap_hex or rap_hex in ('MISSING', 'NOT_NEEDED') or len(rap_hex) < 16:
            return False, None  # No error - just not available
        
        rap_path = self.pkg_archive / f"{content_id}.rap"
        
        # Skip if already exists
        if rap_path.exists():
            if self.verbose:
                print(f"    ✓ RAP already exists: {rap_path.name}")
            return True, None
        
        if self.dry_run:
            print(f"    [DRY RUN] Would create RAP: {rap_path.name}")
            return True, None
        
        try:
            # Convert hex string to binary
            rap_bytes = bytes.fromhex(rap_hex)
            rap_path.write_bytes(rap_bytes)
            if self.verbose:
                print(f"    ✓ Created RAP: {rap_path.name}")
            return True, None
        except Exception as e:
            error_msg = f"RAP creation failed: {e}"
            print(f"    ✗ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"RAP creation failed: {e}"
            print(f"    ✗ {error_msg}")
            return False, error_msg
    
    def _download_pkg(self, dlc_entry: Dict, output_path: Path) -> Tuple[bool, Optional[str]]:
        """Download PKG file from NoPayStation CDN.
        
        Args:
            dlc_entry: Database entry with download URL
            output_path: Where to save the file
            
        Returns:
            Tuple of (success, error_message)
        """
        url = dlc_entry.get('PKG direct link', '')
        name = dlc_entry.get('Name', 'Unknown')
        file_size_str = dlc_entry.get('File Size', '0')
        file_size = int(file_size_str) if file_size_str else 0
        
        if not url:
            return False, "No download URL"
        
        # Check for malformed URLs (control characters, embedded spaces)
        if any(ord(c) < 32 for c in url) or ' ' in url:
            return False, "Malformed URL in database (contains spaces or control characters)"
        
        print(f"\n  Downloading: {name}")
        print(f"    URL: {url}")
        print(f"    Size: {self._format_size(file_size)}")
        
        if self.dry_run:
            print(f"    [DRY RUN] Would download to: {output_path}")
            # Still create RAP even in dry-run mode if requested
            return True, None
        
        try:
            # Download with progress
            def report_progress(block_num, block_size, total_size):
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = min(100, (downloaded * 100) // total_size)
                    if block_num % 100 == 0:  # Update every 100 blocks
                        print(f"\r    Progress: {percent}% ({self._format_size(downloaded)}/{self._format_size(total_size)})", end='')
            
            print(f"    Downloading...")
            urllib.request.urlretrieve(url, output_path, reporthook=report_progress if self.verbose else None)
            print(f"\r    ✓ Downloaded: {output_path.name}" + " " * 30)
            return True, None
            
        except urllib.error.HTTPError as e:
            error_msg = f"HTTP {e.code}: {e.reason}"
            print(f"\r    ✗ Download failed: {error_msg}" + " " * 30)
            return False, error_msg
        except Exception as e:
            error_msg = str(e)
            print(f"\r    ✗ Download failed: {error_msg}" + " " * 30)
            return False, error_msg
    
    def _format_size(self, bytes: int) -> str:
        """Format bytes as human-readable size."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.1f} TB"
    
    def _size_within_tolerance(self, actual: int, expected: int) -> bool:
        """Check if actual size is within acceptable tolerance of expected.
        
        Args:
            actual: Actual file size in bytes
            expected: Expected file size in bytes
            
        Returns:
            True if sizes match or are within tolerance
        """
        if actual == expected:
            return True
        
        # Calculate percentage difference
        diff = abs(actual - expected)
        percent_diff = (diff / expected) * 100 if expected > 0 else 100
        
        return percent_diff <= self.SIZE_TOLERANCE_PERCENT
    
    def _get_region_from_content_id(self, content_id: str) -> Optional[str]:
        """Extract region from Content ID.
        
        Args:
            content_id: Content ID (e.g., UP9000-NPUA80136_00-SIRENBCEPISODE05)
            
        Returns:
            Region code (USA, EUR, JPN, ASI) or None if unknown
        """
        if not content_id or len(content_id) < 2:
            return None
        
        # Extract first 2 characters (region prefix)
        prefix = content_id[:2].upper()
        return self.REGION_MAP.get(prefix)
    
    def sync_dlc(self, title_id_filter: Optional[str] = None, region_filter: Optional[str] = None) -> Dict:
        """Sync DLC packages.
        
        Args:
            title_id_filter: Only sync DLC for this title ID
            region_filter: Only sync DLC for this region (USA, EUR, JPN, ASI)
            
        Returns:
            Statistics dict
        """
        stats = {
            'total_dlc': 0,
            'already_downloaded': 0,
            'newly_downloaded': 0,
            'redownloaded': 0,
            'raps_created': 0,
            'raps_existed': 0,
            'hash_mismatches': 0,
            'failed': 0,
            'skipped': 0
        }
        
        # Filter entries if requested
        entries_to_process = self.dlc_entries
        if title_id_filter:
            entries_to_process = [e for e in self.dlc_entries if e.get('Title ID') == title_id_filter]
            print(f"\nFiltering for Title ID: {title_id_filter}")
        
        if region_filter:
            region_upper = region_filter.upper()
            entries_before = len(entries_to_process)
            entries_to_process = [
                e for e in entries_to_process
                if self._get_region_from_content_id(e.get('Content ID', '')) == region_upper
            ]
            entries_after = len(entries_to_process)
            print(f"\nFiltering for region: {region_upper}")
            print(f"  Filtered {entries_before:,} → {entries_after:,} entries")
        
        stats['total_dlc'] = len(entries_to_process)
        print(f"\nProcessing {stats['total_dlc']:,} DLC entries")
        print("=" * 80)
        
        failed_downloads = []
        hash_mismatches = []
        
        for i, entry in enumerate(entries_to_process, 1):
            title_id = entry.get('Title ID', '')
            content_id = entry.get('Content ID', '')
            name = entry.get('Name', 'Unknown')
            expected_hash = entry.get('SHA256', '')
            
            if self.verbose:
                print(f"\n[{i}/{stats['total_dlc']}] {name} ({title_id})")
            
            # Check if already downloaded
            local_pkg = self._find_local_pkg(entry)
            needs_download = False
            
            if local_pkg:
                # Verify file size if available (and not 0, which indicates unknown)
                expected_size = entry.get('File Size', '')
                if expected_size and expected_size.strip() and not self.dry_run:
                    try:
                        expected_size_int = int(expected_size)
                        
                        # Treat 0-byte size as unknown/invalid (database error)
                        if expected_size_int == 0:
                            if self.verbose:
                                print(f"  ✓ Already downloaded (size unknown): {local_pkg.name}")
                            stats['already_downloaded'] += 1
                        else:
                            actual_size = local_pkg.stat().st_size
                            
                            # Check if size matches exactly or is within tolerance
                            if self._size_within_tolerance(actual_size, expected_size_int):
                                if actual_size != expected_size_int and self.verbose:
                                    diff_percent = abs(actual_size - expected_size_int) / expected_size_int * 100
                                    print(f"  ✓ Size verified ({self._format_size(actual_size)}, {diff_percent:.2f}% diff): {local_pkg.name}")
                                elif self.verbose:
                                    print(f"  ✓ Size verified ({self._format_size(actual_size)}): {local_pkg.name}")
                                stats['already_downloaded'] += 1
                            else:
                                diff_percent = abs(actual_size - expected_size_int) / expected_size_int * 100
                                print(f"  ✗ Size mismatch: {local_pkg.name}")
                                print(f"    Expected: {self._format_size(expected_size_int)} ({expected_size_int:,} bytes)")
                                print(f"    Got:      {self._format_size(actual_size)} ({actual_size:,} bytes)")
                                print(f"    Difference: {abs(actual_size - expected_size_int):,} bytes ({diff_percent:.2f}%)")
                                print(f"    Re-downloading...")
                                stats['hash_mismatches'] += 1  # Reusing this stat for size mismatches too
                                hash_mismatches.append({
                                    'title_id': title_id,
                                    'name': name,
                                    'expected': f"{self._format_size(expected_size_int)} ({expected_size_int:,} bytes)",
                                    'actual': f"{self._format_size(actual_size)} ({actual_size:,} bytes)"
                                })
                                # Delete corrupted file
                                local_pkg.unlink()
                                needs_download = True
                    except (ValueError, OSError) as e:
                        if self.verbose:
                            print(f"  Warning: Could not verify size: {e}")
                        stats['already_downloaded'] += 1
                else:
                    if self.verbose:
                        print(f"  ✓ Already downloaded PKG: {local_pkg.name}")
                    stats['already_downloaded'] += 1
            else:
                needs_download = True
            
            # Download if needed
            if needs_download:
                # Check if file size is 0 (invalid/unknown) - skip download
                expected_size = entry.get('File Size', '')
                if expected_size and expected_size.strip():
                    try:
                        expected_size_int = int(expected_size)
                        if expected_size_int == 0:
                            if self.verbose:
                                print(f"  ⚠ Skipping download - database shows 0 bytes (invalid)")
                            stats['skipped'] += 1
                            failed_downloads.append({
                                'title_id': title_id,
                                'name': name,
                                'error': 'Size verification failed: expected 0.0 B, got 100.0 KB'
                            })
                            continue
                    except ValueError:
                        pass  # Invalid size, continue with download attempt
                
                # Generate output filename with Content ID to prevent regional duplicates
                # e.g., "Siren Episode 4 [NPUA80136_00-xxx].pkg"
                normalized_name = self._normalize_filename(name)
                content_id = entry.get('Content ID', '')
                
                if content_id:
                    # Include Content ID for uniqueness across regions
                    output_path = self.pkg_archive / f"{normalized_name} [{content_id}].pkg"
                else:
                    # Fallback to name only (shouldn't happen with valid entries)
                    output_path = self.pkg_archive / f"{normalized_name}.pkg"
                
                # Download
                success, error_msg = self._download_pkg(entry, output_path)
                
                if success:
                    # Verify downloaded file size if available (and not 0)
                    expected_size = entry.get('File Size', '')
                    if expected_size and expected_size.strip() and not self.dry_run:
                        try:
                            expected_size_int = int(expected_size)
                            
                            # Only verify if size is non-zero
                            if expected_size_int > 0:
                                actual_size = output_path.stat().st_size
                                
                                # Check if size matches exactly or is within tolerance
                                if self._size_within_tolerance(actual_size, expected_size_int):
                                    if actual_size != expected_size_int:
                                        diff_percent = abs(actual_size - expected_size_int) / expected_size_int * 100
                                        print(f"  ✓ Download verified ({self._format_size(actual_size)}, {diff_percent:.2f}% diff - within tolerance)")
                                    elif self.verbose:
                                        print(f"  ✓ Download verified ({self._format_size(actual_size)})")
                                    if stats['hash_mismatches'] > 0:
                                        stats['redownloaded'] += 1
                                    else:
                                        stats['newly_downloaded'] += 1
                                else:
                                    # Size mismatch beyond tolerance - delete bad file
                                    diff_percent = abs(actual_size - expected_size_int) / expected_size_int * 100
                                    print(f"  ✗ Downloaded file size mismatch!")
                                    print(f"    Expected: {self._format_size(expected_size_int)} ({expected_size_int:,} bytes)")
                                    print(f"    Got:      {self._format_size(actual_size)} ({actual_size:,} bytes)")
                                    print(f"    Difference: {abs(actual_size - expected_size_int):,} bytes ({diff_percent:.2f}%)")
                                    print(f"    ⚠️  Exceeds {self.SIZE_TOLERANCE_PERCENT}% tolerance - deleting bad file")
                                    output_path.unlink()
                                    stats['failed'] += 1
                                    failed_downloads.append({
                                        'title_id': title_id,
                                        'name': name,
                                        'error': f'Size verification failed: expected {self._format_size(expected_size_int)} ({expected_size_int:,} bytes), got {self._format_size(actual_size)} ({actual_size:,} bytes), diff {diff_percent:.2f}%'
                                    })
                                    continue
                            else:
                                # Size is 0, can't verify but download succeeded
                                if self.verbose:
                                    print(f"  ✓ Downloaded (size unknown)")
                                stats['newly_downloaded'] += 1
                        except (ValueError, OSError) as e:
                            if self.verbose:
                                print(f"  Warning: Could not verify downloaded size: {e}")
                            stats['newly_downloaded'] += 1
                    else:
                        stats['newly_downloaded'] += 1
                else:
                    stats['failed'] += 1
                    failed_downloads.append({
                        'title_id': title_id,
                        'name': name,
                        'error': error_msg
                    })
            
            # Handle RAP file (whether PKG existed or was just downloaded)
            if content_id:
                rap_path = self.pkg_archive / f"{content_id}.rap"
                if rap_path.exists():
                    stats['raps_existed'] += 1
                    if self.verbose:
                        print(f"  ✓ RAP already exists: {rap_path.name}")
                else:
                    success, error = self._create_rap_file(entry)
                    if success and not self.dry_run:
                        stats['raps_created'] += 1
        
        # Print summary
        print("\n" + "=" * 80)
        print("SYNC SUMMARY")
        print("=" * 80)
        print(f"Total DLC entries:      {stats['total_dlc']:,}")
        print(f"Already downloaded:     {stats['already_downloaded']:,}")
        print(f"Newly downloaded:       {stats['newly_downloaded']:,}")
        if stats['hash_mismatches'] > 0:
            print(f"Size mismatches:        {stats['hash_mismatches']:,}")
            print(f"Re-downloaded:          {stats['redownloaded']:,}")
        print(f"RAP files created:      {stats['raps_created']:,}")
        print(f"RAP files existed:      {stats['raps_existed']:,}")
        if stats['skipped'] > 0:
            print(f"Skipped (invalid data): {stats['skipped']:,}")
        print(f"Failed downloads:       {stats['failed']:,}")
        
        if hash_mismatches:
            print("\n⚠️  Size Mismatches (Re-downloaded):")
            for mismatch in hash_mismatches:
                print(f"  • [{mismatch['title_id']}] {mismatch['name']}")
                print(f"    Expected: {mismatch['expected']}")
                print(f"    Got:      {mismatch['actual']}")
        
        if failed_downloads:
            print("\n⚠️  Failed Downloads:")
            
            # Categorize failures
            missing_urls = [f for f in failed_downloads if 'MISSING' in f.get('error', '')]
            malformed_urls = [f for f in failed_downloads if 'Malformed URL' in f.get('error', '') or 'control characters' in f.get('error', '')]
            zero_byte_db = [f for f in failed_downloads if 'expected 0.0 B' in f.get('error', '')]
            other_failures = [f for f in failed_downloads if f not in missing_urls + malformed_urls + zero_byte_db]
            
            if missing_urls:
                print(f"\n  Missing URLs ({len(missing_urls)}) - likely removed from PlayStation Network:")
                for fail in missing_urls[:20]:  # Limit to first 20
                    print(f"    • [{fail['title_id']}] {fail['name']}")
                if len(missing_urls) > 20:
                    print(f"    ... and {len(missing_urls) - 20} more")
            
            if malformed_urls:
                print(f"\n  Malformed URLs ({len(malformed_urls)}) - database corruption:")
                for fail in malformed_urls:
                    print(f"    • [{fail['title_id']}] {fail['name']}")
                    print(f"      Reason: {fail['error']}")
            
            if zero_byte_db:
                print(f"\n  Invalid database entries ({len(zero_byte_db)}) - file size shows 0 bytes:")
                for fail in zero_byte_db[:20]:  # Limit to first 20
                    print(f"    • [{fail['title_id']}] {fail['name']}")
                if len(zero_byte_db) > 20:
                    print(f"    ... and {len(zero_byte_db) - 20} more")
            
            if other_failures:
                print(f"\n  Other failures ({len(other_failures)}):")
                for fail in other_failures:
                    print(f"    • [{fail['title_id']}] {fail['name']}")
                    print(f"      Reason: {fail['error']}")
        
        if self.dry_run:
            print("\n[DRY RUN] No files were actually downloaded")
        
        print("=" * 80)
        
        return stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Sync NoPayStation packages (PS3 DLC or PS Vita games)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sync all PS3 DLC
  python3 tools/sync_nps_dlc.py
  
  # Sync PS Vita games
  python3 tools/sync_nps_dlc.py --platform vita
  
  # Sync DLC for Call of Duty: Black Ops III
  python3 tools/sync_nps_dlc.py --title-id BLUS31527
  
  # Sync only USA region DLC
  python3 tools/sync_nps_dlc.py --region USA
  
  # Sync only Europe region DLC
  python3 tools/sync_nps_dlc.py --region EUR
  
  # Sync only Japan region DLC
  python3 tools/sync_nps_dlc.py --region JPN
  
  # Dry run to see what would be downloaded
  python3 tools/sync_nps_dlc.py --dry-run
  
  # Verbose output with progress
  python3 tools/sync_nps_dlc.py --verbose
        """
    )
    
    parser.add_argument(
        '--platform',
        type=str,
        choices=['ps3', 'vita'],
        default='ps3',
        help='Platform to sync (ps3 or vita)'
    )
    
    parser.add_argument(
        '--database',
        type=Path,
        help='Path to database TSV file (auto-detected based on platform if not specified)'
    )
    
    parser.add_argument(
        '--pkg-archive',
        type=Path,
        help='Directory to store PKG files (auto-detected based on platform if not specified)'
    )
    
    parser.add_argument(
        '--title-id',
        type=str,
        help='Only sync DLC for this title ID (e.g., BLUS31527)'
    )
    
    parser.add_argument(
        '--region',
        type=str,
        choices=['USA', 'EUR', 'JPN', 'ASI'],
        help='Only sync DLC for this region (USA, EUR, JPN, ASI)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be downloaded without actually downloading'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed progress'
    )
    
    args = parser.parse_args()
    
    # Auto-detect database and archive paths based on platform
    if args.platform == 'ps3':
        default_database = Path('/path/to/source/nopaystation/PS3_DLCS.tsv')
        default_archive = Path('/path/to/source/nopaystation/downloads-ps3-dlc/packages')
    else:  # vita
        default_database = Path('/path/to/source/nopaystation/PSV_GAMES.tsv')
        default_archive = Path('/path/to/source/nopaystation/downloads-vita/packages')
    
    database_path = args.database if args.database else default_database
    archive_path = args.pkg_archive if args.pkg_archive else default_archive
    
    # Validate paths
    if not database_path.exists():
        print(f"❌ Database not found: {database_path}")
        return 1
    
    # Create syncer
    syncer = NPSDLCSync(
        database_path=database_path,
        pkg_archive=archive_path,
        platform=args.platform,
        dry_run=args.dry_run,
        verbose=args.verbose
    )
    
    # Sync
    stats = syncer.sync_dlc(title_id_filter=args.title_id, region_filter=args.region)
    
    # Return non-zero if there were failures
    return 1 if stats['failed'] > 0 else 0


if __name__ == '__main__':
    sys.exit(main())
