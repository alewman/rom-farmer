"""PS3 lowering rule — PS3 JB folder decryption / tree build.

Stage sequence this replaces (``stages/builder.py::_ps3_stages``):
    TransformPS3Stage (includes internal CAS tree-cache)

IR action sequence:
    source-copy   (INTERMEDIATE)  — ingest source ZIP/folder into CAS
    ps3-decrypt   (TERMINAL)      — decrypt + build JB folder tree

PS3 updates (DLC) are acquired separately; the Phase 4 action just models
the base game transform.  Updates become acquisition actions in a future
iteration.
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


class PS3LoweringRule:
    """Lower a PS3 game unit to an action sequence."""

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

        # ── source-copy ────────────────────────────────────────────────
        src_act = source_action(unit, step, src_path, src_path.name, "ps3-pkg")
        actions.append(src_act)
        step += 1
        src_ref: InputRef = PendingRef(src_act.action_id, 0)

        # ── ps3-decrypt ────────────────────────────────────────────────
        decrypt_act = Action(
            action_id=make_action_id(str(unit.unit_id), step, "ps3-decrypt"),
            tool="ps3-decrypt",
            tool_version=probe_tool_version("ps3dec"),
            params={"output_format": "jb-folder"},
            inputs=(src_ref,),
            outputs=(
                ArtifactDecl(
                    logical_name=stem,
                    kind="ps3-folder",
                    retention=Retention.TERMINAL,
                ),
            ),
        )
        actions.append(decrypt_act)

        return UnitPlan(
            unit=unit,
            actions=tuple(actions),
            predicted_output_bytes=unit.source_size,
            prediction=zero_prediction(),
        )
