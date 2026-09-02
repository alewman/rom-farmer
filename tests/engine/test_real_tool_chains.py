"""Real-tool chain tests: cartridge zip→7z and Redump zip→CHD through the Executor.

These run the actual ``7z`` and ``chdman`` binaries and are skipped when they
are not installed.  They guard the wiring between lowering and the transform
registry (``compress-7z``/``compress-zip``/``unzip``/``chdman``) and the two
behaviours a real emulator depends on:

* the member inside the produced archive keeps its real filename/extension
* a multi-track CUE/BIN disc compresses to a single CHD
"""

from __future__ import annotations

import hashlib
import shutil
import zipfile
from pathlib import Path

import pytest

from romfarmer.engine.actioncache import ActionCache
from romfarmer.engine.executor import Executor
from romfarmer.ir.actions import BuildPlan
from romfarmer.ir.catalog import DiscRef, GameUnit, PlatformId, SourceRef, UnitId
from romfarmer.ir.identity import Identity, ZipIdentity
from romfarmer.ir.manifest import BuildManifest
from romfarmer.new_orchestrator import _build_default_transforms, validate_plan
from romfarmer.planner.lowering.base import lower


def _unit(zip_path: Path, platform: str) -> GameUnit:
    """Mirror CatalogBuilder: identity carries the dominant zip member."""
    with zipfile.ZipFile(zip_path) as zf:
        infos = zf.infolist()
        cues = [m for m in infos if m.filename.lower().endswith(".cue")]
        dominant = cues[0] if cues else max(infos, key=lambda m: m.file_size)
    zid = ZipIdentity(
        member_crc32=dominant.CRC, member_size=dominant.file_size, member_name=dominant.filename
    )
    uid = UnitId(hashlib.sha1(f"{platform}:{zip_path.stem}".encode()).hexdigest())
    disc = DiscRef(
        index=1,
        source=SourceRef(path=zip_path, platform=PlatformId(platform)),
        identity=Identity(size=zip_path.stat().st_size, zip_identity=zid),
    )
    return GameUnit(
        unit_id=uid, platform=PlatformId(platform), canonical_name=zip_path.stem, discs=(disc,)
    )


def _executor(tmp_path: Path) -> tuple[Executor, Path]:
    cas = tmp_path / "cas"
    cas.mkdir()
    cache = ActionCache(tmp_path / "cache.db")
    ex = Executor(cache, _build_default_transforms(), cas, scratch_base=tmp_path / "scratch")
    return ex, cas


def _blob(cas: Path, sha256: str) -> Path:
    return next((cas / sha256[:2]).glob(f"{sha256[2:]}*"))


@pytest.mark.skipif(shutil.which("7z") is None, reason="7z not installed")
@pytest.mark.parametrize("fmt", ["7z", "zip"])
def test_cartridge_chain_preserves_member_name(tmp_path: Path, fmt: str) -> None:
    src = tmp_path / "src"
    src.mkdir()
    rom = b"NES\x1a" + bytes(range(256)) * 64
    zip_path = src / "Super Game (USA).zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("Super Game (USA).nes", rom)

    unit = _unit(zip_path, "nes")
    plan = BuildPlan(units=(lower(unit, (fmt,), BuildManifest()),))
    transforms = _build_default_transforms()
    validate_plan(plan, transforms)  # would raise before the registry fix

    ex, cas = _executor(tmp_path)
    outputs = ex.run(plan)
    (terminal,) = outputs.unit_outputs[unit.unit_id]
    assert terminal.sha256 is not None

    produced = _blob(cas, terminal.sha256)
    listing = (
        __import__("subprocess")
        .run(["7z", "l", "-slt", str(produced)], capture_output=True, text=True, check=True)
        .stdout
    )
    assert "Path = Super Game (USA).nes" in listing, listing


@pytest.mark.skipif(shutil.which("chdman") is None, reason="chdman not installed")
def test_disc_chain_multitrack_zip_to_chd(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    sector = 2352
    track1 = bytes(range(256)) * (sector * 16 // 256)
    track2 = bytes(reversed(range(256))) * (sector * 8 // 256)
    cue = (
        'FILE "Game (USA) (Track 1).bin" BINARY\n'
        "  TRACK 01 MODE1/2352\n    INDEX 01 00:00:00\n"
        'FILE "Game (USA) (Track 2).bin" BINARY\n'
        "  TRACK 02 AUDIO\n    INDEX 01 00:00:00\n"
    )
    zip_path = src / "Game (USA).zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        # bin first on purpose: the transform must locate the cue regardless of order
        zf.writestr("Game (USA) (Track 1).bin", track1)
        zf.writestr("Game (USA) (Track 2).bin", track2)
        zf.writestr("Game (USA).cue", cue)

    unit = _unit(zip_path, "psx")
    plan = BuildPlan(units=(lower(unit, ("chd",), BuildManifest()),))
    validate_plan(plan, _build_default_transforms())
    assert [a.tool for a in plan.units[0].actions] == ["source-copy", "chdman"]

    ex, cas = _executor(tmp_path)
    outputs = ex.run(plan)
    (terminal,) = outputs.unit_outputs[unit.unit_id]
    assert terminal.sha256 is not None
    chd = _blob(cas, terminal.sha256)
    assert chd.read_bytes()[:8] == b"MComprHD"
    # CUE/BIN intermediates must not have been ingested into the CAS
    assert sum(1 for _ in cas.rglob("*") if _.is_file()) == 2  # source zip + chd
