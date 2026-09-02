#!/usr/bin/env python3
"""Test loading real config files."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from romfarmer.config import ConfigLoader

console = Console()


def test_build_config():
    """Test loading rocknix-512gb build config."""
    console.print("\n[bold cyan]Loading Build Config: rocknix-512gb[/bold cyan]")

    loader = ConfigLoader()
    build = loader.load_build_config("rocknix-512gb")

    # Display build info
    table = Table(title="Build Configuration")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Name", build.name)
    table.add_row("Description", build.description or "N/A")
    table.add_row("Platforms", ", ".join(build.platforms))
    table.add_row("DAT Priority", ", ".join([s.value for s in build.global_dat_priority]))
    table.add_row("Workspace", str(build.workspace))
    table.add_row("DAT Directory", str(build.dat_directory))
    table.add_row("Checkpoints", "Enabled" if build.checkpoint_enabled else "Disabled")

    console.print(table)
    console.print("[green]✓[/green] Build config loaded successfully!\n")

    return build


def test_platform_config(platform_name: str):
    """Test loading platform config."""
    console.print(f"\n[bold cyan]Loading Platform Config: {platform_name}[/bold cyan]")

    loader = ConfigLoader()
    platform = loader.load_platform_config(platform_name)

    # Create tree structure
    tree = Tree(f"[bold]{platform.name}[/bold] - {platform.system_type.value}")

    # DAT info
    dat_node = tree.add("[cyan]DAT Configuration[/cyan]")
    dat_node.add(f"Source: {platform.dat.source.value}")
    if platform.dat.expected_count:
        dat_node.add(f"Expected Count: {platform.dat.expected_count:,} games")

    # Sources
    sources_node = tree.add("[cyan]Sources[/cyan]")
    for source in platform.sources:
        sources_node.add(f"{source.type}: {source.path}")

    # Lists
    if platform.lists:
        lists_node = tree.add("[cyan]List Files[/cyan]")
        lists_node.add(f"Directory: {platform.lists.directory}")

    # Processing
    processing_node = tree.add("[cyan]Processing[/cyan]")
    processing_node.add(f"Extract Archives: {platform.extract_archives}")
    processing_node.add(f"Multi-disc: {platform.multi_disc_handling}")

    # Compression
    if platform.compression:
        comp_node = tree.add("[cyan]Compression[/cyan]")
        comp_node.add(f"Format: {platform.compression.format.value}")
        if platform.compression.tool:
            comp_node.add(f"Tool: {platform.compression.tool}")

    # Targets
    targets_node = tree.add("[cyan]Targets[/cyan]")
    for target in platform.targets:
        status = "✓" if target.enabled else "✗"
        target_info = f"[{'green' if target.enabled else 'red'}]{status}[/] {target.name} ({target.organization.style.value})"
        target_node = targets_node.add(target_info)
        target_node.add(f"Output: {target.output_path}")
        target_node.add(f"Metadata: {target.metadata}")

    console.print(tree)
    console.print("[green]✓[/green] Platform config loaded successfully!\n")

    return platform


def main():
    """Run all config tests."""
    console.print(
        Panel.fit(
            "[bold white]ROM Farmer Configuration Test[/bold white]\n"
            "Testing YAML loading, validation, and path resolution",
            border_style="blue",
        )
    )

    try:
        # Test build config
        build = test_build_config()

        # Test platform configs
        nes = test_platform_config("nes")
        saturn = test_platform_config("saturn")
        psp = test_platform_config("psp")

        # Summary
        console.print(
            Panel.fit(
                "[bold green]✓ All Configuration Tests Passed![/bold green]\n\n"
                f"Build: {build.name}\n"
                f"Platforms: {len(build.platforms)}\n"
                f"NES Games: {nes.dat.expected_count:,}\n"
                f"Saturn Games: {saturn.dat.expected_count:,}\n"
                f"PSP Games: {psp.dat.expected_count:,}",
                border_style="green",
            )
        )

    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}")
        raise


if __name__ == "__main__":
    main()
