"""romfarmer.driver — the compiler driver layer.

``driver.resolve`` is the public RESOLVE phase: it turns a
``ResolvedPlatformConfig`` (+ composed target) into a frozen
``ResolvedBuild`` — manifest, format chain, DAT file, target profile, source
and output directories — with no I/O beyond config/DAT discovery.

This package sits above the compiler core (``ir``, ``analysis``, ``planner``,
``engine``, ``targets``) and below the operator shells (``cli``, ``web``,
``mcp``).  It must never import ``ai``, ``mcp`` or ``farmhand.optimizer``
(import-linter contract "hermetic core is model-free").
"""

from romfarmer.targets.profiles.loader import TargetProfileError

from .capability import Capabilities, capabilities
from .resolve import (
    FormatNegotiationError,
    ResolvedBuild,
    ResolvePaths,
    negotiate_format_chain,
    negotiate_with_profile,
    resolve_platform,
)

__all__ = [
    "Capabilities",
    "capabilities",
    "FormatNegotiationError",
    "ResolvedBuild",
    "ResolvePaths",
    "TargetProfileError",
    "negotiate_format_chain",
    "negotiate_with_profile",
    "resolve_platform",
]
