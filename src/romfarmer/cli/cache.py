"""Cache management CLI commands."""

import click
from rich.console import Console
from rich.table import Table

from romfarmer.cache import CacheConfig, CacheManager


@click.group(name="cache")
def cache_group() -> None:
    """Manage ROM build cache.

    The cache stores compressed ROMs (CHD, RVZ, etc.) to avoid rebuilding
    the same files. Uses hardlinks by default to save disk space.
    """
    pass


@cache_group.command("status")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed statistics")
@click.pass_context
def cache_status(ctx: click.Context, verbose: bool) -> None:
    """Display cache statistics and status."""
    console = Console()

    try:
        config = CacheConfig.from_env()
        manager = CacheManager(config)
        stats = manager.get_stats()

        console.print("\n[bold cyan]ROM Build Cache Status[/bold cyan]\n")

        # Status table
        table = Table(show_header=False, box=None)
        table.add_column("Property", style="dim")
        table.add_column("Value", style="green")

        table.add_row("Enabled", "✓ Yes" if config.enabled else "✗ No")
        table.add_row("Cache Directory", str(config.cache_dir))
        table.add_row("Link Mode", config.link_mode.value)
        table.add_row("Verify Level", config.verify_level.value)
        table.add_row("Check Tool Version", "✓ Yes" if config.check_tool_version else "✗ No")

        console.print(table)
        console.print()

        # Stats table
        stats_table = Table(show_header=True, header_style="bold cyan", title="Cache Statistics")
        stats_table.add_column("Metric", style="dim")
        stats_table.add_column("Value", justify="right", style="green")

        stats_table.add_row("Total Entries", f"{stats['total_entries']:,}")
        stats_table.add_row("Total Size", _format_size(stats["total_size"]))
        stats_table.add_row("CHD Files", f"{stats.get('chd_count', 0):,}")
        stats_table.add_row("RVZ Files", f"{stats.get('rvz_count', 0):,}")
        stats_table.add_row("7z Files", f"{stats.get('7z_count', 0):,}")

        if verbose and stats.get("tool_versions"):
            stats_table.add_row("", "")  # Spacer
            for tool, version in stats["tool_versions"].items():
                stats_table.add_row(f"  {tool} version", version)

        console.print(stats_table)

        # Space savings estimate
        if stats["total_entries"] > 0:
            console.print(
                f"\n[dim]Estimated space saved by hardlinks: {_format_size(stats['total_size'])}[/dim]"
            )

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort() from e


@cache_group.command("verify")
@click.option("--fix", is_flag=True, help="Remove invalid entries")
@click.pass_context
def cache_verify(ctx: click.Context, fix: bool) -> None:
    """Verify cache integrity.

    Checks that all cached files exist and optionally validates checksums.
    """
    console = Console()

    try:
        config = CacheConfig.from_env()
        manager = CacheManager(config)

        console.print("\n[bold cyan]Verifying ROM Build Cache...[/bold cyan]\n")

        results = manager.verify_all()

        valid = results["valid"]
        invalid = results["invalid"]
        missing = results["missing"]

        # Results table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Status", style="dim")
        table.add_column("Count", justify="right")

        table.add_row("[green]Valid[/green]", str(len(valid)))
        table.add_row("[yellow]Missing Files[/yellow]", str(len(missing)))
        table.add_row("[red]Invalid[/red]", str(len(invalid)))

        console.print(table)

        if missing:
            console.print("\n[yellow]Missing files:[/yellow]")
            for entry in missing[:10]:  # Show first 10
                console.print(f"  • {entry}")
            if len(missing) > 10:
                console.print(f"  ... and {len(missing) - 10} more")

        if invalid:
            console.print("\n[red]Invalid entries:[/red]")
            for entry in invalid[:10]:  # Show first 10
                console.print(f"  • {entry}")
            if len(invalid) > 10:
                console.print(f"  ... and {len(invalid) - 10} more")

        if fix and (missing or invalid):
            console.print("\n[bold]Removing invalid entries...[/bold]")
            removed = manager.remove_orphans()
            console.print(f"[green]Removed {removed} invalid entries.[/green]")
        elif missing or invalid:
            console.print("\n[dim]Run with --fix to remove invalid entries.[/dim]")
        else:
            console.print("\n[green]✓ All cache entries are valid![/green]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort() from e


@cache_group.command("clear")
@click.option(
    "--format",
    "file_format",
    type=click.Choice(["chd", "rvz", "7z", "all"]),
    default="all",
    help="Format to clear",
)
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@click.pass_context
def cache_clear(ctx: click.Context, file_format: str, force: bool) -> None:
    """Clear the cache.

    Removes all cached files and database entries. Use --format to clear
    only specific file types.
    """
    console = Console()

    try:
        config = CacheConfig.from_env()
        manager = CacheManager(config)
        stats = manager.get_stats()

        if stats["total_entries"] == 0:
            console.print("[yellow]Cache is already empty.[/yellow]")
            return

        # Confirmation
        if not force:
            console.print("\n[bold red]Warning:[/bold red] This will delete:")
            console.print(f"  • {stats['total_entries']:,} cached files")
            console.print(f"  • {_format_size(stats['total_size'])} of data")
            console.print()

            if not click.confirm("Are you sure you want to clear the cache?"):
                console.print("[dim]Aborted.[/dim]")
                return

        console.print("\n[bold]Clearing cache...[/bold]")

        if file_format == "all":
            cleared = manager.clear()
        else:
            cleared = manager.clear(format=file_format)

        console.print(f"[green]✓ Removed {cleared} entries from cache.[/green]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort() from e


@cache_group.command("prune")
@click.option("--older-than", type=int, default=90, help="Remove entries older than N days")
@click.option("--dry-run", is_flag=True, help="Show what would be removed without removing")
@click.pass_context
def cache_prune(ctx: click.Context, older_than: int, dry_run: bool) -> None:
    """Remove old cache entries.

    Removes cache entries that haven't been accessed in the specified
    number of days.
    """
    console = Console()

    try:
        config = CacheConfig.from_env()
        manager = CacheManager(config)

        console.print(
            f"\n[bold cyan]Pruning cache entries older than {older_than} days...[/bold cyan]\n"
        )

        entries = manager.get_old_entries(days=older_than)

        if not entries:
            console.print("[green]No old entries to prune.[/green]")
            return

        console.print(f"Found {len(entries)} entries to prune:")

        total_size = sum(e.final_file_size or 0 for e in entries)
        console.print(f"  • Total size: {_format_size(total_size)}")

        if dry_run:
            console.print("\n[dim]Dry run - no entries removed.[/dim]")
            console.print("\n[bold]Entries that would be removed:[/bold]")
            for entry in entries[:20]:
                console.print(f"  • {entry.source_md5[:8]}... ({entry.format})")
            if len(entries) > 20:
                console.print(f"  ... and {len(entries) - 20} more")
        else:
            removed = manager.prune(days=older_than)
            console.print(f"\n[green]✓ Removed {removed} old entries.[/green]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort() from e


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
