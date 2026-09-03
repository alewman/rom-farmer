"""Per-tool implementation versions — the cache-invalidation lever.

``IMPL_VERSIONS`` records the "implementation version" for every tool known
to the lowering layer.  It is the mechanism for invalidating cached
``Action`` rows when a transform's subprocess flags or default parameters
change in a way that produces different output bytes.

Rules:
  1. All entries start at 1.  The ``probe_tool_version`` function and the
     ``static_tool_version`` helper append ``"+i{n}"`` **only when n ≥ 2**,
     so no currently-emitted ``tool_version`` string is affected by the
     addition of this file.
  2. When a transform's command construction, env pins, or ``params.get``
     defaults change in a way that produces different output bytes, bump that
     tool's entry by 1.
  3. A bump is **tool-scoped**: only ``Action`` rows for that specific tool
     miss the cache; all other tools are unaffected.
  4. Never change the frozen canonical form in ``ir/actions.py``.
  5. Add a brief comment next to any entry whose value is ≥ 2 explaining
     what changed and when.

First bumps landed 2026-09-01 (T9 determinism): ``7z`` and ``mksquashfs``.
"""

from __future__ import annotations

from types import MappingProxyType

IMPL_VERSIONS: MappingProxyType[str, int] = MappingProxyType(
    {
        # Built-in / synthetic tools (no external binary)
        "source-copy": 1,
        "passthrough": 1,
        "m3u-create": 1,
        # External tools
        "unzip": 1,
        "7z": 2,  # 2026-09-01: -mtm=off -mmt=4 + pinned env — reproducible output (T9)
        "chdman": 1,
        "mksquashfs": 2,  # 2026-09-01: SOURCE_DATE_EPOCH=0 env + -all-root -no-xattrs -processors 4 (T9)
        "extract-xiso": 1,
        "dolphin-tool": 1,
        "wit": 1,
        "ps3dec": 1,
        "ps3-dkey-lookup": 1,
        "ps3-extract-tree": 1,
    }
)


def impl_version_suffix(tool: str) -> str:
    """Return ``'+i{n}'`` for n ≥ 2, or ``''`` for n == 1 (no suffix today).

    This keeps every currently-emitted ``tool_version`` string byte-identical
    to its pre-T5 value — no existing cache row is invalidated.

    Usage::

        # In probe_tool_version (for tools with external binaries):
        version = "7z 24.05"  # from subprocess
        return version + impl_version_suffix("7z")   # "7z 24.05" (n==1 today)

        # In static_tool_version (for synthetic tools):
        return "1" + impl_version_suffix("m3u-create")  # "1" (n==1 today)
    """
    n = IMPL_VERSIONS.get(tool, 1)
    return f"+i{n}" if n >= 2 else ""
