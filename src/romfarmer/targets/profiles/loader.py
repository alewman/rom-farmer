"""TargetProfile loader — reads config/frontends/*.yaml + config/devices/*.yaml.

The YAML schema is **unchanged** from the legacy config — zero user migration.
A ``ConcreteTargetProfile`` combines one frontend definition with one optional
device definition (device adds unsupported-platform gates and media-sizing caps).

Relationships:
    frontend    — emulator front-end (Batocera, RocknIX, RetroArch, …)
    device      — hardware target (r36s, steamdeck, pc, …)

Phase 5 also wires ``format_preferences`` into ``negotiation.py`` — the
``preferred_compression`` field from frontend platform definitions is read here
and stored as a tuple of ``FormatChain`` for the negotiation pass.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from romfarmer.ir.catalog import PlatformId
from romfarmer.ir.layout import LayoutConstraints, MediaPolicy, MetadataDialect
from romfarmer.planner.lowering.base import FormatChain

logger = logging.getLogger(__name__)

# Compression label → FormatChain mapping (mirrors negotiation.py convention)
_COMPRESSION_TO_CHAIN: dict[str, FormatChain] = {
    "chd": ("chd",),
    "rvz": ("rvz",),
    "wux": ("wux",),
    "xiso": ("xiso",),
    "squashfs": ("xiso", "squashfs"),
    "7z": ("7z",),
    "zip": ("zip",),
    "none": ("passthrough",),
    "passthrough": ("passthrough",),
}

# Output extension a chain produces → the chain(s) a frontend listing that
# extension can therefore load.
_EXTENSION_TO_CHAINS: dict[str, tuple[FormatChain, ...]] = {
    ".7z": (("7z",),),
    ".zip": (("zip",), ("passthrough",)),
    ".chd": (("chd",),),
    ".cue": (("cue_bin",),),
    ".bin": (("cue_bin",),),
    ".iso": (("iso",), ("xiso",), ("passthrough",)),
    ".xiso": (("xiso",),),
    ".squashfs": (("xiso", "squashfs"),),
    ".rvz": (("rvz",),),
    ".wux": (("wux",),),
    ".wud": (("wux",),),
    ".wad": (("passthrough",),),
    ".m3u": (),
}


def _chains_from_extensions(extensions: list[str], preferred: str) -> list[FormatChain]:
    """Ordered chains a frontend supports, given its extension list.

    ``preferred`` (the YAML ``preferred_compression``) moves its chain to the
    front.  Extensions with no compressed counterpart (e.g. ``.nes``) imply the
    frontend also accepts the raw file, i.e. ``passthrough``.
    """
    chains: list[FormatChain] = []
    for ext in extensions:
        for chain in _EXTENSION_TO_CHAINS.get(ext, (("passthrough",),)):
            if chain not in chains:
                chains.append(chain)
    pref_chain = _COMPRESSION_TO_CHAIN.get(preferred)
    if pref_chain is not None:
        if pref_chain in chains:
            chains.remove(pref_chain)
        chains.insert(0, pref_chain)
    return chains


@dataclass(frozen=True)
class ConcreteTargetProfile:
    """A fully resolved target profile combining frontend + optional device.

    This class implements the ``TargetProfile`` protocol from
    ``docs/compiler-refactor/02-ir-contracts.md §5``.
    """

    name: str
    description: str = ""
    # folder_mapping: internal platform id → frontend folder name
    folder_mapping: dict[str, str] = field(default_factory=dict)
    # platform_preferences: platform id → ordered list of FormatChains
    platform_preferences: dict[str, list[FormatChain]] = field(default_factory=dict)
    # unsupported_platforms: set of platform ids this target cannot run
    unsupported_platforms: frozenset[str] = frozenset()
    # layout
    layout_constraints: LayoutConstraints = field(default_factory=LayoutConstraints)
    # metadata
    metadata_dialect: MetadataDialect = MetadataDialect.NONE
    metadata_enabled: bool = False
    # media
    media_policy: MediaPolicy = field(default_factory=MediaPolicy)
    # organisation style ("flat" | "balanced" | "minimal" | "rich")
    organisation_style: str = "flat"

    # TargetProfile protocol
    def supports(self, platform: PlatformId) -> bool:
        return str(platform) not in self.unsupported_platforms

    def format_preferences(self, platform: PlatformId) -> list[FormatChain]:
        return self.platform_preferences.get(str(platform), [])

    def folder_name(self, platform: PlatformId) -> str:
        """Return the folder name for *platform* (falls back to platform id)."""
        return self.folder_mapping.get(str(platform), str(platform))


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


class TargetProfileLoader:
    """Loads and caches ``ConcreteTargetProfile`` instances from YAML files.

    Args:
        config_dir: Root directory containing ``frontends/`` and ``devices/``
            subdirectories.  Defaults to ``config/`` relative to the cwd.
    """

    def __init__(self, config_dir: Path | None = None) -> None:
        self._config_dir = config_dir or Path("config")
        self._cache: dict[str, ConcreteTargetProfile] = {}

    def load(self, target_name: str) -> ConcreteTargetProfile:
        """Return the profile for *target_name* (``frontend`` or ``frontend/device``).

        Examples::

            loader.load("batocera")           # frontend only
            loader.load("batocera/r36s")      # frontend + device
            loader.load("rocknix")            # frontend only
        """
        if target_name in self._cache:
            return self._cache[target_name]

        parts = target_name.split("/", 1)
        frontend_name = parts[0]
        device_name = parts[1] if len(parts) > 1 else None

        frontend_raw = self._load_yaml(self._config_dir / "frontends" / f"{frontend_name}.yaml")
        device_raw = (
            self._load_yaml(self._config_dir / "devices" / f"{device_name}.yaml")
            if device_name
            else {}
        )

        profile = _build_profile(frontend_name, frontend_raw, device_raw)
        self._cache[target_name] = profile
        return profile

    def available_frontends(self) -> list[str]:
        """Return names of available frontend configs."""
        d = self._config_dir / "frontends"
        if not d.exists():
            return []
        return [p.stem for p in d.glob("*.yaml")]

    def available_devices(self) -> list[str]:
        """Return names of available device configs."""
        d = self._config_dir / "devices"
        if not d.exists():
            return []
        return [p.stem for p in d.glob("*.yaml")]

    @staticmethod
    def _load_yaml(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            import yaml

            with open(path) as fh:
                raw = yaml.safe_load(fh) or {}
            return raw if isinstance(raw, dict) else {}
        except Exception as exc:
            logger.warning("TargetProfileLoader: could not load %s: %s", path, exc)
            return {}


# ---------------------------------------------------------------------------
# Internal builder
# ---------------------------------------------------------------------------


def _build_profile(
    name: str,
    frontend: dict[str, Any],
    device: dict[str, Any],
) -> ConcreteTargetProfile:
    """Merge frontend + device YAML into a ``ConcreteTargetProfile``."""

    description = frontend.get("description") or device.get("description") or name

    # Folder mapping
    folder_mapping: dict[str, str] = {}
    fm = frontend.get("folder_mapping") or {}
    if isinstance(fm, dict):
        folder_mapping = {str(k): str(v) for k, v in fm.items()}

    # Unsupported platforms (device gates)
    unsupported: set[str] = set()
    dev_unsupported = device.get("unsupported_platforms") or []
    if isinstance(dev_unsupported, list):
        unsupported.update(str(p) for p in dev_unsupported)

    # Per-platform format preferences (from frontend platform definitions).
    # The frontend's `extensions` list is the ground truth for what it can
    # load; `preferred_compression` only orders the list.  A chain whose
    # output extension the frontend lists is supported.
    platform_prefs: dict[str, list[FormatChain]] = {}
    platform_defs = frontend.get("platforms") or {}
    if isinstance(platform_defs, dict):
        for plat, pdef in platform_defs.items():
            if not isinstance(pdef, dict):
                continue
            prefs = _chains_from_extensions(
                [str(e).lower() for e in (pdef.get("extensions") or [])],
                str(pdef.get("preferred_compression") or ""),
            )
            if prefs:
                platform_prefs[str(plat)] = prefs

    # Media sizing (from device)
    media_sizing = device.get("media_sizing") or {}
    max_w = media_sizing.get("max_image_width")
    max_h = media_sizing.get("max_image_height")
    allow_video = "video" in (frontend.get("media_support") or [])
    media_policy = MediaPolicy(
        max_image_width=int(max_w) if max_w else None,
        max_image_height=int(max_h) if max_h else None,
        allow_video=allow_video,
    )

    # Metadata dialect / organisation style live under `defaults:` in the
    # shipped frontend YAMLs; accept a top-level key too.
    defaults = frontend.get("defaults") or {}
    metadata_enabled = bool(frontend.get("metadata", defaults.get("metadata", False)))
    dialect = MetadataDialect.ES_GAMELIST if metadata_enabled else MetadataDialect.NONE

    # Organisation style
    org_style = str(frontend.get("organization_style") or defaults.get("organization") or "flat")

    return ConcreteTargetProfile(
        name=f"{name}",
        description=description,
        folder_mapping=folder_mapping,
        platform_preferences=platform_prefs,
        unsupported_platforms=frozenset(unsupported),
        layout_constraints=LayoutConstraints(),
        metadata_dialect=dialect,
        metadata_enabled=metadata_enabled,
        media_policy=media_policy,
        organisation_style=org_style,
    )
