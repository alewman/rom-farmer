"""Curated-list artifacts — hash-addressed, frozen, loaded by ref only.

``artifacts/curated/<name>/<sha256>.yaml``::

    name: snes-essentials
    generated_by: "agent:<model-id>"      # provenance
    generated_at: "2026-09-03T…"
    basis: {platform: snes, dat: "…", inventory_digest: "sha256:…"}
    entries:
      - {canonical_name: "Chrono Trigger (USA)", action: include, reason: "…"}
      - {canonical_name: "Bad Dump (USA)",       action: exclude, reason: "…"}

The ref is ``curated/<name>@sha256:<hex>`` where ``<hex>`` is the SHA-256 of
the file bytes.  A ref is resolved by hash: a name-only reference is a hard
error, and a file whose bytes no longer hash to the ref is rejected.  This is
the mechanism that lets stochastic taste ("best") into a deterministic
system: the list is authored above the seam, frozen, and its hash rides in
``spec_hash`` — never in ``Action.params``.

``freeze_lists`` converts the legacy ``lists/{platform}-delete`` /
``lists/{platform}+*`` files into one artifact so existing builds lower to a
``Spec`` without losing their curation.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from romfarmer.ir.spec import SpecError

_REF = re.compile(r"^curated/(?P<name>[A-Za-z0-9._-]+)@sha256:(?P<hex>[0-9a-f]{64})$")


@dataclass(frozen=True)
class CuratedArtifact:
    name: str
    sha256: str
    include: frozenset[str]
    exclude: frozenset[str]
    basis: dict[str, Any]
    generated_by: str = ""

    @property
    def ref(self) -> str:
        return f"curated/{self.name}@sha256:{self.sha256}"


def parse_ref(ref: str) -> tuple[str, str]:
    m = _REF.match(ref)
    if not m:
        raise SpecError(f"curated ref must be 'curated/<name>@sha256:<64 hex>', got {ref!r}")
    return m.group("name"), m.group("hex")


def artifact_path(ref: str, artifacts_dir: Path) -> Path:
    name, hex_ = parse_ref(ref)
    return artifacts_dir / "curated" / name / f"{hex_}.yaml"


def load_curated(ref: str, artifacts_dir: Path) -> CuratedArtifact:
    """Load an artifact by ref; verify its bytes hash to the ref."""
    name, hex_ = parse_ref(ref)
    path = artifact_path(ref, artifacts_dir)
    if not path.exists():
        raise SpecError(f"curated artifact not found: {path} (ref {ref})")
    data = path.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    if actual != hex_:
        raise SpecError(
            f"curated artifact {path} hashes to {actual[:12]}…, ref says {hex_[:12]}… — refusing"
        )
    return _parse(name, hex_, data)


def _parse(name: str, hex_: str, data: bytes) -> CuratedArtifact:
    try:
        raw = yaml.safe_load(data)
    except yaml.YAMLError as exc:
        raise SpecError(f"curated artifact {name}@{hex_[:12]} is not valid YAML: {exc}") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("entries"), list):
        raise SpecError(f"curated artifact {name}@{hex_[:12]}: expected a mapping with 'entries'")
    inc: set[str] = set()
    excl: set[str] = set()
    for i, e in enumerate(raw["entries"]):
        if not isinstance(e, dict) or not e.get("canonical_name"):
            raise SpecError(f"curated artifact {name}: entries[{i}] needs canonical_name")
        action = str(e.get("action", "include"))
        if action == "include":
            inc.add(str(e["canonical_name"]))
        elif action == "exclude":
            excl.add(str(e["canonical_name"]))
        else:
            raise SpecError(f"curated artifact {name}: entries[{i}].action must be include|exclude")
    return CuratedArtifact(
        name=name,
        sha256=hex_,
        include=frozenset(inc),
        exclude=frozenset(excl),
        basis=dict(raw.get("basis") or {}),
        generated_by=str(raw.get("generated_by", "")),
    )


def write_curated(
    name: str,
    entries: list[dict[str, str]],
    artifacts_dir: Path,
    *,
    generated_by: str,
    basis: dict[str, Any] | None = None,
    generated_at: str = "",
) -> CuratedArtifact:
    """Freeze ``entries`` into a new artifact; returns it (with its ref).

    This is the ONE way a model's output enters the system: it becomes bytes,
    the bytes get a hash, the hash goes into the spec.  Canonical YAML
    (sorted entries) so the same list always produces the same ref.
    """
    if not re.match(r"^[A-Za-z0-9._-]+$", name):
        raise SpecError(f"curated artifact name must be [A-Za-z0-9._-]+, got {name!r}")
    norm = sorted(
        (
            {
                "canonical_name": str(e["canonical_name"]),
                "action": str(e.get("action", "include")),
                "reason": str(e.get("reason", "")),
            }
            for e in entries
        ),
        key=lambda e: (e["action"], e["canonical_name"]),
    )
    doc = {
        "name": name,
        "generated_by": generated_by,
        "generated_at": generated_at,
        "basis": dict(basis or {}),
        "entries": norm,
    }
    data = yaml.safe_dump(doc, sort_keys=False, allow_unicode=True).encode("utf-8")
    hex_ = hashlib.sha256(data).hexdigest()
    path = artifacts_dir / "curated" / name / f"{hex_}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(data)
    return _parse(name, hex_, data)


def freeze_lists(platform: str, lists_dir: Path, artifacts_dir: Path) -> CuratedArtifact | None:
    """Convert legacy ``lists/{platform}-delete`` + ``lists/{platform}+*`` into one artifact.

    Returns ``None`` when the platform has no list files (nothing to freeze).
    """
    from romfarmer.driver.resolve import load_curated_lists

    include, exclude = load_curated_lists(platform, lists_dir)
    if not include and not exclude:
        return None
    entries = [
        {"canonical_name": n, "action": "include", "reason": f"lists/{platform}+*"} for n in include
    ]
    entries += [
        {"canonical_name": n, "action": "exclude", "reason": f"lists/{platform}-delete"}
        for n in exclude
    ]
    return write_curated(
        f"{platform}-lists",
        entries,
        artifacts_dir,
        generated_by="freeze_lists",
        basis={"platform": platform, "source": f"lists/{platform}-delete, lists/{platform}+*"},
    )
