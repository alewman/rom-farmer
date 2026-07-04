# Compiler Refactor — Document Set

**Session date:** 2026-07-03
**Status:** Phase 3 complete and merged (2026-07-03). Phase 4 not yet started.
**Authored by:** Principal-architect session (Claude Fable 5) with the project owner.
**Executed by:** Claude Sonnet 4.6 coding agent, one phase per branch.

---

## What this is

ROM Farmer has outgrown its organic structure: ~60 Python modules, 21 pipeline
stages sharing a mutable `StageContext`, filesystem-as-state, and platform quirks
scattered across the stage layer. This document set is the complete, agreed
architectural blueprint for restructuring it into a **content-addressed build
compiler** — plus the tactical migration plan to get there without ever breaking
the build.

The one-sentence diagnosis that drives everything:

> ROM Farmer is already ~80% of a Bazel/Nix-family build system — content-addressed
> store, transformation cache, deterministic external tools, declarative config —
> and every documented pain point is a symptom of one missing piece: **a typed
> Intermediate Representation with hard phase boundaries.**

## Document index

| Doc | Contents | Read when |
|-----|----------|-----------|
| [01-architecture-blueprint.md](01-architecture-blueprint.md) | Target architecture: the five-phase compiler paradigm, the IR, the 21→4 stage collapse, target isolation (Profile/Emitter), system diagrams, module layout, pain-point fixes | First. This is the "why" and the "what" |
| [02-ir-contracts.md](02-ir-contracts.md) | The frozen data contracts: `Identity`, `GameUnit`, `Catalog`, `Action`, `ActionKey`, `BuildPlan`, `LayoutPlan`, target protocols, engine runtime types, invariants | Before implementing any phase; the coding agent treats this as spec |
| [03-migration-roadmap.md](03-migration-roadmap.md) | The five sequential migration phases: files to create/modify, inputs/outputs, pass/fail gates, and the full strangler-bridge code sketch | When planning or executing a phase |
| [04-edge-case-designs.md](04-edge-case-designs.md) | Worked designs for the three hard cases: multi-disc atomicity, the Xbox two-step under the action cache, and mid-build budget breach recovery | When implementing CATALOG (Phase 3), the executor (Phase 2/4), or the supervisor |
| [05-phase1-agent-prompt.md](05-phase1-agent-prompt.md) | The copy-pasteable kickoff prompt for the Claude Sonnet 4.6 coding agent, Phase 1 (reusable skeleton for later phases) | When kicking off implementation |

## The decision, in brief

Restructure as a five-phase data compiler with typed, serializable, frozen
artifacts at every boundary:

```
1. RESOLVE   YAML configs                        → BuildManifest
2. CATALOG   manifest + sources + DATs + DB      → Catalog (GameUnits)
3. PLAN      catalog → pure passes → lowering    → BuildPlan (Action DAG)
4. EXECUTE   plan + CAS + action cache           → OutputSet (artifacts in CAS)
5. EMIT      outputs + TargetProfile             → output tree + metadata
```

Key structural moves (full rationale in doc 01):

- **Caching becomes executor infrastructure, not stages.** `CachePreCheckStage`,
  `CacheStoreStage`, and `CASIngestStage` are deleted; every action is checked
  against the action cache uniformly.
- **Content-addressed `ActionKey`** (Nix-style early cutoff) with a unified
  `Identity` (sha256 primary + md5/crc32/zip aliases) written atomically by a
  single writer — fixes the MD5-vs-CRC32 cache divergence (briefing §3.9).
- **Platform quirks become lowering rules as data** — PS3, Xbox, arcade chains
  are declared per-platform, not hardcoded in `stages/builder.py`.
- **Targets split into `TargetProfile` (declarative constraints consumed at PLAN)
  and `TargetEmitter` (behavior at EMIT)** with one generic hardlink Materializer.
  Everdrive becomes one YAML profile + the default emitter, zero core code.
- **One `CostModel`** (size_data.json priors + telemetry posteriors) powers both
  optimization loops: the within-build budget knapsack and the across-build
  ratio learning.
- **The plan is a policy, not a promise:** a `BudgetLedger` + rating-descending
  execution + pure tail-replan handles mid-build budget breaches without restart.

## What gets deleted by the end

`StageContext` and the entire `stages/` package, both orchestrators
(`build_orchestrator.py`, `platform_processor.py`, `build_loader.py`), the
symlink soft-delete mechanism, `BuildState` YAML (resume becomes
replan-plus-cache-hits), the `organized_files_metadata` shadow dict, and the
temporary `ir/bridge.py` itself.

## Working agreement for implementation

- One phase per branch; merge gated on the phase checklist in doc 03, not on
  the agent's self-report.
- Legacy path stays runnable behind `ROMFARMER_LEGACY=1` until Phase 5.
- Verify-then-commit loop: implement → mypy + pytest → commit, always green.
- The contracts in doc 02 are frozen. If reality contradicts them, stop and
  escalate — do not improvise.
