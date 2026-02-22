"""AI-powered game curation engine.

The AICurator generates intelligent, ranked game lists for ROM Farmer builds.
It operates in multiple modes:

1. **Knowledge-based**: Uses pre-defined rankings from gaming expertise
   (critical consensus, historical importance, genre diversity).
   This is what the agent generates when creating curated lists.

2. **Metadata-enriched**: Combines knowledge rankings with the scraped_games
   database (ratings, genres, descriptions) to validate and extend rankings.

3. **Embedding-powered** (future): Uses sentence-transformers to cluster
   games by similarity, find hidden gems, and match cross-platform titles.

4. **LLM-live** (future): Queries a language model during build decisions
   via Copilot SDK / API integration.

Output format: YAML curated lists that integrate directly with ROM Farmer's
ApplyListsStage and SelectionFilter pipeline stages.
"""

from __future__ import annotations

import enum
import json
import logging
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tier system
# ---------------------------------------------------------------------------

class GameTier(str, enum.Enum):
    """Quality tiers for curated games.
    
    Each tier represents a curatorial judgment, not just a rating threshold.
    A tier-1 game is a game that DEFINES its platform — everyone should play it.
    A tier-4 game is still good, but you'd only include it in a large collection.
    """
    
    ESSENTIAL = "essential"      # Tier 1: Defines the platform. Must-play. (~5-15 per platform)
    EXCELLENT = "excellent"      # Tier 2: Outstanding games. (~15-50 per platform)
    GREAT = "great"              # Tier 3: Very good games. (~50-150 per platform)
    NOTABLE = "notable"          # Tier 4: Good games worth including. (~150-500)
    COMPLETE = "complete"        # Tier 5: The rest of the 1G1R set. Everything else.
    
    @property
    def rank(self) -> int:
        """Numeric rank (lower = better). Essential=1, Complete=5."""
        return list(GameTier).index(self) + 1
    
    @property
    def label(self) -> str:
        """Human-friendly label with tier number."""
        return f"Tier {self.rank}: {self.value.title()}"


@dataclass
class CuratedGame:
    """A game with its curatorial assessment.
    
    Attributes:
        name: Game name as it appears in ROM filenames (No-Intro/Redump style)
        tier: Quality tier assignment
        score: Numeric score 0-100 for ordering within a tier
        tags: Curatorial tags (hidden-gem, genre-defining, japan-exclusive, etc.)
        note: Brief curatorial note explaining the ranking
        genre: Game genre (from metadata or knowledge)
        year: Release year
        players: Player count info
        cross_platform: True if this game exists on other platforms in same gen
        best_platform: The single best platform to play this game on
    """
    
    name: str
    tier: GameTier = GameTier.COMPLETE
    score: int = 50
    tags: list[str] = field(default_factory=list)
    note: str = ""
    genre: str = ""
    year: str = ""
    players: str = ""
    cross_platform: bool = False
    best_platform: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize for YAML output."""
        d: dict[str, Any] = {"name": self.name, "tier": self.tier.value, "score": self.score}
        if self.tags:
            d["tags"] = self.tags
        if self.note:
            d["note"] = self.note
        if self.genre:
            d["genre"] = self.genre
        if self.year:
            d["year"] = self.year
        if self.cross_platform:
            d["cross_platform"] = True
            if self.best_platform:
                d["best_platform"] = self.best_platform
        return d
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CuratedGame:
        """Deserialize from YAML."""
        return cls(
            name=data["name"],
            tier=GameTier(data.get("tier", "complete")),
            score=data.get("score", 50),
            tags=data.get("tags", []),
            note=data.get("note", ""),
            genre=data.get("genre", ""),
            year=data.get("year", ""),
            players=data.get("players", ""),
            cross_platform=data.get("cross_platform", False),
            best_platform=data.get("best_platform", ""),
        )


@dataclass
class PlatformCuration:
    """Complete curated ranking for a platform.
    
    Attributes:
        platform: Platform identifier (psx, ps2, saturn, etc.)
        version: Curation version (bumped when re-generated)
        curator: Who/what generated this curation
        games: All ranked games for this platform
        generation: Console generation identifier
        total_available: Total games in the 1G1R set for this platform
        metadata: Additional curation metadata
    """
    
    platform: str
    version: str = "1.0.0"
    curator: str = "ai-frontier"
    games: list[CuratedGame] = field(default_factory=list)
    generation: str = ""
    total_available: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # --- Tier queries ---
    
    def by_tier(self, tier: GameTier) -> list[CuratedGame]:
        """Get games at a specific tier."""
        return [g for g in self.games if g.tier == tier]
    
    def up_to_tier(self, tier: GameTier) -> list[CuratedGame]:
        """Get games at or above a tier (Essential through the given tier)."""
        return [g for g in self.games if g.tier.rank <= tier.rank]
    
    def essentials(self) -> list[CuratedGame]:
        return self.by_tier(GameTier.ESSENTIAL)
    
    def top_n(self, n: int) -> list[CuratedGame]:
        """Get top N games across all tiers, by score descending."""
        return sorted(self.games, key=lambda g: (-g.tier.rank * -1, -g.score))[:n]
    
    # --- List generation ---
    
    def to_include_list(self, max_tier: GameTier = GameTier.GREAT) -> list[str]:
        """Generate a ROM Farmer include list (just filenames).
        
        This output format is directly consumable by ApplyListsStage.
        One filename per line, no extensions (matched via fuzzy/stem).
        """
        games = self.up_to_tier(max_tier)
        games.sort(key=lambda g: (-g.score, g.name))
        return [g.name for g in games]
    
    def to_rom_farmer_list(
        self,
        max_tier: GameTier = GameTier.GREAT,
        header_comment: bool = True,
    ) -> str:
        """Generate a ROM Farmer list file compatible with ApplyListsStage.
        
        Format: One filename per line, # comments for documentation.
        """
        lines = []
        
        if header_comment:
            lines.append(f"# AI-Curated {self.platform.upper()} Games")
            lines.append(f"# Curator: {self.curator} v{self.version}")
            tier_label = max_tier.label
            count = len(self.up_to_tier(max_tier))
            lines.append(f"# Tier: {tier_label} ({count} games)")
            lines.append(f"# Total available: {self.total_available}")
            lines.append("")
        
        current_tier = None
        for game in sorted(self.up_to_tier(max_tier), key=lambda g: (g.tier.rank, -g.score)):
            if game.tier != current_tier:
                current_tier = game.tier
                if lines and lines[-1] != "":
                    lines.append("")
                lines.append(f"# === {current_tier.label} ===")
            
            lines.append(game.name)
        
        return "\n".join(lines) + "\n"
    
    # --- Serialization ---
    
    def to_yaml(self) -> str:
        """Serialize to YAML for storage."""
        data = {
            "platform": self.platform,
            "version": self.version,
            "curator": self.curator,
            "generation": self.generation,
            "total_available": self.total_available,
            "metadata": self.metadata,
            "tiers": {
                tier.value: {
                    "count": len(self.by_tier(tier)),
                    "games": [g.to_dict() for g in sorted(
                        self.by_tier(tier), key=lambda g: -g.score
                    )],
                }
                for tier in GameTier
                if self.by_tier(tier)
            },
        }
        return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    @classmethod
    def from_yaml(cls, yaml_str: str) -> PlatformCuration:
        """Deserialize from YAML."""
        data = yaml.safe_load(yaml_str)
        games = []
        for tier_name, tier_data in data.get("tiers", {}).items():
            for game_data in tier_data.get("games", []):
                games.append(CuratedGame.from_dict(game_data))
        
        return cls(
            platform=data["platform"],
            version=data.get("version", "1.0.0"),
            curator=data.get("curator", "unknown"),
            games=games,
            generation=data.get("generation", ""),
            total_available=data.get("total_available", 0),
            metadata=data.get("metadata", {}),
        )
    
    def save(self, directory: Path) -> Path:
        """Save curation to a YAML file.
        
        Args:
            directory: Directory to save in
            
        Returns:
            Path to saved file
        """
        directory.mkdir(parents=True, exist_ok=True)
        filepath = directory / f"{self.platform}.yaml"
        filepath.write_text(self.to_yaml())
        logger.info(f"Saved {self.platform} curation: {len(self.games)} games to {filepath}")
        return filepath
    
    @classmethod
    def load(cls, filepath: Path) -> PlatformCuration:
        """Load curation from a YAML file."""
        return cls.from_yaml(filepath.read_text())


# ---------------------------------------------------------------------------
# AI Curator
# ---------------------------------------------------------------------------

class AICurator:
    """Main curator engine.
    
    The curator combines multiple data sources to produce intelligent
    game rankings:
    
    1. Agent knowledge (curated lists generated by the AI agent)
    2. Metadata database (scraped_games: ratings, genres, descriptions)
    3. Cross-platform data (generation configs for 1R1G dedup)
    
    Future:
    4. Embeddings (sentence-transformers for similarity/clustering)
    5. Live LLM queries (Copilot SDK for build-time decisions)
    """
    
    def __init__(
        self,
        metadata_db: Optional[Path] = None,
        curations_dir: Optional[Path] = None,
        workspace_root: Optional[Path] = None,
    ):
        """Initialize the curator.
        
        Args:
            metadata_db: Path to romfarmer.db with scraped_games
            curations_dir: Directory for saved curations
            workspace_root: ROM Farmer workspace root
        """
        self.workspace_root = workspace_root or Path("/data/emu/rom-farmer")
        self.metadata_db = metadata_db or self.workspace_root / "metadata" / "database" / "romfarmer.db"
        self.curations_dir = curations_dir or self.workspace_root / "config" / "curations"
        self._db: Optional[sqlite3.Connection] = None
    
    @property
    def db(self) -> sqlite3.Connection:
        """Lazy database connection."""
        if self._db is None:
            if not self.metadata_db.exists():
                raise FileNotFoundError(f"Metadata DB not found: {self.metadata_db}")
            self._db = sqlite3.connect(str(self.metadata_db))
            self._db.row_factory = sqlite3.Row
        return self._db
    
    def close(self) -> None:
        """Close database connection."""
        if self._db:
            self._db.close()
            self._db = None
    
    # --- Metadata queries ---
    
    def get_platform_games(self, platform: str) -> list[dict[str, Any]]:
        """Get all games for a platform from the metadata DB.
        
        Returns list of dicts with: name, rating, genre, developer,
        publisher, description, players, release_date, region.
        """
        cursor = self.db.execute(
            """SELECT DISTINCT name, rating, genre, developer, publisher,
                      description, players, release_date, region
               FROM scraped_games 
               WHERE system = ?
               ORDER BY rating DESC, name ASC""",
            (platform,),
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def get_platform_stats(self, platform: str) -> dict[str, Any]:
        """Get statistical summary for a platform."""
        cursor = self.db.execute(
            """SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN rating > 0 THEN 1 ELSE 0 END) as has_rating,
                AVG(CASE WHEN rating > 0 THEN rating END) as avg_rating,
                MAX(rating) as max_rating,
                COUNT(DISTINCT genre) as genre_count,
                SUM(CASE WHEN description IS NOT NULL AND description != '' THEN 1 ELSE 0 END) as has_desc
               FROM scraped_games WHERE system = ?""",
            (platform,),
        )
        row = cursor.fetchone()
        return dict(row) if row else {}
    
    def find_cross_platform_games(
        self,
        platform: str,
        other_platforms: list[str],
    ) -> dict[str, list[str]]:
        """Find games that exist on both this platform and others.
        
        Uses a simplified name matching approach (strips parenthetical metadata).
        Returns dict of normalized_name -> list of platforms that have it.
        """
        import re
        
        def normalize(name: str) -> str:
            """Strip region/disc markers for cross-platform matching."""
            name = re.sub(r'\s*\(.*?\)', '', name)    # Remove (USA), (Disc 1), etc.
            name = re.sub(r'\s*\[.*?\]', '', name)    # Remove [!], [b], etc.
            name = re.sub(r'\s*-\s*', ' ', name)      # Normalize dashes
            name = re.sub(r'\s+', ' ', name).strip()   # Collapse whitespace
            return name.lower()
        
        # Get all game names for our platform
        our_games = {}
        cursor = self.db.execute(
            "SELECT DISTINCT name FROM scraped_games WHERE system = ?",
            (platform,),
        )
        for row in cursor:
            norm = normalize(row[0])
            our_games[norm] = row[0]
        
        # Check against other platforms
        cross_platform: dict[str, list[str]] = {}
        for other in other_platforms:
            cursor = self.db.execute(
                "SELECT DISTINCT name FROM scraped_games WHERE system = ?",
                (other,),
            )
            for row in cursor:
                norm = normalize(row[0])
                if norm in our_games:
                    if norm not in cross_platform:
                        cross_platform[norm] = [platform]
                    cross_platform[norm].append(other)
        
        return cross_platform
    
    # --- Curation operations ---
    
    def load_curation(self, platform: str) -> Optional[PlatformCuration]:
        """Load a saved curation for a platform."""
        filepath = self.curations_dir / f"{platform}.yaml"
        if filepath.exists():
            return PlatformCuration.load(filepath)
        return None
    
    def save_curation(self, curation: PlatformCuration) -> Path:
        """Save a platform curation."""
        return curation.save(self.curations_dir)
    
    def list_curations(self) -> list[str]:
        """List all saved platform curations."""
        if not self.curations_dir.exists():
            return []
        return sorted(p.stem for p in self.curations_dir.glob("*.yaml"))
    
    def generate_list_file(
        self,
        platform: str,
        max_tier: GameTier = GameTier.GREAT,
        output_dir: Optional[Path] = None,
    ) -> Optional[Path]:
        """Generate a ROM Farmer list file from a saved curation.
        
        This produces a file compatible with ApplyListsStage, written to
        the lists/ directory by default.
        
        Args:
            platform: Platform name
            max_tier: Maximum tier to include
            output_dir: Output directory (default: lists/)
            
        Returns:
            Path to generated list file, or None if no curation exists
        """
        curation = self.load_curation(platform)
        if not curation:
            logger.warning(f"No curation found for {platform}")
            return None
        
        output_dir = output_dir or self.workspace_root / "lists"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        tier_label = max_tier.value
        filename = f"{platform}+AI-{tier_label.title()}"
        filepath = output_dir / filename
        
        content = curation.to_rom_farmer_list(max_tier=max_tier)
        filepath.write_text(content)
        
        count = len(curation.up_to_tier(max_tier))
        logger.info(f"Generated list: {filepath} ({count} games)")
        return filepath
    
    # --- Future: Embedding-based operations ---
    
    def compute_game_embeddings(self, platform: str) -> None:
        """Compute sentence-transformer embeddings for game descriptions.
        
        This enables:
        - Semantic similarity search ("games like Castlevania")
        - Clustering (find hidden genres/niches)
        - Cross-platform matching (when names differ)
        
        Requires: sentence-transformers, torch
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError("sentence-transformers required: pip install sentence-transformers")
        
        games = self.get_platform_games(platform)
        texts = []
        for g in games:
            # Combine name + genre + description for rich embeddings
            parts = [g["name"]]
            if g.get("genre"):
                parts.append(g["genre"])
            if g.get("description"):
                parts.append(g["description"][:500])  # Truncate long descriptions
            texts.append(" | ".join(parts))
        
        if not texts:
            logger.warning(f"No games with text data for {platform}")
            return
        
        model = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = model.encode(texts, show_progress_bar=True)
        
        # Save embeddings
        output_path = self.curations_dir / "embeddings" / f"{platform}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        embedding_data = {
            "platform": platform,
            "model": "all-MiniLM-L6-v2",
            "count": len(texts),
            "games": [
                {"name": games[i]["name"], "embedding": embeddings[i].tolist()}
                for i in range(len(texts))
            ],
        }
        output_path.write_text(json.dumps(embedding_data))
        logger.info(f"Saved {len(texts)} embeddings for {platform} to {output_path}")
