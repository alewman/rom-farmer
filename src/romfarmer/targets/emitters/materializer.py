"""Materializer — hardlink/copy files from a source set into the output tree.

This module ports the ``_link_or_copy`` helper from ``stages/organize.py``
and the organisation-style logic (flat, balanced, minimal, rich).

It is the only component that performs disk writes during EMIT.  All other
emitter components are pure (return data).
"""

from __future__ import annotations

import logging
import os
import re
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Low-level copy primitive
# ---------------------------------------------------------------------------

def link_or_copy(src: Path, dest: Path) -> None:
    """Hardlink *src* to *dest*, falling back to copy if cross-device.

    Ported from ``stages/organize.py::_link_or_copy``.  Hardlinks are
    preferred: they are instant and consume no additional disk space.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(src, dest)
    except OSError:
        shutil.copy2(src, dest)


# ---------------------------------------------------------------------------
# Organisation styles
# ---------------------------------------------------------------------------

def _first_letter(name: str) -> str:
    """Return the first letter of *name*, uppercased; digits become '0-9'."""
    stem = Path(name).stem
    ch = stem[0].upper() if stem else "0"
    return "0-9" if ch.isdigit() else ch


def _is_rom_file(path: Path) -> bool:
    """Return True for files that belong in the main ROM listing."""
    return path.suffix.lower() not in {".xml", ".jpg", ".png", ".mp4", ".txt"}


class Materializer:
    """Organises a flat list of files into the output directory.

    Organisation styles match the legacy ``OrganizationStyle`` values:
    - ``flat``      — all files directly in output_dir
    - ``balanced``  — letter subdirs (A/, B/, …, 0-9/) when > threshold
    - ``minimal``   — numeric subdirs only when count > threshold
    - ``rich``      — always use letter subdirs

    Args:
        style: Organisation style (default ``"flat"``).
        balanced_threshold: File count above which ``balanced`` adds subdirs
            (default 500).
    """

    _BALANCED_THRESHOLD = 500

    def __init__(
        self,
        style: str = "flat",
        balanced_threshold: int = _BALANCED_THRESHOLD,
    ) -> None:
        self._style = style.lower()
        self._threshold = balanced_threshold

    def emit(self, files: list[Path], output_dir: Path) -> list[Path]:
        """Place *files* into *output_dir* using the configured style.

        Returns the list of destination paths.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        if self._style == "rich":
            return self._emit_by_letter(files, output_dir)
        if self._style == "balanced" and len(files) > self._threshold:
            return self._emit_by_letter(files, output_dir)
        if self._style == "minimal" and len(files) > self._threshold:
            return self._emit_numeric(files, output_dir)
        return self._emit_flat(files, output_dir)

    # ------------------------------------------------------------------

    def _emit_flat(self, files: list[Path], dest_dir: Path) -> list[Path]:
        placed: list[Path] = []
        for src in files:
            dest = dest_dir / src.name
            if not dest.exists():
                link_or_copy(src, dest)
            placed.append(dest)
        return placed

    def _emit_by_letter(self, files: list[Path], dest_dir: Path) -> list[Path]:
        placed: list[Path] = []
        for src in files:
            subdir = dest_dir / _first_letter(src.name)
            dest = subdir / src.name
            if not dest.exists():
                link_or_copy(src, dest)
            placed.append(dest)
        return placed

    def _emit_numeric(self, files: list[Path], dest_dir: Path) -> list[Path]:
        """Group by first numeric block of the stem; fallback to flat."""
        placed: list[Path] = []
        for src in files:
            m = re.search(r"\d+", Path(src).stem)
            if m:
                prefix = str(int(m.group()) // 100 * 100)  # e.g. "0", "100", "200"
                subdir = dest_dir / prefix
            else:
                subdir = dest_dir
            dest = subdir / src.name
            if not dest.exists():
                link_or_copy(src, dest)
            placed.append(dest)
        return placed
