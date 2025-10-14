#!/usr/bin/env python3
"""Demo script for PS3 transformation.

Tests the complete PS3 pipeline:
1. Load PS3 config
2. Find Redump DAT
3. Select small test games
4. Transform to multiple targets (rpcs3, ps3netsrv)
5. Verify outputs

Target 1 (rpcs3): Folder format
Target 2 (ps3netsrv): .iso.gz format

Usage:
    python3 scripts/demo_ps3.py
"""

import shutil
import tempfile
from pathlib import Path

from romgroomer.config import load_platform_config
from romgroomer.dat_parser import DATParser
from romgroomer.stages import (
    FilterDATStage,
    ApplyListsStage,
    TransformPS3Stage,
    OrganizeStage,
    Pipeline,
)


def main():
    """Run PS3 transformation demo."""
    print("=" * 70)
    print("PS3 Transformation Demo")
    print("=" * 70)
    print()
    
    # 1. Load PS3 config
    print("Step 1: Loading PS3 configuration...")
    
    config = load_platform_config("ps3")
    print(f"  Platform: {config.full_name}")
    print(f"  System type: {config.system_type}")
    print(f"  Source: {config.sources[0].path}")
    print(f"  Targets: {len(config.targets)}")
    for target in config.targets:
        print(f"    - {target.name}: {target.format}", end="")
        if hasattr(target, 'compression') and target.compression:
            print(f" ({target.compression})")
        else:
            print()
    print()
    
    # 2. Find Redump DAT
    print("Step 2: Loading Redump DAT...")
    dat_config = config.dats["retool_1g1r_usa"]
    dat_path = (
        Path(dat_config.base_path)
        / dat_config.dat_dir
        / dat_config.dat_filename
    )
    
    if not dat_path.exists():
        print(f"ERROR: DAT not found: {dat_path}")
        return 1
    
    parser = DATParser()
    dat_file = parser.parse(dat_path)
    print(f"  DAT: {dat_file.name}")
    print(f"  Version: {dat_file.version}")
    print(f"  Games: {len(dat_file.games):,}")
    print()
    
    # 3. Select small test games (for faster demo)
    print("Step 3: Selecting test games...")
    
    # Look for smaller PS3 games (< 5 GB) in source directory
    source_dir = Path(config.sources[0].path)
    
    if not source_dir.exists():
        print(f"ERROR: Source not found: {source_dir}")
        print("  This is expected if running outside of the actual environment")
        print("  In production, this would process real PS3 ISOs")
        return 0
    
    # Find some sample games
    all_zips = list(source_dir.glob("*.zip"))
    
    # Try to find small games for demo
    # (In real usage, would process all matched games)
    test_games = [
        "3D Dot Game Heroes (USA).zip",
        "Flow (USA).zip", 
        "Flower (USA).zip",
    ]
    
    sample_files = []
    for game in test_games:
        game_path = source_dir / game
        if game_path.exists():
            sample_files.append(game_path)
            print(f"  Found: {game}")
    
    if not sample_files:
        print("  No test games found (expected in demo environment)")
        print(f"  Available games: {len(all_zips)}")
        if all_zips:
            print(f"  Sample: {all_zips[0].name}")
        return 0
    
    print(f"  Selected {len(sample_files)} test games")
    print()
    
    # 4. Create temporary directories for demo
    print("Step 4: Setting up demo directories...")
    with tempfile.TemporaryDirectory() as temp_root:
        temp_path = Path(temp_root)
        
        # Copy sample files to temp (DRY RUN - don't modify source)
        demo_source = temp_path / "source"
        demo_source.mkdir()
        
        for src_file in sample_files:
            shutil.copy2(src_file, demo_source / src_file.name)
        
        work_dir = temp_path / "work"
        work_dir.mkdir()
        
        # Create output directories for each target
        outputs = {}
        for target in config.targets:
            output_dir = temp_path / "output" / target.name
            output_dir.mkdir(parents=True)
            outputs[target.name] = output_dir
        
        print(f"  Demo source: {demo_source}")
        print(f"  Work dir: {work_dir}")
        for name, path in outputs.items():
            print(f"  Output ({name}): {path}")
        print()
        
        # 5. Run pipeline for each target
        print("=" * 70)
        print("Running PS3 Transformation Pipeline")
        print("=" * 70)
        print()
        
        for target in config.targets:
            print(f"\nTarget: {target.name} ({target.format})")
            print("-" * 70)
            
            # Build pipeline for this target
            pipeline = Pipeline(
                name=f"ps3_{target.name}",
                platform_config=config,
                target_name=target.name,
            )
            
            # Add stages
            pipeline.add_stage(FilterDATStage(dat_file))
            pipeline.add_stage(ApplyListsStage())
            pipeline.add_stage(TransformPS3Stage())
            pipeline.add_stage(OrganizeStage())
            
            # Execute
            try:
                results = pipeline.execute(
                    source_dir=demo_source,
                    work_dir=work_dir,
                    output_dir=outputs[target.name],
                    dat_file_path=dat_path,
                )
                
                # Display results
                print(f"\nPipeline Results ({target.name}):")
                print("-" * 70)
                
                for i, result in enumerate(results, 1):
                    status_symbol = "✓" if result.status.value == "success" else "✗"
                    print(f"{i}. [{status_symbol}] {result.stage_name}")
                    print(f"   {result.message}")
                    
                    if result.files_matched:
                        print(f"   Matched: {result.files_matched}")
                    if result.files_processed:
                        print(f"   Processed: {result.files_processed}")
                    if result.files_failed:
                        print(f"   Failed: {result.files_failed}")
                
                # Show output structure
                print(f"\nOutput Structure ({target.name}):")
                print("-" * 70)
                _print_tree(outputs[target.name], prefix="", max_depth=2)
                
            except Exception as e:
                print(f"ERROR in pipeline: {e}")
                import traceback
                traceback.print_exc()
    
    print()
    print("=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print()
    print("Summary:")
    print(f"  Targets tested: {len(config.targets)}")
    print("  ")
    print("  Format comparison:")
    print("    rpcs3: Folder structure (best RPCS3 compatibility)")
    print("    ps3netsrv: .iso.gz (50% space savings for network streaming)")
    print()
    print("Next steps:")
    print("  1. Verify PS3Dec is installed: /data/emu/bin/PS3Dec")
    print("  2. Verify disc keys directory exists")
    print("  3. Test with real PS3 game")
    print("  4. Validate .iso.gz works with ps3netsrv")
    print("  5. Validate folders work with RPCS3")
    print()
    
    return 0


def _print_tree(path: Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0):
    """Print directory tree structure."""
    if current_depth >= max_depth:
        return
    
    if not path.exists():
        print(f"{prefix}(empty)")
        return
    
    items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
    
    for i, item in enumerate(items[:10]):  # Limit to 10 items per level
        is_last = i == len(items) - 1
        current_prefix = "└── " if is_last else "├── "
        
        if item.is_file():
            size_mb = item.stat().st_size / (1024 * 1024)
            if size_mb < 1:
                size_str = f"{item.stat().st_size / 1024:.1f} KB"
            elif size_mb < 1024:
                size_str = f"{size_mb:.1f} MB"
            else:
                size_str = f"{size_mb / 1024:.2f} GB"
            
            print(f"{prefix}{current_prefix}{item.name} ({size_str})")
        else:
            print(f"{prefix}{current_prefix}{item.name}/")
            
            if current_depth < max_depth - 1:
                next_prefix = prefix + ("    " if is_last else "│   ")
                _print_tree(item, next_prefix, max_depth, current_depth + 1)
    
    if len(items) > 10:
        print(f"{prefix}... ({len(items) - 10} more items)")


if __name__ == "__main__":
    exit(main())
