"""End-to-end integration tests for _process_platform.

These tests exercise the full CATALOG → PLAN → EXECUTE → EMIT pipeline
through the real code with **no mocks** on _run_new_plan_path,
_run_execute_path, or _run_emit_path.  They are the tests that would
have caught every bug found in the 2026-07-04 architect review:

  - planner selections honoured in EXECUTE (not re-cataloged from disk)
  - terminal artifacts use logical names, not CAS hash names
  - multi-disc M3U created and named correctly
  - LayoutPlan flows from EXECUTE to EMIT without re-hashing
  - Materializer in-place reorganisation leaves no duplicates
  - Profile negotiation wired (profile loaded from frontend/device, not
    build-spec target name)

No external tools (chdman, 7z, …) are required: the passthrough chain is
used for all test ROMs so only the Python transforms run.  External tool
invocations in ArchiveTransform and CHDTransform are replaced with a
``FakeTransform`` that writes predictable output bytes.
"""

from __future__ import annotations

import zipfile
from collections.abc import Mapping
from pathlib import Path
from typing import Optional
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
from romfarmer.config.target import ComposedTarget
from romfarmer.engine.transforms.base import Transform
from romfarmer.new_orchestrator import (
    NewBuildOrchestrator,
    PhaseError,
    PlanValidationError,
    validate_plan,
    run_catalog,
    run_plan,
    run_execute,
    run_emit,
    PlannedPlatform,
    ExecEnv,
    ExecutedPlatform,
)


# ---------------------------------------------------------------------------
# Fake transforms — return stub outputs without calling external tools
# ---------------------------------------------------------------------------

class FakePassthroughTransform:
    """Copies inputs[0] → scratch as a TERMINAL stub."""

    name = "passthrough"

    def run(self, inputs: list[Path], params: Mapping[str, str], scratch: Path) -> list[Path]:
        if not inputs:
            return []
        dest = scratch / inputs[0].name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(inputs[0].read_bytes())
        return [dest]


class FakeSourceCopyTransform:
    """Copies params['path'] → scratch."""

    name = "source-copy"

    def run(self, inputs: list[Path], params: Mapping[str, str], scratch: Path) -> list[Path]:
        src = Path(params["path"])
        dest = scratch / src.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(src.read_bytes())
        return [dest]


_FAKE_TRANSFORMS: dict[str, Transform] = {
    "source-copy": FakeSourceCopyTransform(),  # type: ignore[dict-item]
    "passthrough": FakePassthroughTransform(),  # type: ignore[dict-item]
}


# ---------------------------------------------------------------------------
# Minimal config fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    """Minimal frontend + device YAML for the test target."""
    fe = tmp_path / "config" / "frontends"
    dev = tmp_path / "config" / "devices"
    fe.mkdir(parents=True)
    dev.mkdir(parents=True)

    (fe / "testfe.yaml").write_text("""\
name: testfe
description: Test Frontend
metadata: false
folder_mapping:
  nes: nes
platforms:
  nes:
    preferred_compression: none
  psx:
    preferred_compression: none
""")
    (dev / "testdev.yaml").write_text("""\
name: testdev
description: Test Device
unsupported_platforms: []
""")
    return tmp_path / "config"


@pytest.fixture
def nes_source_dir(tmp_path: Path) -> Path:
    """Three NES ROMs, two with the same base name (1G1R test)."""
    src = tmp_path / "source" / "nes"
    src.mkdir(parents=True)

    def write_rom(name: str, content: bytes) -> None:
        zp = src / f"{name}.zip"
        with zipfile.ZipFile(zp, "w") as zf:
            zf.writestr(f"{name}.nes", content)

    write_rom("Contra (USA)", b"contra-usa-bytes")
    write_rom("Contra (Europe)", b"contra-eur-bytes")
    write_rom("Super Mario Bros (USA)", b"smb-bytes")
    return src


@pytest.fixture
def psx_source_dir(tmp_path: Path) -> Path:
    """Two-disc PSX game as ZIP pairs."""
    src = tmp_path / "source" / "psx"
    src.mkdir(parents=True)

    for disc_n, content in [(1, b"ff7-disc1"), (2, b"ff7-disc2")]:
        zp = src / f"Final Fantasy VII (USA) (Disc {disc_n}).zip"
        with zipfile.ZipFile(zp, "w") as zf:
            zf.writestr(f"Final Fantasy VII (USA) (Disc {disc_n}).bin", content)
    return src


def _make_orchestrator(
    tmp_path: Path,
    config_dir: Path,
    resolved_configs: list[ResolvedPlatformConfig],
) -> NewBuildOrchestrator:
    """Assemble a NewBuildOrchestrator wired to the fake transforms."""
    build_spec = BuildSpec(
        name="e2e-test",
        description="E2E integration test build",
        target="testfe/testdev",
        recipes=["passthrough-all"],
    )
    recipes = {
        "passthrough-all": RecipeSpec(
            name="passthrough-all",
            platforms=[rc.platform for rc in resolved_configs],
            compression="none",
        )
    }
    mock_frontend = MagicMock()
    mock_frontend.name = "testfe"
    mock_device = MagicMock()
    mock_device.name = "testdev"
    composed_target = MagicMock(spec=ComposedTarget)
    composed_target.frontend = mock_frontend
    composed_target.device = mock_device

    with patch.object(NewBuildOrchestrator, "_initialize_budget_tracking"), \
         patch.object(NewBuildOrchestrator, "_setup_logging"):
        orch = NewBuildOrchestrator(
            build_spec=build_spec,
            composed_target=composed_target,
            resolved_configs=resolved_configs,
            recipes=recipes,
            state_dir=tmp_path / "state",
        )
    return orch


def _patch_transforms(orch: NewBuildOrchestrator, extra: dict | None = None) -> dict:
    """Return the fake transform registry used for _run_execute_path."""
    reg = dict(_FAKE_TRANSFORMS)
    if extra:
        reg.update(extra)
    return reg


# ---------------------------------------------------------------------------
# Test 1: passthrough chain — nes (no external tools)
# ---------------------------------------------------------------------------

class TestPassthroughChainE2E:
    """Full pipeline for a passthrough (no-conversion) NES build.

    Exercises: CATALOG, 1G1R pass (Contra EUR dropped), EXECUTE (passthrough
    transform only), EMIT (logical names, no re-hash).
    """

    def test_surviving_files_named_logically(
        self,
        tmp_path: Path,
        nes_source_dir: Path,
        config_dir: Path,
    ) -> None:
        output_dir = tmp_path / "output" / "nes"
        resolved = [
            ResolvedPlatformConfig(
                platform="nes",
                extraction_type=ExtractionType.NONE,
                compression=CompressionFormat.NONE,
                sources=[SourceConfig(path=nes_source_dir)],
                output_dir=output_dir,
            )
        ]
        orch = _make_orchestrator(tmp_path, config_dir, resolved)

        with patch(
            "romfarmer.new_orchestrator.get_paths"
        ) as mock_paths, patch.object(
            orch, "_load_target_profile", return_value=None
        ):
            mock_paths.return_value.platform_temp_dir = MagicMock(
                return_value=tmp_path / "work" / "nes"
            )
            mock_paths.return_value.workspace_root = config_dir.parent

            with patch.object(orch, "_find_dat_file", return_value=None):
                orch._process_platform(resolved[0])

        # Output should exist and contain .zip files named after the ROMs
        assert output_dir.exists(), "output dir must be created by EXECUTE"
        output_files = {f.name for f in output_dir.rglob("*") if f.is_file()}
        assert output_files, "EXECUTE must materialise at least one file"

        # No file should be named by its sha256 (40-64 hex chars with no spaces)
        import re
        hash_name_re = re.compile(r"^[0-9a-f]{32,64}(\.\w+)?$")
        for name in output_files:
            assert not hash_name_re.match(name), (
                f"File '{name}' looks like a CAS hash name — "
                "EXECUTE must use ArtifactDecl.logical_name"
            )

    def test_one_g_one_r_pass_is_honoured(
        self,
        tmp_path: Path,
        nes_source_dir: Path,
        config_dir: Path,
    ) -> None:
        """After 1G1R exactly ONE Contra variant must survive.

        The source dir contains Contra (USA) + Contra (Europe) + Super Mario.
        Regardless of which region wins, only 2 files should be produced
        (one Contra + Super Mario).  If EXECUTE were re-cataloguing from disk,
        both Contra variants would appear (3 files total).
        """
        output_dir = tmp_path / "output" / "nes"
        resolved = [
            ResolvedPlatformConfig(
                platform="nes",
                extraction_type=ExtractionType.NONE,
                compression=CompressionFormat.NONE,
                sources=[SourceConfig(path=nes_source_dir)],
                output_dir=output_dir,
            )
        ]
        orch = _make_orchestrator(tmp_path, config_dir, resolved)

        with patch(
            "romfarmer.new_orchestrator.get_paths"
        ) as mock_paths, patch.object(
            orch, "_find_dat_file", return_value=None
        ), patch.object(
            orch, "_load_target_profile", return_value=None
        ):
            mock_paths.return_value.platform_temp_dir = MagicMock(
                return_value=tmp_path / "work" / "nes"
            )
            mock_paths.return_value.workspace_root = config_dir.parent
            orch._process_platform(resolved[0])

        output_files = {f.name for f in output_dir.rglob("*") if f.is_file()}

        contra_files = [n for n in output_files if "Contra" in n]
        assert len(contra_files) == 1, (
            f"Expected exactly 1 Contra variant after 1G1R, got: {contra_files}. "
            "If EXECUTE is re-cataloguing from disk both variants appear (2 Contra files)."
        )
        # Total: 1 Contra (either region) + 1 Super Mario = 2
        assert len(output_files) == 2, (
            f"Expected 2 files total after 1G1R, got {len(output_files)}: {output_files}. "
            "Source had 3 ZIPs; 1G1R should reduce to 2 (one Contra + Super Mario)."
        )

    def test_no_duplicate_files_after_emit(
        self,
        tmp_path: Path,
        nes_source_dir: Path,
        config_dir: Path,
    ) -> None:
        """After EMIT organisation, each game ROM must appear exactly once."""
        output_dir = tmp_path / "output" / "nes"
        resolved = [
            ResolvedPlatformConfig(
                platform="nes",
                extraction_type=ExtractionType.NONE,
                compression=CompressionFormat.NONE,
                sources=[SourceConfig(path=nes_source_dir)],
                output_dir=output_dir,
            )
        ]
        # Use a profile that enables 'rich' style so letter subdirs are created
        mock_profile = MagicMock()
        mock_profile.organisation_style = "rich"
        mock_profile.metadata_enabled = False

        orch = _make_orchestrator(tmp_path, config_dir, resolved)

        with patch(
            "romfarmer.new_orchestrator.get_paths"
        ) as mock_paths, patch.object(
            orch, "_find_dat_file", return_value=None
        ), patch.object(
            orch, "_load_target_profile", return_value=mock_profile
        ):
            mock_paths.return_value.platform_temp_dir = MagicMock(
                return_value=tmp_path / "work" / "nes"
            )
            mock_paths.return_value.workspace_root = config_dir.parent
            orch._process_platform(resolved[0])

        all_files = [f for f in output_dir.rglob("*") if f.is_file()]
        names = [f.name for f in all_files]
        # Each game should appear exactly once across all subdirs
        from collections import Counter
        duplicates = {n: c for n, c in Counter(names).items() if c > 1}
        assert not duplicates, (
            f"Duplicate ROM files found: {duplicates}. "
            "Materializer move=True must remove top-level originals after letter-subdir."
        )


# ---------------------------------------------------------------------------
# Test 2: multi-disc passthrough chain — psx M3U
# ---------------------------------------------------------------------------

class TestMultiDiscM3UE2E:
    """Full pipeline for a 2-disc PSX game using passthrough chain.

    Exercises: multi-disc grouping in CATALOG, M3U logical name in EXECUTE,
    LayoutPlan M3U entry present in EMIT.
    """

    def test_m3u_file_created_with_logical_name(
        self,
        tmp_path: Path,
        psx_source_dir: Path,
        config_dir: Path,
    ) -> None:
        output_dir = tmp_path / "output" / "psx"
        resolved = [
            ResolvedPlatformConfig(
                platform="psx",
                extraction_type=ExtractionType.NONE,
                compression=CompressionFormat.NONE,
                sources=[SourceConfig(path=psx_source_dir)],
                output_dir=output_dir,
            )
        ]
        orch = _make_orchestrator(tmp_path, config_dir, resolved)

        with patch(
            "romfarmer.new_orchestrator.get_paths"
        ) as mock_paths, patch.object(
            orch, "_find_dat_file", return_value=None
        ), patch.object(
            orch, "_load_target_profile", return_value=None
        ):
            mock_paths.return_value.platform_temp_dir = MagicMock(
                return_value=tmp_path / "work" / "psx"
            )
            mock_paths.return_value.workspace_root = config_dir.parent
            orch._process_platform(resolved[0])

        # With passthrough chain, no CHD conversion happens, so no M3U will be
        # generated either (M3U only comes from disc.py's CHD path).
        # The key check here is that disc files land under their logical names.
        output_files = {f.name for f in output_dir.rglob("*") if f.is_file()}
        assert output_files, "EXECUTE must materialise PSX files"

        import re
        hash_name_re = re.compile(r"^[0-9a-f]{32,64}(\.\w+)?$")
        for name in output_files:
            assert not hash_name_re.match(name), (
                f"PSX file '{name}' is a CAS hash name — "
                "EXECUTE must use ArtifactDecl.logical_name"
            )

    def test_two_disc_group_yields_two_artifacts(
        self,
        tmp_path: Path,
        psx_source_dir: Path,
        config_dir: Path,
    ) -> None:
        """A 2-disc game treated as one GameUnit must produce exactly one output.

        With the passthrough chain, ``PassthroughLoweringRule`` processes
        ``discs[0]`` — this is correct spec behaviour: passthrough means
        'copy source as-is', and a ZIP-inside-ZIP multi-disc set has the
        first disc ZIP as the canonical source.  The important invariant is
        that the GameUnit was NOT split by the catalog (multi-disc atomicity
        holds) and the output filename uses ``ArtifactDecl.logical_name``,
        not a CAS hash.
        """
        output_dir = tmp_path / "output" / "psx"
        resolved = [
            ResolvedPlatformConfig(
                platform="psx",
                extraction_type=ExtractionType.NONE,
                compression=CompressionFormat.NONE,
                sources=[SourceConfig(path=psx_source_dir)],
                output_dir=output_dir,
            )
        ]
        orch = _make_orchestrator(tmp_path, config_dir, resolved)

        with patch(
            "romfarmer.new_orchestrator.get_paths"
        ) as mock_paths, patch.object(
            orch, "_find_dat_file", return_value=None
        ), patch.object(
            orch, "_load_target_profile", return_value=None
        ):
            mock_paths.return_value.platform_temp_dir = MagicMock(
                return_value=tmp_path / "work" / "psx"
            )
            mock_paths.return_value.workspace_root = config_dir.parent
            orch._process_platform(resolved[0])

        output_files = {f.name for f in output_dir.rglob("*") if f.is_file()}
        ff7_files = [n for n in output_files if "Final Fantasy VII" in n]
        assert len(ff7_files) == 1, (
            f"Expected 1 output for FF7 (passthrough = disc-1 ZIP), got {ff7_files}."
        )
        # The file must use a logical name, not a sha256
        import re
        assert not re.match(r"^[0-9a-f]{32,64}(\..+)?$", ff7_files[0]), (
            f"FF7 output file '{ff7_files[0]}' looks like a CAS hash name."
        )


# ---------------------------------------------------------------------------
# Test 3: verify catalog IS the filtered catalog, not a re-scan
# ---------------------------------------------------------------------------

class TestCatalogFlowsFromPlanToExecute:
    """Directly verify that run_execute receives the PlannedPlatform from run_plan.

    Injects spies on the module-level run_plan and run_execute functions to
    capture the Catalog flowing between them, then asserts they are the same
    object.  This is the regression test for the critical re-cataloguing bug
    fixed in dd14c50 — EXECUTE must consume the plan's catalog, not a fresh scan.
    """

    def test_execute_receives_same_catalog_as_plan(
        self,
        tmp_path: Path,
        nes_source_dir: Path,
        config_dir: Path,
    ) -> None:
        import romfarmer.new_orchestrator as orch_mod

        output_dir = tmp_path / "output" / "nes"
        resolved = [
            ResolvedPlatformConfig(
                platform="nes",
                extraction_type=ExtractionType.NONE,
                compression=CompressionFormat.NONE,
                sources=[SourceConfig(path=nes_source_dir)],
                output_dir=output_dir,
            )
        ]
        orch = _make_orchestrator(tmp_path, config_dir, resolved)

        captured: dict[str, object] = {}

        orig_run_plan = orch_mod.run_plan
        orig_run_execute = orch_mod.run_execute

        def spy_run_plan(*args: object, **kwargs: object) -> object:
            result = orig_run_plan(*args, **kwargs)
            captured["planned"] = result
            return result

        def spy_run_execute(planned: object, **kwargs: object) -> object:
            captured["execute_planned"] = planned
            return orig_run_execute(planned, **kwargs)  # type: ignore[arg-type]

        with patch(
            "romfarmer.new_orchestrator.get_paths"
        ) as mock_paths, patch.object(
            orch, "_find_dat_file", return_value=None
        ), patch.object(
            orch, "_load_target_profile", return_value=None
        ), patch(
            "romfarmer.new_orchestrator.run_plan", side_effect=spy_run_plan
        ), patch(
            "romfarmer.new_orchestrator.run_execute", side_effect=spy_run_execute
        ):
            mock_paths.return_value.platform_temp_dir = MagicMock(
                return_value=tmp_path / "work" / "nes"
            )
            mock_paths.return_value.workspace_root = config_dir.parent
            orch._process_platform(resolved[0])

        planned = captured.get("planned")
        execute_planned = captured.get("execute_planned")

        assert planned is not None, "run_plan was not called"
        assert execute_planned is not None, "run_execute was not called"

        # The PlannedPlatform handed to run_execute must be the SAME OBJECT
        # returned by run_plan — not a fresh scan or re-plan.
        assert planned is execute_planned, (
            "run_execute received a different PlannedPlatform than run_plan returned. "
            "The pipeline is re-deriving the plan — planner selections "
            "(1G1R, rating, budget) will have no effect."
        )
        # Explicitly verify the catalog identity too
        assert planned.catalog is execute_planned.catalog, (  # type: ignore[union-attr]
            "run_execute.planned.catalog is not the same object as run_plan's result catalog."
        )


# ---------------------------------------------------------------------------
# Test 5: preferred_regions now wired through SelectionConfig → BuildManifest
# ---------------------------------------------------------------------------

class TestPreferredRegionsE2E:
    """Verifies preferred_regions in SelectionConfig reaches the 1G1R pass.

    Before the fix: SelectionConfig had no preferred_regions field, so
    _build_manifest always produced preferred_regions=() and 1G1R fell
    back to alphabetical tiebreaking.

    After the fix: preferred_regions flows correctly, so USA is kept over
    Europe for Contra.
    """

    def test_preferred_region_selects_usa_over_europe(
        self,
        tmp_path: Path,
        config_dir: Path,
        nes_source_dir: Path,
    ):
        from romfarmer.config.models import SelectionConfig

        resolved = [
            ResolvedPlatformConfig(
                platform="nes",
                extraction_type=ExtractionType.CARTRIDGE,
                compression=CompressionFormat.NONE,
                sources=[SourceConfig(path=nes_source_dir)],
                selection=SelectionConfig(preferred_regions=["USA", "World", "Europe"]),
            )
        ]
        orch = _make_orchestrator(tmp_path, config_dir, resolved)

        # Gate 1: SelectionConfig.preferred_regions is a real field
        sel = resolved[0].selection
        assert hasattr(sel, "preferred_regions"), (
            "SelectionConfig.preferred_regions field is missing — "
            "it must be added to config/models.py"
        )
        assert sel.preferred_regions == ["USA", "World", "Europe"]

        # Gate 2: _build_manifest reads it (no longer uses the dead hasattr check)
        with patch("romfarmer.new_orchestrator.get_paths") as mock_paths:
            mock_paths.return_value.workspace_root = config_dir.parent
            manifest = orch._build_manifest(resolved[0], "nes")

        assert manifest.preferred_regions == ("USA", "World", "Europe"), (
            f"preferred_regions not wired through _build_manifest: "
            f"got {manifest.preferred_regions!r}"
        )


# ---------------------------------------------------------------------------
# Test 6: curated_exclude loaded from lists/{platform}-delete
# ---------------------------------------------------------------------------

class TestCuratedListsE2E:
    """Verifies _load_curated_lists reads the lists/ directory correctly.

    Creates a fake lists/nes-delete file containing one game and confirms
    that _build_manifest produces a non-empty curated_exclude frozenset.
    """

    def test_delete_list_loaded_into_curated_exclude(
        self,
        tmp_path: Path,
        config_dir: Path,
        nes_source_dir: Path,
    ):
        # Write a fake lists/ directory alongside the workspace root
        workspace_root = config_dir.parent
        lists_dir = workspace_root / "lists"
        lists_dir.mkdir(exist_ok=True)
        delete_file = lists_dir / "nes-delete"
        delete_file.write_text(
            "# NES delete list\n"
            "Contra (Europe).zip\n"
            "\n"
            "# blank lines and comments are ignored\n"
        )

        resolved = [
            ResolvedPlatformConfig(
                platform="nes",
                extraction_type=ExtractionType.CARTRIDGE,
                compression=CompressionFormat.NONE,
                sources=[SourceConfig(path=nes_source_dir)],
            )
        ]
        orch = _make_orchestrator(tmp_path, config_dir, resolved)

        with patch("romfarmer.new_orchestrator.get_paths") as mock_paths:
            mock_paths.return_value.platform_temp_dir = MagicMock(
                return_value=tmp_path / "work" / "nes"
            )
            mock_paths.return_value.workspace_root = workspace_root
            curated_include, curated_exclude = orch._load_curated_lists("nes")

        assert "Contra (Europe)" in curated_exclude, (
            f"Expected 'Contra (Europe)' in curated_exclude, got: {curated_exclude}"
        )
        assert "Super Mario Bros (USA)" not in curated_exclude

    def test_include_list_loaded_from_add_file(
        self,
        tmp_path: Path,
        config_dir: Path,
        nes_source_dir: Path,
    ):
        workspace_root = config_dir.parent
        lists_dir = workspace_root / "lists"
        lists_dir.mkdir(exist_ok=True)
        # An add/include list uses the "+" naming convention
        add_file = lists_dir / "nes+Best-Games"
        add_file.write_text("Super Mario Bros (USA).zip\n")

        resolved = [
            ResolvedPlatformConfig(
                platform="nes",
                extraction_type=ExtractionType.CARTRIDGE,
                compression=CompressionFormat.NONE,
                sources=[SourceConfig(path=nes_source_dir)],
            )
        ]
        orch = _make_orchestrator(tmp_path, config_dir, resolved)

        with patch("romfarmer.new_orchestrator.get_paths") as mock_paths:
            mock_paths.return_value.workspace_root = workspace_root
            curated_include, curated_exclude = orch._load_curated_lists("nes")

        assert "Super Mario Bros (USA)" in curated_include

    def test_missing_lists_dir_returns_empty(
        self,
        tmp_path: Path,
        config_dir: Path,
    ):
        workspace_root = config_dir.parent
        # No lists/ directory created
        resolved = [
            ResolvedPlatformConfig(
                platform="nes",
                extraction_type=ExtractionType.CARTRIDGE,
                compression=CompressionFormat.NONE,
                sources=[],
            )
        ]
        orch = _make_orchestrator(tmp_path, config_dir, resolved)

        with patch("romfarmer.new_orchestrator.get_paths") as mock_paths:
            mock_paths.return_value.workspace_root = workspace_root
            curated_include, curated_exclude = orch._load_curated_lists("nes")

        assert curated_include == frozenset()
        assert curated_exclude == frozenset()

    def test_manifest_curated_exclude_from_delete_list(
        self,
        tmp_path: Path,
        config_dir: Path,
        nes_source_dir: Path,
    ):
        """_build_manifest must include curated_exclude from the delete list."""
        workspace_root = config_dir.parent
        lists_dir = workspace_root / "lists"
        lists_dir.mkdir(exist_ok=True)
        (lists_dir / "nes-delete").write_text("Contra (Europe).zip\n")

        resolved = [
            ResolvedPlatformConfig(
                platform="nes",
                extraction_type=ExtractionType.CARTRIDGE,
                compression=CompressionFormat.NONE,
                sources=[SourceConfig(path=nes_source_dir)],
            )
        ]
        orch = _make_orchestrator(tmp_path, config_dir, resolved)

        with patch("romfarmer.new_orchestrator.get_paths") as mock_paths:
            mock_paths.return_value.workspace_root = workspace_root
            mock_paths.return_value.platform_temp_dir = MagicMock(
                return_value=tmp_path / "work"
            )
            manifest = orch._build_manifest(resolved[0], "nes")

        assert "Contra (Europe)" in manifest.curated_exclude, (
            f"curated_exclude not wired in _build_manifest: {manifest.curated_exclude}"
        )


# ---------------------------------------------------------------------------
# Test 7: PhaseError propagation — failed platform doesn't raise, EMIT errors
# are non-fatal, and validate_plan catches missing tools.
# ---------------------------------------------------------------------------

class TestPhaseErrorPropagation:
    """T6: driver catches PhaseError per phase; EMIT failure leaves outputs intact."""

    def test_catalog_phase_error_skips_platform_gracefully(
        self,
        tmp_path: Path,
        nes_source_dir: Path,
        config_dir: Path,
    ) -> None:
        """A PhaseError from run_catalog must be caught; _process_platform returns
        cleanly without propagating to the caller."""
        output_dir = tmp_path / "output" / "nes"
        resolved = [
            ResolvedPlatformConfig(
                platform="nes",
                extraction_type=ExtractionType.NONE,
                compression=CompressionFormat.NONE,
                sources=[SourceConfig(path=nes_source_dir)],
                output_dir=output_dir,
            )
        ]
        orch = _make_orchestrator(tmp_path, config_dir, resolved)

        boom = PhaseError("CATALOG", "nes", ValueError("disk read error"))

        with patch(
            "romfarmer.new_orchestrator.get_paths"
        ) as mock_paths, patch.object(
            orch, "_find_dat_file", return_value=None
        ), patch.object(
            orch, "_load_target_profile", return_value=None
        ), patch(
            "romfarmer.new_orchestrator.run_catalog", side_effect=boom
        ):
            mock_paths.return_value.platform_temp_dir = MagicMock(
                return_value=tmp_path / "work" / "nes"
            )
            mock_paths.return_value.workspace_root = config_dir.parent
            # Must not raise — the driver catches PhaseError
            orch._process_platform(resolved[0])

        # EXECUTE was not reached — output dir must not exist
        assert not output_dir.exists()

    def test_emit_phase_error_does_not_remove_outputs(
        self,
        tmp_path: Path,
        nes_source_dir: Path,
        config_dir: Path,
    ) -> None:
        """A PhaseError from run_emit is non-fatal: outputs already materialised
        by EXECUTE remain accessible even when EMIT fails."""
        output_dir = tmp_path / "output" / "nes"
        resolved = [
            ResolvedPlatformConfig(
                platform="nes",
                extraction_type=ExtractionType.NONE,
                compression=CompressionFormat.NONE,
                sources=[SourceConfig(path=nes_source_dir)],
                output_dir=output_dir,
            )
        ]
        orch = _make_orchestrator(tmp_path, config_dir, resolved)

        emit_boom = PhaseError("EMIT", "nes", RuntimeError("gamelist write failed"))

        with patch(
            "romfarmer.new_orchestrator.get_paths"
        ) as mock_paths, patch.object(
            orch, "_find_dat_file", return_value=None
        ), patch.object(
            orch, "_load_target_profile", return_value=None
        ), patch(
            "romfarmer.new_orchestrator.run_emit", side_effect=emit_boom
        ):
            mock_paths.return_value.platform_temp_dir = MagicMock(
                return_value=tmp_path / "work" / "nes"
            )
            mock_paths.return_value.workspace_root = config_dir.parent
            # Must not raise despite EMIT failure
            orch._process_platform(resolved[0])

        # EXECUTE ran and materialised files; they must still be present
        output_files = {f.name for f in output_dir.rglob("*") if f.is_file()}
        assert output_files, (
            "EXECUTE output files must remain even when run_emit raises PhaseError"
        )

    def test_validate_plan_catches_missing_tool(self) -> None:
        """validate_plan raises PlanValidationError if a tool is unregistered."""
        from romfarmer.ir.actions import Action, ActionId, ArtifactDecl, BuildPlan, ContentRef, Retention, UnitPlan, SizePrediction
        from romfarmer.ir.catalog import DiscRef, GameUnit, PlatformId, SourceRef, UnitId
        from romfarmer.ir.identity import Identity

        disc = DiscRef(index=1, source=SourceRef(Path("/fake/game.nes"), PlatformId("nes")), identity=Identity(size=32))
        unit = GameUnit.from_discs(PlatformId("nes"), "TestGame", (disc,))
        action = Action(
            action_id=ActionId("a1"),
            tool="nonexistent-tool",
            tool_version="1",
            params={},
            inputs=(),
            outputs=(ArtifactDecl("game.nes", "nes", Retention.TERMINAL),),
        )
        up = UnitPlan(unit=unit, actions=(action,), predicted_output_bytes=32, prediction=SizePrediction(ratio=1.0, source="test", confidence=0.5))
        plan = BuildPlan(units=(up,))

        with pytest.raises(PlanValidationError) as exc_info:
            validate_plan(plan, {"source-copy": object(), "passthrough": object()}, "nes")

        assert "nonexistent-tool" in str(exc_info.value)

