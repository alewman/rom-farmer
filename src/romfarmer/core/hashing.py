"""
Centralized ROM hashing utilities for metadata matching.

This module provides the canonical implementation of ROM hashing for use
throughout rom-farmer. The hashing strategy varies by system type:

ARCADE SYSTEMS (FBNeo, MAME, Naomi, Atomiswave, Model2, Model3, etc.):
    - Hash the ZIP/7z file itself (not the contents)
    - This matches ARRM's behavior for arcade ROMs
    - Arcade ROMs are multi-file archives that are hashed as a unit
    
DISC-BASED SYSTEMS (CHD, ISO, CUE/BIN, etc.):
    - Hash the file contents directly
    - For compressed disc images, hash the compressed file
    
CARTRIDGE-BASED SYSTEMS (NES, SNES, Genesis, etc.):
    - For uncompressed ROMs: hash the file contents
    - For ZIP/7z archives: extract largest file and hash its contents
    - This matches ARRM's behavior (it hashes the ROM inside the archive)

This matches the documented behavior in README.md under "ARRM Hashing Behavior".
"""

import hashlib
import zipfile
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum, auto
import py7zr


class HashingStrategy(Enum):
    """Strategy for hashing a ROM file."""
    
    # Hash the archive file itself (arcade systems)
    ARCHIVE_AS_FILE = auto()
    
    # Hash contents of the largest file inside archive
    ARCHIVE_CONTENTS = auto()
    
    # Hash the file directly
    DIRECT = auto()


@dataclass
class HashResult:
    """Result of hashing a ROM file."""
    
    md5: str
    sha1: Optional[str] = None
    crc32: Optional[str] = None
    strategy_used: HashingStrategy = HashingStrategy.DIRECT
    inner_filename: Optional[str] = None  # For archive contents, the file that was hashed


# Systems that hash the archive file itself (not contents)
# These are arcade/MAME-style systems where the ZIP contains multiple ROM chips
ARCADE_SYSTEMS = frozenset({
    # Core arcade
    "fbneo",
    "fba",  # Legacy name
    "finalburn",  # Legacy name
    "mame",
    "hbmame",
    
    # MAME-derived arcade platforms
    "naomi",
    "naomigd",
    "naomi2",
    "atomiswave",
    "triforce",
    "hikaru",
    "chihiro",
    "gaelco",
    "stv",  # Sega ST-V
    "model2",
    "model3",
    "system246",
    "taito_type_x",
    "lindbergh",
    "ringedge",
    "examu",
    
    # Neo Geo (arcade mode)
    "neogeo",
    "neogeocd",  # When using MAME/FBNeo
    
    # Other arcade
    "daphne",
    "singe",
})

# File extensions that are always hashed directly (never extract)
DIRECT_HASH_EXTENSIONS = frozenset({
    # Disc images
    ".chd",
    ".iso",
    ".cue",
    ".bin",
    ".img",
    ".mdf",
    ".nrg",
    ".gdi",
    ".cdi",
    ".rvz",
    ".wbfs",
    ".wia",
    ".gcz",
    ".ciso",
    ".wux",  # Wii U
    ".rpx",  # Wii U
    
    # Uncompressed ROMs
    ".nes",
    ".sfc",
    ".smc",
    ".gb",
    ".gbc",
    ".gba",
    ".nds",
    ".3ds",
    ".cia",
    ".n64",
    ".z64",
    ".v64",
    ".md",
    ".smd",
    ".gen",
    ".32x",
    ".gg",
    ".sms",
    ".sg",
    ".pce",
    ".ngp",
    ".ngc",
    ".ws",
    ".wsc",
    ".a26",
    ".a52",
    ".a78",
    ".lnx",
    ".jag",
    ".j64",
    ".vec",
    ".col",
    ".int",
    ".xex",
    ".atr",
    ".tap",
    ".tzx",
    ".dsk",
    ".d64",
    ".t64",
    ".crt",
    ".prg",
    ".vb",
    
    # Already "final form" compressed
    ".pbp",  # PSP EBOOT
    ".pkg",  # PS3/PSP packages
    ".nsz",  # Switch compressed
    ".nsp",  # Switch package
    ".xci",  # Switch cartridge
    ".vpk",  # PS Vita
})


def is_arcade_system(system_name: str) -> bool:
    """
    Check if a system uses arcade-style hashing (hash archive, not contents).
    
    Args:
        system_name: System identifier (e.g., 'fbneo', 'mame', 'naomi')
        
    Returns:
        True if this system hashes the archive file itself
    """
    if not system_name:
        return False
    return system_name.lower().strip() in ARCADE_SYSTEMS


def get_hashing_strategy(
    file_path: Path,
    system_name: Optional[str] = None,
) -> HashingStrategy:
    """
    Determine the appropriate hashing strategy for a file.
    
    Args:
        file_path: Path to the ROM file
        system_name: System identifier for context (optional)
        
    Returns:
        HashingStrategy indicating how to hash the file
    """
    suffix = file_path.suffix.lower()
    
    # Check for arcade systems first
    if system_name and is_arcade_system(system_name):
        # Arcade systems hash the archive file itself
        if suffix in (".zip", ".7z"):
            return HashingStrategy.ARCHIVE_AS_FILE
        # Non-archive arcade files (CHD companions) hash directly
        return HashingStrategy.DIRECT
    
    # Non-archive files always hash directly
    if suffix in DIRECT_HASH_EXTENSIONS:
        return HashingStrategy.DIRECT
    
    # Archives on non-arcade systems extract and hash contents
    if suffix in (".zip", ".7z"):
        return HashingStrategy.ARCHIVE_CONTENTS
    
    # Default to direct hashing
    return HashingStrategy.DIRECT


def calculate_md5(
    file_path: Path,
    system_name: Optional[str] = None,
    chunk_size: int = 8192,
) -> str:
    """
    Calculate MD5 hash of a ROM file using the appropriate strategy.
    
    This is the primary entry point for ROM hashing. It automatically
    determines the correct hashing strategy based on system type and
    file format.
    
    Args:
        file_path: Path to the ROM file
        system_name: System identifier for context (e.g., 'fbneo', 'nes')
        chunk_size: Size of chunks for reading large files
        
    Returns:
        MD5 hash as lowercase hex string
    """
    result = calculate_hash(file_path, system_name, include_sha1=False, chunk_size=chunk_size)
    return result.md5


def calculate_hash(
    file_path: Path,
    system_name: Optional[str] = None,
    include_sha1: bool = True,
    chunk_size: int = 8192,
) -> HashResult:
    """
    Calculate hash(es) of a ROM file using the appropriate strategy.
    
    This function determines the correct hashing approach based on:
    1. System type (arcade systems hash archive files)
    2. File extension (some files always hash directly)
    3. Archive format (ZIP vs 7z vs plain file)
    
    Args:
        file_path: Path to the ROM file
        system_name: System identifier for context (e.g., 'fbneo', 'nes')
        include_sha1: Whether to calculate SHA1 in addition to MD5
        chunk_size: Size of chunks for reading large files
        
    Returns:
        HashResult with MD5 (and optionally SHA1) hash
    """
    strategy = get_hashing_strategy(file_path, system_name)
    
    if strategy == HashingStrategy.ARCHIVE_AS_FILE:
        return _hash_file_direct(file_path, include_sha1, chunk_size, strategy)
    
    elif strategy == HashingStrategy.ARCHIVE_CONTENTS:
        suffix = file_path.suffix.lower()
        if suffix == ".zip":
            return _hash_zip_contents(file_path, include_sha1, chunk_size)
        elif suffix == ".7z":
            return _hash_7z_contents(file_path, include_sha1, chunk_size)
        # Fallback to direct if not recognized archive
        return _hash_file_direct(file_path, include_sha1, chunk_size, HashingStrategy.DIRECT)
    
    else:  # HashingStrategy.DIRECT
        return _hash_file_direct(file_path, include_sha1, chunk_size, strategy)


def _hash_file_direct(
    file_path: Path,
    include_sha1: bool,
    chunk_size: int,
    strategy: HashingStrategy,
) -> HashResult:
    """Hash a file directly (not extracting any contents)."""
    md5 = hashlib.md5()
    sha1 = hashlib.sha1() if include_sha1 else None
    
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            md5.update(chunk)
            if sha1:
                sha1.update(chunk)
    
    return HashResult(
        md5=md5.hexdigest(),
        sha1=sha1.hexdigest() if sha1 else None,
        strategy_used=strategy,
    )


def _hash_zip_contents(
    zip_path: Path,
    include_sha1: bool,
    chunk_size: int,
) -> HashResult:
    """Extract and hash the largest file inside a ZIP archive."""
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            # Get list of files (not directories)
            files = [f for f in zf.namelist() if not f.endswith("/")]
            
            if not files:
                # Empty archive - hash the file itself
                return _hash_file_direct(
                    zip_path, include_sha1, chunk_size, HashingStrategy.ARCHIVE_AS_FILE
                )
            
            # Find the largest file (most likely the actual ROM)
            largest_file = max(files, key=lambda f: zf.getinfo(f).file_size)
            
            # Read and hash
            rom_data = zf.read(largest_file)
            md5 = hashlib.md5(rom_data).hexdigest()
            sha1 = hashlib.sha1(rom_data).hexdigest() if include_sha1 else None
            
            return HashResult(
                md5=md5,
                sha1=sha1,
                strategy_used=HashingStrategy.ARCHIVE_CONTENTS,
                inner_filename=largest_file,
            )
            
    except (zipfile.BadZipFile, IOError):
        # Corrupted or invalid archive - hash file itself
        return _hash_file_direct(
            zip_path, include_sha1, chunk_size, HashingStrategy.ARCHIVE_AS_FILE
        )


def _hash_7z_contents(
    archive_path: Path,
    include_sha1: bool,
    chunk_size: int,
) -> HashResult:
    """Extract and hash the largest file inside a 7z archive."""
    try:
        with py7zr.SevenZipFile(archive_path, mode="r") as zf:
            # Get file info
            file_infos = [(f.filename, f.uncompressed) for f in zf.list() if not f.is_directory]
            
            if not file_infos:
                # Empty archive - hash the file itself
                return _hash_file_direct(
                    archive_path, include_sha1, chunk_size, HashingStrategy.ARCHIVE_AS_FILE
                )
            
            # Find the largest file
            largest_file = max(file_infos, key=lambda x: x[1])[0]
            
            # Extract and read
            extracted = zf.read([largest_file])
            rom_data = extracted[largest_file].read()
            
            md5 = hashlib.md5(rom_data).hexdigest()
            sha1 = hashlib.sha1(rom_data).hexdigest() if include_sha1 else None
            
            return HashResult(
                md5=md5,
                sha1=sha1,
                strategy_used=HashingStrategy.ARCHIVE_CONTENTS,
                inner_filename=largest_file,
            )
            
    except Exception:
        # Any error - fallback to direct hash
        return _hash_file_direct(
            archive_path, include_sha1, chunk_size, HashingStrategy.ARCHIVE_AS_FILE
        )


def hash_for_metadata_lookup(
    file_path: Path,
    system_name: Optional[str] = None,
) -> str:
    """
    Get the MD5 hash for metadata database lookup.
    
    This is a convenience function that's semantically clear about
    the purpose - matching against the metadata database.
    
    Args:
        file_path: Path to the ROM file
        system_name: System identifier for context
        
    Returns:
        MD5 hash suitable for database lookup
    """
    return calculate_md5(file_path, system_name)


def detect_system_from_path(file_path: Path) -> Optional[str]:
    """
    Attempt to detect the system from a file path.
    
    Looks for common system folder names in the path hierarchy.
    This is a heuristic fallback when system name isn't provided.
    
    Args:
        file_path: Path to analyze
        
    Returns:
        Detected system name or None
    """
    path_lower = str(file_path).lower()
    
    # Check each arcade system
    for system in ARCADE_SYSTEMS:
        if f"/{system}/" in path_lower or f"\\{system}\\" in path_lower:
            return system
        if path_lower.endswith(f"/{system}") or path_lower.endswith(f"\\{system}"):
            return system
    
    return None


def calculate_md5_with_auto_detect(file_path: Path) -> str:
    """
    Calculate MD5 with automatic system detection from path.
    
    Use this when the system isn't known but might be inferrable
    from the file path (e.g., /roms/fbneo/kinst.zip).
    
    Args:
        file_path: Path to the ROM file
        
    Returns:
        MD5 hash as lowercase hex string
    """
    system = detect_system_from_path(file_path)
    return calculate_md5(file_path, system)
