"""Build API routes — list, trigger, monitor, and manage builds."""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException, Request

logger = logging.getLogger("romfarmer.web.api.builds")

router = APIRouter()

# Track running builds: {build_name: {"thread": Thread, "status": str, "log": list}}
_running_builds: dict[str, dict[str, Any]] = {}


def _config_root(request: Request) -> Path:
    return request.app.state.config_root


def _workspace(request: Request) -> Path:
    return request.app.state.workspace


def _state_dir(request: Request) -> Path:
    return _workspace(request) / "state"


def _list_build_yamls(builds_dir: Path, format_label: str) -> list[dict]:
    """List build YAML files with metadata."""
    if not builds_dir.exists():
        return []
    results = []
    for f in sorted(builds_dir.glob("*.yaml")):
        try:
            raw = yaml.safe_load(f.read_text())
            results.append(
                {
                    "name": f.stem,
                    "file": f.name,
                    "format": format_label,
                    "description": raw.get("description", raw.get("name", f.stem)),
                    "target": raw.get("target", "—"),
                    "recipes": raw.get("recipes", []),
                    "platforms": raw.get("platforms", []),
                }
            )
        except Exception as e:
            results.append(
                {
                    "name": f.stem,
                    "file": f.name,
                    "format": format_label,
                    "description": f"(error: {e})",
                }
            )
    return results


# ── List Builds ──────────────────────────────────────────────────────────────


@router.get("")
async def list_builds(request: Request):
    """List all build configurations (both legacy and new format)."""
    root = _config_root(request)
    legacy = _list_build_yamls(root / "builds", "legacy")
    new = _list_build_yamls(root / "builds" / "new", "new")
    return {"legacy": legacy, "new": new, "total": len(legacy) + len(new)}


@router.get("/{name}")
async def get_build(name: str, request: Request):
    """Get a specific build configuration."""
    root = _config_root(request)
    # Check new format first, then legacy
    for subdir in ["builds/new", "builds"]:
        path = root / subdir / f"{name}.yaml"
        if path.exists():
            raw = yaml.safe_load(path.read_text())
            return {
                "name": name,
                "format": "new" if "new" in subdir else "legacy",
                "config": raw,
            }
    raise HTTPException(status_code=404, detail=f"Build not found: {name}")


# ── Build State ──────────────────────────────────────────────────────────────


@router.get("/{name}/status")
async def get_build_status(name: str, request: Request):
    """Get the current status of a build."""
    state_dir = _state_dir(request)
    state_file = state_dir / f".build_state_{name}.yaml"

    result: dict[str, Any] = {"name": name}

    # Check if actively running in this process
    if name in _running_builds:
        result["running"] = True
        result["log_lines"] = len(_running_builds[name].get("log", []))
    else:
        result["running"] = False

    # Check persisted state
    if state_file.exists():
        try:
            state = yaml.safe_load(state_file.read_text())
            result["state"] = state
        except Exception:
            result["state"] = None
    else:
        result["state"] = None

    return result


# ── Trigger Build ────────────────────────────────────────────────────────────


@router.post("/{name}/run")
async def run_build(name: str, request: Request):
    """Trigger a build by name. Runs in background thread."""
    if name in _running_builds and _running_builds[name].get("thread", None):
        t = _running_builds[name]["thread"]
        if t.is_alive():
            raise HTTPException(status_code=409, detail=f"Build '{name}' is already running")

    _workspace(request)
    config_root = _config_root(request)

    # Verify build exists
    found = False
    for subdir in ["builds/new", "builds"]:
        if (config_root / subdir / f"{name}.yaml").exists():
            found = True
            break
    if not found:
        raise HTTPException(status_code=404, detail=f"Build not found: {name}")

    # Run in background thread
    build_log: list[str] = []

    def _run_build():

        try:
            build_log.append(f"Starting build: {name}")
            from romfarmer.new_orchestrator import NewBuildOrchestrator

            orchestrator = NewBuildOrchestrator.from_config(name)
            build_log.append("Orchestrator loaded, validating...")

            if hasattr(orchestrator, "validate"):
                orchestrator.validate()
                build_log.append("Validation passed, starting build...")

            orchestrator.run()
            build_log.append("Build completed successfully")
            _running_builds[name]["status"] = "completed"
        except Exception as e:
            build_log.append(f"Build failed: {e}")
            _running_builds[name]["status"] = "failed"
            logger.exception(f"Build {name} failed")

    thread = threading.Thread(target=_run_build, daemon=True, name=f"build-{name}")
    _running_builds[name] = {"thread": thread, "status": "running", "log": build_log}
    thread.start()

    return {"status": "started", "name": name}


@router.post("/{name}/stop")
async def stop_build(name: str):
    """Stop a running build (best-effort — sets a flag)."""
    if name not in _running_builds:
        raise HTTPException(status_code=404, detail=f"No running build: {name}")
    # Note: Python threads can't be forcefully killed. The orchestrator
    # would need to check a stop flag. For now, mark as stopping.
    _running_builds[name]["status"] = "stopping"
    return {"status": "stopping", "name": name}


@router.get("/{name}/log")
async def get_build_log(name: str, after: int = 0):
    """Get build log lines (for polling). Use ?after=N to get lines after N."""
    if name not in _running_builds:
        raise HTTPException(status_code=404, detail=f"No active build: {name}")
    log = _running_builds[name]["log"]
    return {
        "lines": log[after:],
        "total": len(log),
        "status": _running_builds[name]["status"],
    }


# ── Build Config CRUD ────────────────────────────────────────────────────────


@router.put("/{name}")
async def save_build(name: str, request: Request):
    """Save/update a build configuration (new format)."""
    body = await request.json()
    path = _config_root(request) / "builds" / "new" / f"{name}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(body, default_flow_style=False, sort_keys=False))
    return {"status": "saved", "name": name, "format": "new"}


@router.delete("/{name}/state")
async def clean_build_state(name: str, request: Request):
    """Clean build state for a build (like romfarmer build clean)."""
    state_dir = _state_dir(request)
    state_file = state_dir / f".build_state_{name}.yaml"
    if state_file.exists():
        state_file.unlink()
        return {"status": "cleaned", "name": name}
    return {"status": "no_state", "name": name}


# ── Resolve Build ────────────────────────────────────────────────────────────


@router.get("/{name}/resolve")
async def resolve_build(name: str, request: Request):
    """Resolve a new-format build and show what it would do."""
    config_root = _config_root(request)

    # Only works for new format builds
    path = config_root / "builds" / "new" / f"{name}.yaml"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"New-format build not found: {name}")

    try:
        from romfarmer.new_orchestrator import NewBuildOrchestrator

        orch = NewBuildOrchestrator.from_config(name, config_root=config_root)
        platforms = []
        for rc in orch.resolved_configs:
            platforms.append(
                {
                    "name": rc.platform_name,
                    "compression": rc.compression_format,
                    "source_count": getattr(rc, "expected_count", None),
                    "enabled": getattr(rc, "enabled", True),
                }
            )

        return {
            "name": name,
            "target": orch.build_spec.target,
            "recipes": orch.build_spec.recipes,
            "platform_count": len(platforms),
            "platforms": platforms,
            "has_budget": orch.build_spec.has_budget_constraint(),
            "output_base": str(orch.build_spec.get_output_base()),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resolution failed: {e}") from e
