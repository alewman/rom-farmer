"""RVZ extract transform — extract .rvz from a ZIP archive.

Extracted from ``romfarmer.stages.unzip_rvz.UnzipRVZStage``.
RVZ is Dolphin's native compressed format; no conversion is needed.
"""

from __future__ import annotations

import zipfile
from collections.abc import Mapping
from pathlib import Path

from .base import Transform, TransformError


class RVZExtractTransform:
    """Extract ``.rvz`` files from a ZIP archive.

    Recognised params:
        (none currently; all .rvz members extracted)
    """

    name = "unzip-rvz"

    def run(
        self,
        inputs: list[Path],
        params: Mapping[str, str],
        scratch: Path,
    ) -> list[Path]:
        if not inputs:
            raise TransformError("RVZExtractTransform: no input files provided")

        zip_path = inputs[0]
        extracted: list[Path] = []

        with zipfile.ZipFile(zip_path, "r") as zf:
            members = [m for m in zf.namelist() if m.lower().endswith(".rvz")]
            if not members:
                raise TransformError(
                    f"No .rvz files found in {zip_path.name}"
                )
            for member in members:
                zf.extract(member, scratch)
                out = scratch / Path(member).name
                extracted.append(out)

        return extracted


_: Transform = RVZExtractTransform()
