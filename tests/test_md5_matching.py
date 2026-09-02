#!/usr/bin/env python3
"""
Quick test: Verify MD5-based DAT matching logic

This script tests the core MD5 matching logic without requiring
a full PS3 collection or ARRM database.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console

from romfarmer.dat_parser import DATFile, DATGame, DATRom, ROMMatcher


def create_test_dat():
    """Create a test DAT with known MD5 hashes."""
    games = [
        DATGame(
            name="Dragon Age II (USA)",  # Old name
            roms=[
                DATRom(
                    name="Dragon Age II (USA).iso",
                    size=4_000_000_000,
                    crc="12345678",
                    md5="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",  # Fake MD5
                    sha1="1234567890abcdef1234567890abcdef12345678",
                )
            ],
        ),
        DATGame(
            name="Fallout 3 (USA)",  # Old name
            roms=[
                DATRom(
                    name="Fallout 3 (USA).iso",
                    size=5_000_000_000,
                    crc="87654321",
                    md5="f1e2d3c4b5a6f1e2d3c4b5a6f1e2d3c4",  # Fake MD5
                    sha1="fedcba0987654321fedcba0987654321fedcba09",
                )
            ],
        ),
        DATGame(
            name="Uncharted 2 (USA)",  # Old name
            roms=[
                DATRom(
                    name="Uncharted 2 (USA).iso",
                    size=6_000_000_000,
                    crc="abcdef01",
                    md5="1a2b3c4d5e6f1a2b3c4d5e6f1a2b3c4d",  # Fake MD5
                    sha1="0123456789abcdef0123456789abcdef01234567",
                )
            ],
        ),
    ]

    dat_file = DATFile(
        name="Redump - PlayStation 3 (Old)",
        description="Test DAT with old naming",
        version="2024-10-01",
        games=games,
    )

    return dat_file


def test_md5_matching():
    """Test MD5 matching with renamed files."""
    console = Console()
    console.print("[bold cyan]Testing MD5-Based DAT Matching[/bold cyan]\n")

    # Create test DAT
    dat_file = create_test_dat()
    matcher = ROMMatcher(dat_file)

    console.print(f"DAT file: {dat_file.name}")
    console.print(f"Games: {len(dat_file.games)}\n")

    # Test cases: Simulate renamed files
    test_files = [
        {
            "filename": "Dragon Age II (USA, Asia).zip",  # New name (renamed)
            "md5": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",  # Same MD5 as old file
            "expected": "md5_match",
        },
        {
            "filename": "Fallout 3 (USA, Canada).zip",  # New name (renamed)
            "md5": "f1e2d3c4b5a6f1e2d3c4b5a6f1e2d3c4",  # Same MD5 as old file
            "expected": "md5_match",
        },
        {
            "filename": "Uncharted 2 - Among Thieves (USA).zip",  # New name (renamed)
            "md5": "1a2b3c4d5e6f1a2b3c4d5e6f1a2b3c4d",  # Same MD5 as old file
            "expected": "md5_match",
        },
        {
            "filename": "New Game (USA).zip",  # Totally new file
            "md5": "9999999999999999999999999999999",  # Unknown MD5
            "expected": "no_match",
        },
    ]

    console.print("[bold]Test Results:[/bold]\n")

    passed = 0
    failed = 0

    for test in test_files:
        file_path = Path(test["filename"])
        md5 = test["md5"]
        expected = test["expected"]

        # Test MD5 matching
        result = matcher.match_by_hash(file_path, md5=md5)

        # Check result
        match_type = result.match_type.value if result.match_type else "NO_MATCH"
        matched = result.is_matched()

        if match_type == expected:
            console.print(f"[green]✓[/green] {file_path.name}")
            console.print(f"    Match type: {match_type}")
            if matched and result.dat_game:
                console.print(f"    Matched to: {result.dat_game.name}")
            console.print()
            passed += 1
        else:
            console.print(f"[red]✗[/red] {file_path.name}")
            console.print(f"    Expected: {expected}")
            console.print(f"    Got: {match_type}")
            console.print()
            failed += 1

    # Summary
    console.print("[bold]Summary:[/bold]")
    console.print(f"  [green]Passed: {passed}[/green]")
    console.print(f"  [red]Failed: {failed}[/red]")

    # Explanation
    console.print("\n[bold cyan]How It Works:[/bold cyan]")
    console.print("1. DAT contains old game names with MD5 hashes")
    console.print("2. Files have been renamed (new region tags, title changes)")
    console.print("3. MD5 matching finds games by hash, ignoring filename")
    console.print("4. Result: Renamed files still match correctly!")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(test_md5_matching())
