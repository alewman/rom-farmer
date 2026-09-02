"""Tests for romfarmer.ir.catalog."""

from pathlib import Path

import pytest

from romfarmer.ir.catalog import (
    Catalog,
    CatalogWarning,
    DiscRef,
    GameUnit,
    PassTrace,
    PlatformId,
    SourceRef,
    UnitId,
)
from romfarmer.ir.identity import Identity

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_disc(index: int, platform: str = "psx", path: str | None = None) -> DiscRef:
    return DiscRef(
        index=index,
        source=SourceRef(
            path=Path(path or f"/roms/game_disc{index}.bin"),
            platform=PlatformId(platform),
        ),
        identity=Identity(size=700_000_000),
    )


def _make_unit(
    canonical_name: str = "Test Game",
    platform: str = "psx",
    discs: tuple[DiscRef, ...] | None = None,
) -> GameUnit:
    if discs is None:
        discs = (_make_disc(1),)
    return GameUnit.from_discs(PlatformId(platform), canonical_name, discs)


# ---------------------------------------------------------------------------
# SourceRef / DiscRef
# ---------------------------------------------------------------------------


class TestDiscRef:
    def test_frozen(self) -> None:
        disc = _make_disc(1)
        with pytest.raises(Exception):
            disc.index = 2  # type: ignore[misc]


# ---------------------------------------------------------------------------
# GameUnit invariants
# ---------------------------------------------------------------------------


class TestGameUnitInvariants:
    def test_empty_discs_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            GameUnit(
                unit_id=UnitId("x"),
                platform=PlatformId("psx"),
                canonical_name="game",
                discs=(),
            )

    def test_unsorted_discs_raises(self) -> None:
        with pytest.raises(ValueError, match="sorted"):
            GameUnit(
                unit_id=UnitId("x"),
                platform=PlatformId("psx"),
                canonical_name="game",
                discs=(_make_disc(2), _make_disc(1)),
            )

    def test_non_contiguous_indices_allowed(self) -> None:
        # Non-contiguous is a CatalogBuilder policy, NOT a unit invariant
        unit = GameUnit(
            unit_id=UnitId("x"),
            platform=PlatformId("psx"),
            canonical_name="game",
            discs=(_make_disc(1), _make_disc(3)),  # gap at 2
        )
        assert len(unit.discs) == 2

    def test_single_disc_is_multi_disc_false(self) -> None:
        unit = _make_unit()
        assert unit.is_multi_disc is False

    def test_multi_disc_is_multi_disc_true(self) -> None:
        unit = _make_unit(discs=(_make_disc(1), _make_disc(2)))
        assert unit.is_multi_disc is True

    def test_source_size_sums_discs(self) -> None:
        d1 = DiscRef(
            index=1,
            source=SourceRef(Path("/a.bin"), PlatformId("psx")),
            identity=Identity(size=100),
        )
        d2 = DiscRef(
            index=2,
            source=SourceRef(Path("/b.bin"), PlatformId("psx")),
            identity=Identity(size=200),
        )
        unit = _make_unit(discs=(d1, d2))
        assert unit.source_size == 300

    def test_source_size_none_treated_as_zero(self) -> None:
        d = DiscRef(
            index=1,
            source=SourceRef(Path("/x.bin"), PlatformId("psx")),
            identity=Identity(),  # no size
        )
        unit = _make_unit(discs=(d,))
        assert unit.source_size == 0


class TestGameUnitFromDiscs:
    def test_unit_id_is_sha1(self) -> None:
        import hashlib

        unit = _make_unit("Chrono Cross", "psx")
        expected = hashlib.sha1(b"psx:Chrono Cross").hexdigest()
        assert unit.unit_id == expected

    def test_discs_sorted_by_from_discs(self) -> None:
        d1 = _make_disc(1)
        d2 = _make_disc(2)
        # Pass in reverse order — from_discs should sort
        unit = GameUnit.from_discs(PlatformId("psx"), "game", (d2, d1))
        assert unit.discs[0].index == 1
        assert unit.discs[1].index == 2

    def test_unit_id_stable_across_disc_order(self) -> None:
        d1, d2 = _make_disc(1), _make_disc(2)
        u_forward = GameUnit.from_discs(PlatformId("psx"), "game", (d1, d2))
        u_backward = GameUnit.from_discs(PlatformId("psx"), "game", (d2, d1))
        assert u_forward.unit_id == u_backward.unit_id


# ---------------------------------------------------------------------------
# Catalog mutation surface
# ---------------------------------------------------------------------------


class TestCatalogMutation:
    def _two_unit_catalog(self) -> tuple[Catalog, GameUnit, GameUnit]:
        u1 = _make_unit("Alpha", "psx")
        u2 = _make_unit("Beta", "psx")
        cat = Catalog(platform=PlatformId("psx"), units=(u1, u2))
        return cat, u1, u2

    def test_keep_filters(self) -> None:
        cat, u1, u2 = self._two_unit_catalog()
        kept = cat.keep({u1.unit_id})
        assert len(kept.units) == 1
        assert kept.units[0].unit_id == u1.unit_id

    def test_without_removes(self) -> None:
        cat, u1, u2 = self._two_unit_catalog()
        trimmed = cat.without({u1.unit_id})
        assert len(trimmed.units) == 1
        assert trimmed.units[0].unit_id == u2.unit_id

    def test_keep_returns_new_catalog(self) -> None:
        cat, u1, _ = self._two_unit_catalog()
        kept = cat.keep({u1.unit_id})
        assert kept is not cat

    def test_merge_disjoint(self) -> None:
        u1 = _make_unit("Alpha", "psx")
        u2 = _make_unit("Beta", "snes")
        c1 = Catalog(platform=PlatformId("psx"), units=(u1,))
        c2 = Catalog(platform=PlatformId("snes"), units=(u2,))
        merged = c1.merge(c2)
        assert len(merged.units) == 2
        assert merged.platform is None  # merged catalog has no single platform

    def test_merge_overlapping_raises(self) -> None:
        u = _make_unit("Alpha", "psx")
        c1 = Catalog(platform=PlatformId("psx"), units=(u,))
        c2 = Catalog(platform=PlatformId("psx"), units=(u,))
        with pytest.raises(ValueError, match="disjoint"):
            c1.merge(c2)

    def test_no_disc_level_api(self) -> None:
        """Catalog exposes no method that adds, removes, or replaces individual DiscRefs."""
        # The only mutation surface is keep / without / merge — verified by
        # checking that no public methods beyond these three exist.
        public_methods = {
            name
            for name in dir(Catalog)
            if not name.startswith("_") and callable(getattr(Catalog, name, None))
        }
        assert public_methods == {"keep", "without", "merge"}

    def test_warnings_preserved_through_keep(self) -> None:
        u = _make_unit()
        warn = CatalogWarning(unit_key="x", reason="test")
        cat = Catalog(platform=PlatformId("psx"), units=(u,), warnings=(warn,))
        kept = cat.keep({u.unit_id})
        assert kept.warnings == (warn,)

    def test_warnings_combined_on_merge(self) -> None:
        w1 = CatalogWarning("a", "r1")
        w2 = CatalogWarning("b", "r2")
        u1 = _make_unit("Alpha", "psx")
        u2 = _make_unit("Beta", "snes")
        c1 = Catalog(PlatformId("psx"), (u1,), warnings=(w1,))
        c2 = Catalog(PlatformId("snes"), (u2,), warnings=(w2,))
        merged = c1.merge(c2)
        assert w1 in merged.warnings
        assert w2 in merged.warnings


# ---------------------------------------------------------------------------
# PassTrace / PassResult
# ---------------------------------------------------------------------------


class TestPassTrace:
    def test_frozen(self) -> None:
        trace = PassTrace(pass_name="test", removed=())
        with pytest.raises(Exception):
            trace.pass_name = "other"  # type: ignore[misc]

    def test_added_defaults_empty(self) -> None:
        trace = PassTrace(pass_name="test", removed=())
        assert trace.added == ()
