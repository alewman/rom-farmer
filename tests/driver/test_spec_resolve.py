"""Spec → RESOLVE: resolve_build, curated artifacts, and the legacy shim.

Invariant 9 (intent brief): same spec_hash + same catalog inputs → identical
BuildPlan.  Shown here at the RESOLVE level: the shim-lowered Spec resolves to
the same BuildManifest the legacy path produces.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from romfarmer.driver.curated import freeze_lists, load_curated, write_curated
from romfarmer.driver.spec_resolve import compose_target, resolve_build
from romfarmer.ir.spec import Spec, SpecError

CONFIG = Path(__file__).resolve().parents[2] / "config"


def _spec(tmp_path: Path, **plat: object) -> Spec:
    src = tmp_path / "snes"
    src.mkdir(exist_ok=True)
    base = {
        "platform": "snes",
        "sources": [str(src)],
        "extraction": "cartridge",
        "compression": "zip",
        "dat": {"retool_1g1r": True},
        "passes": {"rating": {"min": 0.7, "unrated": "keep"}, "budget": {"max_bytes": 10**9}},
    }
    base.update(plat)
    return Spec.from_dict(
        {
            "target": {
                "frontend": "rocknix",
                "device": "r36s",
                "storage_bytes": 10**10,
                "reserve_bytes": 10**9,
            },
            "platforms": [base],
        }
    )


@pytest.mark.skipif(not (CONFIG / "platforms" / "snes.yaml").exists(), reason="needs repo config/")
class TestResolveBuild:
    def test_resolves_against_real_config(self, tmp_path: Path) -> None:
        spec = _spec(tmp_path)
        (rb,) = resolve_build(spec, CONFIG, workspace_root=tmp_path)
        assert rb.platform == "snes"
        assert rb.chain == ("zip",)  # rocknix has no 7z; spec said zip
        m = rb.manifest
        assert m.platform == "snes" and m.chain == ("zip",)
        assert m.rating_min == 0.7 and m.rating_unrated == "keep"
        assert m.budget_bytes == 10**9 and m.one_g_one_r is False
        assert rb.output_dir == tmp_path / "output" / f"spec-{spec.spec_hash()[:12]}" / "snes"

    def test_is_pure(self, tmp_path: Path) -> None:
        spec = _spec(tmp_path)
        a = resolve_build(spec, CONFIG, workspace_root=tmp_path)
        b = resolve_build(spec, CONFIG, workspace_root=tmp_path)
        assert a == b

    def test_retool_flag_must_match_dat(self, tmp_path: Path) -> None:
        with pytest.raises(SpecError, match="retool_1g1r"):
            resolve_build(
                _spec(tmp_path, dat={"retool_1g1r": False}), CONFIG, workspace_root=tmp_path
            )

    def test_missing_source_dir_is_loud(self, tmp_path: Path) -> None:
        spec = _spec(tmp_path, sources=[str(tmp_path / "nope")])
        with pytest.raises(SpecError, match="source directory not found"):
            resolve_build(spec, CONFIG, workspace_root=tmp_path)

    def test_unknown_platform_is_loud(self, tmp_path: Path) -> None:
        with pytest.raises(SpecError, match="config/platforms"):
            resolve_build(_spec(tmp_path, platform="ghostconsole"), CONFIG, workspace_root=tmp_path)

    def test_curated_ref_flows_into_manifest(self, tmp_path: Path) -> None:
        art = write_curated(
            "snes-test",
            [
                {"canonical_name": "Keep Me (USA)", "action": "include"},
                {"canonical_name": "Drop Me (USA)", "action": "exclude", "reason": "bad"},
            ],
            tmp_path / "artifacts",
            generated_by="test",
        )
        spec = _spec(
            tmp_path,
            passes={"curated_lists": {"ref": art.ref}, "rating": {"min": 0.7, "unrated": "keep"}},
        )
        (rb,) = resolve_build(spec, CONFIG, workspace_root=tmp_path)
        assert rb.manifest.curated_include == frozenset({"Keep Me (USA)"})
        assert rb.manifest.curated_exclude == frozenset({"Drop Me (USA)"})

    def test_compose_target_unknown_is_loud(self) -> None:
        with pytest.raises(SpecError):
            compose_target("nosuchfrontend", "r36s", CONFIG)


class TestCuratedArtifacts:
    def test_write_is_deterministic_and_verified(self, tmp_path: Path) -> None:
        e = [{"canonical_name": "B"}, {"canonical_name": "A", "action": "exclude"}]
        a = write_curated("x", e, tmp_path, generated_by="t")
        b = write_curated("x", list(reversed(e)), tmp_path, generated_by="t")
        assert a.ref == b.ref
        loaded = load_curated(a.ref, tmp_path)
        assert loaded.include == frozenset({"B"}) and loaded.exclude == frozenset({"A"})

    def test_tampered_artifact_is_rejected(self, tmp_path: Path) -> None:
        a = write_curated("x", [{"canonical_name": "A"}], tmp_path, generated_by="t")
        path = tmp_path / "curated" / "x" / f"{a.sha256}.yaml"
        path.write_text(path.read_text() + "\n# tampered\n")
        with pytest.raises(SpecError, match="refusing"):
            load_curated(a.ref, tmp_path)

    def test_name_only_ref_is_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(SpecError, match="sha256"):
            load_curated("curated/x", tmp_path)

    def test_freeze_lists(self, tmp_path: Path) -> None:
        lists = tmp_path / "lists"
        lists.mkdir()
        (lists / "snes-delete").write_text("Bad (USA).sfc\n")
        (lists / "snes+Best").write_text("Good (USA).sfc\n")
        art = freeze_lists("snes", lists, tmp_path / "artifacts")
        assert art is not None and art.name == "snes-lists"
        assert art.exclude == frozenset({"Bad (USA)"}) and art.include == frozenset({"Good (USA)"})
        assert freeze_lists("nes", lists, tmp_path / "artifacts") is None


@pytest.mark.skipif(
    not (CONFIG / "builds" / "smoke-nes-7z.yaml").exists(), reason="needs repo config/"
)
class TestLegacyShim:
    def test_shim_matches_legacy_resolve(self, tmp_path: Path) -> None:
        """The lowered Spec resolves to the same manifest as the legacy path."""
        from romfarmer.driver.spec_resolve import spec_from_build
        from romfarmer.new_orchestrator import NewBuildOrchestrator

        try:
            orch = NewBuildOrchestrator.from_config("smoke-nes-7z")
            legacy = orch.resolve(orch.resolved_configs[0])
        except Exception as exc:  # source dirs live on this host's NAS only
            pytest.skip(f"legacy build not resolvable here: {exc}")
        spec = spec_from_build("smoke-nes-7z", artifacts_dir=tmp_path / "artifacts")
        (rb,) = resolve_build(
            spec, CONFIG, workspace_root=CONFIG.parent, artifacts_dir=tmp_path / "artifacts"
        )
        assert rb.chain == legacy.chain
        assert rb.manifest == legacy.manifest
        assert (
            spec.spec_hash()
            == spec_from_build("smoke-nes-7z", artifacts_dir=tmp_path / "a2").spec_hash()
        )
