# 02 — IR Data Contracts (Frozen Specification)

**Status:** Frozen 2026-07-03. Names, field names, and semantics are fixed.
Implementers supply method bodies, docstrings, `__post_init__` validation, and
serialization. If reality contradicts this spec, stop and escalate — do not
improvise.

These contracts live in `src/romfarmer/ir/` (created in Migration Phase 1) plus
the target/engine protocols introduced in later phases. Global invariants are at
the bottom of this document.

---

## 1. `ir/identity.py`

```python
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class ZipIdentity:
    member_crc32: int          # CRC32 of the dominant member (largest file / the .cue)
    member_size: int           # uncompressed size of that member
    member_name: str

@dataclass(frozen=True, slots=True)
class Identity:
    size: int | None = None
    sha256: str | None = None            # primary CAS key — REQUIRED by executor, optional elsewhere
    md5: str | None = None               # DAT-matching alias
    zip_identity: ZipIdentity | None = None  # pre-extraction alias

    @property
    def is_complete(self) -> bool:
        return self.sha256 is not None

    def merged(self, other: "Identity") -> "Identity":
        """Union of knowledge; raises IdentityConflict(ValueError) if any
        populated field disagrees."""
        ...

    def best_key(self) -> tuple[str, str]:
        """Strongest available (kind, value): sha256 > md5 > zip_identity
        (serialize zip identity as "crc32:size:name"). Raises ValueError if
        all fields are None."""
        ...
```

**Semantics.** `Identity` may be *partial* everywhere except inside the
Executor, which is the only component that requires `is_complete` and the
**only writer** of alias records to the database. Cache lookups may use any
alias. This single-writer rule is the structural fix for briefing §3.9.

---

## 2. `ir/catalog.py`

```python
from dataclasses import dataclass
from pathlib import Path
from typing import AbstractSet, NewType

PlatformId = NewType("PlatformId", str)
UnitId = NewType("UnitId", str)          # stable: sha1(f"{platform}:{canonical_name}")

@dataclass(frozen=True, slots=True)
class SourceRef:
    path: Path
    platform: PlatformId

@dataclass(frozen=True, slots=True)
class DiscRef:
    index: int                           # 1-based disc number; single-disc games have index=1
    source: SourceRef
    identity: Identity
    dat_name: str | None = None          # canonical DAT entry for THIS disc

@dataclass(frozen=True, slots=True)
class GameUnit:
    unit_id: UnitId
    platform: PlatformId
    canonical_name: str                  # disc-tag-stripped normalizer output
    discs: tuple[DiscRef, ...]           # INVARIANT: len >= 1, sorted by index. A single-disc
                                         # game is a 1-tuple — there is no "loose file" concept.
    region: frozenset[str] = frozenset()
    languages: frozenset[str] = frozenset()
    rating: float | None = None
    tier: int | None = None
    generation: str | None = None

    # __post_init__: raise ValueError if discs is empty or not sorted by index.
    # Do NOT reject non-contiguous indices — that is a CatalogBuilder policy
    # (quarantine + CatalogWarning), not a unit invariant.

    @property
    def is_multi_disc(self) -> bool:
        return len(self.discs) > 1

    @property
    def source_size(self) -> int:
        """The ONLY size the budget pass may consult. Sums all discs —
        all-or-nothing accounting falls out for free."""
        return sum(d.identity.size or 0 for d in self.discs)

    @classmethod
    def from_discs(cls, platform: PlatformId, canonical_name: str,
                   discs: tuple[DiscRef, ...]) -> "GameUnit":
        """Computes unit_id = sha1(f"{platform}:{canonical_name}"), sorts discs
        by index."""
        ...

@dataclass(frozen=True, slots=True)
class CatalogWarning:
    unit_key: str
    reason: str        # e.g. "non-contiguous disc set: [1, 3]" or "mixed-region disc set"

@dataclass(frozen=True, slots=True)
class Catalog:
    platform: PlatformId | None          # None = whole-build multi-platform catalog (generation pass)
    units: tuple[GameUnit, ...]
    warnings: tuple[CatalogWarning, ...] = ()

    # The ENTIRE mutation surface. Note: unit granularity only.
    # There is no API that adds, removes, or replaces an individual DiscRef.
    def keep(self, ids: AbstractSet[UnitId]) -> "Catalog": ...
    def without(self, ids: AbstractSet[UnitId]) -> "Catalog": ...
    def merge(self, other: "Catalog") -> "Catalog": ...   # requires disjoint unit_ids, else ValueError

@dataclass(frozen=True, slots=True)
class PassTrace:
    pass_name: str
    removed: tuple[tuple[UnitId, str], ...]   # (unit, human-readable reason) — powers `plan --explain`
    added: tuple[tuple[UnitId, str], ...] = ()

@dataclass(frozen=True, slots=True)
class PassResult:
    catalog: Catalog
    trace: PassTrace
```

**Multi-disc atomicity is structural, not behavioral.** Grouping happens exactly
once — in `CatalogBuilder`. After CATALOG, no pass can see a disc as an
independent thing, because the pass API operates at unit granularity and
`DiscRef` is only reachable through its parent. See
[04-edge-case-designs.md](04-edge-case-designs.md) §1.

---

## 3. `ir/actions.py`

```python
import enum
from collections.abc import Mapping
from dataclasses import dataclass
from typing import NewType

ActionId = NewType("ActionId", str)    # stable WITHIN a plan: sha1(f"{unit_id}:{step_idx}:{tool}")
ActionKey = NewType("ActionKey", str)  # GLOBAL cache key: sha256(tool, tool_version,
                                       #   canonical(params), resolved input identities)

@dataclass(frozen=True, slots=True)
class ContentRef:
    sha256: str                        # input identity known at plan time

@dataclass(frozen=True, slots=True)
class PendingRef:
    producer: ActionId                 # input identity known only once the producer's
    output_index: int                  # outputs are known (from cache row or execution)

InputRef = ContentRef | PendingRef

class Retention(enum.Enum):
    INTERMEDIATE = "intermediate"      # GC-eligible (e.g., the raw Redump ISO)
    TERMINAL = "terminal"              # target-visible; pinned while any layout references it

@dataclass(frozen=True, slots=True)
class ArtifactDecl:
    logical_name: str                  # "Halo (USA).iso"
    kind: str                          # "xiso" | "chd" | "m3u" | "squashfs" | "tree" | ...
    retention: Retention

@dataclass(frozen=True, slots=True)
class Action:
    action_id: ActionId
    tool: str                          # "unzip" | "extract-xiso" | "mksquashfs" | "chdman" | "ps3dec" | "fetch-psn"
    tool_version: str                  # captured at plan time — version bump = cache miss, by design
    params: Mapping[str, str]          # canonicalized (sorted keys) before hashing;
                                       # stored as an immutable mapping (sorted tuple of pairs
                                       # or MappingProxyType — document the choice)
    inputs: tuple[InputRef, ...]
    outputs: tuple[ArtifactDecl, ...]

@dataclass(frozen=True, slots=True)
class SizePrediction:
    ratio: float
    source: str                        # "telemetry:psx/chd,n=212" | "prior:size_data.json" — auditable
    confidence: float                  # 0..1, scales the per-unit safety margin

@dataclass(frozen=True, slots=True)
class UnitPlan:
    unit: GameUnit
    actions: tuple[Action, ...]
    predicted_output_bytes: int
    prediction: SizePrediction

@dataclass(frozen=True, slots=True)
class BuildPlan:
    units: tuple[UnitPlan, ...]

def resolve_key(
    action: Action,
    known_outputs: Mapping[ActionId, tuple[Identity, ...]],
) -> ActionKey | None:
    """None while any PendingRef's producer has no known output identity yet
    (or the referenced output's sha256 is None). known_outputs is fed from BOTH
    cache rows and just-executed actions."""
    ...
```

### The `ActionKey` canonical form — FROZEN FOREVER

`ActionKey(sha256_hex(canonical_form))` where `canonical_form` is the UTF-8
encoding of a JSON document with **sorted keys and no whitespace**:

```json
{"inputs":["<sha256>","<sha256>"],"params":{"...sorted...":"..."},"tool":"...","tool_version":"..."}
```

Inputs are the resolved sha256 strings in declared order. Golden tests hardcode
literal expected hashes; changing this form is a cache-invalidation event for
every user, never a casual test update.

**Design decision (deliberate):** `ActionKey` hashes the **content identity of
inputs**, not the upstream `ActionKey` — Nix-style content addressing, not
Bazel-style transitive action hashing. This buys *early cutoff*: if an upstream
action re-runs but produces byte-identical output, every downstream key is
unchanged and still hits.

---

## 4. `ir/layout.py`

```python
import enum
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

class MetadataDialect(enum.Enum):
    NONE = "none"
    ES_GAMELIST = "es_gamelist"

@dataclass(frozen=True, slots=True)
class LayoutConstraints:
    max_files_per_dir: int | None = None
    max_depth: int | None = None
    filename_max_len: int | None = None
    forbidden_chars: frozenset[str] = frozenset()

@dataclass(frozen=True, slots=True)
class MediaPolicy:
    max_image_width: int | None = None
    max_image_height: int | None = None
    allow_video: bool = True

@dataclass(frozen=True, slots=True)
class LayoutEntry:
    artifact_sha256: str
    relative_path: Path

@dataclass(frozen=True, slots=True)
class LayoutPlan:
    root_name: str
    entries: tuple[LayoutEntry, ...]

@dataclass(frozen=True, slots=True)
class OutputSet:
    unit_outputs: Mapping[UnitId, tuple[Identity, ...]]   # immutable-mapping treatment as Action.params
```

`LayoutPlan` replaces the `organized_files_metadata` shadow dict (briefing §3.6)
with typed subdirectory placement, and is the **only** input to metadata
discovery — emitters never `rglob` the output tree (briefing §3.8).

---

## 5. Target protocols (`targets/`, introduced Phase 5)

```python
from typing import Protocol

class TargetProfile(Protocol):
    """Pure data. Loaded from the existing config/frontends/*.yaml +
    config/devices/*.yaml composition — YAML schema unchanged. Consumed at
    PLAN time (format negotiation) and EMIT time (layout/metadata policy)."""
    def supports(self, platform: PlatformId) -> bool: ...           # device CPU gates + frontend support
    def format_preferences(self, platform: PlatformId) -> list["FormatChain"]: ...  # ordered, e.g. [[chd], [cue_bin]]
    def layout_constraints(self) -> LayoutConstraints: ...
    def metadata_dialect(self) -> MetadataDialect: ...
    def media_policy(self) -> MediaPolicy: ...

class TargetEmitter(Protocol):
    """Behavior — consumed at EMIT time only. Core never branches on target
    identity; it delegates here."""
    def plan_layout(self, outputs: OutputSet, profile: TargetProfile) -> LayoutPlan: ...
        # PURE: returns desired tree as data — {ArtifactRef -> relative path},
        # including subdirectory groups.
    def emit_metadata(self, layout: LayoutPlan, kb: "KnowledgeBase") -> list[ArtifactDecl]: ...
        # gamelist.xml, media rehydration declarations — themselves artifacts (cacheable)
    def post_process(self, root: Path) -> list["PostHook"]: ...
        # jdupes, rsync deploy, install-script emission
```

`FormatChain` is an ordered tuple of format steps (e.g., `(xiso, squashfs)` for
Xbox) resolved by the negotiation step: recipe preferences ∩ profile
preferences, first mutual match wins.

---

## 6. Engine runtime types (`engine/`, introduced Phases 2 and 4)

```python
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

@dataclass(frozen=True, slots=True)
class ActionCacheRow:
    key: ActionKey
    outputs: tuple[Identity, ...]     # COMPLETE identities incl. all aliases
    tool: str
    tool_version: str
    created_at: datetime

class Transform(Protocol):
    """Dumb tool adapter. Cache-unaware, context-unaware, DB-unaware."""
    def run(self, inputs: list[Path], params: Mapping[str, str], scratch: Path) -> list[Path]: ...

# --- Budget supervision (Phase 4) ---

@dataclass(frozen=True, slots=True)
class SelectionResult:
    selected: tuple[UnitPlan, ...]     # RATING-DESCENDING — this ordering is a load-bearing contract
    alternates: tuple[UnitPlan, ...]   # next-best unselected units, same ordering, for backfill
    predicted_total: int
    budget: int
    safety_margin: float               # e.g. 0.05 — the legacy *0.95 factor, made explicit

@dataclass(frozen=True, slots=True)
class LedgerState:
    committed: int                     # actual bytes of COMPLETED units (ground truth)
    estimated_remaining: int           # sum of predictions for units not yet built
    budget: int

    def projected_total(self) -> int:
        return self.committed + self.estimated_remaining

    def is_breach(self, tolerance: float) -> bool:
        return self.projected_total() > int(self.budget * (1 + tolerance))

class BudgetLedger:                    # mutable, owned by the executor supervisor
    def commit(self, unit_id: UnitId, actual_bytes: int) -> LedgerState: ...
    def state(self) -> LedgerState: ...

@dataclass(frozen=True, slots=True)
class Continue: ...

@dataclass(frozen=True, slots=True)
class DropTail:
    dropped: tuple[UnitId, ...]        # lowest-rated remaining units, with ledger evidence

@dataclass(frozen=True, slots=True)
class PromoteAlternates:
    promoted: tuple[UnitPlan, ...]     # headroom discovered — pull in next-best games

Adjustment = Continue | DropTail | PromoteAlternates

class ExecutionSupervisor:
    def on_unit_complete(self, unit: UnitPlan, actual_bytes: int) -> Adjustment: ...
```

---

## 7. Global invariants

1. Every IR class is `@dataclass(frozen=True, slots=True)`. Collection fields
   are `tuple` / `frozenset` — never `list`, `set`, or bare `dict`.
2. `romfarmer.ir` (except `bridge.py`) imports **stdlib only** — no pydantic, no
   sqlalchemy, no click, and zero imports from any `romfarmer.*` module.
   Enforced by import-linter.
3. No I/O in `ir/` except the temporary `bridge.py`'s documented filesystem
   reconciliation and `Path.stat`/`Path.exists` for identity lifting.
4. No `getattr`/`setattr`/`hasattr` dynamic access outside `bridge.py` (the
   quarantine zone). No `typing.Any` anywhere. `mypy --strict` clean.
5. `resolve_key` is deterministic across runs and platforms; golden tests pin
   literal hash values.
6. SQLite is reachable only through three facades: `KnowledgeBase` (read),
   `ActionCache` (executor-only read/write), `Telemetry` (append-only).
7. The Executor is the sole writer of identity aliases, and every action-cache
   store writes the row + all aliases + the telemetry record in one transaction.
8. Phases 1–3 (RESOLVE, CATALOG, PLAN) never mutate the filesystem. Only the
   Executor (scratch + CAS) and the Materializer (output tree) touch disk.
