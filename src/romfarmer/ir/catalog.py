"""Catalog — the typed game-unit layer of the ROM Farmer IR.

After CATALOG phase, no downstream component sees individual disc files.
Multi-disc atomicity is structural: grouping happens once in ``CatalogBuilder``
(Phase 3); the only way to reach a ``DiscRef`` is through its parent
``GameUnit``. See docs/compiler-refactor/04-edge-case-designs.md §1.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import AbstractSet, NewType

from .identity import Identity

PlatformId = NewType("PlatformId", str)
UnitId = NewType("UnitId", str)  # stable: sha1(f"{platform}:{canonical_name}")


@dataclass(frozen=True, slots=True)
class SourceRef:
    """A source file with its platform context."""

    path: Path
    platform: PlatformId


@dataclass(frozen=True, slots=True)
class DiscRef:
    """One disc within a (possibly multi-disc) game.

    Single-disc games are represented as a 1-tuple of ``DiscRef`` — there is
    no "loose file" concept in the IR.
    """

    index: int                          # 1-based disc number
    source: SourceRef
    identity: Identity
    dat_name: str | None = None         # canonical DAT entry for THIS disc


@dataclass(frozen=True, slots=True)
class GameUnit:
    """The atomic unit of selection and scheduling: one game (N discs).

    Invariants (enforced in ``__post_init__``):
    - ``discs`` must contain at least one ``DiscRef``.
    - ``discs`` must be sorted by ``index`` in ascending order.

    Non-contiguous indices are *not* rejected here — that is a
    ``CatalogBuilder`` policy (quarantine + ``CatalogWarning``), not a unit
    invariant.
    """

    unit_id: UnitId
    platform: PlatformId
    canonical_name: str                 # disc-tag-stripped normalised name
    discs: tuple[DiscRef, ...]          # INVARIANT: len >= 1, sorted by index
    region: frozenset[str] = frozenset()
    languages: frozenset[str] = frozenset()
    rating: float | None = None
    tier: int | None = None
    generation: str | None = None

    def __post_init__(self) -> None:
        if not self.discs:
            raise ValueError("GameUnit.discs must not be empty")
        indices = [d.index for d in self.discs]
        if indices != sorted(indices):
            raise ValueError(
                f"GameUnit.discs must be sorted by index; got {indices}"
            )

    @property
    def is_multi_disc(self) -> bool:
        return len(self.discs) > 1

    @property
    def source_size(self) -> int:
        """Total uncompressed size of all discs.

        This is the ONLY size figure the budget pass may consult. Summing all
        discs gives all-or-nothing budget accounting for multi-disc sets.
        """
        return sum(d.identity.size or 0 for d in self.discs)

    @classmethod
    def from_discs(
        cls,
        platform: PlatformId,
        canonical_name: str,
        discs: tuple[DiscRef, ...],
    ) -> "GameUnit":
        """Construct a ``GameUnit``, computing ``unit_id`` and sorting discs.

        ``unit_id = sha1(f"{platform}:{canonical_name}".encode()).hexdigest()``
        """
        unit_id = UnitId(
            hashlib.sha1(f"{platform}:{canonical_name}".encode()).hexdigest()
        )
        sorted_discs = tuple(sorted(discs, key=lambda d: d.index))
        return cls(
            unit_id=unit_id,
            platform=platform,
            canonical_name=canonical_name,
            discs=sorted_discs,
        )


@dataclass(frozen=True, slots=True)
class CatalogWarning:
    """A non-fatal anomaly detected while building the catalog."""

    unit_key: str
    reason: str     # e.g. "non-contiguous disc set: [1, 3]"


@dataclass(frozen=True, slots=True)
class Catalog:
    """Immutable snapshot of the known game universe for one platform (or all).

    ``platform`` is ``None`` for a merged multi-platform catalog produced by
    the generation pass.

    The ENTIRE mutation surface is ``keep`` / ``without`` / ``merge`` — all
    three return NEW ``Catalog`` instances. There is deliberately no API that
    adds, removes, or replaces an individual ``DiscRef``.
    """

    platform: PlatformId | None
    units: tuple[GameUnit, ...]
    warnings: tuple[CatalogWarning, ...] = ()

    def keep(self, ids: AbstractSet[UnitId]) -> "Catalog":
        """Return a new ``Catalog`` containing only units whose id is in ``ids``."""
        return Catalog(
            platform=self.platform,
            units=tuple(u for u in self.units if u.unit_id in ids),
            warnings=self.warnings,
        )

    def without(self, ids: AbstractSet[UnitId]) -> "Catalog":
        """Return a new ``Catalog`` with units in ``ids`` removed."""
        return Catalog(
            platform=self.platform,
            units=tuple(u for u in self.units if u.unit_id not in ids),
            warnings=self.warnings,
        )

    def merge(self, other: "Catalog") -> "Catalog":
        """Combine two catalogs; requires disjoint ``unit_id`` sets.

        Raises:
            ValueError: if any ``unit_id`` appears in both catalogs.
        """
        self_ids = {u.unit_id for u in self.units}
        other_ids = {u.unit_id for u in other.units}
        overlap = self_ids & other_ids
        if overlap:
            raise ValueError(
                f"Catalog.merge requires disjoint unit_ids; "
                f"overlap: {sorted(overlap)[:5]}"
            )
        return Catalog(
            platform=None,  # merged catalog spans platforms
            units=self.units + other.units,
            warnings=self.warnings + other.warnings,
        )


@dataclass(frozen=True, slots=True)
class PassTrace:
    """Audit log for one planner pass — powers ``romfarmer plan --explain``."""

    pass_name: str
    removed: tuple[tuple[UnitId, str], ...]  # (unit_id, human-readable reason)
    added: tuple[tuple[UnitId, str], ...] = ()


@dataclass(frozen=True, slots=True)
class PassResult:
    """Output of one pure planner pass."""

    catalog: Catalog
    trace: PassTrace
