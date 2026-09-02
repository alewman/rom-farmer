"""Tests for pool merge, threshold apply, and BuildSpec optimizer_thresholds
resolver expansion.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from romfarmer.config.models import DATSource
from romfarmer.config.slim_platform import DATReference
from romfarmer.farmhand.optimizer.merge import (
    _merge_entries,
    merge_pools,
    merge_pools_from_builds,
)
from romfarmer.farmhand.optimizer.pool import PoolEntry
from romfarmer.farmhand.optimizer.thresholds import (
    apply_thresholds_to_build,
    apply_thresholds_to_builds,
    load_thresholds_from_optimizer_log,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_pool_manifest(pool_dir: Path, platform: str, entries: list[dict]) -> None:
    pool_dir.mkdir(parents=True, exist_ok=True)
    (pool_dir / f"{platform}.json").write_text(json.dumps(entries, indent=2))


def _make_entry(
    name: str, rating: float = 0.8, generation: str = "gen6", size_bytes: int = 1_000_000_000
) -> dict:
    return dataclasses.asdict(
        PoolEntry(
            name=name,
            rating=rating,
            generation=generation,
            size_bytes=size_bytes,
            platform="psx",
        )
    )


# ===========================================================================
# merge_pools
# ===========================================================================


class TestMergePools:
    def test_single_source_copied(self, tmp_path):
        src = tmp_path / "build-a" / ".pool"
        _write_pool_manifest(src, "psx", [_make_entry("Game A"), _make_entry("Game B")])

        out = tmp_path / "merged"
        result = merge_pools([src], out)

        assert result.platforms_merged == 1
        assert result.games_total == 2
        assert (out / "psx.json").exists()

    def test_two_sources_distinct_platforms(self, tmp_path):
        src_a = tmp_path / "a" / ".pool"
        src_b = tmp_path / "b" / ".pool"
        _write_pool_manifest(src_a, "psx", [_make_entry("Game A")])
        _write_pool_manifest(src_b, "n64", [_make_entry("Game B"), _make_entry("Game C")])

        out = tmp_path / "merged"
        result = merge_pools([src_a, src_b], out)

        assert result.platforms_merged == 2
        assert result.games_total == 3
        assert result.conflicts_resolved == 0
        assert (out / "psx.json").exists()
        assert (out / "n64.json").exists()

    def test_conflict_platforms_merged(self, tmp_path):
        src_a = tmp_path / "a" / ".pool"
        src_b = tmp_path / "b" / ".pool"
        _write_pool_manifest(src_a, "psx", [_make_entry("Game A"), _make_entry("Game B")])
        _write_pool_manifest(src_b, "psx", [_make_entry("Game B"), _make_entry("Game C")])

        out = tmp_path / "merged"
        result = merge_pools([src_a, src_b], out)

        assert result.conflicts_resolved == 1
        entries = json.loads((out / "psx.json").read_text())
        names = {e["name"] for e in entries}
        # All three unique names should be present
        assert names == {"Game A", "Game B", "Game C"}

    def test_missing_source_skipped(self, tmp_path):
        src_a = tmp_path / "a" / ".pool"
        _write_pool_manifest(src_a, "psx", [_make_entry("Game A")])
        missing = tmp_path / "nonexistent" / ".pool"

        out = tmp_path / "merged"
        result = merge_pools([src_a, missing], out)

        assert result.platforms_merged == 1

    def test_no_overwrite_preserves_existing(self, tmp_path):
        src_a = tmp_path / "a" / ".pool"
        _write_pool_manifest(src_a, "psx", [_make_entry("Game A")])

        out = tmp_path / "merged"
        out.mkdir()
        (out / "psx.json").write_text(json.dumps([_make_entry("Existing Game")]))

        merge_pools([src_a], out, overwrite=False)

        entries = json.loads((out / "psx.json").read_text())
        assert entries[0]["name"] == "Existing Game"


class TestMergeEntries:
    def test_deduplication_by_name(self):
        existing = [_make_entry("A"), _make_entry("B")]
        incoming = [_make_entry("B"), _make_entry("C")]
        merged = _merge_entries(existing, incoming)
        names = [e["name"] for e in merged]
        assert names == ["A", "B", "C"]

    def test_existing_wins_on_conflict(self):
        # B appears in both; existing version (rating=0.9) should win
        existing = [
            {
                "name": "B",
                "rating": 0.9,
                "generation": "gen6",
                "size_bytes": 100,
                "multi_disc_group": None,
                "is_disc_anchor": True,
                "platform": "psx",
            }
        ]
        incoming = [
            {
                "name": "B",
                "rating": 0.5,
                "generation": "gen6",
                "size_bytes": 100,
                "multi_disc_group": None,
                "is_disc_anchor": True,
                "platform": "psx",
            }
        ]
        merged = _merge_entries(existing, incoming)
        assert len(merged) == 1
        assert merged[0]["rating"] == 0.9


class TestMergePoolsFromBuilds:
    def test_resolves_pool_dirs(self, tmp_path):
        output_base = tmp_path / "output"
        pool_dir = output_base / "my-build" / ".pool"
        _write_pool_manifest(pool_dir, "gb", [_make_entry("Tetris")])

        out = tmp_path / "merged"
        result = merge_pools_from_builds(
            build_names=["my-build"],
            output=out,
            output_base=output_base,
        )
        assert result.platforms_merged == 1

    def test_raises_when_no_pools_found(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="No pool manifests found"):
            merge_pools_from_builds(
                build_names=["nonexistent"],
                output=tmp_path / "out",
                output_base=tmp_path,
            )


# ===========================================================================
# apply_thresholds_to_build
# ===========================================================================


class TestApplyThresholdsTooBuild:
    def _write_build(self, path: Path, data: dict) -> None:
        path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))

    def test_writes_thresholds(self, tmp_path):
        build_path = tmp_path / "my-build.yaml"
        self._write_build(build_path, {"name": "my-build", "recipes": ["test"]})

        result = apply_thresholds_to_build(build_path, {"gen6": 0.85, "gen7": 0.92})

        assert result.changed is True
        raw = yaml.safe_load(build_path.read_text())
        assert raw["optimizer_thresholds"] == {"gen6": 0.85, "gen7": 0.92}

    def test_zero_thresholds_stripped(self, tmp_path):
        build_path = tmp_path / "my-build.yaml"
        self._write_build(build_path, {"name": "my-build", "recipes": ["test"]})

        apply_thresholds_to_build(build_path, {"gen3": 0.0, "gen4": 0.0, "gen6": 0.85})

        raw = yaml.safe_load(build_path.read_text())
        assert "gen3" not in raw["optimizer_thresholds"]
        assert raw["optimizer_thresholds"]["gen6"] == 0.85

    def test_dry_run_does_not_write(self, tmp_path):
        build_path = tmp_path / "my-build.yaml"
        original = {"name": "my-build", "recipes": ["test"]}
        self._write_build(build_path, original)

        result = apply_thresholds_to_build(build_path, {"gen6": 0.85}, dry_run=True)

        assert result.changed is True  # reports what would change
        raw = yaml.safe_load(build_path.read_text())
        assert "optimizer_thresholds" not in raw  # but file is untouched

    def test_no_change_when_same(self, tmp_path):
        build_path = tmp_path / "my-build.yaml"
        self._write_build(
            build_path,
            {"name": "my-build", "recipes": ["test"], "optimizer_thresholds": {"gen6": 0.85}},
        )

        result = apply_thresholds_to_build(build_path, {"gen6": 0.85})
        assert result.changed is False

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            apply_thresholds_to_build(tmp_path / "nonexistent.yaml", {"gen6": 0.8})


class TestApplyThresholdsToBuilds:
    def test_applies_to_multiple(self, tmp_path):
        builds_dir = tmp_path / "builds"
        builds_dir.mkdir()
        for name in ["build-a", "build-b"]:
            (builds_dir / f"{name}.yaml").write_text(yaml.dump({"name": name, "recipes": ["r"]}))

        results = apply_thresholds_to_builds(
            build_names=["build-a", "build-b"],
            thresholds={"gen6": 0.9},
            builds_dir=builds_dir,
        )

        assert len(results) == 2
        assert all(r.changed for r in results)

    def test_missing_build_skipped(self, tmp_path):
        builds_dir = tmp_path / "builds"
        builds_dir.mkdir()
        (builds_dir / "exists.yaml").write_text(yaml.dump({"name": "exists", "recipes": ["r"]}))

        results = apply_thresholds_to_builds(
            build_names=["exists", "missing"],
            thresholds={"gen6": 0.9},
            builds_dir=builds_dir,
        )

        # Only 1 result (missing was skipped)
        assert len(results) == 1
        assert results[0].build_name == "exists"


# ===========================================================================
# load_thresholds_from_optimizer_log
# ===========================================================================


class TestLoadThresholdsFromLog:
    def test_reads_final_thresholds(self, tmp_path):
        log = tmp_path / "optimizer.log.json"
        log.write_text(
            json.dumps(
                {
                    "build_name": "test",
                    "verdict": "converged",
                    "final_thresholds": {"gen5": 0.75, "gen6": 0.85},
                }
            )
        )

        thresholds = load_thresholds_from_optimizer_log(log)
        assert thresholds["gen5"] == 0.75
        assert thresholds["gen6"] == 0.85

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_thresholds_from_optimizer_log(tmp_path / "missing.json")

    def test_missing_key_raises(self, tmp_path):
        log = tmp_path / "optimizer.log.json"
        log.write_text(json.dumps({"verdict": "exhausted"}))
        with pytest.raises(KeyError, match="final_thresholds"):
            load_thresholds_from_optimizer_log(log)


# ===========================================================================
# BuildSpec optimizer_thresholds field + resolver expansion
# ===========================================================================


class TestBuildSpecOptimizerThresholds:
    def test_field_defaults_empty(self):
        from romfarmer.config.build_spec import BuildSpec

        spec = BuildSpec(name="test", target="t", recipes=["r"])
        assert spec.optimizer_thresholds == {}

    def test_field_accepts_thresholds(self):
        from romfarmer.config.build_spec import BuildSpec

        spec = BuildSpec(
            name="test",
            target="t",
            recipes=["r"],
            optimizer_thresholds={"gen6": 0.85, "gen7": 0.90},
        )
        assert spec.optimizer_thresholds["gen6"] == 0.85

    def test_resolver_applies_threshold_to_platform(self):
        """Platform in gen6 should get min_rating from optimizer_thresholds."""
        from romfarmer.config.build_spec import BuildSpec
        from romfarmer.config.recipe import RecipeSpec
        from romfarmer.config.resolver import ConfigResolver
        from romfarmer.config.slim_platform import SlimPlatformConfig

        _dat = DATReference(source=DATSource.REDUMP_RETOOL_1G1R_ENG)
        # Build a minimal platform + recipe + spec
        platform = SlimPlatformConfig(
            name="psx",
            display_name="PlayStation",
            dat=_dat,
            sources=[],
        )
        recipe = RecipeSpec(name="redump-chd", platforms=["psx"])
        spec = BuildSpec(
            name="retrobat-fill",
            target="retrobat-pc",
            recipes=["redump-chd"],
            optimizer_thresholds={"gen5": 0.8, "gen6": 0.85},
        )

        resolver = ConfigResolver(
            platforms={"psx": platform},
            recipes={"redump-chd": recipe},
            composed_target=None,
        )

        with patch(
            "romfarmer.farmhand.optimizer.pool._get_generation",
            return_value="gen6",
        ):
            resolved = resolver.resolve(spec)

        assert len(resolved) == 1
        psx = resolved[0]
        assert psx.selection is not None
        assert psx.selection.min_rating == pytest.approx(0.85)

    def test_resolver_skips_floor_gen(self):
        """Platforms in floor gens (gen3, gen4) should NOT get a selection added."""
        from romfarmer.config.build_spec import BuildSpec
        from romfarmer.config.recipe import RecipeSpec
        from romfarmer.config.resolver import ConfigResolver
        from romfarmer.config.slim_platform import SlimPlatformConfig

        _dat = DATReference(source=DATSource.RETOOL_1G1R_ENG)
        platform = SlimPlatformConfig(name="nes", display_name="NES", dat=_dat, sources=[])
        recipe = RecipeSpec(name="nointro-7z", platforms=["nes"])
        spec = BuildSpec(
            name="test",
            target="t",
            recipes=["nointro-7z"],
            optimizer_thresholds={"gen3": 0.0, "gen6": 0.85},
        )

        resolver = ConfigResolver(
            platforms={"nes": platform},
            recipes={"nointro-7z": recipe},
            composed_target=None,
        )

        with patch(
            "romfarmer.farmhand.optimizer.pool._get_generation",
            return_value="gen3",
        ):
            resolved = resolver.resolve(spec)

        nes = resolved[0]
        assert nes.selection is None

    def test_resolver_explicit_selection_overrides_threshold(self):
        """A build.selection override should win over optimizer threshold."""
        from romfarmer.config.build_spec import BuildSpec
        from romfarmer.config.models import SelectionConfig
        from romfarmer.config.recipe import RecipeSpec
        from romfarmer.config.resolver import ConfigResolver
        from romfarmer.config.slim_platform import SlimPlatformConfig

        _dat = DATReference(source=DATSource.REDUMP_RETOOL_1G1R_ENG)
        platform = SlimPlatformConfig(name="ps2", display_name="PS2", dat=_dat, sources=[])
        recipe = RecipeSpec(name="redump-chd", platforms=["ps2"])
        spec = BuildSpec(
            name="test",
            target="t",
            recipes=["redump-chd"],
            optimizer_thresholds={"gen6": 0.85},
            selection=SelectionConfig(min_rating=0.95),  # explicit override
        )

        resolver = ConfigResolver(
            platforms={"ps2": platform},
            recipes={"redump-chd": recipe},
            composed_target=None,
        )

        with patch(
            "romfarmer.farmhand.optimizer.pool._get_generation",
            return_value="gen6",
        ):
            resolved = resolver.resolve(spec)

        ps2 = resolved[0]
        assert ps2.selection.min_rating == pytest.approx(0.95)
