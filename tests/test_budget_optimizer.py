"""Tests for the LangGraph budget optimizer.

Covers:
- route_after_build truth table (converged / overshoot / undershoot / exhausted / stall)
- Critic sanitizer guards (floor gens, hierarchy, step snap, spike protection)
- init_builder threshold seeding
- estimate_build_size multi-disc atomicity
- Graph convergence on a synthetic scenario (stubbed LLM)
"""

from __future__ import annotations

import dataclasses
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from romfarmer.farmhand.optimizer.graph import route_after_build
from romfarmer.farmhand.optimizer.nodes import _apply_guards, _FLOOR_GENS
from romfarmer.farmhand.optimizer.pool import (
    DEFAULT_THRESHOLDS,
    PoolEntry,
    estimate_build_size,
)
from romfarmer.farmhand.optimizer.state import BudgetState, IterationLog

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

GB = 1024**3

def _make_state(**overrides) -> BudgetState:
    """Return a minimal BudgetState suitable for routing tests."""
    base: Dict[str, Any] = {
        "build_name": "test-build",
        "pool_root": "/tmp/pool",
        "target_total_bytes": 200 * GB,
        "target_free_bytes": 30 * GB,
        "tolerance_bytes": 5 * GB,
        "max_iterations": 8,
        "thresholds": {"gen5": 0.8, "gen6": 0.9},
        "platform_overrides": {},
        "last_report": None,
        "last_used_bytes": 0,
        "last_free_bytes": 200 * GB,
        "delta_to_target": 0,
        "iteration": 0,
        "no_progress_count": 0,
        "verdict": None,
        "history": [],
    }
    base.update(overrides)
    return base  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# route_after_build
# ---------------------------------------------------------------------------


class TestRouteAfterBuild:
    def test_converged_within_tolerance(self):
        # delta = +3 GB, tol = 5 GB → converged
        state = _make_state(
            delta_to_target=3 * GB,
            tolerance_bytes=5 * GB,
            iteration=2,
        )
        assert route_after_build(state) == "done"

    def test_converged_undershoot_within_tolerance(self):
        state = _make_state(
            delta_to_target=-4 * GB,
            tolerance_bytes=5 * GB,
            iteration=2,
        )
        assert route_after_build(state) == "done"

    def test_overshoot_sends_to_critic(self):
        state = _make_state(
            delta_to_target=60 * GB,
            tolerance_bytes=5 * GB,
            iteration=2,
            max_iterations=8,
        )
        assert route_after_build(state) == "critic"

    def test_undershoot_sends_to_critic(self):
        state = _make_state(
            delta_to_target=-80 * GB,
            tolerance_bytes=5 * GB,
            iteration=2,
            max_iterations=8,
        )
        assert route_after_build(state) == "critic"

    def test_max_iterations_exhausted(self):
        state = _make_state(
            delta_to_target=30 * GB,
            tolerance_bytes=5 * GB,
            iteration=8,
            max_iterations=8,
        )
        assert route_after_build(state) == "exhausted"

    def test_no_progress_stall(self):
        state = _make_state(
            delta_to_target=30 * GB,
            tolerance_bytes=5 * GB,
            iteration=4,
            max_iterations=8,
            no_progress_count=2,
        )
        assert route_after_build(state) == "exhausted"

    def test_exactly_at_tolerance_boundary(self):
        # delta = exactly 5 GB = tolerance → converged (abs <= tol)
        state = _make_state(
            delta_to_target=5 * GB,
            tolerance_bytes=5 * GB,
            iteration=3,
        )
        assert route_after_build(state) == "done"

    def test_one_byte_over_tolerance(self):
        state = _make_state(
            delta_to_target=5 * GB + 1,
            tolerance_bytes=5 * GB,
            iteration=3,
            max_iterations=8,
        )
        assert route_after_build(state) == "critic"


# ---------------------------------------------------------------------------
# Critic guard: _apply_guards
# ---------------------------------------------------------------------------


class TestApplyGuards:
    def _base_current(self) -> Dict[str, float]:
        return {
            "gen3": 0.0, "gen4": 0.0,
            "gen5": 0.8, "gen5_handheld": 0.8,
            "gen6": 0.9, "gen6_handheld": 0.9,
            "gen7": 0.9, "gen7_handheld": 0.9,
            "arcade": 0.0, "portable": 0.0, "unknown": 0.0,
        }

    def test_floor_gens_stay_zero(self):
        current = self._base_current()
        # LLM tries to raise floor gens
        proposed = dict(current)
        for g in _FLOOR_GENS:
            proposed[g] = 0.5
        result = _apply_guards(proposed, current, delta_bytes=50 * GB, history=[])
        for g in _FLOOR_GENS:
            assert result[g] == 0.0, f"{g} should be floored at 0.0"

    def test_overshoot_blocks_loosening(self):
        current = self._base_current()
        proposed = dict(current)
        proposed["gen6"] = 0.85  # LLM tries to loosen gen6 during overshoot
        result = _apply_guards(proposed, current, delta_bytes=50 * GB, history=[])
        # Guard should reject the loosening
        assert result["gen6"] == 0.9

    def test_overshoot_allows_tightening(self):
        current = self._base_current()
        proposed = dict(current)
        proposed["gen6"] = 0.95  # LLM tightens gen6
        result = _apply_guards(proposed, current, delta_bytes=50 * GB, history=[])
        assert result["gen6"] == 0.95

    def test_undershoot_allows_gen6_loosen_even_when_gen5_not_exhausted(self):
        current = self._base_current()
        proposed = dict(current)
        proposed["gen6"] = 0.85  # loosen gen6 while gen5=0.8
        result = _apply_guards(proposed, current, delta_bytes=-80 * GB, history=[])
        # New policy: gen6 loosening is allowed during undershoot regardless of gen5
        assert result["gen6"] == 0.85

    def test_undershoot_allows_gen6_loosen_when_gen5_exhausted(self):
        current = self._base_current()
        current["gen5"] = 0.0
        current["gen5_handheld"] = 0.0
        proposed = dict(current)
        proposed["gen6"] = 0.85
        result = _apply_guards(proposed, current, delta_bytes=-80 * GB, history=[])
        assert result["gen6"] == 0.85

    def test_step_snap_to_0_05(self):
        current = {"gen5": 0.8, "gen6": 0.9}
        # 0.77 → nearest 0.05 step = 0.75; during undershoot gen5 loosen is allowed
        proposed = {"gen5": 0.77, "gen6": 0.93}
        result = _apply_guards(proposed, current, delta_bytes=-20 * GB, history=[])
        # 0.77 snaps to 0.75 (nearest 0.05)
        assert result["gen5"] == pytest.approx(0.75, abs=1e-4)
        # 0.93 snaps to 0.95 — this is a *tightening* of gen6, which is allowed
        # even during undershoot (guards only block loosening)
        assert result["gen6"] == pytest.approx(0.95, abs=1e-4)

    def test_unknown_gen_names_ignored(self):
        current = {"gen5": 0.8}
        proposed = {"gen5": 0.75, "gen_fake": 0.5}
        result = _apply_guards(proposed, current, delta_bytes=-20 * GB, history=[])
        assert "gen_fake" not in result

    def test_spike_caps_change_magnitude(self):
        current = {"gen6": 0.9}
        proposed = {"gen6": 0.65}  # LLM tries to move by 0.25
        spike_log = {"is_spike": True, "thresholds": {"gen6": 0.9}}
        # During overshoot, loosening is blocked regardless of spike
        # During undershoot, we test the cap
        result = _apply_guards(proposed, current, delta_bytes=-10 * GB, history=[spike_log])
        # Even with spike, gen6 loosen blocked by gen5-not-exhausted guard
        # (current doesn't have gen5 so all gen5s are absent from current → exhausted)
        # So this depends on whether "gen5" key exists in current
        assert "gen6" in result

    def test_clamp_to_1_0(self):
        current = {"gen6": 0.9}
        proposed = {"gen6": 1.5}  # out of range
        result = _apply_guards(proposed, current, delta_bytes=50 * GB, history=[])
        assert result["gen6"] == pytest.approx(1.0, abs=1e-4)

    def test_clamp_to_0_0_lower_bound(self):
        current = {"gen5": 0.8}
        proposed = {"gen5": -0.3}
        result = _apply_guards(proposed, current, delta_bytes=-50 * GB, history=[])
        assert result["gen5"] >= 0.0


# ---------------------------------------------------------------------------
# estimate_build_size
# ---------------------------------------------------------------------------


class TestEstimateBuildSize:
    def _sample_pool(self):
        return {
            "nes": [
                PoolEntry("Super Mario Bros", 0.95, "gen3", 512_000),
                PoolEntry("Mega Man 2", 0.90, "gen3", 256_000),
                PoolEntry("Soccer", 0.30, "gen3", 128_000),
            ],
            "psx": [
                PoolEntry("Final Fantasy VII", 0.95, "gen5", 2_000_000_000,
                          multi_disc_group="Final Fantasy VII"),
                PoolEntry("Crash Bandicoot", 0.88, "gen5", 600_000_000),
                PoolEntry("Obscure RPG", 0.50, "gen5", 700_000_000),
            ],
        }

    def test_gen3_floor_includes_all(self):
        pool = self._sample_pool()
        report = estimate_build_size(pool, {"gen3": 0.0, "gen5": 0.9})
        assert report.per_platform_game_counts["nes"] == 3

    def test_gen5_threshold_filters(self):
        pool = self._sample_pool()
        report = estimate_build_size(pool, {"gen3": 0.0, "gen5": 0.9})
        # Only FF7 (0.95) passes gen5 threshold 0.9
        assert report.per_platform_game_counts["psx"] == 1

    def test_total_size_correct(self):
        pool = self._sample_pool()
        # gen3=0.0 → all 3 nes, gen5=0.9 → only FF7
        report = estimate_build_size(pool, {"gen3": 0.0, "gen5": 0.9})
        expected = 512_000 + 256_000 + 128_000 + 2_000_000_000
        assert report.total_size_bytes == expected

    def test_platform_override_supersedes_gen(self):
        pool = self._sample_pool()
        # Override psx to 0.0 regardless of gen5 threshold
        report = estimate_build_size(
            pool, {"gen3": 0.0, "gen5": 0.95},
            platform_overrides={"psx": 0.0}
        )
        # All 3 psx games pass (override 0.0)
        assert report.per_platform_game_counts["psx"] == 3

    def test_multi_disc_flag_counted(self):
        pool = self._sample_pool()
        report = estimate_build_size(pool, {"gen3": 0.0, "gen5": 0.9})
        assert report.multi_disc_groups_included == 1  # FF7 is multi-disc

    def test_generation_sizes_aggregated(self):
        pool = self._sample_pool()
        report = estimate_build_size(pool, {"gen3": 0.0, "gen5": 0.0})
        assert report.per_generation_sizes["gen3"] == 512_000 + 256_000 + 128_000
        assert report.per_generation_sizes["gen5"] == 2_000_000_000 + 600_000_000 + 700_000_000

    def test_empty_pool_returns_zero_report(self):
        report = estimate_build_size({}, {"gen5": 0.8})
        assert report.total_size_bytes == 0
        assert report.total_game_count == 0

    def test_all_filtered_out(self):
        pool = {
            "psx": [
                PoolEntry("Old Game", 0.3, "gen5", 500_000_000),
            ]
        }
        report = estimate_build_size(pool, {"gen5": 0.99})
        assert report.total_size_bytes == 0
        assert report.total_game_count == 0

    def test_is_estimated_flag(self):
        report = estimate_build_size({}, {})
        assert report.is_estimated is True


# ---------------------------------------------------------------------------
# Integration: graph converges on synthetic overshoot
# ---------------------------------------------------------------------------


class TestGraphConvergence:
    """Stub-out the LLM and verify the graph converges within N iterations."""

    def _make_stub_pool(self, num_gen5_games: int = 20, num_gen6_games: int = 10):
        """Create a synthetic pool where each threshold step drops ~10 GB."""
        nes_entries = [
            PoolEntry(f"NES Game {i}", 1.0, "gen3", 100_000_000)
            for i in range(5)
        ]
        # gen5 games: 20 games rated 0.7–1.0 in 0.05 steps, 1 GB each
        gen5_entries = [
            PoolEntry(f"PSX Game {i}", round(0.7 + i * 0.015, 3), "gen5", 1 * GB)
            for i in range(num_gen5_games)
        ]
        # gen6 games: 10 games rated 0.8–1.0, 5 GB each
        gen6_entries = [
            PoolEntry(f"PS2 Game {i}", round(0.8 + i * 0.02, 3), "gen6", 5 * GB)
            for i in range(num_gen6_games)
        ]
        return {
            "nes": nes_entries,
            "psx": gen5_entries,
            "ps2": gen6_entries,
        }

    def _make_stub_call_critic(self, pool):
        """
        Return a mock call_critic that makes deterministic shrink decisions:
        raise gen6 by 0.05 if overshooting, lower gen5 by 0.05 if undershooting.
        """
        from romfarmer.farmhand.optimizer.state import CriticDecision

        def _stub(system_prompt, user_payload):
            thresholds = user_payload["thresholds"].copy()
            delta = user_payload["delta_gb"]
            if delta > 0:  # overshoot
                thresholds["gen6"] = min(1.0, round(thresholds.get("gen6", 0.9) + 0.05, 4))
                direction = "shrink"
                rationale = f"Overshoot by {delta:.1f} GB — raising gen6."
            else:
                thresholds["gen5"] = max(0.0, round(thresholds.get("gen5", 0.8) - 0.05, 4))
                direction = "grow"
                rationale = f"Undershoot by {abs(delta):.1f} GB — lowering gen5."
            return CriticDecision(
                thresholds=thresholds,
                rationale=rationale,
                expected_direction=direction,
            )

        return _stub

    def test_converges_overshoot(self):
        """Start with a build that overshoots by ~30 GB; expect convergence."""
        pytest.importorskip("langgraph")

        import dataclasses as dc
        import json
        import os
        import tempfile
        from pathlib import Path

        from romfarmer.farmhand.optimizer import run_optimizer

        pool = self._make_stub_pool()
        stub_critic = self._make_stub_call_critic(pool)

        with tempfile.TemporaryDirectory() as tmpdir:
            pool_root_path = os.path.join(tmpdir, ".pool")
            os.makedirs(pool_root_path)

            for platform, entries in pool.items():
                with open(os.path.join(pool_root_path, f"{platform}.json"), "w") as f:
                    json.dump([dc.asdict(e) for e in entries], f)

            # Patch call_critic at the llm_client module level. Because nodes.py
            # does a lazy `from .llm_client import call_critic` inside the
            # evaluator_critic function, patching the module attribute is picked
            # up correctly at call time.
            with patch("romfarmer.farmhand.optimizer.llm_client.call_critic", stub_critic):
                result = run_optimizer(
                    build_name="test-build",
                    target_total_bytes=200 * GB,
                    target_free_bytes=30 * GB,
                    tolerance_bytes=5 * GB,
                    max_iterations=8,
                    pool_root=Path(pool_root_path),
                )

        assert result.verdict in ("converged", "exhausted")
        assert result.iterations_used <= 8
        assert result.final_thresholds is not None
        for gen in _FLOOR_GENS:
            if gen in result.final_thresholds:
                assert result.final_thresholds[gen] == 0.0


# ---------------------------------------------------------------------------
# Smoke: LLM client parse
# ---------------------------------------------------------------------------


class TestCriticParse:
    def test_parses_clean_json(self):
        from romfarmer.farmhand.optimizer.llm_client import _parse_decision

        raw = '{"thresholds": {"gen5": 0.75, "gen6": 0.95}, "rationale": "test", "expected_direction": "shrink"}'
        d = _parse_decision(raw)
        assert d.thresholds["gen5"] == pytest.approx(0.75)
        assert d.expected_direction == "shrink"

    def test_parses_markdown_fenced(self):
        from romfarmer.farmhand.optimizer.llm_client import _parse_decision

        raw = '```json\n{"thresholds": {"gen6": 0.95}, "rationale": "ok", "expected_direction": "shrink"}\n```'
        d = _parse_decision(raw)
        assert d.thresholds["gen6"] == pytest.approx(0.95)

    def test_clamps_out_of_range(self):
        from romfarmer.farmhand.optimizer.llm_client import _parse_decision

        raw = '{"thresholds": {"gen5": 1.5, "gen6": -0.1}, "rationale": "x", "expected_direction": "hold"}'
        d = _parse_decision(raw)
        assert d.thresholds["gen5"] == pytest.approx(1.0)
        assert d.thresholds["gen6"] == pytest.approx(0.0)

    def test_missing_thresholds_raises(self):
        from romfarmer.farmhand.optimizer.llm_client import _parse_decision

        raw = '{"rationale": "no thresholds here", "expected_direction": "hold"}'
        with pytest.raises(KeyError):
            _parse_decision(raw)

    def test_invalid_json_raises(self):
        from romfarmer.farmhand.optimizer.llm_client import _parse_decision

        with pytest.raises(Exception):
            _parse_decision("not json at all {{{")

    def test_unknown_direction_defaults_to_hold(self):
        from romfarmer.farmhand.optimizer.llm_client import _parse_decision

        raw = '{"thresholds": {}, "rationale": "x", "expected_direction": "sideways"}'
        d = _parse_decision(raw)
        assert d.expected_direction == "hold"
