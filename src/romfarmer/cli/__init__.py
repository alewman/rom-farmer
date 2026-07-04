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
from .cas import cas_group
from .plugin import plugin_group
from .farmhand import farmhand_group
from .generation import generation_group
from .scores import scores_group
from .plan import plan_group


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
    
    For specific organization modes, use the subcommands instead:
      romfarmer organize region /roms/nes --keep-in-place USA
      romfarmer organize kind /roms/nes
      romfarmer organize language /roms/nes --mode hardlink
      romfarmer organize alphabetical /roms/nes --strategy smart
      romfarmer organize all /roms/nes --region-keep USA
    
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
        logger.warning("No profile specified. Use a subcommand for direct organization:")
        logger.info("  romfarmer organize region <dir>")
        logger.info("  romfarmer organize kind <dir>")
        logger.info("  romfarmer organize language <dir>")
        logger.info("  romfarmer organize alphabetical <dir>")
        logger.info("  romfarmer organize all <dir>")
        return


@cli.command()
@click.argument("source", type=click.Path(exists=True))
@click.option("--dat", type=click.Path(exists=True), help="DAT file for validation")
@click.option("--check-size", is_flag=True, help="Flag zero-size files")
@click.option("--check-m3u", is_flag=True, help="Verify M3U playlists reference existing files")
@click.pass_context
def validate(ctx: click.Context, source: str, dat: str, check_size: bool, check_m3u: bool) -> None:
    """
    Validate ROM collection against DAT file.
    
    Example:
        romfarmer validate ~/roms/nes --dat ~/dats/nes.dat
        romfarmer validate ~/roms/saturn --check-size --check-m3u
    """
    from romfarmer.dat_parser.parser import DATParser

    logger = ctx.obj["logger"]
    console = ctx.obj["console"]
    source_path = Path(source)
    
    logger.section(f"Validating ROMs in {source}")
    
    # Collect all files in source directory
    all_files = sorted(f for f in source_path.rglob("*") if f.is_file())
    
    if not all_files:
        logger.error("No files found in source directory")
        return
    
    logger.info(f"Found {len(all_files)} files")
    
    errors = 0
    warnings = 0
    
    # Basic checks (always run)
    zero_files = [f for f in all_files if f.stat().st_size == 0]
    if zero_files:
        errors += len(zero_files)
        logger.error(f"{len(zero_files)} zero-size file(s):")
        for zf in zero_files[:10]:
            logger.error(f"  {zf.relative_to(source_path)}")
        if len(zero_files) > 10:
            logger.error(f"  ... and {len(zero_files) - 10} more")
    
    # M3U validation
    if check_m3u:
        m3u_files = [f for f in all_files if f.suffix.lower() == '.m3u']
        if m3u_files:
            logger.info(f"Checking {len(m3u_files)} M3U playlists...")
            for m3u in m3u_files:
                try:
                    with open(m3u, 'r', encoding='utf-8', errors='ignore') as fh:
                        for line in fh:
                            line = line.strip()
                            if not line or line.startswith('#'):
                                continue
                            ref = m3u.parent / line
                            if not ref.exists():
                                logger.error(f"  {m3u.name}: missing reference -> {line}")
                                errors += 1
                except Exception as e:
                    logger.warning(f"  Could not read {m3u.name}: {e}")
                    warnings += 1
    
    # DAT validation
    if dat:
        dat_path = Path(dat)
        logger.info(f"Parsing DAT: {dat_path.name}")
        
        parser = DATParser()
        dat_file = parser.parse(dat_path)
        logger.info(f"DAT contains {dat_file.get_game_count()} games, {dat_file.get_rom_count()} ROMs")
        
        # Build set of ROM names from DAT (stem only for comparison)
        dat_stems = {Path(rom.name).stem for game in dat_file.games for rom in game.roms}
        
        # Build set of file stems we have
        file_stems = {f.stem for f in all_files if f.suffix.lower() not in {'.m3u', '.xml', '.txt', '.cfg'}}
        
        # Files we have that aren't in DAT
        extra = file_stems - dat_stems
        if extra:
            warnings += len(extra)
            logger.warning(f"{len(extra)} file(s) not in DAT (extras/transforms OK):")
            for name in sorted(extra)[:10]:
                logger.warning(f"  + {name}")
            if len(extra) > 10:
                logger.warning(f"  ... and {len(extra) - 10} more")
        
        # DAT entries we're missing
        missing = dat_stems - file_stems
        if missing:
            logger.info(f"{len(missing)} DAT entries not found on disk (normal for filtered builds):")
            for name in sorted(missing)[:10]:
                logger.info(f"  - {name}")
            if len(missing) > 10:
                logger.info(f"  ... and {len(missing) - 10} more")
        
        matched = dat_stems & file_stems
        logger.info(f"DAT match: {len(matched)}/{len(dat_stems)} ({100*len(matched)/max(len(dat_stems),1):.0f}%)")
    
    # Summary
    table = Table(title="Validation Summary")
    table.add_column("Check", style="cyan")
    table.add_column("Result", style="green")
    table.add_row("Total files", str(len(all_files)))
    table.add_row("Zero-size files", f"[red]{len(zero_files)}[/red]" if zero_files else "0")
    if dat:
        table.add_row("DAT matched", str(len(matched)))
        table.add_row("DAT missing", str(len(missing)))
        table.add_row("Extra files", str(len(extra)))
    table.add_row("Errors", f"[red]{errors}[/red]" if errors else "[green]0[/green]")
    table.add_row("Warnings", f"[yellow]{warnings}[/yellow]" if warnings else "0")
    console.print(table)
    
    if errors > 0:
        logger.error(f"Validation FAILED with {errors} error(s)")
    else:
        logger.success("Validation PASSED")


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


# ── Web UI Command ───────────────────────────────────────────────────────────


@cli.command()
@click.option("--host", default="0.0.0.0", help="Bind address")
@click.option("--port", "-p", default=8420, type=int, help="Port number")
@click.option("--config-dir", type=click.Path(exists=True), help="Config directory (default: ./config)")
@click.option("--reload", "live_reload", is_flag=True, help="Enable auto-reload for development")
def web(host: str, port: int, config_dir: str, live_reload: bool) -> None:
    """Launch the ROM Farmer web UI.

    Starts a local web server for managing configs and builds
    through a browser interface.

    Example:
        romfarmer web
        romfarmer web --port 9000
        romfarmer web --config-dir /path/to/config
    """
    try:
        import uvicorn
    except ImportError:
        click.echo("Error: uvicorn is required. Install with: pip install 'romfarmer[web]'", err=True)
        raise click.Abort()

    from pathlib import Path as _Path
    config_root = _Path(config_dir) if config_dir else _Path.cwd() / "config"
    if not config_root.exists():
        click.echo(f"Config directory not found: {config_root}", err=True)
        raise click.Abort()

    click.echo(f"🎮 ROM Farmer Web UI — http://{host}:{port}")
    click.echo(f"   Config: {config_root}")

    # Set config root via env so the app factory can pick it up
    import os
    os.environ["ROMFARMER_CONFIG_ROOT"] = str(config_root)

    uvicorn.run(
        "romfarmer.web.app:create_app",
        factory=True,
        host=host,
        port=port,
        reload=live_reload,
        log_level="info",
    )


# Add command groups
cli.add_command(quick)
cli.add_command(build_group)
cli.add_command(organize_group)
cli.add_command(dat_group)
cli.add_command(scan_group)
cli.add_command(metadata_group)
cli.add_command(lists_group)
cli.add_command(cache_group)
cli.add_command(cas_group)
cli.add_command(plugin_group)
cli.add_command(farmhand_group)
cli.add_command(generation_group)
cli.add_command(scores_group)
cli.add_command(plan_group, name="plan")


if __name__ == "__main__":
    cli()
