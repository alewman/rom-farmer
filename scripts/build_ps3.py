#!/usr/bin/env python3
"""PS3 Build Pipeline - Production build tool for PS3 ROM collections.

Complete PS3 pipeline with filtering, transformation, updates, and DLC:
1. Load PS3 config
2. Find Redump DAT
3. Apply pre-filters (letter, region, language)
4. Filter by DAT
5. Transform to multiple targets (rpcs3, ps3netsrv, batocera)
6. Apply updates and DLC
7. Organize outputs

Usage:
    python3 scripts/build_ps3.py
    python3 scripts/build_ps3.py --letter A --region USA
    python3 scripts/build_ps3.py --letter B --language En --target batocera
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


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="PS3 ROM Collection Build Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all games
  python3 scripts/build_ps3.py

  # Process only A games, USA region
  python3 scripts/build_ps3.py --letter A --region USA

  # Process B games, English language, Batocera target only
  python3 scripts/build_ps3.py --letter B --language En --target batocera

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
    print(f"  Platform: {config.name}")
    print(f"  System type: {config.system_type}")
    print(f"  Source: {config.sources[0].path}")
    print(f"  Targets: {', '.join([t.name for t in config.targets])}")

    # Get update/DLC settings from config
    apply_updates = config.updates.enabled if config.updates else True
    apply_dlc = config.dlc.enabled if config.dlc else False
    dlc_mode = config.dlc.mode if config.dlc else "copy"
    nps_database = (
        str(config.updates.nps_database)
        if config.updates
        else "/data/emu/source/nopaystation/PS3_DLCS.tsv"
    )
    pkg_archive = (
        str(config.updates.pkg_archive)
        if config.updates
        else "/data/emu/source/nopaystation/downloads-ps3-dlc/packages"
    )
    use_sony_psn = config.updates.use_sony_psn if config.updates else True

    print(f"  Updates: {'enabled' if apply_updates else 'disabled'}")
    print(f"  DLC: {'enabled' if apply_dlc else 'disabled'}")
    if apply_dlc:
        print(f"  DLC mode: {dlc_mode}")
    print()

    # 2. DAT configuration
    print("Step 2: DAT Configuration...")
    print(f"  Source: {config.dat.source}")
    if config.dat.file:
        print(f"  File: {config.dat.file}")
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
        print(f"    - {target.name}")
    print()

    # 5. Run pipeline for each target
    print("=" * 70)
    print("Running PS3 Transformation Pipeline")
    print("=" * 70)
    print()

    for target in targets_to_process:
        print(f"\nTarget: {target.name}")
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
        pipeline.add_stage(
            ApplyPS3UpdatesStage(  # Updates and DLC
                nps_database=nps_database,
                pkg_archive=pkg_archive,
                apply_updates=apply_updates,
                apply_dlc=apply_dlc,
                dlc_mode=dlc_mode,
                use_sony_psn=use_sony_psn,
            )
        )
        pipeline.add_stage(OrganizeStage())  # Final organization

        # Execute
        try:
            results = pipeline.execute(
                source_dir=source_dir,
                work_dir=work_dir,
                output_dir=base_output,  # Will be modified with descriptive name
            )

            # Display results
            print(f"\nPipeline Results ({target.name}):")
            print("-" * 70)

            for i, result in enumerate(results, 1):
                # Skip StageContext objects, only process StageResult
                if not hasattr(result, "status"):
                    continue

                status_symbol = "✓" if result.status.value == "success" else "✗"
                print(f"{i}. [{status_symbol}] Stage {i}")

                if hasattr(result, "message"):
                    print(f"   {result.message}")

                if hasattr(result, "files_matched") and result.files_matched:
                    print(f"   Matched: {result.files_matched}")
                if hasattr(result, "files_processed") and result.files_processed:
                    print(f"   Processed: {result.files_processed}")
                if hasattr(result, "files_failed") and result.files_failed:
                    print(f"   Failed: {result.files_failed}")

        except Exception as e:
            print(f"ERROR in pipeline: {e}")
            import traceback

            traceback.print_exc()

    print()
    print("=" * 70)
    print("Build Complete!")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    exit(main())
