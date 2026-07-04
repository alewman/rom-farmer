"""romfarmer.planner.lowering — platform-specific action-DAG lowering rules.

Each lowering rule translates a ``GameUnit`` + ``FormatChain`` into a typed
``UnitPlan`` (the action DAG for one game).

The lowering layer is the structural replacement for the eight
``_*_stages()`` factory functions in ``stages/builder.py``.  Unlike those
functions, lowering rules are **pure**: they produce data (``Action``
objects), they never invoke tools or touch the filesystem.

Public API:
    FormatChain     — ordered tuple of format-step names, e.g. ``("chd",)``
    LoweringRule    — protocol: ``lower(unit, chain, manifest) -> UnitPlan``
    lower           — dispatch: pick the right rule for a resolved config
"""

from .base import FormatChain, LoweringRule, lower

__all__ = ["FormatChain", "LoweringRule", "lower"]
