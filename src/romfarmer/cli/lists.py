"""Lists command group for validating list files."""

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table

from romfarmer.config.loader import load_platform_config


@click.group(name="lists")
def lists_group():
    """Validate and manage list files."""
    pass


@lists_group.command("validate")
@click.argument("platform", type=str)
@click.option(
    "--config-dir",
    type=click.Path(exists=True),
    default="config",
    help="Config root directory",
)
@click.pass_context
def validate_lists(ctx: click.Context, platform: str, config_dir: str):
    """Validate list files for a platform.
    
    Checks that all files referenced in list files exist in their respective
    source directories (Myrient or extra).
    
    Example:
        ./romfarmer lists validate saturn
    """
    console = Console()
    
    console.print(f"\n[cyan]Validating list files for: {platform}[/cyan]\n")
    
    # Load platform config
    platform_config = load_platform_config(platform, Path(config_dir))
    
    # Check if lists are configured
    if not platform_config.lists:
        console.print(f"[yellow]⚠ No list configuration found for {platform}[/yellow]")
        ctx.exit(0)
    
    lists_dir = Path(platform_config.lists.directory)
    if not lists_dir.exists():
        console.print(f"[red]✗ Lists directory not found: {lists_dir}[/red]")
        ctx.exit(1)
    
    # Find list files
    delete_lists = list(lists_dir.glob(f"{platform}-delete*"))
    add_myrient_lists = list(lists_dir.glob(f"{platform}+*"))
    add_extra_lists = list(lists_dir.glob(f"{platform}.*"))
    
    console.print(f"Found {len(delete_lists)} delete lists")
    console.print(f"Found {len(add_myrient_lists)} Myrient add lists")
    console.print(f"Found {len(add_extra_lists)} Extra add lists\n")
    
    total_errors = 0
    total_warnings = 0
    
    # Validate delete lists
    if delete_lists:
        console.print("[bold]Delete Lists:[/bold]")
        for list_file in delete_lists:
            errors = _validate_delete_list(list_file, console)
            total_errors += len(errors)
        console.print()
    
    # Validate Myrient add lists
    if add_myrient_lists:
        console.print("[bold]Myrient Add Lists:[/bold]")
        for list_file in add_myrient_lists:
            # Get source directory from config
            if platform_config.sources:
                source_dir = Path(platform_config.sources[0].path)
                errors = _validate_myrient_list(list_file, source_dir, console)
                total_errors += len(errors)
            else:
                console.print(f"  [yellow]⚠ {list_file.name}: No source configured[/yellow]")
                total_warnings += 1
        console.print()
    
    # Validate extra add lists
    if add_extra_lists:
        console.print("[bold]Extra Add Lists:[/bold]")
        from romfarmer.core.paths import paths
        extra_dir = paths.source_dir / "extra" / platform
        for list_file in add_extra_lists:
            errors = _validate_extra_list(list_file, extra_dir, console)
            total_errors += len(errors)
        console.print()
    
    # Summary
    if total_errors > 0 or total_warnings > 0:
        console.print(f"[bold]Summary:[/bold]")
        if total_errors > 0:
            console.print(f"  [red]✗ {total_errors} errors found[/red]")
        if total_warnings > 0:
            console.print(f"  [yellow]⚠ {total_warnings} warnings[/yellow]")
        ctx.exit(1 if total_errors > 0 else 0)
    else:
        console.print(f"[green]✓ All list files validated successfully![/green]")


def _validate_delete_list(list_file: Path, console: Console) -> list:
    """Validate a delete list file."""
    errors = []
    
    with open(list_file) as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
    if not lines:
        console.print(f"  [yellow]⚠ {list_file.name}: Empty list[/yellow]")
        return errors
    
    console.print(f"  [dim]{list_file.name}: {len(lines)} entries (validation skipped - processed at runtime)[/dim]")
    return errors


def _validate_myrient_list(list_file: Path, source_dir: Path, console: Console) -> list:
    """Validate a Myrient add list file."""
    errors = []
    
    with open(list_file) as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
    if not lines:
        console.print(f"  [yellow]⚠ {list_file.name}: Empty list[/yellow]")
        return errors
    
    found = 0
    not_found = []
    
    for filename in lines:
        # Strip list prefixes: + (Myrient add), . (extra add), - (delete)
        clean_filename = filename.lstrip('+.-')
        file_path = source_dir / clean_filename
        if file_path.exists():
            found += 1
        else:
            not_found.append(filename)
            errors.append(f"{list_file.name}: {filename}")
    
    if errors:
        console.print(f"  [red]✗ {list_file.name}: {found}/{len(lines)} found[/red]")
        for filename in not_found:
            console.print(f"    [red]• {filename}[/red]")
    else:
        console.print(f"  [green]✓ {list_file.name}: All {len(lines)} entries found[/green]")
    
    return errors


def _validate_extra_list(list_file: Path, extra_dir: Path, console: Console) -> list:
    """Validate an extra add list file."""
    errors = []
    
    if not extra_dir.exists():
        console.print(f"  [red]✗ {list_file.name}: Extra directory not found: {extra_dir}[/red]")
        errors.append(f"{list_file.name}: Extra directory missing")
        return errors
    
    with open(list_file) as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
    if not lines:
        console.print(f"  [yellow]⚠ {list_file.name}: Empty list[/yellow]")
        return errors
    
    found = 0
    not_found = []
    
    for filename in lines:
        # Strip list prefixes: + (Myrient add), . (extra add), - (delete)
        clean_filename = filename.lstrip('+.-')
        file_path = extra_dir / clean_filename
        if file_path.exists():
            found += 1
        else:
            not_found.append(filename)
            errors.append(f"{list_file.name}: {filename}")
    
    if errors:
        console.print(f"  [red]✗ {list_file.name}: {found}/{len(lines)} found in {extra_dir.name}/[/red]")
        for filename in not_found:
            console.print(f"    [red]• {filename}[/red]")
    else:
        console.print(f"  [green]✓ {list_file.name}: All {len(lines)} entries found in {extra_dir.name}/[/green]")
    
    return errors
