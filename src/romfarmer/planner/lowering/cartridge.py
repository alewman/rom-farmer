"""Cartridge lowering rule — No-Intro ZIP/7z extraction + optional recompression.

Stage sequence this replaces (``stages/builder.py::_cartridge_stages``):
    [CachePreCheckStage →] ExtractArchiveStage [→ CompressArchiveStage]

IR action sequence:
    source-copy   (INTERMEDIATE)  — ingest ZIP into CAS
    unzip         (INTERMEDIATE)  — extract ROM from ZIP
    [compress]    (TERMINAL)      — optional recompression to zip or 7z

    If no recompression (passthrough format):
        source-copy + unzip, output ROM as TERMINAL
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


class CartridgeLoweringRule:
    """Lower a cartridge/ROM game unit to an action sequence."""

    def __init__(
        self,
        action_cache: object | None = None,
        fmt: str = "zip",
    ) -> None:
        self._cache = action_cache
        self._fmt = fmt  # "zip" | "7z" | "passthrough"

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
        src_out_ref: InputRef = PendingRef(src_act.action_id, 0)

        # ── unzip ──────────────────────────────────────────────────────
        unzip_act = Action(
            action_id=make_action_id(str(unit.unit_id), step, "unzip"),
            tool="unzip",
            tool_version=probe_tool_version("unzip"),
            params={"format": "cartridge"},
            inputs=(src_out_ref,),
            outputs=(
                ArtifactDecl(
                    logical_name=f"{stem}.rom",
                    kind="rom",
                    retention=Retention.INTERMEDIATE,
                ),
            ),
        )
        actions.append(unzip_act)
        step += 1
        extracted_ref: InputRef = PendingRef(unzip_act.action_id, 0)

        fmt = chain[0] if chain else self._fmt
        if fmt in ("zip", "7z"):
            # ── recompress ─────────────────────────────────────────────
            compress_act = Action(
                action_id=make_action_id(str(unit.unit_id), step, f"compress-{fmt}"),
                tool=f"compress-{fmt}",
                tool_version=probe_tool_version("7z" if fmt == "7z" else "zip"),
                params={"format": fmt},
                inputs=(extracted_ref,),
                outputs=(
                    ArtifactDecl(
                        logical_name=f"{stem}.{fmt}",
                        kind=fmt,
                        retention=Retention.TERMINAL,
                    ),
                ),
            )
            actions.append(compress_act)
        else:
            # passthrough — just mark extracted ROM as terminal
            pt_act = Action(
                action_id=make_action_id(str(unit.unit_id), step, "passthrough"),
                tool="passthrough",
                tool_version="1",
                params={},
                inputs=(extracted_ref,),
                outputs=(
                    ArtifactDecl(
                        logical_name=f"{stem}.rom",
                        kind="rom",
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
