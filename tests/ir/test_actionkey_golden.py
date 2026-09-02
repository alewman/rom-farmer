"""Golden-hash tests for romfarmer.ir.actions.resolve_key.

GOLDEN VALUES — computed 2026-07-03 and hardcoded below.

If ANY of these assertions fail, it means the ActionKey canonicalization has
changed. That is a cache-invalidation event for EVERY user of the action
cache — not a test to update casually. Before changing a golden value:
  1. Understand exactly why the hash changed.
  2. Write a migration script or bump the cache-schema version.
  3. Update the comment date next to the constant.
"""

import types

import pytest

from romfarmer.ir.actions import (
    Action,
    ActionId,
    ArtifactDecl,
    ContentRef,
    PendingRef,
    Retention,
    resolve_key,
)
from romfarmer.ir.identity import Identity

# ──────────────────────────────────────────────────────────────────────────────
# GOLDEN VALUES — computed 2026-07-03. Do NOT update without a cache-migration
# plan. See module docstring.
# ──────────────────────────────────────────────────────────────────────────────

# Case 1: chdman with two params, one ContentRef input
GOLDEN_CHDMAN = "421755176f73642bbc27f9cb10dc83112765bbfd797e081196473423a9f5679b"

# Case 2: unzip with empty params, one ContentRef input
GOLDEN_UNZIP = "3ef16b0022dac08df385550a853d6adf5aa77f5264f61b510fd419f598184906"

# Case 3a: mksquashfs, two ContentRef inputs in forward order
GOLDEN_SQUASHFS_FWD = "4b3e7c4a0e5756997a119fcad1faed4f47dd63d141fa7ee06552a0214e3aed42"

# Case 3b: same action, inputs reversed → DIFFERENT hash (order is preserved)
GOLDEN_SQUASHFS_REV = "155f98ce22abd694e2d62dd89de9838b7fee755e72be2de339d9f2c0228ee32e"

# Case 4: PendingRef resolved through known_outputs
GOLDEN_PENDING_RESOLVED = "d3fdddaca3eaee7d8b7738a62992c741f22ae2159c8acd02332c5b826f8fff80"


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────


def _chdman_action() -> Action:
    return Action(
        action_id=ActionId("act-001"),
        tool="chdman",
        tool_version="0.263",
        params={"input_track": "0", "output_compression": "cdfl"},
        inputs=(ContentRef(sha256="a" * 64),),
        outputs=(ArtifactDecl("game.chd", "chd", Retention.TERMINAL),),
    )


def _unzip_action() -> Action:
    return Action(
        action_id=ActionId("act-002"),
        tool="unzip",
        tool_version="6.0",
        params={},
        inputs=(ContentRef(sha256="b" * 64),),
        outputs=(ArtifactDecl("out.bin", "bin", Retention.INTERMEDIATE),),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Golden hash assertions
# ──────────────────────────────────────────────────────────────────────────────


class TestGoldenActionKey:
    def test_chdman_golden(self) -> None:
        key = resolve_key(_chdman_action(), {})
        assert key == GOLDEN_CHDMAN

    def test_unzip_golden(self) -> None:
        key = resolve_key(_unzip_action(), {})
        assert key == GOLDEN_UNZIP

    def test_squashfs_input_order_fwd(self) -> None:
        action = Action(
            action_id=ActionId("act-003"),
            tool="mksquashfs",
            tool_version="4.6",
            params={"comp": "zstd"},
            inputs=(ContentRef(sha256="c" * 64), ContentRef(sha256="d" * 64)),
            outputs=(ArtifactDecl("out.squashfs", "squashfs", Retention.TERMINAL),),
        )
        assert resolve_key(action, {}) == GOLDEN_SQUASHFS_FWD

    def test_squashfs_input_order_rev(self) -> None:
        """Input order is preserved in the canonical form — swapping inputs
        produces a different ActionKey."""
        action = Action(
            action_id=ActionId("act-003"),
            tool="mksquashfs",
            tool_version="4.6",
            params={"comp": "zstd"},
            inputs=(ContentRef(sha256="d" * 64), ContentRef(sha256="c" * 64)),
            outputs=(ArtifactDecl("out.squashfs", "squashfs", Retention.TERMINAL),),
        )
        assert resolve_key(action, {}) == GOLDEN_SQUASHFS_REV
        assert GOLDEN_SQUASHFS_REV != GOLDEN_SQUASHFS_FWD

    def test_pending_ref_resolved(self) -> None:
        action = Action(
            action_id=ActionId("act-004"),
            tool="ps3dec",
            tool_version="1.0",
            params={},
            inputs=(PendingRef(producer=ActionId("act-001"), output_index=0),),
            outputs=(ArtifactDecl("decrypted.iso", "iso", Retention.INTERMEDIATE),),
        )
        known = {ActionId("act-001"): (Identity(sha256="e" * 64),)}
        assert resolve_key(action, known) == GOLDEN_PENDING_RESOLVED


# ──────────────────────────────────────────────────────────────────────────────
# Behavioural / invariant tests
# ──────────────────────────────────────────────────────────────────────────────


class TestResolveKeyBehaviour:
    def test_pending_ref_unknown_producer_returns_none(self) -> None:
        action = Action(
            action_id=ActionId("a"),
            tool="t",
            tool_version="1",
            params={},
            inputs=(PendingRef(producer=ActionId("missing"), output_index=0),),
            outputs=(),
        )
        assert resolve_key(action, {}) is None

    def test_pending_ref_output_index_out_of_range_returns_none(self) -> None:
        action = Action(
            action_id=ActionId("a"),
            tool="t",
            tool_version="1",
            params={},
            inputs=(PendingRef(producer=ActionId("p"), output_index=5),),
            outputs=(),
        )
        known = {ActionId("p"): (Identity(sha256="x" * 64),)}
        assert resolve_key(action, known) is None

    def test_pending_ref_output_sha256_none_returns_none(self) -> None:
        action = Action(
            action_id=ActionId("a"),
            tool="t",
            tool_version="1",
            params={},
            inputs=(PendingRef(producer=ActionId("p"), output_index=0),),
            outputs=(),
        )
        known = {ActionId("p"): (Identity(size=100),)}  # no sha256
        assert resolve_key(action, known) is None

    def test_no_inputs_resolves(self) -> None:
        action = Action(
            action_id=ActionId("a"),
            tool="fetch",
            tool_version="1",
            params={},
            inputs=(),
            outputs=(),
        )
        key = resolve_key(action, {})
        assert key is not None
        assert len(key) == 64  # sha256 hex

    def test_params_key_order_does_not_matter(self) -> None:
        """Params are sorted before hashing — insertion order is irrelevant."""
        a_ab = Action(
            action_id=ActionId("a"),
            tool="t",
            tool_version="1",
            params={"a": "1", "b": "2"},
            inputs=(ContentRef(sha256="f" * 64),),
            outputs=(),
        )
        a_ba = Action(
            action_id=ActionId("a"),
            tool="t",
            tool_version="1",
            params={"b": "2", "a": "1"},
            inputs=(ContentRef(sha256="f" * 64),),
            outputs=(),
        )
        assert resolve_key(a_ab, {}) == resolve_key(a_ba, {})

    def test_deterministic_across_calls(self) -> None:
        key1 = resolve_key(_chdman_action(), {})
        key2 = resolve_key(_chdman_action(), {})
        assert key1 == key2


class TestActionImmutability:
    def test_params_frozen_from_dict(self) -> None:
        action = _chdman_action()
        # MappingProxyType raises TypeError on item assignment
        with pytest.raises(TypeError):
            action.params["new_key"] = "v"  # type: ignore[index]

    def test_params_frozen_from_proxy(self) -> None:
        action = Action(
            action_id=ActionId("a"),
            tool="t",
            tool_version="1",
            params=types.MappingProxyType({"k": "v"}),
            inputs=(),
            outputs=(),
        )
        with pytest.raises(TypeError):
            action.params["new_key"] = "v"  # type: ignore[index]

    def test_action_frozen(self) -> None:
        action = _chdman_action()
        with pytest.raises(Exception):
            action.tool = "other"  # type: ignore[misc]


# ──────────────────────────────────────────────────────────────────────────────
# T4: param runtime validation + NFC normalisation (key-preserving)
# ──────────────────────────────────────────────────────────────────────────────


class TestParamValidation:
    def test_int_param_value_rejected(self) -> None:
        """Integer param values must raise TypeError — they'd serialise
        differently from their str equivalent and corrupt the cache key."""
        with pytest.raises(TypeError, match="must be str"):
            Action(
                action_id=ActionId("x"),
                tool="chdman",
                tool_version="1",
                params={"level": 9},  # type: ignore[arg-type]
                inputs=(),
                outputs=(),
            )

    def test_int_param_key_rejected(self) -> None:
        with pytest.raises(TypeError, match="must be str"):
            Action(
                action_id=ActionId("x"),
                tool="chdman",
                tool_version="1",
                params={1: "value"},  # type: ignore[arg-type]
                inputs=(),
                outputs=(),
            )

    def test_nfd_value_normalised_to_nfc(self) -> None:
        """An NFD param value (e.g. from a Mac-sourced filename) must produce
        the same ActionKey as its NFC equivalent."""
        import unicodedata

        # 'é' as NFC (U+00E9) vs NFD (e + U+0301)
        nfc_val = "\u00e9"  # é precomposed
        nfd_val = "e\u0301"  # e + combining acute accent
        assert nfc_val != nfd_val  # sanity: the strings are byte-different
        assert unicodedata.normalize("NFC", nfd_val) == nfc_val

        action_nfc = Action(
            action_id=ActionId("a"),
            tool="m3u-create",
            tool_version="1",
            params={"name": nfc_val},
            inputs=(),
            outputs=(),
        )
        action_nfd = Action(
            action_id=ActionId("a"),
            tool="m3u-create",
            tool_version="1",
            params={"name": nfd_val},
            inputs=(),
            outputs=(),
        )
        # After __post_init__ normalises to NFC, both should produce the
        # same stored value and therefore the same ActionKey.
        assert action_nfc.params["name"] == nfc_val
        assert action_nfd.params["name"] == nfc_val
        assert resolve_key(action_nfc, {}) == resolve_key(action_nfd, {})

    def test_nfc_normalisation_does_not_change_golden_keys(self) -> None:
        """ASCII params are already NFC; golden hashes must be unchanged."""
        assert resolve_key(_chdman_action(), {}) == GOLDEN_CHDMAN
        assert resolve_key(_unzip_action(), {}) == GOLDEN_UNZIP
