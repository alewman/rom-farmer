"""Pre-filter stage for fast filename-based filtering.

Runs BEFORE FilterDAT to minimize MD5 calculations and file I/O.
Filters are composable and applied in sequence:
1. Letter filter (first character)
2. Region filter (USA, EUR, JPN, World, etc.)
3. Language filter (En, Eng, Fr, De, etc.)

This dramatically reduces the number of files that need MD5 hashing
in the subsequent FilterDAT stage.
"""

from pathlib import Path
from typing import List

from .base import Stage, StageContext, StageResult, StageStatus, StagePhase


class PreFilterStage(Stage):
    PHASE = StagePhase.PLAN

    """Pre-filter source files based on filename patterns.
    
    Fast, zero-I/O filtering that runs before DAT matching.
    Reduces source_files list based on:
    - Letter: First character of filename
    - Region: Region tags like (USA), (Europe), (World)
    - Language: Language tags like (En), (Fr), (De)
    
    Example:
        Original: 2000 PS3 games
        After letter 'A': ~80 games (96% reduction)
        After region 'USA': ~60 games (97% reduction)
        
        FilterDAT now only needs to MD5 60 files instead of 2000!
    """

    def __init__(self):
        """Initialize pre-filter stage."""
        super().__init__("Pre-Filter")

    def should_skip(self, context: StageContext) -> bool:
        """Skip if no filters configured or no source files."""
        has_filters = (
            context.letter_filter is not None
            or context.region_filter is not None
            or context.language_filter is not None
        )
        return not has_filters or not context.source_files

    def validate_context(self, context: StageContext) -> str | None:
        """Validate context - no special requirements."""
        return None

    def execute(self, context: StageContext) -> StageResult:
        """Execute pre-filtering on source files.
        
        Args:
            context: Stage context with source_files and filter parameters
            
        Returns:
            Result with filtered file count
        """
        import time
        start_time = time.time()
        
        initial_count = len(context.source_files)
        filtered_files = context.source_files.copy()
        
        self._log(context, f"[cyan]Starting with {initial_count:,} files[/cyan]")
        
        # Apply letter filter
        if context.letter_filter:
            filtered_files = self._filter_by_letter(
                filtered_files, 
                context.letter_filter,
                context
            )
            self._log(
                context, 
                f"  Letter '{context.letter_filter}': {len(filtered_files):,} files "
                f"({len(filtered_files)/initial_count*100:.1f}%)"
            )
        
        # Apply region filter
        if context.region_filter:
            filtered_files = self._filter_by_region(
                filtered_files,
                context.region_filter,
                context
            )
            self._log(
                context,
                f"  Region {context.region_filter}: {len(filtered_files):,} files "
                f"({len(filtered_files)/initial_count*100:.1f}%)"
            )
        
        # Apply language filter
        if context.language_filter:
            filtered_files = self._filter_by_language(
                filtered_files,
                context.language_filter,
                context
            )
            self._log(
                context,
                f"  Language {context.language_filter}: {len(filtered_files):,} files "
                f"({len(filtered_files)/initial_count*100:.1f}%)"
            )
        
        # Update context
        excluded_count = initial_count - len(filtered_files)
        context.source_files = filtered_files
        
        duration = time.time() - start_time
        
        self._log(
            context,
            f"[green]✓ Filtered to {len(filtered_files):,} files "
            f"(excluded {excluded_count:,}, {excluded_count/initial_count*100:.1f}%)[/green]"
        )
        
        return StageResult(
            status=StageStatus.SUCCESS,
            message=f"Pre-filtered to {len(filtered_files):,} files",
            files_processed=initial_count,
            files_matched=len(filtered_files),
            files_skipped=excluded_count,
            duration_seconds=duration,
            details={
                "initial_count": initial_count,
                "final_count": len(filtered_files),
                "excluded_count": excluded_count,
                "letter_filter": context.letter_filter,
                "region_filter": context.region_filter,
                "language_filter": context.language_filter,
            }
        )

    def _filter_by_letter(
        self, 
        files: List[Path], 
        letter: str,
        context: StageContext
    ) -> List[Path]:
        """Filter files by first letter of filename.
        
        Args:
            files: List of file paths
            letter: Single letter (e.g., 'A', 'B')
            context: Stage context for logging
            
        Returns:
            Filtered list of files
        """
        letter_upper = letter.upper()[0]
        
        filtered = [
            f for f in files 
            if f.stem[0].upper() == letter_upper
        ]
        
        return filtered

    def _filter_by_region(
        self,
        files: List[Path],
        regions: List[str],
        context: StageContext
    ) -> List[Path]:
        """Filter files by region tags in filename.
        
        Looks for region tags in parentheses:
        - (USA)
        - (Europe) or (EUR)
        - (Japan) or (JPN)
        - (World)
        - (Asia)
        
        Args:
            files: List of file paths
            regions: List of region strings (e.g., ['USA', 'World'])
            context: Stage context for logging
            
        Returns:
            Filtered list of files
        """
        # Normalize region names
        region_patterns = []
        for region in regions:
            region_upper = region.upper()
            # Add common variations
            if region_upper == "USA":
                region_patterns.extend(["(USA)", "(US)"])
            elif region_upper in ["EUROPE", "EUR"]:
                region_patterns.extend(["(Europe)", "(EUR)"])
            elif region_upper in ["JAPAN", "JPN"]:
                region_patterns.extend(["(Japan)", "(JPN)", "(Jpn)"])
            elif region_upper == "WORLD":
                region_patterns.append("(World)")
            elif region_upper == "ASIA":
                region_patterns.append("(Asia)")
            else:
                # Generic pattern
                region_patterns.append(f"({region})")
        
        filtered = [
            f for f in files
            if any(pattern in f.name for pattern in region_patterns)
        ]
        
        return filtered

    def _filter_by_language(
        self,
        files: List[Path],
        languages: List[str],
        context: StageContext
    ) -> List[Path]:
        """Filter files by language tags in filename.
        
        Looks for language tags in parentheses or comma-separated:
        - (En) or (Eng)
        - (Fr)
        - (De)
        - (Es)
        - (It)
        - (En,Fr,De,Es,It)
        
        Args:
            files: List of file paths
            languages: List of language codes (e.g., ['En', 'Eng'])
            context: Stage context for logging
            
        Returns:
            Filtered list of files
        """
        # Normalize language codes
        lang_patterns = []
        for lang in languages:
            lang_title = lang.title()  # En, Fr, De, etc.
            # Check both standalone and in comma-separated list
            # Match: (En) or (En,Fr) or (Fr,En,De)
            lang_patterns.append(lang_title)
        
        filtered = [
            f for f in files
            if any(
                # Check if language appears in filename
                # Either as (En) or as part of (En,Fr,De,...)
                lang in f.name
                for lang in lang_patterns
            )
        ]
        
        return filtered
