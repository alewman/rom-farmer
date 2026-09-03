"""UnitTelemetryStore — the CostModel feedback loop (intent brief v4 §3)."""

from __future__ import annotations

from pathlib import Path

from romfarmer.engine.telemetry import MAX_RATIO, UnitTelemetryStore


def test_records_and_aggregates(tmp_path: Path) -> None:
    with UnitTelemetryStore(tmp_path / "t.db") as t:
        assert t.record("psx", "chd", "u1", 1000, 500)
        assert t.record("psx", "chd", "u2", 3000, 1500)
        assert t.ratio("psx", "chd") == (0.5, 2)
        assert t.ratio("psx", "7z") is None
        q = t.quantiles("psx", "chd")
        assert q["n"] == 2 and 0.0 < q["p50"] <= 1.0


def test_write_time_filter_rejects_corrupt_rows(tmp_path: Path) -> None:
    with UnitTelemetryStore(tmp_path / "t.db") as t:
        assert not t.record("x360", "xiso", "bad", 100, int(100 * (MAX_RATIO + 1)))  # 2.5×
        assert not t.record("x360", "xiso", "zero", 0, 10)
        assert t.record("x360", "xiso", "ok", 100, 120)  # 1.2× is legitimate (container overhead)
        assert t.ratio("x360", "xiso") == (1.2, 1)


def test_idempotent_per_unit(tmp_path: Path) -> None:
    with UnitTelemetryStore(tmp_path / "t.db") as t:
        t.record("snes", "7z", "u1", 100, 90)
        t.record("snes", "7z", "u1", 100, 88)  # rebuild, cache hit — same unit
        assert t.ratio("snes", "7z") == (0.88, 1)
