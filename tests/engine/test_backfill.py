"""Backfill idempotence test — Gate 1.

Verifies that running migrate_action_cache.py twice produces identical
row counts (INSERT OR IGNORE / ON CONFLICT DO UPDATE semantics).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from scripts.migrate_action_cache import migrate


def _setup_legacy_db(db_path: Path, cache_dir: Path) -> None:
    """Seed a minimal rom_cache table with two rows."""
    conn = sqlite3.connect(str(db_path))
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS rom_cache (
            id                       INTEGER PRIMARY KEY,
            source_md5               TEXT NOT NULL,
            format                   TEXT NOT NULL,
            params_hash              TEXT NOT NULL,
            cache_path               TEXT,
            final_md5                TEXT,
            final_size               INTEGER,
            tool_name                TEXT,
            tool_version             TEXT,
            source_zip_crc32         TEXT,
            source_zip_content_size  INTEGER,
            source_filename          TEXT,
            created_date             TEXT,
            last_used                TEXT
        );
    """)
    # Create fake cache files so sha256 can be computed
    (cache_dir / "chd" / "ab").mkdir(parents=True, exist_ok=True)
    (cache_dir / "rvz" / "cd").mkdir(parents=True, exist_ok=True)

    fake_chd = cache_dir / "chd" / "ab" / "abcdef_lzma.chd"
    fake_rvz = cache_dir / "rvz" / "cd" / "cdef12_passthrough.rvz"
    fake_chd.write_bytes(b"fake_chd_content" * 16)
    fake_rvz.write_bytes(b"fake_rvz_content" * 16)

    conn.execute(
        "INSERT INTO rom_cache VALUES (1,'abcdef1234567890abcdef1234567890','chd','lzma',"
        "'chd/ab/abcdef_lzma.chd','aabbccdd1234567890abcdef12345678',1024,"
        "'chdman','0.263','2578c3f9',1024,'Game.bin',datetime('now'),datetime('now'))"
    )
    conn.execute(
        "INSERT INTO rom_cache VALUES (2,'cdef12345678901234567890cdef1234','rvz','passthrough',"
        "'rvz/cd/cdef12_passthrough.rvz','11223344567890abcdef1234567890ab',2048,"
        "'dolphin-tool','5.0','',NULL,'Wii_Game.zip',datetime('now'),datetime('now'))"
    )
    conn.commit()
    conn.close()


class TestBackfillIdempotence:
    def test_run_twice_same_row_counts(self, tmp_path: Path) -> None:
        """Gate 1: migrate() run twice → identical row counts in both tables."""
        db = tmp_path / "romfarmer.db"
        cache_dir = tmp_path / "cache"
        _setup_legacy_db(db, cache_dir)

        # First run
        p1, a1, al1 = migrate(db, cache_dir)
        assert p1 == 2, f"Expected 2 rows processed, got {p1}"

        conn = sqlite3.connect(str(db))
        action_count_1 = conn.execute("SELECT COUNT(*) FROM action_cache").fetchone()[0]
        alias_count_1 = conn.execute("SELECT COUNT(*) FROM artifact_aliases").fetchone()[0]
        conn.close()

        # Second run — must be identical
        p2, a2, al2 = migrate(db, cache_dir)
        assert p2 == 2

        conn = sqlite3.connect(str(db))
        action_count_2 = conn.execute("SELECT COUNT(*) FROM action_cache").fetchone()[0]
        alias_count_2 = conn.execute("SELECT COUNT(*) FROM artifact_aliases").fetchone()[0]
        conn.close()

        assert action_count_1 == action_count_2, (
            f"action_cache row count changed: {action_count_1} → {action_count_2}"
        )
        assert alias_count_1 == alias_count_2, (
            f"artifact_aliases row count changed: {alias_count_1} → {alias_count_2}"
        )

    def test_aliases_populated_after_backfill(self, tmp_path: Path) -> None:
        """After backfill, artifact_aliases contains md5 and zip entries."""
        db = tmp_path / "romfarmer.db"
        cache_dir = tmp_path / "cache"
        _setup_legacy_db(db, cache_dir)
        migrate(db, cache_dir)

        conn = sqlite3.connect(str(db))
        # The first row has zip_crc32 = '2578c3f9' and source_md5 = 'abcdef...'
        row = conn.execute(
            "SELECT sha256, md5, zip_crc32 FROM artifact_aliases WHERE md5 = ?",
            ("abcdef1234567890abcdef1234567890",),
        ).fetchone()
        conn.close()

        assert row is not None, "Backfilled alias row not found by md5"
        sha256, md5, crc = row
        assert sha256 is not None, "sha256 should have been computed from cache file"
        assert int(crc) == 0x2578C3F9

    def test_missing_cache_file_skipped(self, tmp_path: Path) -> None:
        """Rows where the cache file is missing are silently skipped."""
        db = tmp_path / "romfarmer.db"
        cache_dir = tmp_path / "cache"
        _setup_legacy_db(db, cache_dir)

        # Delete one of the cache files
        (cache_dir / "rvz" / "cd" / "cdef12_passthrough.rvz").unlink()

        processed, actions, aliases = migrate(db, cache_dir)
        assert processed == 2
        # Only 1 action stored (the one with an existing file)
        assert actions == 1
