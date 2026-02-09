"""CLI commands for plugin management and introspection.

Provides `romfarmer plugin list`, `romfarmer plugin info`, and
`romfarmer plugin contracts` commands for inspecting the plugin system.
"""

import click
from rich.console import Console
from rich.table import Table


@click.group()
def plugin_group() -> None:
    """Manage and inspect plugins."""
    pass


@plugin_group.command("list")
@click.option("--capability", "-c", help="Filter by capability (FILTER, EXTRACT, COMPRESS, etc.)")
@click.option("--all", "show_all", is_flag=True, help="Include disabled plugins")
def plugin_list(capability: str, show_all: bool) -> None:
    """List all registered plugins."""
    from romfarmer.plugins.catalog import STAGE_CONTRACTS, register_builtin_plugins
    from romfarmer.plugins.registry import PluginRegistry
    from romfarmer.plugins.protocol import PluginCapability

    console = Console()
    registry = PluginRegistry()
    register_builtin_plugins(registry)
    registry.discover()

    plugins = registry.list_plugins()

    # Filter by capability
    if capability:
        cap_upper = capability.upper()
        plugins = [p for p in plugins if p["capability"] == cap_upper]

    if not plugins:
        console.print("[yellow]No plugins found.[/yellow]")
        return

    table = Table(title="ROM Farmer Plugins", show_header=True)
    table.add_column("Name", style="cyan")
    table.add_column("Capability", style="green")
    table.add_column("Priority", justify="right")
    table.add_column("Source", style="dim")
    table.add_column("Enabled", justify="center")
    table.add_column("Version", style="dim")

    for p in sorted(plugins, key=lambda x: (x["capability"], x["priority"])):
        enabled = "✓" if p["enabled"] else "✗"
        enabled_style = "green" if p["enabled"] else "red"
        table.add_row(
            p["name"],
            p["capability"],
            str(p["priority"]),
            p["source"],
            f"[{enabled_style}]{enabled}[/{enabled_style}]",
            p["version"],
        )

    console.print(table)
    console.print(f"\n[dim]{len(plugins)} plugin(s) registered[/dim]")


@plugin_group.command("contracts")
@click.option("--name", "-n", help="Show contract for specific plugin")
def plugin_contracts(name: str) -> None:
    """Show I/O contracts (requires/provides) for plugins."""
    from romfarmer.plugins.catalog import STAGE_CONTRACTS

    console = Console()

    if name:
        contract = STAGE_CONTRACTS.get(name)
        if not contract:
            console.print(f"[red]Unknown plugin: {name}[/red]")
            console.print(f"[dim]Available: {', '.join(sorted(STAGE_CONTRACTS.keys()))}[/dim]")
            return

        console.print(f"\n[bold cyan]{name}[/bold cyan]")
        console.print(f"  [dim]{contract.get('description', '')}[/dim]")
        console.print(f"  Capability: [green]{contract['capability'].name}[/green]")
        console.print(f"  Priority:   {contract.get('priority', 50)}")

        requires = contract.get("requires", frozenset())
        provides = contract.get("provides", frozenset())
        platforms = contract.get("platforms", frozenset())

        if requires:
            console.print(f"  Requires:   {', '.join(sorted(requires))}")
        if provides:
            console.print(f"  Provides:   {', '.join(sorted(provides))}")
        if platforms:
            console.print(f"  Platforms:  {', '.join(sorted(platforms))}")
        return

    # Show all contracts as a table
    table = Table(title="Plugin I/O Contracts", show_header=True)
    table.add_column("Plugin", style="cyan")
    table.add_column("Capability", style="green")
    table.add_column("Requires", style="yellow")
    table.add_column("Provides", style="blue")
    table.add_column("Platforms", style="dim")

    for plugin_name in sorted(STAGE_CONTRACTS.keys()):
        contract = STAGE_CONTRACTS[plugin_name]
        requires = ", ".join(sorted(contract.get("requires", frozenset())))
        provides = ", ".join(sorted(contract.get("provides", frozenset())))
        platforms = ", ".join(sorted(contract.get("platforms", frozenset()))) or "all"

        table.add_row(
            plugin_name,
            contract["capability"].name,
            requires or "—",
            provides or "—",
            platforms,
        )

    console.print(table)


@plugin_group.command("graph")
def plugin_graph() -> None:
    """Show plugin dependency graph (data flow)."""
    from romfarmer.plugins.catalog import STAGE_CONTRACTS

    console = Console()

    # Build field → producer/consumer maps
    producers = {}  # field → plugin names that provide it
    consumers = {}  # field → plugin names that require it

    for name, contract in STAGE_CONTRACTS.items():
        for field in contract.get("provides", frozenset()):
            producers.setdefault(field, []).append(name)
        for field in contract.get("requires", frozenset()):
            consumers.setdefault(field, []).append(name)

    console.print("\n[bold]Plugin Data Flow Graph[/bold]\n")

    all_fields = sorted(set(producers.keys()) | set(consumers.keys()))
    for field in all_fields:
        prods = producers.get(field, [])
        cons = consumers.get(field, [])

        prod_str = ", ".join(sorted(prods)) if prods else "[dim]pipeline-init[/dim]"
        cons_str = ", ".join(sorted(cons)) if cons else "[dim]unused[/dim]"

        console.print(f"  [yellow]{field}[/yellow]")
        console.print(f"    ← produced by: [cyan]{prod_str}[/cyan]")
        console.print(f"    → consumed by: [green]{cons_str}[/green]")
        console.print()
