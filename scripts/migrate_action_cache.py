#!/usr/bin/env python3
"""Idempotent backfill: every ROMCache row → action_cache + artifact_aliases.

Usage:
    python scripts/migrate_action_cache.py [--db path/to/romfarmer.db]

Run twice → identical row counts (idempotence guaranteed by
INSERT OR IGNORE / ON CONFLICT DO UPDATE).

This script enables the new ActionCache to find entries built by the legacy
CacheManager, bridging the two cache systems during Phases 2-4.

Mapping:
  rom_cache.source_md5              → artifact_aliases.md5
  rom_cache.source_zip_crc32        → artifact_aliases.zip_crc32
  rom_cache.source_zip_content_size → artifact_aliases.zip_size
  rom_cache.source_filename         → artifact_aliases.zip_member
  sha256(cache_file)                → artifact_aliases.sha256

  ActionKey is synthetic:
    sha256(JSON{"inputs":[], "params":{"format":..., "params_hash":...},
                "tool":..., "tool_version":...})
  where inputs=[] because we don't have sha256 for the SOURCE file —
  only the OUTPUT sha256.  These rows provide alias lookup without being
  valid ActionKeys that the executor would use for cache hits.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sqlite3
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _sha256_file(path: Path) -> str | None:
    """Compute sha256 of *path*; return None if the file is missing."""
    if not path.exists():
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1_048_576), b""):
            h.update(chunk)
    return h.hexdigest()


def _synthetic_action_key(tool: str, tool_version: str, fmt: str, params_hash: str) -> str:
    """Synthetic ActionKey for backfilled rows (no source sha256 available)."""
    canonical = json.dumps(
        {
            "inputs": [],
            "params": {"format": fmt, "params_hash": params_hash},
            "tool": tool or "unknown",
            "tool_version": tool_version or "unknown",
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def migrate(db_path: Path, cache_base_dir: Path) -> tuple[int, int, int]:
    """Backfill all ROMCache rows into action_cache + artifact_aliases.

    Returns:
        (processed, stored_actions, stored_aliases)
    """
    conn = sqlite3.connect(str(db_path), isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL")

    # Ensure target tables exist (ActionCache DDL)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS action_cache (
            key          TEXT PRIMARY KEY,
            outputs_json TEXT NOT NULL,
            tool         TEXT NOT NULL,
            tool_version TEXT NOT NULL,
            created_at   TEXT NOT NULL
                DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
        );
        CREATE TABLE IF NOT EXISTS artifact_aliases (
            sha256     TEXT NOT NULL,
            md5        TEXT,
            zip_crc32  INTEGER,
            zip_size   INTEGER,
            zip_member TEXT
        );
        CREATE UNIQUE INDEX IF NOT EXISTS ix_aliases_sha256 ON artifact_aliases(sha256);
        CREATE INDEX IF NOT EXISTS ix_aliases_md5 ON artifact_aliases(md5) WHERE md5 IS NOT NULL;
        CREATE INDEX IF NOT EXISTS ix_aliases_zip ON artifact_aliases(zip_crc32, zip_size) WHERE zip_crc32 IS NOT NULL;
    """)

    rows = conn.execute(
        "SELECT source_md5, format, params_hash, cache_path, "
        "       final_md5, final_size, tool_name, tool_version, "
        "       source_zip_crc32, source_zip_content_size, source_filename "
        "FROM rom_cache"
    ).fetchall()

    processed = stored_actions = stored_aliases = 0

    for row in rows:
        (source_md5, fmt, params_hash, rel_path,
         final_md5, final_size, tool_name, tool_version,
         zip_crc32_str, zip_size, src_filename) = row
        processed += 1

        # Compute sha256 of the cached output file
        cache_file = cache_base_dir / rel_path if rel_path else None
        sha256: str | None = None
        if cache_file:
            sha256 = _sha256_file(cache_file)

        if sha256 is None:
            logger.debug(f"Skipping {rel_path}: file missing or no sha256")
            continue

        # Store in action_cache (synthetic key, no real inputs)
        action_key = _synthetic_action_key(
            tool_name or "unknown",
            tool_version or "unknown",
            fmt or "unknown",
            params_hash or "",
        )
        outputs_json = json.dumps([{
            "sha256": sha256,
            "md5": final_md5,
            "size": final_size,
        }])
        with conn:
            conn.execute(
                "INSERT OR IGNORE INTO action_cache (key, outputs_json, tool, tool_version) "
                "VALUES (?, ?, ?, ?)",
                (action_key, outputs_json, tool_name or "unknown", tool_version or "unknown"),
            )
            stored_actions += conn.execute(
                "SELECT changes()"
            ).fetchone()[0]

        # Store in artifact_aliases
        zip_crc32: int | None = None
        if zip_crc32_str:
            try:
                zip_crc32 = int(zip_crc32_str, 16) if len(zip_crc32_str) <= 8 else int(zip_crc32_str)
            except (ValueError, TypeError):
                zip_crc32 = None

        with conn:
            conn.execute(
                """
                INSERT INTO artifact_aliases (sha256, md5, zip_crc32, zip_size, zip_member)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(sha256) DO UPDATE SET
                    md5       = COALESCE(excluded.md5, md5),
                    zip_crc32 = COALESCE(excluded.zip_crc32, zip_crc32),
                    zip_size  = COALESCE(excluded.zip_size, zip_size),
                    zip_member= COALESCE(excluded.zip_member, zip_member)
                """,
                (sha256, source_md5, zip_crc32, zip_size, src_filename),
            )
            stored_aliases += conn.execute("SELECT changes()").fetchone()[0]

    conn.close()
    return processed, stored_actions, stored_aliases


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db",
        default="metadata/database/romfarmer.db",
        help="Path to romfarmer.db (default: metadata/database/romfarmer.db)",
    )
    parser.add_argument(
        "--cache-dir",
        default="cache",
        help="Root of the ROM cache directory (default: cache)",
    )
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        sys.exit(1)

    cache_base = Path(args.cache_dir)
    logger.info(f"Migrating {db_path} …")
    processed, actions, aliases = migrate(db_path, cache_base)
    logger.info(
        f"Done: {processed} rows processed, "
        f"{actions} action_cache rows inserted, "
        f"{aliases} artifact_alias rows inserted/updated"
    )


if __name__ == "__main__":
    main()
