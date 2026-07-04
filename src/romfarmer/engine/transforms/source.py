"""SourceCopyTransform — copy a source file from disk into the scratch dir.

This is the bridge between filesystem source files and the CAS-aware executor.
It handles the special ``source-copy`` tool declared by the lowering rules.

Unlike all other transforms, SourceCopyTransform reads from a filesystem path
specified in ``params["path"]`` rather than from CAS.  Its output is a copy
of the source file in scratch; the executor then ingests it into CAS and
records the sha256.

Caching semantics: the ActionKey for a source-copy action is derived from
the file path (in params) and tool_version="1" (constant).  If the source
file is immutable (ROM archives are), this is safe.  If the file changes,
the cache must be invalidated manually.

``passthrough`` tool: a no-op transform that copies input → output unchanged.
Used when a lowering rule wants to relabel an intermediate as terminal.
"""

from __future__ import annotations

import shutil
from collections.abc import Mapping
from pathlib import Path


class SourceCopyTransform:
    """Copy ``params["path"]`` into the scratch dir.

    Satisfies the :class:`~romfarmer.engine.transforms.base.Transform` protocol.
    """

    name = "source-copy"

    def run(
        self,
        inputs: list[Path],
        params: Mapping[str, str],
        scratch: Path,
    ) -> list[Path]:
        """Copy the source file to *scratch* and return the destination path."""
        src = Path(params["path"])
        if not src.exists():
            raise FileNotFoundError(f"SourceCopyTransform: source not found: {src}")
        dest = scratch / src.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        return [dest]


class PassthroughTransform:
    """Copy input[0] → output unchanged.

    Used by the passthrough lowering rules to relabel an intermediate
    artifact as terminal without any actual transformation.
    """

    name = "passthrough"

    def run(
        self,
        inputs: list[Path],
        params: Mapping[str, str],
        scratch: Path,
    ) -> list[Path]:
        if not inputs:
            return []
        src = inputs[0]
        dest = scratch / src.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src != dest:
            shutil.copy2(src, dest)
        return [dest]
