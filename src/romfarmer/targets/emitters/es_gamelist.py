"""ESGamelistEmitter — generates gamelist.xml for EmulationStation targets.

Ports the core logic from ``stages/metadata.py::GenerateMetadataStage``.

Key differences from the legacy stage:
- Input is a ``LayoutPlan`` + ``output_dir`` (no ``StageContext``)
- Database lookups go through ``KnowledgeBase`` (no direct SQLAlchemy)
- Multi-disc handling: M3U files are primary; .chd files with a sibling .m3u
  are hidden (path starts with ``./``)
- Returns a list of ``ArtifactDecl`` (the gamelist.xml as an artifact)

The gamelist.xml format is identical to what the legacy stage produced,
so existing Batocera/RocknIX installations require no changes.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING
from xml.etree import ElementTree as ET

from romfarmer.ir.actions import ArtifactDecl, Retention
from romfarmer.ir.layout import LayoutPlan

if TYPE_CHECKING:
    from romfarmer.analysis.knowledge import KnowledgeBase
    from romfarmer.targets.emitters.base import PostHook
    from romfarmer.targets.profiles.loader import ConcreteTargetProfile

logger = logging.getLogger(__name__)

_DISC_TAG = re.compile(r"\s*\((?:Disc|Disk|CD)\s*\d+\)", re.IGNORECASE)


def _canonical(stem: str) -> str:
    """Strip disc tags for grouping and M3U playlist naming."""
    return _DISC_TAG.sub("", stem).strip()


class ESGamelistEmitter:
    """Generates ``gamelist.xml`` for EmulationStation-based frontends.

    Used by targets with ``MetadataDialect.ES_GAMELIST`` (Batocera, RocknIX,
    RetroArch + ES-DE, …).
    """

    def plan_layout(
        self,
        output_dir: Path,
        profile: ConcreteTargetProfile,
    ) -> LayoutPlan:
        """Delegates to GenericEmitter — layout is format-agnostic."""
        from romfarmer.targets.emitters.generic import GenericEmitter

        return GenericEmitter().plan_layout(output_dir, profile)

    def emit_metadata(
        self,
        layout: LayoutPlan,
        output_dir: Path,
        kb: KnowledgeBase,
        profile: ConcreteTargetProfile,
    ) -> list[ArtifactDecl]:
        """Write ``gamelist.xml`` to *output_dir* and return its artifact declaration."""
        if not profile.metadata_enabled:
            return []

        gamelist = ET.Element("gameList")
        processed: set[str] = set()

        # Collect all files
        chd_files: dict[str, Path] = {}
        m3u_files: dict[str, Path] = {}

        for entry in layout.entries:
            abs_path = output_dir / entry.relative_path
            if abs_path.suffix.lower() == ".chd":
                canonical = _canonical(abs_path.stem)
                chd_files[abs_path.name] = abs_path
            elif abs_path.suffix.lower() == ".m3u":
                canonical = _canonical(abs_path.stem)
                m3u_files[canonical] = abs_path

        # Add M3U entries first (multi-disc primary)
        for canonical, m3u_path in sorted(m3u_files.items()):
            if m3u_path.name in processed:
                continue
            game_elem = self._make_game_elem(m3u_path, output_dir, kb)
            gamelist.append(game_elem)
            processed.add(m3u_path.name)
            # Mark individual CHDs as hidden
            for chd_name, chd_path in chd_files.items():
                if _canonical(chd_path.stem) == canonical:
                    hidden_elem = self._make_game_elem(chd_path, output_dir, kb, hidden=True)
                    gamelist.append(hidden_elem)
                    processed.add(chd_name)

        # Add remaining files not covered by M3U
        for entry in layout.entries:
            abs_path = output_dir / entry.relative_path
            if abs_path.name in processed:
                continue
            game_elem = self._make_game_elem(abs_path, output_dir, kb)
            gamelist.append(game_elem)
            processed.add(abs_path.name)

        # Sort by name
        games = gamelist.findall("game")
        gamelist.clear()
        for g in sorted(games, key=lambda e: e.findtext("name") or ""):
            gamelist.append(g)

        # Write
        gamelist_path = output_dir / "gamelist.xml"
        tree = ET.ElementTree(gamelist)
        ET.indent(tree, space="  ")
        tree.write(
            str(gamelist_path),
            encoding="utf-8",
            xml_declaration=True,
        )
        logger.info("ESGamelistEmitter: wrote %s (%d entries)", gamelist_path, len(games))

        return [
            ArtifactDecl(
                logical_name="gamelist.xml",
                kind="gamelist",
                retention=Retention.TERMINAL,
            )
        ]

    def post_process(self, root: Path) -> list[PostHook]:
        return []

    # ------------------------------------------------------------------

    def _make_game_elem(
        self,
        path: Path,
        output_dir: Path,
        kb: KnowledgeBase,
        hidden: bool = False,
    ) -> ET.Element:
        """Build a ``<game>`` element for *path*."""
        game = ET.Element("game")

        rel = path.relative_to(output_dir) if path.is_relative_to(output_dir) else path
        ET.SubElement(game, "path").text = f"./{rel}"
        ET.SubElement(game, "name").text = _canonical(path.stem)

        if hidden:
            ET.SubElement(game, "hidden").text = "true"

        # Try to enrich from KnowledgeBase
        try:
            rating = kb.get_rating(
                path.parent.name,  # platform = parent dir name
                _canonical(path.stem),
            )
            if rating is not None:
                ET.SubElement(game, "rating").text = f"{rating:.1f}"
        except Exception:
            pass

        return game
