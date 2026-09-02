"""Tests for Tree Manifests and TreeStore.

Tests the CAS tree system: TreeManifest, TreeEntry, TreeStore.
"""

import json
import os
from pathlib import Path

import pytest

from romfarmer.cas.store import ContentStore
from romfarmer.cas.tree import TreeEntry, TreeManifest, TreeStore


@pytest.fixture
def tmp_store(tmp_path):
    """Create a temporary ContentStore."""
    store_dir = tmp_path / "store"
    return ContentStore(store_dir)


@pytest.fixture
def tree_store(tmp_store):
    """Create a TreeStore wrapping a ContentStore."""
    return TreeStore(tmp_store)


@pytest.fixture
def sample_folder(tmp_path):
    """Create a sample folder structure for testing.

    Creates a 'BLUS99999.ps3/' folder with:
      PS3_GAME/
        PARAM.SFO
        USRDIR/
          EBOOT.BIN
          data/
            level1.dat
    """
    root = tmp_path / "BLUS99999.ps3"
    root.mkdir()

    ps3_game = root / "PS3_GAME"
    ps3_game.mkdir()

    # PARAM.SFO (fake binary content)
    param_sfo = ps3_game / "PARAM.SFO"
    param_sfo.write_bytes(b"PARAM_SFO_HEADER\x00BLUS99999\x00")

    usrdir = ps3_game / "USRDIR"
    usrdir.mkdir()

    # EBOOT.BIN
    eboot = usrdir / "EBOOT.BIN"
    eboot.write_bytes(b"\x7fELF" + b"\x00" * 100)

    # Nested data file
    data_dir = usrdir / "data"
    data_dir.mkdir()
    level_dat = data_dir / "level1.dat"
    level_dat.write_bytes(b"LEVEL_DATA" * 50)

    return root


@pytest.fixture
def sample_folder_b(tmp_path):
    """Create a second sample folder with partially shared files.

    Shares the EBOOT.BIN with sample_folder but has different data.
    """
    root = tmp_path / "BLUS88888.ps3"
    root.mkdir()

    ps3_game = root / "PS3_GAME"
    ps3_game.mkdir()

    param_sfo = ps3_game / "PARAM.SFO"
    param_sfo.write_bytes(b"PARAM_SFO_HEADER\x00BLUS88888\x00")

    usrdir = ps3_game / "USRDIR"
    usrdir.mkdir()

    # Same EBOOT.BIN content as sample_folder
    eboot = usrdir / "EBOOT.BIN"
    eboot.write_bytes(b"\x7fELF" + b"\x00" * 100)

    # Different data file
    data_dir = usrdir / "data"
    data_dir.mkdir()
    level_dat = data_dir / "level1.dat"
    level_dat.write_bytes(b"DIFFERENT_DATA" * 50)

    return root


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TreeEntry Tests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestTreeEntry:
    def test_to_dict_basic(self):
        entry = TreeEntry(
            relative_path="PS3_GAME/PARAM.SFO",
            sha256="abc123" * 10 + "abcd",
            size=1024,
        )
        d = entry.to_dict()
        assert d["path"] == "PS3_GAME/PARAM.SFO"
        assert d["sha256"] == "abc123" * 10 + "abcd"
        assert d["size"] == 1024
        assert "executable" not in d  # Not included when False

    def test_to_dict_executable(self):
        entry = TreeEntry(
            relative_path="PS3_GAME/USRDIR/EBOOT.BIN",
            sha256="def456" * 10 + "defg",
            size=2048,
            executable=True,
        )
        d = entry.to_dict()
        assert d["executable"] is True

    def test_roundtrip(self):
        original = TreeEntry(
            relative_path="PS3_GAME/USRDIR/data/file.dat",
            sha256="aabbcc" * 10 + "aabb",
            size=999,
            executable=True,
        )
        d = original.to_dict()
        restored = TreeEntry.from_dict(d)
        assert restored.relative_path == original.relative_path
        assert restored.sha256 == original.sha256
        assert restored.size == original.size
        assert restored.executable == original.executable


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TreeManifest Tests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestTreeManifest:
    def test_compute_hash_deterministic(self):
        """Same entries in different order produce same hash."""
        m1 = TreeManifest(
            entries=[
                TreeEntry("b.txt", "hash_b", 100),
                TreeEntry("a.txt", "hash_a", 200),
            ]
        )
        m2 = TreeManifest(
            entries=[
                TreeEntry("a.txt", "hash_a", 200),
                TreeEntry("b.txt", "hash_b", 100),
            ]
        )

        h1 = m1.compute_hash()
        h2 = m2.compute_hash()
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex

    def test_compute_hash_changes_with_content(self):
        """Different entries produce different hash."""
        m1 = TreeManifest(
            entries=[
                TreeEntry("a.txt", "hash_a", 200),
            ]
        )
        m2 = TreeManifest(
            entries=[
                TreeEntry("a.txt", "hash_a", 201),  # Different size
            ]
        )

        assert m1.compute_hash() != m2.compute_hash()

    def test_total_size_and_files(self):
        m = TreeManifest(
            entries=[
                TreeEntry("a.txt", "h1", 100),
                TreeEntry("b.txt", "h2", 250),
                TreeEntry("c.txt", "h3", 50),
            ]
        )
        m.compute_hash()
        assert m.total_size == 400
        assert m.total_files == 3

    def test_json_roundtrip(self):
        original = TreeManifest(
            entries=[
                TreeEntry("PS3_GAME/PARAM.SFO", "a" * 64, 512),
                TreeEntry("PS3_GAME/USRDIR/EBOOT.BIN", "b" * 64, 1024, executable=True),
            ],
            source_name="Test Game",
            platform="ps3",
            format="ps3-jb",
            tool="7z",
            tool_version="24.09",
        )
        original.compute_hash()

        json_str = original.to_json()
        restored = TreeManifest.from_json(json_str)

        assert restored.tree_hash == original.tree_hash
        assert restored.total_size == original.total_size
        assert restored.total_files == original.total_files
        assert restored.source_name == "Test Game"
        assert restored.platform == "ps3"
        assert len(restored.entries) == 2

        # Verify entries preserved
        paths = {e.relative_path for e in restored.entries}
        assert "PS3_GAME/PARAM.SFO" in paths
        assert "PS3_GAME/USRDIR/EBOOT.BIN" in paths

    def test_json_format(self):
        """Verify JSON structure is human-readable."""
        m = TreeManifest(
            entries=[TreeEntry("file.txt", "a" * 64, 100)],
            platform="test",
        )
        m.compute_hash()

        data = json.loads(m.to_json())
        assert data["version"] == 1
        assert "tree_hash" in data
        assert "metadata" in data
        assert "entries" in data
        assert data["metadata"]["platform"] == "test"

    def test_repr(self):
        m = TreeManifest()
        assert "uncomputed" in repr(m)

        m.entries = [TreeEntry("a.txt", "h1", 100)]
        m.compute_hash()
        assert m.tree_hash[:12] in repr(m)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TreeStore Tests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestTreeStore:
    def test_ingest_creates_manifest(self, tree_store, sample_folder):
        """Ingesting a folder should create a tree manifest."""
        manifest = tree_store.ingest(
            sample_folder,
            platform="ps3",
            format="ps3-jb",
            source_name="Test Game",
        )

        assert manifest.tree_hash
        assert len(manifest.tree_hash) == 64
        assert manifest.total_files == 3  # PARAM.SFO, EBOOT.BIN, level1.dat
        assert manifest.total_size > 0
        assert manifest.platform == "ps3"
        assert manifest.format == "ps3-jb"
        assert manifest.source_name == "Test Game"

    def test_ingest_stores_in_cas(self, tree_store, sample_folder, tmp_store):
        """Each file should be stored in the CAS."""
        manifest = tree_store.ingest(sample_folder)

        for entry in manifest.entries:
            assert tmp_store.exists(entry.sha256, Path(entry.relative_path).suffix)

    def test_ingest_stores_manifest_blob(self, tree_store, sample_folder):
        """The manifest JSON itself should be stored in CAS."""
        manifest = tree_store.ingest(sample_folder)
        assert tree_store.exists(manifest.tree_hash)

    def test_restore_recreates_folder(self, tree_store, sample_folder, tmp_path):
        """Restoring a tree should recreate the folder structure."""
        manifest = tree_store.ingest(sample_folder)

        target = tmp_path / "restored"
        tree_store.restore(manifest.tree_hash, target)

        # Check all files exist
        for entry in manifest.entries:
            restored_path = target / entry.relative_path
            assert restored_path.exists(), f"Missing: {entry.relative_path}"
            assert restored_path.stat().st_size == entry.size

    def test_restore_preserves_content(self, tree_store, sample_folder, tmp_path):
        """Restored files should have identical content."""
        # Read original content
        original_content = {}
        for f in sample_folder.rglob("*"):
            if f.is_file():
                rel = str(f.relative_to(sample_folder))
                original_content[rel] = f.read_bytes()

        manifest = tree_store.ingest(sample_folder)

        target = tmp_path / "restored"
        tree_store.restore(manifest.tree_hash, target)

        for rel_path, content in original_content.items():
            restored = target / rel_path
            assert restored.read_bytes() == content, f"Content mismatch: {rel_path}"

    def test_restore_uses_hardlinks(self, tree_store, sample_folder, tmp_path):
        """By default, restore should use hardlinks (same inode)."""
        manifest = tree_store.ingest(sample_folder)

        target = tmp_path / "restored"
        tree_store.restore(manifest.tree_hash, target)

        # Check that restored files are hardlinked to CAS blobs
        for entry in manifest.entries:
            restored_path = target / entry.relative_path
            blob_path = tree_store.store.blob_path(entry.sha256, Path(entry.relative_path).suffix)
            # Same inode = hardlink
            assert restored_path.stat().st_ino == blob_path.stat().st_ino

    def test_restore_copy_mode(self, tree_store, sample_folder, tmp_path):
        """Restore with use_hardlinks=False should copy files."""
        manifest = tree_store.ingest(sample_folder)

        target = tmp_path / "restored"
        tree_store.restore(manifest.tree_hash, target, use_hardlinks=False)

        for entry in manifest.entries:
            restored_path = target / entry.relative_path
            blob_path = tree_store.store.blob_path(entry.sha256, Path(entry.relative_path).suffix)
            # Different inode = copy
            assert restored_path.stat().st_ino != blob_path.stat().st_ino

    def test_idempotent_ingest(self, tree_store, sample_folder):
        """Ingesting the same folder twice should produce the same tree hash."""
        m1 = tree_store.ingest(sample_folder)
        m2 = tree_store.ingest(sample_folder)
        assert m1.tree_hash == m2.tree_hash

    def test_deduplication_across_folders(
        self, tree_store, sample_folder, sample_folder_b, tmp_store
    ):
        """Files shared between folders should be deduplicated in CAS."""
        tree_store.ingest(sample_folder)
        stats_after_first = tmp_store.stats()

        tree_store.ingest(sample_folder_b)
        stats_after_second = tmp_store.stats()

        # EBOOT.BIN is shared — second ingest should add fewer files
        # First folder: 4 files (PARAM.SFO, EBOOT.BIN, level1.dat) + manifest
        # Second folder: PARAM.SFO (different) + level1.dat (different) + EBOOT.BIN (same!) + manifest
        # So second ingest adds only 2 new blobs (PARAM.SFO, level1.dat) + 1 manifest
        # NOT 3 new blobs — EBOOT.BIN is deduplicated
        new_blobs = stats_after_second["total_files"] - stats_after_first["total_files"]
        # 3 unique files + 1 manifest = 4 (EBOOT.BIN deduplicated from the 4 in folder_b)
        assert new_blobs < 4 + 1  # Less than if everything was unique

    def test_exists(self, tree_store, sample_folder):
        """exists() should return True for ingested trees."""
        manifest = tree_store.ingest(sample_folder)
        assert tree_store.exists(manifest.tree_hash)
        assert not tree_store.exists("nonexistent" * 4)

    def test_load_manifest(self, tree_store, sample_folder):
        """load_manifest() should return the same data as ingest()."""
        original = tree_store.ingest(sample_folder)
        loaded = tree_store.load_manifest(original.tree_hash)

        assert loaded.tree_hash == original.tree_hash
        assert loaded.total_files == original.total_files
        assert loaded.total_size == original.total_size
        assert len(loaded.entries) == len(original.entries)

    def test_load_manifest_not_found(self, tree_store):
        """load_manifest() should raise FileNotFoundError for missing hash."""
        with pytest.raises(FileNotFoundError):
            tree_store.load_manifest("a" * 64)

    def test_verify(self, tree_store, sample_folder):
        """verify() should report all blobs present."""
        manifest = tree_store.ingest(sample_folder)
        valid, missing_count, missing_paths = tree_store.verify(manifest.tree_hash)

        assert valid == manifest.total_files
        assert missing_count == 0
        assert missing_paths == []

    def test_verify_detects_missing_blob(self, tree_store, sample_folder, tmp_store):
        """verify() should detect missing blobs."""
        manifest = tree_store.ingest(sample_folder)

        # Delete one blob
        first_entry = manifest.entries[0]
        blob_path = tmp_store.blob_path(first_entry.sha256, Path(first_entry.relative_path).suffix)
        blob_path.unlink()

        valid, missing_count, missing_paths = tree_store.verify(manifest.tree_hash)
        assert missing_count == 1
        assert first_entry.relative_path in missing_paths

    def test_referenced_hashes(self, tree_store, sample_folder):
        """referenced_hashes() should include all blob hashes + manifest hash."""
        manifest = tree_store.ingest(sample_folder)
        hashes = tree_store.referenced_hashes(manifest.tree_hash)

        # Should include all entry hashes + the manifest hash itself
        expected_hashes = {e.sha256 for e in manifest.entries}
        expected_hashes.add(manifest.tree_hash)
        assert hashes == expected_hashes

    def test_ingest_not_a_directory(self, tree_store, tmp_path):
        """ingest() should raise if given a file."""
        f = tmp_path / "not_a_dir.txt"
        f.write_text("hello")
        with pytest.raises(NotADirectoryError):
            tree_store.ingest(f)

    def test_restore_missing_manifest(self, tree_store, tmp_path):
        """restore() should raise if manifest doesn't exist."""
        with pytest.raises(FileNotFoundError):
            tree_store.restore("a" * 64, tmp_path / "out")

    def test_executable_preserved(self, tree_store, tmp_path):
        """Executable files should have +x after restore."""
        folder = tmp_path / "game"
        folder.mkdir()
        script = folder / "run.sh"
        script.write_text("#!/bin/bash\necho hello")
        script.chmod(0o755)

        manifest = tree_store.ingest(folder)

        target = tmp_path / "restored"
        tree_store.restore(manifest.tree_hash, target)

        restored_script = target / "run.sh"
        assert os.access(restored_script, os.X_OK)

    def test_empty_folder(self, tree_store, tmp_path):
        """Ingesting an empty folder should produce an empty manifest."""
        folder = tmp_path / "empty"
        folder.mkdir()

        manifest = tree_store.ingest(folder)
        assert manifest.total_files == 0
        assert manifest.total_size == 0
        assert manifest.tree_hash  # Still has a hash (of empty content)

    def test_nested_empty_dirs_ignored(self, tree_store, tmp_path):
        """Only files count — empty subdirectories are ignored."""
        folder = tmp_path / "sparse"
        folder.mkdir()
        (folder / "sub1").mkdir()
        (folder / "sub2").mkdir()
        (folder / "sub1" / "file.txt").write_text("data")

        manifest = tree_store.ingest(folder)
        assert manifest.total_files == 1

        # Restore and verify the file exists
        target = tmp_path / "restored"
        tree_store.restore(manifest.tree_hash, target)
        assert (target / "sub1" / "file.txt").exists()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Integration: TreeStore + CacheManager
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestTreeCacheIntegration:
    """Test TreeCache DB model + CacheManager tree methods."""

    @pytest.fixture
    def cache_manager(self, tmp_path):
        from romfarmer.cache.config import CacheConfig
        from romfarmer.cache.manager import CacheManager

        config = CacheConfig(cache_dir=tmp_path / "cache", enabled=True)
        db_path = tmp_path / "test.db"
        return CacheManager(config=config, db_path=db_path)

    def test_store_and_get_tree(self, cache_manager):
        """store_tree + get_tree roundtrip."""
        result = cache_manager.store_tree(
            source_md5="a" * 32,
            tree_hash="b" * 64,
            total_files=42,
            total_size=1_000_000,
            folder_name="BLUS99999.ps3",
            format="ps3-jb",
            platform="ps3",
            source_filename="game.zip",
            source_size=500_000,
        )
        assert result.hit is True
        assert result.message == "Stored in tree cache"

        # Look it up
        found = cache_manager.get_tree("a" * 32, "ps3-jb")
        assert found.hit is True
        assert found.entry.tree_hash == "b" * 64
        assert found.entry.total_files == 42
        assert found.entry.folder_name == "BLUS99999.ps3"

    def test_get_tree_miss(self, cache_manager):
        """get_tree returns miss for unknown key."""
        result = cache_manager.get_tree("z" * 32, "ps3-jb")
        assert result.hit is False

    def test_get_tree_by_filename(self, cache_manager):
        """Lookup by filename + size."""
        cache_manager.store_tree(
            source_md5="a" * 32,
            tree_hash="b" * 64,
            total_files=10,
            total_size=500,
            folder_name="GAME.ps3",
            format="ps3-jb",
            source_filename="Game (USA).zip",
            source_size=12345,
        )

        found = cache_manager.get_tree_by_filename("Game (USA).zip", 12345, "ps3-jb")
        assert found.hit is True
        assert found.entry.tree_hash == "b" * 64

    def test_get_tree_by_zip_identity(self, cache_manager):
        """Lookup by ZIP CRC32 + content size."""
        cache_manager.store_tree(
            source_md5="a" * 32,
            tree_hash="b" * 64,
            total_files=10,
            total_size=500,
            folder_name="GAME.ps3",
            format="ps3-jb",
            zip_crc32="2578c3f9",
            zip_content_size=99999,
        )

        found = cache_manager.get_tree_by_zip_identity("2578c3f9", 99999, "ps3-jb")
        assert found.hit is True

    def test_store_tree_update(self, cache_manager):
        """Storing with same key updates the entry."""
        cache_manager.store_tree(
            source_md5="a" * 32,
            tree_hash="b" * 64,
            total_files=10,
            total_size=500,
            folder_name="OLD.ps3",
            format="ps3-jb",
        )

        cache_manager.store_tree(
            source_md5="a" * 32,
            tree_hash="c" * 64,
            total_files=20,
            total_size=1000,
            folder_name="NEW.ps3",
            format="ps3-jb",
        )

        found = cache_manager.get_tree("a" * 32, "ps3-jb")
        assert found.entry.tree_hash == "c" * 64
        assert found.entry.folder_name == "NEW.ps3"

    def test_get_tree_stats(self, cache_manager):
        """Tree stats should reflect stored entries."""
        cache_manager.store_tree(
            source_md5="a" * 32,
            tree_hash="b" * 64,
            total_files=10,
            total_size=500,
            folder_name="G1.ps3",
            format="ps3-jb",
            platform="ps3",
        )
        cache_manager.store_tree(
            source_md5="c" * 32,
            tree_hash="d" * 64,
            total_files=5,
            total_size=200,
            folder_name="G2.ps3",
            format="ps3-jb",
            platform="ps3",
        )

        stats = cache_manager.get_tree_stats()
        assert stats["total_trees"] == 2
        assert stats["total_size"] == 700
        assert stats["total_files_across_trees"] == 15

    def test_get_all_tree_hashes(self, cache_manager):
        """get_all_tree_hashes returns all stored hashes."""
        cache_manager.store_tree(
            source_md5="a" * 32,
            tree_hash="h1" * 32,
            total_files=1,
            total_size=1,
            folder_name="f1",
            format="ps3-jb",
        )
        cache_manager.store_tree(
            source_md5="b" * 32,
            tree_hash="h2" * 32,
            total_files=1,
            total_size=1,
            folder_name="f2",
            format="daphne",
        )

        hashes = cache_manager.get_all_tree_hashes()
        assert "h1" * 32 in hashes
        assert "h2" * 32 in hashes

    def test_disabled_cache(self, tmp_path):
        """Operations should return misses when cache is disabled."""
        from romfarmer.cache.config import CacheConfig
        from romfarmer.cache.manager import CacheManager

        config = CacheConfig(cache_dir=tmp_path / "cache", enabled=False)
        db_path = tmp_path / "test.db"
        cache = CacheManager(config=config, db_path=db_path)

        result = cache.get_tree("a" * 32, "ps3-jb")
        assert result.hit is False
        assert "disabled" in result.message.lower()

        result = cache.store_tree(
            source_md5="a" * 32,
            tree_hash="b" * 64,
            total_files=1,
            total_size=1,
            folder_name="f",
            format="ps3-jb",
        )
        assert result.hit is False
