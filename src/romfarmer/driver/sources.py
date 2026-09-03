"""Named source roots — the machine-specific half of a portable Spec.

A Spec never embeds an absolute path.  It names a root alias from
``config/sources.yaml`` (``roots:`` map, ``${ENV}``-expanded, so each host
maps ``myrient_redump`` to wherever its mirror is mounted) plus a subpath.
Resolution happens here, inside RESOLVE — the layer whose job is
machine-specific facts — so the same Spec hashes identically on every host
and after every remount.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from romfarmer.ir.spec import SpecError, SpecSource


def load_source_roots(config_dir: Path) -> dict[str, Path]:
    """``{alias: absolute path}`` from ``config/sources.yaml`` (env vars expanded)."""
    path = config_dir / "sources.yaml"
    if not path.exists():
        return {}
    try:
        raw = yaml.safe_load(os.path.expandvars(path.read_text())) or {}
    except yaml.YAMLError as exc:
        raise SpecError(f"{path} is not valid YAML: {exc}") from exc
    roots = raw.get("roots") or {}
    if not isinstance(roots, dict):
        raise SpecError(f"{path}: 'roots' must be a mapping of alias → path")
    return {str(k): Path(str(v)) for k, v in roots.items()}


def resolve_source(src: SpecSource, roots: dict[str, Path], where: str = "source") -> Path:
    """Absolute directory for *src*; loud when the alias is unknown."""
    root = roots.get(src.root)
    if root is None:
        raise SpecError(
            f"{where}: unknown source root {src.root!r} — add it to config/sources.yaml "
            f"(known: {sorted(roots)})"
        )
    return root / src.subpath if src.subpath else root


def alias_path(path: Path, roots: dict[str, Path], *, recursive: bool = False) -> SpecSource | None:
    """Reverse map: the longest root that is a prefix of *path* → ``SpecSource``."""
    best: tuple[int, str, Path] | None = None
    resolved = Path(os.path.abspath(path))
    for alias, root in roots.items():
        r = Path(os.path.abspath(root))
        try:
            rel = resolved.relative_to(r)
        except ValueError:
            continue
        depth = len(r.parts)
        if best is None or depth > best[0]:
            best = (depth, alias, rel)
    if best is None:
        return None
    _, alias, rel = best
    return SpecSource(
        root=alias, subpath=rel.as_posix() if str(rel) != "." else "", recursive=recursive
    )
