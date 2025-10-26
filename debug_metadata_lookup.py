#!/usr/bin/env python3
"""Debug metadata lookup for Saturn games."""

import hashlib
from pathlib import Path
from romgroomer.metadata.database import MetadataDatabase
from romgroomer.metadata.transformation import ROMTransformation

def calculate_md5(file_path):
    """Calculate MD5 of a file."""
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5.update(chunk)
    return md5.hexdigest()

# Initialize database
db = MetadataDatabase('metadata/database/romgroomer.db')
session = db.get_session()

# Check a few sample CHD files
output_dir = Path('/data/emu/output/saturn')
test_files = [
    'Dark Legend (USA).chd',
    'Best Games/Daytona USA C.C.E. Net Link Edition (USA).chd',
    'Best Games/Astal (USA) (3S).chd',
]

print("=== Metadata Lookup Debug ===\n")

for filename in test_files:
    file_path = output_dir / filename
    if not file_path.exists():
        print(f"❌ File not found: {filename}\n")
        continue
    
    print(f"File: {filename}")
    
    # Calculate CHD MD5
    chd_md5 = calculate_md5(file_path)
    print(f"  CHD MD5: {chd_md5}")
    
    # Look up transformation
    trans = session.query(ROMTransformation).filter(
        ROMTransformation.final_md5 == chd_md5
    ).first()
    
    if trans:
        print(f"  ✅ Found transformation:")
        print(f"     Source: {trans.source_file_name}")
        print(f"     Game linked: {'Yes' if trans.game_id else 'No'}")
        if trans.game:
            print(f"     Game name: {trans.game.name}")
            print(f"     Has description: {'Yes' if trans.game.description else 'No'}")
    else:
        print(f"  ❌ No transformation found for this CHD MD5")
    
    print()

session.close()
