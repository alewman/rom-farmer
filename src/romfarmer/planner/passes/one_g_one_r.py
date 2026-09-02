"""one_g_one_r pass — select one preferred variant per game.

Groups units by their *base name* (canonical_name with region / language /
revision parentheticals stripped), then picks the single best variant based
on:

1. Region overlap with ``manifest.preferred_regions`` (highest-priority region
   wins; ``preferred_regions`` order is the tiebreaker).
2. Amongst ties: the unit whose ``canonical_name`` sorts earliest (stable,
   deterministic).

Units with no region tag are treated as "World" (kept over explicit regional
variants at the lowest priority slot).

If ``manifest.preferred_regions`` is empty, the pass picks one variant per
base name deterministically (alphabetically first by canonical_name).
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import TYPE_CHECKING

from romfarmer.ir.catalog import Catalog, GameUnit, PassResult, PassTrace, UnitId

if TYPE_CHECKING:
    from romfarmer.analysis.knowledge import KnowledgeBase
    from romfarmer.ir.manifest import BuildManifest
    from romfarmer.planner.costmodel import CostModel

PASS_NAME = "one_g_one_r"

# Strips parenthetical region, language, revision, and version tags.
# e.g. "Final Fantasy VII (USA) (Rev 1)" → "Final Fantasy VII"
_PAREN_TAG = re.compile(
    r"\s*\("
    r"(?:"
    # Region / multi-region tags
    r"USA|Europe|Japan|World|Germany|France|Spain|Italy|Australia|Korea|"
    r"China|Brazil|Netherlands|Sweden|"
    # Short country codes
    r"US|EUR?|JPN?|PAL|NTSC(?:-[UJ])?|"
    # Revision / version
    r"Rev\s*\d+|v\d[\d.]*|Version\s*\d+|"
    # Language codes (2-letter ISO, possibly comma-separated)
    r"(?:En|Fr|De|Es|It|Ja|Nl|Pt|Sv|No|Da|Fi|Pl|Ru|Zh|Ko)(?:[,+][A-Za-z]{2})*"
    r")"
    r"\)",
    re.IGNORECASE,
)


def _base_name(canonical_name: str) -> str:
    """Strip region/language/revision parentheticals for grouping."""
    stripped = _PAREN_TAG.sub("", canonical_name).strip()
    # Normalise multiple internal spaces
    return re.sub(r"  +", " ", stripped)


def _region_priority(unit: GameUnit, preferred: tuple[str, ...]) -> int:
    """Lower value = higher priority.  Units not matching any preferred region
    get a penalty of ``len(preferred) + 1``.  Unknown region = ``len(preferred)``
    (slightly better than a known non-preferred region)."""
    if not preferred:
        return 0
    if not unit.region:
        return len(preferred)  # unknown — keep, but below known preferred
    for i, region in enumerate(preferred):
        if region in unit.region:
            return i
    return len(preferred) + 1


def run(
    catalog: Catalog,
    manifest: BuildManifest,
    kb: KnowledgeBase,
    cost_model: CostModel,
) -> PassResult:
    """Keep the single best regional variant per game base name."""
    if not manifest.one_g_one_r:
        return PassResult(catalog=catalog, trace=PassTrace(pass_name=PASS_NAME, removed=()))
    preferred = manifest.preferred_regions

    # Group by base name (region/revision stripped)
    groups: dict[str, list[GameUnit]] = defaultdict(list)
    for unit in catalog.units:
        groups[_base_name(unit.canonical_name)].append(unit)

    removed: list[tuple[UnitId, str]] = []
    keep_ids: set[UnitId] = set()

    for _base, variants in groups.items():
        if len(variants) == 1:
            keep_ids.add(variants[0].unit_id)
            continue

        # Sort: primary = region priority (asc), secondary = canonical_name (asc)
        sorted_variants = sorted(
            variants,
            key=lambda u: (_region_priority(u, preferred), u.canonical_name),
        )
        winner = sorted_variants[0]
        keep_ids.add(winner.unit_id)

        for loser in sorted_variants[1:]:
            removed.append(
                (
                    loser.unit_id,
                    f"1g1r: '{loser.canonical_name}' region={sorted(loser.region)} "
                    f"superseded by '{winner.canonical_name}' region={sorted(winner.region)}",
                )
            )

    new_catalog = catalog.keep(keep_ids)
    return PassResult(
        catalog=new_catalog,
        trace=PassTrace(
            pass_name=PASS_NAME,
            removed=tuple(removed),
            added=(),
        ),
    )
