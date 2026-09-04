"""PlanSession + PlanSummary — the agent loop's sensory input (intent brief v2 §4 / v3 §4)."""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

import pytest

from romfarmer.driver.session import PlanSession, inventory_digest
from romfarmer.ir.spec import Spec

CONFIG = Path(__file__).resolve().parents[2] / "config"


def _workspace(tmp_path: Path) -> tuple[Path, Path]:
    cfg = tmp_path / "config"
    shutil.copytree(
        CONFIG, cfg, ignore=shutil.ignore_patterns("size_data.json", "builds", "farmhand")
    )
    (cfg / "sources.yaml").write_text(f"roots:\n  test: {tmp_path}\n")
    src = tmp_path / "nes"
    src.mkdir()
    for name, size in (("Alpha (USA)", 3000), ("Beta (USA)", 2000), ("Gamma (Europe)", 1000)):
        with zipfile.ZipFile(src / f"{name}.zip", "w", compression=zipfile.ZIP_STORED) as zf:
            zf.writestr(f"{name}.nes", b"x" * size)
    return tmp_path, cfg


def _spec(max_bytes: int | None = None) -> Spec:
    passes: dict = {"dat_filter": False}
    if max_bytes is not None:
        passes["budget"] = {"max_bytes": max_bytes}
    return Spec.from_dict(
        {
            "target": {
                "frontend": "batocera",
                "device": "pc",
                "storage_bytes": 10**9,
                "reserve_bytes": 0,
            },
            "platforms": [
                {
                    "platform": "nes",
                    "sources": [{"root": "test", "subpath": "nes"}],
                    "extraction": "none",
                    "compression": "none",
                    "dat": {"retool_1g1r": True},
                    "passes": passes,
                }
            ],
        }
    )


@pytest.mark.skipif(not (CONFIG / "platforms" / "nes.yaml").exists(), reason="needs repo config/")
class TestPlanSession:
    def test_inventory_and_summary_shape(self, tmp_path: Path) -> None:
        ws, cfg = _workspace(tmp_path)
        session = PlanSession(ws, cfg)
        inv = session.inventory(_spec())
        assert inv["nes"]["units"] == 3 and inv["nes"]["files"] == 3
        assert inv["nes"]["inventory_digest"].startswith("sha256:")
        assert inv["_inventory_digest"].startswith("sha256:")

        summary = session.dry_run(_spec())
        d = summary.to_dict()
        assert d["spec_hash"] == _spec().spec_hash()
        (p,) = d["platforms"]
        assert p["platform"] == "nes" and p["units_in"] == 3 and p["units_out"] == 3
        assert p["tier"] == "A"  # pc: platforms_default
        assert p["bytes_src"] > 0 and p["bytes_est_p50"] > 0
        assert "rating_quantiles" in p and "removed_by_pass" in p
        assert d["headroom_p50"] == 10**9 - d["bytes_total_p50"]
        assert p["bytes_kept_at_rating"]["0.50"] >= p["bytes_kept_at_rating"]["0.85"]
        assert p["heaviest"] and p["heaviest"][0]["bytes_p50"] >= p["heaviest"][-1]["bytes_p50"]
        assert d["fits"] is True and d["binding"].startswith("p90")  # passthrough is exact
        assert p["p90_source"] == "exact" and p["p90_ratio"] == 1.0
        assert len(summary.to_json(set())) < 2000  # compact without per-unit detail

    def test_catalog_is_cached_across_replans(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ws, cfg = _workspace(tmp_path)
        session = PlanSession(ws, cfg)
        import romfarmer.new_orchestrator as orch

        calls = {"n": 0}
        real = orch.run_catalog

        def counting(*a, **k):  # type: ignore[no-untyped-def]
            calls["n"] += 1
            return real(*a, **k)

        monkeypatch.setattr(orch, "run_catalog", counting)
        a = session.dry_run(_spec())
        b = session.dry_run(_spec(max_bytes=2_500))  # tighter budget → different plan, same catalog
        assert calls["n"] == 1
        assert a.platforms[0].units_out == 3
        assert b.platforms[0].units_out < 3
        assert b.budget_trimmed_units >= 1
        assert b.platforms[0].top_dropped and b.platforms[0].top_dropped[0]["pass"] == "budget"
        assert any(n.startswith("unrated_as=median") for n in b.platforms[0].notes)

    def test_inventory_digest_is_a_function_of_the_catalog(self, tmp_path: Path) -> None:
        ws, cfg = _workspace(tmp_path)
        session = PlanSession(ws, cfg)
        rb = next(
            iter(
                __import__(
                    "romfarmer.driver.spec_resolve", fromlist=["resolve_build"]
                ).resolve_build(_spec(), cfg, workspace_root=ws)
            )
        )
        cat = session.catalog(rb)
        assert inventory_digest(cat) == inventory_digest(cat)
        assert inventory_digest(cat) != inventory_digest(cat.without({cat.units[0].unit_id}))


@pytest.mark.skipif(not (CONFIG / "platforms" / "nes.yaml").exists(), reason="needs repo config/")
def test_inventory_digest_sees_same_size_content_change(tmp_path: Path) -> None:
    """A repaired ROM at the same path and size must change the digest (G4 #3 class)."""
    from romfarmer.driver.spec_resolve import resolve_build

    ws, cfg = _workspace(tmp_path)
    (rb,) = resolve_build(_spec(), cfg, workspace_root=ws)
    a = inventory_digest(PlanSession(ws, cfg).catalog(rb))
    zp = ws / "nes" / "Alpha (USA).zip"
    with zipfile.ZipFile(zp, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.writestr("Alpha (USA).nes", b"y" * 3000)  # same size, different bytes
    b = inventory_digest(PlanSession(ws, cfg).catalog(rb))  # fresh session → re-catalog
    assert a != b


@pytest.mark.skipif(not (CONFIG / "platforms" / "nes.yaml").exists(), reason="needs repo config/")
def test_detail_on_request_and_correctness_warnings(tmp_path: Path) -> None:
    """Silent-substitution sweep: defaults are named, a wrong chain is flagged, detail is opt-in."""
    ws, cfg = _workspace(tmp_path)
    session = PlanSession(ws, cfg)
    summary = session.dry_run(_spec())
    full = summary.to_dict()["platforms"][0]
    slim = summary.to_dict(detail=set())["platforms"][0]
    assert "heaviest" in full and "bytes_kept_at_rating" in full
    assert "heaviest" not in slim and slim["detail"].startswith("omitted")
    assert len(summary.to_json(detail=set())) < len(summary.to_json())
    # the spec stated extraction/compression = none → passthrough; batocera prefers 7z for nes
    assert any("not the frontend's preferred" in w for w in full["warnings"]), full["warnings"]


@pytest.mark.skipif(not (CONFIG / "platforms" / "nes.yaml").exists(), reason="needs repo config/")
def test_defaults_are_named_in_notes(tmp_path: Path) -> None:
    from romfarmer.driver.spec_resolve import resolve_build

    ws, cfg = _workspace(tmp_path)
    raw = _spec().to_dict()
    raw["platforms"][0].pop("extraction")
    raw["platforms"][0].pop("compression")
    (rb,) = resolve_build(Spec.from_dict(raw), cfg, workspace_root=ws)
    assert any("extraction defaulted" in n for n in rb.notes) and any(
        "compression defaulted" in n for n in rb.notes
    )
    assert rb.chain != ("passthrough",)
