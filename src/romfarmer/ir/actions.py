"""Actions — the action graph layer of the ROM Farmer IR.

``Action`` is the unit of caching: one tool invocation with typed
inputs/outputs. ``BuildPlan`` is the full DAG. ``resolve_key`` computes the
``ActionKey`` (the global cache key) once all input identities are known.

The canonical form used by ``resolve_key`` is FROZEN FOREVER — changing it
invalidates the action cache for every user. See the golden test.
"""

from __future__ import annotations

import enum
import hashlib
import json
import types
from collections.abc import Mapping
from dataclasses import dataclass
from typing import NewType

from .catalog import GameUnit, UnitId
from .identity import Identity

ActionId = NewType("ActionId", str)
# GLOBAL cache key: sha256(canonical JSON of tool, tool_version, params, resolved inputs)
ActionKey = NewType("ActionKey", str)


@dataclass(frozen=True, slots=True)
class ContentRef:
    """An input whose content identity (sha256) is known at plan time."""

    sha256: str


@dataclass(frozen=True, slots=True)
class PendingRef:
    """An input whose sha256 is only known once its producer has run (or hit cache)."""

    producer: ActionId
    output_index: int


InputRef = ContentRef | PendingRef


class Retention(enum.Enum):
    INTERMEDIATE = "intermediate"   # GC-eligible once all consumers are done
    TERMINAL = "terminal"           # pinned while any LayoutEntry references it


@dataclass(frozen=True, slots=True)
class ArtifactDecl:
    """Declaration of one output artifact from an ``Action``."""

    logical_name: str   # e.g. "Halo (USA).iso"
    kind: str           # "xiso" | "chd" | "m3u" | "squashfs" | "tree" | ...
    retention: Retention


@dataclass(frozen=True, slots=True)
class Action:
    """One tool invocation in the build plan.

    ``params`` is stored as an immutable ``MappingProxyType`` regardless of
    what the caller passes. The ``__post_init__`` wraps any plain ``dict`` or
    other ``Mapping`` automatically. Caller code may pass a plain ``dict`` for
    convenience; it will be frozen on construction.
    """

    action_id: ActionId
    tool: str           # "unzip" | "extract-xiso" | "mksquashfs" | "chdman" | ...
    tool_version: str   # version bump → cache miss, by design
    params: Mapping[str, str]
    inputs: tuple[InputRef, ...]
    outputs: tuple[ArtifactDecl, ...]

    def __post_init__(self) -> None:
        # Freeze params into an immutable MappingProxyType.
        # object.__setattr__ is required because the dataclass is frozen=True.
        if not isinstance(self.params, types.MappingProxyType):
            object.__setattr__(
                self,
                "params",
                types.MappingProxyType(dict(self.params)),
            )


@dataclass(frozen=True, slots=True)
class SizePrediction:
    """Cost-model output for one ``GameUnit``."""

    ratio: float
    source: str         # "telemetry:psx/chd,n=212" | "prior:size_data.json"
    confidence: float   # 0..1; scales the per-unit safety margin


@dataclass(frozen=True, slots=True)
class UnitPlan:
    """The scheduled work for one ``GameUnit``."""

    unit: GameUnit
    actions: tuple[Action, ...]
    predicted_output_bytes: int
    prediction: SizePrediction


@dataclass(frozen=True, slots=True)
class BuildPlan:
    """The complete action DAG for one build."""

    units: tuple[UnitPlan, ...]


# ---------------------------------------------------------------------------
# ActionKey resolution
# ---------------------------------------------------------------------------

def resolve_key(
    action: Action,
    known_outputs: Mapping[ActionId, tuple[Identity, ...]],
) -> ActionKey | None:
    """Compute the global cache key for ``action`` given resolved output identities.

    Returns ``None`` while any ``PendingRef`` input's producer either:
    - is not yet present in ``known_outputs``, or
    - has a ``None`` sha256 for the referenced output index.

    ``known_outputs`` is populated from BOTH cache rows and just-executed
    actions — the executor drives this.

    ──────────────────────────────────────────────────────────────────────
    CANONICAL FORM — FROZEN FOREVER
    ──────────────────────────────────────────────────────────────────────
    ActionKey = sha256_hex(UTF-8(canonical_json)) where canonical_json is:

        {"inputs":[<sha256>,...], "params":{<sorted>}, "tool":..., "tool_version":...}

    - Top-level keys are sorted alphabetically (sort_keys=True).
    - Inputs are the resolved sha256 strings in declared order.
    - params keys are sorted before serialization.
    - No whitespace (separators=(",", ":")).

    This is Nix-style content addressing: ActionKey hashes the *content
    identity* of inputs, not upstream ActionKeys. Early cutoff: if an
    upstream action re-runs but produces byte-identical output, every
    downstream key is unchanged and still hits the cache.

    Changing any aspect of this form is a cache-invalidation event for
    every user — never a casual update.
    ──────────────────────────────────────────────────────────────────────
    """
    resolved_inputs: list[str] = []
    for inp in action.inputs:
        if isinstance(inp, ContentRef):
            resolved_inputs.append(inp.sha256)
        else:  # PendingRef
            outputs = known_outputs.get(inp.producer)
            if outputs is None:
                return None
            if inp.output_index >= len(outputs):
                return None
            sha256 = outputs[inp.output_index].sha256
            if sha256 is None:
                return None
            resolved_inputs.append(sha256)

    canonical = json.dumps(
        {
            "inputs": resolved_inputs,
            "params": dict(sorted(action.params.items())),
            "tool": action.tool,
            "tool_version": action.tool_version,
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return ActionKey(hashlib.sha256(canonical.encode("utf-8")).hexdigest())
