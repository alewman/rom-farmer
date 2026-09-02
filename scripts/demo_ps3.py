#!/usr/bin/env python3
"""Demo script for PS3 transformation.

Tests the complete PS3 pipeline:
1. Load PS3 config
2. Find Redump DAT
3. Apply pre-filters (letter, region, language)
4. Filter by DAT
5. Transform to multiple targets (rpcs3, ps3netsrv, batocera)
6. Apply updates and DLC
7. Organize outputs

Usage:
    python3 scripts/demo_ps3.py
    python3 scripts/demo_ps3.py --letter A --region USA
    python3 scripts/demo_ps3.py --letter B --language En
"""

import argparse
from pathlib import Path

from romfarmer.stages import (
    ApplyListsStage,
    ApplyPS3UpdatesStage,
    FilterDATStage,
    OrganizeStage,
    Pipeline,
    PreFilterStage,
    TransformPS3Stage,
)

from romfarmer.config import load_platform_config
from romfarmer.dat_parser import DATParser


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="PS3 ROM Farmer Pipeline Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all games
  python3 scripts/demo_ps3.py

  # Process only A games, USA region
  python3 scripts/demo_ps3.py --letter A --region USA

  # Process B games, English language
  python3 scripts/demo_ps3.py --letter B --language En

  # Process specific target
  python3 scripts/demo_ps3.py --target batocera --letter A --region USA
        """,
    )

    parser.add_argument(
        "--letter", type=str, help="Filter by first letter of filename (e.g., A, B, C)"
    )

    parser.add_argument(
        "--region",
        type=str,
        action="append",
        help="Filter by region tag (e.g., USA, EUR, JPN). Can be specified multiple times.",
    )

    parser.add_argument(
        "--language",
        type=str,
        action="append",
        help="Filter by language tag (e.g., En, Fr, De). Can be specified multiple times.",
    )

    parser.add_argument(
        "--target", type=str, help="Process only specific target (batocera, rpcs3, ps3netsrv)"
    )

    parser.add_argument(
        "--dat",
        type=str,
        default="retool_1g1r_usa",
        help="DAT configuration to use (default: retool_1g1r_usa)",
    )

    return parser.parse_args()


def main():
    """Run PS3 transformation demo."""
    args = parse_args()

    print("=" * 70)
    print("PS3 Transformation Demo")
    if args.letter or args.region or args.language:
        print(
            f"  Filters: Letter={args.letter or 'all'}, "
            f"Region={args.region or 'all'}, "
            f"Language={args.language or 'all'}"
        )
    print("=" * 70)
    print()

    # 1. Load PS3 config
    print("Step 1: Loading PS3 configuration...")

    config = load_platform_config("ps3")
    print(f"  Platform: {config.platform}")
    print(f"  System type: {config.system_type}")
    print(f"  Source: {config.sources[0].path}")
    print(f"  Targets: {len(config.targets)}")
    for target in config.targets:
        print(f"    - {target.name}: {target.format}", end="")
        if hasattr(target, "compression") and target.compression:
            print(f" ({target.compression})")
        else:
            print()
    print()

    # 2. Find Redump DAT
    print("Step 2: Loading Redump DAT...")
    dat_config = config.dats[args.dat]
    dat_path = Path(dat_config.base_path) / dat_config.dat_dir / dat_config.dat_filename

    if not dat_path.exists():
        print(f"ERROR: DAT not found: {dat_path}")
        return 1

    parser = DATParser()
    dat_file = parser.parse(dat_path)
    print(f"  DAT: {dat_file.name}")
    print(f"  Version: {dat_file.version}")
    print(f"  Games: {len(dat_file.games):,}")
    print()

    # 3. Setup directories
    print("Step 3: Setting up directories...")

    source_dir = Path(config.sources[0].path)

    if not source_dir.exists():
        print(f"ERROR: Source not found: {source_dir}")
        print("  This is expected if running outside of the actual environment")
        print("  In production, this would process real PS3 ISOs")
        return 0

    # Use /data/emu/output/ps3 for final builds
    base_output = Path("/data/emu/output/ps3")
    work_dir = Path("/data/emu/temp/ps3-work")

    print(f"  Source: {source_dir}")
    print(f"  Base output: {base_output}")
    print(f"  Work dir: {work_dir}")
    print()

    # 4. Determine which targets to process
    print("Step 4: Setting up targets...")
    targets_to_process = config.targets
    if args.target:
        targets_to_process = [t for t in config.targets if t.name == args.target]
        if not targets_to_process:
            print(f"ERROR: Target '{args.target}' not found")
            print(f"Available targets: {[t.name for t in config.targets]}")
            return 1

    print(f"  Processing {len(targets_to_process)} target(s):")
    for target in targets_to_process:
        print(f"    - {target.name}: {target.format}")
    print()

    # 5. Run pipeline for each target
    print("=" * 70)
    print("Running PS3 Transformation Pipeline")
    print("=" * 70)
    print()

    for target in targets_to_process:
        print(f"\nTarget: {target.name} ({target.format})")
        print("-" * 70)

        # Build pipeline for this target
        pipeline = Pipeline(
            platform_config=config,
            target_name=target.name,
            letter_filter=args.letter,
            region_filter=args.region,
            language_filter=args.language,
        )

        # Add stages
        pipeline.add_stage(PreFilterStage())  # NEW: Early filtering
        pipeline.add_stage(FilterDATStage())  # DAT matching
        pipeline.add_stage(ApplyListsStage())  # Apply lists
        pipeline.add_stage(TransformPS3Stage())  # Decrypt/extract
        pipeline.add_stage(ApplyPS3UpdatesStage())  # Updates and DLC
        pipeline.add_stage(OrganizeStage())  # Final organization

        # Execute
        try:
            results = pipeline.execute(
                source_dir=source_dir,
                work_dir=work_dir,
                output_dir=base_output,  # Will be modified with descriptive name
                dat_file_path=dat_path,
                dat_name=args.dat,
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

        except Exception as e:
            print(f"ERROR in pipeline: {e}")
            import traceback

            traceback.print_exc()

    print()
    print("=" * 70)
    print("Demo Complete!")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    exit(main())
