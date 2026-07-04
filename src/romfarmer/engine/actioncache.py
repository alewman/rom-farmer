"""ActionCache — the new SQLite-backed action cache for the ROM Farmer engine.

Uses raw sqlite3 (no SQLAlchemy) over two new tables in the shared
``metadata/database/romfarmer.db``:

  action_cache(key, outputs_json, tool, tool_version, created_at)
  artifact_aliases(sha256, md5, zip_crc32, zip_size, zip_member)

This module is the **SOLE WRITER** of ``artifact_aliases``. Every
known alias for an artifact is written atomically in one transaction
(method ``record_aliases``). This is the structural fix for the
MD5-vs-CRC32 cache divergence described in system briefing §3.9:
previously, CAS ingest and DAT matching each wrote their own alias
independently, so a lookup by the *other* alias missed even though
the file was cached.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Sequence

from romfarmer.ir.actions import ActionKey
from romfarmer.ir.identity import Identity, ZipIdentity

# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------

_DDL = """
CREATE TABLE IF NOT EXISTS action_cache (
    key          TEXT PRIMARY KEY,
    outputs_json TEXT NOT NULL,
    tool         TEXT NOT NULL,
    tool_version TEXT NOT NULL,
    created_at   TEXT NOT NULL
        DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS artifact_aliases (
    sha256      TEXT NOT NULL,
    md5         TEXT,
    zip_crc32   INTEGER,
    zip_size    INTEGER,
    zip_member  TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_aliases_sha256
    ON artifact_aliases (sha256);

CREATE INDEX IF NOT EXISTS ix_aliases_md5
    ON artifact_aliases (md5)
    WHERE md5 IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_aliases_zip
    ON artifact_aliases (zip_crc32, zip_size)
    WHERE zip_crc32 IS NOT NULL;
"""


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def _identity_to_dict(ident: Identity) -> dict[str, object]:
    d: dict[str, object] = {
        "sha256": ident.sha256,
        "md5": ident.md5,
        "size": ident.size,
    }
    if ident.zip_identity is not None:
        d["zip_crc32"] = ident.zip_identity.member_crc32
        d["zip_size"] = ident.zip_identity.member_size
        d["zip_member"] = ident.zip_identity.member_name
    return d


def _dict_to_identity(d: dict[str, object]) -> Identity:
    zi: ZipIdentity | None = None
    crc_val = d.get("zip_crc32")
    sz_val = d.get("zip_size")
    mem_val = d.get("zip_member")
    if crc_val is not None and sz_val is not None and mem_val is not None:
        zi = ZipIdentity(
            member_crc32=int(str(crc_val)),
            member_size=int(str(sz_val)),
            member_name=str(mem_val),
        )
    size_val = d.get("size")
    sha_val = d.get("sha256")
    md5_val = d.get("md5")
    return Identity(
        sha256=str(sha_val) if sha_val else None,
        md5=str(md5_val) if md5_val else None,
        size=int(str(size_val)) if size_val is not None else None,
        zip_identity=zi,
    )


# ---------------------------------------------------------------------------
# ActionCache
# ---------------------------------------------------------------------------

class ActionCache:
    """SQLite facade over ``action_cache`` + ``artifact_aliases`` tables.

    Thread-safe for concurrent readers; writes are serialised by SQLite's
    WAL mode.  The database file is the shared ``romfarmer.db`` so the
    tables coexist with the existing ``rom_cache`` / ``rom_transformation``
    etc. tables.
    """

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(
            str(db_path), check_same_thread=False, isolation_level=None
        )
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(_DDL)

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "ActionCache":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Action cache operations
    # ------------------------------------------------------------------

    def get(self, key: ActionKey) -> tuple[Identity, ...] | None:
        """Return cached output identities for *key*, or ``None`` on miss."""
        row = self._conn.execute(
            "SELECT outputs_json FROM action_cache WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            return None
        raw: list[dict[str, object]] = json.loads(row[0])
        return tuple(_dict_to_identity(d) for d in raw)

    def store(
        self,
        key: ActionKey,
        outputs: Sequence[Identity],
        tool: str,
        tool_version: str,
    ) -> None:
        """Store action outputs and atomically write all known aliases.

        On conflict (same key already present) the existing row is kept —
        identical ActionKey means identical result by construction.
        """
        outputs_json = json.dumps([_identity_to_dict(o) for o in outputs])
        with self._conn:
            self._conn.execute(
                """
                INSERT OR IGNORE INTO action_cache
                    (key, outputs_json, tool, tool_version)
                VALUES (?, ?, ?, ?)
                """,
                (key, outputs_json, tool, tool_version),
            )
            for ident in outputs:
                if ident.sha256 is not None:
                    self._record_aliases_in_tx(ident)

    # ------------------------------------------------------------------
    # Alias operations  (SOLE WRITER of artifact_aliases)
    # ------------------------------------------------------------------

    def record_aliases(self, identity: Identity) -> None:
        """Atomically write all known aliases for *identity*.

        ``identity.sha256`` MUST be set — the executor only calls this
        after computing or verifying the sha256 of an output file.

        Raises:
            ValueError: if ``identity.sha256`` is None.
        """
        if identity.sha256 is None:
            raise ValueError(
                "ActionCache.record_aliases requires a non-null sha256"
            )
        with self._conn:
            self._record_aliases_in_tx(identity)

    def _record_aliases_in_tx(self, identity: Identity) -> None:
        """Write alias row inside the caller's transaction (no commit)."""
        assert identity.sha256 is not None
        zi = identity.zip_identity
        self._conn.execute(
            """
            INSERT INTO artifact_aliases (sha256, md5, zip_crc32, zip_size, zip_member)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(sha256) DO UPDATE SET
                md5        = COALESCE(excluded.md5, md5),
                zip_crc32  = COALESCE(excluded.zip_crc32, zip_crc32),
                zip_size   = COALESCE(excluded.zip_size, zip_size),
                zip_member = COALESCE(excluded.zip_member, zip_member)
            """,
            (
                identity.sha256,
                identity.md5,
                zi.member_crc32 if zi else None,
                zi.member_size if zi else None,
                zi.member_name if zi else None,
            ),
        )

    def lookup_by_md5(self, md5: str) -> Identity | None:
        """Look up the full identity for a file known by its MD5 alias."""
        row = self._conn.execute(
            "SELECT sha256, md5, zip_crc32, zip_size, zip_member "
            "FROM artifact_aliases WHERE md5 = ?",
            (md5,),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_identity(row)

    def lookup_by_zip(
        self, crc32: int, size: int, member: str | None = None
    ) -> Identity | None:
        """Look up the full identity for a file known by its ZIP identity."""
        if member is not None:
            row = self._conn.execute(
                "SELECT sha256, md5, zip_crc32, zip_size, zip_member "
                "FROM artifact_aliases "
                "WHERE zip_crc32 = ? AND zip_size = ? AND zip_member = ?",
                (crc32, size, member),
            ).fetchone()
        else:
            row = self._conn.execute(
                "SELECT sha256, md5, zip_crc32, zip_size, zip_member "
                "FROM artifact_aliases WHERE zip_crc32 = ? AND zip_size = ?",
                (crc32, size),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_identity(row)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_identity(
        row: tuple[str | None, str | None, int | None, int | None, str | None],
    ) -> Identity:
        sha256, md5, zip_crc32, zip_size, zip_member = row
        zi: ZipIdentity | None = None
        if zip_crc32 is not None and zip_size is not None and zip_member is not None:
            zi = ZipIdentity(
                member_crc32=zip_crc32,
                member_size=zip_size,
                member_name=zip_member,
            )
        return Identity(sha256=sha256, md5=md5, zip_identity=zi)
