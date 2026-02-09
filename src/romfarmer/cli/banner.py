"""Beautiful banner display for ROM Farmer."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()

VERSION = "1.0.0"

BANNER = """
[bold green]██████╗  ██████╗ ███╗   ███╗    ███████╗ █████╗ ██████╗ ███╗   ███╗███████╗██████╗[/]
[bold green]██╔══██╗██╔═══██╗████╗ ████║    ██╔════╝██╔══██╗██╔══██╗████╗ ████║██╔════╝██╔══██╗[/]
[bold green]██████╔╝██║   ██║██╔████╔██║    █████╗  ███████║██████╔╝██╔████╔██║█████╗  ██████╔╝[/]
[bold green]██╔══██╗██║   ██║██║╚██╔╝██║    ██╔══╝  ██╔══██║██╔══██╗██║╚██╔╝██║██╔══╝  ██╔══██╗[/]
[bold green]██║  ██║╚██████╔╝██║ ╚═╝ ██║    ██║     ██║  ██║██║  ██║██║ ╚═╝ ██║███████╗██║  ██║[/]
[bold green]╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝    ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝[/]
"""

def show_banner():
    """Display the ROM Farmer banner with system info."""
    console.print(BANNER)
    console.print(f"[dim]v{VERSION}[/]  [bold cyan]Enterprise ROM Collection Management[/]")
    console.print()

def show_status():
    """Display ROM Farmer system status."""
    show_banner()
    
    # Create capabilities table
    table = Table(
        title="[bold]System Capabilities[/]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    
    table.add_column("Feature", style="green")
    table.add_column("Status", style="white")
    table.add_column("Description", style="dim")
    
    table.add_row(
        "🔗 Hash Transformation DB",
        "[bold green]✓ Active[/]",
        "Tracks source→final hashes for metadata persistence"
    )
    table.add_row(
        "📡 Sony PSN Integration",
        "[bold green]✓ Available[/]",
        "Live update queries from PlayStation Network"
    )
    table.add_row(
        "📦 Multi-Source Merging",
        "[bold green]✓ Active[/]",
        "Main + Aftermarket + Private folder support"
    )
    table.add_row(
        "⭐ Rating-Based Selection",
        "[bold green]✓ Available[/]",
        "ScreenScraper ratings for budget builds"
    )
    table.add_row(
        "💾 Storage Budget Tracking",
        "[bold green]✓ Active[/]",
        "Fit best games into target storage size"
    )
    table.add_row(
        "⏸️  Resume Capability",
        "[bold green]✓ Active[/]",
        "Interrupt and continue large builds"
    )
    
    console.print(table)
    console.print()
    
    # Stats
    stats_table = Table(
        title="[bold]Codebase Statistics[/]",
        box=box.ROUNDED,
        show_header=False,
    )
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="bold white", justify="right")
    
    stats_table.add_row("Total Python LOC", "27,584")
    stats_table.add_row("Pipeline Stages", "20")
    stats_table.add_row("Platform Configs", "21+")
    stats_table.add_row("Supported Systems", "30+")
    
    console.print(stats_table)
    console.print()
    
    # Pipeline overview
    pipeline_text = Text()
    pipeline_text.append("\n📋 Pipeline Architecture\n", style="bold cyan")
    pipeline_text.append("   Source → Filter → Transform → Compress → Organize → Metadata → Output\n", style="green")
    pipeline_text.append("     │                  │\n", style="dim")
    pipeline_text.append("     │                  └─ Hash recorded to transformation DB\n", style="dim")
    pipeline_text.append("     └─ DAT verification (No-Intro, Redump)\n", style="dim")
    
    console.print(Panel(pipeline_text, title="[bold]How It Works[/]", box=box.ROUNDED))


def show_platforms():
    """Display supported platforms."""
    show_banner()
    
    table = Table(
        title="[bold]Supported Platforms[/]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    
    table.add_column("Platform", style="green")
    table.add_column("Source", style="white")
    table.add_column("Transforms", style="yellow")
    table.add_column("Output Formats", style="cyan")
    
    # Nintendo
    table.add_row("Nintendo NES", "No-Intro", "—", "ZIP, 7z")
    table.add_row("Nintendo SNES", "No-Intro", "—", "ZIP, 7z")
    table.add_row("Nintendo 64", "No-Intro", "—", "ZIP, 7z")
    table.add_row("Nintendo DS", "No-Intro", "—", "ZIP, 7z")
    table.add_row("Game Boy / Color / Advance", "No-Intro", "—", "ZIP, 7z")
    table.add_row("Nintendo Wii", "Redump", "RVZ extract", "ISO, RVZ")
    table.add_row("Nintendo GameCube", "Redump", "RVZ extract", "ISO, RVZ")
    
    # Sony
    table.add_row("PlayStation", "Redump", "CHD compress", "CHD + M3U")
    table.add_row("PlayStation 2", "Redump", "CHD compress", "CHD + M3U")
    table.add_row("PlayStation 3", "Redump", "Decrypt + JB", "Folder, ISO.gz")
    table.add_row("PSP", "Redump", "CSO compress", "CSO, ISO")
    
    # Sega
    table.add_row("Sega Saturn", "Redump", "CHD compress", "CHD + M3U")
    table.add_row("Sega Dreamcast", "Redump", "CHD compress", "CHD")
    table.add_row("Mega Drive / Genesis", "No-Intro", "—", "ZIP, 7z")
    
    # Microsoft
    table.add_row("Xbox", "Redump", "XISO convert", "XISO, SquashFS")
    table.add_row("Xbox 360", "Redump", "XISO convert", "XISO")
    
    # Other
    table.add_row("+ 15 more systems...", "", "", "")
    
    console.print(table)


if __name__ == "__main__":
    show_status()
