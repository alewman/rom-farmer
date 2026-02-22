"""CLI commands for Farm-Hand deployment system.

Provides: romfarmer farmhand connect|scan|plan|deploy|status|diff
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def _check_paramiko() -> None:
    """Ensure paramiko is installed."""
    try:
        import paramiko  # noqa: F401
    except ImportError:
        click.echo(
            "Error: paramiko is required for Farm-Hand. "
            "Install with: pip install 'romfarmer[farmhand]'",
            err=True,
        )
        raise click.Abort()


@click.group(name="farmhand")
def farmhand_group() -> None:
    """Farm-Hand: AI-driven ROM deployment to remote targets.

    Connect to Batocera/RockNIX devices, analyze storage, plan optimal
    ROM deployment, and transfer files via SSH.

    Example workflow:
        romfarmer farmhand connect batocera-nuc
        romfarmer farmhand scan batocera-nuc
        romfarmer farmhand plan --target batocera-nuc
        romfarmer farmhand deploy --target batocera-nuc --dry-run
    """
    pass


# ── Target management ────────────────────────────────────────────────────────


@farmhand_group.group(name="target")
def target_group() -> None:
    """Manage target connection configs (config/farmhand/targets/).

    Target configs are YAML files that store SSH connection details,
    system identity, and volume hints. Create one per device.

    Examples:
        romfarmer farmhand target list
        romfarmer farmhand target show batocera-nuc
    """
    pass


@target_group.command(name="list")
def target_list() -> None:
    """List all configured targets."""
    from romfarmer.core.paths import get_paths
    from romfarmer.farmhand.config import list_targets, list_profiles, get_targets_dir

    workspace = get_paths().workspace_root
    targets = list_targets(workspace)
    profiles = list_profiles(workspace)
    console = Console()

    if not targets:
        console.print("[dim]No target configs found.[/dim]")
        console.print(f"Create one at: {get_targets_dir(workspace)}/")
        return

    table = Table(title=f"Farm-Hand Targets ({len(targets)})")
    table.add_column("Name", style="cyan bold")
    table.add_column("Has Scan", style="green")

    for name in targets:
        has_profile = "yes" if name in profiles else "no"
        table.add_row(name, has_profile)

    console.print(table)


@target_group.command(name="show")
@click.argument("name")
def target_show(name: str) -> None:
    """Show details of a target config."""
    from romfarmer.core.paths import get_paths
    from romfarmer.farmhand.config import load_target_config, load_profile

    workspace = get_paths().workspace_root
    console = Console()

    try:
        config = load_target_config(workspace, name)
    except Exception as exc:
        console.print(f"[red]{exc}[/red]")
        raise click.Abort()

    # Mask password in display
    display_config = dict(config)
    if display_config.get("password"):
        display_config["password"] = "****"

    import yaml
    console.print(Panel(
        yaml.dump(display_config, default_flow_style=False, sort_keys=False).rstrip(),
        title=f"Target: {name}",
    ))

    # Show profile status
    profile = load_profile(workspace, name)
    if profile:
        si = profile.system_info
        console.print(f"\n[bold green]Scan available[/bold green]"
                      f" (last: {profile.last_scanned:%Y-%m-%d %H:%M})")
        if si:
            console.print(f"  {si.hostname} | {si.os_name} {si.os_version} | {si.architecture}")
        console.print(f"  Volumes: {len(profile.volumes)} | "
                      f"Platforms: {len(profile.existing_roms)} | "
                      f"Available: {profile.total_available_gb():.1f} GB")
    else:
        console.print(f"\n[dim]No scan profile yet. Run: romfarmer farmhand scan {name}[/dim]")


# ── Skill subcommands ────────────────────────────────────────────────────────


@farmhand_group.group(name="skill")
def skill_group() -> None:
    """Manage Farm-Hand skills — reusable agent procedures and artifacts.

    Skills are markdown contracts (SKILL.md) paired with machine-readable
    procedures and artifacts (scripts, game lists, configs). The agent
    auto-captures successful workflows and you can also create skills
    by hand.

    Examples:
        romfarmer farmhand skill list
        romfarmer farmhand skill show scan-and-plan
        romfarmer farmhand skill search "deploy budget"
        romfarmer farmhand skill cat scan-and-plan procedure.yaml
    """
    pass


@skill_group.command(name="list")
@click.option(
    "--category", "-c", default=None,
    help="Filter by category (deployment, build, target, curation, maintenance, scripting, workflow).",
)
@click.option("--tag", "-t", default=None, help="Filter by tag.")
@click.option("--platform", "-p", default=None, help="Filter by ROM platform.")
@click.option("--verbose", "-v", is_flag=True, help="Show full details.")
def skill_list(
    category: Optional[str],
    tag: Optional[str],
    platform: Optional[str],
    verbose: bool,
) -> None:
    """List all available skills."""
    from romfarmer.farmhand.skills import SkillStore, SkillCategory

    store = _get_skill_store()
    skills = store.search(
        category=SkillCategory(category) if category else None,
        tags=[tag] if tag else None,
        platform=platform,
    )

    console = Console()
    if not skills:
        console.print("[dim]No skills found.[/dim]")
        return

    table = Table(title=f"Farm-Hand Skills ({len(skills)})", show_lines=verbose)
    table.add_column("Name", style="cyan bold", min_width=24)
    table.add_column("Category", style="yellow")
    table.add_column("Description", min_width=40)
    table.add_column("Tags", style="dim")
    table.add_column("Source", style="dim")

    for skill in sorted(skills, key=lambda s: (s.meta.category.value, s.meta.name)):
        source = "builtin" if skill.is_builtin else "user"
        tags_str = ", ".join(skill.meta.tags[:4])
        if len(skill.meta.tags) > 4:
            tags_str += f" +{len(skill.meta.tags) - 4}"
        table.add_row(
            skill.meta.name,
            skill.meta.category.value,
            skill.meta.description[:60],
            tags_str,
            source,
        )

    console.print(table)


@skill_group.command(name="show")
@click.argument("name")
def skill_show(name: str) -> None:
    """Show full details of a skill, including SKILL.md content."""
    store = _get_skill_store()
    skill = store.get(name)
    console = Console()

    if not skill:
        console.print(f"[red]Skill '{name}' not found.[/red]")
        raise click.Abort()

    # Header panel
    meta = skill.meta
    header_lines = [
        f"[bold cyan]{meta.name}[/bold cyan] v{meta.version}",
        f"[yellow]{meta.category.value}[/yellow] | by {meta.author}",
        f"Created: {meta.created:%Y-%m-%d} | Updated: {meta.updated:%Y-%m-%d}",
    ]
    if meta.tags:
        header_lines.append(f"Tags: {', '.join(meta.tags)}")
    if meta.platforms:
        header_lines.append(f"Platforms: {', '.join(meta.platforms)}")
    if meta.targets:
        header_lines.append(f"Targets: {', '.join(meta.targets)}")
    if meta.tools_used:
        header_lines.append(f"Tools: {', '.join(meta.tools_used)}")

    source_label = "builtin" if skill.is_builtin else str(skill.source_path)
    header_lines.append(f"Source: {source_label}")

    console.print(Panel("\n".join(header_lines), title="Skill Details"))

    # Parameters
    if meta.params:
        ptable = Table(title="Parameters")
        ptable.add_column("Name", style="green")
        ptable.add_column("Type")
        ptable.add_column("Required")
        ptable.add_column("Default")
        ptable.add_column("Description")
        for p in meta.params:
            ptable.add_row(
                p.name, p.type, "yes" if p.required else "",
                str(p.default) if p.default is not None else "",
                p.description,
            )
        console.print(ptable)

    # Artifacts
    if meta.artifacts:
        atable = Table(title="Artifacts")
        atable.add_column("File", style="cyan")
        atable.add_column("Type")
        atable.add_column("Description")
        for a in meta.artifacts:
            atable.add_row(a.filename, a.artifact_type, a.description)
        console.print(atable)

    # Procedure steps
    if skill.steps:
        stable = Table(title="Procedure Steps")
        stable.add_column("#", style="dim")
        stable.add_column("ID", style="green")
        stable.add_column("Action", style="yellow")
        stable.add_column("Description")
        for i, step in enumerate(skill.steps, 1):
            stable.add_row(
                str(i), step.id, step.action.value, step.description[:60],
            )
        console.print(stable)

    # Body
    if skill.body.strip():
        console.print(Panel(skill.body.strip(), title="SKILL.md Content"))


@skill_group.command(name="search")
@click.argument("query")
@click.option("--category", "-c", default=None, help="Filter by category.")
@click.option("--tag", "-t", default=None, help="Filter by tag.")
def skill_search(query: str, category: Optional[str], tag: Optional[str]) -> None:
    """Search skills by text query."""
    from romfarmer.farmhand.skills import SkillCategory

    store = _get_skill_store()
    results = store.search(
        query=query,
        category=SkillCategory(category) if category else None,
        tags=[tag] if tag else None,
    )

    console = Console()
    if not results:
        console.print(f"[dim]No skills matching '{query}'.[/dim]")
        return

    console.print(f"[bold]Found {len(results)} skill(s):[/bold]")
    for skill in results:
        source = "builtin" if skill.is_builtin else "user"
        console.print(
            f"  [cyan]{skill.meta.name}[/cyan] [{source}] — {skill.meta.description}"
        )


@skill_group.command(name="cat")
@click.argument("name")
@click.argument("filename", default="SKILL.md")
def skill_cat(name: str, filename: str) -> None:
    """Display a file from a skill (default: SKILL.md).

    Examples:
        romfarmer farmhand skill cat scan-and-plan
        romfarmer farmhand skill cat batocera-dual-volume-setup setup-rom-symlinks.sh
        romfarmer farmhand skill cat curated-essentials-list essentials/saturn.yaml
    """
    store = _get_skill_store()
    skill = store.get(name)
    console = Console()

    if not skill:
        console.print(f"[red]Skill '{name}' not found.[/red]")
        raise click.Abort()

    if filename == "SKILL.md":
        if skill.source_path:
            md_path = skill.source_path / "SKILL.md"
            if md_path.exists():
                console.print(md_path.read_text(encoding="utf-8"))
                return
        # Fallback: reconstruct from model
        console.print(skill.body)
        return

    content = store.get_artifact_content(name, filename)
    if content is None:
        console.print(f"[red]File '{filename}' not found in skill '{name}'.[/red]")
        raise click.Abort()
    console.print(content)


@skill_group.command(name="delete")
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation.")
def skill_delete(name: str, yes: bool) -> None:
    """Delete a user-created skill."""
    store = _get_skill_store()
    skill = store.get(name)
    console = Console()

    if not skill:
        console.print(f"[red]Skill '{name}' not found.[/red]")
        raise click.Abort()

    if skill.is_builtin:
        console.print(f"[red]Cannot delete builtin skill '{name}'.[/red]")
        raise click.Abort()

    if not yes:
        click.confirm(f"Delete skill '{name}'?", abort=True)

    store.delete(name)
    console.print(f"[green]Deleted skill '{name}'.[/green]")


@skill_group.command(name="path")
@click.argument("name")
def skill_path(name: str) -> None:
    """Print the filesystem path of a skill."""
    store = _get_skill_store()
    skill = store.get(name)
    console = Console()

    if not skill or not skill.source_path:
        console.print(f"[red]Skill '{name}' not found.[/red]")
        raise click.Abort()

    console.print(str(skill.source_path))


def _get_skill_store() -> "SkillStore":
    """Create a SkillStore with standard paths."""
    from romfarmer.core.paths import get_paths
    from romfarmer.farmhand.skills import SkillStore

    paths = get_paths()
    return SkillStore(workspace_root=paths.workspace_root)


# ── Connect ──────────────────────────────────────────────────────────────────


@farmhand_group.command()
@click.argument("host_or_target")
@click.option("--port", "-p", default=22, type=int, help="SSH port")
@click.option("--user", "-u", default="root", help="SSH username")
@click.option("--password", default=None, help="SSH password")
@click.option("--key-file", default=None, type=click.Path(exists=True), help="SSH private key")
@click.option("--name", "-n", default=None, help="Target profile name (default: auto-generated)")
@click.option("--frontend", default="batocera", type=click.Choice(["batocera", "rocknix"]))
def connect(
    host_or_target: str,
    port: int,
    user: str,
    password: Optional[str],
    key_file: Optional[str],
    name: Optional[str],
    frontend: str,
) -> None:
    """Connect to a remote target and run a quick probe.

    HOST_OR_TARGET can be an IP/hostname or a target config name
    (from config/farmhand/targets/).

    Examples:
        romfarmer farmhand connect 10.10.20.183 --password linux
        romfarmer farmhand connect batocera-nuc
    """
    _check_paramiko()
    console = Console()

    from romfarmer.farmhand.ssh import SSHClient

    # Resolve target config or use direct args
    ssh_kwargs, target_name, resolved_frontend = _resolve_target(
        host_or_target, port=port, user=user, password=password,
        key_file=key_file, name=name, frontend=frontend,
    )

    if not ssh_kwargs.get("password") and not ssh_kwargs.get("key_file"):
        ssh_kwargs["password"] = click.prompt("SSH password", hide_input=True)

    with console.status(f"Connecting to {ssh_kwargs['user']}@{ssh_kwargs['host']}:{ssh_kwargs['port']}..."):
        client = SSHClient(**ssh_kwargs)
        try:
            client.connect()
        except Exception as exc:
            console.print(f"[red]Connection failed:[/red] {exc}")
            raise click.Abort()

        probe = client.run("hostname").strip()
        client.close()

    profile_name = target_name or f"{resolved_frontend}-{probe.lower()}"
    console.print(
        Panel(
            f"[green]Connected to {ssh_kwargs['host']}[/green]\n"
            f"Hostname: {probe}\n"
            f"Profile name: {profile_name}",
            title="Farm-Hand Connect",
        )
    )
    console.print(
        f"\nNext: [bold]romfarmer farmhand scan {host_or_target}[/bold]"
    )


# ── Scan ─────────────────────────────────────────────────────────────────────


@farmhand_group.command()
@click.argument("host_or_target")
@click.option("--port", "-p", default=22, type=int, help="SSH port")
@click.option("--user", "-u", default="root", help="SSH username")
@click.option("--password", default=None, help="SSH password")
@click.option("--key-file", default=None, type=click.Path(exists=True), help="SSH private key")
@click.option("--name", "-n", default=None, help="Target profile name")
@click.option("--frontend", default="batocera", type=click.Choice(["batocera", "rocknix"]))
@click.option("--save/--no-save", default=True, help="Save target profile to config/")
@click.option("--json-output", "output_json", is_flag=True, help="Output as JSON")
def scan(
    host_or_target: str,
    port: int,
    user: str,
    password: Optional[str],
    key_file: Optional[str],
    name: Optional[str],
    frontend: str,
    save: bool,
    output_json: bool,
) -> None:
    """Full scan of a remote target — volumes, ROMs, capabilities.

    HOST_OR_TARGET can be an IP/hostname or a target config name
    (from config/farmhand/targets/).

    Examples:
        romfarmer farmhand scan 10.10.20.183 --password linux
        romfarmer farmhand scan batocera-nuc
    """
    _check_paramiko()
    console = Console()

    from romfarmer.farmhand.analyzer import TargetAnalyzer
    from romfarmer.farmhand.config import save_profile
    from romfarmer.farmhand.ssh import SSHClient

    # Resolve target config or use direct args
    ssh_kwargs, target_name, resolved_frontend = _resolve_target(
        host_or_target, port=port, user=user, password=password,
        key_file=key_file, name=name, frontend=frontend,
    )

    if not ssh_kwargs.get("password") and not ssh_kwargs.get("key_file"):
        ssh_kwargs["password"] = click.prompt("SSH password", hide_input=True)

    client = SSHClient(**ssh_kwargs)
    final_name = target_name or f"{resolved_frontend}-{ssh_kwargs['host'].replace('.', '-')}"

    with console.status(f"Scanning {ssh_kwargs['host']}..."):
        client.connect()
        analyzer = TargetAnalyzer(client)
        profile = analyzer.full_scan(
            name=final_name, frontend=resolved_frontend,
        )
        client.close()

    if output_json:
        click.echo(profile.model_dump_json(indent=2))
        return

    # Display results
    _display_scan_results(console, profile)

    # Save profile
    if save:
        from romfarmer.core.paths import get_paths

        profile_path = save_profile(get_paths().workspace_root, profile)
        console.print(f"\n[dim]Profile saved to {profile_path}[/dim]")


def _display_scan_results(console: Console, profile: "TargetProfile") -> None:
    """Display scan results in a nice Rich table."""
    from romfarmer.farmhand.models import TargetProfile  # noqa: F811

    # System info
    si = profile.system_info
    if si:
        console.print(
            Panel(
                f"Hostname: {si.hostname}\n"
                f"OS: {si.os_name} {si.os_version}\n"
                f"Arch: {si.architecture}\n"
                f"CPU: {si.cpu_model} ({si.cpu_cores}c/{si.cpu_threads}t)\n"
                f"RAM: {si.memory_available_mb}/{si.memory_total_mb} MB",
                title=f"System: {profile.name}",
            )
        )

    # Volumes
    vol_table = Table(title="Storage Volumes", show_header=True, header_style="bold cyan")
    vol_table.add_column("Mount", style="green")
    vol_table.add_column("Device")
    vol_table.add_column("FS")
    vol_table.add_column("Total", justify="right")
    vol_table.add_column("Available", justify="right")
    vol_table.add_column("Use%", justify="right")
    vol_table.add_column("Role", style="yellow")
    vol_table.add_column("ROM Path")

    for vol in profile.volumes:
        vol_table.add_row(
            vol.mount_point,
            vol.device,
            vol.filesystem,
            f"{vol.total_gb:.1f} GB",
            f"{vol.available_gb:.1f} GB",
            f"{vol.use_percent:.0f}%",
            vol.role.value,
            vol.rom_path or "-",
        )
    console.print(vol_table)

    # Existing ROMs summary
    if profile.existing_roms:
        rom_table = Table(
            title="Existing ROMs on Target",
            show_header=True,
            header_style="bold cyan",
        )
        rom_table.add_column("Platform", style="green")
        rom_table.add_column("Files", justify="right")

        for platform, files in sorted(
            profile.existing_roms.items(), key=lambda x: -len(x[1])
        ):
            rom_table.add_row(platform, str(len(files)))
        console.print(rom_table)

    # Capabilities
    caps = profile.capabilities
    if caps:
        console.print(f"\n[bold]Binaries:[/bold] {', '.join(sorted(caps.binaries))}")
        console.print(
            f"[bold]7z support:[/bold] {'Yes' if caps.has_7z else 'No'} | "
            f"[bold]chdman:[/bold] {'Yes' if caps.has_chdman else 'No'}"
        )

    # Summary
    total_gb = profile.total_available_gb()
    console.print(
        f"\n[bold green]Total ROM storage available: {total_gb:.1f} GB[/bold green]"
    )


# ── Plan ─────────────────────────────────────────────────────────────────────


@farmhand_group.command()
@click.option("--target", "-t", required=True, help="Target profile name")
@click.option("--reserve", default=30.0, type=float, help="GB to reserve for saves/BIOS/etc")
@click.option("--exclude", default=None, help="Comma-separated platforms to exclude")
@click.option("--budget", default=None, multiple=True, help="Budget override: platform=GB (e.g., ps2=80)")
@click.option("--json-output", "output_json", is_flag=True, help="Output as JSON")
def plan(
    target: str,
    reserve: float,
    exclude: Optional[str],
    budget: tuple[str, ...],
    output_json: bool,
) -> None:
    """Generate a deployment plan for a target.

    Analyzes available space and proposes optimal platform allocation.

    Example:
        romfarmer farmhand plan --target batocera-nuc --reserve 30 --exclude xbox360
        romfarmer farmhand plan --target batocera-nuc --budget ps2=80 --budget psx=60
    """
    console = Console()

    # Load target profile
    profile = _load_profile(target)
    if not profile:
        console.print(f"[red]Target profile '{target}' not found[/red]")
        console.print("Run: romfarmer farmhand scan <host> --name <target> first")
        raise click.Abort()

    exclude_platforms = [p.strip() for p in exclude.split(",")] if exclude else []
    budget_overrides = {}
    for b in budget:
        if "=" in b:
            k, v = b.split("=", 1)
            budget_overrides[k.strip()] = float(v.strip())

    from romfarmer.farmhand.planner import SpacePlanner

    planner = SpacePlanner()
    deployment_plan = planner.create_plan(
        target=profile,
        reserved_gb=reserve,
        exclude_platforms=exclude_platforms,
        budget_overrides=budget_overrides,
    )

    if output_json:
        click.echo(deployment_plan.model_dump_json(indent=2))
        return

    _display_plan(console, deployment_plan)


def _display_plan(console: Console, plan: "DeploymentPlan") -> None:
    """Display a deployment plan with Rich formatting."""
    from romfarmer.farmhand.models import SelectionAction

    console.print(
        Panel(
            plan.summary(),
            title="Deployment Plan",
            border_style="green",
        )
    )

    # Allocation table
    table = Table(
        title="Platform Allocations",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Platform", style="green")
    table.add_column("Tier")
    table.add_column("Action", style="yellow")
    table.add_column("Full Size", justify="right")
    table.add_column("Allocated", justify="right")
    table.add_column("Volume")
    table.add_column("Strategy")

    for alloc in sorted(plan.allocations, key=lambda a: a.allocated_bytes, reverse=True):
        action_style = {
            SelectionAction.INCLUDE_ALL: "green",
            SelectionAction.BUDGET_SELECT: "yellow",
            SelectionAction.SKIP: "red",
            SelectionAction.CURATED_LIST: "cyan",
        }.get(alloc.action, "white")

        table.add_row(
            alloc.platform,
            alloc.tier.value,
            f"[{action_style}]{alloc.action.value}[/{action_style}]",
            f"{alloc.full_set_gb:.1f} GB" if alloc.full_set_bytes > 0 else "-",
            f"{alloc.allocated_gb:.1f} GB" if alloc.allocated_bytes > 0 else "-",
            alloc.target_volume or "-",
            alloc.selection_strategy or "-",
        )

    console.print(table)

    # Volume summary
    if plan.volume_allocations:
        vol_table = Table(title="Volume Usage", show_header=True, header_style="bold cyan")
        vol_table.add_column("Volume", style="green")
        vol_table.add_column("Allocated", justify="right")
        for mount, allocated in plan.volume_allocations.items():
            vol_table.add_row(mount, f"{allocated / 1024**3:.1f} GB")
        console.print(vol_table)

    # Notes
    if plan.notes:
        console.print("\n[bold]Notes:[/bold]")
        for note in plan.notes:
            console.print(f"  {note}")

    if plan.builds_needed:
        console.print(f"\n[bold yellow]Builds needed:[/bold yellow] {len(plan.builds_needed)}")
        for b in plan.builds_needed:
            console.print(f"  • {b}")


# ── Deploy ───────────────────────────────────────────────────────────────────


@farmhand_group.command()
@click.option("--target", "-t", required=True, help="Target profile name")
@click.option("--build", "-b", default=None, help="Build name (output dir under output/)")
@click.option("--dry-run", is_flag=True, help="Show what would be transferred without doing it")
@click.option("--no-delta", is_flag=True, help="Disable delta sync (transfer everything)")
@click.option("--restart-es", is_flag=True, help="Restart EmulationStation after deploy")
def deploy(
    target: str,
    build: Optional[str],
    dry_run: bool,
    no_delta: bool,
    restart_es: bool,
) -> None:
    """Deploy ROMs to a remote target according to the deployment plan.

    Example:
        romfarmer farmhand deploy --target batocera-nuc --build nointro-1g1r-eng-7z-batocera-v2 --dry-run
    """
    _check_paramiko()
    console = Console()

    profile = _load_profile(target)
    if not profile:
        console.print(f"[red]Target profile '{target}' not found[/red]")
        raise click.Abort()

    if not build:
        console.print("[red]--build is required (name of build output directory)[/red]")
        raise click.Abort()

    from romfarmer.core.paths import get_paths
    from romfarmer.farmhand.deployer import Deployer
    from romfarmer.farmhand.planner import SpacePlanner
    from romfarmer.farmhand.ssh import SSHClient

    output_root = get_paths().workspace_root / "output" / build
    if not output_root.exists():
        console.print(f"[red]Build output not found: {output_root}[/red]")
        raise click.Abort()

    # Create a basic plan from size data
    planner = SpacePlanner()
    plan = planner.create_plan(target=profile)

    # Connect and deploy
    password = click.prompt(f"SSH password for {profile.user}@{profile.host}", hide_input=True)
    client = SSHClient(
        profile.host, port=profile.port, user=profile.user, password=password
    )
    client.connect()

    def on_event(event: str, data: dict) -> None:
        if event == "platform_done":
            console.print(
                f"  [green]✓[/green] {data['platform']}: "
                f"{data['files']} files, {data['bytes'] / 1024**3:.1f} GB"
            )
        elif event == "file_done" and data.get("progress", 0) % 10 < 1:
            console.print(f"    {data['file']} ({data['progress']:.0f}%)", style="dim")

    deployer = Deployer(ssh=client, output_root=output_root, on_event=on_event)

    try:
        if dry_run:
            console.print("[yellow]DRY RUN — no files will be transferred[/yellow]\n")

        result = deployer.deploy(plan, dry_run=dry_run, delta_sync=not no_delta)

        console.print(
            Panel(
                "\n".join(result.notes[-3:]),
                title=f"Deployment {result.status.value}",
                border_style="green" if result.status.value == "completed" else "red",
            )
        )

        if restart_es and not dry_run:
            with console.status("Restarting EmulationStation..."):
                deployer.restart_emulationstation()
            console.print("[green]EmulationStation restarted[/green]")
    finally:
        client.close()


# ── Status ───────────────────────────────────────────────────────────────────


@farmhand_group.command()
@click.option("--target", "-t", required=True, help="Target profile name")
def status(target: str) -> None:
    """Show current state of a target — what's deployed and available space."""
    console = Console()
    profile = _load_profile(target)
    if not profile:
        console.print(f"[red]Target profile '{target}' not found[/red]")
        raise click.Abort()

    _display_scan_results(console, profile)


# ── Estimate ─────────────────────────────────────────────────────────────────


@farmhand_group.command()
@click.argument("available_gb", type=float)
def estimate(available_gb: float) -> None:
    """Quick estimate: what platforms fit in N gigabytes?

    Example:
        romfarmer farmhand estimate 1100
    """
    console = Console()

    from romfarmer.farmhand.planner import SpacePlanner

    planner = SpacePlanner()
    result = planner.estimate_platforms_count(available_gb)

    console.print(
        Panel(
            f"Available: {result['available_gb']} GB\n"
            f"Guaranteed (tiny+small+medium): {result['guaranteed_gb']} GB, "
            f"{result['guaranteed_platforms']} platforms\n"
            f"Need budget: {result['budget_platforms']} platforms\n"
            f"Skip: {result['skip_platforms']} platforms",
            title="Space Estimate",
        )
    )

    if result["include_all"]:
        table = Table(title="Include All", show_header=True, header_style="bold green")
        table.add_column("Platform")
        table.add_column("Size", justify="right")
        table.add_column("Files", justify="right")
        table.add_column("Tier")
        for p in result["include_all"]:
            table.add_row(p["platform"], f"{p['size_gb']} GB", str(p["files"]), p["tier"])
        console.print(table)

    if result["budget_needed"]:
        table = Table(title="Budget Needed", show_header=True, header_style="bold yellow")
        table.add_column("Platform")
        table.add_column("Full Size", justify="right")
        table.add_column("Suggested Budget", justify="right")
        table.add_column("Tier")
        for p in result["budget_needed"]:
            table.add_row(
                p["platform"],
                f"{p['full_size_gb']} GB",
                f"{p['suggested_budget_gb']} GB",
                p["tier"],
            )
        console.print(table)

    if result["skip"]:
        table = Table(title="Skip (No Budget)", show_header=True, header_style="bold red")
        table.add_column("Platform")
        table.add_column("Full Size", justify="right")
        for p in result["skip"]:
            table.add_row(p["platform"], f"{p['full_size_gb']} GB")
        console.print(table)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _resolve_target(
    host_or_target: str,
    *,
    port: int = 22,
    user: str = "root",
    password: Optional[str] = None,
    key_file: Optional[str] = None,
    name: Optional[str] = None,
    frontend: str = "batocera",
) -> tuple[dict, Optional[str], str]:
    """Resolve a host-or-target-name into SSH kwargs + target name + frontend.

    If host_or_target looks like an IP/hostname, use CLI args directly.
    Otherwise, try to load it as a target config name.

    Returns:
        (ssh_kwargs, target_name, frontend)
    """
    from romfarmer.core.paths import get_paths
    from romfarmer.farmhand.config import (
        list_targets,
        load_target_config,
        target_config_to_ssh_kwargs,
    )

    workspace = get_paths().workspace_root

    # Check if it's a target config name first
    available = list_targets(workspace)
    if host_or_target in available:
        config = load_target_config(workspace, host_or_target)
        ssh_kwargs = target_config_to_ssh_kwargs(config)
        target_name = name or config.get("name", host_or_target)
        resolved_frontend = config.get("frontend", frontend)
        return ssh_kwargs, target_name, resolved_frontend

    # It's a direct host — use CLI args
    ssh_kwargs = {
        "host": host_or_target,
        "port": port,
        "user": user,
    }
    if password:
        ssh_kwargs["password"] = password
    if key_file:
        ssh_kwargs["key_file"] = key_file
    return ssh_kwargs, name, frontend


def _load_profile(name: str) -> Optional["TargetProfile"]:
    """Load a saved target profile by name."""
    from romfarmer.core.paths import get_paths
    from romfarmer.farmhand.config import load_profile

    return load_profile(get_paths().workspace_root, name)
