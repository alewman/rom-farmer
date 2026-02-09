"""
ROM scanning and validation against DAT files.

Scans directories for ROM files, calculates hashes, and validates against
imported DAT data to identify matches, missing games, and collection status.
"""

from pathlib import Path
from typing import List, Optional, Dict, Set, Tuple
from dataclasses import dataclass, field
import hashlib
import zlib
from concurrent.futures import ThreadPoolExecutor, as_completed

from romfarmer.catalog.database import RomGroomerDatabase, DatGame
from romfarmer.core.logger import get_logger


logger = get_logger()


@dataclass
class RomScanResult:
    """Result of scanning a single ROM file."""
    file_path: Path
    file_size: int
    crc32: str
    md5: Optional[str] = None
    sha1: Optional[str] = None
    matched_game: Optional[DatGame] = None
    dat_name: Optional[str] = None
    is_matched: bool = False


@dataclass
class ScanStatistics:
    """Statistics from ROM scanning operation."""
    total_files_scanned: int = 0
    total_bytes_scanned: int = 0
    files_matched: int = 0
    files_unmatched: int = 0
    unique_games_found: int = 0
    scan_duration_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)


class RomScanner:
    """
    Scan directories for ROM files and validate against DAT data.
    
    Features:
    - Recursive directory scanning
    - Multiple hash algorithms (CRC32, MD5, SHA1)
    - DAT validation and matching
    - Parallel processing for performance
    - Extension filtering
    - Progress tracking
    """
    
    DEFAULT_EXTENSIONS = {
        '.nes', '.smc', '.sfc', '.gb', '.gbc', '.gba', '.gen', '.md', '.sms',
        '.gg', '.n64', '.z64', '.v64', '.nds', '.3ds', '.cia', '.min',
        '.bin', '.cue', '.iso', '.chd', '.cso', '.pbp', '.zip', '.7z', '.rar',
    }
    
    def __init__(
        self,
        database: RomGroomerDatabase,
        extensions: Optional[Set[str]] = None,
        calculate_md5: bool = False,
        calculate_sha1: bool = False,
        num_workers: int = 4,
    ):
        """
        Initialize ROM scanner.
        
        Args:
            database: Database instance for DAT lookups
            extensions: File extensions to scan (default: common ROM extensions)
            calculate_md5: Calculate MD5 hashes (slower but more accurate)
            calculate_sha1: Calculate SHA1 hashes (slower but more accurate)
            num_workers: Number of parallel workers for scanning
        """
        self.db = database
        self.extensions = extensions or self.DEFAULT_EXTENSIONS
        self.calculate_md5 = calculate_md5
        self.calculate_sha1 = calculate_sha1
        self.num_workers = num_workers
    
    def scan_directory(
        self,
        directory: Path,
        recursive: bool = True,
        dat_name: Optional[str] = None,
    ) -> Tuple[List[RomScanResult], ScanStatistics]:
        """
        Scan a directory for ROM files and validate against DAT.
        
        Args:
            directory: Directory to scan
            recursive: Scan subdirectories recursively
            dat_name: Optional DAT name to validate against (default: all DATs)
        
        Returns:
            Tuple of (scan results, statistics)
        """
        import time
        start_time = time.time()
        
        stats = ScanStatistics()
        results = []
        
        # Find all ROM files
        rom_files = self._find_rom_files(directory, recursive)
        stats.total_files_scanned = len(rom_files)
        
        if not rom_files:
            logger.warning(f"No ROM files found in {directory}")
            stats.scan_duration_seconds = time.time() - start_time
            return results, stats
        
        logger.info(f"Found {len(rom_files)} ROM files to scan")
        
        # Process files in parallel
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            future_to_file = {
                executor.submit(self._scan_file, file_path, dat_name): file_path
                for file_path in rom_files
            }
            
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        stats.total_bytes_scanned += result.file_size
                        
                        if result.is_matched:
                            stats.files_matched += 1
                        else:
                            stats.files_unmatched += 1
                except Exception as e:
                    error_msg = f"Error scanning {file_path}: {e}"
                    logger.error(error_msg)
                    stats.errors.append(error_msg)
        
        # Calculate unique games
        unique_games = {r.matched_game.name for r in results if r.matched_game}
        stats.unique_games_found = len(unique_games)
        
        stats.scan_duration_seconds = time.time() - start_time
        
        logger.info(f"Scan complete: {stats.files_matched}/{stats.total_files_scanned} files matched "
                   f"({stats.unique_games_found} unique games) in {stats.scan_duration_seconds:.2f}s")
        
        return results, stats
    
    def _find_rom_files(self, directory: Path, recursive: bool) -> List[Path]:
        """Find all ROM files in directory."""
        if not directory.exists():
            raise ValueError(f"Directory does not exist: {directory}")
        
        if not directory.is_dir():
            raise ValueError(f"Not a directory: {directory}")
        
        files = []
        
        if recursive:
            for ext in self.extensions:
                files.extend(directory.rglob(f"*{ext}"))
        else:
            for ext in self.extensions:
                files.extend(directory.glob(f"*{ext}"))
        
        # Filter out directories and non-files
        files = [f for f in files if f.is_file()]
        
        # Sort for consistent ordering
        files.sort()
        
        return files
    
    def _scan_file(self, file_path: Path, dat_name: Optional[str] = None) -> Optional[RomScanResult]:
        """
        Scan a single ROM file and validate against DAT.
        
        Args:
            file_path: Path to ROM file
            dat_name: Optional DAT name for validation
        
        Returns:
            RomScanResult or None if file couldn't be scanned
        """
        try:
            # Get file size
            file_size = file_path.stat().st_size
            
            # Calculate hashes
            crc32, md5, sha1 = self._calculate_hashes(file_path)
            
            # Create result
            result = RomScanResult(
                file_path=file_path,
                file_size=file_size,
                crc32=crc32,
                md5=md5,
                sha1=sha1,
            )
            
            # Try to match against DAT
            matched_game = self._match_game(crc32, md5, sha1, dat_name)
            
            if matched_game:
                result.matched_game = matched_game
                result.dat_name = matched_game.dat_file.name if matched_game.dat_file else None
                result.is_matched = True
                logger.debug(f"Matched {file_path.name} -> {matched_game.name}")
            else:
                logger.debug(f"No match found for {file_path.name} (CRC: {crc32})")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to scan {file_path}: {e}")
            return None
    
    def _calculate_hashes(self, file_path: Path) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Calculate file hashes.
        
        Returns:
            Tuple of (crc32, md5, sha1)
        """
        crc32_hash = 0
        md5_hash = hashlib.md5() if self.calculate_md5 else None
        sha1_hash = hashlib.sha1() if self.calculate_sha1 else None
        
        # Read file in chunks for memory efficiency
        chunk_size = 1024 * 1024  # 1MB chunks
        
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                
                # Update CRC32
                crc32_hash = zlib.crc32(chunk, crc32_hash)
                
                # Update MD5 if requested
                if md5_hash:
                    md5_hash.update(chunk)
                
                # Update SHA1 if requested
                if sha1_hash:
                    sha1_hash.update(chunk)
        
        # Convert CRC32 to hex string (8 characters, lowercase)
        crc32_str = f"{crc32_hash & 0xFFFFFFFF:08x}"
        
        # Get hex digests for MD5 and SHA1
        md5_str = md5_hash.hexdigest() if md5_hash else None
        sha1_str = sha1_hash.hexdigest() if sha1_hash else None
        
        return crc32_str, md5_str, sha1_str
    
    def _match_game(
        self,
        crc32: str,
        md5: Optional[str],
        sha1: Optional[str],
        dat_name: Optional[str],
    ) -> Optional[DatGame]:
        """
        Match a ROM against DAT database.
        
        Tries matching in order: CRC32, MD5, SHA1
        """
        session = self.db.get_session()
        try:
            # Get DAT file ID if specified
            dat_file_id = None
            if dat_name:
                dat_file = self.db.get_dat_file(session, dat_name)
                if dat_file:
                    dat_file_id = dat_file.id
            
            # Try CRC32 match first (fastest)
            game = self.db.find_game_by_crc(session, crc32, dat_file_id=dat_file_id)
            if game:
                return game
            
            # Try MD5 if available
            if md5:
                # MD5 matching would require additional database support
                # For now, we rely on CRC32
                pass
            
            # Try SHA1 if available
            if sha1:
                # SHA1 matching would require additional database support
                # For now, we rely on CRC32
                pass
            
            return None
            
        finally:
            session.close()
    
    def find_missing_games(
        self,
        dat_name: str,
        scanned_results: List[RomScanResult],
    ) -> List[DatGame]:
        """
        Find games in DAT that are missing from scanned collection.
        
        Args:
            dat_name: DAT name to check against
            scanned_results: Results from scanning
        
        Returns:
            List of missing DatGame entries
        """
        session = self.db.get_session()
        try:
            # Get all games from DAT
            dat_file = self.db.get_dat_file(session, dat_name)
            if not dat_file:
                logger.error(f"DAT not found: {dat_name}")
                return []
            
            all_games = self.db.get_dat_games(session, dat_file.id, limit=None)
            
            # Get CRCs of matched games
            matched_crcs = {r.matched_game.crc for r in scanned_results if r.matched_game}
            
            # Find missing games
            missing_games = [g for g in all_games if g.crc not in matched_crcs]
            
            return missing_games
            
        finally:
            session.close()
    
    def generate_report(
        self,
        results: List[RomScanResult],
        stats: ScanStatistics,
        output_path: Optional[Path] = None,
    ) -> str:
        """
        Generate a text report of scan results.
        
        Args:
            results: Scan results
            stats: Scan statistics
            output_path: Optional path to write report
        
        Returns:
            Report text
        """
        lines = []
        lines.append("=" * 80)
        lines.append("ROM SCAN REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Statistics
        lines.append("STATISTICS:")
        lines.append(f"  Total Files Scanned: {stats.total_files_scanned:,}")
        lines.append(f"  Total Size: {stats.total_bytes_scanned / (1024**3):.2f} GB")
        lines.append(f"  Files Matched: {stats.files_matched:,}")
        lines.append(f"  Files Unmatched: {stats.files_unmatched:,}")
        lines.append(f"  Unique Games: {stats.unique_games_found:,}")
        lines.append(f"  Match Rate: {stats.files_matched / max(stats.total_files_scanned, 1) * 100:.1f}%")
        lines.append(f"  Scan Duration: {stats.scan_duration_seconds:.2f}s")
        lines.append("")
        
        # Matched files
        matched = [r for r in results if r.is_matched]
        if matched:
            lines.append(f"MATCHED FILES ({len(matched)}):")
            for result in matched[:50]:  # Limit to first 50
                lines.append(f"  {result.file_path.name}")
                lines.append(f"    -> {result.matched_game.name}")
                lines.append(f"    CRC: {result.crc32} | Size: {result.file_size:,} bytes")
                lines.append("")
            
            if len(matched) > 50:
                lines.append(f"  ... and {len(matched) - 50} more matched files")
                lines.append("")
        
        # Unmatched files
        unmatched = [r for r in results if not r.is_matched]
        if unmatched:
            lines.append(f"UNMATCHED FILES ({len(unmatched)}):")
            for result in unmatched[:30]:  # Limit to first 30
                lines.append(f"  {result.file_path.name}")
                lines.append(f"    CRC: {result.crc32} | Size: {result.file_size:,} bytes")
            
            if len(unmatched) > 30:
                lines.append(f"  ... and {len(unmatched) - 30} more unmatched files")
            lines.append("")
        
        # Errors
        if stats.errors:
            lines.append(f"ERRORS ({len(stats.errors)}):")
            for error in stats.errors[:20]:
                lines.append(f"  {error}")
            if len(stats.errors) > 20:
                lines.append(f"  ... and {len(stats.errors) - 20} more errors")
            lines.append("")
        
        lines.append("=" * 80)
        
        report = "\n".join(lines)
        
        # Write to file if requested
        if output_path:
            output_path.write_text(report)
            logger.info(f"Report written to {output_path}")
        
        return report
