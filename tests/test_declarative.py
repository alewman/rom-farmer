"""Tests for the new declarative orchestration system.

Tests cover:
1. SlimPlatformConfig model + loading (including old format conversion)
2. RecipeSpec model + loading
3. BuildSpec model + loading
4. ConfigResolver (composition engine) — the most critical tests
5. Pipeline builder (declarative stage assembly)
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from romfarmer.config.slim_platform import (
    ArcadeFilter,
    DATReference,
    ListPatterns,
    PS3Config,
    SlimPlatformConfig,
    XboxConfig,
)
from romfarmer.config.recipe import RecipeSpec
from romfarmer.config.build_spec import BuildSpec
from romfarmer.config.resolver import (
    ConfigResolver,
    ResolvedPlatformConfig,
    resolve_build,
)
from romfarmer.config.models import (
    CompressionFormat,
    DATSource,
    ExtractionType,
    SelectionConfig,
    SelectionStrategy,
    SourceConfig,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def saturn_platform() -> SlimPlatformConfig:
    """A disc-based platform (Saturn)."""
    return SlimPlatformConfig(
        name="saturn",
        dat=DATReference(
            source=DATSource.REDUMP_RETOOL_1G1R_ENG,
            expected_count=318,
        ),
        sources=[
            SourceConfig(path=Path("/data/emu/roms/saturn"), type="myrient", recursive=False),
        ],
        extraction=ExtractionType.DISC,
        multi_disc=True,
        list_patterns=ListPatterns(
            delete="saturn-delete",
            add_myrient="saturn+*",
            add_extra="saturn.*",
        ),
    )


@pytest.fixture
def nes_platform() -> SlimPlatformConfig:
    """A cartridge-based platform (NES)."""
    return SlimPlatformConfig(
        name="nes",
        dat=DATReference(
            source=DATSource.RETOOL_1G1R_ENG,
            expected_count=1761,
        ),
        sources=[
            SourceConfig(path=Path("/data/emu/roms/nes"), type="myrient", recursive=False),
        ],
        extraction=ExtractionType.CARTRIDGE,
        multi_disc=False,
        list_patterns=ListPatterns(
            delete="nes-delete",
            add_myrient="nes+*",
            add_extra="nes.*",
        ),
    )


@pytest.fixture
def fbneo_platform() -> SlimPlatformConfig:
    """An arcade platform (FBNeo)."""
    return SlimPlatformConfig(
        name="fbneo",
        type="arcade",
        emulator="fbneo",
        dat=DATReference(
            source=DATSource.FBNEO_OFFICIAL,
            file=Path("dats/fbneo/fbneo-arcade.dat"),
            expected_count=2700,
        ),
        sources=[
            SourceConfig(path=Path("/data/emu/roms/fbneo"), type="myrient", recursive=False),
        ],
        extraction=ExtractionType.NONE,
        arcade_filter=ArcadeFilter(
            mode="relaxed",
            include_hacks=True,
            include_working_only=True,
        ),
        list_patterns=ListPatterns(
            delete="fbneo-delete",
            add="fbneo+*",
        ),
    )


@pytest.fixture
def ps3_platform() -> SlimPlatformConfig:
    """PS3 platform with special config."""
    return SlimPlatformConfig(
        name="ps3",
        dat=DATReference(
            source=DATSource.REDUMP_RETOOL_1G1R_ENG,
            expected_count=800,
        ),
        sources=[
            SourceConfig(path=Path("/data/emu/roms/ps3"), type="myrient", recursive=False),
        ],
        extraction=ExtractionType.PS3,
        ps3=PS3Config(
            keys_directory=Path("/data/emu/keys"),
            ps3dec_path=Path("/usr/bin/ps3dec"),
        ),
    )


@pytest.fixture
def xbox_platform() -> SlimPlatformConfig:
    """Xbox platform with XISO extraction."""
    return SlimPlatformConfig(
        name="xbox",
        dat=DATReference(
            source=DATSource.REDUMP_RETOOL_1G1R_ENG,
            expected_count=975,
            match_method="fuzzy_name",
        ),
        sources=[
            SourceConfig(path=Path("/data/emu/roms/xbox"), type="myrient", recursive=False),
        ],
        extraction=ExtractionType.XISO,
        multi_disc=True,
        xbox=XboxConfig(
            extract_xiso_path=Path("/usr/bin/extract-xiso"),
        ),
    )


@pytest.fixture
def all_platforms(saturn_platform, nes_platform, fbneo_platform, ps3_platform, xbox_platform):
    """Dict of all test platforms."""
    return {
        p.name: p for p in [saturn_platform, nes_platform, fbneo_platform, ps3_platform, xbox_platform]
    }


@pytest.fixture
def chd_recipe() -> RecipeSpec:
    """Redump CHD recipe."""
    return RecipeSpec(
        name="redump-chd",
        platforms=["saturn", "psx", "ps2"],
        compression="chd",
        apply_lists=True,
    )


@pytest.fixture
def sevenz_recipe() -> RecipeSpec:
    """No-Intro 7z recipe."""
    return RecipeSpec(
        name="nointro-7z",
        platforms=["nes", "snes", "gba"],
        compression="7z",
        apply_lists=True,
    )


@pytest.fixture
def arcade_recipe() -> RecipeSpec:
    """Arcade FBNeo recipe."""
    return RecipeSpec(
        name="arcade-fbneo",
        platforms=["fbneo", "neogeo"],
        compression="none",
        apply_lists=True,
    )


@pytest.fixture
def test_10_recipe() -> RecipeSpec:
    """Test recipe: 10 random games."""
    return RecipeSpec(
        name="test-10",
        platforms=[],  # Applies to all
        selection=SelectionConfig(
            strategy=SelectionStrategy.RANDOM,
            limit=10,
            seed=42,
        ),
    )


@pytest.fixture
def all_recipes(chd_recipe, sevenz_recipe, arcade_recipe, test_10_recipe):
    """Dict of all test recipes."""
    return {r.name: r for r in [chd_recipe, sevenz_recipe, arcade_recipe, test_10_recipe]}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. SlimPlatformConfig Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestSlimPlatformConfig:
    """Test SlimPlatformConfig model."""
    
    def test_basic_creation(self, saturn_platform):
        assert saturn_platform.name == "saturn"
        assert saturn_platform.extraction == ExtractionType.DISC
        assert saturn_platform.multi_disc is True
        assert saturn_platform.is_arcade is False
    
    def test_arcade_platform(self, fbneo_platform):
        assert fbneo_platform.is_arcade is True
        assert fbneo_platform.emulator == "fbneo"
        assert fbneo_platform.arcade_filter is not None
        assert fbneo_platform.arcade_filter.mode == "relaxed"
    
    def test_ps3_platform(self, ps3_platform):
        assert ps3_platform.extraction == ExtractionType.PS3
        assert ps3_platform.ps3 is not None
        assert ps3_platform.ps3.keys_directory == Path("/data/emu/keys")
    
    def test_xbox_platform(self, xbox_platform):
        assert xbox_platform.extraction == ExtractionType.XISO
        assert xbox_platform.xbox is not None
        assert xbox_platform.xbox.extract_xiso_path == Path("/usr/bin/extract-xiso")
    
    def test_metadata_system_default(self, saturn_platform):
        assert saturn_platform.get_metadata_system() == "saturn"
    
    def test_metadata_system_override(self):
        platform = SlimPlatformConfig(
            name="naomi",
            type="arcade",
            emulator="flycast",
            metadata_system="mame",
            dat=DATReference(source=DATSource.MAME, filter_driver="naomi"),
            sources=[SourceConfig(path=Path("/roms/naomi"), type="myrient")],
        )
        assert platform.get_metadata_system() == "mame"
    
    def test_dat_source_accessor(self, saturn_platform):
        assert saturn_platform.dat_source == DATSource.REDUMP_RETOOL_1G1R_ENG
    
    def test_list_patterns(self, nes_platform):
        assert nes_platform.list_patterns is not None
        assert nes_platform.list_patterns.delete == "nes-delete"
        assert nes_platform.list_patterns.add_myrient == "nes+*"


# ═══════════════════════════════════════════════════════════════════════════════
# 2. RecipeSpec Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestRecipeSpec:
    """Test RecipeSpec model."""
    
    def test_basic_creation(self, chd_recipe):
        assert chd_recipe.name == "redump-chd"
        assert chd_recipe.compression == "chd"
        assert len(chd_recipe.platforms) == 3
    
    def test_applies_to_specific_platform(self, chd_recipe):
        assert chd_recipe.applies_to("saturn") is True
        assert chd_recipe.applies_to("nes") is False
    
    def test_applies_to_all_when_empty(self, test_10_recipe):
        assert test_10_recipe.applies_to("saturn") is True
        assert test_10_recipe.applies_to("anything") is True
    
    def test_effective_compression(self, chd_recipe):
        assert chd_recipe.get_effective_compression() == CompressionFormat.CHD
    
    def test_effective_compression_7z(self, sevenz_recipe):
        assert sevenz_recipe.get_effective_compression() == CompressionFormat.SEVENZ
    
    def test_effective_compression_none(self):
        recipe = RecipeSpec(name="test", platforms=[])
        assert recipe.get_effective_compression() is None
    
    def test_invalid_compression_rejected(self):
        with pytest.raises(ValueError, match="Invalid compression format"):
            RecipeSpec(name="bad", platforms=[], compression="invalid")
    
    def test_selection_config(self, test_10_recipe):
        assert test_10_recipe.selection is not None
        assert test_10_recipe.selection.limit == 10
        assert test_10_recipe.selection.strategy == SelectionStrategy.RANDOM


# ═══════════════════════════════════════════════════════════════════════════════
# 3. BuildSpec Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestBuildSpec:
    """Test BuildSpec model."""
    
    def test_basic_creation(self):
        build = BuildSpec(
            name="test-build",
            target="batocera-pc",
            recipes=["redump-chd"],
        )
        assert build.name == "test-build"
        assert build.target == "batocera-pc"
        assert build.storage_budget == "unlimited"  # Default
    
    def test_requires_recipes(self):
        with pytest.raises(ValueError, match="requires at least one recipe"):
            BuildSpec(
                name="bad",
                target="batocera-pc",
                recipes=[],
            )
    
    def test_exclude_list(self):
        build = BuildSpec(
            name="test",
            target="batocera-pc",
            recipes=["redump-chd"],
            exclude=["3ds", "ps3"],
        )
        assert "3ds" in build.exclude
        assert "ps3" in build.exclude
    
    def test_output_base_default(self):
        build = BuildSpec(
            name="batocera-1tb",
            target="batocera-pc",
            recipes=["redump-chd"],
        )
        assert build.get_output_base() == Path("output/batocera-1tb")
    
    def test_output_base_override(self):
        build = BuildSpec(
            name="test",
            target="batocera-pc",
            recipes=["redump-chd"],
            output_base="/custom/output",
        )
        assert build.get_output_base() == Path("/custom/output")
    
    def test_has_budget_constraint(self):
        build = BuildSpec(
            name="test",
            target="batocera-pc",
            recipes=["redump-chd"],
            storage_budget="512gb",
        )
        assert build.has_budget_constraint() is True
    
    def test_no_budget_constraint(self):
        build = BuildSpec(
            name="test",
            target="batocera-pc",
            recipes=["redump-chd"],
        )
        assert build.has_budget_constraint() is False
    
    def test_platform_override(self):
        build = BuildSpec(
            name="test",
            target="batocera-pc",
            recipes=["redump-chd"],
            platforms=["saturn"],
        )
        assert build.platforms == ["saturn"]


# ═══════════════════════════════════════════════════════════════════════════════
# 4. ConfigResolver Tests (most critical)
# ═══════════════════════════════════════════════════════════════════════════════

class TestConfigResolver:
    """Test the config resolution / composition engine."""
    
    def test_basic_resolution(self, all_platforms, all_recipes):
        """Basic: resolve a build with one recipe."""
        build = BuildSpec(
            name="test",
            target="batocera-pc",
            recipes=["redump-chd"],
        )
        
        resolver = ConfigResolver(
            platforms=all_platforms,
            recipes=all_recipes,
        )
        
        results = resolver.resolve(build)
        
        # Should only resolve saturn (the only platform in all_platforms
        # that is also in redump-chd recipe)
        assert len(results) == 1
        assert results[0].platform == "saturn"
        assert results[0].compression == CompressionFormat.CHD
        assert results[0].extraction_type == ExtractionType.DISC
    
    def test_multi_recipe_union(self, all_platforms, all_recipes):
        """Multiple recipes: platform list is the union."""
        build = BuildSpec(
            name="test",
            target="batocera-pc",
            recipes=["redump-chd", "nointro-7z"],
        )
        
        results = resolve_build(build, all_platforms, all_recipes)
        
        # Saturn from redump-chd + NES from nointro-7z
        platform_names = {r.platform for r in results}
        assert "saturn" in platform_names
        assert "nes" in platform_names
    
    def test_recipe_stacking(self, all_platforms, all_recipes):
        """Later recipes override earlier ones for overlapping platforms."""
        # Add saturn to both recipes to test override
        all_recipes["nointro-7z"] = RecipeSpec(
            name="nointro-7z",
            platforms=["saturn"],  # Now also claims Saturn
            compression="7z",
        )
        
        build = BuildSpec(
            name="test",
            target="batocera-pc",
            recipes=["redump-chd", "nointro-7z"],  # 7z comes last, wins
        )
        
        results = resolve_build(build, all_platforms, all_recipes)
        
        saturn = next(r for r in results if r.platform == "saturn")
        # 7z recipe came last, so it wins
        assert saturn.compression == CompressionFormat.SEVENZ
    
    def test_test_recipe_stacking(self, all_platforms, all_recipes):
        """Test recipe stacks selection on top without changing compression."""
        build = BuildSpec(
            name="test",
            target="batocera-pc",
            recipes=["redump-chd", "test-10"],
        )
        
        results = resolve_build(build, all_platforms, all_recipes)
        
        saturn = next(r for r in results if r.platform == "saturn")
        # CHD from redump-chd recipe
        assert saturn.compression == CompressionFormat.CHD
        # Selection from test-10 recipe
        assert saturn.selection is not None
        assert saturn.selection.limit == 10
        assert saturn.selection.strategy == SelectionStrategy.RANDOM
    
    def test_exclude_platforms(self, all_platforms, all_recipes):
        """Build excludes should remove platforms."""
        build = BuildSpec(
            name="test",
            target="batocera-pc",
            recipes=["redump-chd", "nointro-7z", "arcade-fbneo"],
            exclude=["saturn", "fbneo"],
        )
        
        results = resolve_build(build, all_platforms, all_recipes)
        
        platform_names = {r.platform for r in results}
        assert "saturn" not in platform_names
        assert "fbneo" not in platform_names
        assert "nes" in platform_names
    
    def test_explicit_platforms(self, all_platforms, all_recipes):
        """Explicit platform list overrides recipe union."""
        build = BuildSpec(
            name="test",
            target="batocera-pc",
            recipes=["redump-chd", "nointro-7z"],
            platforms=["saturn"],  # Only saturn, even though NES is in nointro-7z
        )
        
        results = resolve_build(build, all_platforms, all_recipes)
        
        assert len(results) == 1
        assert results[0].platform == "saturn"
    
    def test_build_level_selection_override(self, all_platforms, all_recipes):
        """Build-level selection overrides recipe selection."""
        build = BuildSpec(
            name="test",
            target="batocera-pc",
            recipes=["redump-chd", "test-10"],
            selection=SelectionConfig(
                strategy=SelectionStrategy.FIRST,
                limit=5,
            ),
        )
        
        results = resolve_build(build, all_platforms, all_recipes)
        
        saturn = next(r for r in results if r.platform == "saturn")
        # Build selection overrides recipe
        assert saturn.selection.limit == 5
        assert saturn.selection.strategy == SelectionStrategy.FIRST
    
    def test_arcade_platform_resolution(self, all_platforms, all_recipes):
        """Arcade platforms get correct intrinsics."""
        build = BuildSpec(
            name="test",
            target="batocera-pc",
            recipes=["arcade-fbneo"],
        )
        
        results = resolve_build(build, all_platforms, all_recipes)
        
        fbneo = next(r for r in results if r.platform == "fbneo")
        assert fbneo.is_arcade is True
        assert fbneo.extraction_type == ExtractionType.NONE
        assert fbneo.compression == CompressionFormat.NONE
        assert fbneo.arcade_filter is not None
    
    def test_ps3_intrinsics_preserved(self, all_platforms, all_recipes):
        """PS3-specific config flows through resolution."""
        all_recipes["ps3-jb"] = RecipeSpec(
            name="ps3-jb",
            platforms=["ps3"],
            compression="none",
        )
        
        build = BuildSpec(
            name="test",
            target="batocera-pc",
            recipes=["ps3-jb"],
        )
        
        results = resolve_build(build, all_platforms, all_recipes)
        
        ps3 = next(r for r in results if r.platform == "ps3")
        assert ps3.extraction_type == ExtractionType.PS3
        assert ps3.ps3 is not None
        assert ps3.ps3.keys_directory == Path("/data/emu/keys")
    
    def test_xbox_intrinsics_preserved(self, all_platforms, all_recipes):
        """Xbox-specific config flows through resolution."""
        all_recipes["xbox-xiso"] = RecipeSpec(
            name="xbox-xiso",
            platforms=["xbox"],
            compression="none",
        )
        
        build = BuildSpec(
            name="test",
            target="batocera-pc",
            recipes=["xbox-xiso"],
        )
        
        results = resolve_build(build, all_platforms, all_recipes)
        
        xbox = next(r for r in results if r.platform == "xbox")
        assert xbox.extraction_type == ExtractionType.XISO
        assert xbox.xbox is not None
        assert xbox.xbox.extract_xiso_path == Path("/usr/bin/extract-xiso")
    
    def test_output_path_derivation(self, all_platforms, all_recipes):
        """Output paths are derived from build name + platform."""
        build = BuildSpec(
            name="batocera-1tb",
            target="batocera-pc",
            recipes=["redump-chd"],
        )
        
        results = resolve_build(build, all_platforms, all_recipes)
        
        saturn = results[0]
        assert saturn.output_dir == Path("output/batocera-1tb/saturn")
    
    def test_unknown_recipe_raises(self, all_platforms, all_recipes):
        """Referencing a nonexistent recipe raises ValueError."""
        build = BuildSpec(
            name="test",
            target="batocera-pc",
            recipes=["nonexistent-recipe"],
        )
        
        with pytest.raises(ValueError, match="Recipe 'nonexistent-recipe' not found"):
            resolve_build(build, all_platforms, all_recipes)
    
    def test_unknown_platform_skipped(self, all_platforms, all_recipes):
        """Platforms in recipe but not in platforms dict are skipped with warning."""
        build = BuildSpec(
            name="test",
            target="batocera-pc",
            recipes=["redump-chd"],
            # redump-chd wants psx and ps2, which aren't in our test platforms dict
        )
        
        results = resolve_build(build, all_platforms, all_recipes)
        
        # Only saturn is in both the recipe and the platforms dict
        assert len(results) == 1
        assert results[0].platform == "saturn"
    
    def test_device_unsupported_filter(self, all_platforms, all_recipes):
        """Device unsupported platforms are excluded."""
        # Create a mock composed target where device doesn't support PS3
        mock_target = MagicMock()
        mock_target.supports_platform.side_effect = lambda p: p != "ps3"
        mock_target.get_folder_name.side_effect = lambda p: p
        mock_target.get_preferred_compression.return_value = None
        mock_target.device.name = "r36s"
        mock_target.frontend.defaults = None
        mock_target.frontend.compression_fallback = {}
        
        all_recipes["ps3-jb"] = RecipeSpec(
            name="ps3-jb",
            platforms=["ps3"],
            compression="none",
        )
        
        build = BuildSpec(
            name="test",
            target="rocknix-r36s",
            recipes=["redump-chd", "ps3-jb"],
        )
        
        results = resolve_build(
            build, all_platforms, all_recipes,
            composed_target=mock_target,
        )
        
        platform_names = {r.platform for r in results}
        assert "ps3" not in platform_names
    
    def test_compression_fallback(self, all_platforms, all_recipes):
        """Frontend compression fallback works (e.g., 7z → zip for RocknIX)."""
        mock_frontend = MagicMock()
        mock_frontend.name = "rocknix"
        mock_frontend.compression_fallback = {"7z": "zip"}
        mock_frontend.defaults = MagicMock()
        mock_frontend.defaults.organization = "balanced"
        mock_frontend.defaults.metadata = True
        
        mock_target = MagicMock()
        mock_target.supports_platform.return_value = True
        mock_target.get_folder_name.side_effect = lambda p: p
        mock_target.get_preferred_compression.return_value = None
        mock_target.frontend = mock_frontend
        mock_target.device.name = "r36s"
        
        build = BuildSpec(
            name="test",
            target="rocknix-r36s",
            recipes=["nointro-7z"],  # Recipe says 7z
        )
        
        results = resolve_build(
            build, all_platforms, all_recipes,
            composed_target=mock_target,
        )
        
        nes = next(r for r in results if r.platform == "nes")
        # Should fall back from 7z to zip
        assert nes.compression == CompressionFormat.ZIP


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Pipeline Builder Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestPipelineBuilder:
    """Test declarative pipeline assembly."""
    
    def test_cartridge_7z_pipeline(self, nes_platform):
        """Cartridge + 7z produces correct stages."""
        from romfarmer.stages.builder import build_pipeline
        
        resolved = ResolvedPlatformConfig(
            platform="nes",
            extraction_type=ExtractionType.CARTRIDGE,
            compression=CompressionFormat.SEVENZ,
            dat=nes_platform.dat,
            sources=nes_platform.sources,
            list_patterns=nes_platform.list_patterns,
            apply_lists=True,
            metadata=True,
        )
        
        pipeline = build_pipeline(resolved)
        stage_names = [type(s).__name__ for s in pipeline.stages]
        
        assert "FilterDATStage" in stage_names
        assert "Filter1G1RStage" in stage_names
        assert "ApplyListsStage" in stage_names
        assert "ExtractArchiveStage" in stage_names
        assert "CompressArchiveStage" in stage_names
        assert "OrganizeStage" in stage_names
        assert "GenerateMetadataStage" in stage_names
        # Should NOT have arcade stages
        assert "FilterArcadeStage" not in stage_names
        assert "CopyArcadeStage" not in stage_names
    
    def test_disc_chd_pipeline(self, saturn_platform):
        """Disc + CHD produces correct stages."""
        from romfarmer.stages.builder import build_pipeline
        
        resolved = ResolvedPlatformConfig(
            platform="saturn",
            extraction_type=ExtractionType.DISC,
            compression=CompressionFormat.CHD,
            dat=saturn_platform.dat,
            sources=saturn_platform.sources,
            multi_disc=True,
            apply_lists=True,
            metadata=True,
        )
        
        pipeline = build_pipeline(resolved)
        stage_names = [type(s).__name__ for s in pipeline.stages]
        
        assert "FilterDATStage" in stage_names
        assert "ExtractArchiveStage" in stage_names
        assert "CompressCHDStage" in stage_names
        assert "CreateM3UStage" in stage_names
        assert "OrganizeStage" in stage_names
    
    def test_arcade_pipeline(self, fbneo_platform):
        """Arcade platforms get arcade-specific stages."""
        from romfarmer.stages.builder import build_pipeline
        
        resolved = ResolvedPlatformConfig(
            platform="fbneo",
            platform_type="arcade",
            extraction_type=ExtractionType.NONE,
            compression=CompressionFormat.NONE,
            dat=fbneo_platform.dat,
            sources=fbneo_platform.sources,
            arcade_filter=fbneo_platform.arcade_filter,
            apply_lists=True,
            metadata=True,
        )
        
        pipeline = build_pipeline(resolved)
        stage_names = [type(s).__name__ for s in pipeline.stages]
        
        assert "FilterArcadeStage" in stage_names
        assert "CopyArcadeStage" in stage_names
        assert "GenerateMetadataStage" in stage_names
        # Should NOT have console stages
        assert "FilterDATStage" not in stage_names
        assert "OrganizeStage" not in stage_names
    
    def test_rvz_pipeline(self, saturn_platform):
        """RVZ extraction produces UnzipRVZStage."""
        from romfarmer.stages.builder import build_pipeline
        
        resolved = ResolvedPlatformConfig(
            platform="gamecube",
            extraction_type=ExtractionType.RVZ,
            compression=CompressionFormat.RVZ,
            dat=DATReference(
                source=DATSource.REDUMP_RETOOL_1G1R_ENG,
                match_method="fuzzy_name",
            ),
            sources=saturn_platform.sources,  # Re-use existing fixture's valid source
            apply_lists=True,
            metadata=True,
        )
        
        pipeline = build_pipeline(resolved)
        stage_names = [type(s).__name__ for s in pipeline.stages]
        
        assert "UnzipRVZStage" in stage_names
        assert "OrganizeStage" in stage_names
    
    @patch("romfarmer.stages.extract_ps3.Path.exists", return_value=True)
    def test_ps3_pipeline(self, mock_exists, ps3_platform):
        """PS3 extraction includes tree-cache-accelerated transform stage."""
        from romfarmer.stages.builder import build_pipeline
        
        resolved = ResolvedPlatformConfig(
            platform="ps3",
            extraction_type=ExtractionType.PS3,
            compression=CompressionFormat.NONE,
            dat=ps3_platform.dat,
            sources=ps3_platform.sources,
            ps3=ps3_platform.ps3,
            apply_lists=True,
            metadata=True,
        )
        
        pipeline = build_pipeline(resolved)
        stage_names = [type(s).__name__ for s in pipeline.stages]
        
        assert "TransformPS3Stage" in stage_names
        assert "OrganizeStage" in stage_names
    
    def test_xiso_pipeline(self, xbox_platform):
        """Xbox XISO extraction includes extract + convert stages."""
        from romfarmer.stages.builder import build_pipeline
        
        resolved = ResolvedPlatformConfig(
            platform="xbox",
            extraction_type=ExtractionType.XISO,
            compression=CompressionFormat.NONE,
            dat=xbox_platform.dat,
            sources=xbox_platform.sources,
            xbox=xbox_platform.xbox,
            apply_lists=True,
            metadata=True,
        )
        
        pipeline = build_pipeline(resolved)
        stage_names = [type(s).__name__ for s in pipeline.stages]
        
        assert "ExtractArchiveStage" in stage_names
        assert "ConvertXISOStage" in stage_names
        assert "OrganizeStage" in stage_names
    
    def test_selection_stage_added_when_configured(self, nes_platform):
        """Selection config triggers SelectionFilter stage."""
        from romfarmer.stages.builder import build_pipeline
        
        resolved = ResolvedPlatformConfig(
            platform="nes",
            extraction_type=ExtractionType.CARTRIDGE,
            compression=CompressionFormat.SEVENZ,
            dat=nes_platform.dat,
            sources=nes_platform.sources,
            selection=SelectionConfig(
                strategy=SelectionStrategy.RANDOM,
                limit=10,
                seed=42,
            ),
            apply_lists=True,
            metadata=True,
        )
        
        pipeline = build_pipeline(resolved, work_dir=Path("/tmp"))
        stage_names = [type(s).__name__ for s in pipeline.stages]
        
        assert "SelectionFilter" in stage_names
        # Selection should come before extract
        sel_idx = stage_names.index("SelectionFilter")
        ext_idx = stage_names.index("ExtractArchiveStage")
        assert sel_idx < ext_idx
    
    def test_no_lists_when_disabled(self, nes_platform):
        """apply_lists=False skips ApplyListsStage."""
        from romfarmer.stages.builder import build_pipeline
        
        resolved = ResolvedPlatformConfig(
            platform="nes",
            extraction_type=ExtractionType.CARTRIDGE,
            compression=CompressionFormat.SEVENZ,
            dat=nes_platform.dat,
            sources=nes_platform.sources,
            apply_lists=False,
            metadata=True,
        )
        
        pipeline = build_pipeline(resolved)
        stage_names = [type(s).__name__ for s in pipeline.stages]
        
        assert "ApplyListsStage" not in stage_names
    
    def test_no_metadata_when_disabled(self, nes_platform):
        """metadata=False skips GenerateMetadataStage."""
        from romfarmer.stages.builder import build_pipeline
        
        resolved = ResolvedPlatformConfig(
            platform="nes",
            extraction_type=ExtractionType.CARTRIDGE,
            compression=CompressionFormat.SEVENZ,
            dat=nes_platform.dat,
            sources=nes_platform.sources,
            apply_lists=True,
            metadata=False,
        )
        
        pipeline = build_pipeline(resolved)
        stage_names = [type(s).__name__ for s in pipeline.stages]
        
        assert "GenerateMetadataStage" not in stage_names


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Loader Tests (loading from real YAML files)
# ═══════════════════════════════════════════════════════════════════════════════

class TestLoaders:
    """Test loading configs from YAML files on disk."""
    
    @pytest.fixture
    def config_root(self):
        """Get the real config root."""
        # Try multiple paths: relative to test file, or workspace root
        candidates = [
            Path(__file__).parent.parent / "config",  # rom-farmer/config
            Path(__file__).parent.parent.parent / "config",  # workspace/config
        ]
        for root in candidates:
            if root.exists() and (root / "platforms").exists():
                return root
        pytest.skip("Config directory not found")
    
    def test_load_slim_platform_from_old_format(self, config_root):
        """Load saturn.yaml (old format) and convert to slim."""
        from romfarmer.config.new_loader import load_slim_platform
        
        platform = load_slim_platform("saturn", config_root=config_root)
        
        assert platform.name == "saturn"
        assert platform.extraction == ExtractionType.DISC
        assert platform.multi_disc is True
        assert platform.dat.source == DATSource.REDUMP_RETOOL_1G1R_ENG
        assert platform.dat.expected_count == 318
        assert len(platform.sources) >= 1
        # Should NOT have targets or compression
        assert not hasattr(platform, "targets")
    
    def test_load_slim_arcade_platform(self, config_root):
        """Load fbneo.yaml (arcade) and convert to slim."""
        from romfarmer.config.new_loader import load_slim_platform
        
        platform = load_slim_platform("fbneo", config_root=config_root)
        
        assert platform.name == "fbneo"
        assert platform.is_arcade is True
        assert platform.emulator == "fbneo"
        assert platform.arcade_filter is not None
        assert platform.extraction == ExtractionType.NONE
    
    def test_load_slim_cartridge_platform(self, config_root):
        """Load nes.yaml (cartridge, old format extraction.type=none but is actually cartridge from overrides)."""
        from romfarmer.config.new_loader import load_slim_platform
        
        platform = load_slim_platform("nes", config_root=config_root)
        
        assert platform.name == "nes"
        # NES has extraction.enabled=false in its config (it gets overridden by build)
        # The slim loader preserves what's in the file
        assert platform.dat.source == DATSource.RETOOL_1G1R_ENG
    
    def test_load_recipe_from_yaml(self, config_root):
        """Load a recipe YAML file."""
        from romfarmer.config.new_loader import load_recipe
        
        recipe = load_recipe("redump-chd", config_root=config_root)
        
        assert recipe.name == "redump-chd"
        assert recipe.compression == "chd"
        assert "saturn" in recipe.platforms
        assert "psx" in recipe.platforms
    
    def test_load_all_recipes(self, config_root):
        """Load all recipe YAML files."""
        from romfarmer.config.new_loader import load_all_recipes
        
        recipes = load_all_recipes(config_root=config_root)
        
        assert len(recipes) >= 10  # We created at least 12
        assert "redump-chd" in recipes
        assert "nointro-7z" in recipes
        assert "test-10" in recipes
    
    def test_load_test_recipe(self, config_root):
        """Test recipe has selection config."""
        from romfarmer.config.new_loader import load_recipe
        
        recipe = load_recipe("test-10", config_root=config_root)
        
        assert recipe.selection is not None
        assert recipe.selection.limit == 10
        assert recipe.selection.strategy == SelectionStrategy.RANDOM
        assert recipe.selection.seed == 42
