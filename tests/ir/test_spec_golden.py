"""Golden-hash tests for ``romfarmer.ir.spec.Spec`` (intent brief v4 §5).

GOLDEN VALUE — computed 2026-09-03.  If it changes, the canonical form of the
spec changed: every persisted ``artifacts/specs/<hash>.yaml`` and every
``(intent, inventory_digest) → spec_hash`` record is orphaned.  Not a test to
update casually.
"""

from __future__ import annotations

import dataclasses

import pytest

from romfarmer.ir.spec import Spec, SpecError, SpecIntent

GOLDEN_SPEC_HASH = "182ea3eb526ff4271224d59b8c360777ed6213ec8d880b43b70e4e5221c78b21"

RAW = {
    "spec_version": 1,
    "intent": {
        "text": "build the best 512GB Rocknix system for an R36S console",
        "authored_by": "agent:test",
        "authored_at": "2026-09-03T20:14:00Z",
        "inventory_digest": "sha256:0000",
        "capability_digest": "sha256:1111",
        "allocation_note": "psx gets the lion's share",
    },
    "target": {
        "frontend": "rocknix",
        "device": "r36s",
        "storage_bytes": 512_000_000_000,
        "reserve_bytes": 16_000_000_000,
    },
    "platforms": [
        {
            "platform": "psx",
            "priority": 10,
            "sources": [{"root": "myrient_redump", "subpath": "Sony - PlayStation"}],
            "extraction": "disc",
            "compression": "chd",
            "dat": {"retool_1g1r": True},
            "passes": {
                "dat_filter": True,
                "rating": {"scale": "unit_interval", "min": 0.70, "unrated": "keep"},
                "curated_lists": {"ref": "curated/psx-essentials@sha256:" + "ab" * 32},
                "budget": {"max_bytes": 340_000_000_000, "unrated_as": "median"},
            },
        },
        {
            "platform": "snes",
            "priority": 9,
            "sources": [
                {
                    "root": "myrient_nointro",
                    "subpath": "Nintendo - Super Nintendo Entertainment System",
                }
            ],
            "extraction": "cartridge",
            "compression": "zip",
            "dat": {"retool_1g1r": True},
            "passes": {"budget": {"max_bytes": 2_000_000_000}},
        },
    ],
}


def _spec(**overrides: object) -> Spec:
    raw = {**RAW, **overrides}
    return Spec.from_dict(raw)


class TestGolden:
    def test_golden_hash(self) -> None:
        assert _spec().spec_hash() == GOLDEN_SPEC_HASH

    def test_intent_is_excluded_from_hash(self) -> None:
        a = _spec()
        b = dataclasses.replace(a, intent=SpecIntent(text="something completely different"))
        assert a.spec_hash() == b.spec_hash()

    def test_platform_order_does_not_matter(self) -> None:
        swapped = {**RAW, "platforms": list(reversed(RAW["platforms"]))}
        assert Spec.from_dict(swapped).spec_hash() == GOLDEN_SPEC_HASH

    def test_semantic_change_changes_hash(self) -> None:
        raw = {**RAW, "target": {**RAW["target"], "reserve_bytes": 8_000_000_000}}
        assert Spec.from_dict(raw).spec_hash() != GOLDEN_SPEC_HASH

    def test_round_trip(self) -> None:
        s = _spec()
        assert Spec.from_dict(s.to_dict()) == s


class TestValidation:
    def _plat(self, **passes: object) -> dict:
        p = dict(RAW["platforms"][1])
        p["passes"] = passes
        return {**RAW, "platforms": [RAW["platforms"][0], p]}

    def test_rating_min_above_one_is_rejected(self) -> None:
        with pytest.raises(SpecError, match="unit interval"):
            Spec.from_dict(self._plat(rating={"min": 3.5, "unrated": "keep"}))

    def test_unrated_required_with_min(self) -> None:
        with pytest.raises(SpecError, match="unrated is required"):
            Spec.from_dict(self._plat(rating={"min": 0.7}))

    def test_region_under_retool_dat_is_rejected(self) -> None:
        with pytest.raises(SpecError, match="Retool 1G1R"):
            Spec.from_dict(self._plat(region={"preferred": ["USA"]}))

    def test_1g1r_pass_key_is_rejected(self) -> None:
        with pytest.raises(SpecError, match="dat.retool_1g1r"):
            Spec.from_dict(self._plat(**{"1g1r": True}))

    def test_curated_ref_must_be_hash_addressed(self) -> None:
        with pytest.raises(SpecError, match="sha256"):
            Spec.from_dict(self._plat(curated_lists={"ref": "curated/psx-essentials"}))

    def test_budget_sum_must_fit_usable_storage(self) -> None:
        with pytest.raises(SpecError, match="exceeds usable storage"):
            Spec.from_dict(self._plat(budget={"max_bytes": 200_000_000_000}))

    def test_policy_key_is_rejected(self) -> None:
        with pytest.raises(SpecError, match="policy"):
            Spec.from_dict({**RAW, "policy": {"budget_strategy": "priority_ordered"}})

    def test_unknown_key_is_loud(self) -> None:
        with pytest.raises(SpecError, match="unknown key"):
            Spec.from_dict({**RAW, "platforms": [{**RAW["platforms"][0], "recipe": "x"}]})

    def test_absolute_source_path_is_rejected(self) -> None:
        with pytest.raises(SpecError, match="absolute paths are not allowed"):
            Spec.from_dict(
                {**RAW, "platforms": [{**RAW["platforms"][0], "sources": ["/data/roms/psx"]}]}
            )

    def test_source_subpath_must_be_relative(self) -> None:
        bad = [{"root": "r", "subpath": "../escape"}]
        with pytest.raises(SpecError, match="relative"):
            Spec.from_dict({**RAW, "platforms": [{**RAW["platforms"][0], "sources": bad}]})

    def test_unrated_as_float_and_bad_value(self) -> None:
        Spec.from_dict(self._plat(budget={"unrated_as": "0.5"}))
        with pytest.raises(SpecError, match="unrated_as"):
            Spec.from_dict(self._plat(budget={"unrated_as": "meh"}))


class TestSpecIO:
    def test_yaml_round_trip_and_loud_load(self, tmp_path) -> None:
        from romfarmer.driver.spec_io import dump_spec, load_spec, save_spec

        s = _spec()
        p = save_spec(s, tmp_path / "specs")
        assert p.name == f"{GOLDEN_SPEC_HASH}.yaml"
        assert load_spec(p) == s
        assert dump_spec(s).startswith(f"# spec_hash: {GOLDEN_SPEC_HASH}")
        bad = tmp_path / "bad.yaml"
        bad.write_text("target: [unclosed\n")
        with pytest.raises(SpecError):
            load_spec(bad)
        with pytest.raises(SpecError, match="not found"):
            load_spec(tmp_path / "missing.yaml")
