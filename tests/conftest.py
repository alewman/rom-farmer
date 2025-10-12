"""Test configuration and fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def sample_roms_dir(tmp_path: Path) -> Path:
    """Create directory with sample ROM files."""
    roms_dir = tmp_path / "roms"
    roms_dir.mkdir()
    
    # Create various test ROMs
    test_roms = [
        "Super Mario Bros. (USA).nes",
        "Legend of Zelda, The (USA, Europe).nes",
        "Final Fantasy (Japan) (En,Fr,De).nes",
        "Pokemon Red (USA, Europe) (Rev A).gb",
        "Tetris (World) (v1.1).gb",
        "Sonic the Hedgehog (USA, Europe) (Rev 1).gen",
        "Final Fantasy VII (USA) (Disc 1 of 3).bin",
        "Final Fantasy VII (USA) (Disc 2 of 3).bin",
        "Final Fantasy VII (USA) (Disc 3 of 3).bin",
    ]
    
    for rom in test_roms:
        (roms_dir / rom).touch()
    
    return roms_dir
