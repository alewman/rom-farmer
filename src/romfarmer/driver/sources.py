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
import re
from pathlib import Path

import yaml

# Importing core.paths loads the workspace .env (ROMFARMER_SOURCE_ROOT …) exactly
# once; sources.yaml is ${ENV}-expanded and would otherwise resolve to '/Redump'
# in a process that never touched the CLI.
import romfarmer.core.paths  # noqa: F401
from romfarmer.ir.spec import SpecError, SpecSource

_UNEXPANDED = re.compile(r"\$\{?[A-Za-z_][A-Za-z0-9_]*\}?")


def _load_workspace_env(config_dir: Path) -> None:
    """Load ``<workspace>/.env`` (never overriding a real environment).

    ``core.paths`` loads the .env next to the *installed package*, which is the
    repo checkout in development and nothing at all elsewhere.  RESOLVE must
    not depend on that: the workspace being resolved carries its own .env.
    """
    env_path = config_dir.parent / ".env"
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv

        load_dotenv(env_path, override=False)
    except ImportError:  # pragma: no cover — python-dotenv is a hard dependency
        pass


def load_source_roots(config_dir: Path) -> dict[str, Path]:
    """``{alias: absolute path}`` from ``config/sources.yaml`` (env vars expanded).

    Loud: a root whose ``${VAR}`` is still unexpanded after loading the
    workspace ``.env`` is an error naming the variable — not a path under ``/``.
    """
    path = config_dir / "sources.yaml"
    if not path.exists():
        return {}
    _load_workspace_env(config_dir)
    try:
        raw = yaml.safe_load(os.path.expandvars(path.read_text())) or {}
    except yaml.YAMLError as exc:
        raise SpecError(f"{path} is not valid YAML: {exc}") from exc
    roots = raw.get("roots") or {}
    if not isinstance(roots, dict):
        raise SpecError(f"{path}: 'roots' must be a mapping of alias → path")
    out: dict[str, Path] = {}
    for k, v in roots.items():
        text = str(v)
        m = _UNEXPANDED.search(text)
        if m:
            raise SpecError(
                f"{path}: root {k!r} = {text!r} — {m.group(0)} is not set. Define it in "
                f"{config_dir.parent / '.env'} or the environment."
            )
        out[str(k)] = Path(text)
    return out


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
