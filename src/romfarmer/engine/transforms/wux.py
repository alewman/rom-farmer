"""WUX extract transform — extract .wux from a ZIP archive.

Extracted from ``romfarmer.stages.unzip_wux.UnzipWUXStage``.
WUX is a compressed Wii U disc image used directly by Cemu.
"""

from __future__ import annotations

import zipfile
from collections.abc import Mapping
from pathlib import Path

from .base import Transform, TransformError


class WUXExtractTransform:
    """Extract ``.wux`` files from a ZIP archive.

    Recognised params:
        (none currently; all .wux members extracted)
    """

    name = "unzip-wux"

    def run(
        self,
        inputs: list[Path],
        params: Mapping[str, str],
        scratch: Path,
    ) -> list[Path]:
        if not inputs:
            raise TransformError("WUXExtractTransform: no input files provided")

        zip_path = inputs[0]
        extracted: list[Path] = []

        with zipfile.ZipFile(zip_path, "r") as zf:
            members = [m for m in zf.namelist() if m.lower().endswith(".wux")]
            if not members:
                raise TransformError(
                    f"No .wux files found in {zip_path.name}"
                )
            for member in members:
                zf.extract(member, scratch)
                out = scratch / Path(member).name
                extracted.append(out)

        return extracted


_: Transform = WUXExtractTransform()
