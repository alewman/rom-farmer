"""Executor cache tests — Gate 3: second run performs zero Transform invocations.

Tests:
  1. Basic cache hit: executor runs a plan, caches result; second run skips transform.
  2. OutputSet contains terminal-artifact identities.
  3. PendingRef chains resolve correctly through the executor.
  4. Cache populated by one executor re-used by a second executor instance
     (same ActionCache db) — proves cache persistence.
"""

from __future__ import annotations

import shutil
from collections.abc import Mapping
from pathlib import Path

import pytest

from romfarmer.engine.actioncache import ActionCache
from romfarmer.engine.executor import Executor
from romfarmer.engine.transforms.base import Transform
from romfarmer.ir.actions import (
    Action,
    ActionId,
    ActionKey,
    ArtifactDecl,
    BuildPlan,
    ContentRef,
    PendingRef,
    Retention,
    SizePrediction,
    UnitPlan,
)
from romfarmer.ir.catalog import (
    DiscRef,
    GameUnit,
    PlatformId,
    SourceRef,
    UnitId,
)
from romfarmer.ir.identity import Identity


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_unit(platform: str = "nes", name: str = "TestGame") -> GameUnit:
    disc = DiscRef(
        index=1,
        source=SourceRef(Path("/fake/game.nes"), PlatformId(platform)),
        identity=Identity(size=32),
    )
    return GameUnit.from_discs(PlatformId(platform), name, (disc,))


def _make_prediction() -> SizePrediction:
    return SizePrediction(ratio=0.85, source="prior:test", confidence=0.5)


class CountingTransform:
    """A Transform that copies its first input to scratch and counts calls."""

    name = "copy"
    call_count: int = 0

    def run(
        self,
        inputs: list[Path],
        params: Mapping[str, str],
        scratch: Path,
    ) -> list[Path]:
        CountingTransform.call_count += 1
        out = scratch / "output.bin"
        shutil.copy2(inputs[0], out)
        return [out]

    @classmethod
    def reset(cls) -> None:
        cls.call_count = 0


class AppendingTransform:
    """Transform that appends a marker byte, so output sha256 ≠ input sha256."""

    name = "append"
    call_count: int = 0

    def run(
        self,
        inputs: list[Path],
        params: Mapping[str, str],
        scratch: Path,
    ) -> list[Path]:
        AppendingTransform.call_count += 1
        out = scratch / "output.bin"
        out.write_bytes(inputs[0].read_bytes() + b"\xAB\xCD")
        return [out]

    @classmethod
    def reset(cls) -> None:
        cls.call_count = 0


@pytest.fixture
def tmp_env(tmp_path: Path):
    """Provide (cas_dir, db_path, source_file) for each test."""
    cas = tmp_path / "cas"
    cas.mkdir()
    db = tmp_path / "romfarmer.db"
    src = tmp_path / "game.nes"
    src.write_bytes(b"\x4e\x45\x53\x1a" + b"\x00" * 28)  # minimal NES header
    CountingTransform.reset()
    return cas, db, src


def _make_plan(src: Path, cas_dir: Path) -> tuple[BuildPlan, str]:
    """Create a minimal BuildPlan referencing *src* as a ContentRef input.

    Returns (plan, sha256_of_src).
    """
    import hashlib
    h = hashlib.sha256()
    h.update(src.read_bytes())
    sha256 = h.hexdigest()

    # Ingest source file into CAS so it's materialisable
    prefix = sha256[:2]
    rest = sha256[2:]
    blob = cas_dir / prefix / (rest + src.suffix)
    blob.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, blob)

    unit = _make_unit()
    action = Action(
        action_id=ActionId("a1"),
        tool="copy",
        tool_version="1.0",
        params={},
        inputs=(ContentRef(sha256=sha256),),
        outputs=(ArtifactDecl("output.bin", "bin", Retention.TERMINAL),),
    )
    unit_plan = UnitPlan(
        unit=unit,
        actions=(action,),
        predicted_output_bytes=32,
        prediction=_make_prediction(),
    )
    return BuildPlan(units=(unit_plan,)), sha256


# ---------------------------------------------------------------------------
# Gate 3 smoke test: second run = zero Transform invocations
# ---------------------------------------------------------------------------

class TestExecutorCacheSmoke:
    def test_first_run_calls_transform(self, tmp_env) -> None:
        cas, db, src = tmp_env
        plan, _ = _make_plan(src, cas)
        with ActionCache(db) as cache:
            ex = Executor(cache, {"copy": CountingTransform()}, cas, cas / "scratch")
            ex.run(plan)
        assert CountingTransform.call_count == 1

    def test_second_run_zero_transforms(self, tmp_env) -> None:
        """Gate 3: second invocation hits ActionCache → zero Transform calls."""
        cas, db, src = tmp_env
        plan, _ = _make_plan(src, cas)

        # First run: populates cache
        with ActionCache(db) as cache:
            ex = Executor(cache, {"copy": CountingTransform()}, cas, cas / "scratch")
            ex.run(plan)
        assert CountingTransform.call_count == 1

        # Second run: must hit cache, never call transform
        CountingTransform.reset()
        with ActionCache(db) as cache:
            ex = Executor(cache, {"copy": CountingTransform()}, cas, cas / "scratch")
            ex.run(plan)
        assert CountingTransform.call_count == 0, (
            "Second run should be a full cache hit — zero Transform invocations"
        )

    def test_cache_hit_across_executor_instances(self, tmp_env) -> None:
        """Cache populated by executor A is reused by executor B (same db)."""
        cas, db, src = tmp_env
        plan, _ = _make_plan(src, cas)

        with ActionCache(db) as cache_a:
            Executor(cache_a, {"copy": CountingTransform()}, cas, cas / "scratch").run(plan)

        CountingTransform.reset()
        with ActionCache(db) as cache_b:
            Executor(cache_b, {"copy": CountingTransform()}, cas, cas / "scratch").run(plan)

        assert CountingTransform.call_count == 0

    def test_output_set_contains_terminal_identities(self, tmp_env) -> None:
        cas, db, src = tmp_env
        plan, _ = _make_plan(src, cas)

        with ActionCache(db) as cache:
            ex = Executor(cache, {"copy": CountingTransform()}, cas, cas / "scratch")
            output_set = ex.run(plan)

        # The plan has one unit; its output should be in unit_outputs
        unit_id = plan.units[0].unit.unit_id
        assert unit_id in output_set.unit_outputs
        identities = output_set.unit_outputs[unit_id]
        assert len(identities) == 1
        assert identities[0].sha256 is not None  # must be complete after execution


class TestExecutorPendingRef:
    def test_pending_ref_chain(self, tmp_env) -> None:
        """Two chained actions: second action's input is the first action's output."""
        cas, db, src = tmp_env
        sha256 = _ingest_source(src, cas)

        unit = _make_unit()
        action1 = Action(
            action_id=ActionId("a1"),
            tool="copy",
            tool_version="1.0",
            params={},
            inputs=(ContentRef(sha256=sha256),),
            outputs=(ArtifactDecl("step1.bin", "bin", Retention.INTERMEDIATE),),
        )
        action2 = Action(
            action_id=ActionId("a2"),
            tool="copy",
            tool_version="1.0",
            params={"step": "2"},       # different params → different ActionKey
            inputs=(PendingRef(producer=ActionId("a1"), output_index=0),),
            outputs=(ArtifactDecl("step2.bin", "bin", Retention.TERMINAL),),
        )
        unit_plan = UnitPlan(
            unit=unit,
            actions=(action1, action2),
            predicted_output_bytes=32,
            prediction=_make_prediction(),
        )
        plan = BuildPlan(units=(unit_plan,))

        with ActionCache(db) as cache:
            ex = Executor(cache, {"copy": CountingTransform()}, cas, cas / "scratch")
            output_set = ex.run(plan)

        assert CountingTransform.call_count == 2
        unit_id = unit.unit_id
        assert unit_id in output_set.unit_outputs
        assert output_set.unit_outputs[unit_id][0].sha256 is not None


def _ingest_source(src: Path, cas_dir: Path) -> str:
    import hashlib
    sha256 = hashlib.sha256(src.read_bytes()).hexdigest()
    blob = cas_dir / sha256[:2] / (sha256[2:] + src.suffix)
    blob.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, blob)
    return sha256


class TestSelfHealingCacheHit:
    """T1: verify-on-hit turns a poisoned cache row into a transparent re-execute."""

    def _make_append_plan(self, src: Path, cas_dir: Path) -> tuple[BuildPlan, str]:
        """Plan using AppendingTransform so output sha256 ≠ input sha256."""
        import hashlib
        sha256 = hashlib.sha256(src.read_bytes()).hexdigest()
        blob = cas_dir / sha256[:2] / (sha256[2:] + src.suffix)
        blob.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, blob)

        unit = _make_unit()
        action = Action(
            action_id=ActionId("a-append"),
            tool="append",
            tool_version="1.0",
            params={"marker": "abcd"},
            inputs=(ContentRef(sha256=sha256),),
            outputs=(ArtifactDecl("output.bin", "bin", Retention.TERMINAL),),
        )
        unit_plan = UnitPlan(
            unit=unit,
            actions=(action,),
            predicted_output_bytes=34,
            prediction=_make_prediction(),
        )
        return BuildPlan(units=(unit_plan,)), sha256

    def test_missing_blob_triggers_reexec(self, tmp_env) -> None:
        """Store a cache row, delete the output blob, run again — transform re-runs."""
        cas, db, src = tmp_env
        plan, _ = self._make_append_plan(src, cas)
        AppendingTransform.reset()

        # First run: populate cache + CAS
        with ActionCache(db) as cache:
            ex = Executor(cache, {"append": AppendingTransform()}, cas, cas / "scratch")
            output_set = ex.run(plan)
        assert AppendingTransform.call_count == 1

        # Delete only the *output* blob (input sha256 ≠ output sha256 here).
        unit_id = plan.units[0].unit.unit_id
        out_sha256 = output_set.unit_outputs[unit_id][0].sha256
        assert out_sha256 is not None
        for blob in (cas / out_sha256[:2]).glob(f"{out_sha256[2:]}*"):
            blob.unlink()

        # Second run: cache row present but output blob gone → re-execute, no exception
        AppendingTransform.reset()
        with ActionCache(db) as cache:
            ex = Executor(cache, {"append": AppendingTransform()}, cas, cas / "scratch")
            output_set = ex.run(plan)

        assert AppendingTransform.call_count == 1, (
            "Transform should re-run when cached blob is missing"
        )
        assert output_set.unit_outputs[unit_id][0].sha256 is not None

    def test_intact_blob_still_hits(self, tmp_env) -> None:
        """Normal case: blob present → hit, zero re-executions."""
        cas, db, src = tmp_env
        plan, _ = _make_plan(src, cas)

        with ActionCache(db) as cache:
            Executor(cache, {"copy": CountingTransform()}, cas, cas / "scratch").run(plan)

        CountingTransform.reset()
        with ActionCache(db) as cache:
            Executor(cache, {"copy": CountingTransform()}, cas, cas / "scratch").run(plan)

        assert CountingTransform.call_count == 0


class TestBudgetStopEarly:
    """T10: executor stops launching units when cumulative bytes reach budget_bytes."""

    def _make_multi_unit_plan(
        self, tmp_path: Path, cas_dir: Path
    ) -> tuple[BuildPlan, list[str]]:
        """Three-unit plan where each unit produces small terminal output."""
        import hashlib

        src_dir = tmp_path / "multi_src"
        src_dir.mkdir(exist_ok=True)
        unit_plans = []

        for i, content in enumerate([b"unit-1-data", b"unit-2-data", b"unit-3-data"], 1):
            unit_src = src_dir / f"unit{i}.bin"
            unit_src.write_bytes(content)
            sha256 = hashlib.sha256(content).hexdigest()
            # Ingest into CAS
            blob = cas_dir / sha256[:2] / (sha256[2:] + unit_src.suffix)
            blob.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(unit_src, blob)

            unit = _make_unit(name=f"Game {i}")
            action = Action(
                action_id=ActionId(f"a{i}"),
                tool="copy",
                tool_version="1.0",
                params={"unit": str(i)},
                inputs=(ContentRef(sha256=sha256),),
                outputs=(ArtifactDecl(f"game{i}.bin", "bin", Retention.TERMINAL),),
            )
            unit_plans.append(UnitPlan(
                unit=unit,
                actions=(action,),
                predicted_output_bytes=len(content),
                prediction=_make_prediction(),
            ))

        return BuildPlan(units=tuple(unit_plans)), []

    def test_stop_early_on_budget_breach(self, tmp_path: Path) -> None:
        """Executor stops after the first unit hits the budget."""
        cas = tmp_path / "cas"
        cas.mkdir()
        db = tmp_path / "test.db"
        plan, _ = self._make_multi_unit_plan(tmp_path, cas)

        # Budget of 5 bytes: unit 1 output is 11 bytes, so after unit 1 the
        # cumulative (11) exceeds the budget (5) → units 2 and 3 are stopped.
        budget = 5
        CountingTransform.reset()
        with ActionCache(db) as cache:
            ex = Executor(
                cache,
                {"copy": CountingTransform()},
                cas,
                cas / "scratch",
                budget_bytes=budget,
            )
            output_set = ex.run(plan)

        # First unit executed (0 < 5), second and third stopped (11 >= 5)
        assert CountingTransform.call_count == 1, (
            "Only the first unit should run when budget is hit after unit 1"
        )
        assert len(output_set.unit_outputs) == 1
        assert len(output_set.budget_stopped) == 2, (
            f"Two units should be budget-stopped, got {output_set.budget_stopped}"
        )

    def test_no_stop_when_budget_is_none(self, tmp_path: Path) -> None:
        """All units run when budget_bytes=None (unlimited)."""
        cas = tmp_path / "cas"
        cas.mkdir()
        db = tmp_path / "test.db"
        plan, _ = self._make_multi_unit_plan(tmp_path, cas)

        CountingTransform.reset()
        with ActionCache(db) as cache:
            ex = Executor(
                cache, {"copy": CountingTransform()}, cas, cas / "scratch",
                budget_bytes=None,
            )
            output_set = ex.run(plan)

        assert CountingTransform.call_count == 3
        assert len(output_set.unit_outputs) == 3
        assert len(output_set.budget_stopped) == 0

    def test_budget_stopped_in_output_set(self, tmp_path: Path) -> None:
        """budget_stopped field records skipped unit_ids."""
        cas = tmp_path / "cas"
        cas.mkdir()
        db = tmp_path / "test.db"
        plan, _ = self._make_multi_unit_plan(tmp_path, cas)

        CountingTransform.reset()
        with ActionCache(db) as cache:
            ex = Executor(
                cache, {"copy": CountingTransform()}, cas, cas / "scratch",
                budget_bytes=1,   # tiny budget → all units stop after first
            )
            output_set = ex.run(plan)

        # At least one unit should be budget-stopped
        assert output_set.budget_stopped, "At least one unit must be budget-stopped"
        # All stopped ids are valid unit_ids from the plan
        all_unit_ids = {str(up.unit.unit_id) for up in plan.units}
        for stopped_id in output_set.budget_stopped:
            assert stopped_id in all_unit_ids

