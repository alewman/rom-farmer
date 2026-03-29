"""Page routes — serves HTMX-powered HTML pages."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

logger = logging.getLogger("romfarmer.web.pages")

router = APIRouter()


def _templates(request: Request):
    return request.app.state.templates


def _config_root(request: Request) -> Path:
    return request.app.state.config_root


# ── Dashboard ────────────────────────────────────────────────────────────────


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard — overview of configs and builds."""
    return _templates(request).TemplateResponse("dashboard.html", {"request": request})


# ── Config Browser ───────────────────────────────────────────────────────────


@router.get("/configs", response_class=HTMLResponse)
async def configs_index(request: Request):
    """Config type listing page."""
    return _templates(request).TemplateResponse("configs/index.html", {"request": request})


@router.get("/configs/{config_type}", response_class=HTMLResponse)
async def configs_list(config_type: str, request: Request):
    """List configs of a specific type."""
    valid_types = ["platforms", "recipes", "targets", "frontends", "devices", "selections"]
    if config_type not in valid_types:
        return HTMLResponse(f"<p>Unknown config type: {config_type}</p>", status_code=404)
    return _templates(request).TemplateResponse(
        "configs/list.html",
        {"request": request, "config_type": config_type},
    )


@router.get("/configs/{config_type}/{name}", response_class=HTMLResponse)
async def config_detail(config_type: str, name: str, request: Request):
    """Detail/edit page for a single config."""
    return _templates(request).TemplateResponse(
        "configs/detail.html",
        {"request": request, "config_type": config_type, "name": name},
    )


# ── Build Manager ───────────────────────────────────────────────────────────


@router.get("/builds", response_class=HTMLResponse)
async def builds_index(request: Request):
    """Build listing page."""
    return _templates(request).TemplateResponse("builds/index.html", {"request": request})


@router.get("/builds/{name}", response_class=HTMLResponse)
async def build_detail(name: str, request: Request):
    """Build detail page — view config, run, monitor."""
    return _templates(request).TemplateResponse(
        "builds/detail.html",
        {"request": request, "name": name},
    )
