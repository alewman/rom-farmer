#!/usr/bin/env python3
"""
Patch gamelist.xml to include subfolder game entries.

For each platform directory, reads the existing gamelist.xml, builds a filename
→ game element map, then walks all game subdirectories. For each ROM file found
in a subdir, if the same filename exists in the root gamelist, clones that entry
with the new relative path and appends it to the gamelist.

This is O(n) over filesystem entries with no hashing — safe for CHD/RVZ/ISO platforms.

Usage:
    python patch_gamelist_subdirs.py /path/to/roms-retrobat/3do
    python patch_gamelist_subdirs.py /path/to/roms-retrobat  # all platforms
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import copy

ROM_EXTENSIONS = {
    ".7z", ".zip",                         # compressed cartridge
    ".chd", ".m3u", ".iso", ".cso",        # disc
    ".rvz", ".wua",                         # GameCube/Wii
    ".j64", ".n64", ".z64", ".v64",        # N64
    ".gb", ".gbc", ".gba",                 # Game Boy
    ".nes", ".sfc", ".smc",                # NES/SNES
    ".smd", ".gen", ".bin", ".32x",        # Sega
    ".vb",                                 # Virtual Boy
    ".nds", ".3ds",                        # DS
    ".ws", ".wsc",                         # WonderSwan
    ".pce", ".sgx",                        # PC Engine
    ".a26", ".a52", ".a78",               # Atari
    ".lnx", ".lyx",                        # Lynx
    ".col",                                # ColecoVision
    ".int",                                # Intellivision
    ".vec",                                # Vectrex
    ".ngp", ".ngc",                        # Neo Geo Pocket
    ".sg",                                 # SG-1000
    ".gg",                                 # Game Gear
    ".sms",                                # Master System
    ".fds",                                # Famicom Disk System
    ".mx1", ".mx2", ".rom",               # MSX
    ".xbe", ".iso",                        # Xbox
}

# Subdirectory names that are never game dirs
SKIP_DIRS = {"media", "saves", "states", "screenshots", "cheats", "patches"}

# Platforms where each game IS a directory (skip rglob walk entirely)
FOLDER_FORMAT_PLATFORMS = {"ps3"}


def is_folder_format_platform(platform_dir: Path) -> bool:
    """True if the platform stores games as directories (e.g. PS3 .ps3 folders)."""
    return platform_dir.name.lower() in FOLDER_FORMAT_PLATFORMS


def patch_platform(platform_dir: Path, dry_run: bool = False) -> dict:
    """Patch gamelist.xml for a single platform directory.

    Returns stats dict.
    """
    gamelist_path = platform_dir / "gamelist.xml"
    if not gamelist_path.exists():
        return {"platform": platform_dir.name, "status": "no gamelist", "added": 0}

    # Skip folder-format platforms (PS3 etc.) — game dirs are not curation subdirs
    if is_folder_format_platform(platform_dir):
        return {"platform": platform_dir.name, "status": "skipped (folder format)", "added": 0}

    tree = ET.parse(gamelist_path)
    root = tree.getroot()

    # Build filename → game element map from existing root-level entries
    filename_to_elem: dict[str, ET.Element] = {}
    for game in root.findall("game"):
        path_elem = game.find("path")
        if path_elem is None:
            continue
        path_str = path_elem.text or ""
        # Only include root-level entries (no slash after ./)
        rel = path_str.lstrip("./")
        if "/" not in rel:
            filename_to_elem[rel] = game

    if not filename_to_elem:
        return {"platform": platform_dir.name, "status": "no root entries", "added": 0}

    # Collect existing paths to avoid duplicates
    existing_paths: set[str] = set()
    for game in root.findall("game"):
        path_elem = game.find("path")
        if path_elem is not None and path_elem.text:
            existing_paths.add(path_elem.text)

    added = 0
    skipped_no_match = 0

    # Walk game subdirectories
    for subdir in sorted(platform_dir.iterdir()):
        if not subdir.is_dir():
            continue
        if subdir.name.lower() in SKIP_DIRS:
            continue

        # Walk recursively inside the subdir (no sort — avoid loading huge lists)
        for rom_file in subdir.rglob("*"):
            if rom_file.suffix.lower() not in ROM_EXTENSIONS:
                continue
            if not rom_file.is_file():
                continue

            rel_path = f"./{rom_file.relative_to(platform_dir)}"

            # Skip if already in gamelist
            if rel_path in existing_paths:
                continue

            # Find matching root entry by filename
            filename = rom_file.name
            source_elem = filename_to_elem.get(filename)
            if source_elem is None:
                skipped_no_match += 1
                continue

            # Clone the element with the new path
            new_elem = copy.deepcopy(source_elem)
            new_path = new_elem.find("path")
            if new_path is not None:
                new_path.text = rel_path

            root.append(new_elem)
            existing_paths.add(rel_path)
            added += 1

    if added > 0 and not dry_run:
        ET.indent(tree, space="  ")
        tree.write(gamelist_path, encoding="utf-8", xml_declaration=True)

    return {
        "platform": platform_dir.name,
        "status": "ok",
        "added": added,
        "no_match": skipped_no_match,
        "root_entries": len(filename_to_elem),
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: patch_gamelist_subdirs.py <platform_dir|roms_base_dir>")
        sys.exit(1)

    target = Path(sys.argv[1])
    dry_run = "--dry-run" in sys.argv

    # If target contains a gamelist.xml, it's a single platform dir
    if (target / "gamelist.xml").exists():
        platforms = [target]
    else:
        # Treat as parent dir containing platform subdirs
        platforms = sorted(
            d for d in target.iterdir() if d.is_dir() and (d / "gamelist.xml").exists()
        )

    total_added = 0
    for platform_dir in platforms:
        stats = patch_platform(platform_dir, dry_run=dry_run)
        status = stats.get("status", "?")
        added = stats.get("added", 0)
        no_match = stats.get("no_match", 0)
        root = stats.get("root_entries", 0)

        if added > 0:
            print(f"  {stats['platform']:20s}  +{added:4d} entries  ({root} root, {no_match} unmatched)")
            total_added += added
        elif status == "ok":
            print(f"  {stats['platform']:20s}  (no new entries needed)")
        else:
            print(f"  {stats['platform']:20s}  [{status}]")

    print(f"\nTotal new gamelist entries added: {total_added}")
    if dry_run:
        print("[DRY RUN — no files written]")


if __name__ == "__main__":
    main()
