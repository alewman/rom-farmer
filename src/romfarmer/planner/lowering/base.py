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
    ContentRef,
    Retention,
    SizePrediction,
    UnitPlan,
)
from romfarmer.ir.catalog import GameUnit
from romfarmer.ir.chain import FormatChain as FormatChain  # re-exported for lowering rules
from romfarmer.ir.manifest import BuildManifest
from romfarmer.ir.tool_impl import impl_version_suffix

# ``FormatChain`` is defined in ``romfarmer.ir.chain``; re-exported here for
# the lowering rules.  Examples:
#   ("chd",)              — disc → chdman
#   ("xiso", "squashfs")  — xbox iso → extract-xiso → mksquashfs
#   ("7z",)               — cartridge → unzip → 7z
#   ("passthrough",)      — copy as-is


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
    tool_version: str | None = None,
) -> Action:
    """Return an Action that copies *source_path* into the CAS.

    The executor's ``SourceCopyTransform`` handles this tool.  It is the
    bridge between the filesystem source files and the CAS-aware executor.
    """
    return Action(
        action_id=make_action_id(str(unit.unit_id), step_idx, "source-copy"),
        tool="source-copy",
        tool_version=tool_version
        if tool_version is not None
        else static_tool_version("source-copy"),
        params={"path": str(source_path)},
        inputs=(),  # source file is NOT from CAS — it's a filesystem path
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

# Not every tool understands --version; these print a banner on stdout/stderr.
_VERSION_ARGS: dict[str, tuple[str, ...]] = {
    "7z": ("i",),
    "7zz": ("i",),
    "7za": ("i",),
    "chdman": (),
    "extract-xiso": ("-h",),
    "mksquashfs": ("-version",),
}
_VERSION_TOKEN = re.compile(r"\d+(?:\.\d+)+")


def probe_tool_version(tool: str, *args: str) -> str:
    """Return a stable version string for *tool*, cached per process.

    Runs the tool's banner command (``--version`` unless overridden in
    ``_VERSION_ARGS``) and keeps the first dotted version token found in the
    first non-empty output line (falling back to the sanitised line itself).
    The impl-version suffix from ``IMPL_VERSIONS`` is appended when the entry
    is ≥ 2.  Falls back to ``"unknown"`` if the tool is not found or fails.
    """
    cache_key = tool
    if cache_key in _VERSION_CACHE:
        return _VERSION_CACHE[cache_key]
    banner_args = args or _VERSION_ARGS.get(Path(tool).name, ("--version",))
    try:
        result = subprocess.run(
            [tool, *banner_args],
            capture_output=True,
            text=True,
            timeout=5,
        )
        lines = [ln.strip() for ln in (result.stdout + "\n" + result.stderr).splitlines()]
        line = next((ln for ln in lines if ln), "")
        token = _VERSION_TOKEN.search(line)
        version = token.group(0) if token else re.sub(r"[^\w.\-+]", "", line)[:40]
        version = version or "unknown"
    except Exception:
        version = "unknown"
    version = version + impl_version_suffix(Path(tool).name)
    _VERSION_CACHE[cache_key] = version
    return version


def static_tool_version(tool: str) -> str:
    """Return the ``tool_version`` string for a synthetic (no-subprocess) tool.

    Synthetic tools (source-copy, passthrough, m3u-create) have no external
    binary to probe, so their base version is always ``"1"``.  The impl-version
    suffix is appended using the same ``IMPL_VERSIONS`` registry so bumping
    IMPL_VERSIONS["m3u-create"] to 2 automatically changes the emitted
    ``tool_version`` from ``"1"`` to ``"1+i2"`` and invalidates cache rows.
    """
    return "1" + impl_version_suffix(tool)


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
