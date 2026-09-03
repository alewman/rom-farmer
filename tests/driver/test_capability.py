"""Capability is data, not model knowledge (intent brief §5)."""

from __future__ import annotations

from pathlib import Path

import pytest

from romfarmer.driver.capability import capabilities

CONFIG = Path(__file__).resolve().parents[2] / "config"


@pytest.mark.skipif(not (CONFIG / "devices" / "r36s.yaml").exists(), reason="needs repo config/")
class TestCapabilities:
    def test_r36s_tiers(self) -> None:
        caps = capabilities("rocknix", "r36s", CONFIG)
        assert caps.require("psx").tier == "A"
        assert caps.require("psp").tier == "C"
        assert caps.require("dreamcast").tier == "X"
        assert caps.reserve_bytes == 16_000_000_000
        assert "dreamcast" not in caps.shippable()
        assert "snes" in caps.shippable()

    def test_unlisted_platform_is_an_error_not_a_guess(self) -> None:
        caps = capabilities("rocknix", "r36s", CONFIG)
        with pytest.raises(KeyError, match="does not guess"):
            caps.require("vectrex")

    def test_pc_default_tier(self) -> None:
        caps = capabilities("batocera", "pc", CONFIG)
        assert caps.require("vectrex").tier == "A"

    def test_digest_is_stable_and_prefixed(self) -> None:
        a = capabilities("rocknix", "r36s", CONFIG).digest()
        b = capabilities("rocknix", "r36s", CONFIG).digest()
        assert a == b and a.startswith("sha256:")

    def test_profile_supports_respects_tier_x(self) -> None:
        from romfarmer.ir.catalog import PlatformId
        from romfarmer.targets.profiles.loader import TargetProfileLoader

        p = TargetProfileLoader(CONFIG).load("rocknix/r36s")
        assert p.supports(PlatformId("psx")) and not p.supports(PlatformId("dreamcast"))
