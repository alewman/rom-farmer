"""
External game score fetcher — MobyGames and RAWG APIs.

Fetches professional critic scores and community ratings to supplement
ScreenScraper ratings, which have sparse coverage on many platforms.

Sources
-------
MobyGames (https://www.mobygames.com/info/api/)
    - moby_score: community-voted score (0-10)
    - Excellent retro platform coverage (Saturn, PC Engine, Atari, etc.)
    - API key required (free tier: 360 req/day)
    - Environment variable: MOBYGAMES_API_KEY

RAWG (https://rawg.io/apidocs)  [placeholder, not yet implemented]
    - metacritic field: actual Metacritic Metascore (0-100)
    - Best for modern platforms (PS2-PS5, Xbox, Switch)
    - API key required (free tier: 20k req/month)
    - Environment variable: RAWG_API_KEY

Usage
-----
    from romfarmer.metadata.external_scores import MobyGamesFetcher
    from romfarmer.metadata.database import MetadataDatabase
    from pathlib import Path

    db = MetadataDatabase(Path("metadata/database/romfarmer.db"))
    fetcher = MobyGamesFetcher(api_key="your-key", db=db)
    count = fetcher.fetch_platform("ps2")
    print(f"Stored {count} PS2 scores")
"""

import json
import logging
import os
import re
import time
from datetime import datetime

import requests

from .database import ExternalScore, MetadataDatabase

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Title normalization
# ---------------------------------------------------------------------------


def normalize_title(title: str) -> str:
    """
    Normalize a game title for fuzzy matching against ROM filenames.

    ROM filenames carry region/revision noise:
        "Castlevania - Symphony of the Night (USA) (v1.1)"
    MobyGames stores:
        "Castlevania: Symphony of the Night"

    This function strips that noise to a bare lowercase token string
    that can be compared across sources.

    Examples
    --------
    >>> normalize_title("Resident Evil 4 (USA)")
    'resident evil 4'
    >>> normalize_title("The Legend of Zelda: Ocarina of Time")
    'legend of zelda ocarina of time'
    >>> normalize_title("Gran Turismo 3 - A-spec (Europe) (En,Fr,De,Es,It)")
    'gran turismo 3 aspec'
    >>> normalize_title("Addams Family, The (USA)")
    'addams family'
    """
    t = title

    # Strip trailing parenthetical content (region, revision, language, etc.)
    t = re.sub(r"\s*\([^)]*\)", "", t)

    # Strip disc/part suffixes used in multi-disc titles
    t = re.sub(r"\s*[-:]\s*(Disc|CD|Part|Vol\.?)\s*\d+.*$", "", t, flags=re.IGNORECASE)

    # No-Intro/Redump trailing-article convention ("Legend of Zelda, The")
    # must be dropped before the comma is stripped, or "the" would merge
    # into the title instead of being removed like a leading article.
    t = re.sub(r",\s*(the|a|an)\s*$", "", t, flags=re.IGNORECASE)

    # Normalize subtitle separators (colon, dash) to a single space
    t = re.sub(r"\s*[:\-]\s*", " ", t)

    # Lowercase
    t = t.lower()

    # Strip punctuation except word characters and spaces
    t = re.sub(r"[^\w\s]", "", t)

    # Collapse whitespace
    t = re.sub(r"\s+", " ", t).strip()

    # Strip leading articles (for stable sorting/matching)
    t = re.sub(r"^(the|a|an)\s+", "", t)

    return t


# ---------------------------------------------------------------------------
# Platform ID mappings
# ---------------------------------------------------------------------------

# Maps rom-farmer platform names → MobyGames platform IDs.
# Verify IDs at: https://www.mobygames.com/game/platform/
# To add a platform, find its ID from the MobyGames URL when browsing by platform.
MOBYGAMES_PLATFORM_IDS: dict[str, int] = {
    # Sony
    "psx": 6,  # PlayStation
    "ps2": 7,  # PlayStation 2
    "ps3": 81,  # PlayStation 3
    "psp": 46,  # PlayStation Portable
    "pspminis": 46,  # PSP Minis share the PSP platform
    # Microsoft
    "xbox": 13,  # Xbox
    "xbox360": 69,  # Xbox 360
    # Nintendo home
    "gamecube": 14,  # GameCube
    "wii": 82,  # Wii
    "wiiu": 132,  # Wii U
    "n64": 9,  # Nintendo 64
    "snes": 15,  # Super NES
    "nes": 22,  # NES
    "fds": 22,  # Famicom Disk System (same platform page on MobyGames)
    # Nintendo handheld
    "gb": 10,  # Game Boy
    "gbc": 11,  # Game Boy Color
    "gba": 12,  # Game Boy Advance
    "nds": 44,  # Nintendo DS
    "3ds": 101,  # Nintendo 3DS
    # Sega home
    "dreamcast": 8,  # Dreamcast
    "saturn": 23,  # Saturn
    "megadrive": 16,  # Genesis / Mega Drive
    "megacd": 20,  # Sega CD / Mega-CD
    "sega32x": 21,  # 32X
    "mastersystem": 26,  # Master System
    # Sega handheld
    "gamegear": 25,  # Game Gear
    # NEC
    "pcengine": 40,  # PC Engine / TurboGrafx-16
    # SNK
    "neogeo": 36,  # Neo Geo
    # Atari
    "atari2600": 28,  # Atari 2600
    "atari5200": 33,  # Atari 5200
    "atari7800": 34,  # Atari 7800
    "atarijaguar": 17,  # Atari Jaguar
    "atarilynx": 18,  # Atari Lynx
    # Other home
    "3do": 35,  # 3DO
    "colecovision": 29,  # ColecoVision
    "intellivision": 30,  # Intellivision
    "virtualboy": 38,  # Virtual Boy (37 is Vectrex - do not confuse)
    # Handheld misc
    "wswan": 48,  # WonderSwan
    "wswanc": 49,  # WonderSwan Color
    # MSX (same ID for both revisions on MobyGames)
    "msx1": 57,
    "msx2": 57,
    # Computers / added 2026-08-20 for Myrient-sourced platforms not yet built
    "dos": 2,  # DOS
    "c64": 27,  # Commodore 64
    "amiga": 19,  # Amiga
    "amigacd32": 56,  # Amiga CD32
    "atarist": 24,  # Atari ST
    "atari800": 39,  # Atari 8-bit Family
    "apple2": 31,  # Apple II
    "apple2gs": 51,  # Apple IIgs
    "zxspectrum": 41,  # ZX Spectrum
    "cpc": 60,  # Amstrad CPC
    "pc88": 94,  # NEC PC-88
    "pc98": 95,  # NEC PC-98
    "pcfx": 59,  # NEC PC-FX
    "x68000": 106,  # Sharp X68000
    "fmtowns": 102,  # Fujitsu FM Towns
    "vectrex": 37,  # GCE Vectrex
    "odyssey2": 78,  # Magnavox Odyssey 2
    "channelf": 76,  # Fairchild Channel F
    "gamecom": 50,  # Tiger Game.com
    "ngage": 32,  # Nokia N-Gage
    "neogeocd": 54,  # SNK Neo Geo CD
    "cdi": 73,  # Philips CD-i
}

# Maps rom-farmer platform names → RAWG platform IDs.
# RAWG's 'metacritic' field is the actual Metacritic Metascore.
RAWG_PLATFORM_IDS: dict[str, int] = {
    "psx": 27,  # PlayStation
    "ps2": 15,  # PlayStation 2
    "ps3": 16,  # PlayStation 3
    "psp": 19,  # PSP
    "xbox": 80,  # Xbox
    "xbox360": 14,  # Xbox 360
    "gamecube": 105,  # GameCube
    "wii": 11,  # Wii
    "wiiu": 10,  # Wii U
    "n64": 83,  # Nintendo 64
    "snes": 79,  # SNES
    "nes": 18,  # NES
    "gba": 24,  # GBA
    "nds": 77,  # DS
    "3ds": 8,  # 3DS
    "dreamcast": 106,  # Dreamcast
    "megadrive": 167,  # Genesis
}


# ---------------------------------------------------------------------------
# MobyGames fetcher
# ---------------------------------------------------------------------------


class MobyGamesFetcher:
    """
    Fetches game scores from the MobyGames API v1 and persists them to the DB.

    Rate limit
    ----------
    The MobyGames Hobbyist tier ($9.99/mo) allows 1 request/second.
    The default ``rate_limit_seconds`` of 1.0 uses that full allowance.
    Free tier users should set this to 10.0 (360 req/day budget).

    Parameters
    ----------
    api_key:
        MobyGames API key.  If not provided, the ``MOBYGAMES_API_KEY``
        environment variable is used.
    db:
        Initialized MetadataDatabase instance.
    rate_limit_seconds:
        Minimum seconds between API requests (default 1.0 for Hobbyist tier).
    """

    BASE_URL = "https://api.mobygames.com/v1"

    def __init__(
        self,
        db: MetadataDatabase,
        api_key: str | None = None,
        rate_limit_seconds: float = 1.1,
    ):
        self.api_key = api_key or os.environ.get("MOBYGAMES_API_KEY", "")
        if not self.api_key:
            raise ValueError("MobyGames API key required. Pass api_key= or set MOBYGAMES_API_KEY.")
        self.db = db
        self.rate_limit = rate_limit_seconds
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})
        self._last_request_time: float = 0.0
        self._request_count: int = 0

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def fetch_platform(
        self,
        platform: str,
        progress_callback=None,
        resume: bool = True,
    ) -> int:
        """
        Fetch all scored games for one rom-farmer platform and persist them.

        Parameters
        ----------
        platform:
            rom-farmer platform name (e.g. "ps2", "snes").
        progress_callback:
            Optional callable(fetched: int, stored: int, page: int) for UI updates.
        resume:
            If True (default), skip platforms already fetched today.

        Returns
        -------
        int
            Number of new/updated score records stored.
        """
        platform_id = MOBYGAMES_PLATFORM_IDS.get(platform)
        if platform_id is None:
            raise ValueError(
                f"No MobyGames platform ID for '{platform}'. "
                f"Add it to MOBYGAMES_PLATFORM_IDS in external_scores.py."
            )

        logger.info("Fetching MobyGames scores for platform '%s' (id=%d)", platform, platform_id)

        stored = 0
        offset = 0
        page_size = 100
        page = 0

        while True:
            data = self._get(
                "games",
                {
                    "platform": platform_id,
                    "format": "normal",
                    "limit": page_size,
                    "offset": offset,
                },
            )

            games = data.get("games", [])
            if not games:
                break

            for game in games:
                moby_score = game.get("moby_score")
                if moby_score is None:
                    continue  # Skip games with no community score

                title = game.get("title", "")
                genres = game.get("genres") or []
                cover = game.get("sample_cover") or {}
                screenshots = game.get("sample_screenshots") or []
                release_date = None
                for p in game.get("platforms") or []:
                    if p.get("platform_id") == platform_id:
                        release_date = p.get("first_release_date")
                        break
                score = ExternalScore(
                    platform=platform,
                    title=title,
                    normalized_title=normalize_title(title),
                    critic_score=None,  # MobyGames list endpoint doesn't include critic aggregate
                    user_score=float(moby_score),
                    vote_count=game.get("num_votes"),
                    source="mobygames",
                    source_id=str(game.get("game_id", "")),
                    url=game.get("moby_url"),
                    description=game.get("description"),
                    genres=", ".join(g["genre_name"] for g in genres) or None,
                    release_date=release_date,
                    official_url=game.get("official_url"),
                    cover_url=cover.get("image"),
                    screenshot_urls=json.dumps([s["image"] for s in screenshots])
                    if screenshots
                    else None,
                    fetched_at=datetime.utcnow(),
                )
                self.db.upsert_external_score(score)
                stored += 1

            page += 1
            offset += len(games)

            if progress_callback:
                progress_callback(offset, stored, page)

            logger.debug(
                "  page %d: fetched %d games total, %d scored, offset=%d",
                page,
                offset,
                stored,
                offset,
            )

            if len(games) < page_size:
                break  # Last page

        logger.info("Stored %d scored games for platform '%s'", stored, platform)
        return stored

    def fetch_all_platforms(
        self,
        platforms: list[str] | None = None,
        progress_callback=None,
    ) -> dict[str, int]:
        """
        Fetch scores for multiple platforms sequentially.

        Parameters
        ----------
        platforms:
            List of rom-farmer platform names to fetch.  Defaults to all
            platforms in MOBYGAMES_PLATFORM_IDS.
        progress_callback:
            Optional callable(platform: str, fetched: int, stored: int).

        Returns
        -------
        dict mapping platform name → stored count.
        """
        target_platforms = platforms or list(MOBYGAMES_PLATFORM_IDS.keys())
        # Deduplicate while preserving order (e.g. msx1/msx2 share same ID)
        seen_ids: set[int] = set()
        deduped: list[str] = []
        for p in target_platforms:
            pid = MOBYGAMES_PLATFORM_IDS.get(p)
            if pid is not None and pid not in seen_ids:
                seen_ids.add(pid)
                deduped.append(p)

        results: dict[str, int] = {}
        for platform in deduped:
            try:
                count = self.fetch_platform(platform, progress_callback=progress_callback)
                results[platform] = count
            except Exception as exc:
                logger.error("Error fetching platform '%s': %s", platform, exc)
                results[platform] = -1

        return results

    def lookup_game(self, title: str, platform: str) -> dict | None:
        """
        Search MobyGames for a single game by title and platform.

        Useful for spot-checks or filling gaps. Returns the first result
        dict from the API, or None if not found.
        """
        platform_id = MOBYGAMES_PLATFORM_IDS.get(platform)
        data = self._get(
            "games",
            {
                "title": title,
                "platform": platform_id,
                "format": "normal",
                "limit": 5,
            },
        )
        games = data.get("games", [])
        return games[0] if games else None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _seconds_until_next_utc_hour() -> float:
        """Return seconds until the next UTC :00:00 boundary."""
        import datetime as _dt

        now = _dt.datetime.utcnow()
        next_hour = now.replace(minute=0, second=0, microsecond=0) + _dt.timedelta(hours=1)
        return max((next_hour - now).total_seconds(), 1.0)

    def _get(self, endpoint: str, params: dict, _retry: int = 0) -> dict:
        """Make a rate-limited, authenticated GET request with 429 backoff.

        Retry strategy:
          Retries 0-2: short exponential backoff (5s, 10s, 20s) — handles burst limiting.
          Retry 3+:    wait until the next UTC :00 boundary + 5s buffer, then retry.
                       This survives the ~47-minute hourly quota dead window.
          _MAX_RETRIES: give up after this many retries (covers multiple dead windows).
        """
        _MAX_RETRIES = 12
        _SHORT_RETRIES = 3  # below this index, use short exponential backoff

        # Enforce minimum gap between requests
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)

        call_params = dict(params)  # copy so we never mutate caller's dict
        call_params["api_key"] = self.api_key

        url = f"{self.BASE_URL}/{endpoint}"
        try:
            resp = self._session.get(url, params=call_params, timeout=60)
            resp.raise_for_status()
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 429:
                if _retry >= _MAX_RETRIES:
                    raise RuntimeError(
                        f"MobyGames API rate limit exceeded (429) after "
                        f"{_MAX_RETRIES} retries on {endpoint}. "
                        f"Consider --rate-limit 5.0 to stay within 720 req/hour."
                    ) from exc
                if _retry < _SHORT_RETRIES:
                    backoff = 5.0 * (2**_retry)  # 5s, 10s, 20s
                    logger.warning(
                        "429 burst limit hit — backing off %.0fs (retry %d/%d)",
                        backoff,
                        _retry + 1,
                        _MAX_RETRIES,
                    )
                else:
                    # Likely hourly quota exhausted — wait until next UTC :00
                    wait = self._seconds_until_next_utc_hour() + 5.0
                    logger.warning(
                        "429 hourly quota exhausted — waiting %.0fs for UTC :00 reset "
                        "(retry %d/%d, ~%.0f min)",
                        wait,
                        _retry + 1,
                        _MAX_RETRIES,
                        wait / 60,
                    )
                    backoff = wait
                time.sleep(backoff)
                self._last_request_time = time.monotonic()
                return self._get(endpoint, params, _retry + 1)
            raise
        finally:
            self._last_request_time = time.monotonic()
            self._request_count += 1

        return resp.json()


# ---------------------------------------------------------------------------
# RAWG fetcher (Metacritic scores)
# ---------------------------------------------------------------------------


class RawgFetcher:
    """
    Fetches Metacritic scores via the RAWG API.

    RAWG's ``metacritic`` field is the actual Metacritic Metascore (0-100).
    It provides the best coverage for PS2-PS5, Xbox, Switch, and other
    modern platforms.

    Status: placeholder — not yet implemented.
    Register at https://rawg.io/apidocs for a free API key (20k req/month).
    Set environment variable: RAWG_API_KEY
    """

    BASE_URL = "https://api.rawg.io/api"

    def __init__(
        self,
        db: MetadataDatabase,
        api_key: str | None = None,
        rate_limit_seconds: float = 1.0,
    ):
        self.api_key = api_key or os.environ.get("RAWG_API_KEY", "")
        if not self.api_key:
            raise ValueError("RAWG API key required. Pass api_key= or set RAWG_API_KEY.")
        self.db = db
        self.rate_limit = rate_limit_seconds
        self._session = requests.Session()
        self._last_request_time: float = 0.0

    def fetch_platform(self, platform: str) -> int:
        """Fetch Metacritic scores for one platform from RAWG. Not yet implemented."""
        raise NotImplementedError(
            "RawgFetcher.fetch_platform() is not yet implemented. Use MobyGamesFetcher for now."
        )
