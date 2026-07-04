"""M3U transform — synthesise a multi-disc playlist file.

The ``m3u-create`` tool is declared by the disc lowering rule for
multi-disc CHD sets.  The playlist content comes entirely from
``params`` — the CHD inputs exist only to express DAG ordering and to
make the ActionKey depend on the disc contents (a changed disc must
re-create the playlist's cache entry).
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .base import Transform


class M3UTransform:
    """Write an ``.m3u`` playlist from ``params["entries"]``.

    Recognised params:
        entries: comma-separated CHD filenames, written one per line
        name:    output filename (default ``playlist.m3u``)
    """

    name = "m3u-create"

    def run(
        self,
        inputs: list[Path],
        params: Mapping[str, str],
        scratch: Path,
    ) -> list[Path]:
        entries = [e for e in params.get("entries", "").split(",") if e]
        out_name = params.get("name", "playlist.m3u")
        out_path = scratch / out_name
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(entries) + "\n", encoding="utf-8")
        return [out_path]


# Satisfy the Transform protocol at type-check time
_: Transform = M3UTransform()
