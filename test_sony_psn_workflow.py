#!/usr/bin/env python3
"""Test PS3 update workflow with Sony PSN integration."""

from pathlib import Path
import sys
import tempfile
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from romgroomer.stages.apply_ps3_updates import ApplyPS3UpdatesStage

def create_test_game_folder(temp_dir: Path) -> Path:
    """Create a fake Borderlands 2 game folder for testing."""
    game_folder = temp_dir / "Borderlands 2 [BLUS30982]"
    game_folder.mkdir(parents=True)
    
    # Create PARAM.SFO file (minimal)
    ps3_game = game_folder / "PS3_GAME"
    ps3_game.mkdir()
    
    param_sfo = ps3_game / "PARAM.SFO"
    param_sfo.write_bytes(b'\x00PSF' + b'\x00' * 100)  # Minimal fake SFO
    
    return game_folder

def main():
    """Test Sony PSN update workflow."""
    print("=" * 70)
    print("Testing Sony PSN Update Workflow")
    print("=" * 70)
    
    # Use temp directory for test
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test game folder
        print("\nSetting up test environment...")
        games_dir = temp_path / "games"
        games_dir.mkdir()
        
        game_folder = create_test_game_folder(games_dir)
        print(f"  Created test game: {game_folder.name}")
        
        # Create PKG cache directory
        pkg_cache = temp_path / "pkg_cache"
        pkg_cache.mkdir()
        print(f"  PKG cache: {pkg_cache}")
        
        # Initialize stage with Sony PSN enabled
        print("\nInitializing PS3 update stage...")
        stage = ApplyPS3UpdatesStage(
            nps_database="/data/emu/dats/nointro/PS3_DLCS.tsv",  # Won't be used for this test
            pkg_archive=str(pkg_cache),
            apply_updates=True,
            apply_dlc=False,
            use_sony_psn=True
        )
        
        print(f"  NoPayStation database: {stage.nps_database_path}")
        print(f"  PKG archive: {stage.pkg_archive_path}")
        print(f"  Sony PSN enabled: {stage.psn_client is not None}")
        
        # Test querying Sony PSN for Borderlands 2
        title_id = "BLUS30982"
        print(f"\nQuerying Sony PSN for updates: {title_id}")
        print("-" * 70)
        
        if stage.psn_client:
            updates = stage.psn_client.get_updates_for_title(title_id)
            
            if updates:
                print(f"\n✓ Found {len(updates)} update(s) from Sony PSN:\n")
                
                for i, update in enumerate(updates, 1):
                    size_mb = int(update.get('File Size', '0')) / (1024 * 1024)
                    print(f"  {i}. {update.get('Name', 'Unknown')}")
                    print(f"     Version: {update.get('Version', 'Unknown')}")
                    print(f"     Size: {size_mb:.1f} MB")
                    print(f"     Source: {update.get('Source', 'Unknown')}")
                    print()
                
                # Test download capability (but don't actually download 649MB)
                print("Download test:")
                print(f"  PKG URL: {updates[0].get('PKG direct link', 'N/A')}")
                print(f"  Cache dir: {pkg_cache / 'sony_psn_cache'}")
                print(f"  ⚠️  Skipping actual download (649 MB)")
                
            else:
                print("❌ No updates found!")
                return 1
        else:
            print("❌ Sony PSN client not initialized!")
            return 1
    
    print("\n" + "=" * 70)
    print("✓ Sony PSN workflow test PASSED!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. To test actual download, set a real game folder")
    print("  2. Run stage.run() to download and apply update")
    print("  3. Verify extracted files merged into PS3_GAME folder")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
