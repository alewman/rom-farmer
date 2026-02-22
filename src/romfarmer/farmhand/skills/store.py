"""SkillStore — load, search, and manage Farm-Hand skills.

Dual-path resolution:
  1. library/  — bundled seed skills shipped with farm-hand (read-only)
  2. config/farmhand/skills/  — agent-created / user-edited (read-write)

Agent-created skills shadow bundled ones with the same name.
"""

from __future__ import annotations

import logging
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml

from romfarmer.farmhand.skills.models import (
    Skill,
    SkillArtifact,
    SkillCategory,
    SkillMeta,
    SkillParam,
    SkillStep,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# YAML frontmatter parsing
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(
    r"^---\s*\n(.*?)\n---\s*\n?(.*)",
    re.DOTALL,
)


def _parse_skill_md(text: str) -> tuple[dict[str, Any], str]:
    """Parse SKILL.md into (frontmatter_dict, body_markdown)."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    raw_fm = m.group(1)
    body = m.group(2)
    try:
        fm = yaml.safe_load(raw_fm) or {}
    except yaml.YAMLError as exc:
        logger.warning("Failed to parse SKILL.md frontmatter: %s", exc)
        fm = {}
    return fm, body


def _frontmatter_to_meta(fm: dict[str, Any]) -> SkillMeta:
    """Convert parsed frontmatter dict to a SkillMeta model."""
    # Normalize params from dict-of-dicts to list-of-SkillParam
    raw_params = fm.pop("params", {})
    params: list[SkillParam] = []
    if isinstance(raw_params, dict):
        for pname, pdef in raw_params.items():
            if isinstance(pdef, dict):
                params.append(SkillParam(name=pname, **pdef))
            else:
                params.append(SkillParam(name=pname, default=pdef))
    elif isinstance(raw_params, list):
        for item in raw_params:
            if isinstance(item, dict) and "name" in item:
                params.append(SkillParam(**item))

    # Normalize artifacts
    raw_artifacts = fm.pop("artifacts", [])
    artifacts: list[SkillArtifact] = []
    for art in raw_artifacts:
        if isinstance(art, dict):
            artifacts.append(SkillArtifact(**art))
        elif isinstance(art, str):
            artifacts.append(SkillArtifact(filename=art))

    # Normalize category
    raw_cat = fm.pop("category", "workflow")
    try:
        category = SkillCategory(raw_cat)
    except ValueError:
        category = SkillCategory.WORKFLOW

    return SkillMeta(
        category=category,
        params=params,
        artifacts=artifacts,
        **{k: v for k, v in fm.items() if k in SkillMeta.model_fields},
    )


def _meta_to_frontmatter(meta: SkillMeta) -> str:
    """Serialize SkillMeta back to YAML frontmatter string."""
    data: dict[str, Any] = {
        "name": meta.name,
        "description": meta.description,
        "version": meta.version,
        "category": meta.category.value,
        "author": meta.author,
        "created": meta.created.isoformat(),
        "updated": meta.updated.isoformat(),
    }
    if meta.tags:
        data["tags"] = meta.tags
    if meta.platforms:
        data["platforms"] = meta.platforms
    if meta.targets:
        data["targets"] = meta.targets
    if meta.preconditions:
        data["preconditions"] = meta.preconditions
    if meta.tools_used:
        data["tools_used"] = meta.tools_used

    # Params as dict-of-dicts (compact frontmatter style)
    if meta.params:
        params_dict: dict[str, Any] = {}
        for p in meta.params:
            pdef: dict[str, Any] = {"type": p.type}
            if p.description:
                pdef["description"] = p.description
            if p.required:
                pdef["required"] = True
            if p.default is not None:
                pdef["default"] = p.default
            if p.enum:
                pdef["enum"] = p.enum
            params_dict[p.name] = pdef
        data["params"] = params_dict

    # Artifacts
    if meta.artifacts:
        data["artifacts"] = [
            {
                "filename": a.filename,
                "description": a.description,
                "artifact_type": a.artifact_type,
                **({"executable": True} if a.executable else {}),
            }
            for a in meta.artifacts
        ]

    return yaml.dump(data, default_flow_style=False, sort_keys=False, width=120)


# ---------------------------------------------------------------------------
# Procedure YAML loading / saving
# ---------------------------------------------------------------------------


def _load_procedure(path: Path) -> list[SkillStep]:
    """Load procedure.yaml from a skill folder."""
    proc_file = path / "procedure.yaml"
    if not proc_file.exists():
        return []
    try:
        raw = yaml.safe_load(proc_file.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        logger.warning("Failed to parse procedure.yaml in %s: %s", path, exc)
        return []

    steps_raw = raw.get("steps", [])
    steps: list[SkillStep] = []
    for step_dict in steps_raw:
        if isinstance(step_dict, dict):
            try:
                steps.append(SkillStep(**step_dict))
            except Exception as exc:
                logger.warning("Skipping invalid step in %s: %s", path, exc)
    return steps


def _save_procedure(steps: list[SkillStep], path: Path) -> None:
    """Save procedure steps to procedure.yaml."""
    if not steps:
        return
    proc_file = path / "procedure.yaml"
    data = {
        "steps": [
            {k: v for k, v in step.model_dump(mode="json").items() if v}
            for step in steps
        ]
    }
    proc_file.write_text(
        yaml.dump(data, default_flow_style=False, sort_keys=False, width=120),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# SkillStore
# ---------------------------------------------------------------------------


class SkillStore:
    """Load, search, and manage Farm-Hand skills.

    Parameters
    ----------
    workspace_root
        Root of the rom-farmer project (for resolving config/ paths).
    library_path
        Path to the bundled skill library (defaults to skills/library/
        within the farmhand package).
    user_path
        Path to user/agent-created skills (defaults to
        config/farmhand/skills/ under workspace_root).
    """

    def __init__(
        self,
        workspace_root: Optional[Path] = None,
        library_path: Optional[Path] = None,
        user_path: Optional[Path] = None,
    ) -> None:
        self._workspace_root = workspace_root or Path.cwd()

        self._library_path = library_path or (
            Path(__file__).parent / "library"
        )
        self._user_path = user_path or (
            self._workspace_root / "config" / "farmhand" / "skills"
        )

        # Lazy-loaded cache
        self._cache: dict[str, Skill] = {}
        self._loaded = False

    @property
    def library_path(self) -> Path:
        return self._library_path

    @property
    def user_path(self) -> Path:
        return self._user_path

    # -- Loading ---------------------------------------------------------------

    def _ensure_loaded(self) -> None:
        """Load all skills from both paths (lazy, on first access)."""
        if self._loaded:
            return
        self._cache.clear()

        # Load bundled first (lower priority)
        if self._library_path.is_dir():
            for skill_dir in sorted(self._library_path.iterdir()):
                if skill_dir.is_dir() and self._has_skill_md(skill_dir):
                    skill = self._load_skill_from_dir(skill_dir, is_builtin=True)
                    if skill:
                        self._cache[skill.name] = skill

        # Load user skills (higher priority — shadows bundled)
        if self._user_path.is_dir():
            for skill_dir in sorted(self._user_path.iterdir()):
                if skill_dir.is_dir() and self._has_skill_md(skill_dir):
                    skill = self._load_skill_from_dir(skill_dir, is_builtin=False)
                    if skill:
                        self._cache[skill.name] = skill

        self._loaded = True
        logger.info(
            "Loaded %d skills (%d bundled, %d user)",
            len(self._cache),
            sum(1 for s in self._cache.values() if s.is_builtin),
            sum(1 for s in self._cache.values() if not s.is_builtin),
        )

    @staticmethod
    def _has_skill_md(path: Path) -> bool:
        """Check if a directory contains a SKILL.md."""
        return (path / "SKILL.md").exists() or (path / "skill.md").exists()

    @staticmethod
    def _find_skill_md(path: Path) -> Optional[Path]:
        """Find the SKILL.md file in a directory (case-flexible)."""
        for name in ("SKILL.md", "skill.md"):
            p = path / name
            if p.exists():
                return p
        return None

    def _load_skill_from_dir(
        self, path: Path, is_builtin: bool = False
    ) -> Optional[Skill]:
        """Load a Skill from a directory."""
        skill_md = self._find_skill_md(path)
        if not skill_md:
            return None
        try:
            text = skill_md.read_text(encoding="utf-8")
            fm, body = _parse_skill_md(text)
            if "name" not in fm:
                fm["name"] = path.name  # Use folder name as fallback
            meta = _frontmatter_to_meta(fm)
            steps = _load_procedure(path)
            return Skill(
                meta=meta,
                body=body,
                steps=steps,
                source_path=path,
                is_builtin=is_builtin,
            )
        except Exception as exc:
            logger.warning("Failed to load skill from %s: %s", path, exc)
            return None

    def reload(self) -> None:
        """Force reload of all skills from disk."""
        self._loaded = False
        self._ensure_loaded()

    # -- Query ----------------------------------------------------------------

    def list_all(self) -> list[Skill]:
        """Return all loaded skills."""
        self._ensure_loaded()
        return list(self._cache.values())

    def get(self, name: str) -> Optional[Skill]:
        """Get a skill by exact name."""
        self._ensure_loaded()
        return self._cache.get(name)

    def search(
        self,
        query: str = "",
        category: Optional[SkillCategory] = None,
        tags: Optional[list[str]] = None,
        platform: Optional[str] = None,
        target: Optional[str] = None,
    ) -> list[Skill]:
        """Search skills by text query, category, tags, platform, target.

        Text query matches against name, description, and tags (case-insensitive).
        All filters are AND-combined.
        """
        self._ensure_loaded()
        results: list[Skill] = []
        query_lower = query.lower()

        for skill in self._cache.values():
            # Text match
            if query_lower:
                searchable = " ".join([
                    skill.meta.name,
                    skill.meta.description,
                    " ".join(skill.meta.tags),
                    skill.meta.category.value,
                ]).lower()
                if query_lower not in searchable:
                    continue

            # Category filter
            if category and skill.meta.category != category:
                continue

            # Tag filter (any match)
            if tags:
                skill_tags = set(t.lower() for t in skill.meta.tags)
                if not any(t.lower() in skill_tags for t in tags):
                    continue

            # Platform filter
            if platform:
                if skill.meta.platforms and platform.lower() not in [
                    p.lower() for p in skill.meta.platforms
                ]:
                    continue

            # Target frontend filter
            if target:
                if skill.meta.targets and target.lower() not in [
                    t.lower() for t in skill.meta.targets
                ]:
                    continue

            results.append(skill)

        return results

    def list_categories(self) -> dict[SkillCategory, int]:
        """Return category → count mapping."""
        self._ensure_loaded()
        counts: dict[SkillCategory, int] = {}
        for skill in self._cache.values():
            counts[skill.meta.category] = counts.get(skill.meta.category, 0) + 1
        return counts

    def list_tags(self) -> dict[str, int]:
        """Return tag → count mapping across all skills."""
        self._ensure_loaded()
        counts: dict[str, int] = {}
        for skill in self._cache.values():
            for tag in skill.meta.tags:
                counts[tag] = counts.get(tag, 0) + 1
        return counts

    # -- CRUD (user skills only) -----------------------------------------------

    def save(self, skill: Skill) -> Path:
        """Save a skill to the user skills directory.

        Creates or updates the skill folder with SKILL.md, procedure.yaml,
        and any artifact files.

        Returns the path to the saved skill folder.
        """
        skill_dir = self._user_path / skill.meta.name
        skill_dir.mkdir(parents=True, exist_ok=True)

        # Write SKILL.md
        skill.meta.updated = datetime.now()
        frontmatter = _meta_to_frontmatter(skill.meta)
        skill_md = f"---\n{frontmatter}---\n\n{skill.body}"
        (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

        # Write procedure.yaml
        if skill.steps:
            _save_procedure(skill.steps, skill_dir)

        # Update cache
        saved_skill = skill.model_copy(
            update={"source_path": skill_dir, "is_builtin": False}
        )
        self._cache[skill.meta.name] = saved_skill

        logger.info("Saved skill '%s' to %s", skill.meta.name, skill_dir)
        return skill_dir

    def save_artifact(
        self, skill_name: str, filename: str, content: str | bytes
    ) -> Path:
        """Save an artifact file to a skill's folder.

        Parameters
        ----------
        skill_name
            Name of the skill to add the artifact to.
        filename
            Relative filename within the skill folder.
        content
            File content (str for text, bytes for binary).

        Returns the path to the saved artifact.
        """
        skill_dir = self._user_path / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = skill_dir / filename

        # Create subdirectories if needed
        artifact_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, bytes):
            artifact_path.write_bytes(content)
        else:
            artifact_path.write_text(content, encoding="utf-8")

        logger.info(
            "Saved artifact '%s' for skill '%s'", filename, skill_name
        )
        return artifact_path

    def delete(self, name: str) -> bool:
        """Delete a user skill (cannot delete bundled skills).

        Returns True if deleted, False if not found or is builtin.
        """
        skill = self._cache.get(name)
        if not skill:
            return False
        if skill.is_builtin:
            logger.warning("Cannot delete bundled skill '%s'", name)
            return False
        if skill.source_path and skill.source_path.exists():
            shutil.rmtree(skill.source_path)
        self._cache.pop(name, None)
        logger.info("Deleted skill '%s'", name)
        return True

    def get_artifact_path(self, skill_name: str, filename: str) -> Optional[Path]:
        """Resolve the full path to an artifact file in a skill.

        Returns None if the skill or artifact doesn't exist.
        """
        skill = self.get(skill_name)
        if not skill or not skill.source_path:
            return None
        artifact_path = skill.source_path / filename
        if artifact_path.exists():
            return artifact_path
        return None

    def get_artifact_content(
        self, skill_name: str, filename: str
    ) -> Optional[str]:
        """Read the text content of a skill artifact."""
        path = self.get_artifact_path(skill_name, filename)
        if path:
            return path.read_text(encoding="utf-8")
        return None
