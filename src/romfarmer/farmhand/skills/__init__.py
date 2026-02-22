"""Farm-Hand Skill System — reusable agent procedures and artifacts.

Skills are markdown contracts (SKILL.md) paired with machine-readable
procedures (procedure.yaml) and optional artifacts (scripts, lists, configs).
They enable the AI agent to:

- Capture successful multi-step workflows for replay
- Store scripts and tools it creates for future reuse
- Accumulate curated game lists and build recipes
- Reduce wasted rounds across sessions

Dual-path resolution:
  library/  — bundled seed skills (read-only, shipped with farm-hand)
  config/farmhand/skills/  — agent-created/user-edited (read-write)
"""

from romfarmer.farmhand.skills.models import (
    Skill,
    SkillArtifact,
    SkillCategory,
    SkillMeta,
    SkillParam,
    SkillStep,
    StepAction,
)
from romfarmer.farmhand.skills.store import SkillStore

__all__ = [
    "Skill",
    "SkillArtifact",
    "SkillCategory",
    "SkillMeta",
    "SkillParam",
    "SkillStep",
    "SkillStore",
    "StepAction",
]
