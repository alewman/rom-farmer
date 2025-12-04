"""Tests for configuration override merging."""

import pytest
from pathlib import Path
from unittest.mock import patch

from romgroomer.config.models import (
    CompressionConfig,
    CompressionFormat,
    DATConfig,
    DATSource,
    ExtractionConfig,
    ExtractionType,
    ListFileConfig,
    OrganizationConfig,
    OrganizationStyle,
    PlatformConfig,
    SelectionConfig,
    SelectionStrategy,
    SourceConfig,
    TargetProfile,
)
from romgroomer.config.overrides import (
    apply_overrides,
    _merge_dat_config,
    _merge_compression_config,
    _merge_selection_config,
    _process_targets_override,
)


@pytest.fixture
def base_platform_config(tmp_path):
    """Create a base platform configuration for testing."""
    # Create actual temp directories so validation passes
    source_dir = tmp_path / "roms"
    source_dir.mkdir()
    output_batocera = tmp_path / "output" / "batocera"
    output_batocera.mkdir(parents=True)
    output_rocknix = tmp_path / "output" / "rocknix"
    output_rocknix.mkdir(parents=True)
    
    return PlatformConfig(
        name="test_platform",
        enabled=True,
        dat=DATConfig(source=DATSource.RETOOL_1G1R_ENG),
        sources=[
            SourceConfig(path=source_dir, type="myrient")
        ],
        compression=CompressionConfig(format=CompressionFormat.ZIP),
        targets=[
            TargetProfile(
                name="batocera",
                output_path=output_batocera,
                organization=OrganizationConfig(style=OrganizationStyle.FLAT)
            ),
            TargetProfile(
                name="rocknix",
                output_path=output_rocknix,
                organization=OrganizationConfig(style=OrganizationStyle.BALANCED)
            ),
        ]
    )


class TestApplyOverrides:
    """Tests for the main apply_overrides function."""
    
    def test_empty_overrides_returns_unchanged(self, base_platform_config):
        """Empty overrides should return the same config."""
        result = apply_overrides(base_platform_config, {})
        assert result.name == base_platform_config.name
        assert result.enabled == base_platform_config.enabled
    
    def test_simple_field_override(self, base_platform_config):
        """Simple fields should be directly replaced."""
        result = apply_overrides(base_platform_config, {"enabled": False})
        assert result.enabled is False
        # Original should be unchanged (immutable)
        assert base_platform_config.enabled is True
    
    def test_compression_format_override(self, base_platform_config):
        """Compression format can be overridden with string or enum."""
        result = apply_overrides(
            base_platform_config,
            {"compression": {"format": "7z"}}
        )
        assert result.compression.format == CompressionFormat.SEVENZ
    
    def test_dat_override_preserves_unspecified_fields(self, base_platform_config):
        """DAT override should only change specified fields."""
        result = apply_overrides(
            base_platform_config,
            {"dat": {"expected_count": 100}}
        )
        assert result.dat.expected_count == 100
        assert result.dat.source == DATSource.RETOOL_1G1R_ENG  # Preserved
    
    def test_selection_override_creates_new(self, base_platform_config):
        """Selection override should create new SelectionConfig if none exists."""
        assert base_platform_config.selection is None
        result = apply_overrides(
            base_platform_config,
            {"selection": {"strategy": "first", "limit": 10}}
        )
        assert result.selection is not None
        assert result.selection.strategy == SelectionStrategy.FIRST
        assert result.selection.limit == 10
    
    def test_targets_filter_by_name(self, base_platform_config):
        """List of strings should filter existing targets by name."""
        result = apply_overrides(
            base_platform_config,
            {"targets": ["batocera"]}
        )
        assert len(result.targets) == 1
        assert result.targets[0].name == "batocera"
    
    def test_targets_full_replacement(self, base_platform_config):
        """List of dicts should replace targets entirely."""
        result = apply_overrides(
            base_platform_config,
            {
                "targets": [
                    {
                        "name": "custom",
                        "output_path": "/output/custom",
                        "organization": {"style": "flat"}
                    }
                ]
            }
        )
        assert len(result.targets) == 1
        assert result.targets[0].name == "custom"
        assert result.targets[0].output_path == Path("/output/custom")
    
    def test_targets_organization_shorthand(self, base_platform_config):
        """Organization can be specified as string shorthand."""
        result = apply_overrides(
            base_platform_config,
            {
                "targets": [
                    {
                        "name": "test",
                        "output_path": "/output/test",
                        "organization": "flat"  # Shorthand
                    }
                ]
            }
        )
        assert result.targets[0].organization.style == OrganizationStyle.FLAT
    
    def test_lists_can_be_disabled(self, base_platform_config, tmp_path):
        """Setting lists to None should disable list processing."""
        # First add lists with a real directory
        lists_dir = tmp_path / "lists"
        lists_dir.mkdir()
        config_with_lists = base_platform_config.model_copy(
            update={"lists": ListFileConfig(directory=lists_dir)}
        )
        result = apply_overrides(config_with_lists, {"lists": None})
        assert result.lists is None
    
    def test_sources_full_replacement(self, base_platform_config, tmp_path):
        """Sources should be completely replaced when specified."""
        # Create real directories for sources
        src1 = tmp_path / "source1"
        src1.mkdir()
        src2 = tmp_path / "source2"
        src2.mkdir()
        result = apply_overrides(
            base_platform_config,
            {
                "sources": [
                    {"path": str(src1), "type": "custom"},
                    {"path": str(src2), "type": "archive"}
                ]
            }
        )
        assert len(result.sources) == 2
        assert result.sources[0].path == src1
        assert result.sources[1].path == src2


class TestMergeDatConfig:
    """Tests for DAT config merging."""
    
    def test_merge_with_existing(self):
        """Merge should update only specified fields."""
        existing = DATConfig(
            source=DATSource.RETOOL_1G1R_ENG,
            expected_count=200
        )
        result = _merge_dat_config(existing, {"expected_count": 300})
        assert result.source == DATSource.RETOOL_1G1R_ENG
        assert result.expected_count == 300
    
    def test_merge_with_none_creates_new(self):
        """Merge with None should create new config."""
        result = _merge_dat_config(
            None,
            {"source": "retool_1g1r_usa", "expected_count": 100}
        )
        assert result.source == DATSource.RETOOL_1G1R_USA
        assert result.expected_count == 100
    
    def test_file_path_conversion(self):
        """File path should be converted to Path object."""
        existing = DATConfig(source=DATSource.RETOOL_1G1R_ENG)
        result = _merge_dat_config(
            existing,
            {"file": "/path/to/dat.dat"}
        )
        assert result.file == Path("/path/to/dat.dat")


class TestMergeCompressionConfig:
    """Tests for compression config merging."""
    
    def test_format_enum_conversion(self):
        """Format string should be converted to enum."""
        existing = CompressionConfig(format=CompressionFormat.ZIP)
        result = _merge_compression_config(existing, {"format": "chd"})
        assert result.format == CompressionFormat.CHD
    
    def test_preserves_unspecified_fields(self):
        """Unspecified fields should be preserved."""
        existing = CompressionConfig(
            format=CompressionFormat.ZIP,
            verify=True,
            parameters={"level": 9}
        )
        result = _merge_compression_config(existing, {"format": "7z"})
        assert result.format == CompressionFormat.SEVENZ
        assert result.verify is True
        assert result.parameters == {"level": 9}


class TestMergeSelectionConfig:
    """Tests for selection config merging."""
    
    def test_none_override_clears_selection(self):
        """None should clear the selection config."""
        existing = SelectionConfig(strategy=SelectionStrategy.FIRST, limit=10)
        result = _merge_selection_config(existing, None)
        assert result is None
    
    def test_creates_new_from_dict(self):
        """Should create new config when existing is None."""
        result = _merge_selection_config(
            None,
            {"strategy": "rating_budget", "max_size_gb": 40.0}
        )
        assert result.strategy == SelectionStrategy.RATING_BUDGET
        assert result.max_size_gb == 40.0


class TestProcessTargetsOverride:
    """Tests for target processing."""
    
    def test_filter_mode_with_strings(self):
        """List of strings should filter existing targets."""
        existing = [
            TargetProfile(
                name="a",
                output_path=Path("/a"),
                organization=OrganizationConfig(style=OrganizationStyle.FLAT)
            ),
            TargetProfile(
                name="b", 
                output_path=Path("/b"),
                organization=OrganizationConfig(style=OrganizationStyle.FLAT)
            ),
            TargetProfile(
                name="c",
                output_path=Path("/c"),
                organization=OrganizationConfig(style=OrganizationStyle.FLAT)
            ),
        ]
        result = _process_targets_override(
            existing,
            ["a", "c"],
            None,
            None,
            None
        )
        assert len(result) == 2
        assert result[0].name == "a"
        assert result[1].name == "c"
    
    def test_replacement_mode_with_dicts(self):
        """List of dicts should create new targets."""
        existing = [
            TargetProfile(
                name="old",
                output_path=Path("/old"),
                organization=OrganizationConfig(style=OrganizationStyle.FLAT)
            )
        ]
        result = _process_targets_override(
            existing,
            [
                {
                    "name": "new",
                    "output_path": "/new",
                    "organization": {"style": "balanced"}
                }
            ],
            None,
            None,
            None
        )
        assert len(result) == 1
        assert result[0].name == "new"
        assert result[0].organization.style == OrganizationStyle.BALANCED
    
    def test_default_organization_applied(self):
        """Default organization should be applied to targets without one."""
        result = _process_targets_override(
            [],
            [{"name": "test", "output_path": "/test"}],
            "flat",  # Default organization
            None,
            None
        )
        assert result[0].organization.style == OrganizationStyle.FLAT
