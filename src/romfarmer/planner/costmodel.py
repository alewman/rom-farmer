"""CostModel — enum-keyed compression ratio service.

Design decisions (from the architecture blueprint):
- **Single service** — all size predictions come from here; no scattered
  defaults elsewhere.
- **Enum-keyed** — ``(platform, tool)`` key.  Unknown platform → loud
  ``UnknownPlatformError``, not a silent fallback.  This surfaces missing
  config early rather than silently producing wrong budgets.
- **Priors from ``size_data.json``** — historical output sizes recorded after
  real builds.
- **Posteriors from telemetry** — ``KnowledgeBase.get_compression_ratio``
  feeds back actual ``source_size / output_size`` ratios from
  ``ROMTransformation`` rows.
- **Bayesian merge** — weighted average; telemetry weight scales with sample
  count up to a cap of 1.0 (full confidence at ``TELEMETRY_CAP`` samples).
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from romfarmer.analysis.knowledge import KnowledgeBase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Hard-coded priors (used when size_data.json is absent or has no data)
# From filter_selection.py DEFAULT_COMPRESSION_RATIOS — intentionally
# pessimistic to avoid over-selecting.
# ---------------------------------------------------------------------------
_HARDCODED_PRIORS: dict[str, dict[str, float]] = {
    # platform → {tool → ratio}
    # ratio = output_bytes / input_bytes  (< 1.0 = compression)
    "saturn":      {"chd": 0.65},
    "psx":         {"chd": 0.70},
    "ps2":         {"chd": 0.75},
    "ps3":         {"passthrough": 0.90},
    "psp":         {"cso": 0.85},
    "dreamcast":   {"chd": 0.68},
    "gamecube":    {"rvz": 0.72},
    "wii":         {"rvz": 0.70},
    "wiiu":        {"wux": 0.75},
    "xbox":        {"xiso": 0.80},
    "xbox360":     {"xiso": 0.82},
    "segacd":      {"chd": 0.62},
    "pcenginecd":  {"chd": 0.68},
    "neogeocd":    {"chd": 0.65},
    "3do":         {"chd": 0.70},
    # Cartridge / handheld systems — typically stored in zip
    "nes":         {"zip": 0.55},
    "snes":        {"zip": 0.60},
    "n64":         {"zip": 0.70},
    "gba":         {"zip": 0.75},
    "nds":         {"zip": 0.80},
    "3ds":         {"passthrough": 1.00},  # already compressed
    "gameboy":     {"zip": 0.60},
    "gbc":         {"zip": 0.60},
    "genesis":     {"zip": 0.60},
    "mastersystem": {"zip": 0.60},
    "atari2600":   {"zip": 0.70},
    "arcade":      {"zip": 0.65},
    "mame":        {"zip": 0.65},
    "fbneo":       {"zip": 0.65},
    "switch":      {"passthrough": 1.00},
}

# Number of telemetry samples needed for full confidence
_TELEMETRY_CAP = 100

# Default tool per platform when caller does not specify
_DEFAULT_TOOL: dict[str, str] = {
    "saturn": "chd",
    "psx": "chd",
    "ps2": "chd",
    "ps3": "passthrough",
    "psp": "cso",
    "dreamcast": "chd",
    "gamecube": "rvz",
    "wii": "rvz",
    "wiiu": "wux",
    "xbox": "xiso",
    "xbox360": "xiso",
    "segacd": "chd",
    "pcenginecd": "chd",
    "neogeocd": "chd",
    "3do": "chd",
    "nes": "zip",
    "snes": "zip",
    "n64": "zip",
    "gba": "zip",
    "nds": "zip",
    "3ds": "passthrough",
    "gameboy": "zip",
    "gbc": "zip",
    "genesis": "zip",
    "mastersystem": "zip",
    "atari2600": "zip",
    "arcade": "zip",
    "mame": "zip",
    "fbneo": "zip",
    "switch": "passthrough",
}


class UnknownPlatformError(KeyError):
    """Raised when ``CostModel`` is queried for an unregistered platform.

    Never silently returns 0.85 or any other magic constant — the caller
    must register a prior or handle this explicitly.
    """


class CostModel:
    """Compression-ratio service for the budget pass.

    Args:
        size_data_path: Path to ``config/size_data.json``.  ``None`` means
            use only hard-coded priors.
        knowledge_base: Optional KB for telemetry posteriors.  When ``None``,
            only priors are used.
    """

    def __init__(
        self,
        size_data_path: Path | None = None,
        knowledge_base: "KnowledgeBase | None" = None,
    ) -> None:
        # {platform: {tool: ratio}}
        self._priors: dict[str, dict[str, float]] = {
            plat: dict(tools) for plat, tools in _HARDCODED_PRIORS.items()
        }
        self._kb = knowledge_base

        if size_data_path is not None and size_data_path.exists():
            self._load_size_data(size_data_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ratio(
        self,
        platform: str,
        tool: str | None = None,
    ) -> tuple[float, str]:
        """Return ``(ratio, source_label)`` for *platform*.

        *ratio* is ``output_bytes / input_bytes``.

        Raises:
            UnknownPlatformError: if no prior or telemetry exists for *platform*.
        """
        resolved_tool = tool or _DEFAULT_TOOL.get(platform, "passthrough")
        prior = self._prior_ratio(platform, resolved_tool)
        if prior is None:
            raise UnknownPlatformError(
                f"CostModel: no prior registered for platform={platform!r} "
                f"tool={resolved_tool!r}. Add an entry to size_data.json or "
                f"the _HARDCODED_PRIORS table."
            )

        # Try telemetry posterior
        if self._kb is not None:
            tel = self._kb.get_compression_ratio(platform, resolved_tool)
            if tel is not None:
                tel_ratio, n = tel
                weight = min(1.0, n / _TELEMETRY_CAP)
                merged = prior * (1.0 - weight) + tel_ratio * weight
                label = f"merged:prior={prior:.3f},telemetry={tel_ratio:.3f},n={n}"
                return merged, label

        return prior, f"prior:hardcoded"

    def predict_output_bytes(
        self,
        source_bytes: int,
        platform: str,
        tool: str | None = None,
    ) -> tuple[int, str]:
        """Return ``(predicted_output_bytes, source_label)``."""
        r, label = self.ratio(platform, tool)
        return int(source_bytes * r), label

    def register_prior(self, platform: str, tool: str, ratio: float) -> None:
        """Register or override a prior for *platform* / *tool*.

        Useful in tests and for platforms not in the built-in table.
        """
        if platform not in self._priors:
            self._priors[platform] = {}
        self._priors[platform][tool] = ratio

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _prior_ratio(self, platform: str, tool: str) -> float | None:
        plat_entry = self._priors.get(platform)
        if plat_entry is None:
            return None
        # Exact tool match first
        if tool in plat_entry:
            return plat_entry[tool]
        # Fall back to any tool for this platform (first entry)
        return next(iter(plat_entry.values()), None)

    def _load_size_data(self, path: Path) -> None:
        """Load ``size_data.json`` and update priors.

        ``size_data.json`` format::

            {
              "<platform>": [
                {
                  "output_size_bytes": 453980902260,
                  "input_size_bytes": 670000000000,
                  "compression": "chd",
                  ...
                },
                ...
              ]
            }

        Only records with both ``input_size_bytes > 0`` and
        ``output_size_bytes > 0`` are used.
        """
        try:
            raw = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("CostModel: could not load %s: %s", path, exc)
            return

        for platform, records in raw.items():
            if not isinstance(records, list):
                continue
            platform_key = _normalise_platform(platform)
            totals: dict[str, tuple[float, float]] = {}  # tool → (sum_in, sum_out)
            for rec in records:
                if not isinstance(rec, dict):
                    continue
                in_b = rec.get("input_size_bytes") or 0
                out_b = rec.get("output_size_bytes") or 0
                if in_b <= 0 or out_b <= 0:
                    continue
                tool_key = _normalise_tool(rec.get("compression") or "passthrough")
                prev = totals.get(tool_key, (0.0, 0.0))
                totals[tool_key] = (prev[0] + in_b, prev[1] + out_b)

            for tool_key, (total_in, total_out) in totals.items():
                if total_in > 0:
                    ratio = total_out / total_in
                    if platform_key not in self._priors:
                        self._priors[platform_key] = {}
                    self._priors[platform_key][tool_key] = ratio
                    logger.debug(
                        "CostModel: loaded prior platform=%s tool=%s ratio=%.3f",
                        platform_key, tool_key, ratio,
                    )


def _normalise_platform(name: str) -> str:
    """Lower-case + strip whitespace."""
    return name.lower().strip()


def _normalise_tool(name: str) -> str:
    """Normalise compression string to a canonical tool key."""
    name = name.lower().strip()
    _map = {
        "none": "passthrough",
        "": "passthrough",
        "chdman": "chd",
        "dolphin-rvz": "rvz",
        "extract-xiso": "xiso",
        "maxcso": "cso",
        "wit": "wux",
    }
    return _map.get(name, name)
