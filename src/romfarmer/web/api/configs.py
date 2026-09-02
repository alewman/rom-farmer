"""Config API routes — list, read, and write ROM Farmer configurations."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException, Request

logger = logging.getLogger("romfarmer.web.api.configs")

router = APIRouter()


# ── Helpers ──────────────────────────────────────────────────────────────────


def _config_root(request: Request) -> Path:
    return request.app.state.config_root


def _list_yamls(directory: Path) -> list[dict[str, Any]]:
    """List YAML files in a directory, returning name + metadata."""
    if not directory.exists():
        return []
    results = []
    for f in sorted(directory.glob("*.yaml")):
        try:
            raw = yaml.safe_load(f.read_text())
            results.append(
                {
                    "name": f.stem,
                    "file": f.name,
                    "description": raw.get("description", raw.get("name", f.stem)),
                    "raw": raw,
                }
            )
        except Exception as e:
            results.append(
                {
                    "name": f.stem,
                    "file": f.name,
                    "description": f"(error: {e})",
                    "raw": {},
                }
            )
    return results


def _read_yaml(path: Path) -> dict[str, Any]:
    """Read and parse a YAML file."""
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Config not found: {path.name}")
    try:
        return yaml.safe_load(path.read_text())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse: {e}") from e


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    """Write data to a YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))


# ── Platform Configs ─────────────────────────────────────────────────────────


@router.get("/platforms")
async def list_platforms(request: Request):
    """List all platform configurations."""
    return _list_yamls(_config_root(request) / "platforms")


@router.get("/platforms/{name}")
async def get_platform(name: str, request: Request):
    """Get a specific platform configuration."""
    return _read_yaml(_config_root(request) / "platforms" / f"{name}.yaml")


@router.put("/platforms/{name}")
async def save_platform(name: str, request: Request):
    """Save/update a platform configuration."""
    body = await request.json()
    path = _config_root(request) / "platforms" / f"{name}.yaml"
    _write_yaml(path, body)
    return {"status": "saved", "name": name}


# ── Recipe Configs ───────────────────────────────────────────────────────────


@router.get("/recipes")
async def list_recipes(request: Request):
    """List all recipe configurations."""
    return _list_yamls(_config_root(request) / "recipes")


@router.get("/recipes/{name}")
async def get_recipe(name: str, request: Request):
    """Get a specific recipe configuration."""
    return _read_yaml(_config_root(request) / "recipes" / f"{name}.yaml")


@router.put("/recipes/{name}")
async def save_recipe(name: str, request: Request):
    """Save/update a recipe configuration."""
    body = await request.json()
    path = _config_root(request) / "recipes" / f"{name}.yaml"
    _write_yaml(path, body)
    return {"status": "saved", "name": name}


# ── Target Configs ───────────────────────────────────────────────────────────


@router.get("/targets")
async def list_targets(request: Request):
    """List all target configurations."""
    return _list_yamls(_config_root(request) / "targets")


@router.get("/targets/{name}")
async def get_target(name: str, request: Request):
    """Get a specific target configuration."""
    return _read_yaml(_config_root(request) / "targets" / f"{name}.yaml")


# ── Frontend Configs ─────────────────────────────────────────────────────────


@router.get("/frontends")
async def list_frontends(request: Request):
    """List all frontend configurations."""
    return _list_yamls(_config_root(request) / "frontends")


@router.get("/frontends/{name}")
async def get_frontend(name: str, request: Request):
    """Get a specific frontend configuration."""
    return _read_yaml(_config_root(request) / "frontends" / f"{name}.yaml")


# ── Device Configs ───────────────────────────────────────────────────────────


@router.get("/devices")
async def list_devices(request: Request):
    """List all device configurations."""
    return _list_yamls(_config_root(request) / "devices")


@router.get("/devices/{name}")
async def get_device(name: str, request: Request):
    """Get a specific device configuration."""
    return _read_yaml(_config_root(request) / "devices" / f"{name}.yaml")


# ── Selection Configs ────────────────────────────────────────────────────────


@router.get("/selections")
async def list_selections(request: Request):
    """List all selection configurations."""
    return _list_yamls(_config_root(request) / "selections")


@router.get("/selections/{name}")
async def get_selection(name: str, request: Request):
    """Get a specific selection configuration."""
    return _read_yaml(_config_root(request) / "selections" / f"{name}.yaml")


# ── Summary ──────────────────────────────────────────────────────────────────


@router.get("/summary")
async def config_summary(request: Request):
    """Get a summary of all config types and counts."""
    root = _config_root(request)
    return {
        "platforms": len(list((root / "platforms").glob("*.yaml")))
        if (root / "platforms").exists()
        else 0,
        "recipes": len(list((root / "recipes").glob("*.yaml")))
        if (root / "recipes").exists()
        else 0,
        "targets": len(list((root / "targets").glob("*.yaml")))
        if (root / "targets").exists()
        else 0,
        "frontends": len(list((root / "frontends").glob("*.yaml")))
        if (root / "frontends").exists()
        else 0,
        "devices": len(list((root / "devices").glob("*.yaml")))
        if (root / "devices").exists()
        else 0,
        "selections": len(list((root / "selections").glob("*.yaml")))
        if (root / "selections").exists()
        else 0,
        "builds_legacy": len(list((root / "builds").glob("*.yaml")))
        if (root / "builds").exists()
        else 0,
        "builds_new": len(list((root / "builds" / "new").glob("*.yaml")))
        if (root / "builds" / "new").exists()
        else 0,
    }
