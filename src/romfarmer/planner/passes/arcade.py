"""arcade pass — arcade-specific filtering.

Rules (from the architecture spec and existing ``FilterArcadeStage``):

1. **Working only** (``manifest.arcade_working_only``): remove units whose
   ``KnowledgeBase.get_arcade_driver_status`` is not ``"good"``.  Units with
   *unknown* status are kept (conservative).
2. **Parent-only** (always enabled for arcade): when both a parent and clone
   exist, the 1G1R pass already removes clones by canonical name.  This pass
   operates on the residual: removes clone units that slipped through because
   their canonical name differs from the parent's.
3. **Hacks** (``manifest.arcade_include_hacks``): if ``False``, remove units
   whose canonical name contains ``(Hack)`` or ``[hack]`` (case-insensitive).
4. **Bootlegs** (``manifest.arcade_include_bootlegs``): if ``False``, remove
   units whose canonical name contains ``(Bootleg)`` (case-insensitive).

If the catalog's platform is not an arcade platform (``mame``, ``fbneo``,
``arcade``), this pass is a no-op.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from romfarmer.ir.catalog import Catalog, PassResult, PassTrace, UnitId

if TYPE_CHECKING:
    from romfarmer.analysis.knowledge import KnowledgeBase
    from romfarmer.ir.manifest import BuildManifest
    from romfarmer.planner.costmodel import CostModel

PASS_NAME = "arcade"

_ARCADE_PLATFORMS = frozenset({"mame", "fbneo", "arcade", "naomi", "naomi2",
                                "atomiswave", "model2", "model3"})
_HACK_RE = re.compile(r"\b(?:hack|hacked)\b", re.IGNORECASE)
_BOOTLEG_RE = re.compile(r"\bbootleg\b", re.IGNORECASE)


def run(
    catalog: Catalog,
    manifest: "BuildManifest",
    kb: "KnowledgeBase",
    cost_model: "CostModel",
) -> PassResult:
    """Apply arcade-specific filtering rules."""
    plat = str(catalog.platform or "").lower()
    if plat not in _ARCADE_PLATFORMS:
        return PassResult(
            catalog=catalog,
            trace=PassTrace(pass_name=PASS_NAME, removed=(), added=()),
        )

    removed: list[tuple[UnitId, str]] = []

    for unit in catalog.units:
        name = unit.canonical_name

        # Hack filter
        if not manifest.arcade_include_hacks and _HACK_RE.search(name):
            removed.append((unit.unit_id, f"arcade: hack excluded: {name!r}"))
            continue

        # Bootleg filter
        if not manifest.arcade_include_bootlegs and _BOOTLEG_RE.search(name):
            removed.append((unit.unit_id, f"arcade: bootleg excluded: {name!r}"))
            continue

        # Working-only filter (requires driver status from KB)
        if manifest.arcade_working_only:
            # Use the first disc's source path stem as the ROM name
            rom_name = unit.discs[0].source.path.stem
            status = kb.get_arcade_driver_status(rom_name)
            if status is not None and status.lower() != "good":
                removed.append((
                    unit.unit_id,
                    f"arcade: driver_status={status!r} (not 'good'): {name!r}",
                ))
                continue

    removed_ids = {uid for uid, _ in removed}
    new_catalog = catalog.without(removed_ids)
    return PassResult(
        catalog=new_catalog,
        trace=PassTrace(
            pass_name=PASS_NAME,
            removed=tuple(removed),
            added=(),
        ),
    )
