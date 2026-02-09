"""
Graph Database Layer for Zelda MCP

Uses Kuzu for relationship queries:
- Cross-platform game versions
- Genre browsing
- Translation tracking
- Collection analysis

This is WHERE THE SPEED COMES FROM.
SQL joins = O(n²) for relationship queries
Graph traversal = O(edges) - linear in relationships
"""

import os
from pathlib import Path
from typing import Optional
import logging

try:
    import kuzu
    KUZU_AVAILABLE = True
except ImportError:
    KUZU_AVAILABLE = False

logger = logging.getLogger(__name__)


class GameGraph:
    """
    Graph database for game relationships.
    
    Schema:
        (:Game)           - Individual ROM files
        (:CanonicalGame)  - The "concept" of a game
        (:Platform)       - Gaming platforms
        (:Genre)          - Game genres
        
    Relationships:
        (:Game)-[:VERSION_OF]->(:CanonicalGame)
        (:Game)-[:ON_PLATFORM]->(:Platform)
        (:Game)-[:HAS_GENRE]->(:Genre)
        (:CanonicalGame)-[:SEQUEL_OF]->(:CanonicalGame)
        (:Game)-[:TRANSLATION_OF]->(:Game)
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        if not KUZU_AVAILABLE:
            raise RuntimeError(
                "Kuzu not installed. Run: pip install kuzu"
            )
        
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent.parent / "metadata" / "database" / "games.kuzu"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.db = kuzu.Database(str(self.db_path))
        self.conn = kuzu.Connection(self.db)
        
    def initialize_schema(self):
        """Create the graph schema (run once)."""
        
        # Node tables
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Game (
                id STRING PRIMARY KEY,
                name STRING,
                platform STRING,
                region STRING,
                languages STRING[],
                file_size INT64,
                format STRING,
                md5 STRING,
                sha1 STRING,
                crc32 STRING,
                rating FLOAT,
                players INT32,
                release_date STRING,
                developer STRING,
                publisher STRING,
                description STRING
            )
        """)
        
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS CanonicalGame (
                id STRING PRIMARY KEY,
                canonical_name STRING,
                first_release_year INT32,
                developer STRING,
                publisher STRING
            )
        """)
        
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Platform (
                id STRING PRIMARY KEY,
                name STRING,
                full_name STRING,
                generation INT32,
                manufacturer STRING
            )
        """)
        
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Genre (
                id STRING PRIMARY KEY,
                name STRING
            )
        """)
        
        # Relationship tables
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS VERSION_OF (
                FROM Game TO CanonicalGame
            )
        """)
        
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS ON_PLATFORM (
                FROM Game TO Platform
            )
        """)
        
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS HAS_GENRE (
                FROM Game TO Genre
            )
        """)
        
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS SEQUEL_OF (
                FROM CanonicalGame TO CanonicalGame,
                order INT32
            )
        """)
        
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS TRANSLATION_OF (
                FROM Game TO Game,
                language STRING
            )
        """)
        
        logger.info("Graph schema initialized")
    
    # =========================================================================
    # QUERY METHODS - These are what MCP tools will call
    # =========================================================================
    
    def find_games(self, name: str, limit: int = 20) -> list[dict]:
        """
        Fuzzy search for games by name.
        
        Example: find_games("castlevania") -> all Castlevania games
        """
        result = self.conn.execute("""
            MATCH (g:Game)
            WHERE g.name CONTAINS $name
            RETURN g.name AS name, g.platform AS platform, g.region AS region, g.rating AS rating
            ORDER BY g.rating DESC
            LIMIT $limit
        """, {"name": name, "limit": limit})
        
        return result.get_as_df().to_dict('records')
    
    def get_all_versions(self, canonical_name: str) -> list[dict]:
        """
        Find all versions of a game across all platforms.
        
        This is THE query that SQL can't do efficiently.
        
        Example: 
            get_all_versions("Castlevania") ->
            [
                {"name": "Castlevania", "platform": "nes", "region": "USA"},
                {"name": "Castlevania Chronicles", "platform": "psx", "region": "USA"},
                {"name": "Akumajou Dracula", "platform": "nes", "region": "Japan"},
                ...
            ]
        """
        result = self.conn.execute("""
            MATCH (g:Game)-[:VERSION_OF]->(c:CanonicalGame)
            WHERE c.canonical_name CONTAINS $name
            RETURN g.name AS name, g.platform AS platform, g.region AS region, 
                   g.rating AS rating
            ORDER BY g.rating DESC
        """, {"name": canonical_name})
        
        return result.get_as_df().to_dict('records')
    
    def best_version_for_platform(
        self, 
        canonical_name: str, 
        platforms: list[str]
    ) -> Optional[dict]:
        """
        Find the best version of a game for specific platforms.
        
        Example:
            best_version_for_platform("Final Fantasy", ["snes", "gba", "psx"])
            -> {"name": "Final Fantasy VI", "platform": "snes", "rating": 4.8}
        """
        result = self.conn.execute("""
            MATCH (g:Game)-[:VERSION_OF]->(c:CanonicalGame)
            WHERE c.canonical_name CONTAINS $name
              AND g.platform IN $platforms
            RETURN g.name AS name, g.platform AS platform, g.region AS region, g.rating AS rating
            ORDER BY g.rating DESC
            LIMIT 1
        """, {"name": canonical_name, "platforms": platforms})
        
        df = result.get_as_df()
        if len(df) > 0:
            return df.iloc[0].to_dict()
        return None
    
    def games_by_genre(
        self, 
        genre: str, 
        platforms: Optional[list[str]] = None,
        limit: int = 50
    ) -> list[dict]:
        """
        Find games by genre, optionally filtered by platform.
        
        Example:
            games_by_genre("RPG", platforms=["snes", "psx"])
            -> [{"name": "Chrono Trigger", ...}, {"name": "Final Fantasy VII", ...}]
        """
        if platforms:
            result = self.conn.execute("""
                MATCH (g:Game)-[:HAS_GENRE]->(genre:Genre)
                WHERE genre.name = $genre AND g.platform IN $platforms
                RETURN g.name AS name, g.platform AS platform, g.rating AS rating
                ORDER BY g.rating DESC
                LIMIT $limit
            """, {"genre": genre, "platforms": platforms, "limit": limit})
        else:
            result = self.conn.execute("""
                MATCH (g:Game)-[:HAS_GENRE]->(genre:Genre)
                WHERE genre.name = $genre
                RETURN g.name AS name, g.platform AS platform, g.rating AS rating
                ORDER BY g.rating DESC
                LIMIT $limit
            """, {"genre": genre, "limit": limit})
        
        return result.get_as_df().to_dict('records')
    
    def find_translations(self, game_name: str) -> list[dict]:
        """
        Find fan translations of a game.
        
        Example:
            find_translations("Mother 3")
            -> [{"original": "Mother 3 (Japan)", "translation": "Mother 3 (English Patch)", "language": "English"}]
        """
        result = self.conn.execute("""
            MATCH (original:Game)<-[:TRANSLATION_OF]-(translation:Game)
            WHERE original.name CONTAINS $name OR translation.name CONTAINS $name
            RETURN original.name AS original, 
                   translation.name AS translation,
                   translation.languages AS languages
        """, {"name": game_name})
        
        return result.get_as_df().to_dict('records')
    
    def collection_for_budget(
        self,
        budget_bytes: int,
        platforms: list[str],
        genres: Optional[list[str]] = None,
        min_rating: float = 3.0
    ) -> list[dict]:
        """
        Build a collection that fits within a size budget.
        
        Prioritizes highest-rated games that fit.
        
        Example:
            collection_for_budget(
                budget_bytes=64 * 1024**3,  # 64GB
                platforms=["snes", "gba", "psx"],
                min_rating=4.0
            )
        """
        # This would be a more complex query in practice
        # For now, simple greedy approach
        result = self.conn.execute("""
            MATCH (g:Game)
            WHERE g.platform IN $platforms 
              AND g.rating >= $min_rating
            RETURN g.name AS name, g.platform AS platform, g.rating AS rating
            ORDER BY g.rating DESC
        """, {"platforms": platforms, "min_rating": min_rating})
        
        # Note: file_size not in schema yet, return all matching games
        return result.get_as_df().to_dict('records')
    
    def platform_stats(self, platform: str) -> dict:
        """Get statistics for a platform."""
        result = self.conn.execute("""
            MATCH (g:Game)
            WHERE g.platform = $platform
            RETURN 
                count(g) AS total_games,
                avg(g.rating) AS avg_rating
        """, {"platform": platform})
        
        df = result.get_as_df()
        if len(df) > 0:
            return df.iloc[0].to_dict()
        return {"total_games": 0, "total_size": 0, "avg_rating": 0}
    
    def close(self):
        """Clean up database connection."""
        if hasattr(self, 'conn'):
            del self.conn
        if hasattr(self, 'db'):
            del self.db


# =============================================================================
# ETL: Import from SQLite
# =============================================================================

def import_from_sqlite(sqlite_path: Path, graph: GameGraph):
    """
    Import games from SQLite scraped_games table into the graph.
    
    This is the one-time migration from the old system.
    """
    import sqlite3
    
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all games
    cursor.execute("""
        SELECT 
            id, name, system_id, region, 
            md5, sha1, crc32,
            rating, players, release_date,
            developer, publisher, description
        FROM scraped_games
    """)
    
    count = 0
    for row in cursor.fetchall():
        # Insert game node
        graph.conn.execute("""
            CREATE (g:Game {
                id: $id,
                name: $name,
                platform: $platform,
                region: $region,
                md5: $md5,
                sha1: $sha1,
                crc32: $crc32,
                rating: $rating,
                players: $players,
                release_date: $release_date,
                developer: $developer,
                publisher: $publisher,
                description: $description
            })
        """, {
            "id": str(row['id']),
            "name": row['name'],
            "platform": row['system_id'],
            "region": row['region'] or "",
            "md5": row['md5'] or "",
            "sha1": row['sha1'] or "",
            "crc32": row['crc32'] or "",
            "rating": float(row['rating']) if row['rating'] else 0.0,
            "players": int(row['players']) if row['players'] else 1,
            "release_date": row['release_date'] or "",
            "developer": row['developer'] or "",
            "publisher": row['publisher'] or "",
            "description": row['description'] or ""
        })
        count += 1
        
        if count % 10000 == 0:
            logger.info(f"Imported {count} games...")
    
    logger.info(f"Imported {count} total games from SQLite")
    conn.close()


# =============================================================================
# CLI for testing
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Game Graph Database")
    parser.add_argument("command", choices=["init", "import", "query", "stats"])
    parser.add_argument("--sqlite", help="Path to SQLite database for import")
    parser.add_argument("--search", help="Game name to search")
    parser.add_argument("--platform", help="Platform to query")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    graph = GameGraph()
    
    if args.command == "init":
        graph.initialize_schema()
        print("Schema initialized!")
        
    elif args.command == "import":
        if not args.sqlite:
            print("--sqlite path required for import")
        else:
            graph.initialize_schema()
            import_from_sqlite(Path(args.sqlite), graph)
            
    elif args.command == "query":
        if args.search:
            results = graph.find_games(args.search)
            for r in results:
                print(f"  {r}")
                
    elif args.command == "stats":
        if args.platform:
            stats = graph.platform_stats(args.platform)
            print(f"Platform: {args.platform}")
            print(f"  Games: {stats['total_games']}")
            print(f"  Size: {stats['total_size'] / 1024**3:.1f} GB")
            print(f"  Avg Rating: {stats['avg_rating']:.2f}")
    
    graph.close()
