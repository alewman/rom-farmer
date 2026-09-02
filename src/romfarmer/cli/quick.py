"""Quick build command - interactive wizard for creating and running builds."""

from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

console = Console()


def discover_platforms(config_root: Path = None) -> list[dict]:
    """Discover available platform configurations."""
    if config_root is None:
        config_root = Path("config")

    platforms_dir = config_root / "platforms"
    if not platforms_dir.exists():
        return []

    platforms = []
    for yaml_file in platforms_dir.glob("*.yaml"):
        try:
            with open(yaml_file) as f:
                config = yaml.safe_load(f)
                platforms.append(
                    {
                        "file": yaml_file.stem,
                        "name": config.get("name", yaml_file.stem),
                        "description": config.get("description", ""),
                        "dat_count": config.get("dat", {}).get("expected_count", "?"),
                        "enabled": config.get("enabled", True),
                    }
                )
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load {yaml_file.name}: {e}[/yellow]")

    return sorted(platforms, key=lambda x: x["name"])


def discover_selections(config_root: Path = None) -> list[dict]:
    """Discover available selection configurations."""
    if config_root is None:
        config_root = Path("config")

    selections_dir = config_root / "selections"
    if not selections_dir.exists():
        return []

    selections = []
    for yaml_file in selections_dir.glob("*.yaml"):
        try:
            with open(yaml_file) as f:
                config = yaml.safe_load(f)
                selections.append(
                    {
                        "file": yaml_file.stem,
                        "name": config.get("name", yaml_file.stem),
                        "description": config.get("description", ""),
                        "strategy": config.get("strategy", "unknown"),
                        "limit": config.get("limit", None),
                        "max_size_gb": config.get("max_size_gb", None),
                    }
                )
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load {yaml_file.name}: {e}[/yellow]")

    return sorted(selections, key=lambda x: x["name"])


def discover_builds(config_root: Path = None) -> list[dict]:
    """Discover existing build configurations."""
    if config_root is None:
        config_root = Path("config")

    builds_dir = config_root / "builds"
    if not builds_dir.exists():
        return []

    builds = []
    for yaml_file in builds_dir.glob("*.yaml"):
        if yaml_file.stem.startswith("."):  # Skip hidden files
            continue
        try:
            with open(yaml_file) as f:
                config = yaml.safe_load(f)
                builds.append(
                    {
                        "file": yaml_file.stem,
                        "name": config.get("name", yaml_file.stem),
                        "description": config.get("description", ""),
                        "platforms": config.get("platforms", []),
                    }
                )
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load {yaml_file.name}: {e}[/yellow]")

    return sorted(builds, key=lambda x: x["name"])


def display_platforms(platforms: list[dict]) -> None:
    """Display platforms in a nice table."""
    table = Table(title="Available Platforms", show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("Platform", style="green")
    table.add_column("Games", justify="right")
    table.add_column("Description")

    for i, platform in enumerate(platforms, 1):
        table.add_row(
            str(i), platform["name"], str(platform["dat_count"]), platform["description"] or "—"
        )

    console.print(table)


def display_selections(selections: list[dict]) -> None:
    """Display selections in a nice table."""
    table = Table(
        title="Available Selection Strategies", show_header=True, header_style="bold cyan"
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("Name", style="green")
    table.add_column("Strategy")
    table.add_column("Limit")
    table.add_column("Description")

    for i, sel in enumerate(selections, 1):
        limit_str = str(sel["limit"]) if sel["limit"] else "—"
        if sel["max_size_gb"]:
            limit_str += f" ({sel['max_size_gb']}GB)"

        table.add_row(str(i), sel["name"], sel["strategy"], limit_str, sel["description"] or "—")

    console.print(table)


def display_builds(builds: list[dict]) -> None:
    """Display existing builds in a nice table."""
    table = Table(title="Existing Build Configurations", show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("Build Name", style="green")
    table.add_column("Platforms")
    table.add_column("Description")

    for i, build in enumerate(builds, 1):
        platforms_str = ", ".join(build["platforms"][:3])
        if len(build["platforms"]) > 3:
            platforms_str += f" +{len(build['platforms']) - 3} more"

        table.add_row(str(i), build["name"], platforms_str, build["description"] or "—")

    console.print(table)


def select_from_list(items: list[dict], prompt: str, allow_none: bool = False) -> dict | None:
    """Interactive selection from a list."""
    if not items:
        console.print("[yellow]No options available.[/yellow]")
        return None

    none_option = " (or 0 for none)" if allow_none else ""
    choice = Prompt.ask(f"{prompt} (1-{len(items)}{none_option})", default="1")

    try:
        idx = int(choice)
        if allow_none and idx == 0:
            return None
        if 1 <= idx <= len(items):
            return items[idx - 1]
    except ValueError:
        pass

    console.print("[red]Invalid choice[/red]")
    return None


@click.command()
@click.option("--interactive", "-i", is_flag=True, help="Interactive mode")
@click.option("--platform", "-p", help="Platform name (skip interactive)")
@click.option("--selection", "-s", help="Selection name (skip interactive)")
@click.option("--config-root", type=click.Path(exists=True), help="Config root directory")
def quick(interactive: bool, platform: str, selection: str, config_root: str):
    """
    Quick build wizard - create and run builds interactively.

    Examples:

        # Interactive mode
        romfarmer quick --interactive

        # Direct command (skips prompts)
        romfarmer quick --platform saturn --selection usa-10
    """
    config_path = Path(config_root) if config_root else Path("config")

    # Banner
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]🎮 ROM Farmer Quick Build[/bold cyan]\n"
            "Interactive wizard for building ROM collections",
            border_style="cyan",
        )
    )
    console.print()

    # Discover available resources
    console.print("[cyan]Discovering available configurations...[/cyan]")
    platforms = discover_platforms(config_path)
    selections = discover_selections(config_path)
    builds = discover_builds(config_path)

    console.print(f"  ✓ Found {len(platforms)} platforms")
    console.print(f"  ✓ Found {len(selections)} selections")
    console.print(f"  ✓ Found {len(builds)} existing builds")
    console.print()

    if not platforms:
        console.print("[red]No platforms found! Check your config/platforms/ directory.[/red]")
        return

    # Step 1: Use existing build or create new?
    if builds and interactive:
        console.print("[bold]Step 1: Build Configuration[/bold]")
        console.print("Would you like to use an existing build or create a new one?")
        console.print("  1. Create new build (guided)")
        console.print("  2. Use existing build")
        console.print()

        choice = Prompt.ask("Choice", choices=["1", "2"], default="1")

        if choice == "2":
            display_builds(builds)
            build = select_from_list(builds, "Select build")
            if build:
                # Run existing build
                import subprocess

                cmd = f"python3 -m romfarmer build run {build['name']}"
                console.print()
                console.print(f"[cyan]Running:[/cyan] {cmd}")
                console.print()
                subprocess.run(cmd, shell=True)
                return

    # Step 2: Select platform
    console.print("[bold]Step 2: Select Platform[/bold]")
    display_platforms(platforms)

    if platform:
        selected_platform = next(
            (p for p in platforms if p["name"] == platform or p["file"] == platform), None
        )
        if not selected_platform:
            console.print(f"[red]Platform '{platform}' not found[/red]")
            return
    else:
        selected_platform = select_from_list(platforms, "Select platform")
        if not selected_platform:
            return

    console.print(f"[green]✓ Selected:[/green] {selected_platform['name']}")
    console.print()

    # Step 3: Select selection strategy
    console.print("[bold]Step 3: Select Strategy[/bold]")
    console.print("How many games do you want to process?")

    if selections:
        display_selections(selections)

        if selection:
            selected_selection = next(
                (s for s in selections if s["name"] == selection or s["file"] == selection), None
            )
        else:
            selected_selection = select_from_list(selections, "Select strategy", allow_none=True)
    else:
        selected_selection = None

    if selected_selection:
        console.print(f"[green]✓ Selected:[/green] {selected_selection['name']}")
    else:
        console.print("[green]✓ Selected:[/green] All games (no filtering)")
    console.print()

    # Step 4: Summary and confirmation
    console.print(
        Panel.fit(
            f"[bold]Build Summary[/bold]\n\n"
            f"Platform:  [cyan]{selected_platform['name']}[/cyan]\n"
            f"Selection: [cyan]{selected_selection['name'] if selected_selection else 'All games'}[/cyan]\n"
            f"Games:     [cyan]{selected_platform['dat_count']} available[/cyan]",
            title="Review",
            border_style="green",
        )
    )
    console.print()

    if not Confirm.ask("Proceed with build?", default=True):
        console.print("[yellow]Build cancelled[/yellow]")
        return

    # Step 5: Check if matching build exists
    platform_file = selected_platform["file"]

    # Look for existing build that uses this platform
    matching_build = None
    for build in builds:
        if platform_file in build["platforms"]:
            matching_build = build
            break

    if matching_build:
        console.print(f"[green]Found existing build:[/green] {matching_build['name']}")
        build_name = matching_build["name"]
    else:
        console.print("[yellow]No existing build found with this configuration.[/yellow]")
        console.print("[yellow]Please create a build config or use an existing one.[/yellow]")
        console.print()
        console.print(f"[cyan]Hint:[/cyan] Create config/builds/{platform_file}-test.yaml with:")
        console.print(f"  name: {platform_file}-test")
        console.print(f"  platforms: [{platform_file}]")
        return

    # Step 6: Run the build
    import subprocess

    cmd = f"python3 -m romfarmer build run {build_name}"

    console.print()
    console.print(Panel.fit(f"[cyan]{cmd}[/cyan]", title="Executing", border_style="cyan"))
    console.print()

    subprocess.run(cmd, shell=True)


@click.group(name="quick")
def quick_group():
    """Quick build commands."""
    pass


quick_group.add_command(quick, name="build")


if __name__ == "__main__":
    quick()
