#!/usr/bin/env python3
"""
Detect revision duplicates in build output.

This script identifies cases where both original and revised versions of games
exist in the output directory. This is common with Redump DATs which lack
parent/clone relationships, causing 1G1R filters to keep both versions.

Usage:
    python3 scripts/detect_revision_duplicates.py <output_dir> [--generate-list]

Example:
    python3 scripts/detect_revision_duplicates.py /path/to/output/psx-full
    python3 scripts/detect_revision_duplicates.py /path/to/output/psx-full --generate-list > lists/psx-delete
"""

import re
import sys
from collections import defaultdict
from pathlib import Path


def find_revision_duplicates(output_dir: Path) -> dict[str, list[Path]]:
    """
    Find games where both non-revised and revised versions exist.

    Handles multiple revision patterns:
    - Standard: (Rev 1), (Rev 2), (Rev A), (Rev B)
    - PC Engine pressing codes: (FAAT), (FABT), (FACT), etc.
    - Alternative dumps: (Alt 1), (Alt 2)
    - Combined: (FABT, FACT, FAET)

    Returns:
        Dict mapping base game name to list of files (both non-Rev and Rev versions)
    """
    # Find all CHD, CUE, ISO, ZIP, or CSO files (source or output directories)
    files = []
    for ext in ["*.chd", "*.cue", "*.iso", "*.zip", "*.cso"]:
        files.extend(output_dir.rglob(ext))

    if not files:
        print(f"⚠️  No CHD/CUE/ISO/ZIP files found in {output_dir}")
        return {}

    # Group by base name (without revision info)
    games_by_base: dict[str, list[Path]] = defaultdict(list)

    # Patterns to remove for base name matching:
    # - (Rev N) or (Rev X) - standard revisions
    # - (FA*T), (SA*S), etc. - PC Engine pressing codes
    # - (Alt N) - alternative dumps
    # - Combined codes like (FABT, FACT)
    revision_patterns = [
        r" \(Rev [0-9A-Z]+\)",  # (Rev 1), (Rev A), etc.
        r" \(FA[A-Z]T(?:, FA[A-Z]T)*\)",  # (FAAT), (FABT), (FAAT, FACT), etc.
        r" \(SA[A-Z]S(?:, SA[A-Z]S)*\)",  # (SADS), (SAES), etc.
        r" \(Alt [0-9]+\)",  # (Alt 1), (Alt 2)
        # Complex multi-code patterns (PC Engine often combines multiple codes)
        r" \([A-Z]{4}(?:, [A-Z]{4})+\)",  # Any 4-letter codes combined
    ]

    for file in files:
        name = file.stem

        # Remove all revision markers to get base name
        base_name = name
        for pattern in revision_patterns:
            base_name = re.sub(pattern, "", base_name)

        games_by_base[base_name].append(file)

    # Find games with duplicates (has both revised and non-revised versions)
    duplicates: dict[str, list[Path]] = {}

    # Revision detection patterns (what indicates a revised version)
    revision_indicators = [
        r"\(Rev [0-9A-Z]+\)",  # Standard revisions
        r"\(FA[A-Z]T\)",  # PC Engine FA* codes
        r"\(SA[A-Z]S\)",  # PC Engine SA* codes
        r"\(Alt [0-9]+\)",  # Alternative dumps
        r"\([A-Z]{4}(?:, [A-Z]{4})+\)",  # Multi-code variants
    ]

    for base_name, files in games_by_base.items():
        if len(files) > 1:
            # Check if we have both revised and non-revised versions
            has_rev = False
            has_nonrev = False

            for f in files:
                is_revised = any(re.search(pattern, f.stem) for pattern in revision_indicators)
                if is_revised:
                    has_rev = True
                else:
                    has_nonrev = True

            if has_rev and has_nonrev:
                duplicates[base_name] = sorted(files, key=lambda f: f.stem)

    return duplicates


def get_highest_revision(files: list[Path]) -> Path:
    """
    Determine which file has the highest revision number or best pressing.

    Priority order:
    1. Highest numeric Rev (Rev 7 > Rev 3 > Rev 1)
    2. Latest alphabetic Rev (Rev B > Rev A)
    3. Latest Alt (Alt 2 > Alt 1)
    4. PC Engine codes: FABT/FACT preferred over FAAT
    5. Multi-code pressings (has more codes = better dump)
    """

    # Pattern priorities (higher score = better)
    def score_revision(filename: str) -> tuple:
        # Numeric revision (Rev 1-9)
        numeric_rev = re.search(r"\(Rev (\d+)\)", filename)
        numeric_score = int(numeric_rev.group(1)) if numeric_rev else 0

        # Alpha revision (Rev A-Z)
        alpha_rev = re.search(r"\(Rev ([A-Z])\)", filename)
        alpha_score = ord(alpha_rev.group(1)) - ord("A") if alpha_rev else 0

        # Alt dumps (Alt 1-9)
        alt = re.search(r"\(Alt (\d+)\)", filename)
        alt_score = int(alt.group(1)) if alt else 0

        # PC Engine pressing codes - prefer later alphabet (BT > AT, CT > BT)
        pressing_code = re.search(r"\((FA|SA)([A-Z])T", filename)
        pressing_score = ord(pressing_code.group(2)) - ord("A") if pressing_code else 0

        # Multi-code variants (more codes = more complete dump)
        multi_codes = re.findall(r"\(([A-Z]{4}(?:, [A-Z]{4})+)\)", filename)
        multi_score = len(multi_codes[0].split(", ")) if multi_codes else 0

        # Combined score: (numeric_rev, alpha_rev, pressing, multi, alt)
        # Higher values in earlier positions have priority
        return (numeric_score, alpha_score, pressing_score, multi_score, alt_score)

    # Find file with highest score
    if not files:
        return None

    return max(files, key=lambda f: score_revision(f.stem))


def categorize_duplicates(duplicates: dict[str, list[Path]]) -> tuple[list[str], list[str]]:
    """
    Categorize duplicates into single-disc and multi-disc games.

    Returns:
        Tuple of (single_disc_games, multi_disc_games) with base names
    """
    single_disc = []
    multi_disc = []

    # Group by series (remove disc numbers)
    series_pattern = re.compile(r"(.*?)(?:\s+\(Disc \d+\))?$")
    series_groups: dict[str, list[str]] = defaultdict(list)

    for base_name in duplicates.keys():
        match = series_pattern.match(base_name)
        series_name = match.group(1) if match else base_name
        series_groups[series_name].append(base_name)

    for series_name, games in series_groups.items():
        if len(games) > 1:
            multi_disc.extend(sorted(games))
        else:
            single_disc.append(games[0])

    return sorted(single_disc), sorted(multi_disc)


def analyze_m3u_files(output_dir: Path) -> dict[str, list[str]]:
    """
    Analyze M3U playlists to find games with mixed revisions.

    Detects mixing of:
    - Standard revisions (Rev 1, Rev 2)
    - PC Engine pressing codes (FAAT, FABT)
    - Alternative dumps (Alt 1, Alt 2)

    Returns:
        Dict mapping M3U basename to list of disc entries
    """
    m3u_files = list(output_dir.rglob("*.m3u"))
    mixed_revisions = {}

    # All revision patterns
    revision_patterns = [
        r"\(Rev [0-9A-Z]+\)",
        r"\(FA[A-Z]T\)",
        r"\(SA[A-Z]S\)",
        r"\(Alt [0-9]+\)",
        r"\([A-Z]{4}(?:, [A-Z]{4})+\)",
    ]

    for m3u_file in m3u_files:
        with open(m3u_file) as f:
            discs = [line.strip() for line in f if line.strip()]

        # Check if M3U has both revised and non-revised entries
        has_rev = False
        has_nonrev = False

        for disc in discs:
            is_revised = any(re.search(pattern, disc) for pattern in revision_patterns)
            if is_revised:
                has_rev = True
            else:
                has_nonrev = True

        if has_rev and has_nonrev:
            mixed_revisions[m3u_file.stem] = discs

    return mixed_revisions


def print_report(duplicates: dict[str, list[Path]], output_dir: Path):
    """Print detailed analysis report."""
    print(f"\n{'=' * 80}")
    print("REVISION DUPLICATE ANALYSIS")
    print(f"Output Directory: {output_dir}")
    print(f"{'=' * 80}\n")

    if not duplicates:
        print("✅ No revision duplicates found! All games have only one version.\n")
        return

    # Categorize
    single_disc, multi_disc = categorize_duplicates(duplicates)

    # Count files and identify revision types
    total_duplicate_files = sum(len(files) for files in duplicates.values())
    files_to_delete = []
    files_to_keep = []

    # Revision type statistics
    revision_types = {
        "standard": 0,  # (Rev 1), (Rev A)
        "pc_engine": 0,  # (FAAT), (FABT)
        "alt_dumps": 0,  # (Alt 1), (Alt 2)
        "multi_code": 0,  # (FABT, FACT)
    }

    # For each game, determine the SINGLE best version to keep
    for _base_name, files in duplicates.items():
        # Find the best version
        best_file = get_highest_revision(files)

        for f in files:
            filename = f.stem
            # Check what type of revision this is
            if re.search(r"\(Rev [0-9A-Z]+\)", filename):
                if "(Rev" not in filename.replace(
                    re.search(r"\(Rev [0-9A-Z]+\)", filename).group(), ""
                ):
                    revision_types["standard"] += 1
            if re.search(r"\((FA|SA)[A-Z][TS]\)", filename):
                revision_types["pc_engine"] += 1
            if re.search(r"\(Alt [0-9]+\)", filename):
                revision_types["alt_dumps"] += 1
            if re.search(r"\([A-Z]{4}(?:, [A-Z]{4})+\)", filename):
                revision_types["multi_code"] += 1

            # Keep only the best version, delete all others
            if f == best_file:
                files_to_keep.append(f)
            else:
                files_to_delete.append(f)

    print(f"⚠️  Found {len(duplicates)} games with revision duplicates")
    print(f"    Single-disc games: {len(single_disc)}")
    print(f"    Multi-disc games: {len(multi_disc)}")
    print(f"    Total duplicate files: {total_duplicate_files}")
    print(f"    Files to keep (best version): {len(files_to_keep)}")
    print(f"    Files to delete: {len(files_to_delete)}")
    print()

    # Show revision type breakdown
    print("Revision Types Found:")
    if revision_types["standard"] > 0:
        print(f"  - Standard revisions (Rev 1, Rev A): {revision_types['standard']} files")
    if revision_types["pc_engine"] > 0:
        print(f"  - PC Engine pressing codes (FAAT, FABT): {revision_types['pc_engine']} files")
    if revision_types["alt_dumps"] > 0:
        print(f"  - Alternative dumps (Alt 1, Alt 2): {revision_types['alt_dumps']} files")
    if revision_types["multi_code"] > 0:
        print(f"  - Multi-code variants (FABT, FACT): {revision_types['multi_code']} files")
    print()

    # Analyze M3U files
    print("Checking M3U playlists for mixed revisions...")
    mixed_m3u = analyze_m3u_files(output_dir)

    if mixed_m3u:
        print(f"⚠️  Found {len(mixed_m3u)} M3U playlists with mixed revisions:\n")
        for m3u_name, discs in sorted(mixed_m3u.items()):
            print(f"  {m3u_name}.m3u ({len(discs)} discs)")
            for disc in discs:
                # Check if this disc has revision markers
                has_revision = any(
                    re.search(pattern, disc)
                    for pattern in [
                        r"\(Rev [0-9A-Z]+\)",
                        r"\((FA|SA)[A-Z][TS]\)",
                        r"\(Alt [0-9]+\)",
                        r"\([A-Z]{4}(?:, [A-Z]{4})+\)",
                    ]
                )
                marker = "  [KEEP]  " if has_revision else "  [DELETE]"
                print(f"    {marker} {disc}")
            print()
    else:
        print("✅ No M3U playlists with mixed revisions\n")

    # Detailed list
    print(f"\n{'=' * 80}")
    print("GAMES WITH DUPLICATES")
    print(f"{'=' * 80}\n")

    if single_disc:
        print(f"Single-Disc Games ({len(single_disc)}):")
        print("-" * 80)
        for game in single_disc:
            files = duplicates[game]
            best_file = get_highest_revision(files)
            print(f"\n{game}:")
            for f in files:
                marker = "  [KEEP]  " if f == best_file else "  [DELETE]"
                print(f"  {marker} {f.name}")

    if multi_disc:
        print(f"\n\nMulti-Disc Games ({len({g.split(' (Disc')[0] for g in multi_disc})} series):")
        print("-" * 80)

        # Group by series
        current_series = None
        for game in multi_disc:
            series = game.split(" (Disc")[0]
            if series != current_series:
                current_series = series
                print(f"\n{series}:")

            files = duplicates[game]
            best_file = get_highest_revision(files)
            for f in files:
                marker = "  [KEEP]  " if f == best_file else "  [DELETE]"
                disc_info = f.stem.split("(Disc")[-1].split(")")[0] if "(Disc" in f.stem else ""
                disc_label = f" Disc {disc_info}" if disc_info else ""

                # Extract revision info for display
                rev_info = ""
                if re.search(r"\(Rev [0-9A-Z]+\)", f.stem):
                    rev_match = re.search(r"\(Rev ([0-9A-Z]+)\)", f.stem)
                    rev_info = f" (Rev {rev_match.group(1)})"
                elif re.search(r"\((FA|SA)[A-Z][TS]\)", f.stem):
                    rev_match = re.search(r"\(([FS]A[A-Z][TS])\)", f.stem)
                    rev_info = f" ({rev_match.group(1)})"
                elif re.search(r"\(Alt [0-9]+\)", f.stem):
                    rev_match = re.search(r"\(Alt ([0-9]+)\)", f.stem)
                    rev_info = f" (Alt {rev_match.group(1)})"
                elif re.search(r"\([A-Z]{4}(?:, [A-Z]{4})+\)", f.stem):
                    rev_match = re.search(r"\(([A-Z]{4}(?:, [A-Z]{4})+)\)", f.stem)
                    rev_info = f" ({rev_match.group(1)})"

                print(f"  {marker} {disc_label}{rev_info}")


def generate_delete_list(duplicates: dict[str, list[Path]]) -> str:
    """Generate a delete list file content."""
    single_disc, multi_disc = categorize_duplicates(duplicates)

    lines = [
        "# Auto-generated PSX Delete List - Remove Non-Revised Versions",
        "#",
        "# This list removes original (non-Rev) versions of games where a revised",
        "# version (Rev N) exists. Generated by detect_revision_duplicates.py",
        "#",
        f"# Total games to delete: {len(duplicates)}",
        "",
        "",
    ]

    if single_disc:
        lines.append("# Single-disc games with Rev duplicates")
        lines.extend(single_disc)
        lines.append("")

    if multi_disc:
        lines.append("# Multi-disc games with Rev duplicates (delete all non-Rev discs)")
        lines.extend(multi_disc)
        lines.append("")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    output_dir = Path(sys.argv[1])
    generate_list = "--generate-list" in sys.argv

    if not output_dir.exists():
        print(f"Error: Directory not found: {output_dir}")
        sys.exit(1)

    # Find duplicates
    duplicates = find_revision_duplicates(output_dir)

    if generate_list:
        # Just output the delete list
        print(generate_delete_list(duplicates))
    else:
        # Print full analysis report
        print_report(duplicates, output_dir)

        if duplicates:
            print(f"\n{'=' * 80}")
            print("NEXT STEPS")
            print(f"{'=' * 80}\n")
            print("To generate a delete list for use with ROM Farmer:")
            print(
                f"  python3 scripts/detect_revision_duplicates.py {output_dir} --generate-list > lists/psx-delete"
            )
            print()


if __name__ == "__main__":
    main()
