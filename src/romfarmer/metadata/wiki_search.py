"""
Wikipedia Search API for Game Information

Provides semantic search over Wikipedia game articles using LanceDB
for vector similarity and DuckDB for metadata queries.

Usage:
    from romfarmer.metadata.wiki_search import WikiSearch

    search = WikiSearch()
    results = search.search("horror game with zombies", limit=5)

    # Or get info for a specific game
    info = search.get_game_info("Resident Evil")
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Lazy imports for optional dependencies
_lancedb = None
_duckdb = None
_model = None


def _get_lancedb():
    global _lancedb
    if _lancedb is None:
        import lancedb

        _lancedb = lancedb
    return _lancedb


def _get_duckdb():
    global _duckdb
    if _duckdb is None:
        import duckdb

        _duckdb = duckdb
    return _duckdb


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model


class WikiSearch:
    """
    Semantic search over Wikipedia game articles.

    Combines:
    - LanceDB for vector similarity search
    - DuckDB for SQL queries on metadata
    - Sentence transformers for query embedding
    """

    def __init__(self, data_dir: Path | None = None):
        if data_dir is None:
            data_dir = (
                Path(__file__).parent.parent.parent.parent / "data" / "wikipedia" / "processed"
            )

        self.data_dir = Path(data_dir)
        self.lancedb_path = self.data_dir / "lancedb"
        self.duckdb_path = self.data_dir / "wikipedia.duckdb"

        self._lance_table = None
        self._duck_conn = None

    @property
    def lance_table(self):
        """Lazy-load LanceDB table."""
        if self._lance_table is None:
            lancedb = _get_lancedb()
            db = lancedb.connect(str(self.lancedb_path))
            self._lance_table = db.open_table("wiki_chunks")
        return self._lance_table

    @property
    def duck_conn(self):
        """Lazy-load DuckDB connection."""
        if self._duck_conn is None:
            duckdb = _get_duckdb()
            self._duck_conn = duckdb.connect(str(self.duckdb_path), read_only=True)
        return self._duck_conn

    def search(
        self,
        query: str,
        limit: int = 10,
        section_filter: str | None = None,
        game_filter: str | None = None,
    ) -> list[dict]:
        """
        Semantic search for relevant Wikipedia content.

        Args:
            query: Natural language search query
            limit: Maximum results to return
            section_filter: Filter to specific section types (e.g., "Gameplay", "Plot")
            game_filter: Filter to specific game title

        Returns:
            List of matching chunks with metadata and relevance scores
        """
        model = _get_model()
        embedding = model.encode(query).tolist()

        # Build search
        search = self.lance_table.search(embedding).limit(limit * 2)  # Get extra for filtering

        # Apply filters if provided
        if section_filter:
            search = search.where(f"section_title LIKE '%{section_filter}%'")
        if game_filter:
            search = search.where(f"game_title LIKE '%{game_filter}%'")

        results = search.to_list()

        # Format results with deduplication
        formatted = []
        seen = set()  # Track (article_title, section_title) pairs

        for r in results:
            if len(formatted) >= limit:
                break

            # Deduplicate by article + section
            key = (r["article_title"], r["section_title"])
            if key in seen:
                continue
            seen.add(key)

            formatted.append(
                {
                    "game_title": r["game_title"],
                    "article_title": r["article_title"],
                    "article_url": r["article_url"],
                    "section": r["section_title"],
                    "content": r["content"],
                    "score": 1 - r["_distance"],  # Convert distance to similarity
                    "chunk_id": r["chunk_id"],
                }
            )

        return formatted

    def get_game_info(self, game_title: str) -> dict | None:
        """
        Get all Wikipedia information about a specific game.

        Args:
            game_title: The game title to look up

        Returns:
            Dict with game info organized by section, or None if not found
        """
        _get_duckdb()

        # Search for the game (fuzzy match)
        result = self.duck_conn.execute(
            """
            SELECT DISTINCT article_title, article_url, game_title
            FROM wiki_chunks
            WHERE game_title ILIKE $1 OR article_title ILIKE $1
            LIMIT 1
        """,
            [f"%{game_title}%"],
        ).fetchone()

        if not result:
            return None

        article_title, article_url, matched_game = result

        # Get all sections for this article
        sections = self.duck_conn.execute(
            """
            SELECT section_title, content, chunk_index
            FROM wiki_chunks
            WHERE article_title = $1
            ORDER BY chunk_index
        """,
            [article_title],
        ).fetchall()

        # Organize by section
        organized = {}
        for section_title, content, _ in sections:
            if section_title not in organized:
                organized[section_title] = []
            organized[section_title].append(content)

        # Join chunks within each section
        for section in organized:
            organized[section] = "\n\n".join(organized[section])

        return {
            "title": article_title,
            "game_title": matched_game,
            "url": article_url,
            "sections": organized,
        }

    def get_section(self, game_title: str, section_name: str) -> str | None:
        """
        Get a specific section from a game's Wikipedia article.

        Args:
            game_title: The game to look up
            section_name: The section name (e.g., "Gameplay", "Plot", "Reception")

        Returns:
            The section content or None if not found
        """
        result = self.duck_conn.execute(
            """
            SELECT content
            FROM wiki_chunks
            WHERE (game_title ILIKE $1 OR article_title ILIKE $1)
              AND section_title ILIKE $2
            ORDER BY chunk_index
        """,
            [f"%{game_title}%", f"%{section_name}%"],
        ).fetchall()

        if not result:
            return None

        return "\n\n".join(r[0] for r in result)

    def list_games(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """List all games with Wikipedia articles."""
        result = self.duck_conn.execute(
            """
            SELECT DISTINCT
                game_title,
                article_title,
                article_url,
                COUNT(*) as num_chunks,
                SUM(token_count) as total_tokens
            FROM wiki_chunks
            GROUP BY game_title, article_title, article_url
            ORDER BY game_title
            LIMIT $1 OFFSET $2
        """,
            [limit, offset],
        ).fetchall()

        return [
            {
                "game_title": r[0],
                "article_title": r[1],
                "url": r[2],
                "chunks": r[3],
                "tokens": r[4],
            }
            for r in result
        ]

    def stats(self) -> dict:
        """Get statistics about the Wikipedia data."""
        result = self.duck_conn.execute("SELECT * FROM wiki_stats").fetchone()

        return {
            "total_chunks": result[0],
            "total_articles": result[1],
            "unique_games": result[2],
            "avg_tokens_per_chunk": round(result[3], 1),
            "total_tokens": result[4],
        }

    def search_by_section_type(self, query: str, section_type: str, limit: int = 10) -> list[dict]:
        """
        Search within a specific type of section.

        Useful for targeted queries like:
        - "difficult boss" in "Gameplay" sections
        - "critical acclaim" in "Reception" sections
        - "development history" in "Development" sections

        Args:
            query: Search query
            section_type: Section to search in (Gameplay, Plot, Reception, Development, etc.)
            limit: Max results
        """
        return self.search(query, limit=limit, section_filter=section_type)

    def find_games(
        self,
        query: str,
        limit: int = 10,
        threshold: float = 0.5,
    ) -> list[dict]:
        """
        Fuzzy search for game titles using Jaro-Winkler similarity.

        Handles:
        - Typos and misspellings
        - Partial titles ("sonic 2" -> "Sonic the Hedgehog 2")
        - Word variations

        Scoring:
        - Base: Jaro-Winkler similarity (0-1)
        - Containment bonus (+0.15): Query is substring of title
        - All words bonus (+0.25): All query words appear in title

        Args:
            query: Game title to search for (fuzzy)
            limit: Maximum results to return
            threshold: Minimum similarity score (0-1) to include

        Returns:
            List of matching games with similarity scores, sorted by relevance
        """
        query_lower = query.lower().strip()
        # Keep all words, including single chars like "2" in "sonic 2"
        words = query_lower.split()

        if not words:
            return []

        # Build SQL conditions dynamically (escaping words for safety)
        def escape_like(s: str) -> str:
            """Escape special LIKE characters."""
            return s.replace("%", "\\%").replace("_", "\\_")

        escaped_words = [escape_like(w) for w in words]

        # ILIKE any word match (pre-filter for speed)
        ilike_any = " OR ".join([f"LOWER(game_title) LIKE '%{w}%'" for w in escaped_words])

        # ILIKE all words match (for bonus)
        ilike_all = " AND ".join([f"LOWER(game_title) LIKE '%{w}%'" for w in escaped_words])

        # Containment check (full query as substring)
        escaped_query = escape_like(query_lower)

        # Hybrid search with multiple bonuses
        # - Jaro-Winkler for fuzzy matching
        # - Containment bonus if query is substring of title
        # - All-words bonus if all query words appear in title
        results = self.duck_conn.execute(
            f"""
            SELECT * FROM (
                SELECT DISTINCT
                    game_title,
                    article_title,
                    article_url,
                    jaro_winkler_similarity(LOWER(game_title), ?) as jw_sim,
                    CASE WHEN LOWER(game_title) LIKE '%{escaped_query}%'
                         THEN 0.15 ELSE 0.0 END as containment_bonus,
                    CASE WHEN {ilike_all}
                         THEN 0.25 ELSE 0.0 END as all_words_bonus
                FROM wiki_chunks
                WHERE {ilike_any}
            ) sub
            WHERE jw_sim >= ?
            ORDER BY (jw_sim + containment_bonus + all_words_bonus) DESC, jw_sim DESC
            LIMIT ?
        """,
            [query_lower, threshold, limit * 3],
        ).fetchall()

        # If no word matches, fall back to pure similarity search (slower)
        if not results:
            results = self.duck_conn.execute(
                f"""
                SELECT * FROM (
                    SELECT DISTINCT
                        game_title,
                        article_title,
                        article_url,
                        jaro_winkler_similarity(LOWER(game_title), ?) as jw_sim,
                        CASE WHEN LOWER(game_title) LIKE '%{escaped_query}%'
                             THEN 0.15 ELSE 0.0 END as containment_bonus,
                        0.0 as all_words_bonus
                    FROM wiki_chunks
                ) sub
                WHERE jw_sim >= ?
                ORDER BY (jw_sim + containment_bonus) DESC, jw_sim DESC
                LIMIT ?
            """,
                [query_lower, threshold, limit * 3],
            ).fetchall()

        # Return combined score (capped at 1.0), limited to requested count
        return [
            {
                "game_title": r[0],
                "article_title": r[1],
                "url": r[2],
                "similarity": round(min(float(r[3]) + float(r[4]) + float(r[5]), 1.0), 3),
            }
            for r in results[:limit]
        ]


# Convenience functions for quick access
_search_instance = None


def get_search() -> WikiSearch:
    """Get or create a WikiSearch instance."""
    global _search_instance
    if _search_instance is None:
        _search_instance = WikiSearch()
    return _search_instance


def search(query: str, limit: int = 10) -> list[dict]:
    """Quick semantic search."""
    return get_search().search(query, limit=limit)


def get_game_info(game_title: str) -> dict | None:
    """Quick game lookup."""
    return get_search().get_game_info(game_title)
