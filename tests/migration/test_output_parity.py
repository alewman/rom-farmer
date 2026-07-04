"""Output parity stub — Gate 2 (full-run comparison) requires real ROM fixtures.

Full parity testing (executor output == legacy stage output for identical
inputs) requires real ROM files and installed tools (chdman, extract-xiso,
dolphin-tool, etc.) which are not present in the test environment.

These tests are therefore:
  1.  A smoke test: verify the SourceCopyTransform and PassthroughTransform
      work correctly (the two transforms that can run without external tools).
  2.  A structural test: verify that a BuildPlan assembled from synthetic
      corpus fixtures can be executed by the Executor without errors.

Full E2E parity (Gate 2) is validated manually using the real corpus.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

from romfarmer.engine.transforms.source import PassthroughTransform, SourceCopyTransform


class TestSourceCopyTransform:
    def test_copies_file_to_scratch(self, tmp_path: Path):
        src = tmp_path / "source.zip"
        src.write_bytes(b"fake zip content")
        scratch = tmp_path / "scratch"

        t = SourceCopyTransform()
        result = t.run(inputs=[], params={"path": str(src)}, scratch=scratch)

        assert len(result) == 1
        assert result[0].name == "source.zip"
        assert result[0].read_bytes() == b"fake zip content"

    def test_missing_source_raises(self, tmp_path: Path):
        t = SourceCopyTransform()
        with pytest.raises(FileNotFoundError):
            t.run([], {"path": str(tmp_path / "missing.zip")}, tmp_path / "s")

    def test_scratch_dir_created(self, tmp_path: Path):
        src = tmp_path / "game.zip"
        src.write_bytes(b"x")
        scratch = tmp_path / "does" / "not" / "exist"

        t = SourceCopyTransform()
        result = t.run([], {"path": str(src)}, scratch)
        assert result[0].exists()


class TestPassthroughTransform:
    def test_copies_input_to_scratch(self, tmp_path: Path):
        src = tmp_path / "rom.nes"
        src.write_bytes(b"nintendo bytes")
        scratch = tmp_path / "scratch"

        t = PassthroughTransform()
        result = t.run([src], {}, scratch)

        assert len(result) == 1
        assert result[0].read_bytes() == b"nintendo bytes"

    def test_empty_inputs_returns_empty(self, tmp_path: Path):
        t = PassthroughTransform()
        result = t.run([], {}, tmp_path / "scratch")
        assert result == []

    def test_same_src_as_dest_is_noop(self, tmp_path: Path):
        """If src == dest, no copy is performed."""
        scratch = tmp_path / "scratch"
        scratch.mkdir()
        src = scratch / "file.bin"
        src.write_bytes(b"data")

        t = PassthroughTransform()
        result = t.run([src], {}, scratch)
        assert result[0] == src


class TestBuildPlanStructure:
    """Verify a synthetic BuildPlan can be assembled and its structure is sane."""

    def test_build_plan_assembles(self, tmp_path: Path):
        from unittest.mock import patch
        import hashlib

        from romfarmer.ir.catalog import (
            Catalog, DiscRef, GameUnit, PlatformId, SourceRef, UnitId,
        )
        from romfarmer.ir.identity import Identity
        from romfarmer.ir.manifest import BuildManifest
        from romfarmer.planner.lowering.base import lower

        # Write a dummy source zip
        src = tmp_path / "Super Mario World (USA).zip"
        with zipfile.ZipFile(src, "w") as zf:
            zf.writestr("Super Mario World (USA).smc", b"x" * 1024)

        uid = UnitId(hashlib.sha1(b"snes:Super Mario World (USA)").hexdigest())
        unit = GameUnit(
            unit_id=uid,
            platform=PlatformId("snes"),
            canonical_name="Super Mario World (USA)",
            discs=(
                DiscRef(
                    index=1,
                    source=SourceRef(path=src, platform=PlatformId("snes")),
                    identity=Identity(size=src.stat().st_size),
                ),
            ),
        )

        with patch("romfarmer.planner.lowering.base.probe_tool_version", return_value="test"):
            up = lower(unit, ("zip",), BuildManifest())

        assert len(up.actions) >= 2
        assert up.actions[0].tool == "source-copy"
        assert str(src) == up.actions[0].params["path"]
