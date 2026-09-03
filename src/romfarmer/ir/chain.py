"""FormatChain — the negotiated output-format chain for one platform.

An ordered tuple of lowercase format-step names, e.g. ``("chd",)``,
``("xiso", "squashfs")``, ``("7z",)``, ``("passthrough",)``.  It is decided
at RESOLVE (recipe ∩ target-profile preferences), carried on the
``BuildManifest``, and consumed by the lowering rules.

Lives in ``ir`` so that both PLAN (lowering) and EMIT (target profiles) can
name the type without either importing the other.
"""

from __future__ import annotations

FormatChain = tuple[str, ...]

__all__ = ["FormatChain"]
