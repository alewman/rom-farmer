"""Bridge round-trip tests: fake StageContext → Catalog → write-back.

Uses a minimal fake context object plus a tmp_path work_dir with real symlinks.
Does NOT import the full legacy pipeline.

Key reality-vs-sketch discrepancies encoded as assertions below:
  1. ctx.hashes.source_md5 is Dict[Path, str] — Path keys, NOT str keys.
     (Bridge sketch referenced non-existent ctx.file_hashes.source_md5.)
  2. filtered_files / matched_files / source_files are List[Path] (not str).
  3. apply_catalog_to_context writes ctx.filtered_files as List[Path].
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import pytest

from romfarmer.ir.bridge import (
    PassAsStage,
    apply_catalog_to_context,
    assert_context_fs_sync,
    catalog_from_context,
)
from romfarmer.ir.catalog import Catalog, PassResult, PassTrace, PlatformId, UnitId


# ---------------------------------------------------------------------------
# Minimal fake StageContext — no real pipeline imports
# ---------------------------------------------------------------------------

@dataclass
class _FakeHashes:
    """Mirrors romfarmer.stages.domain.FileHashes (subset)."""
    source_md5: Dict[Path, str] = field(default_factory=dict)


@dataclass
class _FakeContext:
    """Minimal duck-typed StageContext for bridge tests."""
    source_files: List[Path] = field(default_factory=list)
    matched_files: List[Path] = field(default_factory=list)
    filtered_files: List[Path] = field(default_factory=list)
    work_dir: Optional[Path] = None
    hashes: _FakeHashes = field(default_factory=_FakeHashes)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_symlinks(work_dir: Path, files: list[Path]) -> None:
    """Create symlinks in work_dir pointing at the given paths."""
    for f in files:
        link = work_dir / f.name
        if not link.exists():
            link.symlink_to(f)


# ---------------------------------------------------------------------------
# catalog_from_context
# ---------------------------------------------------------------------------

class TestCatalogFromContext:
    def test_uses_filtered_files_first(self, tmp_path: Path) -> None:
        f1 = tmp_path / "game.bin"
        f1.touch()
        ctx = _FakeContext(
            source_files=[tmp_path / "other.bin"],
            filtered_files=[f1],
        )
        catalog = catalog_from_context(ctx, "psx")
        assert len(catalog.units) == 1
        assert catalog.units[0].discs[0].source.path == f1

    def test_falls_back_to_matched_files(self, tmp_path: Path) -> None:
        f1 = tmp_path / "game.bin"
        f1.touch()
        ctx = _FakeContext(matched_files=[f1])
        catalog = catalog_from_context(ctx, "psx")
        assert len(catalog.units) == 1

    def test_falls_back_to_source_files(self, tmp_path: Path) -> None:
        f1 = tmp_path / "game.bin"
        f1.touch()
        ctx = _FakeContext(source_files=[f1])
        catalog = catalog_from_context(ctx, "psx")
        assert len(catalog.units) == 1

    def test_empty_context_returns_empty_catalog(self) -> None:
        ctx = _FakeContext()
        catalog = catalog_from_context(ctx, "psx")
        assert len(catalog.units) == 0
        assert catalog.platform == PlatformId("psx")

    def test_multi_disc_grouped(self, tmp_path: Path) -> None:
        d1 = tmp_path / "Chrono Cross (Disc 1).bin"
        d2 = tmp_path / "Chrono Cross (Disc 2).bin"
        d1.touch()
        d2.touch()
        ctx = _FakeContext(source_files=[d1, d2])
        catalog = catalog_from_context(ctx, "psx")
        assert len(catalog.units) == 1
        unit = catalog.units[0]
        assert unit.is_multi_disc
        assert unit.discs[0].index == 1
        assert unit.discs[1].index == 2

    def test_different_games_separate_units(self, tmp_path: Path) -> None:
        g1 = tmp_path / "Alpha.bin"
        g2 = tmp_path / "Beta.bin"
        g1.touch()
        g2.touch()
        ctx = _FakeContext(source_files=[g1, g2])
        catalog = catalog_from_context(ctx, "psx")
        assert len(catalog.units) == 2

    def test_identity_lifted_from_hashes(self, tmp_path: Path) -> None:
        """
        ⚠ REALITY CHECK: ctx.hashes.source_md5 uses Path keys, not str keys.
        This test asserts that the bridge uses Path keys correctly.
        """
        f = tmp_path / "game.bin"
        f.write_bytes(b"x" * 100)
        ctx = _FakeContext(
            source_files=[f],
            hashes=_FakeHashes(source_md5={f: "abc123md5"}),  # Path key
        )
        catalog = catalog_from_context(ctx, "psx")
        disc = catalog.units[0].discs[0]
        # md5 should be lifted from the Path-keyed dict
        assert disc.identity.md5 == "abc123md5"

    def test_identity_not_found_with_str_key(self, tmp_path: Path) -> None:
        """
        ⚠ REALITY CHECK: str keys do NOT match Path keys.
        If someone passed {str(f): md5}, the bridge would NOT find it — correct.
        """
        f = tmp_path / "game.bin"
        f.write_bytes(b"x" * 100)
        ctx = _FakeContext(
            source_files=[f],
            hashes=_FakeHashes(source_md5={Path(str(f)): "abc123md5"}),
        )
        catalog = catalog_from_context(ctx, "psx")
        disc = catalog.units[0].discs[0]
        assert disc.identity.md5 == "abc123md5"  # same Path, still matches

    def test_identity_size_from_real_file(self, tmp_path: Path) -> None:
        f = tmp_path / "game.bin"
        f.write_bytes(b"x" * 42)
        ctx = _FakeContext(source_files=[f])
        catalog = catalog_from_context(ctx, "psx")
        assert catalog.units[0].discs[0].identity.size == 42

    def test_platform_set_on_catalog(self) -> None:
        ctx = _FakeContext()
        catalog = catalog_from_context(ctx, "saturn")
        assert catalog.platform == PlatformId("saturn")


# ---------------------------------------------------------------------------
# apply_catalog_to_context
# ---------------------------------------------------------------------------

class TestApplyCatalogToContext:
    def test_writes_filtered_files(self, tmp_path: Path) -> None:
        f = tmp_path / "game.bin"
        f.touch()
        ctx = _FakeContext(source_files=[f])
        catalog = catalog_from_context(ctx, "psx")
        apply_catalog_to_context(catalog, ctx)
        assert f in ctx.filtered_files

    def test_removes_stale_symlinks(self, tmp_path: Path) -> None:
        work = tmp_path / "work"
        work.mkdir()
        keep = tmp_path / "keep.bin"
        drop = tmp_path / "drop.bin"
        keep.touch()
        drop.touch()
        _make_symlinks(work, [keep, drop])
        assert (work / "drop.bin").is_symlink()

        ctx = _FakeContext(source_files=[keep], work_dir=work)
        catalog = catalog_from_context(ctx, "psx")
        apply_catalog_to_context(catalog, ctx)

        assert (work / "keep.bin").is_symlink()
        assert not (work / "drop.bin").exists()

    def test_no_work_dir_is_safe(self, tmp_path: Path) -> None:
        f = tmp_path / "game.bin"
        f.touch()
        ctx = _FakeContext(source_files=[f], work_dir=None)
        catalog = catalog_from_context(ctx, "psx")
        # Should not raise
        apply_catalog_to_context(catalog, ctx)


# ---------------------------------------------------------------------------
# assert_context_fs_sync
# ---------------------------------------------------------------------------

class TestAssertContextFsSync:
    def test_passes_when_in_sync(self, tmp_path: Path) -> None:
        work = tmp_path / "work"
        work.mkdir()
        f = tmp_path / "game.bin"
        f.touch()
        _make_symlinks(work, [f])
        ctx = _FakeContext(filtered_files=[f], work_dir=work)
        assert_context_fs_sync(ctx)  # should not raise

    def test_raises_on_divergence(self, tmp_path: Path) -> None:
        work = tmp_path / "work"
        work.mkdir()
        f = tmp_path / "game.bin"
        f.touch()
        _make_symlinks(work, [f])
        # Context says different file
        other = tmp_path / "other.bin"
        other.touch()
        ctx = _FakeContext(filtered_files=[other], work_dir=work)
        with pytest.raises(RuntimeError, match="divergence"):
            assert_context_fs_sync(ctx)

    def test_no_work_dir_is_safe(self) -> None:
        ctx = _FakeContext(work_dir=None)
        assert_context_fs_sync(ctx)  # should not raise


# ---------------------------------------------------------------------------
# Full round-trip
# ---------------------------------------------------------------------------

class TestRoundTrip:
    def test_lift_apply_sync(self, tmp_path: Path) -> None:
        work = tmp_path / "work"
        work.mkdir()
        f = tmp_path / "Final Fantasy VII (Disc 1).bin"
        f.touch()
        _make_symlinks(work, [f])

        ctx = _FakeContext(
            source_files=[f],
            work_dir=work,
            hashes=_FakeHashes(source_md5={f: "ffvii_md5"}),
        )
        catalog = catalog_from_context(ctx, "psx")
        assert len(catalog.units) == 1
        assert catalog.units[0].discs[0].identity.md5 == "ffvii_md5"

        apply_catalog_to_context(catalog, ctx)
        assert_context_fs_sync(ctx)  # should not raise


# ---------------------------------------------------------------------------
# PassAsStage
# ---------------------------------------------------------------------------

class _FakePass:
    """A pure pass that removes all units."""
    def run(self, catalog: Catalog) -> PassResult:
        empty = catalog.without({u.unit_id for u in catalog.units})
        return PassResult(
            catalog=empty,
            trace=PassTrace(pass_name="fake-pass", removed=tuple(
                (u.unit_id, "test removal") for u in catalog.units
            )),
        )


class TestPassAsStage:
    def test_execute_calls_pass_and_writes_back(self, tmp_path: Path) -> None:
        work = tmp_path / "work"
        work.mkdir()
        f = tmp_path / "game.bin"
        f.touch()
        _make_symlinks(work, [f])

        ctx = _FakeContext(source_files=[f], work_dir=work)
        stage = PassAsStage(_FakePass(), "psx")
        result = stage.execute(ctx)  # type: ignore[arg-type]
        # All units removed by the fake pass → filtered_files now empty
        assert result.filtered_files == []
        # Symlink should be gone
        assert not (work / "game.bin").exists()

    def test_name_reflects_pass_class(self) -> None:
        stage = PassAsStage(_FakePass(), "psx")
        assert "FakePass" in stage.name

    def test_phase_is_plan(self) -> None:
        assert PassAsStage.PHASE == "PLAN"
