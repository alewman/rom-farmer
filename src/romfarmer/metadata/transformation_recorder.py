"""
Transformation Recorder for ROM processing.

This module records ROM transformations as they happen during processing.
It captures:
- Source file hashes (from DAT or calculation)
- Transformation metadata (tool, version, parameters)
- Final file hashes (after processing)

Example workflow:
    recorder = TransformationRecorder(db, dat_manager)
    
    # Start recording a transformation
    with recorder.record_transformation(
        source_file=Path("game.iso"),
        system="saturn",
        tool="chdman",
        version="0.251",
        params={"compression": "zstd"}
    ) as transform:
        # Do the actual processing
        final_file = process_with_chdman(source_file)
        
        # Record the final file
        transform.set_final_file(final_file)
    
    # Transformation automatically saved with timing info!
"""

import json
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any

from rich.console import Console
from sqlalchemy.orm import Session

from .dat_manager import DATManager
from .hash_capture import SmartHashCapture
from .transformation import ROMTransformation
from .database import ScrapedGame

console = Console()


@dataclass
class TransformationContext:
    """Context for an in-progress transformation."""
    
    recorder: 'TransformationRecorder'
    source_file: Path
    system: str
    tool: str
    version: str
    params: Dict[str, Any]
    
    # Captured at start
    source_hashes: Any  # SourceHashInfo
    start_time: float
    
    # Will be set during processing
    final_file: Optional[Path] = None
    final_hashes: Any = None
    
    def set_final_file(self, final_file: Path):
        """
        Record the final processed file.
        
        This captures the final file's hashes and prepares for storage.
        """
        if not final_file.exists():
            raise FileNotFoundError(f"Final file not found: {final_file}")
        
        console.print(f"[cyan]Capturing final file hashes:[/cyan] {final_file.name}")
        
        # Capture final file hashes (no DAT lookup, just calculate/cache)
        self.final_file = final_file
        self.final_hashes = self.recorder.hash_capture.get_source_hashes(
            final_file,
            system=None,  # Don't look in DAT for final files
            force_calculate=False  # Use cache if available
        )
    
    def get_duration(self) -> float:
        """Get transformation duration in seconds."""
        return time.time() - self.start_time


class TransformationRecorder:
    """
    Records ROM transformations during processing.
    
    This class integrates with your ROM processing workflow to automatically
    capture and store transformation metadata.
    """
    
    def __init__(
        self,
        session: Session,
        dat_manager: Optional[DATManager] = None
    ):
        """
        Initialize transformation recorder.
        
        Args:
            session: Database session
            dat_manager: Optional DAT manager for source hash lookup
        """
        self.session = session
        self.dat_manager = dat_manager
        self.hash_capture = SmartHashCapture(dat_manager, session)
        
        # Statistics
        self.stats = {
            'transformations_recorded': 0,
            'source_from_dat': 0,
            'source_calculated': 0,
            'total_duration': 0.0,
        }
    
    @contextmanager
    def record_transformation(
        self,
        source_file: Path,
        system: str,
        tool: str,
        version: str,
        params: Optional[Dict[str, Any]] = None,
    ):
        """
        Context manager for recording a transformation.
        
        Usage:
            with recorder.record_transformation(
                source_file=Path("game.iso"),
                system="saturn",
                tool="chdman",
                version="0.251",
                params={"compression": "zstd"}
            ) as transform:
                # Do processing
                final_file = process_rom(source_file)
                transform.set_final_file(final_file)
        
        Args:
            source_file: Source ROM file (before transformation)
            system: System name (e.g., "saturn", "xbox360")
            tool: Transformation tool (e.g., "chdman", "extract-xiso")
            version: Tool version
            params: Optional transformation parameters
        
        Yields:
            TransformationContext that you call set_final_file() on
        """
        if not source_file.exists():
            raise FileNotFoundError(f"Source file not found: {source_file}")
        
        console.print(f"\n[bold cyan]Recording Transformation[/bold cyan]")
        console.print(f"  Source: {source_file.name}")
        console.print(f"  System: {system}")
        console.print(f"  Tool: {tool} v{version}")
        
        # Capture source file hashes
        console.print(f"[cyan]Capturing source file hashes...[/cyan]")
        source_hashes = self.hash_capture.get_source_hashes(
            source_file,
            system=system
        )
        
        if source_hashes.from_dat:
            console.print(f"  [green]✓ Source hashes from DAT: {source_hashes.dat_name}[/green]")
            self.stats['source_from_dat'] += 1
        else:
            console.print(f"  [yellow]⚠ Source hashes calculated ({source_hashes.calculation_time:.1f}s)[/yellow]")
            self.stats['source_calculated'] += 1
        
        # Create transformation context
        context = TransformationContext(
            recorder=self,
            source_file=source_file,
            system=system,
            tool=tool,
            version=version,
            params=params or {},
            source_hashes=source_hashes,
            start_time=time.time(),
        )
        
        try:
            # Yield to processing code
            yield context
            
            # After processing, save the transformation
            if context.final_file is None:
                console.print("[yellow]⚠ Warning: Final file not set, skipping transformation record[/yellow]")
                return
            
            self._save_transformation(context)
            
        except Exception as e:
            console.print(f"[red]✗ Error during transformation recording:[/red] {e}")
            raise
    
    def _save_transformation(self, context: TransformationContext):
        """Save transformation to database."""
        duration = context.get_duration()
        
        console.print(f"\n[bold green]✓ Transformation Complete[/bold green]")
        console.print(f"  Duration: {duration:.1f}s")
        console.print(f"  Source MD5: {context.source_hashes.md5}")
        console.print(f"  Final MD5: {context.final_hashes.md5}")
        
        # Check if transformation already exists
        existing = self.session.query(ROMTransformation).filter_by(
            source_md5=context.source_hashes.md5,
            final_md5=context.final_hashes.md5,
        ).first()
        
        if existing:
            console.print(f"[yellow]  ⚠ Transformation already exists (id={existing.id}), updating...[/yellow]")
            # Update existing record
            existing.transformation_tool = context.tool
            existing.transformation_version = context.version
            existing.transformation_params = json.dumps(context.params)
            existing.transformation_date = datetime.utcnow()
            existing.transformation_duration_seconds = duration
            
            # Update hashes if different
            existing.source_sha1 = context.source_hashes.sha1
            existing.source_sha256 = context.source_hashes.sha256
            existing.source_crc32 = context.source_hashes.crc32
            existing.final_sha1 = context.final_hashes.sha1
            existing.final_sha256 = context.final_hashes.sha256
            existing.final_crc32 = context.final_hashes.crc32
            
            transformation = existing
        else:
            # Create new transformation record
            transformation = ROMTransformation(
                # Source file info
                source_md5=context.source_hashes.md5,
                source_sha1=context.source_hashes.sha1,
                source_sha256=context.source_hashes.sha256,
                source_crc32=context.source_hashes.crc32,
                source_file_size=context.source_hashes.size,
                source_file_name=context.source_file.name,
                source_format=context.source_file.suffix.lstrip('.').lower(),
                source_dat=context.source_hashes.dat_name if context.source_hashes.from_dat else None,
                source_verified=context.source_hashes.from_dat,
                
                # Transformation metadata
                transformation_tool=context.tool,
                transformation_version=context.version,
                transformation_params=json.dumps(context.params),
                transformation_date=datetime.utcnow(),
                transformation_duration_seconds=duration,
                
                # Final file info
                final_md5=context.final_hashes.md5,
                final_sha1=context.final_hashes.sha1,
                final_sha256=context.final_hashes.sha256,
                final_crc32=context.final_hashes.crc32,
                final_file_size=context.final_hashes.size,
                final_file_name=context.final_file.name,
                final_format=context.final_file.suffix.lstrip('.').lower(),
                
                # Verification
                verified=context.source_hashes.from_dat,  # Verified if source is from DAT
                verification_count=1 if context.source_hashes.from_dat else 0,
                community_reported=False,
            )
            
            self.session.add(transformation)
            console.print(f"[green]  ✓ Created new transformation record[/green]")
        
        self.session.commit()
        
        # Update statistics
        self.stats['transformations_recorded'] += 1
        self.stats['total_duration'] += duration
        
        console.print(f"[green]  ✓ Transformation saved to database (id={transformation.id})[/green]")
    
    def find_source_hash(self, final_file: Path) -> Optional[ROMTransformation]:
        """
        Reverse lookup: Given a final file, find the source hash.
        
        This is useful for ScreenScraper lookups - you can find the original
        ISO/ROM hash even though you only have the CHD/XISO/CSO file.
        
        Args:
            final_file: The final processed file
        
        Returns:
            ROMTransformation if found, None otherwise
        """
        console.print(f"[cyan]Looking up source hash for:[/cyan] {final_file.name}")
        
        # First, get the final file's hash
        final_hashes = self.hash_capture.get_source_hashes(
            final_file,
            system=None,
            force_calculate=False
        )
        
        # Look up transformation by final hash
        transformation = self.session.query(ROMTransformation).filter_by(
            final_md5=final_hashes.md5
        ).first()
        
        if transformation:
            console.print(f"[green]  ✓ Found source hash:[/green] {transformation.source_md5}")
            return transformation
        else:
            console.print(f"[yellow]  ⚠ No transformation found for this file[/yellow]")
            return None
    
    def link_to_game(self, transformation: ROMTransformation, game_name: str, system: str):
        """
        Link a transformation to a scraped game.
        
        This creates the connection between the transformation and the game metadata.
        """
        # Find game by name and system
        game = self.session.query(ScrapedGame).filter_by(
            name=game_name,
            system=system
        ).first()
        
        if game:
            transformation.game_id = game.id
            self.session.commit()
            console.print(f"[green]✓ Linked transformation to game:[/green] {game_name}")
        else:
            console.print(f"[yellow]⚠ Game not found in database:[/yellow] {game_name}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get transformation recording statistics."""
        return {
            'transformations_recorded': self.stats['transformations_recorded'],
            'source_from_dat': self.stats['source_from_dat'],
            'source_calculated': self.stats['source_calculated'],
            'avg_duration': (
                self.stats['total_duration'] / self.stats['transformations_recorded']
                if self.stats['transformations_recorded'] > 0 else 0.0
            ),
            'total_duration': self.stats['total_duration'],
        }
    
    def print_stats(self):
        """Print transformation recording statistics."""
        stats = self.get_stats()
        
        if stats['transformations_recorded'] == 0:
            console.print("[yellow]No transformations recorded yet[/yellow]")
            return
        
        console.print("\n[bold cyan]Transformation Recording Statistics:[/bold cyan]")
        console.print(f"  Transformations Recorded: {stats['transformations_recorded']}")
        console.print(f"  Source from DAT: {stats['source_from_dat']}")
        console.print(f"  Source Calculated: {stats['source_calculated']}")
        console.print(f"  Avg Duration: {stats['avg_duration']:.1f}s")
        console.print(f"  Total Duration: {stats['total_duration']:.1f}s")
        
        # Show hash capture stats too
        self.hash_capture.print_stats()
