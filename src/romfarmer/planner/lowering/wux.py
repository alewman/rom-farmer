"""WUX lowering rule — unzip WUX from source archive.

Stage sequence this replaces (``stages/builder.py::_wux_stages``):
    [CachePreCheckStage →] UnzipWUXStage [→ CacheStoreStage]

IR action sequence:
    source-copy   (INTERMEDIATE)  — ingest source ZIP into CAS
    unzip-wux     (TERMINAL)      — extract .wux from ZIP
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
    probe_tool_version,
    source_action,
    zero_prediction,
)


class WUXLoweringRule:
    """Lower a Wii U WUX game unit to an action sequence."""

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
        stem = src_path.stem
        step = 0
        actions: list[Action] = []

        src_act = source_action(unit, step, src_path, src_path.name, "zip")
        actions.append(src_act)
        step += 1
        src_ref: InputRef = PendingRef(src_act.action_id, 0)

        wux_act = Action(
            action_id=make_action_id(str(unit.unit_id), step, "unzip-wux"),
            tool="unzip-wux",
            tool_version=probe_tool_version("wit"),
            params={},
            inputs=(src_ref,),
            outputs=(
                ArtifactDecl(
                    logical_name=f"{stem}.wux",
                    kind="wux",
                    retention=Retention.TERMINAL,
                ),
            ),
        )
        actions.append(wux_act)

        return UnitPlan(
            unit=unit,
            actions=tuple(actions),
            predicted_output_bytes=unit.source_size,
            prediction=zero_prediction(),
        )
