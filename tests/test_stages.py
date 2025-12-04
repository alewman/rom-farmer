"""Tests for processing stages."""

import tempfile
from pathlib import Path
from textwrap import dedent

import pytest

from romfarmer.config import (
    CompressionFormat,
    DATConfig,
    DATSource,
    ListFileConfig,
    OrganizationConfig,
    OrganizationStyle,
    PlatformConfig,
    SourceConfig,
    SystemType,
    TargetProfile,
)
from romfarmer.dat_parser import DATFile, DATGame, DATRom
from romfarmer.stages import (
    ApplyListsStage,
    FilterDATStage,
    OrganizeStage,
    StageContext,
    StageStatus,
)


@pytest.fixture
def sample_dat_file():
    """Create sample DAT file."""
    games = [
        DATGame(
            name="Contra (USA)",
            roms=[
                DATRom(
                    name="Contra (USA).zip",  # Match ZIP filename
                    size=131088,
                    crc="cba3980f",
                )
            ],
        ),
        DATGame(
            name="Super Mario Bros. (USA)",
            roms=[
                DATRom(
                    name="Super Mario Bros. (USA).zip",  # Match ZIP filename
                    size=40976,
                    crc="3337ec46",
                )
            ],
        ),
        DATGame(
            name="Zelda (USA)",
            roms=[
                DATRom(
                    name="Zelda (USA).zip",  # Match ZIP filename
                    size=131088,
                    crc="d7ae93d1",
                )
            ],
        ),
    ]

    return DATFile(
        name="Test NES DAT",
        games=games,
    )


@pytest.fixture
def platform_config(tmp_path):
    """Create test platform configuration."""
    # Create required directories for Pydantic validation
    (tmp_path / "source").mkdir()
    (tmp_path / "lists").mkdir()
    (tmp_path / "output").mkdir()
    
    return PlatformConfig(
        name="nes",
        system_type=SystemType.SIMPLE,
        dat=DATConfig(source=DATSource.RETOOL_1G1R_ENG),
        sources=[
            SourceConfig(
                path=tmp_path / "source",
                type="myrient",
            )
        ],
        lists=ListFileConfig(directory=tmp_path / "lists"),
        targets=[
            TargetProfile(
                name="test",
                output_path=tmp_path / "output",
                organization=OrganizationConfig(
                    style=OrganizationStyle.BALANCED,
                    max_files_per_group=50,
                    create_subdirs=True,
                    subdir_prefix="_",
                ),
                metadata=True,
                enabled=True,
            )
        ],
        extract_archives=False,
        enabled=True,
    )


class TestFilterDATStage:
    """Tests for FilterDATStage."""

    def test_skip_if_no_dat(self, tmp_path, platform_config):
        """Test stage skips if no DAT file."""
        context = StageContext(
            platform_name="nes",
            platform_config=platform_config,
            target_name="test",
            source_dir=tmp_path / "source",
            work_dir=tmp_path / "work",
            output_dir=tmp_path / "output",
            dat_file=None,  # No DAT
            source_files=[],
        )

        stage = FilterDATStage()
        result = stage.execute(context)

        assert result.status == StageStatus.SKIPPED


class TestApplyListsStage:
    """Tests for ApplyListsStage."""

    def test_delete_list(self, tmp_path, platform_config):
        """Test delete list functionality."""
        # Create work directory with files
        work_dir = tmp_path / "work"
        work_dir.mkdir()

        (work_dir / "Contra (USA).zip").write_text("mock")
        (work_dir / "Pirate Game (Asia).zip").write_text("mock")
        (work_dir / "Super Mario Bros. (USA).zip").write_text("mock")

        # Lists dir already created by fixture
        lists_dir = tmp_path / "lists"
        delete_list = lists_dir / "nes-delete"
        delete_list.write_text("Pirate Game (Asia)\n")

        # Update platform config
        platform_config.lists = ListFileConfig(directory=lists_dir)

        # Create context
        context = StageContext(
            platform_name="nes",
            platform_config=platform_config,
            target_name="test",
            source_dir=tmp_path / "source",
            work_dir=work_dir,
            output_dir=tmp_path / "output",
            filtered_files=list(work_dir.glob("*.zip")),
        )

        # Execute stage
        stage = ApplyListsStage()
        result = stage.execute(context)

        # Verify
        assert result.status == StageStatus.SUCCESS
        assert not (work_dir / "Pirate Game (Asia).zip").exists()
        assert (work_dir / "Contra (USA).zip").exists()
        assert (work_dir / "Super Mario Bros. (USA).zip").exists()

    def test_add_list_creates_subdirectory(self, tmp_path, platform_config):
        """Test add list creates subdirectory."""
        # Create work directory with files
        work_dir = tmp_path / "work"
        work_dir.mkdir()

        (work_dir / "Contra (USA).zip").write_text("mock")
        (work_dir / "Super Mario Bros. (USA).zip").write_text("mock")

        # Lists dir already created by fixture
        lists_dir = tmp_path / "lists"
        add_list = lists_dir / "nes+Best-Games"
        add_list.write_text("Contra (USA)\nSuper Mario Bros. (USA)\n")

        # Update platform config
        platform_config.lists = ListFileConfig(directory=lists_dir)

        # Create context
        context = StageContext(
            platform_name="nes",
            platform_config=platform_config,
            target_name="test",
            source_dir=tmp_path / "source",
            work_dir=work_dir,
            output_dir=tmp_path / "output",
            filtered_files=list(work_dir.glob("*.zip")),
        )

        # Execute stage
        stage = ApplyListsStage()
        result = stage.execute(context)

        # Verify
        assert result.status == StageStatus.SUCCESS
        assert (work_dir / "_Best-Games").is_dir()
        assert (work_dir / "_Best-Games" / "Contra (USA).zip").exists()
        assert (work_dir / "_Best-Games" / "Super Mario Bros. (USA).zip").exists()


class TestOrganizeStage:
    """Tests for OrganizeStage."""

    def test_organize_flat(self, tmp_path, platform_config):
        """Test flat organization."""
        # Create work directory with files
        work_dir = tmp_path / "work"
        work_dir.mkdir()
        output_dir = tmp_path / "output"

        (work_dir / "Contra (USA).zip").write_text("mock")
        (work_dir / "Super Mario Bros. (USA).zip").write_text("mock")

        # Update platform config for flat organization
        platform_config.targets[0].organization.style = OrganizationStyle.FLAT

        # Create context
        context = StageContext(
            platform_name="nes",
            platform_config=platform_config,
            target_name="test",
            source_dir=tmp_path / "source",
            work_dir=work_dir,
            output_dir=output_dir,
            filtered_files=list(work_dir.glob("*.zip")),
        )

        # Execute stage
        stage = OrganizeStage()
        result = stage.execute(context)

        # Verify
        assert result.status == StageStatus.SUCCESS
        assert (output_dir / "Contra (USA).zip").exists()
        assert (output_dir / "Super Mario Bros. (USA).zip").exists()

    def test_organize_balanced(self, tmp_path, platform_config):
        """Test balanced organization."""
        # Create work directory with files
        work_dir = tmp_path / "work"
        work_dir.mkdir()
        output_dir = tmp_path / "output"

        (work_dir / "Contra (USA).zip").write_text("mock")
        (work_dir / "Super Mario Bros. (USA).zip").write_text("mock")
        (work_dir / "Zelda (USA).zip").write_text("mock")
        (work_dir / "1942 (USA).zip").write_text("mock")

        # Create context
        context = StageContext(
            platform_name="nes",
            platform_config=platform_config,
            target_name="test",
            source_dir=tmp_path / "source",
            work_dir=work_dir,
            output_dir=output_dir,
            filtered_files=list(work_dir.glob("*.zip")),
        )

        # Execute stage
        stage = OrganizeStage()
        result = stage.execute(context)

        # Verify
        assert result.status == StageStatus.SUCCESS
        assert (output_dir / "A-E" / "Contra (USA).zip").exists()
        assert (output_dir / "N-Z" / "Super Mario Bros. (USA).zip").exists()
        assert (output_dir / "N-Z" / "Zelda (USA).zip").exists()
        assert (output_dir / "#" / "1942 (USA).zip").exists()

    def test_organize_minimal(self, tmp_path, platform_config):
        """Test minimal organization with max files per group."""
        # Create work directory with files
        work_dir = tmp_path / "work"
        work_dir.mkdir()
        output_dir = tmp_path / "output"

        # Create files starting with different letters
        letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O']
        for i, letter in enumerate(letters):
            (work_dir / f"{letter} Game {i} (USA).zip").write_text("mock")

        # Update platform config for minimal organization
        platform_config.targets[0].organization.style = OrganizationStyle.MINIMAL
        platform_config.targets[0].organization.max_files_per_group = 5

        # Create context
        context = StageContext(
            platform_name="nes",
            platform_config=platform_config,
            target_name="test",
            source_dir=tmp_path / "source",
            work_dir=work_dir,
            output_dir=output_dir,
            filtered_files=list(work_dir.glob("*.zip")),
        )

        # Execute stage
        stage = OrganizeStage()
        result = stage.execute(context)

        # Verify
        assert result.status == StageStatus.SUCCESS
        # Should create multiple groups due to 5 file limit
        groups = [d for d in output_dir.iterdir() if d.is_dir()]
        assert len(groups) >= 3  # At least 3 groups for 15 files with max 5 each
