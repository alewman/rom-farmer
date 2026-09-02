"""CHD transform — chdman CD/DVD compression.

Extracted from ``romfarmer.stages.compress.CompressCHDStage``.
Supports ``createcd`` (CUE/BIN disc images) and ``createdvd`` (ISO/DVD).
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Mapping
from pathlib import Path

from .base import Transform, TransformError


class CHDTransform:
    """Compress a disc image (CUE/BIN or ISO) to CHD via chdman.

    Recognised params:
        mode: ``"createcd"`` (default) or ``"createdvd"``
        compression: chdman codec, e.g. ``"lzma"`` (default for createdvd)
        chdman_path: override path to chdman binary
    """

    name = "chdman"

    def run(
        self,
        inputs: list[Path],
        params: Mapping[str, str],
        scratch: Path,
    ) -> list[Path]:
        if not inputs:
            raise TransformError("CHDTransform: no input files provided")

        input_file = inputs[0]
        mode = params.get("mode", "createcd")
        chdman = self._find_chdman(params.get("chdman_path"))
        if chdman is None:
            raise TransformError("chdman not found; install it or set chdman_path param")

        output_name = input_file.stem + ".chd"
        output_path = scratch / output_name

        cmd = [str(chdman), mode, "-i", str(input_file), "-o", str(output_path)]
        if mode == "createdvd" and "compression" in params:
            cmd += ["-c", params["compression"]]

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise TransformError(
                f"chdman {mode} failed for {input_file.name}: {result.stderr[:500]}"
            )
        if not output_path.exists():
            raise TransformError(f"chdman did not produce expected output {output_path}")
        return [output_path]

    @staticmethod
    def _find_chdman(override: str | None) -> Path | None:
        if override:
            p = Path(override)
            return p if p.exists() else None
        workspace_bin = Path("tools/bin/chdman")
        if workspace_bin.exists():
            return workspace_bin
        found = shutil.which("chdman")
        return Path(found) if found else None


# Satisfy the Transform protocol at type-check time
_: Transform = CHDTransform()
