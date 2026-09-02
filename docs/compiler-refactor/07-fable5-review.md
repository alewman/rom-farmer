# 07 — Fable 5 Answers + Work Order

**Session date:** 2026-07-04
**Input:** `06-fable5-questions.md` (all 15 questions), source verified against
commit HEAD on 2026-07-04.
**Audience:** This document is a self-contained work order for Claude Sonnet.
Part I records the decisions and their reasoning. Part II is the prioritized
task list. Part III lists work that was considered and **rejected** — do not
build it.

---

## Global constraints (read first)

1. **The ActionKey canonical form is frozen.** No task below changes
   `resolve_key`'s JSON shape in `src/romfarmer/ir/actions.py`. Tasks that need
   a cache-invalidation lever use the `tool_version` string (see T5), which is
   already a free-form field.
2. **Do not invalidate the existing action cache.** Any change that would alter
   the computed key for an action that lowering emits *today* is a bug in the
   task implementation. T4/T5 are designed to be key-preserving; verify with
   the golden ActionKey test before and after.
3. **Gates for every task:** full suite green
   (`python3 -m pytest --ignore=tests/test_compression_ratio.py -q --no-cov`),
   `mypy --strict` clean, `lint-imports` 4/4 kept. Commit per task
   (verify-then-commit).
4. Repo memory context: `/memories/repo/architecture-refactor.md`.

---

# Part I — Decisions

## Q1. Phase seam — verdict: refactor to typed phase functions (T6)

A method-call seam is not inherently wrong; **this** one is wrong because each
method receives `resolved` + raw paths and can therefore re-derive anything at
any phase. The fix is not functional purity for its own sake — it is
**capability starvation**: a phase function's parameters must make the wiring
bugs unrepresentable.

Bug-by-bug mapping (from the 2026-07-04 review) to the structural change that
would have prevented it:

| Review bug | Structural prevention |
|---|---|
| 1. EXECUTE rebuilt catalog from source dir | EXECUTE's signature takes the PLAN product only — **no source paths, no `resolved` config** |
| 2. CAS-hash filenames in output | Executor returns `(ArtifactDecl, Identity)` **pairs**; the decl↔identity zip lives in exactly one place (the executor), never in glue |
| 3. Missing transform registrations | Plan-time validation: every `Action.tool` must have a registered transform **before** EXECUTE starts (fail at PLAN, not mid-build) |
| 4. EMIT re-hashed the output tree | EMIT's data source is the `LayoutPlan` parameter; delete the rescan fallback |
| 5. Wrong target-profile key | Profile is loaded once at RESOLVE and passed as a `ConcreteTargetProfile` **object**; EMIT never does string lookup |
| 6. Materializer hardlink duplicates | Not type-preventable — covered by invariant test (T7, invariant 5) |

Score: 4/6 prevented by signatures, 1 by plan validation, 1 by invariant test.
That is the ceiling for type-level enforcement in Python and it is enough.

Also part of this decision: **the error policy is a bug factory today.**
`_run_execute_path` catches `Exception`, logs, returns `None` — a unit failure
silently skips an entire platform, and `None` propagation is exactly the kind
of glue the review flagged. Phases must raise; the driver catches once and
implements per-platform skip policy in one place; the executor catches
per-**unit** and reports failed units. See T6.

Explicitly rejected: effect systems, immutable-orchestrator purism, moving
cross-cutting concerns (state save, logging, budget) into phases. The driver
keeps those.

## Q2. Budget feedback loop — verdict: DO NOT BUILD (T10 covers the 80%)

The `ExecutionSupervisor`/`BudgetLedger`/`PromoteAlternates` design (doc 04 §3)
is rejected for this system:

- Single user, single machine, re-runnable builds, CAS-preserved sunk work: the
  worst case of a bad size prediction is one re-run **with a warm cache** —
  minutes, not the hours the supervisor is designed to save.
- A mid-build online posterior makes the realized build a function of
  execution order and timing. That silently destroys the strongest invariant
  the system has: *the plan is a pure deterministic function of
  (manifest, catalog)* — which T7 turns into a regression test and
  `plan --explain` depends on for auditability. This is a real architectural
  conflict, not a style preference: keeping single-shot planning is what makes
  Q14's property tests sound.
- The 80% version is ~50 lines: a **stop-early guard** in the executor
  (cumulative actual terminal bytes ≥ budget → stop launching units, report
  the rest as `budget-stop`), which converts over-runs (bad: must delete) into
  under-fills (safe: re-run picks them up), plus a predicted-vs-actual line in
  the build report so the posterior improves between builds. That is T10.

Doc 04 §3 must be annotated "designed, deliberately not built — see 07" so a
future agent doesn't cargo-cult it into existence.

## Q3. ActionKey soundness — verdict: form is sound; two real holes are outside the hash (T4, T5)

The frozen form (`sort_keys=True`, `separators=(",",":")`,
`ensure_ascii=True` default, inputs as ordered sha256 list) is sound **given**
`params: Mapping[str, str]`. The audit findings, in decreasing severity:

1. **Transform-side param defaults are un-keyed behavior — the only
   silent-corruption hole.** `ArchiveTransform` defaults `format="7z"`,
   `compression_level="9"`; `SquashFSTransform` defaults `compression="lz4"`.
   These defaults are part of the memoized function but not part of the key.
   If a default ever changes, old cache rows **hit** and return artifacts the
   current code would not produce. Same class: editing a transform's command
   construction (adding a flag) changes behavior with no key change. Fix is
   T5's per-tool impl-version folded into `tool_version` — never saturating
   params (that would orphan every backfilled cache row).
2. **`str→str` is enforced only by mypy.** An `int` param sneaking through an
   untyped call site serializes differently than its string twin → false
   miss/thrash, or two keys for one action. Runtime check in
   `Action.__post_init__` (T4). Float representation, int/str coercion, and
   nested-dict ordering are all non-issues *once this check exists*, because
   the type excludes them.
3. **Unicode normalization.** Params carry logical names (`name`, `entries` in
   the m3u action — e.g. "Pokémon …"). NFC vs NFD source filenames (Mac-copied
   collections) produce different `\uXXXX` escapes → false miss. NFC-normalize
   param values in `__post_init__` (T4). Safe direction: miss, never false-hit.
   No-Intro names are NFC in practice, so existing keys are preserved.
4. **`None`/absent ambiguity:** excluded by the str-only rule; "absent key vs
   explicit default" is exactly finding 1.
5. **What Nix/Bazel have that this doesn't:** Nix keys the *tool closure*
   (binary identity); Bazel keys the environment. Here `probe_tool_version`
   trusts a version string — a patched binary with an unchanged version string
   is a false hit. Accepted risk for a single-user system; partially mitigated
   by pinning the subprocess environment (T9), which also removes
   locale-dependent tool output as a corruption vector.

## Q4. Tool determinism — verdict: audit-then-pin; verify empirically (T9)

Key architectural fact first: ActionKeys are **input**-addressed, so a
nondeterministic tool does *not* poison the action cache. The blast radius is:
(a) downstream actions in a chain (only the Xbox `xiso → squashfs` chain is
deep enough to care), (b) CAS dedup across rebuilds after cache loss, (c) the
byte-reproducibility story. So this is hygiene, not fire.

Per-tool assessment (to be confirmed by the T9 double-run harness — do not
trust this table over the harness):

| Tool | Expected | Pin |
|---|---|---|
| `chdman` | Reproducible per version (hunk-indexed, no timestamps) | none; version keyed already |
| `mksquashfs` | 4.4+ reproducible mode default, but **embeds input file mtime**, and CAS-hardlink mtimes are ingest-time (unstable) | `-mkfs-time 0 -all-time 0 -all-root -no-xattrs`, fixed `-processors` |
| `7z` (7z fmt) | **Not** reproducible: stores mtimes; multithreaded LZMA2 chunking varies with `-mmt` | `-mtm=off`, fixed `-mmt=4`. Note: `_ZIP_TIMESTAMP` in archive.py is **dead code** today |
| `7z` (zip fmt) | Not reproducible (DOS timestamps) | Long-term: TorrentZip convention (ROM-community canonical). Short-term: accept + document |
| `extract-xiso` | Unknown — may stamp header | harness decides; feeds squashfs, so it matters most |
| `wit`/wux, `ps3dec`, `dolphin-tool` (RVZ→ISO) | Deterministic (decompression/decryption reconstructs original bytes) | none |
| m3u | In-repo, deterministic | none |

Where determinism is impossible (zip short-term): **exclude from the
reproducibility claim, not from caching** — input-addressed keys already
handle it correctly. Do not build output-normalization machinery.

Every flag change is a behavior change → requires the T5 impl-version bump for
that tool (this is why T5 lands before T9).

## Q5. Catalog rescan — verdict: build the digest cache (T8)

`(size, mtime_ns, inode)` — all three must match — is the sound fast-path key,
with Git's "racy" guard: if a file's mtime equals the scan's start window,
re-hash anyway. Known failure modes and their status here: coarse mtime
(FAT/2s) — covered by racy guard; mtime-preserving replace (rsync `-a` with
changed content but same size) — the only true hole, accepted with a
`--verify-catalog` escape hatch; NFS unstable inodes — not this deployment;
reflink copies get new inodes — correct behavior (cache miss, re-hash). Git's
index and Bazel's digest cache both ship exactly this design. New table in
`romfarmer.db`; prune rows for missing paths lazily.

## Q6. Concurrency — verdict: three concrete fixes (T2, T3), protocol is otherwise sound

Verified against the code:

- **No torn action_cache↔aliases view is possible**: `store()` writes row +
  aliases in one transaction (`INSERT OR IGNORE` + alias upsert with
  `COALESCE`). Readers see both or neither. The executor's earlier per-output
  `record_aliases` commits aliases first — benign (aliases are enrichment).
- **Real bug 1 — no `busy_timeout`.** Two writer processes under WAL: second
  gets `SQLITE_BUSY` → immediate "database is locked" exception. One-line
  pragma. (T3)
- **Real bug 2 — shared tmp name in `_ingest_to_cas`.** Both processes ingest
  the same content → both write `<dest>.tmp` (same path, check-then-act on
  `dest.exists()`), first `rename` wins, second's tmp vanished → spurious unit
  failure. Fix: unique tmp (`.tmp.<pid>.<rand>`) + `os.replace` + tolerate
  pre-existing dest. (T2)
- **Hit-but-no-blob**: possible if a blob is deleted out-of-band (manual, or
  future GC). Closed by T1's verify-on-hit, which degrades a poisoned row to a
  cache miss instead of a crash. With row-written-last ordering (already true)
  plus T1, no `MATERIALIZED` flag or fsync barrier is needed.

## Q7. Crash windows — verdict: T1 + per-unit failure semantics in T6

Window analysis of `run tool → ingest → aliases → store`:

| Crash point | Result | Severity |
|---|---|---|
| During transform | Scratch garbage (swept on next entry; add base sweep in T2) | benign |
| After ingest, before `store` | Orphan blob; re-run re-executes, ingest is idempotent | benign |
| After `store` | Fully consistent | — |
| Blob deleted after `store` | **Poisoned row** — hit that cannot materialize | closed by T1 |

Multi-disc atomicity today: disc-1 actions cache individually (good — retry
resumes), the unit produces no terminal outputs on failure so nothing partial
reaches EMIT (good), **but** the orchestrator's catch-all turns one failed unit
into a skipped *platform* (bad). T6 moves failure handling to per-unit in the
executor with an `ExecutionReport`. The unit remains atomic at the output
level; the disc-1 artifact remains valid and cacheable. This is the correct
recovery protocol; no rollback machinery is warranted.

## Q8. CostModel — verdict: no model change; add observability

The budget decision consumes the *sum* of predictions; per-unit errors cancel
unless correlated within a build. Before adding hierarchy (era/media strata),
measure: emit predicted-vs-actual per platform per build (T10 includes this
line). Revisit only if sustained error > ~15%. The 100-sample cap acts as crude
freshness forgetting — defensible; EWMA is a refinement without evidence of
need. **No task.**

## Q9. Knapsack — verdict: no change; reframe the doc

Greedy-by-rating-then-first-fit (the code already continues past oversized
units — it is first-fit-decreasing-by-rating, not truncate-on-first-overflow)
is *domain-correct as a curation policy*: dropping the highest-rated large game
to fit more Σrating of smaller titles is precisely what a curator does not
want. It is a priority policy, not a failed optimizer. Value-density greedy /
2-approx / DP would optimize the wrong objective. **No task** (one-paragraph
reframe belongs in doc 04 when annotated by T10).

## Q10. GC — verdict: defer GC; T1 changes its safety class

Formal liveness: a blob is live iff referenced by (a) any `action_cache` row's
outputs (re-materialization via early cutoff) or (b) any emitted tree —
and (b) is automatically safe on same-fs because emitted files are hardlinks
(the inode survives CAS deletion). Since rows are never evicted today, real GC
= row-eviction policy (needs a `last_hit_at` column, batched updates) + mark
over remaining rows + sweep, mutually excluded from builds by a lock file.
Refcounting duplicates information the rows already hold; mark-and-sweep is
correct and simple.

The important decision: **T1 (verify-on-hit) makes GC mistakes non-poisonous**
— a wrongly-swept blob degrades to a re-execution. That converts GC from a
correctness feature (must be perfect before shipping) into a disk-space feature
(ship when disk pressure exists). Defer it; when built, follow this paragraph.

## Q11. Negotiation — verdict: empty intersection = hard PLAN error (T11)

Silent fallback re-creates the bug-5 class (silent wrong output). Reject loudly
at PLAN with both sides printed. A tuple of format strings is expressive enough
until a *real* veto case appears; preference-algebra machinery is rejected.

## Q12. Cross-platform identity — verdict: defer; smallest honest fix defined

Name-collision dedup conflates work (Doom), release (Doom (SNES)), and dump.
The correct minimal model when needed: an explicit curated `work_id`
equivalence file (`config/curations/`) that overrides name matching, with the
pass trace recording *which rule fired* (curated vs name-heuristic) so
`--explain` is honest. MusicBrainz-style ontology is rejected. **No task now**
— revisit when a real false-dedup is observed.

## Q13. Key governance — verdict: policy ADR, no code

The day a transform needs richer params: encode them as a canonical **string**
(params stay `str→str` forever) and bump that tool's impl-version (T5). The
outer canonical form never changes; invalidation is **tool-scoped** by
construction (the key includes `tool`), never global. One-shot migrations that
rewrite keys are impossible anyway (hashes don't invert) and dual-read adds
permanent complexity for a one-time event. CAS blobs survive any invalidation;
with T9 determinism, re-execution reconverges on identical blobs. This
paragraph **is** the ADR; T5 implements the lever.

## Q14. Property tests — verdict: build the invariant suite (T7)

Audit of the proposed invariants: all four are sound **today** — and note that
"plan is a pure function of (manifest, catalog)" is sound *only because* Q2
rejected online replanning. Hypothesis-style generative testing is rejected
initially (generator cost > value on a fixture this small); metamorphic pairs
on a fixed fixture platform give the same coverage. Full list in T7.

## Q15. Where the Bazel/Nix analogy misleads — verdict: two cargo-culted costs identified

- **Ingest-by-copy** (`shutil.copy2` in `_ingest_to_cas`) is a Bazel-ism
  (sandbox → cache upload) that costs a full extra write of every artifact —
  ~40 GB of pointless I/O for one PS3 game. Bazel needs it (remote cache);
  same-filesystem ROM Farmer does not: rename into CAS. Fixed in T2. This was
  the highest-value single finding of the review.
- **Early cutoff** is load-bearing in Bazel because build graphs are deep;
  chains here are 1–3 actions. It costs nothing extra (the design falls out of
  input-addressing) but should not drive further investment — e.g. do not
  build output-normalization (Q4) to protect a cutoff that saves one
  `mksquashfs` per Xbox game.
- What is genuinely load-bearing and correctly borrowed: CAS dedup, action
  memoization, plan/execute phase separation, `--explain` provenance.
- What has **no** Bazel analogue and is this system's actual novelty: the
  budget pass selecting *what to build* under a size constraint. Guard it with
  domain reasoning (Q9), not build-system lore.

---

# Part II — Work order (prioritized)

## P0 — correctness, small diffs

### T1. Self-healing cache hits
**File:** `src/romfarmer/engine/executor.py` (`_run_action`).
On cache hit, verify every output identity's blob exists in CAS
(`_cas_path` glob, same as `_materialise_from_cas` lookup). Any missing →
log warning, treat as miss, fall through to execution (which re-ingests and
re-stores idempotently).
**Accept:** new test: store row, delete blob, run action → transform runs,
blob restored, no exception. Existing hit-path test still passes (no
transform run when blobs present).

### T2. CAS ingest: race fix + rename-not-copy + scratch sweep
**File:** `src/romfarmer/engine/executor.py`.
1. `_ingest_to_cas`: unique tmp name (`f"{dest.name}.tmp.{os.getpid()}.{token_hex(4)}"`),
   `os.replace(tmp, dest)`, and if `dest.exists()` after a lost race, treat as
   success (content-addressed ⇒ identical).
2. Ingest by **rename**: transform outputs live in scratch and are dead after
   ingest. `os.rename` into CAS when same filesystem; fall back to
   reflink-aware copy (`shutil.copy2` acceptable fallback). **Trap:** the
   executor currently calls `out_path.stat()` *after* ingest — capture size
   *before* the rename.
3. Executor start: sweep stale `scratch_*` dirs under `scratch_base` (killed
   runs leave them; `ScratchDir` only cleans on context exit).
**Accept:** two-process ingest of identical content test (threads suffice);
E2E suite green; size recorded correctly (regression test on `Identity.size`).

### T3. SQLite busy_timeout
**File:** `src/romfarmer/engine/actioncache.py` `__init__`:
`PRAGMA busy_timeout=30000` next to the WAL pragma.
**Accept:** trivial; existing tests green.

### T4. Action param runtime validation + NFC
**File:** `src/romfarmer/ir/actions.py` (`Action.__post_init__`).
Validate all param keys/values are `str` (raise `TypeError` otherwise);
NFC-normalize values (`unicodedata.normalize("NFC", v)`) before freezing.
**Accept:** golden ActionKey test unchanged (proves key preservation);
new tests: int value rejected; NFD input produces same key as NFC.

### T5. Per-tool impl-version registry
**New file:** `src/romfarmer/ir/tool_impl.py` — a frozen
`IMPL_VERSIONS: Mapping[str, int]` for every tool name, **all starting at 1**.
**Files:** `src/romfarmer/planner/lowering/base.py` — `probe_tool_version`
(and the literal `tool_version="1"` sites) append `f"+i{n}"` **only when
n ≥ 2**, so every currently-emitted `tool_version` string is byte-identical to
today (cache preserved).
Freeze transform-side defaults with a loud comment: changing any
`params.get(..., default)` or any subprocess flag **requires** bumping that
tool's entry in `IMPL_VERSIONS` (this is the Q3-hole-1 and Q13 lever; T9 will
be its first user).
**Accept:** golden plans + golden ActionKey hashes unchanged; unit test that a
bumped registry entry changes the emitted `tool_version`.

## P1 — structure

### T6. Phase-seam refactor
**Files:** `src/romfarmer/new_orchestrator.py` (primary),
`src/romfarmer/engine/executor.py`, `src/romfarmer/ir/layout.py` (additive),
`docs/compiler-refactor/02-ir-contracts.md` (document the additions).
Reshape the three private methods into typed phase functions (module-level or
static; not closures over `self`):

```python
run_catalog(resolved, *, source_dir, dat_file, kb) -> Catalog
run_plan(catalog, manifest, *, cost_model, kb) -> PlannedPlatform      # frozen: catalog + BuildPlan + traces
run_execute(planned: PlannedPlatform, *, env: ExecEnv) -> ExecutedPlatform  # LayoutPlan + ExecutionReport
run_emit(executed, *, profile: ConcreteTargetProfile, output_dir) -> None
```

Hard rules (these are the point — reject the refactor if any is violated):
1. `run_execute` takes **no** source paths and **no** `ResolvedPlatformConfig`.
   `ExecEnv` = cas_dir, scratch_base, db_path, transforms, dry_run.
2. Executor returns decl-paired outputs: additive
   `MaterializedOutput(decl: ArtifactDecl, identity: Identity)`; the
   decl↔identity zip is deleted from the orchestrator.
3. `validate_plan(plan, registered_tools)` runs before EXECUTE; unknown tool →
   `PlanValidationError` listing all missing tools (bug-3 class dies at PLAN).
4. Profile loading moves to RESOLVE (`from_config`/`_process_platform` setup);
   EMIT receives the object. Delete EMIT's tree-rescan fallback (bug-4 class).
5. Error policy: phases raise `PhaseError(phase, platform, cause)`. The driver
   (`_process_platform`) is the **only** try/except; it marks the platform
   failed in state and continues. Executor catches per-unit, continues, and
   reports `ExecutionReport(failed_units=[(unit_id, reason)])`; a failed unit
   contributes no layout entries (multi-disc atomicity preserved).
6. The E2E catalog-identity spy test must survive unmodified in spirit:
   `run_execute` consumes the exact `PlannedPlatform` object from `run_plan`.
**Accept:** all E2E tests green without modification of their assertions;
one failed unit no longer skips its platform (new test); import-linter still
4/4 (add a contract if phases move to a new module).

### T7. Invariant test suite
**New file:** `tests/test_invariants.py`, using the existing E2E fixture
platform. Invariants (each is one test, no mocks on phase functions):
1. Second identical build executes **zero** transforms (count via
   telemetry_cb).
2. `run_plan` is deterministic: two calls on the same (manifest, catalog) →
   identical serialized plans.
3. No output filename matches `^[0-9a-f]{64}` (CAS-name leak).
4. Union: outputs of build(A∪B) ≡ outputs of build(A) ∪ build(B) on disjoint
   fixtures.
5. No duplicate logical name / no duplicate inode among top-level outputs
   (bug-6 class).
6. Gamelist emitted iff the profile declares it (bug-5 class).
**Accept:** suite runs < 30 s; all pass; each test's docstring names the
review bug class it guards.

### T8. CATALOG file-digest cache
**Files:** `src/romfarmer/analysis/catalog_builder.py`,
`src/romfarmer/engine/actioncache.py` or a sibling module for the table
(keep the sole-writer doctrine: a new `file_digest_cache` table, writer =
catalog builder only).
Schema: `path PK, size, mtime_ns, inode, sha256, md5, zip_json`. Hit requires
all three of (size, mtime_ns, inode). Racy guard: re-hash when mtime_ns falls
within the scan's start second. Lazy prune of dead paths. `--verify-catalog`
CLI flag forces full re-hash.
**Accept:** second CATALOG of an unchanged tree does zero full-file hashing
(test with a counter/monkeypatched hasher); touched/replaced/renamed file
re-hashes; golden catalog identical either path.

## P2 — hygiene

### T9. Determinism: pin env + flags + doctor harness
**Files:** `src/romfarmer/engine/transforms/*.py`, new
`src/romfarmer/cli/doctor.py` (or extend existing doctor if present).
1. All transform subprocess calls get a pinned env:
   `LC_ALL=C, TZ=UTC, SOURCE_DATE_EPOCH=0` overlaid on a minimal PATH-bearing
   env.
2. `7z`: add `-mtm=off`, fixed `-mmt=4`; delete dead `_ZIP_TIMESTAMP` or wire
   it. `mksquashfs`: add `-mkfs-time 0 -all-time 0 -all-root -no-xattrs`,
   fixed `-processors 4`.
3. **Bump `IMPL_VERSIONS` for every tool whose flags changed** (T5 lever —
   outputs differ, old rows must miss).
4. `romfarmer doctor --determinism`: run each available transform twice on a
   tiny fixture, compare output sha256s, print a table. The table in Part I
   Q4 is hypothesis; the harness is truth.
**Accept:** doctor reports chdman/xiso/squashfs/7z deterministic on this
machine (or documents which are not); E2E green; impl bumps present.

### T10. Budget stop-early + report + doc annotation
**Files:** `src/romfarmer/engine/executor.py` (guard),
`src/romfarmer/new_orchestrator.py` (report line),
`docs/compiler-refactor/04-edge-case-designs.md` (annotation).
1. Optional `budget_bytes` on the executor: stop launching new units when
   cumulative actual terminal bytes ≥ budget; remaining units reported as
   `budget-stop` in `ExecutionReport` (requires T6's report type; plan units
   should already be rating-descending from the budget pass — verify, else
   sort unit execution order by rating desc).
2. Report predicted vs actual bytes per platform at build end.
3. Annotate doc 04 §3 header: *"Status: deliberately not built — decision
   record in 07-fable5-review.md Q2."*
**Accept:** test: fixture where actuals exceed prediction → executor stops
early, report lists stopped units; no over-run.

### T11. Negotiation: empty intersection fails loudly
**File:** `src/romfarmer/planner/negotiation.py`.
`negotiate_with_profile` raising `FormatNegotiationError` naming platform,
recipe prefs, and profile prefs when the intersection is empty (today's
behavior on empty intersection is unspecified — make it this).
**Accept:** unit test for the error message content; existing negotiation
tests green.

---

## Suggested order

T3 → T1 → T2 → T4 → T5 (P0, each independently committable) →
T6 → T7 (T7 assumes T6 signatures) → T8 → T9 → T10 → T11.

---

# Part III — Explicitly rejected (do not build)

| Item | Why | Decision ref |
|---|---|---|
| `ExecutionSupervisor` / `BudgetLedger` / `PromoteAlternates` / online posterior | Breaks plan-determinism invariant; re-run-with-warm-cache is cheaper than the machinery | Q2 |
| Hierarchical CostModel (era/media strata) | No error evidence yet; observe first (T10 report) | Q8 |
| Knapsack optimizer (density greedy / 2-approx / DP) | Optimizes the wrong objective; rating-priority is curation intent | Q9 |
| GC implementation | Deferred until disk pressure; T1 already de-poisons it; design recorded in Q10 | Q10 |
| Preference-algebra format negotiation | Tuple + loud failure covers reality | Q11 |
| Work/release/recording ontology for dedup | Curated `work_id` override sketch recorded; build on first observed false-dedup | Q12 |
| ActionKey schema-version prefix / dual-read | Tool-scoped invalidation via `tool_version` is strictly simpler | Q13 |
| Hypothesis/generative property testing | Fixture metamorphic pairs give the coverage at a fraction of the cost | Q14 |
| Output-normalization before hashing (canonicalizing archives post-hoc) | Protects only a shallow early-cutoff; input-addressing already correct | Q4/Q15 |
