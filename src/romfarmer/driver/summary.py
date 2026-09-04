"""PlanSummary — the agent's entire sensory input (intent brief v2 §4, v4 §2).

Everything the intent loop knows about the world arrives through this
struct, so every lever it can turn has a signal here:

- ``rating.min``            → ``rated_fraction``, ``rating_quantiles`` (over the
                              catalog ENTERING the budget pass — solve for a
                              unit count in one step, don't binary-search)
- ``budget.max_bytes``      → ``bytes_est_p50`` / ``bytes_est_p90`` (telemetry
                              quantiles; the p50/p90 gap is the cost of
                              ignorance — where a sample build would pay).
                              The card binds on AGGREGATE p90 (``fits``); a fixed
                              safety margin is gone.
- ``rating.min``            → ``bytes_kept_at_rating`` — solve for the threshold
                              in one step so the stated policy, not the budget
                              trim, is why a game is absent
- rating-per-GB (above seam)→ ``heaviest`` — the 4-disc RPG that costs six
                              single-disc games
- ``curated_lists.ref``     → ``removed_by_pass.curated_lists``, ``top_dropped``
- ``dat.retool_1g1r``       → ``removed_by_pass.dat_filter`` (count only; its
                              reasons are uninformative repeats)
- capability tiers          → ``tier`` / ``quality`` per platform

Size discipline: ~60 tokens for a platform with no judgment drops, ~300 with
a full ``top_dropped``; 40 platforms ≈ 4–12k tokens.  ``top_dropped`` never
lists ``dat_filter`` / ``region`` casualties.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Any

from romfarmer.ir.catalog import Catalog, PassTrace

JUDGMENT_PASSES = ("rating", "budget", "curated_lists", "one_g_one_r", "arcade")
TOP_DROPPED = 10

# The correctness checks a summary performs.  Listed in every PlanSummary so
# "zero warnings" reads as "none of THESE fired", never as "correct".  Each has
# a fixture in tests/driver/test_warnings.py — a check that cannot fire and a
# check that never fires look identical otherwise.
CHECKS: tuple[str, ...] = (
    "chain-mismatch: resolved chain ≠ frontend's preferred chain for the platform",
    "no-capability-entry: device profile silent on the platform (tier unknown, not assumed)",
    "tier-x: platform is tier X on this device",
    "tier-c: platform is tier C — only playable_list titles should ship",
    "dat-missing: a DAT was expected for the source but none was found",
    "unrated-drop-thin: unrated=drop with rated_fraction < 50%",
    "p90-family-factor: chain has no telemetry; p90 is a family factor",
    "p90-over-platform-budget: platform p90 exceeds its own max_bytes (informational)",
    "over-capacity: aggregate p90 (or p50 when unknown) exceeds storage − reserve",
    "budget-over-policy: budget removed more than stated policy did and allocation_note is empty",
)

# p90/p50 spread by chain family when a chain has a prior but no telemetry.
# Deliberately wide for unmeasured families; measured ones come from
# unit_telemetry quantiles (2026-09-03: 7z p90/p50 ≈ 1.08 on nes/megadrive,
# chd ≈ 1.19 on psx).  A null p90 would silently drop the card's binding
# constraint back to p50 — cold run #2 had to do this arithmetic by hand.
FAMILY_P90_FACTOR: dict[str, float] = {
    "passthrough": 1.0,
    "zip": 1.03,
    "7z": 1.10,
    "chd": 1.25,
    "cue_bin": 1.0,
    "iso": 1.0,
    "rvz": 1.0,
    "wux": 1.0,
    "xiso": 1.5,
    "squashfs": 1.5,
    "ps3": 1.2,
}


@dataclass(frozen=True)
class PlatformSummary:
    platform: str
    chain: tuple[str, ...]
    tier: str | None
    quality: float | None
    units_in: int
    units_out: int
    bytes_src: int
    bytes_est_p50: int
    bytes_est_p90: int | None
    p90_ratio: (
        float | None
    )  # bytes_est_p90 / bytes_est_p50 — scale max_bytes by 1/this to fit at p90
    p90_source: str  # "telemetry" | "exact" | "family-factor" | "unknown"
    prediction: str  # CostModel label, e.g. "merged:prior:measured=0.83,telemetry=0.828,n=24"
    rated_fraction: float
    rating_quantiles: dict[str, float]  # p10 p25 p50 p75 p90 over the catalog entering budget
    bytes_kept_at_rating: dict[str, int]  # threshold → p50 bytes a rating.min of that value keeps
    heaviest: tuple[
        dict[str, Any], ...
    ]  # ≤10 largest units entering budget: name, bytes_p50, rating
    removed_by_pass: dict[str, int]
    top_dropped: tuple[dict[str, str], ...]
    notes: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self, detail: bool = True) -> dict[str, Any]:
        """``detail=False`` drops the per-unit lists (heaviest, top_dropped,
        bytes_kept_at_rating) — ~2 KB/platform → ~300 B — for platforms the
        agent is not actively tuning."""
        d: dict[str, Any] = {
            "platform": self.platform,
            "chain": list(self.chain),
            "tier": self.tier,
            "quality": self.quality,
            "units_in": self.units_in,
            "units_out": self.units_out,
            "bytes_src": self.bytes_src,
            "bytes_est_p50": self.bytes_est_p50,
            "bytes_est_p90": self.bytes_est_p90,
            "p90_ratio": (round(self.p90_ratio, 4) if self.p90_ratio is not None else None),
            "p90_source": self.p90_source,
            "prediction": self.prediction,
            "rated_fraction": round(self.rated_fraction, 3),
            "rating_quantiles": {k: round(v, 3) for k, v in self.rating_quantiles.items()},
            "removed_by_pass": {k: v for k, v in self.removed_by_pass.items() if v},
        }
        if detail:
            d["bytes_kept_at_rating"] = self.bytes_kept_at_rating
            d["heaviest"] = list(self.heaviest)
            if self.top_dropped:
                d["top_dropped"] = list(self.top_dropped)
        else:
            d["detail"] = "omitted — request with dry_run(detail=[platform])"
        if self.notes:
            d["notes"] = list(self.notes)
        if self.warnings:
            d["warnings"] = list(self.warnings)
        return d


@dataclass(frozen=True)
class PlanSummary:
    spec_hash: str
    platforms: tuple[PlatformSummary, ...]
    storage_bytes: int | None
    reserve_bytes: int | None
    bytes_total_p50: int
    bytes_total_p90: (
        int | None
    )  # aggregate: p50 + sqrt(Σ (p90_i − p50_i)²) — errors decorrelate across platforms
    headroom_p50: int | None  # usable − p50 (negative = over)
    headroom_p90: int | None  # THE constraint: fits iff headroom_p90 ≥ 0 (p50 when p90 unknown)
    fits: bool | None  # None when storage is unknown
    binding: str  # "p90" | "p50 (no telemetry)" | "none (no storage_bytes)"
    budget_trimmed_units: int
    warnings: tuple[str, ...] = field(default_factory=tuple)
    checks: tuple[str, ...] = CHECKS  # what "zero warnings" means: none of THESE fired

    def to_dict(self, detail: set[str] | None = None) -> dict[str, Any]:
        """``detail``: platforms to expand (``None`` = all, ``set()`` = none)."""
        return {
            "spec_hash": self.spec_hash,
            "storage_bytes": self.storage_bytes,
            "reserve_bytes": self.reserve_bytes,
            "bytes_total_p50": self.bytes_total_p50,
            "bytes_total_p90": self.bytes_total_p90,
            "headroom_p50": self.headroom_p50,
            "headroom_p90": self.headroom_p90,
            "fits": self.fits,
            "binding": self.binding,
            "budget_trimmed_units": self.budget_trimmed_units,
            "warnings": list(self.warnings),
            "platform_warnings": sum(len(p.warnings) for p in self.platforms),
            "checks_performed": [c.split(":", 1)[0] for c in self.checks],
            "platforms": [
                p.to_dict(detail=(detail is None or p.platform in detail)) for p in self.platforms
            ],
        }

    def to_json(self, detail: set[str] | None = None) -> str:
        return json.dumps(self.to_dict(detail), separators=(",", ":"), ensure_ascii=False)


# ---------------------------------------------------------------------------
# RESOLVE-time correctness warnings (no catalog needed) — shared with validate_spec
# ---------------------------------------------------------------------------


def correctness_warnings(
    platform: str,
    chain: tuple[str, ...],
    *,
    tier: str | None,
    preferred_chain: tuple[str, ...] | None,
    resolve_notes: tuple[str, ...] = (),
) -> tuple[str, ...]:
    """Warnings derivable from RESOLVE alone.

    Cold run #1 would have shown its whole failure on this list before its
    first dry run.
    """
    out: list[str] = []
    if tier is None:
        out.append(
            "no-capability-entry: device profile has no capability entry for this platform — "
            "tier unknown, not assumed"
        )
    if preferred_chain and tuple(chain) != tuple(preferred_chain):
        out.append(
            f"chain-mismatch: chain {'→'.join(chain)} is not the frontend's preferred "
            f"{'→'.join(preferred_chain)} — a self-consistent spec, but probably not the card you meant"
        )
    if tier == "X":
        out.append("tier-x: tier X on this device — do not ship")
    if tier == "C":
        out.append("tier-c: tier C — only titles on the device's playable_list should ship")
    for n in resolve_notes:
        if n.startswith("DAT expected"):
            out.append("dat-missing: " + n)
    return tuple(out)


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _quantiles(values: list[float]) -> dict[str, float]:
    if not values:
        return {}
    vs = sorted(values)
    n = len(vs)

    def q(p: float) -> float:
        return vs[min(n - 1, int(p * n))]

    return {"p10": q(0.10), "p25": q(0.25), "p50": q(0.50), "p75": q(0.75), "p90": q(0.90)}


def _short_reason(reason: str) -> str:
    # "1g1r: 'X' region=[...] superseded by 'Y' ..." → keep it, but cap length
    return reason if len(reason) <= 120 else reason[:117] + "…"


def summarize_platform(
    *,
    platform: str,
    chain: tuple[str, ...],
    catalog_in: Catalog,
    catalog_out: Catalog,
    traces: tuple[PassTrace, ...],
    stages: tuple[tuple[str, Catalog], ...],
    cost_model: Any,
    telemetry_quantiles: dict[str, float] | None,
    tier: str | None = None,
    quality: float | None = None,
    unrated_rank: float | None = None,
    max_bytes: int | None = None,
    preferred_chain: tuple[str, ...] | None = None,
    resolve_notes: tuple[str, ...] = (),
) -> PlatformSummary:
    """Summarise one platform's plan.  Pure given its inputs.

    ``unrated_rank`` is where the budget pass ranks unrated units (``None`` =
    median of rated, the default policy); ``max_bytes`` the platform's own
    budget, used only for the informational p90 flag.
    """
    tool = chain[0] if chain else None
    bytes_src = sum(u.source_size for u in catalog_out.units)

    try:
        p50, label = cost_model.predict_output_bytes(bytes_src, platform, tool)
    except Exception as exc:
        p50, label = bytes_src, f"fallback:source_size ({exc})"
    p90: int | None = None
    p90_source = "unknown"
    if tool == "passthrough":
        p90, p90_source = int(p50), "exact"  # bytes are copied as-is: no uncertainty
    elif telemetry_quantiles and "p90" in telemetry_quantiles:
        p90, p90_source = int(bytes_src * telemetry_quantiles["p90"]), "telemetry"
    elif tool in FAMILY_P90_FACTOR:
        p90, p90_source = int(p50 * FAMILY_P90_FACTOR[tool]), "family-factor"
    p90_ratio = (p90 / p50) if (p90 is not None and p50) else None

    # rating stats over the catalog ENTERING the budget pass
    entering_budget = next((c for name, c in stages if name == "budget"), catalog_out)
    rated = [u.rating for u in entering_budget.units if u.rating is not None]
    rated_fraction = len(rated) / len(entering_budget.units) if entering_budget.units else 0.0

    # bytes a given rating.min would keep (p50), with unrated ranked as the budget pass would —
    # the agent solves for a threshold in one step, and the stated policy is the actual cause.
    ratio_p50 = (p50 / bytes_src) if bytes_src else 1.0
    median_rated = sorted(rated)[len(rated) // 2] if rated else 0.0
    rank_unrated = median_rated if unrated_rank is None else unrated_rank

    def _rank(u: Any) -> float:
        return float(u.rating) if u.rating is not None else rank_unrated

    per_unit = [
        (_rank(u), int(u.source_size * ratio_p50), u.canonical_name, u.rating)
        for u in entering_budget.units
    ]
    kept_at: dict[str, int] = {}
    for th in (0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85):
        kept_at[f"{th:.2f}"] = sum(b for r, b, _, _ in per_unit if r >= th - 1e-9)
    heaviest = tuple(
        {"name": n, "bytes_p50": b, "rating": (round(rt, 2) if rt is not None else None)}
        for _, b, n, rt in sorted(per_unit, key=lambda t: -t[1])[:TOP_DROPPED]
    )

    removed_by_pass = {t.pass_name: len(t.removed) for t in traces}
    names = {u.unit_id: u.canonical_name for u in catalog_in.units}
    top: list[dict[str, str]] = []
    for t in traces:
        if t.pass_name not in JUDGMENT_PASSES:
            continue
        for uid, why in t.removed:
            if len(top) >= TOP_DROPPED:
                break
            top.append(
                {"name": names.get(uid, str(uid)), "pass": t.pass_name, "why": _short_reason(why)}
            )
    notes = tuple(resolve_notes) + tuple(n for t in traces for n in t.notes)

    warnings: list[str] = list(
        correctness_warnings(
            platform,
            tuple(chain),
            tier=tier,
            preferred_chain=preferred_chain,
            resolve_notes=resolve_notes,
        )
    )
    if rated_fraction < 0.5 and any("unrated=drop" in why for t in traces for _, why in t.removed):
        warnings.append(
            f"unrated-drop-thin: rated_fraction {rated_fraction:.0%} < 50% with unrated=drop"
        )
    if p90_source == "family-factor" and tool is not None:
        warnings.append(
            f"p90-family-factor: no telemetry for chain {tool!r} — p90 is a family factor "
            f"({FAMILY_P90_FACTOR[tool]}×); a --test-sample build would replace it with a measurement"
        )
    elif p90 is None:
        warnings.append(f"p90-unknown: chain {tool!r} has no prior and no telemetry")
    if max_bytes is not None and p90 is not None and p90 > max_bytes:
        warnings.append(
            f"p90-over-platform-budget: p90 {p90:,} exceeds this platform's budget.max_bytes "
            f"{max_bytes:,} (informational — the card binds on aggregate p90)"
        )

    return PlatformSummary(
        platform=platform,
        chain=tuple(chain),
        tier=tier,
        quality=quality,
        units_in=len(catalog_in.units),
        units_out=len(catalog_out.units),
        bytes_src=bytes_src,
        bytes_est_p50=int(p50),
        bytes_est_p90=p90,
        p90_ratio=p90_ratio,
        p90_source=p90_source,
        prediction=label,
        rated_fraction=rated_fraction,
        rating_quantiles=_quantiles([float(r) for r in rated]),
        bytes_kept_at_rating=kept_at,
        heaviest=heaviest,
        removed_by_pass=removed_by_pass,
        top_dropped=tuple(top),
        notes=notes,
        warnings=tuple(warnings),
    )


def summarize(
    spec_hash: str,
    platforms: list[PlatformSummary],
    *,
    storage_bytes: int | None,
    reserve_bytes: int | None,
    allocation_note: str = "",
) -> PlanSummary:
    total_p50 = sum(p.bytes_est_p50 for p in platforms)
    # Aggregate p90: per-platform errors partly decorrelate, so summing per-platform p90s
    # over-states the risk.  Combine the (p90 − p50) spreads in quadrature.
    spreads = [
        (p.bytes_est_p90 - p.bytes_est_p50) for p in platforms if p.bytes_est_p90 is not None
    ]
    known = len(spreads) == len(platforms) and bool(platforms)
    total_p90: int | None = (
        int(total_p50 + math.sqrt(sum(d * d for d in spreads))) if known else None
    )
    usable = None if storage_bytes is None else storage_bytes - (reserve_bytes or 0)
    warnings: list[str] = []
    fits: bool | None
    if usable is None:
        fits, binding = None, "none (no storage_bytes)"
    elif total_p90 is not None:
        fits, binding = (
            total_p90 <= usable,
            "p90 (root-sum-square of per-platform spreads: independent sampling noise only — "
            "a wrong measurement base moves every platform of a chain the same way and is "
            "covered only by that chain's smoke build)",
        )
        if not fits:
            warnings.append(
                f"over-capacity: over usable capacity at p90 by {total_p90 - usable:,} bytes — reduce budget.max_bytes / tighten rating.min"
            )
    else:
        fits, binding = total_p50 <= usable, "p50 (no telemetry for some chain)"
        if not fits:
            warnings.append(
                f"over-capacity: over usable capacity at p50 by {total_p50 - usable:,} bytes"
            )
        else:
            warnings.append(
                "p90 unknown for at least one platform — fits at p50 only; sample builds would settle it"
            )
    trimmed = sum(p.removed_by_pass.get("budget", 0) for p in platforms)
    stated = sum(
        p.removed_by_pass.get("rating", 0) + p.removed_by_pass.get("curated_lists", 0)
        for p in platforms
    )
    if trimmed > stated and not allocation_note.strip():
        warnings.append(
            f"budget-over-policy: the budget pass removed {trimmed} units, more than stated policy did ({stated}); if that is "
            "deliberate, say so in intent.allocation_note so an absent game traces to a decision"
        )
    return PlanSummary(
        spec_hash=spec_hash,
        platforms=tuple(platforms),
        storage_bytes=storage_bytes,
        reserve_bytes=reserve_bytes,
        bytes_total_p50=total_p50,
        bytes_total_p90=total_p90,
        headroom_p50=None if usable is None else usable - total_p50,
        headroom_p90=None if (usable is None or total_p90 is None) else usable - total_p90,
        fits=fits,
        binding=binding,
        budget_trimmed_units=trimmed,
        warnings=tuple(warnings),
    )
