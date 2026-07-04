"""negotiation.py — resolve a ``FormatChain`` from a ``ResolvedPlatformConfig``.

Phase 4 implementation: direct translation of the existing
``(extraction_type, compression_format)`` pair from the resolved config.

Phase 5 will extend this to perform real TargetProfile negotiation
(recipe preferences ∩ profile preferences → first mutual match).

The function is pure: no I/O, no side effects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from romfarmer.planner.lowering.base import FormatChain

if TYPE_CHECKING:
    from romfarmer.config.resolver import ResolvedPlatformConfig
    from romfarmer.targets.profiles.loader import ConcreteTargetProfile


# ---------------------------------------------------------------------------
# ExtractionType / CompressionFormat → FormatChain mapping
# ---------------------------------------------------------------------------

def negotiate_format_chain(resolved: "ResolvedPlatformConfig") -> FormatChain:
    """Return the ``FormatChain`` for *resolved*.

    Maps the existing ``(extraction_type, compression)`` pair to the typed
    chain consumed by the lowering rules.

    Raises:
        ValueError: if the combination is unrecognised.
    """
    # Import lazily to avoid pulling legacy config models into the pure planner
    # at module load time.
    from romfarmer.config.models import CompressionFormat, ExtractionType

    et = resolved.extraction_type
    cf = resolved.compression

    # ── Disc systems ──────────────────────────────────────────────────
    if et == ExtractionType.DISC:
        if cf == CompressionFormat.CHD:
            return ("chd",)
        return ("cue_bin",)  # passthrough — keep CUE/BIN

    # ── Cartridge systems ─────────────────────────────────────────────
    if et == ExtractionType.CARTRIDGE:
        if cf == CompressionFormat.SEVENZ:
            return ("7z",)
        if cf == CompressionFormat.ZIP:
            return ("zip",)
        return ("passthrough",)

    # ── RVZ (GameCube / Wii) ──────────────────────────────────────────
    if et == ExtractionType.RVZ:
        return ("rvz",)

    # ── WUX (Wii U) ───────────────────────────────────────────────────
    if et == ExtractionType.WUX:
        return ("wux",)

    # ── PS3 ───────────────────────────────────────────────────────────
    if et == ExtractionType.PS3:
        return ("ps3",)

    # ── Xbox XISO ─────────────────────────────────────────────────────
    if et == ExtractionType.XISO:
        if cf == CompressionFormat.SQUASHFS:
            return ("xiso", "squashfs")
        return ("xiso",)

    # ── No extraction (3DS, Switch, WAD, etc.) ────────────────────────
    # ExtractionType.NONE → keep the source file as-is
    if et == ExtractionType.NONE:
        return ("passthrough",)

    raise ValueError(
        f"Unrecognised extraction_type={et!r} / compression={cf!r}. "
        "Add a mapping in planner/negotiation.py."
    )


def negotiate_with_profile(
    resolved: "ResolvedPlatformConfig",
    profile: "ConcreteTargetProfile",
) -> FormatChain:
    """Return the best ``FormatChain`` given a target profile's preferences.

    Algorithm (blueprint §2.2 — intersection, not override):
    1. Get the config-based default from ``negotiate_format_chain``.
    2. Ask the profile for its per-platform preferences.
    3. If the config default is among the profile's supported chains, keep
       it (recipe intent wins when mutually supported); otherwise fall back
       to the profile's first preference; with no preferences at all, the
       config default stands.
    """
    from romfarmer.ir.catalog import PlatformId
    default_chain = negotiate_format_chain(resolved)
    platform_prefs = profile.format_preferences(PlatformId(resolved.platform))
    if not platform_prefs:
        return default_chain
    if default_chain in platform_prefs:
        return default_chain
    return platform_prefs[0]
