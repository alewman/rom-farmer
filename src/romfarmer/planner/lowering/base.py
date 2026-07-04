"""Base types and dispatcher for the lowering layer.

``FormatChain`` and ``LoweringRule`` are the two load-bearing contracts;
everything else in this package is concrete implementations.

The ``lower()`` dispatcher is the single entry point used by the
orchestrator — it chooses the right rule based on the chain.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path
from typing import Any, Protocol

from romfarmer.ir.actions import (
    Action,
    ActionId,
    ArtifactDecl,
    BuildPlan,
    ContentRef,
    InputRef,
    PendingRef,
    Retention,
    SizePrediction,
    UnitPlan,
)
from romfarmer.ir.catalog import GameUnit
from romfarmer.ir.manifest import BuildManifest

# ``FormatChain`` is an ordered tuple of lowercase format-step names.
# Examples:
#   ("chd",)              — disc → chdman
#   ("xiso",)             — xbox iso → extract-xiso
#   ("xiso", "squashfs")  — xbox iso → extract-xiso → mksquashfs
#   ("rvz",)              — gamecube/wii → dolphin unzip
#   ("zip",)              — cartridge → passthrough zip
#   ("passthrough",)      — copy as-is
FormatChain = tuple[str, ...]


class LoweringRule(Protocol):
    """Protocol for a platform-specific lowering rule.

    Implementations are in the sibling modules
    (disc.py, cartridge.py, etc.).
    """

    def lower(
        self,
        unit: GameUnit,
        chain: FormatChain,
        manifest: BuildManifest,
    ) -> UnitPlan:
        """Translate *unit* into a ``UnitPlan`` for the given *chain*."""
        ...


# ---------------------------------------------------------------------------
# Action-ID helper
# ---------------------------------------------------------------------------

def make_action_id(unit_id: str, step_idx: int, tool: str) -> ActionId:
    """Stable ActionId = sha1(f"{unit_id}:{step_idx}:{tool}")."""
    raw = f"{unit_id}:{step_idx}:{tool}"
    return ActionId(hashlib.sha1(raw.encode()).hexdigest())


# ---------------------------------------------------------------------------
# Source-copy action helper
# ---------------------------------------------------------------------------

def source_action(
    unit: GameUnit,
    step_idx: int,
    source_path: Path,
    logical_name: str,
    kind: str = "source",
    tool_version: str = "1",
) -> Action:
    """Return an Action that copies *source_path* into the CAS.

    The executor's ``SourceCopyTransform`` handles this tool.  It is the
    bridge between the filesystem source files and the CAS-aware executor.
    """
    return Action(
        action_id=make_action_id(str(unit.unit_id), step_idx, "source-copy"),
        tool="source-copy",
        tool_version=tool_version,
        params={"path": str(source_path)},
        inputs=(),   # source file is NOT from CAS — it's a filesystem path
        outputs=(
            ArtifactDecl(
                logical_name=logical_name,
                kind=kind,
                retention=Retention.INTERMEDIATE,
            ),
        ),
    )


def source_ref(
    unit: GameUnit,
    action_cache: Any | None,
) -> tuple[ContentRef | None, str | None]:
    """Return ``(ContentRef, sha256)`` if the unit's first disc sha256 is known.

    Returns ``(None, None)`` when sha256 is not yet in the CAS.
    """
    disc0 = unit.discs[0]
    if disc0.identity.sha256 is not None:
        return ContentRef(disc0.identity.sha256), disc0.identity.sha256
    # Try MD5 alias lookup
    if action_cache is not None and disc0.identity.md5 is not None:
        try:
            ident = action_cache.lookup_by_md5(disc0.identity.md5)
            if ident is not None and ident.sha256 is not None:
                return ContentRef(ident.sha256), ident.sha256
        except Exception:
            pass
    return None, None


# ---------------------------------------------------------------------------
# Tool version probing
# ---------------------------------------------------------------------------

_VERSION_CACHE: dict[str, str] = {}


def probe_tool_version(tool: str, *args: str) -> str:
    """Run ``tool --version`` and return the first line, cached.

    Falls back to ``"unknown"`` if the tool is not found or fails.
    """
    cache_key = tool
    if cache_key in _VERSION_CACHE:
        return _VERSION_CACHE[cache_key]
    try:
        result = subprocess.run(
            [tool, "--version", *args],
            capture_output=True, text=True, timeout=5,
        )
        line = (result.stdout or result.stderr or "").split("\n")[0].strip()
        version = re.sub(r"[^\w.\-+]", "", line)[:40] or "unknown"
    except Exception:
        version = "unknown"
    _VERSION_CACHE[cache_key] = version
    return version


# ---------------------------------------------------------------------------
# Size-prediction helper
# ---------------------------------------------------------------------------

def zero_prediction() -> SizePrediction:
    return SizePrediction(ratio=1.0, source="prior:passthrough", confidence=0.5)


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def lower(
    unit: GameUnit,
    chain: FormatChain,
    manifest: BuildManifest,
    action_cache: Any | None = None,
) -> UnitPlan:
    """Dispatch to the right lowering rule based on *chain[0]*.

    ``action_cache`` is optional; when provided it is used to resolve sha256
    from MD5 aliases so that ``ContentRef`` can be used instead of a
    source-copy action.
    """
    from . import (
        arcade,
        cartridge,
        disc,
        passthrough,
        ps3,
        rvz,
        wux,
        xiso,
    )

    if not chain:
        raise ValueError(f"Empty FormatChain for unit {unit.canonical_name!r}")

    primary = chain[0].lower()
    rule_map: dict[str, LoweringRule] = {
        "chd": disc.DiscLoweringRule(action_cache=action_cache),
        "cue_bin": disc.DiscLoweringRule(action_cache=action_cache, no_chd=True),
        "iso": disc.DiscLoweringRule(action_cache=action_cache, no_chd=True),
        "rvz": rvz.RVZLoweringRule(action_cache=action_cache),
        "wux": wux.WUXLoweringRule(action_cache=action_cache),
        "xiso": xiso.XisoLoweringRule(action_cache=action_cache),
        "squashfs": xiso.XisoLoweringRule(action_cache=action_cache),
        "ps3": ps3.PS3LoweringRule(action_cache=action_cache),
        "ps3_dec": ps3.PS3LoweringRule(action_cache=action_cache),
        "arcade": arcade.ArcadeLoweringRule(action_cache=action_cache),
        "zip": cartridge.CartridgeLoweringRule(action_cache=action_cache),
        "7z": cartridge.CartridgeLoweringRule(action_cache=action_cache, fmt="7z"),
        "passthrough": passthrough.PassthroughLoweringRule(action_cache=action_cache),
    }

    rule = rule_map.get(primary)
    if rule is None:
        raise ValueError(
            f"No lowering rule for chain primary={primary!r}. "
            f"Register one in planner/lowering/base.py:lower()."
        )
    return rule.lower(unit, chain, manifest)
