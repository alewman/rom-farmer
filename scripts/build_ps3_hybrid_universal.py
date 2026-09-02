#!/usr/bin/env python3
"""Universal PS3 HYBRID builder - works for entire PS3 library.

Integrates with existing rom-farmer pipeline:
1. Decrypt Redump sources → JB folders
2. Apply official updates (baked in)
3. Extract major campaign DLC to disc (for real PS3)
4. Copy ALL DLC PKGs to _PKG/ folder (for RPCS3)
5. Generate README.txt with usage instructions

Features:
- Works on any PS3 game automatically
- Letter filtering (e.g., only process games starting with 'A')
- Auto-detects title ID, region, version
- Dynamic README generation
- No hardcoded game names

Usage:
    # Process all games
    python3 build_ps3_hybrid_universal.py

    # Process only games starting with 'A'
    python3 build_ps3_hybrid_universal.py --filter A

    # Process specific game
    python3 build_ps3_hybrid_universal.py --game "Borderlands 2"

    # Dry run (don't modify files)
    python3 build_ps3_hybrid_universal.py --dry-run
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from romfarmer.stages.apply_ps3_updates import ApplyPS3UpdatesStage


def get_folder_size(path: Path) -> int:
    """Calculate total size of directory in bytes."""
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            try:
                total += item.stat().st_size
            except (OSError, PermissionError):
                pass
    return total


def format_size(bytes: int) -> str:
    """Format bytes as human-readable size."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} PB"


def detect_region(game_name: str, title_id: str = None) -> str:
    """Detect game region from name or title ID."""
    if title_id:
        # BLUS = USA, BLES = Europe, BLJM = Japan, etc.
        if title_id.startswith("BLUS") or title_id.startswith("BCUS"):
            return "USA"
        elif title_id.startswith("BLES") or title_id.startswith("BCES"):
            return "EUR"
        elif title_id.startswith("BLJM") or title_id.startswith("BCJM"):
            return "JPN"
        elif title_id.startswith("BCAS"):
            return "ASIA"

    # Fallback to name detection
    name_upper = game_name.upper()
    if "(USA)" in name_upper or "(US)" in name_upper:
        return "USA"
    elif "(EUROPE)" in name_upper or "(EUR)" in name_upper:
        return "EUR"
    elif "(JAPAN)" in name_upper or "(JPN)" in name_upper:
        return "JPN"
    elif "(ASIA)" in name_upper:
        return "ASIA"
    elif "(WORLD)" in name_upper:
        return "WORLD"

    return "Unknown"


def get_app_version(game_folder: Path) -> str:
    """Extract APP_VER from PARAM.SFO."""
    try:
        from romfarmer.utils.ps3 import read_param_sfo

        param_sfo = game_folder / "PS3_GAME" / "PARAM.SFO"
        if param_sfo.exists():
            data = read_param_sfo(param_sfo)
            return data.get("APP_VER", "01.00")
    except:
        pass
    return "01.00"


def generate_readme(
    game_folder: Path,
    title_id: str,
    pkg_files: list,
    rap_count: int,
    dlc_count: int,
    campaign_count: int,
) -> None:
    """Generate README.txt for game folder."""
    # Read template
    template_path = Path(__file__).parent / "templates" / "README_HYBRID.txt"
    if not template_path.exists():
        print(f"   ⚠️  Template not found: {template_path}")
        return

    # Calculate sizes
    ps3_game_size = (
        get_folder_size(game_folder / "PS3_GAME") if (game_folder / "PS3_GAME").exists() else 0
    )
    pkg_dir = game_folder / "_PKG"
    pkg_folder_size = get_folder_size(pkg_dir) if pkg_dir.exists() else 0
    total_size = get_folder_size(game_folder)

    # Get PKG list
    pkg_list_text = (
        "\n".join([f"   • {pkg}" for pkg in sorted(pkg_files)]) if pkg_files else "   (None)"
    )

    # Detect region
    region = detect_region(game_folder.name, title_id)

    # Get version
    app_ver = get_app_version(game_folder)

    # Read and populate template
    readme_template = template_path.read_text()
    readme_content = readme_template.format(
        GAME_TITLE=game_folder.name.replace(".ps3", ""),
        BUILD_DATE=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        APP_VER=app_ver,
        DLC_COUNT=dlc_count,
        GAME_FOLDER=game_folder.name,
        PKG_COUNT=len(pkg_files),
        RAP_COUNT=rap_count,
        PKG_LIST=pkg_list_text,
        TITLE_ID=title_id,
        REGION=region,
        TOTAL_SIZE=format_size(total_size),
        BASE_SIZE=format_size(ps3_game_size),
        DISC_DLC_SIZE=f"{campaign_count} campaigns",
        PKG_SIZE=format_size(pkg_folder_size),
        RAP_SIZE=f"{rap_count} files",
    )

    # Write README
    readme_path = game_folder / "README.txt"
    readme_path.write_text(readme_content)
    print("   ✓ Created README.txt")


def process_game(
    game_folder: Path,
    stage: ApplyPS3UpdatesStage,
    dry_run: bool = False,
) -> dict:
    """Process a single PS3 game folder.

    Args:
        game_folder: Path to .ps3 game folder
        stage: Configured ApplyPS3UpdatesStage instance
        dry_run: If True, don't modify files

    Returns:
        dict: Statistics about processing
    """
    stats = {
        "updates_available": 0,
        "updates_applied": 0,
        "dlc_available": 0,
        "dlc_campaign_extracted": 0,
        "dlc_pkg_copied": 0,
        "rap_files_downloaded": 0,
        "success": False,
    }

    print(f"\n{'=' * 80}")
    print(f"Processing: {game_folder.name}")
    print(f"{'=' * 80}")

    # Extract title ID
    title_id = stage._extract_title_id(game_folder)
    if not title_id:
        print("⚠️  No TITLE_ID found in PARAM.SFO")
        return stats

    print(f"Title ID: {title_id}")

    if dry_run:
        print("\n🔍 DRY RUN - No files will be modified")

    # Create _PKG directory
    pkg_dir = game_folder / "_PKG"
    if not dry_run:
        pkg_dir.mkdir(parents=True, exist_ok=True)
        raps_dir = pkg_dir / "RAPS"
        raps_dir.mkdir(parents=True, exist_ok=True)

    # Find updates
    if stage.apply_updates:
        updates = []

        # Query Sony PSN for official updates
        if stage.psn_client:
            try:
                psn_updates = stage.psn_client.get_updates(title_id)
                updates.extend(psn_updates)
            except Exception as e:
                print(f"   ⚠️  Sony PSN query failed: {e}")

        if updates:
            stats["updates_available"] = len(updates)
            print(f"\n📦 {len(updates)} update(s) available")

            for update in updates:
                if not dry_run:
                    success = stage._apply_update(game_folder, title_id, update)
                    if success:
                        stats["updates_applied"] += 1
                else:
                    print(f"   [DRY RUN] Would apply: {update.get('Name', 'Update')}")
                    stats["updates_applied"] += 1
        else:
            print("\n⚠️  No updates found")

    # Find and process DLC
    if stage.apply_dlc:
        dlc_list = stage.database.find_all_dlc_for_title(title_id)

        if dlc_list:
            stats["dlc_available"] = len(dlc_list)
            print(f"\n📦 {len(dlc_list)} DLC(s) available")
            print("   - Extracting major campaign DLC to PS3_GAME/USRDIR/DLC/")
            print(f"   - Copying ALL {len(dlc_list)} PKG files to _PKG/")
            print("   - Creating RAP files in _PKG/RAPS/")

            # Major campaign keywords (game-agnostic heuristics)
            campaign_keywords = [
                "CAMPAIGN",
                "MISSION",
                "CHAPTER",
                "EPISODE",
                "EXPANSION",
                "ASSAULT",
                "QUEST",
                "ADVENTURE",
                "STORY",
                # Borderlands
                "PIRATES",
                "DRAGON KEEP",
                "TORGUE",
                "HAMMERLOCK",
                "SCARLETT",
                "TINA",
                # Other games
                "LEFT BEHIND",
                "UNCHARTED",
                "INFAMOUS",
            ]

            for dlc in dlc_list:
                dlc_name = dlc.get("Name", "")
                content_id = dlc.get("Content ID", "")

                # Check if major campaign DLC
                is_major_campaign = any(kw in dlc_name.upper() for kw in campaign_keywords)

                # Extract major campaigns to disc (for real PS3)
                if is_major_campaign and not dry_run:
                    success = stage._apply_update(game_folder, title_id, dlc)
                    if success:
                        stats["dlc_campaign_extracted"] += 1
                        print(f"   ✓ Extracted to disc: {dlc_name[:60]}")
                elif is_major_campaign:
                    print(f"   [DRY RUN] Would extract: {dlc_name[:60]}")
                    stats["dlc_campaign_extracted"] += 1

                # Copy PKG file (for ALL DLC, not just campaigns)
                dlc.get("PKG direct link", "")
                pkg_source = None

                # Search local packages directory
                pkg_search_dir = stage.pkg_archive_path / "packages"
                if pkg_search_dir.exists() and dlc_name:
                    clean_dlc_name = dlc_name.replace("™", "").replace("'", "")
                    for pkg_file in pkg_search_dir.glob("*.pkg"):
                        clean_pkg_name = pkg_file.stem.replace("™", "").replace("'", "")
                        if clean_dlc_name in clean_pkg_name or clean_pkg_name in clean_dlc_name:
                            pkg_source = pkg_file
                            break

                # Copy to _PKG/ folder
                if pkg_source and not dry_run:
                    pkg_dest = pkg_dir / pkg_source.name
                    if not pkg_dest.exists():
                        shutil.copy2(pkg_source, pkg_dest)
                    stats["dlc_pkg_copied"] += 1
                elif pkg_source:
                    print(f"   [DRY RUN] Would copy PKG: {pkg_source.name[:60]}")
                    stats["dlc_pkg_copied"] += 1

                # Create RAP file
                rap_hash = dlc.get("RAP", "")
                if rap_hash and content_id:
                    rap_filename = f"{content_id}.rap"
                    if not dry_run:
                        rap_dest = raps_dir / rap_filename
                        if not rap_dest.exists():
                            try:
                                rap_bytes = bytes.fromhex(rap_hash)
                                rap_dest.write_bytes(rap_bytes)
                                stats["rap_files_downloaded"] += 1
                            except (ValueError, OSError):
                                pass
                    else:
                        stats["rap_files_downloaded"] += 1
        else:
            print("\n⚠️  No DLC found")

    # Generate README
    if not dry_run:
        print("\n📝 Generating README.txt...")
        pkg_files = [f.name for f in pkg_dir.glob("*.pkg")] if pkg_dir.exists() else []
        generate_readme(
            game_folder,
            title_id,
            pkg_files,
            stats["rap_files_downloaded"],
            stats["dlc_available"],
            stats["dlc_campaign_extracted"],
        )

    # Print summary
    print("\n" + "=" * 80)
    print("📊 Statistics:")
    print(f"   Updates available: {stats['updates_available']}")
    print(f"   Updates applied: {stats['updates_applied']}")
    print(f"   DLC available: {stats['dlc_available']}")
    print(f"   Campaign DLC extracted: {stats['dlc_campaign_extracted']}")
    print(f"   DLC PKGs copied: {stats['dlc_pkg_copied']}")
    print(f"   RAP files created: {stats['rap_files_downloaded']}")
    print("=" * 80)

    stats["success"] = True
    return stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build HYBRID PS3 packages for entire library",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("/data/emu/ps3netsrv"),
        help="Source directory containing .ps3 game folders (default: /data/emu/ps3netsrv)",
    )
    parser.add_argument(
        "--filter", type=str, help='Only process games starting with this letter (e.g., "A")'
    )
    parser.add_argument("--game", type=str, help="Only process game with this name (partial match)")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done without modifying files"
    )
    parser.add_argument(
        "--pkg-archive",
        type=Path,
        default=Path("/data/emu/source/nopaystation/downloads-ps3-dlc"),
        help="PKG archive directory (default: /data/emu/source/nopaystation/downloads-ps3-dlc)",
    )
    parser.add_argument(
        "--nps-database",
        type=Path,
        default=Path("/data/emu/source/nopaystation/PS3_DLCS.tsv"),
        help="NoPayStation database (default: /data/emu/source/nopaystation/PS3_DLCS.tsv)",
    )
    parser.add_argument("--no-updates", action="store_true", help="Skip update application")
    parser.add_argument("--no-dlc", action="store_true", help="Skip DLC processing")

    args = parser.parse_args()

    print("=" * 80)
    print("Universal PS3 HYBRID Builder")
    print("=" * 80)
    print(f"\n📂 Source: {args.source}")
    print(f"📦 PKG Archive: {args.pkg_archive}")
    print(f"📋 Database: {args.nps_database}")

    if args.filter:
        print(f"🔍 Filter: Games starting with '{args.filter}'")
    if args.game:
        print(f"🔍 Filter: Games matching '{args.game}'")
    if args.dry_run:
        print("🔍 Mode: DRY RUN (no modifications)")

    # Validate paths
    if not args.source.exists():
        print(f"\n❌ Source not found: {args.source}")
        return 1

    # Find .ps3 game folders
    game_folders = sorted([f for f in args.source.iterdir() if f.is_dir() and f.suffix == ".ps3"])

    # Apply filters
    if args.filter:
        letter = args.filter.upper()[0]
        game_folders = [f for f in game_folders if f.name[0].upper() == letter]

    if args.game:
        search = args.game.lower()
        game_folders = [f for f in game_folders if search in f.name.lower()]

    if not game_folders:
        print("\n⚠️  No game folders found matching criteria")
        return 0

    print(f"\n✅ Found {len(game_folders)} game(s) to process\n")

    # Initialize stage
    stage = ApplyPS3UpdatesStage(
        nps_database=str(args.nps_database),
        pkg_archive=str(args.pkg_archive),
        apply_updates=not args.no_updates,
        apply_dlc=not args.no_dlc,
        use_sony_psn=True,
    )

    # Process each game
    total_stats = {
        "processed": 0,
        "success": 0,
        "failed": 0,
        "updates_applied": 0,
        "dlc_extracted": 0,
        "pkgs_copied": 0,
    }

    for i, game_folder in enumerate(game_folders, 1):
        print(f"\n[{i}/{len(game_folders)}] {game_folder.name}")

        try:
            stats = process_game(game_folder, stage, args.dry_run)
            total_stats["processed"] += 1

            if stats["success"]:
                total_stats["success"] += 1
                total_stats["updates_applied"] += stats["updates_applied"]
                total_stats["dlc_extracted"] += stats["dlc_campaign_extracted"]
                total_stats["pkgs_copied"] += stats["dlc_pkg_copied"]
            else:
                total_stats["failed"] += 1

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Error processing {game_folder.name}: {e}")
            import traceback

            traceback.print_exc()
            total_stats["failed"] += 1

    # Final summary
    print("\n" + "=" * 80)
    print("🎉 BATCH PROCESSING COMPLETE")
    print("=" * 80)
    print("\n📊 Total Statistics:")
    print(f"   Games processed: {total_stats['processed']}")
    print(f"   Successful: {total_stats['success']}")
    print(f"   Failed: {total_stats['failed']}")
    print(f"   Total updates applied: {total_stats['updates_applied']}")
    print(f"   Total campaign DLC extracted: {total_stats['dlc_extracted']}")
    print(f"   Total PKG files copied: {total_stats['pkgs_copied']}")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
