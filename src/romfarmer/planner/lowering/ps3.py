"""PS3 lowering rule — PS3 JB folder decryption / tree build.

Stage sequence this replaces (``stages/builder.py::_ps3_stages`` /
``stages/transform_ps3.py::TransformPS3Stage``).

IR action sequence:
    source-copy       (INTERMEDIATE)  — ingest source ZIP into CAS
    unzip             (INTERMEDIATE)  — extract encrypted .iso from ZIP
    ps3-dkey-lookup   (INTERMEDIATE)  — filesystem lookup of the .dkey
                                        (zero CAS inputs; keyed on params)
    ps3dec            (INTERMEDIATE)  — decrypt .iso using the .dkey
    ps3-extract-tree  (TERMINAL)      — 7z-extract → PS3_GAME/ folder tree

PS3 updates (DLC) are acquired separately; this lowering just models the
base game transform.  Updates become acquisition actions in a future
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
    static_tool_version,
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

        # ── unzip → encrypted .iso ───────────────────────────────────────
        unzip_act = Action(
            action_id=make_action_id(str(unit.unit_id), step, "unzip"),
            tool="unzip",
            tool_version=static_tool_version("unzip"),
            params={},
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

        # ── ps3-dkey-lookup (zero CAS inputs — filesystem lookup) ────────
        keys_directory = getattr(manifest, "ps3_keys_directory", None) or ""
        dkey_act = Action(
            action_id=make_action_id(str(unit.unit_id), step, "ps3-dkey-lookup"),
            tool="ps3-dkey-lookup",
            tool_version=static_tool_version("ps3-dkey-lookup"),
            params={"keys_directory": keys_directory, "stem": stem},
            inputs=(),
            outputs=(
                ArtifactDecl(
                    logical_name=f"{stem}.dkey",
                    kind="dkey",
                    retention=Retention.INTERMEDIATE,
                ),
            ),
        )
        actions.append(dkey_act)
        step += 1
        dkey_ref: InputRef = PendingRef(dkey_act.action_id, 0)

        # ── ps3dec ─────────────────────────────────────────────────────
        # Tool name must match the registered PS3DecTransform (name="ps3dec").
        # Two inputs: [encrypted_iso, dkey_file] (positional, per PS3DecTransform).
        decrypt_act = Action(
            action_id=make_action_id(str(unit.unit_id), step, "ps3dec"),
            tool="ps3dec",
            tool_version=probe_tool_version("ps3dec"),
            params={},
            inputs=(iso_ref, dkey_ref),
            outputs=(
                ArtifactDecl(
                    logical_name=f"{stem}.iso",
                    kind="iso",
                    retention=Retention.INTERMEDIATE,
                ),
            ),
        )
        actions.append(decrypt_act)
        step += 1
        dec_ref: InputRef = PendingRef(decrypt_act.action_id, 0)

        # ── ps3-extract-tree (TERMINAL, folder-shaped artifact) ──────────
        extract_act = Action(
            action_id=make_action_id(str(unit.unit_id), step, "ps3-extract-tree"),
            tool="ps3-extract-tree",
            tool_version=static_tool_version("ps3-extract-tree"),
            params={},
            inputs=(dec_ref,),
            outputs=(
                ArtifactDecl(
                    logical_name=stem,
                    kind="tree",
                    retention=Retention.TERMINAL,
                ),
            ),
        )
        actions.append(extract_act)

        return UnitPlan(
            unit=unit,
            actions=tuple(actions),
            predicted_output_bytes=unit.source_size,
            prediction=zero_prediction(),
        )
