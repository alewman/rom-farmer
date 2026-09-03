"""Spec — the frozen, hash-addressed build specification (the SPEC seam).

Everything above this type may be stochastic (an agent authoring it);
everything below is the deterministic compiler.  ``Spec`` is the only thing
that crosses.  It is the product of INTENT and the input of RESOLVE.

Design (intent brief v4 §5):

* ``intent`` is **provenance only** and is excluded from ``spec_hash`` —
  rewording the prompt must not invalidate a correct build.
* Semantic fields (``target``, ``platforms``) are canonicalised to compact,
  key-sorted JSON; ``spec_hash`` is the SHA-256 of that text.  The canonical
  form is FROZEN — see ``tests/ir/test_spec_golden.py``.
* Sources are ``{root, subpath}`` aliases into ``config/sources.yaml`` — a Spec
  never embeds an absolute path, so it is portable and hashes the same on
  every host (resolution is RESOLVE's job).
* Curated-list references are ``curated/<name>@sha256:<hex>`` and bind to the
  spec hash only — never to ``Action.params`` (selection determinism and
  transform determinism are distinct layers).
* Ratings are on the unit interval (0.0–1.0).  ``rating.min > 1`` is an
  error at construction; ``unrated`` is *required* whenever ``min`` is set.
* ``dat.retool_1g1r`` is THE one-game-one-region lever; there is no
  ``passes.1g1r``.  ``region.preferred`` must be empty under a Retool DAT.

This module is stdlib-only (IR contract).  YAML I/O lives in
``romfarmer.driver.spec_io``.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field, fields
from typing import Any

SPEC_VERSION = 1

_CURATED_REF = re.compile(r"^curated/[A-Za-z0-9._-]+@sha256:[0-9a-f]{64}$")
_UNRATED = ("keep", "drop")
_UNRATED_AS = ("median", "worst", "best")
_RATING_SCALE = "unit_interval"


class SpecError(ValueError):
    """The spec is malformed or violates a validation rule.  Always loud."""


# ---------------------------------------------------------------------------
# Leaf types
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SpecIntent:
    """Provenance.  EXCLUDED from ``spec_hash``."""

    text: str = ""
    authored_by: str = ""
    authored_at: str = ""
    inventory_digest: str = ""
    capability_digest: str = ""
    allocation_note: str = ""


@dataclass(frozen=True, slots=True)
class SpecTarget:
    frontend: str
    device: str | None = None
    storage_bytes: int | None = None
    reserve_bytes: int | None = None

    @property
    def usable_bytes(self) -> int | None:
        if self.storage_bytes is None:
            return None
        return self.storage_bytes - (self.reserve_bytes or 0)


@dataclass(frozen=True, slots=True)
class SpecSource:
    """A source directory named by root alias, never by absolute path.

    ``root`` is a key of ``config/sources.yaml`` ``roots:``; the host maps it
    to a mount point.  Keeps the Spec portable and its hash stable across
    hosts and remounts.
    """

    root: str
    subpath: str = ""
    recursive: bool = False


@dataclass(frozen=True, slots=True)
class SpecDat:
    """Which DAT defines the platform's collection.

    ``retool_1g1r`` is the one-game-one-region lever: when true the DAT has
    already chosen one title per game and the name-heuristic 1g1r pass is off.
    ``source`` is the ``DATSource`` key (``retool_1g1r_eng`` …) or ``None`` to
    take the platform config's intrinsic reference; ``file`` an explicit path.
    """

    retool_1g1r: bool = False
    source: str | None = None
    file: str | None = None


@dataclass(frozen=True, slots=True)
class SpecRegion:
    preferred: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SpecRating:
    scale: str = _RATING_SCALE
    min: float | None = None
    top_n: int | None = None
    unrated: str | None = None  # REQUIRED when min is set: "keep" | "drop"


@dataclass(frozen=True, slots=True)
class SpecCuratedLists:
    ref: str | None = None  # curated/<name>@sha256:<hex>


@dataclass(frozen=True, slots=True)
class SpecBudget:
    max_bytes: int | None = None
    unrated_as: str = "median"  # median | worst | best | "<float>"
    safety_margin: float = 0.05


@dataclass(frozen=True, slots=True)
class SpecSample:
    n: int | None = None
    seed: int = 0


@dataclass(frozen=True, slots=True)
class SpecPasses:
    dat_filter: bool = True
    region: SpecRegion = field(default_factory=SpecRegion)
    rating: SpecRating = field(default_factory=SpecRating)
    curated_lists: SpecCuratedLists = field(default_factory=SpecCuratedLists)
    budget: SpecBudget = field(default_factory=SpecBudget)
    sample: SpecSample = field(default_factory=SpecSample)


@dataclass(frozen=True, slots=True)
class SpecPlatform:
    platform: str
    sources: tuple[SpecSource, ...]
    extraction: str  # ExtractionType value: none | cartridge | disc | rvz | wux | ps3 | xiso
    compression: str  # CompressionFormat value: none | zip | 7z | chd | xiso | sqfs | …
    priority: int = 0
    dat: SpecDat = field(default_factory=SpecDat)
    passes: SpecPasses = field(default_factory=SpecPasses)


@dataclass(frozen=True, slots=True)
class Spec:
    target: SpecTarget
    platforms: tuple[SpecPlatform, ...]
    intent: SpecIntent = field(default_factory=SpecIntent)
    spec_version: int = SPEC_VERSION

    # ------------------------------------------------------------------
    # Canonical form + hash (FROZEN — golden test)
    # ------------------------------------------------------------------

    def semantic_dict(self) -> dict[str, Any]:
        """The hashed content: everything except ``intent``.  Platforms sorted by id."""
        return {
            "spec_version": self.spec_version,
            "target": _to_plain(self.target),
            "platforms": [_to_plain(p) for p in sorted(self.platforms, key=lambda p: p.platform)],
        }

    def canonical_json(self) -> str:
        """Compact, key-sorted, ASCII JSON of ``semantic_dict``.  FROZEN FOREVER."""
        return json.dumps(
            self.semantic_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True
        )

    def spec_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Full round-trippable form (includes ``intent``)."""
        d = self.semantic_dict()
        d["intent"] = _to_plain(self.intent)
        return d

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> Spec:
        """Build and validate a ``Spec`` from a plain mapping.  Unknown keys are errors."""
        _check_keys(raw, {"spec_version", "intent", "target", "platforms", "policy"}, "spec")
        if "policy" in raw:
            raise SpecError(
                "'policy' was removed (v4): budget strategy is agent behaviour, not compiler "
                "behaviour — record the outcome as per-platform budget.max_bytes"
            )
        version = raw.get("spec_version", SPEC_VERSION)
        if version != SPEC_VERSION:
            raise SpecError(f"unsupported spec_version {version!r} (expected {SPEC_VERSION})")
        target = _target_from(raw.get("target"))
        plats_raw = raw.get("platforms")
        if not isinstance(plats_raw, list) or not plats_raw:
            raise SpecError("'platforms' must be a non-empty list")
        platforms = tuple(_platform_from(p) for p in plats_raw)
        intent = _intent_from(raw.get("intent") or {})
        spec = cls(target=target, platforms=platforms, intent=intent, spec_version=version)
        validate_spec(spec)
        return spec


# ---------------------------------------------------------------------------
# Validation (pure; every rule from the briefs lives here)
# ---------------------------------------------------------------------------


def validate_spec(spec: Spec) -> None:
    """Raise ``SpecError`` on the first violated rule.

    Rules (intent briefs v2–v4):
    - platform ids unique; sources non-empty
    - rating.scale == unit_interval; 0 ≤ min ≤ 1; top_n ≥ 1; unrated required with min
    - budget.max_bytes ≥ 0; unrated_as ∈ {median, worst, best, <float in [0,1]>};
      0 ≤ safety_margin < 1
    - region.preferred must be empty when dat.retool_1g1r (it would delete
      Retool's English picks)
    - curated_lists.ref must be hash-addressed
    - Σ budget.max_bytes ≤ target.storage_bytes − reserve_bytes
    """
    t = spec.target
    if not t.frontend:
        raise SpecError("target.frontend is required")
    for name in ("storage_bytes", "reserve_bytes"):
        v = getattr(t, name)
        if v is not None and (not isinstance(v, int) or v < 0):
            raise SpecError(f"target.{name} must be a non-negative integer, got {v!r}")
    if (
        t.storage_bytes is not None
        and t.reserve_bytes is not None
        and t.reserve_bytes > t.storage_bytes
    ):
        raise SpecError("target.reserve_bytes exceeds target.storage_bytes")

    seen: set[str] = set()
    total_budget = 0
    for p in spec.platforms:
        where = f"platforms[{p.platform!r}]"
        if not p.platform:
            raise SpecError("platform id is required")
        if p.platform in seen:
            raise SpecError(f"duplicate platform {p.platform!r}")
        seen.add(p.platform)
        if not p.sources:
            raise SpecError(f"{where}.sources must be non-empty")
        r = p.passes.rating
        if r.scale != _RATING_SCALE:
            raise SpecError(
                f"{where}.passes.rating.scale must be {_RATING_SCALE!r}, got {r.scale!r}"
            )
        if r.min is not None:
            if not (0.0 <= r.min <= 1.0):
                raise SpecError(
                    f"{where}.passes.rating.min must be on the unit interval 0.0–1.0, got {r.min!r} "
                    "(ratings are 0–1; 3.5 would remove every rated unit)"
                )
            if r.unrated is None:
                raise SpecError(
                    f"{where}.passes.rating.unrated is required when min is set (keep|drop)"
                )
        if r.unrated is not None and r.unrated not in _UNRATED:
            raise SpecError(f"{where}.passes.rating.unrated must be keep|drop, got {r.unrated!r}")
        if r.top_n is not None and r.top_n < 1:
            raise SpecError(f"{where}.passes.rating.top_n must be >= 1")
        b = p.passes.budget
        if b.max_bytes is not None:
            if b.max_bytes < 0:
                raise SpecError(f"{where}.passes.budget.max_bytes must be >= 0")
            total_budget += b.max_bytes
        if b.unrated_as not in _UNRATED_AS:
            try:
                f = float(b.unrated_as)
            except ValueError:
                raise SpecError(
                    f"{where}.passes.budget.unrated_as must be median|worst|best|<float>, got {b.unrated_as!r}"
                ) from None
            if not (0.0 <= f <= 1.0):
                raise SpecError(f"{where}.passes.budget.unrated_as float must be in [0, 1]")
        if not (0.0 <= b.safety_margin < 1.0):
            raise SpecError(f"{where}.passes.budget.safety_margin must be in [0, 1)")
        if p.dat.retool_1g1r and p.passes.region.preferred:
            raise SpecError(
                f"{where}.passes.region.preferred must be empty under a Retool 1G1R DAT — "
                "the DAT already chose one title per game and a region filter would delete "
                "its English picks (e.g. Japan-only English releases)"
            )
        ref = p.passes.curated_lists.ref
        if ref is not None and not _CURATED_REF.match(ref):
            raise SpecError(
                f"{where}.passes.curated_lists.ref must be 'curated/<name>@sha256:<64 hex>', got {ref!r}"
            )
        s = p.passes.sample
        if s.n is not None and s.n < 1:
            raise SpecError(f"{where}.passes.sample.n must be >= 1")

    usable = t.usable_bytes
    if usable is not None and total_budget > usable:
        raise SpecError(
            f"sum of platform budget.max_bytes ({total_budget:,}) exceeds usable storage "
            f"({usable:,} = storage_bytes − reserve_bytes)"
        )


# ---------------------------------------------------------------------------
# dict ↔ dataclass helpers
# ---------------------------------------------------------------------------


def Path_parts(sub: str) -> tuple[str, ...]:
    return tuple(part for part in sub.replace("\\", "/").split("/") if part)


def _to_plain(obj: Any) -> Any:
    if hasattr(obj, "__dataclass_fields__"):
        return {f.name: _to_plain(getattr(obj, f.name)) for f in fields(obj)}
    if isinstance(obj, tuple):
        return [_to_plain(x) for x in obj]
    return obj


def _check_keys(raw: Any, allowed: set[str], where: str) -> None:
    if not isinstance(raw, Mapping):
        raise SpecError(f"{where} must be a mapping, got {type(raw).__name__}")
    unknown = set(raw) - allowed
    if unknown:
        raise SpecError(f"{where}: unknown key(s) {sorted(unknown)} (allowed: {sorted(allowed)})")


def _opt_int(raw: Mapping[str, Any], key: str, where: str) -> int | None:
    v = raw.get(key)
    if v is None:
        return None
    if isinstance(v, bool) or not isinstance(v, int):
        raise SpecError(f"{where}.{key} must be an integer, got {v!r}")
    return v


def _opt_float(raw: Mapping[str, Any], key: str, where: str) -> float | None:
    v = raw.get(key)
    if v is None:
        return None
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise SpecError(f"{where}.{key} must be a number, got {v!r}")
    return float(v)


def _intent_from(raw: Mapping[str, Any]) -> SpecIntent:
    _check_keys(raw, {f.name for f in fields(SpecIntent)}, "intent")
    return SpecIntent(**{k: str(v) for k, v in raw.items()})


def _target_from(raw: Any) -> SpecTarget:
    _check_keys(raw, {"frontend", "device", "storage_bytes", "reserve_bytes"}, "target")
    if not raw.get("frontend"):
        raise SpecError("target.frontend is required")
    return SpecTarget(
        frontend=str(raw["frontend"]),
        device=str(raw["device"]) if raw.get("device") is not None else None,
        storage_bytes=_opt_int(raw, "storage_bytes", "target"),
        reserve_bytes=_opt_int(raw, "reserve_bytes", "target"),
    )


def _passes_from(raw: Any, where: str) -> SpecPasses:
    raw = raw or {}
    _check_keys(
        raw, {"dat_filter", "region", "rating", "curated_lists", "budget", "sample", "1g1r"}, where
    )
    if "1g1r" in raw:
        raise SpecError(
            f"{where}.1g1r was removed (v4): use dat.retool_1g1r — the DAT is the 1g1r lever"
        )
    df = raw.get("dat_filter", True)
    if not isinstance(df, bool):
        raise SpecError(f"{where}.dat_filter must be a boolean (the gate is binary), got {df!r}")

    reg_raw = raw.get("region") or {}
    _check_keys(reg_raw, {"preferred"}, f"{where}.region")
    region = SpecRegion(preferred=tuple(str(x) for x in (reg_raw.get("preferred") or [])))

    rat_raw = raw.get("rating")
    if isinstance(rat_raw, bool):
        raise SpecError(f"{where}.rating must be a mapping (scale/min/top_n/unrated)")
    rat_raw = rat_raw or {}
    _check_keys(rat_raw, {"scale", "min", "top_n", "unrated"}, f"{where}.rating")
    rating = SpecRating(
        scale=str(rat_raw.get("scale", _RATING_SCALE)),
        min=_opt_float(rat_raw, "min", f"{where}.rating"),
        top_n=_opt_int(rat_raw, "top_n", f"{where}.rating"),
        unrated=str(rat_raw["unrated"]) if rat_raw.get("unrated") is not None else None,
    )

    cl_raw = raw.get("curated_lists") or {}
    _check_keys(cl_raw, {"ref"}, f"{where}.curated_lists")
    curated = SpecCuratedLists(ref=str(cl_raw["ref"]) if cl_raw.get("ref") is not None else None)

    b_raw = raw.get("budget") or {}
    _check_keys(b_raw, {"max_bytes", "unrated_as", "safety_margin"}, f"{where}.budget")
    sm = _opt_float(b_raw, "safety_margin", f"{where}.budget")
    budget = SpecBudget(
        max_bytes=_opt_int(b_raw, "max_bytes", f"{where}.budget"),
        unrated_as=str(b_raw.get("unrated_as", "median")),
        safety_margin=0.05 if sm is None else sm,
    )

    s_raw = raw.get("sample") or {}
    _check_keys(s_raw, {"n", "seed"}, f"{where}.sample")
    sample = SpecSample(
        n=_opt_int(s_raw, "n", f"{where}.sample"),
        seed=_opt_int(s_raw, "seed", f"{where}.sample") or 0,
    )

    return SpecPasses(
        dat_filter=df,
        region=region,
        rating=rating,
        curated_lists=curated,
        budget=budget,
        sample=sample,
    )


def _platform_from(raw: Any) -> SpecPlatform:
    _check_keys(
        raw,
        {"platform", "priority", "sources", "extraction", "compression", "dat", "passes"},
        "platform",
    )
    pid = str(raw.get("platform") or "")
    where = f"platforms[{pid!r}]"
    srcs = raw.get("sources")
    if not isinstance(srcs, list):
        raise SpecError(f"{where}.sources must be a list of {{root, subpath}} entries")
    sources: list[SpecSource] = []
    for i, entry in enumerate(srcs):
        if isinstance(entry, str):
            raise SpecError(
                f"{where}.sources[{i}]: absolute paths are not allowed — name a root alias from "
                f"config/sources.yaml: {{root: <alias>, subpath: <relative dir>}}"
            )
        _check_keys(entry, {"root", "subpath", "recursive"}, f"{where}.sources[{i}]")
        if not entry.get("root"):
            raise SpecError(f"{where}.sources[{i}].root is required")
        sub = str(entry.get("subpath") or "")
        if sub.startswith("/") or ".." in Path_parts(sub):
            raise SpecError(f"{where}.sources[{i}].subpath must be relative and contain no '..'")
        sources.append(
            SpecSource(
                root=str(entry["root"]), subpath=sub, recursive=bool(entry.get("recursive", False))
            )
        )
    dat_raw = raw.get("dat") or {}
    _check_keys(dat_raw, {"retool_1g1r", "source", "file"}, f"{where}.dat")
    dat = SpecDat(
        retool_1g1r=bool(dat_raw.get("retool_1g1r", False)),
        source=str(dat_raw["source"]) if dat_raw.get("source") is not None else None,
        file=str(dat_raw["file"]) if dat_raw.get("file") is not None else None,
    )
    return SpecPlatform(
        platform=pid,
        sources=tuple(sources),
        extraction=str(raw.get("extraction", "none")),
        compression=str(raw.get("compression", "none")),
        priority=_opt_int(raw, "priority", where) or 0,
        dat=dat,
        passes=_passes_from(raw.get("passes"), f"{where}.passes"),
    )


__all__ = [
    "SPEC_VERSION",
    "Spec",
    "SpecBudget",
    "SpecCuratedLists",
    "SpecDat",
    "SpecError",
    "SpecIntent",
    "SpecPasses",
    "SpecPlatform",
    "SpecRating",
    "SpecRegion",
    "SpecSample",
    "SpecSource",
    "SpecTarget",
    "validate_spec",
]
