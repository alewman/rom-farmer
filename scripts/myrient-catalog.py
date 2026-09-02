#!/usr/bin/env python3
"""
Myrient Catalog Crawler
=======================
Crawls Myrient's HTTP directory listings via rclone and stores
file/directory metadata into a DuckDB database for analysis.

Usage:
    # Crawl everything (top-level collections, then systems, then files)
    python3 myrient-catalog.py

    # Crawl only specific top-level collections
    python3 myrient-catalog.py "No-Intro" "Redump" "Total DOS Collection"

    # Crawl with depth limit (1=collections, 2=systems, 3=files)
    python3 myrient-catalog.py --depth 2

    # Resume after interruption (skips already-crawled directories)
    python3 myrient-catalog.py --resume

    # Retry only systems that previously errored (with longer timeout)
    python3 myrient-catalog.py --retry-errors --timeout 3600

    # Custom timeout (seconds) for huge directories
    python3 myrient-catalog.py --timeout 1800

The DuckDB database is created at /data/emu/source/myrient-catalog.duckdb
"""

import argparse
import json
import subprocess
import sys
import time

try:
    import duckdb
except ImportError:
    print("ERROR: duckdb not installed. pip install duckdb", file=sys.stderr)
    sys.exit(1)


DB_PATH = "/data/emu/source/myrient-catalog.duckdb"
RCLONE_REMOTE = "myrient"
RCLONE_BASE_URL = "https://myrient.erista.me/files/"


def setup_rclone_remote():
    """Ensure the rclone HTTP remote is configured."""
    result = subprocess.run(
        ["rclone", "config", "create", RCLONE_REMOTE, "http", "url", RCLONE_BASE_URL],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR setting up rclone remote: {result.stderr}", file=sys.stderr)
        sys.exit(1)


def setup_database(db_path: str) -> duckdb.DuckDBPyConnection:
    """Create/open the DuckDB database and ensure schema exists."""
    con = duckdb.connect(db_path)

    con.execute("""
        CREATE TABLE IF NOT EXISTS files (
            collection  VARCHAR NOT NULL,  -- top-level: 'No-Intro', 'Redump', etc.
            system      VARCHAR NOT NULL,  -- system dir: 'Nintendo - Game Boy', etc.
            path        VARCHAR NOT NULL,  -- full relative path from collection root
            name        VARCHAR NOT NULL,  -- filename
            size        BIGINT NOT NULL,   -- file size in bytes
            is_dir      BOOLEAN NOT NULL,  -- true if directory
            crawled_at  TIMESTAMP NOT NULL DEFAULT now(),
            PRIMARY KEY (collection, system, path)
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS crawl_log (
            collection  VARCHAR NOT NULL,
            system      VARCHAR,
            depth       INTEGER NOT NULL,
            status      VARCHAR NOT NULL,  -- 'started', 'completed', 'error'
            file_count  INTEGER,
            total_bytes BIGINT,
            error_msg   VARCHAR,
            started_at  TIMESTAMP NOT NULL DEFAULT now(),
            completed_at TIMESTAMP,
            PRIMARY KEY (collection, system)
        )
    """)

    return con


# Default timeout (seconds) for rclone lsjson calls. Overridden by --timeout.
RCLONE_TIMEOUT = 600


def rclone_lsjson(remote_path: str, recursive: bool = False) -> list[dict]:
    """Run rclone lsjson and return parsed JSON list."""
    cmd = ["rclone", "lsjson", f"{RCLONE_REMOTE}:{remote_path}", "--no-modtime"]
    if recursive:
        cmd.append("--recursive")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=RCLONE_TIMEOUT)
    if result.returncode != 0:
        raise RuntimeError(f"rclone lsjson failed for '{remote_path}': {result.stderr.strip()}")

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse JSON from rclone for '{remote_path}': {e}")


def get_completed_systems(con: duckdb.DuckDBPyConnection, collection: str) -> set[str]:
    """Return set of system names already fully file-crawled (depth 3) for a collection."""
    rows = con.execute(
        "SELECT system FROM crawl_log WHERE collection = ? AND status = 'completed' AND system IS NOT NULL AND depth = 3",
        [collection],
    ).fetchall()
    return {r[0] for r in rows}


def crawl_collection_systems(con: duckdb.DuckDBPyConnection, collection: str) -> list[str]:
    """List system-level directories under a collection."""
    print(f"\n{'=' * 60}")
    print(f"Listing systems in: {collection}")
    print(f"{'=' * 60}")

    entries = rclone_lsjson(collection)
    systems = sorted([e["Name"] for e in entries if e.get("IsDir", False)])
    files_at_root = [e for e in entries if not e.get("IsDir", False)]

    # Store any files at collection root level
    if files_at_root:
        rows = [
            (collection, "(root)", e["Path"], e["Name"], e.get("Size", 0), False)
            for e in files_at_root
        ]
        con.executemany(
            """INSERT OR REPLACE INTO files (collection, system, path, name, size, is_dir)
               VALUES (?, ?, ?, ?, ?, ?)""",
            rows,
        )
        print(f"  {len(files_at_root)} files at collection root")

    print(f"  Found {len(systems)} systems")
    return systems


def crawl_system_files(
    con: duckdb.DuckDBPyConnection,
    collection: str,
    system: str,
    recursive: bool = True,
) -> tuple[int, int]:
    """Crawl all files under a system directory. Returns (file_count, total_bytes)."""
    remote_path = f"{collection}/{system}"

    # Log start
    con.execute(
        """INSERT OR REPLACE INTO crawl_log (collection, system, depth, status, started_at)
           VALUES (?, ?, 3, 'started', now())""",
        [collection, system],
    )

    try:
        entries = rclone_lsjson(remote_path, recursive=recursive)
    except Exception as e:
        con.execute(
            """UPDATE crawl_log SET status='error', error_msg=?, completed_at=now()
               WHERE collection=? AND system=?""",
            [str(e), collection, system],
        )
        raise

    file_count = 0
    total_bytes = 0
    batch = []

    for e in entries:
        size = e.get("Size", 0) if not e.get("IsDir", False) else 0
        is_dir = e.get("IsDir", False)
        batch.append((collection, system, e["Path"], e["Name"], size, is_dir))
        if not is_dir:
            file_count += 1
            total_bytes += size

    if batch:
        con.executemany(
            """INSERT OR REPLACE INTO files (collection, system, path, name, size, is_dir)
               VALUES (?, ?, ?, ?, ?, ?)""",
            batch,
        )

    # Log completion
    con.execute(
        """UPDATE crawl_log SET status='completed', file_count=?, total_bytes=?,
                  completed_at=now()
           WHERE collection=? AND system=?""",
        [file_count, total_bytes, collection, system],
    )

    return file_count, total_bytes


def format_size(nbytes: int) -> str:
    """Human-readable file size."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(nbytes) < 1024:
            return f"{nbytes:.1f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} PB"


def get_error_systems(con: duckdb.DuckDBPyConnection) -> list[tuple[str, str]]:
    """Return list of (collection, system) pairs that have status='error'."""
    rows = con.execute(
        "SELECT collection, system FROM crawl_log WHERE status = 'error' ORDER BY collection, system"
    ).fetchall()
    return [(r[0], r[1]) for r in rows]


def crawl_all(
    con: duckdb.DuckDBPyConnection,
    collections: list[str] | None = None,
    max_depth: int = 3,
    resume: bool = False,
    retry_errors: bool = False,
):
    """Main crawl loop."""

    # --retry-errors mode: only retry previously-errored systems
    if retry_errors:
        error_systems = get_error_systems(con)
        if not error_systems:
            print("No errored systems to retry!")
            return
        print(f"Retrying {len(error_systems)} errored systems (timeout={RCLONE_TIMEOUT}s)...")
        for i, (collection, system) in enumerate(error_systems, 1):
            prefix = f"  [{i}/{len(error_systems)}]"
            try:
                print(f"{prefix} Retrying: {collection}/{system} ...", end=" ", flush=True)
                start = time.time()
                count, total = crawl_system_files(con, collection, system)
                elapsed = time.time() - start
                print(f"{count:,} files, {format_size(total)}, {elapsed:.1f}s")
            except Exception as e:
                print(f"ERROR: {e}")
        return

    # Get top-level collections
    if collections:
        top_level = collections
    else:
        print("Listing top-level Myrient collections...")
        entries = rclone_lsjson("")
        top_level = sorted([e["Name"] for e in entries if e.get("IsDir", False)])
        print(f"Found {len(top_level)} collections: {', '.join(top_level)}")

    if max_depth < 2:
        print("Depth=1: Only listing collection names.")
        return

    for collection in top_level:
        systems = crawl_collection_systems(con, collection)

        if max_depth < 3:
            # Just record system names without crawling files
            for system in systems:
                con.execute(
                    """INSERT OR REPLACE INTO crawl_log
                       (collection, system, depth, status, started_at, completed_at)
                       VALUES (?, ?, 2, 'completed', now(), now())""",
                    [collection, system],
                )
            continue

        # Crawl files for each system
        completed = get_completed_systems(con, collection) if resume else set()
        skipped = 0

        for i, system in enumerate(systems, 1):
            if resume and system in completed:
                skipped += 1
                continue

            prefix = f"  [{i}/{len(systems)}]"
            try:
                print(f"{prefix} Crawling: {collection}/{system} ...", end=" ", flush=True)
                start = time.time()
                count, total = crawl_system_files(con, collection, system)
                elapsed = time.time() - start
                print(f"{count:,} files, {format_size(total)}, {elapsed:.1f}s")
            except Exception as e:
                print(f"ERROR: {e}")

        if skipped:
            print(f"  (skipped {skipped} already-completed systems)")


def print_summary(con: duckdb.DuckDBPyConnection):
    """Print a summary of what's in the database."""
    print(f"\n{'=' * 60}")
    print("DATABASE SUMMARY")
    print(f"{'=' * 60}")

    total = con.execute("SELECT COUNT(*) FROM files WHERE NOT is_dir").fetchone()[0]
    total_size = con.execute(
        "SELECT COALESCE(SUM(size), 0) FROM files WHERE NOT is_dir"
    ).fetchone()[0]
    print(f"Total files: {total:,}")
    print(f"Total size:  {format_size(total_size)}")

    print("\nPer collection:")
    rows = con.execute("""
        SELECT collection,
               COUNT(*) FILTER (WHERE NOT is_dir) as file_count,
               COALESCE(SUM(size) FILTER (WHERE NOT is_dir), 0) as total_size
        FROM files
        GROUP BY collection
        ORDER BY total_size DESC
    """).fetchall()
    for coll, count, size in rows:
        print(f"  {coll:45s} {count:>10,} files  {format_size(size):>12s}")

    # Crawl status
    completed = con.execute("SELECT COUNT(*) FROM crawl_log WHERE status='completed'").fetchone()[0]
    errors = con.execute("SELECT COUNT(*) FROM crawl_log WHERE status='error'").fetchone()[0]
    in_progress = con.execute("SELECT COUNT(*) FROM crawl_log WHERE status='started'").fetchone()[0]
    print(f"\nCrawl status: {completed} completed, {errors} errors, {in_progress} in-progress")


def main():
    parser = argparse.ArgumentParser(description="Crawl Myrient and catalog into DuckDB")
    parser.add_argument(
        "collections", nargs="*", help="Specific collections to crawl (default: all)"
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=3,
        choices=[1, 2, 3],
        help="Crawl depth: 1=collections, 2=+systems, 3=+files (default: 3)",
    )
    parser.add_argument("--resume", action="store_true", help="Skip already-completed systems")
    parser.add_argument(
        "--retry-errors", action="store_true", help="Retry only previously-errored systems"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Timeout in seconds for rclone lsjson calls (default: 600)",
    )
    parser.add_argument("--db", default=DB_PATH, help=f"Database path (default: {DB_PATH})")
    parser.add_argument("--summary", action="store_true", help="Just print summary of existing DB")
    args = parser.parse_args()

    # Set global timeout
    global RCLONE_TIMEOUT
    RCLONE_TIMEOUT = args.timeout

    if args.summary:
        con = duckdb.connect(args.db, read_only=True)
        print_summary(con)
        con.close()
        return

    setup_rclone_remote()
    con = setup_database(args.db)

    try:
        crawl_all(
            con,
            collections=args.collections or None,
            max_depth=args.depth,
            resume=args.resume,
            retry_errors=args.retry_errors,
        )
        print_summary(con)
    except KeyboardInterrupt:
        print("\n\nInterrupted! Data collected so far is saved. Use --resume to continue.")
    finally:
        con.close()


if __name__ == "__main__":
    main()
