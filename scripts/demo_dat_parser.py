#!/usr/bin/env python3
"""Demo: Parse Retool DAT and show statistics."""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from romfarmer.dat_parser import RetoolDATParser

console = Console()


def main():
    """Parse NES Retool DAT and show statistics."""
    console.print(Panel.fit(
        "[bold white]DAT Parser Demo - Phase 2[/bold white]\n"
        "Parse Retool DAT and display statistics",
        border_style="blue"
    ))

    # Find NES Retool DAT
    dat_dir = Path("/path/to/dats/nointro/")
    dat_files = list(dat_dir.glob("Nintendo - Nintendo Entertainment System*.dat"))

    if not dat_files:
        console.print("[red]NES Retool DAT not found![/red]")
        return

    dat_file = dat_files[0]
    console.print(f"\n[cyan]Parsing:[/cyan] {dat_file.name}\n")

    # Parse DAT
    parser = RetoolDATParser()
    dat = parser.parse(dat_file)

    # Display header info
    table = Table(title="DAT Header Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Name", dat.name)
    table.add_row("Type", dat.dat_type.value)
    table.add_row("Version", dat.version or "N/A")
    table.add_row("Author", dat.author[:80] + "..." if dat.author and len(dat.author) > 80 else dat.author or "N/A")

    console.print(table)

    # Display statistics
    stats = dat.get_statistics()

    table2 = Table(title="ROM Statistics")
    table2.add_column("Metric", style="cyan")
    table2.add_column("Value", style="green")

    table2.add_row("Games", f"{stats['games']:,}")
    table2.add_row("ROMs", f"{stats['roms']:,}")
    table2.add_row("Multi-disc Games", f"{stats['multi_disc_games']:,}")
    table2.add_row("Total Size", f"{stats['total_size_gb']:.2f} GB")

    console.print(table2)

    # Show sample games
    console.print("\n[bold cyan]Sample Games (First 10):[/bold cyan]\n")

    tree = Tree("[bold]Games[/bold]")
    for game in dat.games[:10]:
        rom = game.get_primary_rom()
        if rom:
            size_mb = rom.size / (1024 * 1024)
            game_info = f"{game.name} ({size_mb:.1f} MB)"
            if game.category:
                game_info += f" [{game.category}]"
            node = tree.add(game_info)
            node.add(f"ROM: {rom.name}")
            if rom.crc:
                node.add(f"CRC: {rom.crc}")

    console.print(tree)

    # Show categories distribution
    console.print("\n[bold cyan]Retool Categories:[/bold cyan]\n")
    categories = {}
    for game in dat.games:
        cat = game.category or "Unknown"
        categories[cat] = categories.get(cat, 0) + 1

    table3 = Table(title="Category Distribution")
    table3.add_column("Category", style="cyan")
    table3.add_column("Count", style="green", justify="right")

    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        table3.add_row(cat, f"{count:,}")

    console.print(table3)

    # Success summary
    console.print(Panel.fit(
        "[bold green]✓ DAT Parsed Successfully![/bold green]\n\n"
        f"Parsed {stats['games']:,} games from Retool DAT\n"
        f"Total collection size: {stats['total_size_gb']:.2f} GB\n"
        f"Ready for ROM matching!",
        border_style="green"
    ))


if __name__ == "__main__":
    main()
