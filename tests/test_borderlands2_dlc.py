#!/usr/bin/env python3
"""Test Borderlands 2 DLC application with Python PKG decrypter."""

import shutil
from pathlib import Path
from romfarmer.stages.apply_ps3_updates import ApplyPS3UpdatesStage
from romfarmer.stages.base import StageContext

# Configuration
NPS_DATABASE = "/data/emu/source/nopaystation/PS3_DLCS.tsv"
PKG_ARCHIVE = "/data/emu/source/nopaystation/downloads-ps3-dlc"
ROMS_DIR = "/data/emu/ps3netsrv/GAMES"  # Original games location
TEST_DIR = "/tmp/ps3_dlc_test"  # Test location (writable)

# Test game
ORIGINAL_GAME = "Borderlands 2 (USA) (En,Fr,De,Es,It).ps3"
TEST_GAME = "Borderlands 2 (USA) (En,Fr,De,Es,It)_DLC_TEST.ps3"

def main():
    print("=" * 80)
    print("Borderlands 2 DLC Application Test")
    print("=" * 80)
    print()
    print("Configuration:")
    print(f"  NPS Database: {NPS_DATABASE}")
    print(f"  PKG Archive:  {PKG_ARCHIVE}")
    print(f"  Source ROMs:  {ROMS_DIR}")
    print(f"  Test Dir:     {TEST_DIR}")
    print()
    
    # Check paths exist
    if not Path(NPS_DATABASE).exists():
        print(f"ERROR: Database not found: {NPS_DATABASE}")
        return 1
    
    if not Path(PKG_ARCHIVE).exists():
        print(f"ERROR: Archive not found: {PKG_ARCHIVE}")
        return 1
    
    if not Path(ROMS_DIR).exists():
        print(f"ERROR: ROMs dir not found: {ROMS_DIR}")
        return 1
    
    # Create test directory
    Path(TEST_DIR).mkdir(parents=True, exist_ok=True)
    
    # Check original game exists
    original_path = Path(ROMS_DIR) / ORIGINAL_GAME
    if not original_path.exists():
        print(f"ERROR: Original game not found: {original_path}")
        return 1
    
    # Create test copy if it doesn't exist
    test_path = Path(TEST_DIR) / TEST_GAME
    if test_path.exists():
        print(f"Test copy already exists: {TEST_GAME}")
        print("Using existing test copy...")
    else:
        print(f"Creating test copy of game...")
        print(f"  Source: {ORIGINAL_GAME}")
        print(f"  Dest:   {TEST_GAME}")
        shutil.copytree(original_path, test_path)
        print(f"  ✓ Copy complete")
    
    print()
    
    # Create stage with DLC enabled
    print("Initializing ApplyPS3UpdatesStage...")
    stage = ApplyPS3UpdatesStage(
        nps_database=NPS_DATABASE,
        pkg_archive=PKG_ARCHIVE,
        apply_updates=False,  # Focus on DLC only
        apply_dlc=True
    )
    
    print()
    print("Processing test game folder only...")
    print("-" * 80)
    
    # Create minimal context pointing to test copy only
    from dataclasses import dataclass, field
    from typing import Dict, List, Any, Optional
    
    @dataclass
    class MinimalContext:
        platform_name: str = "ps3"
        platform_config: Any = None
        target_name: str = "ps3"
        source_dir: Path = Path(TEST_DIR)
        work_dir: Path = Path(TEST_DIR)  # Point to test directory
        output_dir: Path = Path(TEST_DIR)
        dat_file: Optional[Any] = None
        source_files: List[Path] = field(default_factory=list)
        matched_files: List[Path] = field(default_factory=list)
        filtered_files: List[Path] = field(default_factory=list)
        organized_files: Dict[str, List[Path]] = field(default_factory=dict)
        file_md5s: Dict[Path, str] = field(default_factory=dict)
        rom_md5_map: Dict[Path, str] = field(default_factory=dict)
    
    context = MinimalContext()
    
    # Temporarily filter to only process the test game
    original_find_game_folders = stage._find_game_folders
    def find_only_test_game(work_dir):
        return [test_path]
    stage._find_game_folders = find_only_test_game
    
    stage.execute(context)
    
    print()
    print("=" * 80)
    print("Test Complete!")
    print("=" * 80)
    print()
    print("You can now compare:")
    print(f"  Original: {ORIGINAL_GAME}")
    print(f"  With DLC: {TEST_GAME}")
    
    return 0

if __name__ == "__main__":
    exit(main())
