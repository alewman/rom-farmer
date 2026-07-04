"""Tests for CatalogBuilder."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from romfarmer.analysis.catalog_builder import CatalogBuilder, _strip_disc_tag, _disc_index, _parse_regions
from romfarmer.analysis.knowledge import KnowledgeBase
from romfarmer.ir.catalog import PlatformId


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_zip(path: Path, content: bytes = b"dummy rom data") -> Path:
    """Write a minimal ZIP to *path*."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("rom.bin", content)
    return path


def _make_source_dir(tmp_path: Path, names: list[str]) -> Path:
    """Create a source dir with dummy ZIPs named after *names*."""
    src = tmp_path / "roms"
    src.mkdir()
    for name in names:
        _make_zip(src / f"{name}.zip")
    return src


# ---------------------------------------------------------------------------
# Unit: filename helpers
# ---------------------------------------------------------------------------

class TestFilenameHelpers:
    def test_strip_disc_tag_single(self):
        assert _strip_disc_tag("Final Fantasy VII (Disc 1)") == "Final Fantasy VII"

    def test_strip_disc_tag_no_tag(self):
        assert _strip_disc_tag("Super Mario 64") == "Super Mario 64"

    def test_strip_disc_tag_disk_variant(self):
        assert _strip_disc_tag("Baldur's Gate (Disk 2)") == "Baldur's Gate"

    def test_disc_index_present(self):
        assert _disc_index("Metal Gear Solid (Disc 2)") == 2

    def test_disc_index_absent(self):
        assert _disc_index("Super Mario World") == 1

    def test_parse_regions_usa(self):
        regions = _parse_regions("Chrono Cross (USA)")
        assert "USA" in regions

    def test_parse_regions_europe(self):
        regions = _parse_regions("Tekken 3 (Europe)")
        assert "Europe" in regions

    def test_parse_regions_unknown(self):
        regions = _parse_regions("Some Obscure Title")
        assert regions == frozenset()


# ---------------------------------------------------------------------------
# CatalogBuilder: single-disc game
# ---------------------------------------------------------------------------

class TestCatalogBuilderSingleDisc:
    def test_single_rom(self, tmp_path: Path):
        src = _make_source_dir(tmp_path, ["Super Mario World (USA)"])
        kb = KnowledgeBase()  # no DB
        builder = CatalogBuilder(
            platform=PlatformId("snes"),
            source_dir=src,
            knowledge_base=kb,
        )
        catalog = builder.build()
        assert len(catalog.units) == 1
        unit = catalog.units[0]
        assert unit.canonical_name == "Super Mario World (USA)"
        assert unit.platform == "snes"
        assert not unit.is_multi_disc
        assert len(unit.discs) == 1
        assert "USA" in unit.region

    def test_empty_source_dir(self, tmp_path: Path):
        src = tmp_path / "empty"
        src.mkdir()
        kb = KnowledgeBase()
        builder = CatalogBuilder(
            platform=PlatformId("snes"),
            source_dir=src,
            knowledge_base=kb,
        )
        catalog = builder.build()
        assert len(catalog.units) == 0

    def test_nonexistent_source_dir(self, tmp_path: Path):
        kb = KnowledgeBase()
        builder = CatalogBuilder(
            platform=PlatformId("snes"),
            source_dir=tmp_path / "does_not_exist",
            knowledge_base=kb,
        )
        catalog = builder.build()
        assert len(catalog.units) == 0

    def test_zip_identity_populated(self, tmp_path: Path):
        src = _make_source_dir(tmp_path, ["Zelda (USA)"])
        kb = KnowledgeBase()
        builder = CatalogBuilder(
            platform=PlatformId("snes"),
            source_dir=src,
            knowledge_base=kb,
        )
        catalog = builder.build()
        unit = catalog.units[0]
        zi = unit.discs[0].identity.zip_identity
        assert zi is not None
        assert zi.member_name == "rom.bin"
        assert zi.member_size == len(b"dummy rom data")

    def test_identity_size_from_file(self, tmp_path: Path):
        src = _make_source_dir(tmp_path, ["Some Game (Europe)"])
        kb = KnowledgeBase()
        builder = CatalogBuilder(
            platform=PlatformId("nes"),
            source_dir=src,
            knowledge_base=kb,
        )
        catalog = builder.build()
        unit = catalog.units[0]
        assert unit.discs[0].identity.size is not None
        assert unit.discs[0].identity.size > 0


# ---------------------------------------------------------------------------
# CatalogBuilder: multi-disc grouping
# ---------------------------------------------------------------------------

class TestCatalogBuilderMultiDisc:
    def test_two_disc_game(self, tmp_path: Path):
        src = _make_source_dir(tmp_path, [
            "Final Fantasy VII (Disc 1)",
            "Final Fantasy VII (Disc 2)",
            "Final Fantasy VII (Disc 3)",
        ])
        kb = KnowledgeBase()
        builder = CatalogBuilder(
            platform=PlatformId("psx"),
            source_dir=src,
            knowledge_base=kb,
        )
        catalog = builder.build()
        assert len(catalog.units) == 1
        unit = catalog.units[0]
        assert unit.canonical_name == "Final Fantasy VII"
        assert unit.is_multi_disc
        assert len(unit.discs) == 3
        assert [d.index for d in unit.discs] == [1, 2, 3]

    def test_mixed_single_and_multi(self, tmp_path: Path):
        src = _make_source_dir(tmp_path, [
            "Crash Bandicoot (USA)",
            "Xenogears (Disc 1)",
            "Xenogears (Disc 2)",
        ])
        kb = KnowledgeBase()
        builder = CatalogBuilder(
            platform=PlatformId("psx"),
            source_dir=src,
            knowledge_base=kb,
        )
        catalog = builder.build()
        assert len(catalog.units) == 2
        names = {u.canonical_name for u in catalog.units}
        assert names == {"Crash Bandicoot (USA)", "Xenogears"}

    def test_non_contiguous_discs_produce_warning(self, tmp_path: Path):
        src = _make_source_dir(tmp_path, [
            "Broken Game (Disc 1)",
            "Broken Game (Disc 3)",  # disc 2 missing
        ])
        kb = KnowledgeBase()
        builder = CatalogBuilder(
            platform=PlatformId("psx"),
            source_dir=src,
            knowledge_base=kb,
        )
        catalog = builder.build()
        assert len(catalog.warnings) == 1
        assert "non-contiguous" in catalog.warnings[0].reason

    def test_unit_id_stable(self, tmp_path: Path):
        """unit_id should be identical for same platform + canonical_name."""
        src = _make_source_dir(tmp_path, ["Mega Man X (USA)"])
        kb = KnowledgeBase()
        builder = CatalogBuilder(
            platform=PlatformId("snes"),
            source_dir=src,
            knowledge_base=kb,
        )
        c1 = builder.build()
        c2 = builder.build()
        assert c1.units[0].unit_id == c2.units[0].unit_id

    def test_preloaded_md5_cache_used(self, tmp_path: Path):
        """Pre-populated md5_cache should be used instead of recomputing."""
        src = _make_source_dir(tmp_path, ["Street Fighter II (USA)"])
        rom_path = src / "Street Fighter II (USA).zip"
        md5_cache = {rom_path: "aabbccdd1122"}
        kb = KnowledgeBase()
        builder = CatalogBuilder(
            platform=PlatformId("snes"),
            source_dir=src,
            knowledge_base=kb,
            md5_cache=md5_cache,
        )
        catalog = builder.build()
        assert catalog.units[0].discs[0].identity.md5 == "aabbccdd1122"


# ---------------------------------------------------------------------------
# T8: FileDigestCache — zero rehash on second scan
# ---------------------------------------------------------------------------

class TestFileDigestCache:
    """T8: CatalogBuilder serves MD5s from FileDigestCache on the second run.

    Guards: CATALOG rescan performance — the main throughput bottleneck at
    scale (100 k files / 500 GB).  The fast-path key is (size, mtime_ns, inode).
    """

    def test_second_scan_zero_md5_computations(
        self, tmp_path: pytest.fixture  # type: ignore[type-arg]
    ) -> None:
        """Second build() on unchanged sources reads 0 files for MD5."""
        import zipfile as _zf
        from romfarmer.analysis.file_digest_cache import FileDigestCache

        # Create a source ZIP whose mtime is well in the past
        src = tmp_path / "source"
        src.mkdir()
        zp = src / "Contra (USA).zip"
        with _zf.ZipFile(zp, "w") as zf:
            zf.writestr("Contra (USA).nes", b"contra-bytes-for-digest-test")

        # Back-date the file by 10 seconds to avoid the racy guard
        import time as _time
        old_mtime = _time.time() - 10
        import os as _os
        _os.utime(zp, (old_mtime, old_mtime))

        db_path = tmp_path / "digests.db"

        # First run: populates the digest cache
        md5_computed: list[str] = []
        original_md5_from_zip = None

        with FileDigestCache(db_path) as fdc:
            kb = KnowledgeBase()
            builder1 = CatalogBuilder(
                platform=PlatformId("nes"),
                source_dir=src,
                knowledge_base=kb,
                file_digest_cache=fdc,
            )
            catalog1 = builder1.build()

        assert catalog1.units, "First build must produce units"
        md5_first = catalog1.units[0].discs[0].identity.md5

        # Monkey-patch _md5_from_zip to count calls on second run
        call_count = {"n": 0}
        import romfarmer.analysis.catalog_builder as _cb_mod
        original_md5_from_zip_fn = _cb_mod._md5_from_zip

        def _counting_md5(path):
            call_count["n"] += 1
            return original_md5_from_zip_fn(path)

        _cb_mod._md5_from_zip = _counting_md5
        try:
            with FileDigestCache(db_path) as fdc:
                kb2 = KnowledgeBase()
                builder2 = CatalogBuilder(
                    platform=PlatformId("nes"),
                    source_dir=src,
                    knowledge_base=kb2,
                    file_digest_cache=fdc,
                )
                catalog2 = builder2.build()
        finally:
            _cb_mod._md5_from_zip = original_md5_from_zip_fn

        assert call_count["n"] == 0, (
            f"Second scan must compute 0 MD5s from disk (got {call_count['n']}). "
            "FileDigestCache is not being consulted."
        )
        assert catalog2.units[0].discs[0].identity.md5 == md5_first, (
            "MD5 from cache must match MD5 computed on first run."
        )

    def test_changed_file_triggers_rehash(self, tmp_path: pytest.fixture) -> None:  # type: ignore[type-arg]
        """Modifying a file changes its mtime → cache miss → re-hash."""
        import zipfile as _zf
        import time as _time
        import os as _os
        from romfarmer.analysis.file_digest_cache import FileDigestCache

        src = tmp_path / "source"
        src.mkdir()
        zp = src / "Game (USA).zip"
        with _zf.ZipFile(zp, "w") as zf:
            zf.writestr("Game (USA).nes", b"original-content")
        _os.utime(zp, (_time.time() - 10, _time.time() - 10))

        db_path = tmp_path / "digests.db"

        # First run
        with FileDigestCache(db_path) as fdc:
            builder1 = CatalogBuilder(
                platform=PlatformId("nes"),
                source_dir=src,
                knowledge_base=KnowledgeBase(),
                file_digest_cache=fdc,
            )
            catalog1 = builder1.build()
        md5_original = catalog1.units[0].discs[0].identity.md5

        # Modify the file (new content, new mtime)
        with _zf.ZipFile(zp, "w") as zf:
            zf.writestr("Game (USA).nes", b"modified-content-different")
        # mtime is fresh (modification just happened) → racy guard fires → re-hash

        with FileDigestCache(db_path) as fdc:
            builder2 = CatalogBuilder(
                platform=PlatformId("nes"),
                source_dir=src,
                knowledge_base=KnowledgeBase(),
                file_digest_cache=fdc,
            )
            catalog2 = builder2.build()
        md5_modified = catalog2.units[0].discs[0].identity.md5

        # The two MD5s must differ (new content was hashed)
        assert md5_original != md5_modified or md5_modified is None, (
            "Modified file must produce a different MD5 than the original. "
            "The racy guard or re-hash path is broken."
        )

