"""
ROM Farmer MCP Server — modular entry point.

Registers tools, resources, and prompts by importing domain modules
and using a registry-based dispatcher instead of a long if/elif chain.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Callable, Awaitable

# MCP imports
try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.types import (
        Tool,
        TextContent,
        Resource,
        Prompt,
        PromptArgument,
        GetPromptResult,
        PromptMessage,
    )

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("MCP not installed. Run: pip install mcp")

from romfarmer.core.paths import get_paths

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SERVER_NAME = "romfarmer"
SERVER_VERSION = "0.2.0"
WORKSPACE_ROOT = get_paths().workspace_root
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool registry  (name -> handler)
# ---------------------------------------------------------------------------

ToolHandler = Callable[..., Awaitable[dict[str, Any]]]
_TOOL_HANDLERS: dict[str, ToolHandler] = {}


def _register_tools() -> None:
    """Import domain modules and populate the handler registry."""
    from romfarmer.mcp.collection import (
        tool_list_platforms,
        tool_list_builds,
        tool_get_build_status,
        tool_get_platform_stats,
        tool_query_collection,
        tool_calculate_budget,
        tool_get_compression_ratio,
    )
    from romfarmer.mcp.wiki import (
        tool_wiki_search,
        tool_wiki_game_info,
        tool_wiki_get_section,
        tool_wiki_stats,
        tool_wiki_find_game,
    )
    from romfarmer.mcp.scraper import (
        tool_scraper_search,
        tool_scraper_game_info,
        tool_scraper_platforms,
        tool_scraper_genres,
        tool_scraper_top_rated,
    )
    from romfarmer.mcp.dat import (
        tool_dat_hardware_list,
        tool_dat_hardware_games,
        tool_dat_game_variants,
        tool_dat_search,
    )

    _TOOL_HANDLERS.update({
        # Collection / build / budget
        "list_platforms": tool_list_platforms,
        "list_builds": tool_list_builds,
        "get_build_status": tool_get_build_status,
        "get_platform_stats": tool_get_platform_stats,
        "query_collection": tool_query_collection,
        "calculate_budget": tool_calculate_budget,
        "get_compression_ratio": tool_get_compression_ratio,
        # Wikipedia
        "wiki_search": tool_wiki_search,
        "wiki_game_info": tool_wiki_game_info,
        "wiki_get_section": tool_wiki_get_section,
        "wiki_stats": tool_wiki_stats,
        "wiki_find_game": tool_wiki_find_game,
        # ScreenScraper
        "scraper_search": tool_scraper_search,
        "scraper_game_info": tool_scraper_game_info,
        "scraper_platforms": tool_scraper_platforms,
        "scraper_genres": tool_scraper_genres,
        "scraper_top_rated": tool_scraper_top_rated,
        # DAT files
        "dat_hardware_list": tool_dat_hardware_list,
        "dat_hardware_games": tool_dat_hardware_games,
        "dat_game_variants": tool_dat_game_variants,
        "dat_search": tool_dat_search,
    })


# ---------------------------------------------------------------------------
# Tool schemas  (kept here for a single source of truth)
# ---------------------------------------------------------------------------

TOOL_SCHEMAS: list[dict[str, Any]] = [
    # ---- Collection tools ------------------------------------------------
    {
        "name": "list_platforms",
        "description": "List all configured ROM platforms",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_builds",
        "description": "List all available build configurations",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_build_status",
        "description": "Get the status of a build",
        "inputSchema": {
            "type": "object",
            "properties": {
                "build_name": {"type": "string", "description": "Name of the build"},
            },
            "required": ["build_name"],
        },
    },
    {
        "name": "get_platform_stats",
        "description": "Get statistics for a platform's ROM collection",
        "inputSchema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "description": "Platform name (saturn, psx, etc.)"},
            },
            "required": ["platform"],
        },
    },
    {
        "name": "query_collection",
        "description": "Search for ROMs in a platform's collection",
        "inputSchema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "description": "Platform name"},
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results", "default": 20},
            },
            "required": ["platform"],
        },
    },
    {
        "name": "calculate_budget",
        "description": "Calculate how many ROMs fit in a storage budget",
        "inputSchema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "description": "Platform name"},
                "budget_gb": {"type": "number", "description": "Storage budget in GB"},
                "compression_format": {"type": "string", "description": "Compression format", "default": "chd"},
            },
            "required": ["platform", "budget_gb"],
        },
    },
    {
        "name": "get_compression_ratio",
        "description": "Get compression ratio for a platform/format combination",
        "inputSchema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "description": "Platform name"},
                "output_format": {"type": "string", "description": "Output format", "default": "chd"},
            },
            "required": ["platform"],
        },
    },
    # ---- Wikipedia tools -------------------------------------------------
    {
        "name": "wiki_search",
        "description": "Semantic search over Wikipedia game articles. Use this to find games by description, gameplay style, themes, etc.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural language search query (e.g., 'horror game with zombies', 'turn-based JRPG')"},
                "limit": {"type": "integer", "description": "Max results to return", "default": 10},
                "section_filter": {"type": "string", "description": "Filter to specific section type (Gameplay, Plot, Reception, etc.)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "wiki_game_info",
        "description": "Get full Wikipedia information about a specific game including all sections",
        "inputSchema": {
            "type": "object",
            "properties": {
                "game_title": {"type": "string", "description": "Game title to look up"},
            },
            "required": ["game_title"],
        },
    },
    {
        "name": "wiki_get_section",
        "description": "Get a specific section from a game's Wikipedia article (e.g., Gameplay, Plot, Reception)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "game_title": {"type": "string", "description": "Game title"},
                "section_name": {"type": "string", "description": "Section name (Gameplay, Plot, Reception, Development, etc.)"},
            },
            "required": ["game_title", "section_name"],
        },
    },
    {
        "name": "wiki_stats",
        "description": "Get statistics about the Wikipedia game database",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "wiki_find_game",
        "description": "Fuzzy search for game titles by name. Use this when you need to find the exact title of a game. Returns candidates ranked by similarity.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Game title to search for (handles typos, partial names, variations)"},
                "limit": {"type": "integer", "description": "Max results to return", "default": 10},
                "threshold": {"type": "number", "description": "Minimum similarity score 0-1 (default 0.5)", "default": 0.5},
            },
            "required": ["query"],
        },
    },
    # ---- ScreenScraper tools ---------------------------------------------
    {
        "name": "scraper_search",
        "description": "Search ScreenScraper database for games with rich metadata (developer, publisher, genre, rating, description). Has 120K+ games across 49 platforms. By default, deduplicates regional variants (showing US > World > EU > JP preference).",
        "inputSchema": {
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
    },
    {
        "name": "scraper_game_info",
        "description": "Get detailed ScreenScraper info for a specific game including description, developer, publisher, genre, rating, release date. Can also show all regional variants.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Game name to look up"},
                "platform": {"type": "string", "description": "Platform to search in (optional, helps with disambiguation)"},
                "show_variants": {"type": "boolean", "description": "If true, include all regional variants of this game", "default": False},
            },
            "required": ["name"],
        },
    },
    {
        "name": "scraper_platforms",
        "description": "List all platforms in ScreenScraper database with game counts",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "scraper_genres",
        "description": "List all genres with game counts, optionally filtered by platform",
        "inputSchema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "description": "Filter genres by platform"},
            },
        },
    },
    {
        "name": "scraper_top_rated",
        "description": "Get top-rated games for a platform, optionally filtered by genre",
        "inputSchema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "description": "Platform name (required)"},
                "genre": {"type": "string", "description": "Filter by genre"},
                "limit": {"type": "integer", "description": "Max results", "default": 20},
            },
            "required": ["platform"],
        },
    },
    # ---- DAT tools -------------------------------------------------------
    {
        "name": "dat_hardware_list",
        "description": "List all arcade hardware platforms with game counts (CPS1, Neo Geo, etc.)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dat_type": {"type": "string", "description": "DAT source (fbneo or mame)", "default": "fbneo"},
            },
        },
    },
    {
        "name": "dat_hardware_games",
        "description": "Get all games for a specific arcade hardware/driver (e.g., all CPS1 games, all Neo Geo games)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "hardware": {"type": "string", "description": "Hardware name: cps1, cps2, neogeo, sys16b, taitof2, etc."},
                "dat_type": {"type": "string", "description": "DAT source", "default": "fbneo"},
                "parents_only": {"type": "boolean", "description": "Only parent games, no clones/hacks", "default": True},
            },
            "required": ["hardware"],
        },
    },
    {
        "name": "dat_game_variants",
        "description": "Get a game and ALL its variants, clones, bootlegs, and hacks. Use to understand game relationships.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "game_name": {"type": "string", "description": "ROM name (e.g., sf2ce, dino, mslug, sf2rb)"},
                "dat_type": {"type": "string", "description": "DAT source", "default": "fbneo"},
            },
            "required": ["game_name"],
        },
    },
    {
        "name": "dat_search",
        "description": "Search arcade games by name. Returns hardware info, video specs, and parent/clone status.",
        "inputSchema": {
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
    },
]

# ---------------------------------------------------------------------------
# Argument-dispatch map
#
# Maps tool name -> (list of positional arg names, dict of optional arg defaults)
# so the generic dispatcher can unpack arguments without knowing each tool.
# ---------------------------------------------------------------------------

_ARG_MAP: dict[str, tuple[list[str], dict[str, Any]]] = {
    # Collection
    "list_platforms": ([], {}),
    "list_builds": ([], {}),
    "get_build_status": (["build_name"], {}),
    "get_platform_stats": (["platform"], {}),
    "query_collection": (["platform"], {"query": None, "limit": 20}),
    "calculate_budget": (["platform", "budget_gb"], {"compression_format": "chd"}),
    "get_compression_ratio": (["platform"], {"output_format": "chd"}),
    # Wiki
    "wiki_search": (["query"], {"limit": 10, "section_filter": None}),
    "wiki_game_info": (["game_title"], {}),
    "wiki_get_section": (["game_title", "section_name"], {}),
    "wiki_stats": ([], {}),
    "wiki_find_game": (["query"], {"limit": 10, "threshold": 0.5}),
    # Scraper
    "scraper_search": (["query"], {"platform": None, "genre": None, "limit": 20, "show_variants": False, "title_only": True}),
    "scraper_game_info": (["name"], {"platform": None, "show_variants": False}),
    "scraper_platforms": ([], {}),
    "scraper_genres": ([], {"platform": None}),
    "scraper_top_rated": (["platform"], {"genre": None, "limit": 20}),
    # DAT
    "dat_hardware_list": ([], {"dat_type": "fbneo"}),
    "dat_hardware_games": (["hardware"], {"dat_type": "fbneo", "parents_only": True}),
    "dat_game_variants": (["game_name"], {"dat_type": "fbneo"}),
    "dat_search": (["query"], {"dat_type": "fbneo", "hardware": None, "parents_only": False, "limit": 30}),
}


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

PROMPTS: dict[str, dict[str, Any]] = {
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


# ---------------------------------------------------------------------------
# MCP Server Registration
# ---------------------------------------------------------------------------

if MCP_AVAILABLE:
    server = Server(SERVER_NAME)

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """Return list of available tools."""
        return [Tool(**schema) for schema in TOOL_SCHEMAS]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Generic dispatcher — looks up handler and unpacks args via _ARG_MAP."""
        if not _TOOL_HANDLERS:
            _register_tools()

        handler = _TOOL_HANDLERS.get(name)
        if handler is None:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

        try:
            arg_spec = _ARG_MAP.get(name, ([], {}))
            positional_keys, optional_defaults = arg_spec

            args = [arguments[k] for k in positional_keys]
            kwargs = {k: arguments.get(k, v) for k, v in optional_defaults.items()}

            result = await handler(*args, **kwargs)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            logger.exception(f"Error in tool {name}")
            return [TextContent(type="text", text=f"Error: {e!s}")]

    # -- Resources ---------------------------------------------------------

    @server.list_resources()
    async def list_resources() -> list[Resource]:
        """Return list of available resources."""
        resources = []

        platforms_dir = WORKSPACE_ROOT / "config" / "platforms"
        if platforms_dir.exists():
            for yaml_file in platforms_dir.glob("*.yaml"):
                resources.append(Resource(
                    uri=f"romfarmer://platforms/{yaml_file.stem}",
                    name=f"Platform: {yaml_file.stem}",
                    description=f"Configuration for {yaml_file.stem} platform",
                    mimeType="application/yaml",
                ))

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

    # -- Prompts -----------------------------------------------------------

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

        return GetPromptResult(description="Unknown prompt", messages=[])


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
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
