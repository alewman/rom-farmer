"""
ROM Farmer MCP Server

An MCP (Model Context Protocol) server that exposes ROM Farmer functionality
to AI assistants like Claude.

This server provides tools for:
- Querying ROM collections and metadata
- Managing and monitoring builds
- Analyzing storage and compression
- Searching DAT files and configurations
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

# MCP imports (using FastMCP pattern)
# pip install mcp fastmcp
try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.types import (
        Tool,
        TextContent,
        Resource,
        ResourceTemplate,
        Prompt,
        PromptArgument,
        GetPromptResult,
        PromptMessage,
    )
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("MCP not installed. Run: pip install mcp")

# ROM Farmer imports
from romfarmer.core.paths import get_paths
from romfarmer.core.logger import get_logger


# Server configuration
SERVER_NAME = "romfarmer"
SERVER_VERSION = "0.1.0"

# Workspace root
WORKSPACE_ROOT = get_paths().workspace_root

logger = logging.getLogger(__name__)


# =============================================================================
# MCP Server Setup
# =============================================================================

if MCP_AVAILABLE:
    server = Server(SERVER_NAME)


# =============================================================================
# TOOLS: Actions the AI can take
# =============================================================================

async def tool_list_platforms() -> dict[str, Any]:
    """List all configured platforms with basic info."""
    from romfarmer.config.loader import list_platform_configs
    
    platforms = []
    for name in list_platform_configs():
        try:
            # Get basic platform info without full loading
            config_path = WORKSPACE_ROOT / "config" / "platforms" / f"{name}.yaml"
            if config_path.exists():
                platforms.append({
                    "name": name,
                    "config_path": str(config_path),
                })
        except Exception as e:
            logger.warning(f"Error loading platform {name}: {e}")
    
    return {
        "count": len(platforms),
        "platforms": platforms,
    }


async def tool_list_builds() -> dict[str, Any]:
    """List all available build configurations."""
    builds_dir = WORKSPACE_ROOT / "config" / "builds"
    builds = []
    
    if builds_dir.exists():
        for yaml_file in builds_dir.glob("*.yaml"):
            builds.append({
                "name": yaml_file.stem,
                "path": str(yaml_file),
            })
    
    return {
        "count": len(builds),
        "builds": builds,
    }


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
        return {
            "platform": platform,
            "error": "Metadata database not found",
        }
    
    try:
        db = MetadataDatabase(db_path)
        
        # Get game count
        games = db.get_games_for_platform(platform)
        
        # Get compression ratio if available
        ratio = db.get_average_compression_ratio(platform, "chd")
        
        return {
            "platform": platform,
            "game_count": len(games) if games else 0,
            "compression_ratio_chd": ratio,
        }
    except Exception as e:
        return {
            "platform": platform,
            "error": str(e),
        }


async def tool_query_collection(
    platform: str,
    query: Optional[str] = None,
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
                {
                    "name": g.name,
                    "region": g.region,
                    "rating": g.rating,
                    "genre": g.genre,
                }
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
    from romfarmer.stages.filter_selection import DEFAULT_COMPRESSION_RATIOS
    
    db_path = WORKSPACE_ROOT / "metadata" / "database" / "romfarmer.db"
    
    # Get compression ratio (from DB or defaults)
    ratio = DEFAULT_COMPRESSION_RATIOS.get(platform, 0.75)
    
    if db_path.exists():
        try:
            db = MetadataDatabase(db_path)
            db_ratio = db.get_average_compression_ratio(platform, compression_format)
            if db_ratio:
                ratio = db_ratio
        except Exception:
            pass
    
    # Calculate adjusted budget
    # Budget is output size, need to select more source files
    adjusted_budget_gb = (budget_gb / ratio) * 0.95  # 95% safety factor
    
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
    from romfarmer.stages.filter_selection import DEFAULT_COMPRESSION_RATIOS
    
    db_path = WORKSPACE_ROOT / "metadata" / "database" / "romfarmer.db"
    
    default_ratio = DEFAULT_COMPRESSION_RATIOS.get(platform, 0.75)
    db_ratio = None
    sample_count = 0
    
    if db_path.exists():
        try:
            db = MetadataDatabase(db_path)
            db_ratio = db.get_average_compression_ratio(platform, output_format)
            # Could add sample count query here
        except Exception:
            pass
    
    return {
        "platform": platform,
        "output_format": output_format,
        "default_ratio": default_ratio,
        "learned_ratio": db_ratio,
        "active_ratio": db_ratio or default_ratio,
        "sample_count": sample_count,
        "note": "Ratio < 1.0 means compression saves space",
    }


# =============================================================================
# WIKIPEDIA SEARCH TOOLS
# =============================================================================

async def tool_wiki_search(
    query: str,
    limit: int = 10,
    section_filter: Optional[str] = None,
) -> dict[str, Any]:
    """Semantic search over Wikipedia game articles."""
    try:
        from romfarmer.metadata.wiki_search import WikiSearch
        search = WikiSearch()
        
        results = search.search(
            query=query,
            limit=limit,
            section_filter=section_filter,
        )
        
        return {
            "query": query,
            "count": len(results),
            "results": [
                {
                    "game": r["article_title"],
                    "section": r["section"],
                    "score": round(r["score"], 3),
                    "content": r["content"][:500] + "..." if len(r["content"]) > 500 else r["content"],
                    "url": r["article_url"],
                }
                for r in results
            ],
        }
    except Exception as e:
        return {"error": str(e)}


async def tool_wiki_game_info(game_title: str) -> dict[str, Any]:
    """Get Wikipedia information about a specific game."""
    try:
        from romfarmer.metadata.wiki_search import WikiSearch
        search = WikiSearch()
        
        info = search.get_game_info(game_title)
        
        if not info:
            return {
                "game_title": game_title,
                "found": False,
                "message": f"No Wikipedia article found for '{game_title}'",
            }
        
        # Truncate long sections for readability
        sections_preview = {}
        for name, content in info["sections"].items():
            if len(content) > 1000:
                sections_preview[name] = content[:1000] + f"... ({len(content)} chars total)"
            else:
                sections_preview[name] = content
        
        return {
            "game_title": game_title,
            "found": True,
            "article_title": info["title"],
            "url": info["url"],
            "section_names": list(info["sections"].keys()),
            "sections": sections_preview,
        }
    except Exception as e:
        return {"error": str(e)}


async def tool_wiki_get_section(
    game_title: str,
    section_name: str,
) -> dict[str, Any]:
    """Get a specific section from a game's Wikipedia article."""
    try:
        from romfarmer.metadata.wiki_search import WikiSearch
        search = WikiSearch()
        
        content = search.get_section(game_title, section_name)
        
        if not content:
            return {
                "game_title": game_title,
                "section_name": section_name,
                "found": False,
            }
        
        return {
            "game_title": game_title,
            "section_name": section_name,
            "found": True,
            "content": content,
            "length": len(content),
        }
    except Exception as e:
        return {"error": str(e)}


async def tool_wiki_stats() -> dict[str, Any]:
    """Get statistics about the Wikipedia game database."""
    try:
        from romfarmer.metadata.wiki_search import WikiSearch
        search = WikiSearch()
        
        stats = search.stats()
        return {
            "total_chunks": stats["total_chunks"],
            "total_articles": stats["total_articles"],
            "unique_games": stats["unique_games"],
            "avg_tokens_per_chunk": stats["avg_tokens_per_chunk"],
            "total_tokens": stats["total_tokens"],
            "estimated_words": stats["total_tokens"] // 1.3,
        }
    except Exception as e:
        return {"error": str(e)}


async def tool_wiki_find_game(
    query: str,
    limit: int = 10,
    threshold: float = 0.5,
) -> dict[str, Any]:
    """Fuzzy search for game titles by name."""
    try:
        from romfarmer.metadata.wiki_search import WikiSearch
        search = WikiSearch()
        
        results = search.find_games(
            query=query,
            limit=limit,
            threshold=threshold,
        )
        
        return {
            "query": query,
            "count": len(results),
            "matches": results,
            "best_match": results[0] if results else None,
        }
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# SCREENSCRAPER TOOLS: Rich game metadata from ScreenScraper.fr
# =============================================================================

async def tool_scraper_search(
    query: str,
    platform: Optional[str] = None,
    genre: Optional[str] = None,
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
    platform: Optional[str] = None,
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
            return {
                "name": name,
                "platform": platform,
                "error": "Game not found",
            }
        
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
        
        # Add variants if requested
        if show_variants and game.game_id:
            variants = db.get_game_variants(game.game_id)
            if len(variants) > 1:
                result["variants"] = [
                    {
                        "name": v.name,
                        "region": v.region,
                        "language": v.language,
                        "system": v.system,
                    }
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


async def tool_scraper_genres(
    platform: Optional[str] = None,
) -> dict[str, Any]:
    """List all genres with game counts."""
    from romfarmer.metadata.database import MetadataDatabase
    
    db_path = WORKSPACE_ROOT / "metadata" / "database" / "romfarmer.db"
    
    if not db_path.exists():
        return {"error": "Metadata database not found"}
    
    try:
        db = MetadataDatabase(db_path)
        genres = db.get_genres(platform)
        
        return {
            "platform": platform,
            "total_genres": len(genres),
            "genres": genres,
        }
    except Exception as e:
        return {"error": str(e)}


async def tool_scraper_top_rated(
    platform: str,
    genre: Optional[str] = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Get top-rated games for a platform."""
    from romfarmer.metadata.database import MetadataDatabase
    
    db_path = WORKSPACE_ROOT / "metadata" / "database" / "romfarmer.db"
    
    if not db_path.exists():
        return {"error": "Metadata database not found"}
    
    try:
        db = MetadataDatabase(db_path)
        games = db.search_games(
            platform=platform,
            genre=genre,
            min_rating=0.1,  # Must have a rating
            limit=limit,
        )
        
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


# =============================================================================
# DAT FILE TOOLS: Hardware, variants, arcade database
# =============================================================================

async def tool_dat_hardware_list(
    dat_type: str = "fbneo",
) -> dict[str, Any]:
    """
    List all arcade hardware platforms with game counts.
    
    Args:
        dat_type: DAT source (fbneo, mame)
    """
    from romfarmer.metadata.database import MetadataDatabase
    
    db_path = WORKSPACE_ROOT / "metadata" / "database" / "romfarmer.db"
    
    if not db_path.exists():
        return {"error": "Metadata database not found"}
    
    try:
        db = MetadataDatabase(db_path)
        hardware = db.get_hardware_list(dat_type)
        
        return {
            "dat_type": dat_type,
            "count": len(hardware),
            "hardware": hardware,
        }
    except Exception as e:
        return {"error": str(e)}


async def tool_dat_hardware_games(
    hardware: str,
    dat_type: str = "fbneo",
    parents_only: bool = True,
) -> dict[str, Any]:
    """
    Get all games for a specific arcade hardware/driver.
    
    Args:
        hardware: Hardware name (e.g., cps1, neogeo, cps2, sys16b)
        dat_type: DAT source (fbneo, mame)
        parents_only: If True, only return parent games (no clones/hacks)
    """
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
    """
    Get a game and all its variants/clones/hacks.
    
    Use this to understand the relationship between different versions
    of a game (regional variants, bootlegs, hacks, etc.).
    
    Args:
        game_name: ROM name to search for (e.g., sf2ce, dino, mslug)
        dat_type: DAT source (fbneo, mame)
    """
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
    hardware: Optional[str] = None,
    parents_only: bool = False,
    limit: int = 30,
) -> dict[str, Any]:
    """
    Search arcade games by name or description.
    
    Args:
        query: Search query
        dat_type: DAT source (fbneo, mame)
        hardware: Filter by hardware (cps1, neogeo, etc.)
        parents_only: If True, exclude clones/hacks
        limit: Max results
    """
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


# =============================================================================
# RESOURCES: Data the AI can read
# =============================================================================

async def resource_platform_config(platform: str) -> str:
    """Get a platform's YAML configuration."""
    config_path = WORKSPACE_ROOT / "config" / "platforms" / f"{platform}.yaml"
    
    if not config_path.exists():
        return f"Platform config not found: {platform}"
    
    return config_path.read_text()


async def resource_build_config(build_name: str) -> str:
    """Get a build's YAML configuration."""
    config_path = WORKSPACE_ROOT / "config" / "builds" / f"{build_name}.yaml"
    
    if not config_path.exists():
        return f"Build config not found: {build_name}"
    
    return config_path.read_text()


async def resource_platform_list(list_type: str, platform: str) -> str:
    """Get a platform's keep or delete list."""
    list_path = WORKSPACE_ROOT / "lists" / f"{platform}-{list_type}"
    
    if not list_path.exists():
        return f"List not found: {platform}-{list_type}"
    
    return list_path.read_text()


# =============================================================================
# PROMPTS: Pre-defined conversation starters
# =============================================================================

PROMPTS = {
    "build_collection": {
        "name": "build_collection",
        "description": "Build a ROM collection for a target device",
        "arguments": [
            {"name": "platform", "description": "Platform to build (saturn, psx, etc.)", "required": True},
            {"name": "target", "description": "Target device (batocera, rocknix, etc.)", "required": False},
            {"name": "budget", "description": "Storage budget (64GB, 128GB, unlimited)", "required": False},
        ],
    },
    "analyze_collection": {
        "name": "analyze_collection", 
        "description": "Analyze a ROM collection's health and completeness",
        "arguments": [
            {"name": "platform", "description": "Platform to analyze", "required": True},
        ],
    },
    "recommend_games": {
        "name": "recommend_games",
        "description": "Get game recommendations within a budget",
        "arguments": [
            {"name": "platform", "description": "Platform name", "required": True},
            {"name": "budget_gb", "description": "Storage budget in GB", "required": True},
            {"name": "preferences", "description": "Genre/style preferences", "required": False},
        ],
    },
}


# =============================================================================
# MCP Server Registration (when MCP is available)
# =============================================================================

if MCP_AVAILABLE:
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """Return list of available tools."""
        return [
            Tool(
                name="list_platforms",
                description="List all configured ROM platforms",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="list_builds",
                description="List all available build configurations",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="get_build_status",
                description="Get the status of a build",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "build_name": {"type": "string", "description": "Name of the build"},
                    },
                    "required": ["build_name"],
                },
            ),
            Tool(
                name="get_platform_stats",
                description="Get statistics for a platform's ROM collection",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "platform": {"type": "string", "description": "Platform name (saturn, psx, etc.)"},
                    },
                    "required": ["platform"],
                },
            ),
            Tool(
                name="query_collection",
                description="Search for ROMs in a platform's collection",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "platform": {"type": "string", "description": "Platform name"},
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "description": "Max results", "default": 20},
                    },
                    "required": ["platform"],
                },
            ),
            Tool(
                name="calculate_budget",
                description="Calculate how many ROMs fit in a storage budget",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "platform": {"type": "string", "description": "Platform name"},
                        "budget_gb": {"type": "number", "description": "Storage budget in GB"},
                        "compression_format": {"type": "string", "description": "Compression format", "default": "chd"},
                    },
                    "required": ["platform", "budget_gb"],
                },
            ),
            Tool(
                name="get_compression_ratio",
                description="Get compression ratio for a platform/format combination",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "platform": {"type": "string", "description": "Platform name"},
                        "output_format": {"type": "string", "description": "Output format", "default": "chd"},
                    },
                    "required": ["platform"],
                },
            ),
            # Wikipedia Search Tools
            Tool(
                name="wiki_search",
                description="Semantic search over Wikipedia game articles. Use this to find games by description, gameplay style, themes, etc.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Natural language search query (e.g., 'horror game with zombies', 'turn-based JRPG')"},
                        "limit": {"type": "integer", "description": "Max results to return", "default": 10},
                        "section_filter": {"type": "string", "description": "Filter to specific section type (Gameplay, Plot, Reception, etc.)"},
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="wiki_game_info",
                description="Get full Wikipedia information about a specific game including all sections",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "game_title": {"type": "string", "description": "Game title to look up"},
                    },
                    "required": ["game_title"],
                },
            ),
            Tool(
                name="wiki_get_section",
                description="Get a specific section from a game's Wikipedia article (e.g., Gameplay, Plot, Reception)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "game_title": {"type": "string", "description": "Game title"},
                        "section_name": {"type": "string", "description": "Section name (Gameplay, Plot, Reception, Development, etc.)"},
                    },
                    "required": ["game_title", "section_name"],
                },
            ),
            Tool(
                name="wiki_stats",
                description="Get statistics about the Wikipedia game database",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="wiki_find_game",
                description="Fuzzy search for game titles by name. Use this when you need to find the exact title of a game. Returns candidates ranked by similarity.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Game title to search for (handles typos, partial names, variations)"},
                        "limit": {"type": "integer", "description": "Max results to return", "default": 10},
                        "threshold": {"type": "number", "description": "Minimum similarity score 0-1 (default 0.5)", "default": 0.5},
                    },
                    "required": ["query"],
                },
            ),
            # ScreenScraper tools (rich game metadata)
            Tool(
                name="scraper_search",
                description="Search ScreenScraper database for games with rich metadata (developer, publisher, genre, rating, description). Has 120K+ games across 49 platforms. By default, deduplicates regional variants (showing US > World > EU > JP preference).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query (searches name and description)"},
                        "platform": {"type": "string", "description": "Filter by platform (megadrive, psx, snes, etc.)"},
                        "genre": {"type": "string", "description": "Filter by genre (Platform, RPG, Action, etc.)"},
                        "limit": {"type": "integer", "description": "Max results", "default": 20},
                        "show_variants": {"type": "boolean", "description": "If true, show all regional variants instead of deduplicating", "default": False},
                        "title_only": {"type": "boolean", "description": "If true, search only game titles (more precise). If false, also search descriptions.", "default": True},
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="scraper_game_info",
                description="Get detailed ScreenScraper info for a specific game including description, developer, publisher, genre, rating, release date. Can also show all regional variants.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Game name to look up"},
                        "platform": {"type": "string", "description": "Platform to search in (optional, helps with disambiguation)"},
                        "show_variants": {"type": "boolean", "description": "If true, include all regional variants of this game", "default": False},
                    },
                    "required": ["name"],
                },
            ),
            Tool(
                name="scraper_platforms",
                description="List all platforms in ScreenScraper database with game counts",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="scraper_genres",
                description="List all genres with game counts, optionally filtered by platform",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "platform": {"type": "string", "description": "Filter genres by platform"},
                    },
                },
            ),
            Tool(
                name="scraper_top_rated",
                description="Get top-rated games for a platform, optionally filtered by genre",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "platform": {"type": "string", "description": "Platform name (required)"},
                        "genre": {"type": "string", "description": "Filter by genre"},
                        "limit": {"type": "integer", "description": "Max results", "default": 20},
                    },
                    "required": ["platform"],
                },
            ),
            # DAT file tools for arcade hardware and variants
            Tool(
                name="dat_hardware_list",
                description="List all arcade hardware platforms with game counts (CPS1, Neo Geo, etc.)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "dat_type": {"type": "string", "description": "DAT source (fbneo or mame)", "default": "fbneo"},
                    },
                },
            ),
            Tool(
                name="dat_hardware_games",
                description="Get all games for a specific arcade hardware/driver (e.g., all CPS1 games, all Neo Geo games)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "hardware": {"type": "string", "description": "Hardware name: cps1, cps2, neogeo, sys16b, taitof2, etc."},
                        "dat_type": {"type": "string", "description": "DAT source", "default": "fbneo"},
                        "parents_only": {"type": "boolean", "description": "Only parent games, no clones/hacks", "default": True},
                    },
                    "required": ["hardware"],
                },
            ),
            Tool(
                name="dat_game_variants",
                description="Get a game and ALL its variants, clones, bootlegs, and hacks. Use to understand game relationships.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "game_name": {"type": "string", "description": "ROM name (e.g., sf2ce, dino, mslug, sf2rb)"},
                        "dat_type": {"type": "string", "description": "DAT source", "default": "fbneo"},
                    },
                    "required": ["game_name"],
                },
            ),
            Tool(
                name="dat_search",
                description="Search arcade games by name. Returns hardware info, video specs, and parent/clone status.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "dat_type": {"type": "string", "description": "DAT source", "default": "fbneo"},
                        "hardware": {"type": "string", "description": "Filter by hardware (cps1, neogeo, etc.)"},
                        "parents_only": {"type": "boolean", "description": "Exclude clones/hacks", "default": False},
                        "limit": {"type": "integer", "description": "Max results", "default": 30},
                    },
                    "required": ["query"],
                },
            ),
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle tool calls."""
        try:
            if name == "list_platforms":
                result = await tool_list_platforms()
            elif name == "list_builds":
                result = await tool_list_builds()
            elif name == "get_build_status":
                result = await tool_get_build_status(arguments["build_name"])
            elif name == "get_platform_stats":
                result = await tool_get_platform_stats(arguments["platform"])
            elif name == "query_collection":
                result = await tool_query_collection(
                    arguments["platform"],
                    arguments.get("query"),
                    arguments.get("limit", 20),
                )
            elif name == "calculate_budget":
                result = await tool_calculate_budget(
                    arguments["platform"],
                    arguments["budget_gb"],
                    arguments.get("compression_format", "chd"),
                )
            elif name == "get_compression_ratio":
                result = await tool_get_compression_ratio(
                    arguments["platform"],
                    arguments.get("output_format", "chd"),
                )
            # Wikipedia tools
            elif name == "wiki_search":
                result = await tool_wiki_search(
                    arguments["query"],
                    arguments.get("limit", 10),
                    arguments.get("section_filter"),
                )
            elif name == "wiki_game_info":
                result = await tool_wiki_game_info(arguments["game_title"])
            elif name == "wiki_get_section":
                result = await tool_wiki_get_section(
                    arguments["game_title"],
                    arguments["section_name"],
                )
            elif name == "wiki_stats":
                result = await tool_wiki_stats()
            elif name == "wiki_find_game":
                result = await tool_wiki_find_game(
                    arguments["query"],
                    arguments.get("limit", 10),
                    arguments.get("threshold", 0.5),
                )
            # ScreenScraper tools
            elif name == "scraper_search":
                result = await tool_scraper_search(
                    arguments["query"],
                    arguments.get("platform"),
                    arguments.get("genre"),
                    arguments.get("limit", 20),
                    arguments.get("show_variants", False),
                    arguments.get("title_only", True),
                )
            elif name == "scraper_game_info":
                result = await tool_scraper_game_info(
                    arguments["name"],
                    arguments.get("platform"),
                    arguments.get("show_variants", False),
                )
            elif name == "scraper_platforms":
                result = await tool_scraper_platforms()
            elif name == "scraper_genres":
                result = await tool_scraper_genres(
                    arguments.get("platform"),
                )
            elif name == "scraper_top_rated":
                result = await tool_scraper_top_rated(
                    arguments["platform"],
                    arguments.get("genre"),
                    arguments.get("limit", 20),
                )
            # DAT file tools
            elif name == "dat_hardware_list":
                result = await tool_dat_hardware_list(
                    arguments.get("dat_type", "fbneo"),
                )
            elif name == "dat_hardware_games":
                result = await tool_dat_hardware_games(
                    arguments["hardware"],
                    arguments.get("dat_type", "fbneo"),
                    arguments.get("parents_only", True),
                )
            elif name == "dat_game_variants":
                result = await tool_dat_game_variants(
                    arguments["game_name"],
                    arguments.get("dat_type", "fbneo"),
                )
            elif name == "dat_search":
                result = await tool_dat_search(
                    arguments["query"],
                    arguments.get("dat_type", "fbneo"),
                    arguments.get("hardware"),
                    arguments.get("parents_only", False),
                    arguments.get("limit", 30),
                )
            else:
                result = {"error": f"Unknown tool: {name}"}
            
            import json
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
        except Exception as e:
            logger.exception(f"Error in tool {name}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    @server.list_resources()
    async def list_resources() -> list[Resource]:
        """Return list of available resources."""
        resources = []
        
        # Platform configs
        platforms_dir = WORKSPACE_ROOT / "config" / "platforms"
        if platforms_dir.exists():
            for yaml_file in platforms_dir.glob("*.yaml"):
                resources.append(Resource(
                    uri=f"romfarmer://platforms/{yaml_file.stem}",
                    name=f"Platform: {yaml_file.stem}",
                    description=f"Configuration for {yaml_file.stem} platform",
                    mimeType="application/yaml",
                ))
        
        # Build configs
        builds_dir = WORKSPACE_ROOT / "config" / "builds"
        if builds_dir.exists():
            for yaml_file in builds_dir.glob("*.yaml"):
                resources.append(Resource(
                    uri=f"romfarmer://builds/{yaml_file.stem}",
                    name=f"Build: {yaml_file.stem}",
                    description=f"Build configuration: {yaml_file.stem}",
                    mimeType="application/yaml",
                ))
        
        return resources
    
    @server.read_resource()
    async def read_resource(uri: str) -> str:
        """Read a resource by URI."""
        if uri.startswith("romfarmer://platforms/"):
            platform = uri.replace("romfarmer://platforms/", "")
            return await resource_platform_config(platform)
        elif uri.startswith("romfarmer://builds/"):
            build_name = uri.replace("romfarmer://builds/", "")
            return await resource_build_config(build_name)
        elif uri.startswith("romfarmer://lists/"):
            parts = uri.replace("romfarmer://lists/", "").split("/")
            if len(parts) == 2:
                platform, list_type = parts
                return await resource_platform_list(list_type, platform)
        
        return f"Unknown resource: {uri}"
    
    @server.list_prompts()
    async def list_prompts() -> list[Prompt]:
        """Return available prompts."""
        return [
            Prompt(
                name=p["name"],
                description=p["description"],
                arguments=[
                    PromptArgument(
                        name=a["name"],
                        description=a["description"],
                        required=a.get("required", False),
                    )
                    for a in p["arguments"]
                ],
            )
            for p in PROMPTS.values()
        ]
    
    @server.get_prompt()
    async def get_prompt(name: str, arguments: dict[str, str] | None) -> GetPromptResult:
        """Get a prompt with arguments filled in."""
        if name == "build_collection":
            platform = arguments.get("platform", "saturn") if arguments else "saturn"
            target = arguments.get("target", "batocera") if arguments else "batocera"
            budget = arguments.get("budget", "64GB") if arguments else "64GB"
            
            return GetPromptResult(
                description=f"Build {platform} collection for {target}",
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(
                            type="text",
                            text=f"""I want to build a ROM collection for {platform}.

Target device: {target}
Storage budget: {budget}

Please:
1. Check the current collection status
2. Recommend a build configuration
3. Estimate the output size
4. Start the build when ready""",
                        ),
                    ),
                ],
            )
        
        elif name == "analyze_collection":
            platform = arguments.get("platform", "saturn") if arguments else "saturn"
            
            return GetPromptResult(
                description=f"Analyze {platform} collection",
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(
                            type="text",
                            text=f"""Analyze my {platform} ROM collection.

Please check:
1. How many games do I have?
2. What's the compression ratio?
3. Are there any missing games from the DAT?
4. Any recommendations for improvement?""",
                        ),
                    ),
                ],
            )
        
        return GetPromptResult(
            description="Unknown prompt",
            messages=[],
        )


# =============================================================================
# Server Entry Point
# =============================================================================

async def main():
    """Run the MCP server."""
    if not MCP_AVAILABLE:
        print("MCP library not installed. Run: pip install mcp")
        return
    
    from mcp.server.stdio import stdio_server
    from mcp.server.lowlevel.server import NotificationOptions
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=SERVER_NAME,
                server_version=SERVER_VERSION,
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
