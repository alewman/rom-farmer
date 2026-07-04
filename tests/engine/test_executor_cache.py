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
