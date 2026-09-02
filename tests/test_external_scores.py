"""Tests for external_scores module (MobyGames fetcher + title normalization)."""

import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from romfarmer.metadata.external_scores import (
    MOBYGAMES_PLATFORM_IDS,
    MobyGamesFetcher,
    normalize_title,
)
from romfarmer.metadata.database import ExternalScore, MetadataDatabase


# ---------------------------------------------------------------------------
# normalize_title
# ---------------------------------------------------------------------------


class TestNormalizeTitle:
    def test_strips_region_code(self):
        assert normalize_title("Resident Evil 4 (USA)") == "resident evil 4"

    def test_strips_multiple_parens(self):
        assert (
            normalize_title("Gran Turismo 3 (Europe) (En,Fr,De)")
            == "gran turismo 3"
        )

    def test_strips_revision(self):
        assert normalize_title("Castlevania (USA) (v1.1)") == "castlevania"

    def test_normalizes_colon_subtitle(self):
        result = normalize_title("The Legend of Zelda: Ocarina of Time")
        assert result == "legend of zelda ocarina of time"

    def test_normalizes_dash_subtitle(self):
        result = normalize_title("Castlevania - Symphony of the Night")
        assert result == "castlevania symphony of the night"

    def test_strips_leading_the(self):
        assert normalize_title("The Simpsons Game") == "simpsons game"

    def test_strips_leading_a(self):
        assert normalize_title("A Bug's Life") == "bugs life"

    def test_strips_disc_suffix(self):
        result = normalize_title("Final Fantasy VII - Disc 2 (USA)")
        assert "disc" not in result
        assert "final fantasy vii" in result

    def test_lowercases(self):
        assert normalize_title("DOOM") == "doom"

    def test_strips_punctuation(self):
        # Apostrophes stripped, hyphens normalized
        result = normalize_title("Crash Bandicoot: Warped")
        assert result == "crash bandicoot warped"

    def test_collapses_whitespace(self):
        result = normalize_title("  Metal   Gear  Solid  ")
        assert result == "metal gear solid"

    def test_empty_string(self):
        assert normalize_title("") == ""

    def test_real_world_ps2_title(self):
        """ROM filename vs MobyGames title round-trip."""
        rom_name = "Gran Turismo 3 - A-spec (Europe) (En,Fr,De,Es,It)"
        mobygames_name = "Gran Turismo 3: A-spec"
        assert normalize_title(rom_name) == normalize_title(mobygames_name)


# ---------------------------------------------------------------------------
# Platform ID mapping coverage
# ---------------------------------------------------------------------------


class TestPlatformIdMapping:
    def test_all_values_are_positive_ints(self):
        for platform, pid in MOBYGAMES_PLATFORM_IDS.items():
            assert isinstance(pid, int) and pid > 0, f"{platform} has invalid id {pid}"

    def test_core_platforms_present(self):
        required = ["ps2", "ps3", "psx", "xbox", "xbox360", "gamecube", "wii",
                    "snes", "nes", "gba", "nds", "dreamcast", "saturn", "megadrive"]
        for p in required:
            assert p in MOBYGAMES_PLATFORM_IDS, f"'{p}' missing from MOBYGAMES_PLATFORM_IDS"


# ---------------------------------------------------------------------------
# MobyGamesFetcher (mocked API)
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_db(tmp_path: Path) -> MetadataDatabase:
    """Ephemeral in-memory-equivalent DB for tests."""
    return MetadataDatabase(tmp_path / "test.db")


@pytest.fixture
def fetcher(tmp_db: MetadataDatabase) -> MobyGamesFetcher:
    return MobyGamesFetcher(db=tmp_db, api_key="test-key", rate_limit_seconds=0.0)


MOCK_GAMES_PAGE_1 = {
    "games": [
        {
            "game_id": 1001,
            "title": "Resident Evil 4",
            "moby_score": 8.9,
            "moby_url": "https://www.mobygames.com/game/1001/",
        },
        {
            "game_id": 1002,
            "title": "Shadow of the Colossus",
            "moby_score": 9.1,
            "moby_url": "https://www.mobygames.com/game/1002/",
        },
        {
            "game_id": 1003,
            "title": "Obscure Unrated Game",
            "moby_score": None,  # Should be skipped
        },
    ]
}

MOCK_GAMES_PAGE_2: dict = {"games": []}  # Empty = last page


class TestMobyGamesFetcherInit:
    def test_requires_api_key(self, tmp_db: MetadataDatabase, monkeypatch):
        # core.paths loads .env at import, which may populate this var
        monkeypatch.delenv("MOBYGAMES_API_KEY", raising=False)
        with pytest.raises(ValueError, match="API key required"):
            MobyGamesFetcher(db=tmp_db, api_key="")

    def test_reads_env_var(self, tmp_db: MetadataDatabase, monkeypatch):
        monkeypatch.setenv("MOBYGAMES_API_KEY", "env-key")
        f = MobyGamesFetcher(db=tmp_db)
        assert f.api_key == "env-key"


class TestFetchPlatform:
    def test_unknown_platform_raises(self, fetcher: MobyGamesFetcher):
        with pytest.raises(ValueError, match="No MobyGames platform ID"):
            fetcher.fetch_platform("nonexistent_platform")

    def test_fetch_stores_scored_games(self, fetcher: MobyGamesFetcher):
        pages = [MOCK_GAMES_PAGE_1, MOCK_GAMES_PAGE_2]
        with patch.object(fetcher, "_get", side_effect=pages):
            count = fetcher.fetch_platform("ps2")

        assert count == 2  # 3 entries, 1 without score skipped

    def test_fetch_skips_unscored(self, fetcher: MobyGamesFetcher):
        pages = [MOCK_GAMES_PAGE_1, MOCK_GAMES_PAGE_2]
        with patch.object(fetcher, "_get", side_effect=pages):
            fetcher.fetch_platform("ps2")

        scores = fetcher.db.get_external_scores_for_platform("ps2")
        titles = [s.title for s in scores]
        assert "Obscure Unrated Game" not in titles

    def test_fetch_normalizes_titles(self, fetcher: MobyGamesFetcher):
        pages = [MOCK_GAMES_PAGE_1, MOCK_GAMES_PAGE_2]
        with patch.object(fetcher, "_get", side_effect=pages):
            fetcher.fetch_platform("ps2")

        scores = fetcher.db.get_external_scores_for_platform("ps2")
        re4 = next(s for s in scores if s.title == "Resident Evil 4")
        assert re4.normalized_title == "resident evil 4"

    def test_fetch_upserts_on_refetch(self, fetcher: MobyGamesFetcher):
        """Re-fetching the same platform updates existing records."""
        pages_first = [MOCK_GAMES_PAGE_1, MOCK_GAMES_PAGE_2]
        with patch.object(fetcher, "_get", side_effect=pages_first):
            fetcher.fetch_platform("ps2")

        # Second fetch with updated score
        updated_page = {
            "games": [
                {
                    "game_id": 1001,
                    "title": "Resident Evil 4",
                    "moby_score": 9.2,  # score changed
                    "moby_url": "https://www.mobygames.com/game/1001/",
                }
            ]
        }
        pages_second = [updated_page, MOCK_GAMES_PAGE_2]
        with patch.object(fetcher, "_get", side_effect=pages_second):
            fetcher.fetch_platform("ps2")

        scores = fetcher.db.get_external_scores_for_platform("ps2")
        re4 = next(s for s in scores if s.source_id == "1001")
        assert re4.user_score == pytest.approx(9.2)

    def test_progress_callback_called(self, fetcher: MobyGamesFetcher):
        pages = [MOCK_GAMES_PAGE_1, MOCK_GAMES_PAGE_2]
        calls = []
        with patch.object(fetcher, "_get", side_effect=pages):
            fetcher.fetch_platform(
                "ps2",
                progress_callback=lambda fetched, stored, page: calls.append(page),
            )
        assert len(calls) > 0

    def test_rate_limit_429_raises_helpful_error(self, fetcher: MobyGamesFetcher):
        import requests as req_lib

        mock_response = MagicMock()
        mock_response.status_code = 429
        http_err = req_lib.HTTPError(response=mock_response)

        with patch.object(fetcher, "_get", side_effect=http_err):
            with pytest.raises(req_lib.HTTPError):
                fetcher.fetch_platform("ps2")


# ---------------------------------------------------------------------------
# DB query helpers
# ---------------------------------------------------------------------------


class TestExternalScoreDB:
    def _make_score(self, platform="ps2", title="Test Game", score=8.0, source_id="42") -> ExternalScore:
        return ExternalScore(
            platform=platform,
            title=title,
            normalized_title=normalize_title(title),
            user_score=score,
            critic_score=None,
            source="mobygames",
            source_id=source_id,
            fetched_at=datetime.utcnow(),
        )

    def test_upsert_and_retrieve(self, tmp_db: MetadataDatabase):
        score = self._make_score()
        tmp_db.upsert_external_score(score)
        results = tmp_db.get_external_scores_for_platform("ps2")
        assert len(results) == 1
        assert results[0].title == "Test Game"

    def test_upsert_updates_score(self, tmp_db: MetadataDatabase):
        tmp_db.upsert_external_score(self._make_score(score=7.0))
        tmp_db.upsert_external_score(self._make_score(score=8.5))  # same source_id
        results = tmp_db.get_external_scores_for_platform("ps2")
        assert len(results) == 1
        assert results[0].user_score == pytest.approx(8.5)

    def test_lookup_exact_match(self, tmp_db: MetadataDatabase):
        tmp_db.upsert_external_score(self._make_score(title="Resident Evil 4"))
        result = tmp_db.lookup_external_score("ps2", "resident evil 4")
        assert result is not None
        assert result.title == "Resident Evil 4"

    def test_lookup_normalized_rom_filename(self, tmp_db: MetadataDatabase):
        """ROM filename 'Resident Evil 4 (USA)' should match 'Resident Evil 4'."""
        from romfarmer.metadata.external_scores import normalize_title

        tmp_db.upsert_external_score(self._make_score(title="Resident Evil 4"))
        normalized = normalize_title("Resident Evil 4 (USA)")
        result = tmp_db.lookup_external_score("ps2", normalized)
        assert result is not None

    def test_lookup_no_match_returns_none(self, tmp_db: MetadataDatabase):
        result = tmp_db.lookup_external_score("ps2", "completely unknown game")
        assert result is None

    def test_get_stats(self, tmp_db: MetadataDatabase):
        tmp_db.upsert_external_score(self._make_score(source_id="1"))
        tmp_db.upsert_external_score(self._make_score(source_id="2", score=7.5))
        stats = tmp_db.get_external_scores_stats()
        assert len(stats) == 1
        assert stats[0]["platform"] == "ps2"
        assert stats[0]["count"] == 2

    def test_best_score_normalized_user_only(self, tmp_db: MetadataDatabase):
        score = self._make_score(score=8.0)
        assert score.best_score_normalized == pytest.approx(0.8)

    def test_best_score_normalized_prefers_critic(self):
        score = ExternalScore(
            platform="ps2", title="Game", normalized_title="game",
            user_score=7.0, critic_score=90,
            source="rawg", source_id="x", fetched_at=datetime.utcnow(),
        )
        assert score.best_score_normalized == pytest.approx(0.9)

    def test_filter_by_min_user_score(self, tmp_db: MetadataDatabase):
        tmp_db.upsert_external_score(self._make_score(score=5.0, source_id="1"))
        tmp_db.upsert_external_score(self._make_score(score=8.5, source_id="2"))
        results = tmp_db.get_external_scores_for_platform("ps2", min_user_score=7.0)
        assert len(results) == 1
        assert results[0].user_score == pytest.approx(8.5)
