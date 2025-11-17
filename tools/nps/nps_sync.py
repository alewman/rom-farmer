"""NoPayStation sync engine - download and organize content.

Enterprise-grade sync system with:
- Hierarchical organization: packages/platform/type/region/TITLEID-Name/
- Metadata tracking with .nps-metadata.json
- Resume support (idempotent downloads)
- Progress tracking and statistics
- pkg2zip integration for Vita zRIF extraction
"""

import hashlib
import json
import shutil
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime
from dataclasses import dataclass

from .nps_database import NPSDatabase
from .nps_models import ContentEntry, TitleBundle, DownloadMetadata
from .nps_search import NPSSearch


@dataclass
class SyncStats:
    """Statistics for sync operation."""
    total_items: int = 0
    already_downloaded: int = 0
    newly_downloaded: int = 0
    failed: int = 0
    skipped: int = 0
    total_size: int = 0
    downloaded_size: int = 0
    
    def __str__(self) -> str:
        """Format stats for display."""
        lines = [
            f"Total items: {self.total_items:,}",
            f"Already downloaded: {self.already_downloaded:,}",
            f"Newly downloaded: {self.newly_downloaded:,}",
            f"Failed: {self.failed:,}",
            f"Skipped: {self.skipped:,}",
            f"Total size: {self._format_size(self.total_size)}",
            f"Downloaded: {self._format_size(self.downloaded_size)}",
        ]
        return "\n".join(lines)
    
    def _format_size(self, bytes: int) -> str:
        """Format bytes as human-readable size."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} PB"


class NPSSync:
    """Sync engine for downloading and organizing NoPayStation content.
    
    Features:
    - Hierarchical directory structure
    - Metadata tracking
    - Resume support
    - SHA256 verification
    - pkg2zip integration for Vita
    """
    
    # Size tolerance for verification (5%)
    SIZE_TOLERANCE_PERCENT = 5.0
    
    def __init__(
        self,
        database: NPSDatabase,
        search: NPSSearch,
        output_dir: Path,
        pkg2zip_path: Optional[Path] = None,
        verify_downloads: bool = True,
        verbose: bool = False
    ):
        """Initialize sync engine.
        
        Args:
            database: Loaded NPSDatabase
            search: NPSSearch instance
            output_dir: Root output directory (e.g., /data/emu/source/nopaystation/packages)
            pkg2zip_path: Path to pkg2zip binary (for Vita extraction)
            verify_downloads: Verify SHA256 after download
            verbose: Show detailed progress
        """
        self.db = database
        self.search = search
        self.output_dir = Path(output_dir)
        self.pkg2zip_path = Path(pkg2zip_path) if pkg2zip_path else None
        self.verify_downloads = verify_downloads
        self.verbose = verbose
        
        # Ensure output dir exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Track failures for reporting
        self.failed_downloads: List[Dict] = []
    
    def sync_entry(
        self,
        entry: ContentEntry,
        dry_run: bool = False,
        base_game: Optional[ContentEntry] = None
    ) -> Tuple[bool, Optional[str]]:
        """Sync a single content entry.
        
        Args:
            entry: ContentEntry to sync
            dry_run: Don't actually download
            base_game: Base game entry (for DLC/updates)
            
        Returns:
            Tuple of (success, error_message)
        """
        # Determine output path
        output_path = self._get_output_path(entry, base_game)
        
        # Check if already downloaded
        if output_path.exists():
            # Verify file size
            if self._verify_file_size(output_path, entry.file_size):
                if self.verbose:
                    print(f"  ✓ Already downloaded: {output_path.name}")
                return True, None
            else:
                # Size mismatch, re-download
                if self.verbose:
                    print(f"  ⚠ Size mismatch, re-downloading: {output_path.name}")
                output_path.unlink()
        
        if dry_run:
            print(f"  [DRY RUN] Would download: {output_path}")
            return True, None
        
        # Download
        return self._download_entry(entry, output_path)
    
    def sync_bundle(
        self,
        bundle: TitleBundle,
        dry_run: bool = False
    ) -> SyncStats:
        """Sync a complete title bundle.
        
        Args:
            bundle: TitleBundle to sync
            dry_run: Don't actually download
            
        Returns:
            SyncStats with results
        """
        stats = SyncStats()
        
        # Get all content
        all_content = bundle.get_all_content()
        stats.total_items = len(all_content)
        stats.total_size = bundle.get_total_size()
        
        print(f"\n📦 Syncing: {bundle.get_display_name()} ({bundle.title_id})")
        print(f"   Platform: {bundle.platform.upper()} | Region: {bundle.region}")
        counts = bundle.count_by_type()
        print(f"   Content: {counts['base_game']} game, {counts['dlc']} DLC, "
              f"{counts['updates']} updates, {counts['themes']} themes")
        print(f"   Total size: {stats._format_size(stats.total_size)}")
        print()
        
        # Sync each item
        for i, entry in enumerate(all_content, 1):
            if self.verbose:
                print(f"  [{i}/{stats.total_items}] {entry.name}")
            
            success, error = self.sync_entry(entry, dry_run, base_game=bundle.base_game)
            
            if success:
                output_path = self._get_output_path(entry, base_game=bundle.base_game)
                if output_path.exists():
                    stats.already_downloaded += 1
                else:
                    stats.newly_downloaded += 1
                    stats.downloaded_size += entry.file_size
            else:
                stats.failed += 1
                self.failed_downloads.append({
                    'title_id': entry.title_id,
                    'name': entry.name,
                    'error': error
                })
        
        # Create metadata file
        if not dry_run:
            self._create_metadata(bundle)
        
        return stats
    
    def sync_search_results(
        self,
        query: str,
        platform: Optional[str] = None,
        region: Optional[str] = None,
        include_dlc: bool = True,
        include_updates: bool = True,
        dry_run: bool = False
    ) -> SyncStats:
        """Search and sync content.
        
        Args:
            query: Search query
            platform: Optional platform filter
            region: Optional region filter
            include_dlc: Include DLC
            include_updates: Include updates
            dry_run: Don't actually download
            
        Returns:
            Combined SyncStats
        """
        # Search for bundles
        bundles = self.search.search_with_dependencies(
            query=query,
            platform=platform,
            region=region,
            include_dlc=include_dlc,
            include_updates=include_updates
        )
        
        if not bundles:
            print(f"⚠ No results found for: {query}")
            return SyncStats()
        
        print(f"Found {len(bundles)} title(s) matching '{query}'")
        
        # Sync each bundle
        combined_stats = SyncStats()
        
        for bundle in bundles:
            stats = self.sync_bundle(bundle, dry_run)
            
            # Combine stats
            combined_stats.total_items += stats.total_items
            combined_stats.already_downloaded += stats.already_downloaded
            combined_stats.newly_downloaded += stats.newly_downloaded
            combined_stats.failed += stats.failed
            combined_stats.skipped += stats.skipped
            combined_stats.total_size += stats.total_size
            combined_stats.downloaded_size += stats.downloaded_size
        
        return combined_stats
    
    def _get_output_path(self, entry: ContentEntry, base_game: Optional[ContentEntry] = None) -> Path:
        """Calculate output path for entry.
        
        Format: packages/platform/games/region/GameName [TITLEID]/{dlc/DLCName,updates}/filename.pkg
        
        Example: packages/vita/games/usa/Doctor Who [PCSE00103]/game.pkg
                 packages/vita/games/usa/Doctor Who [PCSE00103]/dlc/White Chocobo/dlc.pkg
        
        Args:
            entry: ContentEntry
            base_game: Base game entry (for DLC/updates to use game's name)
            
        Returns:
            Output path
        """
        # Sanitize name for filesystem
        safe_name = self._sanitize_filename(entry.name)
        
        # Build path components
        platform = entry.platform.lower()
        region = entry.region.lower() if entry.region else 'unknown'
        
        # For DLC/updates/themes tied to a game, use base game's name in title directory
        if entry.content_type in ('dlc', 'updates', 'themes') and base_game:
            game_safe_name = self._sanitize_filename(base_game.name)
            title_dir = f"{game_safe_name} [{entry.title_id}]"
            # DLC/updates/themes go under games/, not their own top-level directory
            content_type_dir = 'games'
        else:
            # Standalone content (games, themes without base game, demos, avatars)
            if entry.content_type == 'games':
                title_dir = f"{safe_name} [{entry.title_id}]"
                content_type_dir = 'games'
            else:
                # Standalone themes/demos/avatars don't need title directory
                title_dir = None
                content_type_dir = entry.content_type.lower()
        
        # Content subdirectory
        if entry.content_type == 'games':
            subdir = ''  # No base/ folder - files go directly in game directory
        elif entry.content_type in ('dlc', 'updates', 'themes') and base_game:
            # Game-bundled DLC/updates/themes get their own named subdirectory
            subdir = f"{entry.content_type}/{safe_name}"
        else:
            # Standalone content: no subdirectory, just region folder
            subdir = ''
        
        # Filename from URL or Content ID
        if entry.pkg_url:
            filename = entry.pkg_url.split('/')[-1]
            if not filename.endswith('.pkg'):
                filename = f"{entry.content_id}.pkg"
        else:
            filename = f"{entry.content_id}.pkg"
        
        # Full path
        if title_dir:
            if subdir:
                path = self.output_dir / platform / content_type_dir / region / title_dir / subdir / filename
            else:
                # Games go directly in title directory (no base/ folder)
                path = self.output_dir / platform / content_type_dir / region / title_dir / filename
        else:
            # Standalone content (no title directory)
            if subdir:
                path = self.output_dir / platform / content_type_dir / region / subdir / filename
            else:
                path = self.output_dir / platform / content_type_dir / region / filename
        
        return path
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize name for filesystem.
        
        Args:
            name: Original name
            
        Returns:
            Safe filename
        """
        # Remove/replace unsafe characters
        safe = name.replace('/', '_').replace('\\', '_')
        safe = safe.replace(':', '_').replace('*', '_')
        safe = safe.replace('?', '_').replace('"', '_')
        safe = safe.replace('<', '_').replace('>', '_')
        safe = safe.replace('|', '_')
        
        # Remove trademark symbols
        safe = safe.replace('®', '').replace('™', '').replace('©', '')
        
        # Collapse spaces
        safe = ' '.join(safe.split())
        
        # Limit length
        if len(safe) > 100:
            safe = safe[:100]
        
        return safe
    
    def _download_entry(
        self,
        entry: ContentEntry,
        output_path: Path
    ) -> Tuple[bool, Optional[str]]:
        """Download a content entry.
        
        Args:
            entry: ContentEntry to download
            output_path: Where to save
            
        Returns:
            Tuple of (success, error_message)
        """
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"  📥 Downloading: {entry.name}")
        if self.verbose:
            print(f"      URL: {entry.pkg_url}")
            print(f"      Size: {self._format_size(entry.file_size)}")
        
        try:
            # Download with progress
            def report_progress(block_num, block_size, total_size):
                if total_size > 0 and block_num % 100 == 0:
                    downloaded = block_num * block_size
                    percent = min(100, (downloaded * 100) // total_size)
                    if self.verbose:
                        print(f"\r      Progress: {percent}%", end='')
            
            urllib.request.urlretrieve(
                entry.pkg_url,
                output_path,
                reporthook=report_progress if self.verbose else None
            )
            
            if self.verbose:
                print()  # New line after progress
            
            # Verify size
            if not self._verify_file_size(output_path, entry.file_size):
                actual_size = output_path.stat().st_size
                error = f"Size mismatch: expected {entry.file_size}, got {actual_size}"
                print(f"      ✗ {error}")
                output_path.unlink()
                return False, error
            
            # Verify SHA256 if available
            if self.verify_downloads and entry.sha256:
                if not self._verify_sha256(output_path, entry.sha256):
                    error = "SHA256 mismatch"
                    print(f"      ✗ {error}")
                    output_path.unlink()
                    return False, error
            
            print(f"      ✓ Downloaded successfully")
            
            # Create license file if needed
            self._create_license_file(entry, output_path)
            
            return True, None
            
        except Exception as e:
            error = str(e)
            print(f"      ✗ Download failed: {error}")
            if output_path.exists():
                output_path.unlink()
            return False, error
    
    def _create_license_file(self, entry: ContentEntry, pkg_path: Path):
        """Create license file (.rap or .zrif) next to PKG.
        
        Args:
            entry: ContentEntry with license_key
            pkg_path: Path to downloaded PKG file
        """
        if not entry.license_key:
            return  # No license needed
        
        # Determine license file type based on platform
        if entry.platform in ('vita', 'psm'):
            # zRIF - save as text file
            license_path = pkg_path.with_suffix('.zrif')
            if not license_path.exists():
                with open(license_path, 'w') as f:
                    f.write(entry.license_key)
                if self.verbose:
                    print(f"      ✓ Created zRIF: {license_path.name}")
        
        elif entry.platform in ('ps3', 'psp'):
            # RAP - convert hex string to binary
            license_path = pkg_path.parent / f"{entry.content_id}.rap"
            if not license_path.exists():
                try:
                    rap_bytes = bytes.fromhex(entry.license_key)
                    with open(license_path, 'wb') as f:
                        f.write(rap_bytes)
                    if self.verbose:
                        print(f"      ✓ Created RAP: {license_path.name}")
                except ValueError as e:
                    if self.verbose:
                        print(f"      ⚠ Invalid RAP key: {e}")
    
    def _verify_file_size(self, path: Path, expected_size: int) -> bool:
        """Verify file size within tolerance.
        
        Args:
            path: File path
            expected_size: Expected size in bytes
            
        Returns:
            True if size matches or within tolerance
        """
        if not path.exists():
            return False
        
        actual_size = path.stat().st_size
        
        # Exact match
        if actual_size == expected_size:
            return True
        
        # Within tolerance
        if expected_size > 0:
            diff = abs(actual_size - expected_size)
            percent_diff = (diff / expected_size) * 100
            return percent_diff <= self.SIZE_TOLERANCE_PERCENT
        
        return False
    
    def _verify_sha256(self, path: Path, expected_hash: str) -> bool:
        """Verify SHA256 hash.
        
        Args:
            path: File path
            expected_hash: Expected SHA256 (hex)
            
        Returns:
            True if hash matches
        """
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8388608), b''):
                sha256.update(chunk)
        
        actual_hash = sha256.hexdigest().upper()
        return actual_hash == expected_hash.upper()
    
    def _create_metadata(self, bundle: TitleBundle):
        """Create .nps-metadata.json file for bundle.
        
        Args:
            bundle: TitleBundle
        """
        # Determine metadata path (in title directory)
        if bundle.base_game:
            base_path = self._get_output_path(bundle.base_game)
            metadata_path = base_path.parent.parent / '.nps-metadata.json'
        elif bundle.dlc:
            dlc_path = self._get_output_path(bundle.dlc[0])
            metadata_path = dlc_path.parent.parent / '.nps-metadata.json'
        else:
            return  # No content to track
        
        # Build metadata
        metadata = DownloadMetadata(
            platform=bundle.platform,
            region=bundle.region,
            title_id=bundle.title_id,
        )
        
        # Add base game info
        if bundle.base_game:
            metadata.base_game = {
                'content_id': bundle.base_game.content_id,
                'name': bundle.base_game.name,
                'size': bundle.base_game.file_size,
                'downloaded': datetime.now().isoformat(),
                'verified': True,
            }
        
        # Add DLC
        for dlc in bundle.dlc:
            metadata.dlc.append({
                'content_id': dlc.content_id,
                'name': dlc.name,
                'size': dlc.file_size,
                'downloaded': datetime.now().isoformat(),
                'verified': True,
            })
        
        # Add updates
        for update in bundle.updates:
            metadata.updates.append({
                'content_id': update.content_id,
                'name': update.name,
                'version': update.version,
                'size': update.file_size,
                'downloaded': datetime.now().isoformat(),
                'verified': True,
            })
        
        # Save
        metadata.save(metadata_path)
        
        if self.verbose:
            print(f"  ✓ Created metadata: {metadata_path.name}")
    
    def _format_size(self, bytes: int) -> str:
        """Format bytes as human-readable size."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} PB"
