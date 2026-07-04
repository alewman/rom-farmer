"""Passthrough lowering rule — copy source file as terminal artifact.

Used for platforms where the source format IS the target format
(e.g. 3DS .3ds files, Switch .nsp/.xci, WADs) and no conversion is needed.

Stage sequence this replaces: ``_none_stages`` (CASIngestStage).
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


class PassthroughLoweringRule:
    """Lower a unit that needs no transformation."""

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

        src_act = source_action(unit, step, src_path, src_path.name, "source")
        actions.append(src_act)
        step += 1
        src_ref: InputRef = PendingRef(src_act.action_id, 0)

        # Mark the source directly as terminal — no transform needed
        pt_act = Action(
            action_id=make_action_id(str(unit.unit_id), step, "passthrough"),
            tool="passthrough",
            tool_version=static_tool_version("passthrough"),
            params={},
            inputs=(src_ref,),
            outputs=(
                ArtifactDecl(
                    logical_name=src_path.name,
                    kind=src_path.suffix.lstrip(".") or "rom",
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
