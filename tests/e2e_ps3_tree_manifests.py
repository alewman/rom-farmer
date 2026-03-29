#!/usr/bin/env python3
"""
End-to-end verification: PS3 transform pipeline + Tree Manifests.

Tests the entire chain with a real PS3 game (Terraria) from Myrient:
  1. Unzip encrypted ISO
  2. Find disc key
  3. Decrypt with PS3Dec
  4. Extract to JB folder
  5. Compare every file SHA-256 against a known-good reference build
  6. Ingest into CAS tree store
  7. Restore from tree cache and verify hardlinks match

Usage:
    python -m pytest tests/e2e_ps3_tree_manifests.py -v -s
    # or standalone:
    python tests/e2e_ps3_tree_manifests.py
"""

import hashlib
import shutil
import tempfile
from pathlib import Path

import pytest

# ── Paths ──────────────────────────────────────────────────────
SOURCE_ZIP = Path(
    "/data/emu/source/myrient.erista.me/files/Redump/"
    "Sony - PlayStation 3/Terraria (USA) (En,Fr,Es).zip"
)
KEYS_DIR = Path(
    "/data/emu/source/myrient.erista.me/files/Redump/"
    "Sony - PlayStation 3 - Disc Keys TXT"
)
REFERENCE_DIR = Path(
    "/data/emu/ps3netsrv/GAMES/Terraria (USA) (En,Fr,Es).ps3"
)

# SHA-256 of every file in the reference JB folder (sorted by path)
REFERENCE_HASHES = {
    "PS3_DISC.SFB": "53ec112d3f7025dabd88808a8b98bf72ade3b946a8c98c5c21077be5cd0d3e60",
    "PS3_GAME/ICON0.PNG": "7a645a1487033234917205cf186a340c1a2faa6bc4851308d768ba41df3d363d",
    "PS3_GAME/LICDIR/LIC.DAT": "a6b4a1d659d8a9902993a4ed41935a5e79b6dd0e665080339b7baae4ff819cf7",
    "PS3_GAME/PARAM.SFO": "da066965b3ca1de19dca78ffebde68a9860827be17fc7f738802db584297fa16",
    "PS3_GAME/PS3LOGO.DAT": "e08430957ac3f4ee719dc2ed04d3443c395dd3b997d8f34f68a1b5c37d92f425",
    "PS3_GAME/TROPDIR/NPWR04270_00/TROPHY.TRP": "3f778443b07ecd8211ec34208a72c9a9e4854503eeac73e4b36901430c35d64a",
    "PS3_GAME/USRDIR/EBOOT.BIN": "9538e0f33e8452a465973ef29e4ac8c52f818b5dda3ff70c432883fa27d9685f",
    "PS3_GAME/USRDIR/data.vfs": "6d70ff27c7047841064cf268453e0a7cbdde1ef51dc826232ff72602f2504810",
    "PS3_UPDATE/PS3UPDAT.PUP": "8835bd9c0c82d7d0c2ef7ac62bcbf36cd8f8e5651fb2e109de8734676bb1587c",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def skip_if_missing():
    """Skip tests when source files aren't available."""
    for p, label in [
        (SOURCE_ZIP, "source ZIP"),
        (KEYS_DIR, "disc keys dir"),
        (REFERENCE_DIR, "reference JB folder"),
    ]:
        if not p.exists():
            pytest.skip(f"{label} not found: {p}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Tests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestPS3PipelineE2E:
    """Full pipeline: source ZIP → JB folder → compare to reference."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        skip_if_missing()
        self.tmp_path = tmp_path
        self.output_dir = tmp_path / "output"
        self.output_dir.mkdir()
        self.cas_dir = tmp_path / "cas"
        self.cas_dir.mkdir()
        self.db_path = tmp_path / "cache.db"

    def _make_stage(self):
        """Create TransformPS3Stage with CAS tree store + cache manager."""
        from romfarmer.cas.store import ContentStore
        from romfarmer.cas.tree import TreeStore
        from romfarmer.cache.manager import CacheManager
        from romfarmer.cache.config import CacheConfig

        content_store = ContentStore(self.cas_dir)
        tree_store = TreeStore(content_store)

        config = CacheConfig(cache_dir=self.cas_dir)
        cache_manager = CacheManager(config=config, db_path=self.db_path)

        from romfarmer.stages.transform_ps3 import TransformPS3Stage

        stage = TransformPS3Stage(
            tree_store=tree_store,
            cache_manager=cache_manager,
        )
        return stage, tree_store, cache_manager

    def test_full_pipeline_matches_reference(self):
        """Extract Terraria ISO → compare every file hash to reference."""
        stage, tree_store, cache_manager = self._make_stage()

        # Run the single-game transform
        transformation = stage._transform_ps3_game(
            zip_file=SOURCE_ZIP,
            target_name="ps3netsrv",
            target_format="folder",
            keys_dir=KEYS_DIR,
            temp_dir=self.tmp_path / "temp",
            output_dir=self.output_dir,
        )

        # Basic assertions
        assert transformation.status.value == "success", (
            f"Transform failed: {transformation.error}"
        )
        assert transformation.final_file is not None
        game_folder = transformation.final_file
        assert game_folder.exists(), f"Output folder missing: {game_folder}"

        # Collect all files in output
        output_files = {}
        for f in sorted(game_folder.rglob("*")):
            if f.is_file():
                rel = str(f.relative_to(game_folder))
                output_files[rel] = sha256_file(f)

        # Must have exactly the same files
        assert set(output_files.keys()) == set(REFERENCE_HASHES.keys()), (
            f"File set mismatch.\n"
            f"  Extra:   {set(output_files) - set(REFERENCE_HASHES)}\n"
            f"  Missing: {set(REFERENCE_HASHES) - set(output_files)}"
        )

        # Every hash must match
        mismatches = []
        for rel_path, expected_hash in REFERENCE_HASHES.items():
            actual_hash = output_files[rel_path]
            if actual_hash != expected_hash:
                mismatches.append(
                    f"  {rel_path}: expected {expected_hash[:16]}… got {actual_hash[:16]}…"
                )

        assert not mismatches, (
            f"{len(mismatches)} file(s) differ from reference:\n"
            + "\n".join(mismatches)
        )

        print(f"\n✓ All {len(REFERENCE_HASHES)} files match reference hashes")
        print(f"  Output: {game_folder}")

    def test_tree_cache_ingest_and_stats(self):
        """After pipeline, verify tree was ingested into CAS."""
        stage, tree_store, cache_manager = self._make_stage()

        (self.tmp_path / "temp").mkdir(exist_ok=True)
        transformation = stage._transform_ps3_game(
            zip_file=SOURCE_ZIP,
            target_name="ps3netsrv",
            target_format="folder",
            keys_dir=KEYS_DIR,
            temp_dir=self.tmp_path / "temp",
            output_dir=self.output_dir,
        )
        assert transformation.status.value == "success"

        # Check tree cache has an entry
        stats = cache_manager.get_tree_stats()
        assert stats["total_trees"] >= 1

        # Look up by filename
        result = cache_manager.get_tree_by_filename(
            source_filename=SOURCE_ZIP.name,
            source_size=SOURCE_ZIP.stat().st_size,
            format="ps3-jb",
        )
        assert result.hit, "Expected tree cache hit by filename"
        assert result.entry.total_files == len(REFERENCE_HASHES)
        assert result.entry.folder_name.endswith(".ps3")

        print(f"\n✓ Tree cache entry: {result.entry.tree_hash[:16]}… "
              f"({result.entry.total_files} files, "
              f"{result.entry.total_size / (1024**2):.0f} MB)")

    def test_tree_cache_restore_produces_identical_output(self):
        """Build once → delete output → restore from cache → verify hashes."""
        stage, tree_store, cache_manager = self._make_stage()

        # First build
        (self.tmp_path / "temp").mkdir(exist_ok=True)
        transformation = stage._transform_ps3_game(
            zip_file=SOURCE_ZIP,
            target_name="ps3netsrv",
            target_format="folder",
            keys_dir=KEYS_DIR,
            temp_dir=self.tmp_path / "temp",
            output_dir=self.output_dir,
        )
        assert transformation.status.value == "success"
        first_folder = transformation.final_file

        # Delete the output
        shutil.rmtree(first_folder)
        assert not first_folder.exists()

        # Second build — should hit tree cache
        output_dir2 = self.tmp_path / "output2"
        output_dir2.mkdir()
        (self.tmp_path / "temp2").mkdir(exist_ok=True)
        transformation2 = stage._transform_ps3_game(
            zip_file=SOURCE_ZIP,
            target_name="ps3netsrv",
            target_format="folder",
            keys_dir=KEYS_DIR,
            temp_dir=self.tmp_path / "temp2",
            output_dir=output_dir2,
        )
        assert transformation2.status.value == "success"

        # Should have used tree-cache (check step tool)
        cache_step = transformation2.steps[0]
        assert cache_step.tool == "tree-cache", (
            f"Expected cache hit but got tool={cache_step.tool}"
        )

        # Verify restored files match reference
        restored_folder = transformation2.final_file
        for rel_path, expected_hash in REFERENCE_HASHES.items():
            file_path = restored_folder / rel_path
            assert file_path.exists(), f"Missing after restore: {rel_path}"
            actual_hash = sha256_file(file_path)
            assert actual_hash == expected_hash, (
                f"Hash mismatch after restore: {rel_path}"
            )

        # Verify files are hardlinks to CAS (inode should match CAS blob)
        sample_file = restored_folder / "PS3_GAME/PARAM.SFO"
        assert sample_file.stat().st_nlink >= 2, (
            "Restored file should be hardlinked to CAS blob"
        )

        print(f"\n✓ Cache restore verified — all {len(REFERENCE_HASHES)} files "
              f"match, hardlinked from CAS")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
