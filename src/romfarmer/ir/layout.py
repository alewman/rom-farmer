"""Layout — the emit-phase layer of the ROM Farmer IR.

``LayoutPlan`` replaces the ``organized_files_metadata`` shadow dict
(briefing §3.6) with typed, per-artifact subdirectory placement.
``OutputSet`` is the result of EXECUTE: a mapping from ``UnitId`` to the
resolved ``Identity`` tuples for each unit's terminal artifacts.

Emitters consume ``LayoutPlan`` as their sole input — they never ``rglob``
the output tree (briefing §3.8).
"""

from __future__ import annotations

import enum
import types
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from .catalog import UnitId
from .identity import Identity


class MetadataDialect(enum.Enum):
    NONE = "none"
    ES_GAMELIST = "es_gamelist"


@dataclass(frozen=True, slots=True)
class LayoutConstraints:
    """Filesystem constraints imposed by the target device / frontend."""

    max_files_per_dir: int | None = None
    max_depth: int | None = None
    filename_max_len: int | None = None
    forbidden_chars: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class MediaPolicy:
    """Media asset constraints for the target frontend."""

    max_image_width: int | None = None
    max_image_height: int | None = None
    allow_video: bool = True


@dataclass(frozen=True, slots=True)
class LayoutEntry:
    """One artifact's placement in the output tree."""

    artifact_sha256: str
    relative_path: Path


@dataclass(frozen=True, slots=True)
class LayoutPlan:
    """Complete placement map for one build's output tree.

    This is the only input to emitters — they derive the full output structure
    from ``entries`` without scanning the filesystem.
    """

    root_name: str
    entries: tuple[LayoutEntry, ...]


@dataclass(frozen=True, slots=True)
class OutputSet:
    """Result of EXECUTE: resolved output identities keyed by unit.

    ``unit_outputs`` is stored as an immutable ``MappingProxyType`` regardless
    of what the caller passes (same treatment as ``Action.params``).
    """

    unit_outputs: Mapping[UnitId, tuple[Identity, ...]]

    def __post_init__(self) -> None:
        if not isinstance(self.unit_outputs, types.MappingProxyType):
            object.__setattr__(
                self,
                "unit_outputs",
                types.MappingProxyType(dict(self.unit_outputs)),
            )
