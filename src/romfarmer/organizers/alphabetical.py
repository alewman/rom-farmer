"""
Alphabetical ROM organizer.

Splits ROMs into lettered subdirectories for flashcart and Everdrive
navigation. Supports smart grouping to keep folder file counts manageable.
"""

import logging
from pathlib import Path

from .base import BaseOrganizer, OrganizeMode, OrganizeStats

logger = logging.getLogger(__name__)


class AlphabeticalOrganizer(BaseOrganizer):
    """
    Organize ROMs into alphabetical subdirectories.

    Three grouping strategies:
    - PER_LETTER: One folder per letter (A/, B/, ..., Z/, #/)
    - BALANCED: Fixed ranges (A-E/, F-M/, N-Z/, #/)
    - SMART: Adaptive ranges that keep each folder under max_per_group files
      (e.g., #-B/, C-E/, F/, G-M/, S#-Sg/, Sh-Sz/, ...)

    SMART mode is ideal for flashcarts like Everdrive where scrolling through
    50+ files in one folder is painful.

    Args:
        mode: How to organize files (move, copy, hardlink, or symlink)
        dry_run: Preview changes without actually making them
        strategy: 'per_letter', 'balanced', or 'smart'
        max_per_group: Maximum files per group (smart strategy only, default 50)
    """

    STRATEGY_PER_LETTER = "per_letter"
    STRATEGY_BALANCED = "balanced"
    STRATEGY_SMART = "smart"

    def __init__(
        self,
        mode: OrganizeMode = OrganizeMode.MOVE,
        dry_run: bool = False,
        strategy: str = "smart",
        max_per_group: int = 50,
    ):
        super().__init__(mode=mode, dry_run=dry_run)
        self.strategy = strategy
        self.max_per_group = max_per_group

    def get_organization_dir_name(self) -> str:
        return ""  # Files go directly into sub-letter folders, no wrapper

    def get_organization_value(self, filename: str) -> str | None:
        first = filename[0].upper() if filename else "#"
        return first if first.isalpha() else "#"

    def organize(
        self,
        source_dir: Path,
        dest_dir: Path | None = None,
        recursive: bool = False,
        extensions: list[str] | None = None,
    ) -> OrganizeStats:
        """Organize files into alphabetical groups.

        Override base to use strategy-based grouping instead of per-value dirs.
        """
        if dest_dir is None:
            dest_dir = source_dir

        self.stats = OrganizeStats()

        # Collect files (non-recursive by default — flashcarts are flat)
        files = sorted(
            (f for f in source_dir.iterdir() if f.is_file()),
            key=lambda f: f.name.upper(),
        )
        if extensions:
            exts = {(e if e.startswith(".") else f".{e}").lower() for e in extensions}
            files = [f for f in files if f.suffix.lower() in exts]

        if not files:
            logger.info("No files to organize")
            return self.stats

        logger.info(f"Organizing {len(files)} files with {self.strategy} strategy")

        if self.strategy == self.STRATEGY_PER_LETTER:
            groups = self._group_per_letter(files)
        elif self.strategy == self.STRATEGY_BALANCED:
            groups = self._group_balanced(files)
        else:
            groups = self._group_smart(files)

        for group_name, group_files in groups.items():
            target_dir = dest_dir / group_name
            for f in group_files:
                self.stats.files_processed += 1
                self.organize_file(f, target_dir)

        logger.info(f"Created {len(groups)} groups: {', '.join(groups.keys())}")
        return self.stats

    # ── Grouping strategies ──────────────────────────────────────────────

    def _first_char(self, f: Path) -> str:
        c = f.name[0].upper()
        return c if c.isalpha() else "#"

    def _group_per_letter(self, files: list[Path]) -> dict[str, list[Path]]:
        groups: dict[str, list[Path]] = {}
        for f in files:
            key = self._first_char(f)
            groups.setdefault(key, []).append(f)
        return groups

    def _group_balanced(self, files: list[Path]) -> dict[str, list[Path]]:
        ranges = {"#": [], "A-E": [], "F-M": [], "N-Z": []}
        for f in files:
            c = self._first_char(f)
            if c == "#":
                ranges["#"].append(f)
            elif c <= "E":
                ranges["A-E"].append(f)
            elif c <= "M":
                ranges["F-M"].append(f)
            else:
                ranges["N-Z"].append(f)
        return {k: v for k, v in ranges.items() if v}

    def _group_smart(self, files: list[Path]) -> dict[str, list[Path]]:
        """Adaptive grouping: merge small letters, split large ones."""
        # Count per letter
        by_letter: dict[str, list[Path]] = {}
        for f in files:
            key = self._first_char(f)
            by_letter.setdefault(key, []).append(f)

        letters = ["#"] + [chr(c) for c in range(ord("A"), ord("Z") + 1)]
        groups: dict[str, list[Path]] = {}
        current_files: list[Path] = []
        range_start: str | None = None

        for letter in letters:
            letter_files = by_letter.get(letter, [])

            # If this single letter exceeds max, flush current group and
            # handle the big letter on its own
            if len(letter_files) > self.max_per_group:
                # Flush accumulated range
                if current_files:
                    name = (
                        range_start
                        if range_start
                        == (
                            letters[letters.index(letter) - 1]
                            if letters.index(letter) > 0
                            else range_start
                        )
                        else f"{range_start}-{letters[letters.index(letter) - 1]}"
                    )
                    # Simplify: if start == end, just use the letter
                    prev_idx = letters.index(letter) - 1
                    prev = letters[prev_idx] if prev_idx >= 0 else range_start
                    name = range_start if range_start == prev else f"{range_start}-{prev}"
                    groups[name] = current_files
                    current_files = []
                    range_start = None
                # This letter gets its own folder
                groups[letter] = letter_files
                continue

            # Would adding this overflow?
            if current_files and len(current_files) + len(letter_files) > self.max_per_group:
                # Flush
                prev_idx = letters.index(letter) - 1
                prev = letters[prev_idx] if prev_idx >= 0 else range_start
                name = range_start if range_start == prev else f"{range_start}-{prev}"
                groups[name] = current_files
                current_files = []
                range_start = None

            if letter_files:
                if range_start is None:
                    range_start = letter
                current_files.extend(letter_files)

        # Flush remainder
        if current_files and range_start:
            # Find the last letter that had files
            last_letter = self._first_char(current_files[-1])
            name = range_start if range_start == last_letter else f"{range_start}-{last_letter}"
            groups[name] = current_files

        return groups
