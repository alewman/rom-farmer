"""MCP tools for clone list maintenance: diff, validate, patch, metadata."""

import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Optional

from romfarmer.core.paths import get_paths

WORKSPACE_ROOT = get_paths().workspace_root


async def tool_clonelist_diff(
    old_dat: str,
    new_dat: str,
) -> dict[str, Any]:
    """Diff two DAT versions by hash — detect renames, adds, removes."""
    from romfarmer.dat_parser.clonelist import dat_diff
    from romfarmer.dat_parser.parser import DATParser

    parser = DATParser()
    old_path = _resolve_dat_path(old_dat)
    new_path = _resolve_dat_path(new_dat)

    if not old_path or not old_path.exists():
        return {"error": f"Old DAT not found: {old_dat}"}
    if not new_path or not new_path.exists():
        return {"error": f"New DAT not found: {new_dat}"}

    old_parsed = _parse_dat_file(parser, old_path)
    new_parsed = _parse_dat_file(parser, new_path)

    result = dat_diff(old_parsed, new_parsed)

    return {
        "old_dat": result.old_dat_name,
        "new_dat": result.new_dat_name,
        "old_count": result.old_count,
        "new_count": result.new_count,
        "has_changes": result.has_changes,
        "renames": [
            {"old_name": r.old_name, "new_name": r.new_name}
            for r in result.renames
        ],
        "additions": result.additions[:50],  # Cap output size
        "additions_total": len(result.additions),
        "removals": result.removals[:50],
        "removals_total": len(result.removals),
        "summary": (
            f"{len(result.renames)} renames, "
            f"{len(result.additions)} additions, "
            f"{len(result.removals)} removals"
        ),
    }


async def tool_clonelist_validate(
    clonelist: str,
    dat_file: str,
) -> dict[str, Any]:
    """Validate clone list searchTerms against a DAT — find broken references."""
    from romfarmer.dat_parser.clonelist import clonelist_validate
    from romfarmer.dat_parser.parser import DATParser

    cl_path = _resolve_clonelist_path(clonelist)
    if not cl_path or not cl_path.exists():
        return {"error": f"Clone list not found: {clonelist}"}

    dat_path = _resolve_dat_path(dat_file)
    if not dat_path or not dat_path.exists():
        return {"error": f"DAT not found: {dat_file}"}

    parser = DATParser()
    dat = _parse_dat_file(parser, dat_path)
    result = clonelist_validate(cl_path, dat)

    return {
        "clonelist": result.clonelist_name,
        "dat": result.dat_name,
        "total_search_terms": result.total_search_terms,
        "matched": result.matched,
        "match_rate": f"{result.match_rate:.1%}",
        "unmatched": [
            {
                "group": u.group,
                "search_term": u.search_term,
                "suggestion": u.suggestion,
                "similarity": round(u.similarity, 2),
            }
            for u in result.unmatched[:50]
        ],
        "unmatched_total": len(result.unmatched),
    }


async def tool_clonelist_patch(
    clonelist: str,
    old_dat: str,
    new_dat: str,
    output: Optional[str] = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Auto-patch clone list searchTerms from DAT renames. Dry-run by default."""
    from romfarmer.dat_parser.clonelist import dat_diff, clonelist_patch
    from romfarmer.dat_parser.parser import DATParser

    cl_path = _resolve_clonelist_path(clonelist)
    if not cl_path or not cl_path.exists():
        return {"error": f"Clone list not found: {clonelist}"}

    parser = DATParser()
    old_path = _resolve_dat_path(old_dat)
    new_path = _resolve_dat_path(new_dat)

    if not old_path or not old_path.exists():
        return {"error": f"Old DAT not found: {old_dat}"}
    if not new_path or not new_path.exists():
        return {"error": f"New DAT not found: {new_dat}"}

    old_parsed = _parse_dat_file(parser, old_path)
    new_parsed = _parse_dat_file(parser, new_path)

    diff_result = dat_diff(old_parsed, new_parsed)

    out_path = Path(output) if output else None
    result = clonelist_patch(cl_path, diff_result, output_path=out_path, dry_run=dry_run)

    applied_or_proposed = result.patches_applied if not dry_run else result.patches_skipped
    return {
        "clonelist": result.clonelist_name,
        "dry_run": dry_run,
        "patches": [
            {
                "group": p.group,
                "old": p.old_search_term,
                "new": p.new_search_term,
                "reason": p.reason,
            }
            for p in applied_or_proposed
        ],
        "patch_count": len(applied_or_proposed),
        "output": str(out_path) if out_path else "in-place",
    }


async def tool_clonelist_metadata_generate(
    dat_file: str,
    output: Optional[str] = None,
) -> dict[str, Any]:
    """Auto-generate Retool metadata JSON from DAT filenames."""
    from romfarmer.dat_parser.clonelist import metadata_generate, metadata_to_retool_json
    from romfarmer.dat_parser.parser import DATParser

    dat_path = _resolve_dat_path(dat_file)
    if not dat_path or not dat_path.exists():
        return {"error": f"DAT not found: {dat_file}"}

    parser = DATParser()
    dat = _parse_dat_file(parser, dat_path)

    entries = metadata_generate(dat)
    retool_json = metadata_to_retool_json(entries)

    # Count language coverage
    with_langs = sum(1 for e in entries if e.languages)

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(retool_json, f, indent=2, ensure_ascii=False)
            f.write("\n")

    # Return sample + stats (full JSON could be huge)
    sample_keys = list(retool_json.keys())[:10]
    sample = {k: retool_json[k] for k in sample_keys}

    return {
        "dat": dat.name,
        "total_entries": len(retool_json),
        "with_languages": with_langs,
        "language_coverage": f"{with_langs / len(entries):.1%}" if entries else "0%",
        "output": str(output) if output else "not saved",
        "sample": sample,
    }


# ── Helpers ──────────────────────────────────────────────────────────────


def _resolve_dat_path(dat_ref: str) -> Optional[Path]:
    """Resolve a DAT file reference to a path.

    Accepts: absolute path, relative path, or just a name (searches dats/).
    """
    p = Path(dat_ref)
    if p.is_absolute():
        return p

    # Try relative to workspace
    ws_path = WORKSPACE_ROOT / p
    if ws_path.exists():
        return ws_path

    # Search in dats/ directories
    for dats_dir in [
        WORKSPACE_ROOT / "dats",
        WORKSPACE_ROOT / "dats" / "generated",
        WORKSPACE_ROOT / "dats" / "retool-1g1r-eng",
    ]:
        if dats_dir.exists():
            for f in dats_dir.rglob(f"*{dat_ref}*"):
                if f.suffix in (".dat", ".xml", ".zip"):
                    return f

    return p  # Return as-is, caller checks .exists()


def _resolve_clonelist_path(cl_ref: str) -> Optional[Path]:
    """Resolve a clone list reference to a path.

    Searches in the retool-clonelists-metadata repo.
    """
    p = Path(cl_ref)
    if p.is_absolute():
        return p

    # Try relative to workspace
    ws_path = WORKSPACE_ROOT / p
    if ws_path.exists():
        return ws_path

    # Search in retool repos relative to workspace
    from romfarmer.core.paths import paths as _paths
    for search_dir in [
        _paths.workspace_root.parent / "retool-clonelists-metadata",
        _paths.workspace_root.parent / "retool" / "clonelists",
    ]:
        if search_dir.exists():
            for f in search_dir.rglob(f"*{cl_ref}*"):
                if f.suffix == ".json":
                    return f

    return p


def _parse_dat_file(parser, path: Path):
    """Parse a DAT file, handling ZIP-compressed DATs."""
    if path.suffix.lower() == ".zip":
        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(path, "r") as zf:
                dat_files = [f for f in zf.namelist() if f.endswith(".dat")]
                if not dat_files:
                    raise ValueError(f"No .dat file in {path.name}")
                zf.extract(dat_files[0], tmpdir)
                return parser.parse(Path(tmpdir) / dat_files[0])
    return parser.parse(path)
