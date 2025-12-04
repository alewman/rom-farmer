#!/usr/bin/env python3
"""Prepare Borderlands 2 for RPCS3 with proper DLC structure."""

from pathlib import Path
import shutil

def main():
    """Set up RPCS3 game structure."""
    print("=" * 80)
    print("Setting up Borderlands 2 for RPCS3")
    print("=" * 80)
    
    # Paths
    source_complete = Path("/data/emu/ps3netsrv/GAMES/Borderlands 2 (USA) (En,Fr,De,Es,It)_COMPLETE.ps3")
    
    # Where does RPCS3 store games? Need to find this
    # Typical locations:
    # - ~/.config/rpcs3/dev_hdd0/game/
    # - ./rpcs3/dev_hdd0/game/
    
    print("\nRPCS3 DLC Structure:")
    print("-" * 80)
    print("For RPCS3, DLC should be installed separately as HDD content:")
    print()
    print("  dev_hdd0/")
    print("    └── game/")
    print("        └── BLUS30982/        # Game installation")
    print("            ├── PARAM.SFO")
    print("            └── USRDIR/")
    print("                └── DLC/      # DLC content goes here")
    print()
    print("The disc image (.ps3 folder) should be loaded as a disc,")
    print("and DLC should be in dev_hdd0/game/BLUS30982/")
    print()
    
    # Check if DLC exists
    dlc_source = source_complete / "PS3_GAME" / "USRDIR" / "DLC"
    if dlc_source.exists():
        dlc_size_gb = sum(f.stat().st_size for f in dlc_source.rglob('*') if f.is_file()) / (1024**3)
        dlc_count = len(list(dlc_source.iterdir()))
        print(f"✓ Found {dlc_count} DLC packages ({dlc_size_gb:.1f} GB)")
        print(f"  Location: {dlc_source}")
    
    print()
    print("=" * 80)
    print("Next Steps:")
    print("=" * 80)
    print()
    print("1. In RPCS3, File → Boot Game → Select the .ps3 folder:")
    print(f"   {source_complete}")
    print()
    print("2. The game should show as v01.15")
    print()
    print("3. For DLC to work in RPCS3, you need to:")
    print("   a. Install the DLC PKG files directly in RPCS3")
    print("   b. Or manually copy DLC to RPCS3's dev_hdd0/game/BLUS30982/")
    print()
    print("4. DLC PKG files are in:")
    print("   /data/emu/source/nopaystation/downloads-ps3-dlc/packages/")
    print()
    print("5. In RPCS3: File → Install PKG → Select each DLC .pkg file")
    print()
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
