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
    """Write ``<specs_dir>/<spec_hash>.yaml`` (idempotent) and index the intent.

    ``<specs_dir>/index.jsonl`` records ``(intent_text, inventory_digest,
    capability_digest, authored_by, authored_at) → spec_hash`` — P3's
    durable intent: an intent can be re-run months later against a grown
    collection and the resulting spec diffed against what the agent decided
    last time.  One line per distinct (spec_hash, inventory_digest).
    """
    import json

    specs_dir.mkdir(parents=True, exist_ok=True)
    out = specs_dir / f"{spec.spec_hash()}.yaml"
    if not out.exists():
        out.write_text(dump_spec(spec))
    index = specs_dir / "index.jsonl"
    row = {
        "spec_hash": spec.spec_hash(),
        "intent_text": spec.intent.text,
        "inventory_digest": spec.intent.inventory_digest,
        "capability_digest": spec.intent.capability_digest,
        "authored_by": spec.intent.authored_by,
        "authored_at": spec.intent.authored_at,
    }
    existing = index.read_text().splitlines() if index.exists() else []
    key = (row["spec_hash"], row["inventory_digest"])
    if not any(
        (json.loads(ln).get("spec_hash"), json.loads(ln).get("inventory_digest")) == key
        for ln in existing
        if ln.strip()
    ):
        with index.open("a") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return out


def intent_history(specs_dir: Path, intent_text: str | None = None) -> list[dict[str, Any]]:
    """Rows from ``index.jsonl`` (optionally filtered to one intent text), oldest first."""
    import json

    index = specs_dir / "index.jsonl"
    if not index.exists():
        return []
    rows = [json.loads(ln) for ln in index.read_text().splitlines() if ln.strip()]
    return [r for r in rows if intent_text is None or r.get("intent_text") == intent_text]
