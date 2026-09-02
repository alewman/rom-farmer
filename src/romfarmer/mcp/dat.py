"""MCP tools for arcade DAT file queries: hardware, variants, search."""

from typing import Any

from romfarmer.core.paths import get_paths

WORKSPACE_ROOT = get_paths().workspace_root


async def tool_dat_hardware_list(dat_type: str = "fbneo") -> dict[str, Any]:
    """List all arcade hardware platforms with game counts."""
    from romfarmer.metadata.database import MetadataDatabase

    db_path = WORKSPACE_ROOT / "metadata" / "database" / "romfarmer.db"
    if not db_path.exists():
        return {"error": "Metadata database not found"}

    try:
        db = MetadataDatabase(db_path)
        hardware = db.get_hardware_list(dat_type)
        return {"dat_type": dat_type, "count": len(hardware), "hardware": hardware}
    except Exception as e:
        return {"error": str(e)}


async def tool_dat_hardware_games(
    hardware: str,
    dat_type: str = "fbneo",
    parents_only: bool = True,
) -> dict[str, Any]:
    """Get all games for a specific arcade hardware/driver."""
    from romfarmer.metadata.database import MetadataDatabase

    db_path = WORKSPACE_ROOT / "metadata" / "database" / "romfarmer.db"
    if not db_path.exists():
        return {"error": "Metadata database not found"}

    try:
        db = MetadataDatabase(db_path)
        games = db.get_hardware_games(hardware, dat_type, parents_only)
        return {
            "hardware": hardware,
            "dat_type": dat_type,
            "parents_only": parents_only,
            "count": len(games),
            "games": [
                {
                    "name": g.name,
                    "description": g.description,
                    "year": g.year,
                    "manufacturer": g.manufacturer,
                    "driver_status": g.driver_status,
                    "resolution": g.resolution,
                    "orientation": g.video_orientation,
                }
                for g in games
            ],
        }
    except Exception as e:
        return {"error": str(e)}


async def tool_dat_game_variants(
    game_name: str,
    dat_type: str = "fbneo",
) -> dict[str, Any]:
    """Get a game and all its variants/clones/hacks."""
    from romfarmer.metadata.database import MetadataDatabase

    db_path = WORKSPACE_ROOT / "metadata" / "database" / "romfarmer.db"
    if not db_path.exists():
        return {"error": "Metadata database not found"}

    try:
        db = MetadataDatabase(db_path)
        result = db.get_dat_game_variants(game_name, dat_type)
        if not result["parent"]:
            return {"error": f"Game not found: {game_name}"}
        return result
    except Exception as e:
        return {"error": str(e)}


async def tool_dat_search(
    query: str,
    dat_type: str = "fbneo",
    hardware: str | None = None,
    parents_only: bool = False,
    limit: int = 30,
) -> dict[str, Any]:
    """Search arcade games by name or description."""
    from romfarmer.metadata.database import MetadataDatabase

    db_path = WORKSPACE_ROOT / "metadata" / "database" / "romfarmer.db"
    if not db_path.exists():
        return {"error": "Metadata database not found"}

    try:
        db = MetadataDatabase(db_path)
        games = db.search_dat_games(
            query=query,
            dat_type=dat_type,
            hardware=hardware,
            parents_only=parents_only,
            limit=limit,
        )
        return {
            "query": query,
            "dat_type": dat_type,
            "hardware": hardware,
            "count": len(games),
            "games": games,
        }
    except Exception as e:
        return {"error": str(e)}
