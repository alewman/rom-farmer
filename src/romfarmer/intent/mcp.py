"""``python -m romfarmer.intent.mcp`` — the intent agent's MCP server.

A SEPARATE entry point from ``romfarmer.mcp_server`` (41 tools, including
``farmhand_remote_exec``).  This one exposes exactly the five read-only
intent tools.  The one-way door is enforced by the tool surface not
existing: no execute, no config write, no shell.  ``TOOL_SCHEMAS`` is
importable without the ``mcp`` package so the equality test always runs.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from romfarmer.intent.tools import INTENT_TOOL_NAMES, IntentTools

SERVER_NAME = "romfarmer-intent"
SERVER_VERSION = "0.1.0"
logger = logging.getLogger(__name__)

_SPEC_ARG = {
    "spec_yaml": {"type": "string", "description": "Spec YAML text (see romfarmer.ir.spec)"}
}

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "inventory",
        "description": "INVENTORY: catalog every platform in the spec (once per session; NAS-bound). "
        "Returns per-platform units/files/bytes/dat_matched/rated and inventory_digest.",
        "inputSchema": {"type": "object", "properties": _SPEC_ARG, "required": ["spec_yaml"]},
    },
    {
        "name": "capabilities",
        "description": "What a frontend × device can run: capability tier A/B/C/X, quality, accepted "
        "formats, folder names, reserve_bytes, capability_digest. Data — never guess.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "frontend": {"type": "string", "description": "config/frontends/<name>.yaml"},
                "device": {"type": "string", "description": "config/devices/<name>.yaml"},
            },
            "required": ["frontend"],
        },
    },
    {
        "name": "validate_spec",
        "description": "Validate a Spec (loud rules) and RESOLVE every platform: chain, DAT, 1g1r lever, "
        "rating/budget as the compiler will see them. No source scan. Pass previous_spec_yaml + "
        "previous_headroom_p90 (or _p50) when revising: loosening while over budget is rejected.",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_SPEC_ARG,
                "previous_spec_yaml": {"type": "string"},
                "previous_headroom_p50": {"type": "integer"},
                "previous_headroom_p90": {
                    "type": "integer",
                    "description": "preferred: the binding headroom",
                },
            },
            "required": ["spec_yaml"],
        },
    },
    {
        "name": "dry_run",
        "description": "PLAN over cached catalogs → PlanSummary (units in/out, bytes p50/p90, rated_fraction, "
        "rating_quantiles, removed_by_pass, top_dropped, headroom). Moves zero bytes.",
        "inputSchema": {"type": "object", "properties": _SPEC_ARG, "required": ["spec_yaml"]},
    },
    {
        "name": "write_curated_list",
        "description": "Freeze a curated list into artifacts/curated/<name>/<sha256>.yaml and return the "
        "curated/<name>@sha256:<hex> ref to put in the spec.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "entries": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "canonical_name": {"type": "string"},
                            "action": {"type": "string", "enum": ["include", "exclude"]},
                            "reason": {"type": "string"},
                        },
                        "required": ["canonical_name"],
                    },
                },
                "generated_by": {"type": "string"},
                "basis": {"type": "object"},
            },
            "required": ["name", "entries", "generated_by"],
        },
    },
]

assert {t["name"] for t in TOOL_SCHEMAS} == INTENT_TOOL_NAMES


def build_server(tools: IntentTools) -> Any:
    """Construct the MCP ``Server`` (requires the ``mcp`` package)."""
    from mcp.server import Server
    from mcp.types import TextContent, Tool

    server = Server(SERVER_NAME)

    @server.list_tools()  # type: ignore[untyped-decorator]
    async def list_tools() -> list[Tool]:
        return [Tool(**schema) for schema in TOOL_SCHEMAS]

    @server.call_tool()  # type: ignore[untyped-decorator]
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        result = tools.call(name, arguments or {})
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

    return server


async def main() -> None:
    from mcp.server.lowlevel.server import NotificationOptions
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server

    from romfarmer.core.paths import get_paths

    tools = IntentTools(get_paths().workspace_root)
    server = build_server(tools)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=SERVER_NAME,
                server_version=SERVER_VERSION,
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(), experimental_capabilities={}
                ),
            ),
        )


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
