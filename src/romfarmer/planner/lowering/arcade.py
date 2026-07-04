"""Arcade lowering rule — copy arcade ZIP as-is.

Arcade ROMs are already in the correct format (MAME/FBNeo expect raw ZIPs).
The action sequence just copies the source to the CAS.

Stage sequence this replaces:
    CopyArcadeStage (and optionally RecompressArcadeStage)
"""

from __future__ import annotations

from romfarmer.ir.actions import (
    Action,
    ArtifactDecl,
    InputRef,
    PendingRef,
    Retention,
    UnitPlan,
)
from romfarmer.ir.catalog import GameUnit
from romfarmer.ir.manifest import BuildManifest
from romfarmer.planner.lowering.base import (
    FormatChain,
    make_action_id,
    source_action,
    static_tool_version,
    zero_prediction,
)


class ArcadeLoweringRule:
    """Lower an arcade ROM unit — passthrough (ZIP copy)."""

    def __init__(self, action_cache: object | None = None) -> None:
        self._cache = action_cache

    def lower(
        self,
        unit: GameUnit,
        chain: FormatChain,
        manifest: BuildManifest,
    ) -> UnitPlan:
        disc = unit.discs[0]
        src_path = disc.source.path
        step = 0
        actions: list[Action] = []

        src_act = source_action(unit, step, src_path, src_path.name, "zip")
        actions.append(src_act)
        step += 1
        src_ref: InputRef = PendingRef(src_act.action_id, 0)

        pt_act = Action(
            action_id=make_action_id(str(unit.unit_id), step, "passthrough"),
            tool="passthrough",
            tool_version=static_tool_version("passthrough"),
            params={},
            inputs=(src_ref,),
            outputs=(
                ArtifactDecl(
                    logical_name=src_path.name,
                    kind="zip",
                    retention=Retention.TERMINAL,
                ),
            ),
        )
        actions.append(pt_act)

        return UnitPlan(
            unit=unit,
            actions=tuple(actions),
            predicted_output_bytes=unit.source_size,
            prediction=zero_prediction(),
        )
