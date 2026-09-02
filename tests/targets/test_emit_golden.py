"""Tests for targets/ package — TargetProfile loader and emitters.

Gate 1 (Phase 5): E2E fixture builds for three targets diffed against
golden manifests.  The full golden-tree tests require an actual build run;
this file covers the unit-level contracts:

- TargetProfileLoader correctly parses frontend + device YAML
- ConcreteTargetProfile.supports() gates platforms
- format_preferences() returns the right chain
- Materializer organises files as expected
- ESGamelistEmitter produces valid gamelist.xml
- GenericEmitter produces a LayoutPlan with correct entries
"""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from romfarmer.targets.emitters.es_gamelist import ESGamelistEmitter
from romfarmer.targets.emitters.generic import GenericEmitter
from romfarmer.targets.emitters.materializer import Materializer, link_or_copy
from romfarmer.targets.profiles.loader import ConcreteTargetProfile, TargetProfileLoader

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_config(tmp_path: Path) -> Path:
    """Create minimal frontend + device YAML files."""
    frontends = tmp_path / "frontends"
    devices = tmp_path / "devices"
    frontends.mkdir()
    devices.mkdir()

    (frontends / "testfe.yaml").write_text("""\
name: testfe
description: Test Frontend
metadata: true
media_support:
  - image
  - video
folder_mapping:
  segacd: megacd
platforms:
  psx:
    preferred_compression: chd
  snes:
    preferred_compression: 7z
""")
    (devices / "testdev.yaml").write_text("""\
name: testdev
description: Test Device
media_sizing:
  max_image_width: 320
  max_image_height: 240
unsupported_platforms:
  - ps3
  - switch
""")
    return tmp_path


@pytest.fixture
def profile_loader(tmp_config: Path) -> TargetProfileLoader:
    return TargetProfileLoader(config_dir=tmp_config)


@pytest.fixture
def rom_output_dir(tmp_path: Path) -> Path:
    """Create a fake output directory with a handful of ROM files."""
    out = tmp_path / "output"
    out.mkdir()
    for name in [
        "Game A (USA).chd",
        "Game B (USA).chd",
        "Multi Game (Disc 1).chd",
        "Multi Game (Disc 2).chd",
        "Multi Game.m3u",
    ]:
        (out / name).write_bytes(b"x" * 1024)
    return out


# ---------------------------------------------------------------------------
# TargetProfileLoader
# ---------------------------------------------------------------------------


class TestChainsFromExtensions:
    """Frontend `extensions` define what it can load; `preferred_compression` orders."""

    def test_preferred_first_then_extensions(self):
        from romfarmer.targets.profiles.loader import _chains_from_extensions

        chains = _chains_from_extensions([".zip", ".7z", ".nes"], "7z")
        assert chains[0] == ("7z",)
        assert ("zip",) in chains and ("passthrough",) in chains

    def test_disc_frontend_accepts_chd_and_raw(self):
        from romfarmer.targets.profiles.loader import _chains_from_extensions

        chains = _chains_from_extensions([".chd", ".cue", ".iso", ".m3u"], "chd")
        assert chains[0] == ("chd",)
        assert ("cue_bin",) in chains and ("iso",) in chains

    def test_preferred_none_means_passthrough_first(self):
        from romfarmer.targets.profiles.loader import _chains_from_extensions

        chains = _chains_from_extensions([".xbe", ".iso"], "none")
        assert chains[0] == ("passthrough",)
        assert ("xiso",) in chains

    def test_only_preferred_when_no_extensions(self):
        from romfarmer.targets.profiles.loader import _chains_from_extensions

        assert _chains_from_extensions([], "chd") == [("chd",)]
        assert _chains_from_extensions([], "") == []


class TestTargetProfileLoader:
    def test_loads_frontend_only(self, profile_loader: TargetProfileLoader):
        profile = profile_loader.load("testfe")
        assert profile.name == "testfe"
        assert profile.metadata_enabled is True
        assert profile.folder_mapping.get("segacd") == "megacd"

    def test_loads_frontend_plus_device(self, profile_loader: TargetProfileLoader):
        profile = profile_loader.load("testfe/testdev")
        assert "ps3" in profile.unsupported_platforms
        assert "switch" in profile.unsupported_platforms
        assert profile.media_policy.max_image_width == 320

    def test_supports_gates_platforms(self, profile_loader: TargetProfileLoader):
        from romfarmer.ir.catalog import PlatformId

        profile = profile_loader.load("testfe/testdev")
        assert profile.supports(PlatformId("psx")) is True
        assert profile.supports(PlatformId("ps3")) is False

    def test_format_preferences_from_frontend(self, profile_loader: TargetProfileLoader):
        from romfarmer.ir.catalog import PlatformId

        profile = profile_loader.load("testfe")
        prefs = profile.format_preferences(PlatformId("psx"))
        assert prefs == [("chd",)]
        prefs_snes = profile.format_preferences(PlatformId("snes"))
        assert prefs_snes == [("7z",)]

    def test_available_frontends(self, profile_loader: TargetProfileLoader):
        frontends = profile_loader.available_frontends()
        assert "testfe" in frontends

    def test_missing_frontend_returns_empty(self, profile_loader: TargetProfileLoader):
        profile = profile_loader.load("nonexistent_frontend")
        assert profile.name == "nonexistent_frontend"
        assert profile.metadata_enabled is False

    def test_metadata_dialect_es_gamelist(self, profile_loader: TargetProfileLoader):
        from romfarmer.ir.layout import MetadataDialect

        profile = profile_loader.load("testfe")
        assert profile.metadata_dialect == MetadataDialect.ES_GAMELIST


# ---------------------------------------------------------------------------
# Materializer
# ---------------------------------------------------------------------------


class TestMaterializer:
    def test_flat_style(self, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        out = tmp_path / "out"
        files = []
        for name in ["A Game.chd", "B Game.chd", "C Game.chd"]:
            p = src / name
            p.write_bytes(b"x")
            files.append(p)
        m = Materializer(style="flat")
        placed = m.emit(files, out)
        assert len(placed) == 3
        assert all(p.parent == out for p in placed)

    def test_by_letter_style(self, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        out = tmp_path / "out"
        files = []
        for name in ["Alpha.chd", "Beta.chd"]:
            p = src / name
            p.write_bytes(b"x")
            files.append(p)
        m = Materializer(style="rich")
        placed = m.emit(files, out)
        # Alpha → out/A/Alpha.chd, Beta → out/B/Beta.chd
        assert any(p.parent.name == "A" for p in placed)
        assert any(p.parent.name == "B" for p in placed)

    def test_balanced_flat_below_threshold(self, tmp_path: Path):
        """With few files, balanced style stays flat."""
        src = tmp_path / "src"
        src.mkdir()
        out = tmp_path / "out"
        files = [(src / f"Game{i}.chd") for i in range(5)]
        for f in files:
            f.write_bytes(b"x")
        m = Materializer(style="balanced", balanced_threshold=500)
        placed = m.emit(files, out)
        assert all(p.parent == out for p in placed)

    def test_link_or_copy(self, tmp_path: Path):
        src = tmp_path / "source.bin"
        src.write_bytes(b"hello world")
        dest = tmp_path / "sub" / "dest.bin"
        link_or_copy(src, dest)
        assert dest.read_bytes() == b"hello world"


# ---------------------------------------------------------------------------
# GenericEmitter
# ---------------------------------------------------------------------------


class TestGenericEmitter:
    def test_plan_layout_finds_rom_files(
        self, rom_output_dir: Path, profile_loader: TargetProfileLoader
    ):
        profile = profile_loader.load("testfe")
        emitter = GenericEmitter()
        layout = emitter.plan_layout(rom_output_dir, profile)
        names = {e.relative_path.name for e in layout.entries}
        assert "Game A (USA).chd" in names
        assert "Multi Game.m3u" in names

    def test_plan_layout_excludes_xml(self, tmp_path: Path, profile_loader: TargetProfileLoader):
        out = tmp_path / "out"
        out.mkdir()
        (out / "Game.chd").write_bytes(b"x")
        (out / "gamelist.xml").write_bytes(b"<gameList/>")
        profile = profile_loader.load("testfe")
        layout = GenericEmitter().plan_layout(out, profile)
        names = {e.relative_path.name for e in layout.entries}
        assert "gamelist.xml" not in names
        assert "Game.chd" in names

    def test_empty_dir_returns_empty_plan(
        self, tmp_path: Path, profile_loader: TargetProfileLoader
    ):
        out = tmp_path / "empty"
        out.mkdir()
        layout = GenericEmitter().plan_layout(out, profile_loader.load("testfe"))
        assert layout.entries == ()


# ---------------------------------------------------------------------------
# ESGamelistEmitter
# ---------------------------------------------------------------------------


class TestESGamelistEmitter:
    def test_emits_gamelist_xml(self, rom_output_dir: Path, profile_loader: TargetProfileLoader):
        from romfarmer.analysis.knowledge import KnowledgeBase

        profile = profile_loader.load("testfe")
        emitter = ESGamelistEmitter()
        layout = emitter.plan_layout(rom_output_dir, profile)
        kb = KnowledgeBase()
        artifacts = emitter.emit_metadata(layout, rom_output_dir, kb, profile)
        assert len(artifacts) == 1
        assert artifacts[0].kind == "gamelist"
        gamelist_path = rom_output_dir / "gamelist.xml"
        assert gamelist_path.exists()

    def test_gamelist_xml_is_valid(self, rom_output_dir: Path, profile_loader: TargetProfileLoader):
        from romfarmer.analysis.knowledge import KnowledgeBase

        profile = profile_loader.load("testfe")
        emitter = ESGamelistEmitter()
        layout = emitter.plan_layout(rom_output_dir, profile)
        emitter.emit_metadata(layout, rom_output_dir, KnowledgeBase(), profile)
        gamelist_path = rom_output_dir / "gamelist.xml"
        tree = ET.parse(str(gamelist_path))
        root = tree.getroot()
        assert root.tag == "gameList"
        game_names = [g.findtext("name") for g in root.findall("game")]
        assert "Game A (USA)" in game_names
        assert "Multi Game" in game_names

    def test_m3u_hides_individual_chds(
        self, rom_output_dir: Path, profile_loader: TargetProfileLoader
    ):
        """CHDs with a sibling M3U must be marked hidden."""
        from romfarmer.analysis.knowledge import KnowledgeBase

        profile = profile_loader.load("testfe")
        emitter = ESGamelistEmitter()
        layout = emitter.plan_layout(rom_output_dir, profile)
        emitter.emit_metadata(layout, rom_output_dir, KnowledgeBase(), profile)
        tree = ET.parse(str(rom_output_dir / "gamelist.xml"))
        root = tree.getroot()
        for game in root.findall("game"):
            path = game.findtext("path") or ""
            hidden = game.findtext("hidden")
            if "Disc" in path:
                assert hidden == "true", f"Expected {path} to be hidden"

    def test_no_metadata_skips_gamelist(self, tmp_path: Path, profile_loader: TargetProfileLoader):
        """Profiles with metadata_enabled=False should not write gamelist."""
        from romfarmer.analysis.knowledge import KnowledgeBase

        # Create a profile with metadata disabled
        profile = ConcreteTargetProfile(
            name="no-metadata",
            metadata_enabled=False,
        )
        out = tmp_path / "out"
        out.mkdir()
        (out / "Game.chd").write_bytes(b"x")
        emitter = ESGamelistEmitter()
        from romfarmer.ir.layout import LayoutPlan

        layout = LayoutPlan(root_name="out", entries=())
        artifacts = emitter.emit_metadata(layout, out, KnowledgeBase(), profile)
        assert artifacts == []
        assert not (out / "gamelist.xml").exists()
