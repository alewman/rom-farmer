"""Generate Logiqx XML DAT files from source ROM directories.

Scans a source directory of ROM files (ZIPs, ISOs, WUX, RVZ, etc.),
collects metadata (filename, size, optionally hashes), and outputs a
standard Logiqx XML DAT file.

Can optionally enrich entries by fuzzy-matching against a reference DAT
to borrow category, description, serial, and other metadata.
"""

import hashlib
import os
import re
import xml.etree.ElementTree as ET
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from xml.dom import minidom

from .models import DATFile, DATGame, DATRom


def _normalize_name(name: str) -> str:
    """Normalize a game name for fuzzy matching.

    Strips file extension, removes common format suffixes,
    normalizes whitespace and punctuation.
    """
    # Remove file extension
    stem = Path(name).stem

    # Lowercase for comparison
    s = stem.lower()

    # Remove common parenthetical tags that vary between sources
    # Keep region/language tags for matching accuracy
    s = re.sub(r"\s*\(rev\s*\d+\)", "", s)

    # Normalize punctuation
    s = re.sub(r"[&]", "and", s)
    s = re.sub(r"[^\w\s()-]", "", s)

    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()

    return s


def _normalize_aggressive(name: str) -> str:
    """More aggressive normalization for fallback matching.

    Strips all spaces and punctuation for cases like
    'ZhuZhu' vs 'Zhu Zhu', 'LEGO' vs 'Lego', etc.
    """
    s = _normalize_name(name)
    # Remove all spaces and non-alphanumeric (except parens for regions)
    s = re.sub(r"[\s\-_]", "", s)
    return s


def _build_reference_index(ref_dat: DATFile) -> tuple[dict[str, DATGame], dict[str, DATGame]]:
    """Build normalized-name → DATGame lookups from a reference DAT.

    Returns a tuple of (exact_index, aggressive_index) where:
    - exact_index maps standard-normalized names to DATGame entries
    - aggressive_index maps aggressively-normalized names (no spaces) for fallback
    """
    exact: dict[str, DATGame] = {}
    aggressive: dict[str, DATGame] = {}

    for game in ref_dat.games:
        # Index by game name
        norm = _normalize_name(game.name)
        if norm not in exact:
            exact[norm] = game

        agg = _normalize_aggressive(game.name)
        if agg not in aggressive:
            aggressive[agg] = game

        # Also index by description if different
        if game.description and game.description != game.name:
            desc_norm = _normalize_name(game.description)
            if desc_norm not in exact:
                exact[desc_norm] = game
            desc_agg = _normalize_aggressive(game.description)
            if desc_agg not in aggressive:
                aggressive[desc_agg] = game

    return exact, aggressive


def _match_reference(
    name: str,
    ref_exact: dict[str, DATGame],
    ref_aggressive: dict[str, DATGame],
) -> DATGame | None:
    """Try to find a matching game in the reference indices.

    Attempts exact normalized match first, then aggressive (no-space)
    match, then progressively looser matches.
    """
    norm = _normalize_name(name)

    # Exact normalized match
    if norm in ref_exact:
        return ref_exact[norm]

    # Aggressive match (handles ZhuZhu vs Zhu Zhu, etc.)
    agg = _normalize_aggressive(name)
    if agg in ref_aggressive:
        return ref_aggressive[agg]

    # Try without region/language tags entirely
    no_parens = re.sub(r"\s*\([^)]*\)", "", norm).strip()
    for ref_norm, game in ref_exact.items():
        ref_no_parens = re.sub(r"\s*\([^)]*\)", "", ref_norm).strip()
        if no_parens and no_parens == ref_no_parens:
            return game

    return None


def scan_source_directory(
    source_dir: Path,
    *,
    compute_hashes: bool = False,
    hash_zip_contents: bool = False,
    crc_from_zip: bool = False,
    recursive: bool = False,
    extensions: set[str] | None = None,
    progress_callback=None,
    workers: int | None = None,
) -> list[DATGame]:
    """Scan a source directory and build DATGame entries.

    Args:
        source_dir: Directory containing ROM files
        compute_hashes: Whether to compute MD5/SHA1/CRC for outer files
        hash_zip_contents: Whether to open ZIPs and hash inner files
        crc_from_zip: Whether to extract CRC32 from ZIP central directory
                      (instant, no file I/O needed beyond reading the header)
        recursive: Whether to scan subdirectories
        extensions: File extensions to include (default: common ROM formats)
        progress_callback: Called with (current, total, filename) for progress
        workers: Number of parallel workers (default: CPU count)

    Returns:
        List of DATGame entries with ROM metadata
    """
    if extensions is None:
        extensions = {
            ".zip",
            ".7z",
            ".rvz",
            ".wux",
            ".iso",
            ".wad",
            ".nsp",
            ".xci",
            ".chd",
            ".cso",
            ".pbp",
            ".pkg",
        }

    # Collect files
    if recursive:
        files = sorted(
            f for f in source_dir.rglob("*") if f.is_file() and f.suffix.lower() in extensions
        )
    else:
        files = sorted(
            f for f in source_dir.iterdir() if f.is_file() and f.suffix.lower() in extensions
        )

    total = len(files)

    # Use parallel processing when hashing is involved and we have many files
    use_parallel = (compute_hashes or hash_zip_contents) and total > 1
    if workers is None:
        workers = min(os.cpu_count() or 1, total)

    if use_parallel and workers > 1:
        return _scan_parallel(
            files,
            total,
            compute_hashes=compute_hashes,
            hash_zip_contents=hash_zip_contents,
            crc_from_zip=crc_from_zip,
            workers=workers,
            progress_callback=progress_callback,
        )

    # Serial fallback (fast operations like crc_from_zip, or small file counts)
    games: list[DATGame] = []
    for i, file_path in enumerate(files):
        if progress_callback:
            progress_callback(i + 1, total, file_path.name)

        game = _scan_file(
            file_path,
            compute_hashes=compute_hashes,
            hash_zip_contents=hash_zip_contents,
            crc_from_zip=crc_from_zip,
        )
        if game:
            games.append(game)

    return games


def _scan_file_worker(args: tuple) -> DATGame | None:
    """Worker function for parallel scanning (must be top-level for pickling)."""
    file_path, compute_hashes, hash_zip_contents, crc_from_zip = args
    return _scan_file(
        Path(file_path),
        compute_hashes=compute_hashes,
        hash_zip_contents=hash_zip_contents,
        crc_from_zip=crc_from_zip,
    )


def _scan_parallel(
    files: list[Path],
    total: int,
    *,
    compute_hashes: bool,
    hash_zip_contents: bool,
    crc_from_zip: bool,
    workers: int,
    progress_callback=None,
) -> list[DATGame]:
    """Scan files in parallel using a process pool."""
    # Prepare args as tuples (Path objects need to be passed as strings for pickling)
    work_items = [(str(f), compute_hashes, hash_zip_contents, crc_from_zip) for f in files]

    # Map file paths to original index for sorted output
    results: list[DATGame | None] = [None] * total
    completed = 0

    with ProcessPoolExecutor(max_workers=workers) as executor:
        future_to_idx = {
            executor.submit(_scan_file_worker, item): i for i, item in enumerate(work_items)
        }

        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            completed += 1
            try:
                results[idx] = future.result()
            except Exception:
                results[idx] = None

            if progress_callback:
                progress_callback(completed, total, files[idx].name)

    return [g for g in results if g is not None]


def _scan_file(
    file_path: Path,
    *,
    compute_hashes: bool = False,
    hash_zip_contents: bool = False,
    crc_from_zip: bool = False,
) -> DATGame | None:
    """Scan a single file and create a DATGame entry.

    For ZIP files, records the outer ZIP as a single ROM entry
    (matching how Myrient distributes files). If hash_zip_contents
    is True, also records inner file metadata.
    If crc_from_zip is True, extracts CRC32 from the ZIP central
    directory (no file data reading needed).
    """
    try:
        stat = file_path.stat()
    except OSError:
        return None

    game_name = file_path.stem  # Strip extension for game name
    outer_size = stat.st_size

    # Compute hashes of the outer file if requested
    md5 = None
    sha1 = None
    crc = None

    if compute_hashes:
        md5, sha1, crc = _compute_hashes(file_path)

    # For ZIP files, extract CRC from central directory (free operation)
    zip_inner_crc = None
    if crc_from_zip and not compute_hashes and file_path.suffix.lower() == ".zip":
        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                # Get the largest inner file's CRC (the actual ROM)
                entries = [i for i in zf.infolist() if not i.is_dir()]
                if entries:
                    biggest = max(entries, key=lambda x: x.file_size)
                    zip_inner_crc = format(biggest.CRC, "08x")
        except (zipfile.BadZipFile, OSError):
            pass

    # For ZIP files, try to get inner file info
    inner_roms: list[DATRom] = []
    if hash_zip_contents and file_path.suffix.lower() == ".zip":
        inner_roms = _scan_zip_contents(file_path, compute_hashes=compute_hashes)

    if inner_roms:
        # Use inner ROM entries (more useful for matching)
        return DATGame(
            name=game_name,
            roms=inner_roms,
            description=game_name,
            category="Games",
        )
    else:
        # Single ROM entry for the outer file
        rom = DATRom(
            name=file_path.name,
            size=outer_size,
            md5=md5,
            sha1=sha1,
            crc=crc or zip_inner_crc,
        )
        return DATGame(
            name=game_name,
            roms=[rom],
            description=game_name,
            category="Games",
        )


def _scan_zip_contents(
    zip_path: Path,
    *,
    compute_hashes: bool = False,
) -> list[DATRom]:
    """Scan contents of a ZIP file and return ROM entries for inner files."""
    roms: list[DATRom] = []
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue

                crc_hex = format(info.CRC, "08x") if info.CRC else None

                md5 = None
                sha1 = None
                if compute_hashes:
                    data = zf.read(info.filename)
                    md5 = hashlib.md5(data).hexdigest()
                    sha1 = hashlib.sha1(data).hexdigest()

                roms.append(
                    DATRom(
                        name=info.filename,
                        size=info.file_size,
                        crc=crc_hex,
                        md5=md5,
                        sha1=sha1,
                    )
                )
    except (zipfile.BadZipFile, OSError):
        pass

    return roms


def _compute_hashes(file_path: Path) -> tuple[str, str, str]:
    """Compute MD5, SHA1, and CRC32 of a file."""
    import zlib

    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    crc = 0

    with open(file_path, "rb") as f:
        while chunk := f.read(1024 * 1024):  # 1MB chunks
            md5.update(chunk)
            sha1.update(chunk)
            crc = zlib.crc32(chunk, crc)

    crc_hex = format(crc & 0xFFFFFFFF, "08x")
    return md5.hexdigest(), sha1.hexdigest(), crc_hex


def enrich_from_reference(
    games: list[DATGame],
    ref_dat: DATFile,
    *,
    progress_callback=None,
) -> tuple[int, int]:
    """Enrich game entries with metadata from a reference DAT.

    Fuzzy-matches game names and copies over category, description,
    year, manufacturer, and other metadata from the reference.

    Args:
        games: Games to enrich (modified in place)
        ref_dat: Reference DAT to pull metadata from
        progress_callback: Called with (matched, total)

    Returns:
        Tuple of (matched_count, total_count)
    """
    ref_exact, ref_aggressive = _build_reference_index(ref_dat)
    matched = 0
    total = len(games)

    for game in games:
        ref_game = _match_reference(game.name, ref_exact, ref_aggressive)
        if ref_game:
            matched += 1
            # Borrow metadata but keep our ROM entries (our hashes/sizes)
            if ref_game.category:
                game.category = ref_game.category
            if ref_game.description:
                game.description = ref_game.description
            if ref_game.year:
                game.year = ref_game.year
            if ref_game.manufacturer:
                game.manufacturer = ref_game.manufacturer
            if ref_game.cloneof:
                game.cloneof = ref_game.cloneof
            if ref_game.region:
                game.region = ref_game.region

    if progress_callback:
        progress_callback(matched, total)

    return matched, total


def write_dat_xml(
    games: list[DATGame],
    output_path: Path,
    *,
    dat_name: str,
    description: str | None = None,
    version: str | None = None,
    author: str = "rom-farmer (generated)",
    homepage: str = "https://github.com/rom-farmer",
) -> Path:
    """Write games to a Logiqx XML DAT file.

    Args:
        games: Game entries to write
        output_path: Output .dat file path
        dat_name: Name for the DAT header
        description: Description (defaults to name + game count)
        version: Version string (defaults to current timestamp)
        author: Author string
        homepage: Homepage URL

    Returns:
        Path to the written file
    """
    if version is None:
        version = datetime.now().strftime("%Y-%m-%d %H-%M-%S")

    if description is None:
        description = f"{dat_name} ({len(games)}) ({version})"

    # Build XML
    root = ET.Element("datafile")

    # Header
    header = ET.SubElement(root, "header")
    ET.SubElement(header, "name").text = dat_name
    ET.SubElement(header, "description").text = description
    ET.SubElement(header, "version").text = version
    ET.SubElement(header, "author").text = author
    ET.SubElement(header, "homepage").text = homepage
    ET.SubElement(header, "url").text = homepage

    # Games
    for game in sorted(games, key=lambda g: g.name.lower()):
        game_elem = ET.SubElement(root, "game", name=game.name)

        if game.category:
            ET.SubElement(game_elem, "category").text = game.category
        ET.SubElement(game_elem, "description").text = game.description or game.name

        if game.year:
            ET.SubElement(game_elem, "year").text = game.year
        if game.manufacturer:
            ET.SubElement(game_elem, "manufacturer").text = game.manufacturer
        if game.cloneof:
            game_elem.set("cloneof", game.cloneof)

        for rom in game.roms:
            rom_attrs = {
                "name": rom.name,
                "size": str(rom.size),
            }
            if rom.crc:
                rom_attrs["crc"] = rom.crc
            if rom.md5:
                rom_attrs["md5"] = rom.md5
            if rom.sha1:
                rom_attrs["sha1"] = rom.sha1
            if rom.sha256:
                rom_attrs["sha256"] = rom.sha256

            ET.SubElement(game_elem, "rom", **rom_attrs)

    # Write with pretty-printing
    xml_str = ET.tostring(root, encoding="unicode")
    pretty = minidom.parseString(xml_str).toprettyxml(indent="\t", encoding=None)

    # Remove extra XML declaration that minidom adds (we add our own)
    lines = pretty.split("\n")
    if lines[0].startswith("<?xml"):
        lines = lines[1:]
    content = "\n".join(lines)

    # Write with proper XML declaration and DOCTYPE
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0"?>\n')
        f.write(
            '<!DOCTYPE datafile PUBLIC "-//Logiqx//DTD ROM Management Datafile//EN" '
            '"http://www.logiqx.com/Dats/datafile.dtd">\n'
        )
        f.write(content)

    return output_path
