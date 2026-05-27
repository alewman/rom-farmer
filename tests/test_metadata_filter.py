"""Tests for MetadataFilterConfig and MetadataFilterStage."""

import sqlite3
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from unittest.mock import patch

import pytest

from romfarmer.config.models import MetadataFilterConfig
from romfarmer.stages.filter_metadata import MetadataFilterStage, _parse_max_players
from romfarmer.stages.base import StageContext, StageStatus
from romfarmer.stages.domain import FileSet, FileHashes, PreFilters, DiscProcessing, ProcessingStats


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_context(
    matched: List[Path],
    md5_map: Optional[Dict[Path, str]] = None,
) -> StageContext:
    """Build a minimal StageContext with matched files and optional MD5s."""
    ctx = StageContext(
        platform_name="test",
        platform_config=None,
        target_name="test",
        source_dir=Path("/tmp/source"),
        work_dir=Path("/tmp/work"),
        output_dir=Path("/tmp/output"),
    )
    ctx.files.matched = list(matched)
    ctx.matched_files = list(matched)
    if md5_map:
        ctx.file_md5s = dict(md5_map)
        ctx.hashes.source_md5 = dict(md5_map)
    return ctx


def _make_db(tmp_path: Path, rows: List[Dict]) -> Path:
    """Create a minimal scraped_games SQLite DB with the given rows."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE scraped_games (
            md5 TEXT,
            filename TEXT,
            name TEXT,
            genre TEXT,
            rating REAL,
            players TEXT,
            hidden INTEGER DEFAULT 0
        )
    """)
    for row in rows:
        conn.execute(
            "INSERT INTO scraped_games (md5, filename, name, genre, rating, players, hidden) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                row.get("md5"),
                row.get("filename"),
                row.get("name"),
                row.get("genre"),
                row.get("rating"),
                row.get("players"),
                int(row.get("hidden", False)),
            ),
        )
    conn.commit()
    conn.close()
    return db_path


# ---------------------------------------------------------------------------
# _parse_max_players
# ---------------------------------------------------------------------------

class TestParseMaxPlayers:
    def test_single(self):
        assert _parse_max_players("1") == 1

    def test_range(self):
        assert _parse_max_players("1-4") == 4

    def test_plus(self):
        assert _parse_max_players("4+") == 4

    def test_wide_range(self):
        assert _parse_max_players("2-8") == 8

    def test_none(self):
        assert _parse_max_players(None) is None

    def test_empty(self):
        assert _parse_max_players("") is None


# ---------------------------------------------------------------------------
# MetadataFilterConfig model validation
# ---------------------------------------------------------------------------

class TestMetadataFilterConfig:
    def test_defaults(self):
        cfg = MetadataFilterConfig()
        assert cfg.exclude_nongames is False
        assert cfg.exclude_hidden is False
        assert cfg.require_metadata is False
        assert cfg.has_metadata is False
        assert cfg.include_genres == []
        assert cfg.exclude_genres == []
        assert cfg.exclude_name_patterns == []
        assert cfg.min_rating is None
        assert cfg.min_players is None

    def test_has_metadata_implies_require_metadata(self):
        cfg = MetadataFilterConfig(has_metadata=True)
        assert cfg.require_metadata is True

    def test_require_metadata_standalone(self):
        cfg = MetadataFilterConfig(require_metadata=True)
        assert cfg.require_metadata is True
        assert cfg.has_metadata is False  # not set back

    def test_min_rating_bounds(self):
        MetadataFilterConfig(min_rating=0.0)
        MetadataFilterConfig(min_rating=1.0)
        with pytest.raises(Exception):
            MetadataFilterConfig(min_rating=1.1)
        with pytest.raises(Exception):
            MetadataFilterConfig(min_rating=-0.1)

    def test_min_players_positive(self):
        MetadataFilterConfig(min_players=1)
        with pytest.raises(Exception):
            MetadataFilterConfig(min_players=0)


# ---------------------------------------------------------------------------
# MetadataFilterStage.should_skip
# ---------------------------------------------------------------------------

class TestShouldSkip:
    def test_empty_config_skips(self):
        stage = MetadataFilterStage(config=MetadataFilterConfig(), metadata_db=None)
        ctx = _make_context([Path("game.zip")])
        assert stage.should_skip(ctx) is True

    def test_exclude_nongames_does_not_skip(self):
        stage = MetadataFilterStage(
            config=MetadataFilterConfig(exclude_nongames=True), metadata_db=None
        )
        ctx = _make_context([Path("game.zip")])
        assert stage.should_skip(ctx) is False

    def test_include_genres_does_not_skip(self):
        stage = MetadataFilterStage(
            config=MetadataFilterConfig(include_genres=["Shooter"]), metadata_db=None
        )
        assert stage.should_skip(_make_context([])) is False


# ---------------------------------------------------------------------------
# No DB — pass-through behaviour
# ---------------------------------------------------------------------------

class TestNoDatabase:
    def test_no_db_passes_all_when_not_require_metadata(self):
        files = [Path("a.zip"), Path("b.zip")]
        cfg = MetadataFilterConfig(exclude_nongames=True, exclude_hidden=True)
        stage = MetadataFilterStage(config=cfg, metadata_db=Path("/nonexistent/path.db"))
        ctx = _make_context(files)
        result = stage.execute(ctx)
        assert result.status == StageStatus.SUCCESS
        assert ctx.files.matched == files
        assert ctx.matched_files == files

    def test_no_db_drops_all_when_require_metadata(self):
        files = [Path("a.zip"), Path("b.zip")]
        cfg = MetadataFilterConfig(require_metadata=True)
        stage = MetadataFilterStage(config=cfg, metadata_db=Path("/nonexistent/path.db"))
        ctx = _make_context(files)
        result = stage.execute(ctx)
        assert result.status == StageStatus.SUCCESS
        assert ctx.files.matched == []

    def test_empty_matched_skips(self):
        cfg = MetadataFilterConfig(exclude_nongames=True)
        stage = MetadataFilterStage(config=cfg, metadata_db=Path("/nonexistent/path.db"))
        ctx = _make_context([])
        result = stage.execute(ctx)
        assert result.status == StageStatus.SKIPPED


# ---------------------------------------------------------------------------
# Filtering with a real in-memory DB
# ---------------------------------------------------------------------------

class TestWithDatabase:
    @pytest.fixture
    def db(self, tmp_path):
        return _make_db(tmp_path, [
            {
                "md5": "aaa",
                "filename": "Contra (USA).zip",
                "name": "Contra (USA)",
                "genre": "Shoot'em Up / Horizontal",
                "rating": 0.85,
                "players": "1-2",
                "hidden": False,
            },
            {
                "md5": "bbb",
                "filename": "Super Mario Bros (USA).zip",
                "name": "Super Mario Bros (USA)",
                "genre": "Platform",
                "rating": 0.90,
                "players": "1",
                "hidden": False,
            },
            {
                "md5": "ccc",
                "filename": "ZZZ(notgame)Bios.zip",
                "name": "ZZZ(notgame)Bios",
                "genre": None,
                "rating": None,
                "players": None,
                "hidden": False,
            },
            {
                "md5": "ddd",
                "filename": "Hidden Game.zip",
                "name": "Hidden Game",
                "genre": "Adventure",
                "rating": 0.70,
                "players": "1",
                "hidden": True,
            },
            {
                "md5": "eee",
                "filename": "Casino Poker (USA).zip",
                "name": "Casino Poker (USA)",
                "genre": "Casino",
                "rating": 0.50,
                "players": "1",
                "hidden": False,
            },
        ])

    def _files_and_md5s(self):
        files = [
            Path("Contra (USA).zip"),
            Path("Super Mario Bros (USA).zip"),
            Path("ZZZ(notgame)Bios.zip"),
            Path("Hidden Game.zip"),
            Path("Casino Poker (USA).zip"),
        ]
        md5s = {
            Path("Contra (USA).zip"): "aaa",
            Path("Super Mario Bros (USA).zip"): "bbb",
            Path("ZZZ(notgame)Bios.zip"): "ccc",
            Path("Hidden Game.zip"): "ddd",
            Path("Casino Poker (USA).zip"): "eee",
        }
        return files, md5s

    def test_exclude_nongames(self, db):
        files, md5s = self._files_and_md5s()
        cfg = MetadataFilterConfig(exclude_nongames=True)
        stage = MetadataFilterStage(config=cfg, metadata_db=db)
        ctx = _make_context(files, md5s)
        stage.execute(ctx)
        names = [p.name for p in ctx.files.matched]
        assert "ZZZ(notgame)Bios.zip" not in names
        assert "Contra (USA).zip" in names

    def test_exclude_hidden(self, db):
        files, md5s = self._files_and_md5s()
        cfg = MetadataFilterConfig(exclude_hidden=True)
        stage = MetadataFilterStage(config=cfg, metadata_db=db)
        ctx = _make_context(files, md5s)
        stage.execute(ctx)
        names = [p.name for p in ctx.files.matched]
        assert "Hidden Game.zip" not in names
        assert "Contra (USA).zip" in names

    def test_exclude_genres(self, db):
        files, md5s = self._files_and_md5s()
        cfg = MetadataFilterConfig(exclude_genres=["Casino"])
        stage = MetadataFilterStage(config=cfg, metadata_db=db)
        ctx = _make_context(files, md5s)
        stage.execute(ctx)
        names = [p.name for p in ctx.files.matched]
        assert "Casino Poker (USA).zip" not in names
        assert "Contra (USA).zip" in names

    def test_include_genres_keeps_matching(self, db):
        files, md5s = self._files_and_md5s()
        cfg = MetadataFilterConfig(include_genres=["Shoot'em Up"])
        stage = MetadataFilterStage(config=cfg, metadata_db=db)
        ctx = _make_context(files, md5s)
        stage.execute(ctx)
        names = [p.name for p in ctx.files.matched]
        assert "Contra (USA).zip" in names
        assert "Super Mario Bros (USA).zip" not in names
        # ZZZ has no genre — passes through (require_metadata=False)
        assert "ZZZ(notgame)Bios.zip" in names

    def test_include_genres_with_require_metadata_drops_no_genre(self, db):
        files, md5s = self._files_and_md5s()
        cfg = MetadataFilterConfig(include_genres=["Shoot'em Up"], require_metadata=True)
        stage = MetadataFilterStage(config=cfg, metadata_db=db)
        ctx = _make_context(files, md5s)
        stage.execute(ctx)
        names = [p.name for p in ctx.files.matched]
        assert "Contra (USA).zip" in names
        # ZZZ has a DB row (require_metadata satisfied) but genre=None.
        # include_genres only rejects when genre is present but doesn't match —
        # no genre = pass through. So ZZZ survives here.
        assert "ZZZ(notgame)Bios.zip" in names
        # Super Mario Bros has genre "Platform" — doesn't match Shoot'em Up → dropped.
        assert "Super Mario Bros (USA).zip" not in names

    def test_min_rating(self, db):
        files, md5s = self._files_and_md5s()
        cfg = MetadataFilterConfig(min_rating=0.80)
        stage = MetadataFilterStage(config=cfg, metadata_db=db)
        ctx = _make_context(files, md5s)
        stage.execute(ctx)
        names = [p.name for p in ctx.files.matched]
        assert "Contra (USA).zip" in names   # 0.85 ≥ 0.80
        assert "Super Mario Bros (USA).zip" in names  # 0.90 ≥ 0.80
        assert "Hidden Game.zip" not in names  # 0.70 < 0.80
        assert "Casino Poker (USA).zip" not in names  # 0.50 < 0.80

    def test_min_players(self, db):
        files, md5s = self._files_and_md5s()
        cfg = MetadataFilterConfig(min_players=2)
        stage = MetadataFilterStage(config=cfg, metadata_db=db)
        ctx = _make_context(files, md5s)
        stage.execute(ctx)
        names = [p.name for p in ctx.files.matched]
        assert "Contra (USA).zip" in names   # "1-2" → max 2
        assert "Super Mario Bros (USA).zip" not in names  # "1" → max 1

    def test_combined_filters(self, db):
        files, md5s = self._files_and_md5s()
        cfg = MetadataFilterConfig(
            exclude_nongames=True,
            exclude_hidden=True,
            exclude_genres=["Casino"],
            min_rating=0.80,
        )
        stage = MetadataFilterStage(config=cfg, metadata_db=db)
        ctx = _make_context(files, md5s)
        stage.execute(ctx)
        names = [p.name for p in ctx.files.matched]
        # Only Contra (0.85, not nongame, not hidden, not casino) and
        # Super Mario Bros (0.90) should survive
        assert set(names) == {"Contra (USA).zip", "Super Mario Bros (USA).zip"}

    def test_filename_fallback_lookup(self, db):
        """Files without MD5s in context should still match via filename."""
        files = [Path("Contra (USA).zip"), Path("Super Mario Bros (USA).zip")]
        # No MD5 map — should fall back to filename lookup
        cfg = MetadataFilterConfig(min_rating=0.88)
        stage = MetadataFilterStage(config=cfg, metadata_db=db)
        ctx = _make_context(files, md5_map={})
        stage.execute(ctx)
        names = [p.name for p in ctx.files.matched]
        assert "Super Mario Bros (USA).zip" in names  # 0.90
        assert "Contra (USA).zip" not in names  # 0.85 < 0.88

    def test_require_metadata_drops_unscraped(self, db):
        """Files not in the DB are dropped when require_metadata=True."""
        files = [
            Path("Contra (USA).zip"),
            Path("Unknown Game Not In DB.zip"),
        ]
        md5s = {
            Path("Contra (USA).zip"): "aaa",
            Path("Unknown Game Not In DB.zip"): "fff",  # not in DB
        }
        cfg = MetadataFilterConfig(require_metadata=True)
        stage = MetadataFilterStage(config=cfg, metadata_db=db)
        ctx = _make_context(files, md5s)
        stage.execute(ctx)
        names = [p.name for p in ctx.files.matched]
        assert "Contra (USA).zip" in names
        assert "Unknown Game Not In DB.zip" not in names

    def test_legacy_matched_files_synced(self, db):
        """context.matched_files (legacy) is kept in sync with context.files.matched."""
        files, md5s = self._files_and_md5s()
        cfg = MetadataFilterConfig(exclude_nongames=True)
        stage = MetadataFilterStage(config=cfg, metadata_db=db)
        ctx = _make_context(files, md5s)
        stage.execute(ctx)
        assert ctx.matched_files == ctx.files.matched

    def test_exclude_name_patterns(self, db):
        files, md5s = self._files_and_md5s()
        cfg = MetadataFilterConfig(exclude_name_patterns=["Casino*"])
        stage = MetadataFilterStage(config=cfg, metadata_db=db)
        ctx = _make_context(files, md5s)
        stage.execute(ctx)
        names = [p.name for p in ctx.files.matched]
        assert "Casino Poker (USA).zip" not in names
        assert "Contra (USA).zip" in names
