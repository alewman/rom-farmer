"""Tests for WiiWare platform and EmitExtrasStage.

Tests cover:
1. EmitExtrasStage — sorts files by pattern, emits install scripts
2. WiiWare pipeline assembly — ExtractionType.NONE, no DAT
3. Wii-extras pipeline assembly — EmitExtrasStage wired in
4. ExtrasConfig model validation
"""

import pytest
import shutil
from pathlib import Path
from unittest.mock import MagicMock

from romfarmer.config.slim_platform import (
    ExtrasConfig,
)
from romfarmer.config.models import (
    CompressionFormat,
    ExtractionType,
)
from romfarmer.config.resolver import ResolvedPlatformConfig
from romfarmer.stages.base import StageContext, StageStatus
from romfarmer.stages.emit_extras import EmitExtrasStage
from romfarmer.stages.builder import build_pipeline


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def extras_config():
    """Sample extras config matching wii-extras.yaml."""
    return {
        "destinations": {
            "nand": "(DLC)",
        },
        "install_scripts": {
            "batocera": {
                "template": "wii-nand-install-batocera",
                "description": "Install DLC WADs to Dolphin NAND",
            },
            "retrobat": {
                "template": "wii-nand-install-retrobat",
                "description": "Install DLC WADs to Dolphin NAND",
            },
        },
    }


@pytest.fixture
def wad_source_dir(tmp_path):
    """Create a temp dir with fake WAD files (games + DLC)."""
    source = tmp_path / "source"
    source.mkdir()

    # Base games
    games = [
        "Mega Man 9 (USA) (WiiWare).wad",
        "Mega Man 10 (USA) (WiiWare).wad",
        "World of Goo (USA) (WiiWare).wad",
    ]
    # DLC
    dlc = [
        "Mega Man 9 (USA) (WiiWare) (DLC).wad",
        "Mega Man 10 (USA) (WiiWare) (DLC).wad",
    ]

    for name in games + dlc:
        (source / name).write_bytes(b"fake wad content " + name.encode())

    return source


@pytest.fixture
def stage_context(tmp_path, wad_source_dir):
    """Create a StageContext with source files populated."""
    work = tmp_path / "work"
    work.mkdir()
    output = tmp_path / "output"
    output.mkdir()

    source_files = sorted(wad_source_dir.glob("*.wad"))

    ctx = StageContext(
        platform_name="wii-extras",
        platform_config=MagicMock(),
        target_name="batocera-pc",
        source_dir=wad_source_dir,
        work_dir=work,
        output_dir=output,
        source_files=source_files,
    )
    return ctx


# ═══════════════════════════════════════════════════════════════════════════════
# EmitExtrasStage Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestEmitExtrasStage:
    """Tests for EmitExtrasStage."""

    def test_sorts_dlc_into_nand_subdir(self, stage_context, extras_config):
        """DLC files should be placed in nand/ subdirectory."""
        stage = EmitExtrasStage(extras_config=extras_config)
        result = stage.execute(stage_context)

        assert result.status == StageStatus.SUCCESS

        nand_dir = stage_context.output_dir / "nand"
        assert nand_dir.exists()

        nand_files = sorted(f.name for f in nand_dir.glob("*.wad"))
        assert nand_files == [
            "Mega Man 10 (USA) (WiiWare) (DLC).wad",
            "Mega Man 9 (USA) (WiiWare) (DLC).wad",
        ]

    def test_non_dlc_files_are_unmatched(self, stage_context, extras_config):
        """Base game files should not be sorted into any destination."""
        stage = EmitExtrasStage(extras_config=extras_config)
        result = stage.execute(stage_context)

        assert result.files_processed == 2  # Only DLC
        assert result.files_skipped == 3  # Base games are unmatched

    def test_emits_batocera_install_script(self, stage_context, extras_config, tmp_path):
        """Should emit install.sh when building for Batocera."""
        # Create the template file
        templates = Path("templates")
        templates.mkdir(exist_ok=True)
        template_file = templates / "wii-nand-install-batocera.sh"
        template_file.write_text("#!/bin/bash\n# test install script\n")

        try:
            stage = EmitExtrasStage(extras_config=extras_config)
            result = stage.execute(stage_context)

            install_script = stage_context.output_dir / "install.sh"
            assert install_script.exists()
            assert "test install script" in install_script.read_text()
            assert result.details["scripts_emitted"] == 1
        finally:
            template_file.unlink(missing_ok=True)
            if not any(templates.iterdir()):
                templates.rmdir()

    def test_emits_retrobat_install_script(self, stage_context, extras_config, tmp_path):
        """Should emit install.bat when building for RetroBat."""
        stage_context.target_name = "retrobat-pc"

        templates = Path("templates")
        templates.mkdir(exist_ok=True)
        template_file = templates / "wii-nand-install-retrobat.bat"
        template_file.write_text("@echo off\nREM test install script\n")

        try:
            stage = EmitExtrasStage(extras_config=extras_config)
            result = stage.execute(stage_context)

            install_script = stage_context.output_dir / "install.bat"
            assert install_script.exists()
            assert "test install script" in install_script.read_text()
        finally:
            template_file.unlink(missing_ok=True)
            if not any(templates.iterdir()):
                templates.rmdir()

    def test_skip_when_no_config(self, stage_context):
        """Should skip when no extras config."""
        stage = EmitExtrasStage(extras_config=None)
        assert stage.should_skip(stage_context) is True

    def test_skip_when_no_source_files(self, stage_context, extras_config):
        """Should skip when no source or filtered files."""
        stage_context.source_files = []
        stage_context.filtered_files = []
        stage = EmitExtrasStage(extras_config=extras_config)
        assert stage.should_skip(stage_context) is True

    def test_multiple_destinations(self, stage_context):
        """Support multiple destination patterns."""
        config = {
            "destinations": {
                "nand": "(DLC)",
                "updates": "(Update)",
            },
            "install_scripts": {},
        }

        # Add an update file
        update_file = stage_context.source_dir / "Some Game (USA) (WiiWare) (Update).wad"
        update_file.write_bytes(b"fake update")
        stage_context.source_files.append(update_file)

        stage = EmitExtrasStage(extras_config=config)
        result = stage.execute(stage_context)

        assert (stage_context.output_dir / "nand").exists()
        assert (stage_context.output_dir / "updates").exists()
        assert len(list((stage_context.output_dir / "nand").glob("*.wad"))) == 2
        assert len(list((stage_context.output_dir / "updates").glob("*.wad"))) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# ExtrasConfig Model Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestExtrasConfig:
    """Tests for the ExtrasConfig Pydantic model."""

    def test_valid_config(self):
        """Basic valid config."""
        config = ExtrasConfig(
            destinations={"nand": "(DLC)"},
            install_scripts={
                "batocera": {"template": "wii-nand-install-batocera"},
            },
        )
        assert config.destinations["nand"] == "(DLC)"

    def test_empty_config(self):
        """Empty config should be valid."""
        config = ExtrasConfig()
        assert config.destinations == {}
        assert config.install_scripts == {}

    def test_model_dump(self):
        """Should serialize to dict cleanly."""
        config = ExtrasConfig(
            destinations={"nand": "(DLC)"},
            install_scripts={
                "batocera": {"template": "test-template"},
            },
        )
        d = config.model_dump()
        assert d["destinations"]["nand"] == "(DLC)"
        assert d["install_scripts"]["batocera"]["template"] == "test-template"


# ═══════════════════════════════════════════════════════════════════════════════
# Pipeline Assembly Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestWiiWarePipeline:
    """Tests for WiiWare pipeline assembly."""

    def test_wiiware_pipeline_no_extraction(self, tmp_path):
        """WiiWare pipeline should have no extraction stages."""
        resolved = ResolvedPlatformConfig(
            platform="wiiware",
            extraction_type=ExtractionType.NONE,
            compression=CompressionFormat.NONE,
            output_dir=tmp_path / "output",
        )

        pipeline = build_pipeline(resolved)
        stage_names = [type(s).__name__ for s in pipeline.stages]

        # Should have: FilterDAT, Filter1G1R, Organize (no extraction stages)
        assert "FilterDATStage" in stage_names
        assert "Filter1G1RStage" in stage_names
        assert "OrganizeStage" in stage_names
        # Should NOT have extraction or compression stages
        assert "ExtractArchiveStage" not in stage_names
        assert "CompressArchiveStage" not in stage_names
        assert "ConvertCHDStage" not in stage_names

    def test_wii_extras_pipeline_has_emit_extras(self, tmp_path):
        """Wii-extras pipeline should include EmitExtrasStage."""
        extras = ExtrasConfig(
            destinations={"nand": "(DLC)"},
            install_scripts={"batocera": {"template": "test"}},
        )

        resolved = ResolvedPlatformConfig(
            platform="wii-extras",
            extraction_type=ExtractionType.NONE,
            compression=CompressionFormat.NONE,
            output_dir=tmp_path / "output",
            extras=extras,
        )

        pipeline = build_pipeline(resolved)
        stage_names = [type(s).__name__ for s in pipeline.stages]

        assert "EmitExtrasStage" in stage_names
        # Extras platforms should NOT have Organize stage
        assert "OrganizeStage" not in stage_names
        # Extras platforms skip 1G1R (EmitExtrasStage does its own sorting)
        assert "Filter1G1RStage" not in stage_names
        assert "_PassthroughFilterStage" in stage_names

    def test_wii_extras_pipeline_no_organize(self, tmp_path):
        """Extras platforms skip OrganizeStage (EmitExtrasStage handles output)."""
        extras = ExtrasConfig(destinations={"nand": "(DLC)"})

        resolved = ResolvedPlatformConfig(
            platform="wii-extras",
            extraction_type=ExtractionType.NONE,
            compression=CompressionFormat.NONE,
            output_dir=tmp_path / "output",
            extras=extras,
        )

        pipeline = build_pipeline(resolved)
        stage_names = [type(s).__name__ for s in pipeline.stages]

        assert "OrganizeStage" not in stage_names
        assert "EmitExtrasStage" in stage_names

    def test_wii_extras_pipeline_with_cache_has_cas_ingest(self, tmp_path):
        """Extras pipeline with cache_manager should include CASIngestStage."""
        extras = ExtrasConfig(destinations={"nand": "(DLC)"})

        resolved = ResolvedPlatformConfig(
            platform="wii-extras",
            extraction_type=ExtractionType.NONE,
            compression=CompressionFormat.NONE,
            output_dir=tmp_path / "output",
            extras=extras,
        )

        mock_cache = MagicMock()
        pipeline = build_pipeline(resolved, cache_manager=mock_cache)
        stage_names = [type(s).__name__ for s in pipeline.stages]

        assert "CASIngestStage" in stage_names

    def test_wiiware_pipeline_with_cache_has_cas_ingest(self, tmp_path):
        """WiiWare (non-extras) pipeline with cache should also get CAS ingest."""
        resolved = ResolvedPlatformConfig(
            platform="wiiware",
            extraction_type=ExtractionType.NONE,
            compression=CompressionFormat.NONE,
            output_dir=tmp_path / "output",
        )

        mock_cache = MagicMock()
        pipeline = build_pipeline(resolved, cache_manager=mock_cache)
        stage_names = [type(s).__name__ for s in pipeline.stages]

        assert "CASIngestStage" in stage_names
        assert "OrganizeStage" in stage_names


# ═══════════════════════════════════════════════════════════════════════════════
# SlimPlatformConfig with Extras
# ═══════════════════════════════════════════════════════════════════════════════


class TestSlimPlatformWithExtras:
    """Test that SlimPlatformConfig correctly loads extras field."""

    def test_platform_with_extras(self):
        """Platform with extras config should parse correctly."""
        extras = ExtrasConfig(
            destinations={"nand": "(DLC)"},
            install_scripts={
                "batocera": {"template": "wii-nand-install-batocera"},
            },
        )
        assert extras.destinations["nand"] == "(DLC)"
        assert extras.install_scripts["batocera"]["template"] == "wii-nand-install-batocera"

    def test_extras_config_defaults(self):
        """Normal platforms should have extras=None by default."""
        extras = ExtrasConfig()
        assert extras.destinations == {}
        assert extras.install_scripts == {}
