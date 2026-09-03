"""PS3 decrypt transform — PS3Dec ISO decryption.

Extracted from ``romfarmer.stages.transform_ps3.TransformPS3Stage``.
Runs ``PS3Dec`` to decrypt an encrypted PS3 ISO using a ``.dkey`` file.
"""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
import zipfile
from collections.abc import Mapping
from pathlib import Path

from .base import Transform, TransformError, pinned_env

logger = logging.getLogger(__name__)

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
            raise TransformError("PS3DecTransform requires 2 inputs: [encrypted_iso, dkey_file]")

        iso_file, dkey_file = inputs[0], inputs[1]
        tool = self._find_tool(params.get("ps3dec_path"))
        if tool is None:
            raise TransformError("PS3Dec not found; install it or set ps3dec_path param")

        output_name = params.get("output_name", iso_file.stem + ".iso")
        output_path = scratch / output_name

        result = subprocess.run(
            [
                str(tool),
                "dec",
                "key",
                dkey_file.read_text().strip(),
                str(iso_file),
                str(output_path),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=3600,
            env=pinned_env(),
        )
        if result.returncode != 0:
            raise TransformError(f"PS3Dec failed for {iso_file.name}: {result.stderr[:500]}")
        if not output_path.exists():
            raise TransformError(f"PS3Dec did not produce expected output {output_path}")
        return [output_path]

    @staticmethod
    def _find_tool(override: str | None) -> Path | None:
        if override:
            p = Path(override).resolve()
            return p if p.exists() else None
        if _DEFAULT_TOOL.exists():
            return _DEFAULT_TOOL.resolve()
        for candidate in ("PS3Dec", "ps3dec"):
            found = shutil.which(candidate)
            if found:
                return Path(found).resolve()
        return None


_dec: Transform = PS3DecTransform()


class Ps3DkeyLookupTransform:
    """Locate a PS3 disc's ``.dkey`` in a Redump "Disc Keys TXT" zip.

    This is a zero-CAS-input action: the key is found purely from
    filesystem params (``keys_directory`` + ``stem``), the same pattern
    used by ``source_action`` for the original source file.

    Recognised params:
        keys_directory: directory containing ``<stem>.zip`` key archives
        stem: the disc's base name (source ZIP stem) used to find the key
    """

    name = "ps3-dkey-lookup"

    def run(
        self,
        inputs: list[Path],
        params: Mapping[str, str],
        scratch: Path,
    ) -> list[Path]:
        keys_dir = params.get("keys_directory")
        stem = params.get("stem")
        if not keys_dir or not stem:
            raise TransformError(
                "Ps3DkeyLookupTransform requires 'keys_directory' and 'stem' params"
            )

        keys_path = Path(keys_dir)
        key_zip = keys_path / f"{stem}.zip"
        if not key_zip.exists():
            # Redump disc-key archives sometimes omit revision markers that
            # appear in the Retool-filtered DAT name.
            base_stem = re.sub(r"\s*\(Rev \d+\)", "", stem)
            key_zip = keys_path / f"{base_stem}.zip"
        if not key_zip.exists():
            raise TransformError(f"No disc key found for '{stem}' in {keys_path}")

        with zipfile.ZipFile(key_zip, "r") as zf:
            dkey_names = [n for n in zf.namelist() if n.lower().endswith(".dkey")]
            if not dkey_names:
                raise TransformError(f"No .dkey member in {key_zip.name}")
            dkey_hex = zf.read(dkey_names[0]).decode("ascii").strip()

        if len(dkey_hex) != 32:
            raise TransformError(f"Invalid disc key length {len(dkey_hex)} in {key_zip.name}")

        out = scratch / f"{stem}.dkey"
        out.write_text(dkey_hex)
        return [out]


_dkey: Transform = Ps3DkeyLookupTransform()


class Ps3ExtractTreeTransform:
    """Extract a decrypted PS3 ISO into its JB folder (``PS3_GAME/`` tree).

    Expected inputs:
        inputs[0]: decrypted ISO file

    Output is a *directory* (kind ``"tree"``) — the Executor ingests it via
    the CAS tree store rather than as a single-file blob.
    """

    name = "ps3-extract-tree"

    def run(
        self,
        inputs: list[Path],
        params: Mapping[str, str],
        scratch: Path,
    ) -> list[Path]:
        if not inputs:
            raise TransformError("Ps3ExtractTreeTransform requires 1 input: [decrypted_iso]")

        iso_file = inputs[0]
        sevenzip = shutil.which("7z") or shutil.which("7zz") or shutil.which("7za")
        if sevenzip is None:
            raise TransformError("7z not found; required to extract PS3 ISO contents")

        extract_dir = scratch / "extract"
        extract_dir.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [sevenzip, "x", str(iso_file), f"-o{extract_dir}", "-y"],
            capture_output=True,
            text=True,
            check=False,
            timeout=3600,
            env=pinned_env(),
        )

        game_dirs = list(extract_dir.rglob("PS3_GAME"))
        if not game_dirs:
            raise TransformError(
                f"No PS3_GAME directory found after extracting {iso_file.name} "
                f"(7z exit {result.returncode}): {result.stderr[:500]}"
            )
        if result.returncode != 0:
            # PS3 discs are ISO9660+UDF hybrids; 7z frequently reports a
            # "Headers Error" / trailing-data warning on the UDF side even
            # though every file (including PS3_GAME/) extracted correctly.
            # Trust the PS3_GAME check above over the exit code here.
            logger.warning(
                "7z reported exit %d extracting %s but PS3_GAME/ was found "
                "— treating as a benign UDF header warning: %s",
                result.returncode,
                iso_file.name,
                result.stderr[:300],
            )

        return [game_dirs[0].parent]


_tree: Transform = Ps3ExtractTreeTransform()
