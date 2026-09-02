"""TargetEmitter protocol and PostHook type.

A ``TargetEmitter`` is the EMIT-phase counterpart to the PLAN-phase
planner passes: it takes a materialised ``OutputSet`` and produces the
final on-disk layout (organised files + metadata).

Emitters are **pure** for ``plan_layout`` (returns data, no I/O) and
**side-effecting** for ``emit_metadata`` and ``post_process``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from romfarmer.analysis.knowledge import KnowledgeBase
    from romfarmer.ir.actions import ArtifactDecl
    from romfarmer.ir.layout import LayoutPlan
    from romfarmer.targets.profiles.loader import ConcreteTargetProfile


@dataclass(frozen=True)
class PostHook:
    """A post-EMIT command to run (e.g. jdupes, rsync)."""

    name: str
    command: list[str]


class TargetEmitter(Protocol):
    """EMIT-phase behavior for a specific target type.

    Implementations live in the sibling modules
    (generic.py, es_gamelist.py, extras.py).
    """

    def plan_layout(
        self,
        output_dir: Path,
        profile: ConcreteTargetProfile,
    ) -> LayoutPlan:
        """Return the desired output tree as pure data.  No I/O."""
        ...

    def emit_metadata(
        self,
        layout: LayoutPlan,
        output_dir: Path,
        kb: KnowledgeBase,
        profile: ConcreteTargetProfile,
    ) -> list[ArtifactDecl]:
        """Generate metadata files (gamelist.xml, etc.).  Side-effecting."""
        ...

    def post_process(self, root: Path) -> list[PostHook]:
        """Return post-process hooks to run after all files are placed."""
        ...
