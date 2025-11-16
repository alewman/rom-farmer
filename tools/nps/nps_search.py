"""Advanced search engine for NoPayStation content.

Provides intelligent fuzzy search with:
- Multiple search strategies (exact, fuzzy, Title ID, Content ID)
- Automatic dependency resolution (base game + DLC + updates)
- Region filtering and ranking
- Result deduplication and scoring
"""

from difflib import SequenceMatcher
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict

from .nps_database import NPSDatabase
from .nps_models import ContentEntry, TitleBundle


class NPSSearch:
    """Advanced search engine for NoPayStation content.
    
    Provides multiple search strategies with intelligent ranking:
    1. Exact match (highest priority)
    2. Fuzzy name matching (scored by similarity)
    3. Title ID extraction and relationship mapping
    4. Content ID matching
    """
    
    def __init__(self, database: NPSDatabase):
        """Initialize search engine.
        
        Args:
            database: Loaded NPSDatabase instance
        """
        self.db = database
    
    def search(
        self,
        query: str,
        platform: Optional[str] = None,
        content_type: Optional[str] = None,
        region: Optional[str] = None,
        min_score: float = 0.3,
        limit: int = 50
    ) -> List[Tuple[ContentEntry, float]]:
        """Search for content with fuzzy matching.
        
        Args:
            query: Search query (name, Title ID, or Content ID)
            platform: Optional platform filter
            content_type: Optional content type filter
            region: Optional region filter
            min_score: Minimum similarity score (0.0-1.0)
            limit: Maximum results to return
            
        Returns:
            List of (ContentEntry, score) tuples, sorted by relevance
        """
        query_lower = query.lower().strip()
        
        # Strategy 1: Check if query is a Title ID (exact match)
        if self._looks_like_title_id(query):
            title_results = self.db.get_by_title_id(query.upper(), platform)
            if title_results:
                # Apply filters
                title_results = self._apply_filters(
                    title_results, content_type, region
                )
                # Return with perfect score
                return [(entry, 1.0) for entry in title_results[:limit]]
        
        # Strategy 2: Check if query is a Content ID (exact match)
        if self._looks_like_content_id(query):
            content_result = self.db.get_by_content_id(query.upper())
            if content_result:
                # Apply filters
                if self._matches_filters(content_result, platform, content_type, region):
                    return [(content_result, 1.0)]
        
        # Strategy 3: Fuzzy name matching
        scored_results = []
        
        for entry in self.db.entries:
            # Apply platform/type/region filters early
            if not self._matches_filters(entry, platform, content_type, region):
                continue
            
            # Calculate similarity score
            score = self._calculate_similarity(query_lower, entry.name.lower())
            
            if score >= min_score:
                scored_results.append((entry, score))
        
        # Sort by score (descending) and limit
        scored_results.sort(key=lambda x: x[1], reverse=True)
        return scored_results[:limit]
    
    def search_with_dependencies(
        self,
        query: str,
        platform: Optional[str] = None,
        region: Optional[str] = None,
        include_dlc: bool = True,
        include_updates: bool = True,
        include_themes: bool = False,
        min_score: float = 0.3
    ) -> List[TitleBundle]:
        """Search for games and automatically include related content.
        
        This is the --complete flag behavior: finds base games and includes
        all related DLC, updates, themes automatically.
        
        Args:
            query: Search query
            platform: Optional platform filter
            region: Optional region filter
            include_dlc: Include DLC in bundles
            include_updates: Include updates in bundles
            include_themes: Include themes in bundles
            min_score: Minimum similarity score
            
        Returns:
            List of TitleBundle objects with complete content
        """
        # First, search for base games only
        game_results = self.search(
            query=query,
            platform=platform,
            content_type='games',
            region=region,
            min_score=min_score,
            limit=50
        )
        
        # Build bundles for each game found
        bundles = []
        seen_title_ids = set()
        
        for entry, score in game_results:
            # Skip if we've already processed this Title ID
            if entry.title_id in seen_title_ids:
                continue
            seen_title_ids.add(entry.title_id)
            
            # Build complete bundle
            bundle = self.db.build_title_bundle(
                entry.title_id,
                entry.platform,
                region=region or entry.region
            )
            
            if bundle:
                # Filter bundle content based on flags
                if not include_dlc:
                    bundle.dlc = []
                if not include_updates:
                    bundle.updates = []
                if not include_themes:
                    bundle.themes = []
                
                bundles.append(bundle)
        
        return bundles
    
    def find_dlc_for_title(
        self,
        title_id: str,
        platform: str,
        region: Optional[str] = None
    ) -> List[ContentEntry]:
        """Find all DLC for a specific Title ID.
        
        Args:
            title_id: Title ID to search for
            platform: Platform
            region: Optional region filter
            
        Returns:
            List of DLC entries
        """
        all_content = self.db.get_by_title_id(title_id, platform)
        
        # Filter to DLC only
        dlc = [e for e in all_content if e.content_type == 'dlc']
        
        # Apply region filter if specified
        if region:
            region = region.upper()
            dlc = [e for e in dlc if e.region == region]
        
        return dlc
    
    def find_updates_for_title(
        self,
        title_id: str,
        platform: str,
        region: Optional[str] = None
    ) -> List[ContentEntry]:
        """Find all updates for a specific Title ID.
        
        Args:
            title_id: Title ID to search for
            platform: Platform
            region: Optional region filter
            
        Returns:
            List of update entries
        """
        all_content = self.db.get_by_title_id(title_id, platform)
        
        # Filter to updates only
        updates = [e for e in all_content if e.content_type == 'updates']
        
        # Apply region filter if specified
        if region:
            region = region.upper()
            updates = [e for e in updates if e.region == region]
        
        # Sort by version (newest first)
        # Note: Version sorting could be improved with proper semver
        updates.sort(key=lambda x: x.version or '', reverse=True)
        
        return updates
    
    def get_related_content(
        self,
        entry: ContentEntry,
        include_types: Optional[List[str]] = None
    ) -> Dict[str, List[ContentEntry]]:
        """Get all content related to an entry (same Title ID).
        
        Args:
            entry: ContentEntry to find related content for
            include_types: Optional list of types to include
                          (games, dlc, updates, themes, etc.)
            
        Returns:
            Dictionary mapping content type to list of entries
        """
        # Get all content with same Title ID
        all_content = self.db.get_by_title_id(entry.title_id, entry.platform)
        
        # Group by type
        by_type = defaultdict(list)
        for related in all_content:
            # Skip the entry itself
            if related.content_id == entry.content_id:
                continue
            
            # Filter by type if specified
            if include_types and related.content_type not in include_types:
                continue
            
            by_type[related.content_type].append(related)
        
        return dict(by_type)
    
    def deduplicate_bundles(self, bundles: List[TitleBundle]) -> List[TitleBundle]:
        """Remove duplicate bundles (same Title ID + region).
        
        Args:
            bundles: List of TitleBundle objects
            
        Returns:
            Deduplicated list
        """
        seen = set()
        unique = []
        
        for bundle in bundles:
            key = (bundle.title_id, bundle.platform, bundle.region)
            if key not in seen:
                seen.add(key)
                unique.append(bundle)
        
        return unique
    
    def _looks_like_title_id(self, query: str) -> bool:
        """Check if query looks like a Title ID.
        
        Examples: BLUS31627, PCSE00065, NPJB00769
        """
        query_upper = query.upper().strip()
        
        # Title IDs are typically 9 characters: 4 letters + 5 digits
        # Format: BLUS31627, PCSE00065, etc.
        if len(query_upper) == 9:
            return query_upper[:4].isalpha() and query_upper[4:].isdigit()
        
        return False
    
    def _looks_like_content_id(self, query: str) -> bool:
        """Check if query looks like a Content ID.
        
        Examples: UP9000-NPUA80136_00-SIRENBCEPISODE05
        """
        # Content IDs contain hyphens and underscores
        # Format: UP9000-NPUA80136_00-SIRENBCEPISODE05
        return '-' in query and ('_' in query or len(query) > 15)
    
    def _calculate_similarity(self, query: str, name: str) -> float:
        """Calculate similarity score between query and name.
        
        Uses multiple scoring methods:
        1. Exact substring match (highest)
        2. Word-level matching
        3. SequenceMatcher ratio
        
        Args:
            query: Search query (normalized)
            name: Entry name (normalized)
            
        Returns:
            Similarity score (0.0-1.0)
        """
        # Normalize both strings
        query = query.lower().strip()
        name = name.lower().strip()
        
        # Exact match
        if query == name:
            return 1.0
        
        # Exact substring match
        if query in name:
            # Bonus for matching at start
            if name.startswith(query):
                return 0.95
            return 0.85
        
        # Word-level matching (all query words in name)
        query_words = set(query.split())
        name_words = set(name.split())
        
        if query_words and query_words.issubset(name_words):
            # All query words found
            word_ratio = len(query_words) / len(name_words)
            return 0.7 + (0.2 * word_ratio)  # 0.7-0.9 range
        
        # Partial word matching
        if query_words and name_words:
            matching_words = query_words & name_words
            if matching_words:
                word_score = len(matching_words) / len(query_words)
                return 0.5 + (0.2 * word_score)  # 0.5-0.7 range
        
        # Fallback to SequenceMatcher
        matcher = SequenceMatcher(None, query, name)
        return matcher.ratio()
    
    def _matches_filters(
        self,
        entry: ContentEntry,
        platform: Optional[str] = None,
        content_type: Optional[str] = None,
        region: Optional[str] = None
    ) -> bool:
        """Check if entry matches all specified filters.
        
        Args:
            entry: ContentEntry to check
            platform: Optional platform filter
            content_type: Optional type filter
            region: Optional region filter
            
        Returns:
            True if entry matches all filters
        """
        if platform and entry.platform != platform.lower():
            return False
        
        if content_type and entry.content_type != content_type.lower():
            return False
        
        if region and entry.region != region.upper():
            return False
        
        return True
    
    def _apply_filters(
        self,
        entries: List[ContentEntry],
        content_type: Optional[str] = None,
        region: Optional[str] = None
    ) -> List[ContentEntry]:
        """Apply filters to list of entries.
        
        Args:
            entries: List of ContentEntry objects
            content_type: Optional type filter
            region: Optional region filter
            
        Returns:
            Filtered list
        """
        if content_type:
            content_type = content_type.lower()
            entries = [e for e in entries if e.content_type == content_type]
        
        if region:
            region = region.upper()
            entries = [e for e in entries if e.region == region]
        
        return entries


class SearchResultFormatter:
    """Format search results for display."""
    
    @staticmethod
    def format_entry(entry: ContentEntry, score: Optional[float] = None) -> str:
        """Format a single entry for display.
        
        Args:
            entry: ContentEntry to format
            score: Optional similarity score
            
        Returns:
            Formatted string
        """
        parts = [entry.name]
        parts.append(f"({entry.title_id})")
        parts.append(f"[{entry.platform.upper()}/{entry.content_type}]")
        
        if entry.region:
            parts.append(f"<{entry.region}>")
        
        if score is not None:
            parts.append(f"- {score:.1%} match")
        
        return " ".join(parts)
    
    @staticmethod
    def format_bundle(bundle: TitleBundle, show_details: bool = True) -> str:
        """Format a TitleBundle for display.
        
        Args:
            bundle: TitleBundle to format
            show_details: Show detailed content breakdown
            
        Returns:
            Formatted string
        """
        lines = []
        
        # Header
        game_name = bundle.get_display_name()
        lines.append(f"📦 {game_name} ({bundle.title_id}) [{bundle.platform.upper()}/{bundle.region}]")
        
        if show_details:
            counts = bundle.count_by_type()
            total_size = bundle.get_total_size()
            
            # Content summary
            parts = []
            if counts['base_game']:
                parts.append(f"{counts['base_game']} game")
            if counts['dlc']:
                parts.append(f"{counts['dlc']} DLC")
            if counts['updates']:
                parts.append(f"{counts['updates']} updates")
            if counts['themes']:
                parts.append(f"{counts['themes']} themes")
            
            if parts:
                lines.append(f"   Content: {', '.join(parts)}")
            
            # Size
            size_gb = total_size / (1024**3)
            lines.append(f"   Size: {size_gb:.2f} GB")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_search_results(
        results: List[Tuple[ContentEntry, float]],
        limit: Optional[int] = None
    ) -> str:
        """Format search results for display.
        
        Args:
            results: List of (entry, score) tuples
            limit: Optional limit on results to show
            
        Returns:
            Formatted string
        """
        if not results:
            return "No results found."
        
        lines = [f"Found {len(results)} result(s):"]
        lines.append("")
        
        display_results = results[:limit] if limit else results
        
        for i, (entry, score) in enumerate(display_results, 1):
            formatted = SearchResultFormatter.format_entry(entry, score)
            lines.append(f"{i}. {formatted}")
        
        if limit and len(results) > limit:
            lines.append(f"\n... and {len(results) - limit} more")
        
        return "\n".join(lines)
