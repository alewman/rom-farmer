"""YAML I/O for ``romfarmer.ir.spec.Spec`` — loud on every error.

Specs are persisted under ``artifacts/specs/<spec_hash>.yaml`` so an operator
can diff what an agent changed between iterations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from romfarmer.ir.spec import Spec, SpecError


def load_spec(path: Path) -> Spec:
    """Parse and validate a spec YAML.  Raises ``SpecError`` on any problem."""
    if not path.exists():
        raise SpecError(f"spec not found: {path}")
    try:
        raw = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise SpecError(f"{path} is not valid YAML: {exc}") from exc
    if not isinstance(raw, dict):
        raise SpecError(f"{path}: top level must be a mapping")
    return Spec.from_dict(raw)


def dump_spec(spec: Spec) -> str:
    """YAML text of the full spec (intent first, then the hashed fields)."""
    d: dict[str, Any] = spec.to_dict()
    ordered = {
        "spec_version": d["spec_version"],
        "intent": d["intent"],
        "target": d["target"],
        "platforms": d["platforms"],
    }
    header = f"# spec_hash: {spec.spec_hash()}\n# (hash covers target + platforms; intent is provenance only)\n"
    return header + yaml.safe_dump(
        ordered, sort_keys=False, allow_unicode=True, default_flow_style=False
    )


def save_spec(spec: Spec, specs_dir: Path) -> Path:
    """Write ``<specs_dir>/<spec_hash>.yaml`` (idempotent) and return the path."""
    specs_dir.mkdir(parents=True, exist_ok=True)
    out = specs_dir / f"{spec.spec_hash()}.yaml"
    if not out.exists():
        out.write_text(dump_spec(spec))
    return out
