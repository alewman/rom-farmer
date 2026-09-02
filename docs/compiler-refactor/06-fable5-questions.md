# 06 — Questions for Fable 5

**Session date:** 2026-07-04
**Status of the codebase:** All 5 refactor phases merged. 767 tests pass, mypy
strict clean, 4/4 import-linter contracts green. The compiler
(`RESOLVE → CATALOG → PLAN → EXECUTE → EMIT`) is live and the legacy `stages/`
package is deleted.
**Purpose:** A curated question set for a principal-architect session with
Fable 5. These are the questions where broad reasoning and cross-domain
knowledge earn their keep — not lookups.

---

## How to read this

The questions are ordered by leverage, not by topic. Each is tagged:

- **[JUDGMENT]** — an architectural should-we / which-way call. This is what a
  strong reasoning model is uniquely good at.
- **[CORRECTNESS]** — a soundness question where a wrong answer is a latent bug.
- **[QUALITY]** — a scaling or robustness question; wrong answer = a cliff, not a
  crash.

The **Appendix** at the bottom records facts verified against the source on
2026-07-04 so Fable 5 doesn't have to re-derive them. Where a design doc
describes something that does **not** exist in code, it is flagged there — read
the appendix before answering Tier 1.

---

## Tier 1 — Lead with these

### Q1. The phase-boundary seam — make it impossible to wire wrong. [JUDGMENT]

Every one of the 6 bugs found in the 2026-07-04 architect review lived in the
**orchestrator glue** — the three private methods `_run_new_plan_path`,
`_run_execute_path`, `_run_emit_path` on `NewBuildOrchestrator` — not in the
pure IR/engine/passes/lowering layers, which were implemented faithfully. The
bugs were all wiring mistakes at the phase boundary: catalog rebuilt instead of
passed through; CAS-hash names instead of logical names; wrong target-profile
key.

The five phases are currently composed as **method calls on a mutable
orchestrator** that reads/writes `self.state` and passes objects between
methods by hand.

> **Is a method-call seam the right shape?** Should the five phases instead be
> composed as typed pure functions — `emit ∘ execute ∘ plan ∘ catalog ∘ resolve`
> — where the orchestrator is structurally unable to substitute the wrong object,
> re-derive an artifact a phase already produced, or smuggle state between
> phases? What is the minimal type-level or structural change that would have
> made all 6 review bugs *unrepresentable* rather than merely *tested-for*?

Consider the tradeoff against Python's ergonomics and the need for the
orchestrator to own cross-cutting concerns (logging, state save, budget
tracking, resume).

### Q2. The budget feedback loop is designed but unbuilt — decide its fate. [JUDGMENT]

`docs/compiler-refactor/04-edge-case-designs.md` §3 ("the plan is a policy, not
a promise") specifies an `ExecutionSupervisor` + `BudgetLedger` + rating-
descending execution + pure in-memory tail-replan + `PromoteAlternates`, with an
online CostModel posterior that updates mid-build. **None of this exists in the
code** (see Appendix). The budget pass is a single-shot greedy select at PLAN
time; there is no live ledger, no mid-build re-plan, no online posterior update.

Before anyone optimizes this machinery:

> **Is the feedback loop worth building at all** for a single-user, single-
> machine system where a build can simply be re-run? What is the real cost of
> the naive alternative (predict once with a deliberately pessimistic prior,
> accept the occasional under-fill or over-run, let CAS absorb the sunk work)?
> If it *is* worth building, what is the smallest version that captures 80% of
> the value — is it the full supervisor, or just "update the posterior after
> each unit and stop early on breach"?

### Q3. ActionKey canonicalization soundness. [CORRECTNESS]

The `ActionKey` is `sha256(canonical JSON of (tool, tool_version, params,
resolved input sha256s))` and is declared **frozen forever** — changing it
invalidates every user's action cache. The canonical form is Python's
`json.dumps(..., sort_keys=True)` (see Appendix for the exact call).

> What are the **necessary and sufficient conditions** for this scheme to be both
> sound (no false hits → silent corruption) and stable (no false misses →
> silent cache thrash)? Specifically audit: float representation in `params`
> (block sizes, ratios), integer vs. string coercion, Unicode normalization of
> logical names, `None`/absent-key ambiguity, and nested-dict key ordering.
> Where do Nix (input-addressed derivations) and Bazel (action digests) each
> harden this, and which of their protections is missing here?

### Q4. Determinism auditing — the load-bearing assumption. [CORRECTNESS]

The README thesis names "**deterministic external tools**" as one of the four
pillars that make ROM Farmer "80% of a Bazel/Nix system." The early-cutoff
benefit of content addressing depends on it: identical inputs must produce
byte-identical output sha256s, or downstream `ActionKey`s miss when they
shouldn't and the cache quietly stops paying off.

The transforms shell out to `chdman`, `mksquashfs`, `7z`/`zip`, `extract-xiso`,
`wux`, `ps3dec`, and generate `.m3u` files.

> Which of these tools are actually byte-reproducible, and which embed
> timestamps, thread-count-dependent ordering, or level-nondeterministic output?
> For each non-deterministic tool, what exact flags pin it
> (`SOURCE_DATE_EPOCH`, `-no-exports`, fixed `-processors`, sorted file order,
> etc.)? And where determinism is impossible, what is the right fallback — is
> normalizing the *output* before hashing (e.g. canonicalizing the archive) worth
> it, or should those transforms be excluded from early-cutoff and keyed only on
> inputs?

---

## Tier 2 — Quality cliffs (Sonnet's sharpest picks, kept)

### Q5. Catalog rescanning at scale. [QUALITY]

Resume is now "re-derive the plan + let the action cache skip work," so the
CATALOG phase re-scans source directories on **every** run. For a 100k-file,
500 GB collection, full SHA-256 of every source on every build is prohibitive.
ZIP central-directory identity is already extracted cheaply; full sha256 is the
expensive part.

> What is the correct memoization strategy for CATALOG that stays correct under
> source mutation (added / replaced / deleted / renamed files)? Is
> `(inode, size, mtime)` a sound fast-path key for "sha256 unchanged," and under
> exactly what filesystem assumptions does it break (mtime granularity, mtime-
> preserving restores, hardlink/reflink copies, network filesystems)? What does a
> production-grade version look like (cf. Git's index, Bazel's file digest cache)?

### Q6. Concurrent / interleaved builds against one CAS + action cache. [CORRECTNESS]

Two builds (e.g. `1tb-batocera`, `512gb-batocera`) share one CAS tree and one
SQLite DB (`metadata/database/romfarmer.db`, WAL, single connection per process,
`isolation_level=None`). `ActionCache` is the sole writer of `artifact_aliases`.

> What invariants must hold for concurrent or interleaved builds to be safe?
> Under WAL with one writer at a time, can a second build observe a **torn view**
> — an `action_cache` row present but its `artifact_aliases` row not yet
> committed, or vice versa — given that the CAS blob write happens **outside** the
> SQLite transaction (Appendix Q6)? Is there a real crash/interleaving window
> where a build "hits" a cache row and then cannot materialize the blob, and what
> is the minimal protocol (ordering, a `MATERIALIZED` flag, a fsync barrier) that
> closes it?

### Q7. Crash-consistency and partial-build atomicity. [CORRECTNESS]

An `Action` performs: run tool → ingest output into CAS → `record_aliases` →
`store` action-cache row → (telemetry). The SQLite writes are one transaction,
but the **CAS blob ingest is a separate, earlier filesystem operation**
(Appendix Q6/Q7). The executor `raise`s on tool failure; there is no rollback.

> Where exactly are the crash windows, and which failure mode does each produce —
> orphan blob (wasted space, benign) vs. dangling cache row (poison: future
> "hit" that can't materialize)? For a multi-disc `GameUnit` where disc 2 of 3
> fails, is disc 1 left as a valid, independently-cacheable artifact, and does the
> *unit* fail atomically as the multi-disc-atomicity contract requires? What is
> the correct write-ordering + recovery protocol (write-blob-then-row, startup
> orphan sweep, idempotent re-run)?

---

## Tier 3 — Design completeness

### Q8. CostModel estimator quality. [QUALITY]

`CostModel` merges a static prior (`size_data.json` / hardcoded per-platform
ratios) with a Welford running-mean posterior from telemetry, weighted by sample
count up to a cap of 100. Compression ratios within a platform are **not i.i.d.**
— they cluster by era, media type, and mastering.

> Is a flat running mean the right estimator, or does a hierarchical model
> (platform prior → per-era / per-media posterior) materially improve budget
> prediction? What is the convergence behavior of the current merge, and is the
> 100-sample cap defensible?

### Q9. Budget knapsack optimality. [QUALITY]

The budget pass is greedy rating-descending — a fractional-knapsack heuristic
applied to an integral 0-1 problem.

> When is this greedy order provably optimal, and when does it leave significant
> budget unfilled or drop a high-value cluster? Is there a practical improvement
> (a 2-approx, or a bounded-DP) that still satisfies "re-plan must be
> milliseconds, no I/O"? (Depends on the Q2 decision — only relevant if the loop
> is built.)

### Q10. Safe GC for lazy materialization. [CORRECTNESS]

CAS distinguishes `INTERMEDIATE` (GC-eligible) from `TERMINAL` (pinned while a
layout references it) artifacts. Lazy materialization means a blob may be needed
long after the cache row that references it was written.

> What are the formal safety conditions for GC in a content-addressed store where
> an `INTERMEDIATE` blob is reachable only through an action-cache row, and a
> future build may re-materialize it via early cutoff? Reference-counting vs.
> mark-and-sweep vs. time-based eviction — which is correct here, and how does it
> interact with Q6 concurrency?

### Q11. Format-negotiation completeness. [QUALITY]

`negotiate_with_profile` intersects recipe preferences with target-profile
preferences ("default kept if in prefs"). Empty-intersection behavior is
unspecified, and `FormatChain` is a bare tuple of format strings.

> What is the correct complete semantics when recipe and profile don't intersect
> — fall back to recipe, to platform default, or reject loudly? Is a tuple of
> strings expressive enough for real constraints like "prefer CHD, accept ZIP,
> reject uncompressed ISO," or does negotiation need a partial order / preference-
> with-veto model?

### Q12. Cross-platform "same game" identity. [JUDGMENT]

The generation pass dedups across platforms via a normalized-name reference on
`GameUnit`. But a remaster, a port, and an emulation wrapper share a normalized
name and are *not* the same artifact.

> What is the correct, auditable definition of "same game" across platforms for
> dedup? How do MusicBrainz / Discogs model work-vs-release-vs-recording, and is
> there a clean extension to `GameUnit` that makes the dedup rule explicit rather
> than name-collision-driven?

### Q13. ActionKey migration governance. [JUDGMENT]

The canonical form is "frozen forever," yet the day will come when a new
transform needs a param type the current JSON schema can't represent.

> What is the right governance model for that day? Compare Bazel (versioned
> action digests), Nix (output-addressed / CA derivations), Buck2 (dep files).
> For a single-user system where a one-shot migration script is feasible, what is
> the least-risk path — schema-version prefix in the key, a rebuild-on-bump, or a
> lazy dual-read?

### Q14. Metamorphic / property-test strategy for the seam. [QUALITY]

The review's fix for the glue bugs was hand-written E2E tests. The deeper need
is invariants that hold *by construction*.

> What property/metamorphic tests would have caught all 6 review bugs without
> enumerating them? Candidates to validate or refine: "build twice ⇒ second run
> runs zero transforms"; "plan is a pure deterministic function of
> `(manifest, catalog)`"; "`CAS(build A∪B) = CAS(A) ∪ CAS(B)`"; "output tree
> filenames are logical names, never CAS hashes." Which of these are actually
> sound to assert, and what is the minimal generator set to make them cheap?

### Q15. Interrogate the "80% of Bazel/Nix" framing itself. [JUDGMENT]

The whole architecture is explicitly modeled on Bazel/Nix.

> Where does that analogy **actively mislead**? Bazel/Nix assume hermetic, side-
> effect-free actions over small artifacts and have no concept of a storage
> budget; ROM Farmer's actions are multi-GB binaries, wrap non-hermetic external
> tools, and are *driven* by a budget constraint that shapes selection. Which
> borrowed decisions are load-bearing, and which are cargo-culted from a domain
> whose assumptions don't hold here?

---

## Appendix — facts verified against source (2026-07-04)

Read this before answering Tier 1. Design docs describe the *intended*
architecture; these are the *actual* code facts.

- **The budget feedback loop (doc 04 §3) is unimplemented.** Grep across
  `src/romfarmer/` for `ExecutionSupervisor`, `BudgetLedger`, `LedgerState`,
  `on_unit_complete`, `PromoteAlternates`, `SelectionResult.alternates`,
  `replan`, `breach`, and online `posterior` update returns **nothing** in the
  planner/engine. `planner/passes/budget.py` is a one-shot greedy
  rating-descending select run at PLAN time. `utils/storage_budget.py` has a
  `record_actual` used only for post-hoc size logging in the orchestrator, not a
  live ledger.

- **All 6 review bugs were in the orchestrator glue**, not the pure layers. See
  repo memory `/memories/repo/architecture-refactor.md` "ARCHITECT REVIEW"
  section and commit `dd14c50`. The pure IR/engine/passes/lowering code was
  faithful.

- **ActionKey canonical form:** `ir/actions.py`, `resolve_key` →
  `sha256(json.dumps(canonical, sort_keys=True).encode())`, over
  `(tool, tool_version, params, [resolved input sha256s in input order])`.
  Declared frozen; a golden test locks the hashes.

- **ActionCache storage:** `engine/actioncache.py`. Raw `sqlite3`, single
  connection, `check_same_thread=False`, `isolation_level=None` (autocommit),
  `PRAGMA journal_mode=WAL`, `PRAGMA foreign_keys=ON`. Tables `action_cache(key
  PK, outputs_json, tool, tool_version, created_at)` and `artifact_aliases(sha256
  UNIQUE, md5, zip_crc32, zip_size, zip_member)`. `store()` writes the cache row
  and all alias rows inside one `with self._conn:` transaction. Sole writer of
  `artifact_aliases`. This is the §3.9 MD5-vs-CRC32 fix.

- **CAS blob ingest is NOT in the SQLite transaction.** The executor
  (`engine/executor.py`) ingests the output into CAS as a filesystem operation
  *before* calling `store()`/`record_aliases()`. There is no cross-resource
  transaction spanning "blob on disk" + "row in DB." The executor `raise`s
  (`RuntimeError`, `ValueError`, `FileNotFoundError`) on failure with no
  rollback. This is the basis of Q6 and Q7.

- **CostModel:** `planner/costmodel.py`. Hardcoded pessimistic priors +
  `size_data.json`, merged with `KnowledgeBase` telemetry via a sample-count-
  weighted running mean, `_TELEMETRY_CAP = 100`. `UnknownPlatformError` on
  unknown platform (no silent fallback).

- **DB location:** `metadata/database/romfarmer.db`, shared with the legacy
  `rom_cache` / `rom_transformation` tables and the backfill target of
  `scripts/migrate_action_cache.py`.

- **Known test-suite caveat:** `tests/test_compression_ratio.py` is script-style
  and breaks full-suite collection when the DB is absent; full runs use
  `--ignore=tests/test_compression_ratio.py`.
