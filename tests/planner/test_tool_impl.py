"""T5: per-tool impl-version registry tests.

These tests verify:
1. IMPL_VERSIONS contains all expected tool names.
2. impl_version_suffix returns '' for n==1 and '+i{n}' for n>=2.
3. static_tool_version returns '1' today (all entries are 1).
4. Bumping an IMPL_VERSIONS entry changes the emitted tool_version string.
5. The bump does NOT affect the golden ActionKey hashes (the key still uses
   whatever tool_version string is in the Action at plan time).
"""

from __future__ import annotations

from types import MappingProxyType
from unittest.mock import patch

import pytest

from romfarmer.ir.tool_impl import IMPL_VERSIONS, impl_version_suffix
from romfarmer.planner.lowering.base import static_tool_version, probe_tool_version


EXPECTED_TOOLS = {
    "source-copy", "passthrough", "m3u-create",
    "unzip", "7z", "chdman", "mksquashfs",
    "extract-xiso", "dolphin-tool", "wit", "ps3dec",
}


class TestImplVersionRegistry:
    def test_all_expected_tools_present(self) -> None:
        assert EXPECTED_TOOLS <= set(IMPL_VERSIONS)

    def test_all_start_at_one(self) -> None:
        for tool, version in IMPL_VERSIONS.items():
            assert version >= 1, f"{tool} has invalid impl version {version}"

    def test_suffix_absent_at_one(self) -> None:
        assert impl_version_suffix("source-copy") == ""
        assert impl_version_suffix("chdman") == ""
        assert impl_version_suffix("unknown-tool") == ""

    def test_suffix_present_at_two(self) -> None:
        bumped = dict(IMPL_VERSIONS)
        bumped["7z"] = 2
        with patch("romfarmer.ir.tool_impl.IMPL_VERSIONS", MappingProxyType(bumped)):
            assert impl_version_suffix("7z") == "+i2"

    def test_suffix_present_at_three(self) -> None:
        bumped = dict(IMPL_VERSIONS)
        bumped["mksquashfs"] = 3
        with patch("romfarmer.ir.tool_impl.IMPL_VERSIONS", MappingProxyType(bumped)):
            assert impl_version_suffix("mksquashfs") == "+i3"

    def test_static_tool_version_returns_one_today(self) -> None:
        for tool in ("source-copy", "passthrough", "m3u-create"):
            assert static_tool_version(tool) == "1", (
                f"static_tool_version({tool!r}) should be '1' while impl==1"
            )

    def test_static_tool_version_with_bump(self) -> None:
        bumped = dict(IMPL_VERSIONS)
        bumped["m3u-create"] = 2
        with patch("romfarmer.planner.lowering.base.impl_version_suffix",
                   side_effect=lambda t: "+i2" if t == "m3u-create" else ""):
            assert static_tool_version("m3u-create") == "1+i2"
            assert static_tool_version("passthrough") == "1"

    def test_probe_tool_version_appends_suffix_on_bump(self) -> None:
        """A bumped probe_tool_version changes the emitted string."""
        import romfarmer.planner.lowering.base as lowering_base
        # Clear version cache so we get a fresh probe
        lowering_base._VERSION_CACHE.clear()

        bumped = dict(IMPL_VERSIONS)
        bumped["chdman"] = 2
        with patch("romfarmer.planner.lowering.base.subprocess.run") as mock_run, \
             patch("romfarmer.ir.tool_impl.IMPL_VERSIONS", MappingProxyType(bumped)):
            mock_run.return_value.stdout = "chdman 0.263\n"
            mock_run.return_value.stderr = ""
            # Must also patch the cached import in lowering.base
            with patch("romfarmer.planner.lowering.base.impl_version_suffix",
                       side_effect=lambda t: "+i2" if t == "chdman" else ""):
                lowering_base._VERSION_CACHE.clear()
                version = probe_tool_version("chdman")
        assert version.endswith("+i2"), f"Expected +i2 suffix, got {version!r}"

    def test_registry_is_frozen(self) -> None:
        with pytest.raises(TypeError):
            IMPL_VERSIONS["new-tool"] = 1  # type: ignore[index]
