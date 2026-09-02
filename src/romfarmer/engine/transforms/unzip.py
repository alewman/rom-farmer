"""Generic unzip transform — extract files from a ZIP archive.

Used for cartridge ROMs and other platforms where the source is a ZIP
containing one or more ROM files.
"""

from __future__ import annotations

import shutil
import zipfile
from collections.abc import Mapping
from pathlib import Path

from .base import Transform, TransformError


class UnzipTransform:
    """Extract all non-directory members from a ZIP archive.

    Recognised params:
        extension_filter: comma-separated list of extensions to keep,
                          e.g. ``"nes,sfc"`` (default: all members)
    """

    name = "unzip"

    def run(
        self,
        inputs: list[Path],
        params: Mapping[str, str],
        scratch: Path,
    ) -> list[Path]:
        if not inputs:
            raise TransformError("UnzipTransform: no input files provided")

        zip_path = inputs[0]
        ext_filter: set[str] | None = None
        if "extension_filter" in params:
            ext_filter = {
                e.strip().lower().lstrip(".") for e in params["extension_filter"].split(",")
            }

        extracted: list[Path] = []

        with zipfile.ZipFile(zip_path, "r") as zf:
            infos = [m for m in zf.infolist() if not m.filename.endswith("/")]
            if ext_filter is not None:
                infos = [
                    m for m in infos if Path(m.filename).suffix.lower().lstrip(".") in ext_filter
                ]
            if not infos:
                raise TransformError(f"No matching files found in {zip_path.name}")
            # Output index 0 is the "dominant member" (same rule as ZipIdentity):
            # the cue/gdi sheet for disc images, otherwise the largest file.
            infos.sort(
                key=lambda m: (
                    Path(m.filename).suffix.lower() not in (".cue", ".gdi"),
                    -m.file_size,
                    m.filename,
                )
            )
            for info in infos:
                target = scratch / Path(info.filename).name
                with zf.open(info) as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
                extracted.append(target)

        return extracted


_: Transform = UnzipTransform()
