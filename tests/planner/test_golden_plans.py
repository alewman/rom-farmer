"""Golden BuildPlan snapshot tests.

Gate 1: BuildPlan snapshots must be stable across two runs (determinism).
Each test builds a plan for a synthetic unit and asserts:
  - action count
  - tool names in order
  - ActionId determinism (same inputs → same id)
  - ArtifactDecl kinds

These tests do NOT invoke any external tools.  All tool_version calls are
patched to return "test-v1" for determinism.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import patch
import zipfile

import pytest

from romfarmer.ir.catalog import (
    Catalog,
    DiscRef,
    GameUnit,
    PlatformId,
    SourceRef,
    UnitId,
)
from romfarmer.ir.identity import Identity
from romfarmer.ir.manifest import BuildManifest
from romfarmer.planner.lowering.base import (
    FormatChain,
    lower,
    make_action_id,
)
from romfarmer.planner.lowering import (
    disc as disc_mod,
    rvz as rvz_mod,
    wux as wux_mod,
    xiso as xiso_mod,
    cartridge as cart_mod,
    arcade as arcade_mod,
    passthrough as pt_mod,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _unit(
    name: str,
    platform: str = "psx",
    num_discs: int = 1,
    size: int = 700_000_000,
) -> GameUnit:
    uid = UnitId(hashlib.sha1(f"{platform}:{name}".encode()).hexdigest())
    discs = []
    for i in range(1, num_discs + 1):
        disc_name = f"{name} (Disc {i})" if num_discs > 1 else name
        path = Path(f"/roms/{platform}/{disc_name}.zip")
        disc = DiscRef(
            index=i,
            source=SourceRef(path=path, platform=PlatformId(platform)),
            identity=Identity(size=size // num_discs),
        )
        discs.append(disc)
    return GameUnit(
        unit_id=uid,
        platform=PlatformId(platform),
        canonical_name=name,
        discs=tuple(discs),
    )


FAKE_VERSION = "test-v1"

# Patch probe_tool_version so tests don't depend on installed tools
@pytest.fixture(autouse=True)
def patch_tool_version():
    with patch(
        "romfarmer.planner.lowering.base.probe_tool_version",
        return_value=FAKE_VERSION,
    ):
        yield


# ---------------------------------------------------------------------------
# Gate 1 helpers: assert determinism
# ---------------------------------------------------------------------------

def _plan_twice(unit: GameUnit, chain: FormatChain) -> tuple:
    manifest = BuildManifest()
    up1 = lower(unit, chain, manifest)
    up2 = lower(unit, chain, manifest)
    assert [a.action_id for a in up1.actions] == [a.action_id for a in up2.actions], \
        "ActionIds are not deterministic!"
    assert [a.tool for a in up1.actions] == [a.tool for a in up2.actions]
    return up1, up2


# ---------------------------------------------------------------------------
# Disc (CHD) lowering — single disc
# ---------------------------------------------------------------------------

class TestDiscLoweringCHD:
    def test_single_disc_action_sequence(self):
        unit = _unit("Final Fantasy IX (USA)", platform="psx")
        up, _ = _plan_twice(unit, ("chd",))

        tools = [a.tool for a in up.actions]
        assert tools == ["source-copy", "unzip", "chdman"]

    def test_single_disc_terminal_is_chd(self):
        unit = _unit("Crash Bandicoot (USA)", platform="psx")
        up, _ = _plan_twice(unit, ("chd",))
        terminal = [a for a in up.actions if any(
            o.retention.value == "terminal" for o in a.outputs
        )]
        assert len(terminal) == 1
        assert terminal[0].outputs[0].kind == "chd"

    def test_multi_disc_includes_m3u(self):
        unit = _unit("Final Fantasy VII", platform="psx", num_discs=3)
        up, _ = _plan_twice(unit, ("chd",))

        tools = [a.tool for a in up.actions]
        assert tools.count("chdman") == 3
        assert "m3u-create" in tools
        # M3U is terminal
        m3u_action = next(a for a in up.actions if a.tool == "m3u-create")
        assert m3u_action.outputs[0].kind == "m3u"

    def test_no_chd_no_m3u(self):
        unit = _unit("Chrono Cross (USA)", platform="psx", num_discs=2)
        up, _ = _plan_twice(unit, ("cue_bin",))
        tools = [a.tool for a in up.actions]
        assert "chdman" not in tools
        assert "m3u-create" not in tools

    def test_action_ids_deterministic(self):
        unit = _unit("Xenogears (USA)", platform="psx")
        up1, up2 = _plan_twice(unit, ("chd",))
        for a1, a2 in zip(up1.actions, up2.actions):
            assert a1.action_id == a2.action_id


# ---------------------------------------------------------------------------
# RVZ lowering
# ---------------------------------------------------------------------------

class TestRVZLowering:
    def test_action_sequence(self):
        unit = _unit("Mario Kart Double Dash (USA)", platform="gamecube")
        up, _ = _plan_twice(unit, ("rvz",))
        tools = [a.tool for a in up.actions]
        assert tools == ["source-copy", "unzip-rvz"]

    def test_terminal_is_rvz(self):
        unit = _unit("Zelda Wind Waker (USA)", platform="gamecube")
        up, _ = _plan_twice(unit, ("rvz",))
        terminal = [a for a in up.actions if any(
            o.retention.value == "terminal" for o in a.outputs
        )]
        assert terminal[-1].outputs[0].kind == "rvz"


# ---------------------------------------------------------------------------
# WUX lowering
# ---------------------------------------------------------------------------

class TestWUXLowering:
    def test_action_sequence(self):
        unit = _unit("Breath of the Wild (USA)", platform="wiiu")
        up, _ = _plan_twice(unit, ("wux",))
        tools = [a.tool for a in up.actions]
        assert tools == ["source-copy", "unzip-wux"]

    def test_terminal_is_wux(self):
        unit = _unit("Mario Kart 8 (USA)", platform="wiiu")
        up, _ = _plan_twice(unit, ("wux",))
        terminal = [a for a in up.actions if any(o.retention.value == "terminal" for o in a.outputs)]
        assert terminal[-1].outputs[0].kind == "wux"


# ---------------------------------------------------------------------------
# XISO lowering
# ---------------------------------------------------------------------------

class TestXisoLowering:
    def test_xiso_only(self):
        unit = _unit("Halo (USA)", platform="xbox")
        up, _ = _plan_twice(unit, ("xiso",))
        tools = [a.tool for a in up.actions]
        assert tools == ["source-copy", "unzip", "extract-xiso"]

    def test_xiso_squashfs_chain(self):
        unit = _unit("Halo 2 (USA)", platform="xbox")
        up, _ = _plan_twice(unit, ("xiso", "squashfs"))
        tools = [a.tool for a in up.actions]
        assert tools == ["source-copy", "unzip", "extract-xiso", "mksquashfs"]
        # xiso should be INTERMEDIATE, squashfs TERMINAL
        xiso_action = next(a for a in up.actions if a.tool == "extract-xiso")
        sq_action = next(a for a in up.actions if a.tool == "mksquashfs")
        assert xiso_action.outputs[0].retention.value == "intermediate"
        assert sq_action.outputs[0].retention.value == "terminal"

    def test_determinism(self):
        unit = _unit("Fable (USA)", platform="xbox")
        up1, up2 = _plan_twice(unit, ("xiso",))
        assert [a.action_id for a in up1.actions] == [a.action_id for a in up2.actions]


# ---------------------------------------------------------------------------
# Cartridge lowering
# ---------------------------------------------------------------------------

class TestCartridgeLowering:
    def test_zip_chain(self):
        unit = _unit("Super Mario World (USA)", platform="snes")
        up, _ = _plan_twice(unit, ("zip",))
        tools = [a.tool for a in up.actions]
        assert tools == ["source-copy", "unzip", "compress-zip"]

    def test_passthrough_chain(self):
        # ("passthrough",) routes to PassthroughLoweringRule, not CartridgeLoweringRule
        unit = _unit("Tetris (USA)", platform="nes")
        up, _ = _plan_twice(unit, ("passthrough",))
        tools = [a.tool for a in up.actions]
        assert tools == ["source-copy", "passthrough"]


# ---------------------------------------------------------------------------
# Passthrough lowering
# ---------------------------------------------------------------------------

class TestPassthroughLowering:
    def test_action_sequence(self):
        unit = _unit("Pokemon Red (USA)", platform="3ds")
        up, _ = _plan_twice(unit, ("passthrough",))
        tools = [a.tool for a in up.actions]
        assert tools == ["source-copy", "passthrough"]

    def test_terminal_output(self):
        unit = _unit("Smash Bros (USA)", platform="3ds")
        up, _ = _plan_twice(unit, ("passthrough",))
        terminal = [a for a in up.actions if any(o.retention.value == "terminal" for o in a.outputs)]
        assert len(terminal) >= 1


# ---------------------------------------------------------------------------
# Arcade lowering
# ---------------------------------------------------------------------------

class TestArcadeLowering:
    def test_action_sequence(self):
        unit = _unit("sf2", platform="mame")
        up, _ = _plan_twice(unit, ("arcade",))
        tools = [a.tool for a in up.actions]
        assert tools == ["source-copy", "passthrough"]


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

class TestLowerDispatcher:
    def test_dispatches_chd(self):
        unit = _unit("Tekken 3 (USA)", platform="psx")
        up = lower(unit, ("chd",), BuildManifest())
        assert any(a.tool == "chdman" for a in up.actions)

    def test_dispatches_rvz(self):
        unit = _unit("Twilight Princess (USA)", platform="wii")
        up = lower(unit, ("rvz",), BuildManifest())
        assert any(a.tool == "unzip-rvz" for a in up.actions)

    def test_unknown_chain_raises(self):
        unit = _unit("Unknown Game", platform="unknown")
        with pytest.raises(ValueError, match="No lowering rule"):
            lower(unit, ("totally_unknown_format_xyz",), BuildManifest())

    def test_empty_chain_raises(self):
        unit = _unit("Empty Chain", platform="psx")
        with pytest.raises(ValueError, match="Empty FormatChain"):
            lower(unit, (), BuildManifest())


# ---------------------------------------------------------------------------
# negotiation.py
# ---------------------------------------------------------------------------

class TestNegotiation:
    """Verify negotiate_format_chain maps config enums correctly."""

    def _make_resolved(self, extraction: str, compression: str) -> object:
        """Create a minimal ResolvedPlatformConfig-like object."""
        from types import SimpleNamespace
        from romfarmer.config.models import CompressionFormat, ExtractionType
        return SimpleNamespace(
            extraction_type=ExtractionType(extraction),
            compression=CompressionFormat(compression),
        )

    def test_disc_chd(self):
        from romfarmer.planner.negotiation import negotiate_format_chain
        r = self._make_resolved("disc", "chd")
        assert negotiate_format_chain(r) == ("chd",)

    def test_disc_none(self):
        from romfarmer.planner.negotiation import negotiate_format_chain
        r = self._make_resolved("disc", "none")
        assert negotiate_format_chain(r) == ("cue_bin",)

    def test_rvz(self):
        from romfarmer.planner.negotiation import negotiate_format_chain
        r = self._make_resolved("rvz", "none")
        assert negotiate_format_chain(r) == ("rvz",)

    def test_xiso_squashfs(self):
        from romfarmer.planner.negotiation import negotiate_format_chain
        r = self._make_resolved("xiso", "sqfs")
        assert negotiate_format_chain(r) == ("xiso", "squashfs")

    def test_none_extraction_is_passthrough(self):
        from romfarmer.planner.negotiation import negotiate_format_chain
        r = self._make_resolved("none", "none")
        assert negotiate_format_chain(r) == ("passthrough",)
