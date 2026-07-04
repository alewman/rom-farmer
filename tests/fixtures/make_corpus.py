"""Synthetic mini-collection corpus for parity and integration tests.

Generates tiny ZIP archives with known CRC32/MD5 values, fake CUE/BIN
disc images, and a minimal filesystem structure that the test harness
and migration tests can use without any copyrighted content.

Usage:
    corpus = make_corpus(root_dir)   # creates files under root_dir
    # corpus["psx"]["Fake Game (USA)"]["zip"]  → Path to the ZIP
    # corpus["psx"]["Fake Game (USA)"]["md5"]  → known MD5 of the bin
    # corpus["nes"]["Alpha (USA)"]["zip"]       → Path to the ZIP

All content is deterministic (seed-based) so tests are reproducible.
"""

from __future__ import annotations

import hashlib
import struct
import zipfile
import zlib
from pathlib import Path
from typing import TypedDict


class GameCorpus(TypedDict):
    zip: Path           # Path to source ZIP
    md5: str            # MD5 of the primary ROM/BIN file
    crc32: int          # CRC32 of the primary ROM/BIN file
    size: int           # uncompressed size of primary file
    member_name: str    # name of primary member inside the ZIP


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _make_rom_bytes(seed: bytes, size: int = 512) -> bytes:
    """Create deterministic pseudo-ROM bytes from *seed*."""
    h = hashlib.sha256(seed)
    data = bytearray()
    counter = 0
    while len(data) < size:
        data.extend(hashlib.sha256(h.digest() + counter.to_bytes(4, "little")).digest())
        counter += 1
    return bytes(data[:size])


def _make_zip(dest: Path, members: dict[str, bytes]) -> dict[str, tuple[int, int]]:
    """Create a ZIP at *dest* with *members*.

    Returns:
        {member_name: (crc32, uncompressed_size)}
    """
    identities: dict[str, tuple[int, int]] = {}
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, data in members.items():
            zf.writestr(name, data)
            identities[name] = (zlib.crc32(data) & 0xFFFFFFFF, len(data))
    return identities


def _md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


# ---------------------------------------------------------------------------
# Corpus factories
# ---------------------------------------------------------------------------

def _make_nes_game(root: Path, game_name: str, seed: str) -> GameCorpus:
    """One NES ROM inside a ZIP."""
    rom_bytes = _make_rom_bytes(seed.encode(), size=40_960)  # 40 KB fake ROM
    member = f"{game_name}.nes"
    zip_path = root / f"{game_name}.zip"
    identities = _make_zip(zip_path, {member: rom_bytes})
    crc32, size = identities[member]
    return GameCorpus(
        zip=zip_path,
        md5=_md5(rom_bytes),
        crc32=crc32,
        size=size,
        member_name=member,
    )


def _make_psx_game(root: Path, game_name: str, seed: str) -> GameCorpus:
    """Fake CUE/BIN disc image inside a ZIP."""
    bin_bytes = _make_rom_bytes(seed.encode(), size=2_097_152)  # 2 MB fake BIN
    cue_content = (
        f'FILE "{game_name}.bin" BINARY\n'
        f'  TRACK 01 MODE1/2352\n'
        f'    INDEX 01 00:00:00\n'
    ).encode()
    zip_path = root / f"{game_name}.zip"
    members = {
        f"{game_name}.bin": bin_bytes,
        f"{game_name}.cue": cue_content,
    }
    identities = _make_zip(zip_path, members)
    crc32, size = identities[f"{game_name}.bin"]
    return GameCorpus(
        zip=zip_path,
        md5=_md5(bin_bytes),
        crc32=crc32,
        size=size,
        member_name=f"{game_name}.bin",
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def make_corpus(root: Path) -> dict[str, dict[str, GameCorpus]]:
    """Create a deterministic synthetic corpus under *root*.

    Layout::

        root/
          nes/
            Alpha (USA).zip           NES ROM
            Beta (Japan).zip          NES ROM
          psx/
            Fake RPG (USA).zip        CUE+BIN disc image
            Fake RPG (USA) (Disc 2).zip

    Returns:
        Nested dict: {platform: {game_name: GameCorpus}}
    """
    nes_dir = root / "nes"
    psx_dir = root / "psx"
    nes_dir.mkdir(parents=True, exist_ok=True)
    psx_dir.mkdir(parents=True, exist_ok=True)

    corpus: dict[str, dict[str, GameCorpus]] = {
        "nes": {
            "Alpha (USA)": _make_nes_game(nes_dir, "Alpha (USA)", "nes:alpha"),
            "Beta (Japan)": _make_nes_game(nes_dir, "Beta (Japan)", "nes:beta"),
        },
        "psx": {
            "Fake RPG (USA)": _make_psx_game(psx_dir, "Fake RPG (USA)", "psx:rpg:d1"),
            "Fake RPG (USA) (Disc 2)": _make_psx_game(
                psx_dir, "Fake RPG (USA) (Disc 2)", "psx:rpg:d2"
            ),
        },
    }
    return corpus
