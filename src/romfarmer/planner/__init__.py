"""romfarmer.planner — PLAN phase: pure passes that filter the Catalog.

Public API:
    CostModel       — enum-keyed compression ratio service (priors + posteriors)
    PassRunner      — ordered pass execution, accumulates PassTrace list
    lowering        — sub-package: platform-specific action-DAG lowering rules
    negotiation     — resolve FormatChain from ResolvedPlatformConfig
"""

from . import lowering, passes
from .costmodel import CostModel
from .negotiation import negotiate_format_chain
from .runner import PassRunner

__all__ = ["CostModel", "PassRunner", "lowering", "passes", "negotiate_format_chain"]
