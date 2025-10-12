"""
Organization CLI commands.

Provides commands for organizing ROM collections by region, kind, and language.
"""

import logging
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from ..organizers import (
    RegionOrganizer,
    KindOrganizer,
    LanguageOrganizer,
    OrganizeMode,
)

logger = logging.getLogger(__name__)
console = Console()


@click.group("organize")
def organize_group():
    """Organize ROM collections by various criteria."""
    pass


@organize_group.command("region")
@click.argument("source_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "--mode",
    type=click.Choice(["move", "copy", "symlink"], case_sensitive=False),
    default="move",
    help="How to organize files (move, copy, or symlink)",
)
@click.option(
    "--keep-in-place",
    multiple=True,
    help="Regions to keep in root directory (e.g., --keep-in-place USA --keep-in-place World)",
)
@click.option(
    "--exclude",
    multiple=True,
    help="Regions to exclude from organization",
)
@click.option(
    "--priority",
    multiple=True,
    help="Region priority for multi-region ROMs (e.g., --priority USA --priority Europe)",
)
@click.option(
    "--extensions",
    multiple=True,
    help="File extensions to process (e.g., --extensions .nes --extensions .sfc)",
)
@click.option(
    "--recursive/--no-recursive",
    default=True,
    help="Process subdirectories recursively",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview changes without making them",
)
def organize_region(
    source_dir: Path,
    mode: str,
    keep_in_place: tuple,
    exclude: tuple,
    priority: tuple,
    extensions: tuple,
    recursive: bool,
    dry_run: bool,
):
    """
    Organize ROMs by region.
    
    Examples:
    
      # Keep USA and World in root, organize others
      romgroomer organize region /roms/nes --keep-in-place USA --keep-in-place World
      
      # Create symlinks instead of moving files
      romgroomer organize region /roms/nes --mode symlink
      
      # Dry run to preview changes
      romgroomer organize region /roms/nes --dry-run
    """
    console.print(f"\n[bold cyan]Region Organization[/bold cyan]")
    console.print(f"Source: {source_dir}")
    console.print(f"Mode: {mode}")
    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]")
    console.print()
    
    # Create organizer
    organizer = RegionOrganizer(
        mode=OrganizeMode(mode),
        dry_run=dry_run,
        region_priority=list(priority) if priority else None,
        keep_in_place=list(keep_in_place) if keep_in_place else None,
        exclude_regions=list(exclude) if exclude else None,
    )
    
    # Organize
    stats = organizer.organize(
        source_dir=source_dir,
        recursive=recursive,
        extensions=list(extensions) if extensions else None,
    )
    
    # Display results
    console.print("\n[bold green]Organization Complete![/bold green]")
    _display_stats(stats)


@organize_group.command("kind")
@click.argument("source_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "--mode",
    type=click.Choice(["move", "copy", "symlink"], case_sensitive=False),
    default="move",
    help="How to organize files (move, copy, or symlink)",
)
@click.option(
    "--keep-in-place",
    multiple=True,
    help="Kinds to keep in root directory (e.g., --keep-in-place Demo --keep-in-place Beta)",
)
@click.option(
    "--exclude",
    multiple=True,
    help="Kinds to exclude from organization",
)
@click.option(
    "--extensions",
    multiple=True,
    help="File extensions to process",
)
@click.option(
    "--recursive/--no-recursive",
    default=True,
    help="Process subdirectories recursively",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview changes without making them",
)
def organize_kind(
    source_dir: Path,
    mode: str,
    keep_in_place: tuple,
    exclude: tuple,
    extensions: tuple,
    recursive: bool,
    dry_run: bool,
):
    """
    Organize ROMs by kind (Demo, Beta, Homebrew, etc.).
    
    Examples:
    
      # Keep Demos in place, organize others
      romgroomer organize kind /roms/nes --keep-in-place Demo
      
      # Exclude pirate ROMs from organization
      romgroomer organize kind /roms/nes --exclude Pirate
      
      # Create symlinks for virtual organization
      romgroomer organize kind /roms/nes --mode symlink
    """
    console.print(f"\n[bold cyan]Kind Organization[/bold cyan]")
    console.print(f"Source: {source_dir}")
    console.print(f"Mode: {mode}")
    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]")
    console.print()
    
    # Create organizer
    organizer = KindOrganizer(
        mode=OrganizeMode(mode),
        dry_run=dry_run,
        keep_in_place=list(keep_in_place) if keep_in_place else None,
        exclude_kinds=list(exclude) if exclude else None,
    )
    
    # Organize
    stats = organizer.organize(
        source_dir=source_dir,
        recursive=recursive,
        extensions=list(extensions) if extensions else None,
    )
    
    # Display results
    console.print("\n[bold green]Organization Complete![/bold green]")
    _display_stats(stats)


@organize_group.command("language")
@click.argument("source_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "--mode",
    type=click.Choice(["move", "copy", "symlink"], case_sensitive=False),
    default="symlink",  # Symlink is typical for language organization
    help="How to organize files (move, copy, or symlink)",
)
@click.option(
    "--keep-in-place",
    multiple=True,
    help="Languages to keep in root directory",
)
@click.option(
    "--exclude",
    multiple=True,
    help="Languages to exclude from organization (e.g., --exclude En for English)",
)
@click.option(
    "--priority",
    multiple=True,
    help="Language priority for multi-language ROMs",
)
@click.option(
    "--use-codes",
    is_flag=True,
    help="Use language codes (En, Fr) instead of full names (English, French)",
)
@click.option(
    "--extensions",
    multiple=True,
    help="File extensions to process",
)
@click.option(
    "--recursive/--no-recursive",
    default=True,
    help="Process subdirectories recursively",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview changes without making them",
)
def organize_language(
    source_dir: Path,
    mode: str,
    keep_in_place: tuple,
    exclude: tuple,
    priority: tuple,
    use_codes: bool,
    extensions: tuple,
    recursive: bool,
    dry_run: bool,
):
    """
    Organize ROMs by language.
    
    Creates language-specific directories (typically using symlinks for virtual organization).
    
    Examples:
    
      # Create language symlinks, exclude English (default)
      romgroomer organize language /roms/nes --exclude En
      
      # Use full language names instead of codes
      romgroomer organize language /roms/nes --exclude English
      
      # Move files instead of symlinking
      romgroomer organize language /roms/nes --mode move
    """
    console.print(f"\n[bold cyan]Language Organization[/bold cyan]")
    console.print(f"Source: {source_dir}")
    console.print(f"Mode: {mode}")
    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]")
    console.print()
    
    # Create organizer
    organizer = LanguageOrganizer(
        mode=OrganizeMode(mode),
        dry_run=dry_run,
        language_priority=list(priority) if priority else None,
        keep_in_place=list(keep_in_place) if keep_in_place else None,
        exclude_languages=list(exclude) if exclude else None,
        use_full_names=not use_codes,
    )
    
    # Organize
    stats = organizer.organize(
        source_dir=source_dir,
        recursive=recursive,
        extensions=list(extensions) if extensions else None,
    )
    
    # Display results
    console.print("\n[bold green]Organization Complete![/bold green]")
    _display_stats(stats)


@organize_group.command("all")
@click.argument("source_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "--region-keep",
    multiple=True,
    help="Regions to keep in root",
)
@click.option(
    "--kind-keep",
    multiple=True,
    help="Kinds to keep in place",
)
@click.option(
    "--lang-exclude",
    multiple=True,
    help="Languages to exclude (e.g., --lang-exclude En)",
)
@click.option(
    "--extensions",
    multiple=True,
    help="File extensions to process",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview changes without making them",
)
def organize_all(
    source_dir: Path,
    region_keep: tuple,
    kind_keep: tuple,
    lang_exclude: tuple,
    extensions: tuple,
    dry_run: bool,
):
    """
    Organize ROMs by region, kind, AND language in one command.
    
    This runs all three organizers in sequence:
    1. Region (move files)
    2. Kind (move files recursively in each region)
    3. Language (create symlinks)
    
    Example:
    
      # Full organization: Keep USA in root, organize kinds, symlink languages
      romgroomer organize all /roms/nes --region-keep USA --lang-exclude En
    """
    console.print(f"\n[bold cyan]Full Organization[/bold cyan]")
    console.print(f"Source: {source_dir}")
    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]")
    console.print()
    
    ext_list = list(extensions) if extensions else None
    
    # Phase 1: Region organization
    console.print("[bold]Phase 1: Organizing by region...[/bold]")
    region_org = RegionOrganizer(
        mode=OrganizeMode.MOVE,
        dry_run=dry_run,
        keep_in_place=list(region_keep) if region_keep else None,
    )
    region_stats = region_org.organize(source_dir, recursive=True, extensions=ext_list)
    console.print(f"  Files moved: {region_stats.files_moved}")
    
    # Phase 2: Kind organization (recursive in all folders)
    console.print("\n[bold]Phase 2: Organizing by kind...[/bold]")
    kind_org = KindOrganizer(
        mode=OrganizeMode.MOVE,
        dry_run=dry_run,
        keep_in_place=list(kind_keep) if kind_keep else None,
    )
    kind_stats = kind_org.organize(source_dir, recursive=True, extensions=ext_list)
    console.print(f"  Files moved: {kind_stats.files_moved}")
    
    # Phase 3: Language organization (symlinks)
    console.print("\n[bold]Phase 3: Creating language symlinks...[/bold]")
    lang_org = LanguageOrganizer(
        mode=OrganizeMode.SYMLINK,
        dry_run=dry_run,
        exclude_languages=list(lang_exclude) if lang_exclude else None,
    )
    lang_stats = lang_org.organize(source_dir, recursive=True, extensions=ext_list)
    console.print(f"  Symlinks created: {lang_stats.symlinks_created}")
    
    # Display combined results
    console.print("\n[bold green]Full Organization Complete![/bold green]")
    
    table = Table(title="Combined Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="magenta", justify="right")
    
    total_processed = region_stats.files_processed + kind_stats.files_processed + lang_stats.files_processed
    total_moved = region_stats.files_moved + kind_stats.files_moved
    total_symlinks = lang_stats.symlinks_created
    
    table.add_row("Files Processed", str(total_processed))
    table.add_row("Files Moved", str(total_moved))
    table.add_row("Symlinks Created", str(total_symlinks))
    table.add_row("Errors", str(region_stats.errors + kind_stats.errors + lang_stats.errors))
    
    console.print(table)


def _display_stats(stats):
    """Display organization statistics in a nice table."""
    table = Table(title="Organization Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="magenta", justify="right")
    
    table.add_row("Files Processed", str(stats.files_processed))
    table.add_row("Files Moved", str(stats.files_moved))
    table.add_row("Files Copied", str(stats.files_copied))
    table.add_row("Symlinks Created", str(stats.symlinks_created))
    table.add_row("Directories Created", str(stats.directories_created))
    table.add_row("Files Skipped", str(stats.skipped))
    table.add_row("Errors", str(stats.errors))
    
    console.print(table)
