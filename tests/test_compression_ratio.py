#!/usr/bin/env python3
"""Quick test of compression ratio prediction."""

from pathlib import Path
from romfarmer.metadata.database import MetadataDatabase

# Initialize database
db_path = Path("/data/emu/rom-farmer-python/metadata/database/romfarmer.db")
if not db_path.exists():
    print(f"Database not found: {db_path}")
    exit(1)

db = MetadataDatabase(db_path)

# Test compression ratio queries
print("Testing compression ratio queries:\n")

# Saturn CHD
ratio = db.get_average_compression_ratio(platform="saturn", output_format="chd", min_samples=1)
if ratio:
    print(f"✅ Saturn CHD: {ratio:.3f} (found historical data)")
else:
    print("❌ Saturn CHD: No historical data (will use default 0.65)")

# PSX CHD
ratio = db.get_average_compression_ratio(platform="psx", output_format="chd", min_samples=1)
if ratio:
    print(f"✅ PSX CHD: {ratio:.3f} (found historical data)")
else:
    print("❌ PSX CHD: No historical data (will use default 0.70)")

# Any platform, any format (check if transformations exist at all)
ratio = db.get_average_compression_ratio(platform=None, output_format=None, min_samples=1)
if ratio:
    print(f"✅ Overall average: {ratio:.3f} (found transformations)")
else:
    print("❌ No transformation data in database yet")

print("\n✨ Compression ratio query function works!")
print("📊 After first build, historical data will improve predictions")
