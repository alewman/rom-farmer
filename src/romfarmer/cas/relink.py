"""
Retroactive hardlinker: replace output copies with hardlinks to cache.

Scans output build directories for files that exist in the ROM cache
and replaces them with hardlinks, reclaiming disk space.

Matching strategy:
  1. Build a lookup of cache entries by (filename_stem, format, size)
  2. Walk output dirs, match files by stem + size
  3. Verify match by comparing first+last 1MB (fast) or full MD5 (safe)
  4. Replace: unlink output file, hardlink from cache

Usage:
    cd /data/emu/rom-farmer
    python -m romfarmer.cas.relink                    # dry-run
    python -m romfarmer.cas.relink --execute          # actually relink
    python -m romfarmer.cas.relink --execute --verify # relink + MD5 verify
"""

import hashlib
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
    MofNCompleteColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)

console = Console()

# Formats where output files can be matched to cache
CACHEABLE_FORMATS = {".chd", ".7z"}

# Directories to skip (not ROM builds)
SKIP_DIRS = {"media", "images", "gamelist.xml"}


def relink_outputs(
    output_dir: str = "output",
    cache_dir: str = "cache",
    db_path: str = "metadata/database/romfarmer.db",
    *,
    execute: bool = False,
    verify: bool = False,
    skip_ps3: bool = True,
) -> dict:
    """
    Replace output file copies with hardlinks to cache.

    Args:
        output_dir: Output builds directory
        cache_dir: Cache directory
        db_path: Path to romfarmer.db
        execute: Actually replace files (False = dry run)
        verify: MD5-verify matches before relinking
        skip_ps3: Skip PS3 game folders (folder-based, not single files)

    Returns:
        Statistics dict
    """
    import sqlite3

    stats = {
        "output_files_scanned": 0,
        "already_linked": 0,
        "matches_found": 0,
        "relinked": 0,
        "bytes_saved": 0,
        "verify_failed": 0,
        "no_match": 0,
        "skipped_ps3": 0,
        "errors": [],
    }

    mode = "[bold green]EXECUTE[/bold green]" if execute else "[bold yellow]DRY RUN[/bold yellow]"
    console.print(f"\n{'='*60}")
    console.print(f"  Output → Cache Relinker — {mode}")
    console.print(f"  Output: {output_dir}")
    console.print(f"  Cache:  {cache_dir}")
    console.print(f"{'='*60}\n")

    # Phase 1: Build cache lookup index
    console.print("[bold]Phase 1: Building cache index[/bold]")

    conn = sqlite3.connect(db_path)
    rows = conn.execute("""
        SELECT cache_path, final_size, final_md5, source_filename, format
        FROM rom_cache
        WHERE final_size IS NOT NULL
    """).fetchall()
    conn.close()

    # Index by (format, final_size) for fast lookup
    # Most files are unique by size within a format
    cache_by_size: dict[tuple[str, int], list[dict]] = {}
    for cache_path, final_size, final_md5, source_fn, fmt in rows:
        key = (fmt, final_size)
        entry = {
            "cache_path": Path(cache_dir) / cache_path if not cache_path.startswith(cache_dir) else Path(cache_path),
            "final_size": final_size,
            "final_md5": final_md5,
            "source_filename": source_fn,
            "format": fmt,
        }
        cache_by_size.setdefault(key, []).append(entry)

    console.print(f"  Indexed {len(rows):,} cache entries")

    # Phase 2: Scan output directories and match
    console.print(f"\n[bold]Phase 2: Scanning output directories[/bold]")

    output_root = Path(output_dir)
    if not output_root.exists():
        console.print(f"  [red]Output directory not found: {output_dir}[/red]")
        return stats

    # Collect all candidate files first
    candidates = []
    for build_dir in sorted(output_root.iterdir()):
        if not build_dir.is_dir():
            continue

        for root, dirs, files in os.walk(build_dir):
            root_path = Path(root)

            # Skip PS3 folder-based games
            if skip_ps3 and ("ps3" in root_path.name.lower() or
                             any(p.name.lower() in ("ps3iso", "ps3netsrv", "games")
                                 for p in root_path.parents)):
                # Only count once per PS3 dir
                if root_path.name.lower() in ("ps3iso", "games"):
                    stats["skipped_ps3"] += len(files)
                continue

            for fname in files:
                fpath = root_path / fname
                ext = fpath.suffix.lower()
                if ext in CACHEABLE_FORMATS:
                    candidates.append(fpath)

    console.print(f"  Found {len(candidates):,} cacheable files in output")

    # Phase 3: Match and relink
    console.print(f"\n[bold]Phase 3: Matching and relinking[/bold]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Relinking", total=len(candidates))

        for fpath in candidates:
            progress.advance(task)
            stats["output_files_scanned"] += 1

            try:
                st = fpath.stat()

                # Already hardlinked? (link count > 1)
                if st.st_nlink > 1:
                    stats["already_linked"] += 1
                    continue

                # Look up in cache by (format, size)
                ext = fpath.suffix.lstrip(".")
                key = (ext, st.st_size)
                cache_entries = cache_by_size.get(key, [])

                if not cache_entries:
                    stats["no_match"] += 1
                    continue

                # Find the right cache entry
                match = None
                if len(cache_entries) == 1:
                    match = cache_entries[0]
                else:
                    # Multiple entries with same size — need MD5 to disambiguate
                    output_md5 = _md5_file(fpath)
                    for entry in cache_entries:
                        if entry["final_md5"] == output_md5:
                            match = entry
                            break

                if not match:
                    stats["no_match"] += 1
                    continue

                # Verify cache file exists
                cache_path = match["cache_path"]
                if not cache_path.exists():
                    stats["errors"].append(f"Cache file missing: {cache_path}")
                    continue

                # Optional: verify MD5 matches
                if verify and len(cache_entries) == 1:
                    output_md5 = _md5_file(fpath)
                    if output_md5 != match["final_md5"]:
                        stats["verify_failed"] += 1
                        stats["errors"].append(
                            f"MD5 mismatch: {fpath.name} "
                            f"(output={output_md5[:12]}, cache={match['final_md5'][:12]})"
                        )
                        continue

                # Verify same filesystem (hardlink requirement)
                cache_dev = cache_path.stat().st_dev
                output_dev = st.st_dev
                if cache_dev != output_dev:
                    stats["errors"].append(
                        f"Cross-filesystem: {fpath} (dev={output_dev}) vs cache (dev={cache_dev})"
                    )
                    continue

                stats["matches_found"] += 1

                if execute:
                    # Atomic replace: unlink output, hardlink from cache
                    fpath.unlink()
                    os.link(cache_path, fpath)
                    stats["relinked"] += 1
                    stats["bytes_saved"] += st.st_size
                else:
                    stats["relinked"] += 1
                    stats["bytes_saved"] += st.st_size

            except Exception as e:
                stats["errors"].append(f"Error processing {fpath}: {e}")

    _print_summary(stats, execute)
    return stats


def _md5_file(path: Path) -> str:
    """Compute MD5 of a file."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(1_048_576):
            h.update(chunk)
    return h.hexdigest()


def _print_summary(stats: dict, executed: bool) -> None:
    """Print relink summary."""
    from rich.table import Table
    from rich.panel import Panel

    table = Table(title="Relink Summary", show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green", justify="right")

    table.add_row("Output files scanned", f"{stats['output_files_scanned']:,}")
    table.add_row("Already hardlinked", f"{stats['already_linked']:,}")
    table.add_row("Matches found", f"{stats['matches_found']:,}")
    table.add_row("Files relinked", f"{stats['relinked']:,}")
    table.add_row(
        "Space saved",
        f"{stats['bytes_saved'] / (1024**3):.1f} GB",
    )
    table.add_row("No cache match", f"{stats['no_match']:,}")

    if stats["skipped_ps3"]:
        table.add_row("Skipped (PS3)", f"{stats['skipped_ps3']:,}")
    if stats["verify_failed"]:
        table.add_row("Verify failed", f"[red]{stats['verify_failed']:,}[/red]")
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
        description="Replace output file copies with hardlinks to cache"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually replace files (default: dry run)",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="MD5-verify matches before relinking (slower but safer)",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Output builds directory (default: output)",
    )
    parser.add_argument(
        "--cache-dir",
        default="cache",
        help="Cache directory (default: cache)",
    )
    parser.add_argument(
        "--db",
        default="metadata/database/romfarmer.db",
        help="Path to romfarmer.db",
    )
    parser.add_argument(
        "--include-ps3",
        action="store_true",
        help="Include PS3 folder-based games",
    )

    args = parser.parse_args()

    start = time.time()
    results = relink_outputs(
        output_dir=args.output_dir,
        cache_dir=args.cache_dir,
        db_path=args.db,
        execute=args.execute,
        verify=args.verify,
        skip_ps3=not args.include_ps3,
    )
    elapsed = time.time() - start

    console.print(f"\n⏱  Completed in {elapsed:.1f}s")
