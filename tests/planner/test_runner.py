"""Tests for PassRunner."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from romfarmer.analysis.knowledge import KnowledgeBase
from romfarmer.ir.catalog import (
    Catalog,
    DiscRef,
    GameUnit,
    PlatformId,
    SourceRef,
    UnitId,
)
from romfarmer.ir.identity import Identity
from romfarmer.ir.manifest import BuildManifest
from romfarmer.planner.costmodel import CostModel
from romfarmer.planner.runner import PassRunner


def _unit(name: str, rating: float | None = None) -> GameUnit:
    uid = UnitId(hashlib.sha1(f"psx:{name}".encode()).hexdigest())
    disc = DiscRef(
        index=1,
        source=SourceRef(path=Path(f"/roms/{name}.zip"), platform=PlatformId("psx")),
        identity=Identity(size=1_000_000),
        dat_name=None,
    )
    return GameUnit(
        unit_id=uid,
        platform=PlatformId("psx"),
        canonical_name=name,
        discs=(disc,),
        region=frozenset({"USA"}),
        rating=rating,
    )


def _catalog(*units: GameUnit) -> Catalog:
    return Catalog(platform=PlatformId("psx"), units=tuple(units))


class TestPassRunner:
    def test_empty_pass_list_returns_unchanged(self):
        cat = _catalog(_unit("A"), _unit("B"))
        runner = PassRunner(
            passes=[],
            manifest=BuildManifest(platform=PlatformId("psx")),
            kb=KnowledgeBase(),
            cost_model=CostModel(),
        )
        final, traces = runner.run(cat)
        assert len(final.units) == 2
        assert traces == []

    def test_single_pass_applied(self):
        from romfarmer.planner import passes

        cat = _catalog(
            _unit("Top Game", rating=0.9),
            _unit("Low Game", rating=0.2),
        )
        runner = PassRunner(
            passes=[passes.rating],
            manifest=BuildManifest(platform=PlatformId("psx"), rating_min=0.5),
            kb=KnowledgeBase(),
            cost_model=CostModel(),
        )
        final, traces = runner.run(cat)
        assert len(final.units) == 1
        assert final.units[0].canonical_name == "Top Game"
        assert len(traces) == 1

    def test_multiple_passes_sequential(self):
        from romfarmer.planner import passes

        cat = _catalog(
            _unit("USA Game", rating=0.9),
            _unit("JPN Game", rating=0.5),
        )

        def _region_filter(catalog, manifest, kb, cm):
            from romfarmer.ir.catalog import PassResult, PassTrace
            removed = tuple(
                (u.unit_id, "test remove")
                for u in catalog.units
                if "JPN" in u.canonical_name
            )
            new_cat = catalog.without({uid for uid, _ in removed})
            return PassResult(
                catalog=new_cat,
                trace=PassTrace(pass_name="test_region", removed=removed),
            )

        runner = PassRunner(
            passes=[_region_filter, passes.rating],
            manifest=BuildManifest(platform=PlatformId("psx"), rating_min=0.5),
            kb=KnowledgeBase(),
            cost_model=CostModel(),
        )
        final, traces = runner.run(cat)
        assert len(final.units) == 1
        assert len(traces) == 2

    def test_traces_collected_for_all_passes(self):
        from romfarmer.planner import passes

        cat = _catalog(_unit("A"), _unit("B"))
        runner = PassRunner(
            passes=[passes.region, passes.rating],
            manifest=BuildManifest(platform=PlatformId("psx")),
            kb=KnowledgeBase(),
            cost_model=CostModel(),
        )
        _, traces = runner.run(cat)
        assert len(traces) == 2
        assert traces[0].pass_name == "region"
        assert traces[1].pass_name == "rating"

    def test_noop_passes_preserve_catalog(self):
        from romfarmer.planner import passes

        cat = _catalog(_unit("Lonely Game"))
        runner = PassRunner(
            passes=[passes.region, passes.dat_dedup, passes.one_g_one_r,
                    passes.arcade, passes.rating, passes.curated_lists,
                    passes.budget, passes.generation],
            manifest=BuildManifest(platform=PlatformId("psx")),
            kb=KnowledgeBase(),
            cost_model=CostModel(),
        )
        final, traces = runner.run(cat)
        assert len(final.units) == 1
        assert len(traces) == 8
