"""
Region-based ROM organizer.

Organizes ROMs by region (USA, Europe, Japan, etc.) extracted from filenames.
Supports No-Intro and Redump naming conventions.
"""

import logging
import re

from .base import BaseOrganizer, OrganizeMode

logger = logging.getLogger(__name__)


# Standard region codes from No-Intro
REGION_CODES = [
    "Argentina",
    "Asia",
    "Australia",
    "Austria",
    "Belgium",
    "Brazil",
    "Canada",
    "China",
    "Croatia",
    "Czech Republic",
    "Denmark",
    "Europe",
    "Finland",
    "France",
    "Germany",
    "Greece",
    "Hong Kong",
    "Hungary",
    "Ireland",
    "Israel",
    "Italy",
    "Japan",
    "Korea",
    "Mexico",
    "Netherlands",
    "New Zealand",
    "Norway",
    "Poland",
    "Portugal",
    "Russia",
    "Scandinavia",
    "Singapore",
    "Slovakia",
    "South Africa",
    "Spain",
    "Sweden",
    "Switzerland",
    "Taiwan",
    "Turkey",
    "UK",
    "Ukraine",
    "USA",
    "World",
]


class RegionOrganizer(BaseOrganizer):
    """
    Organize ROMs by region.

    Extracts region information from ROM filenames and organizes them into
    region-specific directories.

    Examples:
        >>> organizer = RegionOrganizer(
        ...     mode=OrganizeMode.MOVE,
        ...     keep_in_place=['USA', 'World']
        ... )
        >>> stats = organizer.organize(Path('/roms/nes'))

        # Results in:
        # /roms/nes/Super Mario Bros (USA).nes         <- kept in place
        # /roms/nes/By Region/Japan/Mario (Japan).nes  <- organized
        # /roms/nes/By Region/Europe/Mario (Europe).nes <- organized

    Args:
        mode: How to organize files (move, copy, or symlink)
        dry_run: Preview changes without actually making them
        region_priority: Preferred regions in order (for multi-region ROMs)
        keep_in_place: Regions to keep in root directory
        exclude_regions: Regions to exclude from organization
    """

    def __init__(
        self,
        mode: OrganizeMode = OrganizeMode.MOVE,
        dry_run: bool = False,
        region_priority: list[str] | None = None,
        keep_in_place: list[str] | None = None,
        exclude_regions: list[str] | None = None,
    ):
        super().__init__(
            mode=mode,
            dry_run=dry_run,
            keep_in_place=keep_in_place,
            exclude_values=exclude_regions,
        )
        self.region_priority = region_priority or ["USA", "Europe", "Japan", "World"]

        # Validate region priority
        for region in self.region_priority:
            if region not in REGION_CODES:
                logger.warning(f"Unknown region in priority list: {region}")

    def get_organization_dir_name(self) -> str:
        """Get the directory name for region organization."""
        return "By Region"

    def get_organization_value(self, filename: str) -> str | None:
        """
        Extract region from filename.

        Supports formats like:
        - (USA)
        - (Europe)
        - (USA, Europe)
        - (Japan) (En)

        For multi-region ROMs, returns the highest priority region.

        Args:
            filename: ROM filename

        Returns:
            Region code, or None if not detected
        """
        # Pattern to match regions in parentheses
        # Matches: (USA), (Europe), (USA, Europe), etc.
        pattern = r"\(([^)]+)\)"

        matches = re.findall(pattern, filename)

        if not matches:
            return None

        # Check each match for region codes
        detected_regions = []

        for match in matches:
            # Split by comma for multi-region entries
            parts = [p.strip() for p in match.split(",")]

            for part in parts:
                # Check if this part is a known region
                if part in REGION_CODES:
                    detected_regions.append(part)

        if not detected_regions:
            return None

        # If multiple regions detected, use priority
        if len(detected_regions) > 1:
            logger.debug(f"Multi-region ROM detected: {detected_regions}")
            for priority_region in self.region_priority:
                if priority_region in detected_regions:
                    logger.debug(f"Selected region: {priority_region} (priority)")
                    return priority_region

        # Return first detected region
        return detected_regions[0]
