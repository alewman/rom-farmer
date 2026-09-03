"""Tests for the new declarative build orchestrator.

Tests the NewBuildOrchestrator which replaces BuildOrchestrator + PlatformProcessor.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from romfarmer.build_models import BuildStatus
from romfarmer.config.build_spec import BuildSpec
from romfarmer.config.models import (
    CompressionFormat,
    ExtractionType,
    SourceConfig,
)
from romfarmer.config.recipe import RecipeSpec
from romfarmer.config.resolver import ResolvedPlatformConfig
from romfarmer.config.slim_platform import (
    DATReference,
    SlimPlatformConfig,
)
from romfarmer.config.target import ComposedTarget
from romfarmer.new_orchestrator import NewBuildOrchestrator, _resolve_all_source_roots

# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def tmp_state_dir(tmp_path):
    """Temporary state directory."""
    return tmp_path / "state"


@pytest.fixture
def mock_composed_target():
    """Minimal mock ComposedTarget."""
    target = MagicMock(spec=ComposedTarget)
    target.frontend = MagicMock()
    target.frontend.name = "batocera"
    target.device = MagicMock()
    target.device.name = "pc"
    target.supports_platform = MagicMock(return_value=True)
    target.get_folder_name = MagicMock(side_effect=lambda p: p)
    target.get_preferred_compression = MagicMock(return_value=None)
    return target


@pytest.fixture
def sample_build_spec():
    """Minimal BuildSpec for testing."""
    return BuildSpec(
        name="test-build",
        description="Test build",
        target="batocera-pc",
        recipes=["nointro-7z"],
    )


@pytest.fixture
def sample_resolved_configs(tmp_path):
    """A couple of resolved configs for testing."""
    # Create source directories so SourceConfig validation passes
    nes_src = tmp_path / "nes-src"
    nes_src.mkdir()
    saturn_src = tmp_path / "saturn-src"
    saturn_src.mkdir()
    return [
        ResolvedPlatformConfig(
            platform="nes",
            extraction_type=ExtractionType.CARTRIDGE,
            compression=CompressionFormat.SEVENZ,
            sources=[SourceConfig(path=nes_src)],
            output_dir=tmp_path / "output" / "nes",
        ),
        ResolvedPlatformConfig(
            platform="saturn",
            extraction_type=ExtractionType.DISC,
            compression=CompressionFormat.CHD,
            sources=[SourceConfig(path=saturn_src)],
            output_dir=tmp_path / "output" / "saturn",
        ),
    ]


@pytest.fixture
def sample_recipes():
    return {
        "nointro-7z": RecipeSpec(
            name="nointro-7z",
            platforms=["nes"],
            compression="7z",
        ),
    }


@pytest.fixture
def orchestrator(
    sample_build_spec,
    mock_composed_target,
    sample_resolved_configs,
    sample_recipes,
    tmp_state_dir,
):
    """Create orchestrator with mocked dependencies."""
    with (
        patch.object(NewBuildOrchestrator, "_initialize_budget_tracking"),
        patch.object(NewBuildOrchestrator, "_setup_logging"),
    ):
        return NewBuildOrchestrator(
            build_spec=sample_build_spec,
            composed_target=mock_composed_target,
            resolved_configs=sample_resolved_configs,
            recipes=sample_recipes,
            state_dir=tmp_state_dir,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TestNewBuildOrchestrator
# ═══════════════════════════════════════════════════════════════════════════════


class TestNewBuildOrchestrator:
    """Test orchestrator initialization and basic functionality."""

    def test_init(self, orchestrator):
        """Test orchestrator initializes correctly."""
        assert orchestrator.build_spec.name == "test-build"
        assert len(orchestrator.resolved_configs) == 2
        assert orchestrator.state.build_name == "test-build"
        assert orchestrator.state.status == BuildStatus.NOT_STARTED

    def test_state_persistence(self, orchestrator):
        """Test in-memory state is tracked (YAML persistence removed in Phase 5)."""
        # Modify in-memory state
        orchestrator.state.completed_platforms.append("nes")
        orchestrator.state.status = BuildStatus.RUNNING
        orchestrator._save_state()  # no-op after Phase 5 removal

        # In-memory state unchanged — no YAML written
        assert orchestrator.state.completed_platforms == ["nes"]
        assert orchestrator.state.status == BuildStatus.RUNNING

    def test_get_status(self, orchestrator):
        """Test status reporting."""
        orchestrator.state.completed_platforms = ["nes"]
        orchestrator.state.failed_platforms = []

        status = orchestrator.get_status()
        assert status["build_name"] == "test-build"
        assert status["progress"]["total"] == 2
        assert status["progress"]["completed"] == 1
        assert status["progress"]["remaining"] == 1
        assert status["progress"]["percent"] == 50.0

    def test_resume_creates_orchestrator(self, orchestrator):
        """Test that resume calls run with resume=True."""
        with patch.object(orchestrator, "run") as mock_run:
            orchestrator.resume()
            mock_run.assert_called_once_with(resume=True)


class TestValidation:
    """Test build validation logic."""

    def test_validates_with_resolved_platforms(self, orchestrator):
        """Test validation passes with valid configs."""
        # Mock source paths to exist
        for rc in orchestrator.resolved_configs:
            for src in rc.sources:
                src.path = Path(tempfile.gettempdir())

        with patch("romfarmer.new_orchestrator.get_paths") as mock_paths:
            mock_paths.return_value.workspace_root = Path(tempfile.gettempdir())
            orchestrator._cached_target_profile = None  # profile presence is tested elsewhere
            assert orchestrator.validate() is True

    def test_fails_with_no_platforms(self, orchestrator):
        """Test validation fails when no platforms resolved."""
        orchestrator.resolved_configs = []
        assert orchestrator.validate() is False


class TestPlatformOrdering:
    """Test platform ordering by tier."""

    def test_tier_ordering(self, orchestrator):
        """Test platforms are ordered by tier (lower first)."""
        # Set up tiers
        mock_tiers = MagicMock()
        mock_tiers.get_platform_tier = MagicMock(
            side_effect=lambda p: {"nes": 1, "saturn": 3}.get(p, 99)
        )
        orchestrator.platform_tiers = mock_tiers

        with patch.object(orchestrator, "_get_tier_strategy", return_value=None):
            ordered = orchestrator._get_platforms_to_process(resume=False)

        # Tier 1 (nes) should come before Tier 3 (saturn)
        platforms = [rc.platform for rc in ordered]
        assert platforms.index("nes") < platforms.index("saturn")

    def test_resume_skips_completed(self, orchestrator):
        """Resume no longer skips completed platforms — replan-plus-cache-hits.

        BuildState YAML persistence was removed in Phase 5.  resume=True now
        re-runs all platforms (the action cache provides fast hits for
        already-completed work), so completed_platforms in the in-memory
        state does NOT affect the platform list.
        """
        orchestrator.state.completed_platforms = ["nes"]
        remaining = orchestrator._get_platforms_to_process(resume=True)
        platforms = [rc.platform for rc in remaining]
        # Both platforms are re-run; action cache handles efficiency
        assert "nes" in platforms
        assert "saturn" in platforms


class TestPlatformProcessing:
    """Test platform processing via pipeline."""

    @patch("romfarmer.new_orchestrator.get_paths")
    def test_process_platform_calls_pipeline(self, mock_paths, orchestrator):
        """Test that _process_platform runs the new compiler pipeline."""
        # Mock paths
        mock_paths.return_value.platform_temp_dir = MagicMock(return_value=Path(tempfile.mkdtemp()))
        mock_paths.return_value.workspace_root = Path(tempfile.gettempdir())

        from dataclasses import replace

        resolved = replace(
            orchestrator.resolved_configs[0],
            sources=[SourceConfig(path=Path(tempfile.gettempdir()))],
        )
        orchestrator.resolved_configs[0] = resolved

        # Empty catalog → driver exits after CATALOG phase cleanly
        mock_catalog = MagicMock()
        mock_catalog.units = ()
        with (
            patch.object(orchestrator, "_find_dat_file", return_value=None),
            patch.object(orchestrator, "_load_target_profile", return_value=None),
            patch("romfarmer.new_orchestrator.run_catalog", return_value=mock_catalog),
        ):
            orchestrator._process_platform(resolved)

        # If we reach here without exception, the pipeline was invoked

    def test_process_platform_raises_on_no_source(self, orchestrator):
        """Test that processing fails when no source directory."""
        resolved = ResolvedPlatformConfig(
            platform="test",
            sources=[],
        )
        with patch("romfarmer.new_orchestrator.get_paths") as mock_paths:
            mock_paths.return_value.platform_temp_dir = MagicMock(return_value=Path("/tmp/test"))
            mock_paths.return_value.workspace_root = Path("/tmp")
            with pytest.raises(ValueError, match="No source directory"):
                orchestrator._process_platform(resolved)


class TestBuildExecution:
    """Test the full run() flow."""

    def test_run_completes(self, orchestrator):
        """Test a successful build run."""
        with (
            patch.object(orchestrator, "validate", return_value=True),
            patch.object(orchestrator, "_get_platforms_to_process", return_value=[]),
            patch.object(orchestrator, "_run_generation_filter"),
            patch.object(orchestrator, "_run_post_build_hooks"),
            patch.object(orchestrator, "_generate_report"),
            patch.object(orchestrator, "_run_deployment"),
            patch.object(orchestrator, "_save_state"),
        ):
            orchestrator.run()

        assert orchestrator.state.status == BuildStatus.COMPLETED

    def test_run_fails_validation(self, orchestrator):
        """Test run raises on validation failure."""
        with patch.object(orchestrator, "validate", return_value=False):
            with pytest.raises(ValueError, match="validation failed"):
                orchestrator.run()

    @patch("romfarmer.new_orchestrator.get_paths")
    def test_run_processes_platforms(self, mock_paths, orchestrator):
        """Test run() processes each platform."""
        mock_paths.return_value.platform_temp_dir = MagicMock(return_value=Path(tempfile.mkdtemp()))
        mock_paths.return_value.workspace_root = Path(tempfile.gettempdir())
        mock_paths.return_value.build_report_file = MagicMock(
            return_value=Path(tempfile.gettempdir()) / "report.txt"
        )

        # Make source dirs "exist"
        from dataclasses import replace

        orchestrator.resolved_configs = [
            replace(rc, sources=[SourceConfig(path=Path(tempfile.gettempdir()))])
            for rc in orchestrator.resolved_configs
        ]

        mock_catalog = MagicMock()
        mock_catalog.units = ()
        with (
            patch.object(orchestrator, "validate", return_value=True),
            patch.object(orchestrator, "_find_dat_file", return_value=None),
            patch.object(orchestrator, "_load_target_profile", return_value=None),
            patch("romfarmer.new_orchestrator.run_catalog", return_value=mock_catalog),
            patch.object(orchestrator, "_run_generation_filter"),
            patch.object(orchestrator, "_run_post_build_hooks"),
            patch.object(orchestrator, "_run_deployment"),
        ):
            orchestrator.run()

        assert orchestrator.state.status == BuildStatus.COMPLETED
        assert "nes" in orchestrator.state.completed_platforms
        assert "saturn" in orchestrator.state.completed_platforms

    @patch("romfarmer.new_orchestrator.get_paths")
    def test_run_records_failures(self, mock_paths, orchestrator):
        """Test that failed platforms are recorded in state."""
        mock_paths.return_value.platform_temp_dir = MagicMock(return_value=Path(tempfile.mkdtemp()))
        mock_paths.return_value.workspace_root = Path(tempfile.gettempdir())
        mock_paths.return_value.build_report_file = MagicMock(
            return_value=Path(tempfile.gettempdir()) / "report.txt"
        )

        # Make _run_new_plan_path raise for all platforms
        from dataclasses import replace

        orchestrator.resolved_configs = [
            replace(rc, sources=[SourceConfig(path=Path(tempfile.gettempdir()))])
            for rc in orchestrator.resolved_configs
        ]

        def _fail_catalog(*args, **kwargs):
            raise RuntimeError("Pipeline failed")

        with (
            patch.object(orchestrator, "validate", return_value=True),
            patch.object(orchestrator, "_find_dat_file", return_value=None),
            patch.object(orchestrator, "_load_target_profile", return_value=None),
            patch("romfarmer.new_orchestrator.run_catalog", side_effect=_fail_catalog),
            patch.object(orchestrator, "_run_generation_filter"),
            patch.object(orchestrator, "_run_post_build_hooks"),
            patch.object(orchestrator, "_run_deployment"),
        ):
            orchestrator.run()

        assert orchestrator.state.status == BuildStatus.COMPLETED
        assert len(orchestrator.state.failed_platforms) == 2
        assert "nes" in orchestrator.state.failed_platforms
        assert "saturn" in orchestrator.state.failed_platforms


class TestPostBuildHooks:
    """Test post-build hook execution."""

    def test_no_hooks(self, orchestrator):
        """Test no error when no hooks configured."""
        orchestrator.build_spec = BuildSpec(
            name="test",
            target="batocera-pc",
            recipes=["nointro-7z"],
            post_build=[],
        )
        # Should not raise
        orchestrator._run_post_build_hooks()

    @patch("romfarmer.driver.hooks.subprocess.run")
    @patch("romfarmer.new_orchestrator.get_paths")
    def test_runs_hook_command(self, mock_paths, mock_run, orchestrator):
        """Test that hook commands are executed."""
        from romfarmer.config.build_spec import PostBuildHook

        mock_paths.return_value.workspace_root = Path("/tmp")
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "done\n"

        orchestrator.build_spec = BuildSpec(
            name="test",
            target="batocera-pc",
            recipes=["nointro-7z"],
            post_build=[
                PostBuildHook(name="test-hook", command="echo hello"),
            ],
        )

        orchestrator._run_post_build_hooks()
        mock_run.assert_called_once()
        # argv list, never a shell string (G4 #11)
        assert mock_run.call_args[0][0] == ["echo", "hello"]
        assert mock_run.call_args[1].get("shell", False) is False


class TestDATFileLookup:
    """Test DAT file resolution."""

    def test_no_dat_returns_none(self, orchestrator):
        """Test returns None when no DAT configured."""
        resolved = ResolvedPlatformConfig(platform="test")
        assert orchestrator._find_dat_file(resolved) is None

    def test_explicit_dat_file(self, orchestrator, tmp_path):
        """Test explicit DAT file path."""
        dat_file = tmp_path / "test.dat"
        dat_file.write_text("test content")

        resolved = ResolvedPlatformConfig(
            platform="test",
            dat=DATReference(source="retool_1g1r_eng", file=dat_file),
        )
        result = orchestrator._find_dat_file(resolved)
        assert result == dat_file

    def test_specific_pattern_beats_generic_fallback(self, orchestrator, tmp_path):
        """Test that specific yaml pattern matches before generic platform name.

        Regression test: 'xbox' platform must select the Xbox DAT, not Xbox 360.
        The generic fallback 'xbox' is a substring of 'xbox 360', so the loop
        must check the specific pattern across ALL files before falling back.
        """
        # retool_1g1r_eng resolves to the redump dir for non-cartridge platforms
        dat_dir = tmp_path / "dats" / "redump.retool.1g1r.eng"
        dat_dir.mkdir(parents=True)

        # Create two DAT files — Xbox 360 listed first alphabetically
        xbox360_dat = dat_dir / "Microsoft - Xbox 360 (1400).dat"
        xbox360_dat.write_text("360 content")
        xbox_dat = dat_dir / "Microsoft - Xbox (975).dat"
        xbox_dat.write_text("xbox content")

        resolved = ResolvedPlatformConfig(
            platform="xbox",
            dat=DATReference(source="retool_1g1r_eng"),
        )

        with (
            patch("romfarmer.new_orchestrator.get_paths") as mock_paths,
            patch.object(orchestrator, "_get_dat_pattern", return_value="microsoft - xbox ("),
        ):
            mock_paths.return_value.dats_dir = tmp_path / "dats"
            mock_paths.return_value.workspace_root = tmp_path
            result = orchestrator._find_dat_file(resolved)

        assert result is not None
        assert "(975)" in result.name, f"Expected Xbox DAT (975) but got: {result.name}"


class TestSourceRootResolution:
    """Test _resolve_all_source_roots helper."""

    def test_resolves_roots(self, tmp_path):
        """Test source roots are resolved from sources.yaml."""
        # Create sources.yaml
        config_root = tmp_path / "config"
        config_root.mkdir()
        (config_root / "sources.yaml").write_text("roots:\n  myrient: /path/to/source/myrient\n")

        source = SourceConfig(root="myrient", subdir="nointro/nes")
        platforms = {
            "nes": SlimPlatformConfig(
                name="nes",
                dat=DATReference(source="retool_1g1r_eng"),
                sources=[source],
            ),
        }

        _resolve_all_source_roots(platforms, config_root)

        assert source.path == Path("/path/to/source/myrient/nointro/nes")

    def test_missing_sources_yaml(self, tmp_path):
        """Test no error when sources.yaml doesn't exist."""
        platforms = {
            "nes": SlimPlatformConfig(
                name="nes",
                dat=DATReference(source="retool_1g1r_eng"),
                sources=[],
            ),
        }
        _resolve_all_source_roots(platforms, tmp_path)
        # Should not raise
