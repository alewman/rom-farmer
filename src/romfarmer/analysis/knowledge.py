"""KnowledgeBase — the sole read facade over romfarmer.db for the planner.

The planner passes must not query the database directly; they receive a
``KnowledgeBase`` instance and call its typed methods.  This keeps the passes
pure (no I/O) when tested with a stub/fake.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Disc-number tag pattern — mirrors the bridge's _DISC_TAG
_DISC_TAG = re.compile(r"\s*\((?:Disc|Disk|CD)\s*\d+\)", re.IGNORECASE)


class KnowledgeBase:
    """Read-only facade over the romfarmer metadata database.

    All query methods are safe to call when no database exists — they return
    sensible defaults (``None`` / empty) rather than raising.

    The class is intentionally *not* frozen or a dataclass because it holds an
    optional heavy SQLAlchemy session.  Planner passes see it only through the
    type annotation and call the documented public methods.

    Args:
        db_path: Path to ``romfarmer.db``.  If ``None`` or the file does not
            exist, all queries silently return defaults.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db: Any = None
        if db_path is not None and db_path.exists():
            try:
                import importlib
                MetadataDatabase = importlib.import_module("romfarmer.metadata.database").MetadataDatabase
                self._db = MetadataDatabase(db_path)
            except Exception as exc:  # pragma: no cover
                logger.warning("KnowledgeBase: could not open %s: %s", db_path, exc)

    # ------------------------------------------------------------------
    # Rating / tier
    # ------------------------------------------------------------------

    def get_rating(self, platform: str, canonical_name: str) -> float | None:
        """Return the scraped rating for *canonical_name* on *platform*.

        Returns ``None`` when the game is unknown or the DB is unavailable.
        Rating is normalised to 0.0–1.0.
        """
        if self._db is None:
            return None
        try:
            import importlib
            ExternalScore = importlib.import_module("romfarmer.metadata.database").ExternalScore
            session = self._db.get_session()
            try:
                # Try external scores first (Metacritic etc.)
                score_row = (
                    session.query(ExternalScore)
                    .filter_by(platform=platform, name=canonical_name)
                    .first()
                )
                if score_row is not None:
                    val = score_row.best_score_normalized()
                    if val is not None:
                        return float(val)
                # Fall back to scraped game rating
                import importlib
                ScrapedGame = importlib.import_module("romfarmer.metadata.database").ScrapedGame
                game = (
                    session.query(ScrapedGame)
                    .filter_by(system=platform, name=canonical_name)
                    .first()
                )
                if game is not None and game.rating is not None:
                    return float(game.rating)
                return None
            finally:
                session.close()
        except Exception as exc:  # pragma: no cover
            logger.debug("KnowledgeBase.get_rating(%s, %s): %s", platform, canonical_name, exc)
            return None

    def get_ratings_bulk(
        self, platform: str, canonical_names: list[str]
    ) -> dict[str, float]:
        """Return {canonical_name: rating} for all names with known ratings.

        More efficient than calling ``get_rating`` in a loop.
        """
        if self._db is None or not canonical_names:
            return {}
        result: dict[str, float] = {}
        try:
            import importlib
            ScrapedGame = importlib.import_module("romfarmer.metadata.database").ScrapedGame
            session = self._db.get_session()
            try:
                games = (
                    session.query(ScrapedGame)
                    .filter(
                        ScrapedGame.system == platform,
                        ScrapedGame.name.in_(canonical_names),
                        ScrapedGame.rating.isnot(None),
                    )
                    .all()
                )
                for g in games:
                    if g.rating is not None:
                        result[g.name] = float(g.rating)
                return result
            finally:
                session.close()
        except Exception as exc:  # pragma: no cover
            logger.debug("KnowledgeBase.get_ratings_bulk(%s): %s", platform, exc)
            return result

    # ------------------------------------------------------------------
    # Arcade driver status
    # ------------------------------------------------------------------

    def get_arcade_driver_status(self, rom_name: str) -> str | None:
        """Return the MAME driver_status for *rom_name* (e.g. ``"good"``).

        Returns ``None`` when unknown.
        """
        if self._db is None:
            return None
        try:
            import importlib
            DatGameEntry = importlib.import_module("romfarmer.metadata.database").DatGameEntry
            session = self._db.get_session()
            try:
                entry = (
                    session.query(DatGameEntry)
                    .filter_by(rom_name=rom_name)
                    .first()
                )
                if entry is not None:
                    status: str | None = getattr(entry, "driver_status", None)
                    return status
                return None
            finally:
                session.close()
        except Exception as exc:  # pragma: no cover
            logger.debug("KnowledgeBase.get_arcade_driver_status(%s): %s", rom_name, exc)
            return None

    def is_arcade_parent(self, rom_name: str) -> bool | None:
        """Return whether *rom_name* is a parent entry (not a clone).

        Returns ``None`` when unknown.
        """
        if self._db is None:
            return None
        try:
            import importlib
            DatGameEntry2 = importlib.import_module("romfarmer.metadata.database").DatGameEntry
            session = self._db.get_session()
            try:
                entry = (
                    session.query(DatGameEntry2)
                    .filter_by(rom_name=rom_name)
                    .first()
                )
                if entry is not None:
                    is_parent: bool = entry.is_parent()
                    return is_parent
                return None
            finally:
                session.close()
        except Exception as exc:  # pragma: no cover
            logger.debug("KnowledgeBase.is_arcade_parent(%s): %s", rom_name, exc)
            return None

    # ------------------------------------------------------------------
    # Compression telemetry (feeds CostModel posteriors)
    # ------------------------------------------------------------------

    def get_compression_ratio(
        self, platform: str, tool: str
    ) -> tuple[float, int] | None:
        """Return ``(avg_ratio, sample_count)`` from recorded transformations.

        Returns ``None`` when there is insufficient data (< 5 samples).
        """
        if self._db is None:
            return None
        try:
            ratio = self._db.get_average_compression_ratio(platform, tool)
            if ratio is not None:
                # The DB method returns a bare float ratio; we don't have a
                # sample count from this API — use a nominal 10 samples so
                # the posterior weight is meaningful but not overwhelming.
                return (float(ratio), 10)
            return None
        except Exception as exc:  # pragma: no cover
            logger.debug("KnowledgeBase.get_compression_ratio(%s, %s): %s", platform, tool, exc)
            return None
