"""The intent MCP surface is exactly five read-only tools (intent brief v2 §6, v4 changelog 6).

"No execute tool" is enforced here, not documented.
"""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

import pytest

from romfarmer.intent import INTENT_TOOL_NAMES, IntentTools
from romfarmer.intent.mcp import TOOL_SCHEMAS

EXPECTED = {"inventory", "capabilities", "validate_spec", "dry_run", "write_curated_list"}
FORBIDDEN_WORDS = (
    "exec",
    "execute",
    "deploy",
    "build",
    "run_build",
    "shell",
    "write_config",
    "ssh",
)
CONFIG = Path(__file__).resolve().parents[2] / "config"


def test_tool_list_is_exactly_the_five() -> None:
    assert {t["name"] for t in TOOL_SCHEMAS} == EXPECTED
    assert INTENT_TOOL_NAMES == EXPECTED
    assert len(TOOL_SCHEMAS) == 5


def test_no_execute_or_shell_tool_names() -> None:
    for t in TOOL_SCHEMAS:
        assert not any(w in t["name"] for w in FORBIDDEN_WORDS), t["name"]


def test_every_schema_has_a_handler_and_unknown_is_rejected(tmp_path: Path) -> None:
    tools = IntentTools(tmp_path)
    for t in TOOL_SCHEMAS:
        assert callable(getattr(tools, t["name"]))
    assert "error" in tools.call("farmhand_remote_exec", {"host": "x", "command": "rm -rf /"})


def test_validate_rejects_bad_spec_without_raising(tmp_path: Path) -> None:
    tools = IntentTools(tmp_path)
    out = tools.call("validate_spec", {"spec_yaml": "target: {frontend: rocknix}\nplatforms: []\n"})
    assert out["ok"] is False and "platforms" in out["error"]
    out = tools.call("validate_spec", {"spec_yaml": ": not yaml ["})
    assert out["ok"] is False


def test_write_curated_list_returns_a_hash_ref(tmp_path: Path) -> None:
    tools = IntentTools(tmp_path)
    out = tools.call(
        "write_curated_list",
        {
            "name": "snes-picks",
            "entries": [{"canonical_name": "Chrono Trigger (USA)"}],
            "generated_by": "agent:test",
        },
    )
    assert out["ref"].startswith("curated/snes-picks@sha256:") and out["include"] == 1
    assert (tmp_path / "artifacts" / "curated" / "snes-picks").exists()


@pytest.mark.skipif(not (CONFIG / "platforms" / "nes.yaml").exists(), reason="needs repo config/")
def test_loop_end_to_end_inventory_validate_dry_run(tmp_path: Path) -> None:
    cfg = tmp_path / "config"
    shutil.copytree(
        CONFIG, cfg, ignore=shutil.ignore_patterns("size_data.json", "builds", "farmhand")
    )
    (cfg / "sources.yaml").write_text(f"roots:\n  test: {tmp_path}\n")
    (tmp_path / "nes").mkdir()
    with zipfile.ZipFile(tmp_path / "nes" / "Alpha (USA).zip", "w") as zf:
        zf.writestr("Alpha (USA).nes", b"x" * 1000)
    spec_yaml = (
        "target: {frontend: batocera, device: pc, storage_bytes: 1000000, reserve_bytes: 0}\n"
        "platforms:\n"
        "  - platform: nes\n    sources: [{root: test, subpath: nes}]\n    extraction: none\n    compression: none\n"
        "    dat: {retool_1g1r: true}\n    passes: {dat_filter: false}\n"
    )
    tools = IntentTools(tmp_path, cfg)
    caps = tools.call("capabilities", {"frontend": "batocera", "device": "pc"})
    assert caps["capability_digest"].startswith("sha256:")
    v = tools.call("validate_spec", {"spec_yaml": spec_yaml})
    assert v["ok"] and v["platforms"][0]["one_g_one_r"].startswith("by-dat")
    inv = tools.call("inventory", {"spec_yaml": spec_yaml})
    assert inv["platforms"]["nes"]["units"] == 1 and inv["inventory_digest"].startswith("sha256:")
    s = tools.call("dry_run", {"spec_yaml": spec_yaml})
    assert s["spec_hash"] == v["spec_hash"] and s["platforms"][0]["units_out"] == 1
    assert s["headroom_p50"] == 1000000 - s["bytes_total_p50"]
    assert s["fits"] is True
