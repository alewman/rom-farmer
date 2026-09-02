"""MCP tools for ROM collection management: platforms, builds, budgets, queries."""

from typing import Any

from romfarmer.core.paths import get_paths

WORKSPACE_ROOT = get_paths().workspace_root


async def tool_list_platforms() -> dict[str, Any]:
    """List all configured platforms with basic info."""
    from romfarmer.config.loader import list_platform_configs

    platforms = []
    for name in list_platform_configs():
        try:
            config_path = WORKSPACE_ROOT / "config" / "platforms" / f"{name}.yaml"
            if config_path.exists():
                platforms.append(
                    {
                        "name": name,
                        "config_path": str(config_path),
                    }
                )
        except Exception:
            pass

    return {"count": len(platforms), "platforms": platforms}


async def tool_list_builds() -> dict[str, Any]:
    """List all available build configurations."""
    builds_dir = WORKSPACE_ROOT / "config" / "builds"
    builds = []

    if builds_dir.exists():
        for yaml_file in builds_dir.glob("*.yaml"):
            builds.append({"name": yaml_file.stem, "path": str(yaml_file)})

    return {"count": len(builds), "builds": builds}


async def tool_get_build_status(build_name: str) -> dict[str, Any]:
    """Get the status of a build (running, completed, failed)."""
    state_file = WORKSPACE_ROOT / f".build_state_{build_name}.yaml"

    if not state_file.exists():
        return {
            "build_name": build_name,
            "status": "not_found",
            "message": f"No state file found for build '{build_name}'",
        }

    import yaml

    with open(state_file) as f:
        state = yaml.safe_load(f)

    return {
        "build_name": build_name,
        "status": state.get("status", "unknown"),
        "started_at": state.get("started_at"),
        "completed_at": state.get("completed_at"),
        "platforms_completed": state.get("platforms_completed", []),
        "platforms_pending": state.get("platforms_pending", []),
        "current_platform": state.get("current_platform"),
    }


async def tool_get_platform_stats(platform: str) -> dict[str, Any]:
    """Get statistics for a platform's ROM collection."""
    from romfarmer.metadata.database import MetadataDatabase

    db_path = WORKSPACE_ROOT / "metadata" / "database" / "romfarmer.db"
    if not db_path.exists():
        return {"platform": platform, "error": "Metadata database not found"}

    try:
        db = MetadataDatabase(db_path)
        games = db.get_games_for_platform(platform)
        ratio = db.get_average_compression_ratio(platform, "chd")
        return {
            "platform": platform,
            "game_count": len(games) if games else 0,
            "compression_ratio_chd": ratio,
        }
    except Exception as e:
        return {"platform": platform, "error": str(e)}


async def tool_query_collection(
    platform: str,
    query: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Search for ROMs in a platform's collection."""
    from romfarmer.metadata.database import MetadataDatabase

    db_path = WORKSPACE_ROOT / "metadata" / "database" / "romfarmer.db"
    if not db_path.exists():
        return {"error": "Metadata database not found"}

    try:
        db = MetadataDatabase(db_path)
        games = db.search_games(platform=platform, query=query, limit=limit)
        return {
            "platform": platform,
            "query": query,
            "count": len(games),
            "games": [
                {"name": g.name, "region": g.region, "rating": g.rating, "genre": g.genre}
                for g in games[:limit]
            ],
        }
    except Exception as e:
        return {"error": str(e)}


async def tool_calculate_budget(
    platform: str,
    budget_gb: float,
    compression_format: str = "chd",
) -> dict[str, Any]:
    """Calculate how many ROMs fit in a storage budget."""
    from romfarmer.metadata.database import MetadataDatabase
    from romfarmer.planner.costmodel import CostModel, UnknownPlatformError

    db_path = WORKSPACE_ROOT / "metadata" / "database" / "romfarmer.db"
    try:
        ratio, _ = CostModel().ratio(platform)
    except UnknownPlatformError:
        ratio = 0.75

    if db_path.exists():
        try:
            db = MetadataDatabase(db_path)
            db_ratio = db.get_average_compression_ratio(platform, compression_format)
            if db_ratio:
                ratio = db_ratio
        except Exception:
            pass

    adjusted_budget_gb = (budget_gb / ratio) * 0.95
    return {
        "platform": platform,
        "target_output_gb": budget_gb,
        "compression_format": compression_format,
        "compression_ratio": ratio,
        "source_selection_budget_gb": round(adjusted_budget_gb, 2),
        "estimated_output_gb": round(adjusted_budget_gb * ratio, 2),
        "safety_margin_pct": 5,
    }


async def tool_get_compression_ratio(
    platform: str,
    output_format: str = "chd",
) -> dict[str, Any]:
    """Get historical compression ratio for a platform/format."""
    from romfarmer.metadata.database import MetadataDatabase
    from romfarmer.planner.costmodel import CostModel, UnknownPlatformError

    db_path = WORKSPACE_ROOT / "metadata" / "database" / "romfarmer.db"
    try:
        default_ratio, _ = CostModel().ratio(platform)
    except UnknownPlatformError:
        default_ratio = 0.75
    db_ratio = None

    if db_path.exists():
        try:
            db = MetadataDatabase(db_path)
            db_ratio = db.get_average_compression_ratio(platform, output_format)
        except Exception:
            pass

    return {
        "platform": platform,
        "output_format": output_format,
        "default_ratio": default_ratio,
        "learned_ratio": db_ratio,
        "active_ratio": db_ratio or default_ratio,
        "note": "Ratio < 1.0 means compression saves space",
    }
