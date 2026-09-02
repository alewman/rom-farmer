"""Build configuration and state models.

These models are used by the BuildOrchestrator for managing builds.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class BuildStatus(Enum):
    """Build status states."""

    NOT_STARTED = "not_started"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BuildConfig:
    """
    Master build configuration.

    Loaded from YAML files in config/builds/
    """

    name: str
    description: str
    version: str
    settings: dict[str, Any]
    storage: dict[str, Any]
    platforms: list[str]
    platform_overrides: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    @classmethod
    def from_yaml(cls, config_path: Path) -> "BuildConfig":
        """Load build config from YAML file."""
        with open(config_path) as f:
            data = yaml.safe_load(f)

        # Validate required fields
        required = ["name", "description", "platforms", "storage"]
        for req_field in required:
            if req_field not in data:
                raise ValueError(f"Missing required field in {config_path}: {req_field}")

        return cls(
            name=data["name"],
            description=data["description"],
            version=data.get("version", "1.0"),
            settings=data.get("settings", {}),
            storage=data["storage"],
            platforms=data["platforms"],
            platform_overrides=data.get("platform_overrides", {}),
            metadata=data.get("metadata", {}),
            notes=data.get("notes", ""),
        )


@dataclass
class BuildState:
    """
    Current build state for resume capability.

    Persisted to .build_state_{name}.yaml for resume support.
    """

    build_name: str
    started_at: datetime
    completed_platforms: list[str] = field(default_factory=list)
    failed_platforms: list[str] = field(default_factory=list)
    current_platform: str | None = None
    status: BuildStatus = BuildStatus.NOT_STARTED
    last_updated: datetime | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML serialization."""
        return {
            "build_name": self.build_name,
            "started_at": self.started_at.isoformat(),
            "completed_platforms": self.completed_platforms,
            "failed_platforms": self.failed_platforms,
            "current_platform": self.current_platform,
            "status": self.status.value,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BuildState":
        """Load from dictionary (YAML deserialization)."""
        return cls(
            build_name=data["build_name"],
            started_at=datetime.fromisoformat(data["started_at"]),
            completed_platforms=data.get("completed_platforms", []),
            failed_platforms=data.get("failed_platforms", []),
            current_platform=data.get("current_platform"),
            status=BuildStatus(data.get("status", "not_started")),
            last_updated=datetime.fromisoformat(data["last_updated"])
            if data.get("last_updated")
            else None,
        )
