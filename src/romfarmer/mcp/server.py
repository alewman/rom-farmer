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
    from romfarmer.mcp.farmhand import (
        tool_farmhand_connect,
        tool_farmhand_scan_target,
        tool_farmhand_analyze_fit,
        tool_farmhand_generate_plan,
        tool_farmhand_remote_exec,
        tool_farmhand_get_target_info,
        tool_farmhand_deploy_status,
    )
    from romfarmer.mcp.farmhand_skills import (
        tool_farmhand_skill_search,
        tool_farmhand_skill_show,
        tool_farmhand_skill_artifact,
        tool_farmhand_skill_save,
        tool_farmhand_skill_save_artifact,
        tool_farmhand_skill_capture_start,
        tool_farmhand_skill_capture_step,
        tool_farmhand_skill_capture_finish,
        tool_farmhand_skill_capture_cancel,
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
        # Farm-Hand deployment
        "farmhand_connect": tool_farmhand_connect,
        "farmhand_scan_target": tool_farmhand_scan_target,
        "farmhand_analyze_fit": tool_farmhand_analyze_fit,
        "farmhand_generate_plan": tool_farmhand_generate_plan,
        "farmhand_remote_exec": tool_farmhand_remote_exec,
        "farmhand_get_target_info": tool_farmhand_get_target_info,
        "farmhand_deploy_status": tool_farmhand_deploy_status,
        # Farm-Hand skills
        "farmhand_skill_search": tool_farmhand_skill_search,
        "farmhand_skill_show": tool_farmhand_skill_show,
        "farmhand_skill_artifact": tool_farmhand_skill_artifact,
        "farmhand_skill_save": tool_farmhand_skill_save,
        "farmhand_skill_save_artifact": tool_farmhand_skill_save_artifact,
        "farmhand_skill_capture_start": tool_farmhand_skill_capture_start,
        "farmhand_skill_capture_step": tool_farmhand_skill_capture_step,
        "farmhand_skill_capture_finish": tool_farmhand_skill_capture_finish,
        "farmhand_skill_capture_cancel": tool_farmhand_skill_capture_cancel,
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
    # ---- Farm-Hand deployment tools --------------------------------------
    {
        "name": "farmhand_connect",
        "description": "Connect to a remote target (Batocera, RockNIX) via SSH and return basic system info. Caches the connection for subsequent calls.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "SSH host (IP address or hostname)"},
                "user": {"type": "string", "description": "SSH username", "default": "root"},
                "password": {"type": "string", "description": "SSH password"},
                "port": {"type": "integer", "description": "SSH port", "default": 22},
            },
            "required": ["host"],
        },
    },
    {
        "name": "farmhand_scan_target",
        "description": "Full scan of a remote target — discovers storage volumes, existing ROMs, installed emulators/binaries, and system info. Saves a target profile for planning.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "SSH host"},
                "user": {"type": "string", "description": "SSH username", "default": "root"},
                "password": {"type": "string", "description": "SSH password"},
                "name": {"type": "string", "description": "Target profile name (e.g., batocera-nuc-livingroom)"},
                "frontend": {"type": "string", "description": "Frontend type", "default": "batocera"},
                "port": {"type": "integer", "description": "SSH port", "default": 22},
                "save": {"type": "boolean", "description": "Save profile to config/farmhand/", "default": True},
            },
            "required": ["host"],
        },
    },
    {
        "name": "farmhand_analyze_fit",
        "description": "Analyze what ROM platforms fit in a given amount of storage. Returns platforms classified as include_all (tiny/small), budget_needed (large), or skip (massive). Provide available_gb directly or target_name to use saved profile.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "available_gb": {"type": "number", "description": "Available storage in GB"},
                "target_name": {"type": "string", "description": "Saved target profile name (alternative to available_gb)"},
            },
        },
    },
    {
        "name": "farmhand_generate_plan",
        "description": "Generate a full deployment plan for a target. Decides which platforms to include in full, which need rating_budget selection, and which to skip. Uses rom-farmer's size_data.json for platform sizes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_name": {"type": "string", "description": "Saved target profile name"},
                "reserved_gb": {"type": "number", "description": "GB to reserve for saves, BIOS, metadata", "default": 30},
                "exclude_platforms": {"type": "string", "description": "Comma-separated platforms to exclude (e.g., 'xbox360,ps2')"},
                "budget_overrides": {"type": "string", "description": "Comma-separated platform=GB pairs (e.g., 'ps2=80,psx=60')"},
            },
            "required": ["target_name"],
        },
    },
    {
        "name": "farmhand_remote_exec",
        "description": "Execute a shell command on a remote target via SSH. Use for ad-hoc inspection: check binaries, configs, file listings, disk usage, etc.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "SSH host"},
                "command": {"type": "string", "description": "Shell command to execute"},
                "user": {"type": "string", "description": "SSH username", "default": "root"},
                "password": {"type": "string", "description": "SSH password"},
                "port": {"type": "integer", "description": "SSH port", "default": 22},
            },
            "required": ["host", "command"],
        },
    },
    {
        "name": "farmhand_get_target_info",
        "description": "Get saved target profile information from the last scan — volumes, capabilities, existing ROMs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_name": {"type": "string", "description": "Target profile name"},
            },
            "required": ["target_name"],
        },
    },
    {
        "name": "farmhand_deploy_status",
        "description": "Get deployment status for a target — what's been planned, allocated, and pending.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_name": {"type": "string", "description": "Target profile name"},
            },
            "required": ["target_name"],
        },
    },
    # ---- Farm-Hand skill tools -------------------------------------------
    {
        "name": "farmhand_skill_search",
        "description": "Search the Farm-Hand skill library. Returns matching skills with summaries. Combine query text with category/tag/platform/target filters (AND-combined).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Text to search in skill names, descriptions, tags", "default": ""},
                "category": {"type": "string", "description": "Filter by category: deployment, build, target, curation, maintenance, scripting, workflow", "default": ""},
                "tag": {"type": "string", "description": "Filter by tag", "default": ""},
                "platform": {"type": "string", "description": "Filter by ROM platform", "default": ""},
                "target": {"type": "string", "description": "Filter by target name", "default": ""},
            },
        },
    },
    {
        "name": "farmhand_skill_show",
        "description": "Get full details of a skill including procedure steps, parameters, artifacts, and SKILL.md body.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Skill name (slug format)"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "farmhand_skill_artifact",
        "description": "Retrieve the contents of an artifact file (script, game list, config) from a skill.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "skill_name": {"type": "string", "description": "Skill name"},
                "filename": {"type": "string", "description": "Artifact filename (e.g. setup-rom-symlinks.sh, essentials/saturn.yaml)"},
            },
            "required": ["skill_name", "filename"],
        },
    },
    {
        "name": "farmhand_skill_save",
        "description": "Create or update a user skill from explicit parameters. Use for directly saving agent knowledge.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Skill name (slug: lowercase, hyphens)"},
                "description": {"type": "string", "description": "What this skill does"},
                "category": {"type": "string", "description": "Category: deployment, build, target, curation, maintenance, scripting, workflow"},
                "body": {"type": "string", "description": "SKILL.md body content (markdown)", "default": ""},
                "tags": {"type": "string", "description": "Comma-separated tags", "default": ""},
                "platforms": {"type": "string", "description": "Comma-separated platforms", "default": ""},
                "targets": {"type": "string", "description": "Comma-separated targets", "default": ""},
                "tools_used": {"type": "string", "description": "Comma-separated tool names", "default": ""},
                "preconditions": {"type": "string", "description": "Comma-separated preconditions", "default": ""},
            },
            "required": ["name", "description", "category"],
        },
    },
    {
        "name": "farmhand_skill_save_artifact",
        "description": "Save an artifact file (script, game list, config) to a user skill.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "skill_name": {"type": "string", "description": "Skill name"},
                "filename": {"type": "string", "description": "Artifact filename"},
                "content": {"type": "string", "description": "File content"},
                "description": {"type": "string", "description": "What this artifact is for", "default": ""},
                "artifact_type": {"type": "string", "description": "Type: script, config, list, data, template", "default": "script"},
                "executable": {"type": "boolean", "description": "Make the file executable", "default": false},
            },
            "required": ["skill_name", "filename", "content"],
        },
    },
    {
        "name": "farmhand_skill_capture_start",
        "description": "Begin recording agent actions for skill auto-capture. Only one recording at a time.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_description": {"type": "string", "description": "What workflow is being recorded"},
            },
            "required": ["task_description"],
        },
    },
    {
        "name": "farmhand_skill_capture_step",
        "description": "Record a step in the active skill capture session.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "Step type: mcp_call, shell, ssh, python, decision"},
                "description": {"type": "string", "description": "What this step does", "default": ""},
                "tool": {"type": "string", "description": "Tool name (for mcp_call)", "default": ""},
                "command": {"type": "string", "description": "Shell command (for shell/ssh)", "default": ""},
                "args": {"type": "string", "description": "JSON-encoded arguments", "default": ""},
                "result": {"type": "string", "description": "Brief result summary", "default": ""},
                "success": {"type": "boolean", "description": "Whether the step succeeded", "default": true},
            },
            "required": ["action"],
        },
    },
    {
        "name": "farmhand_skill_capture_finish",
        "description": "Finish recording and save the captured workflow as a reusable skill.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Skill name (slug: lowercase, hyphens)"},
                "description": {"type": "string", "description": "Override description", "default": ""},
                "category": {"type": "string", "description": "Category", "default": "workflow"},
                "tags": {"type": "string", "description": "Comma-separated tags", "default": ""},
                "platforms": {"type": "string", "description": "Comma-separated platforms", "default": ""},
                "targets": {"type": "string", "description": "Comma-separated targets", "default": ""},
                "save": {"type": "boolean", "description": "Save immediately", "default": true},
            },
            "required": ["name"],
        },
    },
    {
        "name": "farmhand_skill_capture_cancel",
        "description": "Cancel the active skill capture session without saving.",
        "inputSchema": {
            "type": "object",
            "properties": {},
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
    # Farm-Hand deployment
    "farmhand_connect": ([], {"host": "", "user": "root", "password": "", "port": 22, "target": ""}),
    "farmhand_scan_target": ([], {"host": "", "user": "root", "password": "", "name": "", "frontend": "batocera", "port": 22, "save": True, "target": ""}),
    "farmhand_analyze_fit": ([], {"available_gb": 0, "target_name": ""}),
    "farmhand_generate_plan": (["target_name"], {"reserved_gb": 30.0, "exclude_platforms": "", "budget_overrides": ""}),
    "farmhand_remote_exec": (["host", "command"], {"user": "root", "password": "", "port": 22}),
    "farmhand_get_target_info": (["target_name"], {}),
    "farmhand_deploy_status": (["target_name"], {}),
    # Farm-Hand skills
    "farmhand_skill_search": ([], {"query": "", "category": "", "tag": "", "platform": "", "target": ""}),
    "farmhand_skill_show": (["name"], {}),
    "farmhand_skill_artifact": (["skill_name", "filename"], {}),
    "farmhand_skill_save": (["name", "description", "category"], {"body": "", "tags": "", "platforms": "", "targets": "", "tools_used": "", "preconditions": ""}),
    "farmhand_skill_save_artifact": (["skill_name", "filename", "content"], {"description": "", "artifact_type": "script", "executable": False}),
    "farmhand_skill_capture_start": (["task_description"], {}),
    "farmhand_skill_capture_step": (["action"], {"description": "", "tool": "", "command": "", "args": "", "result": "", "success": True}),
    "farmhand_skill_capture_finish": (["name"], {"description": "", "category": "workflow", "tags": "", "platforms": "", "targets": "", "save": True}),
    "farmhand_skill_capture_cancel": ([], {}),
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
