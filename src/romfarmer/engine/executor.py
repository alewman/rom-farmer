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
import shutil
from collections.abc import Callable, Mapping
from pathlib import Path

from romfarmer.ir.actions import (
    Action,
    ActionId,
    ActionKey,
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
    """Copy *file* into CAS; return its sha256.  Idempotent if already present."""
    sha256 = _sha256_file(file)
    dest = _cas_path(cas_dir, sha256, file.suffix)
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".tmp")
        shutil.copy2(file, tmp)
        tmp.rename(dest)
    return sha256


def _materialise_from_cas(sha256: str, cas_dir: Path, dest: Path) -> None:
    """Hardlink (or copy) a CAS blob to *dest*."""
    blobs = list(cas_dir.glob(f"{sha256[:2]}/{sha256[2:]}*"))
    if not blobs:
        raise FileNotFoundError(
            f"CAS blob not found for sha256={sha256[:16]}… in {cas_dir}"
        )
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
    """

    def __init__(
        self,
        action_cache: ActionCache,
        transforms: Mapping[str, Transform],
        cas_dir: Path,
        scratch_base: Path | None = None,
        telemetry_cb: Callable[[Action, tuple[Identity, ...]], None] | None = None,
    ) -> None:
        self._cache = action_cache
        self._transforms = transforms
        self._cas = cas_dir
        self._scratch_base = scratch_base or (cas_dir.parent / "scratch")
        self._telemetry = telemetry_cb

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self, plan: BuildPlan) -> OutputSet:
        """Execute *plan* and return the set of terminal output identities."""
        all_outputs: dict[UnitId, tuple[Identity, ...]] = {}

        for unit_plan in plan.units:
            terminal = self._run_unit(unit_plan)
            if terminal:
                import types
                all_outputs[unit_plan.unit.unit_id] = tuple(terminal)

        return OutputSet(unit_outputs=types.MappingProxyType(all_outputs))

    # ------------------------------------------------------------------
    # Per-unit execution
    # ------------------------------------------------------------------

    def _run_unit(self, unit_plan: UnitPlan) -> list[Identity]:
        """Execute all actions for one game unit; return terminal identities."""
        known_outputs: dict[ActionId, tuple[Identity, ...]] = {}
        terminal_identities: list[Identity] = []

        with ScratchDir(self._scratch_base, str(unit_plan.unit.unit_id)) as scratch:
            for action in unit_plan.actions:
                outputs = self._run_action(action, known_outputs, scratch)
                known_outputs[action.action_id] = outputs

                # Collect terminal outputs
                for decl, ident in zip(action.outputs, outputs):
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
    ) -> tuple[Identity, ...]:
        """Execute one action (cache-first); return resolved output identities."""

        # Attempt early cache lookup
        key = resolve_key(action, known_outputs)
        if key is not None:
            cached = self._cache.get(key)
            if cached is not None:
                logger.debug(
                    "cache hit: %s (%s)", action.tool, key[:16]
                )
                return cached

        # Materialise inputs into the scratch dir
        input_paths = self._materialise_inputs(
            action, known_outputs, scratch / action.action_id
        )

        # Run the transform
        transform = self._transforms.get(action.tool)
        if transform is None:
            raise ValueError(
                f"No transform registered for tool '{action.tool}'"
            )

        logger.debug("executing: %s %s", action.tool, action.action_id)
        output_paths = transform.run(input_paths, action.params, scratch)

        # Ingest outputs into CAS and build Identity tuples
        identities: list[Identity] = []
        for out_path in output_paths:
            sha256 = _ingest_to_cas(out_path, self._cas)
            ident = Identity(
                sha256=sha256,
                size=out_path.stat().st_size,
            )
            self._cache.record_aliases(ident)
            identities.append(ident)

        result = tuple(identities)

        # Store in action cache (resolves key now that outputs are known)
        resolved_known = dict(known_outputs)
        for aid, outs in zip(
            [action.action_id], [result]
        ):
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
    ) -> list[Path]:
        """Copy / hardlink all action inputs into *dest_dir*."""
        dest_dir.mkdir(parents=True, exist_ok=True)
        paths: list[Path] = []

        for idx, inp in enumerate(action.inputs):
            sha256: str
            if isinstance(inp, ContentRef):
                sha256 = inp.sha256
            else:  # PendingRef — must be resolved by now
                assert isinstance(inp, PendingRef)
                outputs = known_outputs.get(inp.producer)
                if outputs is None or inp.output_index >= len(outputs):
                    raise RuntimeError(
                        f"Cannot materialise PendingRef {inp} — "
                        f"producer outputs not yet known"
                    )
                raw_sha = outputs[inp.output_index].sha256
                if raw_sha is None:
                    raise RuntimeError(
                        f"PendingRef {inp} output identity is incomplete (no sha256)"
                    )
                sha256 = raw_sha
            dest = dest_dir / f"input_{idx:03d}"
            _materialise_from_cas(sha256, self._cas, dest)
            paths.append(dest)

        return paths
