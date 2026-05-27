"""Apply optimizer threshold results to build config YAML files.

The optimizer loop produces per-generation rating thresholds
(e.g., ``{"gen6": 0.85, "gen7": 0.92}``).  This module writes those
thresholds back into build spec YAML files so the actual build picks
them up via the ``optimizer_thresholds`` field on :class:`BuildSpec`.

The YAML is re-serialized with ``yaml.dump`` (comments are not preserved),
which is an acceptable trade-off for automation.  Human-edited build configs
should commit the result to version control.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class ApplyResult:
    """Summary of a threshold-apply operation on a single build config."""

    build_name: str
    config_path: Path
    thresholds_written: Dict[str, float]
    previous_thresholds: Optional[Dict[str, float]]
    changed: bool


def apply_thresholds_to_build(
    build_path: Path,
    thresholds: Dict[str, float],
    *,
    dry_run: bool = False,
) -> ApplyResult:
    """Write *thresholds* into a build config YAML file.

    Reads the file, sets the ``optimizer_thresholds`` top-level key, and
    writes it back.  All other fields are preserved (though comment
    formatting may be lost on re-serialization).

    Args:
        build_path: Absolute path to the build config YAML file.
        thresholds: Generation → min_rating dict from the optimizer.
        dry_run: If True, compute what would change but do not write.

    Returns:
        :class:`ApplyResult` describing what changed.
    """
    if not build_path.exists():
        raise FileNotFoundError(f"Build config not found: {build_path}")

    raw = yaml.safe_load(build_path.read_text()) or {}
    build_name = raw.get("name", build_path.stem)
    previous = raw.get("optimizer_thresholds")

    # Strip zero-threshold gens — they're the default and add no value in YAML
    cleaned = {gen: val for gen, val in thresholds.items() if val > 0.0}

    changed = cleaned != (previous or {})

    if changed and not dry_run:
        if cleaned:
            raw["optimizer_thresholds"] = cleaned
        else:
            raw.pop("optimizer_thresholds", None)

        build_path.write_text(
            yaml.dump(raw, default_flow_style=False, sort_keys=False)
        )
        logger.info(
            f"Applied thresholds to '{build_name}': "
            f"{', '.join(f'{k}={v}' for k, v in sorted(cleaned.items()))}"
        )
    elif not changed:
        logger.info(f"No change needed for '{build_name}'")

    return ApplyResult(
        build_name=build_name,
        config_path=build_path,
        thresholds_written=cleaned,
        previous_thresholds=previous,
        changed=changed,
    )


def apply_thresholds_to_builds(
    build_names: List[str],
    thresholds: Dict[str, float],
    builds_dir: Optional[Path] = None,
    *,
    dry_run: bool = False,
) -> List[ApplyResult]:
    """Apply *thresholds* to multiple build config YAML files.

    Args:
        build_names: Build identifiers (must match ``{name}.yaml`` in
                     *builds_dir*).
        thresholds: Generation → min_rating dict from the optimizer.
        builds_dir: Directory containing build config files.  Defaults to
                    ``config/builds/`` relative to workspace root.
        dry_run: If True, no files are written.

    Returns:
        List of :class:`ApplyResult`, one per build name.
    """
    if builds_dir is None:
        from romfarmer.core.paths import get_paths

        builds_dir = get_paths().workspace_root / "config" / "builds"

    results: List[ApplyResult] = []
    for name in build_names:
        path = builds_dir / f"{name}.yaml"
        if not path.exists():
            logger.warning(f"Build config not found: {path} — skipping")
            continue
        result = apply_thresholds_to_build(path, thresholds, dry_run=dry_run)
        results.append(result)

    return results


def load_thresholds_from_optimizer_log(log_path: Path) -> Dict[str, float]:
    """Read final_thresholds from an optimizer audit log JSON file.

    Optimizer logs are written to ``output/{build_name}/optimizer.log.json``.

    Args:
        log_path: Path to the ``optimizer.log.json`` file.

    Returns:
        Generation → threshold dict.

    Raises:
        FileNotFoundError: If *log_path* does not exist.
        KeyError: If the log does not contain ``final_thresholds``.
    """
    if not log_path.exists():
        raise FileNotFoundError(f"Optimizer log not found: {log_path}")

    with open(log_path) as f:
        data = json.load(f)

    if "final_thresholds" not in data:
        raise KeyError(
            f"'final_thresholds' not found in optimizer log: {log_path}. "
            "Make sure the optimizer ran to completion."
        )

    return {k: float(v) for k, v in data["final_thresholds"].items()}
