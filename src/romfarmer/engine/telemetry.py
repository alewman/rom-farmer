"""UnitTelemetryStore — per-unit (source_bytes → output_bytes) records.

This is the feedback loop for the ``CostModel``: EXECUTE records, for every
unit that produced terminal artifacts, how many source bytes went in and how
many output bytes came out, keyed by ``(platform, tool)`` where *tool* is the
first element of the negotiated ``FormatChain`` (``"chd"``, ``"7z"``, …).

Design:
- Raw ``sqlite3`` on the shared ``romfarmer.db`` (same file as the action
  cache), WAL mode.  No ORM, no ``game_id`` join — the legacy
  ``rom_transformations`` table needed a ``ScrapedGame`` join and lost 22 % of
  its rows to NULL ``game_id``.
- **Write-time filter**: a record with ``source_bytes <= 0`` or
  ``output/source > MAX_RATIO`` is a corrupt observation (the legacy table
  holds xbox360 rows at 13×), not a wide distribution.  It is rejected and
  logged, never stored.  Ratios slightly above 1.0 are legitimate
  (incompressible payload + container overhead), hence 1.5.
- Idempotent per ``(platform, tool, unit_id)`` so cache-hit rebuilds do not
  inflate the sample count.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_RATIO = 1.5

_DDL = """
CREATE TABLE IF NOT EXISTS unit_telemetry (
    platform      TEXT    NOT NULL,
    tool          TEXT    NOT NULL,
    unit_id       TEXT    NOT NULL,
    source_bytes  INTEGER NOT NULL,
    output_bytes  INTEGER NOT NULL,
    tool_version  TEXT    NOT NULL DEFAULT '',
    created_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    PRIMARY KEY (platform, tool, unit_id)
);
CREATE INDEX IF NOT EXISTS ix_unit_telemetry_key ON unit_telemetry (platform, tool);
"""


class UnitTelemetryStore:
    """SQLite facade over ``unit_telemetry``.  Sole writer: the EXECUTE phase."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False, isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=30000")
        self._conn.executescript(_DDL)

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> UnitTelemetryStore:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    # ------------------------------------------------------------------

    def record(
        self,
        platform: str,
        tool: str,
        unit_id: str,
        source_bytes: int,
        output_bytes: int,
        tool_version: str = "",
    ) -> bool:
        """Store one observation.  Returns ``False`` (and logs) if rejected."""
        if source_bytes <= 0 or output_bytes < 0:
            logger.warning(
                "telemetry rejected %s/%s %s: source_bytes=%d output_bytes=%d",
                platform,
                tool,
                unit_id[:12],
                source_bytes,
                output_bytes,
            )
            return False
        ratio = output_bytes / source_bytes
        if ratio > MAX_RATIO:
            logger.warning(
                "telemetry rejected %s/%s %s: ratio %.2f > %.1f (corrupt observation)",
                platform,
                tool,
                unit_id[:12],
                ratio,
                MAX_RATIO,
            )
            return False
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO unit_telemetry
                    (platform, tool, unit_id, source_bytes, output_bytes, tool_version)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(platform, tool, unit_id) DO UPDATE SET
                    source_bytes = excluded.source_bytes,
                    output_bytes = excluded.output_bytes,
                    tool_version = excluded.tool_version,
                    created_at   = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
                """,
                (platform, tool, unit_id, source_bytes, output_bytes, tool_version),
            )
        return True

    def ratio(self, platform: str, tool: str) -> tuple[float, int] | None:
        """``(sum(output)/sum(source), n)`` for the key, or ``None`` when n == 0."""
        row = self._conn.execute(
            "SELECT SUM(output_bytes), SUM(source_bytes), COUNT(*) FROM unit_telemetry "
            "WHERE platform = ? AND tool = ?",
            (platform, tool),
        ).fetchone()
        if row is None or not row[2] or not row[1]:
            return None
        return float(row[0]) / float(row[1]), int(row[2])

    def quantiles(self, platform: str, tool: str) -> dict[str, float]:
        """Per-unit ratio quantiles ``{p10, p50, p90}`` (empty dict when no data)."""
        rows = self._conn.execute(
            "SELECT output_bytes * 1.0 / source_bytes FROM unit_telemetry "
            "WHERE platform = ? AND tool = ? ORDER BY 1",
            (platform, tool),
        ).fetchall()
        if not rows:
            return {}
        vals = [float(r[0]) for r in rows]
        n = len(vals)

        def pick(q: float) -> float:
            return vals[min(n - 1, int(q * n))]

        return {"p10": pick(0.10), "p50": pick(0.50), "p90": pick(0.90), "n": float(n)}
