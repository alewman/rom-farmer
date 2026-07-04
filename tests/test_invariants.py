"""Pipeline invariant tests (T7, 2026-07-04).

Six metamorphic properties that hold by construction after the T6 phase-seam
refactor.  No mocks on the four phase functions (run_catalog / run_plan /
run_execute / run_emit) — the real pipeline runs on in-process fixtures.

Each test's docstring names the review-bug class it guards against.
"""

from __future__ import annotations

import os
import re
import zipfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from romfarmer.analysis.knowledge import KnowledgeBase
from romfarmer.config.models import CompressionFormat, ExtractionType, SourceConfig
from romfarmer.config.resolver import ResolvedPlatformConfig
from romfarmer.ir.manifest import BuildManifest
from romfarmer.new_orchestrator import (
    ExecEnv,
    PlannedPlatform,
    _build_default_transforms,
    run_catalog,
    run_emit,
    run_execute,
    run_plan,
)
from romfarmer.planner import CostModel
from romfarmer.planner.negotiation import negotiate_format_chain


# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

def _write_zip(directory: Path, name: str, content: bytes) -> Path:
    """Write a minimal ZIP containing one ROM file; return the ZIP path."""
    zp = directory / f"{name}.zip"
    with zipfile.ZipFile(zp, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.writestr(f"{name}.nes", content)
    return zp


def _resolved(source_dir: Path, platform: str = "nes") -> ResolvedPlatformConfig:
    return ResolvedPlatformConfig(
        platform=platform,
        extraction_type=ExtractionType.NONE,
        compression=CompressionFormat.NONE,
        sources=[SourceConfig(path=source_dir)],
    )


def _manifest() -> BuildManifest:
    return BuildManifest(preferred_regions=("USA", "World", "Europe"))


def _kb() -> KnowledgeBase:
    return KnowledgeBase(None)


def _cost_model() -> CostModel:
    return CostModel(size_data_path=None, knowledge_base=_kb())


def _env(base: Path, *, subdir: str = "run") -> ExecEnv:
    """ExecEnv with all dirs under *base / subdir*."""
    root = base / subdir
    cas = root / "cas"
    scratch = root / "scratch"
    out = root / "output"
    db = root / "test.db"
    for d in (cas, scratch, out):
        d.mkdir(parents=True, exist_ok=True)
    return ExecEnv(
        cas_dir=cas,
        scratch_base=scratch,
        db_path=db,
        output_dir=out,
        transforms=_build_default_transforms(),
    )


class _CountingTransform:
    """Wraps a real Transform and counts calls (= cache misses)."""

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.call_count = 0

    @property
    def name(self) -> str:
        return self._inner.name  # type: ignore[attr-defined]

    def run(
        self,
        inputs: list[Path],
        params: Mapping[str, str],
        scratch: Path,
    ) -> list[Path]:
        self.call_count += 1
        return self._inner.run(inputs, params, scratch)  # type: ignore[no-any-return]


def _counting_env(base: Path, *, subdir: str = "run") -> tuple[ExecEnv, dict[str, _CountingTransform]]:
    """Like _env but wraps every transform in a counter.  Shares CAS/DB with *base*."""
    root = base / subdir
    cas = base / "shared_cas"          # shared across runs
    db = base / "shared.db"            # shared action cache
    scratch = root / "scratch"
    out = root / "output"
    for d in (cas, scratch, out):
        d.mkdir(parents=True, exist_ok=True)

    counters = {
        name: _CountingTransform(impl)
        for name, impl in _build_default_transforms().items()
    }
    env = ExecEnv(
        cas_dir=cas,
        scratch_base=scratch,
        db_path=db,
        output_dir=out,
        transforms=dict(counters),  # type: ignore[arg-type]
    )
    return env, counters


# ─────────────────────────────────────────────────────────────────────────────
# Invariant 1 — second identical build executes zero transforms
# ─────────────────────────────────────────────────────────────────────────────

class TestSecondRunZeroTransforms:
    """Guards: action-cache early-cutoff correctness.

    If this fails the action cache is not being consulted on the second run,
    or ActionKey computation changed between runs (cache thrash).
    Review-bug class: any regression to the content-addressing invariant.
    """

    def test_second_run_executes_zero_transforms(self, tmp_path: Path) -> None:
        src = tmp_path / "source"
        src.mkdir()
        _write_zip(src, "Game Alpha (USA)", b"alpha-bytes-unique-1")
        _write_zip(src, "Super Mario Bros (USA)", b"smb-bytes-unique-2")

        resolved = _resolved(src)
        kb = _kb()
        manifest = _manifest()
        chain = negotiate_format_chain(resolved)
        catalog = run_catalog(resolved, source_dir=src, dat_file=None, kb=kb)
        planned = run_plan(
            catalog, manifest, cost_model=_cost_model(), kb=kb, chain=chain
        )
        assert planned.build_plan.units, "fixture must produce at least one unit"

        # ── First run: populate CAS + action cache ────────────────────
        env1, counters1 = _counting_env(tmp_path, subdir="run1")
        run_execute(planned, env=env1)
        first_count = sum(c.call_count for c in counters1.values())
        assert first_count > 0, "First run must execute at least one transform"

        # ── Second run: same plan, same CAS/DB → all cache hits ───────
        env2, counters2 = _counting_env(tmp_path, subdir="run2")
        run_execute(planned, env=env2)
        second_count = sum(c.call_count for c in counters2.values())

        assert second_count == 0, (
            f"Second identical run must execute zero transforms (got {second_count}). "
            "Content-addressing / early-cutoff is broken."
        )


# ─────────────────────────────────────────────────────────────────────────────
# Invariant 2 — run_plan is deterministic
# ─────────────────────────────────────────────────────────────────────────────

class TestPlanDeterminism:
    """Guards: plan is a pure function of (manifest, catalog).

    If this fails, run_plan has hidden state (e.g. wall-clock time, random
    ordering) that would break the plan-determinism invariant and invalidate
    the Q14 property tests.
    Review-bug class: non-determinism in the PLAN phase.
    """

    def test_two_calls_produce_identical_buildplan(self, tmp_path: Path) -> None:
        src = tmp_path / "source"
        src.mkdir()
        _write_zip(src, "Contra (USA)", b"contra-bytes")
        _write_zip(src, "Contra (Europe)", b"contra-eur-bytes")
        _write_zip(src, "Zelda (USA)", b"zelda-bytes")

        resolved = _resolved(src)
        kb = _kb()
        manifest = _manifest()
        chain = negotiate_format_chain(resolved)
        cost_model = _cost_model()

        catalog = run_catalog(resolved, source_dir=src, dat_file=None, kb=kb)

        plan_a = run_plan(catalog, manifest, cost_model=cost_model, kb=kb, chain=chain)
        plan_b = run_plan(catalog, manifest, cost_model=cost_model, kb=kb, chain=chain)

        assert plan_a.build_plan == plan_b.build_plan, (
            "run_plan returned different BuildPlans on two identical calls. "
            "The PLAN phase has hidden state or non-determinism."
        )
        assert len(plan_a.build_plan.units) > 0, "fixture must produce at least one unit"


# ─────────────────────────────────────────────────────────────────────────────
# Invariant 3 — no CAS-hash filenames in output tree
# ─────────────────────────────────────────────────────────────────────────────

class TestNoHashFilenames:
    """Guards: (decl, identity) zip lives in run_execute only.

    If this fails, run_execute is materialising artifacts under their CAS
    sha256 hash name instead of ArtifactDecl.logical_name.
    Review-bug class: bug-2 (CAS-hash names in output).
    """

    _HASH_NAME_RE = re.compile(r"^[0-9a-f]{32,64}(\.\w+)?$")

    def test_all_output_filenames_are_logical(self, tmp_path: Path) -> None:
        src = tmp_path / "source"
        src.mkdir()
        _write_zip(src, "Final Fantasy VI (USA)", b"ff6-bytes")
        _write_zip(src, "Chrono Trigger (USA)", b"ct-bytes")

        resolved = _resolved(src)
        kb = _kb()
        chain = negotiate_format_chain(resolved)
        catalog = run_catalog(resolved, source_dir=src, dat_file=None, kb=kb)
        planned = run_plan(
            catalog, _manifest(), cost_model=_cost_model(), kb=kb, chain=chain
        )

        env = _env(tmp_path)
        run_execute(planned, env=env)

        output_files = list(env.output_dir.rglob("*"))
        assert output_files, "run_execute must materialise at least one file"

        for path in output_files:
            if path.is_file():
                assert not self._HASH_NAME_RE.match(path.name), (
                    f"File '{path.name}' looks like a CAS hash name. "
                    "run_execute must use ArtifactDecl.logical_name."
                )


# ─────────────────────────────────────────────────────────────────────────────
# Invariant 4 — union build ≡ union of outputs (compositional)
# ─────────────────────────────────────────────────────────────────────────────

class TestUnionCompositionality:
    """Guards: the pipeline is compositional — build(A∪B) = build(A) ∪ build(B).

    Uses two disjoint source sets (distinct game names, no 1G1R interaction).
    If this fails, the CATALOG, PLAN, or EXECUTE phase has a cross-game
    dependency that violates the independence assumption.
    Review-bug class: global state leak between game units.
    """

    def _run_and_collect(self, src: Path, base: Path, label: str) -> set[str]:
        resolved = _resolved(src)
        kb = _kb()
        chain = negotiate_format_chain(resolved)
        catalog = run_catalog(resolved, source_dir=src, dat_file=None, kb=kb)
        planned = run_plan(
            catalog, _manifest(), cost_model=_cost_model(), kb=kb, chain=chain
        )
        env = _env(base, subdir=label)
        run_execute(planned, env=env)
        return {f.name for f in env.output_dir.rglob("*") if f.is_file()}

    def test_union_build_equals_union_of_single_builds(
        self, tmp_path: Path
    ) -> None:
        # Set A: one game
        src_a = tmp_path / "src_a"
        src_a.mkdir()
        _write_zip(src_a, "Metroid (USA)", b"metroid-bytes")

        # Set B: different game
        src_b = tmp_path / "src_b"
        src_b.mkdir()
        _write_zip(src_b, "Castlevania (USA)", b"cv-bytes")

        # Set A∪B: both games in one source dir
        src_ab = tmp_path / "src_ab"
        src_ab.mkdir()
        _write_zip(src_ab, "Metroid (USA)", b"metroid-bytes")
        _write_zip(src_ab, "Castlevania (USA)", b"cv-bytes")

        names_a = self._run_and_collect(src_a, tmp_path, "build_a")
        names_b = self._run_and_collect(src_b, tmp_path, "build_b")
        names_ab = self._run_and_collect(src_ab, tmp_path, "build_ab")

        expected = names_a | names_b
        assert names_ab == expected, (
            f"build(A∪B)={names_ab!r} ≠ build(A)∪build(B)={expected!r}. "
            "The pipeline has a cross-game dependency."
        )


# ─────────────────────────────────────────────────────────────────────────────
# Invariant 5 — no duplicate filenames or inodes in output tree
# ─────────────────────────────────────────────────────────────────────────────

class TestNoDuplicateOutputs:
    """Guards: Materializer move=True leaves no duplicates after letter-subdir org.

    If this fails, the Materializer is not removing top-level originals after
    moving files into letter subdirectories, causing each ROM to appear twice.
    Review-bug class: bug-6 (Materializer hardlink duplicates).
    """

    def test_no_duplicate_filenames(self, tmp_path: Path) -> None:
        src = tmp_path / "source"
        src.mkdir()
        # Use names starting with different letters to exercise letter-org
        _write_zip(src, "Contra (USA)", b"contra-bytes")
        _write_zip(src, "Mega Man 2 (USA)", b"mm2-bytes")
        _write_zip(src, "Super Mario Bros (USA)", b"smb-bytes")

        resolved = _resolved(src)
        kb = _kb()
        chain = negotiate_format_chain(resolved)
        catalog = run_catalog(resolved, source_dir=src, dat_file=None, kb=kb)
        planned = run_plan(
            catalog, _manifest(), cost_model=_cost_model(), kb=kb, chain=chain
        )
        env = _env(tmp_path)
        executed = run_execute(planned, env=env)

        # Run EMIT with a 'rich' style profile so letter subdirs are created
        mock_profile = MagicMock()
        mock_profile.organisation_style = "rich"
        mock_profile.metadata_enabled = False
        run_emit(executed, profile=mock_profile, output_dir=env.output_dir)

        all_files = list(env.output_dir.rglob("*"))
        names = [f.name for f in all_files if f.is_file()]
        from collections import Counter
        dups = {n: c for n, c in Counter(names).items() if c > 1}
        assert not dups, (
            f"Duplicate filenames found after EMIT: {dups}. "
            "Materializer move=True must remove top-level originals."
        )

    def test_no_duplicate_inodes(self, tmp_path: Path) -> None:
        """No two output files share an inode (each logical artifact appears once)."""
        src = tmp_path / "source"
        src.mkdir()
        _write_zip(src, "Contra (USA)", b"contra-bytes-inode")
        _write_zip(src, "Gradius (USA)", b"gradius-bytes-inode")

        resolved = _resolved(src)
        kb = _kb()
        chain = negotiate_format_chain(resolved)
        catalog = run_catalog(resolved, source_dir=src, dat_file=None, kb=kb)
        planned = run_plan(
            catalog, _manifest(), cost_model=_cost_model(), kb=kb, chain=chain
        )
        env = _env(tmp_path)
        run_execute(planned, env=env)

        all_files = [f for f in env.output_dir.rglob("*") if f.is_file()]
        inodes = [os.stat(f).st_ino for f in all_files]
        from collections import Counter
        dup_inodes = {i: c for i, c in Counter(inodes).items() if c > 1}
        assert not dup_inodes, (
            f"Duplicate inodes found in output tree: {len(dup_inodes)} inode(s) "
            "referenced by multiple files. Each logical artifact must appear once."
        )


# ─────────────────────────────────────────────────────────────────────────────
# Invariant 6 — gamelist emitted iff profile declares metadata_enabled
# ─────────────────────────────────────────────────────────────────────────────

class TestGamelistEmittedIffProfileDeclares:
    """Guards: profile controls gamelist generation (not hardcoded or absent).

    If this fails, either gamelist.xml is always written (profile ignored)
    or never written (metadata_enabled check broken).
    Review-bug class: bug-5 (wrong target-profile key → metadata never generated).
    """

    def _run_full_pipeline(
        self,
        src: Path,
        tmp_path: Path,
        label: str,
        profile: Any,
    ) -> Path:
        """Run CATALOG→PLAN→EXECUTE→EMIT; return the output_dir."""
        resolved = _resolved(src)
        kb = _kb()
        chain = negotiate_format_chain(resolved)
        catalog = run_catalog(resolved, source_dir=src, dat_file=None, kb=kb)
        planned = run_plan(
            catalog, _manifest(), cost_model=_cost_model(), kb=kb, chain=chain
        )
        env = _env(tmp_path, subdir=label)
        executed = run_execute(planned, env=env)
        run_emit(executed, profile=profile, output_dir=env.output_dir)
        return env.output_dir

    def _make_src(self, base: Path, label: str) -> Path:
        src = base / f"src_{label}"
        src.mkdir(parents=True)
        _write_zip(src, "Contra (USA)", b"contra-for-gamelist-test")
        return src

    def test_gamelist_created_when_metadata_enabled(
        self, tmp_path: Path
    ) -> None:
        src = self._make_src(tmp_path, "with_meta")
        profile = MagicMock()
        profile.metadata_enabled = True
        profile.organisation_style = "flat"

        out = self._run_full_pipeline(src, tmp_path, "with_meta", profile)
        gamelist = out / "gamelist.xml"
        assert gamelist.exists(), (
            "gamelist.xml must be created when profile.metadata_enabled=True. "
            "Bug-5: profile key was wrong → metadata_enabled never seen."
        )

    def test_gamelist_absent_when_metadata_disabled(
        self, tmp_path: Path
    ) -> None:
        src = self._make_src(tmp_path, "no_meta")
        profile = MagicMock()
        profile.metadata_enabled = False
        profile.organisation_style = "flat"

        out = self._run_full_pipeline(src, tmp_path, "no_meta", profile)
        gamelist = out / "gamelist.xml"
        assert not gamelist.exists(), (
            "gamelist.xml must NOT be created when profile.metadata_enabled=False."
        )

    def test_gamelist_absent_when_no_profile(self, tmp_path: Path) -> None:
        src = self._make_src(tmp_path, "null_profile")
        out = self._run_full_pipeline(src, tmp_path, "null_profile", profile=None)
        gamelist = out / "gamelist.xml"
        assert not gamelist.exists(), (
            "gamelist.xml must NOT be created when profile=None."
        )
