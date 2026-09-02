#!/usr/bin/env python3
"""Fetch and save Batocera wiki system documentation pages.

This script downloads system documentation from the Batocera wiki
using the raw export endpoint and saves them as markdown files.

Usage:
    python3 scripts/fetch_batocera_docs.py [--system SYSTEM] [--all]

Examples:
    python3 scripts/fetch_batocera_docs.py              # Fetch ROM Farmer platforms
    python3 scripts/fetch_batocera_docs.py --all        # Fetch ALL Batocera systems
    python3 scripts/fetch_batocera_docs.py --system xbox  # Fetch just xbox
"""

import argparse
import re
import urllib.request
from datetime import datetime
from pathlib import Path

# All Batocera systems (from https://wiki.batocera.org/systems)
# Format: batocera_wiki_name -> our_filename (usually same)
ALL_BATOCERA_SYSTEMS = {
    # === ARCADE ===
    "mame": "mame",
    "fbneo": "fbneo",
    "dice": "dice",
    "daphne": "daphne",
    "singe": "singe",
    "model2": "model2",
    "model3": "model3",
    "naomi": "naomi",
    "naomi2": "naomi2",
    "namco2x6": "namco2x6",
    "triforce": "triforce",
    "atomiswave": "atomiswave",
    "lindbergh": "lindbergh",
    # === HOME CONSOLES - 1st/2nd Gen ===
    "channelf": "channelf",
    "atari2600": "atari2600",
    "odyssey2": "odyssey2",
    "astrocde": "astrocde",
    "apfm1000": "apfm1000",
    "vc4000": "vc4000",
    "intellivision": "intellivision",
    "atari5200": "atari5200",
    "colecovision": "colecovision",
    "advision": "advision",
    "vectrex": "vectrex",
    "crvision": "crvision",
    "arcadia": "arcadia",
    # === HOME CONSOLES - 3rd Gen (8-bit) ===
    "nes": "nes",
    "sg1000": "sg1000",
    "multivision": "multivision",
    "videopacplus": "videopacplus",
    "pv1000": "pv1000",
    "scv": "scv",
    "mastersystem": "mastersystem",
    "fds": "fds",
    "atari7800": "atari7800",
    "socrates": "socrates",
    # === HOME CONSOLES - 4th Gen (16-bit) ===
    "pcengine": "pcengine",
    "megadrive": "megadrive",
    "pcecd": "pcecd",
    "supergrafx": "supergrafx",
    "snes": "snes",
    "neogeo": "neogeo",
    "cdi": "cdi",
    "amigacdtv": "amigacdtv",
    "gx4000": "gx4000",
    "segacd": "segacd",
    "snes-msu1": "snes-msu1",
    "pico": "pico",
    "sgb": "sgb",
    "supracan": "supracan",
    "msu-md": "msu-md",
    # === HOME CONSOLES - 5th Gen (32-bit/3D) ===
    "jaguar": "jaguar",
    "3do": "3do",
    "amigacd32": "amigacd32",
    "sega32x": "sega32x",
    "psx": "psx",
    "pcfx": "pcfx",
    "neogeocd": "neogeocd",
    "saturn": "saturn",
    "virtualboy": "virtualboy",
    "satellaview": "satellaview",
    "jaguarcd": "jaguarcd",
    "sufami": "sufami",
    "n64": "n64",
    # === HOME CONSOLES - 6th Gen ===
    "dreamcast": "dreamcast",
    "n64dd": "n64dd",
    "ps2": "ps2",
    "gc": "gc",
    "xbox": "xbox",
    "vsmile": "vsmile",
    # === HOME CONSOLES - 7th Gen (HD) ===
    "xbox360": "xbox360",
    "wii": "wii",
    "ps3": "ps3",
    # === HOME CONSOLES - 8th Gen ===
    "wiiu": "wiiu",
    "ps4": "ps4",
    # === FANTASY CONSOLES ===
    "uzebox": "uzebox",
    "voxatron": "voxatron",
    "pico8": "pico8",
    "tic80": "tic80",
    "lowresnx": "lowresnx",
    "wasm4": "wasm4",
    "pyxel": "pyxel",
    "vircon32": "vircon32",
    # === PORTABLE - LCD/Early ===
    "gameandwatch": "gameandwatch",
    "lcdgames": "lcdgames",
    "gamepock": "gamepock",
    # === PORTABLE - 4th Gen ===
    "gb": "gb",
    "gb2players": "gb2players",
    "lynx": "lynx",
    "gamegear": "gamegear",
    "gamate": "gamate",
    "gmaster": "gmaster",
    "supervision": "supervision",
    "megaduck": "megaduck",
    # === PORTABLE - 5th Gen ===
    "gamecom": "gamecom",
    "gbc": "gbc",
    "gbc2players": "gbc2players",
    "ngp": "ngp",
    "ngpc": "ngpc",
    "wswan": "wswan",
    "wswanc": "wswanc",
    # === PORTABLE - 6th Gen ===
    "gba": "gba",
    "pokemini": "pokemini",
    "gp32": "gp32",
    # === PORTABLE - 7th Gen ===
    "nds": "nds",
    "psp": "psp",
    # === PORTABLE - 8th Gen ===
    "3ds": "3ds",
    "psvita": "psvita",
    # === PORTABLE - Fantasy ===
    "arduboy": "arduboy",
    # === HOME COMPUTERS ===
    "pdp1": "pdp1",
    "apple2": "apple2",
    "pet": "pet",
    "atari800": "atari800",
    "atom": "atom",
    "ti99": "ti99",
    "c20": "c20",
    "coco": "coco",
    "pc88": "pc88",
    "zx81": "zx81",
    "bbc": "bbc",
    "x1": "x1",
    "zxspectrum": "zxspectrum",
    "c64": "c64",
    "pc98": "pc98",
    "fm7": "fm7",
    "tutor": "tutor",
    "electron": "electron",
    "camplynx": "camplynx",
    "msx1": "msx1",
    "adam": "adam",
    "spectravideo": "spectravideo",
    "amstradcpc": "amstradcpc",
    "macintosh": "macintosh",
    "thomson": "thomson",
    "cplus4": "cplus4",
    "laser310": "laser310",
    "oricatmos": "oricatmos",
    "atarist": "atarist",
    "msx2": "msx2",
    "c128": "c128",
    "apple2gs": "apple2gs",
    "archimedes": "archimedes",
    "xegs": "xegs",
    "amiga500": "amiga500",
    "x68000": "x68000",
    "msx2+": "msx2plus",
    "fmtowns": "fmtowns",
    "samcoupe": "samcoupe",
    "amiga1200": "amiga1200",
    "vis": "vis",
    "msxturbor": "msxturbor",
    "commanderx16": "commanderx16",
    # === MISCELLANEOUS ===
    "dos": "dos",
    "flash": "flash",
    "scummvm": "scummvm",
    "easyrpg": "easyrpg",
    "openbor": "openbor",
    "solarus": "solarus",
    "ikemen": "ikemen",
    "mugen": "mugen",
}

# Map our ROM Farmer platform names to Batocera wiki system names
# (subset of ALL_BATOCERA_SYSTEMS that we actively support)
ROMFARMER_PLATFORMS = {
    # Cartridge systems - No-Intro
    "nes": "nes",
    "snes": "snes",
    "n64": "n64",
    "gb": "gb",
    "gbc": "gbc",
    "gba": "gba",
    "nds": "nds",
    "3ds": "3ds",
    "virtualboy": "virtualboy",
    "megadrive": "megadrive",
    "mastersystem": "mastersystem",
    "gamegear": "gamegear",
    "sg1000": "sg1000",
    "sega32x": "sega32x",
    "atari2600": "atari2600",
    "atari5200": "atari5200",
    "atari7800": "atari7800",
    "atarilynx": "lynx",
    "atarijaguar": "jaguar",
    "colecovision": "colecovision",
    "intellivision": "intellivision",
    "ngp": "ngp",
    "ngpc": "ngpc",
    "wonderswan": "wswan",
    "wonderswancolor": "wswanc",
    "pcengine": "pcengine",
    "vectrex": "vectrex",
    # Disc-based systems - Redump
    "3do": "3do",
    "saturn": "saturn",
    "dreamcast": "dreamcast",
    "psx": "psx",
    "ps2": "ps2",
    "ps3": "ps3",
    "psp": "psp",
    "megacd": "segacd",
    "pcenginecd": "pcecd",
    "gamecube": "gc",
    "wii": "wii",
    "wiiu": "wiiu",
    "xbox": "xbox",
    "xbox360": "xbox360",
}


def fetch_wiki_raw(system: str) -> str:
    """Fetch raw DokuWiki markup for a system.

    Args:
        system: Batocera wiki system name (e.g., 'xbox', 'saturn')

    Returns:
        Raw DokuWiki markup content
    """
    # Use raw export endpoint for clean content
    url = f"https://wiki.batocera.org/_export/raw/systems:{system}"

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; RomFarmer/2.0; +https://github.com/romfarmer)",
        "Accept": "text/plain",
    }

    request = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8")
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return ""


def dokuwiki_to_markdown(content: str, system: str) -> str:
    """Convert DokuWiki markup to Markdown.

    Args:
        content: Raw DokuWiki content
        system: System name for metadata

    Returns:
        Markdown formatted content
    """
    # Extract title from first heading
    title_match = re.search(r"^====+\s*(.+?)\s*====+", content, re.MULTILINE)
    title = title_match.group(1) if title_match else system.title()

    # Convert DokuWiki headings to Markdown
    # DokuWiki: ====== H1 ======
    # Markdown: # H1
    content = re.sub(r"^======\s*(.+?)\s*======\s*$", r"# \1", content, flags=re.MULTILINE)
    content = re.sub(r"^=====\s*(.+?)\s*=====\s*$", r"## \1", content, flags=re.MULTILINE)
    content = re.sub(r"^====\s*(.+?)\s*====\s*$", r"### \1", content, flags=re.MULTILINE)
    content = re.sub(r"^===\s*(.+?)\s*===\s*$", r"#### \1", content, flags=re.MULTILINE)
    content = re.sub(r"^==\s*(.+?)\s*==\s*$", r"##### \1", content, flags=re.MULTILINE)

    # Convert italic (DokuWiki uses //)
    content = re.sub(r"//(.+?)//", r"*\1*", content)

    # Convert links [[url|text]] -> [text](url)
    content = re.sub(r"\[\[([^|\]]+)\|([^\]]+)\]\]", r"[\2](\1)", content)
    content = re.sub(r"\[\[([^\]]+)\]\]", r"[\1](\1)", content)

    # Convert code blocks
    content = re.sub(r"<code[^>]*>(.*?)</code>", r"```\n\1\n```", content, flags=re.DOTALL)
    content = re.sub(r"<file[^>]*>(.*?)</file>", r"```\n\1\n```", content, flags=re.DOTALL)
    content = re.sub(r"''(.+?)''", r"`\1`", content)  # Inline code

    # Convert lists
    # DokuWiki uses "  * item" for bullets, "  - item" for numbered (sort of)
    content = re.sub(r"^\s{2}\*\s+", "- ", content, flags=re.MULTILINE)
    content = re.sub(r"^\s{4}\*\s+", "  - ", content, flags=re.MULTILINE)
    content = re.sub(r"^\s{6}\*\s+", "    - ", content, flags=re.MULTILINE)

    # Convert tables - DokuWiki uses ^ for headers, | for data
    content = re.sub(r"\^", "|", content)

    # Remove WRAP tags (DokuWiki layout)
    content = re.sub(r"<WRAP[^>]*>", "", content)
    content = re.sub(r"</WRAP>", "", content)

    # Remove image syntax ({{ url }})
    content = re.sub(r"\{\{\s*[^}]+\s*\}\}", "", content)

    # Clean up extra whitespace
    content = re.sub(r"\n{3,}", "\n\n", content)
    content = content.strip()

    # Add header with metadata
    header = f"""# {title}

**Source:** https://wiki.batocera.org/systems:{system}
**Last fetched:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

"""
    return header + content


def save_system_doc(system: str, our_name: str, output_dir: Path) -> bool:
    """Fetch and save documentation for a system.

    Args:
        system: Batocera wiki system name
        our_name: Our platform name (for filename)
        output_dir: Output directory

    Returns:
        True if successful
    """
    print(f"  Fetching {system}...")

    content = fetch_wiki_raw(system)
    if not content:
        print(f"    Failed to fetch {system}")
        return False

    markdown = dokuwiki_to_markdown(content, system)

    output_file = output_dir / f"{our_name}.md"
    output_file.write_text(markdown)

    print(f"    Saved to {output_file.name}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Fetch Batocera wiki documentation")
    parser.add_argument("--system", "-s", help="Fetch just one system")
    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Fetch ALL Batocera systems (not just ROM Farmer platforms)",
    )
    parser.add_argument("--output", "-o", default="docs/systems/batocera", help="Output directory")
    args = parser.parse_args()

    # Get project root (assuming script is in scripts/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    if args.output.startswith("/"):
        output_dir = Path(args.output)
    else:
        output_dir = project_root / args.output

    output_dir.mkdir(parents=True, exist_ok=True)

    if args.system:
        # Fetch single system
        wiki_name = ALL_BATOCERA_SYSTEMS.get(args.system, args.system)
        save_system_doc(wiki_name, args.system, output_dir)
    elif args.all:
        # Fetch ALL Batocera systems
        print(f"Fetching ALL {len(ALL_BATOCERA_SYSTEMS)} Batocera system docs...")
        print(f"Output directory: {output_dir}")

        success = 0
        failed = 0

        for wiki_name, our_name in sorted(ALL_BATOCERA_SYSTEMS.items()):
            if save_system_doc(wiki_name, our_name, output_dir):
                success += 1
            else:
                failed += 1

        print(f"\nComplete: {success} succeeded, {failed} failed")
    else:
        # Fetch ROM Farmer platforms only
        print(f"Fetching {len(ROMFARMER_PLATFORMS)} ROM Farmer platform docs...")
        print(f"(Use --all to fetch all {len(ALL_BATOCERA_SYSTEMS)} Batocera systems)")
        print(f"Output directory: {output_dir}")

        success = 0
        failed = 0

        for our_name, wiki_name in sorted(ROMFARMER_PLATFORMS.items()):
            if save_system_doc(wiki_name, our_name, output_dir):
                success += 1
            else:
                failed += 1

        print(f"\nComplete: {success} succeeded, {failed} failed")


if __name__ == "__main__":
    main()
