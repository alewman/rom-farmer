"""Tests for CostModel."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from romfarmer.planner.costmodel import CostModel, UnknownPlatformError


class TestCostModelPriors:
    def test_known_platform_returns_ratio(self):
        cm = CostModel()
        ratio, label = cm.ratio("psx")
        assert 0.0 < ratio <= 1.0
        assert "prior" in label

    def test_unknown_platform_raises(self):
        cm = CostModel()
        with pytest.raises(UnknownPlatformError):
            cm.ratio("totally_unknown_platform_xyz")

    def test_register_prior_overrides(self):
        cm = CostModel()
        cm.register_prior("psx", "chd", 0.42)
        ratio, _ = cm.ratio("psx", "chd")
        assert ratio == pytest.approx(0.42)

    def test_register_prior_new_platform(self):
        cm = CostModel()
        cm.register_prior("new_platform", "zip", 0.55)
        ratio, _ = cm.ratio("new_platform", "zip")
        assert ratio == pytest.approx(0.55)

    def test_all_hardcoded_platforms_known(self):
        """Every platform in _HARDCODED_PRIORS must be queryable."""
        from romfarmer.planner.costmodel import _HARDCODED_PRIORS

        cm = CostModel()
        for plat in _HARDCODED_PRIORS:
            ratio, _ = cm.ratio(plat)
            assert 0.0 < ratio <= 1.0, f"bad ratio for {plat}"


class TestCostModelSizeData:
    def test_loads_size_data_json(self, tmp_path: Path):
        data = {
            "psx": [
                {
                    "input_size_bytes": 1_000_000,
                    "output_size_bytes": 700_000,
                    "compression": "chd",
                }
            ]
        }
        sd = tmp_path / "size_data.json"
        sd.write_text(json.dumps(data))
        cm = CostModel(size_data_path=sd)
        ratio, label = cm.ratio("psx", "chd")
        assert ratio == pytest.approx(0.7, abs=0.01)

    def test_skips_zero_input(self, tmp_path: Path):
        data = {
            "psx": [
                {"input_size_bytes": 0, "output_size_bytes": 700_000, "compression": "chd"},
                {"input_size_bytes": 1_000_000, "output_size_bytes": 700_000, "compression": "chd"},
            ]
        }
        sd = tmp_path / "size_data.json"
        sd.write_text(json.dumps(data))
        cm = CostModel(size_data_path=sd)
        ratio, _ = cm.ratio("psx", "chd")
        # Only the second record should be used
        assert ratio == pytest.approx(0.7, abs=0.01)

    def test_missing_size_data_file_is_ok(self, tmp_path: Path):
        cm = CostModel(size_data_path=tmp_path / "missing.json")
        # Falls back to hardcoded priors
        ratio, _ = cm.ratio("psx")
        assert 0.0 < ratio <= 1.0

    def test_aggregates_multiple_records(self, tmp_path: Path):
        data = {
            "saturn": [
                {"input_size_bytes": 600_000, "output_size_bytes": 360_000, "compression": "chd"},
                {"input_size_bytes": 400_000, "output_size_bytes": 260_000, "compression": "chd"},
            ]
        }
        sd = tmp_path / "size_data.json"
        sd.write_text(json.dumps(data))
        cm = CostModel(size_data_path=sd)
        ratio, _ = cm.ratio("saturn", "chd")
        # (360_000 + 260_000) / (600_000 + 400_000) = 620_000 / 1_000_000 = 0.62
        assert ratio == pytest.approx(0.62, abs=0.01)


class TestCostModelPrediction:
    def test_predict_output_bytes(self):
        cm = CostModel()
        cm.register_prior("test_plat", "chd", 0.70)
        predicted, _ = cm.predict_output_bytes(1_000_000, "test_plat", "chd")
        assert predicted == 700_000

    def test_predict_unknown_platform_raises(self):
        cm = CostModel()
        with pytest.raises(UnknownPlatformError):
            cm.predict_output_bytes(100, "ghost_platform")


class TestCostModelLoudUnknown:
    """The architecture spec requires loud failure for unknown platforms.

    Gate 4 from the Phase 3 spec:
    "CostModel unit tests: prior/posterior merge, enum-keyed lookup,
    loud unknown-platform failure."
    """

    def test_unknown_is_loud_not_silent(self):
        cm = CostModel()
        # Must raise, not return a magic 0.85 default
        with pytest.raises(UnknownPlatformError) as exc_info:
            cm.ratio("nonexistent_platform_should_fail_loudly")
        assert "nonexistent_platform_should_fail_loudly" in str(exc_info.value)
