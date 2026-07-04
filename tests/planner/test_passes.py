"""Tests for pure planner passes.

Each pass is tested in isolation using synthetic Catalog fixtures.
No filesystem access, no DB, no external dependencies.
"""

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
from romfarmer.planner import passes


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _uid(platform: str, name: str) -> UnitId:
    return UnitId(hashlib.sha1(f"{platform}:{name}".encode()).hexdigest())


def _unit(
    name: str,
    platform: str = "psx",
    region: frozenset[str] = frozenset(),
    rating: float | None = None,
    size_bytes: int = 1_000_000,
    dat_name: str | None = None,
    disc_index: int = 1,
) -> GameUnit:
    path = Path(f"/roms/{platform}/{name}.zip")
    identity = Identity(size=size_bytes)
    disc = DiscRef(
        index=disc_index,
        source=SourceRef(path=path, platform=PlatformId(platform)),
        identity=identity,
        dat_name=dat_name,
    )
    return GameUnit(
        unit_id=_uid(platform, name),
        platform=PlatformId(platform),
        canonical_name=name,
        discs=(disc,),
        region=region,
        rating=rating,
    )


def _catalog(*units: GameUnit, platform: str = "psx") -> Catalog:
    return Catalog(platform=PlatformId(platform), units=tuple(units))


def _manifest(**kwargs: object) -> BuildManifest:
    return BuildManifest(**kwargs)  # type: ignore[arg-type]


def _kb() -> KnowledgeBase:
    return KnowledgeBase()  # no DB


def _cm() -> CostModel:
    cm = CostModel()
    cm.register_prior("psx", "chd", 0.70)
    cm.register_prior("snes", "zip", 0.60)
    return cm


# ---------------------------------------------------------------------------
# region pass
# ---------------------------------------------------------------------------

class TestRegionPass:
    def test_noop_when_no_preferred(self):
        cat = _catalog(
            _unit("Game A", region=frozenset({"Japan"})),
            _unit("Game B", region=frozenset({"USA"})),
        )
        m = _manifest()
        result = passes.region(cat, m, _kb(), _cm())
        assert len(result.catalog.units) == 2
        assert len(result.trace.removed) == 0

    def test_removes_non_preferred_region(self):
        cat = _catalog(
            _unit("USA Game", region=frozenset({"USA"})),
            _unit("Japan Game", region=frozenset({"Japan"})),
        )
        m = _manifest(preferred_regions=("USA",))
        result = passes.region(cat, m, _kb(), _cm())
        assert len(result.catalog.units) == 1
        assert result.catalog.units[0].canonical_name == "USA Game"
        assert len(result.trace.removed) == 1

    def test_keeps_unknown_region(self):
        cat = _catalog(
            _unit("No Region Game", region=frozenset()),
            _unit("USA Game", region=frozenset({"USA"})),
            _unit("Japan Game", region=frozenset({"Japan"})),
        )
        m = _manifest(preferred_regions=("USA",))
        result = passes.region(cat, m, _kb(), _cm())
        # No Region + USA kept; Japan removed
        assert len(result.catalog.units) == 2
        names = {u.canonical_name for u in result.catalog.units}
        assert "No Region Game" in names
        assert "Japan Game" not in names

    def test_pass_name(self):
        cat = _catalog(_unit("X"))
        m = _manifest()
        result = passes.region(cat, m, _kb(), _cm())
        assert result.trace.pass_name == "region"


# ---------------------------------------------------------------------------
# dat_dedup pass
# ---------------------------------------------------------------------------

class TestDatDedupPass:
    def test_noop_when_unique_dat_names(self):
        cat = _catalog(
            _unit("Game A", dat_name="Game A (USA)"),
            _unit("Game B", dat_name="Game B (USA)"),
        )
        m = _manifest()
        result = passes.dat_dedup(cat, m, _kb(), _cm())
        assert len(result.catalog.units) == 2

    def test_removes_worse_match(self):
        # Two units claim the same dat_name; one has exact name match
        u1 = _unit("Resident Evil (USA)", dat_name="Resident Evil (USA)")
        u2 = _unit("Resident Evil (USA) (RE1 Edition)", dat_name="Resident Evil (USA)")
        cat = _catalog(u1, u2)
        m = _manifest()
        result = passes.dat_dedup(cat, m, _kb(), _cm())
        assert len(result.catalog.units) == 1
        # u1 has exact match
        assert result.catalog.units[0].canonical_name == "Resident Evil (USA)"

    def test_passes_through_no_dat_units(self):
        cat = _catalog(
            _unit("NoDatGame"),
            _unit("AnotherNoDatGame"),
        )
        m = _manifest()
        result = passes.dat_dedup(cat, m, _kb(), _cm())
        assert len(result.catalog.units) == 2


# ---------------------------------------------------------------------------
# one_g_one_r pass
# ---------------------------------------------------------------------------

class TestOneG1RPass:
    def test_keeps_preferred_region(self):
        cat = _catalog(
            _unit("Final Fantasy VII (USA)", region=frozenset({"USA"})),
            _unit("Final Fantasy VII (Japan)", region=frozenset({"Japan"})),
        )
        m = _manifest(preferred_regions=("USA", "Japan"))
        result = passes.one_g_one_r(cat, m, _kb(), _cm())
        assert len(result.catalog.units) == 1
        assert "USA" in result.catalog.units[0].region

    def test_different_games_both_kept(self):
        cat = _catalog(
            _unit("Street Fighter II (USA)", region=frozenset({"USA"})),
            _unit("Mega Man X (USA)", region=frozenset({"USA"})),
        )
        m = _manifest(preferred_regions=("USA",))
        result = passes.one_g_one_r(cat, m, _kb(), _cm())
        assert len(result.catalog.units) == 2

    def test_no_preferred_picks_deterministically(self):
        cat = _catalog(
            _unit("Game (USA)", region=frozenset({"USA"})),
            _unit("Game (Japan)", region=frozenset({"Japan"})),
        )
        m = _manifest()  # no preferred_regions
        result = passes.one_g_one_r(cat, m, _kb(), _cm())
        assert len(result.catalog.units) == 1  # one variant per canonical name

    def test_single_variant_unchanged(self):
        cat = _catalog(_unit("Lonely Game (USA)", region=frozenset({"USA"})))
        m = _manifest(preferred_regions=("USA",))
        result = passes.one_g_one_r(cat, m, _kb(), _cm())
        assert len(result.catalog.units) == 1


# ---------------------------------------------------------------------------
# rating pass
# ---------------------------------------------------------------------------

class TestRatingPass:
    def test_noop_when_no_config(self):
        cat = _catalog(
            _unit("Good Game", rating=0.9),
            _unit("Bad Game", rating=0.3),
        )
        m = _manifest()
        result = passes.rating(cat, m, _kb(), _cm())
        assert len(result.catalog.units) == 2

    def test_min_rating_removes_low_rated(self):
        cat = _catalog(
            _unit("Good Game", rating=0.9),
            _unit("Bad Game", rating=0.3),
        )
        m = _manifest(rating_min=0.5)
        result = passes.rating(cat, m, _kb(), _cm())
        assert len(result.catalog.units) == 1
        assert result.catalog.units[0].canonical_name == "Good Game"

    def test_min_rating_keeps_none_rating(self):
        cat = _catalog(
            _unit("Unrated Game", rating=None),
            _unit("Bad Game", rating=0.3),
        )
        m = _manifest(rating_min=0.5)
        result = passes.rating(cat, m, _kb(), _cm())
        assert len(result.catalog.units) == 1
        assert result.catalog.units[0].canonical_name == "Unrated Game"

    def test_top_n_keeps_highest_rated(self):
        cat = _catalog(
            _unit("Great", rating=0.95),
            _unit("Good", rating=0.80),
            _unit("Ok", rating=0.60),
            _unit("Meh", rating=0.40),
        )
        m = _manifest(rating_top_n=2)
        result = passes.rating(cat, m, _kb(), _cm())
        assert len(result.catalog.units) == 2
        remaining = {u.canonical_name for u in result.catalog.units}
        assert remaining == {"Great", "Good"}

    def test_top_n_none_rated_after_rated(self):
        cat = _catalog(
            _unit("Rated", rating=0.8),
            _unit("Unrated", rating=None),
        )
        m = _manifest(rating_top_n=1)
        result = passes.rating(cat, m, _kb(), _cm())
        # Rated wins over unrated when top_n=1
        assert result.catalog.units[0].canonical_name == "Rated"


# ---------------------------------------------------------------------------
# curated_lists pass
# ---------------------------------------------------------------------------

class TestCuratedListsPass:
    def test_exclude_removes_game(self):
        cat = _catalog(
            _unit("Good Game"),
            _unit("Banned Game"),
        )
        m = _manifest(curated_exclude=frozenset({"Banned Game"}))
        result = passes.curated_lists(cat, m, _kb(), _cm())
        assert len(result.catalog.units) == 1
        assert result.catalog.units[0].canonical_name == "Good Game"

    def test_include_rescues_from_exclude(self):
        cat = _catalog(
            _unit("Contested Game"),
            _unit("Normal Game"),
        )
        m = _manifest(
            curated_exclude=frozenset({"Contested Game"}),
            curated_include=frozenset({"Contested Game"}),
        )
        result = passes.curated_lists(cat, m, _kb(), _cm())
        # Contested game rescued; both kept
        assert len(result.catalog.units) == 2
        assert len(result.trace.added) == 1

    def test_noop_when_empty_lists(self):
        cat = _catalog(_unit("Game A"), _unit("Game B"))
        m = _manifest()
        result = passes.curated_lists(cat, m, _kb(), _cm())
        assert len(result.catalog.units) == 2


# ---------------------------------------------------------------------------
# generation pass
# ---------------------------------------------------------------------------

class TestGenerationPass:
    def _gen_manifest(self) -> BuildManifest:
        return _manifest(
            generation_name="gen6",
            generation_platform_order=("ps2", "gamecube", "xbox"),
        )

    def test_noop_when_no_generation(self):
        cat = _catalog(_unit("GTA Vice City", platform="ps2"))
        m = _manifest()
        result = passes.generation(cat, m, _kb(), _cm())
        assert len(result.catalog.units) == 1

    def test_removes_lower_priority_duplicate(self):
        ps2_unit = _unit("GTA Vice City", platform="ps2")
        xbox_unit = _unit("GTA Vice City", platform="xbox")
        # Multi-platform catalog
        from romfarmer.ir.catalog import Catalog
        cat = Catalog(
            platform=None,
            units=(ps2_unit, xbox_unit),
        )
        m = self._gen_manifest()
        result = passes.generation(cat, m, _kb(), _cm())
        # PS2 has priority 0, Xbox priority 2 — Xbox removed
        assert len(result.catalog.units) == 1
        assert result.catalog.units[0].platform == "ps2"

    def test_keeps_exclusives(self):
        ps2_unit = _unit("PS2 Exclusive", platform="ps2")
        xbox_unit = _unit("Xbox Exclusive", platform="xbox")
        from romfarmer.ir.catalog import Catalog
        cat = Catalog(platform=None, units=(ps2_unit, xbox_unit))
        m = self._gen_manifest()
        result = passes.generation(cat, m, _kb(), _cm())
        assert len(result.catalog.units) == 2

    def test_platforms_not_in_generation_are_skipped(self):
        wii_unit = _unit("Wii Only", platform="wii")
        from romfarmer.ir.catalog import Catalog
        cat = Catalog(platform=None, units=(wii_unit,))
        m = self._gen_manifest()
        result = passes.generation(cat, m, _kb(), _cm())
        assert len(result.catalog.units) == 1  # Wii not in gen6 order

    def test_insufficient_platform_order_is_noop(self):
        cat = _catalog(_unit("Game A"))
        m = _manifest(generation_name="gen6", generation_platform_order=("ps2",))
        result = passes.generation(cat, m, _kb(), _cm())
        assert len(result.catalog.units) == 1


# ---------------------------------------------------------------------------
# budget pass
# ---------------------------------------------------------------------------

class TestBudgetPass:
    def test_noop_when_no_budget(self):
        cat = _catalog(
            _unit("Big Game", size_bytes=10_000_000_000),
            _unit("Also Big", size_bytes=10_000_000_000),
        )
        m = _manifest()
        result = passes.budget(cat, m, _kb(), _cm())
        assert len(result.catalog.units) == 2

    def test_removes_when_over_budget(self):
        # Budget: 1 GB. Each game: 800 MB source → ~560 MB after CHD at 0.70
        cat = _catalog(
            _unit("High Rated", rating=0.9, size_bytes=800_000_000),
            _unit("Low Rated", rating=0.3, size_bytes=800_000_000),
        )
        m = _manifest(budget_bytes=int(1.0 * 1024**3))  # 1 GB
        result = passes.budget(cat, m, _kb(), _cm())
        # Only the highest-rated fits
        assert len(result.catalog.units) == 1
        assert result.catalog.units[0].canonical_name == "High Rated"

    def test_both_fit_within_budget(self):
        cat = _catalog(
            _unit("Game A", size_bytes=100_000_000),
            _unit("Game B", size_bytes=100_000_000),
        )
        # Budget 10 GB — both fit easily
        m = _manifest(budget_bytes=int(10 * 1024**3))
        result = passes.budget(cat, m, _kb(), _cm())
        assert len(result.catalog.units) == 2

    def test_safety_margin_applied(self):
        # With 10% margin, effective budget = 0.9 * budget
        # Source: 1 GB, ratio 0.70 → 700 MB predicted
        # Budget: 800 MB, safety_margin 0.10 → effective = 720 MB
        # 700 MB < 720 MB → fits
        cat = _catalog(_unit("Exactly Fits", size_bytes=int(1e9)))
        m = _manifest(budget_bytes=int(800e6), safety_margin=0.10)
        result = passes.budget(cat, m, _kb(), _cm())
        assert len(result.catalog.units) == 1

    def test_removal_reason_includes_size_info(self):
        cat = _catalog(
            _unit("Big Loser", size_bytes=5_000_000_000),
        )
        m = _manifest(budget_bytes=int(1e9))
        result = passes.budget(cat, m, _kb(), _cm())
        assert len(result.trace.removed) == 1
        reason = result.trace.removed[0][1]
        assert "budget" in reason
        assert "bytes" in reason
