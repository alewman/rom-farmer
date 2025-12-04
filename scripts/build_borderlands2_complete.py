#!/usr/bin/env python3
"""Build HYBRID Borderlands 2 - fully updated game + PKG files for manual install."""

from pathlib import Path
import sys
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from romfarmer.stages.apply_ps3_updates import ApplyPS3UpdatesStage
from romfarmer.stages.base import StageContext

def main():
    """Build HYBRID Borderlands 2 with updates baked in + DLC PKGs for manual install."""
    print("=" * 80)
    print("Building HYBRID Borderlands 2 (v01.15 baked in + DLC PKGs)")
    print("=" * 80)
    
    # Paths
    source_game = Path("/data/emu/ps3netsrv/Borderlands 2 (USA) (En,Fr,De,Es,It).ps3")
    output_game = Path("/data/emu/ps3netsrv/Borderlands 2 (USA) (En,Fr,De,Es,It)_HYBRID.ps3")
    pkg_archive = Path("/data/emu/source/nopaystation/downloads-ps3-dlc")  # DLC PKG source
    nps_database = Path("/data/emu/source/nopaystation/PS3_DLCS.tsv")
    
    # Validate source exists
    if not source_game.exists():
        print(f"❌ Source game not found: {source_game}")
        return 1
    
    print(f"\n📦 Source: {source_game.name}")
    print(f"📦 Output: {output_game.name}")
    print(f"📦 PKG Archive: {pkg_archive}")
    print(f"📦 NPS Database: {nps_database}")
    print(f"\n💡 HYBRID Build:")
    print(f"   - Updates: Baked into game (v01.15)")
    print(f"   - DLC: Extracted for real PS3 + PKGs for RPCS3")
    print(f"   - PKG files stored in: _PKG/ (at root, ignored by real PS3)")
    
    # Remove old output if exists
    if output_game.exists():
        print(f"\n🗑️  Removing old output: {output_game.name}")
        shutil.rmtree(output_game)
    
    # Copy source to output
    print(f"\n📋 Copying base game...")
    shutil.copytree(source_game, output_game)
    print(f"   ✓ Copied to {output_game.name}")
    
    # Create _PKG directory at ROOT for RPCS3 installation files (real PS3 will ignore it)
    pkg_dir = output_game / "_PKG"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n📁 Created PKG directory: {pkg_dir.relative_to(output_game)}")

    
    # Initialize PS3 update stage
    print(f"\n⚙️  Initializing PS3 update stage...")
    stage = ApplyPS3UpdatesStage(
        nps_database=str(nps_database),
        pkg_archive=str(pkg_archive),
        pkgrip_path="/data/emu/rom-farmer-python/tools/pkgrip/src/pkgrip",
        apply_updates=True,   # Apply game updates from Sony PSN
        apply_dlc=True,       # Apply DLC from NoPayStation
        use_sony_psn=True     # Enable Sony PSN update queries
    )
    
    print(f"   ✓ NoPayStation: {len(stage.database.entries)} entries")
    print(f"   ✓ Sony PSN: {'Enabled' if stage.psn_client else 'Disabled'}")
    print(f"   ✓ pkgrip: {stage.pkgrip_path}")
    # Process only the output game (not entire directory)
    print(f"\n🔧 Processing game...")
    print("-" * 80)
    
    # Process just this one game folder
    game_folder = output_game
    
    stats = {
        'updates_available': 0,
        'updates_applied': 0,
        'dlc_available': 0,
        'dlc_campaign_extracted': 0,  # Major DLC extracted for real PS3
        'dlc_pkg_copied': 0,           # All PKGs copied for RPCS3
        'rap_files_downloaded': 0      # RAP files for RPCS3
    }
    
    # Extract title ID
    title_id = stage._extract_title_id(game_folder)
    if not title_id:
        print(f"❌ Could not extract TITLE_ID from {game_folder.name}")
        return 1
    
    print(f"Processing: {game_folder.name}")
    print(f"Title ID: {title_id}")
    
    # Find and apply UPDATES ONLY (bake into game)
    if stage.apply_updates:
        # Try NoPayStation database first
        nps_updates = stage.database.find_updates_for_title(title_id)
        
        # Try Sony PSN servers for live updates
        psn_updates = []
        if stage.psn_client:
            psn_updates = stage.psn_client.get_updates_for_title(title_id)
        
        # Combine both sources
        updates = nps_updates + psn_updates
        
        if updates:
            stats['updates_available'] += len(updates)
            sources = []
            if nps_updates:
                sources.append(f"{len(nps_updates)} from NoPayStation")
            if psn_updates:
                sources.append(f"{len(psn_updates)} from Sony PSN")
            source_info = ", ".join(sources)
            print(f"\n📦 {len(updates)} update(s) available ({source_info})")
            
            for update in updates:
                success = stage._apply_update(game_folder, title_id, update)
                if success:
                    stats['updates_applied'] += 1
        else:
            print(f"\n⚠️  No updates found")
    
    # Find and process DLC
    if stage.apply_dlc:
        # Get ALL DLC (not just story/campaigns)
        dlc_list = stage.database.find_all_dlc_for_title(title_id)
        
        if dlc_list:
            stats['dlc_available'] += len(dlc_list)
            print(f"\n📦 {len(dlc_list)} DLC(s) available")
            print(f"   - Extracting major campaign DLC to PS3_GAME/USRDIR/DLC/ (for real PS3)")
            print(f"   - Copying ALL {len(dlc_list)} PKG files to _PKG/ (for RPCS3 - at root)")
            print(f"   - Downloading RAP files to _PKG/RAPS/ (for RPCS3)")
            
            # Create RAPS directory
            raps_dir = pkg_dir / "RAPS"
            raps_dir.mkdir(parents=True, exist_ok=True)
            
            # Major campaign DLC names (extract these for real PS3 disc compatibility)
            major_campaigns = ['ORCHID', 'IRIS', 'SAGE', 'ASTER']  # Captain Scarlett, Mr. Torgue, Sir Hammerlock, Tiny Tina
            
            for dlc in dlc_list:
                dlc_name = dlc.get('Name', '')
                content_id = dlc.get('Content ID', '')
                
                # Determine if this is a major campaign DLC
                is_major_campaign = any(x in dlc_name.upper() for x in ['SCARLETT', 'TORGUE', 'HAMMERLOCK', 'TINA'])
                
                # Extract major campaign DLC to DLC/ directory (for real PS3)
                # Note: Real PS3 loads these from disc, but only extracting large campaigns to save space
                if is_major_campaign:
                    success = stage._apply_update(game_folder, title_id, dlc)
                    if success:
                        stats['dlc_campaign_extracted'] += 1
                        print(f"   ✓ Extracted to disc: {dlc_name[:50]}")
                
                # ========================================================================
                # COPY PKG FILES FOR ALL DLC (not just campaigns)
                # ========================================================================
                # RPCS3 requires PKG installation for ALL DLC (disc DLC not recognized)
                # Real PS3 can also use PKGs if users prefer to install to HDD
                # Strategy: 1) Check local packages/, 2) Download if needed, 3) Copy to _PKG/
                
                import urllib.request
                import urllib.error
                
                dlc_name = dlc.get('Name', '')
                pkg_url = dlc.get('PKG direct link', '')
                pkg_filename = dlc.get('File Name') or pkg_url.split('/')[-1] if pkg_url else None
                
                # Try to find PKG locally first
                pkg_source = None
                
                # Method 1: Search by DLC name in packages directory
                pkg_search_dir = pkg_archive / "packages"
                if pkg_search_dir.exists() and dlc_name:
                    for pkg_file in pkg_search_dir.glob("*.pkg"):
                        # Match by name (remove trademark symbols for matching)
                        clean_dlc_name = dlc_name.replace("™", "").replace("'", "")
                        clean_pkg_name = pkg_file.stem.replace("™", "").replace("'", "")
                        if clean_dlc_name in clean_pkg_name or clean_pkg_name in clean_dlc_name:
                            pkg_source = pkg_file
                            break
                
                # Method 2: Try direct filename if we have it
                if not pkg_source and pkg_filename and pkg_filename != 'N/A':
                    possible_paths = [
                        pkg_archive / "packages" / pkg_filename,
                        pkg_archive / pkg_filename,
                    ]
                    for path in possible_paths:
                        if path.exists():
                            pkg_source = path
                            break
                
                # Method 3: Download from NoPayStation if not found locally
                if not pkg_source and pkg_url:
                    # Generate safe filename from DLC name
                    safe_filename = dlc_name.replace("/", "-").replace(":", "").replace("™", "") + ".pkg"
                    download_path = pkg_archive / "packages" / safe_filename
                    
                    print(f"   📥 Downloading: {dlc_name[:50]}...")
                    try:
                        urllib.request.urlretrieve(pkg_url, download_path)
                        pkg_source = download_path
                        print(f"      ✓ Downloaded to packages/")
                    except (urllib.error.URLError, urllib.error.HTTPError) as e:
                        print(f"      ⚠️  Download failed: {e}")
                
                # Copy to _PKG/ folder
                if pkg_source:
                    pkg_dest = pkg_dir / pkg_source.name
                    if not pkg_dest.exists():
                        shutil.copy2(pkg_source, pkg_dest)
                    stats['dlc_pkg_copied'] += 1
                else:
                    print(f"   ⚠️  PKG not found (local or download): {dlc_name}")
                
                # Create RAP file from hex data (for RPCS3)
                rap_hash = dlc.get('RAP', '')  # This is the RAP hex string (16 bytes = 32 hex chars)
                if rap_hash and content_id:
                    # RAP filename is content ID + .rap
                    rap_filename = f"{content_id}.rap"
                    rap_dest = raps_dir / rap_filename
                    
                    # Create RAP file from hex data if not already present
                    if not rap_dest.exists():
                        try:
                            # RAP files are 16-byte license keys stored as hex in database
                            rap_bytes = bytes.fromhex(rap_hash)
                            rap_dest.write_bytes(rap_bytes)
                            stats['rap_files_downloaded'] += 1
                        except (ValueError, OSError) as e:
                            print(f"   ⚠️  Could not create RAP: {rap_filename}")
                    else:
                        stats['rap_files_downloaded'] += 1  # Already exists, count it
        else:
            print(f"\n⚠️  No DLC found")
    
    # ========================================================================
    # GENERATE README.txt
    # ========================================================================
    print("\n📝 Generating README.txt...")
    
    from datetime import datetime
    import locale
    
    # Get folder sizes
    def get_folder_size(path):
        total = 0
        for item in path.rglob('*'):
            if item.is_file():
                total += item.stat().st_size
        return total
    
    def format_size(bytes):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
    
    # Calculate sizes
    ps3_game_size = get_folder_size(output_game / "PS3_GAME") if (output_game / "PS3_GAME").exists() else 0
    pkg_folder_size = get_folder_size(pkg_dir) if pkg_dir.exists() else 0
    total_size = get_folder_size(output_game)
    
    # Get PKG file list
    pkg_files = sorted([f.name for f in pkg_dir.glob("*.pkg")]) if pkg_dir.exists() else []
    pkg_list_text = "\n".join([f"   • {pkg}" for pkg in pkg_files]) if pkg_files else "   (None)"
    
    # Read template
    template_path = Path(__file__).parent / "templates" / "README_HYBRID.txt"
    if template_path.exists():
        readme_template = template_path.read_text()
        
        # Replace placeholders
        readme_content = readme_template.format(
            GAME_TITLE=output_game.name.replace("_HYBRID.ps3", ""),
            BUILD_DATE=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            APP_VER="01.15",
            DLC_COUNT=stats['dlc_available'],
            GAME_FOLDER=output_game.name,
            PKG_COUNT=len(pkg_files),
            RAP_COUNT=stats['rap_files_downloaded'],
            PKG_LIST=pkg_list_text,
            TITLE_ID=title_id,
            REGION="USA",
            TOTAL_SIZE=format_size(total_size),
            BASE_SIZE=format_size(ps3_game_size),
            DISC_DLC_SIZE=f"{stats['dlc_campaign_extracted']} campaigns",
            PKG_SIZE=format_size(pkg_folder_size),
            RAP_SIZE=f"{stats['rap_files_downloaded']} files"
        )
        
        # Write README to game folder
        readme_path = output_game / "README.txt"
        readme_path.write_text(readme_content)
        print(f"   ✓ Created README.txt in game folder")
    else:
        print(f"   ⚠️  Template not found: {template_path}")
    
    print("\n" + "=" * 80)
    print("📊 Statistics:")
    print(f"   Updates available: {stats['updates_available']}")
    print(f"   Updates applied (baked in): {stats['updates_applied']}")
    print(f"   DLC available: {stats['dlc_available']}")
    print(f"   Major campaign DLC extracted (for real PS3): {stats['dlc_campaign_extracted']}")
    print(f"   All DLC PKGs copied (for RPCS3): {stats['dlc_pkg_copied']}")
    print(f"   RAP files downloaded (for RPCS3): {stats['rap_files_downloaded']}")
    print("=" * 80)
    print("✓ HYBRID BUILD COMPLETE!")
    print("=" * 80)
    print(f"\nOutput: {output_game}")
    print(f"\n📖 Usage:")
    print(f"  Real PS3:")
    print(f"    1. Copy {output_game.name} to PS3")
    print(f"    2. Launch - major campaign DLC loads from PS3_GAME/USRDIR/DLC/")
    print(f"    3. Already at v01.15 (no update needed)")
    print(f"    4. For cosmetic/character DLC: Install PKGs from _PKG/ folder")
    print(f"\n  RPCS3:")
    print(f"    1. Boot {output_game.name} in RPCS3")
    print(f"    2. Install ALL DLC via File → Install PKG")
    print(f"    3. PKG files in: _PKG/ (at root of game folder)")
    print(f"    4. Copy RAP files from _PKG/RAPS/ to RPCS3's dev_hdd0/home/00000001/exdata/")
    print(f"    5. Game already at v01.15")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
