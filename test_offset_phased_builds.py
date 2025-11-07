#!/usr/bin/env python3
"""
Test offset + percentage functionality for phased builds.

Simulates a 1000-game library and verifies that offset works correctly.
"""

def test_offset_calculation():
    """Test offset + percentage math."""
    
    total_games = 1000
    
    test_cases = [
        # (offset, percentage, expected_start, expected_end)
        (0, 20, 0, 200),      # Phase 1: First 20%
        (20, 20, 200, 400),   # Phase 2: Skip 20%, take next 20%
        (40, 20, 400, 600),   # Phase 3: Skip 40%, take next 20%
        (60, 20, 600, 800),   # Phase 4: Skip 60%, take next 20%
        (80, 20, 800, 1000),  # Phase 5: Skip 80%, take final 20%
        (0, 50, 0, 500),      # First half
        (50, 50, 500, 1000),  # Second half
        (0, 25, 0, 250),      # First quarter
        (25, 25, 250, 500),   # Second quarter
        (50, 25, 500, 750),   # Third quarter
        (75, 25, 750, 1000),  # Fourth quarter
        (0, 33, 0, 330),      # First third (approximately)
        (33, 33, 330, 660),   # Second third
        (66, 34, 660, 1000),  # Final third (adjusted to 34% to reach 1000)
    ]
    
    print("Testing offset + percentage calculations:\n")
    print(f"{'Offset':<8} {'Percentage':<12} {'Expected Range':<20} {'Calculated Range':<20} {'Status'}")
    print("=" * 80)
    
    all_passed = True
    
    for offset, percentage, expected_start, expected_end in test_cases:
        # Calculate offset
        offset_count = int(total_games * (offset / 100))
        
        # Calculate limit
        limit = int(total_games * (percentage / 100))
        
        # Calculated range
        calc_start = offset_count
        calc_end = min(offset_count + limit, total_games)
        
        # Check if matches expected
        matches = (calc_start == expected_start and calc_end == expected_end)
        status = "✅ PASS" if matches else "❌ FAIL"
        
        if not matches:
            all_passed = False
        
        print(f"{offset:<8.1f} {percentage:<12.1f} {expected_start}-{expected_end:<14} {calc_start}-{calc_end:<14} {status}")
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    return all_passed


def test_phased_coverage():
    """Test that 5 phases cover entire library with no gaps/overlaps."""
    
    total_games = 1000
    phases = []
    
    print("\n\nTesting 5-phase coverage (20% each):\n")
    print(f"{'Phase':<8} {'Offset':<10} {'Percentage':<12} {'Range':<15} {'Count'}")
    print("=" * 60)
    
    for i in range(5):
        offset = i * 20
        percentage = 20
        
        offset_count = int(total_games * (offset / 100))
        limit = int(total_games * (percentage / 100))
        
        start = offset_count
        end = min(offset_count + limit, total_games)
        count = end - start
        
        phases.append((start, end))
        
        print(f"Phase {i+1}  {offset:<10.0f} {percentage:<12.0f} {start}-{end:<10} {count}")
    
    # Verify coverage
    print("\n" + "=" * 60)
    
    # Check for gaps
    has_gaps = False
    for i in range(len(phases) - 1):
        if phases[i][1] != phases[i+1][0]:
            print(f"❌ GAP detected between Phase {i+1} and Phase {i+2}: {phases[i][1]} != {phases[i+1][0]}")
            has_gaps = True
    
    # Check for overlaps
    has_overlaps = False
    for i in range(len(phases) - 1):
        if phases[i][1] > phases[i+1][0]:
            print(f"❌ OVERLAP detected between Phase {i+1} and Phase {i+2}")
            has_overlaps = True
    
    # Check full coverage
    if phases[0][0] == 0 and phases[-1][1] == total_games:
        print(f"✅ Full coverage: 0-{total_games}")
    else:
        print(f"❌ Incomplete coverage: {phases[0][0]}-{phases[-1][1]} (expected 0-{total_games})")
    
    if not has_gaps and not has_overlaps and phases[0][0] == 0 and phases[-1][1] == total_games:
        print("✅ Perfect 5-phase coverage with no gaps or overlaps!")
        return True
    else:
        print("❌ Coverage issues detected!")
        return False


if __name__ == "__main__":
    test1_passed = test_offset_calculation()
    test2_passed = test_phased_coverage()
    
    print("\n" + "=" * 80)
    if test1_passed and test2_passed:
        print("🎉 All offset tests passed! Ready for phased builds!")
        exit(0)
    else:
        print("⚠️  Some tests failed - review implementation")
        exit(1)
