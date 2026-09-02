"""CHD transform — chdman CD/DVD compression.

Supports ``createcd`` (CUE/BIN, GDI) and ``createdvd`` (ISO).  The input may
be the disc image itself or a ZIP containing it (Redump/Myrient layout); a ZIP
is extracted into a private directory so multi-track BIN files stay next to
their CUE without ever entering the CAS as intermediates.
"""

from __future__ import annotations

import shutil
import subprocess
import zipfile
from collections.abc import Mapping
from pathlib import Path

from .base import Transform, TransformError, pinned_env

_SHEET_PRIORITY = (".cue", ".gdi", ".toc", ".iso")


def _pick_disc_image(files: list[Path]) -> Path:
    for ext in _SHEET_PRIORITY:
        for f in files:
            if f.suffix.lower() == ext:
                return f
    return max(files, key=lambda f: f.stat().st_size)


class CHDTransform:
    """Compress a disc image (CUE/BIN, GDI or ISO — loose or zipped) to CHD.

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

        if zipfile.is_zipfile(input_file):
            extract_dir = scratch / f"{input_file.stem}.extracted"
            extract_dir.mkdir(exist_ok=True)
            with zipfile.ZipFile(input_file) as zf:
                members = [m for m in zf.namelist() if not m.endswith("/")]
                if not members:
                    raise TransformError(f"{input_file.name} is an empty archive")
                zf.extractall(extract_dir)
            input_file = _pick_disc_image([extract_dir / m for m in members])

        cmd = [str(chdman), mode, "-i", str(input_file), "-o", str(output_path)]
        if mode == "createdvd" and "compression" in params:
            cmd += ["-c", params["compression"]]

        result = subprocess.run(cmd, capture_output=True, text=True, check=False, env=pinned_env())
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
            p = Path(override).resolve()
            return p if p.exists() else None
        workspace_bin = Path("tools/bin/chdman")
        if workspace_bin.exists():
            return workspace_bin.resolve()
        found = shutil.which("chdman")
        return Path(found).resolve() if found else None


# Satisfy the Transform protocol at type-check time
_: Transform = CHDTransform()
