"""Size tracking infrastructure for ROM output estimation.

Tracks actual output sizes per platform and compression format to enable
better storage budget estimation in future builds.
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PlatformSizeRecord:
    """Record of a single platform build's output size.

    Attributes:
        platform: Platform name (e.g., 'nes', 'psx')
        compression: Compression format used (e.g., '7z', 'chd')
        selection: Selection strategy used (e.g., 'all', 'best_of')
        input_files: Number of input files
        output_files: Number of output files
        input_size_bytes: Total input size
        output_size_bytes: Total output size
        timestamp: When this record was created
        notes: Optional notes about the build
    """

    platform: str
    compression: str
    selection: str = "all"
    input_files: int = 0
    output_files: int = 0
    input_size_bytes: int = 0
    output_size_bytes: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""

    @property
    def compression_ratio(self) -> float:
        """Compression ratio (output/input). Lower is better."""
        if self.input_size_bytes == 0:
            return 1.0
        return self.output_size_bytes / self.input_size_bytes

    @property
    def output_mb(self) -> float:
        """Output size in MB."""
        return self.output_size_bytes / (1024 * 1024)

    @property
    def output_gb(self) -> float:
        """Output size in GB."""
        return self.output_size_bytes / (1024 * 1024 * 1024)


class SizeDatabase:
    """Database of platform size records.

    Stores historical size data in a JSON file for future estimation.
    """

    def __init__(self, db_path: Path | None = None):
        """Initialize size database.

        Args:
            db_path: Path to JSON database file. Defaults to 'config/size_data.json'
        """
        self.db_path = db_path or Path("config/size_data.json")
        self.records: dict[str, list[dict]] = {}  # platform -> list of records
        self._load()

    def _load(self):
        """Load records from disk."""
        if self.db_path.exists():
            try:
                with open(self.db_path) as f:
                    self.records = json.load(f)
                logger.debug(f"Loaded {sum(len(v) for v in self.records.values())} size records")
            except Exception as e:
                logger.warning(f"Failed to load size database: {e}")
                self.records = {}
        else:
            logger.debug(f"No size database found at {self.db_path}")

    def _save(self):
        """Save records to disk."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.db_path, "w") as f:
                json.dump(self.records, f, indent=2)
            logger.debug(f"Saved size database to {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to save size database: {e}")

    def add_record(self, record: PlatformSizeRecord):
        """Add a new size record.

        Args:
            record: PlatformSizeRecord to add
        """
        if record.platform not in self.records:
            self.records[record.platform] = []

        self.records[record.platform].append(asdict(record))

        # Keep only last 10 records per platform
        if len(self.records[record.platform]) > 10:
            self.records[record.platform] = self.records[record.platform][-10:]

        self._save()

        logger.info(
            f"Recorded size for {record.platform}: "
            f"{record.output_mb:.1f} MB ({record.compression}, {record.selection})"
        )

    def get_estimate(
        self, platform: str, compression: str = "7z", selection: str = "all"
    ) -> int | None:
        """Get estimated output size for a platform.

        Uses historical data to estimate, with fallbacks.

        Args:
            platform: Platform name
            compression: Compression format
            selection: Selection strategy

        Returns:
            Estimated size in bytes, or None if no data available
        """
        if platform not in self.records:
            return None

        records = self.records[platform]

        # Try to find exact match first
        for r in reversed(records):  # Most recent first
            if r["compression"] == compression and r["selection"] == selection:
                return r["output_size_bytes"]

        # Try same compression, different selection
        for r in reversed(records):
            if r["compression"] == compression:
                # Scale based on selection strategy
                base_size = r["output_size_bytes"]
                base_selection = r["selection"]
                return self._scale_for_selection(base_size, base_selection, selection)

        # Use any available data
        if records:
            return records[-1]["output_size_bytes"]

        return None

    def _scale_for_selection(self, size: int, from_sel: str, to_sel: str) -> int:
        """Scale a size estimate based on selection strategy change.

        Args:
            size: Base size
            from_sel: Original selection strategy
            to_sel: Target selection strategy

        Returns:
            Scaled size estimate
        """
        # Selection strategy scaling factors
        # These are rough estimates - best_of typically has ~20-50 games
        scale_factors = {
            "all": 1.0,
            "best_of_extended": 0.15,
            "best_of": 0.10,
        }

        from_factor = scale_factors.get(from_sel, 1.0)
        to_factor = scale_factors.get(to_sel, 1.0)

        if from_factor == 0:
            return size

        return int(size * to_factor / from_factor)

    def get_all_platforms(self) -> list[str]:
        """Get list of all platforms with size data."""
        return list(self.records.keys())

    def get_summary(self, platform: str) -> dict | None:
        """Get summary statistics for a platform.

        Args:
            platform: Platform name

        Returns:
            Dictionary with summary statistics, or None if no data
        """
        if platform not in self.records:
            return None

        records = self.records[platform]
        if not records:
            return None

        sizes = [r["output_size_bytes"] for r in records]

        return {
            "platform": platform,
            "record_count": len(records),
            "avg_size_mb": sum(sizes) / len(sizes) / (1024 * 1024),
            "min_size_mb": min(sizes) / (1024 * 1024),
            "max_size_mb": max(sizes) / (1024 * 1024),
            "compressions": list({r["compression"] for r in records}),
            "last_updated": records[-1]["timestamp"],
        }


# Global instance for convenience
_size_db: SizeDatabase | None = None


def get_size_db(db_path: Path | None = None) -> SizeDatabase:
    """Get the global size database instance.

    Args:
        db_path: Optional path to database file

    Returns:
        SizeDatabase instance
    """
    global _size_db
    if _size_db is None:
        _size_db = SizeDatabase(db_path)
    return _size_db


def record_platform_size(
    platform: str,
    compression: str,
    output_size_bytes: int,
    selection: str = "all",
    input_files: int = 0,
    output_files: int = 0,
    input_size_bytes: int = 0,
    notes: str = "",
):
    """Convenience function to record a platform's output size.

    Args:
        platform: Platform name
        compression: Compression format
        output_size_bytes: Total output size in bytes
        selection: Selection strategy used
        input_files: Number of input files
        output_files: Number of output files
        input_size_bytes: Total input size
        notes: Optional notes
    """
    record = PlatformSizeRecord(
        platform=platform,
        compression=compression,
        selection=selection,
        input_files=input_files,
        output_files=output_files,
        input_size_bytes=input_size_bytes,
        output_size_bytes=output_size_bytes,
        notes=notes,
    )
    get_size_db().add_record(record)


def estimate_platform_size(
    platform: str,
    compression: str = "7z",
    selection: str = "all",
) -> int | None:
    """Convenience function to estimate a platform's output size.

    Args:
        platform: Platform name
        compression: Compression format
        selection: Selection strategy

    Returns:
        Estimated size in bytes, or None if no data
    """
    return get_size_db().get_estimate(platform, compression, selection)
