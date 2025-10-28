"""Filter ROMs by rating from ARRM metadata database."""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .base import Stage, StageContext, StageResult, StageStatus


class FilterRatingStage(Stage):
    """
    Filter ROMs based on ratings from ARRM metadata database.
    
    This stage runs after FilterDAT but before ApplyLists. It:
    1. Queries ARRM database for ratings of all remaining files
    2. Sorts by rating (highest first)
    3. Keeps top N games or games that fit within size budget
    4. Deletes filtered-out files
    
    Supports three filter modes:
    - top_n: Keep only the N highest-rated games
    - max_size_gb: Keep top-rated games that fit within size budget
    - min_rating: Keep only games above rating threshold
    """
    
    def __init__(
        self,
        work_dir: Path,
        top_n: Optional[int] = None,
        max_size_gb: Optional[float] = None,
        min_rating: Optional[float] = None,
        metadata_db: Optional[Path] = None
    ):
        """
        Initialize rating filter stage.
        
        Args:
            work_dir: Working directory containing files to filter
            top_n: Keep only top N highest-rated games
            max_size_gb: Keep top-rated games within size budget (GB)
            min_rating: Minimum rating threshold (0.0-1.0)
            metadata_db: Path to ARRM metadata database (auto-detected if None)
        """
        super().__init__(work_dir)
        self.top_n = top_n
        self.max_size_gb = max_size_gb
        self.min_rating = min_rating
        self.metadata_db = metadata_db or self._find_metadata_db()
        
    def _find_metadata_db(self) -> Optional[Path]:
        """Find ARRM metadata database."""
        # Look in standard location
        possible_paths = [
            Path.cwd() / "metadata" / "database" / "romgroomer.db",
            Path.cwd().parent / "metadata" / "database" / "romgroomer.db",
            Path(__file__).parent.parent.parent / "metadata" / "database" / "romgroomer.db"
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
                
        return None
        
    def execute(self, context: StageContext) -> StageResult:
        """
        Filter files by rating.
        
        Args:
            context: Stage context with files to process
            
        Returns:
            StageResult with filtering results
        """
        if not self.metadata_db or not self.metadata_db.exists():
            self._log(context, "[yellow]No metadata database available, skipping rating filter[/yellow]")
            return StageResult(
                status=StageStatus.SUCCESS,
                message="Rating filter skipped (no database)",
                files_processed=0
            )
        
        # Get files to filter (from previous stage)
        files_to_filter = context.filtered_files or context.matched_files
        if not files_to_filter:
            self._log(context, "[yellow]No files to filter[/yellow]")
            return StageResult(
                status=StageStatus.SUCCESS,
                message="No files to filter",
                files_processed=0
            )
            
        self._log(context, "[cyan]Filtering by rating...[/cyan]")
        
        # Apply filters (handles rating lookup and multi-disc grouping internally)
        files_to_keep = self._apply_filters(list(files_to_filter))
        
        # Delete filtered-out files
        filtered_out = [f for f in files_to_filter if f not in files_to_keep]
        
        for file_path in filtered_out:
            if file_path.exists():
                file_path.unlink()
        
        # Update context
        context.filtered_files = list(files_to_keep)
        
        # Log results
        filter_desc = self._get_filter_description()
        self._log(context, f"  Filter: {filter_desc}")
        self._log(context, f"  Kept: {len(files_to_keep)} files")
        self._log(context, f"  Filtered out: {len(filtered_out)} files")
        
        return StageResult(
            status=StageStatus.SUCCESS,
            message=f"Filtered to {len(files_to_keep)} files by rating",
            files_processed=len(files_to_filter)
        )
        
    def _get_file_ratings(
        self, 
        files: List[Path]
    ) -> Dict[Path, Dict[str, any]]:
        """
        Get ratings for files from ARRM database.
        Groups multi-disc games together and assigns the same rating.
        
        Args:
            files: List of file paths to look up
            
        Returns:
            Dictionary mapping file path to {name, rating, size_bytes, game_base}
        """
        import re
        
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()
        
        file_ratings = {}
        
        # Group files by game base name (remove disc number)
        disc_pattern = re.compile(r'\s*\(Disc\s+\d+\)|\s*\(Disk\s+\d+\)', re.IGNORECASE)
        game_groups: Dict[str, List[Path]] = {}
        
        for file_path in files:
            # Remove disc number to get base game name
            stem = file_path.stem
            base_name = disc_pattern.sub('', stem).strip()
            
            if base_name not in game_groups:
                game_groups[base_name] = []
            game_groups[base_name].append(file_path)
        
        # Look up rating for each game group
        for base_name, disc_files in game_groups.items():
            # Query for game rating (try to match base name)
            cursor.execute("""
                SELECT name, rating 
                FROM scraped_games 
                WHERE name LIKE ? OR filename LIKE ?
                ORDER BY rating DESC 
                LIMIT 1
            """, (f"%{base_name}%", f"%{base_name}%"))
            
            result = cursor.fetchone()
            if result:
                game_name, rating = result
            else:
                game_name = base_name
                rating = 0.0
            
            # Calculate total size for all discs of this game
            total_size = sum(f.stat().st_size if f.exists() else 0 for f in disc_files)
            
            # Assign same rating and total size to all discs
            for file_path in disc_files:
                file_ratings[file_path] = {
                    'name': game_name,
                    'rating': rating or 0.0,
                    'size_bytes': total_size,  # Total size for all discs
                    'game_base': base_name,  # Group identifier
                    'disc_count': len(disc_files)
                }
        
        conn.close()
        return file_ratings
        
    def _apply_filters(
        self, 
        files: List[Path]
    ) -> Set[Path]:
        """
        Apply rating-based filters to determine which files to keep.
        Treats multi-disc games as atomic units.
        
        Args:
            files: List of file paths to filter
            
        Returns:
            Set of file paths to keep
        """
        if not files:
            return set()
        
        # Get ratings for all files (groups multi-disc games)
        file_ratings = self._get_file_ratings(files)
        
        # Group files by game base name
        game_groups: Dict[str, List[Path]] = {}
        for file_path, info in file_ratings.items():
            game_base = info['game_base']
            if game_base not in game_groups:
                game_groups[game_base] = []
            game_groups[game_base].append(file_path)
        
        # Create game entries with aggregated info
        games = []
        for game_base, disc_files in game_groups.items():
            # All discs have same rating and total size
            first_file = disc_files[0]
            info = file_ratings[first_file]
            
            games.append({
                'base': game_base,
                'name': info['name'],
                'rating': info['rating'],
                'size_bytes': info['size_bytes'],  # Already total for all discs
                'disc_files': disc_files,
                'disc_count': len(disc_files)
            })
        
        # Sort games by rating (descending)
        games.sort(key=lambda g: g['rating'], reverse=True)
        
        # Apply filters
        files_to_keep = set()
        
        if self.top_n:
            # Keep top N games (all discs of each game)
            kept_games = games[:self.top_n]
            for game in kept_games:
                files_to_keep.update(game['disc_files'])
        
        elif self.max_size_gb:
            # Keep games until size budget exceeded (complete games only)
            max_bytes = int(self.max_size_gb * 1024 * 1024 * 1024)
            total_size = 0
            kept_games = []
            
            for game in games:
                game_size = game['size_bytes']
                if total_size + game_size <= max_bytes:
                    kept_games.append(game)
                    files_to_keep.update(game['disc_files'])
                    total_size += game_size
                else:
                    # Game doesn't fit - stop here
                    break
        
        return files_to_keep
    
    def _get_filter_description(self) -> str:
        """Get human-readable filter description."""
        parts = []
        if self.top_n:
            parts.append(f"top {self.top_n}")
        if self.max_size_gb:
            parts.append(f"within {self.max_size_gb}GB")
        if self.min_rating:
            parts.append(f"rating >= {self.min_rating:.2f}")
        return " + ".join(parts) if parts else "no filter"

