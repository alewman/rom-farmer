"""
Build commands for ROM Farmer.

Multi-platform ROM processing orchestration.
"""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@click.group(name="build")
def build_group():
    """
    Multi-platform build orchestration.

    Run complete builds across multiple platforms with progress tracking,
    error handling, and resume capability.
    """
    pass


@build_group.command("run")
@click.argument("build_name")
@click.option("--platforms", help="Comma-separated platform list (overrides config)")
@click.option("--resume", is_flag=True, help="Resume interrupted build")
@click.option("--validate-only", is_flag=True, help="Only validate, do not run")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option("--test-sample", type=int, help="Test mode: randomly sample N games per platform")
@click.option("--seed", type=int, help="Random seed for reproducible test sampling")
@click.option(
    "--passthrough", is_flag=True, help="Skip extraction/compression, copy original archives"
)
@click.option("--target", help="Override target (e.g., batocera-pc, rocknix-r36s)")
@click.option("--storage-budget", help="Override storage budget (e.g., 512gb, 1tb, unlimited)")
@click.option(
    "--dry-run", "dry_run", is_flag=True, help="Print the BuildPlan and exit; no files are written."
)
def build_run(
    build_name: str,
    platforms: str = None,
    resume: bool = False,
    validate_only: bool = False,
    yes: bool = False,
    test_sample: int = None,
    seed: int = None,
    passthrough: bool = False,
    target: str = None,
    storage_budget: str = None,
    dry_run: bool = False,
):
    """
    Run a build profile.

    BUILD_NAME is the name of the build config (without .yaml extension).

    Examples:

        \b
        # Run complete build
        romfarmer build run batocera-complete

        \b
        # Run specific platforms only
        romfarmer build run batocera-complete --platforms saturn,wii

        \b
        # Resume interrupted build
        romfarmer build run batocera-complete --resume

        \b
        # Validate without running
        romfarmer build run batocera-complete --validate-only

        \b
        # Test mode: 10 random games per platform
        romfarmer build run batocera-complete --test-sample 10

        \b
        # Reproducible test (same random selection)
        romfarmer build run batocera-complete --test-sample 10 --seed 42

        \b
        # Fast test: skip extraction/compression, copy original archives
        romfarmer build run batocera-complete --test-sample 10 --passthrough

        \b
        # Override target for existing build config
        romfarmer build run batocera-complete --target rocknix-r36s

        \b
        # Override storage budget
        romfarmer build run r36s-build --storage-budget 256gb
    """
    try:
        from romfarmer.new_orchestrator import NewBuildOrchestrator

        console.print(f"[cyan]Loading build: {build_name}[/cyan]")
        with console.status("[cyan]Resolving build config..."):
            platform_list = [p.strip() for p in platforms.split(",")] if platforms else None
            orchestrator = NewBuildOrchestrator.from_config(
                build_name, platform_filter=platform_list
            )

        # Apply --platforms filter (post-load filter kept for any remaining differences)
        if platform_list:
            orchestrator.resolved_configs = [
                rc for rc in orchestrator.resolved_configs if rc.platform in platform_list
            ]
            console.print(f"[yellow]Filtering to platforms: {', '.join(platform_list)}[/yellow]")

        spec = orchestrator.build_spec
        info = f"""
[cyan]Build:[/cyan] {spec.name}
[cyan]Description:[/cyan] {spec.description}
[cyan]Target:[/cyan] {spec.target}
[cyan]Recipes:[/cyan] {", ".join(spec.recipes)}
[cyan]Platforms:[/cyan] {len(orchestrator.resolved_configs)}
[cyan]Output:[/cyan] {spec.get_output_base()}
        """
        console.print(Panel(info.strip(), title="Build Configuration", border_style="cyan"))

        console.print("\n[cyan]Validating build...[/cyan]")
        if not orchestrator.validate():
            console.print("[red]❌ Validation failed[/red]")
            sys.exit(1)

        if validate_only:
            console.print("[green]✅ Validation passed[/green]")
            return

        if not resume and not yes:
            if not click.confirm("\nProceed with build?", default=True):
                console.print("[yellow]Build cancelled[/yellow]")
                return

        if dry_run:
            orchestrator._dry_run = True
            console.print("[yellow]--dry-run: building plans, no files written[/yellow]\n")
        if test_sample:
            orchestrator._test_sample = test_sample
            orchestrator._test_seed = seed or 0
            console.print(
                f"[yellow]--test-sample: {test_sample} games per platform (seed={seed or 0})[/yellow]\n"
            )
        if passthrough:
            orchestrator._passthrough = True
            console.print(
                "[yellow]⚡ PASSTHROUGH MODE: Skipping extraction/compression, copying original archives[/yellow]\n"
            )
        console.print(f"\n[green]Starting build: {build_name}[/green]\n")
        orchestrator.run(resume=resume)
        if dry_run:
            console.print("\n[yellow]✅ Dry-run complete — no files written[/yellow]")
        else:
            console.print(f"\n[green]✅ Build complete: {build_name}[/green]")

    except FileNotFoundError as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Build failed: {e}[/red]")
        sys.exit(1)


@build_group.command("status")
@click.argument("build_name")
@click.option("--verbose", is_flag=True, help="Show detailed platform information")
def build_status(build_name: str, verbose: bool = False):
    """
    Show build status.

    BUILD_NAME is the name of the build config.

    Examples:

        \b
        # Show status
        romfarmer build status batocera-complete

        \b
        # Show detailed status
        romfarmer build status batocera-complete --verbose
    """
    try:
        from romfarmer.new_orchestrator import NewBuildOrchestrator

        orchestrator = NewBuildOrchestrator.from_config(build_name)
        console.print(f"Build: {build_name}")
        console.print(f"Platforms: {len(orchestrator.resolved_configs)}")
        for rc in orchestrator.resolved_configs:
            console.print(f"  {rc.platform}")

    except FileNotFoundError as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@build_group.command("resume")
@click.argument("build_name")
def build_resume(build_name: str):
    """
    Resume interrupted build.

    BUILD_NAME is the name of the build config.

    Examples:

        \b
        # Resume build
        romfarmer build resume batocera-complete
    """
    try:
        console.print(f"[cyan]Resuming build: {build_name}[/cyan]\n")
        from romfarmer.new_orchestrator import NewBuildOrchestrator

        orchestrator = NewBuildOrchestrator.from_config(build_name)
        orchestrator.run(resume=True)
        console.print(f"\n[green]✅ Build complete: {build_name}[/green]")

    except FileNotFoundError as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Build failed: {e}[/red]")
        sys.exit(1)


@build_group.command("list")
@click.option("--verbose", is_flag=True, help="Show platform lists")
def build_list(verbose: bool = False):
    """
    List available build profiles.

    Examples:

        \b
        # List builds
        romfarmer build list

        \b
        # List with details
        romfarmer build list --verbose
    """
    import yaml

    builds_dir = Path("config/builds")

    if not builds_dir.exists():
        console.print("[yellow]No build configs found[/yellow]")
        return

    # Find all build configs
    configs = []
    for config_file in sorted(builds_dir.glob("*.yaml")):
        if config_file.name == "template.yaml":
            continue

        try:
            with open(config_file) as f:
                config = yaml.safe_load(f)
            configs.append(config)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load {config_file}: {e}[/yellow]")

    if not configs:
        console.print("[yellow]No build configs found[/yellow]")
        return

    # Show table
    table = Table(title="Available Build Profiles")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    table.add_column("Platforms", style="green", justify="right")

    if verbose:
        table.add_column("Platform List", style="dim")

    for config in configs:
        name = config["name"]
        description = config.get("description", "No description")
        platform_count = len(config.get("platforms", []))

        if verbose:
            platform_list = ", ".join(config.get("platforms", [])[:5])
            if platform_count > 5:
                platform_list += f", ... (+{platform_count - 5} more)"
            table.add_row(name, description, str(platform_count), platform_list)
        else:
            table.add_row(name, description, str(platform_count))

    console.print(table)


@build_group.command("targets")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed target information")
def build_targets(verbose: bool = False):
    """
    List available targets (frontend + device combinations).

    Examples:

        \b
        # List targets
        romfarmer build targets

        \b
        # List with details
        romfarmer build targets --verbose
    """
    from romfarmer.config import list_devices, list_frontends, list_targets, load_composed_target

    # List targets
    targets = list_targets()

    if not targets:
        console.print("[yellow]No targets found in config/targets/[/yellow]")
        return

    # Show targets table
    table = Table(title="Available Targets")
    table.add_column("Target", style="cyan", no_wrap=True)
    table.add_column("Frontend", style="green")
    table.add_column("Device", style="magenta")

    if verbose:
        table.add_column("Unsupported Platforms", style="yellow")
        table.add_column("Manual/Video Support", style="dim")

    for target_name in sorted(targets):
        try:
            composed = load_composed_target(target_name)
            frontend = composed.frontend.name
            device = composed.device.name

            if verbose:
                unsupported = ", ".join(composed.device.unsupported_platforms[:3]) or "None"
                if len(composed.device.unsupported_platforms) > 3:
                    unsupported += f" (+{len(composed.device.unsupported_platforms) - 3})"

                from romfarmer.config.frontend import MediaType

                manual = "✓" if composed.supports_media(MediaType.MANUAL) else "✗"
                video = "✓" if composed.supports_media(MediaType.VIDEO) else "✗"
                media_support = f"Manual: {manual}, Video: {video}"

                table.add_row(target_name, frontend, device, unsupported, media_support)
            else:
                table.add_row(target_name, frontend, device)
        except Exception as e:
            table.add_row(target_name, f"[red]Error: {e}[/red]", "")

    console.print(table)

    if verbose:
        # Also list frontends and devices
        console.print()

        frontend_table = Table(title="Available Frontends")
        frontend_table.add_column("Frontend", style="green")
        for frontend in sorted(list_frontends()):
            frontend_table.add_row(frontend)
        console.print(frontend_table)

        console.print()

        device_table = Table(title="Available Devices")
        device_table.add_column("Device", style="magenta")
        for device in sorted(list_devices()):
            device_table.add_row(device)
        console.print(device_table)


@build_group.command("clean")
@click.argument("build_name")
def build_clean(build_name: str):
    """
    Clean build state (allows fresh start).

    BUILD_NAME is the name of the build config.

    This removes the build state file, allowing you to start fresh.
    Does NOT delete any output files.

    Examples:

        \b
        # Clean state
        romfarmer build clean batocera-complete
    """
    state_file = Path(f".build_state_{build_name}.yaml")

    if not state_file.exists():
        console.print(f"[yellow]No state file found for: {build_name}[/yellow]")
        return

    if click.confirm(f"Remove state file: {state_file}?", default=False):
        state_file.unlink()
        console.print(f"[green]✅ State file removed: {state_file}[/green]")
        console.print("[cyan]You can now run a fresh build[/cyan]")
    else:
        console.print("[yellow]Cancelled[/yellow]")


def _show_status_table(status_data: dict) -> None:
    """Show status table."""
    table = Table(title=f"Build Status: {status_data.get('build_name', '')}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    str(status_data.get("status", "unknown"))
    console.print(table)


def _show_platform_details(status_data: dict):
    """Show detailed platform lists."""
    if status_data["completed_platforms"]:
        console.print("\n[green]Completed Platforms:[/green]")
        for platform in status_data["completed_platforms"]:
            console.print(f"  ✅ {platform}")

    if status_data["failed_platforms"]:
        console.print("\n[red]Failed Platforms:[/red]")
        for platform in status_data["failed_platforms"]:
            console.print(f"  ❌ {platform}")
