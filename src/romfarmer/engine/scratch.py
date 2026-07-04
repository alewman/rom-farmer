"""Scratch directory lifecycle for per-unit work areas.

Each :class:`ScratchDir` context manager creates a temporary directory,
yields it to the caller, and deletes it on exit — regardless of whether
the unit succeeded or failed.  The peak-disk cap from the legacy pipeline
is preserved via the optional *peak_cap* argument (enforcement is the
caller's responsibility; ``ScratchDir`` only deletes the directory on
exit, it does not enforce limits mid-run).
"""

from __future__ import annotations

import shutil
from pathlib import Path
from types import TracebackType


class ScratchDir:
    """Context manager for a per-unit scratch directory.

    Example::

        with ScratchDir(base, unit_id) as scratch:
            output = transform.run(inputs, params, scratch)
    """

    def __init__(
        self,
        base_dir: Path,
        unit_id: str,
        *,
        peak_cap: int | None = None,
    ) -> None:
        """
        Args:
            base_dir:  Parent directory under which the scratch dir is created.
            unit_id:   Stable identifier (e.g. ``unit.unit_id``) used to name
                       the scratch dir.  Sanitized to be filesystem-safe.
            peak_cap:  Soft maximum bytes allowed in ``base_dir`` while this
                       scratch dir exists.  Not enforced by ``ScratchDir``
                       itself — intended for callers to check before invoking
                       transforms.
        """
        safe_id = unit_id[:64].replace("/", "_").replace("\x00", "_")
        self.path: Path = base_dir / f"scratch_{safe_id}"
        self.peak_cap = peak_cap
        self._entered = False

    def __enter__(self) -> Path:
        self.path.mkdir(parents=True, exist_ok=True)
        self._entered = True
        return self.path

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._entered:
            shutil.rmtree(self.path, ignore_errors=True)
