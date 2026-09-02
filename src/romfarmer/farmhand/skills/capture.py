"""SkillCapture — auto-capture successful workflows as reusable skills.

When the agent completes a multi-step workflow successfully, this module
distills the sequence of tool calls, commands, and decisions into a
Skill with a SKILL.md contract and procedure.yaml.

Usage:
    recorder = SkillRecorder()
    recorder.start("deploy psx to batocera within 60GB budget")

    # ... agent does work, recording each step ...
    recorder.record_step(action="mcp_call", tool="farmhand_connect", ...)
    recorder.record_step(action="shell", command="romfarmer build psx ...", ...)

    # On success, capture as a skill
    skill = recorder.capture(
        name="deploy-psx-budget",
        category=SkillCategory.DEPLOYMENT,
        tags=["deployment", "budget", "disc-based"],
    )
    store.save(skill)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from romfarmer.farmhand.skills.models import (
    Skill,
    SkillArtifact,
    SkillCategory,
    SkillMeta,
    SkillParam,
    SkillStep,
    StepAction,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Step recording
# ---------------------------------------------------------------------------


class RecordedStep:
    """A single step captured during workflow execution."""

    def __init__(
        self,
        action: str,
        description: str = "",
        tool: str = "",
        command: str = "",
        args: dict[str, Any] | None = None,
        result: Any = None,
        exit_code: int | None = None,
        success: bool = True,
        duration_ms: int = 0,
    ) -> None:
        self.action = action
        self.description = description
        self.tool = tool
        self.command = command
        self.args = args or {}
        self.result = result
        self.exit_code = exit_code
        self.success = success
        self.duration_ms = duration_ms
        self.timestamp = datetime.now()


# ---------------------------------------------------------------------------
# SkillRecorder
# ---------------------------------------------------------------------------


class SkillRecorder:
    """Records agent actions during a workflow for later skill capture.

    This is the primary interface the agent uses to build up a skill
    from a successful workflow execution.
    """

    def __init__(self) -> None:
        self._task_description: str = ""
        self._steps: list[RecordedStep] = []
        self._artifacts: list[tuple[str, str, str]] = []  # (filename, content, type)
        self._params_observed: dict[str, Any] = {}
        self._tools_used: set[str] = set()
        self._started: datetime | None = None
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def step_count(self) -> int:
        return len(self._steps)

    def start(self, task_description: str) -> None:
        """Begin recording a new workflow.

        Parameters
        ----------
        task_description
            Natural language description of what the agent is doing.
        """
        self._task_description = task_description
        self._steps.clear()
        self._artifacts.clear()
        self._params_observed.clear()
        self._tools_used.clear()
        self._started = datetime.now()
        self._active = True
        logger.info("Skill recording started: %s", task_description)

    def record_step(
        self,
        action: str,
        description: str = "",
        tool: str = "",
        command: str = "",
        args: dict[str, Any] | None = None,
        result: Any = None,
        exit_code: int | None = None,
        success: bool = True,
        duration_ms: int = 0,
    ) -> None:
        """Record a single step in the workflow.

        Parameters
        ----------
        action
            Step type: "mcp_call", "shell", "ssh", "python", "decision"
        description
            Human-readable explanation of what this step does.
        tool
            MCP tool name (for mcp_call actions).
        command
            Shell/SSH command (for shell/ssh actions).
        args
            Arguments passed to MCP tools.
        result
            The output/result of the step.
        exit_code
            Shell command exit code (None for non-shell steps).
        success
            Whether the step succeeded.
        duration_ms
            How long the step took in milliseconds.
        """
        if not self._active:
            logger.warning("record_step called but recorder is not active")
            return

        step = RecordedStep(
            action=action,
            description=description,
            tool=tool,
            command=command,
            args=args,
            result=result,
            exit_code=exit_code,
            success=success,
            duration_ms=duration_ms,
        )
        self._steps.append(step)

        if tool:
            self._tools_used.add(tool)

    def record_param(self, name: str, value: Any) -> None:
        """Record a parameter value observed during the workflow.

        These become template variables in the captured procedure.
        """
        self._params_observed[name] = value

    def record_artifact(
        self,
        filename: str,
        content: str,
        artifact_type: str = "file",
        description: str = "",
    ) -> None:
        """Record a file artifact created during the workflow.

        Parameters
        ----------
        filename
            Relative filename for the artifact.
        content
            File content as text.
        artifact_type
            Type: script, list, config, template, data.
        description
            What this artifact is for.
        """
        self._artifacts.append((filename, content, artifact_type))

    def cancel(self) -> None:
        """Cancel the current recording without capturing."""
        self._active = False
        self._steps.clear()
        self._artifacts.clear()
        logger.info("Skill recording cancelled")

    # -- Capture ---------------------------------------------------------------

    def capture(
        self,
        name: str,
        description: str = "",
        category: SkillCategory = SkillCategory.WORKFLOW,
        tags: list[str] | None = None,
        platforms: list[str] | None = None,
        targets: list[str] | None = None,
        preconditions: list[str] | None = None,
    ) -> Skill:
        """Distill the recorded workflow into a reusable Skill.

        Analyzes the recorded steps to:
        - Extract template parameters from observed values
        - Build a procedure.yaml from the step sequence
        - Generate a SKILL.md body from step descriptions
        - Collect artifact metadata

        Parameters
        ----------
        name
            Skill slug (lowercase, hyphens).
        description
            One-line summary. Defaults to the task description.
        category
            Skill category.
        tags, platforms, targets, preconditions
            Optional metadata filters.

        Returns
        -------
        Skill
            The captured skill, ready to save via SkillStore.save().
        """
        if not self._active:
            raise RuntimeError("Cannot capture — recorder is not active")

        if not description:
            description = self._task_description

        # Build params from observed values
        params = self._extract_params()

        # Build procedure steps
        steps = self._build_procedure(params)

        # Build artifacts list
        artifacts = [
            SkillArtifact(
                filename=fname,
                artifact_type=atype,
                description="",
                executable=atype == "script",
            )
            for fname, _, atype in self._artifacts
        ]

        # Generate markdown body
        body = self._generate_body()

        meta = SkillMeta(
            name=name,
            description=description,
            category=category,
            author="agent",
            created=self._started or datetime.now(),
            updated=datetime.now(),
            tags=tags or [],
            platforms=platforms or [],
            targets=targets or [],
            params=params,
            preconditions=preconditions or [],
            tools_used=sorted(self._tools_used),
            artifacts=artifacts,
        )

        skill = Skill(meta=meta, body=body, steps=steps)

        self._active = False
        logger.info(
            "Captured skill '%s' with %d steps and %d artifacts",
            name,
            len(steps),
            len(artifacts),
        )
        return skill

    # -- Internal helpers ------------------------------------------------------

    def _extract_params(self) -> list[SkillParam]:
        """Convert observed parameter values into SkillParam definitions."""
        params: list[SkillParam] = []
        for pname, pvalue in self._params_observed.items():
            ptype = "string"
            if isinstance(pvalue, bool):
                ptype = "boolean"
            elif isinstance(pvalue, (int, float)):
                ptype = "number"
            elif isinstance(pvalue, list):
                ptype = "list"

            params.append(
                SkillParam(
                    name=pname,
                    type=ptype,
                    required=True,
                    default=pvalue,
                )
            )
        return params

    def _build_procedure(self, params: list[SkillParam]) -> list[SkillStep]:
        """Convert recorded steps into templatized SkillSteps.

        Replaces observed parameter values with ``{{param_name}}``
        template variables in commands and args.
        """
        param_values = {p.name: self._params_observed[p.name] for p in params}
        steps: list[SkillStep] = []

        for i, recorded in enumerate(self._steps):
            if not recorded.success:
                continue  # Skip failed steps

            step_id = recorded.tool or f"step_{i + 1}"
            # Deduplicate step IDs
            existing_ids = {s.id for s in steps}
            if step_id in existing_ids:
                step_id = f"{step_id}_{i + 1}"

            try:
                action = StepAction(recorded.action)
            except ValueError:
                action = StepAction.SHELL

            # Templatize command
            command = self._templatize(recorded.command, param_values)

            # Templatize args
            args = {}
            for k, v in recorded.args.items():
                if isinstance(v, str):
                    args[k] = self._templatize(v, param_values)
                else:
                    args[k] = v

            steps.append(
                SkillStep(
                    id=step_id,
                    description=recorded.description,
                    action=action,
                    tool=recorded.tool,
                    command=command,
                    args=args,
                    expect_exit=recorded.exit_code
                    if action in (StepAction.SHELL, StepAction.SSH)
                    else None,
                )
            )

        return steps

    @staticmethod
    def _templatize(text: str, param_values: dict[str, Any]) -> str:
        """Replace concrete parameter values with {{param}} templates.

        Longer values are replaced first to avoid partial matches.
        """
        if not text or not param_values:
            return text

        # Sort by value length descending (replace longer values first)
        sorted_params = sorted(
            param_values.items(),
            key=lambda kv: len(str(kv[1])),
            reverse=True,
        )
        for pname, pvalue in sorted_params:
            str_val = str(pvalue)
            if str_val and str_val in text:
                text = text.replace(str_val, "{{" + pname + "}}")
        return text

    def _generate_body(self) -> str:
        """Generate SKILL.md body markdown from recorded steps."""
        lines: list[str] = []

        # Title
        clean_desc = self._task_description or "Untitled Workflow"
        lines.append(f"# {clean_desc}")
        lines.append("")

        # When to use
        lines.append("## When to use")
        lines.append(f"Use this skill when you need to: {clean_desc.lower()}")
        lines.append("")

        # Steps
        lines.append("## Steps")
        for i, step in enumerate(self._steps, 1):
            if not step.success:
                continue
            desc = step.description or step.tool or step.command[:60]
            lines.append(f"{i}. {desc}")
        lines.append("")

        # Artifacts
        if self._artifacts:
            lines.append("## Artifacts")
            for fname, _, atype in self._artifacts:
                lines.append(f"- `{fname}` ({atype})")
            lines.append("")

        # Known issues
        lines.append("## Known issues")
        lines.append("<!-- Add known issues and edge cases here -->")
        lines.append("")

        return "\n".join(lines)
