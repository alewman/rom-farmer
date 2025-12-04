"""Filter ROMs using various selection strategies."""

import random
import re
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Set

from ..config.models import SelectionConfig, SelectionStrategy, PatternType
from ..core.paths import get_paths
from .base import Stage, StageContext, StageResult, StageStatus


# Conservative compression ratio defaults (used when no historical data)
# These are intentionally pessimistic to avoid over-selecting
# Actual ratios improve over time as builds record real transformations
DEFAULT_COMPRESSION_RATIOS = {
    "saturn": 0.65,      # Sega Saturn CD-ROMs → CHD (binary + audio)
    "psx": 0.70,         # PlayStation 1 CD-ROMs → CHD
    "ps2": 0.75,         # PlayStation 2 DVD-ROMs → CHD/CSO
    "psp": 0.85,         # PSP UMD → CSO (already compressed)
    "dreamcast": 0.68,   # Dreamcast GD-ROMs → CHD
    "gamecube": 0.72,    # GameCube mini-DVDs → RVZ
    "wii": 0.70,         # Wii DVDs → RVZ
    "xbox": 0.80,        # Xbox DVDs → XISO (removes padding)
    "xbox360": 0.82,     # Xbox 360 DVDs → XISO/GOD
    "ps3": 0.90,         # PS3 Blu-rays → JB format (large files, less compression)
    "segacd": 0.62,      # Sega CD → CHD (excellent compression)
    "pcenginecd": 0.68,  # PC Engine CD → CHD
    "neogeocd": 0.65,    # Neo Geo CD → CHD
    "3do": 0.70,         # 3DO CD-ROMs → CHD
}


class SelectionFilter(Stage):
    """
    Filter ROMs using flexible selection strategies.
    
    This stage runs after FilterDAT but before ApplyLists. It:
    1. Takes files from work_dir (symlinks created by DAT filter)
    2. Applies selection strategy (rating_budget, first, last, random, etc.)
    3. Deletes unwanted symlinks
    4. Preserves multi-disc game atomicity
    
    Supported strategies:
    - RATING_BUDGET: Quality-based selection with size limit (production)
    - FIRST: Take first N files alphabetically (testing)
    - LAST: Take last N files alphabetically (testing)
    - RANDOM: Random sampling (testing)
    - SMALLEST: Take N smallest files (testing)
    - LARGEST: Take N largest files (testing)
    - ALPHABETICAL: Take N files sorted alphabetically (testing)
    """
    
    def __init__(
        self,
        work_dir: Path,
        selection: SelectionConfig,
        metadata_db: Optional[Path] = None,
        platform: Optional[str] = None,
        output_format: Optional[str] = None
    ):
        """
        Initialize selection filter stage.
        
        Args:
            work_dir: Working directory containing files to filter
            selection: Selection configuration with strategy and parameters
            metadata_db: Path to ARRM metadata database (for rating_budget strategy)
            platform: Platform name (e.g., "saturn", "psx") for compression ratio lookup
            output_format: Output format (e.g., "chd", "cso") for compression ratio lookup
        """
        super().__init__(work_dir)
        self.selection = selection
        self.metadata_db = metadata_db or self._find_metadata_db()
        self.platform = platform
        self.output_format = output_format
        
    def _find_metadata_db(self) -> Optional[Path]:
        """Find ARRM metadata database using PathResolver."""
        # Use PathResolver for consistent path resolution
        db_path = get_paths().metadata_db
        if db_path.exists():
            return db_path
        
        # Fallback: check relative paths for compatibility
        fallback_paths = [
            Path.cwd() / "metadata" / "database" / "romgroomer.db",
            Path.cwd().parent / "metadata" / "database" / "romgroomer.db",
        ]
        
        for path in fallback_paths:
            if path.exists():
                return path
                
        return None
        
    def execute(self, context: StageContext) -> StageResult:
        """
        Filter files by selection strategy.
        
        Args:
            context: Stage context with files to process
            
        Returns:
            StageResult with filtering results
        """
        # Get files to filter (from previous stage)
        files_to_filter = context.filtered_files or context.matched_files
        if not files_to_filter:
            self._log(context, "[yellow]No files to filter[/yellow]")
            return StageResult(
                status=StageStatus.SUCCESS,
                message="No files to filter",
                files_processed=0
            )
            
        self._log(context, "[cyan]Applying selection filter...[/cyan]")
        
        # Apply selection strategy
        files_to_keep = self._apply_selection(list(files_to_filter))
        
        # Delete filtered-out files
        filtered_out = [f for f in files_to_filter if f not in files_to_keep]
        
        for file_path in filtered_out:
            if file_path.exists():
                file_path.unlink()
        
        # Update context
        context.filtered_files = list(files_to_keep)
        
        # Log results
        strategy_desc = self._get_strategy_description()
        self._log(context, f"  Strategy: {strategy_desc}")
        self._log(context, f"  Kept: {len(files_to_keep)} files")
        self._log(context, f"  Filtered out: {len(filtered_out)} files")
        
        return StageResult(
            status=StageStatus.SUCCESS,
            message=f"Selected {len(files_to_keep)} files using {self.selection.strategy.value}",
            files_processed=len(files_to_filter)
        )
        
    def _apply_selection(self, files: List[Path]) -> Set[Path]:
        """
        Apply selection strategy to files.
        
        Args:
            files: List of file paths to select from
            
        Returns:
            Set of selected file paths
        """
        # Group multi-disc games
        game_groups = self._group_multi_disc_games(files)
        total_games = len(game_groups)
        
        # Calculate offset and limit from percentage if specified
        offset_count = 0
        if self.selection.offset:
            offset_count = max(0, int(total_games * (self.selection.offset / 100)))
        
        if self.selection.percentage and not self.selection.limit:
            calculated_limit = max(1, int(total_games * (self.selection.percentage / 100)))
            # Temporarily set limit for selection methods
            self.selection.limit = calculated_limit
        
        # Apply offset by skipping first N games (if specified)
        if offset_count > 0:
            # Convert to sorted list for consistent ordering
            sorted_games = sorted(game_groups.keys())
            # Skip first offset_count games
            games_to_keep = sorted_games[offset_count:]
            # Filter game_groups to only include games after offset
            game_groups = {k: v for k, v in game_groups.items() if k in games_to_keep}
        
        # Apply strategy based on type
        strategy = self.selection.strategy
        
        if strategy == SelectionStrategy.RATING_BUDGET:
            return self._select_by_rating_budget(game_groups)
        elif strategy == SelectionStrategy.FIRST:
            return self._select_first(game_groups)
        elif strategy == SelectionStrategy.LAST:
            return self._select_last(game_groups)
        elif strategy == SelectionStrategy.RANDOM:
            return self._select_random(game_groups)
        elif strategy == SelectionStrategy.SMALLEST:
            return self._select_smallest(game_groups)
        elif strategy == SelectionStrategy.LARGEST:
            return self._select_largest(game_groups)
        elif strategy == SelectionStrategy.ALPHABETICAL:
            return self._select_alphabetical(game_groups)
        else:
            # Default: keep all
            return set(files)
    
    def _group_multi_disc_games(self, files: List[Path]) -> Dict[str, List[Path]]:
        """
        Group multi-disc games together.
        
        Args:
            files: List of file paths
            
        Returns:
            Dictionary mapping game base name to list of disc paths
        """
        # Pattern for multi-disc detection
        disc_pattern = re.compile(r'\(Dis[ck] \d+\)|\(Dis[ck] [A-Z]\)', re.IGNORECASE)
        
        game_groups = {}
        
        for file_path in files:
            # Apply demo exclusion filter if enabled
            if self.selection.exclude_demos and self._is_demo(file_path):
                continue
            
            # Remove disc number to get base name
            base_name = disc_pattern.sub('', file_path.stem).strip()
            
            if base_name not in game_groups:
                game_groups[base_name] = []
            
            game_groups[base_name].append(file_path)
        
        return game_groups
    
    def _is_demo(self, file_path: Path) -> bool:
        """
        Check if file is a demo/beta/proto/sample based on filename.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file appears to be a demo/beta/proto
        """
        filename_lower = file_path.name.lower()
        demo_patterns = [
            r'\(demo\)',
            r'\(beta\)',
            r'\(proto\)',
            r'\(prototype\)',
            r'\(sample\)',
            r'\(preview\)',
            r'\(trial\)',
            r'\(kiosk\)',
            r'\[demo\]',
            r'\[beta\]',
            r'\[proto\]',
            r'\[sample\]',
        ]
        
        for pattern in demo_patterns:
            if re.search(pattern, filename_lower):
                return True
        
        return False
        
        for file_path in files:
            # Remove disc number to get base game name
            stem = file_path.stem
            base_name = disc_pattern.sub('', stem).strip()
            
            if base_name not in game_groups:
                game_groups[base_name] = []
            game_groups[base_name].append(file_path)
        
        return game_groups
    
    def _select_by_rating_budget(self, game_groups: Dict[str, List[Path]]) -> Set[Path]:
        """
        Select games by rating within size budget.
        
        Uses historical compression ratios to predict final output size
        and select games accordingly. Budget is inflated by compression
        ratio to account for transformation (e.g., ISO → CHD).
        
        Args:
            game_groups: Dictionary of game base name to disc files
            
        Returns:
            Set of selected file paths
        """
        if not self.metadata_db or not self.metadata_db.exists():
            self._log_warning("No metadata database available for rating_budget strategy")
            return set()
        
        # Get compression ratio (historical or default)
        compression_ratio = self._get_compression_ratio()
        
        # Calculate adjusted budget (with safety factor for slack space)
        safety_factor = 0.95  # Target 95% to leave breathing room
        max_size_bytes = None
        if self.selection.max_size_gb:
            # Inflate budget by compression ratio, then apply safety factor
            adjusted_budget_gb = (self.selection.max_size_gb / compression_ratio) * safety_factor
            max_size_bytes = int(adjusted_budget_gb * 1024 * 1024 * 1024)
            
            # Log budget adjustment
            print(f"  Budget adjustment:")
            print(f"    Target output: {self.selection.max_size_gb:.1f} GB")
            print(f"    Compression ratio: {compression_ratio:.2f}")
            print(f"    Safety factor: {safety_factor:.2f}")
            print(f"    Adjusted source budget: {adjusted_budget_gb:.1f} GB")
        
        # Get ratings for all games
        game_ratings = self._get_game_ratings(game_groups)
        
        # Sort by rating (highest first)
        sorted_games = sorted(
            game_ratings.items(),
            key=lambda x: (x[1]['rating'] or 0, x[0]),
            reverse=True
        )
        
        # Apply filters
        selected = set()
        total_size = 0
        
        for game_base, info in sorted_games:
            game_files = game_groups[game_base]
            game_size = info['total_size']
            
            # Apply metadata exclusion filters
            if self.selection.exclude_hidden and info.get('hidden', False):
                continue
            
            if self.selection.exclude_unrated and (info['rating'] is None or info['rating'] == 0.0):
                continue
            
            # Check min_rating filter
            if self.selection.min_rating and (info['rating'] or 0) < self.selection.min_rating:
                continue
            
            # Check top_n filter
            if self.selection.limit and len(selected) >= self.selection.limit:
                break
            
            # Check size budget
            if max_size_bytes and (total_size + game_size) > max_size_bytes:
                continue
            
            # Add all discs for this game
            selected.update(game_files)
            total_size += game_size
        
        # Log final selection stats
        if max_size_bytes:
            predicted_output_gb = (total_size / (1024 * 1024 * 1024)) * compression_ratio
            print(f"  Selection results:")
            print(f"    Source size: {total_size / (1024 * 1024 * 1024):.1f} GB")
            print(f"    Predicted output: {predicted_output_gb:.1f} GB")
            print(f"    Budget utilization: {(predicted_output_gb / self.selection.max_size_gb) * 100:.1f}%")
        
        return selected
    
    def _get_compression_ratio(self) -> float:
        """
        Get compression ratio from historical data or defaults.
        
        Returns:
            Compression ratio (0.0-1.0) representing output_size / input_size
        """
        # Try to get historical ratio from database
        if self.metadata_db and self.metadata_db.exists():
            try:
                from ..metadata.database import MetadataDatabase
                db = MetadataDatabase(self.metadata_db)
                
                ratio = db.get_average_compression_ratio(
                    platform=self.platform,
                    output_format=self.output_format,
                    min_samples=5
                )
                
                if ratio:
                    print(f"  Using historical compression ratio: {ratio:.2f} ({self.platform}/{self.output_format})")
                    return ratio
            except Exception as e:
                print(f"  Warning: Failed to query compression ratio: {e}")
        
        # Fall back to defaults
        if self.platform and self.platform.lower() in DEFAULT_COMPRESSION_RATIOS:
            ratio = DEFAULT_COMPRESSION_RATIOS[self.platform.lower()]
            print(f"  Using default compression ratio: {ratio:.2f} ({self.platform})")
            return ratio
        
        # Ultimate fallback
        print(f"  Using generic compression ratio: 0.75 (no platform data)")
        return 0.75
    
    def _select_first(self, game_groups: Dict[str, List[Path]]) -> Set[Path]:
        """Select first N games alphabetically."""
        sorted_games = sorted(game_groups.keys())
        limit = self.selection.limit or len(sorted_games)
        
        selected = set()
        for game_base in sorted_games[:limit]:
            selected.update(game_groups[game_base])
        
        return selected
    
    def _select_last(self, game_groups: Dict[str, List[Path]]) -> Set[Path]:
        """Select last N games alphabetically."""
        sorted_games = sorted(game_groups.keys())
        limit = self.selection.limit or len(sorted_games)
        
        selected = set()
        for game_base in sorted_games[-limit:]:
            selected.update(game_groups[game_base])
        
        return selected
    
    def _select_random(self, game_groups: Dict[str, List[Path]]) -> Set[Path]:
        """Select N random games."""
        game_list = list(game_groups.keys())
        limit = min(self.selection.limit or len(game_list), len(game_list))
        
        selected_games = random.sample(game_list, limit)
        
        selected = set()
        for game_base in selected_games:
            selected.update(game_groups[game_base])
        
        return selected
    
    def _select_smallest(self, game_groups: Dict[str, List[Path]]) -> Set[Path]:
        """Select N smallest games by total size."""
        # Calculate total size for each game
        game_sizes = []
        for game_base, files in game_groups.items():
            total_size = sum(f.stat().st_size for f in files if f.exists())
            game_sizes.append((game_base, total_size))
        
        # Sort by size (smallest first)
        sorted_games = sorted(game_sizes, key=lambda x: x[1])
        limit = self.selection.limit or len(sorted_games)
        
        selected = set()
        for game_base, _ in sorted_games[:limit]:
            selected.update(game_groups[game_base])
        
        return selected
    
    def _select_largest(self, game_groups: Dict[str, List[Path]]) -> Set[Path]:
        """Select N largest games by total size."""
        # Calculate total size for each game
        game_sizes = []
        for game_base, files in game_groups.items():
            total_size = sum(f.stat().st_size for f in files if f.exists())
            game_sizes.append((game_base, total_size))
        
        # Sort by size (largest first)
        sorted_games = sorted(game_sizes, key=lambda x: x[1], reverse=True)
        limit = self.selection.limit or len(sorted_games)
        
        selected = set()
        for game_base, _ in sorted_games[:limit]:
            selected.update(game_groups[game_base])
        
        return selected
    
    def _select_alphabetical(self, game_groups: Dict[str, List[Path]]) -> Set[Path]:
        """Select N games alphabetically (same as FIRST)."""
        return self._select_first(game_groups)
    
    def _get_game_ratings(self, game_groups: Dict[str, List[Path]]) -> Dict[str, Dict]:
        """
        Get ratings and metadata for games from metadata database.
        
        Args:
            game_groups: Dictionary of game base name to disc files
            
        Returns:
            Dictionary mapping game base name to {rating, total_size, file_count, hidden, metadata}
        """
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()
        
        # Check which tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}
        has_scraped_games = 'scraped_games' in tables
        has_games = 'games' in tables
        
        game_ratings = {}
        
        for game_base, files in game_groups.items():
            # Look up metadata for first disc (all discs have same metadata)
            first_file = files[0]
            file_name = first_file.name
            
            rating = None
            hidden = False
            favorite = False
            kidgame = False
            playcount = 0
            lastplayed = None
            
            found = False
            
            # Try scraped_games table first (new schema with hidden/favorite/etc)
            if has_scraped_games:
                try:
                    cursor.execute(
                        """
                        SELECT rating, hidden, favorite, kidgame, playcount, lastplayed
                        FROM scraped_games 
                        WHERE LOWER(filename) = LOWER(?)
                        """,
                        (file_name,)
                    )
                    result = cursor.fetchone()
                    if result:
                        rating, hidden, favorite, kidgame, playcount, lastplayed = result
                        found = True
                except sqlite3.OperationalError:
                    pass
            
            if not found and has_games:
                # Fallback to old games table (legacy compatibility)
                try:
                    cursor.execute(
                        """
                        SELECT rating 
                        FROM games 
                        WHERE LOWER(file_name) = LOWER(?)
                        """,
                        (file_name,)
                    )
                    old_result = cursor.fetchone()
                    if old_result:
                        rating = old_result[0]
                        found = True
                except sqlite3.OperationalError:
                    pass
            
            # Calculate total size for all discs
            total_size = sum(f.stat().st_size for f in files if f.exists())
            
            game_ratings[game_base] = {
                'rating': rating,
                'total_size': total_size,
                'file_count': len(files),
                'hidden': bool(hidden),
                'favorite': bool(favorite),
                'kidgame': bool(kidgame),
                'playcount': playcount or 0,
                'lastplayed': lastplayed,
            }
        
        conn.close()
        return game_ratings
    
    def _get_strategy_description(self) -> str:
        """Get human-readable description of selection strategy."""
        strategy = self.selection.strategy
        parts = [strategy.value]
        
        if self.selection.offset:
            parts.append(f"offset={self.selection.offset}%")
        
        if self.selection.percentage:
            parts.append(f"percentage={self.selection.percentage}%")
        elif self.selection.limit:
            parts.append(f"limit={self.selection.limit}")
        
        if strategy == SelectionStrategy.RATING_BUDGET:
            if self.selection.max_size_gb:
                parts.append(f"max_size={self.selection.max_size_gb}GB")
            if self.selection.min_rating:
                parts.append(f"min_rating={self.selection.min_rating}")
        
        if self.selection.pattern:
            parts.append(f"pattern={self.selection.pattern.value}")
        
        # Add exclusion filters
        exclusions = []
        if self.selection.exclude_hidden:
            exclusions.append("hidden")
        if self.selection.exclude_unrated:
            exclusions.append("unrated")
        if self.selection.exclude_demos:
            exclusions.append("demos")
        
        if exclusions:
            parts.append(f"exclude={','.join(exclusions)}")
        
        return ", ".join(parts)
    
    def _log_warning(self, message: str):
        """Log warning message (compatibility method)."""
        # TODO: Use proper logging when context is available
        print(f"[yellow]Warning: {message}[/yellow]")
