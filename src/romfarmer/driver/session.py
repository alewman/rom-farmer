"""PlanSession — INVENTORY once, replan many times (intent brief v3 §4 / v4 §4).

CATALOG is NAS-I/O bound (9m50 wall / 20 s CPU for 20 platforms); PLAN is
~30 ms.  The agent loop therefore catalogs each platform once per session
and iterates ``run_plan`` alone.  Catalogs are cached by
``(platform, source dirs, dat file)`` and each carries an
``inventory_digest`` — sha256 over every disc's path + strongest identity
(derived from the Catalog itself, zero extra I/O) — which the Spec records as
``intent.inventory_digest``.  Within a session the cache is frozen by design
(INVENTORY once); a new session re-catalogs through the FileDigestCache's
stat check.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from romfarmer.ir.catalog import Catalog
from romfarmer.ir.spec import Spec

from .capability import Capabilities, capabilities
from .resolve import ResolvedBuild
from .spec_resolve import resolve_build
from .summary import PlanSummary, PlatformSummary, summarize, summarize_platform

logger = logging.getLogger(__name__)


def inventory_digest(catalog: Catalog) -> str:
    """``sha256:<hex>`` over every disc's path and its strongest known identity.

    Identity precedence is sha256 > md5 > zip ``crc32:size:member`` (from the
    zip central directory, which CATALOG always reads), falling back to size
    only when the catalog has no hash at all.  A repaired ROM at the same
    path and size therefore changes the digest — the G4 #3 class of staleness
    is not invisible here.
    """
    h = hashlib.sha256()
    for u in sorted(catalog.units, key=lambda u: u.unit_id):
        for d in u.discs:
            ident = d.identity
            try:
                kind, value = ident.best_key()
            except ValueError:
                kind, value = "size", str(ident.size or 0)
            h.update(f"{d.source.path}\0{kind}:{value}\n".encode())
    return "sha256:" + h.hexdigest()


@dataclass
class PlanSession:
    """Holds cached Catalogs + shared KB/CostModel for one agent session."""

    workspace_root: Path
    config_root: Path
    _catalogs: dict[tuple[str, tuple[str, ...], str], Catalog] = field(default_factory=dict)
    _kb: Any = None
    _cost_model: Any = None

    # ------------------------------------------------------------------

    def kb(self) -> Any:
        if self._kb is None:
            from romfarmer.analysis.knowledge import KnowledgeBase
            from romfarmer.driver.workspace import Workspace

            db = Workspace.at(self.workspace_root).metadata_db
            self._kb = KnowledgeBase(db if db.exists() else None)
        return self._kb

    def cost_model(self) -> Any:
        if self._cost_model is None:
            from romfarmer.planner import CostModel

            sd = self.config_root / "size_data.json"
            self._cost_model = CostModel(
                size_data_path=sd if sd.exists() else None, knowledge_base=self.kb()
            )
        return self._cost_model

    def _key(self, rb: ResolvedBuild) -> tuple[str, tuple[str, ...], str]:
        return (rb.platform, tuple(str(d) for d, _ in rb.source_dirs), str(rb.dat_file or ""))

    def catalog(self, rb: ResolvedBuild) -> Catalog:
        """CATALOG for *rb*, computed once per (platform, sources, DAT) per session."""
        key = self._key(rb)
        cat = self._catalogs.get(key)
        if cat is None:
            from romfarmer.new_orchestrator import run_catalog

            logger.info("INVENTORY %s: cataloging %s", rb.platform, ", ".join(key[1]))
            cat = run_catalog(
                rb.resolved, source_dir=rb.source_dir, dat_file=rb.dat_file, kb=self.kb()
            )
            self._catalogs[key] = cat
        return cat

    def inventory(self, spec: Spec) -> dict[str, dict[str, Any]]:
        """INVENTORY step: catalog every platform of *spec*; returns per-platform facts."""
        out: dict[str, dict[str, Any]] = {}
        for rb in resolve_build(spec, self.config_root, workspace_root=self.workspace_root):
            cat = self.catalog(rb)
            files = sum(len(u.discs) for u in cat.units)
            out[rb.platform] = {
                "units": len(cat.units),
                "files": files,
                "bytes": sum(u.source_size for u in cat.units),
                "dat_matched": sum(1 for u in cat.units if any(d.dat_name for d in u.discs)),
                "rated": sum(1 for u in cat.units if u.rating is not None),
                "inventory_digest": inventory_digest(cat),
            }
        combined = hashlib.sha256()
        for plat in sorted(out):
            combined.update(f"{plat}={out[plat]['inventory_digest']}\n".encode())
        result: dict[str, Any] = dict(out)
        result["_inventory_digest"] = "sha256:" + combined.hexdigest()
        return result

    def capabilities(self, spec: Spec) -> Capabilities:
        return capabilities(spec.target.frontend, spec.target.device, self.config_root)

    def dry_run(self, spec: Spec) -> PlanSummary:
        """VALIDATE + PLAN over cached catalogs → PlanSummary.  Zero bytes moved."""
        from romfarmer.driver.workspace import Workspace
        from romfarmer.engine.telemetry import UnitTelemetryStore
        from romfarmer.new_orchestrator import run_plan

        caps = self.capabilities(spec)
        db = Workspace.at(self.workspace_root).metadata_db
        tele = UnitTelemetryStore(db) if db.exists() else None
        rows: list[PlatformSummary] = []
        try:
            for rb in resolve_build(spec, self.config_root, workspace_root=self.workspace_root):
                cat = self.catalog(rb)
                planned = run_plan(
                    cat, rb.manifest, cost_model=self.cost_model(), kb=self.kb(), chain=rb.chain
                )
                tool = rb.chain[0] if rb.chain else ""
                tq = tele.quantiles(rb.platform, tool) if tele is not None else {}
                try:
                    cap = caps.require(rb.platform)
                    tier, quality = cap.tier, cap.quality
                except KeyError:
                    tier, quality = None, None
                rows.append(
                    summarize_platform(
                        platform=rb.platform,
                        chain=rb.chain,
                        catalog_in=cat,
                        catalog_out=planned.catalog,
                        traces=tuple(planned.traces),
                        stages=tuple(planned.stages),
                        cost_model=self.cost_model(),
                        telemetry_quantiles=tq or None,
                        tier=tier,
                        quality=quality,
                        unrated_rank=rb.manifest.unrated_rank(),
                        max_bytes=rb.manifest.budget_bytes,
                    )
                )
        finally:
            if tele is not None:
                tele.close()
        return summarize(
            spec.spec_hash(),
            rows,
            storage_bytes=spec.target.storage_bytes,
            reserve_bytes=spec.target.reserve_bytes
            if spec.target.reserve_bytes is not None
            else caps.reserve_bytes,
        )
