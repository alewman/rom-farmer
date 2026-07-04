"""Generic unzip transform — extract files from a ZIP archive.

Used for cartridge ROMs and other platforms where the source is a ZIP
containing one or more ROM files.
"""

from __future__ import annotations

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
                e.strip().lower().lstrip(".")
                for e in params["extension_filter"].split(",")
            }

        extracted: list[Path] = []

        with zipfile.ZipFile(zip_path, "r") as zf:
            members = [
                m for m in zf.namelist()
                if not m.endswith("/")
            ]
            if ext_filter is not None:
                members = [
                    m for m in members
                    if Path(m).suffix.lower().lstrip(".") in ext_filter
                ]
            if not members:
                raise TransformError(
                    f"No matching files found in {zip_path.name}"
                )
            for member in members:
                zf.extract(member, scratch)
                out = scratch / Path(member).name
                extracted.append(out)

        return extracted


_: Transform = UnzipTransform()
