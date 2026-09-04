"""Workspace — the ONE declared root every path derives from.

Three bugs of one class (review G4 #8; the ``${ROMFARMER_SOURCE_ROOT}``
expansion; ``core.paths`` loading ``.env`` from beside the installed package)
all inferred configuration location and happened to be right in the
development checkout.  The class dies here: a ``Workspace`` is constructed
from an explicit root or from ``ROMFARMER_WORKSPACE`` — never from the cwd,
never from where the code lives — loads ``<root>/.env`` exactly once, and
every other path is a derived field.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ENV_VAR = "ROMFARMER_WORKSPACE"
LEGACY_ENV_VAR = "ROMGROOMER_WORKSPACE"


class WorkspaceError(RuntimeError):
    """No workspace was declared (or the declared one is not a workspace)."""


@dataclass(frozen=True)
class Workspace:
    root: Path
    config_dir: Path
    dats_dir: Path
    lists_dir: Path
    artifacts_dir: Path
    output_dir: Path
    store_dir: Path
    cas_dir: Path
    metadata_db: Path
    size_data: Path
    env_file: Path

    @classmethod
    def at(cls, root: Path | str, *, require_config: bool = False) -> Workspace:
        """Declare *root* as the workspace and load its ``.env`` (never overriding the environment)."""
        r = Path(root).expanduser().resolve()
        if require_config and not (r / "config").is_dir():
            raise WorkspaceError(f"{r} is not a ROM Farmer workspace (no config/ directory)")
        env_file = r / ".env"
        if env_file.exists():
            from dotenv import load_dotenv

            load_dotenv(env_file, override=False)
        return cls(
            root=r,
            config_dir=r / "config",
            dats_dir=r / "dats",
            lists_dir=r / "lists",
            artifacts_dir=r / "artifacts",
            output_dir=r / "output",
            store_dir=r / "store",
            cas_dir=r / "store" / "cas",
            metadata_db=r / "metadata" / "database" / "romfarmer.db",
            size_data=r / "config" / "size_data.json",
            env_file=env_file,
        )

    @classmethod
    def from_env(cls) -> Workspace:
        """``ROMFARMER_WORKSPACE`` (or legacy ``ROMGROOMER_WORKSPACE``).  Loud when unset."""
        root = os.environ.get(ENV_VAR) or os.environ.get(LEGACY_ENV_VAR)
        if not root:
            raise WorkspaceError(
                f"no workspace declared: set {ENV_VAR}=/path/to/workspace (the directory holding config/)"
            )
        return cls.at(root, require_config=True)

    @classmethod
    def resolve(cls, explicit: Path | str | None = None) -> Workspace:
        """Explicit root if given, else the environment variable.  Never the cwd."""
        return cls.at(explicit) if explicit is not None else cls.from_env()
