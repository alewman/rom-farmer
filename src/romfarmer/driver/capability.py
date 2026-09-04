"""Capability is data, not model knowledge (intent brief v1 §5, v4 §1).

An agent asked what an R36S can run will confidently invent an answer.  This
module is what it reads instead: the frontend × device profile, flattened
into a frozen ``Capabilities`` value with a digest the Spec records as
``intent.capability_digest``.

``Capabilities.require(platform)`` raises for a platform the device profile
does not mention — an absent platform is an error, never a guess.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from romfarmer.ir.catalog import PlatformId
from romfarmer.ir.chain import FormatChain
from romfarmer.ir.layout import PlatformCapability
from romfarmer.targets.profiles.loader import ConcreteTargetProfile, TargetProfileLoader


@dataclass(frozen=True)
class Capabilities:
    frontend: str
    device: str | None
    reserve_bytes: int | None
    platforms: MappingProxyType[str, PlatformCapability]  # listed platforms
    default: PlatformCapability | None  # applies to unlisted platforms, if any
    formats: MappingProxyType[str, tuple[FormatChain, ...]]  # frontend-accepted chains
    folder_names: MappingProxyType[str, str]
    source_roots: MappingProxyType[str, tuple[str, ...]] = MappingProxyType({})  # alias → subdirs

    def require(self, platform: str) -> PlatformCapability:
        cap = self.platforms.get(platform)
        if cap is not None:
            return cap
        if self.default is not None:
            return self.default
        raise KeyError(
            f"device {self.device!r} has no capability entry for {platform!r} — add it to "
            f"config/devices/{self.device}.yaml (tier A/B/C/X); the intent layer does not guess"
        )

    def shippable(self) -> tuple[str, ...]:
        """Platforms with a tier other than X that the frontend can also load."""
        out = []
        for plat in sorted(set(self.platforms) | set(self.formats)):
            try:
                cap = self.require(plat)
            except KeyError:
                continue
            if cap.tier != "X" and plat in self.formats:
                out.append(plat)
        return tuple(out)

    def to_dict(self) -> dict[str, Any]:
        return {
            "frontend": self.frontend,
            "device": self.device,
            "reserve_bytes": self.reserve_bytes,
            "default": _cap_dict(self.default) if self.default else None,
            "platforms": {
                k: {
                    **_cap_dict(v),
                    "formats": [list(c) for c in self.formats.get(k, ())],
                    "folder": self.folder_names.get(k, k),
                }
                for k, v in sorted(self.platforms.items())
            },
            "frontend_only": {
                k: [list(c) for c in v]
                for k, v in sorted(self.formats.items())
                if k not in self.platforms
            },
            "source_roots": {k: list(v) for k, v in sorted(self.source_roots.items())},
        }

    def digest(self) -> str:
        """``sha256:<hex>`` of the canonical JSON — recorded as ``intent.capability_digest``."""
        text = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _cap_dict(c: PlatformCapability) -> dict[str, Any]:
    return {
        "tier": c.tier,
        "quality": c.quality,
        "playable_list": c.playable_list,
        "notes": c.notes,
    }


def capabilities_from_profile(
    profile: ConcreteTargetProfile, frontend: str, device: str | None
) -> Capabilities:
    return Capabilities(
        frontend=frontend,
        device=device,
        reserve_bytes=profile.reserve_bytes,
        platforms=MappingProxyType(dict(profile.capabilities)),
        default=profile.capability_default,
        formats=MappingProxyType({k: tuple(v) for k, v in profile.platform_preferences.items()}),
        folder_names=MappingProxyType(
            {k: profile.folder_name(PlatformId(k)) for k in profile.platform_preferences}
        ),
    )


def _source_roots(config_dir: Path) -> MappingProxyType[str, tuple[str, ...]]:
    """``alias → immediate subdirectory names`` from ``config/sources.yaml`` (one readdir per root)."""
    from romfarmer.driver.sources import load_source_roots

    out: dict[str, tuple[str, ...]] = {}
    try:
        roots = load_source_roots(config_dir)
    except Exception:
        return MappingProxyType(out)
    for alias, root in roots.items():
        try:
            out[alias] = tuple(sorted(p.name for p in root.iterdir() if p.is_dir()))
        except OSError:
            out[alias] = ()
    return MappingProxyType(out)


def capabilities(frontend: str, device: str | None, config_dir: Path) -> Capabilities:
    """Read ``config/frontends/<frontend>.yaml`` + ``config/devices/<device>.yaml``.  Loud.

    Also lists the named source roots and their subdirectories so an agent can
    author ``sources: [{root, subpath}]`` without guessing paths.
    """
    key = f"{frontend}/{device}" if device else frontend
    profile = TargetProfileLoader(config_dir).load(key)
    caps = capabilities_from_profile(profile, frontend, device)
    fields = {f: getattr(caps, f) for f in caps.__dataclass_fields__}
    fields["source_roots"] = _source_roots(config_dir)
    return Capabilities(**fields)
