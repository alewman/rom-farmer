#!/usr/bin/env python3
"""
Debug utility to figure out which MD5 ARRM is storing.

Compares:
1. MD5 in database (what ARRM scraped)
2. MD5s in DAT file (CUE file per Redump standard)
3. Actual file MD5s (ZIP, CUE, first BIN)
"""

import hashlib
import zipfile
from pathlib import Path
import sys

# Add project to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from romgroomer.metadata.database import MetadataDatabase, ScrapedGame


def calculate_md5(file_path: Path) -> str:
    """Calculate MD5 of a file."""
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5.update(chunk)
    return md5.hexdigest()


def get_cue_md5_from_zip(zip_path: Path) -> str:
    """Extract and hash the CUE file from a ZIP."""
    with zipfile.ZipFile(zip_path, 'r') as zf:
        # Find .cue file
        cue_files = [f for f in zf.namelist() if f.lower().endswith('.cue')]
        if not cue_files:
            return None
        
        # Hash the CUE content
        cue_content = zf.read(cue_files[0])
        return hashlib.md5(cue_content).hexdigest()


def get_first_bin_md5_from_zip(zip_path: Path) -> str:
    """Extract and hash the first BIN file from a ZIP."""
    with zipfile.ZipFile(zip_path, 'r') as zf:
        # Find .bin files and get the first track (usually Track 01)
        bin_files = sorted([f for f in zf.namelist() if f.lower().endswith('.bin')])
        if not bin_files:
            return None
        
        # Look for Track 01 specifically
        track01 = [f for f in bin_files if 'Track 01' in f or 'Track 1)' in f]
        first_bin = track01[0] if track01 else bin_files[0]
        
        # Hash the first BIN content
        print(f"  Hashing: {first_bin} (size: {zf.getinfo(first_bin).file_size:,} bytes)")
        bin_content = zf.read(first_bin)
        return hashlib.md5(bin_content).hexdigest()


def main():
    # Test with 3D Lemmings
    test_game = "3D Lemmings"
    
    print(f"=== Investigating: {test_game} ===\n")
    
    # 1. Get MD5 from database
    db = MetadataDatabase(Path("metadata/database/romgroomer.db"))
    session = db.get_session()
    
    game = session.query(ScrapedGame).filter(
        ScrapedGame.system == 'saturn',
        ScrapedGame.name.like(f'%{test_game}%')
    ).first()
    
    if not game:
        print(f"❌ Game not found in database")
        return
    
    print(f"📊 Database (ARRM scraped):")
    print(f"   MD5: {game.md5}")
    print(f"   Name: {game.name}")
    print(f"   Filename: {game.filename}\n")
    
    # 2. Check actual file MD5s
    zip_path = Path(f"/data/emu/roms/saturn/{test_game} (Europe).zip")
    
    if not zip_path.exists():
        print(f"❌ ZIP file not found: {zip_path}")
        return
    
    print(f"📦 Actual File Hashes:")
    
    # ZIP file itself
    zip_md5 = calculate_md5(zip_path)
    print(f"   ZIP file MD5:   {zip_md5}")
    print(f"   Match: {'✅ YES' if zip_md5 == game.md5 else '❌ NO'}\n")
    
    # CUE file inside ZIP
    cue_md5 = get_cue_md5_from_zip(zip_path)
    if cue_md5:
        print(f"   CUE file MD5:   {cue_md5}")
        print(f"   Match: {'✅ YES' if cue_md5 == game.md5 else '❌ NO'}\n")
    
    # First BIN file inside ZIP
    print("   First BIN file:")
    bin_md5 = get_first_bin_md5_from_zip(zip_path)
    if bin_md5:
        print(f"   First BIN MD5:  {bin_md5}")
        print(f"   Match: {'✅ YES' if bin_md5 == game.md5 else '❌ NO'}\n")
    
    # 3. Summary
    print("=" * 60)
    print("\n🔍 CONCLUSION:")
    if cue_md5 == game.md5:
        print("   ARRM stored the CUE file's MD5 ✅")
    elif bin_md5 == game.md5:
        print("   ARRM stored the first BIN file's MD5 ✅")
    elif zip_md5 == game.md5:
        print("   ARRM stored the ZIP file's MD5 ✅")
    else:
        print("   ❌ MD5 doesn't match any of the tested files!")
        print("   Database MD5 might be from a different file or calculation method.")
    
    session.close()


if __name__ == "__main__":
    main()
