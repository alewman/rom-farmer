"""Deterministic guards on stochastic proposals (moved from farmhand/optimizer)."""

from __future__ import annotations

from romfarmer.intent.guards import apply_guards, guard_spec_revision
from romfarmer.ir.spec import Spec

RAW = {
    "target": {"frontend": "rocknix", "device": "r36s", "storage_bytes": 10**9, "reserve_bytes": 0},
    "platforms": [
        {
            "platform": "psx",
            "sources": [{"root": "r", "subpath": "psx"}],
            "extraction": "disc",
            "compression": "chd",
            "dat": {"retool_1g1r": True},
            "passes": {"rating": {"min": 0.7, "unrated": "drop"}, "budget": {"max_bytes": 500}},
        }
    ],
}


def _spec(min_: float | None = 0.7, unrated: str = "drop", max_bytes: int = 500) -> Spec:
    raw = {**RAW, "platforms": [dict(RAW["platforms"][0])]}
    rating = {"min": min_, "unrated": unrated} if min_ is not None else {}
    raw["platforms"][0]["passes"] = {"rating": rating, "budget": {"max_bytes": max_bytes}}
    return Spec.from_dict(raw)


class TestApplyGuards:
    def test_clamp_snap_floor_and_unknown_keys(self) -> None:
        out = apply_guards(
            {"gen5": 0.87, "gen3": 0.9, "made_up": 0.5},
            {"gen5": 0.8, "gen3": 0.0},
            -1,
            floor_keys=frozenset({"gen3"}),
        )
        assert out == {"gen5": 0.85, "gen3": 0.0}

    def test_overshoot_rejects_loosening(self) -> None:
        out = apply_guards({"gen5": 0.7}, {"gen5": 0.8}, delta_bytes=1)
        assert out["gen5"] == 0.8
        out = apply_guards({"gen5": 0.9}, {"gen5": 0.8}, delta_bytes=1)
        assert out["gen5"] == 0.9

    def test_spike_caps_change_to_one_step(self) -> None:
        out = apply_guards({"gen5": 0.95}, {"gen5": 0.8}, -1, history=[{"is_spike": True}])
        assert out["gen5"] == 0.85


class TestGuardSpecRevision:
    def test_no_guard_when_under_budget(self) -> None:
        assert (
            guard_spec_revision(_spec(0.7), _spec(0.5, "keep", 900), previous_headroom_p50=10) == []
        )

    def test_loosening_while_over_budget_is_rejected(self) -> None:
        v = guard_spec_revision(_spec(0.7), _spec(0.6), previous_headroom_p50=-100)
        assert v and "rating.min loosened" in v[0]
        v = guard_spec_revision(
            _spec(0.7, max_bytes=500), _spec(0.7, max_bytes=800), previous_headroom_p50=-100
        )
        assert v and "budget.max_bytes raised" in v[0]
        v = guard_spec_revision(_spec(0.7, "drop"), _spec(0.7, "keep"), previous_headroom_p50=-100)
        assert v and "unrated loosened" in v[0]

    def test_tightening_while_over_budget_is_fine(self) -> None:
        assert (
            guard_spec_revision(_spec(0.7), _spec(0.8, max_bytes=400), previous_headroom_p50=-100)
            == []
        )
