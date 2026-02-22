"""MCP tools for Farm-Hand deployment system.

Exposes target introspection, space planning, and deployment operations
as MCP tools for AI agent-driven workflows.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Module-level SSH client cache — persists across tool calls in a session
_active_clients: dict[str, Any] = {}  # host -> SSHClient


def _get_workspace_root() -> Path:
    from romfarmer.core.paths import get_paths
    return get_paths().workspace_root


def _check_paramiko() -> None:
    try:
        import paramiko  # noqa: F401
    except ImportError:
        raise RuntimeError(
            "paramiko not installed. Run: pip install 'romfarmer[farmhand]'"
        )


# ---------------------------------------------------------------------------
# Tool: farmhand_connect
# ---------------------------------------------------------------------------


async def tool_farmhand_connect(
    host: str, user: str = "root", password: str = "", port: int = 22
) -> dict[str, Any]:
    """Connect to a remote target and return basic system info."""
    _check_paramiko()
    from romfarmer.farmhand.ssh import SSHClient

    try:
        client = SSHClient(host, port=port, user=user, password=password)
        client.connect()
        probe = client.run("hostname").strip()
        uname = client.run("uname -srm").strip()

        # Cache the client for reuse
        _active_clients[host] = client

        return {
            "connected": True,
            "host": host,
            "hostname": probe,
            "uname": uname,
            "message": f"Connected to {probe} ({host}). Client cached for subsequent calls.",
        }
    except Exception as exc:
        return {"connected": False, "host": host, "error": str(exc)}


# ---------------------------------------------------------------------------
# Tool: farmhand_scan_target
# ---------------------------------------------------------------------------


async def tool_farmhand_scan_target(
    host: str,
    user: str = "root",
    password: str = "",
    name: str = "",
    frontend: str = "batocera",
    port: int = 22,
    save: bool = True,
) -> dict[str, Any]:
    """Full scan of a remote target — volumes, ROMs, capabilities.

    Returns complete target profile as a dict.
    """
    _check_paramiko()
    from romfarmer.farmhand.analyzer import TargetAnalyzer
    from romfarmer.farmhand.ssh import SSHClient

    try:
        # Reuse cached client or create new one
        client = _active_clients.get(host)
        if client is None or not client.is_connected:
            client = SSHClient(host, port=port, user=user, password=password)
            client.connect()
            _active_clients[host] = client

        analyzer = TargetAnalyzer(client)
        target_name = name or f"{frontend}-{host.replace('.', '-')}"
        profile = analyzer.full_scan(name=target_name, frontend=frontend)

        # Save profile
        if save:
            profile_dir = _get_workspace_root() / "config" / "farmhand"
            profile_dir.mkdir(parents=True, exist_ok=True)
            profile_path = profile_dir / f"{profile.name}.json"
            profile_path.write_text(profile.model_dump_json(indent=2))

        # Build a clean summary dict
        result = {
            "name": profile.name,
            "host": profile.host,
            "system": None,
            "volumes": [],
            "capabilities": None,
            "existing_roms": {},
            "total_available_gb": round(profile.total_available_gb(), 1),
        }

        if profile.system_info:
            si = profile.system_info
            result["system"] = {
                "hostname": si.hostname,
                "os": f"{si.os_name} {si.os_version}",
                "arch": si.architecture,
                "cpu": si.cpu_model,
                "cores": si.cpu_cores,
                "threads": si.cpu_threads,
                "ram_mb": si.memory_total_mb,
            }

        for vol in profile.volumes:
            result["volumes"].append({
                "mount": vol.mount_point,
                "device": vol.device,
                "fs": vol.filesystem,
                "total_gb": round(vol.total_gb, 1),
                "available_gb": round(vol.available_gb, 1),
                "use_percent": vol.use_percent,
                "role": vol.role.value,
                "rom_path": vol.rom_path,
            })

        if profile.capabilities:
            result["capabilities"] = {
                "binaries": profile.capabilities.binaries,
                "emulators": profile.capabilities.emulators[:20],
                "has_7z": profile.capabilities.has_7z,
                "has_chdman": profile.capabilities.has_chdman,
            }

        for platform, files in profile.existing_roms.items():
            result["existing_roms"][platform] = {
                "count": len(files),
                "sample": files[:5],
            }

        return result
    except Exception as exc:
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Tool: farmhand_analyze_fit
# ---------------------------------------------------------------------------


async def tool_farmhand_analyze_fit(
    available_gb: float = 0,
    target_name: str = "",
) -> dict[str, Any]:
    """Analyze what platforms fit in the available space.

    Either provide available_gb directly, or target_name to load from saved profile.
    """
    try:
        if target_name:
            profile_path = (
                _get_workspace_root() / "config" / "farmhand" / f"{target_name}.json"
            )
            if profile_path.exists():
                from romfarmer.farmhand.models import TargetProfile
                profile = TargetProfile.model_validate_json(profile_path.read_text())
                available_gb = profile.total_available_gb()

        if available_gb <= 0:
            return {"error": "Provide available_gb or a valid target_name"}

        from romfarmer.farmhand.planner import SpacePlanner
        planner = SpacePlanner()
        return planner.estimate_platforms_count(available_gb)
    except Exception as exc:
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Tool: farmhand_generate_plan
# ---------------------------------------------------------------------------


async def tool_farmhand_generate_plan(
    target_name: str,
    reserved_gb: float = 30.0,
    exclude_platforms: str = "",
    budget_overrides: str = "",
) -> dict[str, Any]:
    """Generate a deployment plan for a saved target profile.

    Args:
        target_name: Name of the saved target profile.
        reserved_gb: Space to reserve for saves, BIOS, etc.
        exclude_platforms: Comma-separated list of platforms to exclude.
        budget_overrides: Comma-separated platform=gb pairs (e.g., "ps2=80,psx=60").
    """
    try:
        profile_path = (
            _get_workspace_root() / "config" / "farmhand" / f"{target_name}.json"
        )
        if not profile_path.exists():
            return {"error": f"Target profile '{target_name}' not found. Run farmhand_scan_target first."}

        from romfarmer.farmhand.models import TargetProfile
        from romfarmer.farmhand.planner import SpacePlanner

        profile = TargetProfile.model_validate_json(profile_path.read_text())
        planner = SpacePlanner()

        excludes = [p.strip() for p in exclude_platforms.split(",") if p.strip()]

        budgets: dict[str, float] = {}
        if budget_overrides:
            for pair in budget_overrides.split(","):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    budgets[k.strip()] = float(v.strip())

        plan = planner.create_plan(
            target=profile,
            reserved_gb=reserved_gb,
            exclude_platforms=excludes,
            budget_overrides=budgets,
        )

        # Save plan
        plan_dir = _get_workspace_root() / "config" / "farmhand"
        plan_path = plan_dir / f"{target_name}-plan.json"
        plan_path.write_text(plan.model_dump_json(indent=2))

        # Build summary
        allocs = []
        for a in plan.allocations:
            allocs.append({
                "platform": a.platform,
                "tier": a.tier.value,
                "action": a.action.value,
                "full_set_gb": round(a.full_set_gb, 1),
                "allocated_gb": round(a.allocated_gb, 1),
                "volume": a.target_volume,
                "strategy": a.selection_strategy or None,
                "budget_gb": a.selection_max_gb or None,
            })

        return {
            "target": target_name,
            "summary": plan.summary(),
            "platforms_included": plan.platforms_included,
            "platforms_skipped": plan.platforms_skipped,
            "total_allocated_gb": round(plan.total_allocated_gb, 1),
            "headroom_gb": round(plan.headroom_gb, 1),
            "builds_needed": plan.builds_needed,
            "allocations": allocs,
            "notes": plan.notes,
            "plan_saved_to": str(plan_path),
        }
    except Exception as exc:
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Tool: farmhand_remote_exec
# ---------------------------------------------------------------------------


async def tool_farmhand_remote_exec(
    host: str, command: str, user: str = "root", password: str = "", port: int = 22
) -> dict[str, Any]:
    """Execute an arbitrary command on a remote target via SSH.

    Use this for ad-hoc inspection: check binaries, configs, file listings, etc.
    """
    _check_paramiko()
    from romfarmer.farmhand.ssh import SSHClient

    try:
        client = _active_clients.get(host)
        if client is None or not client.is_connected:
            client = SSHClient(host, port=port, user=user, password=password)
            client.connect()
            _active_clients[host] = client

        output = client.run(command, timeout=60)
        return {
            "host": host,
            "command": command,
            "output": output,
        }
    except Exception as exc:
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Tool: farmhand_get_target_info
# ---------------------------------------------------------------------------


async def tool_farmhand_get_target_info(target_name: str) -> dict[str, Any]:
    """Get saved target profile information (from last scan)."""
    try:
        profile_path = (
            _get_workspace_root() / "config" / "farmhand" / f"{target_name}.json"
        )
        if not profile_path.exists():
            return {"error": f"Target profile '{target_name}' not found"}

        from romfarmer.farmhand.models import TargetProfile
        profile = TargetProfile.model_validate_json(profile_path.read_text())

        return {
            "name": profile.name,
            "host": profile.host,
            "frontend": profile.frontend,
            "last_scanned": str(profile.last_scanned) if profile.last_scanned else None,
            "total_available_gb": round(profile.total_available_gb(), 1),
            "volumes": [
                {
                    "mount": v.mount_point,
                    "total_gb": round(v.total_gb, 1),
                    "available_gb": round(v.available_gb, 1),
                    "role": v.role.value,
                    "rom_path": v.rom_path,
                }
                for v in profile.volumes
            ],
            "existing_rom_platforms": list(profile.existing_roms.keys()),
            "existing_rom_count": sum(len(v) for v in profile.existing_roms.values()),
        }
    except Exception as exc:
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Tool: farmhand_deploy_status
# ---------------------------------------------------------------------------


async def tool_farmhand_deploy_status(target_name: str) -> dict[str, Any]:
    """Get deployment status — what's been planned and deployed for a target."""
    try:
        ws = _get_workspace_root()
        plan_path = ws / "config" / "farmhand" / f"{target_name}-plan.json"
        profile_path = ws / "config" / "farmhand" / f"{target_name}.json"

        result: dict[str, Any] = {"target": target_name}

        if profile_path.exists():
            from romfarmer.farmhand.models import TargetProfile
            profile = TargetProfile.model_validate_json(profile_path.read_text())
            result["last_scanned"] = str(profile.last_scanned) if profile.last_scanned else None
            result["total_available_gb"] = round(profile.total_available_gb(), 1)
        else:
            result["profile"] = "not found"

        if plan_path.exists():
            from romfarmer.farmhand.models import DeploymentPlan
            plan = DeploymentPlan.model_validate_json(plan_path.read_text())
            result["plan_status"] = plan.status.value
            result["platforms_included"] = plan.platforms_included
            result["platforms_skipped"] = plan.platforms_skipped
            result["total_allocated_gb"] = round(plan.total_allocated_gb, 1)
            result["builds_needed"] = plan.builds_needed
        else:
            result["plan"] = "no plan generated yet"

        return result
    except Exception as exc:
        return {"error": str(exc)}
