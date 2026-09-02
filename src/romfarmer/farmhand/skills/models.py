"""Pydantic models for the Farm-Hand skill system.

A Skill is a reusable unit of agent knowledge — a markdown contract
(SKILL.md) paired with a structured procedure (procedure.yaml) and
optional artifacts (scripts, curated lists, configs).
"""

from __future__ import annotations

import enum
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class SkillCategory(str, enum.Enum):
    """Broad classification of what a skill does."""

    DEPLOYMENT = "deployment"  # Deploy ROMs to a target
    BUILD = "build"  # Drive rom-farmer builds
    TARGET = "target"  # Target management (setup, migrate, audit)
    CURATION = "curation"  # Game lists, cultural picks, recommendations
    MAINTENANCE = "maintenance"  # Cleanup, sync, verify, repair
    SCRIPTING = "scripting"  # Reusable scripts / shell tools
    WORKFLOW = "workflow"  # Multi-step orchestration across tools


class StepAction(str, enum.Enum):
    """What kind of action a procedure step performs."""

    MCP_CALL = "mcp_call"  # Call an MCP tool
    SHELL = "shell"  # Run a shell command (local or remote)
    SSH = "ssh"  # Run a command on a remote target
    PYTHON = "python"  # Execute a Python snippet
    SKILL = "skill"  # Invoke another skill (composition)
    CONDITIONAL = "conditional"  # Branch based on a condition
    PROMPT = "prompt"  # Ask the agent to decide something


# ---------------------------------------------------------------------------
# Skill parameter definition
# ---------------------------------------------------------------------------


class SkillParam(BaseModel):
    """A parameter that a skill accepts.

    Parameters use Jinja2-style template variables in procedures:
    ``{{platform}}``, ``{{budget_gb}}``, etc.
    """

    name: str = Field(description="Parameter name (used as template variable)")
    type: str = Field(
        default="string",
        description="Parameter type: string, number, boolean, list, path",
    )
    description: str = Field(default="", description="What this parameter controls")
    required: bool = Field(default=False, description="Must be provided to run")
    default: Any = Field(default=None, description="Default value if not provided")
    enum: list[str] = Field(
        default_factory=list,
        description="Allowed values (empty = any)",
    )


# ---------------------------------------------------------------------------
# Procedure step
# ---------------------------------------------------------------------------


class SkillStep(BaseModel):
    """A single step in a skill's procedure.

    Steps form a linear sequence by default. Use ``depends_on`` to
    define DAG-style dependencies or ``condition`` for branches.
    """

    id: str = Field(description="Unique step identifier within the procedure")
    description: str = Field(default="", description="Human-readable explanation")
    action: StepAction = Field(description="What kind of action to perform")

    # -- Action-specific fields (only relevant fields need to be set) --
    tool: str = Field(default="", description="MCP tool name (for mcp_call actions)")
    command: str = Field(
        default="",
        description="Shell/SSH command template (for shell/ssh actions)",
    )
    args: dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments for MCP calls (supports {{param}} templates)",
    )
    code: str = Field(
        default="",
        description="Python code snippet (for python actions)",
    )
    skill_name: str = Field(
        default="",
        description="Name of skill to invoke (for skill actions)",
    )
    skill_args: dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments to pass to sub-skill",
    )

    # -- Control flow --
    condition: str = Field(
        default="",
        description="Jinja2 expression; step runs only if truthy",
    )
    depends_on: list[str] = Field(
        default_factory=list,
        description="Step IDs that must complete first",
    )
    on_failure: str = Field(
        default="abort",
        description="What to do on failure: abort, skip, retry, rollback",
    )
    retries: int = Field(default=0, description="Number of retry attempts")

    # -- Output capture --
    outputs: list[str] = Field(
        default_factory=list,
        description="Variable names to capture from step result",
    )
    expect_exit: int | None = Field(
        default=None,
        description="Expected exit code (for shell/ssh; None = don't check)",
    )


# ---------------------------------------------------------------------------
# Artifact — files bundled with the skill
# ---------------------------------------------------------------------------


class SkillArtifact(BaseModel):
    """A file bundled with a skill — a script, list, config, template, etc.

    Artifacts live in the skill folder alongside SKILL.md and procedure.yaml.
    They can be referenced by procedure steps via relative path.
    """

    filename: str = Field(description="Filename relative to skill folder")
    description: str = Field(default="", description="What this artifact is for")
    artifact_type: str = Field(
        default="file",
        description="Type: script, list, config, template, data",
    )
    executable: bool = Field(
        default=False,
        description="Whether this file should be chmod +x on deploy",
    )


# ---------------------------------------------------------------------------
# Skill metadata (maps to SKILL.md frontmatter)
# ---------------------------------------------------------------------------


class SkillMeta(BaseModel):
    """Metadata extracted from / written to SKILL.md YAML frontmatter."""

    name: str = Field(description="Unique skill identifier (slug)")
    description: str = Field(description="One-line summary of what the skill does")
    version: str = Field(default="1.0.0", description="Semver version string")
    category: SkillCategory = Field(
        default=SkillCategory.WORKFLOW,
        description="Broad classification",
    )
    author: str = Field(
        default="agent",
        description="Who created this: 'agent', 'user', or a name",
    )
    created: datetime = Field(
        default_factory=datetime.now,
        description="When the skill was first created",
    )
    updated: datetime = Field(
        default_factory=datetime.now,
        description="When the skill was last modified",
    )

    # -- Applicability --
    tags: list[str] = Field(
        default_factory=list,
        description="Searchable tags: [deployment, budget, disc-based, ...]",
    )
    platforms: list[str] = Field(
        default_factory=list,
        description="ROM platforms this skill applies to (empty = any)",
    )
    targets: list[str] = Field(
        default_factory=list,
        description="Target frontends: [batocera, rocknix, ...] (empty = any)",
    )

    # -- Requirements --
    params: list[SkillParam] = Field(
        default_factory=list,
        description="Parameters the skill accepts",
    )
    preconditions: list[str] = Field(
        default_factory=list,
        description="Conditions that must be true before running",
    )
    tools_used: list[str] = Field(
        default_factory=list,
        description="MCP tools / CLI commands this skill calls",
    )
    artifacts: list[SkillArtifact] = Field(
        default_factory=list,
        description="Bundled files (scripts, lists, configs)",
    )


# ---------------------------------------------------------------------------
# Full Skill — the loaded, ready-to-use object
# ---------------------------------------------------------------------------


class Skill(BaseModel):
    """A complete skill — metadata, procedure, and artifact info.

    Loaded from a skill folder containing:
      SKILL.md — markdown contract with YAML frontmatter
      procedure.yaml — machine-readable steps
      (optional artifacts: scripts, lists, configs, etc.)
    """

    meta: SkillMeta = Field(description="Skill metadata from SKILL.md frontmatter")
    body: str = Field(
        default="",
        description="Markdown body from SKILL.md (after frontmatter)",
    )
    steps: list[SkillStep] = Field(
        default_factory=list,
        description="Procedure steps from procedure.yaml",
    )
    source_path: Path | None = Field(
        default=None,
        description="Filesystem path to the skill folder",
    )
    is_builtin: bool = Field(
        default=False,
        description="True if loaded from bundled library (read-only)",
    )

    # -- Convenience --

    @property
    def name(self) -> str:
        return self.meta.name

    @property
    def description(self) -> str:
        return self.meta.description

    @property
    def category(self) -> SkillCategory:
        return self.meta.category

    def get_required_params(self) -> list[SkillParam]:
        """Return parameters that must be provided."""
        return [p for p in self.meta.params if p.required]

    def get_param_defaults(self) -> dict[str, Any]:
        """Return a dict of param_name → default_value for all params with defaults."""
        return {p.name: p.default for p in self.meta.params if p.default is not None}

    def get_artifacts_by_type(self, artifact_type: str) -> list[SkillArtifact]:
        """Filter artifacts by type (script, list, config, etc.)."""
        return [a for a in self.meta.artifacts if a.artifact_type == artifact_type]

    def has_procedure(self) -> bool:
        """Whether this skill has machine-readable steps."""
        return len(self.steps) > 0

    def summary(self) -> str:
        """One-line summary for display."""
        parts = [f"[{self.meta.category.value}]", self.meta.name]
        if self.meta.description:
            parts.append(f"— {self.meta.description}")
        n_steps = len(self.steps)
        n_artifacts = len(self.meta.artifacts)
        extras = []
        if n_steps:
            extras.append(f"{n_steps} steps")
        if n_artifacts:
            extras.append(f"{n_artifacts} artifacts")
        if extras:
            parts.append(f"({', '.join(extras)})")
        return " ".join(parts)
