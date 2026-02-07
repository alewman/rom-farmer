"""
DAT file parser for No-Intro, Redump, FBNeo, and MAME DAT files.

Extracts:
- Parent-clone relationships (cloneof/romof)
- Year, manufacturer
- Source file (hardware driver)
- Video specs (resolution, orientation)
- Driver status (emulation quality)
- Comments (bootleg, prototype, etc.)
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Iterator
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class VideoSpec:
    """Video hardware specifications."""
    type: str = "raster"  # raster or vector
    orientation: str = "horizontal"  # horizontal or vertical
    width: int = 0
    height: int = 0
    aspect_x: int = 4
    aspect_y: int = 3
    refresh: float = 60.0

    @property
    def resolution(self) -> str:
        if self.width and self.height:
            return f"{self.width}x{self.height}"
        return ""

    @property
    def aspect_ratio(self) -> str:
        return f"{self.aspect_x}:{self.aspect_y}"


@dataclass
class DatGame:
    """Represents a game entry from a DAT file."""
    name: str  # ROM name (e.g., "sf2ce")
    description: str  # Full title (e.g., "Street Fighter II': Champion Edition")
    year: Optional[str] = None
    manufacturer: Optional[str] = None
    
    # Parent-clone relationships
    cloneof: Optional[str] = None  # Parent game name
    romof: Optional[str] = None  # ROM parent (for merged sets)
    sampleof: Optional[str] = None  # Sample parent
    
    # Hardware/driver info
    sourcefile: Optional[str] = None  # Driver source (e.g., "capcom/d_cps1.cpp")
    driver_status: str = "good"  # good, imperfect, preliminary
    
    # Video specs
    video: Optional[VideoSpec] = None
    
    # Metadata
    comment: Optional[str] = None  # Bootleg, Prototype, etc.
    category: Optional[str] = None
    
    # ROM hashes (first ROM only for identification)
    rom_name: Optional[str] = None
    rom_crc: Optional[str] = None
    rom_size: Optional[int] = None
    
    # Source DAT info
    dat_name: Optional[str] = None
    dat_type: Optional[str] = None  # fbneo, mame, nointro, redump

    @property
    def hardware(self) -> Optional[str]:
        """Extract hardware name from sourcefile."""
        if not self.sourcefile:
            return None
        # capcom/d_cps1.cpp -> cps1
        # sega/d_megadrive.cpp -> megadrive
        match = re.search(r'd_(\w+)\.cpp', self.sourcefile)
        if match:
            return match.group(1)
        # Also try without d_ prefix
        match = re.search(r'/(\w+)\.cpp', self.sourcefile)
        if match:
            return match.group(1)
        return self.sourcefile

    @property
    def hardware_family(self) -> Optional[str]:
        """Extract hardware family from sourcefile path."""
        if not self.sourcefile:
            return None
        # capcom/d_cps1.cpp -> capcom
        parts = self.sourcefile.split('/')
        if len(parts) >= 2:
            return parts[0]
        return None

    @property
    def is_clone(self) -> bool:
        return self.cloneof is not None

    @property
    def is_bootleg(self) -> bool:
        if self.comment and 'bootleg' in self.comment.lower():
            return True
        if self.description and 'bootleg' in self.description.lower():
            return True
        return False

    @property
    def is_prototype(self) -> bool:
        if self.comment and 'proto' in self.comment.lower():
            return True
        if self.description and 'proto' in self.description.lower():
            return True
        return False


class DatParser:
    """Parser for various DAT file formats."""
    
    def __init__(self, dat_path: Path):
        self.dat_path = Path(dat_path)
        self.dat_name: Optional[str] = None
        self.dat_description: Optional[str] = None
        self.dat_version: Optional[str] = None
        self.dat_type: Optional[str] = None

    def _detect_dat_type(self, root: ET.Element) -> str:
        """Detect DAT type from content."""
        header = root.find('header')
        if header is not None:
            name = header.findtext('name', '').lower()
            if 'fbneo' in name or 'finalburn' in name:
                return 'fbneo'
            elif 'mame' in name:
                return 'mame'
            elif 'no-intro' in name or 'nointro' in name:
                return 'nointro'
            elif 'redump' in name:
                return 'redump'
        
        # Check for machine vs game elements (MAME uses machine)
        if root.find('machine') is not None:
            return 'mame'
        
        return 'unknown'

    def _parse_header(self, root: ET.Element) -> None:
        """Parse DAT header information."""
        header = root.find('header')
        if header is not None:
            self.dat_name = header.findtext('name')
            self.dat_description = header.findtext('description')
            self.dat_version = header.findtext('version')
        self.dat_type = self._detect_dat_type(root)

    def _parse_video(self, game_elem: ET.Element) -> Optional[VideoSpec]:
        """Parse video element."""
        video_elem = game_elem.find('video')
        if video_elem is None:
            return None
        
        video = VideoSpec()
        video.type = video_elem.get('type', 'raster')
        video.orientation = video_elem.get('orientation', 'horizontal')
        
        width = video_elem.get('width')
        if width:
            video.width = int(width)
        
        height = video_elem.get('height')
        if height:
            video.height = int(height)
        
        aspect_x = video_elem.get('aspectx')
        if aspect_x:
            video.aspect_x = int(aspect_x)
        
        aspect_y = video_elem.get('aspecty')
        if aspect_y:
            video.aspect_y = int(aspect_y)
        
        refresh = video_elem.get('refresh')
        if refresh:
            video.refresh = float(refresh)
        
        return video

    def _parse_game(self, game_elem: ET.Element) -> DatGame:
        """Parse a single game/machine element."""
        # Get basic attributes
        name = game_elem.get('name', '')
        
        game = DatGame(
            name=name,
            description=game_elem.findtext('description', name),
            year=game_elem.findtext('year'),
            manufacturer=game_elem.findtext('manufacturer'),
            cloneof=game_elem.get('cloneof'),
            romof=game_elem.get('romof'),
            sampleof=game_elem.get('sampleof'),
            sourcefile=game_elem.get('sourcefile'),
            comment=game_elem.findtext('comment'),
            category=game_elem.findtext('category'),
            dat_name=self.dat_name,
            dat_type=self.dat_type,
        )
        
        # Parse video specs
        game.video = self._parse_video(game_elem)
        
        # Parse driver status
        driver_elem = game_elem.find('driver')
        if driver_elem is not None:
            game.driver_status = driver_elem.get('status', 'good')
        
        # Get first ROM for identification
        rom_elem = game_elem.find('rom')
        if rom_elem is not None:
            game.rom_name = rom_elem.get('name')
            game.rom_crc = rom_elem.get('crc')
            size = rom_elem.get('size')
            if size:
                game.rom_size = int(size)
        
        return game

    def parse(self) -> Iterator[DatGame]:
        """Parse DAT file and yield game entries."""
        logger.info(f"Parsing DAT file: {self.dat_path}")
        
        try:
            tree = ET.parse(self.dat_path)
            root = tree.getroot()
        except ET.ParseError as e:
            logger.error(f"Failed to parse DAT file: {e}")
            return
        
        self._parse_header(root)
        logger.info(f"DAT: {self.dat_name} ({self.dat_type}), version: {self.dat_version}")
        
        # Find all game/machine elements
        game_tag = 'machine' if self.dat_type == 'mame' else 'game'
        
        count = 0
        for game_elem in root.findall(game_tag):
            yield self._parse_game(game_elem)
            count += 1
        
        logger.info(f"Parsed {count} games from {self.dat_path.name}")

    def parse_all(self) -> list[DatGame]:
        """Parse DAT file and return all games as a list."""
        return list(self.parse())


def get_hardware_games(dat_path: Path, hardware: str) -> list[DatGame]:
    """Get all games for a specific hardware/driver."""
    parser = DatParser(dat_path)
    games = []
    
    hardware_lower = hardware.lower()
    
    for game in parser.parse():
        if game.hardware and hardware_lower in game.hardware.lower():
            games.append(game)
        elif game.sourcefile and hardware_lower in game.sourcefile.lower():
            games.append(game)
    
    return games


def get_game_variants(dat_path: Path, game_name: str) -> dict:
    """Get a game and all its variants/clones."""
    parser = DatParser(dat_path)
    all_games = {g.name: g for g in parser.parse()}
    
    # Find the target game
    target = all_games.get(game_name)
    if not target:
        # Try to find by partial match
        for name, game in all_games.items():
            if game_name.lower() in name.lower():
                target = game
                break
    
    if not target:
        return {"parent": None, "clones": []}
    
    # Find the root parent
    parent = target
    while parent.cloneof and parent.cloneof in all_games:
        parent = all_games[parent.cloneof]
    
    # Find all clones of the parent
    clones = [g for g in all_games.values() if g.cloneof == parent.name]
    
    return {
        "parent": parent,
        "clones": sorted(clones, key=lambda g: g.name),
        "target": target,
    }


# Quick test
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python dat_parser.py <dat_file> [hardware|game_name]")
        sys.exit(1)
    
    dat_path = Path(sys.argv[1])
    
    if len(sys.argv) >= 3:
        query = sys.argv[2]
        
        # Try hardware search first
        games = get_hardware_games(dat_path, query)
        if games:
            print(f"\n=== {query.upper()} Games ({len(games)}) ===\n")
            for g in sorted(games, key=lambda x: x.description):
                status = f"[{g.driver_status}]" if g.driver_status != "good" else ""
                clone = f" (clone of {g.cloneof})" if g.cloneof else ""
                print(f"  {g.name}: {g.description}{clone} {status}")
        else:
            # Try game variant search
            result = get_game_variants(dat_path, query)
            if result["parent"]:
                p = result["parent"]
                print(f"\n=== {p.description} ({p.name}) ===")
                print(f"Year: {p.year}")
                print(f"Manufacturer: {p.manufacturer}")
                print(f"Hardware: {p.hardware}")
                if p.video:
                    print(f"Video: {p.video.resolution} {p.video.orientation}")
                print(f"\nClones ({len(result['clones'])}):")
                for c in result["clones"]:
                    print(f"  - {c.name}: {c.description}")
    else:
        # Just parse and show stats
        parser = DatParser(dat_path)
        games = parser.parse_all()
        
        print(f"\nDAT: {parser.dat_name}")
        print(f"Type: {parser.dat_type}")
        print(f"Total games: {len(games)}")
        print(f"Parents: {len([g for g in games if not g.cloneof])}")
        print(f"Clones: {len([g for g in games if g.cloneof])}")
        
        # Hardware breakdown
        hw_counts = {}
        for g in games:
            hw = g.hardware or "unknown"
            hw_counts[hw] = hw_counts.get(hw, 0) + 1
        
        print(f"\nTop hardware:")
        for hw, count in sorted(hw_counts.items(), key=lambda x: -x[1])[:20]:
            print(f"  {hw}: {count}")
