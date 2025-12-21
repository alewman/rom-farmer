#!/usr/bin/env python3
"""ROM Farmer - Beautiful Status Display

Run this in a terminal at least 90 characters wide for best results.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()

def main():
    print()
    console.print("[bold green]╔══════════════════════════════════════════════════════════════════════════════╗[/]")
    console.print("[bold green]║[/]                                                                            [bold green]║[/]")
    console.print("[bold green]║[/]    [bold white]██████╗  ██████╗ ███╗   ███╗    ███████╗ █████╗ ██████╗ ███╗   ███╗[/]       [bold green]║[/]")
    console.print("[bold green]║[/]    [bold white]██╔══██╗██╔═══██╗████╗ ████║    ██╔════╝██╔══██╗██╔══██╗████╗ ████║[/]       [bold green]║[/]")
    console.print("[bold green]║[/]    [bold white]██████╔╝██║   ██║██╔████╔██║    █████╗  ███████║██████╔╝██╔████╔██║[/]       [bold green]║[/]")
    console.print("[bold green]║[/]    [bold white]██╔══██╗██║   ██║██║╚██╔╝██║    ██╔══╝  ██╔══██║██╔══██╗██║╚██╔╝██║[/]       [bold green]║[/]")
    console.print("[bold green]║[/]    [bold white]██║  ██║╚██████╔╝██║ ╚═╝ ██║    ██║     ██║  ██║██║  ██║██║ ╚═╝ ██║[/]       [bold green]║[/]")
    console.print("[bold green]║[/]    [bold white]╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝    ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝[/]       [bold green]║[/]")
    console.print("[bold green]║[/]                                                                            [bold green]║[/]")
    console.print("[bold green]║[/]    [dim]v1.0.0[/]  [bold cyan]Enterprise ROM Collection Management[/]                           [bold green]║[/]")
    console.print("[bold green]║[/]    [dim]Hash Transformation Tracking · Multi-Source Merging · Budget Builds[/]    [bold green]║[/]")
    console.print("[bold green]║[/]                                                                            [bold green]║[/]")
    console.print("[bold green]╚══════════════════════════════════════════════════════════════════════════════╝[/]")
    print()
    
    # Capabilities
    console.print("[bold cyan]━━━ System Capabilities ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]")
    print()
    console.print("  [bold green]✓[/] [bold]Hash Transformation Database[/]     Tracks source→final hashes for metadata lookup")
    console.print("  [bold green]✓[/] [bold]Sony PSN API Integration[/]         Live game updates from PlayStation Network")
    console.print("  [bold green]✓[/] [bold]Multi-Source Merging[/]             Combines Main + Aftermarket + Private folders")
    console.print("  [bold green]✓[/] [bold]Rating-Based Selection[/]           ScreenScraper ratings for curated builds")
    console.print("  [bold green]✓[/] [bold]Storage Budget Tracking[/]          Fits best games into target storage size")
    console.print("  [bold green]✓[/] [bold]Resume Capability[/]                Interrupts and continues large builds")
    print()
    
    # Statistics
    console.print("[bold cyan]━━━ Codebase Statistics ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]")
    print()
    console.print("  [dim]Python Lines of Code:[/]  [bold white]27,584[/]")
    console.print("  [dim]Pipeline Stages:[/]       [bold white]20[/]")
    console.print("  [dim]Platform Configs:[/]      [bold white]21+[/]")
    console.print("  [dim]Supported Systems:[/]     [bold white]30+[/]")
    print()
    
    # Pipeline
    console.print("[bold cyan]━━━ Pipeline Architecture ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]")
    print()
    console.print("  [bold green]Source[/] ─→ [bold yellow]Filter[/] ─→ [bold cyan]Transform[/] ─→ [bold magenta]Compress[/] ─→ [bold blue]Organize[/] ─→ [bold white]Output[/]")
    console.print("                          [dim]│[/]")
    console.print("                          [dim]↓[/]")
    console.print("              [dim]┌─────────────────────────────────────┐[/]")
    console.print("              [dim]│ Hash recorded to transformation DB │[/]")
    console.print("              [dim]│ Original hash → ScreenScraper lookup│[/]")
    console.print("              [dim]└─────────────────────────────────────┘[/]")
    print()
    
    # Key Innovation
    console.print("[bold cyan]━━━ Key Innovation ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]")
    print()
    console.print("  [bold yellow]The Problem:[/]  When you compress a game (ISO → CHD), its fingerprint changes.")
    console.print("               Metadata services can no longer recognize it. [red]Metadata is lost.[/]")
    print()
    console.print("  [bold green]Our Solution:[/] ROM Farmer records every transformation in a database.")
    console.print("               CHD fingerprint → lookup → original ISO fingerprint → metadata!")
    console.print("               [green]Metadata is preserved through any format conversion.[/]")
    print()
    
    console.print("[dim]─────────────────────────────────────────────────────────────────────────────────────[/]")
    console.print("[dim]                     https://github.com/yourusername/rom-farmer[/]")
    print()


if __name__ == "__main__":
    main()
