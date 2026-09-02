"""XISO lowering rule — Redump Xbox ISO → extract-xiso [→ squashfs].

Stage sequence this replaces (``stages/builder.py::_xiso_stages``):
    [CachePreCheckStage →] ExtractArchiveStage → ConvertXISOStage
    [→ CompressSquashfsStage]

IR action sequence:
    source-copy   (INTERMEDIATE)  — ingest source ZIP into CAS
    unzip         (INTERMEDIATE)  — extract .iso from ZIP
    extract-xiso  (TERMINAL)      — strip padding → .xiso
    [mksquashfs]  (TERMINAL)      — optional squashfs for Xbox-on-Linux targets
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
    static_tool_version,
    zero_prediction,
)


class XisoLoweringRule:
    """Lower an Xbox XISO game unit to an action sequence."""

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
        src_act = source_action(unit, step, src_path, src_path.name, "zip")
        actions.append(src_act)
        step += 1
        src_ref: InputRef = PendingRef(src_act.action_id, 0)

        # ── unzip → .iso ───────────────────────────────────────────────
        unzip_act = Action(
            action_id=make_action_id(str(unit.unit_id), step, "unzip"),
            tool="unzip",
            tool_version=static_tool_version("unzip"),
            params={"format": "xbox-iso"},
            inputs=(src_ref,),
            outputs=(
                ArtifactDecl(
                    logical_name=f"{stem}.iso",
                    kind="iso",
                    retention=Retention.INTERMEDIATE,
                ),
            ),
        )
        actions.append(unzip_act)
        step += 1
        iso_ref: InputRef = PendingRef(unzip_act.action_id, 0)

        # ── extract-xiso ───────────────────────────────────────────────
        xiso_retention = Retention.INTERMEDIATE if "squashfs" in chain else Retention.TERMINAL
        xiso_act = Action(
            action_id=make_action_id(str(unit.unit_id), step, "extract-xiso"),
            tool="extract-xiso",
            tool_version=probe_tool_version("extract-xiso"),
            params={},
            inputs=(iso_ref,),
            outputs=(
                ArtifactDecl(
                    logical_name=f"{stem}.xiso",
                    kind="xiso",
                    retention=xiso_retention,
                ),
            ),
        )
        actions.append(xiso_act)
        step += 1

        # ── optional squashfs ──────────────────────────────────────────
        if "squashfs" in chain:
            xiso_ref: InputRef = PendingRef(xiso_act.action_id, 0)
            squash_act = Action(
                action_id=make_action_id(str(unit.unit_id), step, "mksquashfs"),
                tool="mksquashfs",
                tool_version=probe_tool_version("mksquashfs"),
                params={"compression": "lz4"},
                inputs=(xiso_ref,),
                outputs=(
                    ArtifactDecl(
                        logical_name=f"{stem}.squashfs",
                        kind="squashfs",
                        retention=Retention.TERMINAL,
                    ),
                ),
            )
            actions.append(squash_act)

        return UnitPlan(
            unit=unit,
            actions=tuple(actions),
            predicted_output_bytes=unit.source_size,
            prediction=zero_prediction(),
        )
