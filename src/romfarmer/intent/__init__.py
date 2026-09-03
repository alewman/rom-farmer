"""romfarmer.intent — the stochastic layer ABOVE the SPEC seam.

Everything here may involve an agent; nothing below the seam (``ir``,
``planner``, ``engine``, ``targets``, ``driver``) may import it (import-linter
"hermetic core is model-free").  The MCP surface in ``intent.mcp`` exposes
exactly five read-only tools — no execute, no config write, no shell — and
that list is asserted by ``tests/intent/test_mcp_surface.py``.
"""

from .tools import INTENT_TOOL_NAMES, IntentTools

__all__ = ["INTENT_TOOL_NAMES", "IntentTools"]
