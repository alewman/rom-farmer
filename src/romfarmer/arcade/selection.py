"""Bridge: platform ``ArcadeFilter`` config + parsed DAT → selected DAT names.

Arcade selection depends on DAT-only facts (``cloneof``, ``sourcefile``,
``romof``, ``comment``, ``driver_status``) that never reach ``GameUnit``.  So
the decision is made once at RESOLVE time and carried on the ``BuildManifest``
(``arcade_selected`` / ``arcade_rejections``); the pure ``arcade`` pass then
applies it.  The plan therefore stays a pure function of (manifest, catalog).
"""

from __future__ import annotations

from typing import Any

from .filter import ArcadeFilter, ArcadeFilterConfig, ArcadeFilterMode

_MODE = {
    "strict": ArcadeFilterMode.STRICT,
    "relaxed": ArcadeFilterMode.RELAXED,
    "complete": ArcadeFilterMode.COMPLETE,
    "permissive": ArcadeFilterMode.COMPLETE,
    "all": ArcadeFilterMode.ALL,
}


def filter_config_from_platform(arcade_filter: Any, dat_ref: Any) -> ArcadeFilterConfig:
    """Map the platform YAML ``arcade_filter`` + ``dat`` sections to a filter config."""
    cfg = ArcadeFilterConfig()
    if arcade_filter is not None:
        cfg.mode = _MODE.get(str(getattr(arcade_filter, "mode", "relaxed")).lower(), cfg.mode)
        for field in (
            "include_working_only",
            "include_bootlegs",
            "include_hacks",
            "include_prototypes",
            "include_homebrew",
            "include_demos",
        ):
            if hasattr(arcade_filter, field):
                setattr(cfg, field, bool(getattr(arcade_filter, field)))
        regions = getattr(arcade_filter, "region_priority", None)
        if regions:
            cfg.preferred_regions = [str(r) for r in regions]
    if dat_ref is not None:
        cfg.filter_driver = getattr(dat_ref, "filter_driver", None)
        cfg.filter_romof = getattr(dat_ref, "filter_romof", None)
        cfg.exclude_romof = getattr(dat_ref, "exclude_romof", None)
    return cfg


def select_arcade_games(
    dat_file: Any, arcade_filter: Any, dat_ref: Any
) -> tuple[frozenset[str], tuple[tuple[str, str], ...]]:
    """Return ``(selected DAT names, ((rejected name, reason), ...))``.

    Games removed by the DAT pre-filters (device entries, other drivers,
    BIOS mismatch) never appear in either set; the ``dat_filter`` pass drops
    them as unmatched.
    """
    cfg = filter_config_from_platform(arcade_filter, dat_ref)
    results = ArcadeFilter(cfg).filter_dat(dat_file)
    selected = frozenset(r.game.name for r in results if r.selected)
    rejected = tuple((r.game.name, r.reason) for r in results if not r.selected)
    return selected, rejected
