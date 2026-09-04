"""Entry-point gate: RESOLVE must work in a bare process (review G4 #8, cold-run finding).

"Works only because something else imported the CLI first" and "works only
from the right cwd" are the same failure class: the system functioning in the
one configuration the author happens to use.  Every new entry point (the
intent MCP server, a cron, a web thread) re-tests those assumptions.  This
test resolves a spec in a subprocess with an empty environment and a foreign
cwd, importing nothing but the driver.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

CONFIG = Path(__file__).resolve().parents[2] / "config"
SRC = Path(__file__).resolve().parents[2] / "src"


@pytest.mark.skipif(not (CONFIG / "platforms" / "nes.yaml").exists(), reason="needs repo config/")
def test_resolve_and_summarise_in_bare_subprocess(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    cfg = ws / "config"
    shutil.copytree(
        CONFIG, cfg, ignore=shutil.ignore_patterns("size_data.json", "builds", "farmhand")
    )
    # sources.yaml references an env var the way the real one does — it must be
    # satisfied from the workspace .env, not from the parent process.
    (cfg / "sources.yaml").write_text("roots:\n  test: ${ROMFARMER_TEST_ROOT}/roms\n")
    (ws / ".env").write_text(f"ROMFARMER_TEST_ROOT={tmp_path}\n")
    (tmp_path / "roms" / "nes").mkdir(parents=True)
    with zipfile.ZipFile(tmp_path / "roms" / "nes" / "Alpha (USA).zip", "w") as zf:
        zf.writestr("Alpha (USA).nes", b"x" * 100)
    spec_yaml = (
        "target: {frontend: batocera, device: pc, storage_bytes: 1000000, reserve_bytes: 0}\n"
        "platforms:\n  - platform: nes\n    sources: [{root: test, subpath: nes}]\n"
        "    extraction: none\n    compression: none\n    dat: {retool_1g1r: true}\n    passes: {dat_filter: false}\n"
    )
    (ws / "spec.yaml").write_text(spec_yaml)

    program = f"""
import json, sys
from pathlib import Path
sys.path.insert(0, {str(SRC)!r})
from romfarmer.intent import IntentTools
tools = IntentTools(Path({str(ws)!r}))
spec = Path({str(ws)!r}) / "spec.yaml"
v = tools.call("validate_spec", {{"spec_yaml": spec.read_text()}})
s = tools.call("dry_run", {{"spec_yaml": spec.read_text()}})
c = tools.call("capabilities", {{"frontend": "batocera", "device": "pc"}})
print(json.dumps({{"validate": v, "summary_fits": s.get("fits"), "err": s.get("error"), "template": bool(c.get("spec_template")), "cap_err": c.get("error")}}))
"""
    env = {
        "PATH": os.environ.get("PATH", ""),
        "ROMGROOMER_WORKSPACE": str(ws),
    }  # no HOME, no dotenv vars
    out = subprocess.run(
        [sys.executable, "-c", program],
        cwd=tmp_path.parent,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert out.returncode == 0, out.stderr[-2000:]
    result = json.loads(out.stdout.strip().splitlines()[-1])
    assert result["validate"]["ok"] is True, result
    assert result["summary_fits"] is True, result
    assert result["template"] is True and result["cap_err"] is None, result
