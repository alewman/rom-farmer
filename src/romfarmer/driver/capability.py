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
    platform_sources: MappingProxyType[str, tuple[dict[str, Any], ...]] = MappingProxyType(
        {}
    )  # platform → [{root, subpath, recursive}]
    spec_template: str = ""  # a complete, valid Spec skeleton for this frontend/device

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
            "platform_sources": {k: list(v) for k, v in sorted(self.platform_sources.items())},
            "spec_template": self.spec_template,
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


def _platform_sources(
    config_dir: Path, platforms: list[str]
) -> dict[str, tuple[dict[str, Any], ...]]:
    """``platform → [{root, subpath, recursive}]`` — the exact fragment a Spec needs.

    Read from each supported platform's config and reverse-mapped through the
    named roots in ``config/sources.yaml``; platforms whose sources are under
    no named root are omitted (the Spec cannot express them).
    """
    from romfarmer.config.new_loader import load_slim_platform
    from romfarmer.driver.sources import alias_path, load_source_roots

    try:
        roots = load_source_roots(config_dir)
    except Exception:
        return {}
    out: dict[str, tuple[dict[str, Any], ...]] = {}
    for plat in platforms:
        try:
            slim = load_slim_platform(plat, config_dir, check_source_paths=False)
        except Exception:
            continue
        frags = []
        for src in slim.sources or []:
            if src.path is None:
                continue
            a = alias_path(Path(src.path), roots, recursive=bool(src.recursive))
            if a is not None:
                frags.append({"root": a.root, "subpath": a.subpath, "recursive": a.recursive})
        if frags:
            out[plat] = tuple(frags)
    return out


def _spec_template(
    frontend: str,
    device: str | None,
    reserve: int | None,
    sources: dict[str, tuple[dict[str, Any], ...]],
    tiers: dict[str, str],
) -> str:
    """A complete Spec skeleton: every supported platform with its exact sources; policy fields commented."""
    lines = [
        "spec_version: 2",
        "intent:",
        '  text: "<the intent, verbatim>"',
        '  authored_by: "agent:<model-id>"',
        '  inventory_digest: ""      # from inventory',
        '  capability_digest: ""     # from capabilities',
        "target:",
        f"  frontend: {frontend}",
        f"  device: {device or 'pc'}",
        "  storage_bytes: 512000000000",
        f"  reserve_bytes: {reserve if reserve is not None else 0}",
        "platforms:",
    ]
    for plat in sorted(sources):
        lines.append(f"  - platform: {plat}    # tier {tiers.get(plat, '?')}")
        lines.append("    sources:")
        for f in sources[plat]:
            sub = f["subpath"].replace('"', '\\"')
            lines.append(
                f'      - {{root: {f["root"]}, subpath: "{sub}", recursive: {str(f["recursive"]).lower()}}}'
            )
        lines.append(
            "    dat: {retool_1g1r: true}   # true when the platform's DAT is a Retool 1G1R export (it is for No-Intro/Redump *_eng sources)"
        )
        lines.append(
            "    # extraction / compression: omit → platform intrinsic + frontend preferred format"
        )
        lines.append("    passes:")
        lines.append("      dat_filter: true")
        lines.append(
            "      # rating: {min: 0.70, unrated: keep}      # unit interval 0–1; unrated REQUIRED with min"
        )
        lines.append("      # budget: {max_bytes: 0, unrated_as: median}")
        lines.append(
            "      # curated_lists: {ref: curated/<name>@sha256:<hex>}   # from write_curated_list"
        )
    return "\n".join(lines) + "\n"


def capabilities(frontend: str, device: str | None, config_dir: Path) -> Capabilities:
    """Read ``config/frontends/<frontend>.yaml`` + ``config/devices/<device>.yaml``.  Loud.

    Also returns ``platform_sources`` (each supported platform's exact
    ``{root, subpath}`` fragments) and a complete ``spec_template`` — the cold
    run showed an agent cannot author a Spec from directory names.
    """
    key = f"{frontend}/{device}" if device else frontend
    profile = TargetProfileLoader(config_dir).load(key)
    caps = capabilities_from_profile(profile, frontend, device)
    fields = {f: getattr(caps, f) for f in caps.__dataclass_fields__}
    supported = list(caps.shippable())
    sources = _platform_sources(config_dir, supported)
    tiers = {p: caps.require(p).tier for p in supported}
    fields["platform_sources"] = MappingProxyType(sources)
    fields["spec_template"] = _spec_template(frontend, device, caps.reserve_bytes, sources, tiers)
    return Capabilities(**fields)
