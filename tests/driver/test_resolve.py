"""RESOLVE phase tests — ``romfarmer.driver.resolve``.

Invariant 8 (intent brief): ``resolve_platform`` is pure — same inputs, same
``config_root`` → identical ``ResolvedBuild``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from romfarmer.config.models import CompressionFormat, ExtractionType, SelectionConfig, SourceConfig
from romfarmer.config.resolver import ResolvedPlatformConfig
from romfarmer.driver.resolve import (
    FormatNegotiationError,
    ResolvePaths,
    load_curated_lists,
    negotiate_format_chain,
    negotiate_with_profile,
    resolve_platform,
)
from romfarmer.targets.profiles.loader import ConcreteTargetProfile


def _paths(tmp_path: Path) -> ResolvePaths:
    for d in ("config", "dats", "lists"):
        (tmp_path / d).mkdir(exist_ok=True)
    return ResolvePaths.from_workspace(tmp_path)


def _resolved(src: Path, **kw: object) -> ResolvedPlatformConfig:
    return ResolvedPlatformConfig(
        platform="snes",
        extraction_type=ExtractionType.CARTRIDGE,
        compression=CompressionFormat.SEVENZ,
        sources=[SourceConfig(path=src)],
        **kw,  # type: ignore[arg-type]
    )


class TestResolvePlatform:
    def test_is_pure_same_inputs_same_product(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (tmp_path / "lists").mkdir()
        (tmp_path / "lists" / "snes-delete").write_text("Bad Game (USA).sfc\n")
        r = _resolved(src, selection=SelectionConfig(min_rating=0.7, max_size_gb=1.0))
        a = resolve_platform(r, None, _paths(tmp_path), dat_file=None, profile=None)
        b = resolve_platform(r, None, _paths(tmp_path), dat_file=None, profile=None)
        assert a == b
        assert a.manifest.chain == ("7z",)
        assert a.manifest.platform == "snes"
        assert a.manifest.rating_min == 0.7
        assert a.manifest.budget_bytes == 1024**3
        assert a.manifest.curated_exclude == frozenset({"Bad Game (USA)"})
        assert a.output_dir.is_absolute()

    def test_frozen_product(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        rb = resolve_platform(_resolved(src), None, _paths(tmp_path), dat_file=None, profile=None)
        with pytest.raises(Exception):
            rb.chain = ("zip",)  # type: ignore[misc]

    def test_no_source_directory_is_a_value_error(self, tmp_path: Path) -> None:
        r = ResolvedPlatformConfig(platform="snes", sources=[])
        with pytest.raises(ValueError, match="No source directory"):
            resolve_platform(r, None, _paths(tmp_path), dat_file=None, profile=None)

    def test_profile_disagreement_is_loud(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        profile = ConcreteTargetProfile(name="fe", platform_preferences={"snes": [("zip",)]})
        with pytest.raises(FormatNegotiationError):
            resolve_platform(_resolved(src), None, _paths(tmp_path), dat_file=None, profile=profile)


class TestNegotiation:
    def test_chain_mapping(self, tmp_path: Path) -> None:
        r = _resolved(tmp_path)
        assert negotiate_format_chain(r) == ("7z",)
        assert negotiate_with_profile(r, ConcreteTargetProfile(name="fe")) == ("7z",)


class TestCuratedLists:
    def test_include_and_exclude(self, tmp_path: Path) -> None:
        lists = tmp_path / "lists"
        lists.mkdir()
        (lists / "snes-delete").write_text("# comment\nA (USA).zip\n\nB (USA) (Disc 2).zip\n")
        (lists / "snes+Best").write_text("C (USA).sfc\n")
        inc, exc = load_curated_lists("snes", lists)
        assert exc == frozenset({"A (USA)", "B (USA)"})
        assert inc == frozenset({"C (USA)"})
