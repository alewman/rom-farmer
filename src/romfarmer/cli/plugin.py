"""CLI stub for the plugin system.

The legacy plugin system (StageContext-based) was removed in Phase 5.
"""

import click
from rich.console import Console

console = Console()


@click.group(name="plugin")
def plugin_group() -> None:
    """Plugin management (deprecated)."""


@plugin_group.command("list")
def plugin_list() -> None:
    """List registered plugins."""
    console.print("[yellow]Legacy plugin system removed in Phase 5.[/yellow]")


@plugin_group.command("info")
@click.argument("plugin_name")
def plugin_info(plugin_name: str) -> None:
    """Show plugin info."""
    console.print(f"[yellow]Plugin {plugin_name!r}: legacy system removed.[/yellow]")
