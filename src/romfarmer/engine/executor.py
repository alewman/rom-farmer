"""Executor — drives the BuildPlan DAG through the ActionCache and CAS.

The Executor is the only component that:
  * requires ``Identity.is_complete`` (sha256 non-null) for CAS operations
  * writes ``artifact_aliases`` (via :class:`ActionCache.record_aliases`)
  * emits telemetry records (``ROMTransformation`` rows, if a recorder is set)

The execution model is:
  1. For each :class:`UnitPlan`, process :class:`Action`\\s in order.
  2. For each :class:`Action`:
     a. Attempt to resolve the :class:`ActionKey` via :func:`resolve_key`.
     b. If resolved → check :class:`ActionCache`. Hit → use cached outputs.
     c. Miss (or key not yet resolvable) → materialise inputs from CAS →
        run the :class:`Transform` → ingest outputs into CAS → record
        aliases → store in :class:`ActionCache`.
  3. Accumulate ``known_outputs`` across actions so later actions can
     resolve their :class:`PendingRef` inputs.

This is intentionally **not** threaded — a future parallel executor can
be built on top of the same interfaces.
"""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
import shutil
from collections.abc import Callable, Mapping
from pathlib import Path

from romfarmer.ir.actions import (
    Action,
    ActionId,
    ArtifactDecl,
    BuildPlan,
    ContentRef,
    PendingRef,
    Retention,
    UnitPlan,
    resolve_key,
)
from romfarmer.ir.catalog import UnitId
from romfarmer.ir.identity import Identity
from romfarmer.ir.layout import OutputSet

from .actioncache import ActionCache
from .scratch import ScratchDir
from .transforms.base import Transform

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CAS helpers  (thin wrappers so the Executor doesn't depend on ContentStore)
# ---------------------------------------------------------------------------


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1_048_576), b""):
            h.update(chunk)
    return h.hexdigest()


def _cas_path(cas_dir: Path, sha256: str, ext: str = "") -> Path:
    """Return the CAS blob path for *sha256* (2-char prefix sharding)."""
    prefix = sha256[:2]
    rest = sha256[2:]
    return cas_dir / prefix / (rest + ext)


def _ingest_to_cas(file: Path, cas_dir: Path) -> str:
    """Move (or copy) *file* into CAS; return its sha256.  Idempotent.

    Prefers ``os.rename`` so the source bytes are not read twice (zero extra
    I/O for same-filesystem scratch→CAS paths).  Falls back to
    ``shutil.copy2`` when the rename crosses a filesystem boundary.

    The tmp name includes PID + random token so concurrent ingests of the same
    content cannot collide on the intermediate file.
    """
    sha256 = _sha256_file(file)
    dest = _cas_path(cas_dir, sha256, file.suffix)
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(f"{dest.suffix}.tmp.{os.getpid()}.{secrets.token_hex(4)}")
        try:
            os.rename(file, tmp)
        except OSError:
            # Cross-device move; fall back to copy
            shutil.copy2(file, tmp)
        # os.replace is atomic and handles the race: if another process already
        # wrote the same content-addressed blob, we overwrite it with identical
        # bytes — safe because CAS is content-addressed.
        os.replace(tmp, dest)
    return sha256


def _blob_exists(sha256: str, cas_dir: Path) -> bool:
    """Return True if a CAS blob for *sha256* exists on disk."""
    parent = cas_dir / sha256[:2]
    if not parent.is_dir():
        return False
    return any(parent.glob(f"{sha256[2:]}*"))


def _materialise_from_cas(sha256: str, cas_dir: Path, dest: Path) -> None:
    """Hardlink (or copy) a CAS blob to *dest*."""
    blobs = list(cas_dir.glob(f"{sha256[:2]}/{sha256[2:]}*"))
    if not blobs:
        raise FileNotFoundError(f"CAS blob not found for sha256={sha256[:16]}… in {cas_dir}")
    src = blobs[0]
    dest.parent.mkdir(parents=True, exist_ok=True)
    import os

    try:
        os.link(src, dest)
    except OSError:
        shutil.copy2(src, dest)


# ---------------------------------------------------------------------------
# Executor
# ---------------------------------------------------------------------------


class Executor:
    """Runs a :class:`BuildPlan` through the :class:`ActionCache` and CAS.

    Args:
        action_cache:  The unified action + alias cache.
        transforms:    Registry mapping ``tool`` name → :class:`Transform`.
        cas_dir:       Root of the content-addressable store.
        scratch_base:  Parent for per-unit scratch dirs.
        telemetry_cb:  Optional callback ``(action, outputs) → None`` called
                       after each successful execution (for stats / DB writes).
        budget_bytes:  Optional stop-early threshold.  When cumulative actual
                       terminal bytes reaches this limit, remaining units are
                       skipped and returned as ``budget_stop`` names.  ``None``
                       means unlimited.
    """

    def __init__(
        self,
        action_cache: ActionCache,
        transforms: Mapping[str, Transform],
        cas_dir: Path,
        scratch_base: Path | None = None,
        telemetry_cb: Callable[[Action, tuple[Identity, ...]], None] | None = None,
        budget_bytes: int | None = None,
    ) -> None:
        self._cache = action_cache
        self._transforms = transforms
        self._cas = cas_dir
        self._scratch_base = scratch_base or (cas_dir.parent / "scratch")
        self._telemetry = telemetry_cb
        self._budget_bytes = budget_bytes

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def _sweep_stale_scratch(self) -> None:
        """Remove any leftover scratch dirs from previously killed runs."""
        if not self._scratch_base.exists():
            return
        for entry in self._scratch_base.iterdir():
            if entry.name.startswith("scratch_") and entry.is_dir():
                try:
                    shutil.rmtree(entry)
                    logger.debug("swept stale scratch dir: %s", entry.name)
                except OSError as exc:
                    logger.warning("could not sweep stale scratch %s: %s", entry, exc)

    def run(self, plan: BuildPlan) -> OutputSet:
        """Execute *plan* and return the set of terminal output identities.

        When ``budget_bytes`` is set, units are expected to be in
        rating-descending order (as produced by the budget pass).  Once
        cumulative actual terminal bytes reach the budget, remaining units
        are skipped and their ``unit_id`` is recorded in
        ``OutputSet.budget_stopped``.
        """
        self._sweep_stale_scratch()
        all_outputs: dict[UnitId, tuple[Identity, ...]] = {}
        budget_stopped: list[str] = []
        cumulative_bytes = 0

        for unit_plan in plan.units:
            if self._budget_bytes is not None and cumulative_bytes >= self._budget_bytes:
                budget_stopped.append(str(unit_plan.unit.unit_id))
                logger.info(
                    "budget stop-early: skipping %s (cumulative %d bytes ≥ budget %d)",
                    unit_plan.unit.canonical_name,
                    cumulative_bytes,
                    self._budget_bytes,
                )
                continue

            terminal = self._run_unit(unit_plan)
            if terminal:
                all_outputs[unit_plan.unit.unit_id] = tuple(terminal)
                cumulative_bytes += sum(ident.size or 0 for ident in terminal)

        import types

        return OutputSet(
            unit_outputs=types.MappingProxyType(all_outputs),
            budget_stopped=tuple(budget_stopped),
        )

    # ------------------------------------------------------------------
    # Per-unit execution
    # ------------------------------------------------------------------

    def _run_unit(self, unit_plan: UnitPlan) -> list[Identity]:
        """Execute all actions for one game unit; return terminal identities."""
        known_outputs: dict[ActionId, tuple[Identity, ...]] = {}
        terminal_identities: list[Identity] = []
        # Declared output names, so inputs can be materialised under the
        # filenames tools expect (7z member names, chdman extension sniffing).
        declared = {a.action_id: a.outputs for a in unit_plan.actions}

        with ScratchDir(self._scratch_base, str(unit_plan.unit.unit_id)) as scratch:
            for action in unit_plan.actions:
                outputs = self._run_action(action, known_outputs, scratch, declared)
                known_outputs[action.action_id] = outputs

                # Collect terminal outputs
                for decl, ident in zip(action.outputs, outputs, strict=False):
                    if decl.retention == Retention.TERMINAL:
                        terminal_identities.append(ident)

        return terminal_identities

    # ------------------------------------------------------------------
    # Per-action execution
    # ------------------------------------------------------------------

    def _run_action(
        self,
        action: Action,
        known_outputs: dict[ActionId, tuple[Identity, ...]],
        scratch: Path,
        declared: Mapping[ActionId, tuple[ArtifactDecl, ...]] | None = None,
    ) -> tuple[Identity, ...]:
        """Execute one action (cache-first); return resolved output identities."""

        # Attempt early cache lookup
        key = resolve_key(action, known_outputs)
        if key is not None:
            cached = self._cache.get(key)
            if cached is not None:
                # Verify every blob still exists — a deleted or GC'd blob would
                # otherwise produce a materialise failure on the next step.
                # On any missing blob, treat the row as a miss and re-execute.
                missing = [
                    ident.sha256
                    for ident in cached
                    if ident.sha256 is not None and not _blob_exists(ident.sha256, self._cas)
                ]
                if not missing:
                    logger.debug("cache hit: %s (%s)", action.tool, key[:16])
                    return cached
                logger.warning(
                    "cache hit for %s (%s) but %d blob(s) missing — re-executing",
                    action.tool,
                    key[:16],
                    len(missing),
                )

        # Materialise inputs into the scratch dir
        input_paths = self._materialise_inputs(
            action, known_outputs, scratch / action.action_id, declared or {}
        )

        # Run the transform
        transform = self._transforms.get(action.tool)
        if transform is None:
            raise ValueError(f"No transform registered for tool '{action.tool}'")

        logger.debug("executing: %s %s", action.tool, action.action_id)
        output_paths = transform.run(input_paths, action.params, scratch)

        # Ingest outputs into CAS and build Identity tuples.
        # Capture size BEFORE ingest: _ingest_to_cas may rename the file out of
        # scratch, making the path unavailable for stat() afterwards.
        identities: list[Identity] = []
        for out_path in output_paths:
            file_size = out_path.stat().st_size
            sha256 = _ingest_to_cas(out_path, self._cas)
            ident = Identity(
                sha256=sha256,
                size=file_size,
            )
            self._cache.record_aliases(ident)
            identities.append(ident)

        result = tuple(identities)

        # Store in action cache (resolves key now that outputs are known)
        resolved_known = dict(known_outputs)
        for aid, outs in zip([action.action_id], [result], strict=False):
            resolved_known[aid] = outs
        final_key = resolve_key(action, resolved_known)
        if final_key is not None:
            self._cache.store(final_key, result, action.tool, action.tool_version)

        # Emit telemetry
        if self._telemetry is not None:
            self._telemetry(action, result)

        return result

    # ------------------------------------------------------------------
    # Input materialisation
    # ------------------------------------------------------------------

    def _materialise_inputs(
        self,
        action: Action,
        known_outputs: dict[ActionId, tuple[Identity, ...]],
        dest_dir: Path,
        declared: Mapping[ActionId, tuple[ArtifactDecl, ...]],
    ) -> list[Path]:
        """Copy / hardlink all action inputs into *dest_dir*.

        Inputs produced by an earlier action are named after that action's
        declared ``logical_name``; anything else falls back to ``input_NNN``.
        """
        dest_dir.mkdir(parents=True, exist_ok=True)
        paths: list[Path] = []
        used: set[str] = set()

        for idx, inp in enumerate(action.inputs):
            sha256: str
            name = f"input_{idx:03d}"
            if isinstance(inp, ContentRef):
                sha256 = inp.sha256
            else:  # PendingRef — must be resolved by now
                assert isinstance(inp, PendingRef)
                outputs = known_outputs.get(inp.producer)
                if outputs is None or inp.output_index >= len(outputs):
                    raise RuntimeError(
                        f"Cannot materialise PendingRef {inp} — producer outputs not yet known"
                    )
                raw_sha = outputs[inp.output_index].sha256
                if raw_sha is None:
                    raise RuntimeError(
                        f"PendingRef {inp} output identity is incomplete (no sha256)"
                    )
                sha256 = raw_sha
                decls = declared.get(inp.producer, ())
                if inp.output_index < len(decls):
                    name = Path(decls[inp.output_index].logical_name).name
            if name in used:
                name = f"{idx:03d}_{name}"
            used.add(name)
            dest = dest_dir / name
            _materialise_from_cas(sha256, self._cas, dest)
            paths.append(dest)

        return paths
