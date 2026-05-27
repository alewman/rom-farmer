"""Filter ROMs based on scraped metadata (genre, rating, players, flags)."""

import fnmatch
import logging
import re
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from ..config.models import MetadataFilterConfig
from ..core.paths import get_paths
from .base import Stage, StageContext, StageResult, StageStatus, StagePhase

logger = logging.getLogger(__name__)

# Parses player strings like "1", "1-2", "1-4", "4+", "2-8"
_PLAYERS_RE = re.compile(r"(\d+)")


def _parse_max_players(players_str: Optional[str]) -> Optional[int]:
    """Return the maximum player count from a scraped 'players' field.

    Examples:
        "1"     → 1
        "1-2"   → 2
        "1-4"   → 4
        "4+"    → 4  (treat '+' as the stated number)
        "2-8"   → 8
        None    → None
    """
    if not players_str:
        return None
    nums = [int(m) for m in _PLAYERS_RE.findall(players_str)]
    return max(nums) if nums else None


class MetadataFilterStage(Stage):
    """PLAN-phase stage: filter matched ROMs using scraped_games metadata.

    Runs after FilterDATStage (which populates MD5s) and before
    SelectionFilter/ApplyLists.  Each matched file is looked up in the
    ``scraped_games`` database by MD5 hash (filename fallback), then tested
    against every active condition in ``MetadataFilterConfig``.

    Condition logic:
    - All active conditions are ANDed.
    - ``require_metadata=True``: ROMs with *no* DB entry are dropped.
    - ``require_metadata=False`` (default): ROMs with no DB entry pass through
      all metadata conditions but still fail name/flag conditions derived from
      the file name alone.
    - ``include_genres``: if the list is non-empty, a ROM passes only if its
      scraped genre contains at least one listed substring.  ROMs with no genre
      entry pass unless ``require_metadata=True``.
    - ``exclude_genres``: a ROM is dropped if its genre contains any listed
      substring (regardless of require_metadata).
    - ``exclude_nongames``: drops ROMs whose scraped *name* starts with 'ZZZ'.
    """

    PHASE = StagePhase.PLAN

    def __init__(
        self,
        config: MetadataFilterConfig,
        metadata_db: Optional[Path] = None,
    ):
        super().__init__("Metadata Filter")
        self.config = config
        self.metadata_db: Optional[Path] = metadata_db or self._find_metadata_db()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _find_metadata_db(self) -> Optional[Path]:
        try:
            return get_paths().metadata_db
        except Exception:
            return None

    def _load_metadata(
        self,
        md5s: Dict[Path, str],
        filenames: List[Path],
    ) -> Dict[str, Dict]:
        """Return a dict mapping MD5 → scraped row (or filename → scraped row).

        Falls back to filename lookup when MD5 is not in the DB.
        """
        if not self.metadata_db or not self.metadata_db.exists():
            logger.debug("MetadataFilterStage: no metadata DB found — all ROMs pass through")
            return {}

        conn = sqlite3.connect(str(self.metadata_db))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Verify table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scraped_games'")
        if not cursor.fetchone():
            conn.close()
            logger.warning("MetadataFilterStage: scraped_games table not found in DB")
            return {}

        result: Dict[str, Dict] = {}

        # Batch MD5 lookup
        all_md5s = [v for v in md5s.values() if v]
        if all_md5s:
            placeholders = ",".join("?" * len(all_md5s))
            try:
                cursor.execute(
                    f"""
                    SELECT md5, name, genre, rating, players, hidden, filename
                    FROM scraped_games
                    WHERE LOWER(md5) IN ({placeholders})
                    """,
                    [m.lower() for m in all_md5s],
                )
                for row in cursor.fetchall():
                    result[row["md5"].lower() if row["md5"] else ""] = dict(row)
            except sqlite3.OperationalError as exc:
                logger.warning("MetadataFilterStage: MD5 lookup failed: %s", exc)

        # Filename fallback for files not found by MD5
        found_md5s = set(result.keys())
        for fp in filenames:
            md5 = md5s.get(fp, "")
            if md5 and md5.lower() in found_md5s:
                continue  # already found via MD5
            fname = fp.name
            try:
                cursor.execute(
                    """
                    SELECT md5, name, genre, rating, players, hidden, filename
                    FROM scraped_games
                    WHERE LOWER(filename) = LOWER(?)
                    """,
                    (fname,),
                )
                row = cursor.fetchone()
                if row:
                    key = f"__fname__{fname.lower()}"
                    result[key] = dict(row)
            except sqlite3.OperationalError:
                pass

        conn.close()
        return result

    def _get_row(
        self,
        fp: Path,
        md5: Optional[str],
        db_rows: Dict[str, Dict],
    ) -> Optional[Dict]:
        """Retrieve the scraped row for a file (MD5 first, filename fallback)."""
        if md5 and md5.lower() in db_rows:
            return db_rows[md5.lower()]
        key = f"__fname__{fp.name.lower()}"
        return db_rows.get(key)

    def _passes(self, fp: Path, row: Optional[Dict]) -> Tuple[bool, str]:
        """Test a single file against all active filter conditions.

        Returns (passes: bool, reason: str).
        """
        cfg = self.config

        # --- require_metadata ------------------------------------------------
        if cfg.require_metadata and row is None:
            return False, "no metadata entry (require_metadata=True)"

        # --- exclude_nongames ------------------------------------------------
        if cfg.exclude_nongames:
            name = (row or {}).get("name") or ""
            if name.startswith("ZZZ"):
                return False, f"nongame marker (name={name!r})"

        # --- exclude_name_patterns -------------------------------------------
        if cfg.exclude_name_patterns:
            name = (row or {}).get("name") or ""
            for pattern in cfg.exclude_name_patterns:
                if fnmatch.fnmatch(name, pattern):
                    return False, f"name matches exclude pattern {pattern!r}"

        # --- exclude_hidden --------------------------------------------------
        if cfg.exclude_hidden:
            hidden = bool((row or {}).get("hidden", False))
            if hidden:
                return False, "hidden=True in scraped data"

        # --- min_rating ------------------------------------------------------
        if cfg.min_rating is not None and row is not None:
            rating = row.get("rating")
            if rating is not None and float(rating) < cfg.min_rating:
                return False, f"rating {rating:.2f} < min_rating {cfg.min_rating:.2f}"

        # --- genre filters ---------------------------------------------------
        genre_raw = (row or {}).get("genre") or ""
        genre_lower = genre_raw.lower()

        if cfg.exclude_genres and genre_raw:
            for g in cfg.exclude_genres:
                if g.lower() in genre_lower:
                    return False, f"genre {genre_raw!r} matches exclude_genres {g!r}"

        if cfg.include_genres and row is not None:
            if not genre_raw:
                # No genre info — keep unless require_metadata would already drop it
                pass
            else:
                if not any(g.lower() in genre_lower for g in cfg.include_genres):
                    return False, f"genre {genre_raw!r} not in include_genres"

        # --- min_players -----------------------------------------------------
        if cfg.min_players is not None and row is not None:
            players_raw = row.get("players")
            max_players = _parse_max_players(players_raw)
            if max_players is not None and max_players < cfg.min_players:
                return False, (
                    f"max players {max_players} < min_players {cfg.min_players} "
                    f"(scraped: {players_raw!r})"
                )

        return True, ""

    # ------------------------------------------------------------------
    # Stage interface
    # ------------------------------------------------------------------

    def should_skip(self, context: StageContext) -> bool:
        """Skip if filter is effectively a no-op."""
        cfg = self.config
        return not any([
            cfg.exclude_nongames,
            cfg.exclude_name_patterns,
            cfg.exclude_hidden,
            cfg.min_rating is not None,
            cfg.include_genres,
            cfg.exclude_genres,
            cfg.min_players is not None,
            cfg.require_metadata,
        ])

    def execute(self, context: StageContext) -> StageResult:
        """Apply metadata filters to context.files.matched (and legacy matched_files)."""
        # Use domain object if populated, fall back to legacy list
        matched: List[Path] = list(context.files.matched or context.matched_files or [])
        if not matched:
            return StageResult(
                status=StageStatus.SKIPPED,
                message="No matched files to filter",
            )

        # Collect MD5s (prefer new domain object, fall back to legacy dicts)
        md5_map: Dict[Path, str] = {}
        for fp in matched:
            md5 = (
                context.hashes.source_md5.get(fp)
                or context.hashes.rom_md5.get(fp)
                or context.file_md5s.get(fp)
                or context.rom_md5_map.get(fp)
                or ""
            )
            md5_map[fp] = md5

        db_rows = self._load_metadata(md5_map, matched)

        kept: List[Path] = []
        excluded: List[Tuple[Path, str]] = []

        for fp in matched:
            md5 = md5_map.get(fp, "")
            row = self._get_row(fp, md5, db_rows)
            passes, reason = self._passes(fp, row)
            if passes:
                kept.append(fp)
            else:
                excluded.append((fp, reason))

        # Log exclusions
        if excluded:
            logger.info(
                "MetadataFilterStage: excluded %d / %d ROMs",
                len(excluded),
                len(matched),
            )
            for fp, reason in excluded:
                logger.debug("  EXCLUDED %s — %s", fp.name, reason)
        else:
            logger.info(
                "MetadataFilterStage: all %d ROMs passed filters",
                len(matched),
            )

        # Write back to both domain object and legacy fields
        context.files.matched = kept
        context.matched_files = kept

        return StageResult(
            status=StageStatus.SUCCESS,
            message=(
                f"Metadata filter: kept {len(kept)}, excluded {len(excluded)}"
                + (f" (no DB — {len(matched)} passed)" if not db_rows and not excluded else "")
            ),
            files_processed=len(kept),
        )
