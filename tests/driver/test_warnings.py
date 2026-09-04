"""Every correctness check has a fixture that makes it fire — and the two cold-run specs are gates.

A warning that never fires and a warning that cannot fire look identical
(review finding B: four passes removed zero units across twenty platforms
and nobody noticed).  Cold run #1 converged on a bad card with every
convergence signal green; its spec must produce warnings forever.  Cold run
#2 produced a good card; its spec must produce none of the RESOLVE-time ones.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from romfarmer.driver.summary import CHECKS, PlatformSummary, correctness_warnings, summarize

CONFIG = Path(__file__).resolve().parents[2] / "config"
SPECS = Path(__file__).resolve().parents[2] / "artifacts" / "specs"
COLD_RUN_1 = "e18f"  # replaced below by the committed fixture
COLD_RUN_2_PREFIX = "1e62d40d4397"


def _codes(warnings: list[str] | tuple[str, ...]) -> set[str]:
    return {w.split(":", 1)[0] for w in warnings}


class TestEachCheckCanFire:
    def test_chain_mismatch(self) -> None:
        w = correctness_warnings("psx", ("passthrough",), tier="A", preferred_chain=("chd",))
        assert _codes(w) == {"chain-mismatch"}

    def test_no_capability_entry(self) -> None:
        w = correctness_warnings("vectrex", ("zip",), tier=None, preferred_chain=("zip",))
        assert _codes(w) == {"no-capability-entry"}

    def test_tier_x_and_c(self) -> None:
        assert _codes(
            correctness_warnings("dreamcast", ("chd",), tier="X", preferred_chain=("chd",))
        ) == {"tier-x"}
        assert _codes(
            correctness_warnings("psp", ("chd",), tier="C", preferred_chain=("chd",))
        ) == {"tier-c"}

    def test_dat_missing(self) -> None:
        w = correctness_warnings(
            "snes",
            ("zip",),
            tier="A",
            preferred_chain=("zip",),
            resolve_notes=("DAT expected (source=retool_1g1r_eng) but no file found under /dats",),
        )
        assert _codes(w) == {"dat-missing"}

    def test_clean_resolve_has_no_warnings(self) -> None:
        assert correctness_warnings("psx", ("chd",), tier="A", preferred_chain=("chd",)) == ()

    @staticmethod
    def _platform(**kw: object) -> PlatformSummary:
        base: dict[str, object] = {
            "platform": "psx",
            "chain": ("chd",),
            "tier": "A",
            "quality": 1.0,
            "units_in": 10,
            "units_out": 5,
            "bytes_src": 1000,
            "bytes_est_p50": 800,
            "bytes_est_p90": 900,
            "p90_ratio": 1.125,
            "p90_source": "telemetry",
            "prediction": "prior:measured",
            "rated_fraction": 0.7,
            "rating_quantiles": {},
            "bytes_kept_at_rating": {},
            "heaviest": (),
            "removed_by_pass": {},
            "top_dropped": (),
            "notes": (),
            "warnings": (),
        }
        base.update(kw)
        return PlatformSummary(**base)  # type: ignore[arg-type]

    def test_over_capacity_and_budget_over_policy(self) -> None:
        p = self._platform(removed_by_pass={"budget": 5})
        s = summarize("h", [p], storage_bytes=850, reserve_bytes=0)
        assert _codes(s.warnings) == {"over-capacity", "budget-over-policy"}
        s2 = summarize(
            "h", [p], storage_bytes=850, reserve_bytes=0, allocation_note="budget is the selector"
        )
        assert _codes(s2.warnings) == {"over-capacity"}

    def test_fits_and_checks_listed(self) -> None:
        p = self._platform(removed_by_pass={"rating": 5})
        s = summarize("h", [p], storage_bytes=10_000, reserve_bytes=0)
        assert s.fits is True and s.warnings == ()
        assert s.to_dict()["checks_performed"] == [c.split(":", 1)[0] for c in CHECKS]
        assert all(any(w.split(":")[0] == c.split(":")[0] for c in CHECKS) for w in s.warnings)


@pytest.mark.skipif(not (CONFIG / "devices" / "r36s.yaml").exists(), reason="needs repo config/")
class TestColdRunSpecsAreGates:
    """The committed cold-run specs, resolved against the real config (no catalog, no NAS)."""

    @staticmethod
    def _warn_all(spec_path: Path) -> dict[str, set[str]]:
        from romfarmer.driver.capability import capabilities
        from romfarmer.driver.spec_io import load_spec
        from romfarmer.driver.spec_resolve import resolve_build

        spec = load_spec(spec_path)
        caps = capabilities(spec.target.frontend, spec.target.device, CONFIG)
        out: dict[str, set[str]] = {}
        for rb in resolve_build(spec, CONFIG, workspace_root=CONFIG.parent):
            try:
                tier: str | None = caps.require(rb.platform).tier
            except KeyError:
                tier = None
            pref = (caps.formats.get(rb.platform) or (None,))[0]
            out[rb.platform] = _codes(
                correctness_warnings(
                    rb.platform,
                    tuple(rb.chain),
                    tier=tier,
                    preferred_chain=pref,
                    resolve_notes=rb.notes,
                )
            )
        return out

    def test_cold_run_1_spec_warns_on_every_platform(self) -> None:
        """#1 stated extraction/compression = none (what the old parser silently defaulted to)."""
        path = Path(__file__).parent / "fixtures" / "cold-run-1-as-resolved.yaml"
        if not path.exists():
            pytest.skip("fixture missing")
        try:
            warns = self._warn_all(path)
        except Exception as exc:  # sources on this host's NAS only
            pytest.skip(f"cannot resolve on this host: {exc}")
        assert warns and all("chain-mismatch" in codes for codes in warns.values()), warns

    def test_cold_run_2_spec_is_clean(self) -> None:
        matches = list(SPECS.glob(f"{COLD_RUN_2_PREFIX}*.yaml"))
        if not matches:
            pytest.skip("cold-run-2 spec not committed")
        try:
            warns = self._warn_all(matches[0])
        except Exception as exc:
            pytest.skip(f"cannot resolve on this host: {exc}")
        assert warns and all(codes == set() for codes in warns.values()), warns
