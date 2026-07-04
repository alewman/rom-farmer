# 04 — Edge-Case Designs

**Status:** Agreed 2026-07-03. Worked designs for the three scenarios that
stress the architecture hardest. Type signatures here are excerpts of the frozen
contracts in [02-ir-contracts.md](02-ir-contracts.md) — that document wins if
they ever drift.

---

## 1. Multi-Disc Atomicity

**Principle: atomicity is structural, not behavioral.** Grouping happens exactly
once — in `CatalogBuilder` — using the name normalizer, the `(Disc N)` regex,
and DAT parent/serial cross-checks where a DAT exists. After CATALOG, no pass
can see a disc as an independent thing, because the pass API operates at unit
granularity and `DiscRef` is only reachable through its parent.

The load-bearing contract excerpts:

```python
@dataclass(frozen=True, slots=True)
class DiscRef:
    index: int                           # 1-based; single-disc games have index=1
    source: SourceRef
    identity: Identity
    dat_name: str | None = None

@dataclass(frozen=True, slots=True)
class GameUnit:
    unit_id: UnitId
    platform: PlatformId
    canonical_name: str
    discs: tuple[DiscRef, ...]           # INVARIANT: len >= 1, sorted by index.
                                         # A single-disc game is a 1-tuple — there
                                         # is no "loose file" concept.
    # ... region / languages / rating / tier / generation ...

    @property
    def source_size(self) -> int:
        """The ONLY size the budget pass may consult. Sums all discs —
        all-or-nothing accounting falls out for free."""
        return sum(d.identity.size or 0 for d in self.discs)

@dataclass(frozen=True, slots=True)
class Catalog:
    platform: PlatformId | None
    units: tuple[GameUnit, ...]
    warnings: tuple[CatalogWarning, ...] = ()

    # The ENTIRE mutation surface — unit granularity only. There is no API
    # that adds, removes, or replaces an individual DiscRef.
    def keep(self, ids: AbstractSet[UnitId]) -> "Catalog": ...
    def without(self, ids: AbstractSet[UnitId]) -> "Catalog": ...
    def merge(self, other: "Catalog") -> "Catalog": ...
```

**How the guarantee propagates downstream:**

- **PLAN:** `SelectionPass` iterates `GameUnit`s and calls `unit.source_size` —
  it *cannot* partially select Final Fantasy VII because discs aren't
  addressable. The legacy `_group_multi_disc_games()` regex-at-selection-time
  dance is gone.
- **Lowering fan-out:** one `GameUnit` lowers to N per-disc compress `Action`s
  **plus** one M3U derived-artifact `Action` whose inputs are the N disc
  outputs — disc membership is plan-time knowledge, so the M3U needs no
  post-hoc regex regrouping (retiring `stages/m3u.py`'s discovery logic).
- **Degenerate sets:** `CatalogBuilder` policy — non-contiguous disc sets
  (`[1, 3]`) or mixed-region disc groups (Disc 1 USA / Disc 2 Europe rip
  variants) are *quarantined with a `CatalogWarning`*, never silently merged or
  split. Loud at CATALOG, invisible everywhere after. Grouping resolution order:
  normalized name AND DAT parent where present; conflicts → warning + quarantine.
- **Unit invariant vs builder policy:** `GameUnit.__post_init__` enforces only
  "non-empty, sorted by index." Contiguity is deliberately a *builder policy*,
  not a type invariant, so a legitimately weird collection can still be
  represented and flagged rather than crashing plan construction.

---

## 2. Complex Transform Chains — the Xbox Two-Step under the Action Cache

The Xbox path (`FormatChain = (xiso, squashfs)`) lowers one unit into a chain of
three actions:

```
A1: unzip(Halo.zip)            → halo_redump.iso   [INTERMEDIATE]
A2: extract-xiso(A1.out)       → halo.xiso.iso     [INTERMEDIATE]
A3: mksquashfs(A2.out, bs=1M)  → halo.squashfs     [TERMINAL]
```

Contract excerpts that make the evaluation work:

```python
@dataclass(frozen=True, slots=True)
class ContentRef:
    sha256: str                        # input identity known at plan time

@dataclass(frozen=True, slots=True)
class PendingRef:
    producer: ActionId                 # identity known only once the producer's
    output_index: int                  # outputs are known (from cache row or execution)

InputRef = ContentRef | PendingRef

def resolve_key(
    action: Action,
    known_outputs: Mapping[ActionId, tuple[Identity, ...]],
) -> ActionKey | None:
    """None while any PendingRef's producer has no known output identity yet.
    known_outputs is fed from BOTH cache rows and just-executed actions."""
```

**The critical design decision:** `ActionKey` hashes the **content identity of
inputs**, not the upstream `ActionKey` (Nix-style content addressing, not
Bazel-style transitive action hashing). This buys *early cutoff*: if an upstream
action re-runs but produces byte-identical output, every downstream key is
unchanged and still hits.

### Trace: A1 and A2 hit, A3 misses

Scenario: Halo was previously built for Batocera (plain XISO). Today's build
adds SquashFS with a new block size — so the conversion is cached but the final
compression is not.

| Step | Executor action | Key resolvable? | Cache | Filesystem effect |
|---|---|---|---|---|
| 1 | Visit A1. Inputs are `ContentRef(zip sha256)` — resolvable immediately. | Yes | **HIT** | **None.** Output identities read from the cache row into `known_outputs[A1]`. Nothing is materialized. |
| 2 | Visit A2. Its `PendingRef(A1, 0)` now resolves from `known_outputs`. | Yes | **HIT** | **None.** `known_outputs[A2]` populated from the row. The raw Redump ISO is never linked to disk at all. |
| 3 | Visit A3. `PendingRef(A2, 0)` resolves. New `bs=1M` param → new key. | Yes | **MISS** | **Lazy materialization, now and only now:** `cas.link(known_outputs[A2][0].sha256, scratch/halo.xiso.iso)` — a hardlink, zero-copy. Run `mksquashfs`. Ingest output into CAS; write the A3 cache row + **all** alias hashes + telemetry row in one transaction. Delete scratch. |

Three invariants make this correct and cheap:

1. **Satisfied-by-cache ≠ materialized.** A cache hit only teaches the executor
   the output's identity. Bytes are hardlinked into scratch *only* when they're
   an input to an action that actually runs. Peak disk = one unit's live
   intermediates (preserving today's per-game-group property, enforced by
   `engine/scratch.py`).
2. **The mirror case (A1 misses, A2 "would" hit) degrades gracefully.** A2's key
   is unresolvable until A1 runs — but after A1 runs, if its output identity
   matches what some previous build produced, A2's key resolves to an existing
   row and **hits anyway**. That's early cutoff paying off: a re-downloaded zip
   with different mtimes but identical content invalidates nothing downstream.
3. **GC by retention class.** `INTERMEDIATE` artifacts (the 7 GB raw Redump ISO)
   are evictable under a policy like "unreferenced by any cache row younger than
   N days"; `TERMINAL` artifacts are pinned while any emitted layout references
   them. CAS growth stays bounded without ever risking a target-visible file.

---

## 3. Backward-Budget Feedback Loop — breach handling without restart

**Problem:** the PLAN phase predicted psx compresses at ratio 0.70; reality is
0.82. The naive outcome is blowing the storage budget or a full 3-hour restart.

**Principle: the plan is a policy, not a promise.** Selection emits a *ranked*
plan with a contingency tail; the executor owns a live ledger; a breach triggers
a *pure, in-memory tail re-plan* — never a restart.

Contract excerpts (full versions in [02-ir-contracts.md](02-ir-contracts.md) §6):

```python
@dataclass(frozen=True, slots=True)
class SelectionResult:
    selected: tuple[UnitPlan, ...]     # RATING-DESCENDING — this ordering is a load-bearing contract
    alternates: tuple[UnitPlan, ...]   # next-best unselected units, for under-budget backfill
    predicted_total: int
    budget: int
    safety_margin: float               # the legacy *0.95 factor, made explicit

@dataclass(frozen=True, slots=True)
class LedgerState:
    committed: int                     # actual bytes of COMPLETED units (ground truth)
    estimated_remaining: int           # predictions for units not yet built
    budget: int
    def projected_total(self) -> int: ...
    def is_breach(self, tolerance: float) -> bool: ...

Adjustment = Continue | DropTail | PromoteAlternates

class ExecutionSupervisor:
    def on_unit_complete(self, unit: UnitPlan, actual_bytes: int) -> Adjustment: ...
```

### The loop, concretely

1. **Execution order = rating-descending** — the same ordering selection used.
   The most-wanted games are built first, so any future cut can only hit the
   *least*-wanted remainder.
2. After each unit: `ledger.commit(unit, actual)`; the CostModel posterior
   updates **online** (Welford running mean per `(platform, format)` — after
   ~10 units the 0.82 reality dominates the stale 0.70 prior).
3. `on_unit_complete` recomputes `estimated_remaining` using the *fresh*
   posterior and checks `is_breach(tolerance)`.
4. **Breach → tail re-plan:** call the budget pass again —
   `replan(remaining_units, budget - committed, updated_cost_model)`. This is a
   pure function over in-memory data: milliseconds, no I/O, no restart. It
   returns the trimmed tail; the supervisor emits `DropTail([...])`, and those
   units simply never execute. Since they were the lowest-rated remainder, the
   outcome converges to exactly what the original plan would have chosen had the
   true ratio been known.
5. **Nothing is wasted.** Dropped units cost zero (never built). Already-built
   units that "overspent" are sunk *into CAS* — warm cache for any future,
   larger-budget build.
6. **EMIT separation is what makes this safe.** Because layout happens only
   after the final unit set is settled, there is no output-tree surgery: no
   built-then-deleted files, no gamelist rewrites, no orphaned media.
7. **The pleasant inverse:** reality beats prediction → headroom →
   `PromoteAlternates` pulls the next-highest-rated games from the pre-ranked
   `alternates` list (their lowering is a pure computation, done lazily on
   promotion). The legacy system leaves that budget on the table.
8. **Cross-platform budgets:** the ledger is global; per-platform figures are
   soft allocations. Rebalancing happens at platform boundaries in the
   supervisor — under-spend on `snes` flows to `psx`'s remaining allocation via
   the same re-plan call.
