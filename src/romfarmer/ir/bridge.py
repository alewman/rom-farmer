"""TEMPORARY strangler bridge between the legacy StageContext and the immutable IR.

Lifecycle: created in Phase 1, load-bearing in Phases 2–4, DELETED in Phase 5.

Rules:
  * This is the ONLY module permitted to import both romfarmer.ir.* and
    romfarmer.stages.*.
  * This is the ONLY module where defensive attribute access (getattr) is
    permitted — the legacy context has two config eras (briefing §3.5) and
    quarantining that mess here is the point.
  * The IR snapshot is authoritative. Legacy fields are derived views.
  * Every write-back also reconciles work_dir symlinks, because unconverted
    stages still treat the filesystem as state (briefing §3.7).

⚠ FIELD-NAME DISCREPANCY (found 2026-07-03):
  The bridge sketch in docs/compiler-refactor/03-migration-roadmap.md
  references ``ctx.file_hashes.source_md5`` — this field does NOT exist.
  The real domain object is ``ctx.hashes`` (a ``FileHashes`` instance) with
  ``ctx.hashes.source_md5: Dict[Path, str]`` (Path keys, not str keys).
  The bridge is adapted to reality here; the round-trip test encodes the
  discrepancy as assertions.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from romfarmer.ir.catalog import (
    Catalog,
    DiscRef,
    GameUnit,
    PassResult,
    PlatformId,
    SourceRef,
)
from romfarmer.ir.identity import Identity

if TYPE_CHECKING:  # never a runtime import — keeps ir/ decoupled from stages
    from romfarmer.stages.base import StageContext

# ---------------------------------------------------------------------------
# Protocol for pure planner passes (duck-typed; avoids Any)
# ---------------------------------------------------------------------------

class _PurePass(Protocol):
    def run(self, catalog: Catalog) -> PassResult: ...

# ---------------------------------------------------------------------------
# Disc-grouping helpers — mirrors SelectionFilter._group_multi_disc_games
# ---------------------------------------------------------------------------

# Match "(Disc 1)", "(Disc A)", "(Disk 2)", "(Disk B)" etc. (case-insensitive)
_DISC_TAG = re.compile(r"\(Dis[ck]\s+(\w+)\)", re.IGNORECASE)


def _unit_key(path: Path) -> str:
    """Disc-number-stripped grouping key (lower-cased, stripped)."""
    return _DISC_TAG.sub("", path.stem).strip().lower()


def _disc_index(path: Path) -> int:
    """Return the 1-based disc index from a filename, or 1 for single-disc."""
    m = _DISC_TAG.search(path.stem)
    if m is None:
        return 1
    token = m.group(1)
    if token.isdigit():
        return int(token)
    # Letter-based disc tags (Disc A=1, Disc B=2, …)
    return ord(token.upper()) - ord("A") + 1


def _identity_for(ctx: "StageContext", path: Path) -> Identity:
    """Lift whatever identity the legacy context already knows.

    Partial Identity is fine here — the Executor is the only component that
    REQUIRES a complete identity (sha256 populated).

    ⚠ DISCREPANCY NOTE: the bridge sketch used ``ctx.file_hashes.source_md5``
    but the real field is ``ctx.hashes.source_md5: Dict[Path, str]`` with
    Path objects as keys (not strings). Adapted to reality.
    """
    md5: str | None = None
    hashes = getattr(ctx, "hashes", None)           # quarantined defensive access
    if hashes is not None:
        source_md5 = getattr(hashes, "source_md5", None)
        if isinstance(source_md5, dict):
            md5 = source_md5.get(path)              # Path key, not str
    size: int | None = path.stat().st_size if path.exists() else None
    return Identity(size=size, md5=md5)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def catalog_from_context(ctx: "StageContext", platform: str) -> Catalog:
    """Lift the mutable legacy context into an immutable Catalog snapshot.

    Reads the SAME precedence chain the legacy stages use:
    ``filtered_files`` → ``matched_files`` → ``source_files``.
    All three are ``List[Path]`` in the real ``StageContext``.
    """
    raw: list[Path] = (
        getattr(ctx, "filtered_files", None)
        or getattr(ctx, "matched_files", None)
        or getattr(ctx, "source_files", None)
        or []
    )
    files = [Path(p) for p in raw]

    groups: dict[str, list[Path]] = {}
    for f in files:
        groups.setdefault(_unit_key(f), []).append(f)

    units: list[GameUnit] = []
    for key in sorted(groups):
        members = sorted(groups[key], key=_disc_index)
        discs = tuple(
            DiscRef(
                index=_disc_index(p),
                source=SourceRef(path=p, platform=PlatformId(platform)),
                identity=_identity_for(ctx, p),
                dat_name=None,  # enrichment is CatalogBuilder's job (Phase 3)
            )
            for p in members
        )
        units.append(GameUnit.from_discs(PlatformId(platform), key, discs))
    return Catalog(platform=PlatformId(platform), units=tuple(units))


def apply_catalog_to_context(catalog: Catalog, ctx: "StageContext") -> None:
    """Write-back: make the legacy context fields agree with the IR snapshot.

    Performs BOTH halves of the undocumented legacy dual-write contract
    (briefing §3.7) so unconverted downstream stages keep working:
      1. ``filtered_files`` list (legacy context field)
      2. ``work_dir`` symlink population
    """
    selected = [d.source.path for u in catalog.units for d in u.discs]
    ctx.filtered_files = list(selected)

    work_dir = getattr(ctx, "work_dir", None)
    if work_dir is None:
        return
    keep = {p.name for p in selected}
    for link in Path(work_dir).glob("*"):
        if link.is_symlink() and link.name not in keep:
            link.unlink()


def assert_context_fs_sync(ctx: "StageContext") -> None:
    """Loud drift detector — turns the silent §3.7 divergence into a failure.

    Raises:
        RuntimeError: if the work_dir symlinks do not match ``filtered_files``.
    """
    work_dir = getattr(ctx, "work_dir", None)
    if work_dir is None:
        return
    fs = {p.name for p in Path(work_dir).glob("*") if p.is_symlink()}
    mem = {Path(p).name for p in (getattr(ctx, "filtered_files", None) or [])}
    if fs != mem:
        raise RuntimeError(
            "context/filesystem divergence: "
            f"only-in-fs={sorted(fs - mem)[:5]} "
            f"only-in-context={sorted(mem - fs)[:5]}"
        )


class PassAsStage:
    """Run a pure IR pass inside the legacy pipeline.

    The legacy pipeline executor sees a duck-typed Stage (has ``PHASE`` +
    ``execute``); internally we lift → run pure pass → write back → verify.
    This is how converted passes ship one at a time in Phase 3 while
    unconverted stages still surround them.
    """

    PHASE = "PLAN"
    name = "pass-as-stage"

    def __init__(self, pure_pass: _PurePass, platform: str) -> None:
        self._pass: _PurePass = pure_pass
        self._platform = platform
        self.name = f"bridged:{type(pure_pass).__name__}"

    def execute(self, context: "StageContext") -> "StageContext":
        before = catalog_from_context(context, self._platform)
        result = self._pass.run(before)          # PassResult(catalog, trace)
        apply_catalog_to_context(result.catalog, context)
        assert_context_fs_sync(context)
        return context
