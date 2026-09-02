"""MCP tools for ScreenScraper rich game metadata."""

from typing import Any

from romfarmer.core.paths import get_paths

WORKSPACE_ROOT = get_paths().workspace_root


async def tool_scraper_search(
    query: str,
    platform: str | None = None,
    genre: str | None = None,
    limit: int = 20,
    show_variants: bool = False,
    title_only: bool = True,
) -> dict[str, Any]:
    """Search ScreenScraper game database with rich metadata."""
    from romfarmer.metadata.database import MetadataDatabase

    db_path = WORKSPACE_ROOT / "metadata" / "database" / "romfarmer.db"
    if not db_path.exists():
        return {"error": "Metadata database not found"}

    try:
        db = MetadataDatabase(db_path)
        games = db.search_games(
            platform=platform,
            query=query,
            genre=genre,
            limit=limit,
            deduplicate=not show_variants,
            title_only=title_only,
        )
        return {
            "query": query,
            "platform": platform,
            "genre": genre,
            "show_variants": show_variants,
            "count": len(games),
            "games": [
                {
                    "name": g.name,
                    "system": g.system,
                    "developer": g.developer,
                    "publisher": g.publisher,
                    "genre": g.genre,
                    "players": g.players,
                    "rating": g.rating,
                    "release_date": g.release_date,
                    "region": g.region,
                    "game_id": g.game_id,
                }
                for g in games
            ],
        }
    except Exception as e:
        return {"error": str(e)}


async def tool_scraper_game_info(
    name: str,
    platform: str | None = None,
    show_variants: bool = False,
) -> dict[str, Any]:
    """Get detailed ScreenScraper info for a specific game."""
    from romfarmer.metadata.database import MetadataDatabase

    db_path = WORKSPACE_ROOT / "metadata" / "database" / "romfarmer.db"
    if not db_path.exists():
        return {"error": "Metadata database not found"}

    try:
        db = MetadataDatabase(db_path)
        game = db.get_game_by_name(name, platform)

        if not game:
            return {"name": name, "platform": platform, "error": "Game not found"}

        result = {
            "name": game.name,
            "system": game.system,
            "developer": game.developer,
            "publisher": game.publisher,
            "genre": game.genre,
            "players": game.players,
            "rating": game.rating,
            "release_date": game.release_date,
            "region": game.region,
            "language": game.language,
            "description": game.description,
            "screenscraper_id": game.game_id,
        }

        if show_variants and game.game_id:
            variants = db.get_game_variants(game.game_id)
            if len(variants) > 1:
                result["variants"] = [
                    {"name": v.name, "region": v.region, "language": v.language, "system": v.system}
                    for v in variants
                ]
                result["variant_count"] = len(variants)

        return result
    except Exception as e:
        return {"error": str(e)}


async def tool_scraper_platforms() -> dict[str, Any]:
    """List all platforms with game counts from ScreenScraper data."""
    from romfarmer.metadata.database import MetadataDatabase

    db_path = WORKSPACE_ROOT / "metadata" / "database" / "romfarmer.db"
    if not db_path.exists():
        return {"error": "Metadata database not found"}

    try:
        db = MetadataDatabase(db_path)
        platforms = db.get_platforms()
        return {
            "total_platforms": len(platforms),
            "total_games": sum(p["game_count"] for p in platforms),
            "platforms": platforms,
        }
    except Exception as e:
        return {"error": str(e)}


async def tool_scraper_genres(platform: str | None = None) -> dict[str, Any]:
    """List all genres with game counts."""
    from romfarmer.metadata.database import MetadataDatabase

    db_path = WORKSPACE_ROOT / "metadata" / "database" / "romfarmer.db"
    if not db_path.exists():
        return {"error": "Metadata database not found"}

    try:
        db = MetadataDatabase(db_path)
        genres = db.get_genres(platform)
        return {"platform": platform, "total_genres": len(genres), "genres": genres}
    except Exception as e:
        return {"error": str(e)}


async def tool_scraper_top_rated(
    platform: str,
    genre: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Get top-rated games for a platform."""
    from romfarmer.metadata.database import MetadataDatabase

    db_path = WORKSPACE_ROOT / "metadata" / "database" / "romfarmer.db"
    if not db_path.exists():
        return {"error": "Metadata database not found"}

    try:
        db = MetadataDatabase(db_path)
        games = db.search_games(platform=platform, genre=genre, min_rating=0.1, limit=limit)
        return {
            "platform": platform,
            "genre": genre,
            "count": len(games),
            "games": [
                {
                    "name": g.name,
                    "rating": g.rating,
                    "genre": g.genre,
                    "developer": g.developer,
                    "release_date": g.release_date,
                }
                for g in games
            ],
        }
    except Exception as e:
        return {"error": str(e)}
