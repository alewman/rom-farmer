"""
One-time migration: metadata/media/{type}/... → store/{hash[:2]}/...

Moves all tracked media files from the old per-type directory layout
into the unified content-addressable store. Uses os.rename() for
atomic, instant moves on the same ZFS pool.

Usage:
    cd /path/to/rom-farmer
    python -m romfarmer.cas.migrate              # dry-run by default
    python -m romfarmer.cas.migrate --execute    # actually migrate
    python -m romfarmer.cas.migrate --verify     # verify after migration
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    MofNCompleteColumn,
)

console = Console()


def migrate_media_store(
    db_path: str = "metadata/database/romfarmer.db",
    old_media_dir: str = "metadata/media",
    new_store_dir: str = "store",
    *,
    execute: bool = False,
    verify: bool = False,
) -> dict:
    """
    Migrate media files from old layout to unified CAS store.

    Old layout: metadata/media/{type}/{hash[:2]}/{hash[2:]}.{ext}
    New layout: store/{hash[:2]}/{hash[2:]}.{ext}

    The migration is DB-driven: only files tracked in the database
    are moved. Orphan files are reported but not touched.

    Args:
        db_path: Path to romfarmer.db
        old_media_dir: Current media directory
        new_store_dir: Target store directory
        execute: If False, dry-run only. If True, actually move files.
        verify: If True, verify all blobs after migration.

    Returns:
        Dict with migration statistics.
    """
    # Import here to avoid circular imports
    from romfarmer.metadata.database import MetadataDatabase, MediaFile
    from romfarmer.cas.store import ContentStore

    stats = {
        "total_records": 0,
        "already_migrated": 0,
        "files_moved": 0,
        "files_missing": 0,
        "files_deduplicated": 0,
        "bytes_moved": 0,
        "errors": [],
        "orphan_files": 0,
        "verified_ok": 0,
        "verified_fail": 0,
    }

    store = ContentStore(new_store_dir)
    db = MetadataDatabase(db_path)

    mode = "[bold green]EXECUTE[/bold green]" if execute else "[bold yellow]DRY RUN[/bold yellow]"
    console.print(f"\n{'='*60}")
    console.print(f"  Media Store Migration — {mode}")
    console.print(f"  From: {old_media_dir}")
    console.print(f"  To:   {new_store_dir}")
    console.print(f"{'='*60}\n")

    # Phase 1: Move files based on DB records
    console.print("[bold]Phase 1: Moving tracked files[/bold]")

    with db.get_session() as session:
        all_media = session.query(MediaFile).all()
        stats["total_records"] = len(all_media)
        console.print(f"  Found {len(all_media):,} MediaFile records in database")

        path_updates = []  # (media_file_id, old_path, new_path)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Moving files", total=len(all_media))

            for mf in all_media:
                old_path = Path(mf.file_path)
                ext = old_path.suffix
                new_path = store.blob_path(mf.file_hash, ext)
                new_path_str = str(new_path)

                progress.advance(task)

                # Already at the new location?
                if mf.file_path == new_path_str:
                    stats["already_migrated"] += 1
                    continue

                # Does the new path already exist? (dedup across media types)
                if new_path.exists():
                    # Blob already in store — just update the DB path
                    path_updates.append((mf.id, mf.file_path, new_path_str))

                    # Remove the old copy if it still exists
                    if execute and old_path.exists():
                        old_path.unlink()

                    stats["files_deduplicated"] += 1
                    continue

                # Does the source file exist?
                if not old_path.exists():
                    stats["files_missing"] += 1
                    stats["errors"].append(
                        f"Missing: {mf.file_path} (hash: {mf.file_hash[:12]}...)"
                    )
                    # Still update the DB path — the file might appear later
                    path_updates.append((mf.id, mf.file_path, new_path_str))
                    continue

                # Move the file
                if execute:
                    new_path.parent.mkdir(parents=True, exist_ok=True)
                    os.rename(str(old_path), str(new_path))

                path_updates.append((mf.id, mf.file_path, new_path_str))
                stats["files_moved"] += 1
                stats["bytes_moved"] += mf.file_size or 0

    # Phase 2: Bulk-update database paths
    console.print(f"\n[bold]Phase 2: Updating {len(path_updates):,} database paths[/bold]")

    if execute and path_updates:
        with db.get_session() as session:
            # Batch update for performance
            batch_size = 5000
            for i in range(0, len(path_updates), batch_size):
                batch = path_updates[i : i + batch_size]
                for media_id, _, new_path_str in batch:
                    session.query(MediaFile).filter(
                        MediaFile.id == media_id
                    ).update({"file_path": new_path_str})
                session.commit()
                console.print(
                    f"  Updated batch {i // batch_size + 1}"
                    f" ({min(i + batch_size, len(path_updates)):,}/{len(path_updates):,})"
                )
    elif not execute:
        console.print("  [yellow]Skipped (dry run)[/yellow]")

    # Phase 3: Count orphan files in old directory
    old_dir = Path(old_media_dir)
    if old_dir.exists():
        console.print(f"\n[bold]Phase 3: Scanning for orphan files in {old_media_dir}[/bold]")
        orphan_count = 0
        for root, dirs, files in os.walk(old_dir):
            orphan_count += len(files)

        if execute:
            # After migration, remaining files are orphans
            stats["orphan_files"] = orphan_count
            if orphan_count > 0:
                console.print(
                    f"  [yellow]Found {orphan_count:,} orphan files"
                    f" still in {old_media_dir}[/yellow]"
                )
                console.print(
                    "  These are NOT tracked in the database."
                    " Remove manually after inspection:"
                )
                console.print(f"    rm -rf {old_media_dir}")
            else:
                console.print("  [green]No orphans — old directory is clean[/green]")
                console.print(f"  Safe to remove: rm -rf {old_media_dir}")
        else:
            # In dry run, count total files that would remain
            stats["orphan_files"] = orphan_count - stats["files_moved"] - stats["files_deduplicated"]

    # Phase 4: Optional verification
    if verify and execute:
        console.print(f"\n[bold]Phase 4: Verifying blob integrity[/bold]")

        with db.get_session() as session:
            all_media = session.query(MediaFile).all()

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Verifying", total=len(all_media))

                for mf in all_media:
                    progress.advance(task)
                    ext = Path(mf.file_path).suffix
                    if store.verify(mf.file_hash, ext):
                        stats["verified_ok"] += 1
                    else:
                        stats["verified_fail"] += 1
                        stats["errors"].append(
                            f"Verify failed: {mf.file_hash[:12]}... ({mf.file_path})"
                        )

    # Print summary
    _print_summary(stats, execute)
    return stats


def _print_summary(stats: dict, executed: bool) -> None:
    """Print migration summary."""
    from rich.table import Table
    from rich.panel import Panel

    table = Table(title="Migration Summary", show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green", justify="right")

    table.add_row("Total DB records", f"{stats['total_records']:,}")
    table.add_row("Already migrated", f"{stats['already_migrated']:,}")
    table.add_row("Files moved", f"{stats['files_moved']:,}")
    table.add_row("Files deduplicated", f"{stats['files_deduplicated']:,}")
    table.add_row("Files missing (source)", f"{stats['files_missing']:,}")
    table.add_row(
        "Data moved",
        f"{stats['bytes_moved'] / (1024**3):.1f} GB",
    )
    table.add_row("Orphan files (old dir)", f"{stats['orphan_files']:,}")

    if stats["verified_ok"] or stats["verified_fail"]:
        table.add_row("Verified OK", f"{stats['verified_ok']:,}")
        table.add_row("Verified FAILED", f"{stats['verified_fail']:,}")

    if stats["errors"]:
        table.add_row("Errors", f"[red]{len(stats['errors'])}[/red]")

    console.print()
    console.print(Panel(table))

    if not executed:
        console.print(
            "\n[bold yellow]This was a DRY RUN."
            " Re-run with --execute to apply changes.[/bold yellow]"
        )

    if stats["errors"] and len(stats["errors"]) <= 20:
        console.print("\n[bold red]Errors:[/bold red]")
        for err in stats["errors"]:
            console.print(f"  • {err}")
    elif stats["errors"]:
        console.print(
            f"\n[bold red]{len(stats['errors'])} errors"
            f" (showing first 20):[/bold red]"
        )
        for err in stats["errors"][:20]:
            console.print(f"  • {err}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate media store to unified CAS layout"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually move files and update DB (default: dry run)",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify blob integrity after migration",
    )
    parser.add_argument(
        "--db",
        default="metadata/database/romfarmer.db",
        help="Path to romfarmer.db",
    )
    parser.add_argument(
        "--old-dir",
        default="metadata/media",
        help="Old media directory (default: metadata/media)",
    )
    parser.add_argument(
        "--new-dir",
        default="store",
        help="New store directory (default: store)",
    )

    args = parser.parse_args()

    start = time.time()
    results = migrate_media_store(
        db_path=args.db,
        old_media_dir=args.old_dir,
        new_store_dir=args.new_dir,
        execute=args.execute,
        verify=args.verify,
    )
    elapsed = time.time() - start

    console.print(f"\n⏱  Completed in {elapsed:.1f}s")

    # Exit with error code if there were failures
    if results["verified_fail"] > 0:
        sys.exit(1)
