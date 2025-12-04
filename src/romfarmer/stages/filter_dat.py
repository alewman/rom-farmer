"""Filter ROMs against DAT file stage."""

import hashlib
import time
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

from ..dat_parser import DATFile, ROMMatcher
from ..metadata.database import MetadataDatabase
from .base import Stage, StageContext, StageResult, StageStatus


class FilterDATStage(Stage):
    """Filter source ROM files against DAT file.

    For No-Intro:
    - Match ZIP files against Retool DAT entries
    - Copy matched ZIPs to work directory (no extraction!)
    - Track unmatched files for reporting

    For Redump:
    - Match ZIP files against Retool DAT entries
    - Mark for extraction in next stage
    """

    def __init__(self):
        """Initialize DAT filter stage."""
        super().__init__("Filter DAT")

    def should_skip(self, context: StageContext) -> bool:
        """Skip if no DAT file. If source files exist, pass them through."""
        # If we have source files but no DAT, skip this stage but allow pipeline to continue
        # This enables DAT-less workflows (e.g., using metadata database only)
        return context.dat_file is None

    def validate_context(self, context: StageContext) -> str | None:
        """Validate context."""
        if not context.source_dir.exists():
            return f"Source directory not found: {context.source_dir}"
        if not context.work_dir.exists():
            context.work_dir.mkdir(parents=True, exist_ok=True)
        return None

    def _populate_md5s(self, context: StageContext) -> None:
        """Populate MD5 hashes for source files.
        
        Loads MD5s from database first, then calculates for missing files.
        """
        self._log(context, "[cyan]Loading MD5 hashes...[/cyan]")
        
        # Try to load from database first
        db_md5s = self._load_md5s_from_database(context)
        if db_md5s:
            context.file_md5s.update(db_md5s)
            self._log(context, f"  Loaded {len(db_md5s):,} MD5s from database")
        
        # Calculate MD5s for files not in database
        missing_files = [f for f in context.source_files if f not in context.file_md5s]
        if missing_files:
            self._log(context, f"  Calculating MD5s for {len(missing_files):,} files...")
            calculated = self._calculate_md5s(missing_files, context)
            context.file_md5s.update(calculated)
            self._log(context, f"  Calculated {len(calculated):,} MD5s")
        
        self._log(context, f"  Total MD5s available: {len(context.file_md5s):,}")

    def _load_md5s_from_database(self, context: StageContext) -> Dict[Path, str]:
        """Load MD5 hashes from metadata database.
        
        Returns:
            Dictionary mapping file paths to MD5 hashes
        """
        try:
            # Try multiple possible database locations
            db_paths = [
                Path("metadata/database/romfarmer.db"),
                Path.cwd() / "metadata" / "database" / "romfarmer.db",
                Path(__file__).parent.parent.parent / "metadata" / "database" / "romfarmer.db",
            ]
            
            db_path = None
            for path in db_paths:
                if path.exists():
                    db_path = path
                    break
            
            if not db_path:
                self._log(context, "  [yellow]Warning: Database not found, skipping MD5 lookup[/yellow]")
                return {}
            
            from ..metadata.database import ScrapedGame
            
            db = MetadataDatabase(db_path)
            session = db.get_session()
            md5_map = {}
            
            try:
                # Query database for files in this system
                system = context.platform_name
                games = session.query(ScrapedGame).filter(
                    ScrapedGame.system == system,
                    ScrapedGame.md5.isnot(None)
                ).all()
                
                # Build mapping: filename -> MD5
                # The filename field contains paths like "./filename.zip", so strip "./"
                db_entries = {}
                for game in games:
                    if game.filename:
                        # Strip "./" prefix from ARRM paths
                        clean_filename = game.filename.lstrip("./")
                        db_entries[clean_filename] = game.md5
                
                # Match source files to database entries
                for file_path in context.source_files:
                    # Try exact name match
                    if file_path.name in db_entries:
                        md5_map[file_path] = db_entries[file_path.name]
                
                return md5_map
                
            finally:
                session.close()
            
        except Exception as e:
            self._log(context, f"  [yellow]Warning: Could not load MD5s from database: {e}[/yellow]")
            return {}

    def _calculate_md5s(self, files: List[Path], context: StageContext) -> Dict[Path, str]:
        """Calculate MD5 hashes for ROM files.
        
        For ZIP files, extracts the ROM and calculates its MD5.
        
        Returns:
            Dictionary mapping file paths to MD5 hashes
        """
        md5_map = {}
        
        for file_path in files:
            try:
                md5_hash = self._calculate_file_md5(file_path)
                if md5_hash:
                    md5_map[file_path] = md5_hash
            except Exception as e:
                self._log(context, f"  [yellow]Warning: Failed to calculate MD5 for {file_path.name}: {e}[/yellow]")
        
        return md5_map

    def _calculate_file_md5(self, file_path: Path) -> Optional[str]:
        """Calculate MD5 hash of a file.
        
        For ZIP files, extracts and hashes the ROM content.
        For other files, hashes the file directly.
        """
        if file_path.suffix.lower() == '.zip':
            return self._calculate_md5_from_zip(file_path)
        else:
            # For non-ZIP files, hash directly
            md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    md5.update(chunk)
            return md5.hexdigest()

    def _calculate_md5_from_zip(self, zip_path: Path) -> Optional[str]:
        """Extract ROM from ZIP and calculate MD5.
        
        For CD-based systems (.cue/.bin pairs), prioritizes .cue files
        to match Redump DAT standards and ARRM/ScreenScraper expectations.
        
        Returns:
            MD5 hash of the ROM content, or None if extraction failed
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Get list of files, excluding directories
                files = [f for f in zf.namelist() if not f.endswith('/')]
                
                if not files:
                    return None
                
                # Priority order for file selection:
                # 1. .cue (CD-based systems - Redump standard, what ARRM expects)
                # 2. .m3u (multi-disc playlists)
                # 3. Cartridge ROMs (.nes, .sfc, .gba, etc.)
                # 4. Disc images (.iso, .chd)
                # 5. .bin (CD data - only if no .cue exists)
                
                # Find .cue files first (CD-based systems)
                cue_files = [f for f in files if f.lower().endswith('.cue')]
                if cue_files:
                    rom_file = cue_files[0]
                else:
                    # Try m3u (multi-disc)
                    m3u_files = [f for f in files if f.lower().endswith('.m3u')]
                    if m3u_files:
                        rom_file = m3u_files[0]
                    else:
                        # Try cartridge ROM extensions
                        rom_extensions = {'.nes', '.sfc', '.smc', '.gb', '.gbc', '.gba', '.nds', '.3ds', '.n64', '.z64', '.v64'}
                        rom_file = None
                        for f in files:
                            ext = Path(f).suffix.lower()
                            if ext in rom_extensions:
                                rom_file = f
                                break
                        
                        # Try disc images
                        if not rom_file:
                            disc_extensions = {'.iso', '.chd'}
                            for f in files:
                                ext = Path(f).suffix.lower()
                                if ext in disc_extensions:
                                    rom_file = f
                                    break
                        
                        # Fallback: use largest file (likely .bin for CD systems)
                        if not rom_file:
                            if len(files) == 1:
                                rom_file = files[0]
                            else:
                                rom_file = max(files, key=lambda f: zf.getinfo(f).file_size)
                
                # Extract and hash in memory
                md5 = hashlib.md5()
                with zf.open(rom_file) as f:
                    for chunk in iter(lambda: f.read(8192), b''):
                        md5.update(chunk)
                
                return md5.hexdigest()
                
        except Exception as e:
            return None

    def execute(self, context: StageContext) -> StageResult:
        """Execute DAT filtering.

        Args:
            context: Stage context with DAT and source files

        Returns:
            StageResult with matched files
        """
        start_time = time.time()

        # Validate
        error = self.validate_context(context)
        if error:
            return StageResult(
                status=StageStatus.FAILED,
                message="Validation failed",
                error=ValueError(error),
            )

        if self.should_skip(context):
            return StageResult(
                status=StageStatus.SKIPPED,
                message="No DAT file or source files",
            )

        self._log(context, f"[cyan]Filtering against DAT: {context.dat_file.name}[/cyan]")
        self._log(context, f"  Games in DAT: {context.dat_file.get_game_count():,}")
        self._log(context, f"  Source files: {len(context.source_files):,}")

        # Populate MD5 hashes for better matching
        self._populate_md5s(context)

        # Create matcher
        matcher = ROMMatcher(context.dat_file)

        # Match files
        matched_files = []
        unmatched_files = []
        hash_matched = 0
        name_matched = 0
        hash_rejected = 0  # Files with hash but no match

        for file_path in context.source_files:
            result = None
            
            # PRIORITY 1: Hash-based matching (most accurate)
            # If we have an MD5 hash, use ONLY hash matching - no filename fallback
            # This prevents false positives like "Game (USA).zip" matching "Game (USA) (Rev 1)" in DAT
            if hasattr(context, 'file_md5s') and file_path in context.file_md5s:
                md5 = context.file_md5s[file_path]
                result = matcher.match_by_hash(file_path, md5=md5)
                if result.is_matched():
                    hash_matched += 1
                    matched_files.append(file_path)
                else:
                    # Hash available but no match - reject without trying filename
                    hash_rejected += 1
                    unmatched_files.append(file_path)
                continue  # Skip filename matching
            
            # PRIORITY 2: Filename matching (fallback for files without hashes)
            # Only used when MD5 hash is not available
            result = matcher.match_file(file_path)
            if result.is_matched():
                name_matched += 1
                matched_files.append(file_path)
            else:
                unmatched_files.append(file_path)

        # Copy matched files to work directory (for No-Intro, these stay as ZIPs)
        copied_files = []
        for file_path in matched_files:
            dest_path = context.work_dir / file_path.name
            if not dest_path.exists():
                # For now, create symlink (copy in production)
                try:
                    dest_path.symlink_to(file_path)
                    copied_files.append(dest_path)
                except OSError:
                    # If symlink fails, try copy
                    import shutil
                    shutil.copy2(file_path, dest_path)
                    copied_files.append(dest_path)
            else:
                copied_files.append(dest_path)

        # Update context
        context.matched_files = copied_files
        context.filtered_files = copied_files

        # Statistics
        duration = time.time() - start_time
        match_rate = (len(matched_files) / len(context.source_files) * 100) if context.source_files else 0

        context.stats["dat_filter"] = {
            "source_files": len(context.source_files),
            "matched_files": len(matched_files),
            "unmatched_files": len(unmatched_files),
            "match_rate": match_rate,
            "copied_files": len(copied_files),
            "hash_matched": hash_matched,
            "name_matched": name_matched,
            "hash_rejected": hash_rejected,
        }

        self._log(
            context,
            f"  [green]Matched: {len(matched_files):,} ({match_rate:.1f}%)[/green]",
        )
        if hash_matched > 0:
            self._log(
                context,
                f"    [cyan]MD5 matched: {hash_matched:,}[/cyan]",
            )
        if hash_rejected > 0:
            self._log(
                context,
                f"    [yellow]MD5 rejected: {hash_rejected:,} (wrong version)[/yellow]",
            )
        if name_matched > 0:
            self._log(
                context,
                f"    [cyan]Name matched: {name_matched:,}[/cyan]",
            )
        self._log(
            context,
            f"  [yellow]Unmatched: {len(unmatched_files):,}[/yellow]",
        )

        return StageResult(
            status=StageStatus.SUCCESS,
            message=f"Filtered {len(matched_files):,} ROMs from {len(context.source_files):,} files",
            files_processed=len(context.source_files),
            files_matched=len(matched_files),
            files_skipped=len(unmatched_files),
            duration_seconds=duration,
            details={
                "matched": [f.name for f in matched_files[:10]],  # Sample
                "unmatched": [f.name for f in unmatched_files[:10]],  # Sample
                "match_rate": match_rate,
            },
        )
