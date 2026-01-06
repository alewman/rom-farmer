#!/usr/bin/env python3
"""Test arcade filtering end-to-end.

This script validates the arcade pipeline without copying files.
"""

from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from romfarmer.dat_parser.parser import DATParser
from romfarmer.arcade.classifier import ArcadeClassifier, CloneImportance
from romfarmer.arcade.filter import ArcadeFilter, ArcadeFilterConfig, ArcadeFilterMode
from collections import Counter


def test_fbneo():
    """Test FBNeo arcade filtering."""
    print("=" * 60)
    print("FBNeo Arcade Filter Test")
    print("=" * 60)
    
    # Parse DAT
    dat_path = Path("dats/fbneo/fbneo-arcade.dat")
    if not dat_path.exists():
        print(f"ERROR: DAT not found: {dat_path}")
        return False
    
    parser = DATParser()
    dat = parser.parse(dat_path)
    print(f"\n✓ Parsed DAT: {dat.name}")
    print(f"  Total games: {len(dat.games):,}")
    
    # Test classifier
    classifier = ArcadeClassifier()
    classifications = [(g, classifier.classify(g)) for g in dat.games]
    
    # Count by type
    type_counts = Counter(c.clone_type.value for _, c in classifications)
    print(f"\n✓ Classification distribution:")
    for t, count in type_counts.most_common():
        print(f"  {t}: {count:,}")
    
    # Count working
    working = sum(1 for _, c in classifications if c.is_working)
    print(f"\n✓ Working games: {working:,} ({100*working/len(dat.games):.1f}%)")
    
    # Test filter modes
    for mode in [ArcadeFilterMode.STRICT, ArcadeFilterMode.RELAXED, ArcadeFilterMode.COMPLETE]:
        config = ArcadeFilterConfig(
            mode=mode,
            include_hacks=True,
            include_bootlegs=False,
            include_prototypes=True,
            include_working_only=True,
        )
        
        arcade_filter = ArcadeFilter(config=config)
        results = arcade_filter.filter_dat(dat)
        selected = sum(1 for r in results if r.selected)
        
        print(f"\n✓ {mode.value.upper()} mode: {selected:,} selected")
    
    # Test source matching
    source_dir = Path("/data/emu/source/myrient.erista.me/files/FinalBurn Neo/arcade")
    if source_dir.exists():
        source_files = {f.stem for f in source_dir.glob("*.zip")}
        
        config = ArcadeFilterConfig(
            mode=ArcadeFilterMode.RELAXED,
            include_hacks=True,
            include_working_only=True,
        )
        arcade_filter = ArcadeFilter(config=config)
        results = arcade_filter.filter_dat(dat)
        selected = [r for r in results if r.selected]
        selected_names = {r.game.name for r in selected}
        
        matched = selected_names & source_files
        missing = selected_names - source_files
        
        print(f"\n✓ Source file matching:")
        print(f"  Source files: {len(source_files):,}")
        print(f"  Selected games: {len(selected):,}")
        print(f"  Matched: {len(matched):,}")
        print(f"  Missing: {len(missing):,}")
        
        if missing:
            print(f"\n  First 5 missing:")
            for name in sorted(missing)[:5]:
                print(f"    - {name}")
    else:
        print(f"\n⚠ Source directory not found: {source_dir}")
    
    # Check essential hacks
    config = ArcadeFilterConfig(
        mode=ArcadeFilterMode.RELAXED,
        include_hacks=True,
        include_working_only=True,
    )
    arcade_filter = ArcadeFilter(config=config)
    results = arcade_filter.filter_dat(dat)
    
    essential = [r for r in results if r.selected and r.classification.importance == CloneImportance.ESSENTIAL and r.game.cloneof]
    print(f"\n✓ Essential hacks/bootlegs included: {len(essential)}")
    for r in essential[:10]:
        print(f"  {r.game.name}: {r.game.description[:50]}...")
    
    print("\n" + "=" * 60)
    print("TEST PASSED ✓")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_fbneo()
    sys.exit(0 if success else 1)
