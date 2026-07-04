"""GenericEmitter — pure layout planner for the EMIT phase.

``plan_layout`` scans *output_dir* (files already materialised by the
executor) and returns a ``LayoutPlan`` describing where each file goes
in the final organised tree.  No I/O is performed here.

``emit_metadata`` is a no-op for targets that use ``MetadataDialect.NONE``.

``post_process`` returns an empty list unless the profile opts in to
post-processing hooks (Phase 5 stub — add jdupes/rsync hooks here later).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from romfarmer.ir.layout import LayoutEntry, LayoutPlan

if TYPE_CHECKING:
    from romfarmer.analysis.knowledge import KnowledgeBase
    from romfarmer.ir.actions import ArtifactDecl
    from romfarmer.targets.emitters.base import PostHook
    from romfarmer.targets.profiles.loader import ConcreteTargetProfile

logger = logging.getLogger(__name__)

# ROM file extensions to include in the layout
_ROM_EXTS: frozenset[str] = frozenset({
    ".chd", ".m3u", ".iso", ".cso", ".cue", ".bin",
    ".rvz", ".wua", ".wbfs", ".gcm",
    ".xiso", ".wux",
    ".7z", ".zip",
    ".nes", ".sfc", ".smc", ".gb", ".gbc", ".gba",
    ".nds", ".3ds", ".nsp", ".xci",
    ".n64", ".z64", ".v64",
    ".rom", ".img", ".a26", ".a52", ".lnx",
    ".ps3",  # PS3 JB folder marker
})


class GenericEmitter:
    """Layout planner for generic file-based targets.

    Works for any target where the organisation style is determined by
    the ``ConcreteTargetProfile.organisation_style`` field.
    """

    def plan_layout(
        self,
        output_dir: Path,
        profile: "ConcreteTargetProfile",
    ) -> LayoutPlan:
        """Scan *output_dir* and return a ``LayoutPlan``.

        The layout maps each artifact's sha256 to a relative output path.
        Files not in ``_ROM_EXTS`` (e.g. .xml, .jpg) are excluded from
        the plan — metadata emitters handle those separately.
        """
        import hashlib

        entries: list[LayoutEntry] = []
        if not output_dir.exists():
            return LayoutPlan(root_name=output_dir.name, entries=())

        for f in sorted(output_dir.iterdir()):
            if not f.is_file():
                continue
            if f.suffix.lower() not in _ROM_EXTS:
                continue
            try:
                sha256 = _sha256_file(f)
                rel = Path(f.name)
                entries.append(LayoutEntry(artifact_sha256=sha256, relative_path=rel))
            except OSError as exc:
                logger.warning("GenericEmitter.plan_layout: could not hash %s: %s", f, exc)

        return LayoutPlan(root_name=output_dir.name, entries=tuple(entries))

    def emit_metadata(
        self,
        layout: LayoutPlan,
        output_dir: Path,
        kb: "KnowledgeBase",
        profile: "ConcreteTargetProfile",
    ) -> list["ArtifactDecl"]:
        """No-op for targets with ``MetadataDialect.NONE``."""
        return []

    def post_process(self, root: Path) -> list["PostHook"]:
        return []


def _sha256_file(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1_048_576), b""):
            h.update(chunk)
    return h.hexdigest()
