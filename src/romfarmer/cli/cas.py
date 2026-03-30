"""CAS (Content-Addressable Store) CLI commands.

Provides tools for bulk-ingesting existing folder outputs into the CAS
and tree cache, e.g. PS3 JB folders that were built before rom-farmer
tracked them.
"""

import hashlib
import time
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from romfarmer.cache import CacheConfig, CacheManager
from romfarmer.cas import ContentStore, TreeStore


@click.group(name="cas")
def cas_group() -> None:
    """Content-Addressable Store operations.

    Manage the CAS blob store and tree manifests.
    Ingest existing folder builds into the cache for future deduplication.
    """
    pass


@cas_group.command("ingest")
@click.argument(
    "source_dir",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
)
@click.option(
    "--platform",
    default="ps3",
    help="Platform identifier (default: ps3)",
)
@click.option(
    "--format",
    "output_format",
    default="ps3-jb",
    help="Output format (default: ps3-jb)",
)
@click.option(
    "--suffix",
    default=".ps3",
    help="Folder suffix to match (default: .ps3)",
)
@click.option(
    "--myrient-dir",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    help="Myrient source directory for ZIP matching (optional)",
)
@click.option(
    "--store-dir",
    type=click.Path(resolve_path=True),
    default=None,
    help="CAS store directory (default: ./store)",
)
@click.option(
    "--hash-sources",
    is_flag=True,
    default=False,
    help="Compute MD5 of Myrient source ZIPs (slow, ~hours for full set)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be ingested without doing it",
)
@click.option(
    "--limit",
    type=int,
    default=0,
    help="Limit number of folders to ingest (0=all)",
)
@click.option(
    "--skip-existing",
    is_flag=True,
    default=True,
    help="Skip folders already in tree cache (default: True)",
)
def cas_ingest(
    source_dir: str,
    platform: str,
    output_format: str,
    suffix: str,
    myrient_dir: Optional[str],
    store_dir: Optional[str],
    hash_sources: bool,
    dry_run: bool,
    limit: int,
    skip_existing: bool,
) -> None:
    """Ingest existing folder builds into the CAS via hardlinks.

    Walks SOURCE_DIR for folders matching --suffix (default: .ps3),
    ingests each into the CAS tree store using hardlinks (zero-copy
    on the same filesystem), and records tree cache entries.

    Examples:

        # Ingest all PS3 JB folders
        romfarmer cas ingest /data/emu/ps3netsrv/GAMES/

        # With Myrient source matching
        romfarmer cas ingest /data/emu/ps3netsrv/GAMES/ \\
            --myrient-dir "/data/emu/source/myrient.erista.me/files/Redump/Sony - PlayStation 3"

        # Dry run first
        romfarmer cas ingest /data/emu/ps3netsrv/GAMES/ --dry-run

        # Ingest just one folder for testing
        romfarmer cas ingest /data/emu/ps3netsrv/GAMES/ --limit 1
    """
    console = Console()
    source_path = Path(source_dir)
    myrient_path = Path(myrient_dir) if myrient_dir else None

    # Default store_dir to ./store relative to cwd
    cas_dir = Path(store_dir) if store_dir else Path.cwd() / "store"

    # ── Discover folders ──────────────────────────────────────────────
    folders = sorted(
        [d for d in source_path.iterdir() if d.is_dir() and d.name.endswith(suffix)]
    )

    if not folders:
        console.print(f"[yellow]No folders matching *{suffix} found in {source_dir}[/yellow]")
        return

    console.print(f"\n[bold cyan]CAS Batch Ingest[/bold cyan]")
    console.print(f"  Source:   {source_dir}")
    console.print(f"  Platform: {platform}")
    console.print(f"  Format:   {output_format}")
    console.print(f"  Suffix:   {suffix}")
    console.print(f"  CAS dir:  {cas_dir}")
    if myrient_path:
        console.print(f"  Myrient:  {myrient_path}")
    console.print(f"  Folders:  {len(folders)}")
    console.print()

    # ── Build Myrient source lookup ───────────────────────────────────
    myrient_zips: dict[str, Path] = {}
    if myrient_path:
        for zf in myrient_path.iterdir():
            if zf.is_file() and zf.suffix == ".zip":
                # Key: stem matches folder name without .ps3
                myrient_zips[zf.stem] = zf
        console.print(f"  Myrient ZIPs indexed: {len(myrient_zips)}")

    # ── Initialize CAS + Cache ────────────────────────────────────────
    store = ContentStore(cas_dir)
    tree_store = TreeStore(store)

    config = CacheConfig.from_env()
    cache_manager = CacheManager(config)

    # ── Check existing entries ────────────────────────────────────────
    existing_folders: set[str] = set()
    if skip_existing:
        try:
            from romfarmer.cache.models import TreeCache
            existing = cache_manager.session.query(TreeCache.folder_name).filter_by(
                format=output_format,
            ).all()
            existing_folders = {row[0] for row in existing}
            if existing_folders:
                console.print(f"  Already cached: {len(existing_folders)} (will skip)")
        except Exception:
            pass  # Table may not exist yet

    # ── Filter ────────────────────────────────────────────────────────
    to_ingest = []
    skipped = 0
    for folder in folders:
        if skip_existing and folder.name in existing_folders:
            skipped += 1
            continue
        to_ingest.append(folder)

    if limit > 0:
        to_ingest = to_ingest[:limit]

    if skipped:
        console.print(f"  Skipping: {skipped} already in cache")
    console.print(f"  To ingest: {len(to_ingest)}")
    console.print()

    # ── Dry run ───────────────────────────────────────────────────────
    if dry_run:
        console.print("[bold yellow]DRY RUN — no changes will be made[/bold yellow]\n")
        table = Table(title="Folders to Ingest", show_lines=False)
        table.add_column("#", style="dim", width=5)
        table.add_column("Folder", style="green")
        table.add_column("Source ZIP", style="cyan")
        for i, folder in enumerate(to_ingest, 1):
            base = folder.stem  # e.g., "Terraria (USA) (En,Fr,Es)"
            source_zip = myrient_zips.get(base)
            table.add_row(str(i), folder.name, source_zip.name if source_zip else "—")
            if i >= 50:
                table.add_row("...", f"(+{len(to_ingest) - 50} more)", "")
                break
        console.print(table)
        return

    if not to_ingest:
        console.print("[green]Nothing to ingest — all folders already cached.[/green]")
        return

    # ── Ingest loop ───────────────────────────────────────────────────
    results = {"success": 0, "error": 0, "files": 0, "bytes": 0}
    errors: list[tuple[str, str]] = []
    t0 = time.monotonic()

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}[/bold blue]"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Ingesting folders", total=len(to_ingest))

        for folder in to_ingest:
            folder_name = folder.name
            base_name = folder.stem  # folder name without .ps3

            progress.update(task, description=f"[bold blue]{folder_name}[/bold blue]")

            try:
                # ── Ingest into CAS via hardlinks ─────────────────────
                manifest = tree_store.ingest(
                    folder,
                    platform=platform,
                    format=output_format,
                    source_name=base_name,
                    tool="batch-ingest",
                    hardlink=True,
                )

                # ── Match Myrient source ──────────────────────────────
                source_zip = myrient_zips.get(base_name)
                # Generate a deterministic pseudo-MD5 from folder name
                # so each folder gets a unique cache key. Without this,
                # all entries share source_md5="0"*32 and overwrite each
                # other (store_tree upserts on source_md5+format+params).
                source_md5 = hashlib.md5(folder_name.encode()).hexdigest()
                source_size = 0
                source_filename = folder_name

                if source_zip:
                    source_filename = source_zip.name
                    source_size = source_zip.stat().st_size
                    if hash_sources:
                        source_md5 = _md5_file(source_zip)

                # ── Record in tree cache ──────────────────────────────
                cache_manager.store_tree(
                    source_md5=source_md5,
                    tree_hash=manifest.tree_hash,
                    total_files=manifest.total_files,
                    total_size=manifest.total_size,
                    folder_name=folder_name,
                    format=output_format,
                    platform=platform,
                    tool_name="batch-ingest",
                    source_filename=source_filename,
                    source_size=source_size,
                )

                results["success"] += 1
                results["files"] += manifest.total_files
                results["bytes"] += manifest.total_size

            except Exception as e:
                results["error"] += 1
                errors.append((folder_name, str(e)))

            progress.advance(task)

    elapsed = time.monotonic() - t0

    # ── Summary ───────────────────────────────────────────────────────
    console.print()
    console.print("[bold cyan]Ingest Complete[/bold cyan]\n")

    table = Table(show_header=False, box=None)
    table.add_column("", style="dim")
    table.add_column("", style="green")

    table.add_row("Ingested", f"{results['success']:,} folders")
    table.add_row("Files", f"{results['files']:,}")
    table.add_row("Total Size", _format_size(results["bytes"]))
    table.add_row("Errors", f"[red]{results['error']}[/red]" if results["error"] else "0")
    table.add_row("Elapsed", f"{elapsed:.1f}s")

    if results["success"] > 0:
        rate = results["files"] / elapsed if elapsed > 0 else 0
        table.add_row("Rate", f"{rate:.0f} files/s")

    console.print(table)

    if errors:
        console.print(f"\n[bold red]Errors ({len(errors)}):[/bold red]")
        for name, err in errors[:20]:
            console.print(f"  [red]✗[/red] {name}: {err}")
        if len(errors) > 20:
            console.print(f"  ... and {len(errors) - 20} more")


@cas_group.command("status")
def cas_status() -> None:
    """Show CAS store and tree cache statistics."""
    console = Console()
    cas_dir = Path.cwd() / "store"

    if not cas_dir.exists():
        console.print("[yellow]CAS store not found at ./store[/yellow]")
        return

    store = ContentStore(cas_dir)
    tree_store = TreeStore(store)

    # Blob stats
    console.print("\n[bold cyan]CAS Store Status[/bold cyan]\n")
    stats = store.stats()

    table = Table(show_header=False, box=None)
    table.add_column("", style="dim")
    table.add_column("", style="green")
    table.add_row("Store Dir", str(cas_dir))
    table.add_row("Total Blobs", f"{stats['total_files']:,}")
    table.add_row("Total Size", _format_size(stats['total_size']))
    table.add_row("Buckets Used", f"{stats['buckets_used']}/256")
    console.print(table)

    # Tree cache stats
    try:
        config = CacheConfig.from_env()
        manager = CacheManager(config)
        tree_stats = manager.get_tree_stats()

        console.print(f"\n[bold cyan]Tree Cache[/bold cyan]\n")
        tree_table = Table(show_header=False, box=None)
        tree_table.add_column("", style="dim")
        tree_table.add_column("", style="green")
        tree_table.add_row("Entries", f"{tree_stats.get('total_entries', 0):,}")
        tree_table.add_row("Platforms", str(tree_stats.get('platforms', {})))
        tree_table.add_row("Formats", str(tree_stats.get('formats', {})))
        console.print(tree_table)
    except Exception as e:
        console.print(f"[dim]Tree cache: {e}[/dim]")


def _md5_file(path: Path, chunk_size: int = 1_048_576) -> str:
    """Compute MD5 hex digest of a file."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _format_size(size_bytes: int) -> str:
    """Format bytes as human-readable size."""
    if size_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(size_bytes)
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    return f"{size:.1f} {units[unit_index]}"
