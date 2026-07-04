"""Tests for romfarmer.ir.identity."""

import pytest

from romfarmer.ir.identity import Identity, IdentityConflict, ZipIdentity


class TestZipIdentity:
    def test_serialized(self) -> None:
        zi = ZipIdentity(member_crc32=0xDEADBEEF, member_size=1024, member_name="game.bin")
        assert zi.serialized() == "3735928559:1024:game.bin"

    def test_frozen(self) -> None:
        zi = ZipIdentity(member_crc32=1, member_size=2, member_name="x")
        with pytest.raises(Exception):
            zi.member_crc32 = 99  # type: ignore[misc]


class TestIdentityIsComplete:
    def test_complete_with_sha256(self) -> None:
        ident = Identity(sha256="abc123")
        assert ident.is_complete is True

    def test_incomplete_without_sha256(self) -> None:
        assert Identity(md5="abc").is_complete is False
        assert Identity(size=100).is_complete is False
        assert Identity().is_complete is False


class TestIdentityMerge:
    def test_merge_disjoint(self) -> None:
        a = Identity(sha256="aaa", size=100)
        b = Identity(md5="bbb")
        result = a.merged(b)
        assert result.sha256 == "aaa"
        assert result.md5 == "bbb"
        assert result.size == 100

    def test_merge_agreeing_fields(self) -> None:
        a = Identity(sha256="same", md5="m")
        b = Identity(sha256="same", size=50)
        result = a.merged(b)
        assert result.sha256 == "same"
        assert result.md5 == "m"
        assert result.size == 50

    def test_merge_with_none_self(self) -> None:
        empty = Identity()
        other = Identity(sha256="xyz")
        assert empty.merged(other).sha256 == "xyz"

    def test_merge_with_none_other(self) -> None:
        ident = Identity(sha256="xyz")
        assert ident.merged(Identity()).sha256 == "xyz"

    def test_merge_conflict_sha256(self) -> None:
        a = Identity(sha256="aaa")
        b = Identity(sha256="bbb")
        with pytest.raises(IdentityConflict):
            a.merged(b)

    def test_merge_conflict_md5(self) -> None:
        a = Identity(md5="aaa")
        b = Identity(md5="bbb")
        with pytest.raises(IdentityConflict):
            a.merged(b)

    def test_merge_conflict_size(self) -> None:
        a = Identity(size=100)
        b = Identity(size=200)
        with pytest.raises(IdentityConflict):
            a.merged(b)

    def test_merge_conflict_zip_identity(self) -> None:
        zi_a = ZipIdentity(1, 10, "a.bin")
        zi_b = ZipIdentity(2, 10, "a.bin")
        a = Identity(zip_identity=zi_a)
        b = Identity(zip_identity=zi_b)
        with pytest.raises(IdentityConflict):
            a.merged(b)

    def test_merge_returns_new_instance(self) -> None:
        a = Identity(sha256="a")
        b = Identity(md5="b")
        result = a.merged(b)
        assert result is not a
        assert result is not b

    def test_identity_conflict_is_value_error(self) -> None:
        a = Identity(sha256="aaa")
        b = Identity(sha256="bbb")
        with pytest.raises(ValueError):
            a.merged(b)


class TestIdentityBestKey:
    def test_sha256_wins(self) -> None:
        ident = Identity(sha256="s", md5="m", zip_identity=ZipIdentity(1, 2, "x"))
        assert ident.best_key() == ("sha256", "s")

    def test_md5_when_no_sha256(self) -> None:
        ident = Identity(md5="m", zip_identity=ZipIdentity(1, 2, "x"))
        assert ident.best_key() == ("md5", "m")

    def test_zip_identity_last_resort(self) -> None:
        zi = ZipIdentity(member_crc32=12345, member_size=512, member_name="rom.bin")
        ident = Identity(zip_identity=zi)
        kind, value = ident.best_key()
        assert kind == "zip_identity"
        assert value == "12345:512:rom.bin"

    def test_raises_when_all_none(self) -> None:
        with pytest.raises(ValueError):
            Identity().best_key()

    def test_size_only_raises(self) -> None:
        with pytest.raises(ValueError):
            Identity(size=100).best_key()
