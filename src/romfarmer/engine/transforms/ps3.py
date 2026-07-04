"""PS3 decrypt transform — PS3Dec ISO decryption.

Extracted from ``romfarmer.stages.transform_ps3.TransformPS3Stage``.
Runs ``PS3Dec`` to decrypt an encrypted PS3 ISO using a ``.dkey`` file.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Mapping
from pathlib import Path

from .base import Transform, TransformError

_DEFAULT_TOOL = Path("tools/bin/ps3dec")


class PS3DecTransform:
    """Decrypt a PS3 ISO using PS3Dec.

    Expected inputs:
        inputs[0]: encrypted ISO file
        inputs[1]: .dkey file

    Recognised params:
        ps3dec_path: override path to PS3Dec binary
        output_name: explicit output filename (default: same stem + .iso)
    """

    name = "ps3dec"

    def run(
        self,
        inputs: list[Path],
        params: Mapping[str, str],
        scratch: Path,
    ) -> list[Path]:
        if len(inputs) < 2:
            raise TransformError(
                "PS3DecTransform requires 2 inputs: [encrypted_iso, dkey_file]"
            )

        iso_file, dkey_file = inputs[0], inputs[1]
        tool = self._find_tool(params.get("ps3dec_path"))
        if tool is None:
            raise TransformError(
                "PS3Dec not found; install it or set ps3dec_path param"
            )

        output_name = params.get("output_name", iso_file.stem + ".iso")
        output_path = scratch / output_name

        result = subprocess.run(
            [str(tool), "dec", "key", dkey_file.read_text().strip(), str(iso_file), str(output_path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=3600,
        )
        if result.returncode != 0:
            raise TransformError(
                f"PS3Dec failed for {iso_file.name}: {result.stderr[:500]}"
            )
        if not output_path.exists():
            raise TransformError(
                f"PS3Dec did not produce expected output {output_path}"
            )
        return [output_path]

    @staticmethod
    def _find_tool(override: str | None) -> Path | None:
        if override:
            p = Path(override)
            return p if p.exists() else None
        if _DEFAULT_TOOL.exists():
            return _DEFAULT_TOOL
        for candidate in ("PS3Dec", "ps3dec"):
            found = shutil.which(candidate)
            if found:
                return Path(found)
        return None


_: Transform = PS3DecTransform()
