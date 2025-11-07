#!/usr/bin/env python3
"""Test selection filter with compression ratio prediction."""

from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from romgroomer.config.models import SelectionConfig, SelectionStrategy, ScopePattern, PatternType
from romgroomer.stages.filter_selection import SelectionFilter, DEFAULT_COMPRESSION_RATIOS

print("🧪 Testing Compression Ratio Prediction\n")

# Show default ratios
print("Default Compression Ratios:")
for platform, ratio in sorted(DEFAULT_COMPRESSION_RATIOS.items())[:5]:
    print(f"  {platform:15} → {ratio:.2f}")
print(f"  ... and {len(DEFAULT_COMPRESSION_RATIOS) - 5} more\n")

# Create selection config with budget
selection = SelectionConfig(
    strategy=SelectionStrategy.RATING_BUDGET,
    max_size_gb=40.0,  # 40GB target
    min_rating=0.7,
    pattern=ScopePattern(type=PatternType.GLOB, value="*USA*")
)

print("Selection Config:")
print(f"  Strategy: {selection.strategy.value}")
print(f"  Target Budget: {selection.max_size_gb} GB")
print(f"  Min Rating: {selection.min_rating}\n")

# Test compression ratio calculation
print("Budget Adjustment Calculation:")
print(f"  Target output: {selection.max_size_gb} GB")

for platform in ["saturn", "psx", "ps3"]:
    ratio = DEFAULT_COMPRESSION_RATIOS[platform]
    safety_factor = 0.95
    adjusted_budget = (selection.max_size_gb / ratio) * safety_factor
    
    print(f"\n  {platform.upper()}:")
    print(f"    Compression ratio: {ratio:.2f}")
    print(f"    Safety factor: {safety_factor:.2f}")
    print(f"    Adjusted source budget: {adjusted_budget:.1f} GB")
    print(f"    Expected output: ~{selection.max_size_gb * safety_factor:.1f} GB (95% of target)")

print("\n✅ Compression ratio system ready!")
print("📝 Next: Run actual build to see it work with real files")
