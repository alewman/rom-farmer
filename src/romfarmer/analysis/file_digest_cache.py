"""File digest cache — fast-path memoisation for CATALOG phase.

Avoids re-hashing unchanged source files on every build by storing
``(size, mtime_ns, inode) → md5`` in a lightweight SQLite table.

Design follows Git's index and Bazel's digest cache:
- Hit requires ALL THREE of (size, mtime_ns, inode) to match.
- Racy guard: if a file's mtime_ns falls within the same second as the
  scan's start time, the entry is treated as a miss (re-hash anyway).
  This matches the "racy-stat" guard in Git.
- Writer: CatalogBuilder only — sole-writer doctrine.

Known failure modes and their status:
- Coarse mtime (FAT, 2 s granularity): covered by racy guard.
- mtime-preserving replace (rsync -a): the only true hole; accepted risk
  with a ``force_rehash=True`` escape hatch on CatalogBuilder.build().
- NFS unstable inodes: not this deployment.
- Reflink copies: get new inodes → correct cache miss.
"""

from __future__ import annotations

import logging
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

_DDL = """
CREATE TABLE IF NOT EXISTS file_digest_cache (
    path        TEXT    PRIMARY KEY,
    size        INTEGER NOT NULL,
    mtime_ns    INTEGER NOT NULL,
    inode       INTEGER NOT NULL,
    md5         TEXT,
    updated_at  TEXT    NOT NULL
        DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
"""

# Added after the initial schema: dominant zip member (name, crc32, size) so
# a warm CATALOG needs no zip I/O at all.  NULL for non-zip files.
_MIGRATIONS = (
    "ALTER TABLE file_digest_cache ADD COLUMN member_name TEXT",
    "ALTER TABLE file_digest_cache ADD COLUMN member_crc32 INTEGER",
    "ALTER TABLE file_digest_cache ADD COLUMN member_size INTEGER",
)


@dataclass(frozen=True, slots=True)
class DigestEntry:
    md5: str | None
    member_name: str | None = None
    member_crc32: int | None = None
    member_size: int | None = None


class FileDigestCache:
    """Fast-path md5 cache keyed on ``(size, mtime_ns, inode)`` triples.

    Thread-safe for concurrent readers under WAL mode.
    ``CatalogBuilder`` is the sole writer of this table.
    """

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False, isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=30000")
        self._conn.executescript(_DDL)
        existing = {r[1] for r in self._conn.execute("PRAGMA table_info(file_digest_cache)")}
        for stmt in _MIGRATIONS:
            if stmt.split(" ADD COLUMN ")[1].split()[0] not in existing:
                self._conn.execute(stmt)

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> FileDigestCache:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def lookup(
        self,
        path: Path,
        stat: os.stat_result,
        scan_start_ns: int,
    ) -> str | None:
        """Return cached md5 if the stat triple matches; ``None`` on miss."""
        entry = self.lookup_entry(path, stat, scan_start_ns)
        return entry.md5 if entry is not None else None

    def lookup_entry(
        self,
        path: Path,
        stat: os.stat_result,
        scan_start_ns: int,
    ) -> DigestEntry | None:
        """Return the full cached entry if the stat triple matches; ``None`` on miss.

        Racy guard: if ``stat.st_mtime_ns // 1_000_000_000`` equals
        ``scan_start_ns // 1_000_000_000``, the entry is treated as a miss
        regardless of the cached value.
        """
        # Racy guard: mtime within the current second → force re-hash
        if stat.st_mtime_ns // 1_000_000_000 >= scan_start_ns // 1_000_000_000:
            return None

        row = self._conn.execute(
            "SELECT md5, member_name, member_crc32, member_size FROM file_digest_cache "
            "WHERE path = ? AND size = ? AND mtime_ns = ? AND inode = ?",
            (str(path), stat.st_size, stat.st_mtime_ns, stat.st_ino),
        ).fetchone()
        if row is None:
            return None
        return DigestEntry(
            md5=str(row[0]) if row[0] is not None else None,
            member_name=row[1],
            member_crc32=row[2],
            member_size=row[3],
        )

    def store(
        self,
        path: Path,
        stat: os.stat_result,
        md5: str | None,
        member: tuple[str, int, int] | None = None,
    ) -> None:
        """Upsert the digest entry for *path* (``member`` = name, crc32, size)."""
        name, crc, size = member if member is not None else (None, None, None)
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO file_digest_cache
                    (path, size, mtime_ns, inode, md5, member_name, member_crc32, member_size)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    size     = excluded.size,
                    mtime_ns = excluded.mtime_ns,
                    inode    = excluded.inode,
                    md5      = excluded.md5,
                    member_name  = excluded.member_name,
                    member_crc32 = excluded.member_crc32,
                    member_size  = excluded.member_size,
                    updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
                """,
                (str(path), stat.st_size, stat.st_mtime_ns, stat.st_ino, md5, name, crc, size),
            )

    def prune_missing(self, known_paths: set[str]) -> int:
        """Delete rows for paths no longer in *known_paths*.  Returns count."""
        rows = self._conn.execute("SELECT path FROM file_digest_cache").fetchall()
        to_delete = [r[0] for r in rows if r[0] not in known_paths]
        if to_delete:
            with self._conn:
                self._conn.executemany(
                    "DELETE FROM file_digest_cache WHERE path = ?",
                    [(p,) for p in to_delete],
                )
        return len(to_delete)
