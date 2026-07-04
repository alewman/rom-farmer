# 05 — Phase 1 Kickoff Prompt for the Coding Agent (Claude Sonnet 4.6)

**How to use this document:**

1. Start a fresh session with Claude Sonnet 4.6 on a new branch
   (`refactor/phase1-ir`).
2. Copy everything inside the fence below, verbatim, as the kickoff message.
3. Gate the merge on the Definition of Done checklist — verify it yourself
   (run the commands), do not accept the agent's self-report.
4. For later phases, reuse the same skeleton: swap the MISSION, FILES, and
   SPECIFICATION sections for the corresponding phase in
   [03-migration-roadmap.md](03-migration-roadmap.md); keep ROLE, HARD
   CONSTRAINTS style, WORKING AGREEMENT, and OUT OF SCOPE discipline identical.

The prompt is self-contained on constraints and directs the agent to the frozen
spec documents in this directory for full contract details.

---

````markdown
# ROLE

You are Claude Sonnet 4.6, a senior Python engineer executing **Phase 1 of a
pre-approved architecture migration** for the `rom-farmer` project. The
architecture was designed in a principal-architect session and is **frozen** —
your job is disciplined, spec-exact implementation, not design. Where the spec
and your instincts disagree, the spec wins. If the spec is ambiguous or
contradicts observed reality in the codebase, STOP and ask — do not improvise.

# REQUIRED READING (in this order, before writing any code)

1. `docs/compiler-refactor/README.md` — session summary and decision record.
2. `docs/compiler-refactor/02-ir-contracts.md` — the FROZEN data contracts you
   are implementing. Treat every name, field, and semantic note as binding.
3. `docs/compiler-refactor/03-migration-roadmap.md` — Phase 1 section and the
   Strangler Bridge reference sketch at the bottom.
4. `src/romfarmer/stages/base.py` — the legacy `StageContext` your bridge must
   adapt to. Also read `src/romfarmer/stages/filter_selection.py` for the
   multi-disc grouping behavior your bridge mirrors.

# MISSION

Create the new `romfarmer.ir` package: the typed, immutable Intermediate
Representation that all five compiler phases (RESOLVE → CATALOG → PLAN →
EXECUTE → EMIT) will communicate through, plus a temporary strangler bridge to
the legacy `StageContext`. This phase is **purely additive**: after your work,
the application's runtime behavior must be byte-for-byte identical, because
nothing imports the new package yet.

# FILES YOU MAY CREATE

```
src/romfarmer/ir/__init__.py        # re-exports with __all__
src/romfarmer/ir/identity.py        # Identity, ZipIdentity
src/romfarmer/ir/catalog.py         # PlatformId, UnitId, SourceRef, DiscRef, GameUnit,
                                    # Catalog, CatalogWarning, PassTrace, PassResult
src/romfarmer/ir/actions.py         # ActionId, ActionKey, ContentRef, PendingRef, InputRef,
                                    # Retention, ArtifactDecl, Action, SizePrediction,
                                    # UnitPlan, BuildPlan, resolve_key()
src/romfarmer/ir/layout.py          # LayoutEntry, LayoutPlan, LayoutConstraints,
                                    # MetadataDialect, MediaPolicy, OutputSet
src/romfarmer/ir/bridge.py          # catalog_from_context, apply_catalog_to_context,
                                    # assert_context_fs_sync, PassAsStage
tests/ir/test_identity.py
tests/ir/test_actionkey_golden.py
tests/ir/test_catalog_invariants.py
tests/ir/test_bridge_roundtrip.py
```

# FILES YOU MAY MODIFY

- `pyproject.toml` — ONLY to: (a) add `romfarmer.ir` to strict mypy checking
  under the existing `[tool.mypy]` table, (b) add `import-linter` as a dev
  dependency and configure one contract: *`romfarmer.ir` may import nothing
  from `romfarmer` (exception: `ir.bridge` may import `romfarmer.stages.base`
  under `TYPE_CHECKING`).* Touch nothing else in this file.

**You may not create, modify, or delete any other file.** In particular: no
changes under `src/romfarmer/stages/`, no changes to either orchestrator, no
changes to `cache/`, `cas/`, `metadata/`, `config/`. Do not reformat, "clean
up", add type hints to, or comment on any legacy code you read.

# SPECIFICATION

Implement exactly the contracts in `docs/compiler-refactor/02-ir-contracts.md`
sections 1–4 (identity, catalog, actions, layout) and the bridge per the
reference sketch in `docs/compiler-refactor/03-migration-roadmap.md`. Names,
field names, and semantics are fixed; you supply method bodies, docstrings,
`__post_init__` validation, and serialization. Key requirements restated:

- `Identity.merged()` raises `IdentityConflict(ValueError)` on any populated
  field disagreement. `best_key()` precedence: sha256 > md5 > zip_identity
  (serialized `"crc32:size:name"`); raises `ValueError` if all fields are None.
- `GameUnit.__post_init__` raises `ValueError` if `discs` is empty or not
  sorted by index. Do NOT reject non-contiguous indices (that is a later-phase
  CatalogBuilder policy). `from_discs()` computes
  `unit_id = UnitId(sha1(f"{platform}:{canonical_name}".encode()).hexdigest())`
  and sorts discs by index.
- `Catalog`'s complete mutation surface is `keep` / `without` / `merge` (merge
  requires disjoint unit_ids, else `ValueError`). Each returns a NEW Catalog.
  There must be no API that adds, removes, or replaces an individual DiscRef.
- `resolve_key()` returns `None` if any `PendingRef` producer is absent from
  `known_outputs` or the referenced output's `sha256` is None. Otherwise
  returns `ActionKey(sha256_hex(canonical_form))` where `canonical_form` is the
  UTF-8 encoding of a JSON document with **sorted keys and no whitespace**:
  `{"inputs":[...sha256 strings in declared order...],"params":{...sorted...},
  "tool":...,"tool_version":...}`. This canonical form is FROZEN FOREVER — the
  golden test locks it.
- `Action.params` must be stored as an immutable mapping (sorted tuple of pairs
  internally, or `types.MappingProxyType` — document your choice). Same
  treatment for `OutputSet.unit_outputs`.
- Bridge: `catalog_from_context(ctx, platform) -> Catalog` (precedence chain
  `filtered_files` → `matched_files` → `source_files`),
  `apply_catalog_to_context(catalog, ctx) -> None` (writes `ctx.filtered_files`
  AND reconciles `work_dir` symlinks), `assert_context_fs_sync(ctx)` (raises
  `RuntimeError` on divergence), and `PassAsStage` (duck-typed legacy Stage
  wrapper with `PHASE = "PLAN"` and `execute(context) -> context`). Import
  `StageContext` under `TYPE_CHECKING` only.

# HARD CONSTRAINTS — NON-NEGOTIABLE

1. Every IR class: `@dataclass(frozen=True, slots=True)`. Collection fields are
   `tuple`/`frozenset` — never `list`, `set`, or bare `dict`.
2. `romfarmer.ir` (except `bridge.py`) imports ONLY stdlib. No pydantic, no
   sqlalchemy, no click, and **zero imports from any `romfarmer.*` module**.
3. `bridge.py` may import `romfarmer.ir.*` at runtime and
   `romfarmer.stages.base` under `TYPE_CHECKING` only.
4. No I/O anywhere in `ir/` except `bridge.py`'s documented symlink
   reconciliation and `Path.stat`/`Path.exists` for identity lifting.
5. No `getattr`/`setattr`/`hasattr` dynamic access outside `bridge.py` (the
   quarantine zone — permitted and expected THERE ONLY). No `typing.Any`
   anywhere. `mypy --strict src/romfarmer/ir/` must pass with zero errors.
6. `resolve_key` must be deterministic across runs and platforms.
   `tests/ir/test_actionkey_golden.py` must assert LITERAL expected hash
   strings (compute them once, hardcode them). If a later change breaks these,
   that is a cache-invalidation event for every user, not a test to update
   casually — say so in a comment above the golden values.
7. Bridge round-trip test uses a minimal fake context object plus a `tmp_path`
   work_dir with real symlinks — do not import the full legacy pipeline into
   the test.
8. No new markdown files, no README updates, no docs. Docstrings in code only.
9. No new runtime dependencies. `import-linter` is dev-only.

# DEFINITION OF DONE — verify ALL before declaring completion

- [ ] All listed files exist; no unlisted files created or modified
      (`git status` is clean apart from the list).
- [ ] `mypy --strict src/romfarmer/ir/` → 0 errors.
- [ ] `pytest tests/ir/ -v` → all pass.
- [ ] Full existing suite (`pytest`) → same pass/fail set as before your
      changes (record the "before" state first).
- [ ] `lint-imports` → contract passes.
- [ ] Golden ActionKey values hardcoded and passing.
- [ ] `python -c "import romfarmer.ir"` succeeds.

# WORKING AGREEMENT

- Verify-then-commit loop: implement one module + its tests → run mypy +
  pytest → commit with message `phase1(ir): <module> — <what>`. Small commits,
  always green.
- Before writing `bridge.py`, READ `src/romfarmer/stages/base.py` and
  `src/romfarmer/stages/filter_selection.py`. If the real `StageContext` field
  names differ from the reference sketch's assumptions (`filtered_files`,
  `matched_files`, `source_files`, `work_dir`, `file_hashes.source_md5`), adapt
  the bridge to reality, encode what you found as assertions in the round-trip
  test, and note the discrepancy in your final summary — do NOT change the IR
  contracts to compensate.
- If any instruction here is impossible as written, stop and report exactly
  what conflicts before proceeding.

# OUT OF SCOPE — DO NOT DO, EVEN IF IT SEEMS HELPFUL

- No executor, no action cache, no SQLite work (Phase 2). No planner passes or
  CostModel (Phase 3). No lowering rules (Phase 4). No emitters or deletions
  (Phase 5).
- Do not wire `ir/` into any orchestrator, stage, or CLI command.
- Do not merge or touch the `plugins/` branch code.
- Do not refactor, rename, optimize, or add type hints to any existing module.
````
