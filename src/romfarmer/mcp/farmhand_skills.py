"""MCP tools for Farm-Hand skill system.

Exposes skill search, display, capture, and artifact management
as MCP tools for AI agent-driven workflows.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Module-level recorder — persists across tool calls in a session
_active_recorder: Optional[Any] = None


def _get_workspace_root() -> Path:
    from romfarmer.core.paths import get_paths
    return get_paths().workspace_root


def _get_store() -> Any:
    from romfarmer.farmhand.skills import SkillStore
    return SkillStore(workspace_root=_get_workspace_root())


# ---------------------------------------------------------------------------
# Tool: farmhand_skill_search
# ---------------------------------------------------------------------------


async def tool_farmhand_skill_search(
    query: str = "",
    category: str = "",
    tag: str = "",
    platform: str = "",
    target: str = "",
) -> dict[str, Any]:
    """Search the skill library. Returns matching skills with summaries.

    Combine query text with filters. All filters are AND-combined.
    """
    from romfarmer.farmhand.skills import SkillCategory

    store = _get_store()
    results = store.search(
        query=query or None,
        category=SkillCategory(category) if category else None,
        tags=[tag] if tag else None,
        platform=platform or None,
        target=target or None,
    )

    return {
        "count": len(results),
        "skills": [
            {
                "name": s.meta.name,
                "description": s.meta.description,
                "category": s.meta.category.value,
                "version": s.meta.version,
                "tags": s.meta.tags,
                "platforms": s.meta.platforms,
                "targets": s.meta.targets,
                "has_procedure": s.has_procedure,
                "artifact_count": len(s.meta.artifacts),
                "is_builtin": s.is_builtin,
            }
            for s in results
        ],
    }


# ---------------------------------------------------------------------------
# Tool: farmhand_skill_show
# ---------------------------------------------------------------------------


async def tool_farmhand_skill_show(name: str) -> dict[str, Any]:
    """Get full details of a skill including procedure steps and body.

    Returns everything needed to understand and execute the skill.
    """
    store = _get_store()
    skill = store.get(name)

    if not skill:
        return {"error": f"Skill '{name}' not found"}

    meta = skill.meta
    result: dict[str, Any] = {
        "name": meta.name,
        "description": meta.description,
        "version": meta.version,
        "category": meta.category.value,
        "author": meta.author,
        "created": str(meta.created.date()),
        "updated": str(meta.updated.date()),
        "tags": meta.tags,
        "platforms": meta.platforms,
        "targets": meta.targets,
        "tools_used": meta.tools_used,
        "preconditions": meta.preconditions,
        "is_builtin": skill.is_builtin,
        "body": skill.body,
    }

    if meta.params:
        result["params"] = [
            {
                "name": p.name,
                "type": p.type,
                "description": p.description,
                "required": p.required,
                "default": p.default,
                "enum": p.enum,
            }
            for p in meta.params
        ]

    if meta.artifacts:
        result["artifacts"] = [
            {
                "filename": a.filename,
                "description": a.description,
                "artifact_type": a.artifact_type,
                "executable": a.executable,
            }
            for a in meta.artifacts
        ]

    if skill.steps:
        result["procedure_steps"] = [
            {
                "id": step.id,
                "description": step.description,
                "action": step.action.value,
                "tool": step.tool,
                "command": step.command,
                "args": step.args,
                "condition": step.condition,
                "on_failure": step.on_failure,
            }
            for step in skill.steps
        ]

    return result


# ---------------------------------------------------------------------------
# Tool: farmhand_skill_artifact
# ---------------------------------------------------------------------------


async def tool_farmhand_skill_artifact(
    skill_name: str, filename: str
) -> dict[str, Any]:
    """Retrieve the contents of an artifact file from a skill.

    Use this to read scripts, game lists, configs, etc. bundled in skills.
    """
    store = _get_store()
    skill = store.get(skill_name)

    if not skill:
        return {"error": f"Skill '{skill_name}' not found"}

    content = store.get_artifact_content(skill_name, filename)
    if content is None:
        available = [a.filename for a in skill.meta.artifacts]
        return {
            "error": f"Artifact '{filename}' not found in skill '{skill_name}'",
            "available_artifacts": available,
        }

    return {
        "skill": skill_name,
        "filename": filename,
        "content": content,
    }


# ---------------------------------------------------------------------------
# Tool: farmhand_skill_save
# ---------------------------------------------------------------------------


async def tool_farmhand_skill_save(
    name: str,
    description: str,
    category: str,
    body: str = "",
    tags: str = "",
    platforms: str = "",
    targets: str = "",
    tools_used: str = "",
    preconditions: str = "",
) -> dict[str, Any]:
    """Create or update a user skill from explicit parameters.

    Use this when the agent wants to persist a skill directly rather
    than through the capture workflow.

    Comma-separated strings for tags, platforms, targets, tools_used, preconditions.
    """
    from romfarmer.farmhand.skills import Skill, SkillCategory, SkillMeta

    try:
        meta = SkillMeta(
            name=name,
            description=description,
            category=SkillCategory(category),
            tags=[t.strip() for t in tags.split(",") if t.strip()] if tags else [],
            platforms=[p.strip() for p in platforms.split(",") if p.strip()] if platforms else [],
            targets=[t.strip() for t in targets.split(",") if t.strip()] if targets else [],
            tools_used=[t.strip() for t in tools_used.split(",") if t.strip()] if tools_used else [],
            preconditions=[p.strip() for p in preconditions.split(",") if p.strip()] if preconditions else [],
        )

        skill = Skill(meta=meta, body=body, steps=[], is_builtin=False)

        store = _get_store()
        store.save(skill)

        return {
            "saved": True,
            "name": name,
            "category": category,
            "message": f"Skill '{name}' saved successfully.",
        }
    except Exception as exc:
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Tool: farmhand_skill_save_artifact
# ---------------------------------------------------------------------------


async def tool_farmhand_skill_save_artifact(
    skill_name: str,
    filename: str,
    content: str,
    description: str = "",
    artifact_type: str = "script",
    executable: bool = False,
) -> dict[str, Any]:
    """Save an artifact file to a user skill.

    Creates the skill directory if needed. The artifact is stored as a plain
    file alongside the SKILL.md. Also updates the skill metadata.
    """
    store = _get_store()
    skill = store.get(skill_name)

    if skill and skill.is_builtin:
        return {"error": f"Cannot add artifacts to builtin skill '{skill_name}'"}

    try:
        store.save_artifact(skill_name, filename, content, executable=executable)

        # If the skill exists, update its artifact list in metadata
        if skill:
            from romfarmer.farmhand.skills import SkillArtifact
            existing_filenames = {a.filename for a in skill.meta.artifacts}
            if filename not in existing_filenames:
                skill.meta.artifacts.append(
                    SkillArtifact(
                        filename=filename,
                        description=description,
                        artifact_type=artifact_type,
                        executable=executable,
                    )
                )
                store.save(skill)

        return {
            "saved": True,
            "skill": skill_name,
            "filename": filename,
            "message": f"Artifact '{filename}' saved to skill '{skill_name}'.",
        }
    except Exception as exc:
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Tool: farmhand_skill_capture_start
# ---------------------------------------------------------------------------


async def tool_farmhand_skill_capture_start(
    task_description: str,
) -> dict[str, Any]:
    """Begin recording agent actions for skill auto-capture.

    Call this when starting a workflow you want to save as a reusable skill.
    Then call farmhand_skill_capture_step for each significant action.
    Finally call farmhand_skill_capture_finish to save the skill.

    Only one recording can be active at a time.
    """
    global _active_recorder

    from romfarmer.farmhand.skills.capture import SkillRecorder

    if _active_recorder is not None and _active_recorder.is_active:
        return {
            "error": "A recording is already active. Finish or cancel it first.",
            "step_count": _active_recorder.step_count,
        }

    _active_recorder = SkillRecorder()
    _active_recorder.start(task_description)

    return {
        "recording": True,
        "task": task_description,
        "message": "Recording started. Use farmhand_skill_capture_step for each action.",
    }


# ---------------------------------------------------------------------------
# Tool: farmhand_skill_capture_step
# ---------------------------------------------------------------------------


async def tool_farmhand_skill_capture_step(
    action: str,
    description: str = "",
    tool: str = "",
    command: str = "",
    args: str = "",
    result: str = "",
    success: bool = True,
) -> dict[str, Any]:
    """Record a step in the active skill capture session.

    Parameters
    ----------
    action
        Step type: mcp_call, shell, ssh, python, decision
    description
        What this step does
    tool
        Tool/function name (for mcp_call)
    command
        Shell command (for shell/ssh)
    args
        JSON-encoded arguments dict
    result
        Brief result/output summary
    success
        Whether the step succeeded
    """
    global _active_recorder

    if _active_recorder is None or not _active_recorder.is_active:
        return {"error": "No active recording. Call farmhand_skill_capture_start first."}

    import json as json_mod
    parsed_args = {}
    if args:
        try:
            parsed_args = json_mod.loads(args)
        except json_mod.JSONDecodeError:
            parsed_args = {"raw": args}

    _active_recorder.record_step(
        action=action,
        description=description,
        tool=tool,
        command=command,
        args=parsed_args,
        result=result,
        success=success,
    )

    return {
        "recorded": True,
        "step_count": _active_recorder.step_count,
        "action": action,
    }


# ---------------------------------------------------------------------------
# Tool: farmhand_skill_capture_finish
# ---------------------------------------------------------------------------


async def tool_farmhand_skill_capture_finish(
    name: str,
    description: str = "",
    category: str = "workflow",
    tags: str = "",
    platforms: str = "",
    targets: str = "",
    save: bool = True,
) -> dict[str, Any]:
    """Finish recording and optionally save the captured skill.

    Converts the recorded steps into a Skill with SKILL.md and procedure.yaml,
    then saves it to the user skill directory.

    Parameters
    ----------
    name
        Skill name (slug format: lowercase, hyphens)
    description
        Override description (default: auto-generated from task)
    category
        Skill category
    tags
        Comma-separated tags
    platforms, targets
        Comma-separated platform/target filters
    save
        Whether to save immediately (default: True)
    """
    global _active_recorder

    if _active_recorder is None or not _active_recorder.is_active:
        return {"error": "No active recording to finish."}

    from romfarmer.farmhand.skills import SkillCategory

    try:
        skill = _active_recorder.capture(
            name=name,
            description=description or None,
            category=SkillCategory(category),
            tags=[t.strip() for t in tags.split(",") if t.strip()] if tags else None,
            platforms=[p.strip() for p in platforms.split(",") if p.strip()] if platforms else None,
            targets=[t.strip() for t in targets.split(",") if t.strip()] if targets else None,
        )

        result: dict[str, Any] = {
            "captured": True,
            "name": skill.meta.name,
            "description": skill.meta.description,
            "category": skill.meta.category.value,
            "step_count": len(skill.steps),
            "param_count": len(skill.meta.params),
        }

        if save:
            store = _get_store()
            store.save(skill)
            result["saved"] = True
            result["message"] = f"Skill '{name}' captured and saved ({len(skill.steps)} steps)."
        else:
            result["saved"] = False
            result["message"] = f"Skill '{name}' captured but not saved."

        _active_recorder = None
        return result
    except Exception as exc:
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Tool: farmhand_skill_capture_cancel
# ---------------------------------------------------------------------------


async def tool_farmhand_skill_capture_cancel() -> dict[str, Any]:
    """Cancel the active skill capture session without saving."""
    global _active_recorder

    if _active_recorder is None or not _active_recorder.is_active:
        return {"error": "No active recording to cancel."}

    steps = _active_recorder.step_count
    _active_recorder.cancel()
    _active_recorder = None

    return {
        "cancelled": True,
        "steps_discarded": steps,
        "message": "Recording cancelled.",
    }
