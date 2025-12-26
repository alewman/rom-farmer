"""Command-line interface for ROM Farmer."""

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table

from romfarmer.core.logger import get_logger
from romfarmer.core.config import RomGroomerConfig
from .organize import organize_group
from .dat import dat_group
from .scan import scan_group
from .metadata_commands import metadata_group
from .build import build_group
from .lists import lists_group
from .quick import quick
from .cache import cache_group


@click.group()
@click.option("--config", type=click.Path(exists=True), help="Config file path")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Quiet output")
@click.pass_context
def cli(ctx: click.Context, config: str, verbose: bool, quiet: bool) -> None:
    """
    ROM Farmer - Enterprise-grade ROM collection management.
    
    Organize, validate, and manage your ROM collections with database-backed
    cataloging and intelligent organization.
    """
    # Initialize context
    ctx.ensure_object(dict)
    
    # Load configuration
    config_path = Path(config) if config else None
    ctx.obj["config"] = RomGroomerConfig.load(config_path)
    
    # Setup logging
    import logging
    if verbose:
        level = logging.DEBUG
    elif quiet:
        level = logging.WARNING
    else:
        level = logging.INFO
    
    ctx.obj["logger"] = get_logger(level=level)
    ctx.obj["console"] = Console()


@cli.command()
@click.pass_context
def init(ctx: click.Context) -> None:
    """Initialize ROM Farmer configuration."""
    logger = ctx.obj["logger"]
    console = ctx.obj["console"]
    
    logger.section("Initializing ROM Farmer")
    
    # Create default configuration
    config = RomGroomerConfig.create_default_config()
    
    # Save configuration
    config_path = Path.home() / ".config" / "romfarmer" / "config.yaml"
    config.save(config_path)
    
    logger.success(f"Configuration saved to [path]{config_path}[/path]")
    
    # Create database directory
    db_path = config.database.path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.success(f"Database directory created at [path]{db_path.parent}[/path]")
    
    # Display profiles
    console.print("\n[bold]Available Profiles:[/bold]")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Profile", style="green")
    table.add_column("Regions")
    table.add_column("Languages")
    table.add_column("Exclude Regions")
    
    for name, profile in config.profiles.items():
        table.add_row(
            name,
            ", ".join(profile.regions),
            "Yes" if profile.organize_languages else "No",
            ", ".join(profile.exclude_language_regions),
        )
    
    console.print(table)
    console.print("\n[dim]Edit ~/.config/romfarmer/config.yaml to customize profiles[/dim]")


@cli.group()
def catalog() -> None:
    """Manage ROM catalog database."""
    pass


@catalog.command("stats")
@click.pass_context
def catalog_stats(ctx: click.Context) -> None:
    """Display catalog statistics."""
    from romfarmer.catalog.database import RomGroomerDatabase
    
    config = ctx.obj["config"]
    console = ctx.obj["console"]
    
    db = RomGroomerDatabase(str(config.database.path))
    
    with db.get_session() as session:
        stats = db.get_statistics(session)
    
    db.close()
    
    console.print("\n[bold]Catalog Statistics[/bold]\n")
    
    table = Table(show_header=False, box=None)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green", justify="right")
    
    table.add_row("DAT Files", str(stats["total_dat_files"]))
    table.add_row("DAT Games", str(stats["total_dat_games"]))
    table.add_row("ROM Files", str(stats["total_rom_files"]))
    table.add_row("Verified ROMs", str(stats["verified_roms"]))
    table.add_row("Total Operations", str(stats["total_operations"]))
    
    console.print(table)
    console.print()


@cli.command()
@click.argument("source", type=click.Path(exists=True))
@click.option("--profile", "-p", help="Organization profile to use")
@click.option("--dest", "-d", type=click.Path(), help="Destination directory")
@click.option("--dry-run", is_flag=True, help="Simulate without making changes")
@click.pass_context
def organize(
    ctx: click.Context,
    source: str,
    profile: str,
    dest: str,
    dry_run: bool,
) -> None:
    """
    Organize ROMs according to profile settings.
    
    Example:
        romfarmer organize ~/roms/nes --profile nes-usa --dest ~/organized/nes
    """
    logger = ctx.obj["logger"]
    config = ctx.obj["config"]
    
    logger.section(f"Organizing ROMs from {source}")
    
    if profile:
        org_profile = config.get_profile(profile)
        if not org_profile:
            logger.error(f"Profile '{profile}' not found")
            raise click.Abort()
        
        logger.info(f"Using profile: [highlight]{profile}[/highlight]")
    else:
        logger.warning("No profile specified, using default settings")
    
    if dry_run:
        logger.info("[yellow]DRY RUN MODE - No changes will be made[/yellow]")
    
    # TODO: Implement organization logic
    logger.warning("Organization logic not yet implemented")


@cli.command()
@click.argument("source", type=click.Path(exists=True))
@click.option("--dat", type=click.Path(exists=True), help="DAT file for validation")
@click.pass_context
def validate(ctx: click.Context, source: str, dat: str) -> None:
    """
    Validate ROM collection against DAT file.
    
    Example:
        romfarmer validate ~/roms/nes --dat ~/dats/nes.dat
    """
    logger = ctx.obj["logger"]
    
    logger.section(f"Validating ROMs in {source}")
    
    if dat:
        logger.info(f"Using DAT: [path]{dat}[/path]")
    
    # TODO: Implement validation logic
    logger.warning("Validation logic not yet implemented")


@cli.group()
def profile() -> None:
    """Manage organization profiles."""
    pass


@profile.command("list")
@click.pass_context
def profile_list(ctx: click.Context) -> None:
    """List all organization profiles."""
    config = ctx.obj["config"]
    console = ctx.obj["console"]
    
    table = Table(show_header=True, header_style="bold cyan", title="Organization Profiles")
    table.add_column("Profile", style="green")
    table.add_column("Regions")
    table.add_column("Languages")
    table.add_column("Exclude Regions")
    table.add_column("Kinds")
    
    for name, prof in config.profiles.items():
        table.add_row(
            name,
            ", ".join(prof.regions[:3]) + ("..." if len(prof.regions) > 3 else ""),
            "✓" if prof.organize_languages else "✗",
            ", ".join(prof.exclude_language_regions),
            "✓" if prof.organize_kinds else "✗",
        )
    
    console.print(table)


# Add command groups
cli.add_command(quick)
cli.add_command(build_group)
cli.add_command(organize_group)
cli.add_command(dat_group)
cli.add_command(scan_group)
cli.add_command(metadata_group)
cli.add_command(lists_group)
cli.add_command(cache_group)


if __name__ == "__main__":
    cli()
