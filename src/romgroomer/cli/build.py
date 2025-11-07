"""
Build commands for ROM Groomer.

Multi-platform ROM processing orchestration.
"""

import click
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from romgroomer.build_orchestrator import BuildOrchestrator, BuildStatus


console = Console()


@click.group(name='build')
def build_group():
    """
    Multi-platform build orchestration.
    
    Run complete builds across multiple platforms with progress tracking,
    error handling, and resume capability.
    """
    pass


@build_group.command('run')
@click.argument('build_name')
@click.option('--platforms', help='Comma-separated platform list (overrides config)')
@click.option('--resume', is_flag=True, help='Resume interrupted build')
@click.option('--validate-only', is_flag=True, help='Only validate, do not run')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
def build_run(build_name: str, platforms: str = None, resume: bool = False, validate_only: bool = False, yes: bool = False):
    """
    Run a build profile.
    
    BUILD_NAME is the name of the build config (without .yaml extension).
    
    Examples:
    
        \b
        # Run complete build
        romgroomer build run batocera-complete
        
        \b
        # Run specific platforms only
        romgroomer build run batocera-complete --platforms saturn,wii
        
        \b
        # Resume interrupted build
        romgroomer build run batocera-complete --resume
        
        \b
        # Validate without running
        romgroomer build run batocera-complete --validate-only
    """
    try:
        # Load orchestrator
        with console.status(f"[cyan]Loading build config: {build_name}..."):
            orchestrator = BuildOrchestrator.from_config(build_name)
        
        # Override platforms if specified
        if platforms:
            platform_list = [p.strip() for p in platforms.split(',')]
            console.print(f"[yellow]Overriding platforms: {', '.join(platform_list)}[/yellow]")
            orchestrator.config.platforms = platform_list
        
        # Show build info
        _show_build_info(orchestrator)
        
        # Validate
        console.print("\n[cyan]Validating build...[/cyan]")
        if not orchestrator.validate():
            console.print("[red]❌ Validation failed[/red]")
            sys.exit(1)
        
        if validate_only:
            console.print("[green]✅ Validation passed (dry run)[/green]")
            return
        
        # Confirm if not resuming and not auto-confirmed
        if not resume and not yes:
            if not click.confirm("\nProceed with build?", default=True):
                console.print("[yellow]Build cancelled[/yellow]")
                return
        
        # Run build
        console.print(f"\n[green]Starting build: {build_name}[/green]\n")
        orchestrator.run(resume=resume)
        
        console.print(f"\n[green]✅ Build complete: {build_name}[/green]")
        
    except FileNotFoundError as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Build failed: {e}[/red]")
        sys.exit(1)


@build_group.command('status')
@click.argument('build_name')
@click.option('--verbose', is_flag=True, help='Show detailed platform information')
def build_status(build_name: str, verbose: bool = False):
    """
    Show build status.
    
    BUILD_NAME is the name of the build config.
    
    Examples:
    
        \b
        # Show status
        romgroomer build status batocera-complete
        
        \b
        # Show detailed status
        romgroomer build status batocera-complete --verbose
    """
    try:
        orchestrator = BuildOrchestrator.from_config(build_name)
        status_data = orchestrator.get_status()
        
        # Show status table
        _show_status_table(status_data)
        
        # Show platform lists if verbose
        if verbose:
            _show_platform_details(status_data)
        
    except FileNotFoundError as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@build_group.command('resume')
@click.argument('build_name')
def build_resume(build_name: str):
    """
    Resume interrupted build.
    
    BUILD_NAME is the name of the build config.
    
    Examples:
    
        \b
        # Resume build
        romgroomer build resume batocera-complete
    """
    try:
        console.print(f"[cyan]Resuming build: {build_name}[/cyan]\n")
        
        orchestrator = BuildOrchestrator.from_config(build_name)
        
        # Show what will be skipped
        status_data = orchestrator.get_status()
        if status_data['completed_platforms']:
            console.print("[green]Skipping completed platforms:[/green]")
            for platform in status_data['completed_platforms']:
                console.print(f"  ✅ {platform}")
            console.print()
        
        # Resume
        orchestrator.resume()
        
        console.print(f"\n[green]✅ Build complete: {build_name}[/green]")
        
    except FileNotFoundError as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Build failed: {e}[/red]")
        sys.exit(1)


@build_group.command('list')
@click.option('--verbose', is_flag=True, help='Show platform lists')
def build_list(verbose: bool = False):
    """
    List available build profiles.
    
    Examples:
    
        \b
        # List builds
        romgroomer build list
        
        \b
        # List with details
        romgroomer build list --verbose
    """
    import yaml
    
    builds_dir = Path("config/builds")
    
    if not builds_dir.exists():
        console.print("[yellow]No build configs found[/yellow]")
        return
    
    # Find all build configs
    configs = []
    for config_file in sorted(builds_dir.glob("*.yaml")):
        if config_file.name == 'template.yaml':
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
        name = config['name']
        description = config.get('description', 'No description')
        platform_count = len(config.get('platforms', []))
        
        if verbose:
            platform_list = ', '.join(config.get('platforms', [])[:5])
            if platform_count > 5:
                platform_list += f", ... (+{platform_count - 5} more)"
            table.add_row(name, description, str(platform_count), platform_list)
        else:
            table.add_row(name, description, str(platform_count))
    
    console.print(table)


@build_group.command('clean')
@click.argument('build_name')
def build_clean(build_name: str):
    """
    Clean build state (allows fresh start).
    
    BUILD_NAME is the name of the build config.
    
    This removes the build state file, allowing you to start fresh.
    Does NOT delete any output files.
    
    Examples:
    
        \b
        # Clean state
        romgroomer build clean batocera-complete
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


def _show_build_info(orchestrator: BuildOrchestrator):
    """Show build information panel."""
    version = getattr(orchestrator.config, 'version', 'N/A')
    description = getattr(orchestrator.config, 'description', 'N/A')
    storage = getattr(orchestrator.config, 'storage', {})
    output_base = storage.get('output_base', 'N/A') if isinstance(storage, dict) else 'N/A'
    
    info = f"""
[cyan]Build:[/cyan] {orchestrator.config.name}
[cyan]Description:[/cyan] {description}
[cyan]Version:[/cyan] {version}
[cyan]Platforms:[/cyan] {len(orchestrator.config.platforms)}
[cyan]Output:[/cyan] {output_base}
    """
    
    console.print(Panel(info.strip(), title="Build Configuration", border_style="cyan"))


def _show_status_table(status_data: dict):
    """Show status table."""
    table = Table(title=f"Build Status: {status_data['build_name']}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    # Status with color
    status = status_data['status']
    if status == BuildStatus.COMPLETED.value:
        status_display = "[green]completed[/green]"
    elif status == BuildStatus.FAILED.value:
        status_display = "[red]failed[/red]"
    elif status == BuildStatus.RUNNING.value:
        status_display = "[yellow]running[/yellow]"
    else:
        status_display = status
    
    table.add_row("Status", status_display)
    table.add_row("Description", status_data['description'])
    table.add_row("Current Platform", status_data['current_platform'] or 'None')
    table.add_row("Progress", f"{status_data['progress']['percent']:.1f}%")
    table.add_row("Completed", str(status_data['progress']['completed']))
    table.add_row("Failed", str(status_data['progress']['failed']))
    table.add_row("Remaining", str(status_data['progress']['remaining']))
    
    console.print(table)


def _show_platform_details(status_data: dict):
    """Show detailed platform lists."""
    if status_data['completed_platforms']:
        console.print("\n[green]Completed Platforms:[/green]")
        for platform in status_data['completed_platforms']:
            console.print(f"  ✅ {platform}")
    
    if status_data['failed_platforms']:
        console.print("\n[red]Failed Platforms:[/red]")
        for platform in status_data['failed_platforms']:
            console.print(f"  ❌ {platform}")
