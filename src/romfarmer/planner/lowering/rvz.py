"""RVZ lowering rule — unzip RVZ from source archive.

Stage sequence this replaces (``stages/builder.py::_rvz_stages``):
    [CachePreCheckStage →] UnzipRVZStage [→ CacheStoreStage]

IR action sequence:
    source-copy   (INTERMEDIATE)  — ingest source ZIP into CAS
    unzip-rvz     (TERMINAL)      — extract .rvz from ZIP
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


class RVZLoweringRule:
    """Lower a GameCube/Wii RVZ game unit to an action sequence."""

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

        rvz_act = Action(
            action_id=make_action_id(str(unit.unit_id), step, "unzip-rvz"),
            tool="unzip-rvz",
            tool_version=probe_tool_version("dolphin-tool"),
            params={},
            inputs=(src_ref,),
            outputs=(
                ArtifactDecl(
                    logical_name=f"{stem}.rvz",
                    kind="rvz",
                    retention=Retention.TERMINAL,
                ),
            ),
        )
        actions.append(rvz_act)

        return UnitPlan(
            unit=unit,
            actions=tuple(actions),
            predicted_output_bytes=unit.source_size,
            prediction=zero_prediction(),
        )
