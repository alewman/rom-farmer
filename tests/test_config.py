"""Tests for configuration system."""

import tempfile
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from romgroomer.config import (
    BuildConfig,
    ConfigLoader,
    DATSource,
    ExtractionType,
    OrganizationStyle,
    PlatformConfig,
    SystemType,
)


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary config directory structure."""
    config_root = tmp_path / "config"
    config_root.mkdir()
    (config_root / "builds").mkdir()
    (config_root / "platforms").mkdir()
    return config_root


@pytest.fixture
def sample_platform_config():
    """Sample platform configuration."""
    return {
        "name": "nes",
        "system_type": "simple",
        "dat": {
            "source": "retool_1g1r_eng",
            "expected_count": 1761,
        },
        "sources": [
            {
                "path": "/tmp/source",
                "type": "myrient",
                "recursive": False,
            }
        ],
        "extract_archives": False,
        "multi_disc_handling": False,
        "targets": [
            {
                "name": "rocknix",
                "output_path": "/tmp/output",
                "organization": {
                    "style": "balanced",
                    "max_files_per_group": 100,
                    "create_subdirs": True,
                },
                "metadata": True,
                "enabled": True,
            }
        ],
        "enabled": True,
    }


@pytest.fixture
def sample_build_config():
    """Sample build configuration."""
    return {
        "name": "test-build",
        "platforms": ["nes", "saturn"],
        "global_dat_priority": ["retool_1g1r_eng"],
        "workspace": "/tmp",
        "dat_directory": "/tmp",
        "checkpoint_enabled": True,
        "parallel_platforms": False,
        "max_workers": 4,
    }


class TestPlatformConfig:
    """Tests for PlatformConfig model."""

    def test_valid_simple_system(self, sample_platform_config, tmp_path):
        """Test valid simple system configuration."""
        # Create required directories
        (tmp_path / "source").mkdir()
        (tmp_path / "output").mkdir()

        # Update paths
        sample_platform_config["sources"][0]["path"] = tmp_path / "source"
        sample_platform_config["targets"][0]["output_path"] = tmp_path / "output"

        config = PlatformConfig(**sample_platform_config)
        assert config.name == "nes"
        assert config.system_type == SystemType.SIMPLE
        assert not config.extract_archives

    def test_simple_system_migration(self, sample_platform_config, tmp_path):
        """Test that simple systems with extraction get migrated correctly."""
        import warnings
        # Create required directories
        (tmp_path / "source").mkdir()
        (tmp_path / "output").mkdir()

        sample_platform_config["sources"][0]["path"] = tmp_path / "source"
        sample_platform_config["targets"][0]["output_path"] = tmp_path / "output"
        sample_platform_config["extract_archives"] = True

        # Should emit deprecation warning but not fail
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            config = PlatformConfig(**sample_platform_config)
            # Verify deprecation warning was emitted
            assert any("deprecated" in str(warning.message).lower() for warning in w)
            # Extraction should be migrated from legacy field
            assert config.extraction.enabled == True

    def test_medium_system_migration(self, sample_platform_config, tmp_path):
        """Test that medium systems auto-detect extraction type when not explicitly disabled."""
        import warnings
        # Create required directories
        (tmp_path / "source").mkdir()
        (tmp_path / "output").mkdir()

        sample_platform_config["sources"][0]["path"] = tmp_path / "source"
        sample_platform_config["targets"][0]["output_path"] = tmp_path / "output"
        sample_platform_config["system_type"] = "medium"
        # Don't set extract_archives - let system_type auto-detect
        if "extract_archives" in sample_platform_config:
            del sample_platform_config["extract_archives"]

        # Should emit deprecation warning but not fail
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            config = PlatformConfig(**sample_platform_config)
            # Verify deprecation warning was emitted for system_type
            assert any("deprecated" in str(warning.message).lower() for warning in w)
            # Medium system should auto-enable extraction when not explicitly set
            assert config.extraction.enabled == True
            # Should auto-detect cartridge type (no CHD compression)
            assert config.extraction.type == ExtractionType.CARTRIDGE

    def test_source_path_must_exist(self, sample_platform_config, tmp_path):
        """Test that source path must exist."""
        (tmp_path / "output").mkdir()
        sample_platform_config["sources"][0]["path"] = tmp_path / "nonexistent"
        sample_platform_config["targets"][0]["output_path"] = tmp_path / "output"

        with pytest.raises(ValidationError, match="Source path not found"):
            PlatformConfig(**sample_platform_config)


class TestBuildConfig:
    """Tests for BuildConfig model."""

    def test_valid_build_config(self, sample_build_config):
        """Test valid build configuration."""
        config = BuildConfig(**sample_build_config)
        assert config.name == "test-build"
        assert len(config.platforms) == 2
        assert config.global_dat_priority[0] == DATSource.RETOOL_1G1R_ENG

    def test_workspace_must_exist(self, sample_build_config):
        """Test that workspace must exist."""
        sample_build_config["workspace"] = "/nonexistent/path"

        with pytest.raises(ValidationError, match="Directory not found"):
            BuildConfig(**sample_build_config)

    def test_dat_directory_must_exist(self, sample_build_config):
        """Test that DAT directory must exist."""
        sample_build_config["dat_directory"] = "/nonexistent/path"

        with pytest.raises(ValidationError, match="Directory not found"):
            BuildConfig(**sample_build_config)


class TestConfigLoader:
    """Tests for ConfigLoader."""

    def test_load_yaml_with_env_vars(self, temp_config_dir, monkeypatch):
        """Test loading YAML with environment variable substitution."""
        monkeypatch.setenv("TEST_PATH", "/test/path")

        yaml_content = """
        name: test
        path: ${TEST_PATH}/subdir
        """
        config_file = temp_config_dir / "test.yaml"
        config_file.write_text(yaml_content)

        loader = ConfigLoader(temp_config_dir)
        data = loader._load_yaml(config_file)

        assert data["path"] == "/test/path/subdir"

    def test_resolve_paths(self, temp_config_dir):
        """Test path resolution."""
        loader = ConfigLoader(temp_config_dir)

        config = {
            "name": "test",
            "path": "relative/path",
            "other": "not a path",
        }

        resolved = loader._resolve_paths(config)
        assert isinstance(resolved["path"], Path)
        assert resolved["path"].is_absolute()
        assert resolved["other"] == "not a path"

    def test_load_platform_config(self, temp_config_dir, sample_platform_config, tmp_path):
        """Test loading platform configuration from file."""
        # Create required directories
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        source_dir.mkdir()
        output_dir.mkdir()

        # Update paths
        sample_platform_config["sources"][0]["path"] = str(source_dir)
        sample_platform_config["targets"][0]["output_path"] = str(output_dir)

        # Write config file
        config_file = temp_config_dir / "platforms" / "nes.yaml"
        with open(config_file, "w") as f:
            yaml.dump(sample_platform_config, f)

        # Load config
        loader = ConfigLoader(temp_config_dir)
        config = loader.load_platform_config("nes")

        assert config.name == "nes"
        assert config.system_type == SystemType.SIMPLE
        assert isinstance(config.sources[0].path, Path)
        assert config.sources[0].path == source_dir

    def test_load_build_config(self, temp_config_dir, sample_build_config):
        """Test loading build configuration from file."""
        # Write config file
        config_file = temp_config_dir / "builds" / "test-build.yaml"
        with open(config_file, "w") as f:
            yaml.dump(sample_build_config, f)

        # Load config
        loader = ConfigLoader(temp_config_dir)
        config = loader.load_build_config("test-build")

        assert config.name == "test-build"
        assert len(config.platforms) == 2
        assert isinstance(config.workspace, Path)

    def test_file_not_found(self, temp_config_dir):
        """Test loading nonexistent file."""
        loader = ConfigLoader(temp_config_dir)

        with pytest.raises(FileNotFoundError):
            loader.load_platform_config("nonexistent")


class TestEnumTypes:
    """Tests for enum types."""

    def test_dat_source_enum(self):
        """Test DATSource enum values."""
        assert DATSource.RETOOL_1G1R_ENG == "retool_1g1r_eng"
        assert DATSource.RETOOL_1G1R_USA == "retool_1g1r_usa"
        assert DATSource.MANUAL_SCAN == "manual_scan"

    def test_organization_style_enum(self):
        """Test OrganizationStyle enum values."""
        assert OrganizationStyle.RICH == "rich"
        assert OrganizationStyle.BALANCED == "balanced"
        assert OrganizationStyle.MINIMAL == "minimal"
        assert OrganizationStyle.FLAT == "flat"

    def test_system_type_enum(self):
        """Test SystemType enum values."""
        assert SystemType.SIMPLE == "simple"
        assert SystemType.MEDIUM == "medium"
        assert SystemType.COMPLEX == "complex"
        assert SystemType.VERY_COMPLEX == "very_complex"
