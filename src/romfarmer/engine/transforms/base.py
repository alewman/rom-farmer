"""Transform protocol — the cache-unaware tool-invocation interface.

A :class:`Transform` knows nothing about :class:`StageContext`, caches,
databases, or the IR.  It takes a list of input files, a parameter mapping,
and a scratch directory; it returns a list of output files (inside *scratch*
or elsewhere).  The :class:`~romfarmer.engine.executor.Executor` handles
caching, CAS ingestion, and identity tracking.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Protocol, runtime_checkable


class TransformError(Exception):
    """Raised when a Transform fails to produce its expected outputs."""


@runtime_checkable
class Transform(Protocol):
    """Protocol for all tool-invocation cores.

    Implementations:
      - Must be **cache-unaware** and **context-unaware**.
      - Must write outputs inside *scratch* (or return absolute paths).
      - Must raise :class:`TransformError` on non-zero tool exit codes.
      - May raise standard :mod:`subprocess` / :mod:`os` exceptions for
        lower-level failures.
    """

    name: str
    """Stable identifier used as the ``tool`` field in :class:`ActionKey`."""

    def run(
        self,
        inputs: list[Path],
        params: Mapping[str, str],
        scratch: Path,
    ) -> list[Path]:
        """Execute the transformation.

        Args:
            inputs:  Materialised input file paths (from CAS).
            params:  Immutable parameter mapping (from :class:`Action.params`).
            scratch: Writable directory for intermediate and output files.

        Returns:
            List of output file paths (in *scratch* or absolute CAS paths).

        Raises:
            TransformError: tool returned non-zero or produced no output.
        """
        ...
