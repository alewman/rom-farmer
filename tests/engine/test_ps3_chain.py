"""PS3 chain tests: dkey lookup, tree extraction, and Executor tree ingestion.

The full chain (source-copy → unzip → ps3-dkey-lookup → ps3dec →
ps3-extract-tree) can't be exercised end-to-end without a real encrypted
Redump ISO + matching disc key, so these tests cover each new piece in
isolation:

* ``Ps3DkeyLookupTransform`` — pure filesystem lookup, no real tool needed.
* ``Ps3ExtractTreeTransform`` — uses ``7z`` (which sniffs archive format from
  content, not the ``.iso`` extension) as a stand-in for a decrypted ISO.
* The Executor's ``kind="tree"`` branch — ingests/restores a folder-shaped
  artifact via the CAS tree store instead of the single-file blob path.
"""

from __future__ import annotations

import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

from romfarmer.engine.transforms.base import TransformError
from romfarmer.engine.transforms.ps3 import (
    Ps3DkeyLookupTransform,
    Ps3ExtractTreeTransform,
)


class TestPs3DkeyLookupTransform:
    def test_reads_matching_key(self, tmp_path: Path) -> None:
        keys_dir = tmp_path / "keys"
        keys_dir.mkdir()
        with zipfile.ZipFile(keys_dir / "Game (USA).zip", "w") as zf:
            zf.writestr("Game (USA).dkey", "AB" * 16)

        result = Ps3DkeyLookupTransform().run(
            [], {"keys_directory": str(keys_dir), "stem": "Game (USA)"}, tmp_path
        )
        assert len(result) == 1
        assert result[0].read_text() == "AB" * 16

    def test_falls_back_without_rev_marker(self, tmp_path: Path) -> None:
        keys_dir = tmp_path / "keys"
        keys_dir.mkdir()
        with zipfile.ZipFile(keys_dir / "Game (USA).zip", "w") as zf:
            zf.writestr("Game (USA).dkey", "CD" * 16)

        result = Ps3DkeyLookupTransform().run(
            [], {"keys_directory": str(keys_dir), "stem": "Game (USA) (Rev 1)"}, tmp_path
        )
        assert result[0].read_text() == "CD" * 16

    def test_missing_key_raises(self, tmp_path: Path) -> None:
        keys_dir = tmp_path / "keys"
        keys_dir.mkdir()
        with pytest.raises(TransformError, match="No disc key found"):
            Ps3DkeyLookupTransform().run(
                [], {"keys_directory": str(keys_dir), "stem": "Nope"}, tmp_path
            )

    def test_invalid_key_length_raises(self, tmp_path: Path) -> None:
        keys_dir = tmp_path / "keys"
        keys_dir.mkdir()
        with zipfile.ZipFile(keys_dir / "Game (USA).zip", "w") as zf:
            zf.writestr("Game (USA).dkey", "AB")
        with pytest.raises(TransformError, match="Invalid disc key length"):
            Ps3DkeyLookupTransform().run(
                [], {"keys_directory": str(keys_dir), "stem": "Game (USA)"}, tmp_path
            )

    def test_missing_params_raises(self, tmp_path: Path) -> None:
        with pytest.raises(TransformError, match="requires"):
            Ps3DkeyLookupTransform().run([], {}, tmp_path)


@pytest.mark.skipif(shutil.which("7z") is None, reason="7z not installed")
class TestPs3ExtractTreeTransform:
    def test_finds_ps3_game_dir(self, tmp_path: Path) -> None:
        payload = tmp_path / "payload" / "PS3_GAME"
        (payload / "USRDIR").mkdir(parents=True)
        (payload / "PARAM.SFO").write_bytes(b"fake-sfo")
        (payload / "USRDIR" / "EBOOT.BIN").write_bytes(b"fake-eboot")

        # 7z sniffs archive format from content, not the .iso extension —
        # a real 7z archive is a convenient stand-in for a decrypted ISO here.
        iso = tmp_path / "Game.iso"
        subprocess.run(["7z", "a", "-t7z", str(iso), str(payload)], check=True, capture_output=True)

        scratch = tmp_path / "scratch"
        scratch.mkdir()
        result = Ps3ExtractTreeTransform().run([iso], {}, scratch)

        assert len(result) == 1
        folder = result[0]
        assert folder.is_dir()
        assert (folder / "PS3_GAME" / "PARAM.SFO").read_bytes() == b"fake-sfo"
        assert (folder / "PS3_GAME" / "USRDIR" / "EBOOT.BIN").read_bytes() == b"fake-eboot"

    def test_no_ps3_game_dir_raises(self, tmp_path: Path) -> None:
        payload = tmp_path / "payload"
        payload.mkdir()
        (payload / "readme.txt").write_bytes(b"nothing here")
        iso = tmp_path / "Game.iso"
        subprocess.run(
            ["7z", "a", "-t7z", str(iso), str(payload / "readme.txt")],
            check=True,
            capture_output=True,
        )

        scratch = tmp_path / "scratch"
        scratch.mkdir()
        with pytest.raises(TransformError, match="No PS3_GAME directory"):
            Ps3ExtractTreeTransform().run([iso], {}, scratch)


class TestExecutorTreeIngestion:
    """The Executor must ingest kind="tree" outputs via the CAS tree store."""

    def test_tree_output_ingested_and_restorable(self, tmp_path: Path) -> None:
        from romfarmer.cas.store import ContentStore
        from romfarmer.cas.tree import TreeStore
        from romfarmer.engine.actioncache import ActionCache
        from romfarmer.engine.executor import Executor
        from romfarmer.ir.actions import (
            Action,
            ArtifactDecl,
            BuildPlan,
            Retention,
            UnitPlan,
        )
        from romfarmer.ir.catalog import DiscRef, GameUnit, PlatformId, SourceRef
        from romfarmer.ir.identity import Identity

        # A trivial fake transform whose output is a directory, standing in
        # for Ps3ExtractTreeTransform without needing real PS3 tools.
        class _FakeTreeTransform:
            name = "fake-tree"

            def run(self, inputs, params, scratch):
                folder = scratch / "Game.ps3"
                (folder / "PS3_GAME").mkdir(parents=True)
                (folder / "PS3_GAME" / "PARAM.SFO").write_bytes(b"sfo-bytes")
                return [folder]

        cas = tmp_path / "cas"
        cas.mkdir()
        cache = ActionCache(tmp_path / "cache.db")
        executor = Executor(
            cache,
            {"fake-tree": _FakeTreeTransform()},
            cas,
            scratch_base=tmp_path / "scratch",
        )

        unit = GameUnit.from_discs(
            platform=PlatformId("ps3"),
            canonical_name="Game (USA)",
            discs=[
                DiscRef(
                    index=1,
                    source=SourceRef(Path("/src/Game (USA).zip"), PlatformId("ps3")),
                    identity=Identity(md5="d41d8cd98f00b204e9800998ecf8427e"),
                )
            ],
        )
        action = Action(
            action_id="a1",  # type: ignore[arg-type]
            tool="fake-tree",
            tool_version="1",
            params={},
            inputs=(),
            outputs=(
                ArtifactDecl(logical_name="Game (USA)", kind="tree", retention=Retention.TERMINAL),
            ),
        )
        unit_plan = UnitPlan(
            unit=unit,
            actions=(action,),
            predicted_output_bytes=0,
            prediction=__import__(
                "romfarmer.ir.actions", fromlist=["SizePrediction"]
            ).SizePrediction(ratio=1.0, source="test", confidence=1.0),
        )
        output_set = executor.run(BuildPlan(units=(unit_plan,)))

        (terminal,) = output_set.unit_outputs[unit.unit_id]
        assert terminal.sha256 is not None
        assert terminal.size == len(b"sfo-bytes")

        # The manifest is a real tree in the CAS — restorable independently.
        restore_dir = tmp_path / "restored"
        TreeStore(ContentStore(cas)).restore(terminal.sha256, restore_dir)
        assert (restore_dir / "PS3_GAME" / "PARAM.SFO").read_bytes() == b"sfo-bytes"
