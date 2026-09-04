"""The five intent tools as plain functions (transport-agnostic).

Inputs are what an agent authors — Spec YAML text — and outputs are
JSON-serialisable dicts.  Errors come back as ``{"error": ...}`` so the loop
can revise instead of crashing.  One ``PlanSession`` per ``IntentTools``
instance holds the catalog cache for the session (INVENTORY once, replan
many).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from romfarmer.driver.capability import capabilities as _capabilities
from romfarmer.driver.curated import write_curated
from romfarmer.driver.session import PlanSession
from romfarmer.driver.spec_resolve import resolve_build
from romfarmer.ir.spec import Spec, SpecError

INTENT_TOOL_NAMES: frozenset[str] = frozenset(
    {"inventory", "capabilities", "validate_spec", "dry_run", "write_curated_list"}
)


def _parse(spec_yaml: str) -> Spec:
    try:
        raw = yaml.safe_load(spec_yaml)
    except yaml.YAMLError as exc:
        raise SpecError(f"spec is not valid YAML: {exc}") from exc
    if not isinstance(raw, dict):
        raise SpecError("spec must be a YAML mapping")
    return Spec.from_dict(raw)


class IntentTools:
    def __init__(
        self, workspace_root: Path | str | None = None, config_root: Path | None = None
    ) -> None:
        from romfarmer.driver.workspace import Workspace

        ws = Workspace.resolve(
            workspace_root
        )  # explicit root, else ROMFARMER_WORKSPACE — never the cwd
        self.workspace = ws
        self.workspace_root = ws.root
        self.config_root = Path(config_root) if config_root else ws.config_dir
        self.session = PlanSession(self.workspace_root, self.config_root)

    # -- 1. inventory ---------------------------------------------------
    def inventory(self, spec_yaml: str) -> dict[str, Any]:
        """Catalog every platform in the spec (once per session); per-platform facts + digest."""
        try:
            spec = _parse(spec_yaml)
            inv = self.session.inventory(spec)
        except SpecError as exc:
            return {"error": str(exc)}
        digest = inv.pop("_inventory_digest", "")
        return {"spec_hash": spec.spec_hash(), "inventory_digest": digest, "platforms": inv}

    # -- 2. capabilities ------------------------------------------------
    def capabilities(self, frontend: str, device: str | None = None) -> dict[str, Any]:
        """What this frontend × device can run (tiers, formats, reserve).  Data, not guesses."""
        try:
            caps = _capabilities(frontend, device, self.config_root)
        except Exception as exc:
            return {"error": str(exc)}
        d = caps.to_dict()
        d["capability_digest"] = caps.digest()
        d["shippable"] = list(caps.shippable())
        return d

    # -- 3. validate_spec -----------------------------------------------
    def validate_spec(
        self,
        spec_yaml: str,
        previous_spec_yaml: str | None = None,
        previous_headroom_p50: int | None = None,
        previous_headroom_p90: int | None = None,
    ) -> dict[str, Any]:
        """Loud validation + RESOLVE every platform (no source scan).

        When revising a spec, pass the previous spec and the previous
        dry-run's headroom (``headroom_p90`` when known — that is the binding
        one — else ``headroom_p50``): the deterministic guards reject a
        revision that *loosens* a threshold while the last plan overshot.
        """
        try:
            spec = _parse(spec_yaml)
            builds = resolve_build(spec, self.config_root, workspace_root=self.workspace_root)
        except Exception as exc:  # SpecError, FormatNegotiationError, TargetProfileError …
            return {"ok": False, "error": str(exc)}
        if previous_spec_yaml is not None:
            from romfarmer.intent.guards import guard_spec_revision

            try:
                previous = _parse(previous_spec_yaml)
            except SpecError as exc:
                return {"ok": False, "error": f"previous_spec_yaml: {exc}"}
            headroom = (
                previous_headroom_p90
                if previous_headroom_p90 is not None
                else previous_headroom_p50
            )
            violations = guard_spec_revision(previous, spec, headroom)
            if violations:
                return {
                    "ok": False,
                    "error": "guard: " + "; ".join(violations),
                    "guard_violations": violations,
                }
        return {
            "ok": True,
            "spec_hash": spec.spec_hash(),
            "platforms": [
                {
                    "platform": rb.platform,
                    "extraction": rb.resolved.extraction_type.value,
                    "compression": rb.resolved.compression.value,
                    "chain": list(rb.chain),
                    "dat": rb.dat_file.name if rb.dat_file else None,
                    "one_g_one_r": (
                        "by-dat (Retool 1G1R DAT already chose one title per game)"
                        if not rb.manifest.one_g_one_r
                        else "by-name-pass (name heuristic + region.preferred; no Retool DAT)"
                    ),
                    "rating_min": rb.manifest.rating_min,
                    "budget_bytes": rb.manifest.budget_bytes,
                    "notes": list(rb.notes),
                }
                for rb in builds
            ],
        }

    # -- 4. dry_run -----------------------------------------------------
    def dry_run(self, spec_yaml: str) -> dict[str, Any]:
        """PLAN over cached catalogs → PlanSummary.  Moves zero bytes."""
        try:
            spec = _parse(spec_yaml)
            summary = self.session.dry_run(spec)
        except Exception as exc:
            return {"error": str(exc)}
        return summary.to_dict()

    # -- 5. write_curated_list ------------------------------------------
    def write_curated_list(
        self,
        name: str,
        entries: list[dict[str, str]],
        generated_by: str,
        basis: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Freeze a curated list into a hash-addressed artifact; returns its ref."""
        try:
            art = write_curated(
                name,
                entries,
                self.workspace_root / "artifacts",
                generated_by=generated_by,
                basis=basis,
            )
        except SpecError as exc:
            return {"error": str(exc)}
        return {"ref": art.ref, "include": len(art.include), "exclude": len(art.exclude)}

    # -- dispatch -------------------------------------------------------
    def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name not in INTENT_TOOL_NAMES:
            return {"error": f"unknown tool {name!r}"}
        fn = getattr(self, name)
        try:
            result: dict[str, Any] = fn(**arguments)
        except TypeError as exc:
            return {"error": f"{name}: bad arguments: {exc}"}
        return result
