#!/usr/bin/env python3
"""Demo: Wii RVZ extraction pipeline.

This demonstrates the simplest possible transformation:
Just unzip RVZ files from Myrient archives!

No conversion, no compression, no complexity - RVZ is
Dolphin's native format and works perfectly as-is.
"""

import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree

from romgroomer.config import load_platform_config
from romgroomer.dat_parser import DATParser
from romgroomer.stages import (
    ApplyListsStage,
    FilterDATStage,
    OrganizeStage,
    Pipeline,
    StageContext,
    UnzipRVZStage,
)


def main():
    """Run Wii RVZ extraction demo."""
    console = Console()
    
    console.print(Panel.fit(
        "[bold cyan]Wii RVZ Extraction Demo[/bold cyan]\n"
        "[dim]Extract RVZ files from Myrient archives[/dim]",
        border_style="cyan"
    ))
    
    # Load Wii config
    console.print("\n[bold]1. Loading Wii configuration...[/bold]")
    wii_config = load_platform_config("wii")
    console.print(f"  Platform: {wii_config.name}")
    console.print(f"  System type: {wii_config.system_type}")
    
    # Find Redump Retool DAT
    console.print("\n[bold]2. Loading Redump Retool DAT...[/bold]")
    
    # Build DAT path from config
    dat_base = Path("/data/emu/dats")
    dat_dir = dat_base / "redump.retool.1g1r.usa"
    
    if not dat_dir.exists():
        console.print(f"  [red]Error: DAT directory not found: {dat_dir}[/red]")
        return 1
    
    # Find Wii DAT file
    dat_files = list(dat_dir.glob("*Wii*.dat"))
    if not dat_files:
        console.print(f"  [red]Error: No Wii DAT file found in {dat_dir}[/red]")
        return 1
    
    dat_path = dat_files[0]
    parser = DATParser()
    dat_file = parser.parse(dat_path)
    console.print(f"  Found: {dat_file.name}")
    console.print(f"  Games: {len(dat_file.games)}")
    
    # Find source directory
    console.print("\n[bold]3. Finding Myrient Wii source...[/bold]")
    source_dir = Path(wii_config.sources[0].path)
    
    if not source_dir.exists():
        console.print(f"  [red]Error: Source directory not found: {source_dir}[/red]")
        return 1
    
    # Count available files
    all_zips = list(source_dir.glob("*.zip"))
    console.print(f"  Directory: {source_dir}")
    console.print(f"  Total ZIPs: {len(all_zips)}")
    
    # Select first 5 for demo
    demo_files = all_zips[:5]
    console.print(f"  [cyan]Demo: Using first {len(demo_files)} files[/cyan]")
    for f in demo_files:
        size_mb = f.stat().st_size / 1e6
        console.print(f"    - {f.name} ({size_mb:.1f} MB)")
    
    # Create temporary directories for DRY RUN
    console.print("\n[bold]4. Setting up temporary directories...[/bold]")
    with tempfile.TemporaryDirectory() as temp_base:
        temp_path = Path(temp_base)
        
        # Copy demo files to temp
        temp_source = temp_path / "source"
        temp_source.mkdir()
        
        for f in demo_files:
            import shutil
            dest = temp_source / f.name
            shutil.copy2(f, dest)
            console.print(f"  Copied: {f.name}")
        
        # Work and output directories
        work_dir = temp_path / "work"
        output_dir = temp_path / "output"
        work_dir.mkdir()
        output_dir.mkdir()
        
        console.print(f"  Source: {temp_source}")
        console.print(f"  Work: {work_dir}")
        console.print(f"  Output: {output_dir}")
        
        # Create and configure pipeline
        console.print("\n[bold]5. Configuring pipeline...[/bold]")
        pipeline = Pipeline(
            platform_config=wii_config,
            target_name=wii_config.targets[0].name,
            console=console,
        )
        
        # Add stages
        pipeline.add_stage(FilterDATStage())      # Match against DAT
        pipeline.add_stage(ApplyListsStage())     # Apply delete/keep lists
        pipeline.add_stage(UnzipRVZStage())       # Extract RVZ files ✅
        pipeline.add_stage(OrganizeStage())       # Organize by target style
        
        console.print("  Pipeline stages:")
        for i, stage in enumerate(pipeline.stages, 1):
            console.print(f"    {i}. {stage.name}")
        
        # Execute pipeline
        console.print("\n[bold cyan]6. Executing pipeline...[/bold cyan]\n")
        
        import time
        start_time = time.time()
        
        try:
            results = pipeline.execute(
                source_dir=temp_source,
                work_dir=work_dir,
                output_dir=output_dir,
                dat_file_path=dat_path,
            )
            duration = time.time() - start_time
            
            # Show results
            console.print(f"\n[bold green]✓ Pipeline completed in {duration:.1f}s[/bold green]")
            
            # Get context from results (last result has final context)
            final_context = results[-1] if results else None
            
            # Show extracted files
            if final_context and hasattr(final_context, 'extracted_files') and final_context.extracted_files:
                console.print(f"\n[bold]Extracted RVZ files ({len(final_context.extracted_files)}):[/bold]")
                
                total_size = 0
                for rvz_file in final_context.extracted_files:
                    if rvz_file.exists():
                        size_gb = rvz_file.stat().st_size / 1e9
                        total_size += rvz_file.stat().st_size
                        console.print(f"  ✓ {rvz_file.name} ({size_gb:.2f} GB)")
                
                total_gb = total_size / 1e9
                console.print(f"\n[bold]Total size:[/bold] {total_gb:.2f} GB")
            else:
                # Check work directory for extracted files
                extracted_files = list(work_dir.rglob("*.rvz"))
                if extracted_files:
                    console.print(f"\n[bold]Extracted RVZ files ({len(extracted_files)}):[/bold]")
                    total_size = 0
                    for rvz_file in extracted_files:
                        size_gb = rvz_file.stat().st_size / 1e9
                        total_size += rvz_file.stat().st_size
                        console.print(f"  ✓ {rvz_file.name} ({size_gb:.2f} GB)")
                    
                    total_gb = total_size / 1e9
                    console.print(f"\n[bold]Total size:[/bold] {total_gb:.2f} GB)")
            
            # Show output structure
            console.print("\n[bold]Output directory structure:[/bold]")
            tree = Tree(f"📁 {output_dir.name}/")
            
            def add_tree_contents(parent_tree, parent_path, max_depth=3, current_depth=0):
                if current_depth >= max_depth:
                    return
                
                try:
                    items = sorted(parent_path.iterdir())
                    for item in items:
                        if item.is_dir():
                            branch = parent_tree.add(f"📁 {item.name}/")
                            add_tree_contents(branch, item, max_depth, current_depth + 1)
                        else:
                            size_mb = item.stat().st_size / 1e6
                            parent_tree.add(f"📄 {item.name} ({size_mb:.1f} MB)")
                except PermissionError:
                    parent_tree.add("[dim]<permission denied>[/dim]")
            
            add_tree_contents(tree, output_dir)
            console.print(tree)
            
            # Summary
            console.print("\n[bold cyan]Summary:[/bold cyan]")
            console.print(f"  • Source ZIPs: 5")
            if results:
                console.print(f"  • Pipeline stages: {len(results)}")
            console.print(f"  • Processing time: {duration:.1f}s")
            
            console.print("\n[green]✓ Wii RVZ extraction successful![/green]")
            console.print("[dim]RVZ files are ready to use in Dolphin![/dim]")
            
        except Exception as e:
            console.print(f"\n[red]✗ Pipeline failed: {e}[/red]")
            import traceback
            console.print(traceback.format_exc())
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
