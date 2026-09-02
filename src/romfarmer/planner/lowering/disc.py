"""Disc lowering rule — Redump CUE/BIN → CHD (or passthrough).

Stage sequence this replaces (from ``stages/builder.py::_disc_stages``):
    CachePreCheckStage → ExtractArchiveStage → CompressCHDStage → CreateM3UStage

IR action sequence:
    For each disc:
        source-copy   (INTERMEDIATE)  — ingest ZIP into CAS
        unzip         (INTERMEDIATE)  — extract CUE/BIN from ZIP
        chdman        (TERMINAL)      — compress to CHD

    If multi-disc:
        m3u-create    (TERMINAL)      — synthesise M3U playlist

    If no CHD (passthrough):
        source-copy + unzip, outputs CUE/BIN as TERMINAL
"""

from __future__ import annotations

from romfarmer.ir.actions import (
    Action,
    ActionId,
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
    source_ref,
    static_tool_version,
    zero_prediction,
)


class DiscLoweringRule:
    """Lower a disc-based game unit to an action sequence."""

    def __init__(
        self,
        action_cache: object | None = None,
        no_chd: bool = False,
    ) -> None:
        self._cache = action_cache
        self._no_chd = no_chd

    def lower(
        self,
        unit: GameUnit,
        chain: FormatChain,
        manifest: BuildManifest,
    ) -> UnitPlan:
        actions: list[Action] = []
        chd_action_ids: list[ActionId] = []
        step = 0

        for disc in unit.discs:
            src_path = disc.source.path
            zip_name = src_path.name
            stem = src_path.stem

            # ── Step A: source-copy ────────────────────────────────────
            cref, sha256 = source_ref(unit, self._cache) if disc.index == 1 else (None, None)
            src_act = source_action(unit, step, disc.source.path, zip_name, "zip")
            # If sha256 is already known, we can skip source-copy and use ContentRef directly
            # For now always emit source-copy (executor will cache-hit if already ingested)
            actions.append(src_act)
            step += 1
            src_out_ref: InputRef = PendingRef(src_act.action_id, 0)

            # ── Step B: unzip ──────────────────────────────────────────
            unzip_act = Action(
                action_id=make_action_id(str(unit.unit_id), step, "unzip"),
                tool="unzip",
                tool_version=probe_tool_version("unzip"),
                params={"format": "disc"},
                inputs=(src_out_ref,),
                outputs=(
                    ArtifactDecl(
                        logical_name=f"{stem}.cue",
                        kind="cue",
                        retention=Retention.INTERMEDIATE,
                    ),
                ),
            )
            actions.append(unzip_act)
            step += 1
            extracted_ref: InputRef = PendingRef(unzip_act.action_id, 0)

            if self._no_chd:
                # passthrough — CUE+BIN as terminal
                passthrough_act = Action(
                    action_id=make_action_id(str(unit.unit_id), step, "source-copy-out"),
                    tool="source-copy",
                    tool_version=static_tool_version("source-copy"),
                    params={"path": str(src_path)},
                    inputs=(extracted_ref,),
                    outputs=(
                        ArtifactDecl(
                            logical_name=f"{stem}.cue",
                            kind="cue_bin",
                            retention=Retention.TERMINAL,
                        ),
                    ),
                )
                actions.append(passthrough_act)
                step += 1
            else:
                # ── Step C: chdman ────────────────────────────────────
                chd_act = Action(
                    action_id=make_action_id(str(unit.unit_id), step, "chdman"),
                    tool="chdman",
                    tool_version=probe_tool_version("chdman"),
                    params={"compression": "dvd"},
                    inputs=(extracted_ref,),
                    outputs=(
                        ArtifactDecl(
                            logical_name=f"{stem}.chd",
                            kind="chd",
                            retention=Retention.TERMINAL,
                        ),
                    ),
                )
                actions.append(chd_act)
                chd_action_ids.append(chd_act.action_id)
                step += 1

        # ── M3U for multi-disc CHD sets ────────────────────────────────
        if unit.is_multi_disc and not self._no_chd and chd_action_ids:
            m3u_inputs = tuple(PendingRef(aid, 0) for aid in chd_action_ids)
            m3u_entries = ",".join(f"{d.source.path.stem}.chd" for d in unit.discs)
            m3u_act = Action(
                action_id=make_action_id(str(unit.unit_id), step, "m3u-create"),
                tool="m3u-create",
                tool_version=static_tool_version("m3u-create"),
                params={
                    "entries": m3u_entries,
                    "name": f"{unit.canonical_name}.m3u",
                },
                inputs=m3u_inputs,
                outputs=(
                    ArtifactDecl(
                        logical_name=f"{unit.canonical_name}.m3u",
                        kind="m3u",
                        retention=Retention.TERMINAL,
                    ),
                ),
            )
            actions.append(m3u_act)

        return UnitPlan(
            unit=unit,
            actions=tuple(actions),
            predicted_output_bytes=unit.source_size,
            prediction=zero_prediction(),
        )
