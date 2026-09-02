"""XISO transform — extract-xiso rewrite mode.

Extracted from ``romfarmer.stages.convert_xiso.ConvertXISOStage``.
Converts a Redump ISO to XISO format (game partition only) using
``extract-xiso -r``.  The source file is modified in-place; the
original is renamed to ``.iso.old`` by extract-xiso and removed here.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Mapping
from pathlib import Path

from .base import Transform, TransformError

_DEFAULT_TOOL = Path("tools/bin/extract-xiso")


class XisoTransform:
    """Rewrite a Redump ISO to XISO format via ``extract-xiso -r``.

    Recognised params:
        extract_xiso_path: override path to the extract-xiso binary
    """

    name = "extract-xiso"

    def run(
        self,
        inputs: list[Path],
        params: Mapping[str, str],
        scratch: Path,
    ) -> list[Path]:
        if not inputs:
            raise TransformError("XisoTransform: no input files provided")

        source = inputs[0]
        # extract-xiso -r modifies in place; copy to scratch first so the
        # original CAS blob is not touched.
        work_iso = scratch / source.name
        shutil.copy2(source, work_iso)

        tool = self._find_tool(params.get("extract_xiso_path"))
        if tool is None:
            raise TransformError(
                "extract-xiso not found; install it or set extract_xiso_path param"
            )

        result = subprocess.run(
            [str(tool), "-r", work_iso.name],
            capture_output=True,
            text=True,
            check=False,
            cwd=scratch,
            timeout=600,
        )
        if result.returncode != 0:
            raise TransformError(f"extract-xiso failed for {source.name}: {result.stderr[:500]}")

        # extract-xiso renames original to .iso.old; clean up
        old = work_iso.with_suffix(".iso.old")
        if old.exists():
            old.unlink()

        if not work_iso.exists():
            raise TransformError(f"extract-xiso did not produce expected output {work_iso}")
        return [work_iso]

    @staticmethod
    def _find_tool(override: str | None) -> Path | None:
        if override:
            p = Path(override)
            return p if p.exists() else None
        if _DEFAULT_TOOL.exists():
            return _DEFAULT_TOOL
        found = shutil.which("extract-xiso")
        return Path(found) if found else None


_: Transform = XisoTransform()
