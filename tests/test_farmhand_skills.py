"""Unit tests for the Farm-Hand skill system.

Tests: models, SkillStore, SkillRecorder (capture), and CLI output.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
import yaml

from romfarmer.farmhand.skills.capture import RecordedStep, SkillRecorder
from romfarmer.farmhand.skills.models import (
    Skill,
    SkillArtifact,
    SkillCategory,
    SkillMeta,
    SkillParam,
    SkillStep,
    StepAction,
)
from romfarmer.farmhand.skills.store import (
    SkillStore,
    _frontmatter_to_meta,
    _meta_to_frontmatter,
    _parse_skill_md,
)

# =========================================================================
# Model tests
# =========================================================================


class TestSkillCategory:
    def test_all_values(self) -> None:
        expected = {
            "deployment",
            "build",
            "target",
            "curation",
            "maintenance",
            "scripting",
            "workflow",
        }
        assert {c.value for c in SkillCategory} == expected

    def test_from_string(self) -> None:
        assert SkillCategory("deployment") == SkillCategory.DEPLOYMENT
        assert SkillCategory("workflow") == SkillCategory.WORKFLOW


class TestStepAction:
    def test_all_values(self) -> None:
        expected = {
            "mcp_call",
            "shell",
            "ssh",
            "python",
            "skill",
            "conditional",
            "prompt",
        }
        assert {a.value for a in StepAction} == expected


class TestSkillParam:
    def test_defaults(self) -> None:
        p = SkillParam(name="host")
        assert p.type == "string"
        assert p.required is False
        assert p.default is None
        assert p.enum == []

    def test_full(self) -> None:
        p = SkillParam(
            name="budget_gb",
            type="number",
            description="Storage budget in GB",
            required=True,
            default=60.0,
            enum=[],
        )
        assert p.name == "budget_gb"
        assert p.type == "number"
        assert p.required is True
        assert p.default == 60.0


class TestSkillStep:
    def test_minimal(self) -> None:
        s = SkillStep(id="step1", action=StepAction.SHELL)
        assert s.id == "step1"
        assert s.action == StepAction.SHELL
        assert s.tool == ""
        assert s.command == ""
        assert s.on_failure == "abort"

    def test_mcp_call(self) -> None:
        s = SkillStep(
            id="connect",
            description="Connect to target",
            action=StepAction.MCP_CALL,
            tool="farmhand_connect",
            args={"host": "{{host}}", "user": "root"},
        )
        assert s.tool == "farmhand_connect"
        assert s.args["host"] == "{{host}}"


class TestSkillArtifact:
    def test_defaults(self) -> None:
        a = SkillArtifact(filename="script.sh")
        assert a.artifact_type == "file"
        assert a.executable is False

    def test_executable_script(self) -> None:
        a = SkillArtifact(
            filename="deploy.sh",
            description="Deploy ROMs",
            artifact_type="script",
            executable=True,
        )
        assert a.executable is True
        assert a.artifact_type == "script"


class TestSkillMeta:
    def test_defaults(self) -> None:
        m = SkillMeta(
            name="test-skill",
            description="A test skill",
        )
        assert m.name == "test-skill"
        assert m.version == "1.0.0"
        assert m.category == SkillCategory.WORKFLOW
        assert m.author == "agent"
        assert m.tags == []
        assert m.platforms == []
        assert m.params == []
        assert m.artifacts == []

    def test_full_meta(self) -> None:
        m = SkillMeta(
            name="deploy-psx",
            description="Deploy PSX ROMs within budget",
            version="2.1.0",
            category=SkillCategory.DEPLOYMENT,
            author="user",
            tags=["deployment", "psx", "budget"],
            platforms=["psx"],
            targets=["batocera"],
            preconditions=["Target connected"],
            tools_used=["farmhand_connect", "farmhand_scan_target"],
            params=[
                SkillParam(name="budget_gb", type="number", required=True),
            ],
            artifacts=[
                SkillArtifact(filename="deploy.sh", artifact_type="script"),
            ],
        )
        assert m.category == SkillCategory.DEPLOYMENT
        assert len(m.params) == 1
        assert len(m.artifacts) == 1
        assert "psx" in m.tags


class TestSkill:
    def _make_skill(self, **kwargs: Any) -> Skill:
        meta = SkillMeta(
            name=kwargs.pop("name", "test-skill"),
            description=kwargs.pop("description", "Test description"),
            category=kwargs.pop("category", SkillCategory.WORKFLOW),
            params=kwargs.pop("params", []),
            artifacts=kwargs.pop("artifacts", []),
            **{k: v for k, v in kwargs.items() if k in SkillMeta.model_fields},
        )
        return Skill(
            meta=meta,
            body=kwargs.get("body", "# Test\n"),
            steps=kwargs.get("steps", []),
            is_builtin=kwargs.get("is_builtin", False),
        )

    def test_convenience_properties(self) -> None:
        skill = self._make_skill(name="my-skill", description="Does things")
        assert skill.name == "my-skill"
        assert skill.description == "Does things"
        assert skill.category == SkillCategory.WORKFLOW

    def test_has_procedure(self) -> None:
        skill = self._make_skill()
        assert skill.has_procedure() is False

        step = SkillStep(id="s1", action=StepAction.SHELL, command="ls")
        skill_with_steps = self._make_skill(steps=[step])
        assert skill_with_steps.has_procedure() is True

    def test_get_required_params(self) -> None:
        params = [
            SkillParam(name="host", required=True),
            SkillParam(name="port", required=False, default=22),
        ]
        skill = self._make_skill(params=params)
        required = skill.get_required_params()
        assert len(required) == 1
        assert required[0].name == "host"

    def test_get_param_defaults(self) -> None:
        params = [
            SkillParam(name="host", required=True),
            SkillParam(name="port", required=False, default=22),
            SkillParam(name="user", default="root"),
        ]
        skill = self._make_skill(params=params)
        defaults = skill.get_param_defaults()
        assert defaults == {"port": 22, "user": "root"}

    def test_get_artifacts_by_type(self) -> None:
        artifacts = [
            SkillArtifact(filename="run.sh", artifact_type="script"),
            SkillArtifact(filename="games.yaml", artifact_type="list"),
            SkillArtifact(filename="check.sh", artifact_type="script"),
        ]
        skill = self._make_skill(artifacts=artifacts)
        scripts = skill.get_artifacts_by_type("script")
        assert len(scripts) == 2
        assert scripts[0].filename == "run.sh"

    def test_summary(self) -> None:
        step = SkillStep(id="s1", action=StepAction.SHELL)
        skill = self._make_skill(
            name="deploy-psx",
            description="Deploy PSX ROMs",
            steps=[step],
            artifacts=[SkillArtifact(filename="x.sh")],
        )
        s = skill.summary()
        assert "deploy-psx" in s
        assert "Deploy PSX ROMs" in s
        assert "1 steps" in s
        assert "1 artifacts" in s


# =========================================================================
# Frontmatter parsing tests
# =========================================================================


class TestFrontmatterParsing:
    def test_parse_skill_md(self) -> None:
        text = "---\nname: test\ndescription: A test\n---\n\n# Body here\n"
        fm, body = _parse_skill_md(text)
        assert fm["name"] == "test"
        assert fm["description"] == "A test"
        assert "# Body here" in body

    def test_parse_no_frontmatter(self) -> None:
        text = "# Just markdown\nNo frontmatter here\n"
        fm, body = _parse_skill_md(text)
        assert fm == {}
        assert body == text

    def test_frontmatter_to_meta_basic(self) -> None:
        fm = {
            "name": "test-skill",
            "description": "A test",
            "category": "deployment",
            "version": "1.2.0",
            "tags": ["deploy", "test"],
        }
        meta = _frontmatter_to_meta(fm)
        assert meta.name == "test-skill"
        assert meta.category == SkillCategory.DEPLOYMENT
        assert meta.version == "1.2.0"
        assert meta.tags == ["deploy", "test"]

    def test_frontmatter_to_meta_params_dict(self) -> None:
        fm = {
            "name": "test",
            "description": "test",
            "params": {
                "host": {"type": "string", "required": True, "description": "Target host"},
                "budget_gb": {"type": "number", "default": 60},
            },
        }
        meta = _frontmatter_to_meta(fm)
        assert len(meta.params) == 2
        host_param = next(p for p in meta.params if p.name == "host")
        assert host_param.required is True
        budget_param = next(p for p in meta.params if p.name == "budget_gb")
        assert budget_param.default == 60

    def test_frontmatter_to_meta_params_list(self) -> None:
        fm = {
            "name": "test",
            "description": "test",
            "params": [
                {"name": "host", "type": "string", "required": True},
            ],
        }
        meta = _frontmatter_to_meta(fm)
        assert len(meta.params) == 1
        assert meta.params[0].name == "host"

    def test_frontmatter_to_meta_artifacts(self) -> None:
        fm = {
            "name": "test",
            "description": "test",
            "artifacts": [
                {"filename": "run.sh", "artifact_type": "script", "executable": True},
                "simple.txt",
            ],
        }
        meta = _frontmatter_to_meta(fm)
        assert len(meta.artifacts) == 2
        assert meta.artifacts[0].executable is True
        assert meta.artifacts[1].filename == "simple.txt"

    def test_frontmatter_to_meta_invalid_category(self) -> None:
        fm = {"name": "test", "description": "test", "category": "bogus"}
        meta = _frontmatter_to_meta(fm)
        assert meta.category == SkillCategory.WORKFLOW  # fallback

    def test_meta_to_frontmatter_roundtrip(self) -> None:
        meta = SkillMeta(
            name="roundtrip-skill",
            description="Tests roundtrip serialization",
            version="1.0.0",
            category=SkillCategory.BUILD,
            tags=["build", "test"],
            platforms=["psx"],
            params=[
                SkillParam(name="budget", type="number", required=True, default=60),
            ],
            artifacts=[
                SkillArtifact(filename="run.sh", artifact_type="script"),
            ],
        )
        yaml_text = _meta_to_frontmatter(meta)
        parsed = yaml.safe_load(yaml_text)
        assert parsed["name"] == "roundtrip-skill"
        assert parsed["category"] == "build"
        assert "budget" in parsed["params"]
        assert parsed["params"]["budget"]["type"] == "number"
        assert parsed["artifacts"][0]["filename"] == "run.sh"


# =========================================================================
# SkillStore tests
# =========================================================================


@pytest.fixture
def skill_dirs(tmp_path: Path) -> tuple[Path, Path]:
    """Create temporary library and user skill directories with sample skills."""
    library = tmp_path / "library"
    user = tmp_path / "user_skills"

    # Create a bundled skill
    s1_dir = library / "scan-and-plan"
    s1_dir.mkdir(parents=True)
    (s1_dir / "SKILL.md").write_text(
        "---\n"
        "name: scan-and-plan\n"
        "description: First-run target discovery\n"
        "category: workflow\n"
        "tags:\n  - workflow\n  - scan\n"
        "---\n\n"
        "# Scan and Plan\nConnect, scan, review.\n"
    )
    (s1_dir / "procedure.yaml").write_text(
        yaml.dump(
            {
                "steps": [
                    {
                        "id": "connect",
                        "action": "mcp_call",
                        "description": "Connect to target",
                        "tool": "farmhand_connect",
                    },
                    {
                        "id": "scan",
                        "action": "mcp_call",
                        "description": "Run full scan",
                        "tool": "farmhand_scan_target",
                    },
                ]
            }
        ),
    )

    # Create another bundled skill
    s2_dir = library / "deploy-platform"
    s2_dir.mkdir(parents=True)
    (s2_dir / "SKILL.md").write_text(
        "---\n"
        "name: deploy-platform\n"
        "description: Deploy a platform within budget\n"
        "category: deployment\n"
        "tags:\n  - deployment\n  - budget\n"
        "platforms:\n  - psx\n  - ps2\n"
        "params:\n"
        "  budget_gb:\n"
        "    type: number\n"
        "    required: true\n"
        "    description: Storage budget\n"
        "artifacts:\n"
        "  - filename: deploy.sh\n"
        "    artifact_type: script\n"
        "    description: Deployment script\n"
        "---\n\n"
        "# Deploy Platform\nDeploys ROMs within budget.\n"
    )
    (s2_dir / "deploy.sh").write_text("#!/bin/bash\necho 'deploy'\n")

    # Create a user skill
    s3_dir = user / "custom-cleanup"
    s3_dir.mkdir(parents=True)
    (s3_dir / "SKILL.md").write_text(
        "---\n"
        "name: custom-cleanup\n"
        "description: Custom cleanup workflow\n"
        "category: maintenance\n"
        "tags:\n  - cleanup\n  - maintenance\n"
        "---\n\n"
        "# Cleanup\nRemoves stale files.\n"
    )

    return library, user


class TestSkillStore:
    def test_load_from_library(self, skill_dirs: tuple[Path, Path]) -> None:
        library, user = skill_dirs
        store = SkillStore(library_path=library, user_path=user)
        skills = store.list_all()
        assert len(skills) == 3

    def test_get_by_name(self, skill_dirs: tuple[Path, Path]) -> None:
        library, user = skill_dirs
        store = SkillStore(library_path=library, user_path=user)
        skill = store.get("scan-and-plan")
        assert skill is not None
        assert skill.name == "scan-and-plan"
        assert skill.is_builtin is True

    def test_get_builtin_has_steps(self, skill_dirs: tuple[Path, Path]) -> None:
        library, user = skill_dirs
        store = SkillStore(library_path=library, user_path=user)
        skill = store.get("scan-and-plan")
        assert skill is not None
        assert len(skill.steps) == 2
        assert skill.steps[0].id == "connect"
        assert skill.steps[0].tool == "farmhand_connect"

    def test_get_user_skill(self, skill_dirs: tuple[Path, Path]) -> None:
        library, user = skill_dirs
        store = SkillStore(library_path=library, user_path=user)
        skill = store.get("custom-cleanup")
        assert skill is not None
        assert skill.is_builtin is False

    def test_get_nonexistent(self, skill_dirs: tuple[Path, Path]) -> None:
        library, user = skill_dirs
        store = SkillStore(library_path=library, user_path=user)
        assert store.get("no-such-skill") is None

    def test_user_shadows_builtin(self, skill_dirs: tuple[Path, Path]) -> None:
        """User skill with same name should shadow builtin."""
        library, user = skill_dirs
        shadow_dir = user / "scan-and-plan"
        shadow_dir.mkdir(parents=True)
        (shadow_dir / "SKILL.md").write_text(
            "---\n"
            "name: scan-and-plan\n"
            "description: User override of scan-and-plan\n"
            "category: workflow\n"
            "---\n\n"
            "# Custom scan\n"
        )
        store = SkillStore(library_path=library, user_path=user)
        skill = store.get("scan-and-plan")
        assert skill is not None
        assert skill.is_builtin is False
        assert "User override" in skill.description

    def test_search_by_query(self, skill_dirs: tuple[Path, Path]) -> None:
        library, user = skill_dirs
        store = SkillStore(library_path=library, user_path=user)
        results = store.search(query="deploy")
        assert len(results) == 1
        assert results[0].name == "deploy-platform"

    def test_search_by_category(self, skill_dirs: tuple[Path, Path]) -> None:
        library, user = skill_dirs
        store = SkillStore(library_path=library, user_path=user)
        results = store.search(category=SkillCategory.MAINTENANCE)
        assert len(results) == 1
        assert results[0].name == "custom-cleanup"

    def test_search_by_tag(self, skill_dirs: tuple[Path, Path]) -> None:
        library, user = skill_dirs
        store = SkillStore(library_path=library, user_path=user)
        results = store.search(tags=["scan"])
        assert len(results) == 1
        assert results[0].name == "scan-and-plan"

    def test_search_combined_filters(self, skill_dirs: tuple[Path, Path]) -> None:
        library, user = skill_dirs
        store = SkillStore(library_path=library, user_path=user)
        # query matches both "scan-and-plan" and "deploy-platform",
        # but category limits to deployment
        results = store.search(query="plan", category=SkillCategory.DEPLOYMENT)
        # "scan-and-plan" is workflow, not deployment
        assert all(r.meta.category == SkillCategory.DEPLOYMENT for r in results)

    def test_search_no_results(self, skill_dirs: tuple[Path, Path]) -> None:
        library, user = skill_dirs
        store = SkillStore(library_path=library, user_path=user)
        results = store.search(query="zzz_no_match")
        assert results == []

    def test_list_categories(self, skill_dirs: tuple[Path, Path]) -> None:
        library, user = skill_dirs
        store = SkillStore(library_path=library, user_path=user)
        cats = store.list_categories()
        assert cats[SkillCategory.WORKFLOW] == 1
        assert cats[SkillCategory.DEPLOYMENT] == 1
        assert cats[SkillCategory.MAINTENANCE] == 1

    def test_list_tags(self, skill_dirs: tuple[Path, Path]) -> None:
        library, user = skill_dirs
        store = SkillStore(library_path=library, user_path=user)
        tags = store.list_tags()
        assert tags["workflow"] == 1
        assert tags["deployment"] == 1
        assert tags["cleanup"] == 1

    # -- CRUD --

    def test_save_new_skill(self, skill_dirs: tuple[Path, Path]) -> None:
        library, user = skill_dirs
        store = SkillStore(library_path=library, user_path=user)

        meta = SkillMeta(
            name="new-skill",
            description="A brand new skill",
            category=SkillCategory.SCRIPTING,
            tags=["test"],
        )
        skill = Skill(meta=meta, body="# New Skill\nDoes something.\n")
        path = store.save(skill)

        assert path.exists()
        assert (path / "SKILL.md").exists()

        # Should be retrievable
        loaded = store.get("new-skill")
        assert loaded is not None
        assert loaded.name == "new-skill"
        assert loaded.is_builtin is False

    def test_save_with_steps(self, skill_dirs: tuple[Path, Path]) -> None:
        library, user = skill_dirs
        store = SkillStore(library_path=library, user_path=user)

        steps = [
            SkillStep(id="s1", action=StepAction.SHELL, command="ls -la"),
            SkillStep(id="s2", action=StepAction.MCP_CALL, tool="farmhand_connect"),
        ]
        meta = SkillMeta(name="with-steps", description="Has procedure")
        skill = Skill(meta=meta, body="# Test\n", steps=steps)
        path = store.save(skill)

        assert (path / "procedure.yaml").exists()
        proc = yaml.safe_load((path / "procedure.yaml").read_text())
        assert len(proc["steps"]) == 2

    def test_save_artifact(self, skill_dirs: tuple[Path, Path]) -> None:
        library, user = skill_dirs
        store = SkillStore(library_path=library, user_path=user)

        # Create skill first
        meta = SkillMeta(name="artifact-test", description="Has artifacts")
        skill = Skill(meta=meta, body="# Test\n")
        store.save(skill)

        # Save artifact
        artifact_path = store.save_artifact("artifact-test", "run.sh", "#!/bin/bash\necho hello\n")
        assert artifact_path.exists()
        assert artifact_path.read_text() == "#!/bin/bash\necho hello\n"

    def test_save_artifact_nested(self, skill_dirs: tuple[Path, Path]) -> None:
        library, user = skill_dirs
        store = SkillStore(library_path=library, user_path=user)

        meta = SkillMeta(name="nested-test", description="Nested artifact")
        store.save(Skill(meta=meta, body=""))

        path = store.save_artifact("nested-test", "data/games.yaml", "games:\n  - Castlevania\n")
        assert path.exists()
        assert "Castlevania" in path.read_text()

    def test_delete_user_skill(self, skill_dirs: tuple[Path, Path]) -> None:
        library, user = skill_dirs
        store = SkillStore(library_path=library, user_path=user)
        assert store.get("custom-cleanup") is not None

        result = store.delete("custom-cleanup")
        assert result is True
        assert store.get("custom-cleanup") is None

    def test_delete_builtin_fails(self, skill_dirs: tuple[Path, Path]) -> None:
        library, user = skill_dirs
        store = SkillStore(library_path=library, user_path=user)
        result = store.delete("scan-and-plan")
        assert result is False
        assert store.get("scan-and-plan") is not None

    def test_delete_nonexistent(self, skill_dirs: tuple[Path, Path]) -> None:
        library, user = skill_dirs
        store = SkillStore(library_path=library, user_path=user)
        result = store.delete("no-such-skill")
        assert result is False

    def test_get_artifact_content(self, skill_dirs: tuple[Path, Path]) -> None:
        library, user = skill_dirs
        store = SkillStore(library_path=library, user_path=user)

        content = store.get_artifact_content("deploy-platform", "deploy.sh")
        assert content is not None
        assert "echo 'deploy'" in content

    def test_get_artifact_content_nonexistent(self, skill_dirs: tuple[Path, Path]) -> None:
        library, user = skill_dirs
        store = SkillStore(library_path=library, user_path=user)
        assert store.get_artifact_content("deploy-platform", "missing.sh") is None

    def test_reload(self, skill_dirs: tuple[Path, Path]) -> None:
        library, user = skill_dirs
        store = SkillStore(library_path=library, user_path=user)
        assert len(store.list_all()) == 3

        # Add a new skill on disk
        new_dir = library / "new-bundled"
        new_dir.mkdir()
        (new_dir / "SKILL.md").write_text(
            "---\nname: new-bundled\ndescription: Added later\ncategory: workflow\n---\n\n"
        )

        # Before reload, cache is stale
        assert store.get("new-bundled") is None

        store.reload()
        assert store.get("new-bundled") is not None
        assert len(store.list_all()) == 4

    def test_empty_paths(self, tmp_path: Path) -> None:
        """Store works fine when directories don't exist yet."""
        store = SkillStore(
            library_path=tmp_path / "no-lib",
            user_path=tmp_path / "no-user",
        )
        assert store.list_all() == []


# =========================================================================
# SkillRecorder (auto-capture) tests
# =========================================================================


class TestRecordedStep:
    def test_basic(self) -> None:
        step = RecordedStep(action="shell", command="ls")
        assert step.action == "shell"
        assert step.command == "ls"
        assert step.success is True
        assert isinstance(step.timestamp, datetime)


class TestSkillRecorder:
    def test_lifecycle(self) -> None:
        recorder = SkillRecorder()
        assert recorder.is_active is False
        assert recorder.step_count == 0

        recorder.start("Deploy PSX to batocera")
        assert recorder.is_active is True

        recorder.record_step("mcp_call", tool="farmhand_connect", description="Connect")
        recorder.record_step("mcp_call", tool="farmhand_scan_target", description="Scan")
        assert recorder.step_count == 2

    def test_cancel(self) -> None:
        recorder = SkillRecorder()
        recorder.start("Test workflow")
        recorder.record_step("shell", command="ls")
        assert recorder.step_count == 1

        recorder.cancel()
        assert recorder.is_active is False
        assert recorder.step_count == 0

    def test_record_param(self) -> None:
        recorder = SkillRecorder()
        recorder.start("Test params")
        recorder.record_param("host", "192.168.1.100")
        recorder.record_param("budget_gb", 60.0)

        # Params show up in captured skill
        recorder.record_step("shell", command="echo 192.168.1.100")
        skill = recorder.capture(
            name="param-test",
            category=SkillCategory.WORKFLOW,
        )
        assert len(skill.meta.params) == 2
        host_param = next(p for p in skill.meta.params if p.name == "host")
        assert host_param.type == "string"
        budget_param = next(p for p in skill.meta.params if p.name == "budget_gb")
        assert budget_param.type == "number"

    def test_capture_basic(self) -> None:
        recorder = SkillRecorder()
        recorder.start("Test workflow capture")
        recorder.record_step(
            "mcp_call",
            description="Connect to target",
            tool="farmhand_connect",
            args={"host": "192.168.1.1"},
        )
        recorder.record_step(
            "shell",
            description="List files",
            command="ls -la /roms",
            exit_code=0,
        )

        skill = recorder.capture(
            name="test-capture",
            description="Captured workflow",
            category=SkillCategory.WORKFLOW,
            tags=["test"],
        )

        assert skill.name == "test-capture"
        assert skill.description == "Captured workflow"
        assert skill.meta.category == SkillCategory.WORKFLOW
        assert "test" in skill.meta.tags
        assert skill.meta.author == "agent"
        assert len(skill.steps) == 2
        assert skill.steps[0].tool == "farmhand_connect"
        assert skill.steps[1].command == "ls -la /roms"
        assert "farmhand_connect" in skill.meta.tools_used
        assert recorder.is_active is False  # recorder deactivated

    def test_capture_default_description(self) -> None:
        recorder = SkillRecorder()
        recorder.start("Deploy PSX to target")
        recorder.record_step("shell", command="echo done")
        skill = recorder.capture(name="auto-desc")
        assert skill.description == "Deploy PSX to target"

    def test_capture_skips_failed_steps(self) -> None:
        recorder = SkillRecorder()
        recorder.start("Workflow with failures")
        recorder.record_step("shell", command="good cmd", success=True)
        recorder.record_step("shell", command="bad cmd", success=False)
        recorder.record_step("shell", command="final cmd", success=True)
        skill = recorder.capture(name="filter-test")
        assert len(skill.steps) == 2  # failed step excluded

    def test_capture_templatizes_params(self) -> None:
        recorder = SkillRecorder()
        recorder.start("Template test")
        recorder.record_param("host", "192.168.1.100")
        recorder.record_step(
            "shell",
            command="ssh root@192.168.1.100 'ls /roms'",
        )
        skill = recorder.capture(name="template-test")
        # The concrete host should be replaced with {{host}}
        assert "{{host}}" in skill.steps[0].command
        assert "192.168.1.100" not in skill.steps[0].command

    def test_capture_generates_body(self) -> None:
        recorder = SkillRecorder()
        recorder.start("Generate body test")
        recorder.record_step("shell", description="Step one", command="echo one")
        recorder.record_step("shell", description="Step two", command="echo two")
        skill = recorder.capture(name="body-test")

        assert "# Generate body test" in skill.body
        assert "Step one" in skill.body
        assert "Step two" in skill.body
        assert "## When to use" in skill.body

    def test_capture_with_artifacts(self) -> None:
        recorder = SkillRecorder()
        recorder.start("Artifact capture test")
        recorder.record_step("shell", command="echo hi")
        recorder.record_artifact(
            "deploy.sh",
            "#!/bin/bash\necho deploy",
            artifact_type="script",
        )
        skill = recorder.capture(name="art-test")
        assert len(skill.meta.artifacts) == 1
        assert skill.meta.artifacts[0].filename == "deploy.sh"
        assert skill.meta.artifacts[0].executable is True  # scripts are executable

    def test_capture_not_active_raises(self) -> None:
        recorder = SkillRecorder()
        with pytest.raises(RuntimeError, match="not active"):
            recorder.capture(name="fail")

    def test_capture_deduplicates_step_ids(self) -> None:
        recorder = SkillRecorder()
        recorder.start("Dedup test")
        recorder.record_step("mcp_call", tool="farmhand_connect")
        recorder.record_step("mcp_call", tool="farmhand_connect")
        skill = recorder.capture(name="dedup-test")
        ids = [s.id for s in skill.steps]
        assert len(ids) == len(set(ids))  # all unique


# =========================================================================
# integration: SkillStore + SkillRecorder
# =========================================================================


class TestStoreRecorderIntegration:
    def test_capture_and_save(self, tmp_path: Path) -> None:
        """Full round-trip: record → capture → save → load."""
        store = SkillStore(
            library_path=tmp_path / "lib",
            user_path=tmp_path / "user",
        )

        recorder = SkillRecorder()
        recorder.start("Integration test workflow")
        recorder.record_param("host", "10.0.0.1")
        recorder.record_step(
            "mcp_call",
            description="Connect",
            tool="farmhand_connect",
            args={"host": "10.0.0.1", "user": "root"},
        )
        recorder.record_step(
            "shell",
            description="Check disk space",
            command="ssh root@10.0.0.1 df -h",
            exit_code=0,
        )

        skill = recorder.capture(
            name="integration-test",
            category=SkillCategory.WORKFLOW,
            tags=["test", "integration"],
        )

        path = store.save(skill)
        assert path.exists()
        assert (path / "SKILL.md").exists()
        assert (path / "procedure.yaml").exists()

        # Reload and verify
        store.reload()
        loaded = store.get("integration-test")
        assert loaded is not None
        assert loaded.name == "integration-test"
        assert loaded.meta.category == SkillCategory.WORKFLOW
        assert len(loaded.steps) == 2
        assert "{{host}}" in loaded.steps[0].args.get("host", "")
        assert "farmhand_connect" in loaded.meta.tools_used

    def test_capture_save_with_artifact(self, tmp_path: Path) -> None:
        store = SkillStore(
            library_path=tmp_path / "lib",
            user_path=tmp_path / "user",
        )

        recorder = SkillRecorder()
        recorder.start("Artifact integration")
        recorder.record_step("shell", command="echo test")
        recorder.record_artifact(
            "setup.sh",
            "#!/bin/bash\necho setup",
            artifact_type="script",
        )

        skill = recorder.capture(name="art-integration")
        store.save(skill)

        # Save the actual artifact content
        store.save_artifact("art-integration", "setup.sh", "#!/bin/bash\necho setup")

        content = store.get_artifact_content("art-integration", "setup.sh")
        assert content is not None
        assert "echo setup" in content


# =========================================================================
# Bundled library smoke test
# =========================================================================


class TestBundledLibrary:
    """Verify bundled seed skills in library/ load correctly."""

    @pytest.fixture
    def real_store(self) -> SkillStore:
        """SkillStore pointing at the real bundled library."""
        return SkillStore(
            library_path=Path(__file__).parent.parent
            / "src"
            / "romfarmer"
            / "farmhand"
            / "skills"
            / "library",
            user_path=Path("/tmp/test-no-user-skills"),  # empty
        )

    def test_bundled_skills_load(self, real_store: SkillStore) -> None:
        skills = real_store.list_all()
        # We have 4 seed skills:
        # scan-and-plan, deploy-platform-budget,
        # batocera-dual-volume-setup, curated-essentials-list
        assert len(skills) >= 4

    def test_bundled_skill_names(self, real_store: SkillStore) -> None:
        names = {s.name for s in real_store.list_all()}
        expected = {
            "scan-and-plan",
            "deploy-platform-budget",
            "batocera-dual-volume-setup",
            "curated-essentials-list",
        }
        assert expected.issubset(names)

    def test_bundled_skills_have_procedures(self, real_store: SkillStore) -> None:
        for skill in real_store.list_all():
            assert skill.has_procedure(), f"Skill {skill.name} has no procedure"

    def test_bundled_skills_are_builtin(self, real_store: SkillStore) -> None:
        for skill in real_store.list_all():
            assert skill.is_builtin is True

    def test_essentials_has_artifacts(self, real_store: SkillStore) -> None:
        skill = real_store.get("curated-essentials-list")
        assert skill is not None
        filenames = [a.filename for a in skill.meta.artifacts]
        assert "essentials/saturn.yaml" in filenames
        assert "essentials/psx.yaml" in filenames

    def test_batocera_has_scripts(self, real_store: SkillStore) -> None:
        skill = real_store.get("batocera-dual-volume-setup")
        assert skill is not None
        filenames = [a.filename for a in skill.meta.artifacts]
        assert "setup-rom-symlinks.sh" in filenames
        assert "verify-symlinks.sh" in filenames
