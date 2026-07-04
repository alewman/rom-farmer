"""Tests for the M3U and SquashFS transforms added in the post-Phase-5 review.

These two tools are declared by the lowering rules (``m3u-create`` for every
multi-disc CHD set, ``mksquashfs`` for the Xbox squashfs chain) but had no
Transform implementations — every multi-disc unit failed at EXECUTE.
"""

from __future__ import annotations

from pathlib import Path

from romfarmer.engine.transforms.m3u import M3UTransform
from romfarmer.engine.transforms.squashfs import SquashFSTransform


class TestM3UTransform:
    def test_writes_playlist_lines(self, tmp_path: Path) -> None:
        t = M3UTransform()
        result = t.run(
            inputs=[],
            params={
                "entries": "Game (Disc 1).chd,Game (Disc 2).chd",
                "name": "Game.m3u",
            },
            scratch=tmp_path,
        )
        assert len(result) == 1
        assert result[0].name == "Game.m3u"
        assert result[0].read_text() == "Game (Disc 1).chd\nGame (Disc 2).chd\n"

    def test_default_name(self, tmp_path: Path) -> None:
        t = M3UTransform()
        result = t.run(inputs=[], params={"entries": "a.chd"}, scratch=tmp_path)
        assert result[0].name == "playlist.m3u"

    def test_registered_tool_name_matches_lowering(self) -> None:
        # disc.py lowering emits tool="m3u-create"
        assert M3UTransform.name == "m3u-create"


class TestSquashFSTransformNaming:
    def test_registered_tool_name_matches_lowering(self) -> None:
        # xiso.py lowering emits tool="mksquashfs"
        assert SquashFSTransform.name == "mksquashfs"


class TestPS3ToolNameAlignment:
    def test_ps3_lowering_tool_matches_transform(self) -> None:
        """The lowering rule's tool string must match the registered transform.

        Regression: lowering emitted ``ps3-decrypt`` while the transform was
        named ``ps3dec`` — every PS3 unit raised ``No transform registered``.
        """
        from romfarmer.engine.transforms.ps3 import PS3DecTransform
        from romfarmer.ir.catalog import DiscRef, GameUnit, PlatformId, SourceRef
        from romfarmer.ir.identity import Identity
        from romfarmer.ir.manifest import BuildManifest
        from romfarmer.planner.lowering.ps3 import PS3LoweringRule

        unit = GameUnit.from_discs(
            platform=PlatformId("ps3"),
            canonical_name="Test Game (USA)",
            discs=[
                DiscRef(
                    index=1,
                    source=SourceRef(Path("/src/Test Game (USA).zip"), PlatformId("ps3")),
                    identity=Identity(md5="d41d8cd98f00b204e9800998ecf8427e"),
                )
            ],
        )
        plan = PS3LoweringRule().lower(unit, ("ps3",), BuildManifest(platform=PlatformId("ps3")))
        decrypt_tools = [a.tool for a in plan.actions if a.tool != "source-copy"]
        assert decrypt_tools == [PS3DecTransform.name]
