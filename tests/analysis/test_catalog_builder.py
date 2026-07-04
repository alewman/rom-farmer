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
