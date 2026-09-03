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
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from romfarmer.analysis.knowledge import KnowledgeBase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Priors.  ratio = output_bytes / input_bytes where input_bytes is what the
# budget pass actually feeds in: ``GameUnit.source_size`` — the SOURCE FILE
# bytes (a No-Intro .zip, a Redump .zip), NOT the uncompressed ROM.
#
# Measured 2026-09-03 (review P0 item 2):
#   7z:   output/nointro-1g1r-eng-7z-batocera-v2/<platform>/*.7z vs the source
#         .zip size from file_digest_cache — 7z re-compression of a zip saves
#         only 7–20 %.  The previous table (nes 0.55, snes 0.60 …) was relative
#         to uncompressed ROM bytes and over-predicted savings by ~40 %.
#   chd:  psx from unit_telemetry (smoke-psx-chd n=12) — 0.828 vs the source
#         zip.  Legacy rom_transformations ratios were vs uncompressed bytes
#         and are deliberately not used (see the disc block below).
# Unmeasured platforms fall back to ``_FAMILY_PRIORS`` by tool (label
# ``prior:family:<tool>``) — visible in every budget PassTrace reason so an
# operator can see when a number is a family guess rather than a measurement.
# ---------------------------------------------------------------------------
_HARDCODED_PRIORS: dict[str, dict[str, float]] = {
    # platform → {tool → ratio}
    # ── disc ──
    # psx measured 2026-09-03 from unit_telemetry (smoke-psx-chd, n=12, CHD vs
    # SOURCE ZIP bytes: agg 0.828, per-unit 0.66–0.98).  The legacy
    # rom_transformations numbers (psx 0.551, dreamcast 0.353, xbox 0.279 …)
    # were measured against the UNCOMPRESSED bin/iso and under-predict output
    # by ~⅓ — the unsafe direction for a storage budget.  They are NOT used;
    # every other disc platform takes the family prior until its own
    # unit_telemetry accumulates.
    "psx": {"chd": 0.83},
    "psp": {"cso": 0.85, "chd": 0.85},
    "pspminis": {"chd": 0.85, "passthrough": 1.0},
    "ps3": {"passthrough": 0.90, "ps3": 0.90},
    "gamecube": {"rvz": 1.0},  # source is already .rvz inside the zip
    "wii": {"rvz": 1.0},
    "wiiu": {"wux": 1.0},
    # ── cartridge / handheld (measured, 7z vs source zip) ──
    "atari2600": {"7z": 0.977, "zip": 1.0},  # n=696
    "atari5200": {"7z": 0.928, "zip": 1.0},  # n=134
    "atari7800": {"7z": 0.856, "zip": 1.0},  # n=81
    "atarijaguar": {"7z": 0.910, "zip": 1.0},  # n=70
    "atarilynx": {"7z": 0.910, "zip": 1.0},  # n=103
    "colecovision": {"7z": 0.933, "zip": 1.0},  # n=165
    "fds": {"7z": 0.877, "zip": 1.0},  # n=257
    "gamegear": {"7z": 0.880, "zip": 1.0},  # n=300
    "gb": {"7z": 0.886, "zip": 1.0},  # n=666
    "gb2players": {"7z": 0.881, "zip": 1.0},  # n=799
    "gba": {"7z": 0.829, "zip": 1.0},  # n=1137
    "gbc": {"7z": 0.820, "zip": 1.0},  # n=667
    "gbc2players": {"7z": 0.800, "zip": 1.0},  # n=1013
    "intellivision": {"7z": 0.861, "zip": 1.0},  # n=133
    "mastersystem": {"7z": 0.879, "zip": 1.0},  # n=408
    "megadrive": {"7z": 0.857, "zip": 1.0},  # n=937
    "msx1": {"7z": 0.915, "zip": 1.0},  # n=37
    "msx2": {"7z": 0.890, "zip": 1.0},  # n=20
    "n64": {"7z": 0.921, "zip": 1.0},  # n=373
    "nds": {"7z": 0.814, "zip": 1.0},  # n=866
    "sgb": {"7z": 0.872, "zip": 1.0},  # n=100
    "sgb-gbc": {"7z": 0.813, "zip": 1.0},  # n=58
    "snes": {"7z": 0.894, "zip": 1.0},  # n=895
    # ── cartridge (unmeasured — family prior applies via _FAMILY_PRIORS) ──
    "nes": {"7z": 0.88, "zip": 1.0},
    "3ds": {"passthrough": 1.00},
    "switch": {"passthrough": 1.00},
    # ── arcade (source zip copied as-is) ──
    "arcade": {"zip": 1.0, "passthrough": 1.0, "arcade": 1.0},
    "mame": {"zip": 1.0, "passthrough": 1.0, "arcade": 1.0},
    "fbneo": {"zip": 1.0, "passthrough": 1.0, "arcade": 1.0},
    "neogeo": {"zip": 1.0, "passthrough": 1.0, "arcade": 1.0},
}

# Tool-family fallback for platforms with no measured prior.  Values are the
# medians of the measured platforms above (7z: 0.877 across 23 platforms;
# chd: 0.83 from psx, n=12).  Deliberately on the HIGH side: over-predicting
# under-fills a card (safe, re-run picks it up); under-predicting overfills it.
_FAMILY_PRIORS: dict[str, float] = {
    "7z": 0.88,
    "zip": 1.0,
    "chd": 0.85,
    "cue_bin": 1.0,
    "iso": 1.0,
    "xiso": 0.70,
    "squashfs": 0.70,
    "rvz": 1.0,
    "wux": 1.0,
    "ps3": 0.90,
    "cso": 0.85,
    "passthrough": 1.0,
    "arcade": 1.0,
}

# Number of telemetry samples needed for full confidence
_TELEMETRY_CAP = 100

# Default tool per platform when caller does not specify.  The budget pass
# passes ``manifest.chain[0]`` so this is only a last resort.
_DEFAULT_TOOL: dict[str, str] = {
    plat: next(iter(tools)) for plat, tools in _HARDCODED_PRIORS.items()
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
        knowledge_base: KnowledgeBase | None = None,
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
        if tool is None and platform not in self._priors:
            # No tool named and no platform prior: nothing to reason from.
            # Loud by design — never a silent magic constant.
            raise UnknownPlatformError(
                f"CostModel: no prior registered for platform={platform!r} and no "
                f"tool given. Add an entry to _HARDCODED_PRIORS or pass tool=."
            )
        resolved_tool = _normalise_tool(tool or _DEFAULT_TOOL.get(platform, "passthrough"))
        prior, prior_label = self._prior_ratio(platform, resolved_tool)
        if prior is None:
            raise UnknownPlatformError(
                f"CostModel: no prior registered for platform={platform!r} "
                f"tool={resolved_tool!r} and no family prior for that tool. "
                f"Add an entry to _HARDCODED_PRIORS or _FAMILY_PRIORS."
            )

        # Telemetry posterior — weight grows with the REAL sample count
        if self._kb is not None:
            tel = self._kb.get_compression_ratio(platform, resolved_tool)
            if tel is not None:
                tel_ratio, n = tel
                weight = min(1.0, n / _TELEMETRY_CAP)
                merged = prior * (1.0 - weight) + tel_ratio * weight
                label = f"merged:{prior_label}={prior:.3f},telemetry={tel_ratio:.3f},n={n}"
                return merged, label

        return prior, prior_label

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

    def _prior_ratio(self, platform: str, tool: str) -> tuple[float | None, str]:
        """``(ratio, label)`` — exact (platform, tool) first, else the tool family.

        The old behaviour fell through to "any tool for this platform", which
        made the tool key decorative (a snes ``zip`` prior answered ``7z``).
        """
        plat_entry = self._priors.get(platform)
        if plat_entry is not None and tool in plat_entry:
            return plat_entry[tool], "prior:measured"
        fam = _FAMILY_PRIORS.get(tool)
        if fam is not None:
            return fam, f"prior:family:{tool}"
        return None, "prior:none"

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
                        platform_key,
                        tool_key,
                        ratio,
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
