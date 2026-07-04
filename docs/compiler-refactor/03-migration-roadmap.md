# 03 — Technical Migration Roadmap (Strangler Pattern)

**Status:** Agreed 2026-07-03. Five sequential phases, each independently
shippable and gated. Verified against the codebase: `StageContext`, `Stage`,
`StageResult`, `StageStatus`, and `StagePhase` all live in
`src/romfarmer/stages/base.py`; `pyproject.toml` already carries `[tool.mypy]`,
`[tool.pytest.ini_options]`, and `[tool.ruff]` sections (no import-linter yet).

**Global rules for every phase:**

- One feature branch per phase; merge gated on the phase checklist below, not on
  the coding agent's self-report.
- The legacy path stays runnable behind `ROMFARMER_LEGACY=1` until Phase 5.
- Every phase ends with the full existing test suite green **plus** that phase's
  new gate.
- Verify-then-commit loop: implement one module + tests → mypy + pytest →
  commit. Small commits, always green.

---

## Phase overview

| # | Phase | Risk | Depends on | Shippable value when done |
|---|-------|------|------------|---------------------------|
| 1 | IR Foundation + Strangler Bridge | None (pure additive) | — | Typed contracts exist; drift detector makes §3.7 divergence loud |
| 2 | Engine: ActionCache + Executor + Transforms | Medium (touches cache path) | 1 | §3.9 fixed; cache stages become shells; repeat builds provably zero-work |
| 3 | Catalog + Pure Planner Passes | Medium | 1, 2 | Symlink soft-delete dead; `romfarmer plan --explain`; single CostModel |
| 4 | Lowering + Plan-Driven Execution | High (replaces stage routing) | 2, 3 | `stages/builder.py` retired; BuildPlan serializable; `--dry-run` |
| 5 | Target Profiles/Emitters + Legacy Deletion | Low (deletion + parity) | 4 | `stages/`, both orchestrators, `StageContext`, bridge all deleted |

---

## Phase 1 — IR Foundation + Strangler Bridge

**Create:**

| File | Contents |
|---|---|
| `src/romfarmer/ir/__init__.py` | Re-exports; `__all__` |
| `src/romfarmer/ir/identity.py` | `Identity`, `ZipIdentity` |
| `src/romfarmer/ir/catalog.py` | `PlatformId`, `UnitId`, `SourceRef`, `DiscRef`, `GameUnit`, `Catalog`, `PassTrace`, `PassResult`, `CatalogWarning` |
| `src/romfarmer/ir/actions.py` | `ActionId`, `ActionKey`, `ContentRef`, `PendingRef`, `InputRef`, `ArtifactDecl`, `Retention`, `Action`, `SizePrediction`, `UnitPlan`, `BuildPlan`, `resolve_key()` |
| `src/romfarmer/ir/layout.py` | `OutputSet`, `LayoutEntry`, `LayoutPlan`, `LayoutConstraints`, `MetadataDialect`, `MediaPolicy` |
| `src/romfarmer/ir/bridge.py` | `catalog_from_context`, `apply_catalog_to_context`, `assert_context_fs_sync`, `PassAsStage` (full sketch in §Bridge below) |
| `tests/ir/test_identity.py` | Merge semantics, `best_key` precedence, completeness |
| `tests/ir/test_actionkey_golden.py` | **Golden hashes** — hardcoded expected `ActionKey` values for fixed inputs; fails if canonicalization ever drifts |
| `tests/ir/test_catalog_invariants.py` | Unit granularity (no disc-level removal API), immutability, `keep`/`without` |
| `tests/ir/test_bridge_roundtrip.py` | Fake `StageContext` → `Catalog` → write-back → assert legacy fields + symlink reconciliation |

**Modify:** `pyproject.toml` only — add `romfarmer.ir` to strict mypy scope; add
`import-linter` dev dependency with one contract: *`romfarmer.ir` may import
nothing from `romfarmer` (exception: `ir.bridge` may import
`romfarmer.stages.base` under `TYPE_CHECKING`).*

**Inputs:** the type contracts in [02-ir-contracts.md](02-ir-contracts.md).
**Outputs:** an importable `romfarmer.ir` package with zero runtime integration
— no legacy module imports it yet.

**Gate before Phase 2:**

1. `mypy --strict src/romfarmer/ir/` clean.
2. `pytest tests/ir/` green; golden ActionKey test committed with literal hash
   values.
3. `lint-imports` passes.
4. Full existing suite green; `git diff --stat` shows **zero** lines changed
   under `src/romfarmer/stages/` or either orchestrator.

---

## Phase 2 — Engine: ActionCache + Executor absorb caching

**Create:**

| File | Contents |
|---|---|
| `src/romfarmer/engine/actioncache.py` | SQLite facade over new tables `action_cache(key, outputs_json, tool, tool_version, created_at)` + `artifact_aliases(sha256, md5, zip_crc32, zip_size, zip_member)`. **Sole writer of aliases.** |
| `src/romfarmer/engine/scratch.py` | Per-unit scratch dir lifecycle (create → run → delete), preserving today's peak-disk cap |
| `src/romfarmer/engine/executor.py` | DAG walk, deferred key resolution, uniform cache check/store, lazy materialization, telemetry emission |
| `src/romfarmer/engine/transforms/base.py` | `Transform` protocol: `(inputs: list[Path], params, scratch: Path) -> list[Path]` — cache-unaware, context-unaware |
| `src/romfarmer/engine/transforms/{chd,archive,xiso,ps3,rvz,wux,unzip}.py` | Tool-invocation cores **extracted** (not rewritten) from `stages/compress.py`, `stages/convert_xiso.py`, `stages/transform_ps3.py`, etc. |
| `scripts/migrate_action_cache.py` | Idempotent backfill: every `ROMCache` row → one `action_cache` row + `artifact_aliases` row |
| `tests/fixtures/make_corpus.py` | Generates a synthetic mini-collection (tiny zips with known CRC32/MD5, fake cue/bin) for all parity gates — no copyrighted content |
| `tests/engine/test_executor_cache.py`, `tests/engine/test_alias_atomicity.py` | See gate |

**Modify:** `src/romfarmer/cache/manager.py` becomes a thin compatibility shim
delegating to `ActionCache` (legacy callers keep working);
`stages/cache_precheck.py` and `stages/cache_store.py` internals delegate to the
same facade — the stages stay in the pipeline as shells until Phase 4.

**Inputs:** existing `ROMCache` rows + CAS blobs. **Outputs:** one action cache
with unified alias table; executor able to run a hand-built `BuildPlan` in
tests.

**Gate before Phase 3:**

1. Backfill script run twice = identical row counts (idempotence).
2. **§3.9 regression test:** store via zip-identity path, then query by MD5 →
   hit (and vice versa). Both aliases written in one transaction, asserted.
3. Smoke: build fixture platform twice through the legacy pipeline (now backed
   by ActionCache); second run performs **zero** transform invocations (assert
   via call-counter injected into `Transform`).
4. Full legacy suite green.

---

## Phase 3 — Catalog + Pure Planner Passes

**Create:**

| File | Contents |
|---|---|
| `src/romfarmer/analysis/catalog_builder.py` | Scan + hash + DAT match + multi-disc grouping → `Catalog`. Absorbs the identity half of `stages/filter_dat.py` |
| `src/romfarmer/analysis/knowledge.py` | `KnowledgeBase` — the only read facade over `romfarmer.db` metadata |
| `src/romfarmer/planner/passes/{region,dat_dedup,one_g_one_r,arcade,rating,curated_lists,generation,budget}.py` | Each: `run(Catalog, BuildManifest, KnowledgeBase, CostModel) -> PassResult`. Pure — no filesystem, no symlinks |
| `src/romfarmer/planner/costmodel.py` | Enum-keyed; `size_data.json` priors + `ROMTransformation` posteriors; **unknown platform = loud error**, not silent 0.85 |
| `src/romfarmer/planner/runner.py` | Ordered pass execution, accumulates `PassTrace` list |
| `src/romfarmer/cli/plan.py` | `romfarmer plan --explain` renders per-pass deltas |
| `tests/migration/test_plan_parity.py` | A/B harness (see gate) |

**Modify:** `src/romfarmer/new_orchestrator.py` — its PLAN section becomes:
`CatalogBuilder` → `PassRunner` → `ContextBridge.apply_catalog_to_context()` →
legacy EXECUTE loop continues unchanged. Legacy PLAN stages remain runnable via
`ROMFARMER_LEGACY=1`.

**Inputs:** `BuildManifest` + source dirs + DATs + KnowledgeBase. **Outputs:**
final `Catalog` + trace, handed to the still-legacy EXECUTE loop through the
bridge.

**Gate before Phase 4:**

1. A/B parity: for each fixture config and each selection strategy, legacy PLAN
   stages and new passes produce **identical selected sets** (compare normalized
   names, not paths).
2. New path creates zero symlinks; `assert_context_fs_sync` passes after bridge
   write-back.
3. `plan --explain` output snapshot test ("Chrono Cross — removed by generation
   pass, kept on psx").
4. CostModel unit tests: prior/posterior merge, enum-keyed lookup, loud
   unknown-platform failure.

---

## Phase 4 — Lowering + Plan-Driven Execution

**Create:**

| File | Contents |
|---|---|
| `src/romfarmer/planner/lowering/base.py` | `LoweringRule` protocol: `lower(GameUnit, FormatChain, BuildManifest) -> UnitPlan` |
| `src/romfarmer/planner/lowering/{disc,cartridge,rvz,wux,xiso,ps3,arcade,passthrough}.py` | Replaces the eight `_*_stages()` lists in `stages/builder.py`. M3U declared here as a derived artifact; PS3 updates become acquisition actions |
| `src/romfarmer/planner/negotiation.py` | Recipe `FormatChain`s ∩ `TargetProfile.format_preferences` → chosen chain |
| `tests/planner/test_golden_plans.py` | Serialized `BuildPlan` snapshots per fixture config |
| `tests/migration/test_output_parity.py` | Legacy vs new full-run output tree comparison |

**Modify:** `src/romfarmer/new_orchestrator.py` EXECUTE loop →
`engine.executor.run(build_plan)`; add `romfarmer build --dry-run` (prints plan,
touches nothing).

**Inputs:** final `Catalog` + negotiated format chains. **Outputs:** serialized
`BuildPlan`; executed `OutputSet` (artifacts in CAS).

**Gate before Phase 5:**

1. Golden plan snapshots stable across two runs (determinism).
2. Output parity vs legacy per platform family (disc, cartridge, rvz, xiso,
   ps3-lite fixture): identical file sets, identical hashes.
3. Cache-hit parity: CAS populated by a *legacy* build yields hits under the
   *new* executor (proves the ActionKey ↔ ROMCache backfill mapping).
4. FINALIZE stages still run via bridge; suite green.

---

## Phase 5 — Target Profiles/Emitters + Legacy Deletion

**Create:**

| File | Contents |
|---|---|
| `src/romfarmer/targets/profiles/loader.py` | Loads existing `config/frontends/*.yaml` + `config/devices/*.yaml` into `TargetProfile` (YAML schema unchanged — zero user migration) |
| `src/romfarmer/targets/emitters/{base,materializer,generic,es_gamelist,extras}.py` | `plan_layout` (pure), generic hardlink materializer (ports `_link_or_copy`), gamelist emitter (ports the `metadata/generator.py` call path), extras emitter |
| `tests/targets/test_emit_golden.py` | Golden tree manifests + gamelist.xml for batocera / rocknix / everdrive fixture builds |

**Delete (after the parity gate passes, in this order):**

1. `stages/m3u.py`, `stages/organize.py`, `stages/metadata.py`,
   `stages/emit_extras.py` — replaced by emitters.
2. The whole `stages/` package including `stages/base.py`.
3. `build_orchestrator.py`, `platform_processor.py`, `build_loader.py`.
4. `ir/bridge.py` — the bridge itself dies.
5. `BuildState` YAML handling in `build_models.py` — resume is now
   replan-plus-cache-hits.

**Gate (final):**

1. E2E fixture builds for three targets diffed against golden manifests (tree
   listing + hashes); gamelist.xml golden.
2. Resume test: kill build mid-EXECUTE, rerun — completes via replan + cache
   hits with **no** `state/.build_state_*.yaml`.
3. `grep -rn "StageContext\|stages\." src/romfarmer/` → zero hits.
4. Final import-linter contract (full layering rules from
   [01-architecture-blueprint.md](01-architecture-blueprint.md) §3.2) enforced
   in CI.

---

## The Strangler Bridge — reference sketch

This is the only module that ever knows about both worlds. It is load-bearing in
Phases 2–4 and deleted in Phase 5.

```python
# src/romfarmer/ir/bridge.py
"""TEMPORARY strangler bridge between the legacy StageContext and the immutable IR.

Lifecycle: created in Phase 1, load-bearing in Phases 2-4, DELETED in Phase 5.
Rules:
  * This is the ONLY module permitted to import both worlds.
  * This is the ONLY module where defensive attribute access (getattr) is
    permitted — the legacy context has two config eras (briefing §3.5) and
    quarantining that mess here is the point.
  * The IR snapshot is authoritative. Legacy fields are derived views.
  * Every write-back also reconciles work_dir symlinks, because unconverted
    stages still treat the filesystem as state (briefing §3.7).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from romfarmer.ir.catalog import Catalog, DiscRef, GameUnit, PlatformId, SourceRef
from romfarmer.ir.identity import Identity

if TYPE_CHECKING:  # never a runtime import — keeps ir/ decoupled
    from romfarmer.stages.base import StageContext

_DISC_TAG = re.compile(r"\s*\((?:Disc|Disk|CD)\s*(\d+)\)", re.IGNORECASE)


def _unit_key(path: Path) -> str:
    """Disc-number-stripped grouping key. Mirrors SelectionFilter._group_multi_disc_games."""
    return _DISC_TAG.sub("", path.stem).strip().lower()


def _disc_index(path: Path) -> int:
    m = _DISC_TAG.search(path.stem)
    return int(m.group(1)) if m else 1


def _identity_for(ctx: "StageContext", path: Path) -> Identity:
    """Lift whatever identity the legacy context already knows. Partial is fine —
    the executor is the only component that REQUIRES complete identity."""
    md5: str | None = None
    hashes = getattr(ctx, "file_hashes", None)          # quarantined defensive access
    if hashes is not None:
        source_md5 = getattr(hashes, "source_md5", None)
        if isinstance(source_md5, dict):
            md5 = source_md5.get(str(path))
    size = path.stat().st_size if path.exists() else None
    return Identity(size=size, md5=md5)


def catalog_from_context(ctx: "StageContext", platform: str) -> Catalog:
    """Lift the mutable legacy context into an immutable Catalog snapshot.

    Reads the SAME precedence chain the legacy stages use:
    filtered_files -> matched_files -> source_files.
    """
    raw = ctx.filtered_files or ctx.matched_files or ctx.source_files or []
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
                dat_name=None,  # enrichment is CatalogBuilder's job (Phase 3); bridge stays shallow
            )
            for p in members
        )
        units.append(GameUnit.from_discs(PlatformId(platform), key, discs))
    return Catalog(platform=PlatformId(platform), units=tuple(units))


def apply_catalog_to_context(catalog: Catalog, ctx: "StageContext") -> None:
    """Write-back: make the legacy views agree with the authoritative snapshot.

    Performs BOTH halves of the undocumented legacy dual-write contract
    (briefing §3.7) so unconverted downstream stages keep functioning:
      1. the context list fields
      2. the work_dir symlink population
    """
    selected = [str(d.source.path) for u in catalog.units for d in u.discs]
    ctx.filtered_files = list(selected)

    work_dir = getattr(ctx, "work_dir", None)
    if work_dir is None:
        return
    keep = {Path(p).name for p in selected}
    for link in Path(work_dir).glob("*"):
        if link.is_symlink() and link.name not in keep:
            link.unlink()


def assert_context_fs_sync(ctx: "StageContext") -> None:
    """Loud drift detector for the migration period. Turns the silent §3.7
    divergence into an immediate, diagnosable failure."""
    work_dir = getattr(ctx, "work_dir", None)
    if work_dir is None:
        return
    fs = {p.name for p in Path(work_dir).glob("*") if p.is_symlink()}
    mem = {Path(p).name for p in (ctx.filtered_files or [])}
    if fs != mem:
        raise RuntimeError(
            "context/filesystem divergence: "
            f"only-in-fs={sorted(fs - mem)[:5]} only-in-context={sorted(mem - fs)[:5]}"
        )


class PassAsStage:
    """Run a pure IR pass inside the legacy pipeline: new engine in the old shell.

    The legacy pipeline executor sees a duck-typed Stage (has PHASE + execute);
    internally we lift -> run pure pass -> write back -> verify. This is how
    converted passes ship one at a time in Phase 3 while unconverted stages
    still surround them.
    """

    PHASE = "PLAN"
    name = "pass-as-stage"

    def __init__(self, pure_pass: object, platform: str) -> None:
        self._pass = pure_pass
        self._platform = platform
        self.name = f"bridged:{type(pure_pass).__name__}"

    def execute(self, context: "StageContext") -> "StageContext":
        before = catalog_from_context(context, self._platform)
        result = self._pass.run(before)          # PassResult(catalog, trace)
        apply_catalog_to_context(result.catalog, context)
        assert_context_fs_sync(context)
        return context
```

**Why this keeps the project compilable at every commit:** legacy code never
imports `ir/` (the bridge imports *it*, one-directional); each converted pass is
dropped into the old pipeline via `PassAsStage`; each converted subsystem moves
the authority boundary one step right, and the bridge shrinks until Phase 5
deletes it.

**Implementation note for Phase 1:** before writing the bridge, read the real
`src/romfarmer/stages/base.py` and `src/romfarmer/stages/filter_selection.py`.
If actual field names differ from this sketch's assumptions (`filtered_files`,
`matched_files`, `source_files`, `work_dir`, `file_hashes.source_md5`), adapt
the bridge to reality and encode the findings as assertions in the round-trip
test — do **not** change the IR contracts to compensate.
