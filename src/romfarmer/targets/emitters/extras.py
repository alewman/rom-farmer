"""ExtrasEmitter — places DLC, updates, and extras alongside the main output.

Ports the core of ``stages/emit_extras.py``.  An 'extras' platform is one
where ``resolved.extras`` is set in the build config; its files are not
DAT-filtered but placed in a subdirectory alongside the main platform output.

For Phase 5, this is a minimal port — it copies extras files to a
``_extras/`` subdirectory under *output_dir* and returns a ``LayoutPlan``
covering those files.
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


class ExtrasEmitter:
    """Places extras/DLC files into ``<output_dir>/_extras/``."""

    def __init__(self, extras_source_dir: Path | None = None) -> None:
        self._source = extras_source_dir

    def plan_layout(
        self,
        output_dir: Path,
        profile: ConcreteTargetProfile,
    ) -> LayoutPlan:
        """Return a LayoutPlan for extras files — no I/O performed here."""
        import hashlib

        if self._source is None or not self._source.exists():
            return LayoutPlan(root_name=output_dir.name, entries=())

        entries: list[LayoutEntry] = []
        for f in sorted(self._source.rglob("*")):
            if not f.is_file():
                continue
            try:
                h = hashlib.sha256()
                with open(f, "rb") as fh:
                    for chunk in iter(lambda: fh.read(65536), b""):
                        h.update(chunk)
                rel = Path("_extras") / f.relative_to(self._source)
                entries.append(LayoutEntry(artifact_sha256=h.hexdigest(), relative_path=rel))
            except OSError as exc:
                logger.debug("ExtrasEmitter.plan_layout: %s: %s", f, exc)

        return LayoutPlan(root_name=output_dir.name, entries=tuple(entries))

    def emit_metadata(
        self,
        layout: LayoutPlan,
        output_dir: Path,
        kb: KnowledgeBase,
        profile: ConcreteTargetProfile,
    ) -> list[ArtifactDecl]:
        """No-op — extras don't need gamelist entries."""
        return []

    def post_process(self, root: Path) -> list[PostHook]:
        return []
