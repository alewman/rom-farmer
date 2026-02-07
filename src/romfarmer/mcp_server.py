"""
ROM Farmer MCP Server — backward-compatible redirect.

The server has been split into ``romfarmer.mcp`` sub-package.
This file remains so ``python -m romfarmer.mcp_server`` keeps working.
"""

import asyncio
from romfarmer.mcp.server import main  # noqa: F401

if __name__ == "__main__":
    asyncio.run(main())
