"""AI-powered rescue list generator for 1G1Gen cross-platform deduplication.

Uses the GitHub Copilot SDK (via copilot Python package) to query a cheap model
(Claude Haiku 4.5) in batch to identify games where a lower-priority platform
has the definitively superior version.

Architecture:
    1. Load cross-platform duplicate games from the build output
    2. Batch them into prompts (20-30 games per prompt for efficiency)
    3. Ask the model: "Which platform has the best version of each game?"
    4. Parse structured responses into rescue lists
    5. Save as YAML files that plug into FilterGenerationStage

The rescue lists OVERRIDE the deterministic priority system. Without them,
gen6 would always keep the PS2 version. With rescue lists, we keep the
GameCube version of Soul Calibur II (has Link) and the Xbox version of
Splinter Cell (runs better).

Usage:
    generator = RescueListGenerator()
    await generator.connect()
    rescue_lists = await generator.generate("gen6", duplicate_games)
    generator.save(rescue_lists, output_dir)

    # Result: {
    #   "gamecube": {"Soul Calibur II", "Resident Evil 4", ...},
    #   "xbox": {"Splinter Cell", "Half-Life 2", ...},
    #   "dreamcast": {"Marvel vs. Capcom 2", ...},
    # }
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# Default model — cheapest Copilot model, good enough for game knowledge
DEFAULT_MODEL = "claude-haiku-4.5"

# How many games to include per AI prompt batch
BATCH_SIZE = 50

# Copilot Router endpoint (OpenAI-compatible)
COPILOT_ROUTER_URL = "http://localhost:7318/v1"

# Max concurrent API batches (backoff handles rate limits)
MAX_CONCURRENT_BATCHES = 3

# System prompt for rescue list generation
SYSTEM_PROMPT = """\
You are a video game expert helping build a ROM collection. We are deduplicating \
games that appear on multiple platforms within the same console generation.

By default, we keep the PRIMARY platform's version of each cross-platform game \
and remove the others. Your job is to identify EXCEPTIONS — games where a \
NON-primary platform has a definitively superior version.

Criteria for "rescue" (keeping a non-primary version):
- Exclusive content: Extra characters, levels, modes, weapons (e.g., GameCube \
  Soul Calibur II has Link as exclusive character)
- Significantly better performance: Higher framerate, resolution, or stability \
  (e.g., Xbox Splinter Cell runs at higher res than PS2)
- Different/enhanced game: Port is substantially reworked, not just a straight \
  copy (e.g., Dreamcast Crazy Taxi has original soundtrack vs PS2)
- Definitive edition: Platform version widely considered the best way to play

Do NOT rescue games just because of minor differences. The bar is HIGH — only \
rescue when a gaming enthusiast would specifically seek out that platform's version.

Respond in JSON format ONLY. No markdown, no explanation outside the JSON.\
"""


@dataclass
class RescueDecision:
    """AI's decision about a single cross-platform game."""

    game_name: str
    platforms_available: list[str]
    primary_platform: str
    rescue_platform: str | None = None
    reason: str = ""
    confidence: str = "high"  # high, medium, low


@dataclass
class RescueListResult:
    """Complete rescue list generation result for a generation."""

    generation: str
    model: str
    timestamp: float = 0.0
    decisions: list[RescueDecision] = field(default_factory=list)
    rescue_lists: dict[str, set[str]] = field(default_factory=dict)
    stats: dict[str, Any] = field(default_factory=dict)

    def to_rescue_dict(self) -> dict[str, set[str]]:
        """Get rescue lists in the format FilterGenerationStage expects.

        Returns:
            Dict of platform -> set of game names to protect from removal.
        """
        return dict(self.rescue_lists)

    def to_yaml(self) -> str:
        """Serialize to YAML for caching/review."""
        data = {
            "generation": self.generation,
            "model": self.model,
            "timestamp": self.timestamp,
            "stats": self.stats,
            "rescue_lists": {
                platform: sorted(games) for platform, games in self.rescue_lists.items()
            },
            "decisions": [
                {
                    "game": d.game_name,
                    "platforms": d.platforms_available,
                    "primary": d.primary_platform,
                    "rescue_to": d.rescue_platform,
                    "reason": d.reason,
                    "confidence": d.confidence,
                }
                for d in self.decisions
                if d.rescue_platform  # Only include actual rescues
            ],
        }
        return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> RescueListResult:
        """Load from saved YAML."""
        data = yaml.safe_load(yaml_str)
        result = cls(
            generation=data["generation"],
            model=data["model"],
            timestamp=data.get("timestamp", 0),
            stats=data.get("stats", {}),
        )
        # Rebuild rescue lists
        for platform, games in data.get("rescue_lists", {}).items():
            result.rescue_lists[platform] = set(games)
        # Rebuild decisions
        for d in data.get("decisions", []):
            result.decisions.append(
                RescueDecision(
                    game_name=d["game"],
                    platforms_available=d["platforms"],
                    primary_platform=d["primary"],
                    rescue_platform=d.get("rescue_to"),
                    reason=d.get("reason", ""),
                    confidence=d.get("confidence", "high"),
                )
            )
        return result


class RescueListGenerator:
    """Generate AI-powered rescue lists using the Copilot SDK.

    Uses the `copilot` Python package (github-copilot-sdk) which communicates
    with the Copilot CLI subprocess via JSON-RPC. No HTTP server needed.
    """

    def __init__(self, model: str = DEFAULT_MODEL, batch_size: int = BATCH_SIZE):
        self.model = model
        self.batch_size = batch_size
        self._client = None
        self._session = None

    async def connect(self) -> None:
        """Initialize the Copilot SDK client and create a session."""
        try:
            import copilot
        except ImportError:
            raise ImportError(
                "github-copilot-sdk required: pip install github-copilot-sdk\n"
                "Also requires Copilot CLI: npm install -g @github/copilot"
            ) from None

        logger.info(f"Connecting to Copilot SDK (model: {self.model})...")
        self._client = copilot.CopilotClient()
        await self._client.start()

        state = self._client.get_state()
        if state != "connected":
            raise RuntimeError(f"Copilot SDK failed to connect: state={state}")

        auth = await self._client.get_auth_status()
        if not auth.isAuthenticated:
            raise RuntimeError("Copilot SDK not authenticated. Run: copilot /login")

        logger.info(f"Connected to Copilot SDK as {getattr(auth, 'user', 'unknown')}")

    async def disconnect(self) -> None:
        """Shut down the SDK client."""
        if self._client:
            try:
                await self._client.stop()
            except Exception as e:
                logger.warning(f"Error stopping Copilot client: {e}")
            self._client = None
            self._session = None

    async def _send_prompt(self, prompt: str) -> str:
        """Send a prompt to the model and get the text response.

        Creates a fresh session per prompt to avoid context contamination.
        """
        if not self._client:
            raise RuntimeError("Not connected. Call connect() first.")

        session = await self._client.create_session({"model": self.model})
        try:
            result = await session.send_and_wait(
                {"prompt": prompt},
                timeout=120,
            )
            if result and result.data and result.data.content:
                return result.data.content.strip()
            return ""
        except Exception as e:
            logger.error(f"Prompt failed: {e}")
            return ""

    def _build_batch_prompt(
        self,
        generation_name: str,
        primary_platform: str,
        platform_priority: list[str],
        games: list[dict[str, list[str]]],
    ) -> str:
        """Build a prompt for a batch of cross-platform games.

        Args:
            generation_name: e.g. "gen6"
            primary_platform: e.g. "ps2"
            platform_priority: e.g. ["ps2", "gamecube", "xbox", "dreamcast"]
            games: List of {"name": str, "platforms": [str, ...]}

        Returns:
            Complete prompt string.
        """
        priority_str = " > ".join(platform_priority)
        games_block = "\n".join(
            f"  {i + 1}. {g['name']} — available on: {', '.join(g['platforms'])}"
            for i, g in enumerate(games)
        )

        return f"""{SYSTEM_PROMPT}

Generation: {generation_name}
Platform priority (highest first): {priority_str}
Primary (default keeper): {primary_platform}

For each game below, decide: should we KEEP the {primary_platform} version \
(default), or RESCUE a different platform's version because it's definitively better?

Games to evaluate:
{games_block}

Respond with a JSON array. For each game, include:
- "game": the game name exactly as listed
- "rescue": null if the {primary_platform} version is fine, or the platform name to rescue
- "reason": brief reason (only needed if rescuing)

Example response:
[
  {{"game": "Soul Calibur II", "rescue": "gamecube", "reason": "Exclusive Link character, best version"}},
  {{"game": "Grand Theft Auto Vice City", "rescue": null}},
  {{"game": "Splinter Cell", "rescue": "xbox", "reason": "Higher resolution, better lighting"}}
]

Respond with ONLY the JSON array:\
"""

    def _parse_batch_response(
        self,
        response: str,
        primary_platform: str,
        games: list[dict[str, list[str]]],
    ) -> list[RescueDecision]:
        """Parse the model's JSON response into RescueDecision objects."""
        decisions = []

        # Try to extract JSON from the response (model might wrap in markdown)
        json_match = re.search(r"\[.*\]", response, re.DOTALL)
        if not json_match:
            logger.warning(f"No JSON array found in response: {response[:200]}")
            # Fall back: no rescues for this batch
            for g in games:
                decisions.append(
                    RescueDecision(
                        game_name=g["name"],
                        platforms_available=g["platforms"],
                        primary_platform=primary_platform,
                        rescue_platform=None,
                        reason="(parse failure — defaulting to primary)",
                    )
                )
            return decisions

        try:
            parsed = json.loads(json_match.group())
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}")
            # Same fallback
            for g in games:
                decisions.append(
                    RescueDecision(
                        game_name=g["name"],
                        platforms_available=g["platforms"],
                        primary_platform=primary_platform,
                        rescue_platform=None,
                        reason="(parse failure — defaulting to primary)",
                    )
                )
            return decisions

        # Build lookup for quick matching
        game_lookup = {g["name"].lower(): g for g in games}

        for item in parsed:
            game_name = item.get("game", "")
            rescue_platform = item.get("rescue")
            reason = item.get("reason", "")

            # Find matching game from our input
            game_info = game_lookup.get(game_name.lower())
            if not game_info:
                # Try fuzzy match
                for key, val in game_lookup.items():
                    if game_name.lower() in key or key in game_name.lower():
                        game_info = val
                        break

            if not game_info:
                logger.debug(f"Could not match response game: {game_name}")
                continue

            # Validate rescue platform is in the available platforms
            if rescue_platform and rescue_platform not in game_info["platforms"]:
                logger.warning(
                    f"Model suggested {rescue_platform} for {game_name}, "
                    f"but only available on: {game_info['platforms']}"
                )
                rescue_platform = None

            decisions.append(
                RescueDecision(
                    game_name=game_info["name"],
                    platforms_available=game_info["platforms"],
                    primary_platform=primary_platform,
                    rescue_platform=rescue_platform if rescue_platform else None,
                    reason=reason,
                )
            )

        return decisions

    async def generate(
        self,
        generation_name: str,
        platform_priority: list[str],
        duplicate_games: list[dict[str, list[str]]],
    ) -> RescueListResult:
        """Generate rescue lists for a generation's cross-platform duplicates.

        Args:
            generation_name: e.g. "gen6"
            platform_priority: Platforms in priority order, e.g. ["ps2", "gamecube", "xbox"]
            duplicate_games: List of {"name": str, "platforms": [str, ...]}
                Each entry is a game that exists on 2+ platforms.

        Returns:
            RescueListResult with platform -> set of rescued game names.
        """
        if not duplicate_games:
            logger.info("No duplicate games to evaluate.")
            return RescueListResult(
                generation=generation_name,
                model=self.model,
                timestamp=time.time(),
            )

        primary = platform_priority[0]
        total = len(duplicate_games)
        logger.info(
            f"Generating rescue lists for {generation_name}: "
            f"{total} cross-platform games, primary={primary}"
        )

        # Split into batches
        batches = [
            duplicate_games[i : i + self.batch_size] for i in range(0, total, self.batch_size)
        ]
        logger.info(f"Processing {len(batches)} batches of ~{self.batch_size} games")

        all_decisions: list[RescueDecision] = []

        for batch_idx, batch in enumerate(batches):
            logger.info(f"Batch {batch_idx + 1}/{len(batches)} ({len(batch)} games)...")

            prompt = self._build_batch_prompt(generation_name, primary, platform_priority, batch)

            response = await self._send_prompt(prompt)
            if not response:
                logger.warning(f"Empty response for batch {batch_idx + 1}")
                continue

            decisions = self._parse_batch_response(response, primary, batch)
            all_decisions.extend(decisions)

            # Brief pause between batches to be respectful of rate limits
            if batch_idx < len(batches) - 1:
                await asyncio.sleep(1)

        # Build rescue lists from decisions
        rescue_lists: dict[str, set[str]] = {}
        rescued_count = 0
        for d in all_decisions:
            if d.rescue_platform:
                if d.rescue_platform not in rescue_lists:
                    rescue_lists[d.rescue_platform] = set()
                rescue_lists[d.rescue_platform].add(d.game_name)
                rescued_count += 1

        result = RescueListResult(
            generation=generation_name,
            model=self.model,
            timestamp=time.time(),
            decisions=all_decisions,
            rescue_lists=rescue_lists,
            stats={
                "total_duplicates": total,
                "batches": len(batches),
                "total_evaluated": len(all_decisions),
                "total_rescued": rescued_count,
                "rescue_rate": f"{rescued_count / max(len(all_decisions), 1) * 100:.1f}%",
                "by_platform": {p: len(games) for p, games in rescue_lists.items()},
            },
        )

        logger.info(
            f"Rescue generation complete: {rescued_count}/{len(all_decisions)} "
            f"games rescued ({result.stats['rescue_rate']})"
        )
        for platform, games in rescue_lists.items():
            logger.info(f"  {platform}: {len(games)} rescued games")

        return result

    # ------------------------------------------------------------------
    # OpenAI-compatible API path (via Copilot Router)
    # ------------------------------------------------------------------

    def _build_enriched_batch_prompt(
        self,
        generation_name: str,
        primary_platform: str,
        platform_priority: list[str],
        games: list[dict],
    ) -> str:
        """Build a prompt enriched with metadata for better LLM decisions.

        Unlike _build_batch_prompt, this includes genre/rating/developer info
        from ScreenScraper so the model has concrete data to reason about.
        """
        priority_str = " > ".join(platform_priority)
        lines = []
        for i, g in enumerate(games):
            plats = ", ".join(g["platforms"])
            line = f"  {i + 1}. {g['name']} — on: {plats}"
            meta = g.get("metadata", {})
            if meta:
                meta_parts = []
                for p, m in meta.items():
                    parts = []
                    if m.get("genre"):
                        parts.append(m["genre"])
                    if m.get("rating"):
                        parts.append(f"rating={m['rating']:.1f}")
                    if m.get("developer"):
                        parts.append(f"dev={m['developer']}")
                    if parts:
                        meta_parts.append(f"{p}({', '.join(parts)})")
                if meta_parts:
                    line += f"  [{'; '.join(meta_parts)}]"
            lines.append(line)
        games_block = "\n".join(lines)

        return f"""{SYSTEM_PROMPT}

Generation: {generation_name}
Platform priority (highest first): {priority_str}
Primary (default keeper): {primary_platform}

For each game below, decide: should we KEEP the {primary_platform} version \
(default), or RESCUE a different platform's version because it's definitively better?

Metadata is provided where available (genre, rating, developer) per platform.

Games to evaluate:
{games_block}

Respond with a JSON array. For each game, include:
- "game": the game name exactly as listed
- "rescue": null if the {primary_platform} version is fine, or the platform name to rescue
- "reason": brief reason (only needed if rescuing)

Respond with ONLY the JSON array:\
"""

    async def _send_prompt_via_api(self, prompt: str) -> str:
        """Send a prompt via the OpenAI-compatible Copilot Router HTTP API.

        Uses httpx for async HTTP. Falls back to urllib if httpx unavailable.
        """
        import urllib.error
        import urllib.request

        payload = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
                "max_tokens": 4096,
            }
        )

        req = urllib.request.Request(
            f"{COPILOT_ROUTER_URL}/chat/completions",
            data=payload.encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer not-required",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"].strip()
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            logger.error(f"API call failed: {e}")
            return ""
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected API response: {e}")
            return ""

    async def _send_batch_concurrent(
        self,
        prompts: list[str],
    ) -> list[str]:
        """Send multiple prompts concurrently (up to MAX_CONCURRENT_BATCHES).

        Uses asyncio.to_thread to run synchronous urllib calls concurrently.
        """
        import asyncio

        sem = asyncio.Semaphore(MAX_CONCURRENT_BATCHES)

        async def _one(prompt: str) -> str:
            async with sem:
                return await asyncio.to_thread(self._send_prompt_sync, prompt)

        return await asyncio.gather(*[_one(p) for p in prompts])

    def _send_prompt_sync(self, prompt: str, max_retries: int = 6) -> str:
        """Synchronous version of _send_prompt_via_api for use with to_thread.

        Retries on failure with exponential backoff + jitter.
        Rate-limit (429) errors use longer backoff and respect Retry-After.
        """
        import urllib.error
        import urllib.request

        payload = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
                "max_tokens": 4096,
            }
        )

        base_delay = 5  # seconds

        for attempt in range(max_retries + 1):
            req = urllib.request.Request(
                f"{COPILOT_ROUTER_URL}/chat/completions",
                data=payload.encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer not-required",
                },
                method="POST",
            )

            try:
                with urllib.request.urlopen(req, timeout=180) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    content = data["choices"][0]["message"]["content"].strip()
                    if content:
                        return content
                    logger.warning(f"Attempt {attempt + 1}: empty response from API")
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    retry_after = e.headers.get("Retry-After")
                    if retry_after:
                        wait = int(retry_after)
                    else:
                        wait = base_delay * (2**attempt)
                    wait = min(wait, 120)
                    jitter = random.uniform(0, wait * 0.25)
                    logger.warning(
                        f"Rate limited (429) on attempt {attempt + 1}. "
                        f"Waiting {wait + jitter:.1f}s..."
                    )
                    time.sleep(wait + jitter)
                    continue
                logger.warning(f"HTTP {e.code} on attempt {attempt + 1}: {e.reason}")
            except Exception as e:
                logger.warning(f"API call attempt {attempt + 1} failed: {e}")

            if attempt < max_retries:
                wait = base_delay * (2**attempt)
                wait = min(wait, 120)
                jitter = random.uniform(0, wait * 0.25)
                logger.info(f"Retrying in {wait + jitter:.1f}s...")
                time.sleep(wait + jitter)

        logger.error(f"All {max_retries + 1} attempts exhausted")
        return ""

    async def generate_via_api(
        self,
        generation_name: str,
        platform_priority: list[str],
        duplicate_games: list[dict],
    ) -> RescueListResult:
        """Generate rescue lists using the OpenAI-compatible Copilot Router API.

        This is the optimized path:
        - Uses HTTP API instead of Copilot SDK subprocess
        - Supports metadata-enriched prompts
        - Sends concurrent batches for speed
        - Larger default batch size (50 vs 25)

        Args:
            generation_name: e.g. "gen6"
            platform_priority: Platforms in priority order
            duplicate_games: List of {"name": str, "platforms": [str, ...],
                             "metadata": {platform: {genre, rating, ...}}}

        Returns:
            RescueListResult with rescue lists.
        """
        if not duplicate_games:
            return RescueListResult(
                generation=generation_name,
                model=self.model,
                timestamp=time.time(),
            )

        primary = platform_priority[0]
        total = len(duplicate_games)
        logger.info(
            f"Generating rescue lists for {generation_name} via API: "
            f"{total} games, model={self.model}, batch_size={self.batch_size}"
        )

        # Build batched prompts
        batches = [
            duplicate_games[i : i + self.batch_size] for i in range(0, total, self.batch_size)
        ]

        prompts = [
            self._build_enriched_batch_prompt(generation_name, primary, platform_priority, batch)
            for batch in batches
        ]

        logger.info(f"Sending {len(prompts)} batches ({MAX_CONCURRENT_BATCHES} concurrent)")

        # Send all batches (concurrent within limit)
        responses = await self._send_batch_concurrent(prompts)

        # Parse all responses
        all_decisions: list[RescueDecision] = []
        for batch_idx, (response, batch) in enumerate(zip(responses, batches, strict=False)):
            if not response:
                logger.warning(f"Empty response for batch {batch_idx + 1}")
                continue
            decisions = self._parse_batch_response(response, primary, batch)
            all_decisions.extend(decisions)
            logger.info(
                f"Batch {batch_idx + 1}/{len(batches)}: "
                f"{sum(1 for d in decisions if d.rescue_platform)} rescues"
            )

        # Build rescue lists
        rescue_lists: dict[str, set[str]] = {}
        rescued_count = 0
        for d in all_decisions:
            if d.rescue_platform:
                if d.rescue_platform not in rescue_lists:
                    rescue_lists[d.rescue_platform] = set()
                rescue_lists[d.rescue_platform].add(d.game_name)
                rescued_count += 1

        result = RescueListResult(
            generation=generation_name,
            model=self.model,
            timestamp=time.time(),
            decisions=all_decisions,
            rescue_lists=rescue_lists,
            stats={
                "total_duplicates": total,
                "batches": len(batches),
                "total_evaluated": len(all_decisions),
                "total_rescued": rescued_count,
                "rescue_rate": f"{rescued_count / max(len(all_decisions), 1) * 100:.1f}%",
                "by_platform": {p: len(g) for p, g in rescue_lists.items()},
            },
        )

        logger.info(f"Rescue generation complete: {rescued_count}/{len(all_decisions)} rescued")
        return result

    def save(self, result: RescueListResult, output_dir: Path) -> Path:
        """Save rescue lists to a YAML file.

        Args:
            result: The generation result.
            output_dir: Directory to save in (e.g., config/curations/rescue/).

        Returns:
            Path to the saved file.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = output_dir / f"rescue-{result.generation}.yaml"
        filepath.write_text(result.to_yaml())
        logger.info(f"Saved rescue lists to {filepath}")
        return filepath

    @staticmethod
    def load(filepath: Path) -> RescueListResult:
        """Load previously generated rescue lists."""
        return RescueListResult.from_yaml(filepath.read_text())


# ---------------------------------------------------------------------------
# Convenience function for CLI / build integration
# ---------------------------------------------------------------------------


async def generate_rescue_lists(
    generation_name: str,
    platform_priority: list[str],
    duplicate_games: list[dict[str, list[str]]],
    model: str = DEFAULT_MODEL,
    cache_dir: Path | None = None,
    force_regenerate: bool = False,
) -> dict[str, set[str]]:
    """High-level function to generate or load cached rescue lists.

    This is the main entry point for build integration. It:
    1. Checks for cached results (skip AI call if fresh enough)
    2. Generates new rescue lists via Copilot SDK
    3. Caches the results for future builds
    4. Returns the rescue dict for FilterGenerationStage

    Args:
        generation_name: e.g. "gen6"
        platform_priority: Platforms in priority order
        duplicate_games: Cross-platform duplicate games to evaluate
        model: Copilot model to use
        cache_dir: Directory for cached results
        force_regenerate: Skip cache and regenerate

    Returns:
        Dict of platform -> set of game names to rescue.
    """
    if cache_dir is None:
        from romfarmer.core.paths import paths

        cache_dir = paths.workspace_root / "config" / "curations" / "rescue"

    # Check cache
    cache_file = cache_dir / f"rescue-{generation_name}.yaml"
    if cache_file.exists() and not force_regenerate:
        logger.info(f"Loading cached rescue lists from {cache_file}")
        result = RescueListResult.from_yaml(cache_file.read_text())
        logger.info(
            f"Cached: {result.stats.get('total_rescued', '?')} rescues for {generation_name}"
        )
        return result.to_rescue_dict()

    # Generate fresh
    generator = RescueListGenerator(model=model)
    try:
        await generator.connect()
        result = await generator.generate(generation_name, platform_priority, duplicate_games)
        generator.save(result, cache_dir)
        return result.to_rescue_dict()
    finally:
        await generator.disconnect()
