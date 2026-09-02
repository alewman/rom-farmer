"""ROM Farmer Web UI — FastAPI application.

Provides a web interface for managing ROM Farmer configs and builds
using FastAPI + Jinja2 + HTMX.
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from romfarmer.web.api.builds import router as builds_router
from romfarmer.web.api.configs import router as configs_router
from romfarmer.web.api.schemas import router as schemas_router
from romfarmer.web.pages import router as pages_router

logger = logging.getLogger("romfarmer.web")

WEB_DIR = Path(__file__).parent
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"


def create_app(config_root: Path | None = None) -> FastAPI:
    """Create the FastAPI application.

    Args:
        config_root: Path to rom-farmer config directory.
                     Defaults to ROMFARMER_CONFIG_ROOT env var, or workspace/config.
    """
    import os

    if config_root is None:
        env_root = os.environ.get("ROMFARMER_CONFIG_ROOT")
        if env_root:
            config_root = Path(env_root)
        else:
            config_root = Path(__file__).parents[4] / "config"

    app = FastAPI(
        title="ROM Farmer",
        description="ROM Collection Management — Web UI",
        version="0.1.0",
    )

    # Store config root for use in route handlers
    app.state.config_root = config_root
    app.state.workspace = config_root.parent

    # Static files (CSS, JS)
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Templates
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    app.state.templates = templates

    # API routes
    app.include_router(configs_router, prefix="/api/configs", tags=["configs"])
    app.include_router(builds_router, prefix="/api/builds", tags=["builds"])
    app.include_router(schemas_router, prefix="/api/schemas", tags=["schemas"])

    # Page routes (HTMX)
    app.include_router(pages_router)

    # Health check
    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "romfarmer-web"}

    logger.info(f"ROM Farmer Web UI initialized (config: {config_root})")

    return app
