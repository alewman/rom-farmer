"""SquashFS transform — mksquashfs compression.

Used as the optional second step of the Xbox chain
(``("xiso", "squashfs")``) for Xbox-on-Linux targets.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Mapping
from pathlib import Path

from .base import Transform, TransformError


class SquashFSTransform:
    """Compress ``inputs[0]`` into a ``.squashfs`` image via mksquashfs.

    Recognised params:
        compression:     mksquashfs codec (default ``"lz4"``)
        mksquashfs_path: override path to the mksquashfs binary
    """

    name = "mksquashfs"

    def run(
        self,
        inputs: list[Path],
        params: Mapping[str, str],
        scratch: Path,
    ) -> list[Path]:
        if not inputs:
            raise TransformError("SquashFSTransform: no input files provided")

        input_file = inputs[0]
        tool = self._find_tool(params.get("mksquashfs_path"))
        if tool is None:
            raise TransformError(
                "mksquashfs not found; install squashfs-tools or set mksquashfs_path param"
            )

        output_path = scratch / (input_file.stem + ".squashfs")
        cmd = [
            str(tool),
            str(input_file),
            str(output_path),
            "-comp",
            params.get("compression", "lz4"),
            "-noappend",
            "-quiet",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise TransformError(f"mksquashfs failed for {input_file.name}: {result.stderr[:500]}")
        if not output_path.exists():
            raise TransformError(f"mksquashfs did not produce expected output {output_path}")
        return [output_path]

    @staticmethod
    def _find_tool(override: str | None) -> Path | None:
        if override:
            p = Path(override)
            return p if p.exists() else None
        found = shutil.which("mksquashfs")
        return Path(found) if found else None


# Satisfy the Transform protocol at type-check time
_: Transform = SquashFSTransform()
