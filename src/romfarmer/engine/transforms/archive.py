"""Archive transform — compress a ROM to 7z or ZIP.

Extracted from ``romfarmer.stages.compress_archive.CompressArchiveStage``.
Uses the system ``7z`` binary for compression.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Mapping
from pathlib import Path

from .base import Transform, TransformError, pinned_env

# Determinism pins (IMPL_VERSIONS["7z"] == 2). Changing these requires a bump.
#   -mtm=off  do not store file modification times
#   -mmt=4    fixed thread count: LZMA2 block layout depends on it
_DETERMINISM_FLAGS = ("-mtm=off", "-mmt=4")


class ArchiveTransform:
    """Compress a ROM file to 7z or ZIP format.

    Recognised params:
        format:            ``"7z"`` (default) or ``"zip"``
        compression_level: ``"9"`` (default)
        method:            LZMA2 for 7z, Deflate for zip (defaults by format)
        sevenzip_path:     override path to 7z binary
    """

    name = "7z"

    def run(
        self,
        inputs: list[Path],
        params: Mapping[str, str],
        scratch: Path,
    ) -> list[Path]:
        if not inputs:
            raise TransformError("ArchiveTransform: no input files provided")

        input_file = inputs[0]
        fmt = params.get("format", "7z")
        level = params.get("compression_level", "9")
        tool = self._find_7z(params.get("sevenzip_path"))
        if tool is None:
            raise TransformError("7z not found; install p7zip or set sevenzip_path param")

        ext = ".7z" if fmt == "7z" else ".zip"
        output_path = scratch / (input_file.stem + ext)

        cmd = [
            str(tool),
            "a",
            f"-mx={level}",
            *_DETERMINISM_FLAGS,
            str(output_path),
            str(input_file),
        ]
        if fmt == "zip":
            cmd = [
                str(tool),
                "a",
                "-tzip",
                f"-mx={level}",
                *_DETERMINISM_FLAGS,
                str(output_path),
                str(input_file),
            ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=False, env=pinned_env())
        if result.returncode not in (0, 1):  # 7z returns 1 for warnings
            raise TransformError(f"7z failed for {input_file.name}: {result.stderr[:500]}")
        if not output_path.exists():
            raise TransformError(f"7z did not produce expected output {output_path}")
        return [output_path]

    @staticmethod
    def _find_7z(override: str | None) -> Path | None:
        if override:
            p = Path(override)
            return p if p.exists() else None
        for name in ("7z", "7zz", "7za"):
            found = shutil.which(name)
            if found:
                return Path(found)
        return None


_: Transform = ArchiveTransform()
